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
"""Manage the news-curator agent's schedule with the google-genai SDK.

A Trigger binds this template's agent, environment, prompt, and cron schedule
into a persistent resource that fires without manual intervention. Every
execution reuses the SAME environment, which is what makes this template work:
seen_items.json, interests.json, and curation_history.csv written by one run
are read by the next, so the agent accumulates a longitudinal view with zero
external storage.

The interaction config (agent, AGENTS.md, skills, workspace files, network
allowlist) is assembled inline below, so scheduled runs carry exactly the
same environment sources as the template checkout they were created from.

Usage (from the news-curator/ template directory):
    export GEMINI_API_KEY="your_api_key_here"

    python3 client/triggers.py create                      # daily at 09:00 UTC
    python3 client/triggers.py create --schedule "0 */6 * * *" --tz "America/New_York"
    python3 client/triggers.py list
    python3 client/triggers.py run TRIGGER_ID              # fire now (works while paused)
    python3 client/triggers.py executions TRIGGER_ID       # history + interaction ids
    python3 client/triggers.py digest TRIGGER_ID           # print latest run's output
    python3 client/triggers.py usage TRIGGER_ID            # token usage per execution
    python3 client/triggers.py pause TRIGGER_ID
    python3 client/triggers.py resume TRIGGER_ID
    python3 client/triggers.py delete TRIGGER_ID

Requires: Python 3.10+ and the google-genai SDK (`pip install google-genai`).
"""

import argparse
import base64
import os
import shutil
import sys
import warnings
from pathlib import Path

# Keep command output clean: the SDK warns that the Triggers API (in
# preview) may change. Drop this filter once the API is GA.
warnings.filterwarnings("ignore", message="Triggers usage is experimental")

from google import genai

AGENT_ID = "antigravity-preview-05-2026"

# The agent only ever needs the three news sources and the chat platforms it
# may deliver to — everything else stays unreachable from the sandbox.
NETWORK_ALLOWLIST = [
    {"domain": "news.google.com"},
    {"domain": "hn.algolia.com"},
    {"domain": "medium.com"},
    {"domain": "chat.googleapis.com"},
    {"domain": "hooks.slack.com"},
    {"domain": "discord.com"},
]

TEXT_EXTENSIONS = (".py", ".md", ".txt", ".sh", ".csv", ".env", ".json", ".yaml")

DEFAULT_SCHEDULE = "0 9 * * *"  # daily at 09:00
DEFAULT_TZ = "UTC"
DEFAULT_PROMPT = (
    "Run the daily curation sweep: fetch the latest news and community "
    "discussion for my interests, curate the briefing, and update the "
    "trend history."
)


def make_client():
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("Error: GEMINI_API_KEY is not set.")
    return genai.Client()


