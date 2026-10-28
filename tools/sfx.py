"""Procedural sound design for Breach Uncovered — zero licensing risk, fully deterministic.
All functions return float32 mono numpy arrays at SR (peak-normalised ~0.9 unless stated).
`mix_track()` places events on a timeline and returns stereo audio.
"""
import numpy as np
from scipy import signal

SR = 44100
_rng = np.random.default_rng(7)

def _t(d): return np.arange(int(SR * d)) / SR
def _norm(x, peak=0.9):
    m = np.max(np.abs(x)) or 1.0
    return (x / m * peak).astype(np.float32)
def _env(n, a=0.005, d=0.3, curve=3.0):
    t = np.arange(n) / SR
    e = np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-t * curve / max(d, 1e-3))
    return e
def _lp(x, f, order=4): return signal.sosfilt(signal.butter(order, f, "low", fs=SR, output="sos"), x)
def _hp(x, f, order=4): return signal.sosfilt(signal.butter(order, f, "high", fs=SR, output="sos"), x)
def _bp(x, lo, hi, order=3): return signal.sosfilt(signal.butter(order, [lo, hi], "band", fs=SR, output="sos"), x)
def _noise(n, rng=None): return (rng or _rng).standard_normal(n).astype(np.float32)

def sub_boom(d=1.6, f0=62, f1=32):
    t = _t(d); f = f1 + (f0 - f1) * np.exp(-t * 6)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.003, d * .9, 4.2)
    n = _lp(_noise(len(t)), 160) * _env(len(t), 0.002, .35, 7) * 0.7
    return _norm(x + n)

def impact(d=1.4):
    """Cinematic hit: transient crack + sub boom + short reverb-ish tail."""
    t = _t(d)
    crack = _hp(_noise(len(t)), 1800) * _env(len(t), 0.001, .09, 9) * .6
    body = _bp(_noise(len(t)), 60, 700) * _env(len(t), 0.002, .5, 6) * .8
    x = sub_boom(d) * 1.0 + crack + body
    tail = _lp(_noise(len(t)), 900) * _env(len(t), 0.05, d, 2.2) * .12
    return _norm(x + tail)

def whoosh(d=0.7, up=True):
    n = int(SR * d); x = _noise(n)
    t = np.arange(n) / SR; sweep = np.linspace(0, 1, n) if up else np.linspace(1, 0, n)
    out = np.zeros(n, np.float32); blocks = 24
    for i in range(blocks):
        a, b = int(i * n / blocks), int((i + 1) * n / blocks)
        c = 250 + 5200 * (sweep[a] ** 1.6)
        out[a:b] = _bp(x, max(60, c * .6), min(c * 1.4, 18000), 2)[a:b]
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.6
    return _norm(out * env, .8)

def riser(d=4.0):
    n = int(SR * d); t = np.arange(n) / SR
    f = 80 * (2 ** (t / d * 4)); tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .35
    nz = _hp(_noise(n), 800) * (t / d) ** 2 * .6
    shim = np.sin(2 * np.pi * np.cumsum(500 * 2 ** (t / d * 3)) / SR) * (t / d) ** 3 * .2
    return _norm((tone + nz + shim) * (t / d) ** 1.2, .85)

def reverse_hit(d=1.8):
    x = impact(d)[::-1].copy(); x *= np.linspace(0, 1, len(x)) ** 1.5
    return _norm(x, .85)

def glitch(d=0.45):
    n = int(SR * d); out = np.zeros(n, np.float32); r = np.random.default_rng(int(d * 1000))
    pos = 0
    while pos < n:
        L = int(r.integers(int(SR * .008), int(SR * .05))); seg = _noise(L, r) * (r.random() > .35)
        seg = _bp(seg, r.integers(300, 900), r.integers(2500, 9000), 2) if r.random() > .3 else seg * .3
        out[pos:pos + L] += seg[:max(0, min(L, n - pos))] if pos + L <= n else seg[:n - pos]
        pos += L + int(r.integers(0, int(SR * .02)))
    bit = np.round(out * 6) / 6
    return _norm(bit * _env(n, .001, d, 3.2), .75)

