#!/usr/bin/env python3
"""Breach Uncovered video renderer: script JSON + timing + visual assets -> 1080p MP4 with sound design.

  python3 tools/render.py --script scripts/001-sony.json --workdir work/001 --out out/001.mp4
Inputs in workdir (all optional — missing pieces fall back gracefully so the pipeline never stalls):
  timing.json : [{"id":1,"audio":"voice/01.mp3","duration":12.3,"words":[{"w":"Hello","s":0.1,"e":0.4}, ...]}, ...]
  assets.json : {"1:0": {"path": "...", "kind": "video|image", "credit": "..."}, ...}   key = "<scene id>:<visual index>"
"""
import argparse, json, math, os, random, re, subprocess, sys, time
import numpy as np, cv2
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import motion, sfx
from thumbnail import ACCENT

W, H, FPS = 1920, 1080, 24
YEL = (255, 212, 0)
GAP, ACT_GAP, OUTRO = 0.40, 0.65, 3.0
BRAND = os.path.join(HERE, "..", "assets", "brand")
_LOGO = {}
def _load(name, key, w=None, h=None):
    k = (name, w, h)
    if k not in _LOGO:
        im = Image.open(os.path.join(BRAND, name)).convert("RGBA")
        if w: h = round(im.height * w / im.width)
        else: w = round(im.width * h / im.height)
        _LOGO[k] = im.resize((w, h), Image.LANCZOS)
    return _LOGO[k]
def logo(height): return _load("logo_mark.png", "m", h=height)        # B keyhole mark (transparent background)
def wordmark(width): return _load("logo_wordmark.png", "w", w=width)   # mark + BREACH UNCOVERED (transparent background)

# ------------------------------------------------------------------------------------------ timing
def words_of(narr): return re.sub(r"\[[^\]]*\]", " ", narr).split()

def estimate_timing(script):
    out = []
    for s in script["scenes"]:
        w = words_of(s["narration"]); pauses = sum({"short pause": .35, "pause": .7, "long pause": 1.3}.get(t.lower(), 0) for t in re.findall(r"\[([^\]]*)\]", s["narration"]))
        dur = max(3.0, len(w) * 0.385 + pauses); per = (dur - pauses) / max(1, len(w)); t = 0.0; ws = []
        for x in w:
            ws.append({"w": x, "s": t, "e": t + per * .92}); t += per
        out.append({"id": s["id"], "audio": None, "duration": dur, "words": ws})
    return out

def build_plan(script, timing):
    tm = {x["id"]: x for x in timing}; t = 0.0; scenes = []
    prev_act = None
    for s in script["scenes"]:
        x = tm[s["id"]]; dur = float(x["duration"])
        scenes.append({"s": s, "t0": t, "dur": dur, "audio": x.get("audio"), "words": x.get("words", [])})
        t += dur + (ACT_GAP if s.get("act") != prev_act else GAP); prev_act = s.get("act")
    total = scenes[-1]["t0"] + scenes[-1]["dur"] + OUTRO
    return scenes, total

