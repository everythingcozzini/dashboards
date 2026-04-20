# PROCESS — How to ship updates to the Cozzini Dashboards

Every change goes through **test environment → preview → commit → push → live**.
Nothing is pushed "from memory" — each kind of change has a runnable script that
encodes the logic, so the same fix can be applied twice and produce the same result.

If you're new to this codebase: read `RUNBOOK.md` first (system architecture),
then this file (workflow).

---

## The 6-step release loop

Every update follows this cycle. Do them in order; don't skip.

### 1. Capture the spec as code (not memory)

Before editing any HTML or parser, write a declarative spec in `tests/` that
encodes the intent. This is "the source of truth" for the change — every
downstream runner reads from it.

Examples:
- `tests/spec_productchurn_v2.py` — columns, filters, section text for v2 table
- `tests/_iphone13_audit.md` — per-file CSS patches (produced by review agent)
- `tests/_productchurn_truth.json` — expected values from parsing the xlsx

**Rule:** if you find yourself saying "I remember that X should be Y," stop
and put `X = Y` in a spec file. Then the next person (or future-you) can verify
without asking.

### 2. Write or update a runner in `tests/`

Every change gets a runner. Naming conventions:

| Prefix | Purpose | Example |
|---|---|---|
| `spec_*.py` | Declarative spec (pure data) | `spec_productchurn_v2.py` |
| `recompute_*.py` | Pulls ground truth from Excel | `recompute_productchurn.py` |
| `fix_*.py` | One-shot fixer (idempotent, `--dry-run`) | `fix_productchurn_revert.py`, `fix_voc_integrity.py` |
| `apply_*.py` | Applies patches across many files | `apply_iphone13_responsive.py` |
| `verify_*.py` | Asserts invariants (exit code 0/1) | `verify_structure.py`, `verify_data.py` |
| `run_*.py` / `run_*.sh` | Executes something (parsers, tests) | `run_parsers_local.py`, `run_all.sh` |

Every runner:
- Has a docstring citing its source of truth
- Supports `--dry-run` if it mutates files
- Is idempotent (run it twice → same result)
- Exits 0 on success, non-zero on failure

### 3. Test locally (push-free harness)

```bash
cd /path/to/Dash
# Run the change
python3 tests/fix_<my_change>.py --dry-run    # preview
python3 tests/fix_<my_change>.py              # apply

# Repopulate dashboards from Excel WITHOUT pushing
python3 tests/run_parsers_local.py

# Full integrity check
bash tests/run_all.sh
```

Expected: **all 6 suites pass** (structure / palette / gates / data / responsive / ground-truth).

If one fails, fix the code OR the runner — but never skip it to "just push." Fix in place.

### 4. Preview in a browser

```bash
# Local HTTP server (stays up between iterations)
cd /path/to/Dash
python3 -m http.server 8765 --bind 127.0.0.1

# Then in a browser:
open http://127.0.0.1:8765/                   # root landing
open http://127.0.0.1:8765/voc/               # VOC gate (Cozzini2026!)
open http://127.0.0.1:8765/mkt/               # MKT gate (Marketing2026$)
```

Click through every page you touched. For layout/responsive changes, use
DevTools "iPhone 13" device mode (390×844) and verify.

### 5. Commit

Stage only the files you intended to touch:

```bash
git add <specific files>    # DON'T use git add .
git status --short          # confirm nothing unexpected staged
git diff --cached --stat    # line-count sanity check
```

Commit message pattern: **headline + bullet list of what changed + why**.
Include any bugs fixed, any decisions made.

```bash
git commit -F /tmp/msg.txt     # use a file for multi-paragraph messages
                               # (shell heredocs break on special chars)
```

### 6. Push (with the watcher off)

The watcher auto-pushes when an xlsx lands. If the watcher fires during your
push, both sides race on `origin/main`. Prevent this:

```bash
# Before push
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Push
git push origin main
git push origin <any-tags>    # if you made tags this session

# After push — reload so the agent picks up new code
rm -rf __pycache__            # force recompile of watcher.py
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
launchctl list | grep cozzini.dash     # confirm PID > 0 and exit code 0
```

GitHub Pages rebuilds in 30–90 s. Check:

```bash
curl -sI https://everythingcozzini.github.io/dashboards/ | head -1
curl -sI https://everythingcozzini.github.io/dashboards/voc/productchurn.html | head -1
```

Both should return `HTTP/2 200`.

---

## Playbooks for specific change types

### A) Adding a new Excel column to an existing dashboard

1. In `product_churn.xlsx` (or whichever): verify column index + header text.
2. `tests/spec_<dashboard>_v<N>.py`: update `EXCEL_COLS` + `TABLE_COLUMNS`.
3. `watcher.py` → `parse_<dashboard>(filepath)`: read the new cell, add to
   the row dict + the returned feedback dict.
4. Dashboard HTML (`voc/<dashboard>.html`): add a `<th>` for the column;
   update JS renderRows to include it.
5. `watcher.py` → `update_<dashboard>_html`: the JSON-injection regex
   (`const feedback = [...]`) already picks up richer shapes; no change needed
   unless you change the JS variable name.
