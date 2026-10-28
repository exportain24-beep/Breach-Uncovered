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

def mix_track(total, events, music=None, music_gain=0.20, seed=0):
    """events: list of dicts {t, sfx, gain, pan, dur?}. Returns stereo float32 [2, N] (no voice)."""
    N = int(SR * total) + SR; buf = np.zeros((2, N), np.float32)
    cache = {}
    for e in events:
        k = e["sfx"]
        if k not in cache: cache[k] = LIB[k]()
        ev = cache[k]
        if "dur" in e and k in ("typing", "alarm", "heartbeat", "static", "chirps", "riser"):
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
