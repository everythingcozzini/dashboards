#!/bin/bash
# tests/run_all.sh
# -----------------
# Master runner: every verifier in order, short summary at the end.
# Run from Dash/ root: bash tests/run_all.sh
set -u
cd "$(dirname "$0")/.."

pass=0
fail=0

run() {
    name="$1"; shift
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶ $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if "$@"; then
        pass=$((pass + 1))
        echo "  → ✓ $name PASSED"
    else
        fail=$((fail + 1))
        echo "  → ✗ $name FAILED"
    fi
    echo
}

run "1. Recompute ground-truth from xlsx" python3 tests/recompute_productchurn.py >/dev/null
# (we suppressed output above; next tests depend on the JSON it wrote)
python3 tests/recompute_productchurn.py >/dev/null
run "2. Structure audit"                 python3 tests/verify_structure.py
run "3. Palette integrity"               python3 tests/verify_palette.py
run "4. Gate configuration"              python3 tests/verify_gates.py
run "5. Data accuracy (productchurn)"    python3 tests/verify_data.py
run "6. iPhone 13 responsive"            python3 tests/verify_responsive.py

echo "════════════════════════════════════════════════════════════"
echo "SUMMARY   passed: $pass    failed: $fail"
echo "════════════════════════════════════════════════════════════"
exit $fail