def blip(f=1200, d=0.06):
    t = _t(d); return _norm(np.sign(np.sin(2 * np.pi * f * t)) * .5 * _env(len(t), .001, d, 6), .5)

def data_chirps(d=1.2):
    out = np.zeros(int(SR * d), np.float32); r = np.random.default_rng(11); pos = 0
    while pos < len(out) - SR // 10:
        b = blip(float(r.choice([900, 1400, 1800, 2400, 3200])), float(r.uniform(.03, .08)))
        out[pos:pos + len(b)] += b; pos += int(SR * r.uniform(.04, .13))
    return _norm(out, .6)

def keystroke(d=0.07, seed=0):
    r = np.random.default_rng(seed); n = int(SR * d)
    click = _bp(_noise(n, r), 1500, 6000, 2) * _env(n, .0005, .02, 9)
    thock = _bp(_noise(n, r), 150, 600, 2) * _env(n, .001, .05, 8) * .7
    return click + thock

def typing(d=2.0, cps=9, seed=3):
    out = np.zeros(int(SR * d), np.float32); r = np.random.default_rng(seed); t = 0.0
    while t < d - .1:
        k = keystroke(seed=int(r.integers(0, 999))); a = int(t * SR)
        out[a:a + len(k)] += k[:len(out) - a] * float(r.uniform(.6, 1.0)); t += float(r.exponential(1 / cps)) + .02
    return _norm(out, .55)

def heartbeat(d=4.0, bpm=62):
    out = np.zeros(int(SR * d), np.float32); beat = 60 / bpm; t = 0.0
    while t < d - .5:
        for off, g in ((0, 1.0), (.27, .7)):
            h = _lp(_noise(int(SR * .25)), 140) * _env(int(SR * .25), .004, .12, 6)
            h += np.sin(2 * np.pi * 52 * _t(.25)) * _env(int(SR * .25), .004, .15, 5)
            a = int((t + off) * SR); out[a:a + len(h)] += h[:len(out) - a] * g
        t += beat
    return _norm(out, .8)

def alarm(d=2.4, f=760):
    t = _t(d); sw = np.where(np.sin(2 * np.pi * 1.7 * t) > 0, f, f * 1.32)
    x = signal.sawtooth(2 * np.pi * np.cumsum(sw) / SR) * .4
    return _norm(_lp(x, 3800) * np.minimum(t / .05, 1) * np.minimum((d - t) / .15, 1), .55)

def static(d=1.2):
    n = int(SR * d); x = _hp(_noise(n), 500) * (.6 + .4 * np.sin(2 * np.pi * 23 * np.arange(n) / SR))
    return _norm(x * _env(n, .002, d, 1.6), .6)

def tape_stop(d=1.0):
    n = int(SR * d); t = np.arange(n) / SR; f = 520 * (1 - t / d) ** 2.2 + 22
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (1 - t / d)
    return _norm(_lp(x, 2400), .6)

def drone(d, base=55.0, seed=0, dark=True):
    """Evolving tension bed: detuned saw stack + sub + filtered noise swell; loopable length d seconds."""
    n = int(SR * d); t = np.arange(n) / SR; r = np.random.default_rng(seed)
    x = np.zeros(n)
    for k, ratio in enumerate((1.0, 1.5, 2.0, 2.997, 4.0)):
        det = 1 + r.uniform(-.004, .004)
        lfo = 0.55 + 0.45 * np.sin(2 * np.pi * (0.03 + .02 * k) * t + r.uniform(0, 6.28))
        x += signal.sawtooth(2 * np.pi * base * ratio * det * t) * lfo * (.5 / (k + 1))
    x = _lp(x, 700 if dark else 1400, 2)
    x += np.sin(2 * np.pi * base / 2 * t) * .6
    bed = _lp(_noise(n, r), 400) * (.15 + .1 * np.sin(2 * np.pi * .05 * t))
    pulse = (np.sin(2 * np.pi * (base / 2) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * (1 / 2.0) * t)) ** 6) * .3
    y = x + bed + pulse
    fade = np.minimum(t / 3, 1) * np.minimum((d - t) / 3, 1)
    return _norm(y * fade, .8)

