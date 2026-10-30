"""Build one vertical Short (1080x1920, 30 fps) from shorts/NNN-key.json with the 2D / semi-3D canvas engine.
voice (ElevenLabs; or estimated timing with --offline) -> visuals timed to the words -> frames from headless Chromium canvas -> captions + music + sfx -> mp4.
usage: python3 shorts2d/make_short2d.py shorts/003-bangladesh.json out/short.mp4 [--workdir DIR] [--offline] [--seconds N] [--stills 1 5 9]"""
import argparse, json, os, re, subprocess, sys, time, threading, functools, http.server, socketserver
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import render as R, sfx, motion
W, H, FPS = 1080, 1920, 30
GAP, OUTRO = 0.12, 1.5
YEL = (255, 212, 0)
SFXK = {"building": "globe", "office": "email", "hacker": "terminal", "servers": "rack", "people": "headline", "phone": "email", "email": "email", "object": "counter",
        "network": "network", "globe": "globe", "flow": "flow", "counter": "counter", "timeline": "timeline", "lock": "lock", "terminal": "terminal", "dossier": "dossier",
        "headline": "headline", "stamp": "redact", "split": "quote"}

def serve():
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Q, directory=ROOT)); srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start(); return srv.server_address[1]

def open_page(p, port):
    b = p.chromium.launch(args=["--disable-gpu-vsync", "--disable-web-security"])
    pg = b.new_page(viewport={"width": W, "height": H}); pg.on("console", lambda m: print("[browser]", m.text[:400]) if "ERR" in m.text else None)
    pg.goto(f"http://127.0.0.1:{port}/shorts2d/player.html"); pg.wait_for_function("window.ready===true || window.err", timeout=60000)
    if pg.evaluate("window.err || ''"): raise SystemExit("player error: " + pg.evaluate("window.err"))
    return b, pg

def timeline(script, timing):
    tm = {x["id"]: x for x in timing}; t = 0.0; scenes = []
    for s in script["scenes"]:
        x = tm[s["id"]]; scenes.append({"s": s, "t0": t, "dur": float(x["duration"]), "audio": x.get("audio"), "words": x.get("words", [])}); t += float(x["duration"]) + GAP
    return scenes, scenes[-1]["t0"] + scenes[-1]["dur"] + OUTRO

