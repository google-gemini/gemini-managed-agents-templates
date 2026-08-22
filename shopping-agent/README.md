# Shopping Research Agent Template

A template for [Managed Agents using the Gemini API](https://ai.google.dev/gemini-api/managed-agents). This agent assists users with end-to-end shopping research: finding products that match user constraints, comparing alternatives side-by-side, analyzing pricing and discounts, and providing tailored recommendations with clear rationale.

---

## 🚀 Features

*   **Product Research**: Searches for current products across manufacturers, retailers, and trusted review sources based on category, budget, and required features.
*   **Product Comparison**: Normalizes specifications and provides structured comparisons highlighting trade-offs, strengths, and weaknesses.
*   **Price Analysis**: Evaluates pricing relative to budget constraints, calculates price differences, and identifies value-for-money propositions.
*   **Product Recommendation**: Ranks options and delivers well-reasoned recommendations tailored to user priorities (Best Overall, Best Budget, Best Value).

---

## 🛠️ Usage

```bash
cd shopping-agent
gemini-api agents test --prompt "I need wireless noise-cancelling headphones under $200 with long battery life. Research and recommend the best options."
```

---

## 🧪 Testing the Prober

To quickly test the template end-to-end, run:

```bash
export GEMINI_API_KEY="your_api_key_here"
./probers.sh
```
