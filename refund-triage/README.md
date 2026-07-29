# Refund Triage Template

A template for building [Managed Agents using the Gemini API](https://ai.google.dev/gemini-api/managed-agents). This agent triages customer refund requests against a written policy: it auto-approves the clear cases through a custom `issue_refund` function, and escalates ambiguous or high-value cases to a human through an `escalate_to_human` function — demonstrating **function calling** and a **human-in-the-loop approval gate**.

The core idea: the agent is autonomous about *analysis* but can only *act* through functions your application controls. Money never moves inside the sandbox — the environment has an empty network allowlist, so every real-world side effect flows through your code.

---

## 🚀 Features

*   **Custom Function Calling**: Declares `issue_refund` and `escalate_to_human` functions the host application executes, using the `previous_interaction_id` round-trip.
*   **Calibrated Human-in-the-Loop**: Clear cases (≤$50, in-window, no fraud signals) are actioned automatically; everything else is escalated with a recommendation for a human to approve, deny, or investigate.
*   **Deterministic Policy Engine**: Mechanical rules (amount cap, return window, duplicates, identity match) live in a triage script so they apply identically every run — the agent can escalate more, never approve more.
*   **Compliance Audit Trail**: Every refund, escalation, and human decision is appended to a workspace audit log with its policy basis.
*   **Fully Offline Sandbox**: Empty network allowlist — the agent's only channels to the outside world are the declared functions.

---

## ✨ Try the Approvals Dashboard (web)

The `client-web/` app is a browser-based approvals dashboard — the shape this pattern takes in production. A small TypeScript server runs the function-calling loop and streams agent activity to a single-page UI; escalations appear as review cards where **you** click Approve, Deny, or Investigate, and your decision flows back into the running interaction.

```bash
export GEMINI_API_KEY="your_api_key_here"
cd refund-triage/client-web
npm install
npm start          # open http://localhost:8787
```

Click **Process refund queue** and watch: refunds the policy allows are issued against the simulated payment system in the activity feed, while everything else lands in your review queue. The API key never reaches the browser — the UI only talks to the local server, the same isolation you'd want in a real deployment. Zero build step: the frontend is one static HTML file.

---

## 🛠️ Try the Human-in-the-Loop Console (zero-dependency)

The `client/refund_console.py` script is the application side of the template. It executes the agent's function calls: refunds are "issued" against a simulated payment system, and escalations prompt **you** at the terminal to approve or deny.

```bash
export GEMINI_API_KEY="your_api_key_here"
cd refund-triage
python3 client/refund_console.py
```

The sample queue in `workspace/refund_requests.csv` is engineered to exercise every path: two automatic approvals and six escalations covering high value (E1), expired window (E2), final sale (E3), duplicate request (E4), email mismatch (E5), and over-order-amount (E6).

Analysis-only prompts never trigger function calls:

```bash
python3 client/refund_console.py "Which pending requests qualify for automatic approval, and why?"
```

---

## 🧪 Testing the Prober

To quickly test the template end-to-end, run:

```bash
export GEMINI_API_KEY="your_api_key_here"
./probers.sh
```

The prober uses the analysis-only example prompt, so it completes without the function-calling round-trip (which requires the interactive client above).
