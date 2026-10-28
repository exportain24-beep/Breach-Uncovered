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
        if h["id"] in used or h.get("duration", 0) < 5: continue
        vs = h["videos"]; v = vs.get("large") if vs.get("large", {}).get("url") else vs.get("medium")
        if not v or not v.get("url"): continue
        p = _download(v["url"], os.path.join(CACHE, f"pxv_{h['id']}.mp4"))
        return {"path": p, "kind": "video", "credit": f"Video by {h.get('user', 'Pixabay contributor')} via Pixabay", "id": h["id"]}
    return None

def pixabay_image(q, used):
    hits = _pix_get("", {"q": q, "image_type": "photo", "orientation": "horizontal", "min_width": 1280, "order": "popular"}) or []
    for h in hits:
        if h["id"] in used: continue
        p = _download(h["largeImageURL"], os.path.join(CACHE, f"pxi_{h['id']}.jpg"))
        return {"path": p, "kind": "image", "credit": f"Photo by {h.get('user', 'Pixabay contributor')} via Pixabay", "id": h["id"]}
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
        if pg["pageid"] in used: continue
        url = ii.get("thumburl") or ii["url"]
        p = _download(url, os.path.join(CACHE, f"wc_{pg['pageid']}.jpg"))
        who = _strip(md.get("Artist", {}).get("value", "")) or "Wikimedia Commons contributor"
        return {"path": p, "kind": "image", "credit": f"{pg['title'].replace('File:', '')} — {who[:60]} / {lic} / Wikimedia Commons", "id": pg["pageid"], "license": lic}
    return None

def fetch(v, used):
    q = (v.get("query") or "").strip()
    if not q: return None
    order = [commons_image, pixabay_image, pixabay_video] if v["type"] == "archival" else [pixabay_video, pixabay_image, commons_image]
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
    return None

def fetch_all(script, workdir):
    assets, used, credits = {}, set(), []
    for s in script["scenes"]:
        for vi, v in enumerate(s.get("visuals", [])):
            if v["type"] in ("stock", "archival"):
                a = fetch(v, used)
                if a: assets[f"{s['id']}:{vi}"] = {k: a[k] for k in ("path", "kind", "credit")}; credits.append(a["credit"])
                else: print(f"no asset for scene {s['id']} visual {vi}: {v.get('query')}")
    json.dump(assets, open(os.path.join(workdir, "assets.json"), "w"), indent=1)
    return assets, sorted(set(credits))
