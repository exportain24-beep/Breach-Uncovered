"""ElevenLabs narration — LOCKED to model eleven_v4_turbo (owner's standing rule). One call per scene,
with request-stitching context; returns mp3 + word timings (audio tags are stripped from timings)."""
import base64, hashlib, json, os, re, subprocess, time
import requests

MODEL = "eleven_v4_turbo"          # LOCKED. Never change.
VOICE = os.environ.get("ELEVENLABS_VOICE_ID", "fPIfC3elMLbN9tNwMXkw")
API = "https://api.elevenlabs.io/v1"
# Natural, expressive storytelling delivery (owner feedback): moderate stability lets the audio tags and the story's emotion come through.
VOICE_SETTINGS = {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3, "use_speaker_boost": True, "speed": 1.0}

def _headers(): return {"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "Content-Type": "application/json"}

def ffprobe_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())

def words_from_alignment(al):
    """al = {characters, character_start_times_seconds, character_end_times_seconds}; drops [tags]."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    words, cur, depth = [], None, 0
    for c, s, e in zip(chars, st, en):
        if c == "[": depth += 1; continue
        if c == "]": depth = max(0, depth - 1); continue
        if depth: continue
        if c.isspace():
            if cur: words.append(cur); cur = None
            continue
        if cur is None: cur = {"w": c, "s": s, "e": e}
        else: cur["w"] += c; cur["e"] = e
    if cur: words.append(cur)
    return words

def synth(text, prev_text, next_text, out_path):
    assert MODEL == "eleven_v4_turbo", "model is locked to eleven_v4_turbo"
    assert len(text) < 9500, "scene too long for one request"
    url = f"{API}/text-to-speech/{VOICE}/with-timestamps?output_format=mp3_44100_128"
    body = {"model_id": MODEL, "text": text, "voice_settings": dict(VOICE_SETTINGS)}
    if prev_text: body["previous_text"] = prev_text[-600:]
    if next_text: body["next_text"] = next_text[:600]
    last = None
    for attempt in range(5):
        r = requests.post(url, headers=_headers(), json=body, timeout=240)
        if r.status_code == 200: break
        last = f"{r.status_code} {r.text[:300]}"
        if r.status_code == 400 and ("previous_text" in body or "next_text" in body) and re.search(r"previous_text|next_text|stitch", r.text, re.I):
            body.pop("previous_text", None); body.pop("next_text", None); continue
        if r.status_code == 400 and "voice_settings" in body:             # a setting this model does not accept: retry once without it
            print("ElevenLabs rejected voice_settings, retrying with the voice's defaults:", r.text[:200]); body.pop("voice_settings", None); continue
        if r.status_code in (429, 500, 502, 503, 504): time.sleep(5 * (attempt + 1)); continue
        raise RuntimeError("ElevenLabs error " + last)
    else:
        raise RuntimeError("ElevenLabs failed: " + str(last))
    j = r.json(); open(out_path, "wb").write(base64.b64decode(j["audio_base64"]))
    al = j.get("alignment") or j.get("normalized_alignment")
    dur = ffprobe_duration(out_path)
    words = words_from_alignment(al) if al else []
    return dur, words

def synth_script(script, workdir):
    """Returns timing list for render.py; caches by text hash so reruns don't re-spend credits."""
    os.makedirs(os.path.join(workdir, "voice"), exist_ok=True); sc = script["scenes"]; timing = []
    plain = lambda n: re.sub(r"\[[^\]]*\]", "", n).strip()
    for i, s in enumerate(sc):
        h = hashlib.sha1((MODEL + VOICE + s["narration"]).encode()).hexdigest()[:12]
        mp3 = os.path.join(workdir, "voice", f"{s['id']:02d}-{h}.mp3"); meta = mp3 + ".json"
        if os.path.exists(mp3) and os.path.exists(meta):
            d = json.load(open(meta)); dur, words = d["duration"], d["words"]
        else:
            dur, words = synth(s["narration"], plain(sc[i - 1]["narration"]) if i else "", plain(sc[i + 1]["narration"]) if i + 1 < len(sc) else "", mp3)
            if not words:   # alignment missing -> proportional fallback
                ws = plain(s["narration"]).split(); per = dur / max(1, len(ws)); words = [{"w": w, "s": k * per, "e": (k + .9) * per} for k, w in enumerate(ws)]
            json.dump({"duration": dur, "words": words}, open(meta, "w"))
        timing.append({"id": s["id"], "audio": mp3, "duration": dur, "words": words})
    json.dump(timing, open(os.path.join(workdir, "timing.json"), "w"))
    return timing
