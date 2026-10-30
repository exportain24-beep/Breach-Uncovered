"""Render the fixed 2.5 s logo outro once (assets/brand/outro_vertical.mp4, 1080x1920, 30 fps).
Every Short ends with exactly this clip, so the brand ending is always identical. Re-run only if the logo changes."""
import os, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); B = os.path.join(ROOT, "assets", "brand"); F = os.path.join(ROOT, "assets", "fonts")
W, H, FPS, DUR = 1080, 1920, 30, 2.5
ease = lambda x: 1 - (1 - min(1, max(0, x))) ** 3
eio = lambda x: (lambda y: y * y * (3 - 2 * y))(min(1, max(0, x)))
def back(x):
    x = min(1, max(0, x)); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def load(name, width):
    im = Image.open(os.path.join(B, name)).convert("RGBA"); h = int(im.height * width / im.width)
    return np.asarray(im.resize((width, h), Image.LANCZOS)).astype(np.float32) / 255.0
MARK = load("anim_mark.png", 780); TEXT = load("anim_text.png", 920)

def over(dst, src, cx, cy, scale=1.0, alpha=1.0, add=False):
    if alpha <= 0.002: return
    s = src if abs(scale - 1) < 1e-3 else cv2.resize(src, (max(1, int(src.shape[1] * scale)), max(1, int(src.shape[0] * scale))), interpolation=cv2.INTER_LINEAR)
    h, w = s.shape[:2]; x0, y0 = int(cx - w / 2), int(cy - h / 2); x1, y1 = x0 + w, y0 + h
    a0, b0 = max(0, x0), max(0, y0); a1, b1 = min(W, x1), min(H, y1)
    if a1 <= a0 or b1 <= b0: return
    p = s[b0 - y0:b1 - y0, a0 - x0:a1 - x0]; al = p[..., 3:4] * alpha; reg = dst[b0:b1, a0:a1]
    dst[b0:b1, a0:a1] = reg + p[..., :3] * al if add else reg * (1 - al) + p[..., :3] * al

def background(t):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - 900) / H) ** 2)
    base = np.dstack([np.full((H, W), c) for c in (0.043, 0.07, 0.15)]) * np.clip(1.2 - 1.6 * r, 0.25, 1.0)[..., None]
    return base
BG = background(0)
rng = np.random.default_rng(7); PX, PY, PS, PV = rng.uniform(0, W, 70), rng.uniform(0, H, 70), rng.uniform(1.5, 4, 70), rng.uniform(10, 40, 70)
FONT1 = ImageFont.truetype(os.path.join(F, "Inter-Bold.otf"), 50); FONT2 = ImageFont.truetype(os.path.join(F, "Inter-Bold.otf"), 38)
def tagline():
    im = Image.new("RGBA", (1000, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((500, 46), "TRUE STORIES OF REAL HACKS", font=FONT1, fill=(255, 212, 0, 255), anchor="mm"); d.text((500, 122), "FOLLOW FOR THE NEXT STORY", font=FONT2, fill=(255, 255, 255, 235), anchor="mm")
    return np.asarray(im).astype(np.float32) / 255.0
TAG = tagline()

def frame(t):
    f = BG.copy(); zoom = 1 + .03 * eio(t / DUR)
    # drifting particles + grid
    for x, y, s, v in zip(PX, PY, PS, PV):
        cv2.circle(f, (int(x), int((y - t * v) % H)), int(s), (0.16, 0.55, 0.85), -1, cv2.LINE_AA)
    # light streaks converging (0.0 - 0.6)
    k = ease(t / .6)
    for i, (y, col, d) in enumerate([(630, (0.16, .82, 1.0), -1), (690, (1.0, .55, .12), 1), (750, (0.16, .82, 1.0), 1), (570, (1.0, .55, .12), -1), (810, (0.3, .6, 1.0), -1)]):
        if t < .7:
            L = 600 * (1 - k) + 40; x = W / 2 + d * (1 - k) * 700
            cv2.line(f, (int(x - L), y), (int(x + L), y), col, 6 - i % 3 * 2, cv2.LINE_AA)
    # mark: scale-in with glitch RGB split, bloom
    km = back((t - .1) / .5); am = ease((t - .1) / .25)
    sc = (.55 + .45 * km) * zoom * (1 + .015 * np.sin(t * 3))
    split = int(26 * max(0, 1 - (t - .1) / .45))
    if split > 0:
        r = MARK.copy(); r[..., 1:3] = 0; over(f, r, 540 - split, 760, sc, am * .55, add=True)
        b = MARK.copy(); b[..., 0] = 0; over(f, b, 540 + split, 760, sc, am * .55, add=True)
    over(f, MARK, 540, 690, sc, am)
    glow = cv2.GaussianBlur(MARK, (0, 0), 18); over(f, glow, 540, 690, sc, am * .55, add=True)
    # keyhole flare burst (0.5 - 1.0)
    kf = (t - .5) / .5
    if 0 < kf < 1:
        fl = np.zeros((H, W, 3), np.float32); cx, cy = int(540 + (.48 - .5) * 780 * sc), int(690 + (.55 - .5) * MARK.shape[0] * sc)
        cv2.circle(fl, (cx, cy), int(40 + 380 * ease(kf)), (0.6, 0.9, 1.0), -1, cv2.LINE_AA); fl = cv2.GaussianBlur(fl, (0, 0), 60)
        f += fl * (1 - kf) * .9
    # text: left-to-right wipe with bright edge, small rise
    kw = eio((t - .55) / .6)
    if kw > 0:
        tx = TEXT.copy(); w = tx.shape[1]; edge = int(w * kw); tx[:, edge:, 3] = 0
        over(f, tx, 540, int(1200 + 30 * (1 - ease((t - .55) / .6))), zoom, 1.0)
        if kw < 1:
            ex = int(540 - w * zoom / 2 + edge * zoom); cv2.line(f, (ex, 1110), (ex, 1290), (1, 1, 1), 6, cv2.LINE_AA)
            sp = np.zeros_like(f); cv2.line(sp, (ex, 1090), (ex, 1310), (.4, .85, 1), 30, cv2.LINE_AA); f += cv2.GaussianBlur(sp, (0, 0), 25) * .8
    # shine sweep across everything (1.25 - 1.85)
    ks = (t - 1.25) / .6
    if 0 < ks < 1:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); band = np.exp(-(((xx + yy * .45) - (-300 + ks * 2400)) / 70) ** 2)
        lum = (f.max(2) > .35).astype(np.float32); f += (band * lum * .55)[..., None]
    # tagline
    ka = ease((t - 1.35) / .4)
    if ka > 0: over(f, TAG, 540, int(1490 + 40 * (1 - ka)), 1.0, ka)
    return np.clip(f, 0, 1)

if __name__ == "__main__":
    out = os.path.join(B, "outro_vertical.mp4"); n = int(DUR * FPS)
    p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n):
        fr = (frame(i / FPS) * 255).astype(np.uint8); p.stdin.write(fr.tobytes())
        if i in (6, 18, 30, 45, 74): cv2.imwrite(f"/tmp/outro_{i}.png", cv2.cvtColor(cv2.resize(fr, (360, 640)), cv2.COLOR_RGB2BGR))
    p.stdin.close(); p.wait(); print("wrote", out, os.path.getsize(out))
