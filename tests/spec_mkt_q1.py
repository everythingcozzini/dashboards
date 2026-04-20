#!/usr/bin/env python3
"""
tests/spec_mkt_q1.py
--------------------
Declarative spec for the Marketing Q1 "Planned × Results" dashboard.

Source of truth for:
  - which Excel files feed which dashboard section
  - what the Q1 target is for each focus area
  - status thresholds (green/amber/red)
  - the 4 focus areas from Q1Snap.xlsx "Planned" sheet

All downstream runners import from here. Change a target here → dashboard
label + status threshold updates automatically on next build.
"""

# ============================================================
# SOURCE FILES (relative to mkt/Q1/)
# ============================================================
SOURCE_DIR = "mkt/Q1"
SOURCES = {
    "snapshot":        "Q1Snap.xlsx",                                         # "Planned" sheet
    "budget":          "Budget.xlsx",
    "social":          "Social Media.xlsx",
    "matched_leads":   "Q1_2026_Matched_Leads_Detail.xlsx",
    "leads_details":   "Details of Leads Assigned YTD-2026-04-20-04-11-14.xlsx",
}

# ============================================================
# PLANNED × RESULTS — targets per metric
# ============================================================
# Each target has:
#   label           — short display name
#   target_value    — numeric goal
#   target_display  — human-readable target (e.g. ">= 35" or "25%")
#   unit            — "score" | "rating" | "pct" | "dollars" | "count"
#   direction       — "higher_is_better" | "lower_is_better" (budget)
#   amber_at        — value at which we flag amber (between green & red)
#
# metric_type:
#   "point_in_time"    — current-state reading (NPS, CES, Google rating,
#                        post cadence, engagement rate). Compare actual
#                        vs target directly.
#   "cumulative_pacing" — accumulates over the year toward an annual goal.
#                         Compare actual to the *pro-rated* target based
#                         on fraction of year elapsed. E.g. if goal is
#                         25% annual and we're 30% through the year,
#                         expected = 7.5%; actual 12.1% → 161% of pace
#                         → GREEN (ahead of pace).
#   "quarterly"        — the target IS a quarterly figure (e.g. Q1 budget
#                         plan). Compare actual vs Q1 target directly.
#
TARGETS = {
    "nps": {
        "label": "Net Promoter Score",
        "target_value": 35.0,
        "target_display": ">= 35",
        "unit": "score",
        "direction": "higher_is_better",
        "metric_type": "point_in_time",
        "amber_at": 30.0,
    },
    "ces": {
        "label": "Customer Effort Score",
        "target_value": 5.0,
        "target_display": ">= 5.0",
        "unit": "score",
        "direction": "higher_is_better",
        "metric_type": "point_in_time",
        "amber_at": 4.5,
    },
    "google_rating": {
        "label": "Google Reviews Rating",
        "target_value": 4.0,
        "target_display": ">= 4.0 stars",
        "unit": "rating",
        "direction": "higher_is_better",
        "metric_type": "point_in_time",
        "amber_at": 3.0,
    },
    "social_engagement": {
        "label": "Social Media Engagement Rate",
        "target_value": 10.0,
        "target_display": "10% annual",
        "unit": "pct",
        "direction": "higher_is_better",
        # Engagement rate matures as strategy evolves — pacing applies.
        # 5% in Q1 (30% of year) → 1.66x expected pace → green.
        "metric_type": "cumulative_pacing",
        "amber_at": 7.0,
    },
    "posts_per_month": {
        "label": "Social Posts / Month",
        "target_value": 20.0,
        "target_display": ">= 20 / mo",
        "unit": "count",
        "direction": "higher_is_better",
        "metric_type": "point_in_time",
        # 19.3 is 96.5% of target — well inside the "near-target" zone,
        # so a lighter-green status communicates "essentially hitting it."
        "near_at": 17.0,
        "amber_at": 13.0,
    },
    "new_biz_origin": {
        "label": "Marketing Share of New Business",
        "target_value": 25.0,
        "target_display": "> 25% annual",
        "unit": "pct",
        "direction": "higher_is_better",
        "metric_type": "cumulative_pacing",
        "amber_at": 18.0,
    },
    "q1_budget": {
        "label": "Q1 Budget Spend vs Plan",
        "target_value": 68250.0,
        "target_display": "<= $68,250",
        "unit": "dollars",
        "direction": "lower_is_better",
        "metric_type": "quarterly",
        "amber_at": 75000.0,
    },
}

