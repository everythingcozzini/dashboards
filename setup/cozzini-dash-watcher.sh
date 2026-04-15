#!/bin/bash
# Cozzini Dashboard Watcher — launched by macOS LaunchAgent
DASH_DIR="/Users/pperretti/Library/CloudStorage/OneDrive-CozziniBros(2)/claude/Dash"
PYTHON="/Users/pperretti/micromamba/envs/workbench/bin/python3"

# Wait for OneDrive to mount (up to 30s after login)
for i in {1..15}; do
    [ -d "$DASH_DIR" ] && break
    sleep 2
done

if [ ! -d "$DASH_DIR" ]; then
    echo "ERROR: Dash directory not found after 30s: $DASH_DIR" >&2
    exit 1
fi

cd "$DASH_DIR" || exit 1
exec "$PYTHON" watcher.py
