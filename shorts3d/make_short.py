"""Build one fully-3D vertical Short (1080x1920) from shorts/NNN-key.json.
   voice (ElevenLabs, or estimated timing offline) -> 3D shots timed to the narration -> frames from headless WebGL -> captions + sound -> mp4.
usage: python3 shorts3d/make_short.py shorts/001-bangladesh.json out/short.mp4 [--workdir DIR] [--offline] [--seconds N]"""
import argparse, json, os, re, subprocess, sys, time, random
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools")); sys.path.insert(0, HERE)
import render as R, sfx, motion, render3d
W, H, FPS = 1080, 1920, 24
GAP, OUTRO = 0.22, 2.2
YEL = (255, 212, 0)
KIND = {"office": "email", "printer": "email", "server": "rack", "den": "terminal", "bank": "flow", "vault": "lock", "fbi": "dossier", "war": "headline", "cyber": "network", "globe": "globe"}

def kind_of(recipe):
    for k, v in KIND.items():
        if recipe.startswith(k): return v
    return "headline"

def timeline(script, timing):
    tm = {x["id"]: x for x in timing}; t = 0.0; scenes = []
    for s in script["scenes"]:
        x = tm[s["id"]]; scenes.append({"s": s, "t0": t, "dur": float(x["duration"]), "audio": x.get("audio"), "words": x.get("words", [])}); t += float(x["duration"]) + GAP
    return scenes, scenes[-1]["t0"] + scenes[-1]["dur"] + OUTRO

