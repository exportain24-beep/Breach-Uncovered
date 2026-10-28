"""Procedural 1280x720 thumbnail generator for Breach Uncovered (no stock images needed).
Usage: python3 tools/thumbnail.py meta.json out.jpg
meta: {"line1","line2","tag","year","episode","category"}  (line2 is drawn in the accent colour)
"""
import json, math, random, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

W, H = 1280, 720
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "assets", "fonts")
def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), size)

ACCENT = {  # category -> (accent, glow)
    "state": (255, 59, 48), "espionage": (0, 200, 255), "infra": (255, 176, 0), "finance": (46, 230, 140),
    "ransomware": (255, 59, 48), "breach": (255, 120, 40), "profile": (190, 110, 255),
    "malware": (120, 255, 90), "vuln": (255, 210, 0), "hacker": (0, 200, 255)}

def bg(rng, accent):
    img = Image.new("RGB", (W, H), (6, 8, 14))
    px = ImageDraw.Draw(img)
    # radial glow behind the icon area (right side)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse((660, -40, 1400, 760), fill=tuple(int(c * .55) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(150))
    img = ImageChops.add(img, glow)
    # faint hex "matrix"
    d = ImageDraw.Draw(img, "RGBA"); f = font("Inter-Medium.otf", 15)
    for x in range(8, W, 22):
        for y in range(rng.randint(0, 20), H, 24):
            if rng.random() < .55:
                d.text((x, y), rng.choice("0123456789ABCDEF"), font=f, fill=(accent[0], accent[1], accent[2], rng.randint(8, 34)))
    # scanlines
    for y in range(0, H, 4): d.line([(0, y), (W, y)], fill=(0, 0, 0, 38))
    return img

def icon(d, cat, cx, cy, s, col):
    """Bold geometric icon, ~s px tall, centred on (cx,cy)."""
    w = max(8, s // 14)
    if cat in ("breach", "ransomware", "finance_lock"):      # broken padlock
        bw, bh = s * .62, s * .5
        d.rounded_rectangle((cx - bw/2, cy - bh/2 + s*.14, cx + bw/2, cy + bh/2 + s*.14), s*.06, fill=col)
        d.arc((cx - bw*.36, cy - s*.5, cx + bw*.36, cy + s*.1), 180, 360, fill=col, width=w*2)
        d.line([(cx - bw*.36, cy - s*.2), (cx - bw*.36, cy - s*.02)], fill=col, width=w*2)
        d.ellipse((cx - s*.06, cy + s*.04, cx + s*.06, cy + s*.16), fill=(6, 8, 14))
        d.rectangle((cx - s*.025, cy + s*.12, cx + s*.025, cy + s*.3), fill=(6, 8, 14))
        d.polygon([(cx - s*.05, cy - s*.5), (cx + s*.02, cy - s*.18), (cx - s*.06, cy - s*.16), (cx + s*.06, cy + s*.2)], fill=(6, 8, 14))
    elif cat == "infra":                                       # lightning bolt
        p = [(.1,-.5),(-.28,.06),(-.02,.06),(-.14,.5),(.3,-.12),(.04,-.12),(.1,-.5)]
        d.polygon([(cx + x*s, cy + y*s) for x, y in p], fill=col)
    elif cat in ("espionage",):                                # eye
        d.ellipse((cx - s*.55, cy - s*.26, cx + s*.55, cy + s*.26), outline=col, width=w)
        d.ellipse((cx - s*.2, cy - s*.2, cx + s*.2, cy + s*.2), fill=col)
        d.ellipse((cx - s*.07, cy - s*.07, cx + s*.07, cy + s*.07), fill=(6, 8, 14))
    elif cat == "finance":                                     # coin with $
        d.ellipse((cx - s*.42, cy - s*.42, cx + s*.42, cy + s*.42), outline=col, width=w)
        f = font("InterDisplay-Black.otf", int(s*.62)); d.text((cx, cy), "$", font=f, fill=col, anchor="mm")
    elif cat in ("malware",):                                  # virus
        d.ellipse((cx - s*.26, cy - s*.26, cx + s*.26, cy + s*.26), fill=col)
        for a in range(0, 360, 45):
            x1, y1 = cx + math.cos(math.radians(a))*s*.26, cy + math.sin(math.radians(a))*s*.26
            x2, y2 = cx + math.cos(math.radians(a))*s*.48, cy + math.sin(math.radians(a))*s*.48
            d.line([(x1, y1), (x2, y2)], fill=col, width=w*2); d.ellipse((x2-w*1.6, y2-w*1.6, x2+w*1.6, y2+w*1.6), fill=col)
    elif cat in ("profile", "hacker"):                         # hooded figure
        d.ellipse((cx - s*.2, cy - s*.46, cx + s*.2, cy - s*.06), fill=col)
        d.pieslice((cx - s*.5, cy - s*.12, cx + s*.5, cy + s*.9), 180, 360, fill=col)
        d.ellipse((cx - s*.11, cy - s*.34, cx + s*.11, cy - s*.12), fill=(6, 8, 14))
    else:                                                      # shield (state / vuln)
        p = [(0,-.5),(.4,-.34),(.38,.1),(0,.5),(-.38,.1),(-.4,-.34)]
        d.polygon([(cx + x*s, cy + y*s) for x, y in p], outline=col, fill=None, width=w)
        d.line([(cx - s*.16, cy - s*.02), (cx - s*.03, cy + s*.12), (cx + s*.2, cy - s*.14)], fill=col, width=w)

def glitch_text(img, xy, text, f, fill, shift=5):
    """Chromatic-aberration text with a hard black stroke."""
    x, y = xy
    for dx, c in ((-shift, (0, 230, 255)), (shift, (255, 40, 90))):
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(layer).text((x + dx, y), text, font=f, fill=c + (170,))
        img.paste(layer, (0, 0), layer)
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=f, fill=fill, stroke_width=7, stroke_fill=(0, 0, 0))
    d.text((x, y), text, font=f, fill=fill)

