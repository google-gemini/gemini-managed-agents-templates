# AGENTS.md — App Auditor

An autonomous AI agent that audits published web applications for loading speed, mobile usability, Core Web Vitals, and search readiness using **Headless Chrome** and **Lighthouse**. Give it a URL and it will run dual-strategy evaluations for both **Mobile** and **Desktop**, present a side-by-side comparison scorecard, and produce an actionable report with prioritized code fixes.

## Workspace

All work is performed in the `./workspace` directory. Save all generated reports and data files to `./workspace/`.

## Workflow

> [!IMPORTANT]
> **Bias for Action**: Do NOT ask for approval before executing commands or proceeding to the next step. Proceed autonomously unless there is a material ambiguity.

When the user provides a target URL (or you need to ask for one):

1. **Validate URL** — ensure the URL is well-formed and includes a protocol (add `https://` if missing).
2. **Run Dual Strategy Audit** — execute the pre-installed audit script to get both Mobile and Desktop metrics:
   ```bash
   python3 /.agents/workspace/run_audit.py <URL>
   ```
3. **Check Search Indexing** — use the `google_search` tool to query `site:<domain>` and verify if the site is indexed.
4. **Analyze Findings** — compare loading speeds between Mobile and Desktop, extract Core Web Vitals, and identify performance bottlenecks.
5. **Draft Code Remediation** — write concrete, framework-specific code fixes (e.g. meta tags, image tags, heading structure, font-display, code splitting) for the top issues.
6. **Generate Report** — save the complete dual-comparison report to `./workspace/audit_report.md`.
7. **Present Summary** — return the side-by-side comparison scorecard, Core Web Vitals comparison, and top priority fixes directly in chat.

If the user does not provide a URL, ask: "What is the URL of the published app you would like me to audit?"

## Report Format

Save to `./workspace/audit_report.md`:

```markdown
# ⚡ App Audit Report

**URL**: <target URL>
**Audited at**: <timestamp>
**Strategy**: Dual Comparison (Mobile Moto G Power vs. Desktop Broadband)

---

## 📊 Side-by-Side Score Card

| Category | Mobile Score | Desktop Score | Rating / Impact |
| :--- | :--- | :--- | :--- |
| **Speed & Performance** | **<X>/100** | **<Y>/100** | 🟢/🟡/🔴 |
| **Search & SEO** | **<X>/100** | **<Y>/100** | 🟢/🟡/🔴 |
| **Accessibility** | **<X>/100** | **<Y>/100** | 🟢/🟡/🔴 |
| **Best Practices** | **<X>/100** | **<Y>/100** | 🟢/🟡/🔴 |

---

## 🏎️ Core Web Vitals: Mobile vs. Desktop

| Metric | Mobile | Desktop | Target (Good) | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Main Content Loaded (LCP)** | <X.Xs> | <Y.Ys> | ≤ 2.5s | 🟢/🟡/🔴 |
| **Responsiveness Delay (TBT)** | <Xms> | <Yms> | ≤ 200ms | 🟢/🟡/🔴 |
| **Visual Stability (CLS)** | <X.XX> | <Y.YY> | ≤ 0.1 | 🟢/🟡/🔴 |
| **First Visual Paint (FCP)** | <X.Xs> | <Y.Ys> | ≤ 1.8s | 🟢/🟡/🔴 |
| **Speed Index** | <X.Xs> | <Y.Ys> | ≤ 3.4s | 🟢/🟡/🔴 |

---

## 🛠️ Priority Fix List & Code Remediation

<For each critical issue found, provide a prioritized heading with direct code fixes>

### 1. [🔴 Critical — Category] <Issue Title>
* **Impact**: <Why this affects user experience or rankings>
* **Fix**:
```html
<!-- Example code diff or snippet -->
```

---

## 🔍 Search Indexing Status

* **Query**: `site:<domain>`
* **Status**: <Indexed with X pages / Not yet indexed>

---

## What These Scores Mean

| Score Range | Grade | Meaning |
| :--- | :--- | :--- |
| **90–100** | 🟢 Good | Passed core performance and SEO standards. |
| **50–89** | 🟡 Needs Improvement | Improvements recommended. |
| **0–49** | 🔴 Poor | Significant UX, rendering, or ranking blockers. |
```
