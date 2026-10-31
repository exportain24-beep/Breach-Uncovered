"""Validate Shorts scripts (docs/SHORTS_SPEC.md). usage: python3 tools/validate_short.py shorts/*.json"""
import json, re, sys
from urllib.parse import urlparse
KINDS = {"building": ["type", "name"], "office": ["who", "action"], "hacker": [], "servers": ["state"], "people": ["who", "action"], "phone": ["app", "text"],
         "email": ["from", "subject"], "object": ["icon"], "network": [], "globe": ["points"], "flow": ["nodes"], "counter": ["value"], "timeline": ["items"],
         "lock": ["state"], "terminal": ["lines"], "dossier": ["title", "rows"], "headline": ["text"], "stamp": ["text"], "split": ["left", "right"]}
ROLES = {"worker", "workerF", "banker", "agent", "agentF", "hacker", "guard", "engineer", "exec", "crook", "police", "doctor", "soldier", "student"}
ICONS = set("printer usb laptop money clock calendar envelope key file wifi camera plane ship car atm card bitcoin skull bug shield satellite pipeline bulb".split())
BTYPES = set("bank fbi office hospital government factory police airport school studio power".split())
TEXT_FIELDS = ("name", "screen", "label", "text", "from", "subject", "line", "title", "left", "right", "amount")
plain = lambda n: re.sub(r"\[[^\]]*\]", " ", n)
def norm(s): return re.sub(r"[^\w\s']", "", s.lower().replace("’", "'"))

def validate(path):
    E, Wn = [], []
    try: s = json.load(open(path, encoding="utf-8"))
    except Exception as e: return [f"bad json: {e}"], []
    for k in ("episode", "key", "title", "scenes", "facts", "seo"):
        if k not in s: E.append(f"missing {k}")
    sc = s.get("scenes", []); words = sum(len(plain(x.get("narration", "")).split()) for x in sc)
    if not 75 <= words <= 102: E.append(f"narration {words} words (need 75-102: with the 2.5 s logo ending the Short must stay under 50 s)")
    if not 4 <= len(sc) <= 8: E.append(f"{len(sc)} scenes (need 4-8)")
    allt = " ".join(plain(x.get("narration", "")) for x in sc).strip()
    sents = [t for t in re.split(r"(?<=[.!?])\s+", allt) if t.strip()]
    if sents and len(sents[0].split()) > 12: E.append(f"hook is {len(sents[0].split())} words (max 12)")
    if sents and words / len(sents) > 12.5: E.append(f"average sentence {words / len(sents):.1f} words (max 12)")
    tags = sum(len(re.findall(r"\[[^\]]*\]", x.get("narration", ""))) for x in sc)
    if tags > 6: E.append(f"{tags} audio tags (max 6)")
    nv, prev = 0, None
    for i, x in enumerate(sc):
        if x.get("mood") not in ("calm", "curious", "tense", "shock", "reveal", "sad", "hopeful"): E.append(f"scene {i + 1}: bad mood")
        n = norm(plain(x.get("narration", ""))); vs = x.get("visuals") or []
        if not vs: E.append(f"scene {i + 1}: no visuals")
        for v in vs:
            nv += 1; k = v.get("kind")
            if k not in KINDS: E.append(f"scene {i + 1}: bad kind {k}"); continue
            if k == prev: Wn.append(f"scene {i + 1}: same kind twice in a row ({k})")
            prev = k
            for f in KINDS[k]:
                if f not in v: E.append(f"scene {i + 1}: {k} needs '{f}'")
            at = norm(v.get("at", ""))
            if not at: E.append(f"scene {i + 1}: visual without 'at'")
            elif at not in n: E.append(f"scene {i + 1}: 'at' not in narration: {v.get('at')}")
            for f in TEXT_FIELDS:
                if isinstance(v.get(f), str) and len(v[f].split()) > 6: E.append(f"scene {i + 1}: {k}.{f} longer than 6 words")
            whos = v.get("who") if isinstance(v.get("who"), list) else [v.get("who")] if v.get("who") else []
            for w in whos:
                if w not in ROLES: E.append(f"scene {i + 1}: unknown role {w}")
            if k == "object" and v.get("icon") not in ICONS: E.append(f"scene {i + 1}: unknown icon {v.get('icon')}")
            if k == "building" and v.get("type") not in BTYPES: E.append(f"scene {i + 1}: unknown building type {v.get('type')}")
            if v.get("type") in ("stock", "archival", "clip", "video", "photo"): E.append("clips/photos are not allowed")
    if nv < max(10, words // 10): E.append(f"only {nv} visuals (need >= {max(10, words // 10)}: a new picture every 2-4 s)")
    if nv > words // 5: E.append(f"{nv} visuals is too many for {words} words")
    facts = s.get("facts", [])
    if len(facts) < 4: E.append("need >= 4 facts with sources")
    doms = {urlparse(f.get("source", "")).netloc for f in facts if f.get("source", "").startswith("http")}
    if len(doms) < 2: E.append("facts need sources from >= 2 domains")
    seo = s.get("seo", {})
    for k in ("title", "description", "facebook_text", "first_comment"):
        if not seo.get(k): E.append(f"seo.{k} missing")
    if len(seo.get("title", "")) > 70: E.append("seo.title > 70 chars")
    if s.get("pillar") not in (None, "cyber", "ai", "crime", "mystery", "privacy", "future", "money", "history"): E.append("bad pillar")
    if s.get("slot_type") not in (None, "trending", "curiosity", "ai", "mystery"): E.append("bad slot_type")
    for k in ("pillar", "slot_type", "hooks", "hook_type", "score"):
        if k not in s: Wn.append(f"missing {k} (new scripts must have it)")
    if isinstance(s.get("hooks"), list) and 0 < len(s["hooks"]) < 3: Wn.append("hooks: write 5 candidates")
    if isinstance(s.get("score"), dict) and s["score"].get("total", 100) < 70: E.append("score.total < 70: pick a stronger topic")
    yh = [h for h in seo.get("hashtags", []) if h.startswith("#")]
    if yh and not 2 <= len(yh) <= 4: Wn.append(f"YouTube hashtags {len(yh)} (use 2-4)")
    fh = re.findall(r"#\w+", seo.get("facebook_text", ""))
    if seo.get("facebook_text") and not 3 <= len(fh) <= 5: Wn.append(f"Facebook hashtags {len(fh)} (use 3-5)")
    if re.search(r"\b(like if|share to win|comment yes|tag a friend)\b", (seo.get("facebook_text", "") + seo.get("description", "")).lower()): E.append("engagement bait in captions")
    th = seo.get("thumb") or {}
    if not th.get("text"): Wn.append("seo.thumb.text missing (cover falls back to the title)")
    elif len(th["text"].split()) > 6: E.append("seo.thumb.text longer than 6 words")
    return E, Wn

if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        e, w = validate(p); print(("OK   " if not e else "FAIL ") + p)
        for x in e: print("   ERROR:", x)
        for x in w: print("   warn:", x)
        bad += bool(e)
    print(f"{len(sys.argv) - 1 - bad}/{len(sys.argv) - 1} passed"); sys.exit(1 if bad else 0)