def fit(text, name, max_w, start, minimum=70):
    s = start
    while s > minimum and font(name, s).getlength(text) > max_w: s -= 4
    return font(name, s)

def make(meta, out):
    cat = meta.get("category", "state"); accent, _ = ACCENT.get(cat, ACCENT["state"]), None
    rng = random.Random(meta.get("episode", 1) * 7919)
    img = bg(rng, accent); d = ImageDraw.Draw(img, "RGBA")
    # icon on the right, with a soft glow copy
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); icon(ImageDraw.Draw(glow), cat, 960, 360, 430, accent + (255,))
    img.paste(glow.filter(ImageFilter.GaussianBlur(28)), (0, 0), glow.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img, "RGBA"); icon(d, cat, 960, 360, 430, accent + (255,))
    # text block (left)
    l1, l2 = meta["line1"].upper(), meta["line2"].upper()
    f1 = fit(l1, "InterDisplay-Black.otf", 700, 150); f2 = fit(l2, "InterDisplay-Black.otf", 700, 150)
    y = 190
    glitch_text(img, (56, y), l1, f1, (255, 255, 255)); y += int(f1.size * 1.02)
    glitch_text(img, (56, y), l2, f2, accent)
    d = ImageDraw.Draw(img, "RGBA")
    # top-left case tag + year badge
    tag = f"CASE #{meta['episode']:03d}"
    ft = font("Inter-Bold.otf", 34); tw = ft.getlength(tag)
    d.rectangle((56, 44, 56 + tw + 40, 96), fill=accent + (255,)); d.text((76, 70), tag, font=ft, fill=(0, 0, 0), anchor="lm")
    fy = font("InterDisplay-Black.otf", 52); d.text((56 + tw + 70, 70), str(meta["year"]), font=fy, fill=(255, 255, 255), anchor="lm", stroke_width=4, stroke_fill=(0, 0, 0))
    # bottom bar: true-story tag + brand
    d.rectangle((0, H - 74, W, H), fill=(0, 0, 0, 200)); d.rectangle((0, H - 78, W, H - 74), fill=accent + (255,))
    fb = font("Inter-Bold.otf", 30)
    d.text((56, H - 37), meta.get("tag", "THE TRUE STORY").upper(), font=fb, fill=(255, 255, 255), anchor="lm")
    d.text((W - 56, H - 37), "BREACH UNCOVERED", font=fb, fill=accent, anchor="rm")
    # vignette
    v = Image.new("L", (W, H), 0); ImageDraw.Draw(v).ellipse((-260, -200, W + 260, H + 200), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120)); img = Image.composite(img, Image.new("RGB", (W, H), (0, 0, 0)), v)
    q = 92
    img.save(out, "JPEG", quality=q, optimize=True)
    while os.path.getsize(out) > 1_900_000 and q > 60:   # YouTube limit 2 MB
        q -= 6; img.save(out, "JPEG", quality=q, optimize=True)
    return out

if __name__ == "__main__":
    make(json.load(open(sys.argv[1])), sys.argv[2]); print("saved", sys.argv[2], os.path.getsize(sys.argv[2]) // 1024, "KB")
