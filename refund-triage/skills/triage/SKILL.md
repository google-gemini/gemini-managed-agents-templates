---
name: triage
description: Deterministically evaluates every pending refund request against the numbered policy rules and emits structured verdicts (auto_approve or needs_review) with the exact rules that passed or failed.
---

# Triage Skill

Use this skill to evaluate the pending refund queue. The mechanical policy rules
(amount cap, return window, final sale, duplicates, identity match, amount sanity)
live in code so they are applied identically every run — your judgment is layered
on top, never substituted for the rules.

## Usage

```bash
python3 skills/triage/scripts/triage.py
```

The script:
1. Loads `.agents/workspace/orders.csv` and `.agents/workspace/refund_requests.csv`.
2. Applies policy rules P1–P6 from `.agents/workspace/policy.md` to every `pending` request.
3. Writes verdicts to `.agents/workspace/triage_results.json` and prints them to stdout.

## Output format

```json
{
  "generated_from": "refund_requests.csv",
  "verdicts": [
    {
      "request_id": "R-1001",
      "order_id": "O-2001",
      "verdict": "auto_approve",
      "amount": 23.50,
      "checks_passed": ["P1", "P2", "P3", "P4", "P5", "P6"],
      "policy_flags": []
    },
    {
      "request_id": "R-1002",
      "order_id": "O-2002",
      "verdict": "needs_review",
      "amount": 189.99,
      "checks_passed": ["P2", "P3", "P4", "P5", "P6"],
      "policy_flags": ["E1: amount over $50"]
    }
  ]
}
```

## Instructions for the Agent

- Treat `auto_approve` verdicts as necessary but not sufficient: skim the request
  `reason` text for anything the mechanical rules cannot see (threats, confusion,
  signs the customer wants an exchange rather than a refund). If something feels
  off, escalate anyway with recommendation `investigate` — the script's verdict
  never forces your hand toward paying out.
- Never "upgrade" a `needs_review` verdict to an automatic refund. The rules only
  work one way: you may escalate more, never approve more.
