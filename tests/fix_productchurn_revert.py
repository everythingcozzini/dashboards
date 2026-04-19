#!/usr/bin/env python3
"""
tests/fix_productchurn_revert.py
--------------------------------
Revert voc/productchurn.html to the canonical Cozzini pastel palette + the
6-reason chart structure that watcher.update_product_churn_html expects.

Why: The prior Plan B applied an off-brand "Warm Corporate" palette to this
file only, forking it from the 4 sibling VOC dashboards. It also added an
"Other (exclusive)" 7th chart entry that breaks the watcher's regex
(watcher.py:1293-1301 writes a 6-slot data array into the reason chart).

This script:
  1. Restores the pre-Plan B CSS variables, auth gate inline styles,
     PALETTE array, and all four chart backgroundColor arrays.
  2. Restores the 6-reason chart labels + data array shape.
  3. Does NOT touch the numeric values — the watcher will populate those
     when run next (see tests/run_watcher_once.sh).

Source of truth for the pastel palette:
  - Screenshots at Dash/layout/*.png (pre-fork state)
  - voc/nps.html, voc/customerchurn.html, voc/ces.html all still use these
    same colors today — diff against any of them confirms the palette

Usage:  python3 tests/fix_productchurn_revert.py [--dry-run]
"""
from pathlib import Path
import sys
import argparse

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "voc" / "productchurn.html"

# ----------------------------------------------------------------------------
# Expected state AFTER revert (sourced from voc/customerchurn.html + screenshot)
# ----------------------------------------------------------------------------
PASTEL_CSS_VARS = """  :root {
    --cozzini-navy: #1a2744;
    --cozzini-blue: #7bafd4;
    --cozzini-red: #d4918b;
    --cozzini-gold: #d4a45e;
    --cozzini-green: #8ebf7b;
    --bg: #ffffff;
    --card-bg: #ffffff;
    --text: #0a0a0a;
    --text-muted: #555555;
    --border: #e5e5e5;
  }"""

WARM_CSS_VARS = """  :root {
    /* Warm Corporate palette */
    --cozzini-navy: #1b3a4b;
    --cozzini-blue: #3d7c98;
    --cozzini-red: #b44d2d;
    --cozzini-gold: #c78c3a;
    --cozzini-green: #4a7c59;
    --bg: #ffffff;
    --card-bg: #ffffff;
    --text: #0a0a0a;
    --text-muted: #555555;
    --border: #e5e5e5;
  }"""

# Each entry: (warm hex, pastel hex, description)
SWAPS = [
    # Auth gate inline styles
    ("background:#1b3a4b;font-family",      "background:#1a2744;font-family",       "gate bg"),
    ('color:#1b3a4b;margin-bottom:4px',     'color:#1a2744;margin-bottom:4px',      "gate h2 color"),
    ("onfocus=\"this.style.borderColor='#3d7c98'\"", "onfocus=\"this.style.borderColor='#7bafd4'\"", "input focus"),
    ("background:#1b3a4b;color:white",      "background:#1a2744;color:white",       "button bg"),
    ("onmouseover=\"this.style.background='#3d7c98'\"", "onmouseover=\"this.style.background='#7bafd4'\"", "button hover"),
    ("onmouseout=\"this.style.background='#1b3a4b'\"",  "onmouseout=\"this.style.background='#1a2744'\"",  "button restore"),
    ("color:#b44d2d;font-size:13px;margin-top:12px", "color:#d4918b;font-size:13px;margin-top:12px", "gate error text"),
    # JS error border
    ("borderColor='#b44d2d'", "borderColor='#d4918b'", "input error border"),
    # PALETTE array
    ("['#3d7c98','#b44d2d','#c78c3a','#4a7c59','#7b6ba1','#c07840','#2c7a7b','#9b5c7a','#6b8a94']",
     "['#7bafd4','#d4918b','#d4a45e','#8ebf7b','#a99bc4','#d4cb7b','#5a90b5','#b87872','#6da362']",
     "PALETTE"),
    # Product doughnut colors (6 entries — was 6 pastel originally)
    ("backgroundColor: ['#3d7c98','#c78c3a','#4a7c59','#9b5c7a','#6b8a94','#c07840'], borderWidth: 2",
     "backgroundColor: ['#7bafd4','#d4a45e','#8ebf7b','#b87872','#6da362'], borderWidth: 2",
     "productChart colors"),
    # Tenure chart colors
    ("backgroundColor: ['#b44d2d','#c07840','#c78c3a','#4a7c59','#3d7c98','#1b3a4b'], borderRadius: 6, barPercentage: 0.7 }]\n  },\n  options: { responsive: true, maintainAspectRatio: false, animation: { duration: 600 }, interaction: { mode: 'index', intersect: false }, scales: { y: { grid: { color: '#f5f5f5' }, ticks: { stepSize: 1 }, beginAtZero: true }, x: { grid: { display: false } } }, plugins: { tooltip: { callbacks: { label: ctx => `${ctx.raw} product cancellations` } } } }\n});",
     "backgroundColor: ['#d4918b','#d4cb7b','#d4a45e','#8ebf7b','#7bafd4','#1a2744'], borderRadius: 6, barPercentage: 0.7 }]\n  },\n  options: { responsive: true, maintainAspectRatio: false, animation: { duration: 600 }, interaction: { mode: 'index', intersect: false }, scales: { y: { grid: { color: '#f5f5f5' }, ticks: { stepSize: 1 }, beginAtZero: true }, x: { grid: { display: false } } }, plugins: { tooltip: { callbacks: { label: ctx => `${ctx.raw} product cancellations` } } } }\n});",
     "tenureChart colors"),
    # Sentiment-actionable (was hardcoded pastel yellow)
    (".sentiment-actionable { color: var(--cozzini-gold); font-weight: 600; }",
     ".sentiment-actionable { color: #d4cb7b; font-weight: 600; }",
     "sentiment-actionable color"),
]

