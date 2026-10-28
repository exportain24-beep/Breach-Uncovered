#!/usr/bin/env python3
"""Daily orchestrator: next unpublished episode -> voice (eleven_v4_turbo) -> visuals -> render -> thumbnail -> SEO
-> scheduled upload to YouTube + Facebook. Safe to re-run: state.json remembers what is already live per platform.

  python3 tools/run_episode.py [--episode N] [--dry]      (--dry = build everything, upload nothing)
"""
import argparse, datetime as dt, glob, json, os, sys, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, HERE)
os.chdir(ROOT)
import validate_script, tts, media, render, seo, thumbnail

SLOTS_UTC = [(17, 0), (23, 0)]          # 23:00 and 05:00 Bangladesh time = US lunch / US evening
MIN_LEAD = dt.timedelta(minutes=150)
STATE = "data/state.json"

def load_state():
    return json.load(open(STATE)) if os.path.exists(STATE) else {"episodes": {}, "playlists": {}, "slots_used": []}
def save_state(s): os.makedirs("data", exist_ok=True); json.dump(s, open(STATE, "w"), indent=1)

def next_slot(state):
    now = dt.datetime.now(dt.timezone.utc); used = set(state.get("slots_used", []))
    for day in range(0, 4):
        for h, m in SLOTS_UTC:
            t = (now + dt.timedelta(days=day)).replace(hour=h, minute=m, second=0, microsecond=0)
            if t - now >= MIN_LEAD and t.isoformat() not in used: return t
    raise RuntimeError("no free slot")

def pick_episode(cases, state, forced=None):
    for c in cases:
        n = c["episode"]
        if forced and n != forced: continue
        st = state["episodes"].get(str(n), {})
        if st.get("yt") and st.get("fb"): continue
        files = glob.glob(f"scripts/{n:03d}-*.json")
        if not files: print(f"episode {n}: no script yet — skipping"); continue
        errs, _ = validate_script.validate(files[0])
        sc = json.load(open(files[0]))
        if errs: print(f"episode {n}: script fails validation {errs[:3]} — skipping"); continue
        if sc.get("needs_review"): print(f"episode {n}: needs_review ({sc.get('review_note','')}) — skipping"); continue
        return n, files[0], sc
    return None, None, None

def post_pending_comments(state):
    import youtube, facebook
    now = dt.datetime.now(dt.timezone.utc)
    for n, st in state["episodes"].items():
        if st.get("comment_done") or not st.get("publish_at") or dt.datetime.fromisoformat(st["publish_at"]) + dt.timedelta(minutes=10) > now: continue
        q = st.get("first_comment")
        if not q: continue
        ok = True
        try:
            if st.get("yt"): ok &= youtube.comment(st["yt"], q)
            if st.get("fb"): ok &= facebook.comment(st["fb"], q)
        except Exception as e: print("comment error", e); ok = False
        if ok: st["comment_done"] = True

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--episode", type=int); ap.add_argument("--dry", action="store_true"); ap.add_argument("--now", action="store_true", help="publish ~15 min after upload instead of the next fixed slot"); ap.add_argument("--offline", action="store_true", help="no network: estimated timing, procedural visuals (local testing)"); a = ap.parse_args()
    state = load_state(); cases = json.load(open("data/cases.json"))
    if not a.dry:
        try: post_pending_comments(state); save_state(state)
        except Exception as e: print("pending comments skipped:", e)
    n, path, script = pick_episode(cases, state, a.episode)
    if not n: print("nothing to publish"); return 0
    print(f"=== episode {n}: {script['title']} ===")
    work = f"work/{n:03d}"; os.makedirs(work, exist_ok=True); out = f"out/{n:03d}.mp4"
    st = state["episodes"].setdefault(str(n), {})

    if a.offline:
        timing = render.estimate_timing(script); assets, credits = {}, []
        for f in ("timing.json", "assets.json"):
            if os.path.exists(f"{work}/{f}"): os.remove(f"{work}/{f}")
    else:
        print("stage: voice (eleven_v4_turbo)", flush=True); t0 = time.time()
        timing = tts.synth_script(script, work)                              # eleven_v4_turbo only
        print(f"stage: voice done in {time.time()-t0:.0f}s; fetching visuals", flush=True); t0 = time.time()
        assets, credits = media.fetch_all(script, work)
        print(f"stage: visuals done in {time.time()-t0:.0f}s ({len(assets)} assets); rendering", flush=True)
    render.render(path, work, out)
    print("stage: render done", flush=True)
    tl = json.load(open(f"{work}/timeline.json")); scenes, total = render.build_plan(script, timing)
    th = script["seo"]["thumb"]; photo = next((v["path"] for v in assets.values() if v["kind"] == "image"), None)
    cat = script["category"]; thumbnail.make({"line1": th["line1"], "line2": th["line2"], "tag": th["tag"], "year": script["year"], "episode": n, "category": cat, "photo": photo}, f"{work}/thumb.jpg")
    snippet = seo.youtube_snippet(script, tl, credits); srt_text = seo.srt(scenes, render.chunk_words)
    open(f"{work}/captions.srt", "w").write(srt_text); json.dump(snippet, open(f"{work}/youtube.json", "w"), indent=1)
    print(f"built {out}  {os.path.getsize(out)/1e6:.0f} MB  {total/60:.1f} min  title: {snippet['title']}")
    if a.dry: return 0

    slot = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=15)).replace(second=0, microsecond=0) if a.now else next_slot(state); st.update({"publish_at": slot.isoformat(), "first_comment": script["seo"]["first_comment"], "title": snippet["title"]})
    if not a.now: state["slots_used"].append(slot.isoformat())
    save_state(state)
    err = []
    if not st.get("yt"):
        try:
            import youtube
            vid = youtube.upload_video(out, snippet, slot.strftime("%Y-%m-%dT%H:%M:%S.000Z")); st["yt"] = vid; save_state(state)
            for step, fn in (("thumbnail", lambda: youtube.set_thumbnail(vid, f"{work}/thumb.jpg")), ("captions", lambda: youtube.upload_captions(vid, srt_text)),
                             ("playlist", lambda: [youtube.add_to_playlist(youtube.ensure_playlist(t, d, state), vid) for t, d in (
                                 ("Breach Uncovered — All Case Files", "Every real hack, breach and cyber-heist we have uncovered, in order."),
                                 (f"Breach Uncovered — {cat.title()} Cases", f"True stories of real {cat} cyber incidents."))])):
                try: fn()
                except Exception as e: print(f"YT {step} warning: {e}")
            print("YouTube OK", vid)
        except Exception as e: traceback.print_exc(); err.append(f"youtube: {e}")
    if not st.get("fb"):
        try:
            import facebook
            tg = {"geo_locations": {"countries": ["US", "GB", "CA", "AU"]}}
            vid = facebook.upload_video(out, snippet["title"], seo.facebook_description(script), f"{work}/thumb.jpg", slot.timestamp(), tg); st["fb"] = vid; save_state(state)
            try: facebook.upload_captions(vid, srt_text)
            except Exception as e: print("FB captions warning:", e)
            print("Facebook OK", vid)
        except Exception as e: traceback.print_exc(); err.append(f"facebook: {e}")
    save_state(state)
    if err: print("FAILED:", err); return 1
    print(f"episode {n} scheduled for {slot.isoformat()}"); return 0

if __name__ == "__main__": sys.exit(main())