# ---------------------------------------------------------------- extra variants (so a video never repeats one sound)
def impact_metal(d=1.5):
    t = _t(d); x = np.zeros(len(t))
    for f, g in ((180, 1.0), (283, .8), (417, .6), (655, .45), (1110, .3)):
        x += np.sin(2 * np.pi * f * t) * g * np.exp(-t * (3.5 + f / 300))
    x = x * .35 + sub_boom(d) * .8 + _hp(_noise(len(t)), 2500) * _env(len(t), .001, .05, 9) * .4
    return _norm(x)

def impact_thud(d=1.2):
    t = _t(d); f = 90 * np.exp(-t * 9) + 38
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), .002, .6, 5) + _lp(_noise(len(t)), 300) * _env(len(t), .001, .08, 10) * .8
    return _norm(x)

def impact_crack(d=0.9):
    t = _t(d); x = _hp(_noise(len(t)), 900) * _env(len(t), .0008, .12, 8) + _bp(_noise(len(t)), 120, 900) * _env(len(t), .001, .25, 7) * .8
    return _norm(x + sub_boom(d) * .5)

def whoosh_fast(d=0.35): return whoosh(d, True)
def whoosh_low(d=1.0):
    n = int(SR * d); x = _lp(_noise(n), 900); env = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.2
    return _norm(x * env, .75)
def whoosh_air(d=0.9):
    n = int(SR * d); x = _hp(_noise(n), 3000) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return _norm(x, .55)

def ping(d=1.6, f=1175):
    t = _t(d); x = (np.sin(2 * np.pi * f * t) + .35 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t * 3.2)
    return _norm(x, .5)

def tick(d=0.12):
    t = _t(d); x = _bp(_noise(len(t)), 2200, 6500, 2) * _env(len(t), .0004, .02, 9) + np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * .5
    return _norm(x, .5)

def shutter(d=0.28):
    a = tick(.05); b = np.zeros(int(SR * d), np.float32); b[:len(a)] += a; c = _bp(_noise(int(SR * .08)), 900, 4200, 2) * _env(int(SR * .08), .001, .04, 7)
    b[int(SR * .12):int(SR * .12) + len(c)] += c * .8
    return _norm(b, .55)

def zap(d=0.5):
    n = int(SR * d); t = np.arange(n) / SR; f = 2600 * np.exp(-t * 7) + 300
    x = signal.square(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    return _norm(_lp(x, 6000), .5)

def sting(d=1.8):
    t = _t(d); x = np.zeros(len(t))
    for f in (233, 247, 349, 370):                      # tense cluster (minor 2nds)
        x += signal.sawtooth(2 * np.pi * f * t) * .25
    x = _lp(x, 1800) * _env(len(t), .01, d * .8, 3.2)
    return _norm(x + sub_boom(d) * .4, .7)

def swell(d=3.2, f=110):
    t = _t(d); x = np.zeros(len(t))
    for r in (1, 1.5, 2.0, 2.52):
        x += np.sin(2 * np.pi * f * r * t + r) * .4
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.6
    return _norm(_lp(x, 900) * env, .6)

def sub_drop(d=1.8):
    t = _t(d); f = 120 * np.exp(-t * 1.8) + 28
    return _norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), .01, d, 2.0), .85)

def riser_noise(d=2.5):
    n = int(SR * d); t = np.arange(n) / SR; x = _bp(_noise(n), 600, 7000, 2) * (t / d) ** 2.2
    return _norm(x, .6)

def low_pulse(d=3.0, bpm=70):
    out = np.zeros(int(SR * d), np.float32); beat = 60 / bpm; t = 0.0
    while t < d - .3:
        h = np.sin(2 * np.pi * 46 * _t(.3)) * _env(int(SR * .3), .004, .2, 5); a = int(t * SR); out[a:a + len(h)] += h[:len(out) - a]; t += beat
    return _norm(out, .75)

VARIABLE = ("typing", "alarm", "heartbeat", "static", "chirps", "riser", "swell", "riser_noise", "low_pulse")

