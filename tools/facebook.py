"""Facebook Page video publishing via Graph API (System User token -> Page token, appsecret_proof on every call)."""
import hashlib, hmac, json, os, time
import requests

V = "v23.0"; G = f"https://graph.facebook.com/{V}"; GV = f"https://graph-video.facebook.com/{V}"
_pt = {"v": None}

def _proof(tok): return hmac.new(os.environ["FB_APP_SECRET"].encode(), tok.encode(), hashlib.sha256).hexdigest()

def page_token():
    if _pt["v"]: return _pt["v"]
    sut = os.environ["FB_SYSTEM_USER_TOKEN"]; pid = os.environ["FB_PAGE_ID"]
    r = requests.get(f"{G}/{pid}", params={"fields": "access_token", "access_token": sut, "appsecret_proof": _proof(sut)}, timeout=30)
    r.raise_for_status(); _pt["v"] = r.json()["access_token"]; return _pt["v"]

def _auth(): t = page_token(); return {"access_token": t, "appsecret_proof": _proof(t)}

def upload_video(path, title, description, thumb_jpg, publish_unix, targeting=None, chunk=8 * 1024 * 1024):
    pid = os.environ["FB_PAGE_ID"]; size = os.path.getsize(path)
    r = requests.post(f"{GV}/{pid}/videos", data={"upload_phase": "start", "file_size": size, **_auth()}, timeout=60)
    if r.status_code != 200: raise RuntimeError(f"FB start failed {r.status_code} {r.text[:300]}")
    j = r.json(); sid, vid = j["upload_session_id"], j["video_id"]; start, end = int(j["start_offset"]), int(j["end_offset"])
    with open(path, "rb") as f:
        while start < end:
            f.seek(start); data = f.read(end - start)
            for attempt in range(6):
                rr = requests.post(f"{GV}/{pid}/videos", data={"upload_phase": "transfer", "upload_session_id": sid, "start_offset": start, **_auth()},
                                   files={"video_file_chunk": ("chunk", data, "application/octet-stream")}, timeout=600)
                if rr.status_code == 200: jj = rr.json(); start, end = int(jj["start_offset"]), int(jj["end_offset"]); break
                time.sleep(5 * (attempt + 1))
            else: raise RuntimeError("FB chunk upload failed: " + rr.text[:200])
    base = {"upload_phase": "finish", "upload_session_id": sid, "title": title[:250], "description": description,
            "published": "false", "scheduled_publish_time": int(publish_unix), **_auth()}
    attempts = [dict(base, feed_targeting=json.dumps(targeting))] if targeting else []
    attempts.append(base)
    last = None
    for payload in attempts:                      # preferred-audience targeting is best-effort; fall back without it
        with open(thumb_jpg, "rb") as tf:
            rr = requests.post(f"{GV}/{pid}/videos", data=payload, files={"thumb": ("thumb.jpg", tf.read(), "image/jpeg")}, timeout=300)
        if rr.status_code == 200 and rr.json().get("success", True): return vid
        last = f"{rr.status_code} {rr.text[:300]}"
    raise RuntimeError("FB finish failed " + str(last))

def upload_captions(video_id, srt_text, locale="en_US"):
    r = requests.post(f"{G}/{video_id}/captions", data={"default_locale": locale, **_auth()},
                      files={"captions_file": (f"captions.{locale}.srt", srt_text.encode("utf-8"), "text/plain")}, timeout=120)
    return r.status_code == 200

def comment(video_id, text):
    r = requests.post(f"{G}/{video_id}/comments", data={"message": text, **_auth()}, timeout=30)
    return r.status_code == 200
