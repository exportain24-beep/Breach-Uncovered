"""Pre-flight check for all secrets and services (spends no ElevenLabs credits). Writes reports/selftest.md"""
import os, sys, json, requests, datetime
sys.path.insert(0, os.path.dirname(__file__)); os.chdir(os.path.join(os.path.dirname(__file__), ".."))
rows = []
def row(name, ok, detail=""): rows.append(f"| {'✅' if ok else '❌'} | {name} | {detail} |"); print(rows[-1])

k = os.environ.get("ELEVENLABS_API_KEY", "")
row("ELEVENLABS_API_KEY present", bool(k))
if k:
    r = requests.get("https://api.elevenlabs.io/v1/models", headers={"xi-api-key": k}, timeout=30)
    ids = [m["model_id"] for m in r.json()] if r.status_code == 200 else []
    row("Model eleven_v4_turbo available on this key", "eleven_v4_turbo" in ids, f"HTTP {r.status_code}; v4-family: {[i for i in ids if 'v4' in i]}")
    r = requests.get("https://api.elevenlabs.io/v1/voices/" + os.environ.get("ELEVENLABS_VOICE_ID", "fPIfC3elMLbN9tNwMXkw"), headers={"xi-api-key": k}, timeout=30)
    row("Voice reachable", r.status_code == 200, f"{r.json().get('name') if r.status_code == 200 else r.text[:120]}")
    r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers={"xi-api-key": k}, timeout=30)
    if r.status_code == 200:
        j = r.json(); left = j["character_limit"] - j["character_count"]; row("ElevenLabs usage", True, f"info only: {left:,} plan characters left; pay-as-you-go API usage is not gated by this")
import media
os.environ.setdefault("MEDIA_CACHE", "/tmp/mediatest"); os.makedirs(os.environ["MEDIA_CACHE"], exist_ok=True)
row("PIXABAY_API_KEY present", bool(os.environ.get("PIXABAY_API_KEY")))
try:
    a = media.pixabay_video("server room", set()); row("Pixabay video search + download", bool(a), a and a["credit"] or "no result")
except Exception as e: row("Pixabay video search", False, str(e)[:120])
try:
    a = media.commons_image("Sony Pictures Entertainment", set()); row("Wikimedia Commons search + license filter", bool(a), a and a["credit"][:90] or "no result")
except Exception as e: row("Wikimedia Commons", False, str(e)[:120])
try:
    import youtube; row("YouTube token + channel", True, youtube.channel_id())
except Exception as e: row("YouTube", False, str(e)[:150])
try:
    import facebook; row("Facebook page token", bool(facebook.page_token()))
except Exception as e: row("Facebook", False, str(e)[:150])
os.makedirs("reports", exist_ok=True)
open("reports/selftest.md", "w").write(f"# Self-test {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n| | Check | Detail |\n|---|---|---|\n" + "\n".join(rows) + "\n")
sys.exit(0 if all(r.startswith("| ✅") for r in rows) else 1)
