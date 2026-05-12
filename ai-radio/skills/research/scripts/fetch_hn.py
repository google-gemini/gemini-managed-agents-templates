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
"""Fetch Hacker News stories in two phases: scan, then deep-dive.

Phase 1 — Scan (agent picks what's interesting):
    python3 fetch_hn.py --workspace ./workspace --mode scan --top 10

Phase 2 — Deep-dive (agent tells us which stories to expand):
    python3 fetch_hn.py --workspace ./workspace --mode deep-dive --stories 43210987,43209876,43208765

Output:
    scan:       {workspace}/data/research/hn-scan.md
    deep-dive:  {workspace}/data/research/hacker-news.md
"""

import argparse
import json
import os
import re
import time
import urllib.request
from datetime import datetime

BASE_URL = "https://hacker-news.firebaseio.com/v0"


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "AI-Radio/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def fetch_item(item_id):
    return fetch_json(f"{BASE_URL}/item/{item_id}.json")


def strip_html(text):
    for old, new in [
        ("<p>", "\n"), ("</p>", ""), ("<i>", ""), ("</i>", ""),
        ("<b>", ""), ("</b>", ""), ("&#x27;", "'"), ("&amp;", "&"),
        ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'),
    ]:
        text = text.replace(old, new)
    text = re.sub(r'<a[^>]*>', '', text)
    text = text.replace("</a>", "")
    return text.strip()


def fetch_top_comments(story, max_comments=12):
    kid_ids = story.get("kids", [])[:max_comments]
    comments = []
    for kid_id in kid_ids:
        try:
            c = fetch_item(kid_id)
            if c and c.get("text") and not c.get("deleted") and not c.get("dead"):
                comments.append({
                    "by": c.get("by", "anon"),
                    "text": strip_html(c["text"])[:500],
                })
            time.sleep(0.1)
        except Exception:
            continue
    return comments


# ──────────────────────────────────────────────
# Phase 1: Scan — lightweight metadata only
# ──────────────────────────────────────────────

def do_scan(args):
    """Fetch top N story titles, scores, and comment counts. No deep-diving."""
    out_dir = os.path.join(args.workspace, "data", "research")
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== AI Talk Radio Research: HN Scan (top {args.top}) ===\n")
    print("Fetching story metadata (no comments)...")

    top_ids = fetch_json(f"{BASE_URL}/topstories.json")[:args.top]

    stories = []
    for sid in top_ids:
        try:
            s = fetch_item(sid)
            if s and s.get("title"):
                stories.append(s)
            time.sleep(0.1)
        except Exception:
            continue

    # Build scan output
    lines = [f"# Hacker News — Top {len(stories)} Stories ({datetime.now().strftime('%B %d, %Y')})"]
    lines.append("")
    lines.append("Pick the 2-3 stories that would make the best radio discussion, then run:")
    lines.append("```")
    lines.append("python3 skills/research/scripts/fetch_hn.py --workspace ./workspace --mode deep-dive --stories <id1>,<id2>,<id3>")
    lines.append("```")
    lines.append("")

    for idx, s in enumerate(stories, 1):
        sid = s["id"]
        title = s.get("title", "Untitled")
        url = s.get("url", "")
        score = s.get("score", 0)
        comments = s.get("descendants", 0)
        by = s.get("by", "unknown")

        lines.append(f"### {idx}. {title}")
        lines.append(f"- **ID**: `{sid}`")
        lines.append(f"- **Score**: {score} points | **Comments**: {comments}")
        lines.append(f"- **By**: {by}")
        if url:
            lines.append(f"- **URL**: {url}")
        lines.append("")

        print(f"  {idx}. [{score}pts, {comments}c] {title}")

    out_path = os.path.join(out_dir, "hn-scan.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Scan saved to {out_path}")
    print(f"   {len(stories)} stories — now pick the interesting ones and run deep-dive.")


# ──────────────────────────────────────────────
# Phase 2: Deep-dive — full comments for selected stories
# ──────────────────────────────────────────────

def do_deep_dive(args):
    """Fetch full comment threads for specific story IDs."""
    out_dir = os.path.join(args.workspace, "data", "research")
    os.makedirs(out_dir, exist_ok=True)

    story_ids = [int(sid.strip()) for sid in args.stories.split(",") if sid.strip()]
    print(f"=== AI Talk Radio Research: HN Deep Dive ({len(story_ids)} stories) ===\n")

    lines = [f"# Hacker News Deep Dive — {datetime.now().strftime('%B %d, %Y')}\n"]

    for idx, sid in enumerate(story_ids, 1):
        try:
            story = fetch_item(sid)
        except Exception as e:
            print(f"  ✗ Failed to fetch story {sid}: {e}")
            continue

        title = story.get("title", "Untitled")
        url = story.get("url", f"https://news.ycombinator.com/item?id={sid}")
        hn_url = f"https://news.ycombinator.com/item?id={sid}"
        points = story.get("score", 0)
        comment_count = story.get("descendants", 0)

        print(f"--- Story {idx}: {title} ---")
        comments = fetch_top_comments(story)
        print(f"    Got {len(comments)} top-level comments.\n")

        lines.append(f"## {idx}. {title}")
        lines.append(f"- **URL**: {url}")
        lines.append(f"- **HN Thread**: {hn_url}")
        lines.append(f"- **Points**: {points} | **Comments**: {comment_count}\n")

        if comments:
            lines.append("### The Discussion\n")
            for c in comments[:8]:
                lines.append(f"**{c['by']}**: {c['text']}\n")
        else:
            lines.append("*(No comments yet)*\n")
        lines.append("---\n")

    out_path = os.path.join(out_dir, "hacker-news.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Deep dive saved to {out_path}")
    print(f"   {len(story_ids)} stories with full comment analysis")


def main():
    parser = argparse.ArgumentParser(description="Fetch HN stories for AI Talk Radio")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument(
        "--mode",
        choices=["scan", "deep-dive"],
        required=True,
        help="scan = grab titles/metadata; deep-dive = fetch comments for selected stories",
    )
    parser.add_argument("--top", type=int, default=10, help="Number of stories to scan (scan mode)")
    parser.add_argument("--stories", help="Comma-separated story IDs to deep-dive (deep-dive mode)")
    args = parser.parse_args()

    if args.mode == "scan":
        do_scan(args)
    elif args.mode == "deep-dive":
        if not args.stories:
            print("ERROR: --stories is required for deep-dive mode")
            print("Usage: python3 fetch_hn.py --mode deep-dive --stories 12345,67890")
            return
        do_deep_dive(args)


if __name__ == "__main__":
    main()
