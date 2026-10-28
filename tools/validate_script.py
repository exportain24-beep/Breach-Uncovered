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
        nb = sum(1 for x in v if x.get("type") in ("stock", "archival"))
        need = max(3, int(w / 8))          # about one shot per 3-4 seconds of speech
        if nb < min(need, 6): errs.append(f"scene {i}: {nb} stock/archival shots, need >= {min(need, 6)} (aim ~{max(3, w // 8)})")
        elif nb < need - 2: warns.append(f"scene {i}: only {nb} shots for {w} words (aim ~{max(3, w // 8)})")
        if sum(1 for x in v if x.get("type") == "motion") > 1: errs.append(f"scene {i}: max 1 motion card per scene")
        plain_low = re.sub(r"\[[^\]]*\]", " ", n).lower()
        for x in v:
            at = (x.get("at") or "").strip().lower()
            if not at: warns.append(f"scene {i}: visual without 'at' cue")
            elif re.sub(r"[^\w\s']", "", at) not in re.sub(r"[^\w\s']", "", plain_low): warns.append(f"scene {i}: 'at' phrase not found in narration: {at}")
        for x in v:
            t = x.get("type")
            if t not in ("motion", "archival", "stock"): errs.append(f"scene {i}: bad visual type {t}")
            elif t == "motion" and x.get("kind") not in MOTION_KINDS: errs.append(f"scene {i}: bad motion kind {x.get('kind')}")
            elif t in ("archival", "stock") and not x.get("query"): errs.append(f"scene {i}: {t} visual needs query")
    first = re.split(r"(?<=[.!?])\s+", re.sub(r"\[[^\]]*\]", " ", sc[0]["narration"]).strip())[0] if sc else ""
    if len(first.split()) > 14: errs.append(f"hook: first sentence is {len(first.split())} words (max 14, must grab in 5 seconds)")
    allv = [x for s in sc for x in (s.get("visuals") or [])]
    if sum(1 for x in allv if x.get("type") == "motion") > 8: errs.append("more than 8 motion cards in the episode (text overload)")
    if sum(1 for x in allv if x.get("overlay")) > 4: errs.append("more than 4 overlay texts in the episode")
    qs = [x.get("query", "").lower() for x in allv if x.get("query")]
    if len(set(qs)) < len(qs): warns.append("repeated visual queries: " + ", ".join(sorted({q for q in qs if qs.count(q) > 1})[:5]))
    if sum(1 for x in allv if x.get("type") in ("stock", "archival")) < 55: errs.append("fewer than 55 stock/archival shots in the episode")
    alltext = " ".join(re.sub(r"\[[^\]]*\]", " ", s.get("narration", "")) for s in sc)
    sents = [t for t in re.split(r"(?<=[.!?])\s+", alltext) if t.strip()]
    avg = len(alltext.split()) / max(1, len(sents))
    if avg > 14: errs.append(f"average sentence length {avg:.1f} words (need <= 14: simpler, shorter sentences)")
    hard = re.findall(r"\b(?:infiltrat\w+|exfiltrat\w+|orchestrat\w+|ostensibl\w+|subsequent\w*|attribut\w+|nefarious|perpetrat\w+|compromis\w+|clandestine|utiliz\w+|aforementioned|notwithstanding)\b", alltext, re.I)
    if len(hard) > 3: errs.append("too much formal vocabulary: " + ", ".join(sorted(set(h.lower() for h in hard))))
    if "mood" not in sc[0]: warns.append("scenes should have a 'mood'")
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
