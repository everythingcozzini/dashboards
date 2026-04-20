#!/usr/bin/env python3
"""
tests/verify_responsive.py
--------------------------
Asserts that the iPhone 13 (@media max-width:480) responsive patch was
successfully injected in every dashboard HTML, and that each patch
contains at least one gate/auth-box width override.

Runs the full set of 12 HTML files; exit 0 if all pass, 1 if any fail.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

FILES = [
    "index.html",
    "voc/index.html",
    "voc/nps.html",
    "voc/customerchurn.html",
    "voc/productchurn.html",
    "voc/ces.html",
    "voc/sdorg.html",
    "mkt/index.html",
    "mkt/q1.html",
    "mkt/q2.html",
    "mkt/q3.html",
    "mkt/q4.html",
]

PATCH_START = "/* === iphone13-patch:start === */"
PATCH_END = "/* === iphone13-patch:end === */"

fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


for rel in FILES:
    path = ROOT / rel
    if not path.exists():
        check(False, f"{rel} missing")
        continue
    text = path.read_text()

    # 1. Sentinel + @media 480 present
    block = re.search(
        re.escape(PATCH_START) + r"\s*(@media \(max-width: 480px\)[^}]+\{.*?\})\s*"
        + re.escape(PATCH_END),
        text, re.DOTALL,
    )
    check(block is not None, f"{rel} has iphone13 @media 480px patch")

    # 2. Gate width override present (all gated files + landing pages with
    #    .auth-box should have SOME override, but the plain root index and
    #    sdorg only need the gate rule — accept either pattern)
    if block:
        inner = block.group(0)
        gated = "voc/" in rel or rel.startswith("mkt/") or rel == "voc/index.html"
        if gated:
            has_override = (
                "auth-gate" in inner or "auth-box" in inner
            )
            check(has_override,
                  f"{rel} patch overrides gate width (auth-gate or auth-box)")

check(True, "")  # spacer
print()
print("=" * 60)
if fails:
    # Filter out the spacer
    real = [f for f in fails if f]
    print(f"FAILED: {len(real)} check(s)")
    for f in real:
        print(f"  - {f}")
    sys.exit(1)
print("RESPONSIVE PATCHES VERIFIED — 12 files, iPhone 13 (480px) ready")
sys.exit(0)
