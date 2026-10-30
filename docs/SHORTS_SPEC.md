# Breach Uncovered - SHORTS spec (LOCKED by the owner, 2026-10-30)

The channel now publishes **only vertical Shorts** (YouTube Shorts + Facebook Reels): **3 per day**, each **30-50 seconds**, in English.
Every Short tells ONE complete true cyber-attack story from start to end, explained so simply that anyone understands it.
**100% of the picture is our own visualisation** (2D / semi-3D isometric illustrated motion graphics). No stock clips, no Pixabay, no photos, no AI video.
Voice: ElevenLabs `eleven_v4_turbo`, voice `oO7sLA3dWfQXsKeSAjpA`. Captions word-synced. Music and sound effects follow the mood.

## Story (85-125 words of narration)
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
{"episode": 3, "key": "bangladesh", "title": "...", "year": 2016, "category": "state", "needs_review": false, "review_note": "",
 "scenes": [{"id": 1, "mood": "shock", "narration": "[serious] ...", "visuals": [{"at": "exact words", "kind": "building", "type": "bank", "name": "Bangladesh Bank"}]}],
 "facts": [{"claim": "...", "source": "https://...", "confidence": "confirmed|reported|alleged"}],
 "sources": ["https://..."],
 "seo": {"title": "<= 70 chars, keyword first, curiosity, honest", "description": "2-3 sentences + 3 hashtags", "hashtags": ["#cybersecurity", "#truecrime", "#shorts"], "facebook_text": "hook line + 1 line + 3 hashtags", "first_comment": "a question to spark discussion"}}
```
Audio tags in [square brackets] are allowed sparingly (max 6): [serious], [whispers], [dramatically], [pause], [short pause], [sighs].
Run `python3 tools/validate_short.py shorts/NNN-key.json` and fix every ERROR.
