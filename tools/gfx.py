"""Full-frame motion-graphics scenes drawn by us (no stock footage). Every kind returns an RGB uint8 frame (1080x1920).
gfx.render(kind, spec, t, dur, acc, seed) -> frame.   t = seconds since the shot started, dur = shot length.
Look: dark navy studio background with a perspective grid floor and drifting particles, neon-glow line work, soft bloom.
All text is kept in y 110..800 (captions live at y>=850, the logo HUD at the top-left)."""
import math, random, re
import numpy as np, cv2
from PIL import Image, ImageDraw
import motion
from motion import DISP, BOLD, MED, MONO, MONOB, wrap, ease, ease_io, seed_of

W, H = 1920, 1080
RED, CYAN, GREEN, YEL, WHITE = (255, 62, 76), (70, 210, 255), (60, 255, 150), (255, 212, 0), (255, 255, 255)
AA = cv2.LINE_AA

# ---------------------------------------------------------------------------------- helpers
class Text:
    """Collects text operations, then composites them once (PIL layer -> numpy, bbox only)."""
    def __init__(self): self.ops = []
    def add(self, xy, s, font, fill=WHITE, anchor="la", alpha=1.0, stroke=0):
        if alpha > .01 and s: self.ops.append((xy, str(s), font, fill, anchor, alpha, stroke))
    def apply(self, fr):
        if not self.ops: return fr
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (xy, s, font, fill, anchor, alpha, stroke) in self.ops:
            col = tuple(int(c) for c in fill) + (int(255 * min(1, alpha)),)
            d.text(xy, s, font=font, fill=col, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, int(255 * min(1, alpha))) if stroke else None)
        bb = lay.getbbox()
        if not bb: return fr
        x0, y0, x1, y1 = bb; a = np.asarray(lay.crop(bb)).astype(np.uint16)
        reg = fr[y0:y1, x0:x1].astype(np.uint16); al = a[..., 3:4]
        fr[y0:y1, x0:x1] = ((reg * (255 - al) + a[..., :3] * al) // 255).astype(np.uint8)
        return fr

def col(c, k=1.0): return tuple(int(max(0, min(255, v * k))) for v in c)

_BG = {}; _PART = {}
def base(t, acc, seed):
    key = tuple(acc)
    if key not in _BG:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]; xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :, None]
        top, bot = np.array([10, 14, 28], np.float32), np.array([3, 5, 11], np.float32)
        g = top * (1 - yy) + bot * yy + np.array(acc, np.float32) * .085 * np.exp(-(xx ** 2) * 1.5) * np.exp(-((yy - .42) ** 2) * 6)
        _BG[key] = np.ascontiguousarray(g.clip(0, 255).astype(np.uint8))
    f = _BG[key].copy(); lay = np.zeros_like(f); hz = int(H * .60); gc = col(acc, .30)
    for k in range(12):
        p = ((k + t * .30) % 12) / 12; y = int(hz + (H - hz) * p ** 2.3); cv2.line(lay, (0, y), (W, y), col(acc, .12 + .5 * p * .35), 1, AA)
    for i in range(-18, 19): cv2.line(lay, (int(W / 2 + i * 22), hz), (int(W / 2 + i * 190), H), gc, 1, AA)
    cv2.line(lay, (0, hz), (W, hz), col(acc, .55), 1, AA)
    f = cv2.add(f, (lay * .55).astype(np.uint8))
    if seed not in _PART:
        r = np.random.default_rng(seed); _PART[seed] = (r.uniform(0, W, 80), r.uniform(60, hz, 80), r.uniform(6, 30, 80), r.uniform(.8, 2.2, 80))
    px, py, sp, rad = _PART[seed]
    for x, y, s, r_ in zip(px, py, sp, rad): cv2.circle(f, (int((x + t * s) % W), int(y + 8 * math.sin(t * .6 + x))), int(round(r_)), col(acc, .75), -1, AA)
    return f

def bloom(f, k=.55):
    s = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), 7); return cv2.addWeighted(f, 1.0, cv2.resize(s, (W, H), interpolation=cv2.INTER_LINEAR), k, 0)

