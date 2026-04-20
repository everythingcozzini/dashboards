#!/usr/bin/env python3
"""
tests/spec_productchurn_v2.py
-----------------------------
Declarative spec for the Product Churn v2 feedback table.

This file encodes the user-approved specification as data (not prose),
so every downstream runner can import it and every verifier can check
against it. Source of truth for:
  - which Excel columns feed which feedback fields
  - what the KPI 4 (top reason) semantic rule is
  - what the feedback table looks like (columns, order, filters)
  - what the section title + subtitle say

User requirements encoded here (verbatim from 2026-04-19 session):
  "We should not count Other as a KPI unless the only answer from the
   customer was Other"
  "include all the customer details at the bottom that added a 'Other'
   and/or 'Is there anything we could have done differently to keep your
   service active?' details"
  1. Section header: "Open-ended comments/responses to 'Other' and/or
     'Is there anything we could have done differently?'"
  2. Keep Actionable / Positive / Negative sentiment filters
  3. Split Feedback column into "Other" | "Is there anything"
  4. Add columns: Area Manager, DSD, Driver, Route, Buying Group, Rep,
     Rep Title
  5. Add leader-useful filters (center / DSD / rep / product / buying group)
  6. iPhone 13 responsive for this table specifically
  7. iPhone 13 responsive for all other dashboards (separate pass)
"""

# ============================================================
# KPI 4 SEMANTIC RULE
# ============================================================
# Top Churn Reason excludes "Other (exclusive)" — we only show a real
# actionable reason. "Other" respondents still appear in the verbatim
# table at the bottom, but the KPI headline should be a standard reason.
KPI4_EXCLUDES_OTHER_EXCLUSIVE = True


# ============================================================
# FEEDBACK SECTION CONTENT
# ============================================================
FEEDBACK_SECTION_TITLE = "Customer Verbatim Feedback"
FEEDBACK_SECTION_SUBTITLE = (
    "Open-ended comments/responses to \"Other\" and/or "
    "\"Is there anything we could have done differently?\""
)


# ============================================================
# EXCEL COLUMN MAP (1-indexed, as used by openpyxl ws.cell(row, col))
# ============================================================
EXCEL_COLS = {
    "center":         1,   # Sharpening Center (or fallback 21)
    "center_alt":     21,
    "email":          2,
    "respondent_num": 3,
    "date":           4,
    "first_name":     5,
    "last_name":      6,
    "email2":         7,
    "company":        8,
    "area_manager":   9,
    "dsd":            10,  # Director - Service and Delivery
    "driver":         11,
    "route":          12,
    "customer_num":   13,
    "buying_group":   14,
    "item_name":      15,
    "product":        16,
    "sales_rep":      17,
    "sales_rep_title": 18,
    "quantity":       19,
    "days_active":    20,
    "other_text":     29,  # Free text when "Other" was selected (or 'X')
    "anything_text":  30,  # Is there anything we could have done differently?
}


# ============================================================
# FEEDBACK TABLE COLUMNS (rendered in this order left-to-right)
# ============================================================
FEEDBACK_TABLE_COLUMNS = [
    # (field key,        display header,     mobile-priority)
    ("company",          "Company",           1),   # always visible
    ("center",           "Sharpening Center", 1),   # always visible
    ("area_manager",     "Area Manager",      2),
    ("dsd",              "DSD",               2),
    ("driver",           "Driver",            3),
    ("route",            "Route",             3),
    ("buying_group",     "Buying Group",      3),
    ("rep",              "Rep",               2),
    ("rep_title",        "Rep Title",         3),
    ("product",          "Product",           1),   # always visible
    ("sentiment",        "Sentiment",         1),   # always visible
    ("other",            "Other",             2),
    ("anything",         "Is there anything", 1),   # always visible
]


# ============================================================
# FILTERS
# ============================================================
# Sentiment filters (existing, must keep)
SENTIMENT_FILTERS = ["all", "actionable", "positive", "negative"]

# Leader-useful dropdown filters (added for v2). All pull unique values
# from the current feedback dataset and default to "All".
DROPDOWN_FILTERS = [
    ("center",       "Sharpening Center"),
    ("dsd",          "DSD"),
    ("rep",          "Sales Rep"),
    ("product",      "Product"),
    ("buying_group", "Buying Group"),
]


# ============================================================
# RESPONSIVE BREAKPOINTS
# ============================================================
# iPhone 13 is 390 CSS px portrait. We use 600px as the "mobile" threshold
# (common tablet-phone boundary) and 430px for deep-mobile (columns
# hidden). Mobile-priority 1 = always visible, 2 = hidden under 600px,
# 3 = hidden under 430px.
BREAKPOINTS = {
    "desktop_min":    769,
    "tablet_max":     768,
    "mobile_max":     600,
    "small_max":      430,
}


# ============================================================
# Meta — allow other runners to import this spec cleanly
# ============================================================
if __name__ == "__main__":
    import json
    import sys
    spec = {
        k: v for k, v in globals().items()
        if k.isupper() and not k.startswith("_")
    }
    json.dump(spec, sys.stdout, indent=2, default=str)
    print()
