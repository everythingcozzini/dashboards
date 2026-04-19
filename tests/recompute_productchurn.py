#!/usr/bin/env python3
"""
tests/recompute_productchurn.py
-------------------------------
Ground-truth dump for product churn data.
Imports the EXISTING parser from watcher.py (which already implements the
priority-counting logic at watcher.py:768-778) and prints every value the
dashboard should display. No memory, no assumptions — this is the source of
truth the dashboard HTML must match.

Usage:  python3 tests/recompute_productchurn.py
"""
from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from watcher import parse_product_churn  # noqa: E402

XLSX = ROOT / "product_churn.xlsx"


def main():
    print(f"Reading: {XLSX}")
    if not XLSX.exists():
        print("ERROR: xlsx not found")
        sys.exit(1)

    data = parse_product_churn(XLSX)
    if data is None:
        print("ERROR: parser returned None")
        sys.exit(1)

    # Headline KPIs
    print()
    print("=" * 60)
    print("PRODUCT CHURN — GROUND TRUTH (from product_churn.xlsx)")
    print("=" * 60)
    print(f"Total Cancellations ............. {data['total']}")
    print(f"N Sharpening Centers ............ {data['n_centers']}")
    print(f"Avg Days Active ................. {data['avg_days']}")
    print(f"Median Days Active .............. {data['median_days']}")
    print(f"Early Cancellations (<90 days) .. {data['early_cancel']}")
    print(f"Early Cancel % .................. {data['early_pct']}%")
    print(f"Top Reason ...................... {data['top_reason']!r} ({data['top_reason_count']})")
    print(f"Date Range ...................... {data['date_min']} – {data['date_max']}")

    # Reason counts
    print()
    print("-- Reason Counts (priority logic applied) --")
    for reason, count in sorted(data["reason_counts"].items(), key=lambda x: -x[1]):
        print(f"  {count:>3}  {reason}")

    # Centers
    print()
    print("-- By Sharpening Center --")
    for label, count in zip(data["center_labels"], data["center_counts"]):
        print(f"  {count:>3}  {label}")

    # Products
    print()
    print("-- By Product Type --")
    for label, count in zip(data["product_labels"], data["product_counts"]):
        print(f"  {count:>3}  {label}")

    # Tenure buckets
    print()
    print("-- Tenure Distribution --")
    tenure_labels = ["0-30 days", "31-90 days", "91-180 days",
                     "181-365 days", "1-2 years", "2+ years"]
    for label, count in zip(tenure_labels, data["tenure_buckets"]):
        print(f"  {count:>3}  {label}")

    print()
    print("-- Verbatim Feedback Count --")
    print(f"  Total verbatims ....... {len(data['feedback'])}")
    for sentiment in ("positive", "negative", "neutral", "actionable"):
        n = sum(1 for f in data["feedback"] if f["sentiment"] == sentiment)
        print(f"  {sentiment:>12s} ....... {n}")

    # JSON dump for downstream fix script
    out = ROOT / "tests" / "_productchurn_truth.json"
    out.write_text(json.dumps({
        "total": data["total"],
        "n_centers": data["n_centers"],
        "avg_days": data["avg_days"],
        "median_days": data["median_days"],
        "early_cancel": data["early_cancel"],
        "early_pct": data["early_pct"],
        "top_reason": data["top_reason"],
        "top_reason_count": data["top_reason_count"],
        "reason_counts": data["reason_counts"],
        "center_labels": data["center_labels"],
        "center_counts": data["center_counts"],
        "product_labels": data["product_labels"],
        "product_counts": data["product_counts"],
        "tenure_buckets": data["tenure_buckets"],
        "feedback_count": len(data["feedback"]),
        "date_min": data["date_min"],
        "date_max": data["date_max"],
    }, indent=2, default=str))
    print(f"\nWrote ground-truth JSON → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
