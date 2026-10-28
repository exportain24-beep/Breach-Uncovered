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
    """Stock clip as background. Reads sequentially and loops by seeking back (never re-decodes the clip per frame)."""
    def __init__(self, path, start_frac=0.0):
        self.cap = cv2.VideoCapture(path)
        if not self.cap.isOpened(): raise ValueError("bad video")
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0); self.n = n if n > 5 else 0
        self.off = int(start_frac * max(0, self.n - 1)); self.idx = -2; self.last = None
    def frame(self, t, dur):
        want = self.off + int(max(0, t) * self.fps)
        if self.n: want %= self.n
        if self.idx == -2 or want < self.idx or want - self.idx > 90:   # first frame / loop point / big jump: seek once
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, want); self.idx = want - 1
        while self.idx < want:
            ok, f = self.cap.read()
            if not ok:
                if self.last is not None: break                      # clip ended early: hold last frame
                return None
            self.idx += 1; self.last = f
        if self.last is None: return None
        return cover(cv2.cvtColor(self.last, cv2.COLOR_BGR2RGB))
    def release(self): self.cap.release()

def make_bg(asset, seed):
    try:
        if asset and asset.get("path") and os.path.exists(asset["path"]):
            return VidBG(asset["path"], random.Random(seed).random() * .6) if asset["kind"] == "video" else ImgBG(asset["path"], seed)
    except Exception as e: print("asset failed:", e)
    return None