6. Run: `python3 tests/run_parsers_local.py` → check the HTML.
7. Run: `bash tests/run_all.sh`.
8. Preview → commit → push.

### B) Changing a KPI calculation

1. Update the calculation in `watcher.py` (e.g. `top_reason`, `avg_days`).
2. Update `tests/recompute_<dashboard>.py` if the exposed field name changes.
3. Update `tests/verify_data.py` assertions if the expected value changes.
4. Run `python3 tests/run_parsers_local.py` + `bash tests/run_all.sh`.
5. Preview → commit → push.

### C) Adding a new dashboard page (e.g. `voc/newdash.html`)

1. Build the page in `voc/` using an existing dashboard as template
   (`voc/customerchurn.html` is a good reference).
2. Ensure the same pastel CSS vars, same password gate block, same footer.
3. Add a card to `voc/index.html` hub.
4. If it has an Excel backing file:
   - Add a `classify_file()` rule in `watcher.py`.
   - Write `parse_newdash(filepath)` + `update_newdash_html(data)`.
   - Update the file-naming table in `setup/README.md`.
5. Append the new file to the relevant `FILES` list in `tests/verify_structure.py`
   and `tests/verify_palette.py` and `tests/verify_gates.py` and
   `tests/apply_iphone13_responsive.py`.
6. Run all verifiers → preview → commit → push.

### D) Brand / palette change across all dashboards

1. Write a `fix_*.py` runner with a dict of `(warm_hex, target_hex)` per file.
2. `--dry-run` first; inspect the diff.
3. Apply; run `bash tests/run_all.sh`.
4. If `tests/verify_palette.py` fails because new hexes aren't in its
   allow-list, update the verifier's PASTEL or WARM_FORK constants too.
5. Preview on 3+ pages → commit → push.

### E) Responsive / mobile fix

1. Identify the breakpoint + files.
2. Add to `tests/apply_iphone13_responsive.py` → `PATCHES` dict (or
   create a new `apply_<device>_responsive.py` for a different target).
3. Run it; `tests/verify_responsive.py` should pass.
4. DevTools device mode verification → commit → push.

### F) URL / path / routing change (e.g. move files between folders)

⚠️ **High-risk.** Follow this sequence without shortcuts:

1. `git tag -a "backup/pre-<change>-YYYY-MM-DD" <current-HEAD> -m "rollback point"`
2. `tar -czf ~/Dash_backups/pre-<change>-$(date +%Y%m%d-%H%M%S).tar.gz .`
3. Unload watcher (`launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist`).
4. Move files; build redirect shims at old paths if they might be bookmarked.
5. Update `watcher.py` output paths (every `DASH_DIR / "<file>"` → new path).
6. Update `setup/README.md` file-naming table.
7. Run `bash tests/run_all.sh` — should stay green. If a test references an
   old path, update the test.
8. Preview every redirect (curl both old and new URLs).
9. Commit → push → reload watcher → curl live.

---

## Emergency recovery

If something broke live:

### Full repo rollback to last known good
```bash
git fetch --tags
git reset --hard backup/pre-restructure-2026-04-19    # or another tag
git push --force-with-lease origin main               # CAUTION — destructive
```

### Restore a specific file from a backup
```bash
git checkout backup/pre-restructure-2026-04-19 -- voc/productchurn.html
```

### Restore from tarball
```bash
cd ~/Dash_backups
ls -1t                                    # most recent first
tar -tzf <newest>.tar.gz | head -20       # inspect first
# Then extract whatever you need:
tar -xzf <newest>.tar.gz --strip-components=1 -C /tmp/restore-staging
# Compare + copy files manually — never overwrite your working tree blindly
```

### Unload the watcher in a hurry
```bash
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
```

This stops auto-push immediately. Safe to leave unloaded while investigating.

---

## Rules of engagement

1. **No memory-only changes.** If you can't explain a change with a runnable
   script or a spec file, stop and write one.
2. **Idempotent runners only.** Running `fix_X.py` twice must be safe.
3. **Watcher off during commit/push.** Always.
4. **Don't skip `tests/run_all.sh`.** If it fails, fix the code *or* update the
   test — never `--no-verify`.
5. **Backup tag before routing changes.** `git tag backup/pre-<change>-<date>`.
6. **Preview before commit.** Local HTTP server + DevTools mobile mode.
7. **Specific `git add`.** Never `git add .` — it grabs scratch files and noise.
8. **Update the docs** (`setup/README.md`, `RUNBOOK.md`, this file) when the
   workflow changes. A stale doc is worse than no doc.

---

## File map

- `tests/run_all.sh` — run before every commit
- `tests/run_parsers_local.py` — safe dry-run of watcher parsers
- `tests/_*.{json,md}` — generated artifacts used as input to runners
- `setup/README.md` — onboarding + file-naming + manual commands
- `RUNBOOK.md` — system architecture + watcher pipeline + troubleshooting
- `SESSION_LOG.md` — historical decisions (why X was done on Y date)
- `PROCESS.md` — this file — how to ship changes

*Last updated: April 2026 — after productchurn v2 + iPhone 13 responsive pass*