def label(T, spec, t, y=772):
    s = spec.get("label") or ""
    if not s: return
    a = ease((t - .25) / .4); w = DISP(40).getlength(s.upper())
    T.add((W // 2, y), s.upper(), DISP(40), YEL, "mm", a, 4)

def txt_of(spec, key="text"):
    v = spec.get(key)
    if v: return str(v)
    d = spec.get("data")
    return str(d) if isinstance(d, str) else ""

def D(spec, key, default=None):
    d = spec.get("data")
    return d.get(key, default) if isinstance(d, dict) else default

def rrect(img, p0, p1, color, r=18, thick=-1):
    x0, y0 = p0; x1, y1 = p1
    if thick < 0:
        cv2.rectangle(img, (x0 + r, y0), (x1 - r, y1), color, -1, AA); cv2.rectangle(img, (x0, y0 + r), (x1, y1 - r), color, -1, AA)
        for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)): cv2.circle(img, (cx, cy), r, color, -1, AA)
    else:
        cv2.line(img, (x0 + r, y0), (x1 - r, y0), color, thick, AA); cv2.line(img, (x0 + r, y1), (x1 - r, y1), color, thick, AA)
        cv2.line(img, (x0, y0 + r), (x0, y1 - r), color, thick, AA); cv2.line(img, (x1, y0 + r), (x1, y1 - r), color, thick, AA)
        for (cx, cy, a0) in ((x0 + r, y0 + r, 180), (x1 - r, y0 + r, 270), (x0 + r, y1 - r, 90), (x1 - r, y1 - r, 0)):
            cv2.ellipse(img, (cx, cy), (r, r), 0, a0, a0 + 90, color, thick, AA)

def alpha_rect(f, p0, p1, color, a):
    x0, y0 = p0; x1, y1 = p1; reg = f[y0:y1, x0:x1]
    f[y0:y1, x0:x1] = (reg * (1 - a) + np.array(color, np.float32) * a).astype(np.uint8)