# ============================================================
# THE 4 FOCUS AREAS (from Q1Snap.xlsx "Planned" sheet, rows 8-17)
# ============================================================
FOCUS_AREAS = [
    {
        "name": "Voice of Customer",
        "actions": [
            "Survey all churned customers",
            "Solicit Google reviews",
            "Monitor Customer Effort Score",
        ],
        "metric_keys": ["nps", "ces", "google_rating"],
    },
    {
        "name": "Value Proposition",
        "actions": [
            "Social media / SMS / email / newsletter",
            "Educational content",
        ],
        "metric_keys": ["posts_per_month", "social_engagement"],
    },
    {
        "name": "Revenue Growth",
        "actions": [
            "New customer acquisition",
            "Share of wallet",
        ],
        "metric_keys": ["new_biz_origin"],
    },
]

# ============================================================
# Pacing / status helpers
# ============================================================
def year_fraction_elapsed(today=None):
    """Fraction of the calendar year 2026 that has elapsed (0..1)."""
    from datetime import date
    today = today or date.today()
    start = date(today.year, 1, 1)
    days_elapsed = (today - start).days + 1
    total_days = 366 if today.year % 4 == 0 and (today.year % 100 != 0 or today.year % 400 == 0) else 365
    return max(0.0, min(1.0, days_elapsed / total_days))


def status_for(metric_key, actual, year_frac=None):
    """Returns 'green' | 'amber' | 'red' based on metric type.

    For cumulative_pacing metrics: compare actual vs prorated target.
    For point_in_time: compare actual vs absolute target.
    For quarterly: compare actual vs Q1 target.
    """
    t = TARGETS.get(metric_key)
    if t is None or actual is None:
        return "unknown"

    mtype = t.get("metric_type", "point_in_time")

    if mtype == "cumulative_pacing":
        yf = year_frac if year_frac is not None else year_fraction_elapsed()
        # Expected progress if we were on a linear pace to target
        expected = t["target_value"] * yf
        if expected <= 0:
            return "unknown"
        ratio = actual / expected
        if ratio >= 1.0:   return "green"   # on or ahead of pace
        if ratio >= 0.75:  return "amber"   # modestly behind pace
        return "red"                         # well behind

    # point_in_time or quarterly — direct comparison.
    # "near_at" (optional) gives a lighter-green zone for "essentially
    # hitting the target" (e.g. 19/20 posts/month).
    tgt = t["target_value"]
    amber = t["amber_at"]
    near  = t.get("near_at")
    if t["direction"] == "higher_is_better":
        if actual >= tgt:                 return "green"
        if near is not None and actual >= near: return "green_light"
        if actual >= amber:               return "amber"
        return "red"
    else:
        if actual <= tgt:                 return "green"
        if near is not None and actual <= near: return "green_light"
        if actual <= amber:               return "amber"
        return "red"


def pacing_ratio(metric_key, actual, year_frac=None):
    """Returns a (ratio, expected) tuple for cumulative_pacing metrics.
    Used to show 'X% of annual goal achieved at Y% of year elapsed'.
    Returns (None, None) for non-pacing metrics."""
    t = TARGETS.get(metric_key)
    if t is None or actual is None:
        return (None, None)
    if t.get("metric_type") != "cumulative_pacing":
        return (None, None)
    yf = year_frac if year_frac is not None else year_fraction_elapsed()
    expected = t["target_value"] * yf
    ratio = actual / expected if expected else None
    return (ratio, expected)


# ============================================================
# Dashboard section order (top-to-bottom in the final page)
# ============================================================
SECTIONS = [
    "hero_strip",        # 4 big KPI cards — all trending GREEN at the top
    "highlights",        # "Q1 at a glance" callout bar — quick-read wins
    "focus_scorecard",   # 3 focus-area cards (VoC merged VoE)
    "budget",            # Q1 + YTD plan vs actual + variance
    "lead_funnel",       # 398 → 240 → $387k  (moved above social per user)
    "social_media",      # per-platform split + engagement + post cadence
    # leads_ytd section removed by request — too much noise, not exec-useful
    # Voice of Employee section merged into Voice of Customer per exec
    # feedback (NPS/CES/Google all measure CUSTOMER experience, not employee)
]

# ============================================================
# Cozzini palette (must match voc/* pastel — don't fork)
# ============================================================
PALETTE = {
    "navy":  "#1a2744",
    "blue":  "#7bafd4",
    "red":   "#d4918b",
    "gold":  "#d4a45e",
    "green": "#8ebf7b",
    "lav":   "#a99bc4",
    "yel":   "#d4cb7b",
}

# MKT-specific accent (from mkt/ gate gradient — used sparingly for banner)
MKT_ACCENT = {
    "burnt":  "#b44d2d",
    "burgundy": "#8a2d1f",
    "tan":    "#d4a45e",
}


if __name__ == "__main__":
    import json, sys
    out = {k: v for k, v in globals().items() if k.isupper() and not k.startswith("_")}
    # functions aren't JSON-serializable — skip
    out = {k: v for k, v in out.items() if not callable(v)}
    json.dump(out, sys.stdout, indent=2, default=str)
    print()
