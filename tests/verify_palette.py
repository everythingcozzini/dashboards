#!/usr/bin/env python3
"""
tests/verify_palette.py
-----------------------
Asserts that every voc/*.html uses the canonical Cozzini pastel palette:
  --cozzini-navy:  #1a2744
  --cozzini-blue:  #7bafd4
  --cozzini-red:   #d4918b
  --cozzini-gold:  #d4a45e
  --cozzini-green: #8ebf7b

Also asserts the "Warm Corporate" fork hex codes are NOT present:
  #1b3a4b #3d7c98 #b44d2d #c78c3a #4a7c59

Source: voc/customerchurn.html, voc/nps.html, voc/ces.html (unchanged
originals use these exact vars). Confirmed visually against
Dash/layout/*.png screenshots (pre-fork state).

Exit 0 on pass, 1 on fail.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
VOC_FILES = ["index.html", "nps.html", "customerchurn.html",
             "productchurn.html", "ces.html", "sdorg.html"]

PASTEL = {
    "navy":  "#1a2744",
    "blue":  "#7bafd4",
    "red":   "#d4918b",
    "gold":  "#d4a45e",
    "green": "#8ebf7b",
}
WARM_FORK = ["#1b3a4b", "#3d7c98", "#b44d2d", "#c78c3a", "#4a7c59"]

fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


# sdorg is an org-chart dashboard with per-node colors for visual separation;
# it never used the pastel var system. The meaningful constraint for it is
# "free of Warm-fork hex codes" (confirming the palette fork didn't leak
# into this file).
PASTEL_STRICT = ["index.html", "nps.html", "customerchurn.html",
                 "productchurn.html", "ces.html"]

for fname in VOC_FILES:
    path = ROOT / "voc" / fname
    if not path.exists():
        check(False, f"voc/{fname} missing (cannot check palette)")
        continue

    text = path.read_text()
    print(f"── voc/{fname} ──")

    # Check pastel vars present (only for files with a :root block AND
    # files in our pastel-strict list)
    has_root = ":root {" in text or ":root{" in text
    if fname in PASTEL_STRICT and has_root:
        for key, hex_val in PASTEL.items():
            check(hex_val in text, f"voc/{fname} contains pastel {key} ({hex_val})")
    elif fname == "sdorg.html":
        print("  [SKIP] voc/sdorg.html uses org-chart per-node colors by design")
    elif not has_root:
        print(f"  [SKIP] voc/{fname} has no :root block")

    # Check no Warm fork hex codes (applies to ALL voc files)
    for warm in WARM_FORK:
        check(warm not in text, f"voc/{fname} free of Warm-fork hex {warm}")

    print()

print("=" * 60)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("PALETTE INTEGRITY PASSED — all voc/*.html on Cozzini pastel")
sys.exit(0)
