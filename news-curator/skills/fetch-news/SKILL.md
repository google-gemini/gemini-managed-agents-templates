---
name: fetch-news
description: Pulls the latest Google News and Hacker News items for every topic and genre in the reader's interests, deduped against every item shown in previous runs.
---

# Fetch News Skill

Use this skill at the start of every sweep. It queries two public sources —
no account, credentials, or API key required for either — and owns the
cross-run dedupe state:

- **Google News RSS** (`news.google.com`) — a search feed per topic plus a
  headline feed per genre (`WORLD`, `NATION`, `BUSINESS`, `TECHNOLOGY`,
  `ENTERTAINMENT`, `SCIENCE`, `SPORTS`, `HEALTH`)
- **Hacker News** via the Algolia search API (`hn.algolia.com`) — stories and
  comments per topic, for the community-buzz angle
- **Medium RSS** (`medium.com`) — long-form posts per tag from
  `interests.json`'s `medium_tags`, for the practitioner-writing angle

## Usage

```bash
python3 skills/fetch-news/scripts/fetch_news.py
```

Topics, genres, and the per-topic cap all come from
`.agents/workspace/interests.json` — change that file, not the script.

The script:
1. Reads the interests profile.
2. Fetches every topic (both sources) and every genre (Google News). If a
   source fails for one topic, the sweep continues and records the error in
   `source_errors`.
3. Drops every item whose id is already in `.agents/workspace/seen_items.json`,
   then adds the new ids to that file (bootstrapping it on the first run).
4. Writes the fresh items to `.agents/workspace/new_items.json` and prints them
   to stdout, with a one-line summary on stderr.

## Output format (`new_items.json`)

```json
{
  "topics": ["Gemini API"],
  "genres": ["TECHNOLOGY"],
  "fetched_at": "2026-07-15T09:00:03Z",
  "source_errors": [],
  "new_count": 42,
  "items": [
    {
      "id": "gn:CBMiXyz…",
      "source": "news",
      "outlet": "The Verge",
      "title": "…headline…",
      "context": null,
      "url": "https://news.google.com/rss/articles/…",
      "published": "2026-07-15T08:12:44Z",
      "engagement": null,
      "topic": "Gemini API"
    },
    {
      "id": "hn:44581234",
      "source": "community",
      "outlet": "Hacker News (comment by example_dev)",
      "title": "…comment text…",
      "context": "Title of the story the comment is on",
      "url": "https://news.ycombinator.com/item?id=44581234",
      "published": "2026-07-15T07:03:10Z",
      "engagement": 12,
      "topic": "Gemini API"
    }
  ]
}
```

`source` is `news` (Google News), `community` (Hacker News), or `longform`
(Medium, with ids prefixed `md:` and `topic: "medium:<tag>"`). `engagement`
is only present for community items (points or comment count). Genre items
carry `topic: "genre:<name>"`.

## Instructions for the Agent

- Run this exactly once per sweep. Running it twice in one sweep marks items
  as seen without you having curated them.
- Treat `items` as the complete candidate pool for the sweep. `new_count: 0`
  means a quiet interval — still write the briefing.
- If `source_errors` is non-empty, name the degraded source in the briefing —
  the counts only cover the sources that responded.
