# News Curator Template

A template for building [Managed Agents using the Gemini API](https://ai.google.dev/gemini-api/docs/custom-agents) that run **on a schedule with the Triggers API**. This agent sweeps Google News, Hacker News, and Medium for the topics and genres you care about, curates a daily briefing — and learns your taste from feedback, so tomorrow's briefing is sharper than today's.

The core idea: **the Trigger's persistent environment is both the memory and the personalization.** Every scheduled execution reuses the same sandbox: the dedupe state means you never see an article twice, the history CSV powers "this topic is heating up" trend analysis, and the taste profile you tune in conversation is read by the next scheduled run. Zero external storage, zero credentials, nothing deployed on your side.

---

## 🚀 Features

*   **Scheduled with Triggers**: One `triggers.py create` call binds the agent, environment, prompt, and cron schedule into a resource that fires on its own — pause, resume, run-now, and execution history included.
*   **Learns Your Taste Across Runs**: Tell it "less funding news" or "add quantum computing" in chat — it updates `interests.json` in the persistent environment, and the next scheduled briefing curates differently. Every briefing includes a taste note so the learning stays visible and correctable.
*   **Trend Analysis from Run History**: `curation_history.csv` grows sweep over sweep, letting each briefing say "mentions of X rose from 4 to 15 across the last three sweeps" — with real numbers.
*   **Three Zero-Credential Sources**: Google News RSS (any search topic, plus genre feeds like TECHNOLOGY or SCIENCE), Hacker News (community buzz), and Medium tag feeds (longform practitioner writing) — no account, token, or paid tier for any of them; the network allowlist is exactly three domains.
*   **Curation, Not Firehose**: Hard cap of 10 news picks + 4 community items per briefing, each with a why-it-matters line and its source link. Selection quality is the product.
*   **Delivers Itself (optional)**: Configure a Slack, Discord, or Google Chat incoming webhook and each scheduled run pushes a condensed briefing straight into your chat — no poller, no cron on your side. Without a webhook, briefings simply accumulate in the workspace.

---

## ✅ Prerequisites

- **Python 3.10+** with the [google-genai SDK](https://pypi.org/project/google-genai/): `pip install -r requirements.txt`.
- A **Gemini API key** exported as `GEMINI_API_KEY` ([get one](https://aistudio.google.com/app/api-keys)).
- No accounts, tokens, or paid tiers for the news sources; delivery to a chat webhook is optional (see below).

---

## ⏰ Schedule It

```bash
export GEMINI_API_KEY="your_api_key_here"
cd news-curator

# Create the daily briefing (09:00 UTC by default). Prints the trigger id — copy it.
python3 client/triggers.py create

# Use that id in the commands below (or run `list` any time to see all triggers).
python3 client/triggers.py run <TRIGGER_ID>          # fire now, don't wait for 09:00
python3 client/triggers.py executions <TRIGGER_ID>   # run history
python3 client/triggers.py digest <TRIGGER_ID>       # print the latest briefing
python3 client/triggers.py usage <TRIGGER_ID>        # token usage per execution
python3 client/triggers.py list                      # all triggers + their ids
```

Other schedules: `--schedule "0 7 * * *" --tz "America/New_York"` (7am Eastern daily), `--schedule "0 8 * * 1-5"` (weekday mornings). Manage with `pause`, `resume`, `list`, and `delete <TRIGGER_ID>`.

Run it two days in a row and compare briefings: day two contains only articles that appeared *since day one*, and its Trends section cites the history day one wrote — that's the persistent environment doing the work.

---

## 💬 Tune Its Taste From Your Terminal

The taste profile lives in the trigger's persistent environment, so you tune it by talking to the agent *in that environment*:

```bash
python3 client/triggers.py feedback TRIGGER_ID "less funding-round news, and add Formula 1 to my topics"
```

The agent updates `interests.json`, confirms what it recorded, and the **next scheduled run curates against the updated profile**. Every briefing's Taste Note tells you which preferences shaped that day's picks, so the learning stays visible and correctable.

---

## 📬 Get It Delivered (optional)

Give the trigger a webhook at creation time and the briefing arrives in your chat every morning by itself. Pick whichever platform you use — each is a 30-second, one-time setup.

**Step 1 — create an incoming webhook and copy its URL:**

| Platform | How to get a webhook URL | Notes |
| --- | --- | --- |
| **Discord** | Channel → *Edit Channel* → *Integrations* → *Webhooks* → *New Webhook* → *Copy Webhook URL* | Works on free personal accounts. Easiest option. |
| **Slack** | Create an app at [api.slack.com/apps](https://api.slack.com/apps) → *Incoming Webhooks* → *Activate* → *Add New Webhook to Workspace* → pick a channel → copy the URL | Free plan works. |
| **Google Chat** | Space → space name → *Apps & integrations* → *Webhooks* → *Add* → copy the URL | **Requires Google Workspace** — not available on personal Gmail, and some org admins disable it. If the option is missing, use Slack or Discord. |

**Step 2 — export it and create the trigger** (never hardcode the URL):

```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."   # or SLACK_WEBHOOK_URL / CHAT_WEBHOOK_URL
python3 client/triggers.py create
```

You'll see `Delivery enabled: … will be available to the deliver skill` confirming it was picked up. The URL is baked into the trigger's environment as a credentials file (not committed anywhere); the deliver skill formats the briefing for the target platform — clickable headlines, emoji section anchors — and splits it across multiple messages if it exceeds the platform's per-message limit (Discord 2k, Slack/Chat ~4k chars), so nothing is truncated. The full briefing is always saved in the workspace too. No webhook exported? Delivery is skipped silently and everything else works.

> **Webhook vs. Chat app**: incoming webhooks are the right tool for one-way notifications like this. If you want two-way interaction — replying to the briefing in Chat to tune your taste profile — that's a [Google Chat app](https://developers.google.com/workspace/chat), which needs a hosted backend. The `feedback` command above gives you the same loop from the terminal without any of that infrastructure.

---

## 🎯 Make It Yours

The reader profile ships as **`interests.default.json`** (the tracked, pristine default). On the first `./probers.sh` or `triggers.py create`, it's copied to `workspace/interests.json` — your working copy, which the agent then owns and edits as it learns your taste. To start from your own interests, either edit `interests.default.json` before the first run, or edit `workspace/interests.json` after it's created:

```json
{
  "topics": ["your product", "rust programming", "Formula 1"],
  "genres": ["TECHNOLOGY", "SCIENCE"],
  "medium_tags": ["rust", "machine-learning"],
  "preferences": {
    "more": ["primary sources"],
    "less": ["rumor pieces"],
    "notes": []
  },
  "max_items_per_topic": 15
}
```

Valid genres: `WORLD`, `NATION`, `BUSINESS`, `TECHNOLOGY`, `ENTERTAINMENT`, `SCIENCE`, `SPORTS`, `HEALTH`. Or just tell the agent in chat — "add quantum computing to my topics" — and it maintains the working copy itself.

> `workspace/interests.json` is git-ignored runtime state the agent mutates; `interests.default.json` is the version-controlled default. Editing the working copy never shows up as a repo change.

---

## 🧪 Testing the Prober

To test a single sweep end-to-end without creating a trigger:

```bash
export GEMINI_API_KEY="your_api_key_here"
./probers.sh
```

Note the prober provisions a fresh environment each time, so it always behaves like a "first run" — the never-repeat-an-article and taste-learning stories only show up under a Trigger, where executions share one environment.

---

## 🛟 Troubleshooting

- **Google Chat: no *Webhooks* option, or delivery returns HTTP 403** — incoming webhooks require Google Workspace and may be disabled by your org admin; they don't work on personal Gmail. Use Slack or Discord instead.
- **The briefing wrote to the workspace but wasn't delivered** — check the run output (`digest <TRIGGER_ID>`); a delivery failure is reported verbatim there and never blocks the briefing itself. Confirm the webhook URL was exported *before* `create` (look for the `Delivery enabled: …` line at creation).
- **Nothing new in a later briefing** — that's the dedupe working: only articles unseen in previous runs are surfaced. A quiet interval still produces a briefing noting "0 new items" plus the trend read.
