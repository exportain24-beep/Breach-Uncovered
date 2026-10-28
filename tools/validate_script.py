"""Validate episode script JSON files. Usage: python3 tools/validate_script.py scripts/*.json"""
import json, re, sys, glob, urllib.parse

ALLOWED_TAGS = {
    "serious", "slowly", "softly", "whispers", "whispering", "dramatically", "cautiously", "nervous", "curious",
    "surprised", "exhales", "sighs", "short pause", "pause", "long pause", "deep voice", "breathless", "tired",
    "sarcastic", "warmly", "excited", "angry", "sad", "gasps", "clears throat", "trembling voice", "raspy",
    "frustrated", "worried", "grim", "calmly", "urgently", "incredulous", "reflective", "ominously", "quietly",
}
MOTION_KINDS = {"timeline", "counter", "doc_callout", "network", "map", "terminal", "quote", "headline", "redact", "title"}
BANNED = ["next episode", "previous episode", "last video", "next video", "welcome back", "in today's video",
          "hey guys", "hello everyone", "welcome to breach uncovered"]

def validate(path):
    errs, warns = [], []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return [f"invalid JSON: {e}"], []
    for k in ("episode", "key", "title", "year", "category", "scenes", "facts", "sources", "seo"):
        if k not in d: errs.append(f"missing key '{k}'")
    if errs: return errs, warns
    sc = d["scenes"]
    words = 0
    if not 10 <= len(sc) <= 20: warns.append(f"{len(sc)} scenes (target 12-18)")
    for i, s in enumerate(sc, 1):
        n = s.get("narration", "")
        w = len(re.sub(r"\[[^\]]*\]", "", n).split())
        words += w
        if s.get("id") != i: errs.append(f"scene id {s.get('id')} should be {i}")
        if not n.strip(): errs.append(f"scene {i}: empty narration")
        if re.search(r"[*_#`]|\(.*?\)", re.sub(r"\[[^\]]*\]", "", n)): warns.append(f"scene {i}: markdown/parentheses in narration")
        for t in re.findall(r"\[([^\]]*)\]", n):
            if t.strip().lower() not in ALLOWED_TAGS: warns.append(f"scene {i}: unusual tag [{t}]")
        low = n.lower()
        for b in BANNED:
            if b in low: errs.append(f"scene {i}: banned phrase '{b}'")
        if w > 140: warns.append(f"scene {i}: {w} words (long beat)")
        if not s.get("label") or len(s["label"]) > 40: errs.append(f"scene {i}: label missing or >40 chars")
        v = s.get("visuals") or []
        if not 1 <= len(v) <= 3: errs.append(f"scene {i}: needs 1-3 visuals")
        for x in v:
            t = x.get("type")
            if t not in ("motion", "archival", "stock"): errs.append(f"scene {i}: bad visual type {t}")
            elif t == "motion" and x.get("kind") not in MOTION_KINDS: errs.append(f"scene {i}: bad motion kind {x.get('kind')}")
            elif t in ("archival", "stock") and not x.get("query"): errs.append(f"scene {i}: {t} visual needs query")
    if sc and len(re.sub(r"\[[^\]]*\]", "", sc[0]["narration"]).split()) > 90: errs.append("cold open > 90 words")
    if not 900 <= words <= 1400: errs.append(f"narration {words} words (need 900-1400)")
    tags = sum(len(re.findall(r"\[[^\]]*\]", s.get("narration", ""))) for s in sc)
    if not 6 <= tags <= 45: warns.append(f"{tags} audio tags (target 8-25)")
    caps = sum(len(re.findall(r"\b[A-Z]{3,}\b", re.sub(r"\[[^\]]*\]", "", s.get("narration", "")))) for s in sc)
    if caps > 12: warns.append(f"{caps} ALL-CAPS words (use sparingly; acronyms count)")
    f = d["facts"]
    if len(f) < 8: errs.append(f"only {len(f)} facts (need >= 8)")
    for i, x in enumerate(f):
        if not str(x.get("source", "")).startswith("http"): errs.append(f"fact {i+1}: no source URL")
        if x.get("confidence") not in ("confirmed", "reported", "alleged"): errs.append(f"fact {i+1}: bad confidence")
    src = d["sources"]
    if len({urllib.parse.urlparse(u).netloc for u in src}) < 3: errs.append("need sources from >= 3 different domains")
    seo = d["seo"]
    for k in ("youtube_title", "youtube_description", "tags", "hashtags", "thumb", "facebook_text", "first_comment", "search_terms"):
        if k not in seo: errs.append(f"seo missing '{k}'")
    if errs: return errs, warns
    if len(seo["youtube_title"]) > 70: (errs if len(seo["youtube_title"]) > 100 else warns).append(f"title {len(seo['youtube_title'])} chars")
    desc = seo["youtube_description"]
    if "{{CHAPTERS}}" not in desc: errs.append("description missing {{CHAPTERS}}")
    if len(desc) < 800: errs.append(f"description {len(desc)} chars (< 800)")
    if len(desc) > 4800: errs.append("description too long")
    if len(seo["hashtags"]) != 3: errs.append("need exactly 3 hashtags")
    tl = sum(len(t) + 1 for t in seo["tags"])
    if tl > 450: errs.append(f"tags total {tl} chars (> 450)")
    if not 8 <= len(seo["tags"]) <= 20: warns.append(f"{len(seo['tags'])} tags")
    th = seo["thumb"]
    for k in ("line1", "line2", "tag"):
        if k not in th: errs.append(f"thumb missing {k}")
    if not errs:
        if len(th["line1"]) > 18 or len(th["line2"]) > 18: errs.append("thumb lines must be <= 18 chars")
        if len(th["tag"]) > 30: errs.append("thumb tag > 30 chars")
    if "http" in seo["facebook_text"] or "http" in seo["first_comment"]: errs.append("no links in facebook_text/first_comment")
    return errs, warns

if __name__ == "__main__":
    files = sorted(sum((glob.glob(a) for a in sys.argv[1:]), []))
    bad = 0
    for p in files:
        e, w = validate(p)
        print(("FAIL " if e else "ok   ") + p)
        for x in e: print("   ERROR:", x)
        for x in w: print("   warn: ", x)
        bad += bool(e)
    print(f"\n{len(files)-bad}/{len(files)} passed")
    sys.exit(1 if bad else 0)
