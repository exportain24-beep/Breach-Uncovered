#!/usr/bin/env python3
"""Weekly performance + SEO status report -> reports/seo-report.md (never fails the workflow; every error is written into the report).
Sources: YouTube Data API (stats per uploaded video), YouTube Analytics API (impressions, CTR, retention - if the API is enabled and the token has the scope),
Facebook Graph (video views). Nothing is guessed: a missing number is reported as missing together with the API error."""
import datetime as dt, json, os, sys
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import youtube, facebook

out = [f"# SEO & performance report - {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC", ""]
state = json.load(open("data/state.json")) if os.path.exists("data/state.json") else {"episodes": {}}
eps = {n: e for n, e in state["episodes"].items() if e.get("yt") or e.get("fb")}
out.append(f"Published/scheduled episodes tracked: {len(eps)}\n")

# ---- YouTube Data API: stats
out.append("## YouTube - Data API (public stats)\n")
ids = [e["yt"] for e in eps.values() if e.get("yt")]
try:
    if ids:
        r = requests.get(f"{youtube.API}/videos", headers=youtube.H(), params={"part": "snippet,statistics,status", "id": ",".join(ids)}, timeout=30)
        if r.status_code != 200: out.append(f"- ERROR {r.status_code}: {r.text[:300]}")
        else:
            out.append("| Ep | Title | Privacy | Published/scheduled | Views | Likes | Comments |\n|---|---|---|---|---|---|---|")
            byid = {v["id"]: v for v in r.json().get("items", [])}
            for n, e in sorted(eps.items(), key=lambda x: int(x[0])):
                v = byid.get(e.get("yt"))
                if not v: out.append(f"| {n} | (not found: deleted or private?) | | | | | |"); continue
                s, st = v.get("statistics", {}), v.get("status", {})
                out.append(f"| {n} | {v['snippet']['title'][:60]} | {st.get('privacyStatus')} | {st.get('publishAt') or v['snippet'].get('publishedAt')} | {s.get('viewCount', 0)} | {s.get('likeCount', 0)} | {s.get('commentCount', 0)} |")
    else: out.append("- no YouTube videos yet")
except Exception as ex: out.append(f"- ERROR: {ex}")

# ---- YouTube Analytics API
out.append("\n## YouTube - Analytics API (last 28 days, per video)\n")
end = dt.date.today(); start = end - dt.timedelta(days=28)
sets = [("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,videoThumbnailImpressions,videoThumbnailImpressionsClickRate",),
        ("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained",)]
done = False
for (metrics,) in sets:
    try:
        r = requests.get("https://youtubeanalytics.googleapis.com/v2/reports", headers=youtube.H(), timeout=30,
                         params={"ids": "channel==MINE", "startDate": str(start), "endDate": str(end), "metrics": metrics, "dimensions": "video", "sort": "-views", "maxResults": 50})
        if r.status_code == 200:
            j = r.json(); cols = [c["name"] for c in j.get("columnHeaders", [])]
            out.append("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols))
            for row in j.get("rows", []): out.append("| " + " | ".join(str(round(x, 3)) if isinstance(x, float) else str(x) for x in row) + " |")
            if not j.get("rows"): out.append("(no rows yet)")
            if "videoThumbnailImpressions" not in cols: out.append("\nNote: impressions/CTR columns were not accepted by the API for this channel.")
            done = True; break
        out.append(f"- metrics `{metrics[:40]}...` -> {r.status_code}: {r.text[:250]}")
    except Exception as ex: out.append(f"- ERROR: {ex}")
if not done: out.append("- Analytics unavailable. Usual fix: enable 'YouTube Analytics API' in the Google Cloud project and re-issue the refresh token with scope yt-analytics.readonly.")

# ---- Facebook
out.append("\n## Facebook - video stats\n")
try:
    out.append("| Ep | Video id | Views | Likes | Comments |\n|---|---|---|---|---|")
    for n, e in sorted(eps.items(), key=lambda x: int(x[0])):
        if not e.get("fb"): continue
        r = requests.get(f"{facebook.G}/{e['fb']}", params={**facebook._auth(), "fields": "title,length,views,likes.summary(true).limit(0),comments.summary(true).limit(0)"}, timeout=30)
        if r.status_code != 200: out.append(f"| {n} | {e['fb']} | ERROR {r.status_code}: {r.text[:150]} | | |"); continue
        j = r.json(); out.append(f"| {n} | {e['fb']} | {j.get('views', 'n/a')} | {j.get('likes', {}).get('summary', {}).get('total_count', 'n/a')} | {j.get('comments', {}).get('summary', {}).get('total_count', 'n/a')} |")
except Exception as ex: out.append(f"- ERROR: {ex}")

os.makedirs("reports", exist_ok=True); open("reports/seo-report.md", "w").write("\n".join(out) + "\n"); print("\n".join(out))
