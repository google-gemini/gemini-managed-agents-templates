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
"""Application-side console for the refund-triage agent.

This is the half of the template that runs OUTSIDE the sandbox. The agent
analyzes the refund queue in its environment, but money only moves through
the custom functions declared in agent.yaml — and those execute *here*:

  issue_refund       -> simulated payment-system call (prints + confirms)
  escalate_to_human  -> prompts YOU at this terminal to approve or deny

The loop is the standard Interactions API function-calling round-trip:
create an interaction, and whenever the agent requests a function call,
execute it locally and continue the interaction with the result via
previous_interaction_id, until the agent finishes with plain text.

Usage:
    export GEMINI_API_KEY="your_api_key_here"
    cd refund-triage
    python3 client/refund_console.py            # process the whole queue
    python3 client/refund_console.py "PROMPT"   # custom prompt

Requires: Python 3.10+ (stdlib only), run from the refund-triage/ directory.
"""

import json
import os
import ssl
import subprocess
import sys
import urllib.request

# macOS python.org builds ship without linked root certificates; fall back to
# certifi's bundle when available so HTTPS works out of the box.
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
API_REVISION = "2026-05-20"

DEFAULT_PROMPT = (
    "Process all pending refund requests: issue refunds for the ones policy "
    "allows, and escalate the rest to me with your recommendation."
)


def build_initial_payload(prompt):
    """Reuse the repo's generate_payload.py so the client environment exactly
    matches what the prober and the template ship (AGENTS.md, skills,
    workspace data, tools including the function declarations)."""
    raw = subprocess.check_output(
        [sys.executable, "../generate_payload.py", prompt], text=True
    )
    payload = json.loads(raw)
    payload["stream"] = False  # simple request/response loop for this console
    return payload


def post(payload, api_key):
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
            "Api-Revision": API_REVISION,
            "x-server-timeout": "600",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=620, context=SSL_CONTEXT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"Interactions API {error.code}: {body[:2000]}"
        ) from error


def extract_function_calls(interaction):
    """Collect pending custom function calls awaiting a result from us.

    The interaction's steps also contain the agent's built-in tool activity
    (read_file, code execution, ...) as function_call/function_result PAIRS.
    Only unpaired function_call steps are ours to answer, and only when the
    interaction is paused with status "requires_action"."""
    if interaction.get("status") != "requires_action":
        return []
    steps = interaction.get("steps", [])
    answered = {s.get("call_id") for s in steps if s.get("type") == "function_result"}
    return [
        s for s in steps
        if s.get("type") == "function_call" and s.get("id") not in answered
    ]


def extract_text(interaction):
    parts = []
    for step in interaction.get("steps", []):
        if step.get("type") == "model_output":
            for item in step.get("content", []):
                if item.get("type") == "text" and item.get("text"):
                    parts.append(item["text"])
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# The application-controlled functions. In a real deployment, issue_refund
# would hit your payment provider and escalate_to_human would post to a review
# queue (chat channel, ticketing system, approvals dashboard). Here the
# "payment system" is a print statement and the "review queue" is your keyboard.
# ---------------------------------------------------------------------------

def issue_refund(arguments):
    print("\n  [payment system] Issuing refund:")
    print(f"    request={arguments['request_id']} order={arguments['order_id']} "
          f"amount=${float(arguments['amount']):.2f}")
    print(f"    reason: {arguments['reason']}")
    confirmation = f"PAY-{arguments['request_id']}-OK"
    return {"status": "success", "confirmation_id": confirmation}


def escalate_to_human(arguments):
    print("\n  ══════════════ HUMAN REVIEW REQUIRED ══════════════")
    print(f"  Request:        {arguments['request_id']}")
    print(f"  Summary:        {arguments['summary']}")
    print(f"  Agent suggests: {arguments['recommendation'].upper()}")
    print(f"  Policy flags:   {', '.join(arguments.get('policy_flags', []))}")
    while True:
        decision = input("  Your decision [approve/deny/investigate]: ").strip().lower()
        if decision in ("approve", "deny", "investigate"):
            break
        print("  Please type approve, deny, or investigate.")
    note = input("  Optional note for the audit log: ").strip()
    return {"decision": decision, "approver": "console-reviewer", "note": note}


HANDLERS = {"issue_refund": issue_refund, "escalate_to_human": escalate_to_human}


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Error: GEMINI_API_KEY is not set.")
    if not os.path.exists("agent.yaml"):
        sys.exit("Error: run this from the refund-triage/ template directory.")

    prompt = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT
    print(f"Prompt: {prompt}\nStarting interaction (the agent will triage the queue)...")

    initial_payload = build_initial_payload(prompt)
    # Continuation requests must repeat the agent/model parameter.
    agent_param = {
        key: initial_payload[key] for key in ("agent", "model") if key in initial_payload
    }
    interaction = post(initial_payload, api_key)

    # Function-calling loop: keep continuing the interaction until the agent
    # has no more pending function calls and returns plain text.
    while True:
        calls = extract_function_calls(interaction)
        if not calls:
            break

        results = []
        for call in calls:
            name = call.get("name")
            arguments = call.get("arguments", {})
            if isinstance(arguments, str):
                arguments = json.loads(arguments)
            handler = HANDLERS.get(name)
            if handler is None:
                result = {"status": "error", "message": f"Unknown function: {name}"}
            else:
                result = handler(arguments)
            results.append({
                "type": "function_result",
                "call_id": call.get("id"),
                "name": name,
                "is_error": isinstance(result, dict) and result.get("status") == "error",
                "result": [{"type": "text", "text": json.dumps(result)}],
            })

        interaction = post(
            {
                **agent_param,
                "previous_interaction_id": interaction["id"],
                # Reuse the same sandbox so workspace state (audit log, triage
                # results) persists across the function-calling round-trips.
                "environment": interaction["environment_id"],
                "input": results,
            },
            api_key,
        )

    print("\n════════════════ AGENT SUMMARY ════════════════")
    print(extract_text(interaction))


if __name__ == "__main__":
    main()
