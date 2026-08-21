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
"""App Auditor — Lighthouse & Web Vitals Evaluation Engine.

Queries Google Lighthouse (via the PageSpeed Insights API) for BOTH
Mobile and Desktop strategies to provide authentic, side-by-side performance comparisons.
Uses strictly Python standard library modules with zero external dependencies.
"""
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request


def run_single_audit(url: str, strategy: str = "mobile") -> dict:
  """Runs a Lighthouse audit for a single strategy (mobile or desktop)."""
  if not url.startswith("http"):
    url = "https://" + url

  params = {
      "url": url,
      "strategy": strategy,
      "category": [
          "PERFORMANCE",
          "SEO",
          "ACCESSIBILITY",
          "BEST_PRACTICES",
      ],
  }
  # Accept dedicated PAGESPEED_API_KEY or general GOOGLE_API_KEY with PageSpeed enabled
  api_key = os.getenv("PAGESPEED_API_KEY") or os.getenv("GOOGLE_API_KEY")
  if api_key:
    params["key"] = api_key

  api_url = (
      "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?"
      + urllib.parse.urlencode(params, doseq=True)
  )
  ctx = ssl.create_default_context()
  req = urllib.request.Request(
      api_url,
      headers={"User-Agent": f"AppAuditor/2.0 ({strategy})"},
  )

  try:
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
      data = json.loads(resp.read().decode("utf-8"))
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8", errors="ignore")
    detail = str(e)
    try:
      err_json = json.loads(err_body)
      detail = err_json.get("error", {}).get("message", str(e))
    except Exception:
      pass
    if e.code == 429:
      raise RuntimeError(
          f"PageSpeed Insights API rate limit reached ({strategy}). "
          "Set a PAGESPEED_API_KEY environment variable to enable higher quota."
      ) from e
    raise RuntimeError(f"PageSpeed audit failed ({strategy}): {detail}") from e
  except Exception as e:
    raise RuntimeError(f"Network error auditing {url} ({strategy}): {e}") from e

  lighthouse = data.get("lighthouseResult", {})
  categories = lighthouse.get("categories", {})
  audits = lighthouse.get("audits", {})

  def get_score(cid):
    cat = categories.get(cid)
    if cat and cat.get("score") is not None:
      return round(float(cat.get("score", 0)) * 100)
    return 0

  def get_vital(audit_key, target):
    audit = audits.get(audit_key, {})
    s = audit.get("score")
    return {
        "title": audit.get("title", audit_key),
        "display": audit.get("displayValue", "N/A"),
        "score": float(s) if s is not None else 0.0,
        "target": target,
    }

  failures = []
  for k, a in audits.items():
    s = a.get("score")
    if s is not None and float(s) < 0.9 and a.get("details"):
      failures.append({
          "id": k,
          "title": a.get("title"),
          "description": a.get("description"),
          "displayValue": a.get("displayValue", ""),
          "score": float(s),
      })

  return {
      "strategy": strategy,
      "scores": {
          "performance": get_score("performance"),
          "seo": get_score("seo"),
          "accessibility": get_score("accessibility"),
          "best_practices": get_score("best-practices"),
      },
      "vitals": {
          "fcp": get_vital("first-contentful-paint", "≤ 1.8s"),
          "lcp": get_vital("largest-contentful-paint", "≤ 2.5s"),
          "tbt": get_vital("total-blocking-time", "≤ 200ms"),
          "cls": get_vital("cumulative-layout-shift", "≤ 0.1"),
          "speed_index": get_vital("speed-index", "≤ 3.4s"),
      },
      "failures": failures[:15],
  }


def run_audit(url: str, strategy: str = "both") -> dict:
  """Runs audits for both Mobile and Desktop strategies by default."""
  if not url.startswith("http"):
    url = "https://" + url

  timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

  if strategy in ("mobile", "desktop"):
    single = run_single_audit(url, strategy)
    single["url"] = url
    single["timestamp"] = timestamp
    return single

  mobile_res = run_single_audit(url, "mobile")
  desktop_res = run_single_audit(url, "desktop")

  return {
      "url": url,
      "timestamp": timestamp,
      "strategy": "dual_comparison",
      "mobile": mobile_res,
      "desktop": desktop_res,
      "failures": mobile_res.get("failures", []),
  }


if __name__ == "__main__":
  if len(sys.argv) < 2:
    print(json.dumps({"error": "Usage: run_audit.py <URL> [mobile|desktop|both]"}))
    sys.exit(1)

  target = sys.argv[1]
  strat = sys.argv[2] if len(sys.argv) > 2 else "both"

  try:
    results = run_audit(target, strat)
    print(json.dumps(results, indent=2))
  except Exception as err:
    print(json.dumps({"error": str(err), "url": target}, indent=2))
    sys.exit(1)
