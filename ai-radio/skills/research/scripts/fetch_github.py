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
"""Fetch GitHub repository activity for AI Talk Radio research.

Usage:
    python3 fetch_github.py --repo googleapis/python-genai --workspace ./workspace
    python3 fetch_github.py --repo https://github.com/google/generative-ai-python --workspace ./workspace

Output:
    {workspace}/data/research/github.md
"""

import argparse
import json
import os
import re
import time
import urllib.request
from datetime import datetime

API_BASE = "https://api.github.com"
HEADERS = {"User-Agent": "AI-Radio/1.0", "Accept": "application/vnd.github.v3+json"}


def fetch_json(url):
    """Fetch JSON from a URL with GitHub API headers."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def parse_repo(repo_input):
    """Parse 'owner/repo' from various input formats."""
    # Strip trailing slashes and .git
    repo_input = repo_input.rstrip("/").removesuffix(".git")

    # Full URL: https://github.com/owner/repo
    match = re.match(r"https?://github\.com/([^/]+/[^/]+)", repo_input)
    if match:
        return match.group(1)

    # Short form: owner/repo
    if "/" in repo_input and not repo_input.startswith("http"):
        return repo_input

    raise ValueError(f"Cannot parse repo from: {repo_input}. Use 'owner/repo' or a GitHub URL.")


def fetch_readme(owner_repo):
    """Fetch and decode the README."""
    try:
        data = fetch_json(f"{API_BASE}/repos/{owner_repo}/readme")
        import base64
        return base64.b64decode(data.get("content", "")).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠ Could not fetch README: {e}")
        return None


def fetch_releases(owner_repo, limit=5):
    """Fetch recent releases."""
    try:
        return fetch_json(f"{API_BASE}/repos/{owner_repo}/releases?per_page={limit}")
    except Exception as e:
        print(f"  ⚠ Could not fetch releases: {e}")
        return []


def fetch_issues(owner_repo, limit=10):
    """Fetch issues sorted by most comments (includes PRs)."""
    try:
        return fetch_json(
            f"{API_BASE}/repos/{owner_repo}/issues?sort=comments&direction=desc&state=all&per_page={limit}"
        )
    except Exception as e:
        print(f"  ⚠ Could not fetch issues: {e}")
        return []


def fetch_issue_comments(owner_repo, issue_number, limit=8):
    """Fetch top comments on an issue."""
    try:
        return fetch_json(
            f"{API_BASE}/repos/{owner_repo}/issues/{issue_number}/comments?per_page={limit}"
        )
    except Exception as e:
        return []


def fetch_repo_info(owner_repo):
    """Fetch basic repo metadata."""
    try:
        return fetch_json(f"{API_BASE}/repos/{owner_repo}")
    except Exception as e:
        print(f"  ⚠ Could not fetch repo info: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(description="Fetch GitHub repo activity for AI Talk Radio")
    parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo or full URL)")
    parser.add_argument("--workspace", default="workspace", help="Workspace directory")
    parser.add_argument("--releases", type=int, default=5, help="Number of releases to fetch")
    parser.add_argument("--issues", type=int, default=8, help="Number of issues to fetch")
    args = parser.parse_args()

    owner_repo = parse_repo(args.repo)
    out_dir = os.path.join(args.workspace, "data", "research")
    os.makedirs(out_dir, exist_ok=True)

    print(f"=== AI Talk Radio Research: GitHub Deep Dive ===")
    print(f"Repository: {owner_repo}\n")

    # Repo info
    print("Fetching repo info...")
    info = fetch_repo_info(owner_repo)
    time.sleep(0.5)

    # README
    print("Fetching README...")
    readme = fetch_readme(owner_repo)
    time.sleep(0.5)

    # Releases
    print(f"Fetching recent releases (up to {args.releases})...")
    releases = fetch_releases(owner_repo, args.releases)
    time.sleep(0.5)

    # Issues
    print(f"Fetching top issues by engagement (up to {args.issues})...")
    issues = fetch_issues(owner_repo, args.issues)

    # Build markdown
    lines = [f"# GitHub Deep Dive: {owner_repo} — {datetime.now().strftime('%B %d, %Y')}\n"]

    # Repo overview
    if info:
        lines.append("## Repository Overview\n")
        lines.append(f"- **Name**: {info.get('full_name', owner_repo)}")
        lines.append(f"- **Description**: {info.get('description', 'N/A')}")
        lines.append(f"- **Stars**: {info.get('stargazers_count', 0):,}")
        lines.append(f"- **Forks**: {info.get('forks_count', 0):,}")
        lines.append(f"- **Open Issues**: {info.get('open_issues_count', 0):,}")
        lines.append(f"- **Language**: {info.get('language', 'N/A')}")
        lines.append(f"- **License**: {info.get('license', {}).get('name', 'N/A') if info.get('license') else 'N/A'}")
        lines.append(f"- **URL**: https://github.com/{owner_repo}\n")

    # README summary (first 1000 chars)
    if readme:
        lines.append("## README (excerpt)\n")
        lines.append(readme[:1500])
        if len(readme) > 1500:
            lines.append(f"\n*(truncated — {len(readme)} chars total)*")
        lines.append("")

    # Releases
    if releases:
        lines.append(f"## Recent Releases ({len(releases)})\n")
        for rel in releases:
            tag = rel.get("tag_name", "?")
            name = rel.get("name", tag)
            date = rel.get("published_at", "")[:10]
            body = (rel.get("body") or "")[:600]
            lines.append(f"### {name} ({tag}) — {date}\n")
            if body:
                lines.append(body)
                if len(rel.get("body", "")) > 600:
                    lines.append("*(truncated)*")
            lines.append("")
    else:
        lines.append("## Releases\n\n*(No releases found)*\n")

    # Issues
    if issues:
        lines.append(f"## Hot Issues & Discussions ({len(issues)})\n")
        for issue in issues:
            title = issue.get("title", "Untitled")
            number = issue.get("number", 0)
            state = issue.get("state", "unknown")
            comments_count = issue.get("comments", 0)
            labels = ", ".join(l.get("name", "") for l in issue.get("labels", []))
            is_pr = "pull_request" in issue
            kind = "PR" if is_pr else "Issue"

            lines.append(f"### #{number}: {title}")
            lines.append(f"- **Type**: {kind} | **State**: {state} | **Comments**: {comments_count}")
            if labels:
                lines.append(f"- **Labels**: {labels}")

            body = (issue.get("body") or "")[:400]
            if body:
                lines.append(f"- **Description**: {body}")

            # Fetch top comments for high-engagement issues
            if comments_count >= 3:
                print(f"  Fetching comments for #{number}...")
                comments = fetch_issue_comments(owner_repo, number, limit=5)
                if comments:
                    lines.append("\n**Top Comments:**\n")
                    for c in comments:
                        user = c.get("user", {}).get("login", "anon")
                        text = (c.get("body") or "")[:300]
                        lines.append(f"**{user}**: {text}\n")
                time.sleep(0.3)

            lines.append("")
    else:
        lines.append("## Issues\n\n*(No issues found)*\n")

    lines.append("---\n")

    out_path = os.path.join(out_dir, "github.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))

    print(f"\n✅ Research saved to {out_path}")
    print(f"   Releases: {len(releases)} | Issues: {len(issues)}")


if __name__ == "__main__":
    main()
