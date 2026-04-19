# Cozzini Dashboard Automation — Setup Guide

Everything needed to run the dashboard auto-updater on a new Mac.

## What This Does

1. You drop a new Excel survey file into the `Dash/` folder
2. `watcher.py` detects it within seconds
3. Parses the data and updates the matching HTML dashboard **inside `voc/`**
4. Pushes to GitHub — live on https://everythingcozzini.github.io/dashboards/

No manual steps. Fully automatic.

---

## Site Structure (Post-April 2026 Restructure)

```
https://everythingcozzini.github.io/dashboards/
├── /                   Landing page — two tiles, no password
│                       (Voice of Customer + Marketing)
│
├── /voc/               Voice of Customer — password: Cozzini2026!
│   ├── index.html      VOC hub: 5 dashboard cards
│   ├── nps.html        Net Promoter Score (existing + new customer sections)
│   ├── customerchurn.html
│   ├── productchurn.html
│   ├── ces.html        Customer Effort Score (5 surveys aggregated)
│   └── sdorg.html      Sales & Distribution org chart
│
├── /mkt/               Marketing — password: Marketing2026$
│   ├── index.html      Marketing hub: Q1-Q4 tiles
│   ├── q1.html         Q1 2026 — Social / Budget / Leads (placeholder data)
│   ├── q2.html         Coming-soon stub
│   ├── q3.html         Coming-soon stub
│   └── q4.html         Coming-soon stub
│
└── nps.html / customerchurn.html / productchurn.html / ces.html / sdorg.html
                        Legacy root paths — now redirect shims to /voc/*.html
                        (meta-refresh + JS fallback; preserves old bookmarks)
```

**The watcher writes to `voc/` — never touch root-level HTML dashboards;
those are redirect shims only.**

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `watcher.py` | Main automation — Excel parser + HTML updater + git push |
| `cozzini-dash-watcher.sh` | Shell wrapper for macOS launch agent |
| `com.cozzini.dash.watcher.plist` | macOS Launch Agent config (auto-start on login) |
| `README.md` | This file |

---

## Setup on a New Mac

### 1. Install Python Dependencies

```bash
# Using micromamba (or conda/pip — just needs Python 3.10+)
pip install watchdog openpyxl
```

### 2. Clone the Repo

```bash
git clone https://github.com/everythingcozzini/dashboards.git
cd dashboards
```

### 3. Copy watcher.py to the Dash Folder Root

```bash
cp setup/watcher.py ./watcher.py
```

### 4. Install the Wrapper Script

```bash
mkdir -p ~/.local/bin
cp setup/cozzini-dash-watcher.sh ~/.local/bin/cozzini-dash-watcher.sh
chmod +x ~/.local/bin/cozzini-dash-watcher.sh
```

**Edit the paths** in `~/.local/bin/cozzini-dash-watcher.sh` if your Dash folder or Python location differs:
- `DASH_DIR=` — full path to the Dash folder
- `PYTHON=` — full path to python3 with watchdog/openpyxl installed

### 5. Install the Launch Agent

```bash
cp setup/com.cozzini.dash.watcher.plist ~/Library/LaunchAgents/
```

**Edit the paths** in the plist if needed:
- `ProgramArguments` — path to the wrapper script
- `StandardOutPath` / `StandardErrorPath` — log file location
- `PATH` environment variable — must include your Python's bin directory

### 6. Start the Agent

```bash
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
```

### 7. Verify

```bash
# Check it's running
launchctl list | grep cozzini.dash
# Should show a PID (number) and exit code 0

# Check the log
cat ~/.local/bin/dash-watcher.log
# Should show "Cozzini Dashboard Watcher started"
```

---

## File Naming Convention

The watcher classifies files by keyword in the filename and writes the
updated HTML to `voc/` (NOT to the project root):

| Filename pattern | Dashboard updated |
|------------------|-------------------|
| `*nps*existing*.xlsx` | `voc/nps.html` (existing-customer section) |
| `*nps*new*.xlsx` | `voc/nps.html` (new-customer section at bottom) |
| `*customer*churn*.xlsx` | `voc/customerchurn.html` |
| `*product*churn*.xlsx` | `voc/productchurn.html` |
| `*ces_price*.xlsx` | `voc/ces.html` (pricing) |
| `*ces_onboard*.xlsx` | `voc/ces.html` (onboarding) |
| `*ces_knife*.xlsx` | `voc/ces.html` (knife sharpness) |
| `*ces_driver_service*.xlsx` | `voc/ces.html` (driver service) |
| `*ces_invoice_payment*.xlsx` | `voc/ces.html` (invoice payment) |
| `*ces_invoice_under*.xlsx` | `voc/ces.html` (invoice understanding) |