# ------------------------------------------------------------------------------------------ backgrounds
def cover(img, w=W, h=H):
    ih, iw = img.shape[:2]; sc = max(w / iw, h / ih)
    r = cv2.resize(img, (int(iw * sc + .5), int(ih * sc + .5)), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    y0, x0 = (r.shape[0] - h) // 2, (r.shape[1] - w) // 2
    return r[y0:y0 + h, x0:x0 + w]

class ProcBG:
    def __init__(self, seed, acc):
        r = np.random.default_rng(seed); yy = np.linspace(0, 1, H)[:, None]
        base = np.zeros((H, W, 3), np.float32)
        for c in range(3): base[..., c] = (10 + (acc[c] * .10) * (1 - yy)) + 6 * (c == 2)
        cx = np.linspace(-1, 1, W)[None, :]; base *= (1 + .5 * np.exp(-(cx ** 2) * 2.2))[..., None]
        self.base = base.clip(0, 255).astype(np.uint8)
        rain = Image.new("RGB", (W, H * 2), (0, 0, 0)); d = ImageDraw.Draw(rain); f = motion.MONO(22)
        for x in range(10, W, 34):
            y = int(r.integers(0, H * 2)); L = int(r.integers(6, 26))
            for k in range(L):
                d.text((x, (y + k * 26) % (H * 2)), "0123456789ABCDEF"[int(r.integers(0, 16))], font=f, fill=tuple(int(c * (.15 + .65 * (1 - k / L))) for c in acc))
        self.rain = np.asarray(rain); self.r2 = np.roll(self.rain, 700, axis=0)
    def frame(self, t, dur):
        o = int(t * 55) % H; o2 = int(t * 28) % H
        f = cv2.add(self.base, self.rain[o:o + H]); f = cv2.add(f, (self.r2[o2:o2 + H] * .45).astype(np.uint8))
        return f

class ImgBG:
    def __init__(self, path, seed):
        im = cv2.imread(path, cv2.IMREAD_COLOR)
        if im is None: raise ValueError("bad image")
        im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB); self.img = cover(im, int(W * 1.25), int(H * 1.25))
        r = random.Random(seed); self.z1 = r.choice([1.0, 1.12]); self.z2 = 2.12 - self.z1 if self.z1 == 1.0 else 1.0
        self.z2 = 1.14 if self.z1 == 1.0 else 1.0; self.dx = r.uniform(-.06, .06); self.dy = r.uniform(-.04, .04)
    def frame(self, t, dur):
        k = min(1, t / max(dur, 1)); z = self.z1 + (self.z2 - self.z1) * k
        ih, iw = self.img.shape[:2]; cw, ch = int(iw / z / 1.0 * (W / (iw)) * 1.0 * (iw / W)), 0
        cw = int(iw / z); ch = int(cw * H / W)
        if ch > ih: ch = ih; cw = int(ch * W / H)
        cx = iw / 2 + self.dx * iw * (k - .5) * 2; cy = ih / 2 + self.dy * ih * (k - .5) * 2
        x0 = int(min(max(cx - cw / 2, 0), iw - cw)); y0 = int(min(max(cy - ch / 2, 0), ih - ch))
        return cv2.resize(self.img[y0:y0 + ch, x0:x0 + cw], (W, H), interpolation=cv2.INTER_LINEAR)

class VidBG:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened(): raise ValueError("bad video")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25; self.idx = -1; self.last = None
    def frame(self, t, dur):
        want = int(t * self.fps)
        while self.idx < want:
            ok, f = self.cap.read()
            if not ok:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); self.idx = -1; want = 0
                ok, f = self.cap.read()
                if not ok: break
            self.idx += 1; self.last = f
            if self.idx >= want: break
        if self.last is None: return None
        return cover(cv2.cvtColor(self.last, cv2.COLOR_BGR2RGB))

def make_bg(asset, seed):
    try:
        if asset and asset.get("path") and os.path.exists(asset["path"]):
            return VidBG(asset["path"]) if asset["kind"] == "video" else ImgBG(asset["path"], seed)
    except Exception as e: print("asset failed:", e)
    return None

