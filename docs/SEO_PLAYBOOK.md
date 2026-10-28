# Breach Uncovered - SEO playbook (verified facts only)

Rule from the owner: **never guess.** Every item below has a source or is marked "unverified". The weekly SEO audit (scheduled task) re-checks this file against current official guidance and the latest `reports/seo-report.md` numbers, and fixes the code.

## A. Official statements (primary sources)
YouTube Help - "YouTube performance FAQ & Troubleshooting" (https://support.google.com/youtube/answer/141805):
- Search is ranked by how well title, description and video content match the query, plus which videos drive the most engagement for that search.
- Home/Up Next are ranked by how well a video satisfied similar viewers; watch time (absolute and relative) and audience retention are the engagement signals YouTube names.
- Use accurate, compelling titles and thumbnails; avoid misleading, clickbait, shocking or "loud" (ALL CAPS, excessive punctuation) titles/thumbnails. Changing a title/thumbnail only matters through how viewers respond - do not change what works.
- Tags are not important (only help with common misspellings). Upload frequency is not correlated with views. Publish time does not affect long-term performance (only Live/Premiere). Location settings are not used for recommendations.
YouTube Help - "Inauthentic content" (https://support.google.com/youtube/answer/1311392): mass-produced / templated / repetitive videos are not monetizable; series with a distinct storyline per video are fine.
YouTube Help - altered/synthetic content disclosure (https://support.google.com/youtube/answer/14328491): disclosure only for realistic synthetic people/events; AI scripts/thumbnails/titles do not need it.
Meta, summarised by Social Media Today (https://www.socialmediatoday.com/news/meta-provides-new-insights-into-how-its-video-distribution-algorithms-work/631106): Facebook ranks original video; reads retention (early drop-off is a negative signal); repeat viewing / loyalty is a strong signal (multi-video storytelling); conversation between real people; clear titles, descriptions and a few relevant tags help Facebook search. Reduced distribution for: mostly static-image videos, re-shared content, engagement bait, clickbait/watchbait.

## B. What the pipeline already does (tools/seo.py, youtube.py, facebook.py)
- Keyword once in the title, naturally; first description line carries the keyword; chapters from 0:00 from the scene labels; exactly 3 hashtags; tags limited and secondary.
- Custom 1280x720 thumbnail (<2 MB) per video; English captions (SRT) uploaded to YouTube and Facebook; burned-in word-synced captions in the video.
- Playlist "All Case Files" (retry on transient errors); first comment with a discussion question (YouTube + Facebook); Facebook text with a hook line and no links.
- Facebook targeting US/UK/CA/AU (best effort), 16:9 original video, scheduled posting.
- Content: plain spoken English, 5-second hook, a new story and new footage in every video (anti-"inauthentic" rule), mostly video footage (Facebook penalises static-image videos).
- Title/thumbnail language: accurate to the story, no invented claims.

## C. Cannot be automated by API (do manually in YouTube Studio if wanted)
- End screens and cards (not in the Data API), pinned comment (API cannot pin), channel trailer, channel keywords/banner, community posts.

## D. Watch items (not verified - test, do not assume)
- Thumbnails use bold UPPERCASE text. Official guidance warns against "loud" ALL CAPS; the thumbnail text itself is a design convention, but compare CTR of mixed-case vs caps thumbnails when the report has CTR data (YouTube Analytics API).
- Whether 23:00 / 05:00 Bangladesh time (US lunch / evening) matters: YouTube says publish time does not affect long-term performance; keep as is, do not optimise further.
- Ranking-weight claims from vendor blogs (CTR > retention etc.) are opinion; decide only from our own report numbers.

## E. Weekly audit checklist (for the scheduled task)
1. Read `reports/seo-report.md`: views, CTR, average view duration/percentage, subscribers per video; Facebook views.
2. Find the best and worst two videos; compare title, thumbnail, hook, first 30 s retention; write findings to `reports/seo-findings.md`.
3. Re-check sections A-D against official YouTube/Meta pages (search the web; do not guess); update this file with source links and dates.
4. Fix code/spec/templates when evidence supports it (tools/seo.py, docs/SCRIPT_SPEC.md), keep changes small, validate scripts, push.
5. List what the owner must do manually (section C) and anything unavailable (e.g. Analytics API not enabled).
