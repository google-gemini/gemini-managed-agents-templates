---
name: briefing
description: Formats the standalone daily briefing — curated picks with why-it-matters lines, community buzz, the trend read across runs, and the taste note that keeps the learning visible.
---

# Briefing Skill

Use this skill to end every sweep. The briefing is the run's product: it must
be fully understandable by someone who reads nothing else — no "as I
mentioned", no open questions, no references to the conversation.

## Instructions for the Agent

Write `.agents/workspace/briefings/<YYYY-MM-DD-HHMM>.md` (UTC, from `date -u`).
Create the `briefings/` directory if needed.

> [!IMPORTANT]
> **Exact structure required.** The delivery step parses this file to build
> the chat message, so follow the heading structure precisely:
> - the title is a single `#` line,
> - each section is a `##` line,
> - **every item** — in every section — is a `### [headline] — [source]`
>   line, followed by its why-it-matters sentence, followed by a link line
>   `[Source Link](url)`.
>
> Do NOT use tables, bullet lists for items, or any other layout for the
> curated items. The `###`-heading-plus-link shape is what makes each
> headline render as a clean clickable link. (Trends, Taste Note, and Data
> Health are prose/bullets, not items — they have no `###` entries.)

Use this exact layout:

```markdown
# Daily Briefing — [date] — [reader's topics, comma-separated]

## Top Stories
### [headline] — [outlet]
[1-2 sentences: why this matters to THIS reader, tied to their topics or
stated preferences. Mention breadth if multiple outlets covered it.]
[Source Link](url)

### [headline] — [outlet]
[why-it-matters sentence]
[Source Link](url)

## Discoveries
### [headline] — [outlet]
[one line on why this genre-feed item outside the explicit topics earned a slot]
[Source Link](url)

## Community Buzz
### [paraphrased comment/story hook] — Hacker News, [n] points
[One line on what the discussion adds beyond the news coverage.]
[Source Link](url)

## Worth a Longer Read
### [title] — Medium (by [author])
[one line on the depth it offers; member-only stories may be paywalled at the link]
[Source Link](url)

## Trends
[2-4 sentences computed from curation_history.csv: which topics are heating
up or cooling across sweeps, with the numbers cited
("Gemini API: 4 → 9 → 15 items over the last three sweeps").
First run: "First sweep — trend data starts today."]

## Taste Note
[1-3 sentences: which stored preferences shaped today's selection, any
profile change made since the last run, and — at most once per week — one
question-free observation the reader could correct
(e.g. "I've been down-ranking funding news per your 2026-07-15 note.").]

## Data Health
- Fetched: [new_count] new items ([x] news, [y] community, [z] longform) · History rows: [line count of curation_history.csv]
- [Source errors from new_items.json verbatim, or "All sources healthy."]
```

Rules:
1. Omit an entire section (its `##` header included) when nothing qualified —
   never emit an empty section or a placeholder item.
2. Every item links to its source. Headlines may be lightly trimmed but never
   rewritten into something the outlet did not say.
3. Community items are paraphrased (≤ 25 words) — never reproduce full comment
   text.
4. Every number is derived, never guessed: `Fetched` counts come from
   `new_items.json` (`new_count` and the per-item `source` field), and
   `History rows` from the line count of `curation_history.csv`. If you cannot
   derive a number, omit it rather than estimate.
5. The Taste Note never asks a question — scheduled runs have no one to answer.
   It states, in declarative form, what the reader could correct in chat later.
6. Keep it plain and factual — no meta-commentary about cognitive load,
   utility, or attention; just the news and why it matters.
