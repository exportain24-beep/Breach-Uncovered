# Breach Uncovered - SHORTS spec (LOCKED by the owner, 2026-10-30; updated 2026-10-31: 4 a day, wider tech pillars, algorithm rules)

The channel publishes **only vertical Shorts** (YouTube Shorts + Facebook Reels): **4 per day** at **8:00 AM, 12:00 PM, 5:00 PM and 8:30 PM New York time** (America/New_York, DST handled), each **30-50 seconds**, in natural American English, for a US-first audience (then UK/CA/AU/NZ).
Every Short tells ONE complete true technology story from start to end, explained so simply that anyone understands it.

## Brand pillars (topics)
Breach Uncovered = the hidden stories behind technology, cybersecurity, AI, digital crime and the internet.
A cybersecurity & hacking - B artificial intelligence (breakthroughs, AI scams, deepfakes, AI security) - C digital crime & investigations (FBI cases, fraud, SIM swapping, social engineering) - D internet mysteries & internet history - E digital privacy & surveillance - F future technology (quantum, robotics, space tech) - G digital money & fintech (crypto incidents, investment scams) - H technology history (famous software failures, discoveries).
Field `pillar`: one of cyber, ai, crime, mystery, privacy, future, money, history.

## Four daily formats (field `slot_type`)
| slot (New York) | slot_type | purpose |
|---|---|---|
| 8:00 AM | `trending` | a verified tech/cyber/AI story from the last days (written daily, fresh) |
| 12:00 PM | `curiosity` | a shocking real-world tech story with broad appeal (breaches, failures, big scams) |
| 5:00 PM | `ai` | AI and future technology (widens the audience) |
| 8:30 PM | `mystery` | digital mystery, investigation or privacy story (comments and shares) |
These are editorial assignments, not cages: a strong story can fill another slot. Never invent a trend to fill a slot.

## Algorithm alignment (verified 2026-10-31 - official sources only)
- YouTube Shorts ranking uses the % of viewers who choose to view (vs swipe away), average view duration, average % viewed, likes and survey results; it is personalized by topic interest; topic interest, competition and seasonality matter; there is no required posting cadence; the system prefers no format. (support.google.com/youtube/answer/11914225)
- Since Aug 24, 2026 YouTube counts a view from the first frame; the old view is now the "engaged view", and retention/AVD analytics use engaged views. Judge Shorts by engaged views and retention, not raw views. (blog.youtube/inside-youtube/engaged-views-youtube-explained)
- Facebook (Meta, Mar 13 2026): original content made by the Page is rewarded; duplicates, minor edits, re-uploads and narrating someone else's footage are deprioritized and can make a Page non-recommendable. Everything we publish is 100% our own visuals, script and voice. (about.fb.com/news/2026/03/rewarding-original-creators-on-facebook)
- Meta Reels recommendations weigh real interest matching and viewer satisfaction, not only likes/watch time (engineering.fb.com, Jan 14 2026).
What this means for every script:
1. The first 1-2 seconds must stop the scroll: the hook sentence starts the video with no intro, no channel name; the first visual is the strongest picture.
2. Retention: every scene opens a small question the next scene answers (open loops); a new picture every 2-4 s; no slow middle; the ending pays off the hook (no bait the video does not deliver).
3. Satisfaction: the viewer learns something real and specific (a number, a name, a twist) worth sharing; end with one line that makes people comment.
4. Hook lab: write 5 different hooks in `hooks` (question, shocking fact, mystery, unexpected consequence, real-world warning, historical...) and use the strongest; set `hook_type`. Do not reuse the same hook structure on consecutive Shorts.
5. Score every topic in `score` (audience 20, story 20, hook 15, current interest 15, shareability 10, visual 10, reliability 10; `total`). Produce only total >= 70.
6. Platform-specific metadata (never identical): YouTube `seo.title` (subject first, accurate, no ALL CAPS, <= 70 chars), `seo.description` (accurate context + natural keywords), `seo.hashtags` 2-4, `seo.tags` (descriptive, not a ranking shortcut); Facebook `seo.fb_title` and `seo.facebook_text` (a natural caption that complements, not repeats, the narration) with 3-5 relevant hashtags. No unrelated or trending-bait hashtags, no keyword stuffing, no engagement bait ("like if...", "share to win").
7. Never: copied/reused clips, fake engagement, fake news, fake locations, misleading thumbnails.
**100% of the picture is our own visualisation** (2D / semi-3D isometric illustrated motion graphics). No stock clips, no Pixabay, no photos, no AI video.
Voice: ElevenLabs `eleven_v4_turbo`, voice `oO7sLA3dWfQXsKeSAjpA`. Captions word-synced. Music and sound effects follow the mood.

## Story (75-102 words of narration: the narrator reads about 2.3 words a second, so this is 33-45 s plus the fixed 2.5 s logo ending)
- **Hook first:** the first sentence is at most 12 words and states the most surprising TRUE fact ("A printer helped hide a billion-dollar bank heist.").
- Then, in time order: who was hit -> how the attackers got in (one simple idea, no how-to) -> the moment it broke -> the twist or clue -> who was blamed / what happened after -> one strong last line.
- Plain spoken English, short sentences (average <= 12 words), no jargon. If a technical word is needed, explain it in five words ("malware, a hidden program").
- 4-8 scenes. Each scene is 1-3 sentences and has a `mood`: calm, curious, tense, shock, reveal, sad, hopeful.
- Accuracy: every number, name and date must be in `facts` with a source URL (official/court/major media). "Alleged" for unproven blame. No invented quotes, no invented scenes presented as real.

