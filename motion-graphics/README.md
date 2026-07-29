# Motion Graphics Template

A template for [Managed Agents using the Gemini API](https://ai.google.dev/gemini-api/managed-agents). This agent turns a simple prompt, website URL, quote, stat, logo, tweet, or news story into a short, high-impact motion graphic (~5–10s) rendered directly to MP4 using **HyperFrames**.

---

## 🚀 Features

*   **Website & UI Motion Graphics**: Pass a URL (e.g. `https://aistudio.google.com/welcome`) to extract brand elements, callouts, and cursor interactions into a webpage showcase graphic.
*   **Kinetic Typography & Stat Count-Ups**: Animate quotes, hero statistics, and data visualization charts with custom timing and smooth easing curves.
*   **Design-First Motion Architecture**: Powered by HyperFrames seeking, GSAP timelines, and registry blocks for deterministic video rendering.
*   **Automated Quality Verification**: Automatically runs linter checks, DOM validation, and proof snapshot captures prior to rendering final high-quality MP4 video.

---

## 🛠️ Usage Example

```bash
cd motion-graphics
gemini-api agents test --prompt "Make a motion graphic based on my website https://aistudio.google.com/welcome"
```

---

## 🧪 Testing the Prober

To test payload generation and execution end-to-end:

```bash
export GEMINI_API_KEY="your_api_key_here"
./probers.sh
```
