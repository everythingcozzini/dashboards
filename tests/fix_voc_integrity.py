#!/usr/bin/env python3
"""
tests/fix_voc_integrity.py
--------------------------
Fixes two VOC integrity issues the verifiers flagged:

  1. voc/index.html line 22 `.auth-box .kicker` uses #b44d2d (Warm-fork red)
     on a white auth box. This was copy-pasted from the mkt gate where it's
     on-palette. For VOC, use the pastel navy (#1a2744) so the kicker
     matches the page's navy header + link accents.

  2. PASS_HASH in all 6 voc/*.html is declared as '8a9b0c1d' but the actual
     simpleHash of 'Cozzini2026!' is 'b2917ac7' (verified via node). The
     gate still works because checkAuth falls back to literal-string compare,
     but the hash is a decoy. Replace it with the real hash so the primary
     check works without relying on the fallback.

Source of truth for simpleHash:
  * In-page JS at bottom of each voc/*.html (simpleHash function)
  * Verified via:  node -e "... simpleHash('Cozzini2026!')"  → 'b2917ac7'

Usage:  python3 tests/fix_voc_integrity.py [--dry-run]
"""
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parent.parent
VOC_FILES = ["index.html", "nps.html", "customerchurn.html",
             "productchurn.html", "ces.html", "sdorg.html"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    log = []
    changed = 0

    # Fix 1: voc/index.html kicker
    idx_path = ROOT / "voc" / "index.html"
    idx = idx_path.read_text()
    bad_kicker = ".auth-box .kicker { color: #b44d2d;"
    good_kicker = ".auth-box .kicker { color: #1a2744;"
    if bad_kicker in idx:
        idx_new = idx.replace(bad_kicker, good_kicker)
        log.append(f"✓ voc/index.html kicker color #b44d2d → #1a2744")
        if not args.dry_run:
            idx_path.write_text(idx_new)
            changed += 1
    elif good_kicker in idx:
        log.append(f"· voc/index.html kicker already pastel (skip)")
    else:
        log.append(f"✗ voc/index.html kicker pattern not found")

    # Fix 2: PASS_HASH correction across all voc files
    OLD_HASH = "'8a9b0c1d'"
    NEW_HASH = "'b2917ac7'"  # simpleHash('Cozzini2026!') verified via node
    for fname in VOC_FILES:
        p = ROOT / "voc" / fname
        if not p.exists():
            log.append(f"✗ voc/{fname} missing")
            continue
        text = p.read_text()
        if OLD_HASH in text:
            text_new = text.replace(OLD_HASH, NEW_HASH)
            log.append(f"✓ voc/{fname}: PASS_HASH corrected {OLD_HASH} → {NEW_HASH}")
            if not args.dry_run:
                p.write_text(text_new)
                changed += 1
        elif NEW_HASH in text:
            log.append(f"· voc/{fname}: PASS_HASH already correct (skip)")
        else:
            log.append(f"✗ voc/{fname}: neither old nor new hash found")

    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print()
    for line in log:
        print(line)
    print()
    print(f"Files changed: {changed}")
    ok = all(not line.startswith("✗") for line in log)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
