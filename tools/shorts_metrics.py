"""Performance tracking for every published Short (owner's growth system).
Snapshots at 1 h, 6 h, 24 h, 48 h, 7 d after publishing -> data/metrics.json; report -> reports/shorts-performance.md.
Never invents numbers: anything the APIs do not return is recorded as "unavailable"."""
import datetime as dt, json, os, statistics, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import youtube, facebook
BUCKETS = [("1h", 1), ("6h", 6), ("24h", 24), ("48h", 48), ("7d", 168)]
STATE, OUT, REP = "data/shorts_state.json", "data/metrics.json", "reports/shorts-performance.md"

def yt_stats(ids):
    out = {}
    for i in range(0, len(ids), 50):
        r = requests.get("https://www.googleapis.com/youtube/v3/videos", headers=youtube.H(), params={"part": "statistics,status", "id": ",".join(ids[i:i + 50])}, timeout=30)
        if r.status_code == 200:
            for v in r.json().get("items", []): out[v["id"]] = {k: int(x) for k, x in v.get("statistics", {}).items() if x.isdigit()} | {"privacy": v.get("status", {}).get("privacyStatus")}
    return out

def yt_analytics(ids, start):
    sets = ["engagedViews,views,averageViewDuration,averageViewPercentage,likes,shares,comments,subscribersGained",
            "views,averageViewDuration,averageViewPercentage,likes,shares,comments,subscribersGained"]
    for m in sets:
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=youtube.H(), timeout=30, params={
            "ids": "channel==MINE", "startDate": start, "endDate": str(dt.date.today()), "metrics": m, "dimensions": "video", "filters": "video==" + ",".join(ids)})
        if r.status_code == 200:
            j = r.json(); cols = [c["name"] for c in j["columnHeaders"]]
            return {row[0]: dict(zip(cols[1:], row[1:])) for row in j.get("rows", [])}, m
    return {}, f"unavailable ({r.status_code}: {r.text[:120]})"

def fb_metrics(vid):
    out = {}
    try:
        r = requests.get(f"{facebook.G}/{vid}/video_insights", params=facebook._auth(), timeout=30)
        if r.status_code == 200:
            for m in r.json().get("data", []):
                vals = m.get("values") or []
                if vals and isinstance(vals[0].get("value"), (int, float)): out[m["name"]] = vals[0]["value"]
        else: out["error"] = f"{r.status_code}: {r.text[:120]}"
        r = requests.get(f"{facebook.G}/{vid}", params={**facebook._auth(), "fields": "likes.summary(true).limit(0),comments.summary(true).limit(0)"}, timeout=30)
        if r.status_code == 200:
            j = r.json(); out["likes"] = j.get("likes", {}).get("summary", {}).get("total_count"); out["comments"] = j.get("comments", {}).get("summary", {}).get("total_count")
    except Exception as e: out["error"] = str(e)[:120]
    return out or {"status": "unavailable"}

def main():
    st = json.load(open(STATE)); db = json.load(open(OUT)) if os.path.exists(OUT) else {}
    now = dt.datetime.now(dt.timezone.utc); shorts = {n: s for n, s in st["shorts"].items() if s.get("published_at")}
    yids = [s["yt"] for s in shorts.values() if s.get("yt")]
    ys = yt_stats(yids) if yids else {}
    first = min((dt.datetime.fromisoformat(s["published_at"]) for s in shorts.values()), default=now).date()
    ya, ya_note = yt_analytics(yids, str(first)) if yids else ({}, "no videos")
    for n, s in shorts.items():
        age_h = (now - dt.datetime.fromisoformat(s["published_at"])).total_seconds() / 3600
        rec = db.setdefault(n, {"title": s.get("title"), "yt": s.get("yt"), "fb": s.get("fb"), "published_at": s["published_at"], "snapshots": {}})
        due = [b for b, h in BUCKETS if age_h >= h and b not in rec["snapshots"]]
        if not due: continue
        snap = {"taken_at": now.isoformat(), "age_hours": round(age_h, 1),
                "youtube": {**ys.get(s.get("yt"), {"status": "unavailable"}), "analytics": ya.get(s.get("yt"), f"unavailable ({ya_note})" if isinstance(ya_note, str) and ya_note.startswith("unavailable") else "not yet reported (YouTube Analytics lags ~1-2 days)")},
                "facebook": fb_metrics(s["fb"]) if s.get("fb") else {"status": "not published"}}
        rec["snapshots"][due[-1]] = snap          # one API snapshot fills the latest bucket reached
    json.dump(db, open(OUT, "w"), indent=1)
    # ---- report with a baseline (median of the channel's own Shorts at the same age)
    L = ["# Shorts performance", f"Updated {now:%Y-%m-%d %H:%M} UTC. Raw YouTube views count from the first frame since Aug 24 2026; judge by engaged views, average % viewed and shares.", ""]
    for b, _ in BUCKETS:
        rows = [(n, r["snapshots"][b]) for n, r in db.items() if b in r["snapshots"]]
        if not rows: continue
        views = [x["youtube"].get("viewCount", 0) for _, x in rows if isinstance(x["youtube"].get("viewCount"), int)]
        med = statistics.median(views) if views else 0
        L += [f"## At {b}", "| Short | YT views | YT likes | YT comments | engaged views | avg % viewed | FB plays | verdict |", "|---|---|---|---|---|---|---|---|"]
        for n, x in rows:
            y = x["youtube"]; a = y.get("analytics") if isinstance(y.get("analytics"), dict) else {}
            fbp = next((v for k, v in x["facebook"].items() if "play" in k or "views" in k), "n/a")
            v = y.get("viewCount", 0) if isinstance(y.get("viewCount"), int) else None
            verdict = "insufficient data" if v is None or len(views) < 3 else ("exceptional" if v > 3 * med else "above baseline" if v > 1.3 * med else "below baseline" if v < .7 * med else "normal")
            L.append(f"| {n} {db[n]['title'][:40]} | {v if v is not None else 'n/a'} | {y.get('likeCount', 'n/a')} | {y.get('commentCount', 'n/a')} | {a.get('engagedViews', 'n/a')} | {a.get('averageViewPercentage', 'n/a')} | {fbp} | {verdict} |")
        L.append("")
    os.makedirs("reports", exist_ok=True); open(REP, "w").write("\n".join(L)); print("\n".join(L[:40]))

if __name__ == "__main__": main()
