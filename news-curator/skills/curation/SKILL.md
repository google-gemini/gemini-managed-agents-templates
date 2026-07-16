---
name: curation
description: Selection and ranking rules — how to turn the raw fetched pool into the handful of items the reader actually wants, guided by the taste profile in interests.json.
---

# Curation Skill

Curation is editing, not summarizing. From the candidate pool in
`new_items.json`, choose the items this specific reader should see today.

## Selection Rules

1. **The taste profile decides.** Re-read `interests.json` before selecting.
   `preferences.more` entries boost an item; `preferences.less` entries drop it
   unless it is genuinely major; `preferences.notes` carry dated, specific
   guidance from past feedback — treat recent notes as the strongest signal.
2. **Cap the briefing at 10 news items total** across all topics, and up to 4
   community-buzz items. Fewer is fine; padding is not. If a topic produced
   nothing worth including, say so in one line rather than including filler.
3. **Prefer, in order**: primary sources and official announcements → original
   reporting → high-engagement community discussion → aggregation/commentary.
   Drop listicles and rumor pieces by default (they are on the default
   `less` list).
4. **Collapse duplicates of one story.** When several outlets carry the same
   development, pick the strongest single link and mention coverage breadth in
   the why-it-matters line ("also covered by Reuters and The Verge") — breadth
   itself is a signal the story matters.
5. **Genre feeds are the serendipity channel.** Pick at most 2-3 genre items
   the reader did not explicitly ask about but would plausibly care about,
   given their profile. Label them as discoveries.
6. **Community items are for signal, not noise.** Select a Hacker News item
   only when it adds something the news coverage lacks: practitioner
   experience, technical pushback, or early buzz on something not yet covered.
7. **Longform earns its slot with depth.** Select at most 2 Medium pieces per
   briefing, and only for genuine substance — tutorials, architecture
   write-ups, first-hand experience reports. Medium has no engagement signal
   in the feed, so judge entirely on title substance and taste-profile fit;
   skip anything that reads as engagement-bait or paywalled teaser fluff.

## Ranking Within the Briefing

Lead with the item that best combines: relevance to an explicit topic,
recency, source quality, and taste-profile fit. Genre discoveries and
community buzz always come after the reader's explicit topics.

## What Never Gets Selected

- Items you cannot link.
- Items whose headline alone is too thin to say why it matters — do not pad
  with invented detail.
- Pure engagement-bait framed as news, regardless of topic match.
