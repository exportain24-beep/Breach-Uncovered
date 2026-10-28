"""Free, license-safe visuals: Pixabay (video+photo, API key) and Wikimedia Commons (no key).
Everything cached; every asset's credit is recorded so descriptions stay honest."""
import hashlib, json, os, re, time, html
import requests

UA = {"User-Agent": "BreachUncoveredBot/1.0 (educational documentary channel; github.com/exportain24-beep/Breach-Uncovered)"}
CACHE = os.environ.get("MEDIA_CACHE", "cache/media")
os.makedirs(CACHE, exist_ok=True)
_last = {"pixabay": 0.0}
OK_LICENSE = re.compile(r"public domain|pd[- ]|cc0|cc[- ]by(?![- ]?n[cd])|cc[- ]by-sa|attribution", re.I)
BAD_LICENSE = re.compile(r"non-?commercial|\bnc\b|no-?deriv|\bnd\b|fair use|copyrighted", re.I)

def _h(s): return hashlib.sha1(s.encode()).hexdigest()[:14]
def _strip(s): return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()

def _download(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 1000: return dest
    with requests.get(url, headers=UA, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest + ".part", "wb") as f:
            for ch in r.iter_content(1 << 20): f.write(ch)
    os.replace(dest + ".part", dest); return dest

def _pix_get(path, params):
    key = os.environ.get("PIXABAY_API_KEY")
    if not key: return None
    wait = 0.7 - (time.time() - _last["pixabay"])
    if wait > 0: time.sleep(wait)
    _last["pixabay"] = time.time()
    r = requests.get("https://pixabay.com/api/" + path, params={"key": key, "safesearch": "true", "per_page": 20, **params}, headers=UA, timeout=30)
    return r.json().get("hits", []) if r.status_code == 200 else None

def pixabay_video(q, used):
    hits = _pix_get("videos/", {"q": q, "order": "popular"}) or []
    for h in hits:
        key = f"pxv{h['id']}"
        if key in used or h.get("duration", 0) < 5: continue
        vs = h["videos"]; lg = vs.get("large") or {}
        v = lg if (lg.get("url") and 0 < lg.get("size", 0) <= 45_000_000) else (vs.get("medium") if vs.get("medium", {}).get("url") else lg)
        if not v or not v.get("url"): continue
        p = _download(v["url"], os.path.join(CACHE, f"pxv_{h['id']}.mp4"))
        return {"path": p, "kind": "video", "credit": f"Video by {h.get('user', 'Pixabay contributor')} via Pixabay", "id": key}
    return None

def pixabay_image(q, used):
    hits = _pix_get("", {"q": q, "image_type": "photo", "orientation": "horizontal", "min_width": 1280, "order": "popular"}) or []
    for h in hits:
        key = f"pxi{h['id']}"
        if key in used: continue
        p = _download(h["largeImageURL"], os.path.join(CACHE, f"pxi_{h['id']}.jpg"))
        return {"path": p, "kind": "image", "credit": f"Photo by {h.get('user', 'Pixabay contributor')} via Pixabay", "id": key}
    return None

def commons_image(q, used):
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "query", "format": "json", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 12,
        "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1920})
    if r.status_code != 200: return None
    pages = sorted((r.json().get("query", {}).get("pages", {})).values(), key=lambda p: p.get("index", 99))
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = _strip(md.get("LicenseShortName", {}).get("value", ""))
        if ii.get("mime") not in ("image/jpeg", "image/png") or ii.get("width", 0) < 900: continue
        if not lic or BAD_LICENSE.search(lic) or not OK_LICENSE.search(lic): continue
        if f"wc{pg['pageid']}" in used: continue
        url = ii.get("thumburl") or ii["url"]
        p = _download(url, os.path.join(CACHE, f"wc_{pg['pageid']}.jpg"))
        who = _strip(md.get("Artist", {}).get("value", "")) or "Wikimedia Commons contributor"
        return {"path": p, "kind": "image", "credit": f"{pg['title'].replace('File:', '')} — {who[:60]} / {lic} / Wikimedia Commons", "id": f"wc{pg['pageid']}", "license": lic}
    return None

FALLBACK_Q = {"calm": ["city skyline morning", "people walking street", "office window sunlight"], "curious": ["magnifying glass documents", "typing laptop closeup", "city night lights"],
              "tense": ["dark corridor", "red warning light", "server room dark"], "shock": ["glitch screen", "red alert screen", "lightning storm"],
              "reveal": ["spotlight dark room", "documents desk lamp", "courtroom"], "sad": ["rain window", "empty office", "lonely street night"],
              "hopeful": ["sunrise city", "people working together", "green light"]}
USED_FILE = os.environ.get("USED_MEDIA_FILE", "data/used_media.json")

def load_used():
    try: return set(json.load(open(USED_FILE)))
    except Exception: return set()

def save_used(ids):
    try:
        os.makedirs(os.path.dirname(USED_FILE) or ".", exist_ok=True); json.dump(sorted(ids)[-4000:], open(USED_FILE, "w"))
    except Exception as e: print("could not save used media:", e)

def fetch(v, used, mood="curious", allow_images=True):
    q = (v.get("query") or "").strip()
    if not q: return None
    order = [commons_image, pixabay_image, pixabay_video] if v["type"] == "archival" else [pixabay_video, pixabay_image, commons_image]
    if not allow_images: order = [f for f in order if f not in (pixabay_image,)] + ([commons_image] if v["type"] == "archival" and commons_image not in order else [])
    for fn in order:
        try:
            a = fn(q, used)
            if a: used.add(a["id"]); return a
        except Exception as e: print("media error", fn.__name__, q, e)
    # broaden: first two words
    short = " ".join(q.split()[:2])
    if short != q:
        for fn in order:
            try:
                a = fn(short, used)
                if a: used.add(a["id"]); return a
            except Exception as e: print("media error", fn.__name__, short, e)
    for q2 in FALLBACK_Q.get(mood, FALLBACK_Q["curious"]):            # last resort: a generic shot that fits the mood
        try:
            a = pixabay_video(q2, used)
            if a: used.add(a["id"]); return a
        except Exception as e: print("media error fallback", q2, e)
    return None

def fetch_all(script, workdir):
    assets, used, credits = {}, load_used(), []
    for s in script["scenes"]:
        for vi, v in enumerate(s.get("visuals", [])):
            if v["type"] in ("stock", "archival"):
                nimg = sum(1 for x in assets.values() if x["kind"] == "image")       # Facebook reduces reach of mostly-static videos: keep stills <= 25%
                a = fetch(v, used, s.get("mood", "curious"), allow_images=(nimg <= .25 * max(8, len(assets))))
                if a: assets[f"{s['id']}:{vi}"] = {k: a[k] for k in ("path", "kind", "credit")}; credits.append(a["credit"])
                else: print(f"no asset for scene {s['id']} visual {vi}: {v.get('query')}")
    json.dump(assets, open(os.path.join(workdir, "assets.json"), "w"), indent=1); save_used(used)
    return assets, sorted(set(credits))