# Reason chart revert (7-entry with Other → 6-entry matching watcher.reason_order)
REASON_CHART_WARM = (
    "labels: ['No longer\\nneeded','Other\\n(exclusive)','Never agreed\\nto start',"
    "'Price /\\nbudget','Menu /\\nequip. changes','Switched\\nvendor','Product\\nperformance'],\n"
    "    datasets: [{ data: [12, 10, 5, 4, 1, 0, 0], "
    "backgroundColor: ['#3d7c98','#b44d2d','#c78c3a','#4a7c59','#7b6ba1','#c07840','#2c7a7b'], "
    "borderRadius: 6, barPercentage: 0.7 }]"
)
# Match watcher.reason_order at watcher.py:1293-1295 (6 standard reasons, no "Other")
REASON_CHART_PASTEL = (
    "labels: ['No longer\\nneeded','Never agreed\\nto start','Price /\\nbudget',"
    "'Product\\nperformance','Menu /\\nequip. changes','Switched\\nvendor'],\n"
    "    datasets: [{ data: [13, 6, 7, 3, 2, 0], "
    "backgroundColor: ['#7bafd4','#d4918b','#d4a45e','#8ebf7b','#a99bc4','#d4cb7b'], "
    "borderRadius: 6, barPercentage: 0.7 }]"
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Show what would change, don't write")
    args = ap.parse_args()

    text = TARGET.read_text()
    orig = text
    log = []

    # 1. CSS vars
    if WARM_CSS_VARS in text:
        text = text.replace(WARM_CSS_VARS, PASTEL_CSS_VARS)
        log.append("✓ CSS vars reverted to Cozzini pastel")
    elif PASTEL_CSS_VARS in text:
        log.append("· CSS vars already pastel (skip)")
    else:
        log.append("✗ CSS vars block not matched — manual inspection needed")

    # 2. Inline swaps
    for warm, pastel, label in SWAPS:
        if warm in text:
            text = text.replace(warm, pastel)
            log.append(f"✓ {label} reverted")
        elif pastel in text:
            log.append(f"· {label} already pastel (skip)")
        else:
            log.append(f"✗ {label} not matched")

    # 3. Reason chart — 7→6 entries
    if REASON_CHART_WARM in text:
        text = text.replace(REASON_CHART_WARM, REASON_CHART_PASTEL)
        log.append("✓ reasonChart reverted to 6-entry structure")
    elif REASON_CHART_PASTEL in text:
        log.append("· reasonChart already 6-entry (skip)")
    else:
        log.append("✗ reasonChart shape not matched — manual inspection needed")

    print(f"Target: {TARGET.relative_to(ROOT)}")
    print(f"Mode:   {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()
    for line in log:
        print(line)
    print()
    ok = all(not line.startswith("✗") for line in log)
    changed = text != orig

    if not args.dry_run and changed:
        TARGET.write_text(text)
        print(f"→ wrote {len(text)} bytes back to {TARGET.name}")
    elif args.dry_run and changed:
        print(f"→ would write {len(text)} bytes (dry run — no change)")
    else:
        print("→ no changes needed")

    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
