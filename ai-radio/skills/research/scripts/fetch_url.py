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
"""Fetch and extract content from any URL for AI Talk Radio research.

Usage:
    python3 fetch_url.py --url https://example.com/blog-post --workspace ./workspace
    python3 fetch_url.py --url https://arxiv.org/abs/2401.12345 --workspace ./workspace

Output:
    {workspace}/data/research/url_content.md
"""

import argparse
import os
import re
import urllib.request
from datetime import datetime


def fetch_page(url):
    """Fetch raw HTML/text from a URL."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "AI-Radio/1.0 (Content Research)",
        "Accept": "text/html,application/xhtml+xml,text/plain,*/*",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_html(html):
    """Basic HTML to text conversion using stdlib only."""
    # Remove script and style blocks
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<nav[^>]*>.*?</nav>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<footer[^>]*>.*?</footer>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<header[^>]*>.*?</header>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Convert common elements to markdown
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<p[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</p>', '\n', text, flags=re.IGNORECASE)

    # Strip remaining tags
    text = re.sub(r'<[^>]+>', '', text)

    # Decode HTML entities
    for old, new in [
        ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
        ('&quot;', '"'), ('&#39;', "'"), ('&nbsp;', ' '),
        ('&#x27;', "'"), ('&mdash;', '—'), ('&ndash;', '–'),
    ]:
        text = text.replace(old, new)

    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


def extract_title(html):
    """Extract page title from HTML."""
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if match:
        title = match.group(1).strip()
        title = re.sub(r'<[^>]+>', '', title)
        return title
    return None


def extract_meta_description(html):
    """Extract meta description."""
    match = re.search(
        r'<meta[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']',
        html, re.IGNORECASE
    )
    if match:
        return match.group(1).strip()
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch URL content for AI Talk Radio")
    parser.add_argument("--url", required=True, help="URL to fetch content from")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument("--max-chars", type=int, default=8000, help="Max chars to extract")
    args = parser.parse_args()

    out_dir = os.path.join(args.workspace, "data", "research")
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== AI Talk Radio Research: URL Content ===")
    print(f"URL: {args.url}\n")

    print("Fetching page...")
    html = fetch_page(args.url)
    print(f"  Got {len(html)} bytes of HTML")

    # Extract metadata
    title = extract_title(html) or args.url
    description = extract_meta_description(html)

    # Convert to text
    print("Extracting text content...")
    text = strip_html(html)

    # Truncate if too long
    if len(text) > args.max_chars:
        text = text[:args.max_chars]
        text += f"\n\n*(content truncated at {args.max_chars} characters)*"

    print(f"  Extracted {len(text)} chars of text")

    # Build markdown
    lines = [f"# URL Content: {title} — {datetime.now().strftime('%B %d, %Y')}\n"]
    lines.append(f"- **Source URL**: {args.url}")
    if description:
        lines.append(f"- **Description**: {description}")
    lines.append("")
    lines.append("## Content\n")
    lines.append(text)
    lines.append("\n---\n")

    # Generate a safe filename from the URL
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', args.url)[:60]
    out_path = os.path.join(out_dir, f"url_{safe_name}.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Research saved to {out_path}")
    print(f"   Title: {title}")
    print(f"   Content length: {len(text)} chars")


if __name__ == "__main__":
    main()
