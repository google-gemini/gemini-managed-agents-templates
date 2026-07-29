---
name: audit
description: Appends a compliance-grade decision record to the audit log for every refund issued, escalation raised, and human decision received.
---

# Audit Skill

Use this skill to keep `.agents/workspace/audit_log.md` complete enough that a
compliance reviewer could reconstruct every decision without reading the
conversation. Every `issue_refund` result, every `escalate_to_human` call, and
every human decision gets an entry — no exceptions.

## Instructions for the Agent

Append entries directly to `.agents/workspace/audit_log.md` using your file
writing capabilities. Create the file if it does not exist. Use this layout:

```markdown
## [Request ID] — [Outcome]
- **When**: [request processing date from the data, e.g. 2026-07-12]
- **Order**: [order ID] — [item] — $[amount]
- **Decision path**: [automatic under policy | escalated to human]
- **Policy basis**: [rule IDs, e.g. P1-P6 all passed | E1, E5]
- **Human involvement**: [none | approved by reviewer | denied by reviewer — note]
- **Function result**: [confirmation ID or failure message from issue_refund, if any]

---
```

Rules:
1. Write the entry immediately after the outcome is known — not batched at the end.
2. Record failures too: a failed `issue_refund` call gets an entry with the error verbatim.
3. Never edit or delete existing entries; the log is append-only.
