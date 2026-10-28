"""Animated motion-graphic overlays (all drawn procedurally — no external assets).
Each drawer: fn(spec, t, dur, acc) -> (PIL.Image RGBA, (x, y)) or None.  t = seconds since the overlay appeared.
Canvas coordinate system is 1920x1080.
"""
import math, os, random, re, hashlib
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "..", "assets", "fonts")
YEL, WHITE, INK = (255, 212, 0), (255, 255, 255), (8, 10, 16)
_F, _CACHE = {}, {}

def F(name, size):
    k = (name, size)
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(FD, name), size)
    return _F[k]
def DISP(s): return F("InterDisplay-Black.otf", s)
def BOLD(s): return F("Inter-Bold.otf", s)
def MED(s): return F("Inter-Medium.otf", s)
def MONO(s): return F("DejaVuSansMono.ttf", s)
def MONOB(s): return F("DejaVuSansMono-Bold.ttf", s)

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0.0, min(1.0, x)); return 3 * x * x - 2 * x ** 3
def seed_of(s): return int(hashlib.md5(str(s).encode()).hexdigest()[:8], 16)

def wrap(text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if font.getlength(trial) <= maxw or not cur: cur = trial
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def _txt(spec):
    t = spec.get("text") or ""
    d = spec.get("data")
    if not t and isinstance(d, str): t = d
    if not t and isinstance(d, dict): t = str(d.get("text") or d.get("label") or d.get("value") or "")
    return str(t)

def _shadow_text(d, xy, text, font, fill, anchor="la", stroke=6):
    d.text(xy, text, font=font, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 255))