# ------------------------------------------------------------------------------------------ look
class Look:
    def __init__(self, acc):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        v = np.clip(1.12 - .55 * r ** 1.8, .22, 1.0); self.vig = np.repeat((v * 255).astype(np.uint8)[..., None], 3, 2)
        rg = np.random.default_rng(3); self.grain = [cv2.merge([g, g, g]) for g in (cv2.resize(rg.integers(0, 12, (H // 3, W // 3), dtype=np.uint8), (W, H), interpolation=cv2.INTER_LINEAR) for _ in range(6))]
        self.acc = acc; scan = np.ones((H, 1), np.uint8) * 255; scan[::4] = 244; self.scan = np.repeat(scan[:, None, :].repeat(W, 1), 3, 2)
        self.tint = np.array([acc[0] * .10, acc[1] * .10, acc[2] * .10], np.float32)
    def grade(self, f, fi):
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY); g3 = cv2.merge([g, g, g])
        f = cv2.addWeighted(f, .62, g3, .38, 0); f = cv2.convertScaleAbs(f, alpha=.80, beta=-6)
        f = cv2.add(f, np.uint8(self.tint)); f = cv2.multiply(f, self.vig, scale=1 / 255.)
        f = cv2.multiply(f, self.scan, scale=1 / 255.); f = cv2.subtract(cv2.add(f, self.grain[fi % 6]), 4)
        return f

def blend(frame, img, x, y, alpha=1.0):
    a = np.asarray(img); h, w = a.shape[:2]
    x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0 or alpha <= 0: return
    a = a[y0 - y:y1 - y, x0 - x:x1 - x]; al = (a[..., 3:4].astype(np.float32) / 255.0) * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32); frame[y0:y1, x0:x1] = (reg * (1 - al) + a[..., :3].astype(np.float32) * al).astype(np.uint8)

# ------------------------------------------------------------------------------------------ captions
_capcache = {}
def chunk_words(words):
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        end = re.search(r"[.!?…—:;]$", w["w"]) or (re.search(r",$", w["w"]) and len(cur) >= 3)
        if len(cur) >= 7 or (end and len(cur) >= 3) or sum(len(x["w"]) + 1 for x in cur) > 44: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def caption_img(chunk, hi):
    key = (tuple(x["w"] for x in chunk), hi)
    if key in _capcache: return _capcache[key]
    f = motion.DISP(60); words = [x["w"] for x in chunk]; sp = f.getlength(" ") + 12
    lines, cur, cw = [], [], 0
    for i, w in enumerate(words):
        wl = f.getlength(w)
        if cur and cw + sp + wl > 1500: lines.append(cur); cur, cw = [], 0
        cur.append(i); cw += wl + (sp if len(cur) > 1 else 0)
    lines.append(cur)
    img = Image.new("RGBA", (1700, 150 * len(lines) // 2 + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(img); y = 10
    for ln in lines:
        tw = sum(f.getlength(words[i]) for i in ln) + sp * (len(ln) - 1); x = (1700 - tw) / 2
        for i in ln:
            col = YEL if i == hi else (255, 255, 255)
            d.text((x, y), words[i], font=f, fill=col + (255,), stroke_width=7, stroke_fill=(0, 0, 0, 255)); x += f.getlength(words[i]) + sp
        y += 78
    _capcache[key] = img; return img

# ------------------------------------------------------------------------------------------ sound plan
STRONG = {"escalation", "scramble", "unmasking", "cold_open"}
def plan_sfx(scenes, total):
    ev = []; last_big = -9
    for i, sc in enumerate(scenes):
        t0, act = sc["t0"], sc["s"].get("act", "")
        if i == 0:
            ev += [{"t": 0.0, "sfx": "boom", "gain": .95}, {"t": 0.05, "sfx": "static", "gain": .25}]
        else:
            ev.append({"t": max(0, t0 - .45), "sfx": "whoosh_up", "gain": .42, "pan": random.Random(i).uniform(-.5, .5)})
            ev.append({"t": t0, "sfx": "impact" if act in STRONG else "boom", "gain": .8 if act in STRONG else .45})
            last_big = t0
        if act in ("escalation", "scramble") and i and scenes[i - 1]["s"].get("act") != act:
            ev.append({"t": t0 + .2, "sfx": "alarm", "gain": .22, "dur": 1.5})
        for k, vis in enumerate([v for v in sc["s"].get("visuals", []) if v["type"] == "motion"]):
            ts = t0 + overlay_window(sc, k, len([1 for v in sc["s"]["visuals"] if v["type"] == "motion"]))[0]; kd = vis.get("kind")
            m = {"counter": [("chirps", .5, 1.6)], "terminal": [("typing", .6, 2.4)], "headline": [("glitch", .6, None), ("static", .25, None)],
                 "redact": [("impact", .85, None)], "network": [("chirps", .4, 2.6)], "map": [("whoosh_down", .5, None)],
                 "doc_callout": [("whoosh_up", .4, None)], "timeline": [("whoosh_up", .35, None)], "quote": [("boom", .35, None)], "title": [("whoosh_down", .35, None)]}.get(kd, [])
            for name, g, du in m:
                e = {"t": ts + (1.4 if kd == "redact" else 0), "sfx": name, "gain": g}
                if du: e["dur"] = du
                ev.append(e)
    ev.append({"t": max(0, total - 3.0), "sfx": "reverse", "gain": .5}); ev.append({"t": max(0, total - 2.6), "sfx": "impact", "gain": .6})
    return ev

def overlay_window(sc, k, n):
    """(start, length) of k-th motion overlay inside scene (relative seconds)."""
    dur = sc["dur"]; span = max(2.5, dur - 1.0)
    start = 0.6 + k * span / max(1, n); length = min(6.5, max(2.5, span / max(1, n) + (0.5 if k == n - 1 else 0)))
    return start, min(length, dur - start + 0.3)

def load_audio(path, total):
    out = np.zeros(int(sfx.SR * total) + sfx.SR, np.float32)
    return out

def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sfx.SR), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32)

def build_audio(scenes, total, cat, seed, out_wav):
    N = int(sfx.SR * total) + sfx.SR; voice = np.zeros(N, np.float32)
    for sc in scenes:
        if sc["audio"] and os.path.exists(sc["audio"]):
            a = decode(sc["audio"]); i0 = int(sc["t0"] * sfx.SR); L = min(len(a), N - i0); voice[i0:i0 + L] += a[:L]
    base = {"infra": 49, "state": 55, "espionage": 52, "finance": 58, "ransomware": 46, "breach": 55, "profile": 58, "malware": 52}.get(cat, 55)
    music = sfx.drone(total + 2, base, seed); ev = plan_sfx(scenes, total)
    fx = sfx.mix_track(total, ev, None); env = np.abs(voice)
    k = int(sfx.SR * .18); env = np.convolve(env, np.ones(k) / k, "same"); env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-6) if (env > 0).any() else env, 0, 1)
    env = np.convolve(env, np.ones(int(sfx.SR * .12)) / int(sfx.SR * .12), "same")
    m = music[:N] if len(music) >= N else np.pad(music, (0, N - len(music)))
    mix = np.zeros((2, N), np.float32)
    for ch in (0, 1):
        mix[ch] = voice * 1.0 + m * 0.20 * (1 - .62 * env) + fx[ch][:N] * (1 - .30 * env)
    mix /= max(1.0, np.abs(mix).max() / 0.97); sfx.write_wav(out_wav, mix)

# ------------------------------------------------------------------------------------------ main render
def render(script_path, workdir, out, max_seconds=None, seed=1):
    script = json.load(open(script_path, encoding="utf-8")); os.makedirs(workdir, exist_ok=True)
    tp = os.path.join(workdir, "timing.json"); ap = os.path.join(workdir, "assets.json")
    timing = json.load(open(tp)) if os.path.exists(tp) else estimate_timing(script)
    assets = json.load(open(ap)) if os.path.exists(ap) else {}
    scenes, total = build_plan(script, timing)
    cat = script.get("category", "state"); acc = ACCENT.get(cat, ACCENT["state"]); ep = script["episode"]
    if max_seconds: total = min(total, max_seconds)
    wav = os.path.join(workdir, "mix.wav"); build_audio(scenes, total, cat, ep * 31 + 1, wav)
    json.dump({"total": total, "scenes": [{"id": s["s"]["id"], "label": s["s"]["label"], "t0": s["t0"], "dur": s["dur"]} for s in scenes]}, open(os.path.join(workdir, "timeline.json"), "w"), indent=1)

    look = Look(acc); proc = ProcBG(ep, acc)
    # per-scene background providers (lazy)
    sbg = {}
    def bgs_for(i):
        if i in sbg: return sbg[i]
        sc = scenes[i]; lst = []
        for vi, v in enumerate(sc["s"].get("visuals", [])):
            if v["type"] in ("stock", "archival"):
                b = make_bg(assets.get(f"{sc['s']['id']}:{vi}"), ep * 100 + i * 7 + vi)
                if b: lst.append(b)
        sbg[i] = lst; return lst
    hud = Image.new("RGBA", (520, 70), (0, 0, 0, 0)); hd = ImageDraw.Draw(hud)
    hd.text((86, 35), f"CASE #{ep:03d}  ·  {script['year']}", font=motion.BOLD(28), fill=(255, 255, 255, 215), anchor="lm")
    hud.alpha_composite(logo(64), (6, 3))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(total * FPS); si = 0; t_start = time.time(); chunks_cache = {}
    for fi in range(nfr):
        T = fi / FPS
        while si + 1 < len(scenes) and T >= scenes[si + 1]["t0"] - (0 if True else 0): si += 1
        sc = scenes[si]; lt = T - sc["t0"]; in_scene = lt < sc["dur"] + (ACT_GAP if si + 1 < len(scenes) else OUTRO)
        sdur = sc["dur"] + GAP
        # background (cross-fading list of stock/archival, or procedural)
        bl = bgs_for(si)
        if bl:
            seg = sdur / len(bl); bi = min(len(bl) - 1, int(max(lt, 0) / seg)); fr = bl[bi].frame(max(lt, 0) - bi * seg, seg)
            if fr is None: fr = proc.frame(T, 0)
            elif bi + 1 < len(bl) and (bi + 1) * seg - lt < .4:
                nx = bl[bi + 1].frame(0, seg)
                if nx is not None: a = 1 - ((bi + 1) * seg - lt) / .4; fr = cv2.addWeighted(fr, 1 - a, nx, a, 0)
        else: fr = proc.frame(T, 0)
        fr = look.grade(np.ascontiguousarray(fr), fi)
        # motion overlays
        motions = [v for v in sc["s"].get("visuals", []) if v["type"] == "motion"]
        for k, v in enumerate(motions):
            st, ln = overlay_window(sc, k, len(motions))
            if st <= lt < st + ln:
                lt2 = lt - st; res = motion.draw(v.get("kind", ""), v, lt2, ln, acc)
                if res:
                    img, (x, y) = res; al = min(1, lt2 / .22) * min(1, (ln - lt2) / .3); blend(fr, img, int(x), int(y), al)
        # plain overlay text on stock visuals
        for vi, v in enumerate(sc["s"].get("visuals", [])):
            if v.get("overlay") and v["type"] != "motion" and .5 <= lt < min(sc["dur"], 5.5):
                img, (x, y) = motion.title({"text": v["overlay"]}, lt - .5, 5, acc); blend(fr, img, int(x), int(y), min(1, (lt - .5) / .2) * min(1, (5.0 - (lt - .5)) / .3))
        # transition punch + shake
        tp_ = lt if lt >= 0 else 9
        if si > 0 and 0 <= lt < .32:
            p = lt / .32; off = int((1 - p) ** 2 * 26)
            if off: fr[..., 0] = np.roll(fr[..., 0], off, 1); fr[..., 2] = np.roll(fr[..., 2], -off, 1)
            if lt < .09: fr = np.clip(fr.astype(np.int16) + int(70 * (1 - lt / .09)), 0, 255).astype(np.uint8)
        strong = sc["s"].get("act") in STRONG or si == 0
        if strong and 0 <= lt < .45:
            amp = 16 * (1 - lt / .45) ** 2; M = np.float32([[1, 0, random.uniform(-amp, amp)], [0, 1, random.uniform(-amp, amp)]])
            fr = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        # captions
        key = si
        if key not in chunks_cache: chunks_cache[key] = chunk_words(sc["words"])
        for ch in chunks_cache[key]:
            if ch[0]["s"] - .05 <= lt <= ch[-1]["e"] + .25:
                hi = max([i for i, w in enumerate(ch) if w["s"] <= lt] or [0]); img = caption_img(ch, hi)
                a = min(1, (lt - ch[0]["s"] + .05) / .12); blend(fr, img, (W - img.width) // 2, 835 + (0 if len(ch) < 6 else 0), a)
                break
        # logo sting right after the cold open (scene 2): channel identity, once per video
        if si == 1 and .15 <= lt < 2.2:
            q = lt - .15; a = min(1, q / .3) * min(1, (2.05 - q) / .4); sz = int(300 + 40 * min(1, q / 2.0))
            wm = wordmark(int(820 + 60 * min(1, q / 2.0)))
            blend(fr, wm, (W - wm.width) // 2, (H - wm.height) // 2 - 40, a * .98)
        # hud, progress, fades
        blend(fr, hud, 28, 22, .9)
        cv2.rectangle(fr, (0, H - 6), (int(W * T / total), H), acc, -1)
        if T < .35: fr = cv2.multiply(fr, np.uint8(255 * (T / .35)), scale=1 / 255.) if False else (fr * (T / .35)).astype(np.uint8)
        if T > total - OUTRO + .3:
            k = min(1, (T - (total - OUTRO + .3)) / 1.0); fr = (fr * (1 - k)).astype(np.uint8)
            if k > .5:
                wm = wordmark(1180); end = Image.new("RGBA", (1400, wm.height + 170), (0, 0, 0, 0)); ed = ImageDraw.Draw(end)
                end.alpha_composite(wm, ((1400 - wm.width) // 2, 0))
                ed.text((700, wm.height + 40), "TRUE STORIES OF REAL HACKS", font=motion.BOLD(40), fill=YEL + (255,), anchor="mm")
                ed.text((700, wm.height + 110), "SUBSCRIBE FOR THE NEXT CASE FILE", font=motion.BOLD(30), fill=(255, 255, 255, 200), anchor="mm")
                blend(fr, end, (W - 1400) // 2, (H - end.height) // 2, (k - .5) * 2)
        pipe.stdin.write(np.ascontiguousarray(fr).tobytes())
        if fi % 240 == 0: print(f"  frame {fi}/{nfr}  ({time.time() - t_start:.0f}s)", flush=True)
    pipe.stdin.close(); pipe.wait()
    print("rendered", out, f"{os.path.getsize(out) / 1e6:.1f} MB in {time.time() - t_start:.0f}s")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--script", required=True); ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--max-seconds", type=float)
    a = ap.parse_args(); render(a.script, a.workdir, a.out, a.max_seconds)