def plan(scenes, total):
    """-> 3D shot list for the browser + pseudo-plans for the sound planner."""
    shots, plans = [], []
    for sc in scenes:
        s = sc["s"]; pos = 0; items = []
        for v in s.get("shots", []):
            i = R.find_cue(sc["words"], v.get("at", ""), pos) if v.get("at") else None
            if i is not None: pos = i; t = float(sc["words"][i]["s"])
            else: t = None
            items.append([t, v])
        for k, it in enumerate(items):                       # interpolate missing cues
            if it[0] is None:
                lo = items[k - 1][0] if k else 0.0; hi = next((x[0] for x in items[k + 1:] if x[0] is not None), sc["dur"]); it[0] = lo + (hi - lo) / 2
        items[0][0] = 0.0; keep = []
        for t, v in items:
            if keep and t - keep[-1][0] < 1.5: continue
            keep.append([t, v])
        pl = {"shots": [], "texts": []}
        for t, v in keep:
            shots.append({**v, "t0": sc["t0"] + t, "mood": v.get("mood", s.get("mood", "calm"))}); pl["shots"].append({"type": "gfx", "kind": kind_of(v["recipe"]), "t0": t, "t1": t + 3})
        plans.append(pl)
    for i, sh in enumerate(shots): sh["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else total + 1
    shots[0]["t0"] = 0.0
    return shots, plans

# ------------------------------------------------------------------ captions (vertical)
_cap = {}
def chunks(words):
    out, cur = [], []
    for w in words:
        cur.append(w); end = re.search(r"[.!?…—:;]$", w["w"]) or (re.search(r",$", w["w"]) and len(cur) >= 2)
        if len(cur) >= 4 or (end and len(cur) >= 2) or sum(len(x["w"]) + 1 for x in cur) > 22: out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def cap_img(ch, hi):
    key = (tuple(x["w"] for x in ch), hi)
    if key in _cap: return _cap[key]
    f = motion.DISP(74); words = [x["w"] for x in ch]; sp = f.getlength(" ") + 14; lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        wl = f.getlength(w)
        if cur and cw + sp + wl > 940: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wl + (sp if len(cur) > 1 else 0)
    lines.append(cur); img = Image.new("RGBA", (1040, 100 * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img); y = 10
    for ln in lines:
        tw = sum(f.getlength(words[i]) for i in ln) + sp * (len(ln) - 1); x = (1040 - tw) / 2
        for i in ln:
            d.text((x, y), words[i], font=f, fill=(YEL if i == hi else (255, 255, 255)) + (255,), stroke_width=9, stroke_fill=(0, 0, 0, 255)); x += f.getlength(words[i]) + sp
        y += 100
    _cap[key] = img; return img

def blend(fr, img, x, y, a=1.0):
    h, w = img.height, img.width; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    t = np.asarray(img)[y0 - y:y1 - y, x0 - x:x1 - x]; al = (t[..., 3:4].astype(np.float32) / 255.0) * a
    reg = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = (reg * (1 - al) + t[..., :3] * al).astype(np.uint8)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("out"); ap.add_argument("--workdir", default="/tmp/short_work"); ap.add_argument("--offline", action="store_true"); ap.add_argument("--seconds", type=float)
    a = ap.parse_args(); script = json.load(open(a.script, encoding="utf-8")); os.makedirs(a.workdir, exist_ok=True); ep = script["episode"]
    if a.offline or not os.environ.get("ELEVENLABS_API_KEY"): timing = R.estimate_timing(script); print("timing: estimated (no voice)")
    else:
        import tts; timing = tts.synth_script(script, a.workdir); print("timing: ElevenLabs voice")
    scenes, total = timeline(script, timing); shots, plans = plan(scenes, total)
    if a.seconds: total = min(total, a.seconds)
    print(f"short: {total:.1f}s, {len(scenes)} scenes, {len(shots)} shots", flush=True)
    wav = os.path.join(a.workdir, "mix.wav"); R.build_audio(scenes, plans, total, script.get("category", "state"), ep, wav)
    # ---- frames
    srv, port = render3d.serve(); logo = R.logo(84); wm = R.wordmark(620)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2); vig = np.clip(1.1 - .5 * r ** 1.9, .3, 1)[..., None]
    grain = [np.random.default_rng(i).integers(-7, 8, (H // 2, W // 2, 1)).astype(np.int16) for i in range(4)]
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", a.out]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b, pg = render3d.open_page(p, port, W, H); pg.evaluate("s => window.loadShots(s)", shots)
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); n = int(total * FPS); t_start = time.time(); si = 0; cc = {}
        for fi in range(n):
            T = fi / FPS
            pg.evaluate(f"window.draw({T})"); jpg = pg.locator("#c").screenshot(type="jpeg", quality=92)
            fr = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            fr = (fr.astype(np.float32) * vig).astype(np.uint8)
            g = grain[fi % 4]; fr = np.clip(fr.astype(np.int16) + cv2.resize(g, (W, H), interpolation=cv2.INTER_NEAREST)[..., None], 0, 255).astype(np.uint8)
            for q, sh in enumerate(shots):                                      # cut flash + tiny punch
                if sh["t0"] <= T < sh["t0"] + .22 and q > 0:
                    k = 1 - (T - sh["t0"]) / .22; fr = np.clip(fr.astype(np.int16) + int(55 * k * k), 0, 255).astype(np.uint8); break
            while si + 1 < len(scenes) and T >= scenes[si + 1]["t0"]: si += 1
            sc = scenes[si]; lt = T - sc["t0"]
            if si not in cc: cc[si] = chunks(sc["words"])
            for ch in cc[si]:
                if ch[0]["s"] - .05 <= lt <= ch[-1]["e"] + .25:
                    hi = max([i for i, w in enumerate(ch) if w["s"] <= lt] or [0]); img = cap_img(ch, hi); blend(fr, img, (W - img.width) // 2, 1240, min(1, (lt - ch[0]["s"] + .05) / .1)); break
            if T < 8: blend(fr, logo, 40, 56, .92)
            end0 = total - OUTRO
            if T > end0:
                k = min(1, (T - end0) / .5); fr = (fr.astype(np.float32) * (1 - .88 * k)).astype(np.uint8); blend(fr, wm, (W - wm.width) // 2, 760, k)
                tg = Image.new("RGBA", (900, 160), (0, 0, 0, 0)); d = ImageDraw.Draw(tg); d.text((450, 40), "TRUE STORIES OF REAL HACKS", font=motion.BOLD(44), fill=YEL + (255,), anchor="mm"); d.text((450, 110), "FOLLOW FOR THE NEXT STORY", font=motion.BOLD(34), fill=(255, 255, 255, 220), anchor="mm"); blend(fr, tg, 90, 1000, k)
            ff.stdin.write(np.ascontiguousarray(fr).tobytes())
            if fi % 48 == 0: print(f"  frame {fi}/{n} ({time.time() - t_start:.0f}s)", flush=True)
        ff.stdin.close(); ff.wait(); b.close(); print(f"rendered {a.out} {os.path.getsize(a.out) / 1e6:.1f} MB in {time.time() - t_start:.0f}s")

if __name__ == "__main__": main()