# ---------------------------------------------------------------- music beds (different per episode, change with the mood)
SCALE_MINOR = (0, 2, 3, 5, 7, 8, 10)
MOOD_LEVEL = {"calm": .55, "curious": .65, "tense": .95, "shock": 1.1, "reveal": .85, "sad": .5, "hopeful": .7}
MOOD_DARK = {"calm": .3, "curious": .4, "tense": .9, "shock": 1.0, "reveal": .7, "sad": .8, "hopeful": .1}
ROOTS = (41.2, 43.65, 46.25, 49.0, 51.9, 55.0, 58.3, 61.7)      # E1 .. B1 (low, dark)

def _hz(root, semis): return root * 2 ** (semis / 12)

def _style_drone(n, root, r):
    return drone(n / SR, root, int(r.integers(0, 999)))[:n]

def _style_pulse(n, root, r, bpm=78):
    t = np.arange(n) / SR; out = np.zeros(n); step = 60 / bpm / 2; k = 0; notes = [0, 0, 7, 0, 3, 0, 5, 0]
    for i in range(int(n / SR / step)):
        f = _hz(root * 2, notes[i % 8]); a = int(i * step * SR); L = int(step * SR * .9)
        if a + L > n: break
        tt = np.arange(L) / SR; env = np.minimum(tt / .005, 1) * np.exp(-tt * 7)
        out[a:a + L] += signal.sawtooth(2 * np.pi * f * tt) * env * .5
    out = _lp(out, 1200, 2) + np.sin(2 * np.pi * root * t) * .35 * (0.6 + .4 * np.sin(2 * np.pi * t / 8))
    return _norm(out, .8)

def _style_pads(n, root, r):
    t = np.arange(n) / SR; out = np.zeros(n); chords = [(0, 3, 7), (8, 0, 3), (5, 8, 0), (10, 2, 5)]; seg = 8.0
    for i in range(int(n / SR / seg) + 1):
        a, b = int(i * seg * SR), min(n, int((i + 1) * seg * SR) + int(SR * 2))
        if a >= n: break
        tt = np.arange(b - a) / SR; env = np.minimum(tt / 2.5, 1) * np.minimum((b - a) / SR - tt, 2.5) / 2.5
        for semi in chords[(i + int(r.integers(0, 4))) % 4]:
            f = _hz(root * 2, semi); out[a:b] += (np.sin(2 * np.pi * f * tt) + .4 * np.sin(2 * np.pi * f * 2.003 * tt)) * env * .3
    out += np.sin(2 * np.pi * root * t) * .3
    return _norm(_lp(out, 1500, 2), .8)

def _style_tick(n, root, r):
    t = np.arange(n) / SR; out = np.sin(2 * np.pi * root * t) * .45 + _lp(signal.sawtooth(2 * np.pi * root * 1.5 * t), 400, 2) * .2
    k = tick(); step = 0.5
    for i in range(int(n / SR / step)):
        a = int(i * step * SR)
        if a + len(k) >= n: break
        out[a:a + len(k)] += k * (.5 if i % 4 else .9)
    pl = ping(1.2, _hz(root * 8, SCALE_MINOR[int(r.integers(0, 7))]))
    for i in range(int(n / SR / 6.5)):
        a = int((i * 6.5 + 2) * SR)
        if a + len(pl) < n: out[a:a + len(pl)] += pl * .25
    return _norm(out, .8)

STYLES = (_style_drone, _style_pulse, _style_pads, _style_tick)
STYLE_NAMES = ("drone", "pulse", "pads", "tick")

