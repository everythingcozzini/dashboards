# Cozzini Dashboard Automation — Setup Guide

Everything needed to run the dashboard auto-updater on a new Mac.

## What This Does

1. You drop a new Excel survey file into the `Dash/` folder
2. `watcher.py` detects it within seconds
3. Parses the data, updates the matching HTML dashboard
4. Pushes to GitHub — live on https://everythingcozzini.github.io/dashboards/

No manual steps. Fully automatic.

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

The watcher classifies files by keyword in the filename:

| Filename pattern | Dashboard updated |
|------------------|-------------------|
| `*nps*existing*.xlsx` | nps.html |
| `*customer*churn*.xlsx` | customerchurn.html |
| `*product*churn*.xlsx` | productchurn.html |
| `*ces_price*.xlsx` | ces.html (pricing) |
| `*ces_onboard*.xlsx` | ces.html (onboarding) |
| `*ces_knife*.xlsx` | ces.html (knife sharpness) |
| `*ces_driver_service*.xlsx` | ces.html (driver service) |
| `*ces_invoice_payment*.xlsx` | ces.html (invoice payment) |
| `*ces_invoice_under*.xlsx` | ces.html (invoice understanding) |

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

# Restart the background agent
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Agent shows exit code 78 | Path issue — check all paths in plist and wrapper script |
| Agent shows `-` for PID | Not running — check log file for errors |
| Dashboard not updating | Check watcher.log — file may not match naming pattern |
| Git push fails | Check git credentials / SSH keys are configured |
| "No changes to commit" | File was already processed — delete `.processed_files.json` to reprocess |

---

*Last updated: April 2026*