When a matching xlsx lands in `Dash/`, the watcher reads it, updates the
target HTML, and auto-commits + auto-pushes to `origin/main`.

---

## Password Gates

| Section | Password | PASS_HASH (simpleHash output) | sessionStorage key |
|---|---|---|---|
| `/voc/` | `Cozzini2026!` | `b2917ac7` | `cozzini-auth` |
| `/mkt/` | `Marketing2026$` | `90ec951c` | `mkt-auth` |
| `/` (root landing) | _no gate_ | — | — |

The in-page `simpleHash(password)` must equal `PASS_HASH`. The code also
accepts a literal-string fallback — this is client-side only and not
security-sensitive (anyone can read the page source).

---

## Local Integrity Tests

The `tests/` folder at the project root contains a standalone audit
toolkit. Run after any manual edit or before a push:

```bash
cd /path/to/Dash
bash tests/run_all.sh
```

Expected output:
```
1. Recompute ground-truth from xlsx       ✓
2. Structure audit                        ✓
3. Palette integrity                      ✓
4. Gate configuration                     ✓
5. Data accuracy (productchurn)           ✓
SUMMARY   passed: 5    failed: 0
```

Individual runners:
- `tests/recompute_productchurn.py` — prints what product_churn.xlsx should yield
- `tests/run_parsers_local.py` — runs every watcher updater, skips git push (safe dry-run)
- `tests/fix_productchurn_revert.py` — one-shot palette + chart-shape revert
- `tests/fix_voc_integrity.py` — corrects kicker color + PASS_HASH

---

## Manual Commands

```bash
# Run watcher in foreground (see live output)
cd /path/to/Dash
python3 watcher.py

# Process all pending files once and exit
python3 watcher.py --once

# Stop the background agent
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Restart the background agent (picks up new watcher.py)
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Check agent status
launchctl list | grep cozzini.dash

# Run a full local integrity check
bash tests/run_all.sh

# Run parsers without pushing (useful for local verification)
python3 tests/run_parsers_local.py
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Agent shows exit code 78 | Path issue — check all paths in plist and wrapper script |
| Agent shows `-` for PID | Not running — check log file for errors |
| Dashboard not updating | Check watcher.log — file may not match naming pattern |
| Dashboard KPI didn't change | Check HTML structure hasn't changed (regex may not match — see `tests/verify_data.py`) |
| Git push fails | Check git credentials / SSH keys are configured |
| "No changes to commit" | File was already processed — delete `.processed_files.json` to reprocess |
| Old HTML shows after an edit | `__pycache__/` bytecode is stale — `rm -rf __pycache__/` and restart agent |
| Watcher processing but values wrong | Run `python3 tests/recompute_productchurn.py` to see truth; compare to HTML |

---

## Recovery / Rollback

If something breaks badly:

```bash
# Hard reset to pre-restructure state (tag on origin/main)
git fetch --tags
git reset --hard backup/pre-restructure-2026-04-19
git push --force-with-lease origin main    # CAUTION — destructive

# Or restore a specific file from the tag
git checkout backup/pre-restructure-2026-04-19 -- path/to/file

# Or unpack the local tarball
cd ~/Dash_backups
tar -xzf dash-pre-push-20260419-160806.tar.gz
# Then compare / copy files manually
```

---

## Architecture Summary

```
xlsx file dropped in Dash/
        ↓
   watcher.py (watchdog observer)
        ↓ classify_file() matches filename pattern
        ↓
   parse_<dashboard>(xlsx) — returns a typed dict
        ↓
   update_<dashboard>_html(data) — regex-patches voc/*.html
        ↓
   git_push(files, commit_msg) — stages, commits, pushes to origin/main
        ↓
   GitHub Pages rebuilds
        ↓
   Live at https://everythingcozzini.github.io/dashboards/voc/<page>.html
```

---

*Last updated: April 2026 — post VOC/MKT restructure*
