"""Verify YouTube + Facebook access for Breach Uncovered.
Prints/writes only non-secret facts (scope names, channel/page names, pass/fail)."""
import os, json, hmac, hashlib, datetime, urllib.request, urllib.parse, urllib.error

G = "https://graph.facebook.com/v23.0"
out = []
def log(s): print(s); out.append(s)

def req(url, data=None, method=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return f.status, json.loads(f.read() or b"{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or b"{}")
        except Exception: return e.code, {}
    except Exception as e:
        return 0, {"error": str(e)}

def err(j):
    e = j.get("error", j)
    if isinstance(e, dict):
        return f"{e.get('code','')} {e.get('message', e.get('error_description',''))}".strip()
    return str(e)[:200]

def check(name, ok, detail=""):
    log(f"| {'✅' if ok else '❌'} | {name} | {detail} |")

log(f"# Access verification — {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n")

# ---------------- YouTube ----------------
log("## YouTube\n\n| | Check | Detail |\n|---|---|---|")
need_yt = ["youtube", "youtube.upload", "youtube.force-ssl", "yt-analytics.readonly", "yt-analytics-monetary.readonly"]
s, t = req("https://oauth2.googleapis.com/token", {
    "client_id": os.environ.get("YT_CLIENT_ID",""), "client_secret": os.environ.get("YT_CLIENT_SECRET",""),
    "refresh_token": os.environ.get("YT_REFRESH_TOKEN",""), "grant_type": "refresh_token"})
at = t.get("access_token")
check("Refresh token → access token", bool(at), "" if at else err(t))
if at:
    print(f"::add-mask::{at}")
    granted = t.get("scope","").split()
    short = [g.replace("https://www.googleapis.com/auth/","") for g in granted]
    for sc in need_yt:
        check(f"Scope `{sc}`", sc in short)
    H = {"Authorization": f"Bearer {at}"}
    def yget(url):
        r = urllib.request.Request(url, headers=H)
        try:
            with urllib.request.urlopen(r, timeout=60) as f: return f.status, json.loads(f.read())
        except urllib.error.HTTPError as e:
            try: return e.code, json.loads(e.read())
            except Exception: return e.code, {}
    s, c = yget("https://www.googleapis.com/youtube/v3/channels?part=snippet,status,brandingSettings&mine=true")
    items = c.get("items", [])
    if items:
        ch = items[0]
        check("Channel read", True, f"**{ch['snippet']['title']}** (id {ch['id']})")
        st = ch.get("status", {})
        check("Long uploads / custom thumbnails (verified channel)", st.get("longUploadsStatus") == "allowed", f"longUploadsStatus={st.get('longUploadsStatus')}")
        check("Branding settings readable (SEO: channel keywords/description)", "brandingSettings" in ch)
    else:
        check("Channel read", False, err(c) if c else "no channel on this token")
    s, p = yget("https://www.googleapis.com/youtube/v3/playlists?part=id&mine=true&maxResults=1")
    check("Playlists API", s == 200, "" if s == 200 else err(p))
    today = datetime.date.today().isoformat()
    s, a = yget("https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(
        {"ids": "channel==MINE", "startDate": "2025-01-01", "endDate": today, "metrics": "views"}))
    check("YouTube Analytics API", s == 200, "" if s == 200 else err(a))

# ---------------- Facebook ----------------
log("\n## Facebook\n\n| | Check | Detail |\n|---|---|---|")
tok = os.environ.get("FB_SYSTEM_USER_TOKEN",""); app_id = os.environ.get("FB_APP_ID","")
app_sec = os.environ.get("FB_APP_SECRET",""); page_id = os.environ.get("FB_PAGE_ID","")
def proof(t): return hmac.new(app_sec.encode(), t.encode(), hashlib.sha256).hexdigest()
s, d = req(f"{G}/debug_token?" + urllib.parse.urlencode({"input_token": tok, "access_token": f"{app_id}|{app_sec}"}))
dd = d.get("data", {})
check("System user token valid", dd.get("is_valid") is True, err(d) if not dd else f"type={dd.get('type')}, app_id match={str(dd.get('app_id'))==app_id}")
if dd:
    exp = dd.get("expires_at", None)
    check("Token never expires", exp == 0, f"expires_at={exp}")
    scopes = dd.get("scopes", [])
    for sc in ["pages_show_list","pages_manage_posts","pages_read_engagement","pages_manage_engagement",
               "pages_read_user_content","pages_manage_metadata","read_insights","business_management","pages_messaging"]:
        check(f"Permission `{sc}`", sc in scopes, "" if sc in scopes else ("optional" if sc=="pages_messaging" else "missing"))
    extra = [x for x in scopes if x not in ("pages_show_list","pages_manage_posts","pages_read_engagement","pages_manage_engagement","pages_read_user_content","pages_manage_metadata","read_insights","business_management","pages_messaging")]
    if extra: log(f"| ℹ️ | Other granted | {', '.join(extra)} |")
# Require App Secret check: call without proof should fail if enabled
s, n = req(f"{G}/me?" + urllib.parse.urlencode({"access_token": tok}))
check("“Require App Secret” enabled (call without proof is blocked)", s != 200, ("blocked ✔ — " + err(n)[:90]) if s != 200 else "NOT enabled — turn it on in App settings → Advanced")
s, pg = req(f"{G}/{page_id}?" + urllib.parse.urlencode({"fields": "name,access_token,category", "access_token": tok, "appsecret_proof": proof(tok)}))
ptok = pg.get("access_token")
check("Page found + page token derived", bool(ptok), f"**{pg.get('name')}** ({pg.get('category')})" if ptok else err(pg))
if ptok:
    print(f"::add-mask::{ptok}")
    P = {"access_token": ptok, "appsecret_proof": proof(ptok)}
    s, acc = req(f"{G}/me/accounts?" + urllib.parse.urlencode({"fields": "id,tasks", "access_token": tok, "appsecret_proof": proof(tok)}))
    tasks = next((a.get("tasks", []) for a in acc.get("data", []) if a.get("id") == page_id), [])
    check("Page tasks (full control)", all(x in tasks for x in ["MANAGE","CREATE_CONTENT","MODERATE","ANALYZE"]), ", ".join(tasks))
    s, x = req(f"{G}/{page_id}/feed?" + urllib.parse.urlencode({**P, "limit": 1, "fields": "id"}))
    check("Read posts (feed)", s == 200, "" if s == 200 else err(x))
    s, x = req(f"{G}/{page_id}/videos?" + urllib.parse.urlencode({**P, "limit": 1, "fields": "id"}))
    check("Read videos", s == 200, "" if s == 200 else err(x))
    s, x = req(f"{G}/{page_id}/insights?" + urllib.parse.urlencode({**P, "metric": "page_post_engagements", "period": "day"}))
    check("Insights", s == 200, "" if s == 200 else err(x))
    s, x = req(f"{G}/{page_id}?" + urllib.parse.urlencode({**P, "fields": "about,description,website,emails"}))
    check("Page info (About/description) readable", s == 200, "" if s == 200 else err(x))
    s, x = req(f"{G}/{page_id}/subscribed_apps?" + urllib.parse.urlencode(P))
    check("Webhook subscriptions endpoint", s == 200, "" if s == 200 else err(x))
s, a = req(f"{G}/{app_id}?" + urllib.parse.urlencode({"fields": "name", "access_token": f"{app_id}|{app_sec}"}))
log(f"| ℹ️ | App | {a.get('name', err(a))} |")

open("verify-report.md", "w").write("\n".join(out) + "\n")
