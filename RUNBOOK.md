# Cozzini Dashboards — Project Runbook

> Read this before touching the code. It covers the whole pipeline: what's on
> disk, what each file does, how the auto-updater works, how to recover from a
> bad push, and which regex booby-traps are latent in the HTML updaters.

## What this system does (1-paragraph summary)

The Cozzini Dashboards project is a GitHub Pages static site, served from the
`main` branch of `everythingcozzini/dashboards`, that presents two gated sections
of internal reporting: **Voice of Customer (VOC)** — 5 dashboards covering NPS,
Customer Churn, Product Churn, CES, and the S&D Org — and **Marketing (MKT)** —
four quarterly dashboards (Q1 live, Q2–Q4 stubs). A Python file-watcher
(`watcher.py`) runs as a macOS LaunchAgent on Pamela's Mac: when an `.xlsx` file
is dropped into `Dash/`, the watcher classifies it by filename keywords, parses
it with `openpyxl`, injects fresh numbers/chart data into the matching
`voc/*.html` file via targeted regex replacements, then `git add / commit / push`
to origin/main — which GitHub Pages auto-deploys within ~30 seconds. No manual
steps; drop file, wait for the push, refresh the page.

---

## Live URL + gated sections

| Section | URL | Gate |
|---------|-----|------|
| Landing page | `https://everythingcozzini.github.io/dashboards/` | ungated |
| VOC hub | `.../voc/` | password: `Cozzini2026!` |
| MKT hub | `.../mkt/` | password: `Marketing2026$` |
| VOC dashboards | `.../voc/{nps,customerchurn,productchurn,ces,sdorg}.html` | inherit VOC gate via sessionStorage |
| MKT quarterly | `.../mkt/{q1,q2,q3,q4}.html` | inherit MKT gate |

Repo remote: `https://github.com/everythingcozzini/dashboards.git`

The root page is intentionally ungated — it's just two tiles. The individual
HTML files under `voc/` and `mkt/` each carry their own auth gate script so a
direct deep-link (e.g. someone bookmarks `voc/nps.html`) still prompts for a
password.

---

## Repo layout

All paths are relative to `/Users/pperretti/Library/CloudStorage/OneDrive-CozziniBros(2)/claude/Dash/`.

