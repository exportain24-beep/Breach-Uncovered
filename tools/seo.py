"""Final SEO assets: chapters, description (US/English), SRT captions, YouTube + Facebook payloads."""
import re

def fmt_ts(sec):
    sec = int(sec); h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def chapters(timeline):
    sc = timeline["scenes"]; out = [(0.0, sc[0]["label"])]; last = 0.0
    for s in sc[1:]:
        if s["t0"] - last >= 28 and timeline["total"] - s["t0"] > 25: out.append((s["t0"], s["label"])); last = s["t0"]
    if len(out) < 3:
        out = [(0.0, sc[0]["label"])]; last = 0.0
        for s in sc[1:]:
            if s["t0"] - last >= 14: out.append((s["t0"], s["label"])); last = s["t0"]
    return "\n".join(f"{fmt_ts(t)} {l}" for t, l in out[:20])

def description(script, timeline, credits):
    d = script["seo"]["youtube_description"].replace("{{CHAPTERS}}", "Chapters:\n" + chapters(timeline))
    cc = [c for c in credits if "Pixabay" not in c]
    block = ""
    if credits:
        block = "\n\nVisual credits:\n" + "\n".join("• " + c for c in cc[:14])
        block += ("\n" if cc else "") + ("• Stock footage & photos via Pixabay" if any("Pixabay" in c for c in credits) else "")
    lines = d.rstrip().split("\n")
    tag_idx = next((i for i in range(len(lines) - 1, -1, -1) if lines[i].strip().startswith("#")), None)
    if tag_idx is None: d = d.rstrip() + block
    else: d = "\n".join(lines[:tag_idx]).rstrip() + block + "\n\n" + "\n".join(lines[tag_idx:])
    return d[:4900]

def youtube_snippet(script, timeline, credits):
    s = script["seo"]; tags, total = [], 0
    for t in s["tags"]:
        if total + len(t) + 1 > 480: break
        tags.append(t); total += len(t) + 1
    return {"title": s["youtube_title"][:100], "description": description(script, timeline, credits), "tags": tags,
            "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"}

def facebook_description(script):
    s = script["seo"]; return s["facebook_text"].strip()

def srt(scenes_plan, chunk_words):
    """scenes_plan: render.build_plan() output; one cue per caption chunk, offset by scene start."""
    def t(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{(ms // 60000) % 60:02d}:{(ms // 1000) % 60:02d},{ms % 1000:03d}"
    out, n = [], 1
    for sc in scenes_plan:
        for ch in chunk_words(sc["words"]):
            a, b = sc["t0"] + ch[0]["s"], sc["t0"] + ch[-1]["e"] + .15
            out.append(f"{n}\n{t(a)} --> {t(b)}\n" + " ".join(w["w"] for w in ch) + "\n"); n += 1
    return "\n".join(out)
