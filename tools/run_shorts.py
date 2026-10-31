"""Build and publish the next Short (YouTube Shorts + Facebook Reel). Runs 3x a day from .github/workflows/shorts.yml.
--preview: build only (no upload). --episode N: force a specific short. Publishing needs data/SHORTS_GO (owner approval)."""
import argparse, datetime as dt, glob, json, os, subprocess, sys, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_short
STATE = "data/shorts_state.json"
def load(): return json.load(open(STATE)) if os.path.exists(STATE) else {"shorts": {}}
def save(s): json.dump(s, open(STATE, "w"), indent=1)

def pick(state, forced=None):
    files = sorted(glob.glob("shorts/*.json"))
    def prio(p):
        try: return 0 if json.load(open(p, encoding="utf-8")).get("priority") else 1
        except Exception: return 1
    for p in sorted(files, key=lambda p: (prio(p), p)):
        s = json.load(open(p, encoding="utf-8")); n = f"{int(s['episode']):03d}"
        if forced is not None and int(s["episode"]) != forced: continue
        if forced is None and (n in state["shorts"] and state["shorts"][n].get("yt") and state["shorts"][n].get("fb")): continue
        if s.get("needs_review") and forced is None: print("skip (needs review):", p); continue
        e, _ = validate_short.validate(p)
        if e: print("skip (invalid):", p, e[:3]); continue
        return n, p, s
    return None, None, None

def srt(shots_words):
    def ts(x): h, r = divmod(x, 3600); m, s = divmod(r, 60); return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    out, i = [], 1
    for t0, t1, txt in shots_words: out.append(f"{i}\n{ts(t0)} --> {ts(t1)}\n{txt}\n"); i += 1
    return "\n".join(out)

def post_comments(state):
    import youtube, facebook
    now = dt.datetime.now(dt.timezone.utc)
    for n, st in state["shorts"].items():
        if st.get("comment_done") or not st.get("published_at"): continue
        if dt.datetime.fromisoformat(st["published_at"]) + dt.timedelta(minutes=30) > now: continue
        ok = True
        try:
            if st.get("yt"): ok &= youtube.comment(st["yt"], st["first_comment"])
            if st.get("fb"): ok &= facebook.comment(st["fb"], st["first_comment"])
        except Exception as e: print("comment error", e); ok = False
        if ok: st["comment_done"] = True

SLOTS_NY = (8, 14, 18)          # owner's schedule: 8 am, 2 pm, 6 pm New York time (handles EDT/EST automatically)
def due_slot(state):
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York"); now = dt.datetime.now(dt.timezone.utc)
    for h in SLOTS_NY:
        local = now.astimezone(ny); slot = local.replace(hour=h, minute=0, second=0, microsecond=0)
        if -dt.timedelta(minutes=40) <= now - slot <= dt.timedelta(hours=4) and slot.isoformat() not in state.setdefault("slots_done", []):
            return slot.astimezone(dt.timezone.utc)
    return None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", action="store_true"); ap.add_argument("--episode", type=int); ap.add_argument("--scheduled", action="store_true", help="cron run: only act inside a New York slot window"); ap.add_argument("--check-due", action="store_true"); a = ap.parse_args()
    ap2 = a
    state = load(); slot = None
    if getattr(a, "check_due", False):
        print("DUE" if due_slot(state) else "NOT_DUE"); return 0
    if not a.preview and not a.scheduled and a.episode is not None: slot = due_slot(state)   # a manual publish fills the current slot so it is not doubled later
    if a.scheduled:
        slot = due_slot(state)
        if not slot: print("no New York slot due now"); return 0
    if not a.preview:
        if not os.path.exists("data/SHORTS_GO") and a.episode is None: print("publishing not approved yet (data/SHORTS_GO missing)"); return 0
        try: post_comments(state); save(state)
        except Exception as e: print("comments skipped:", e)
    n, path, s = pick(state, a.episode)
    if not n: print("no short left to publish"); return 0
    out = f"out/short-{n}.mp4"; work = f"work/short-{n}"
    print("building", path, flush=True)
    r = subprocess.run([sys.executable, "-u", "shorts2d/make_short2d.py", path, out, "--workdir", work])
    if r.returncode or not os.path.exists(out): print("build failed"); return 1
    if a.preview: print("preview built:", out); return 0
    seo = s["seo"]; tags = [h.lstrip("#") for h in seo.get("hashtags", [])]
    desc = seo["description"] + ("" if "#shorts" in seo["description"].lower() else " #shorts") + "\n\nSources: " + " ".join(s.get("sources", [])[:3]) + "\nEducational true story based on public records. No hacking instructions."
    st = state["shorts"].setdefault(n, {}); st.update({"title": seo["title"], "first_comment": seo["first_comment"]}); err = []
    if not st.get("yt"):
        try:
            import youtube
            soon = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=6)).replace(microsecond=0)
            pub = max(slot, soon) if slot else soon
            vid = youtube.upload_video(out, {"title": seo["title"][:100], "description": desc[:4900], "tags": tags + ["cybersecurity", "hacking", "true story", "shorts"], "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"}, pub.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
            st["yt"] = vid; st["published_at"] = pub.isoformat(); save(state); print("YouTube Short OK", vid)
            if os.path.exists(f"{work}/thumb.jpg"):
                try: youtube.set_thumbnail(vid, f"{work}/thumb.jpg"); print("YouTube thumbnail set")
                except Exception as e: print("thumbnail warning (Shorts thumbnails via API are best-effort):", e)
            try:
                sh = json.load(open(f"{work}/shots.json")); tm = json.load(open(f"{work}/timing.json")); t0 = 0.0; cues = []
                for sc, x in zip(s["scenes"], tm):
                    ws = x["words"]
                    for i in range(0, len(ws), 4): grp = ws[i:i + 4]; cues.append((t0 + grp[0]["s"], t0 + grp[-1]["e"] + .1, " ".join(w["w"] for w in grp)))
                    t0 += x["duration"] + .18
                youtube.upload_captions(vid, srt(cues))
            except Exception as e: print("captions warning:", e)
        except Exception as e: traceback.print_exc(); err.append(f"youtube: {e}")
    if not st.get("fb"):
        try:
            import facebook
            vid = facebook.upload_reel(out, seo["facebook_text"], seo["title"]); st["fb"] = vid; st.setdefault("published_at", dt.datetime.now(dt.timezone.utc).isoformat()); print("Facebook Reel OK", vid)
        except Exception as e: traceback.print_exc(); err.append(f"facebook: {e}")
    if slot and not err: state.setdefault("slots_done", []).append(slot.astimezone(__import__("zoneinfo").ZoneInfo("America/New_York")).isoformat())
    save(state)
    if err: print("FAILED:", err); return 1
    print(f"short {n} published"); return 0

if __name__ == "__main__": sys.exit(main())
