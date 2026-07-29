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
"""Evaluate pending refund requests against policy rules P1-P6.

Emits structured verdicts (auto_approve / needs_review) to
.agents/workspace/triage_results.json and stdout. The mechanical rules live
here so they are applied identically on every run; the agent layers judgment
on top but can only escalate more, never approve more.
"""

import csv
import json
import sys
from datetime import date
from pathlib import Path

AMOUNT_CAP = 50.00       # P1
WINDOW_DAYS = 30         # P2

WORKSPACE_CANDIDATES = [
    Path(".agents/workspace"),
    Path("/.agents/workspace"),
    Path("workspace"),
]


def find_workspace():
    for candidate in WORKSPACE_CANDIDATES:
        if (candidate / "refund_requests.csv").exists():
            return candidate
    sys.exit("Error: could not locate workspace with refund_requests.csv")


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def parse_date(value):
    return date.fromisoformat(value.strip())


def evaluate(request, order, prior_requests_for_order):
    passed, flags = [], []

    if order is None:
        return [], ["E7: order not found"]

    amount = float(request["amount_requested"])
    order_amount = float(order["amount"])

    if amount <= AMOUNT_CAP:
        passed.append("P1")
    else:
        flags.append(f"E1: amount over ${AMOUNT_CAP:.0f}")

    days = (parse_date(request["request_date"]) - parse_date(order["order_date"])).days
    if 0 <= days <= WINDOW_DAYS:
        passed.append("P2")
    else:
        flags.append(f"E2: outside {WINDOW_DAYS}-day window ({days} days)")

    if order["final_sale"].strip().lower() != "true":
        passed.append("P3")
    else:
        flags.append("E3: final sale item")

    if not prior_requests_for_order:
        passed.append("P4")
    else:
        flags.append(f"E4: duplicate request (see {', '.join(prior_requests_for_order)})")

    if request["customer_email"].strip().lower() == order["customer_email"].strip().lower():
        passed.append("P5")
    else:
        flags.append("E5: email mismatch (fraud signal)")

    if amount <= order_amount:
        passed.append("P6")
    else:
        flags.append(f"E6: requested ${amount:.2f} exceeds order amount ${order_amount:.2f} (fraud signal)")

    return passed, flags


def main():
    workspace = find_workspace()
    orders = {o["order_id"]: o for o in load_csv(workspace / "orders.csv")}
    requests = load_csv(workspace / "refund_requests.csv")

    verdicts = []
    seen_orders = {}
    for req in requests:
        if req.get("status", "pending").strip().lower() != "pending":
            continue
        order = orders.get(req["order_id"])
        prior = seen_orders.get(req["order_id"], [])
        passed, flags = evaluate(req, order, prior)
        seen_orders.setdefault(req["order_id"], []).append(req["request_id"])

        verdicts.append({
            "request_id": req["request_id"],
            "order_id": req["order_id"],
            "verdict": "auto_approve" if not flags else "needs_review",
            "amount": float(req["amount_requested"]),
            "reason": req["reason"],
            "checks_passed": passed,
            "policy_flags": flags,
        })

    result = {"generated_from": "refund_requests.csv", "verdicts": verdicts}
    out_path = workspace / "triage_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    auto = sum(1 for v in verdicts if v["verdict"] == "auto_approve")
    print(
        f"\nTriage complete: {len(verdicts)} pending requests — "
        f"{auto} auto-approve, {len(verdicts) - auto} need human review. "
        f"Verdicts written to {out_path}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