def plan(scenes, total):
    shots, plans = [], []
    for sc in scenes:
        s = sc["s"]; pos = 0; items = []
        for v in s.get("visuals", []):
            i = R.find_cue(sc["words"], v.get("at", ""), pos) if v.get("at") else None
            if i is not None: pos = i
            items.append([float(sc["words"][i]["s"]) if i is not None else None, v])
        for k, it in enumerate(items):
            if it[0] is None:
                lo = items[k - 1][0] if k else 0.0; hi = next((x[0] for x in items[k + 1:] if x[0] is not None), sc["dur"]); it[0] = (lo + hi) / 2
        if items: items[0][0] = 0.0
        keep = []
        for t, v in items:
            if keep and t - keep[-1][0] < 1.2: continue
            keep.append([t, v])
        pl = {"shots": [], "texts": []}
        for t, v in keep:
            shots.append({**v, "t0": round(sc["t0"] + t, 3), "mood": s.get("mood", "calm")}); pl["shots"].append({"type": "gfx", "kind": SFXK.get(v.get("kind"), "headline"), "t0": t})
        plans.append(pl)
    for i, sh in enumerate(shots): sh["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else total + 1
    if shots: shots[0]["t0"] = 0.0
    return shots, plans

_cap = {}
def chunks(words):
    out, cur = [], []
    for w in words:
        cur.append(w); end = re.search(r"[.!?…—:;]$", w["w"]) or (re.search(r",$", w["w"]) and len(cur) >= 2)
        if len(cur) >= 3 or (end and len(cur) >= 1) or sum(len(x["w"]) + 1 for x in cur) > 18: out.append(cur); cur = []
    if cur: out.append(cur)
    return out
def cap_img(ch, hi):
    key = (tuple(x["w"] for x in ch), hi)
    if key in _cap: return _cap[key]
    f = motion.DISP(84); words = [x["w"] for x in ch]; sp = f.getlength(" ") + 16; lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        wl = f.getlength(w)
        if cur and cw + sp + wl > 960: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wl + (sp if len(cur) > 1 else 0)
    lines.append(cur); img = Image.new("RGBA", (1060, 112 * len(lines) + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img); y = 12
    for ln in lines:
        tw = sum(f.getlength(words[i]) for i in ln) + sp * (len(ln) - 1); x = (1060 - tw) / 2
        for i in ln:
            d.text((x, y), words[i], font=f, fill=(YEL if i == hi else (255, 255, 255)) + (255,), stroke_width=10, stroke_fill=(0, 0, 0, 255)); x += f.getlength(words[i]) + sp
        y += 112
    _cap[key] = img; return img
def blend(fr, img, x, y, a=1.0):
    h, w = img.height, img.width; x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0: return
    t = np.asarray(img)[y0 - y:y1 - y, x0 - x:x1 - x]; al = (t[..., 3:4].astype(np.float32) / 255.0) * a
    reg = fr[y0:y1, x0:x1].astype(np.float32); fr[y0:y1, x0:x1] = (reg * (1 - al) + t[..., :3] * al).astype(np.uint8)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("out"); ap.add_argument("--workdir", default="/tmp/short2d_work"); ap.add_argument("--offline", action="store_true")
    ap.add_argument("--seconds", type=float); ap.add_argument("--stills", type=float, nargs="*")
    a = ap.parse_args(); script = json.load(open(a.script, encoding="utf-8")); os.makedirs(a.workdir, exist_ok=True); ep = script["episode"]
    if a.offline or not os.environ.get("ELEVENLABS_API_KEY"):
        timing = R.estimate_timing(script)
        for x in timing:                                   # estimate tuned to the narrator's real pace (~2.45 words/s)
            for w in x["words"]: w["s"] *= .98; w["e"] *= .98
            x["duration"] *= .98
        print("timing: estimated (no voice)")
    else:
        import tts; timing = tts.synth_script(script, a.workdir); print("timing: ElevenLabs voice")
    scenes, total = timeline(script, timing); shots, plans = plan(scenes, total)
    json.dump({"total": total, "shots": shots}, open(os.path.join(a.workdir, "shots.json"), "w"), indent=1)
    if a.seconds: total = min(total, a.seconds)
    print(f"short: {total:.1f}s, {len(scenes)} scenes, {len(shots)} visuals", flush=True)
    port = serve()
    from playwright.sync_api import sync_playwright
    if a.stills:
        with sync_playwright() as p:
            b, pg = open_page(p, port); pg.evaluate("s => window.loadShots(s)", shots)
            for t in a.stills: pg.evaluate(f"window.draw({t})"); pg.locator("#c").screenshot(path=f"{a.out}_{t:.1f}.png"); print("still", t)
            b.close()
        return
    wav = os.path.join(a.workdir, "mix.wav"); R.build_audio(scenes, plans, total, script.get("category", "state"), ep, wav)
    logo = R.logo(92); wm = R.wordmark(660)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rr = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2); vig = np.clip(1.12 - .45 * rr ** 2, .35, 1)[..., None]
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-maxrate", "8M", "-bufsize", "16M", "-g", "60", "-keyint_min", "60", "-sc_threshold", "0", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", "-t", f"{total:.3f}", a.out]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with sync_playwright() as p:
        b, pg = open_page(p, port); pg.evaluate("s => window.loadShots(s)", shots)
        ff = subprocess.Popen(cmd, stdin=subprocess.PIPE); n = int(total * FPS); t_start = time.time(); si = 0; cc = {}
        for fi in range(n):
            T = fi / FPS; pg.evaluate(f"window.draw({T})"); jpg = pg.locator("#c").screenshot(type="jpeg", quality=93)
            fr = cv2.cvtColor(cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB); fr = (fr.astype(np.float32) * vig).astype(np.uint8)
            for q, sh in enumerate(shots):
                if q and sh["t0"] <= T < sh["t0"] + .12: k = 1 - (T - sh["t0"]) / .12; fr = np.clip(fr.astype(np.int16) + int(60 * k), 0, 255).astype(np.uint8); break
            while si + 1 < len(scenes) and T >= scenes[si + 1]["t0"]: si += 1
            sc = scenes[si]; lt = T - sc["t0"]
            if si not in cc: cc[si] = chunks(sc["words"])
            for ch in cc[si]:
                if ch[0]["s"] - .04 <= lt <= ch[-1]["e"] + .2:
                    hi = max([i for i, w in enumerate(ch) if w["s"] <= lt] or [0]); img = cap_img(ch, hi); blend(fr, img, (W - img.width) // 2, 1290, min(1, (lt - ch[0]["s"] + .04) / .08)); break
            blend(fr, logo, 44, 70, .95)
            end0 = total - OUTRO
            if T > end0:
                k = min(1, (T - end0) / .4); fr = (fr.astype(np.float32) * (1 - .9 * k)).astype(np.uint8); blend(fr, wm, (W - wm.width) // 2, 760, k)
                tg = Image.new("RGBA", (980, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(tg); d.text((490, 44), "TRUE STORIES OF REAL HACKS", font=motion.BOLD(48), fill=YEL + (255,), anchor="mm"); d.text((490, 118), "FOLLOW FOR THE NEXT STORY", font=motion.BOLD(38), fill=(255, 255, 255, 230), anchor="mm"); blend(fr, tg, 50, 1010, k)
            ff.stdin.write(np.ascontiguousarray(fr).tobytes())
            if fi % 60 == 0: print(f"  frame {fi}/{n} ({time.time() - t_start:.0f}s)", flush=True)
        ff.stdin.close(); ff.wait(); b.close(); print(f"rendered {a.out} {os.path.getsize(a.out) / 1e6:.1f} MB, {total:.1f}s in {time.time() - t_start:.0f}s")

if __name__ == "__main__": main()
