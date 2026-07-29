# Gap Report: Gemini Managed Agent Templates vs. Claude Managed Agents Cookbooks

*Analysis date: 2026-07-13. Compared `gemini-managed-agents-templates` (branch `new-templates`, 6 templates) against Anthropic's `claude-cookbooks/managed_agents` (17 examples), grounded in the Gemini Managed Agents docs ([custom-agents](https://ai.google.dev/gemini-api/docs/custom-agents), [antigravity-agent](https://ai.google.dev/gemini-api/docs/antigravity-agent)).*

## TL;DR

The two collections are solving different problems, and that's the core gap. Gemini's 6 templates are **agent definitions** — polished examples of what an agent *is* (persona, skills, allowlists). Claude's 17 examples are **integration recipes** — examples of how an agent *plugs into a real system* (Slack, webhooks, schedulers, human approval queues, cost dashboards, multi-agent fleets). A developer evaluating both walks away from Claude's cookbooks knowing how to ship an agent to production; they walk away from Gemini's templates knowing how to configure one. The biggest missing categories are: **function calling / MCP** (supported by the platform, demonstrated nowhere), **human-in-the-loop**, **platform integrations**, **background/scheduled execution**, **multi-turn session patterns**, and **a learning path** that teaches the API surface progressively.

## Where Gemini is strong (for context)

Credit where due — the Gemini templates beat Claude's cookbooks on a few axes, and these are worth leaning into rather than diluting:

- **Multimodal output**: AI Radio (text → TTS → Lyria music → mixed audio → cover art) has no Claude equivalent; Claude's examples are entirely text/HTML.
- **Declarative, testable agent packaging**: `agent.yaml` + `AGENTS.md` + skills + `probers.sh` is a cleaner reproducible unit than a notebook.
- **Security-by-configuration**: every template ships a network allowlist; Claude's data analyst runs with unrestricted networking.
- **Skill depth**: the document-processor's slide design system is more polished than anything in the Claude set.

## The gaps, with creative alternatives

For each gap, the suggested example ideas demonstrate the same capability through a clearly different scenario, so nothing reads as a port of an Anthropic cookbook.

### 1. Function calling and custom tools — *highest priority*

Claude has three examples of custom tools (SRE responder, HITL gate, production ops). The Gemini docs explicitly support function calling via `previous_interaction_id` round-trips, yet **zero templates demonstrate it**. This is the single most glaring gap because it's the bridge between "agent in a sandbox" and "agent that acts on my systems."

**Alternative examples:**
- **Warehouse/inventory agent**: the agent reasons about stock levels and calls `reserve_stock()`, `create_purchase_order()` functions that your application executes against a mock ERP. Shows the request → app executes → result → agent continues loop.
- **Smart-building facilities agent**: reads sensor CSVs in the sandbox, then calls `adjust_hvac()` / `file_maintenance_ticket()` custom functions — a nice contrast of built-in code execution *plus* app-controlled tools.

### 2. Human-in-the-loop approval gates

Claude has two dedicated examples (calibrated decide/escalate tooling, and an SRE flow where a PR merge is gated on human sign-off). Gemini has none — every template is "bias for action, never seek approval," which is the exact opposite story enterprises ask about.

**Alternative examples (deliberately far from SRE/incident-response):**
- **Release notes & changelog publisher**: agent drafts release notes from git history, then calls a `request_signoff()` function; only after a human approves does it call `publish()`. Same gate pattern, developer-tooling flavor without copying the PagerDuty scenario.
- **Refund-request triage agent**: auto-approves refunds under a threshold via `issue_refund()`, escalates ambiguous or high-value cases to a human queue via `escalate()`. This is the calibrated two-tool pattern (clear cases decided, ambiguous cases escalated) in a commerce setting.

### 3. Platform integrations (the "where does this live" question)

Claude ships full working integrations: Slack (twice — notebook and production TypeScript), Linear with OAuth, an MCP wrapper so any client can drive sessions, and a Next.js chat UI. Gemini has **zero** examples of an agent embedded in a place users actually work.

**Alternative examples (Google-ecosystem-native, which is both differentiated and on-brand):**
- **Google Chat bot** wrapping the existing data-analyst template — @mention with an attached CSV in a space, get the analysis back in-thread. Uses `previous_interaction_id` for thread continuity.
- **GitHub Issues responder**: a GitHub Action that runs the customer-support agent against new issues and posts a grounded, source-linked draft reply. Reuses an existing template in an integration story.
- **Firebase/Next.js chat app** on the Interactions API with streaming — the "build a product on this" reference.

