#!/usr/bin/env python3
"""
tests/run_parsers_local.py
--------------------------
Run every watcher parser + HTML updater against the local xlsx files,
but SKIP the git push step. Populates voc/*.html with current Excel data
without touching the remote.

Matches watcher.process_file logic at watcher.py:1449-1532 except:
  * No git add / commit / push
  * No processed-files bookkeeping
  * Prints a summary table instead of logging

Usage:  python3 tests/run_parsers_local.py
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from watcher import (  # noqa: E402
    parse_nps, update_nps_html,
    parse_nps_new_customers, update_nps_new_customers_section,
    parse_customer_churn, update_customer_churn_html,
    parse_product_churn, update_product_churn_html,
    parse_ces_file, update_ces_html, load_all_ces_data, classify_file,
)

TASKS = [
    ("nps_existing_customers.xlsx", "nps"),
    ("nps_new_customers.xlsx",       "nps_new"),
    ("customer_churn.xlsx",          "customer_churn"),
    ("product_churn.xlsx",           "product_churn"),
]


def run_one(filename, dash_type):
    src = ROOT / filename
    if not src.exists():
        return f"✗ {filename} not found"
    try:
        if dash_type == "nps":
            d = parse_nps(str(src))
            update_nps_html(d)
            return f"✓ {filename:36s} → voc/nps.html (existing section) | n={d['total']}, NPS {d['nps']}"
        if dash_type == "nps_new":
            d = parse_nps_new_customers(str(src))
            update_nps_new_customers_section(d)
            return f"✓ {filename:36s} → voc/nps.html (new-customer section) | n={d['total']}"
        if dash_type == "customer_churn":
            d = parse_customer_churn(str(src))
            update_customer_churn_html(d)
            return f"✓ {filename:36s} → voc/customerchurn.html | n={d['total']}"
        if dash_type == "product_churn":
            d = parse_product_churn(str(src))
            update_product_churn_html(d)
            return (f"✓ {filename:36s} → voc/productchurn.html | "
                    f"n={d['total']}, top={d['top_reason']} ({d['top_reason_count']})")
    except Exception as exc:
        return f"✗ {filename} ERROR: {exc}"
    return f"? {filename} unhandled"


def run_ces():
    # Aggregate all ces_*.xlsx → single update
    ces_data = load_all_ces_data()
    if not ces_data:
        return "✗ no CES xlsx files found"
    update_ces_html(ces_data)
    parts = [f"{k}:{v['mean']:.2f}" for k, v in ces_data.items()]
    # CES parser returns 'n' (count) per survey, not 'total'
    total = sum(v["n"] for v in ces_data.values())
    return f"✓ {len(ces_data):2d} CES files                 → voc/ces.html | total={total}, {' '.join(parts)}"


def main():
    print(f"ROOT: {ROOT}")
    print()
    print("Running parsers (NO git push) …")
    print("-" * 78)
    for filename, dash_type in TASKS:
        print(run_one(filename, dash_type))
    print(run_ces())
    print("-" * 78)
    print("Done. voc/*.html updated in-place. Check `git diff voc/` for changes.")


if __name__ == "__main__":
    main()
