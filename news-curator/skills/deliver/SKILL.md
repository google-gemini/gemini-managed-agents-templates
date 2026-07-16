---
name: deliver
description: Posts a condensed version of the briefing to a Google Chat or Slack incoming webhook, so the daily run delivers itself — skips silently when no webhook is configured.
---

# Deliver Skill

Use this skill as the final step of a sweep, after the briefing file is
written. It closes the last mile: instead of the briefing waiting in the
workspace until someone polls for it, the run pushes a condensed version to
a chat space.

## Usage

```bash
python3 skills/deliver/scripts/deliver.py .agents/workspace/briefings/<file>.md
```

The script:
1. Looks for a webhook URL in `/credentials/webhook.env` (written into the
   environment by `client/triggers.py create` when `CHAT_WEBHOOK_URL` or
   `SLACK_WEBHOOK_URL` is set at creation time).
2. **If none is configured, prints a skip notice and exits 0** — delivery is
   optional and its absence is never an error.
3. Condenses the briefing markdown for chat (headings bolded, links kept,
   capped below the ~4,096-character Chat message limit, with a note that the
   full briefing lives in the workspace).
4. POSTs `{"text": ...}` to the webhook — the same wire format works for both
   Google Chat and Slack incoming webhooks.

## Instructions for the Agent

- Run this exactly once per sweep, after the briefing file exists, passing the
  briefing's path.
- A "skipping delivery" message is normal operation — do not mention it as a
  problem in your output.
- If the POST fails (non-2xx), report the status and response body verbatim in
  your final output — the briefing itself is already safely written, so a
  delivery failure never warrants rewriting it or retrying more than once.
