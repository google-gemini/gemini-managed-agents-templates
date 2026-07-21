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
"""Deliver a condensed briefing to a Google Chat or Slack incoming webhook.

Delivery is optional: when no webhook is configured this script prints a
skip notice and exits 0, so the same template works with or without it.
Both Chat and Slack accept the same `{"text": ...}` payload.
"""

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

MAX_CHARS = 3800  # stay under Google Chat's ~4096-char text message limit

# Emoji anchors give the eye a scanning target at each section boundary.
SECTION_EMOJI = {
    "daily briefing": "🗞️", "top stories": "📰", "discoveries": "🔭",
    "community buzz": "💬", "worth a longer read": "📖", "trends": "📈",
    "taste note": "🎛️", "data health": "✅",
}
# Matches [text](url) and tolerates [text](<url>) — the agent may or may not
# wrap the URL in angle brackets.
LINK_RE = re.compile(r"\[([^\]]+)\]\(<?(https?://[^)\s>]+)>?\)")

CREDENTIAL_CANDIDATES = [
    Path("/credentials/webhook.env"),
    Path("credentials/webhook.env"),
]
WEBHOOK_KEYS = ("CHAT_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "DISCORD_WEBHOOK_URL")


def load_webhook_url():
    for path in CREDENTIAL_CANDIDATES:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            key, _, value = line.partition("=")
            if key.strip() in WEBHOOK_KEYS and value.strip():
                return value.strip()
    return None


def condense(markdown, platform):
    """Flatten briefing markdown into chat-friendly text under the size cap.

    Markup dialects differ: Chat/Slack bold is *text*, Discord bold is
    **text** (single asterisks are italic there). On Discord, bare URLs also
    auto-expand into preview embeds — wrapping them in <...> suppresses that
    and keeps the message compact."""
    discord = platform == "discord"
    bold = (lambda s: f"**{s}**") if discord else (lambda s: f"*{s}*")
    # Slack/Google Chat share <url|text>; Discord uses [text](<url>) (the
    # <...> suppresses its link-preview embed). Both hide giant redirect URLs.
    masked = (lambda text, url: f"[{text}](<{url}>)") if discord \
        else (lambda text, url: f"<{url}|{text}>")

    # Parse into blocks of [heading level, heading text, body lines]. A block
    # (a heading plus everything under it) is never split across messages, so
    # a story is never shown without its link.
    parsed, cur = [], None
    for raw in markdown.splitlines():
        line = raw.rstrip()
        heading = re.match(r"^(#{1,6})\s+(.*)", line)
        if heading:
            if cur is not None:
                parsed.append(cur)
            cur = [len(heading.group(1)), heading.group(2).strip(), []]
        elif cur is not None:
            cur[2].append(line)
        elif line.strip():
            cur = [0, None, [line]]
    if cur is not None:
        parsed.append(cur)

    blocks = []
    for level, title, body in parsed:
        # Pull the story's source URL out of the body and drop the standalone
        # "Source Link" line — the headline itself becomes the clickable link.
        url, kept = None, []
        for bl in body:
            stripped = bl.strip().lstrip(">").strip()
            match = LINK_RE.search(stripped)
            if match and url is None:
                url = match.group(2)
            if match and LINK_RE.sub("", stripped).strip(" —-·|") == "":
                continue  # line was only a source-link label
            converted = LINK_RE.sub(
                lambda m: masked(m.group(1), m.group(2)), bl.lstrip("> "))
            if not discord:
                converted = converted.replace("**", "*")
            kept.append(converted)

        rendered = []
        if title and level >= 3:            # story headline → clickable + bold
            rendered.append(bold(masked(title, url) if url else title))
        elif title:                         # section header / title → emoji anchor
            emoji = SECTION_EMOJI.get(title.lower().split(" — ")[0].strip())
            rendered.append(bold(f"{emoji} {title}" if emoji else title))
        rendered.extend(kept)
        block = re.sub(r"\n{3,}", "\n\n", "\n".join(rendered).strip())
        if block:
            blocks.append(block)

    # Pack whole blocks into messages. Discord caps content at 2000 chars,
    # so overflow continues into follow-up messages (at most MAX_MESSAGES);
    # Chat/Slack get one larger message. Anything that still does not fit is
    # dropped at a block boundary with a truncation notice.
    max_chars = 1900 if discord else MAX_CHARS
    max_messages = 3  # both platforms split long briefings rather than truncate
    messages, buffer = [], ""
    truncated = False
    for block in blocks:
        candidate = f"{buffer}\n\n{block}".strip() if buffer else block
        if len(candidate) <= max_chars:
            buffer = candidate
        elif len(messages) + 1 < max_messages:
            messages.append(buffer)
            buffer = block[:max_chars]
        else:
            truncated = True
            break
    if truncated:
        notice = "\n\n_(continued in the full briefing in the workspace)_"
        buffer = buffer[: max_chars - len(notice)] + notice
    if buffer:
        messages.append(buffer)
    return messages


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: deliver.py <path-to-briefing.md>")
    briefing_path = Path(sys.argv[1])
    if not briefing_path.exists():
        sys.exit(f"Error: briefing not found: {briefing_path}")

    url = load_webhook_url()
    if not url:
        print("No webhook configured — skipping delivery (this is normal).")
        return

    # Google Chat and Slack take {"text": ...}; Discord takes {"content": ...}
    # with a 2000-char cap, so long briefings go out as consecutive messages.
    platform = "discord" if ("discord.com" in url or "discordapp.com" in url) else "chat"
    messages = condense(briefing_path.read_text(encoding="utf-8"), platform)
    payload_key = "content" if platform == "discord" else "text"

    for index, message in enumerate(messages, start=1):
        request = urllib.request.Request(
            url,
            data=json.dumps({payload_key: message}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                # Identify ourselves properly: Discord/Cloudflare reject the
                # default Python-urllib user agent (HTTP 403, error code 1010).
                "User-Agent": "news-curator-deliver/1.0 (Gemini Managed Agents template)",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                print(f"Delivered part {index}/{len(messages)} (HTTP {response.status}).")
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            sys.exit(f"Delivery failed on part {index}/{len(messages)}: "
                     f"HTTP {error.code}: {body[:500]}")
        if index < len(messages):
            time.sleep(1)  # keep ordering and stay far from rate limits


if __name__ == "__main__":
    main()
