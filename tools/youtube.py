"""YouTube Data API v3 helpers (resumable upload, thumbnail, captions, playlists, comments). Secrets via env only."""
import json, os, time
import requests

API = "https://www.googleapis.com/youtube/v3"
_tok = {"v": None, "t": 0}

def token():
    if _tok["v"] and time.time() - _tok["t"] < 2400: return _tok["v"]
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status(); _tok["v"], _tok["t"] = r.json()["access_token"], time.time(); return _tok["v"]

def H(extra=None): return {"Authorization": f"Bearer {token()}", **(extra or {})}

def upload_video(path, snippet, publish_at_iso, chunk=32 * 1024 * 1024):
    size = os.path.getsize(path)
    body = {"snippet": snippet, "status": {"privacyStatus": "private", "publishAt": publish_at_iso, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False, "embeddable": True, "publicStatsViewable": True}}
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers=H({"Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}), json=body, timeout=60)
    if r.status_code != 200: raise RuntimeError(f"YT init failed {r.status_code} {r.text[:300]}")
    loc = r.headers["Location"]; pos = 0
    with open(path, "rb") as f:
        while pos < size:
            f.seek(pos); data = f.read(chunk); end = pos + len(data) - 1
            for attempt in range(6):
                try:
                    rr = requests.put(loc, data=data, headers={"Content-Length": str(len(data)), "Content-Range": f"bytes {pos}-{end}/{size}", "Content-Type": "video/mp4"}, timeout=600)
                except requests.RequestException as e:
                    time.sleep(4 * (attempt + 1)); rr = None
                if rr is not None and rr.status_code in (200, 201): return rr.json()["id"]
                if rr is not None and rr.status_code == 308: pos = int(rr.headers["Range"].split("-")[1]) + 1 if "Range" in rr.headers else pos; break
                # unknown state: ask server how much it has
                st = requests.put(loc, headers={"Content-Range": f"bytes */{size}", "Content-Length": "0"}, timeout=60)
                if st.status_code in (200, 201): return st.json()["id"]
                if st.status_code == 308: pos = int(st.headers["Range"].split("-")[1]) + 1 if "Range" in st.headers else 0; break
                time.sleep(5 * (attempt + 1))
            else: raise RuntimeError("YT chunk upload failed repeatedly")
    raise RuntimeError("YT upload ended without video id")

def set_thumbnail(video_id, jpg):
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={video_id}&uploadType=media",
                      headers=H({"Content-Type": "image/jpeg"}), data=open(jpg, "rb").read(), timeout=120)
    if r.status_code != 200: raise RuntimeError(f"thumbnail failed {r.status_code} {r.text[:200]}")

def upload_captions(video_id, srt_text, lang="en", name="English"):
    meta = {"snippet": {"videoId": video_id, "language": lang, "name": name, "isDraft": False}}
    files = {"snippet": ("meta.json", json.dumps(meta), "application/json; charset=UTF-8"), "media": ("captions.srt", srt_text.encode("utf-8"), "application/octet-stream")}
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/captions?uploadType=multipart&part=snippet", headers=H(), files=files, timeout=120)
    if r.status_code != 200: raise RuntimeError(f"captions failed {r.status_code} {r.text[:200]}")

def ensure_playlist(title, description, state):
    pl = state.setdefault("playlists", {})
    if title in pl: return pl[title]
    r = requests.post(f"{API}/playlists?part=snippet,status", headers=H({"Content-Type": "application/json"}),
                      json={"snippet": {"title": title, "description": description, "defaultLanguage": "en"}, "status": {"privacyStatus": "public"}}, timeout=30)
    if r.status_code != 200: raise RuntimeError(f"playlist failed {r.status_code} {r.text[:200]}")
    pl[title] = r.json()["id"]; return pl[title]

def add_to_playlist(pl_id, video_id):
    import time
    for attempt in range(4):                       # YouTube answers 409/5xx now and then; the video itself is fine
        r = requests.post(f"{API}/playlistItems?part=snippet", headers=H({"Content-Type": "application/json"}),
                          json={"snippet": {"playlistId": pl_id, "resourceId": {"kind": "youtube#video", "videoId": video_id}}}, timeout=30)
        if r.status_code == 200: return
        if r.status_code not in (409, 500, 502, 503, 504): break
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"playlist add failed {r.status_code} {r.text[:200]}")

def comment(video_id, text):
    r = requests.post(f"{API}/commentThreads?part=snippet", headers=H({"Content-Type": "application/json"}),
                      json={"snippet": {"videoId": video_id, "topLevelComment": {"snippet": {"textOriginal": text}}}}, timeout=30)
    return r.status_code == 200

def channel_id():
    r = requests.get(f"{API}/channels?part=id&mine=true", headers=H(), timeout=30); r.raise_for_status(); return r.json()["items"][0]["id"]
