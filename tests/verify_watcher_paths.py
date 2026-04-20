#!/usr/bin/env python3
"""
tests/verify_watcher_paths.py
-----------------------------
Regression guard for the "silent no-commit" bug fixed in 89bf8bc:
  watcher.process_file appended bare filenames (e.g. "nps.html") to
  updated_files, but post-restructure the dashboards live at
  voc/nps.html. `git add nps.html` staged the root redirect shim
  instead (unchanged) → `git diff --cached --quiet` returned 0 →
  "No changes to commit" → nothing ever pushed.

Rules enforced here:
  1. Every updated_files.append("<x>.html") must use a voc/ or mkt/
     prefix. Bare filenames are the bug.
  2. Every html_path assignment that references a dashboard page must
     use VOC_DIR or (future) MKT_DIR — not bare DASH_DIR.

Exit 0 on pass, 1 on fail.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
WATCHER = ROOT / "watcher.py"
SETUP_WATCHER = ROOT / "setup" / "watcher.py"

# Dashboard filenames we expect to see under voc/
VOC_PAGES = {"nps.html", "customerchurn.html", "productchurn.html", "ces.html", "sdorg.html"}

fails = []


def check(cond, msg):
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        fails.append(msg)


def audit(path, label):
    """Scan a watcher.py file for the bug signatures."""
    print(f"── {label}: {path.name} ──")
    if not path.exists():
        check(False, f"{label} missing at {path}")
        return

    text = path.read_text()

    # 1. updated_files.append — every match must have voc/ or mkt/ prefix
    for m in re.finditer(r'updated_files\.append\(\s*"([^"]+)"\s*\)', text):
        arg = m.group(1)
        bare_dashboard = arg in VOC_PAGES
        properly_prefixed = arg.startswith("voc/") or arg.startswith("mkt/")
        check(
            not bare_dashboard or properly_prefixed,
            f"{label}: updated_files.append(\"{arg}\") uses full path (not bare filename)"
        )

    # 2. html_path = DASH_DIR / "<dashboard>.html"  — forbidden
    for m in re.finditer(r'html_path\s*=\s*DASH_DIR\s*/\s*"([^"]+)"', text):
        arg = m.group(1)
        is_dashboard = arg in VOC_PAGES
        check(
            not is_dashboard,
            f"{label}: html_path uses VOC_DIR (not DASH_DIR) for \"{arg}\""
        )


audit(WATCHER, "runtime")
print()
audit(SETUP_WATCHER, "setup")
print()

# 3. Confirm VOC_DIR is defined in both
for path, label in [(WATCHER, "runtime"), (SETUP_WATCHER, "setup")]:
    if path.exists():
        t = path.read_text()
        check("VOC_DIR" in t, f"{label}/watcher.py defines VOC_DIR constant")

# 4. Runtime and setup copies must match
if WATCHER.exists() and SETUP_WATCHER.exists():
    check(
        WATCHER.read_bytes() == SETUP_WATCHER.read_bytes(),
        "runtime watcher.py == setup/watcher.py (in sync)"
    )

print()
print("=" * 60)
if fails:
    print(f"FAILED: {len(fails)} check(s)")
    for f in fails:
        print(f"  - {f}")
    sys.exit(1)
print("WATCHER PATH INTEGRITY PASSED — no bare-filename append bugs")
sys.exit(0)
