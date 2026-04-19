#!/usr/bin/env python3
"""
tests/verify_data.py
--------------------
Compares numeric values displayed in voc/productchurn.html against the
ground-truth JSON produced by tests/recompute_productchurn.py
(which uses the watcher parser as source of truth).

Only validates product churn in this pass; the same pattern can extend
to NPS / CES / customer churn if desired.

Exit 0 on pass, 1 on fail.
"""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "voc" / "productchurn.html"
TRUTH = ROOT / "tests" / "_productchurn_truth.json"

fails = []
warns = []


def check(cond, msg, warn_only=False):
    status = "PASS" if cond else ("WARN" if warn_only else "FAIL")
    print(f"  [{status}] {msg}")
    if not cond:
        (warns if warn_only else fails).append(msg)


if not TRUTH.exists():
    print("truth JSON missing — run tests/recompute_productchurn.py first")
    sys.exit(2)

truth = json.loads(TRUTH.read_text())
html = HTML.read_text()


def find_kpi_value(label_fragment, value_regex=r'\d+'):
    """Find the KPI card value given a fragment of its label text.

    NB: uses non-greedy .*? to survive labels that contain <br> or
    &lt;90 days&gt; inside the label div (e.g. 'Early Product Cancellations').
    """
    pattern = (
        rf'<div class="label">{re.escape(label_fragment)}.*?</div>'
        rf'\s*<div class="value">({value_regex})'
    )
    m = re.search(pattern, html, re.DOTALL)
    return m.group(1) if m else None


print("── KPI 1: Total Cancellations ──")
v = find_kpi_value("Total Cancellations")
check(v is not None, "Total Cancellations KPI found")
if v:
    check(int(v) == truth["total"], f"Total = {v}  (truth {truth['total']})")

print()
print("── KPI 2: Avg Product Subscription Duration ──")
v = find_kpi_value("Avg. Product Subscription Duration")
check(v is not None, "Avg Duration KPI found")
if v:
    check(int(v) == truth["avg_days"], f"Avg = {v}  (truth {truth['avg_days']})")

m = re.search(r"Median: (\d+)", html)
if m:
    check(int(m.group(1)) == truth["median_days"],
          f"Median = {m.group(1)}  (truth {truth['median_days']})")

print()
print("── KPI 3: Early Product Cancellations ──")
v = find_kpi_value("Early Product Cancellations")
check(v is not None, "Early Cancellations KPI found")
if v:
    check(int(v) == truth["early_cancel"],
          f"Early = {v}  (truth {truth['early_cancel']})")

m = re.search(r">(\d+)% of all product cancellations<", html)
if m:
    check(int(m.group(1)) == truth["early_pct"],
          f"Early % = {m.group(1)}%  (truth {truth['early_pct']}%)")

print()
print("── Chart: Reasons (6-entry, matches watcher.reason_order) ──")
m = re.search(r"getElementById\('reasonChart'\).*?data:\s*(\[[\d,\s]+\])",
              html, re.DOTALL)
if m:
    chart = eval(m.group(1))
    watcher_order = ["No longer needed", "Never agreed to start the service",
                     "Price / budget", "Product performance",
                     "Menu or equipment changes", "Switched to another vendor"]
    expected = [truth["reason_counts"].get(r, 0) for r in watcher_order]
    check(len(chart) == 6, f"reasonChart has 6 entries (got {len(chart)})")
    check(chart == expected,
          f"reasonChart data = {chart}  (truth {expected})",
          warn_only=True)
else:
    check(False, "reasonChart data array not found")

print()
print("── Chart: Centers ──")
m = re.search(r"getElementById\('centerChart'\).*?data:\s*(\[[\d,\s]+\])",
              html, re.DOTALL)
if m:
    chart = eval(m.group(1))
    check(chart == truth["center_counts"],
          f"centerChart data = {chart}  (truth {truth['center_counts']})",
          warn_only=True)

print()
print("── Chart: Tenure ──")
m = re.search(r"getElementById\('tenureChart'\).*?data:\s*(\[[\d,\s]+\])",
              html, re.DOTALL)
if m:
    chart = eval(m.group(1))
    check(chart == truth["tenure_buckets"],
          f"tenureChart data = {chart}  (truth {truth['tenure_buckets']})",
          warn_only=True)

print()
print("=" * 60)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print(f"  - {f}")
if warns:
    print(f"WARNINGS: {len(warns)}  — dashboard values drifted from source")
    for w in warns:
        print(f"  - {w}")
    print("(run tests/run_parsers_local.py to sync values)")
sys.exit(1 if fails else 0)
