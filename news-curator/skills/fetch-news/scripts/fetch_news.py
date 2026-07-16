#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Fetch fresh news and community discussion for the reader's interests,
deduped across runs.

Sources (all public, no account or API key required):
  - Google News RSS: search feed per topic + headline feed per genre
  - Hacker News via the Algolia search API: stories + comments per topic
  - Medium RSS: long-form posts per tag (e.g. medium.com/feed/tag/gemini)

The cross-run seen-set lives in the workspace so a scheduled Trigger only
ever surfaces items it has not shown before. If a source fails, the sweep
continues with the others and records the failure in the output.
"""

import html
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

GOOGLE_NEWS_BASE = "https://news.google.com/rss"
HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
MEDIUM_FEED_BASE = "https://medium.com/feed/tag"
DC_CREATOR = "{http://purl.org/dc/elements/1.1/}creator"
FEED_LOCALE = "hl=en-US&gl=US&ceid=US:en"
VALID_GENRES = {"WORLD", "NATION", "BUSINESS", "TECHNOLOGY", "ENTERTAINMENT",
                "SCIENCE", "SPORTS", "HEALTH"}
SEEN_CAP = 8000  # keep the dedupe file bounded across long-lived schedules

WORKSPACE_CANDIDATES = [
    Path(".agents/workspace"),
    Path("/.agents/workspace"),
    Path("workspace"),
]


def find_workspace():
    for candidate in WORKSPACE_CANDIDATES:
        if (candidate / "interests.json").exists():
            return candidate
    sys.exit("Error: could not locate workspace containing interests.json")


def http_get(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "gemini-managed-agent-news-curator/1.0"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def clean_text(text):
    return html.unescape(re.sub(r"<[^>]+>", " ", text or "")).strip()


def iso_date(rfc822):
    try:
        return parsedate_to_datetime(rfc822).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:
        return rfc822 or ""


def parse_google_rss(xml_text, topic, limit):
    items = []
    for item in ET.fromstring(xml_text).iter("item"):
        title = clean_text(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        if not title or not guid:
            continue
        outlet = clean_text(item.findtext("source")) or "unknown"
        # Google News titles end with " - Outlet"; drop the duplication.
        if outlet != "unknown" and title.endswith(f"- {outlet}"):
            title = title[: -len(outlet) - 2].strip()
        items.append({
            "id": "gn:" + guid[-64:],
            "source": "news",
            "outlet": outlet,
            "title": title[:300],
            "context": None,
            "url": link,
            "published": iso_date(item.findtext("pubDate")),
            "engagement": None,
            "topic": topic,
        })
        if len(items) >= limit:
            break
    return items


def fetch_topic_news(topic, limit):
    query = urllib.parse.quote(topic)
    url = f"{GOOGLE_NEWS_BASE}/search?q={query}&{FEED_LOCALE}"
    return parse_google_rss(http_get(url), topic, limit)


def fetch_genre_news(genre, limit):
    genre = genre.upper()
    if genre not in VALID_GENRES:
        raise ValueError(f"unknown genre {genre!r}; valid: {', '.join(sorted(VALID_GENRES))}")
    url = f"{GOOGLE_NEWS_BASE}/headlines/section/topic/{genre}?{FEED_LOCALE}"
    return parse_google_rss(http_get(url), f"genre:{genre.lower()}", limit)


def fetch_hackernews(topic, limit):
    params = urllib.parse.urlencode({
        "query": topic, "tags": "(story,comment)", "hitsPerPage": limit,
    })
    hits = json.loads(http_get(f"{HN_SEARCH_URL}?{params}")).get("hits", [])
    items = []
    for hit in hits:
        object_id = hit.get("objectID")
        if not object_id:
            continue
        is_story = hit.get("title") is not None
        text = hit.get("title") if is_story else clean_text(hit.get("comment_text"))
        if not text:
            continue
        items.append({
            "id": f"hn:{object_id}",
            "source": "community",
            "outlet": f"Hacker News ({'story' if is_story else 'comment'} by {hit.get('author', 'unknown')})",
            "title": text[:300] if is_story else text[:500],
            "context": None if is_story else hit.get("story_title"),
            "url": f"https://news.ycombinator.com/item?id={object_id}",
            "published": (hit.get("created_at") or "").replace(".000Z", "Z"),
            "engagement": hit.get("points") or hit.get("num_comments") or 0,
            "topic": topic,
        })
    return items


def fetch_medium(tag, limit):
    tag = tag.strip().lstrip("#").lower().replace(" ", "-")
    xml_text = http_get(f"{MEDIUM_FEED_BASE}/{urllib.parse.quote(tag)}")
    items = []
    for item in ET.fromstring(xml_text).iter("item"):
        title = clean_text(item.findtext("title"))
        link = (item.findtext("link") or "").split("?")[0].strip()
        guid = (item.findtext("guid") or link).strip()
        if not title or not guid:
            continue
        author = clean_text(item.findtext(DC_CREATOR)) or "unknown"
        items.append({
            "id": "md:" + guid.rsplit("/", 1)[-1][-64:],
            "source": "longform",
            "outlet": f"Medium (by {author})",
            "title": title[:300],
            "context": None,
            "url": link,
            "published": iso_date(item.findtext("pubDate")),
            "engagement": None,
            "topic": f"medium:{tag}",
        })
        if len(items) >= limit:
            break
    return items


def main():
    workspace = find_workspace()
    interests = json.loads((workspace / "interests.json").read_text(encoding="utf-8"))
    topics = interests.get("topics", [])
    genres = interests.get("genres", [])
    medium_tags = interests.get("medium_tags", [])
    per_topic = int(interests.get("max_items_per_topic", 15))
    if not topics and not genres and not medium_tags:
        sys.exit("Error: interests.json has no topics, genres, or medium_tags to sweep.")

    seen_path = workspace / "seen_items.json"
    seen = []
    if seen_path.exists():
        seen = json.loads(seen_path.read_text(encoding="utf-8")).get("seen", [])
    seen_set = set(seen)

    fetched, errors = [], []
    for topic in topics:
        try:
            fetched += fetch_topic_news(topic, per_topic)
        except Exception as error:
            errors.append(f"google-news[{topic}]: {error}")
        try:
            fetched += fetch_hackernews(topic, max(3, per_topic // 3))
        except Exception as error:
            errors.append(f"hackernews[{topic}]: {error}")
    for genre in genres:
        try:
            fetched += fetch_genre_news(genre, per_topic)
        except Exception as error:
            errors.append(f"google-news[genre:{genre}]: {error}")
    for tag in medium_tags:
        try:
            fetched += fetch_medium(tag, max(3, per_topic // 3))
        except Exception as error:
            errors.append(f"medium[{tag}]: {error}")

    if errors and not fetched:
        sys.exit("Error: every source failed: " + "; ".join(errors))

    unique = {}
    for item in fetched:  # an item can match several topics; keep the first
        unique.setdefault(item["id"], item)
    new_items = [item for iid, item in unique.items() if iid not in seen_set]
    new_items.sort(key=lambda item: item["published"], reverse=True)

    seen.extend(item["id"] for item in new_items)
    seen = seen[-SEEN_CAP:]
    seen_path.write_text(json.dumps({"seen": seen}, indent=2), encoding="utf-8")

    result = {
        "topics": topics,
        "genres": genres,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_errors": errors,
        "new_count": len(new_items),
        "items": new_items,
    }
    (workspace / "new_items.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(
        f"Sweep complete: {len(unique)} unique items fetched across "
        f"{len(topics)} topics + {len(genres)} genres + {len(medium_tags)} medium tags "
        f"({len(new_items)} new after dedupe, {len(seen)} ids tracked)"
        + (f" — source errors: {'; '.join(errors)}" if errors else ""),
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