def camera(f, t, dur, z0=1.0, z1=1.05):
    z = z0 + (z1 - z0) * min(1, t / max(dur, 1))
    return cv2.warpAffine(f, np.float32([[z, 0, W * (1 - z) / 2], [0, z, H * (1 - z) / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------------------------- network (spreading infection)
def network(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); r = random.Random(seed_of(txt_of(spec) or "net") + seed); n = 78
    pts = []
    while len(pts) < n:
        x, y = r.randint(170, 1750), r.randint(290, 740)
        if all((x - a) ** 2 + (y - b) ** 2 > 78 ** 2 for a, b in pts): pts.append((x, y))
    c0 = (int(r.choice([600, 960, 1300])), 470); pts[0] = c0
    order = sorted(range(n), key=lambda i: (pts[i][0] - c0[0]) ** 2 + (pts[i][1] - c0[1]) ** 2); rank = {i: k for k, i in enumerate(order)}
    edges = set()
    for i in range(n):
        for j in sorted(range(n), key=lambda j: (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2)[1:4]: edges.add((min(i, j), max(i, j)))
    total_t = max(2.5, min(dur * .8, 5.5)); frac = ease_io(t / total_t); inf_n = frac * n
    lay = np.zeros_like(f)
    for i, j in edges:
        both = rank[i] < inf_n and rank[j] < inf_n
        cv2.line(lay, pts[i], pts[j], col(RED, .85) if both else (50, 66, 96), 2 if both else 1, AA)
        if both:
            q = (t * 1.3 + (i * 7 + j) % 10 / 10) % 1; px = int(pts[i][0] + (pts[j][0] - pts[i][0]) * q); py = int(pts[i][1] + (pts[j][1] - pts[i][1]) * q)
            cv2.circle(lay, (px, py), 4, WHITE, -1, AA)
    for i, (x, y) in enumerate(pts):
        if rank[i] < inf_n:
            age = (inf_n - rank[i]) / 6.0; pr = int(11 + 4 * math.sin(t * 5 + i))
            cv2.circle(lay, (x, y), pr, RED, -1, AA)
            if age < 1: cv2.circle(lay, (x, y), int(14 + 70 * age), col(RED, 1 - age), 3, AA)
        else: cv2.circle(lay, (x, y), 8, CYAN, -1, AA); cv2.circle(lay, (x, y), 15, col(CYAN, .35), 1, AA)
    f = cv2.add(f, lay); f = bloom(f)
    total = D(spec, "total"); big = txt_of(spec)
    if total:
        try: tv = float(str(total).replace(",", "")); shown = f"{int(tv * frac):,}"
        except ValueError: shown = str(total)
        T.add((W // 2, 150), shown, DISP(120), WHITE, "mm", ease(t / .4), 6)
        T.add((W // 2, 228), (big or "SYSTEMS HIT").upper(), BOLD(38), RED, "mm", ease((t - .2) / .4), 4)
    elif big: T.add((W // 2, 170), big.upper(), DISP(64), WHITE, "mm", ease(t / .4), 6)
    label(T, spec, t); return T.apply(camera(f, t, dur))

# ---------------------------------------------------------------------------------- globe with attack arcs
def _sph(lat, lon, yaw, R):
    la, lo = math.radians(lat), math.radians(lon) + yaw
    x, y, z = math.cos(la) * math.sin(lo), -math.sin(la), math.cos(la) * math.cos(lo)
    return x * R, y * R, z

def globe(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); R = 350; cx, cy = W // 2, 450
    pins = []
    d0 = spec.get("data")
    for p in (d0 if isinstance(d0, list) else D(spec, "points", [])) or []:
        try: pins.append((str(p[0]), float(p[1]), float(p[2])))
        except Exception: pass
    if not pins: pins = [("", 37.5, 127.0)]
    mid = sum(p[2] for p in pins) / len(pins); yaw = -math.radians(mid) + math.sin(t * .35) * .22
    midlat = sum(p[1] for p in pins) / len(pins)
    cv2.circle(lay, (cx, cy), R, (16, 26, 48), -1, AA)
    for q in range(1, 9): cv2.circle(lay, (cx - int(q * 6), cy - int(q * 6)), int(R * (1 - q / 11)), (16 + q * 3, 26 + q * 4, 48 + q * 5), -1, AA)
    cv2.circle(lay, (cx, cy), R, col(acc, .95), 3, AA)
    cv2.circle(lay, (cx, cy), R + 22, col(acc, .25), 1, AA)
    for la in range(-60, 90, 30):
        pts = [_sph(la, lo, yaw, R) for lo in range(-180, 181, 6)]
        for a, b in zip(pts, pts[1:]):
            if a[2] > 0 and b[2] > 0: cv2.line(lay, (int(cx + a[0]), int(cy + a[1])), (int(cx + b[0]), int(cy + b[1])), col(acc, .75), 2, AA)
    for lo in range(-180, 180, 30):
        pts = [_sph(la, lo, yaw, R) for la in range(-90, 91, 6)]
        for a, b in zip(pts, pts[1:]):
            if a[2] > 0 and b[2] > 0: cv2.line(lay, (int(cx + a[0]), int(cy + a[1])), (int(cx + b[0]), int(cy + b[1])), col(acc, .75), 2, AA)
    rr = random.Random(seed_of("globe"))
    for _ in range(420):
        la, lo = math.degrees(math.asin(rr.uniform(-1, 1))), rr.uniform(-180, 180); x, y, z = _sph(la, lo, yaw, R)
        if z > .02: cv2.circle(lay, (int(cx + x), int(cy + y)), 1, col(CYAN, .25 + .6 * z), -1, AA)
    pos = []
    for name, la, lo in pins:
        x, y, z = _sph(la, lo, yaw, R); pos.append((x, y, z))
    for i in range(len(pins) - 1):
        a, b = pins[i], pins[i + 1]; prog = ease_io((t - .5 - i * .9) / 1.6)
        if prog <= 0: continue
        la1, lo1, la2, lo2 = map(math.radians, (a[1], a[2], b[1], b[2]))
        v1 = np.array([math.cos(la1) * math.sin(lo1), -math.sin(la1), math.cos(la1) * math.cos(lo1)]); v2 = np.array([math.cos(la2) * math.sin(lo2), -math.sin(la2), math.cos(la2) * math.cos(lo2)])
        om = math.acos(max(-1, min(1, float(v1 @ v2)))) or 1e-3; prev = None
        for s in np.linspace(0, prog, 40):
            v = (math.sin((1 - s) * om) * v1 + math.sin(s * om) * v2) / math.sin(om); v = v / np.linalg.norm(v) * (1 + .28 * math.sin(math.pi * s) * min(1, om))
            yw = yaw; x0, z0 = v[0], v[2]; xr = x0 * math.cos(yw) + z0 * math.sin(yw); zr = -x0 * math.sin(yw) + z0 * math.cos(yw)
            p = (int(cx + xr * R), int(cy + v[1] * R));
            if prev is not None and zr > -.1: cv2.line(lay, prev, p, RED, 3, AA)
            prev = p
        if prev is not None: cv2.circle(lay, prev, 7, WHITE, -1, AA)
    for (name, la, lo), (x, y, z) in zip(pins, pos):
        if z > 0:
            p = (int(cx + x), int(cy + y)); pul = (t * .9) % 1
            cv2.circle(lay, p, 8, YEL, -1, AA); cv2.circle(lay, p, int(10 + 40 * pul), col(YEL, 1 - pul), 2, AA)
            side = 1 if pins.index((name, la, lo)) % 2 == 0 else -1
            T.add((p[0] + side * 26, p[1] - 34 + (24 if side < 0 else 0)), name.upper(), DISP(40), WHITE, "lm" if side > 0 else "rm", ease((t - .3) / .4), 5)
    f = bloom(cv2.add(f, lay)); big = txt_of(spec)
    if big: T.add((W // 2, 150), big.upper(), DISP(60), WHITE, "mm", ease(t / .4), 6)
    label(T, spec, t); return T.apply(camera(f, t, dur, 1.0, 1.04))

# ---------------------------------------------------------------------------------- rack of screens that go dark
def rack(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); r = random.Random(seed_of(txt_of(spec) or "rack") + seed)
    cols, rows, cw, ch, gap = 11, 5, 132, 86, 22; x0 = (W - (cols * cw + (cols - 1) * gap)) // 2; y0 = 205
    origin = (r.randint(0, cols - 1), r.randint(0, rows - 1)); start = .7; spreadT = max(2.2, min(dur * .75, 4.5))
    items = []
    for ry in range(rows):
        for cx_ in range(cols): items.append((math.hypot(cx_ - origin[0], (ry - origin[1]) * 1.3), cx_, ry))
    mx = max(i[0] for i in items); dead = 0
    for dist, cx_, ry in items:
        x, y = x0 + cx_ * (cw + gap), y0 + ry * (ch + gap); tt = t - start - dist / mx * spreadT
        if tt < 0: c_body, c_scr, glow = (26, 34, 52), (18, 70, 90), CYAN
        elif tt < .5: c_body, c_scr, glow = (60, 20, 26), col(RED, .9 if int(tt * 20) % 2 == 0 else .35), RED
        else: c_body, c_scr, glow = (22, 18, 22), (6, 6, 10), (60, 30, 40); dead += 1
        cv2.rectangle(f, (x, y), (x + cw, y + ch), c_body, -1); cv2.rectangle(f, (x + 7, y + 7), (x + cw - 7, y + ch - 14), c_scr, -1)
        if tt < 0:
            for k in range(3): cv2.line(f, (x + 14, y + 20 + k * 16), (x + 14 + r.randint(30, 90), y + 20 + k * 16), col(CYAN, .6), 2, AA)
        elif tt >= .5: cv2.line(f, (x + 7, y + 7), (x + cw - 7, y + ch - 14), (40, 14, 20), 2, AA)
        cv2.rectangle(f, (x, y), (x + cw, y + ch), col(glow, .55 if tt < .5 else .12), 1, AA)
        cv2.rectangle(f, (x + cw // 2 - 22, y + ch - 7), (x + cw // 2 + 22, y + ch - 3), (70, 80, 100), -1)
    f = bloom(f, .4); total = D(spec, "total"); big = txt_of(spec)
    n = rows * cols
    if total:
        try: tv = float(str(total).replace(",", "")); shown = f"{int(tv * dead / n):,}"
        except ValueError: shown = str(total)
        T.add((W // 2, 112), shown, DISP(76), WHITE if dead < n else RED, "mm", ease(t / .4), 6)
    if big: T.add((W // 2, 648 + 140 if False else 790), big.upper(), DISP(40), RED if dead > 3 else WHITE, "mm", ease(t / .4), 5)
    return T.apply(camera(f, t, dur, 1.0, 1.03))

# ---------------------------------------------------------------------------------- terminal
def terminal(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); raw = txt_of(spec)
    lines = [l.strip() for l in re.split(r"\n|;|\|", raw) if l.strip()] or ["..."]
    lines = [("> " if not l.startswith((">", "$", "#")) else "") + l for l in lines][:8]
    r = random.Random(seed_of(raw) + 5)
    for c_ in range(0, W, 46):                                             # falling hex column hints behind the window
        y0 = (r.randint(0, H) + t * r.randint(40, 110)) % (H + 300) - 300
        for k in range(9): cv2.putText(f, r.choice("0123456789ABCDEF"), (c_, int(y0 + k * 28)), cv2.FONT_HERSHEY_PLAIN, 1.5, col(GREEN, .10 + .25 * k / 9), 1, AA)
    x0, y0, x1, y1 = 300, 170, 1620, 780
    alpha_rect(f, (x0, y0), (x1, y1), (4, 8, 12), .93); cv2.rectangle(f, (x0, y0), (x1, y1), col(acc, .95), 2, AA)
    cv2.rectangle(f, (x0, y0), (x1, y0 + 58), (22, 28, 38), -1)
    for i, c_ in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))): cv2.circle(f, (x0 + 34 + i * 40, y0 + 29), 10, c_, -1, AA)
    T.add(((x0 + x1) // 2, y0 + 29), "terminal", MONO(24), (150, 160, 175), "mm")
    budget, y = int(max(0, t - .3) * 34), y0 + 120; shown_last = ""
    for ln in lines:
        seg = ln[:max(0, budget)]; budget -= len(ln) + 8
        T.add((x0 + 46, y), seg, MONOB(54), (70, 255, 140), "la"); y += 86
        if budget < 0:
            if int(t * 2.4) % 2 == 0: cv2.rectangle(f, (x0 + 50 + int(MONOB(54).getlength(seg)), y - 80), (x0 + 50 + int(MONOB(54).getlength(seg)) + 28, y - 30), (70, 255, 140), -1)
            break
    f = bloom(f, .35); label(T, spec, t); return T.apply(camera(f, t, dur))

# ---------------------------------------------------------------------------------- counter (gauge)
def counter(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f)
    txt = txt_of(spec); val = D(spec, "value"); pre = str(D(spec, "prefix", "")); suf = str(D(spec, "suffix", "")); lab = str(D(spec, "label", ""))
    if val is None:
        pn = motion._parse_num(txt)
        if pn: pre, val, _, _, suf = pn; lab = lab or ""
        else: val = 0
    val = float(str(val).replace(",", "")); k = ease_io(t / min(2.2, max(1.2, dur * .6))); cur = val * k
    cx, cy, R = W // 2, 420, 290
    for i in range(120):
        a = i / 120 * 2 * math.pi - math.pi / 2; on = i / 120 <= k
        r0, r1 = R - (34 if i % 5 == 0 else 18), R
        cv2.line(lay, (int(cx + math.cos(a) * r0), int(cy + math.sin(a) * r0)), (int(cx + math.cos(a) * r1), int(cy + math.sin(a) * r1)), col(YEL if on else acc, 1 if on else .35), 4 if i % 5 == 0 else 2, AA)
    ang = k * 360; cv2.ellipse(lay, (cx, cy), (R + 30, R + 30), -90, 0, ang, col(acc, .9), 5, AA)
    ang2 = (t * 40) % 360; cv2.ellipse(lay, (cx, cy), (R - 70, R - 70), 0, ang2, ang2 + 70, col(acc, .5), 3, AA)
    f = bloom(cv2.add(f, lay), .7); s = f"{cur:,.0f}" if val >= 1000 else (f"{cur:.1f}".rstrip("0").rstrip(".") if val != int(val) else f"{int(cur)}")
    big = f"{pre}{s}{(' ' + suf) if suf else ''}".strip(); size = 170
    while DISP(size).getlength(big) > 480 and size > 60: size -= 6
    T.add((cx, cy - 10), big, DISP(size), WHITE, "mm", ease(t / .3), 7)
    if lab or (txt and not motion._parse_num(txt)): T.add((cx, cy + 90), (lab or txt).upper(), BOLD(40), YEL, "mm", ease((t - .5) / .4), 4)
    label(T, spec, t); return T.apply(camera(f, t, dur))

# ---------------------------------------------------------------------------------- timeline
def timeline(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); d0 = spec.get("data"); items = []
    if isinstance(d0, list):
        for it in d0:
            if isinstance(it, dict): items.append((str(it.get("date") or it.get("year") or ""), str(it.get("label") or it.get("text") or "")))
            elif isinstance(it, (list, tuple)) and len(it) >= 2: items.append((str(it[0]), str(it[1])))
            else: items.append(motion._split_item(str(it)))
    else: items = [motion._split_item(p) for p in re.split(r"\s*(?:→|->|\||;|\n)\s*", txt_of(spec)) if p.strip()]
    items = [(a, b) for a, b in items if a or b][:5] or [("", txt_of(spec))]; n = len(items)
    x0, x1, y = 230, 1690, 440; reveal = ease_io(t / min(max(1.5, .8 * n), dur * .85 + .01))
    cv2.line(lay, (x0, y), (int(x0 + (x1 - x0) * reveal), y), WHITE, 5, AA)
    for i, (a, b) in enumerate(items):
        fr_ = i / (n - 1) if n > 1 else .5; x = int(x0 + (x1 - x0) * fr_)
        if n > 1 and reveal + .001 < fr_: continue
        s = ease((t - (.2 + i * min(.9, dur * .8 / n))) / .4) if n > 1 else ease(t / .5)
        if s <= 0: continue
        cv2.circle(lay, (x, y), int(20 * s), acc, -1, AA); cv2.circle(lay, (x, y), int(30 * s), WHITE, 3, AA)
        up = i % 2 == 0
        cv2.line(lay, (x, y + (-30 if up else 30)), (x, y + (-120 if up else 120)), col(acc, .7), 2, AA)
        T.add((x, y + (-160 if up else 160)), a.upper(), DISP(84), YEL, "mm", s, 5)
        ls = wrap(b, BOLD(44), 340)[:3]; base_y = y + (-160 - 86 - 52 * (len(ls) - 1)) if up else y + 160 + 86
        for j, ln in enumerate(ls): T.add((x, base_y + 52 * j), ln, BOLD(44), WHITE, "mm", s, 4)
    f = bloom(cv2.add(f, lay)); label(T, spec, t); return T.apply(camera(f, t, dur, 1.0, 1.04))

# ---------------------------------------------------------------------------------- padlock
def lock(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); state = str(D(spec, "state", "open")); cx, cy = W // 2, 470
    ev = 1.3; k = ease_io((t - ev) / .7)
    body_c = col(acc, .9) if state == "locked" else (col(RED, .95) if state == "crack" else col(acc, .9))
    if state == "locked": body_c = col(GREEN, .9)
    sh_lift = int(k * 70) if state == "open" else 0; sh_ang = int(k * 38) if state == "open" else 0
    shackle_c = body_c
    cv2.ellipse(lay, (cx - sh_ang // 2, cy - 110 - sh_lift), (105, 125), 0, 180, 360, shackle_c, 26, AA)
    cv2.line(lay, (cx + 105 - sh_ang // 2, cy - 110 - sh_lift), (cx + 105 - sh_ang // 2, cy - 60 - sh_lift // 2), shackle_c, 26, AA)
    cv2.line(lay, (cx - 105 - sh_ang // 2, cy - 110 - sh_lift), (cx - 105 - sh_ang // 2, cy - 60), shackle_c, 26, AA)
    rrect(lay, (cx - 190, cy - 70), (cx + 190, cy + 190), body_c, 26)
    cv2.circle(lay, (cx, cy + 55), 36, (8, 10, 18), -1, AA); cv2.rectangle(lay, (cx - 12, cy + 55), (cx + 12, cy + 130), (8, 10, 18), -1)
    if state == "crack" and t > ev:
        r = random.Random(7); x, y = cx - 60, cy - 70
        for seg in range(int(k * 9)):
            nx, ny = x + r.randint(-30, 50), y + r.randint(25, 45); cv2.line(lay, (x, y), (nx, ny), WHITE, 4, AA); x, y = nx, ny
    f = bloom(cv2.add(f, lay), .8)
    if state == "crack" and 0 < t - ev < .25: f = np.clip(f.astype(np.int16) + 60, 0, 255).astype(np.uint8)
    big = txt_of(spec)
    if big: T.add((W // 2, 150), big.upper(), DISP(70), WHITE, "mm", ease(t / .4), 6)
    label(T, spec, t); return T.apply(camera(f, t, dur))

# ---------------------------------------------------------------------------------- phishing email
def email(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); x0, y0, x1, y1 = 340, 150, 1580, 770; s = ease(t / .5)
    off = int((1 - s) * 90); y0 += off; y1 += off
    alpha_rect(f, (x0 - 10, y0 - 10), (x1 + 10, y1 + 10), (0, 0, 0), .45); cv2.rectangle(f, (x0, y0), (x1, y1), (240, 241, 245), -1)
    cv2.rectangle(f, (x0, y0), (x1, y0 + 62), (52, 62, 84), -1)
    for i, c_ in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))): cv2.circle(f, (x0 + 32 + i * 36, y0 + 31), 9, c_, -1, AA)
    T.add((x0 + 150, y0 + 31), "INBOX", BOLD(26), (200, 210, 230), "lm", s)
    fr_ = str(D(spec, "from", "unknown sender")); sub = str(D(spec, "subject", txt_of(spec) or "Important")); line = str(D(spec, "line", ""))
    T.add((x0 + 50, y0 + 100), "FROM", BOLD(24), (110, 118, 140), "la", s); T.add((x0 + 190, y0 + 88), fr_, MED(44), (20, 24, 34), "la", s)
    cv2.line(f, (x0 + 40, y0 + 150), (x1 - 40, y0 + 150), (210, 214, 224), 2)
    T.add((x0 + 50, y0 + 176), "SUBJECT", BOLD(24), (110, 118, 140), "la", s); T.add((x0 + 250, y0 + 160), sub, DISP(46), (20, 24, 34), "la", s)
    r = random.Random(seed_of(sub))
    for i in range(5): cv2.rectangle(f, (x0 + 50, y0 + 270 + i * 40), (x0 + 50 + r.randint(560, 1020), y0 + 284 + i * 40), (190, 195, 207), -1)
    hl = ease((t - 1.0) / .5); ly = y0 + 270 + 5 * 40 + 20
    if line:
        w = int(BOLD(40).getlength(line)) + 40
        cv2.rectangle(f, (x0 + 40, ly), (x0 + 40 + int(w * hl), ly + 66), YEL, -1)
        if hl > .6: T.add((x0 + 60, ly + 33), line, BOLD(40), (10, 10, 12), "lm")
    if t > 1.9:
        k = ease((t - 1.9) / .5); mx, my = int(x0 + 400 + (1 - k) * 500), int(ly + 40 + (1 - k) * 220)
        cv2.fillPoly(f, [np.array([[mx, my], [mx, my + 44], [mx + 12, my + 34], [mx + 30, my + 34]])], (10, 10, 14), AA)
        if t > 2.5:
            pul = ((t - 2.5) * 1.6) % 1; cv2.circle(f, (mx, my), int(14 + 70 * pul), col(RED, 1 - pul), 4, AA)
    label(T, spec, t); return T.apply(camera(bloom(f, .25), t, dur, 1.0, 1.03))

# ---------------------------------------------------------------------------------- money / data flow between nodes
def flow(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); d0 = spec.get("data")
    names = [str(x) for x in (d0 if isinstance(d0, list) else D(spec, "nodes", ["SOURCE", "TARGET"]))][:4] or ["SOURCE", "TARGET"]
    amount = str(D(spec, "amount", "")); blocked = bool(D(spec, "blocked", False)); n = len(names)
    xs = [int(280 + i * (1360 / max(1, n - 1))) if n > 1 else W // 2 for i in range(n)]; y = 440; bw, bh = 340, 160
    for i in range(n - 1):
        a, b = xs[i] + bw // 2, xs[i + 1] - bw // 2; prog = ease_io((t - .4 - i * .9) / 1.3)
        cv2.line(lay, (a, y), (b, y), col(acc, .3), 3, AA)
        if prog > 0:
            e = int(a + (b - a) * prog); cv2.line(lay, (a, y), (e, y), YEL if not (blocked and i == n - 2 and prog >= 1) else RED, 6, AA)
            cv2.circle(lay, (e, y), 11, WHITE, -1, AA)
            for q in range(3):
                px = int(a + (e - a) * ((t * .8 + q / 3) % 1)); cv2.circle(lay, (px, y), 6, YEL, -1, AA)
            if amount and prog > .4: T.add(((a + b) // 2, y - 70), amount, DISP(58), YEL, "mm", min(1, (prog - .4) / .3), 5)
        if blocked and i == n - 2 and prog >= 1:
            mx = (a + b) // 2; k = ease((t - 3.0) / .3)
            if k > 0: cv2.line(lay, (mx - 40, y - 40), (mx + 40, y + 40), RED, int(10 * k) + 1, AA); cv2.line(lay, (mx + 40, y - 40), (mx - 40, y + 40), RED, int(10 * k) + 1, AA)
    for i, nm in enumerate(names):
        s = ease((t - i * .25) / .4); x = xs[i]
        rrect(lay, (x - bw // 2, y - bh // 2), (x + bw // 2, y + bh // 2), (22, 30, 50)); rrect(lay, (x - bw // 2, y - bh // 2), (x + bw // 2, y + bh // 2), col(acc, .95), 18, 3)
        ls = wrap(nm.upper(), DISP(38), bw - 30)[:2]
        for j, ln in enumerate(ls): T.add((x, y + (j - (len(ls) - 1) / 2) * 46), ln, DISP(38), WHITE, "mm", s, 3)
    f = bloom(cv2.add(f, lay)); big = txt_of(spec)
    if big: T.add((W // 2, 160), big.upper(), DISP(60), WHITE, "mm", ease(t / .4), 6)
    label(T, spec, t); return T.apply(camera(f, t, dur))

# ---------------------------------------------------------------------------------- bar chart
def bars(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); d0 = spec.get("data"); items = []
    for it in (d0 if isinstance(d0, list) else D(spec, "items", [])):
        try: items.append((str(it[0]), float(str(it[1]).replace(",", ""))))
        except Exception: pass
    items = items[:6] or [("", 1.0)]; mx = max(v for _, v in items) or 1; unit = str(D(spec, "unit", "")); n = len(items)
    bw = min(190, 1300 // n - 40); gap = 60; tot = n * bw + (n - 1) * gap; x0 = (W - tot) // 2; base_y = 700; maxh = 430
    cv2.line(lay, (x0 - 40, base_y), (x0 + tot + 40, base_y), WHITE, 3, AA)
    for i, (nm, v) in enumerate(items):
        k = ease_io((t - .3 - i * .25) / 1.0); h = int(maxh * v / mx * k); x = x0 + i * (bw + gap); hot = v == mx
        cv2.rectangle(lay, (x, base_y - h), (x + bw, base_y), col(YEL if hot else acc, .95), -1)
        cv2.rectangle(lay, (x, base_y - h), (x + bw, base_y - h + 6), WHITE, -1)
        T.add((x + bw // 2, base_y + 46), nm.upper(), BOLD(36), WHITE, "mm", min(1, k * 2), 3)
        sv = f"{v * k:,.0f}" if v >= 100 else f"{v * k:.1f}".rstrip("0").rstrip(".")
        T.add((x + bw // 2, base_y - h - 36), sv + unit, DISP(56), YEL if hot else WHITE, "mm", min(1, k * 2), 4)
    f = bloom(cv2.add(f, lay), .5); big = txt_of(spec)
    if big: T.add((W // 2, 150), big.upper(), DISP(60), WHITE, "mm", ease(t / .4), 6)
    label(T, spec, t); return T.apply(camera(f, t, dur, 1.0, 1.03))

# ---------------------------------------------------------------------------------- dossier (who is behind it)
def dossier(spec, t, dur, acc, seed):
    f = base(t, acc, seed); T = Text(); lay = np.zeros_like(f); ttl = txt_of(spec) or str(D(spec, "title", "UNKNOWN ACTOR"))
    rows = [(str(a), str(b)) for a, b in (D(spec, "rows", []) or [])][:5]; s = ease(t / .5)
    px, py = 390, 440
    pts = np.array([[px + int(cx_ * 230), py + int(cy_ * 230)] for cx_, cy_ in ((math.cos(a), math.sin(a)) for a in [i * math.pi / 3 for i in range(6)])])
    cv2.fillPoly(lay, [pts], (16, 24, 40), AA); cv2.polylines(lay, [pts], True, col(acc, .95), 4, AA)
    cv2.circle(lay, (px, py - 40), 62, col(acc, .55), -1, AA); cv2.ellipse(lay, (px, py + 150), (130, 140), 0, 180, 360, col(acc, .55), -1, AA)
    sy = py - 200 + int(((t * .9) % 1) * 400); cv2.line(lay, (px - 190, sy), (px + 190, sy), GREEN, 3, AA)
    T.add((px, py + 290), "IDENTITY UNCONFIRMED" if not rows else "PROFILE", BOLD(26), (150, 160, 180), "mm", s)
    T.add((760, 200), ttl.upper(), DISP(92), WHITE, "lm", s, 6); cv2.rectangle(lay, (760, 250), (760 + int(560 * s), 256), YEL, -1)
    for i, (a, b) in enumerate(rows):
        k = ease((t - .6 - i * .45) / .35); y = 330 + i * 92
        T.add((760, y), a.upper(), BOLD(36), YEL, "lm", k, 3); T.add((1060, y), b, MED(50), WHITE, "lm", k, 3)
        cv2.line(lay, (760, y + 36), (760 + int(900 * k), y + 36), col(acc, .35), 2, AA)
    f = bloom(cv2.add(f, lay)); label(T, spec, t); return T.apply(camera(f, t, dur, 1.0, 1.03))

# ---------------------------------------------------------------------------------- reuse overlay cards on the studio background
def _card(kind):
    def fn(spec, t, dur, acc, seed):
        f = base(t, acc, seed); T = Text(); res = motion.draw(kind, spec, t, max(dur, 4.0), acc)
        if res:
            img, (x, y) = res; w, h = img.size; sc = min(1.6, 660 / h, 1700 / w)
            if abs(sc - 1) > .02: img = img.resize((int(w * sc), int(h * sc)), Image.LANCZOS)
            x = int((W - img.width) / 2); y = max(100, min(int((800 - img.height) / 2 + 40), 800 - img.height))
            lay = Image.fromarray(f).convert("RGBA"); lay.alpha_composite(img, (x, y)); f = np.asarray(lay.convert("RGB")).copy()
        return camera(bloom(f, .25), t, dur, 1.0, 1.03)
    return fn

KINDS = {"network": network, "globe": globe, "rack": rack, "terminal": terminal, "counter": counter, "timeline": timeline, "lock": lock,
         "email": email, "flow": flow, "bars": bars, "dossier": dossier,
         "headline": _card("headline"), "quote": _card("quote"), "redact": _card("redact"), "doc": _card("doc_callout")}
LEN = {"network": 5.5, "globe": 5.5, "rack": 5.5, "terminal": 5.0, "counter": 4.5, "timeline": 6.0, "lock": 4.0, "email": 4.5, "flow": 5.0, "bars": 4.5,
       "dossier": 5.0, "headline": 4.0, "quote": 5.0, "redact": 4.5, "doc": 4.5}

def render(kind, spec, t, dur, acc, seed=1):
    fn = KINDS.get(kind)
    try:
        if fn: return np.ascontiguousarray(fn(spec, t, dur, acc, seed))
    except Exception as e:
        print("gfx error", kind, repr(e)[:120])
    return base(t, acc, seed)