def music_bed(total, ep, moods, cat_shift=0):
    """moods: list of (t0, t1, mood). Style, key and layering depend on the episode, intensity follows the mood."""
    n = int(SR * (total + 2)); r = np.random.default_rng(1000 + ep)
    style = (ep - 1) % len(STYLES); root = ROOTS[(ep * 3 + cat_shift) % len(ROOTS)]
    base = STYLES[style](n, root, r); base = np.pad(base, (0, max(0, n - len(base))))[:n]
    dark = drone(total + 2, root, 7 + ep, True)[:n]; dark = np.pad(dark, (0, max(0, n - len(dark))))[:n]
    lvl = np.full(n, .6, np.float32); drk = np.zeros(n, np.float32)
    for t0, t1, m in moods:
        a, b = int(max(0, t0) * SR), min(n, int(t1 * SR)); lvl[a:b] = MOOD_LEVEL.get(m, .65); drk[a:b] = MOOD_DARK.get(m, .4)
    from scipy.ndimage import uniform_filter1d
    k = int(SR * 2.5); sm = lambda x: uniform_filter1d(x, k, mode="nearest")
    lvl, drk = sm(lvl), sm(drk)
    mix = base * lvl * (1 - .5 * drk) + dark * drk * .8 * lvl
    fade = np.minimum(np.arange(n) / (SR * 2), 1) * np.minimum((n - np.arange(n)) / (SR * 3), 1)
    return _norm(mix * fade, .8)

def _place(buf, ev, at, gain=1.0, pan=0.0):
    a = int(at * SR)
    if a >= buf.shape[1]: return
    L = min(len(ev), buf.shape[1] - a)
    gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, a:a + L] += ev[:L] * gain * gl; buf[1, a:a + L] += ev[:L] * gain * gr

LIB = {
    "impact": impact, "boom": sub_boom, "whoosh_up": lambda: whoosh(.7, True), "whoosh_down": lambda: whoosh(.7, False),
    "riser": riser, "reverse": reverse_hit, "glitch": glitch, "chirps": data_chirps, "typing": typing,
    "heartbeat": heartbeat, "alarm": alarm, "static": static, "tape_stop": tape_stop,
}

LIB.update({
    "impact_metal": impact_metal, "impact_thud": impact_thud, "impact_crack": impact_crack,
    "whoosh_fast": whoosh_fast, "whoosh_low": whoosh_low, "whoosh_air": whoosh_air, "ping": ping, "tick": tick, "shutter": shutter,
    "zap": zap, "sting": sting, "swell": swell, "sub_drop": sub_drop, "riser_noise": riser_noise, "low_pulse": low_pulse,
})
def mix_track(total, events, music=None, music_gain=0.20, seed=0):
    """events: list of dicts {t, sfx, gain, pan, dur?}. Returns stereo float32 [2, N] (no voice)."""
    N = int(SR * total) + SR; buf = np.zeros((2, N), np.float32)
    cache = {}
    for e in events:
        k = e["sfx"]
        if k not in cache: cache[k] = LIB[k]()
        ev = cache[k]
        if "dur" in e and k in VARIABLE:
            ev = LIB[k](e["dur"]) if k != "chirps" else data_chirps(e["dur"])
        _place(buf, ev, e["t"], e.get("gain", 0.8), e.get("pan", 0.0))
    if music is not None:
        m = music[:N] if len(music) >= N else np.pad(music, (0, N - len(music)))
        buf[0] += m * music_gain; buf[1] += m * music_gain
    return buf

def write_wav(path, stereo):
    import wave
    x = np.clip(stereo.T, -1, 1); pcm = (x * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    import sys, os, time
    out = sys.argv[1] if len(sys.argv) > 1 else "sfx_demo.wav"; t0 = time.time()
    ev = [{"t": 1.0, "sfx": "whoosh_up"}, {"t": 1.65, "sfx": "impact", "gain": 1.0}, {"t": 3.0, "sfx": "typing", "dur": 2.0},
          {"t": 5.5, "sfx": "glitch"}, {"t": 6.2, "sfx": "heartbeat", "dur": 3.0}, {"t": 9.5, "sfx": "riser", "dur": 3.5},
          {"t": 13.0, "sfx": "impact", "gain": 1.0}, {"t": 13.6, "sfx": "alarm", "dur": 1.6}, {"t": 15.5, "sfx": "tape_stop"}]
    st = mix_track(18, ev, drone(18, 55, 1), .22); write_wav(out, st / max(1, np.abs(st).max()) * .9)
    print("wrote", out, f"{time.time() - t0:.1f}s")