## Visuals: a new picture every 2-4 seconds, matched to the words
Each scene has `visuals`, in spoken order. Each visual has `at` (2-5 words copied exactly from that scene's narration: the picture starts when the narrator says them), a `kind`, and the kind's fields. Short text only (<= 6 words per text field). About one visual per 7-10 words of narration (12-20 visuals per Short). Vary the kinds; never the same kind twice in a row.

Characters (`who`): worker, workerF, banker, agent, agentF, hacker, guard, engineer, exec, crook, police, doctor, soldier, student.

| kind | shows | fields |
|---|---|---|
| `building` | isometric building with a name sign, lights flicker | `type`: bank / fbi / office / hospital / government / factory / police / airport / school / studio / power; `name` (the sign) |
| `office` | person at a desk with a computer | `who`, `action`: type / phone / shock / think / sleep, `screen` (short text on the monitor) |
| `hacker` | hooded attacker at a laptop in a dark room | `screen` (short text), `count` 1-3 people |
| `servers` | isometric server room | `state`: ok / alarm / dark, `label` |
| `people` | a group of characters | `who`: list of roles, `action`: talk / shock / point / walk / cheer / arrest, `label` |
| `phone` | smartphone mockup | `app`: email / chat / call / alert / bank, `from`, `text` |
| `email` | computer email window, the bad line highlighted | `from`, `subject`, `line` |
| `object` | one hero object, animated | `icon`: printer / usb / laptop / money / clock / calendar / envelope / key / file / wifi / camera / plane / ship / car / atm / card / bitcoin / skull / bug / shield / satellite / pipeline / bulb; `text` |
| `network` | infection spreading across computers | `text`, `total` (number for live counter) |
| `globe` | world globe with attack arcs | `points`: list of [place, lat, lon], 2-4 places far apart |
| `flow` | money or data moving between parties | `nodes`: 2-4 names, `amount`, `blocked`: true/false |
| `counter` | big number counting up | `value`, `prefix`, `suffix`, `label` |
| `timeline` | dated steps | `items`: list of [date, event], 2-4 items |
| `lock` | padlock | `state`: locked / open / crack, `text` |
| `terminal` | code window typing harmless lines | `lines`: 2-4 short lines |
| `dossier` | profile card of a named group or charged person | `title`, `rows`: list of [field, value] |
| `headline` | news card | `text` |
| `stamp` | document stamped | `text` (CLASSIFIED / CHARGED / WANTED / HACKED) |
| `split` | two sides compared | `left`, `right` |

Text on screen is never repeated twice at the same time; captions already carry the words, so graphic text adds information (a name, a number, a date).

## JSON (file `shorts/NNN-<key>.json`, NNN = the case's episode number from data/cases.json)
```json
{"episode": 3, "key": "bangladesh", "title": "...", "year": 2016, "category": "state", "pillar": "cyber", "slot_type": "curiosity", "needs_review": false, "review_note": "",
 "hooks": ["5 candidate opening lines"], "hook_type": "shocking_fact", "score": {"audience": 18, "story": 18, "hook": 14, "interest": 9, "share": 9, "visual": 9, "reliability": 10, "total": 87},
 "scenes": [{"id": 1, "mood": "shock", "narration": "[serious] ...", "visuals": [{"at": "exact words", "kind": "building", "type": "bank", "name": "Bangladesh Bank"}]}],
 "facts": [{"claim": "...", "source": "https://...", "confidence": "confirmed|reported|alleged"}],
 "sources": ["https://..."],
 "seo": {"title": "<= 70 chars, subject first, curiosity, honest", "description": "2-3 sentences of real context + 2-4 hashtags", "hashtags": ["#cybersecurity", "#truecrime", "#shorts"], "tags": ["descriptive tags"], "fb_title": "Facebook title", "facebook_text": "natural caption + 3-5 hashtags", "first_comment": "a question to spark discussion", "thumb": {"text": "A TYPO SAVED $1 BILLION", "hl": "$1 BILLION", "visual": 1}}}
```
Audio tags in [square brackets] are allowed sparingly (max 6): [serious], [whispers], [dramatically], [pause], [short pause], [sighs].
Run `python3 tools/validate_short.py shorts/NNN-key.json` and fix every ERROR.

## Thumbnail (cover) - every Short
`seo.thumb.text`: 3-6 huge words that make people curious and are TRUE (no clickbait lies), e.g. "A TYPO SAVED $1 BILLION", "ONE EMAIL SHUT DOWN A PIPELINE". `seo.thumb.hl`: the 1-3 words to paint yellow. `seo.thumb.visual`: index (0-based, across all visuals) of the picture shown behind the text (pick the most dramatic one).
The engine draws a high-contrast cover (dark top, giant white/yellow text with thick outline, red highlight) and (a) uploads it as the YouTube custom thumbnail, (b) shows it in the very first 0.2 s of the video so feeds that use the first frame pick it.

## Timely stories (news of the week)
Each weekly batch should include 1-3 stories about cyber attacks reported THAT WEEK, if major, widely reported by reliable outlets (Reuters, AP, BBC, official statements, CISA/FBI, company filings). Only confirmed facts; blame is "alleged" unless officially attributed; no speculation. Add the case to data/cases.json with the next free episode number, and set `"priority": true` in the short so it is published first while it is news.

## Ending (LOCKED)
Every Short ends with the same pre-rendered 2.5 s logo animation `assets/brand/outro_vertical.mp4` (made once by tools/make_outro.py from the owner's logo). Never re-animate it per video; consistency is the point.
