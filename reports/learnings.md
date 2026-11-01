# Learnings (append a dated section every weekly review)

## 2026-11-01 (week 1 review, automated)
Data: 5 published Shorts (003, 001, 101, 102, 103). YouTube Analytics (engaged views, avg % viewed) is not reported yet for any of them, and only 001 has a 6h snapshot with >500 views; no Short has a 24h/48h/7d comparison with 3+ Shorts. **Not enough data yet to conclude anything.** Raw numbers only:
- 001 Sony (curiosity, 12:00 PM slot): 891 YT views / 17 likes at ~9h; FB 14 plays. Best YT start by far.
- 102 GMO: 186 YT views / 2 likes at 1h; FB 59.
- 003 Bangladesh: 73 YT views / 0 likes at 38h; but FB 221 plays (best FB so far).
- 101 Binance: 46 YT views / 1 like at 6h; FB 60.
- 103 UNM Hospital: no snapshot yet.
Observation only (n=5, not a rule): the same story did very differently per platform (003 weak on YT, best on FB; 001 the reverse), so keep metadata platform-specific.
Gap found: published JSONs have no `hook_type`, `pillar`, `slot_type` or `score`, so winners cannot be grouped by hook type or pillar yet. Fix in the next batch.

Rules for next week:
1. Every new Short must set `hook_type`, `pillar`, `slot_type` (validator already warns) so the 7d comparison can group by them.
2. Do not draw conclusions until 3+ Shorts have 48h/7d engaged-view and avg % viewed data; compare at the same age only.
3. Keep thumbnail/title lead with a concrete number or object (001 "A COMEDY GOT SONY HACKED" is the early leader); change one variable at a time (hook wording OR thumb wording) so a difference can be attributed.

Slot times: no slot has 2+ weeks of data, no proposal.

Metadata changes this review (unpublished 002, 004-026): hashtags made story-specific (2-4 YouTube, instead of the same three on every Short), a natural search-intent sentence added to each description, descriptive `tags` added. Facts, narration, titles, thumbs and first comments unchanged (already match the spec).