# ------------------------------------------------------------------------------------------ look
class Look:
    def __init__(self, acc):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        v = np.clip(1.12 - .55 * r ** 1.8, .22, 1.0); self.vig = np.repeat((v * 255).astype(np.uint8)[..., None], 3, 2)
        rg = np.random.default_rng(3); self.grain = [cv2.merge([g, g, g]) for g in (cv2.resize(rg.integers(0, 12, (H // 3, W // 3), dtype=np.uint8), (W, H), interpolation=cv2.INTER_LINEAR) for _ in range(6))]
        self.acc = acc; scan = np.ones((H, 1), np.uint8) * 255; scan[::4] = 244; self.scan = np.repeat(scan[:, None, :].repeat(W, 1), 3, 2)
        self.tint = np.array([acc[0] * .10, acc[1] * .10, acc[2] * .10], np.float32); self.mood_tint = np.zeros(3, np.int16)
    def grade(self, f, fi):
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY); g3 = cv2.merge([g, g, g])
        f = cv2.addWeighted(f, .74, g3, .26, 0); f = cv2.convertScaleAbs(f, alpha=.88, beta=-4)
        f = np.clip(f.astype(np.int16) + self.mood_tint, 0, 255).astype(np.uint8)
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
        if len(cur) >= 5 or (end and len(cur) >= 2) or sum(len(x["w"]) + 1 for x in cur) > 34: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    return chunks

def caption_img(chunk, hi):
    key = (tuple(x["w"] for x in chunk), hi)
    if key in _capcache: return _capcache[key]
    f = motion.DISP(54); words = [x["w"] for x in chunk]; sp = f.getlength(" ") + 12
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

# ------------------------------------------------------------------------------------------ scene plan (shots + text, timed to the narration)
STRONG = {"escalation", "scramble", "unmasking", "cold_open"}
MOOD_TINT = {"calm": (-6, 2, 10), "curious": (0, 7, 9), "tense": (14, -4, -6), "shock": (8, 8, 8), "reveal": (10, 6, -6),
             "sad": (-8, -2, 6), "hopeful": (8, 10, 2)}
CARD_LEN = {"counter": 4.0, "title": 3.5, "quote": 4.5, "headline": 4.5, "redact": 4.0, "doc_callout": 5.0, "timeline": 5.0,
            "network": 5.0, "map": 4.5, "terminal": 5.0}
MIN_SHOT, TR = 2.2, 0.30

def _tok(w): return re.sub(r"[^a-z0-9']", "", w.lower().replace("’", "'"))

def find_cue(words, phrase, start):
    toks = [t for t in (_tok(x) for x in phrase.split()) if t]
    if not toks: return None
    wt = [_tok(w["w"]) for w in words]
    for i in range(start, len(wt) - len(toks) + 1):
        if wt[i:i + len(toks)] == toks: return i
    for i in range(start, len(wt)):
        if wt[i] == toks[0]: return i
    return None

def scene_plan(sc, seed):
    """-> {"shots": [{t0,t1,vi,type,tr}], "texts": [{t,len,kind,vi,text}]} with times relative to the scene start."""
    words, dur, vis = sc["words"], sc["dur"], sc["s"].get("visuals", [])
    rng = random.Random(seed); pos = 0; cues = []
    for v in vis:
        i = find_cue(words, v.get("at", ""), pos) if v.get("at") else None
        if i is not None: pos = i; cues.append(float(words[i]["s"]))
        else: cues.append(None)
    k = 0
    while k < len(cues):                                   # interpolate missing cues between known neighbours
        if cues[k] is None:
            j = k
            while j < len(cues) and cues[j] is None: j += 1
            lo = cues[k - 1] if k else 0.0; hi = cues[j] if j < len(cues) else dur
            for m in range(k, j): cues[m] = lo + (hi - lo) * (m - k + 1) / (j - k + 1)
            k = j
        else: k += 1
    for m in range(1, len(cues)): cues[m] = max(cues[m], cues[m - 1])
    shots = []
    for vi, v in enumerate(vis):
        if v["type"] not in ("stock", "archival"): continue
        t = cues[vi]
        if shots and t - shots[-1]["t0"] < (1.6 if sc["s"].get("act") == "cold_open" else MIN_SHOT): continue          # too close: previous shot simply stays
        shots.append({"t0": t, "vi": vi, "type": v["type"]})
    if shots: shots[0]["t0"] = 0.0
    if len(shots) > 1 and dur - shots[-1]["t0"] < 1.4: shots.pop()
    mood = sc["s"].get("mood", "curious")
    wts = {"calm": (.1, 0, .7, .2), "curious": (.2, .2, .4, .2), "tense": (.3, .3, .1, .3), "shock": (.4, .4, 0, .2),
           "reveal": (.3, .2, .3, .2), "sad": (0, 0, .8, .2), "hopeful": (.1, .2, .5, .2)}.get(mood, (.25, .25, .25, .25))
    for i, sh in enumerate(shots):
        sh["t1"] = shots[i + 1]["t0"] if i + 1 < len(shots) else dur + 3.0
        sh["tr"] = rng.choices(("flash", "punch", "dissolve", "dip"), weights=wts)[0]
    texts = []
    for vi, v in enumerate(vis):
        if v["type"] == "motion": texts.append({"t": cues[vi], "len": CARD_LEN.get(v.get("kind"), 4.0), "kind": "motion", "vi": vi})
        elif v.get("overlay"): texts.append({"t": cues[vi], "len": 2.8, "kind": "overlay", "vi": vi, "text": v["overlay"]})
    texts.sort(key=lambda e: e["t"]); keep = []; last_end = -1.0
    for e in texts:                                       # never two texts at once, never in the first half second
        st = max(e["t"], .5, last_end + .4); ln = min(e["len"], dur + .6 - st)
        if ln < 1.8: continue
        e["t"], e["len"] = st, ln; last_end = st + ln; keep.append(e)
    return {"shots": shots, "texts": keep}

def fit_card(img, x, y):
    """Scale a motion-card canvas so it never reaches the caption zone (y > 812) or the HUD (y < 100)."""
    w, h = img.size; f = min(1.0, 722 / h, 1760 / w)
    if f < 1.0: img = img.resize((int(w * f), int(h * f)), Image.LANCZOS)
    nx = int(x + (w - img.width) / 2); ny = int(y + (h - img.height) / 2)
    return img, (nx, max(100, min(ny, 812 - img.height)))

# ------------------------------------------------------------------------------------------ sound plan
POOLS = {"calm": ["whoosh_air", "whoosh_low", "swell", "ping"], "curious": ["ping", "whoosh_fast", "tick", "whoosh_air"],
         "tense": ["riser_noise", "sub_drop", "low_pulse", "tick", "sting"], "shock": ["impact", "impact_metal", "impact_thud", "impact_crack", "glitch", "zap"],
         "reveal": ["reverse", "impact_thud", "sting", "ping"], "sad": ["swell", "sub_drop", "whoosh_low"], "hopeful": ["whoosh_air", "ping", "swell"]}
GAIN = {"impact": .7, "impact_metal": .62, "impact_thud": .72, "impact_crack": .62, "glitch": .45, "zap": .32, "sting": .48, "reverse": .5, "riser_noise": .45,
        "sub_drop": .58, "low_pulse": .38, "tick": .3, "ping": .34, "whoosh_fast": .36, "whoosh_air": .38, "whoosh_low": .4, "swell": .34, "boom": .6, "static": .22}
LEAD = {"riser_noise": 2.3, "swell": 1.4, "reverse": 1.7, "whoosh_fast": .3, "whoosh_air": .5, "whoosh_low": .6}
ACCENT_P = {"calm": .12, "curious": .28, "tense": .42, "shock": .5, "reveal": .3, "sad": .08, "hopeful": .18}
TEXT_FX = {"counter": ("ping", "tick"), "terminal": ("typing",), "headline": ("shutter", "glitch"), "redact": ("impact_crack",), "network": ("chirps",),
           "map": ("whoosh_low",), "doc_callout": ("whoosh_air",), "timeline": ("whoosh_fast",), "quote": ("sub_drop",), "title": ("whoosh_air",)}

def plan_sfx(scenes, plans, total, ep):
    rng = random.Random(ep * 7 + 3); ev = []; recent = []; last_t = [-9.0]
    def pick(pool):
        cand = [x for x in pool if x not in recent[-3:]] or pool
        c = rng.choice(cand); recent.append(c); return c
    def put(name, t, gain=None, dur=None, force=False):
        if not force and t - last_t[0] < 0.9: return
        e = {"t": max(0.0, t - LEAD.get(name, 0)), "sfx": name, "gain": gain if gain is not None else GAIN.get(name, .4), "pan": rng.uniform(-.4, .4)}
        if dur: e["dur"] = dur
        ev.append(e); last_t[0] = t
    for i, (sc, pl) in enumerate(zip(scenes, plans)):
        t0 = sc["t0"]; mood = sc["s"].get("mood", "curious")
        if i == 0:
            put("boom", 0.0, .9, force=True); ev.append({"t": .05, "sfx": "static", "gain": .2}); put("whoosh_air", 6.0) if False else None
        elif i == 1:
            put("whoosh_low", t0 + .1, .35, force=True); put("impact_thud", t0 + .5, .5, force=True)    # logo sting
        else:
            nm = pick(POOLS.get(mood, POOLS["curious"])); put(nm, t0, dur={"low_pulse": 2.5}.get(nm), force=True)
        for k, sh in enumerate(pl["shots"][1:], 1):
            if rng.random() < ACCENT_P.get(mood, .25):
                nm = "shutter" if sh["type"] == "archival" and rng.random() < .6 else pick(["tick", "whoosh_fast", "whoosh_air"] + (["zap"] if mood in ("shock", "tense") else []))
                put(nm, t0 + sh["t0"], .26)
        for e in pl["texts"]:
            if e["kind"] != "motion": continue
            kd = sc["s"]["visuals"][e["vi"]].get("kind")
            for nm in TEXT_FX.get(kd, ()):
                put(nm, t0 + e["t"], GAIN.get(nm, .4), dur={"typing": 2.4, "chirps": 2.2}.get(nm), force=True)
    ev.append({"t": max(0, total - 3.0), "sfx": "reverse", "gain": .45})
    ev.append({"t": max(0, total - 2.6), "sfx": ("impact_thud", "impact", "impact_metal", "impact_crack")[ep % 4], "gain": .55})
    return ev

def decode(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sfx.SR), "-"], capture_output=True)
    return np.frombuffer(r.stdout, np.float32)

def build_audio(scenes, plans, total, cat, ep, out_wav):
    N = int(sfx.SR * total) + sfx.SR; voice = np.zeros(N, np.float32)
    for sc in scenes:
        if sc["audio"] and os.path.exists(sc["audio"]):
            a = decode(sc["audio"]); i0 = int(sc["t0"] * sfx.SR); L = min(len(a), N - i0); voice[i0:i0 + L] += a[:L]
    moods = [(sc["t0"], sc["t0"] + sc["dur"] + GAP, sc["s"].get("mood", "curious")) for sc in scenes]
    music = sfx.music_bed(total, ep, moods, cat_shift=len(cat)); ev = plan_sfx(scenes, plans, total, ep)
    fx = sfx.mix_track(total, ev, None)
    from scipy.ndimage import uniform_filter1d
    env = np.abs(voice); env = uniform_filter1d(env, int(sfx.SR * .18))
    env = np.clip(env / (np.percentile(env[env > 0], 90) + 1e-6) if (env > 0).any() else env, 0, 1); env = uniform_filter1d(env, int(sfx.SR * .12))
    m = music[:N] if len(music) >= N else np.pad(music, (0, N - len(music)))
    mix = np.zeros((2, N), np.float32)
    for ch in (0, 1):
        mix[ch] = voice * 1.0 + m * 0.20 * (1 - .62 * env) + fx[ch][:N] * (1 - .35 * env)
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
    plans = [scene_plan(sc, ep * 100 + i) for i, sc in enumerate(scenes)]
    wav = os.path.join(workdir, "mix.wav"); build_audio(scenes, plans, total, cat, ep, wav)
    json.dump({"total": total, "scenes": [{"id": s["s"]["id"], "label": s["s"]["label"], "t0": s["t0"], "dur": s["dur"]} for s in scenes]}, open(os.path.join(workdir, "timeline.json"), "w"), indent=1)
    nshots = sum(len(p["shots"]) for p in plans); print(f"  plan: {len(scenes)} scenes, {nshots} shots (avg {total / max(1, nshots):.1f}s), {sum(len(p['texts']) for p in plans)} text events", flush=True)

    look = Look(acc); proc = ProcBG(ep, acc); provs = {}; tint_cur = np.zeros(3, np.float32)
    def prov(si, vi):
        key = (si, vi)
        if key not in provs:
            a = assets.get(f"{scenes[si]['s']['id']}:{vi}"); provs[key] = make_bg(a, ep * 1000 + si * 37 + vi) if a else None
        return provs[key]
    def cleanup(si, k):
        for key in [q for q in provs if q[0] < si or (q[0] == si and q[1] < k)]:
            p_ = provs.pop(key)
            if p_ is not None and hasattr(p_, "release"): p_.release()
    hud = Image.new("RGBA", (520, 70), (0, 0, 0, 0)); hd = ImageDraw.Draw(hud)
    hud.alpha_composite(logo(66), (6, 2))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-maxrate", "9M", "-bufsize", "18M", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{total:.3f}", out]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(total * FPS); si = 0; t_start = time.time(); chunks_cache = {}; rng = random.Random(ep)
    for fi in range(nfr):
        T = fi / FPS
        while si + 1 < len(scenes) and T >= scenes[si + 1]["t0"]: si += 1
        sc, pl = scenes[si], plans[si]; lt = T - sc["t0"]; sh_list = pl["shots"]
        # ---- current shot
        k = 0
        for q, sh in enumerate(sh_list):
            if sh["t0"] <= lt: k = q
        fr = None; sh = sh_list[k] if sh_list else None
        if sh:
            cleanup(si, k - 1)
            ts = max(0.0, lt - sh["t0"]); L = max(1.0, sh["t1"] - sh["t0"]); p_ = prov(si, sh["vi"])
            fr = p_.frame(ts, L) if p_ is not None else None
            if fr is not None and isinstance(p_, VidBG):                       # slow push-in / pull-out on video shots
                z = 1.0 + .06 * min(1.0, ts / L) if k % 2 == 0 else 1.06 - .06 * min(1.0, ts / L)
                fr = cv2.warpAffine(fr, np.float32([[z, 0, W * (1 - z) / 2], [0, z, H * (1 - z) / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            if fr is not None and k > 0 and ts < TR:                              # transition between shots
                tr = sh["tr"]
                if tr == "dissolve":
                    pv = sh_list[k - 1]; pp = prov(si, pv["vi"]); pf = pp.frame((pv["t1"] - pv["t0"]) + ts, 1) if pp is not None else None
                    if pf is not None: a = ts / TR; fr = cv2.addWeighted(pf, 1 - a, fr, a, 0)
                elif tr == "punch":
                    z = 1 + .08 * (1 - ts / TR) ** 2; fr = cv2.warpAffine(fr, np.float32([[z, 0, W * (1 - z) / 2], [0, z, H * (1 - z) / 2]]), (W, H), borderMode=cv2.BORDER_REFLECT)
                elif tr == "flash" and ts < .1: fr = np.clip(fr.astype(np.int16) + int(70 * (1 - ts / .1)), 0, 255).astype(np.uint8)
                elif tr == "dip": fr = (fr * (.4 + .6 * ts / TR)).astype(np.uint8)
        if fr is None: fr = proc.frame(T, 0)
        # ---- mood colour (smooth)
        tgt = np.array(MOOD_TINT.get(sc["s"].get("mood", "curious"), (0, 0, 0)), np.float32); tint_cur += (tgt - tint_cur) * .06
        look.mood_tint = tint_cur.astype(np.int16)
        fr = look.grade(np.ascontiguousarray(fr), fi)
        # ---- text: one thing at a time, kept clear of captions and HUD
        for e in pl["texts"]:
            if e["t"] <= lt < e["t"] + e["len"]:
                lt2 = lt - e["t"]; al = min(1, lt2 / .22) * min(1, (e["len"] - lt2) / .3)
                if e["kind"] == "motion":
                    v = sc["s"]["visuals"][e["vi"]]; res = motion.draw(v.get("kind", ""), v, lt2, e["len"], acc)
                    if res: img, (x, y) = fit_card(res[0], *res[1]); blend(fr, img, int(x), int(y), al)
                else:
                    img, (x, y) = motion.title({"text": e["text"]}, lt2, e["len"], acc); blend(fr, img, int(x), int(y), al)
                break
        # ---- transition punch + shake at scene starts
        if si > 0 and 0 <= lt < .32:
            p = lt / .32; off = int((1 - p) ** 2 * 26)
            if off: fr[..., 0] = np.roll(fr[..., 0], off, 1); fr[..., 2] = np.roll(fr[..., 2], -off, 1)
            if lt < .09: fr = np.clip(fr.astype(np.int16) + int(70 * (1 - lt / .09)), 0, 255).astype(np.uint8)
        if (sc["s"].get("act") in STRONG or si == 0) and 0 <= lt < .45:
            amp = 16 * (1 - lt / .45) ** 2; M = np.float32([[1, 0, rng.uniform(-amp, amp)], [0, 1, rng.uniform(-amp, amp)]])
            fr = cv2.warpAffine(fr, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        # ---- captions (word-synced)
        if si not in chunks_cache: chunks_cache[si] = chunk_words(sc["words"])
        for ch in chunks_cache[si]:
            if ch[0]["s"] - .05 <= lt <= ch[-1]["e"] + .25:
                hi = max([i for i, w in enumerate(ch) if w["s"] <= lt] or [0]); img = caption_img(ch, hi)
                blend(fr, img, (W - img.width) // 2, 850, min(1, (lt - ch[0]["s"] + .05) / .12)); break
        # ---- HUD (logo + case no.), progress, fades, outro
        blend(fr, hud, 28, 22, .9)
        cv2.rectangle(fr, (0, H - 5), (int(W * T / total), H), acc, -1)
        if T < .35: fr = (fr * (T / .35)).astype(np.uint8)
        if T > total - OUTRO + .3:
            kk = min(1, (T - (total - OUTRO + .3)) / 1.0); fr = (fr * (1 - kk)).astype(np.uint8)
            if kk > .5:
                wm = wordmark(1180); end = Image.new("RGBA", (1400, wm.height + 170), (0, 0, 0, 0)); ed = ImageDraw.Draw(end)
                end.alpha_composite(wm, ((1400 - wm.width) // 2, 0))
                ed.text((700, wm.height + 40), "TRUE STORIES OF REAL HACKS", font=motion.BOLD(40), fill=YEL + (255,), anchor="mm")
                ed.text((700, wm.height + 110), "SUBSCRIBE FOR THE NEXT STORY", font=motion.BOLD(30), fill=(255, 255, 255, 200), anchor="mm")
                blend(fr, end, (W - 1400) // 2, (H - end.height) // 2, (kk - .5) * 2)
        # ---- logo sting right after the cold open
        if si == 1 and .15 <= lt < 2.2:
            q = lt - .15; a = min(1, q / .3) * min(1, (2.05 - q) / .4)
            wm = wordmark(int(820 + 60 * min(1, q / 2.0))); blend(fr, wm, (W - wm.width) // 2, (H - wm.height) // 2 - 40, a * .98)
        pipe.stdin.write(np.ascontiguousarray(fr).tobytes())
        if fi % 240 == 0: print(f"  frame {fi}/{nfr}  ({time.time() - t_start:.0f}s)", flush=True)
    pipe.stdin.close(); pipe.wait()
    for p_ in provs.values():
        if p_ is not None and hasattr(p_, "release"): p_.release()
    print("rendered", out, f"{os.path.getsize(out) / 1e6:.1f} MB in {time.time() - t_start:.0f}s")
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--script", required=True); ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--max-seconds", type=float)
    a = ap.parse_args(); render(a.script, a.workdir, a.out, a.max_seconds)