### 4. Background execution and scheduling

The platform supports `background=True` with polling and cancellation, and the new **Triggers API** (launching ~2026-07-15) adds first-class server-side cron scheduling: `client.triggers.create(schedule=..., interaction=...)` with pause/resume, run-now, execution history, auto-pause after consecutive failures, and — importantly — **environment reuse across runs**, so files written by one execution persist to the next. This matches (and in some respects exceeds) Claude's scheduled-deployment story, but only if templates showcase it at launch. No current template shows async execution or a recurring agent.

**Alternative examples (built on Triggers, zero external infra — a cleaner story than Claude's Sentry example, which needs setup scripts):**
- **Nightly dependency & CVE auditor**: a trigger that clones a repo, audits `requirements.txt`/`package.json` against advisories, and writes reports to `/workspace/` — using the persistent environment to track what's already been reported (dedupe across runs). Extends the repo-maintainer story.
- **Competitor pricing watcher**: daily trigger that scrapes allowlisted pages, diffs against the previous run's snapshot sitting in the shared environment, and produces a change digest. Environment persistence *is* the demo here — it doubles as the cross-run memory story.
- The trigger docs' own issue-solver example (review PRs, fix `accepted` issues, track solved ones in `/workspace/solved-issues/`) is effectively an autonomous repo-maintainer — worth shipping as a template variant since it composes an existing template with the new API.

### 5. Multi-turn sessions and state continuity as a *taught* pattern

Claude devotes whole notebooks to multi-turn steering, mid-task recovery (CI fails → agent reads the log → fixes), and resuming sessions. Gemini's templates are conversational in prompt design but every prober is effectively single-shot; `previous_interaction_id` and `environment_id` reuse are never demonstrated.

**Alternative examples:**
- **Interactive data-cleaning session**: turn 1 profiles a messy dataset, the user chooses which issues to fix across turns, and the environment carries the evolving dataframe. Recovery angle: the agent's first cleaning script breaks on an edge case and it must diagnose and retry.
- **Migration copilot**: multi-turn Django/SQL schema migration where a mid-way failure (planted) forces observe-and-recover — teaches the same resilience lesson as Claude's issue-to-PR notebook via a completely different task.

### 6. Multi-agent orchestration and cost economics

Claude has a coordinator-with-specialist-roster example and a "frontier planner + cheap parallel workers" example with real token/cost math. Gemini's platform doesn't support subagent nesting (per the docs), but **client-side orchestration of parallel interactions is fully possible** and undemonstrated. The cost-metering story is entirely absent.

**Alternative examples:**
- **Newsroom pipeline**: an editor process fans out parallel background interactions (fact-checker, style editor, headline writer — each a small managed agent with scoped tools/allowlists), then a final interaction synthesizes. Demonstrates orchestration *and* per-agent tool scoping as policy.
- **Literature-review swarm**: N parallel Flash interactions each read one arXiv paper; one Pro interaction synthesizes. Publish the actual token/cost comparison versus doing it all in one Pro session — Gemini's Flash pricing makes this a *better* economics story than Anthropic can tell.

### 7. MCP integration

The platform supports remote MCP servers with auth headers and `allowed_tools` filtering. No template uses it. Claude demonstrates MCP in two examples plus ships an MCP *server* wrapper.

**Alternative example:** a **travel-logistics or maps-adjacent agent** connecting to a public/remote MCP server, plus an `allowed_tools` filtering demo showing least-privilege tool exposure. Separately, an **"Interactions-as-MCP" bridge** would let any MCP client (including IDEs) drive a managed agent — the mirror image of Claude's cma-mcp, but genuinely useful.

### 8. Quality gates / evaluator loops

Claude's outcome-grader notebook (write → independent grader verifies citations against live URLs → revise) has no Gemini counterpart, and it's a credibility feature for enterprise buyers. Gemini has no platform-level outcome API, but the pattern is reproducible with a second judge interaction.

**Alternative example:** **ad-copy or localization generator with a brand-compliance judge** — a separate fresh interaction grades output against a rubric file (tone, banned claims, terminology) and the loop revises until it passes. Different domain, same grade-and-revise lesson.

### 9. Pedagogy and packaging

Structural gaps rather than feature gaps:

- **No learning path.** Claude names an explicit entry-point notebook and builds the API surface incrementally across 10 tutorials. Gemini's README-per-template approach never teaches `interactions.create()` → environment reuse → function calling → background as a progression. A "getting started" tutorial sequence (even 4–5 short notebooks) would fix this — e.g., starting with a **dependency-upgrade agent** that iterates until tests pass (same do-observe-fix hook as Claude's entry point, different scenario).
- **No application-side code at all.** Every Gemini artifact is agent config; there is not one example of an app *consuming* an agent (streaming events, polling background runs, downloading outputs). Claude has ~10.
- **Python-only.** Claude covers TypeScript heavily; the `@google/genai` SDK exists but has zero representation.
- **Credential injection is documented (network transform rules) but never shown** — one template hitting an authenticated API would cover it.