def field(obj, name, default=None):
    """Read a field from an SDK model or a plain dict interchangeably."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def environment_sources():
    """Collect AGENTS.md, skills/, and workspace/ into environment sources —
    the same layout the sandbox expects (/.agents/...)."""
    sources = []

    api_key = os.environ["GEMINI_API_KEY"]
    sources.append({
        "type": "inline",
        "target": "/credentials/.env",
        "content": f"GEMINI_API_KEY={api_key}\n",
    })

    if os.path.exists("AGENTS.md"):
        sources.append({
            "type": "inline",
            "target": "/.agents/AGENTS.md",
            "content": Path("AGENTS.md").read_text(encoding="utf-8"),
        })

    for directory in ("skills", "workspace"):
        for path in sorted(Path(directory).rglob("*")):
            if not path.is_file():
                continue
            source = {"type": "inline", "target": f"/.agents/{path.as_posix()}"}
            if path.suffix in TEXT_EXTENSIONS:
                try:
                    source["content"] = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    source["content"] = base64.b64encode(path.read_bytes()).decode()
                    source["encoding"] = "base64"
            else:
                source["content"] = base64.b64encode(path.read_bytes()).decode()
                source["encoding"] = "base64"
            sources.append(source)

    # Optional delivery: if a webhook URL is exported when the trigger is
    # created, bake it into the environment as a credentials file the deliver
    # skill reads. Never hardcode webhook URLs here or in the repo.
    for key in ("CHAT_WEBHOOK_URL", "SLACK_WEBHOOK_URL", "DISCORD_WEBHOOK_URL"):
        url = os.environ.get(key)
        if url:
            sources.append({
                "type": "inline",
                "target": "/credentials/webhook.env",
                "content": f"{key}={url}\n",
            })
            print(f"Delivery enabled: {key} will be available to the deliver skill.")
            break
    else:
        print("No CHAT_WEBHOOK_URL / SLACK_WEBHOOK_URL / DISCORD_WEBHOOK_URL "
              "exported — briefings will be written to the workspace only.")
    return sources


def build_interaction(prompt):
    if not os.path.exists("AGENTS.md"):
        sys.exit("Error: run this from the news-curator/ template directory.")

    # Seed the reader profile from the shipped default if absent, so a fresh
    # clone gets a working profile the first time a trigger is created.
    # workspace/interests.json is git-ignored runtime state the agent edits;
    # interests.default.json is the tracked, pristine starting point.
    os.makedirs("workspace", exist_ok=True)
    if not os.path.exists("workspace/interests.json") and os.path.exists("interests.default.json"):
        shutil.copy("interests.default.json", "workspace/interests.json")

    return {
        "agent": AGENT_ID,
        "input": prompt,
        "tools": [{"type": "code_execution"}],
        "environment": {
            "type": "remote",
            "sources": environment_sources(),
            "network": {"allowlist": NETWORK_ALLOWLIST},
        },
    }


def interaction_text(interaction):
    parts = []
    for step in field(interaction, "steps") or []:
        if field(step, "type") == "model_output":
            for item in field(step, "content") or []:
                if field(item, "type") == "text" and field(item, "text"):
                    parts.append(field(item, "text"))
    return "\n".join(parts)


def cmd_create(args):
    client = make_client()
    trigger = client.triggers.create(
        schedule=args.schedule,
        time_zone=args.tz,
        display_name=args.name,
        execution_timeout_seconds=600,
        interaction=build_interaction(args.prompt),
    )
    print(f"Trigger created: {field(trigger, 'id')}")
    print(f"  Status:   {field(trigger, 'status')}")
    print(f"  Schedule: {args.schedule} ({args.tz})")
    print(f"  Next run: {field(trigger, 'next_run_time')}")


def cmd_list(_args):
    client = make_client()  # hold the client: a temporary gets GC'd mid-call
    triggers = field(client.triggers.list(), "triggers") or []
    if not triggers:
        print("No triggers.")
    for t in triggers:
        print(f"{field(t, 'id')}  {field(t, 'display_name')}  [{field(t, 'status')}]  "
              f"next: {field(t, 'next_run_time')}")


def cmd_run(args):
    # The run-now call may hold the connection while the execution runs; the
    # execution starts regardless, so a timeout here is not a failure.
    client = make_client()
    try:
        client.triggers.run(args.trigger_id, timeout=15)
    except Exception as error:  # noqa: BLE001 — only swallow timeouts
        if "timed out" not in str(error).lower() and "timeout" not in str(error).lower():
            raise
    print(f"Execution requested for {args.trigger_id}. "
          f"Watch it with: python3 client/triggers.py executions {args.trigger_id}")


def cmd_status(args, status):
    client = make_client()
    client.triggers.update(args.trigger_id, status=status)
    print(f"Trigger {args.trigger_id} -> {status}")


def list_executions(client, trigger_id):
    result = client.triggers.list_executions(trigger_id)
    return field(result, "trigger_executions") or []


def cmd_executions(args):
    client = make_client()
    executions = list_executions(client, args.trigger_id)
    if not executions:
        print("No executions yet.")
    for ex in executions:
        print(f"{field(ex, 'id')}  [{field(ex, 'status')}]  {field(ex, 'start_time')} -> "
              f"{field(ex, 'end_time')}  interaction: {field(ex, 'interaction_id')}")


def latest_interaction(client, trigger_id):
    done = [ex for ex in list_executions(client, trigger_id) if field(ex, "interaction_id")]
    if not done:
        sys.exit("No executions with an interaction yet — run the trigger once first "
                 f"(python3 client/triggers.py run {trigger_id}).")
    latest = max(done, key=lambda ex: str(field(ex, "start_time") or ""))
    return client.interactions.get(field(latest, "interaction_id"))


def cmd_digest(args):
    """Fetch the most recent execution's interaction and print its output —
    the quickest way to read the latest briefing without opening the sandbox."""
    client = make_client()
    interaction = latest_interaction(client, args.trigger_id)
    print(interaction_text(interaction) or "(no text output on the latest execution)")


def cmd_usage(args):
    """Print token usage per execution."""
    client = make_client()
    executions = [ex for ex in list_executions(client, args.trigger_id)
                  if field(ex, "interaction_id")]
    if not executions:
        print("No executions with an interaction yet.")
        return
    executions.sort(key=lambda ex: str(field(ex, "start_time") or ""), reverse=True)
    print(f"{'started (UTC)':<17} {'input':>9} {'cached':>9} {'output':>8} "
          f"{'thought':>8} {'total':>9}")
    for ex in executions:
        usage = field(client.interactions.get(field(ex, "interaction_id")), "usage")
        if usage is None:
            continue
        print(f"{str(field(ex, 'start_time'))[:16]:<17} "
              f"{field(usage, 'total_input_tokens') or 0:>9,} "
              f"{field(usage, 'total_cached_tokens') or 0:>9,} "
              f"{field(usage, 'total_output_tokens') or 0:>8,} "
              f"{field(usage, 'total_thought_tokens') or 0:>8,} "
              f"{field(usage, 'total_tokens') or 0:>9,}")


def cmd_delete(args):
    client = make_client()
    client.triggers.delete(args.trigger_id)
    print(f"Trigger {args.trigger_id} deleted (execution history is retained).")


def cmd_feedback(args):
    """Send taste feedback into the trigger's PERSISTENT environment.

    The agent applies its taste-learning protocol (updates interests.json)
    and the next scheduled run curates against the updated profile — this is
    the same environment every execution reuses."""
    client = make_client()
    env_id = field(latest_interaction(client, args.trigger_id), "environment_id")
    if not env_id:
        sys.exit("Could not resolve the trigger's environment id.")
    print(f"Sending feedback into environment {env_id} (may take a minute)...")
    # Interactions that reuse an environment by id do NOT auto-load the
    # environment's AGENTS.md into context (verified empirically — trigger
    # executions get it, bare reuse does not). So point the agent at the
    # environment's own copy rather than duplicating the protocol here:
    # AGENTS.md stays the single source of truth.
    interaction = client.interactions.create(
        agent=AGENT_ID,
        environment=env_id,
        input=(
            "First read /.agents/AGENTS.md and adopt its persona and rules "
            "for this conversation. Then handle this reader taste feedback "
            f"per its protocol: {args.message}"
        ),
        timeout=620,
    )
    print(interaction_text(interaction) or "(no text reply)")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create the scheduled sweep")
    create.add_argument("--schedule", default=DEFAULT_SCHEDULE, help="cron expression")
    create.add_argument("--tz", default=DEFAULT_TZ, help="IANA time zone")
    create.add_argument("--name", default="news-curator-sweep", help="display name")
    create.add_argument("--prompt", default=DEFAULT_PROMPT, help="sweep prompt")
    create.set_defaults(func=cmd_create)

    sub.add_parser("list", help="list triggers").set_defaults(func=cmd_list)

    feedback = sub.add_parser(
        "feedback",
        help="send taste feedback into the trigger's environment "
             '(e.g. feedback TRIGGER_ID "less funding news")',
    )
    feedback.add_argument("trigger_id")
    feedback.add_argument("message")
    feedback.set_defaults(func=cmd_feedback)

    for name, help_text in [("run", "fire immediately"), ("executions", "show run history"),
                            ("digest", "print the latest run's briefing output"),
                            ("usage", "show token usage per execution"),
                            ("pause", "pause the schedule"), ("resume", "resume the schedule"),
                            ("delete", "delete the trigger")]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("trigger_id")
        if name == "pause":
            p.set_defaults(func=lambda a: cmd_status(a, "paused"))
        elif name == "resume":
            p.set_defaults(func=lambda a: cmd_status(a, "active"))
        elif name == "run":
            p.set_defaults(func=cmd_run)
        elif name == "executions":
            p.set_defaults(func=cmd_executions)
        elif name == "digest":
            p.set_defaults(func=cmd_digest)
        elif name == "usage":
            p.set_defaults(func=cmd_usage)
        else:
            p.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as error:
        # Surface SDK/API failures as a one-line message, not a traceback.
        if type(error).__module__.startswith("google.genai"):
            sys.exit(f"API error: {error}")
        raise


if __name__ == "__main__":
    main()
