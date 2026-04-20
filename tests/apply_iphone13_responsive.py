#!/usr/bin/env python3
"""
tests/apply_iphone13_responsive.py
-----------------------------------
Applies file-specific @media (max-width: 480px) blocks to the 12
dashboard HTML files so they render cleanly on iPhone 13 (390×844).

Patches come from tests/_iphone13_audit.md (produced by the responsive
audit agent) — this runner encodes those patches as data and injects
them immediately before `</style>` in each file.

All patches are wrapped with sentinel comments so this runner is idempotent:
  /* === iphone13-patch:start === */
  @media (max-width: 480px) { ... }
  /* === iphone13-patch:end === */

Running it twice just replaces the block; it never stacks.

Usage: python3 tests/apply_iphone13_responsive.py [--dry-run]
"""
from pathlib import Path
import argparse
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

PATCH_START = "/* === iphone13-patch:start === */"
PATCH_END = "/* === iphone13-patch:end === */"

# ============================================================================
# File-specific patches (sourced from tests/_iphone13_audit.md)
# ============================================================================
PATCHES = {
    "index.html": """@media (max-width: 480px) {
  .hero { padding: 24px 16px 20px; }
  .hero h1 { font-size: 24px; }
  .tile { padding: 24px 18px; min-height: 200px; }
  .tile h2 { font-size: 22px; }
  .tile .cta { padding: 12px 22px; }
  .topbar { padding: 12px 16px; }
  .footer { padding: 16px; }
}""",

    "voc/index.html": """@media (max-width: 480px) {
  .page-title { padding: 24px 16px 8px; }
  .page-title h1 { font-size: 22px; }
  .container { padding: 12px 16px 32px; }
  .dash-item { padding: 16px 14px; gap: 12px; }
  .dash-item h3 { font-size: 14px; }
  .dash-item p { font-size: 12px; }
  .topbar { padding: 12px 16px; }
  .topbar img { height: 22px; }
  .footer { padding: 16px; }
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
}""",

    "voc/nps.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; }
  .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; }
  .kpi-card .value { font-size: 28px; }
  .nps-gauge-section { padding: 20px 14px; }
  .nps-gauge-bar { height: 28px; }
  .nps-score-big { font-size: 44px; }
  .chart-wrap { height: 260px; }
  .chart-wrap.tall { height: 340px; }
  .tab-btn { padding: 10px 14px; font-size: 12px; min-height: 40px; }
  .new-cust-row { grid-template-columns: repeat(2, 1fr) !important; }
  .new-chart-pair { grid-template-columns: 1fr !important; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}""",

    "voc/customerchurn.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .chart-wrap { height: 260px; } .chart-wrap.tall { height: 320px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .feedback-section { padding: 14px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}""",

    "voc/productchurn.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .chart-wrap { height: 260px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  .feedback-section { padding: 14px; }
  .feedback-filters-dropdowns { gap: 8px; }
  .feedback-filters-dropdowns label { font-size: 11px; }
  .feedback-filters-dropdowns select { font-size: 11px; padding: 8px 8px; max-width: 140px; min-height: 38px; }
  table.feedback-table { min-width: 900px; font-size: 11px; }
  table.feedback-table td { padding: 8px 6px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}""",

    "voc/ces.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .overview-chart .chart-wrap { height: 260px; }
  .chart-card .chart-wrap { height: 220px; }
  .center-chart .chart-wrap { height: 280px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}""",

    "voc/sdorg.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
}""",

    "mkt/index.html": """@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .page-title { padding: 24px 16px 8px; } .page-title h1 { font-size: 22px; }
  .container { padding: 12px 16px 32px; }
  .quarter-grid { grid-template-columns: 1fr !important; gap: 12px; }
  .quarter-tile { min-height: 120px; padding: 20px 18px; }
  .quarter-label { font-size: 24px; }
  .topbar { padding: 12px 16px; } .footer { padding: 16px; }
}""",

    "mkt/q1.html": """@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 26px; }
  .chart-card .chart-wrap { height: 240px; }
  .full-chart .chart-wrap { height: 280px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}""",

    "mkt/q2.html": """@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .empty-state { padding: 40px 20px; }
  .empty-state h2 { font-size: 20px; }
  .empty-icon { width: 60px; height: 60px; font-size: 26px; }
}""",

    "mkt/q3.html": """@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .empty-state { padding: 40px 20px; }
  .empty-state h2 { font-size: 20px; }
  .empty-icon { width: 60px; height: 60px; font-size: 26px; }
}""",

    "mkt/q4.html": """@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .empty-state { padding: 40px 20px; }
  .empty-state h2 { font-size: 20px; }
  .empty-icon { width: 60px; height: 60px; font-size: 26px; }
}""",
}


def patch_file(relpath, css_block, dry_run):
    path = ROOT / relpath
    if not path.exists():
        return f"✗ {relpath}: file not found"

    text = path.read_text()
    block = f"\n  {PATCH_START}\n  {css_block}\n  {PATCH_END}\n"

    # 1. If sentinel already present, replace between them (idempotent)
    sentinel_pat = re.compile(
        re.escape(PATCH_START) + r".*?" + re.escape(PATCH_END),
        re.DOTALL,
    )
    if sentinel_pat.search(text):
        new_text = sentinel_pat.sub(f"{PATCH_START}\n  {css_block}\n  {PATCH_END}", text)
        status = "replaced"
    else:
        # 2. Otherwise insert just before the FIRST </style>
        if "</style>" not in text:
            return f"✗ {relpath}: no </style> found"
        new_text = text.replace("</style>", f"{block}</style>", 1)
        status = "inserted"

    if new_text == text:
        return f"· {relpath}: unchanged"
    if not dry_run:
        path.write_text(new_text)
    return f"✓ {relpath}: {status} ({len(new_text) - len(text):+d} bytes)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print(f"Files: {len(PATCHES)}")
    print()
    fails = 0
    for relpath, css in PATCHES.items():
        result = patch_file(relpath, css, args.dry_run)
        print(result)
        if result.startswith("✗"):
            fails += 1
    print()
    print(f"Done. {fails} failure(s).")
    sys.exit(0 if fails == 0 else 2)


if __name__ == "__main__":
    main()
