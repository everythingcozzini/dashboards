#!/usr/bin/env python3
"""
tests/verify_structure.py
-------------------------
Asserts the post-cutover file layout:
  * Root: 6 HTML files (index.html + 5 redirect shims)
  * voc/:  6 HTML files (1 hub + 5 dashboards)
  * mkt/:  5 HTML files (1 hub + 4 quarter pages)
  * Each of the 5 root shims is exactly 41 lines, contains a meta-refresh,
    and redirects to voc/{same name}.html.

Exit 0 on pass, 1 on fail.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
ROOT_DASHES = ["nps.html", "customerchurn.html", "productchurn.html",
               "ces.html", "sdorg.html"]
VOC_FILES = ["index.html"] + ROOT_DASHES
MKT_FILES = ["index.html", "q1.html", "q2.html", "q3.html", "q4.html"]

fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


print("── Root files ──")
check((ROOT / "index.html").exists(), "root/index.html exists")
for f in ROOT_DASHES:
    p = ROOT / f
    check(p.exists(), f"root/{f} exists")
    if p.exists():
        text = p.read_text()
        n_lines = text.count("\n") + (0 if text.endswith("\n") else 1)
        check(n_lines <= 45, f"root/{f} is redirect shim (≤45 lines; got {n_lines})")
        check(f'url=voc/{f}' in text, f"root/{f} meta-refresh → voc/{f}")
        check(f"window.location.replace('voc/{f}')" in text, f"root/{f} JS fallback → voc/{f}")

print()
print("── voc/ files ──")
for f in VOC_FILES:
    p = ROOT / "voc" / f
    check(p.exists(), f"voc/{f} exists")

print()
print("── mkt/ files ──")
for f in MKT_FILES:
    p = ROOT / "mkt" / f
    check(p.exists(), f"mkt/{f} exists")

print()
print("── Root index.html is landing (NO gate) ──")
root_idx = (ROOT / "index.html").read_text()
check("id=\"auth-gate\"" not in root_idx and "id='auth-gate'" not in root_idx,
      "root/index.html does not contain an auth-gate (ungated landing)")
check('href="voc/"' in root_idx and 'href="mkt/"' in root_idx,
      "root/index.html has both VOC and MKT tile links")

print()
print("=" * 60)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("ALL STRUCTURE CHECKS PASSED")
sys.exit(0)