```
Dash/
├── index.html                         # Landing page — 2 tiles, no gate
├── nps.html                           # Redirect shim → voc/nps.html
├── customerchurn.html                 # Redirect shim → voc/customerchurn.html
├── productchurn.html                  # Redirect shim → voc/productchurn.html
├── ces.html                           # Redirect shim → voc/ces.html
├── sdorg.html                         # Redirect shim → voc/sdorg.html
│
├── watcher.py                         # THE pipeline (64KB). gitignored from root.
├── watcher.log                        # Rolling log (gitignored)
├── run-watcher.sh                     # Bare-bones root wrapper (gitignored)
├── .processed_files.json              # Content signature cache {filename: {size, mtime}} (gitignored)
├── .am_reference.json                 # DSD → [AM names] cache for NPS drilldown (gitignored)
├── .gitignore
│
├── voc/                               # VOC-gated section
│   ├── index.html                     # VOC hub (5 dashboard links)
│   ├── nps.html                       # 36 KB — full NPS dashboard (written by watcher)
│   ├── customerchurn.html             # 32 KB
│   ├── productchurn.html              # 26 KB
│   ├── ces.html                       # 21 KB — aggregates 6 CES surveys
│   └── sdorg.html                     # 278 KB — hand-curated org chart, updated by sdorg skill
│
├── mkt/                               # MKT-gated section
│   ├── index.html                     # MKT hub (Q1 live, Q2-Q4 "Coming soon")
│   ├── q1.html                        # 21 KB — Q1 2026 marketing dashboard
│   ├── q2.html                        # Stub (132 lines placeholder)
│   ├── q3.html                        # Stub
│   └── q4.html                        # Stub
│
├── setup/                             # New-Mac install kit — all tracked
│   ├── watcher.py                     # Mirror of root watcher.py (kept in lockstep)
│   ├── cozzini-dash-watcher.sh        # LaunchAgent entry-point wrapper
│   ├── com.cozzini.dash.watcher.plist # macOS launchd definition
│   └── README.md                      # Install guide (slightly outdated — see note below)
│
├── tests/                             # Local verifier toolkit (all runnable)
│   ├── run_all.sh                     # Master runner
│   ├── recompute_productchurn.py      # Ground-truth dump from xlsx
│   ├── verify_structure.py            # File layout + redirect shim contracts
│   ├── verify_palette.py              # Ensures pastel palette, no Warm-fork hexes
│   ├── verify_gates.py                # PASS_HASH/sessionStorage/fallback-string sanity
│   ├── verify_data.py                 # Dashboard numbers match xlsx truth
│   ├── run_parsers_local.py           # Run watcher parsers w/o git push
│   ├── fix_productchurn_revert.py     # One-shot: undo the Warm-palette fork
│   ├── fix_voc_integrity.py           # One-shot: fix decoy PASS_HASH + kicker color
│   └── _productchurn_truth.json       # Output from recompute_productchurn.py
│
├── layout/                            # PNG reference screenshots (pre-fork "truth")
│   ├── nps.png customerchurn.png productchurn.png ces.png sdorg.png
│
├── archive/                           # Old xlsx + legacy HTML (ignored via .gitignore? no, checked in)
│   └── (dated xlsx snapshots, old PNGs, product-churn-dashboard.html)
│
├── __pycache__/                       # Python bytecode (gitignored)
│
├── *.xlsx                             # Input data files at repo root (all gitignored)
│   ├── nps_existing_customers.xlsx    # Existing-customer NPS survey export
│   ├── nps_new_customers.xlsx         # New-customer NPS survey (bottom section of nps.html)
│   ├── customer_churn.xlsx
│   ├── product_churn.xlsx
│   ├── ces_*.xlsx                     # 6 CES surveys (price, onboarding, knife, driver, invoice_payment, invoice_understanding)
│   └── DSDs and AMs.xlsx              # DSD→AM reference; feeds .am_reference.json
│
├── claude_code_thread.txt             # Local transcript export (gitignored)
└── RUNBOOK.md                         # This file
```

---

## The watcher pipeline (end-to-end: xlsx drop → live)

`Dash/watcher.py` is the single Python file that owns the whole pipeline.
All parsers + updaters + git ops live in it. The `setup/watcher.py` is a
**mirror copy** that ships with the install kit — it must be kept in lockstep.

### Flow

```
1. User drops file into Dash/
2. watchdog.Observer → DashboardHandler (on_created / on_modified)
3. Debounce: ignore same-path events within 30s
4. Sleep 3s so OneDrive finishes writing
5. Signature check (.processed_files.json) — size+mtime
   ├─ already processed & signature matches → skip
   └─ new or changed → continue
6. classify_file(filename) → (dash_type, ces_subtype)
7. parse_<type>(filepath) → dict
8. update_<type>_html(data) → writes voc/<name>.html in place
9. git_push([changed_files], auto-commit-message)
   ├─ git add <files>
   ├─ git diff --cached --quiet → bail if no changes
   ├─ git commit -m "Auto-update <files> from <filename> (YYYY-MM-DD HH:MM)"
   └─ git push origin main
10. Save signature into .processed_files.json
11. GitHub Pages picks up the commit → site is live in ~30s
```

### Functions in watcher.py