## Platform-level gaps (not fixable with templates — flag to the API team)

These are places where Claude's cookbooks showcase *platform primitives Gemini doesn't have*; templates can only partially paper over them:

- **Agent versioning/rollback** (Claude has version pinning + A/B rollback)
- **First-class memory stores** (Gemini's customer-support memory.md is a workaround, not cross-session — though Trigger environment persistence now covers the scheduled-agent case)
- ~~Server-side scheduling~~ — **closed by the Triggers API** (cron schedule + time zone, pause/resume, run-now, execution history, failure auto-pause, persistent environment across runs). Gemini's version arguably beats Claude's deployments API on the environment-persistence point; the remaining gap is purely that no template demonstrates it yet.
- **Webhooks for idle/completion events** (Gemini requires polling; trigger executions surface an `interaction_id` to poll, but there's no push notification)
- **Credential vaults** (per-user credential containers injected at tool-invocation time)
- **Self-hosted sandbox execution** (Claude shows 6 compute-provider variants)

Worth noting in any roadmap conversation, because the cookbook gap partly reflects an API-surface gap.

## Prioritized recommendation

1. **Function calling template** (refund triage or inventory agent) — unlocks HITL and integrations stories simultaneously.
2. **One real integration** (Google Chat bot reusing data-analyst) — answers "where does this live."
3. **Triggers example, timed to the Triggers launch** (nightly CVE auditor or the issue-solver pattern) — a day-one template showcasing cron scheduling + persistent environments would land while the feature is news, and it's a story Claude's cookbooks tell with far more setup friction.
4. **Getting-started tutorial path** with app-side consumption code in Python *and* TypeScript.
5. **Client-side multi-agent + cost story** (literature-review swarm) — turns the "no subagents" limitation into a Flash-economics win.
6. **MCP example** with `allowed_tools` scoping.

The through-line for differentiation: lean into **Google-ecosystem integrations, multimodal output, Flash cost economics, and security-by-configuration** — those are stories Anthropic's cookbooks can't tell, and they keep every new example from reading as a clone.

## Appendix: Inventory comparison

### Gemini templates (6)

| Template | Use case | Level |
|----------|----------|-------|
| data-analyst | BI/ML analysis on pre-loaded CSVs | Intermediate-Advanced |
| ai-radio | Multi-modal radio show production (TTS, Lyria, image gen) | Advanced |
| customer-support | Grounded support bot with site crawling + memory.md | Intermediate |
| document-processor | Expense/invoice reconciliation + Wikidata verification + HTML slides | Advanced |
| repo-maintainer | GitHub issue analysis + patch generation | Intermediate-Advanced |
| agy-agent-template | Minimal reference template | Starter |

### Claude cookbooks (17)

| Category | Examples |
|----------|----------|
| Applied notebooks (3) | data analyst → HTML/Plotly reports; Slack data bot; SRE incident responder (skills + custom tools + HITL) |
| Guided tutorials (10) | fix-failing-tests (entry point), issue-to-PR steering/recovery, codebase exploration, HITL gate, memory stores, production ops (MCP/vaults/webhooks), prompt versioning, multi-agent coordinator, plan-big-execute-small cost split, outcome grader |
| Production deployments (4+) | Slack (TS), Linear (OAuth, TS), Sentry (scheduled cron), roadtrip planner (Next.js chat UI), cma-mcp (MCP server wrapper), self-hosted sandboxes (6 compute variants) |