# ------------------------------------------------------------------ title (lower third)
def title(spec, t, dur, acc):
    txt = _txt(spec); parts = [p.strip() for p in re.split(r"\s*[·|•]\s*", txt) if p.strip()]
    big = parts[0] if parts else ""; small = "  ·  ".join(parts[1:])
    img = Image.new("RGBA", (1200, 170), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    s = ease(t / 0.55); wbox = int(1150 * s)
    d.rectangle((0, 18, wbox, 160), fill=(6, 8, 14, 215)); d.rectangle((0, 18, 12, 160), fill=acc + (255,))
    if s > .35:
        d.text((40, 30), big.upper(), font=DISP(56), fill=WHITE + (255,))
        if small: d.text((40, 100), small.upper(), font=BOLD(32), fill=YEL + (255,))
    return img, (70 - int((1 - s) * 80), 610)

# ------------------------------------------------------------------ counter
def _parse_num(txt):
    m = re.search(r"([^\d\-]*?)(\d[\d,]*\.?\d*)(.*)", txt)
    if not m: return None
    pre, num, suf = m.group(1).strip(), m.group(2), m.group(3).strip()
    try: val = float(num.replace(",", ""))
    except ValueError: return None
    return pre, val, ("," in num), (len(num.split(".")[1]) if "." in num else 0), suf

def counter(spec, t, dur, acc):
    d0 = spec.get("data") if isinstance(spec.get("data"), dict) else {}
    txt = _txt(spec)
    if "value" in d0:
        pre, val, comma, dec, suf = str(d0.get("prefix", "")), float(d0["value"]), True, 0, str(d0.get("suffix", ""))
        label = str(d0.get("label", txt))
    else:
        pn = _parse_num(txt)
        if not pn: return quote(spec, t, dur, acc)
        pre, val, comma, dec, suf = pn; label = ""
        m = re.match(r"([^\d\-]*?)(\d[\d,]*\.?\d*)(.*)", txt)
        if suf and len(suf.split()) > 1: label = " ".join(suf.split()[1:]); suf = suf.split()[0]
    k = ease_io(t / 1.7); cur = val * k
    s = (f"{cur:,.{dec}f}" if comma else f"{cur:.{dec}f}")
    big = f"{pre}{s}{(' ' + suf) if suf else ''}".strip()
    img = Image.new("RGBA", (1700, 420), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    size = 250
    while DISP(size).getlength(big) > 1600 and size > 90: size -= 10
    pulse = 1 + (0.025 * math.sin(t * 9) if k >= 1 else 0)
    f = DISP(int(size * pulse))
    _shadow_text(d, (850, 170), big, f, YEL + (255,), "mm", 9)
    if label:
        _shadow_text(d, (850, 340), label.upper(), BOLD(54), WHITE + (255,), "mm", 5)
        d.rectangle((850 - 120, 385, 850 + 120, 392), fill=acc + (255,))
    return img, ((W - 1700) // 2, 230)

# ------------------------------------------------------------------ quote
def quote(spec, t, dur, acc):
    txt = _txt(spec); attr = ""
    if " — " in txt: txt, attr = txt.rsplit(" — ", 1)
    elif " - " in txt and txt.count(" - ") == 1: txt, attr = txt.split(" - ")
    txt = txt.strip().strip('"“”')
    f = BOLD(70 if len(txt) < 90 else 58); lines = wrap(txt, f, 1300)
    shown = int(len(txt) * min(1.0, t / max(0.8, len(txt) / 42)))
    img = Image.new("RGBA", (1500, 140 + 88 * len(lines) + 90), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.text((10, -50), "“", font=DISP(330), fill=acc + (255,))
    y, used = 120, 0
    for ln in lines:
        part = ln[:max(0, shown - used)]; used += len(ln) + 1
        _shadow_text(d, (130, y), part, f, WHITE + (255,), "la", 6); y += 88
    if attr and shown >= len(txt): _shadow_text(d, (130, y + 10), "— " + attr.upper(), BOLD(40), YEL + (255,), "la", 5)
    return img, ((W - 1500) // 2, (H - img.height) // 2 - 60)

# ------------------------------------------------------------------ headline (breaking-news card)
def headline(spec, t, dur, acc):
    txt = _txt(spec); key = ("hl", txt)
    if key not in _CACHE:
        f = DISP(76); lines = wrap(txt.upper(), f, 1080)[:4]
        h = 170 + 92 * len(lines)
        card = Image.new("RGBA", (1240, h + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
        d.rectangle((10, 10, 1230, h + 30), fill=(0, 0, 0, 120)); d.rectangle((0, 0, 1220, h), fill=(244, 241, 232, 255))
        d.rectangle((0, 0, 1220, 78), fill=(190, 20, 30, 255)); d.text((40, 39), "BREAKING", font=DISP(46), fill=WHITE + (255,), anchor="lm")
        for i in range(3): d.rectangle((1010 + i * 60, 28, 1050 + i * 60, 50), fill=(255, 255, 255, 220))
        y = 110
        for ln in lines: d.text((50, y), ln, font=f, fill=(15, 15, 18, 255)); y += 92
        d.rectangle((50, h - 30, 1170, h - 26), fill=(15, 15, 18, 255))
        _CACHE[key] = card.rotate(-2.2, resample=Image.BICUBIC, expand=True)
    card = _CACHE[key]; s = ease(t / 0.5)
    return card, ((W - card.width) // 2, int((H - card.height) // 2 + (1 - s) * 360))

# ------------------------------------------------------------------ doc_callout
def doc_callout(spec, t, dur, acc):
    txt = _txt(spec); key = ("doc", txt)
    if key not in _CACHE:
        pg = Image.new("RGBA", (820, 980), (0, 0, 0, 0)); d = ImageDraw.Draw(pg); rnd = random.Random(seed_of(txt))
        d.rectangle((14, 14, 810, 970), fill=(0, 0, 0, 110)); d.rectangle((0, 0, 800, 956), fill=(238, 238, 232, 255))
        d.rectangle((50, 54, 330, 70), fill=(60, 60, 70, 255))
        y = 120
        for i in range(17):
            w = rnd.randint(380, 700); d.rectangle((50, y, 50 + w, y + 13), fill=(160, 160, 170, 255)); y += 40
            if i == 7: d.rectangle((50, y, 750, y + 2), fill=(210, 210, 215, 255))
        _CACHE[key] = pg.rotate(2.0, resample=Image.BICUBIC, expand=True)
    pg = _CACHE[key]; s = ease(t / 0.5)
    img = Image.new("RGBA", (1900, 1000), (0, 0, 0, 0)); img.paste(pg, (560, 10), pg)
    d = ImageDraw.Draw(img); sweep = ease((t - 0.5) / 0.6)
    f = MONOB(44); lines = wrap(txt, f, 700)[:3]; hh = 20 + 62 * len(lines)
    ty = 400
    d.rectangle((600, ty, 600 + int(780 * sweep), ty + hh), fill=YEL + (255,))
    if sweep > .6:
        yy = ty + 12
        for ln in lines: d.text((620, yy), ln, font=f, fill=(10, 10, 12, 255)); yy += 62
    if sweep > .9:
        r = int(14 * math.sin(t * 8) ** 2); d.rounded_rectangle((590 - r, ty - 10 - r, 1390 + r, ty + hh + 10 + r), 14, outline=acc + (255,), width=6)
    return img, (10, 40 + int((1 - s) * 500))

# ------------------------------------------------------------------ network
def network(spec, t, dur, acc):
    txt = _txt(spec); r = random.Random(seed_of(txt or "net")); n = 62
    pts = [(r.randint(60, 1560), r.randint(60, 700)) for _ in range(n)]
    pts[0] = (780, 380)
    order = sorted(range(n), key=lambda i: (pts[i][0] - 780) ** 2 + (pts[i][1] - 380) ** 2)
    rank = {i: k for k, i in enumerate(order)}
    edges = []
    for i in range(n):
        near = sorted(range(n), key=lambda j: (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2)[1:3]
        edges += [(i, j) for j in near]
    img = Image.new("RGBA", (1620, 760), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    spread = ease_io(t / 3.2) * n
    for i, j in edges:
        inf = rank[i] < spread and rank[j] < spread
        d.line([pts[i], pts[j]], fill=(acc + (190,) if inf else (120, 135, 160, 70)), width=3 if inf else 1)
    for i, (x, y) in enumerate(pts):
        if rank[i] < spread:
            rr = 9 + int(3 * math.sin(t * 6 + i)); d.ellipse((x - rr * 2, y - rr * 2, x + rr * 2, y + rr * 2), fill=acc + (45,))
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=acc + (255,))
        else: d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(170, 185, 210, 200))
    if txt: _shadow_text(d, (810, 28), txt.upper(), BOLD(42), WHITE + (255,), "mm", 5)
    return img, ((W - 1620) // 2, 120)

# ------------------------------------------------------------------ map -> location lock HUD
def map_(spec, t, dur, acc):
    txt = _txt(spec); r = random.Random(seed_of(txt or "map"))
    img = Image.new("RGBA", (1500, 800), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    for gx in range(0, 1500, 75): d.line([(gx, 0), (gx, 800)], fill=(120, 150, 190, 60), width=1)
    for gy in range(0, 800, 75): d.line([(0, gy), (1500, gy)], fill=(120, 150, 190, 60), width=1)
    cx, cy = r.randint(450, 1050), r.randint(280, 520); s = ease(t / 0.9)
    x1, y1 = int(cx * s + 750 * (1 - s)), int(cy * s + 400 * (1 - s))
    d.line([(x1, 0), (x1, 800)], fill=acc + (190,), width=2); d.line([(0, y1), (1500, y1)], fill=acc + (190,), width=2)
    for k in range(3):
        ph = ((t * 0.8 + k / 3) % 1.0); rr = int(30 + 170 * ph); a = int(200 * (1 - ph))
        d.ellipse((x1 - rr, y1 - rr, x1 + rr, y1 + rr), outline=acc + (a,), width=4)
    d.ellipse((x1 - 14, y1 - 14, x1 + 14, y1 + 14), fill=acc + (255,)); d.ellipse((x1 - 5, y1 - 5, x1 + 5, y1 + 5), fill=WHITE + (255,))
    if s > .8 and txt:
        f = DISP(54); w = int(f.getlength(txt.upper())) + 60; bx = min(max(x1 + 40, 10), 1490 - w)
        d.rectangle((bx, y1 - 110, bx + w, y1 - 40), fill=(6, 8, 14, 230)); d.rectangle((bx, y1 - 110, bx + 8, y1 - 40), fill=acc + (255,))
        d.text((bx + 30, y1 - 75), txt.upper(), font=f, fill=WHITE + (255,), anchor="lm")
    for x, y in ((0, 0), (1500, 0), (0, 800), (1500, 800)):
        d.rectangle((x - (60 if x else 0), y - (4 if y else 0), x + (0 if x else 60), y + (0 if y else 4)), fill=acc + (255,))
    return img, ((W - 1500) // 2, 130)

# ------------------------------------------------------------------ terminal
def terminal(spec, t, dur, acc):
    txt = _txt(spec); raw = [l.strip() for l in re.split(r"\n|;|\|", txt) if l.strip()] or ["..."]
    lines = [("> " if not l.startswith((">", "$", "#")) else "") + l for l in raw][:7]
    img = Image.new("RGBA", (1300, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    d.rounded_rectangle((10, 10, 1290, 640), 18, fill=(0, 0, 0, 120)); d.rounded_rectangle((0, 0, 1280, 620), 18, fill=(7, 11, 16, 245), outline=acc + (255,), width=3)
    d.rounded_rectangle((0, 0, 1280, 62), 18, fill=(22, 28, 38, 255)); d.rectangle((0, 40, 1280, 62), fill=(22, 28, 38, 255))
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))): d.ellipse((26 + i * 38, 20, 46 + i * 38, 40), fill=c + (255,))
    d.text((640, 31), "terminal", font=MONO(24), fill=(150, 160, 175, 255), anchor="mm")
    cps, budget, y = 30, int(t * 30), 100
    for ln in lines:
        seg = ln[:max(0, budget)]; budget -= len(ln) + 6
        d.text((40, y), seg, font=MONOB(42), fill=(70, 255, 140, 255)); y += 70
        if budget < 0:
            if int(t * 2.2) % 2 == 0: d.rectangle((44 + MONOB(42).getlength(seg), y - 66, 44 + MONOB(42).getlength(seg) + 24, y - 20), fill=(70, 255, 140, 255))
            break
    return img, ((W - 1300) // 2, 190)

# ------------------------------------------------------------------ redact
def redact(spec, t, dur, acc):
    txt = _txt(spec) or "CLASSIFIED"; key = ("red", txt)
    if key not in _CACHE:
        rnd = random.Random(seed_of(txt)); pg = Image.new("RGBA", (1180, 700), (0, 0, 0, 0)); d = ImageDraw.Draw(pg)
        d.rectangle((14, 14, 1170, 690), fill=(0, 0, 0, 110)); d.rectangle((0, 0, 1156, 666), fill=(236, 235, 228, 255))
        words = ("SUBJECT LOCATION ACCESS SYSTEM RECORDS ACCOUNT NETWORK TRANSFER SERVER FILES USER AUTHORIZED TARGET PAYLOAD "
                 "REPORT INTERNAL CONFIDENTIAL").split()
        y = 60
        for i in range(9):
            x = 50
            while x < 1000:
                w_ = rnd.choice(words); wd = int(MONO(34).getlength(w_)); d.text((x, y), w_, font=MONO(34), fill=(30, 30, 36, 255)); x += wd + 22
            y += 62
        _CACHE[key] = pg
    pg = _CACHE[key].copy(); d = ImageDraw.Draw(pg); rnd = random.Random(seed_of(txt) + 1)
    for i in range(9):
        k = ease_io((t - 0.25 - i * 0.12) / 0.45)
        if k > 0:
            x0 = rnd.randint(40, 300); w = int(rnd.randint(380, 880) * k); d.rectangle((x0, 55 + i * 62, x0 + w, 55 + i * 62 + 44), fill=(8, 8, 10, 255))
    st = ease((t - 1.4) / 0.25)
    if st > 0:
        stamp = Image.new("RGBA", (900, 220), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
        sd.rounded_rectangle((8, 8, 892, 212), 16, outline=(210, 30, 40, 255), width=14); sd.text((450, 112), txt.upper()[:18], font=DISP(110), fill=(210, 30, 40, 255), anchor="mm")
        stamp = stamp.rotate(-9, resample=Image.BICUBIC, expand=True); sc = 1.9 - 0.9 * st
        stamp = stamp.resize((int(stamp.width * sc), int(stamp.height * sc)))
        pg.paste(stamp, (590 - stamp.width // 2, 340 - stamp.height // 2), stamp)
    return pg, ((W - 1180) // 2, 190)

# ------------------------------------------------------------------ timeline
def _split_item(p):
    p = p.strip()
    if ":" in p and len(p.split(":", 1)[0]) <= 20: a, b = p.split(":", 1); return a.strip(), b.strip()
    return "", p

def timeline(spec, t, dur, acc):
    d0 = spec.get("data"); items = []
    if isinstance(d0, list):
        for it in d0:
            if isinstance(it, dict):
                items.append((str(it.get("date") or it.get("year") or it.get("when") or ""), str(it.get("label") or it.get("text") or it.get("event") or "")))
            else: items.append(_split_item(str(it)))
    else:
        items = [_split_item(p) for p in re.split(r"\s*(?:→|->|\||;|\n)\s*", _txt(spec)) if p.strip()]
    items = [(a, b) for a, b in items if a or b][:6] or [("", _txt(spec))]
    n = len(items); img = Image.new("RGBA", (1720, 560), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x0, x1, y = 120, 1600, 280; reveal = ease_io(t / (0.5 + 0.55 * n))
    d.line([(x0, y), (x0 + (x1 - x0) * reveal, y)], fill=WHITE + (235,), width=6)
    for i, (a, b) in enumerate(items):
        frac = i / (n - 1) if n > 1 else 0.5; x = x0 + (x1 - x0) * frac
        if n > 1 and reveal + 0.001 < frac: continue
        s = ease((t - (0.15 + i * 0.5)) / 0.4) if n > 1 else ease(t / 0.5)
        if s <= 0: continue
        rr = int(18 * s); d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=acc + (255,), outline=WHITE + (255,), width=4)
        up = (i % 2 == 0); al = int(255 * s)
        if a: _shadow_text(d, (x, y - 70 if up else y + 62), a.upper(), DISP(60), YEL + (al,), "mm", 5)
        lines = wrap(b, BOLD(36), 340)[:3]
        base = (y - 70 - 52 - 44 * (len(lines) - 1)) if up else (y + 62 + 52)
        if not a: base = (y - 60 - 44 * (len(lines) - 1)) if up else (y + 60)
        for j, ln in enumerate(lines): _shadow_text(d, (x, base + 44 * j), ln, BOLD(36), WHITE + (al,), "mm", 4)
    return img, ((W - 1720) // 2, 170)

DRAWERS = {"title": title, "counter": counter, "quote": quote, "headline": headline, "doc_callout": doc_callout,
           "network": network, "map": map_, "terminal": terminal, "redact": redact, "timeline": timeline}

def draw(kind, spec, t, dur, acc):
    fn = DRAWERS.get(kind)
    if not fn: return None
    try: return fn(spec, t, dur, acc)
    except Exception as e:           # never let one graphic kill an episode
        print("motion error", kind, e); return None