| Function | Line approx | Purpose |
|----------|-------------|---------|
| `load_processed()` / `save_processed(data)` | 58-65 | Read/write `.processed_files.json` |
| `classify_file(filename)` | 71 | Filename → `(dashboard, ces_subtype)` |
| `parse_am_reference(filepath)` | 107 | Parse `DSDs and AMs.xlsx`, normalize DSD names to "Last, First", cache to `.am_reference.json` |
| `load_am_reference()` | 143 | Read cached DSD→AMs dict |
| `parse_nps(filepath)` | 161 | Handles both NEW format (single `Responses` sheet) and OLD format (`NPS E How Likely` / `Chart` / `Drilldown` sheets). Returns NPS, avg_score, promoters/passives/detractors, distribution 1–10, date range, center_data, drill_center, drill_dsd, drill_am |
| `parse_nps_new_customers(filepath)` | 489 | New-customer NPS — only the bottom section of nps.html |
| `parse_customer_churn(filepath)` | 571 | Reads `churn` sheet; emits satisfaction dim means, support scores, reached-out %, sentiment-classified verbatim feedback |
| `parse_product_churn(filepath)` | 708 | Reads `product_churn` sheet. Priority-counting logic: standard reasons count first; "Other (exclusive)" only when no standard reason flagged |
| `parse_ces_file(filepath, ces_type)` | 866 | Per-CES-survey parser; emits mean, n, dist[1..7], per-row center/dsd |
| `to_num(val)` | 909 | Coerce Excel cell → int/float/None |
| `classify_sentiment(text)` | 921 | Keyword-based classifier → positive/negative/actionable/neutral |
| `update_nps_html(data)` | 965 | Regex-injects NPS numbers + chart data into `voc/nps.html` (preserves AM data if parser didn't provide it) |
| `update_nps_new_customers_section(data)` | 1078 | Updates only the `new-cust-row` block + new-cust charts + respondent table at bottom of `nps.html` |
| `update_customer_churn_html(data)` | 1157 | Same pattern for customerchurn.html |
| `update_product_churn_html(data)` | 1255 | Same pattern for productchurn.html (contains two latent-regex-bug-fixes — see Troubleshooting) |
| `update_ces_html(all_ces_data)` | 1344 | Rebuilds the full surveys/distributions/center/DSD arrays across all 6 CES subtypes |
| `git_push(files, message)` | 1420 | `git add` → `git diff --cached --quiet` guard → commit → `git push origin main` |
| `process_file(filepath)` | 1453 | The orchestrator — dispatches to parser + updater, writes signature, triggers git push |
| `load_all_ces_data()` | 1542 | Glob `Dash/*ces*.xlsx` to aggregate across all 6 CES surveys when any one file changes |
| `DashboardHandler(FileSystemEventHandler)` | 1558 | watchdog event → debounce → signature check → `process_file` |
| `_file_signature(filepath)` | 1599 | `f"{st.st_size}:{st.st_mtime}"` — FULL precision mtime (fixed in commit a66732e) |
| `_already_processed(filepath, filename)` | 1613 | True iff filename is logged AND current signature matches |
| `main()` | 1626 | `--once` mode or long-running Observer loop |

### Dashboard update regexes (HTML injection points)

Every HTML updater uses `re.sub` against the target HTML file. The patterns are
anchored on stable sentinels (CSS class names, `getElementById(...)` strings,
Chart.js `labels:`/`datasets:` blocks, and `const <name> = [...];` assignments).

The KPI card regexes look for blocks of the shape:

```html
<div class="label">Total Cancellations</div>
<div class="value">38</div>
<div class="detail">Across 9 sharpening centers</div>
```

and rewrite the inner numbers. Any structural edit to these blocks (e.g. adding
an icon, changing `class="value"` to `class="kpi-value"`) will silently break
the regex — the dashboard will keep showing stale numbers with no error.

Chart data arrays are updated in place, e.g.:

```js
getElementById('reasonChart') ... datasets: [{ data: [13,6,7,3,2,0], ...
```

The regex captures `data: [...]` and rewrites it. Ordering matters — see
`reason_order` in `update_product_churn_html` for the fixed 6-slot order the
chart expects.

---

## File-naming convention

Files are matched by **keyword in the filename** (case-insensitive), not by
strict glob. All recognizers live in `classify_file()` in `watcher.py`.

| Filename pattern | Dashboard | Notes |
|------------------|-----------|-------|
| `DSDs and AMs.xlsx` (must contain `dsd` AND `am`) | — (cache refresh) | Rebuilds `.am_reference.json`, then re-runs `nps` parse if the NPS xlsx exists |
| `*nps*existing*.xlsx` | `voc/nps.html` (top) | `dash_type = "nps"` |
| `*nps*new*.xlsx` | `voc/nps.html` (bottom "New Customer" section only) | `dash_type = "nps_new"` |
| `*customer*churn*.xlsx` | `voc/customerchurn.html` | `dash_type = "customer_churn"` |
| `*product*churn*.xlsx` | `voc/productchurn.html` | `dash_type = "product_churn"` |
| `*ces_price*.xlsx` | `voc/ces.html` — Pricing Satisfaction section | CES aggregator refreshes all 6 sections every time |
| `*ces_onboard*.xlsx` | `voc/ces.html` — Onboarding Ease | |
| `*ces_knife*.xlsx` | `voc/ces.html` — Knife Sharpness | |
| `*ces_driver_service*.xlsx` | `voc/ces.html` — Driver Service | keyword `driver` + NOT `last` |
| `*ces_driver_last*.xlsx` | (classified but NOT used) | `ces_subtype = "driver_last"` — skipped in `load_all_ces_data` |
| `*ces_invoice_payment*.xlsx` | `voc/ces.html` — Invoice Payment | |
| `*ces_invoice_under*.xlsx` | `voc/ces.html` — Invoice Understanding | |
| Anything else | (skipped, logged to watcher.log) | |

Excel temp files (`~$...`) are ignored. Non-`.xlsx/.xls` files are ignored.

---

## Gate configuration

Both gated hubs use the same pattern: `sessionStorage` flag + a tiny in-page
`simpleHash()` JS function + a literal-string fallback. The fallback means the
gate still works even if the hash is wrong — which is why the decoy hash slipped
through unnoticed before today's fix.

| Section | Password | SHA | sessionStorage key | Files |
|---------|----------|--------|--------------------|-------|
| VOC | `Cozzini2026!` | `b2917ac7` | `cozzini-auth` | all 6 `voc/*.html` |
| MKT | `Marketing2026$` | `90ec951c` | `mkt-auth` | all 5 `mkt/*.html` |

`simpleHash(s)` is a toy JS hash (8-hex-char truncation of a rolling 32-bit
integer with sign-flip). `tests/verify_gates.py` contains a Python port so CI
can verify `simpleHash('<password>') == PASS_HASH` without a browser.

Gate logic (inlined in every gated page):

```js
function simpleHash(s){let h=0;for(let i=0;i<s.length;i++){h=((h<<5)-h)+s.charCodeAt(i);h|=0;}return(h>>>0).toString(16).slice(0,8);}
function checkAuth(){
  const input=document.getElementById('auth-pass').value;
  if(simpleHash(input)===PASS_HASH||input==='Cozzini2026!'){
    // ... unhide #hub-content, set sessionStorage
  }
}
```

This is **not** a security boundary — it's a "keep casual visitors out" latch.
Anyone who views source sees both the hash and the literal fallback. The
repo is marked `noindex, nofollow` and the URL is not linked publicly. If
real auth is ever needed, move to a server-backed gate (GitHub Pages won't do
that; would need Cloudflare Access or similar).

---

## The tests/ toolkit — when + how to use each script

All scripts run from the repo root. No environment setup beyond what watcher.py
already needs (watchdog, openpyxl).

| Script | Purpose | When to run | Expected output |
|--------|---------|-------------|-----------------|
| `tests/run_all.sh` | Master runner for all verifiers in order | Before a push; after any manual HTML edit | `SUMMARY  passed: 4  failed: 0` (after the truth-JSON regen pass) |
| `tests/recompute_productchurn.py` | Dump ground-truth numbers from `product_churn.xlsx` (uses `parse_product_churn` as source of truth) | Re-run whenever `product_churn.xlsx` changes | Writes `tests/_productchurn_truth.json`; prints a table of totals, reasons, centers, products, tenure |
| `tests/verify_structure.py` | Asserts 6 root files (index + 5 shims), 6 voc files, 5 mkt files. Each shim is ≤45 lines with a meta-refresh + JS fallback to `voc/<same>.html`. Root index.html has no auth-gate | Before a push | `ALL STRUCTURE CHECKS PASSED` |
| `tests/verify_palette.py` | Asserts every `voc/*.html` uses Cozzini pastel (`#1a2744, #7bafd4, #d4918b, #d4a45e, #8ebf7b`) and contains NONE of the Warm-fork hexes (`#1b3a4b, #3d7c98, #b44d2d, #c78c3a, #4a7c59`). `voc/sdorg.html` is exempt from the pastel-vars check (org chart has per-node colors by design) but still must be Warm-fork-free | After any palette-adjacent edit | `PALETTE INTEGRITY PASSED` |
| `tests/verify_gates.py` | For every `voc/*.html`: `PASS_HASH` is `b2917ac7`, sessionStorage key is `cozzini-auth`, fallback string is `'Cozzini2026!'`. For every `mkt/*.html`: analogous with `90ec951c` / `mkt-auth` / `'Marketing2026$'` AND no leak of the VOC hash. Root index.html has neither | Before a push | `GATE CONFIGURATION PASSED` |
| `tests/verify_data.py` | Compares KPI numbers + chart data in `voc/productchurn.html` against `_productchurn_truth.json`. Fails on KPI mismatch; warns on chart-data mismatch (chart drift triggers a WARN, not a hard FAIL — run `run_parsers_local.py` to resync) | After a watcher run, before a push | `ALL DATA CHECKS PASSED` (with warnings if charts drifted) |
| `tests/run_parsers_local.py` | Run every watcher parser+updater against the current local xlsx files, **skipping git**. Repopulates all `voc/*.html` in place | When you need to refresh numbers without pushing (e.g. previewing locally, or before running verify_data) | Prints one "✓ <file> → <html>" line per dataset |
| `tests/fix_productchurn_revert.py` | One-shot remediation: undo the Warm-palette fork in `voc/productchurn.html` (CSS vars, auth inline styles, PALETTE array, per-chart backgroundColor arrays, 7-entry reasonChart→6-entry). `--dry-run` to preview | Only if someone reintroduces the Warm fork | Lists each replacement done; writes file |
| `tests/fix_voc_integrity.py` | One-shot remediation: replace the decoy `PASS_HASH = '8a9b0c1d'` with the real `b2917ac7` across all 6 `voc/*.html`, and fix `voc/index.html` auth-box kicker color from MKT-borrowed `#b44d2d` to pastel navy `#1a2744`. `--dry-run` to preview | Only if the decoy hash regresses | Lists each file changed |
| `tests/_productchurn_truth.json` | Output artifact from `recompute_productchurn.py`. Checked in as a snapshot of "what the dashboard should show" | (not run — read by verify_data.py) | — |

---

## Commit history explained

Fresh commits from today (2026-04-19) on `main`, newest first:

| SHA | Title | What it did |
|-----|-------|-------------|
| `314c3c5` | Fix productchurn integrity + repopulate from Excel source | **Latest.** Reverted the Warm-palette fork (cancels 460f172), fixed `voc/index.html` auth-box kicker color from MKT-red `#b44d2d` → pastel navy `#1a2744`, corrected `PASS_HASH` from decoy `8a9b0c1d` → real `b2917ac7` across all 6 `voc/*.html`, **fixed two silent-failure regexes** in `watcher.py` KPI 2 + KPI 3 product-churn updaters, repopulated numbers from `product_churn.xlsx`, kept `setup/watcher.py` in lockstep. 7 files, +33/−30 |
| `460f172` | Revise productchurn.html: Warm Corporate palette + fix churn reasons | Applied a "Warm Corporate" color palette to `voc/productchurn.html` (navy `#1b3a4b`, blue `#3d7c98`, red `#b44d2d`, gold `#c78c3a`, green `#4a7c59`), switched chart to 7-entry with "Other (exclusive)" column. **Reverted** by 314c3c5 because it forked this one file from the 5 sibling VOC pages which still used Cozzini pastel |
| `8dd8ebd` | Restructure: split dashboards into VOC + MKT sections | **The cutover.** Root `index.html` turned into the two-tile landing page. Moved 5 existing root-level dashboards into `voc/*.html`. Replaced the old root paths with 41-line redirect shims (meta-refresh + JS fallback + inline CSS). Added `mkt/` section (Q1 live with full dashboard; Q2/Q3/Q4 stubs). Updated `setup/watcher.py` to write into `voc/`. 19 files, +3381/−1936 |
| `a66732e` | Fix watcher dedup: use full-precision mtime in signature | Removed `int(...)` truncation in `_file_signature`. Previously an xlsx re-save with identical byte-size within the same integer second was misclassified as already-processed. Now `signature = f"{st.st_size}:{st.st_mtime}"` with sub-second precision |
| ...earlier... | `Auto-update ...` | Automated commits from the watcher itself. Every dashboard data refresh is a new commit with an auto-generated message `Auto-update <files> from <xlsx> (YYYY-MM-DD HH:MM)` |

The restructure commit (8dd8ebd) has a pre-restructure safety tag:
`backup/pre-restructure-2026-04-19`. See Recovery.

---

## Launch agent: install, start, stop, restart

The watcher runs as a user LaunchAgent. It auto-starts on login, auto-restarts
if it crashes (but `SuccessfulExit=false` means it does NOT restart on clean
exit — e.g. `Ctrl-C` during a manual foreground run).

### Install on a new Mac

```bash
# 1. Install Python deps (any Python 3.10+ with watchdog + openpyxl)
pip install watchdog openpyxl
# (or use the existing micromamba env: /Users/pperretti/micromamba/envs/workbench)

# 2. Clone
git clone https://github.com/everythingcozzini/dashboards.git
cd dashboards

# 3. Copy the watcher to repo root (it's gitignored from there; setup/ has the tracked copy)
cp setup/watcher.py ./watcher.py

# 4. Wrapper script
mkdir -p ~/.local/bin
cp setup/cozzini-dash-watcher.sh ~/.local/bin/
chmod +x ~/.local/bin/cozzini-dash-watcher.sh
# Edit DASH_DIR and PYTHON paths inside if different from defaults

# 5. LaunchAgent
cp setup/com.cozzini.dash.watcher.plist ~/Library/LaunchAgents/
# Edit ProgramArguments, StandardOutPath, StandardErrorPath, EnvironmentVariables.PATH if needed

# 6. Load it
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
```

### Day-to-day commands

```bash
# Check it's running
launchctl list | grep cozzini.dash
# PID column: number = running; "-" = not running

# Stop
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Start
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Restart (common after updating watcher.py)
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist && \
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist

# Tail the log
tail -f /Users/pperretti/.local/bin/dash-watcher.log
# (the plist redirects stdout+stderr here; watcher.py also writes Dash/watcher.log)

# Run manually in foreground (bypass the agent)
cd "/path/to/Dash" && python3 watcher.py

# One-shot: process all unprocessed xlsx files in Dash/ and exit
python3 watcher.py --once
```

### Key file paths the plist assumes

```
/Users/pperretti/.local/bin/cozzini-dash-watcher.sh       # wrapper (chmod +x)
/Users/pperretti/.local/bin/dash-watcher.log              # stdout+stderr sink
/Users/pperretti/micromamba/envs/workbench/bin/python3    # Python with watchdog+openpyxl
/Users/pperretti/Library/CloudStorage/OneDrive-CozziniBros(2)/claude/Dash  # DASH_DIR
```

---

## Common operations

### Refresh a dashboard from an updated xlsx

Just drop the new file into `Dash/` (or re-save it). The watcher will detect
the size/mtime change and push an `Auto-update ...` commit within ~3 seconds.
Nothing manual required.

If the watcher is off, run once:

```bash
cd "/Users/pperretti/Library/CloudStorage/OneDrive-CozziniBros(2)/claude/Dash"
python3 watcher.py --once
```

### Re-run a parse without pushing (preview-only)

```bash
python3 tests/run_parsers_local.py
# Then:
git diff voc/
```

### Add a new xlsx type (new dashboard)

1. Add a classifier clause in `classify_file()` — pick unique keywords.
2. Add a parser `parse_<type>(filepath)` that returns a dict.
3. Add an updater `update_<type>_html(data)` that regex-injects into your HTML.
   Use existing updaters as a pattern — anchor regex on stable class names and
   Chart.js `getElementById` strings.
4. Dispatch in `process_file()`.
5. Mirror the same changes in `setup/watcher.py` (they must match).
6. Add/extend a test in `tests/verify_data.py`.

### Change a password

1. Hash the new password with the same `simpleHash` JS function (or use
   `simple_hash()` in `tests/verify_gates.py`).
2. In every file under the affected section (`voc/*.html` or `mkt/*.html`):
   - Replace `const PASS_HASH = '<old>';` with the new hex.
   - Replace the literal-string fallback `input==='<old-pass>'` with the new.
3. Update `tests/verify_gates.py` constants (both the hash check and the
   literal-string check).
4. Run `bash tests/run_all.sh` — gate check must pass.
5. Commit and push.

### Add a new section behind its own gate

Copy the `mkt/` pattern. Create a new top-level folder (e.g. `sales/`) with:
- `index.html` with its own `PASS_HASH`, sessionStorage key (`sales-auth`),
  and literal-fallback string.
- Same auth-gate div/script pattern as `voc/index.html`.
- Add a tile to root `index.html`.
- Update `tests/verify_structure.py` + `tests/verify_gates.py` to cover it.

### Add a redirect shim for a moved page

All 5 existing shims (`nps.html`, `customerchurn.html`, `productchurn.html`,
`ces.html`, `sdorg.html`) are identical templates differing only in the target
path and the title prose. Copy one, swap 3 occurrences of the filename, and
update `tests/verify_structure.py` if adding more.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Dashboard numbers unchanged after dropping a new xlsx | File was already processed (same signature) — OR the file doesn't match a `classify_file` keyword | Check `watcher.log`. If it says "Already processed", delete the relevant entry from `.processed_files.json` or re-save the file. If it says "Skipping unrecognized file", the name doesn't match any pattern |
| Dashboard HTML has stale numbers but a commit message says "Auto-update" was pushed | **A regex silently failed.** The updater wrote the file, but one of the `re.sub` calls didn't match, so that KPI/chart never changed. Check whether the HTML's label text or `<div class="...">` structure drifted from what the updater expects | Run `tests/verify_data.py` to spot which values mismatch, then fix either the HTML anchor or the regex in the updater. Two recent examples, both fixed in commit 314c3c5: |
| ⤷ KPI 2 "Avg. Product Subscription Duration" never updating | Old regex required a literal ` days` suffix inside the `<div class="value">` block, but the template only had the unit in the `<div class="detail">` line. Regex never matched | Current regex (watcher.py ~line 1276) no longer requires ` days` after the `\d+` |
| ⤷ KPI 3 "Early Product Cancellations" never updating | Old regex used `[^<]*` to consume the label text, but the label contains `<br>(&lt;90 days)` — `[^<]*` stopped at the `<br>` tag and the rest of the pattern failed | Current regex (watcher.py ~line 1285) uses non-greedy `.*?` with `re.DOTALL` to survive `<br>` inside labels |
| LaunchAgent exit code 78 | Path problem in plist or wrapper script | Verify `/Users/pperretti/.local/bin/cozzini-dash-watcher.sh` exists + `chmod +x`, and that the `PATH` env var in the plist points to a Python that has `watchdog` and `openpyxl` |
| LaunchAgent PID shows `-` | Process died on startup | Tail `/Users/pperretti/.local/bin/dash-watcher.log` and `Dash/watcher.log` for traceback |
| `git push` fails | Missing auth or offline | Check `git remote -v`, `git push origin main` manually. HTTPS auth uses the Mac's Keychain-stored GitHub credential |
| File dropped but watcher didn't fire | Debounce window (30s from same path) OR file wasn't fully written by OneDrive within 3s | Wait 30s, re-save the file, or run `python3 watcher.py --once` |
| "No changes to commit" logged after a parse | Parser ran but the HTML was already correct (or the regex silently failed — see above). Safe case is no-op; unsafe case is stale numbers | If suspicious, run `tests/verify_data.py` |
| `voc/productchurn.html` chart has 7 bars instead of 6 | Warm-fork regression | `python3 tests/fix_productchurn_revert.py` |
| `voc/*.html` PASS_HASH is `'8a9b0c1d'` again | Decoy regression | `python3 tests/fix_voc_integrity.py` |
| Duplicate commits in rapid succession | OneDrive re-sync triggered two modify events under 30s apart AND file size changed between them | Check signatures; normally the debounce handles this. Signature fix (commit a66732e) made this much less likely |

---

## Recovery / rollback

### Safety tag

A tag `backup/pre-restructure-2026-04-19` was created before commit 8dd8ebd
(the VOC/MKT split). Check out the pre-cutover state with:

```bash
git checkout backup/pre-restructure-2026-04-19
# inspect, then return to main:
git checkout main
```

### Revert the most recent auto-update commit

```bash
git revert HEAD              # creates a new "Revert ..." commit
git push origin main
# (GitHub Pages will deploy the revert within ~30s)
```

### Roll back the palette fork

Already done in 314c3c5. If it regresses:

```bash
python3 tests/fix_productchurn_revert.py --dry-run   # preview
python3 tests/fix_productchurn_revert.py             # apply
bash tests/run_all.sh                                # verify
git commit -am "Re-revert productchurn palette fork"
git push origin main
```

### Nuclear option — hard reset to last known good

Make sure you have no uncommitted work, then:

```bash
git fetch origin
git reset --hard origin/main      # blow away local
# OR to go back further:
git reset --hard 8dd8ebd          # the cutover commit, known-good structure
```

(Don't do this without explicit approval.)

### Rebuild all dashboards from current xlsx after a rollback

```bash
python3 tests/run_parsers_local.py   # repopulate voc/*.html from xlsx (no push)
bash tests/run_all.sh                 # verify
git add voc/ && git commit -m "Rebuild dashboards from source data"
git push origin main
```

### Stop/start the watcher during recovery work

```bash
launchctl unload ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
# ... do work ...
launchctl load ~/Library/LaunchAgents/com.cozzini.dash.watcher.plist
```

---

## Source-of-truth table

| Artifact | Canonical source | Generated / derived |
|----------|-------------------|---------------------|
| Dashboard numbers (KPIs, charts) | `Dash/<name>.xlsx` at repo root | `voc/<name>.html` (regenerated by watcher) |
| DSD → AM mapping | `DSDs and AMs.xlsx` | `.am_reference.json` (cache, gitignored) |
| NPS drilldown: AM names column | `.am_reference.json` + NPS xlsx DSD column | `voc/nps.html` drillAM array |
| Gate passwords | The two literal strings `Cozzini2026!` and `Marketing2026$` — typed into the gate by humans | `PASS_HASH` constants in every gated file (hashed via `simpleHash`) |
| Gate hashes | `simpleHash('Cozzini2026!') == 'b2917ac7'` / `simpleHash('Marketing2026$') == '90ec951c'` | Embedded in every gated file |
| Cozzini pastel palette | Screenshots in `Dash/layout/*.png` + `voc/customerchurn.html` (reference implementation) | CSS vars in every `voc/*.html` |
| File-naming rules | `classify_file()` in `watcher.py` | — |
| Ground-truth numbers for `productchurn.html` | `parse_product_churn(product_churn.xlsx)` | `tests/_productchurn_truth.json` via `tests/recompute_productchurn.py` |
| `watcher.py` (repo root) | `setup/watcher.py` (the tracked mirror) | Root copy is gitignored — install by `cp setup/watcher.py ./watcher.py` |
| `voc/sdorg.html` | Hand-curated; updated by the `cozzini-sdorg-updater` skill from `DSDs and AMs.xlsx` | Not touched by watcher.py |
| `mkt/q1.html` | Hand-authored | Not touched by watcher.py (no xlsx pipeline for MKT yet) |
| Root `index.html` | Hand-authored (2-tile landing) | — |
| Root `*.html` shims | Hand-authored, 5 identical templates | Validated by `tests/verify_structure.py` (≤45 lines, meta-refresh + JS fallback) |

---

## Known outdated docs

- `setup/README.md` predates the VOC/MKT split (commit 8dd8ebd). It still
  describes a flat "root-level dashboards" layout and doesn't mention the
  redirect shims, the `voc/`/`mkt/` structure, or the gated landing page. Its
  install instructions (sections 1–7) are still correct. Prefer this RUNBOOK
  for anything layout- or gate-related.

---

*Runbook last updated: 2026-04-19. Dash state as of commit 314c3c5.*
