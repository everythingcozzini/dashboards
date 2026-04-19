#!/usr/bin/env python3
"""
tests/verify_gates.py
---------------------
Asserts the auth gate configuration is correct and consistent:
  * All voc/*.html (except redirect shims, which have no gate) use
    PASS_HASH = 'b2917ac7' and sessionStorage key 'cozzini-auth'
  * All mkt/*.html use PASS_HASH = '90ec951c' and 'mkt-auth'
  * Gate fallback password strings match section:
      voc → 'Cozzini2026!'
      mkt → 'Marketing2026$'
  * Hash of each password via the in-page simpleHash produces the
    declared PASS_HASH

Exit 0 on pass, 1 on fail.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
VOC = ["index.html", "nps.html", "customerchurn.html",
       "productchurn.html", "ces.html", "sdorg.html"]
MKT = ["index.html", "q1.html", "q2.html", "q3.html", "q4.html"]

fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


def simple_hash(s: str) -> str:
    """Mirror of the in-page JS simpleHash — must match exactly."""
    h = 0
    for ch in s:
        h = (((h << 5) - h) + ord(ch)) & 0xFFFFFFFF
        # replicate JS |= 0 sign flip for values with top bit set
        if h & 0x80000000:
            h -= 0x100000000
    h &= 0xFFFFFFFF
    return f"{h:08x}"[:8]


print("── Password → hash verification ──")
check(simple_hash("Cozzini2026!") == "b2917ac7",
      f"simpleHash('Cozzini2026!') == 'b2917ac7' (got {simple_hash('Cozzini2026!')})")
check(simple_hash("Marketing2026$") == "90ec951c",
      f"simpleHash('Marketing2026$') == '90ec951c' (got {simple_hash('Marketing2026$')})")

print()
print("── voc/ gate configuration ──")
for fname in VOC:
    p = ROOT / "voc" / fname
    if not p.exists():
        check(False, f"voc/{fname} missing")
        continue
    t = p.read_text()
    check("b2917ac7" in t, f"voc/{fname} contains PASS_HASH 'b2917ac7'")
    check("'cozzini-auth'" in t, f"voc/{fname} uses sessionStorage 'cozzini-auth'")
    check("'Cozzini2026!'" in t, f"voc/{fname} literal fallback password present")

print()
print("── mkt/ gate configuration ──")
for fname in MKT:
    p = ROOT / "mkt" / fname
    if not p.exists():
        check(False, f"mkt/{fname} missing")
        continue
    t = p.read_text()
    check("90ec951c" in t, f"mkt/{fname} contains PASS_HASH '90ec951c'")
    check("'mkt-auth'" in t, f"mkt/{fname} uses sessionStorage 'mkt-auth'")
    check("'Marketing2026$'" in t, f"mkt/{fname} literal fallback password present")
    check("b2917ac7" not in t, f"mkt/{fname} does NOT leak voc hash")

print()
print("── root/index.html (landing, should be UNGATED) ──")
t = (ROOT / "index.html").read_text()
check("PASS_HASH" not in t, "root/index.html has no PASS_HASH (ungated)")
check("sessionStorage" not in t, "root/index.html has no sessionStorage (ungated)")

print()
print("=" * 60)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("GATE CONFIGURATION PASSED")
sys.exit(0)
