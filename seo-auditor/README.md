# SEO Auditor Agent Template

An autonomous AI agent template that audits published web applications for loading speed, mobile usability, Core Web Vitals, and search indexability using Lighthouse (via the PageSpeed Insights API) and Google Search.

## Features

- **Core Web Vitals & Performance**: Evaluates LCP, TBT, CLS, FCP, and Speed Index against Google's recommended thresholds.
- **Search Index Readiness**: Checks Google Search indexing status using `site:<domain>` queries.
- **Actionable Code Remediation**: Analyzes failed Lighthouse audits and generates framework-specific code fixes.
- **Zero External Dependencies**: Uses a self-contained Python evaluation script (`run_audit.py`).

## Quick Start

1. Set your `GEMINI_API_KEY`:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

2. Run the prober script:
   ```bash
   ./probers.sh
   ```
