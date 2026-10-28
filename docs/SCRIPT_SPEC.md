# Breach Uncovered — episode script spec

Channel: English-language documentary storytelling about REAL hacks. Narrated by one ElevenLabs voice
(`oO7sLA3dWfQXsKeSAjpA`, model **`eleven_v4_turbo` ONLY — locked by the owner, no other model ever**). Output of this spec = one JSON file per episode in `scripts/`.

## Goal
A viewer who knows nothing about security should be unable to stop listening. Think investigative-podcast
storytelling: a cold open that grabs in 10 seconds, a human at the centre, rising tension, a twist, and a
consequence that lands. Every fact is real and sourced; the drama comes from structure, pacing and voice —
never from invented facts.

## LANGUAGE — the most important rule (owner feedback after episode 1)
Write the way a friend tells a true story over dinner. A 14-year-old who speaks English as a second language must follow every line.
- **Plain, everyday, spoken English.** Common words only ("hacked into", "stole", "found out", "got scared", not "infiltrated", "exfiltrated", "orchestrated", "ostensibly", "subsequently", "attributed to").
- **Short sentences** (average 8–14 words, none over 25). One idea per sentence. Use contractions (it's, they didn't, we'll).
- **Tell it as a STORY in time order**: who these people were -> what normal life looked like -> the first small thing that went wrong -> it gets worse -> people panic -> they work out who did it -> what it cost and what changed. The listener must always know who, where, when and what is happening now. Say the year/date early and keep time words ("that night", "two days later", "by morning").
- Name the people and companies, one or two at a time. Give each important person a simple handle on first use ("Kim, the IT guy"; only real roles from sources). Don't pile up names, acronyms or numbers: at most 2 big numbers per scene; round them ("about 100 terabytes" -> "a huge amount of data, about 100 terabytes").
- Explain any tech word in one plain sentence the first time, or avoid it. No jargon dumps, no lists of malware names.
- Feelings and stakes: show what it felt like for people (confusion, fear, anger) ONLY where sources support it; otherwise use neutral suspense ("Nobody knew what was coming.").
- Curiosity hooks: end most scenes with a line that makes the listener want the next scene (a question, a "but", a cliffhanger). Light humor/irony is fine when the facts allow it.
- Read it out loud: if you stumble, simplify. If a sentence needs re-reading, split it.
- Voice: write for ONE natural, warm, expressive narrator. Use audio tags (see Voice direction) so the delivery changes with the emotion of each moment: surprise, worry, calm explanation, sharp suspense, relief.

## Audience & SEO targeting (US-first, then UK / Canada / Australia)
Every word, title and tag is written for **native English speakers, US viewers first**.
- **American English**: spelling (organization, color, defense), idiom, dates as "November 24, 2014", money in $
  (convert only if the source is non-USD, and say "about $X"). Never Indian/Bangladeshi/translated English.
- Anchor foreign events to something an American instantly gets (scale: "more than the population of…",
  everyday objects, brands, US institutions) — one or two comparisons per script, accurate ones.
- Explain non-US agencies/places in half a sentence (e.g. "GCHQ, Britain's NSA").
- Titles/descriptions use the phrases an American would type into YouTube/Google: "how … was hacked",
  "the true story of …", "biggest cyberattack", "hacked", "explained", "documentary". Put the main keyword
  in the first 40 characters of the title and in the first line of the description.
- `search_terms` = real US search phrasing (e.g. "how was sony pictures hacked", "sony hack north korea explained").
- Tags: include the case name, the group/actor name, the year, "cyber attack", "true story", "hacking documentary",
  "cybersecurity", "cybercrime" plus 3–5 long-tail phrases. No non-English tags.
- Facebook text: conversational, US tone, first line is a scroll-stopping hook, asks a question; no hashtags spam (max 3).
- Never mention Bangladesh/the creator's location as the channel identity (a case *about* Bangladesh Bank is fine).

## Length (LOCKED by the owner, 2026-10-28)
**The finished video must be under 6 minutes** (target 5:00-5:40). That is **700-840 words** of narration (validator enforces it; the voice runs about 150 words per minute).
10-14 scenes, each one beat of the story (50-75 words, about 20-30 seconds). Every word must earn its place: cut background, keep the story.

## Story architecture (vary it — do not make every episode identical)
0. **THE 5-SECOND HOOK (non-negotiable).** The very first 1–2 sentences (about 5 seconds of speech, **at most 14 words in the first sentence**) must make a stranger think "wait, WHAT? I have to hear this." Use the single most shocking, strange or emotional TRUE detail of the story, stated simply: a startling number, a bizarre moment, a quiet question, a promise that something went terribly wrong. No setup, no greeting, no channel name, no "this is the story of". Examples of the right feel: "A single typo stopped a billion dollars from vanishing." / "Thousands of computers died at the same second, and nobody knew why." The hook is spoken with a strong audio tag ([dramatically], [whispers], [serious]) and its first 5 seconds get the fastest cuts.
1. **Cold open (≤ 80 words, no greeting, no channel name, no "today we'll look at").** It starts with the 5-second hook above, then explains it. Start mid-action, or with
   a startling real number, or with a real quote from the sources, or with the moment the victim noticed.
   Pick a *different* opener style from the neighbouring episodes.
2. **Stakes + who** — who was hit, why it mattered, in plain words.
3. **The quiet part** — how long the attackers were inside / how it began (patient, concrete, human).
4. **Escalation** — the moment it became undeniable.
5. **The scramble** — people reacting; the mistake, the twist, or the lucky break.
6. **The unmasking** — how investigators or luck revealed who did it (indictments, arrests, reports).
7. **Aftermath** — real consequences, what changed, one memorable closing line. Optional soft CTA
   ("If you like stories like this, subscribe to Breach Uncovered") — one sentence max, only at the very end.
   Never refer to "the previous/next episode/video".

Use: short sentences for tension, a longer one to breathe, rhetorical questions sparingly, "—" beats,
concrete details (dates, times, numbers, objects, places). Second-person ("you") only for a vivid moment or two.
Explain every technical term the first time in one plain sentence. Never lecture.

## HARD accuracy rules (non-negotiable)
- Research first with WebSearch/WebFetch. Prefer primary sources: DOJ/FBI/CISA/NCSC/Europol/court documents,
  company incident reports, then reputable journalism (Wired, Reuters, AP, BBC, Krebs, ArsTechnica, Guardian...).
- **Every number, date, name and quote in the narration must be supported by a source you actually read.**
  If sources disagree, use the safer wording ("roughly", "according to prosecutors").
- Do **not** invent dialogue, thoughts, motives, people, or scenes. "Imagine…" framing is allowed only for
  generic, plainly hypothetical colour ("Picture an operator staring at a screen…") and must not state facts.
- People not convicted: say "accused", "charged", "indicted", "according to the FBI". Attribution to a state
  = "the US government says / attributes". Convicted people: say so with year.
- No operational how-to: no exploit steps, commands, code, malware build details, or anything a viewer could
  reuse to attack. Explain *what happened and why it worked* at concept level only.
- No gore, no graphic violence, no hate. Keep it monetisation-safe.
- If a case in `data/cases.json` is thin or its note says the original source was wrong, find the real facts
  yourself; if you cannot verify enough for 5+ minutes, set `"needs_review": true` and explain in `review_note`.
- `sources_from_user_file` in cases.json are hints only — verify them.

## Voice direction (ElevenLabs `eleven_v4_turbo` — supports audio tags per ElevenLabs docs)
- Tags are free-form words in [square brackets] placed right before the words they colour; a tag holds until
  the next one. Use them where delivery **changes**, not every sentence. Target 8–25 tags per script.
- Good for this channel: `[serious]`, `[slowly]`, `[softly]`, `[whispers]`, `[dramatically]`, `[cautiously]`,
  `[nervous]`, `[curious]`, `[surprised]`, `[exhales]`, `[sighs]`, `[short pause]`, `[pause]`, `[long pause]`,
  `[deep voice]`, `[breathless]`, `[tired]`, `[sarcastic]` (rare).
- Describe how a line is *spoken*, not stage directions (`[pacing]`, `[music]` do nothing).
- Capitalise a word for emphasis very sparingly (max ~6 per script). Use "…" for a thoughtful pause and "—" for a beat.
- Numbers/dates in normal written form (digits), e.g. "$81 million", "November 24, 2014".
- Never put tags inside quoted source text unless the speaker's delivery is documented.
- No markdown, no stage directions, no sound-effect tags, no parentheses in `narration`.

## Visual direction - OWN MOTION GRAPHICS first, a few stock clips second (LOCKED by the owner, 2026-10-28)
The picture must CHANGE about every 3-4 seconds and match what the narrator says at that moment (**70-90 shots per episode**).
**At least 70% of the shots are our own full-frame motion graphics (`type: "gfx"`); stock/archival clips are at most 30%**, used only where a real place, building or scene is named and the clip clearly relates. Clips must contain no readable text. The look is a premium dark studio style (neon line work, glow, camera push-ins), like a high-end motion-graphics edit - never a slideshow of stock footage.
Each visual carries an `at` cue: a 2-5 word phrase copied EXACTLY (same words, any case) from that scene's narration; the shot starts when the narrator says it. Order the visuals as they are spoken. Use mixed beats inside a scene (for example gfx, gfx, clip, gfx, gfx). Vary the graphic kinds: no single kind more than 25% of the gfx shots (max 4 uses if the episode is short).

### `type: "gfx"` - fields: `kind`, `text` (short headline, <= 6 words, optional), `label` (small yellow line above the captions, <= 5 words, optional), `data` (kind specific), `at`
Think about what the narrator is explaining and draw it:
- `network` - spreading infection across many computers. `text`: what is spreading, `data: {"total": 48000}` makes a live counter.
- `globe` - a rotating globe with attack arcs. `data`: a list of `[place, latitude, longitude]` (2-4 places, pick places FAR apart so labels do not collide: for example `[["Pyongyang", 39.0, 125.7], ["Dhaka", 23.8, 90.4], ["New York", 40.7, -74.0]]`). Arcs are drawn from each place to the next.
- `rack` - a grid of screens that go dark one by one (wipers, outages, ransomware). `text`: what died, `data: {"total": 48000}` for the live count.
- `terminal` - a typing console. `text`: 2-6 short commands separated by `;`. Never real exploit code, only harmless illustrative lines.
- `counter` - a big gauge number counting up. `data: {"value": 81, "prefix": "$", "suffix": "M", "label": "stolen in hours"}`.
- `timeline` - dated steps on a line. `data`: 2-5 items `["2014", "Short event"]`, dates short, events <= 5 words.
- `lock` - a padlock. `data: {"state": "locked" | "open" | "crack"}` (open = the lock is bypassed, crack = broken). `text` optional.
- `email` - a phishing or fake-message mockup. `data: {"from": "hr@example-careers.com", "subject": "Your job offer", "line": "Open the attached file"}`. Use invented, obviously generic addresses, never a real person's address.
- `flow` - money or data moving between 2-4 parties. `data: {"nodes": ["Bangladesh Bank", "New York Fed", "Manila bank"], "amount": "$81M", "blocked": true}` (blocked puts a red X on the last link).
- `bars` - a comparison. `data: {"items": [["Sony", 100], ["Bank", 81]], "unit": "M"}`.
- `dossier` - a profile card for an attacker group. `text`: the name, `data: {"rows": [["Base", "North Korea"], ["Target", "Banks"]]}` (<= 5 rows, each value <= 4 words). Only for state groups or indicted people already named in public records.
- `headline` (a news card; `text` <= 10 words), `quote` (`text`: "words - Speaker", only quotes documented in the sources), `redact` (a classified document stamp; `text`: stamp word), `doc` (a document with a highlighted line; `text`: the line).
All text on a graphic is short (<= 8 words) and is never repeated on a second element at the same time. Numbers in a graphic must be facts listed in `facts`.

### `type: "stock"` / `type: "archival"` (at most 30% of the shots)
- `stock`: Pixabay video. Query = 2-3 plain words that literally show the moment and contain NO readable text: "server room blue", "airplane takeoff", "city traffic night", "police car lights", "hospital corridor", "worried man office". Never reuse a query in an episode.
- `archival`: a real place/building/seal from Wikimedia Commons ("Sony Pictures Studios Culver City", "Federal Reserve Bank of New York building"). Never a private person's photo.
- `overlay` text on a clip: max 3 in the whole episode, <= 5 words.
- Scene field `mood`: one of `calm`, `curious`, `tense`, `shock`, `reveal`, `sad`, `hopeful` - drives music and sound effects. Vary moods across the episode.
- The old `motion` type is retired.

## JSON schema (file: `scripts/NNN-<key>.json`, NNN = zero-padded episode number)
```json
{
  "episode": 1, "key": "sony", "title": "Sony Pictures hack — the Guardians of Peace", "year": 2014,
  "category": "state", "needs_review": false, "review_note": "",
  "scenes": [
    {"id": 1, "act": "cold_open", "label": "The skeleton on the screen", "mood": "shock",
     "narration": "[serious] ... text with tags ...",
     "visuals": [
       {"type": "gfx", "kind": "rack", "text": "Screens go dark", "data": {"total": 48000}, "at": "words from the narration"},
       {"type": "archival", "query": "Sony Pictures Studios Culver City", "at": "another phrase"},
       {"type": "gfx", "kind": "timeline", "data": [["2014", "Hack begins"], ["Nov 24", "Screens go red"]], "at": "a third phrase"}
     ]}
  ],
  "facts": [
    {"claim": "…", "source": "https://…", "confidence": "confirmed|reported|alleged"}
  ],
  "sources": ["https://…", "https://…"],
  "seo": {
    "youtube_title": "≤ 70 chars, primary keyword + curiosity gap, no ALL-CAPS, no clickbait lies",
    "youtube_description": "First 2 lines = keyword-rich hook (shown before 'Show more'). Then 2 short paragraphs summarising the real story (≥ 800 chars total), then the literal line {{CHAPTERS}}, then 'Sources:' with 3–6 URLs, then a short disclaimer line: 'Educational documentary based on public records. No hacking instructions.', then exactly 3 hashtags.",
    "tags": ["10–18 tags, total ≤ 450 chars, mix of broad + specific"],
    "hashtags": ["#cybersecurity", "#truecrime", "#<case>"],
    "thumb": {"line1": "≤ 16 chars", "line2": "≤ 16 chars (accent colour)", "tag": "≤ 28 chars, e.g. NORTH KOREA VS HOLLYWOOD"},
    "facebook_text": "Hook line, blank line, 3 short bullets (real facts), blank line, 3 hashtags. No links.",
    "first_comment": "A question that sparks discussion about the case. No links.",
    "search_terms": ["the 5–8 phrases people really search for about this case"]
  }
}
```
Chapters: `scenes[].label` become chapter titles (the renderer computes timestamps). Labels ≤ 40 chars, curiosity-style,
the first label must describe the opening scene (YouTube needs a 0:00 chapter). 3+ chapters at ≥10 s each.

## Self-check before finishing each file
Run `python3 tools/validate_script.py scripts/NNN-key.json` and fix every ERROR. Re-read the narration aloud
in your head: would a stranger keep listening past 20 seconds? Does each scene end by pulling into the next?
