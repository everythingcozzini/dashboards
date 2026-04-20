# iPhone 13 Responsive Audit — 2026-04-19

Target: 390×844 px portrait. Min touch 44×44, min font 12px, 12px radius.

## Summary

| File | Critical | Moderate | Status |
|---|---|---|---|
| index.html | 0 | 1 | OK |
| voc/index.html | 0 | 1 | OK |
| voc/nps.html | 2 | 3 | Patch |
| voc/customerchurn.html | 1 | 2 | Patch |
| voc/productchurn.html | 1 | 2 | Patch (non-feedback) |
| voc/ces.html | 1 | 2 | Patch |
| voc/sdorg.html | 0 | 1 | OK (Tailwind 768) |
| mkt/index.html | 0 | 1 | OK |
| mkt/q1.html | 2 | 3 | Patch |
| mkt/q2.html | 1 | 0 | Patch (gate) |
| mkt/q3.html | 1 | 0 | Patch (gate) |
| mkt/q4.html | 1 | 0 | Patch (gate) |

## Per-file findings + patch plan

### index.html
Only bp=780. `.tile .cta` ~36px tall (<44px).
```css
@media (max-width: 480px) {
  .hero { padding: 24px 16px 20px; }
  .hero h1 { font-size: 24px; }
  .tile { padding: 24px 18px; min-height: 200px; }
  .tile h2 { font-size: 22px; }
  .tile .cta { padding: 12px 22px; }
  .topbar { padding: 12px 16px; }
  .footer { padding: 16px; }
}
```

### voc/index.html
bp=700; dash-items stack fine.
```css
@media (max-width: 480px) {
  .page-title { padding: 24px 16px 8px; }
  .page-title h1 { font-size: 22px; }
  .container { padding: 12px 16px 32px; }
  .dash-item { padding: 16px 14px; gap: 12px; }
  .dash-item h3 { font-size: 14px; }
  .dash-item p { font-size: 12px; }
  .topbar { padding: 12px 16px; }
  .topbar img { height: 22px; }
  .footer { padding: 16px; }
}
```

### voc/nps.html
**Critical:** inline gate `width:380px;padding:48px` (line 139) = 476px, overflows. `.chart-wrap.tall {height:420px}` cramped.
**Moderate:** bp=900, tab-btn ~30px tall (<44px), gauge-bar tall on narrow.
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; }
  .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; }
  .kpi-card .value { font-size: 28px; }
  .nps-gauge-section { padding: 20px 14px; }
  .nps-gauge-bar { height: 28px; }
  .nps-score-big { font-size: 44px; }
  .chart-wrap { height: 260px; }
  .chart-wrap.tall { height: 340px; }
  .tab-btn { padding: 10px 14px; font-size: 12px; min-height: 40px; }
  .new-cust-row { grid-template-columns: repeat(2, 1fr) !important; }
  .new-chart-pair { grid-template-columns: 1fr !important; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
}
```

### voc/customerchurn.html
**Critical:** gate overflow (line 113). **Moderate:** `.chart-wrap.tall {height:380px}`; filter-btn ~28px.
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .chart-wrap { height: 260px; } .chart-wrap.tall { height: 320px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .feedback-section { padding: 14px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
}
```

### voc/productchurn.html
**Critical:** gate overflow (line 109). (Scope excludes feedback-table.)
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .chart-wrap { height: 260px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
}
```

### voc/ces.html
**Critical:** gate overflow (line 127). **Moderate:** `.center-chart .chart-wrap{height:340px}`, `.overview-chart .chart-wrap{height:320px}`.
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 28px; }
  .overview-chart .chart-wrap { height: 260px; }
  .chart-card .chart-wrap { height: 220px; }
  .center-chart .chart-wrap { height: 280px; }
  .filter-btn { padding: 10px 14px; min-height: 40px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
}
```

### voc/sdorg.html
Tailwind bundle, 768px switch fine. Gate width only.
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
}
```

### mkt/index.html
Gate `.auth-box{width:380px;padding:48px}` (line 26) overflows.
```css
@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .page-title { padding: 24px 16px 8px; } .page-title h1 { font-size: 22px; }
  .container { padding: 12px 16px 32px; }
  .quarter-grid { grid-template-columns: 1fr !important; gap: 12px; }
  .quarter-tile { min-height: 120px; padding: 20px 18px; }
  .quarter-label { font-size: 24px; }
  .topbar { padding: 12px 16px; } .footer { padding: 16px; }
}
```

### mkt/q1.html
**Critical:** inline gate overflow (line 116); `full-chart` 320px tight.
```css
@media (max-width: 480px) {
  #auth-gate > div { width: 92% !important; max-width: 360px !important; padding: 32px 24px !important; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; } .kpi-card .value { font-size: 26px; }
  .chart-card .chart-wrap { height: 240px; }
  .full-chart .chart-wrap { height: 280px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
}
```

### mkt/q2.html, mkt/q3.html, mkt/q4.html
**Critical:** `.auth-box{width:380px;padding:48px}` (line 17) overflows.
```css
@media (max-width: 480px) {
  .auth-box { width: 92%; max-width: 360px; padding: 32px 24px; }
  .header { padding: 16px; } .header h1 { font-size: 20px; }
  .empty-state { padding: 40px 20px; }
  .empty-state h2 { font-size: 20px; }
  .empty-icon { width: 60px; height: 60px; font-size: 26px; }
}
```

## Cross-file patterns

1. **Gate overflow everywhere:** `width:380px + padding:48px` = 476px on every gated page.
2. **No ≤480px breakpoint:** all dashboards stop at 900/780/700 — 390px gets cramped variants of tablet layout.
3. **Touch targets <44px:** `.filter-btn` / `.tab-btn` ~28–30px tall.
4. **Chart heights 320–420px** too tall on mobile.
5. **Table padding 10–12px** wastes width; 8×6 + 11px font keeps `overflow-x:auto` rarely needed.
6. **Fonts 11px on kickers/chart-sub** borderline but within design; leaving.

## Proposed shared base responsive rules

```css
@media (max-width: 480px) {
  #auth-gate > div,
  .auth-box {
    width: 92% !important;
    max-width: 360px !important;
    padding: 32px 24px !important;
  }
  .header { padding: 16px; }
  .header h1 { font-size: 20px; }
  .container { padding: 12px; }
  .kpi-card { padding: 16px; }
  .kpi-card .value { font-size: 28px; }
  .section-title { font-size: 16px; margin: 24px 0 14px; }
  .chart-wrap { height: 260px; }
  .chart-wrap.tall { height: 320px; }
  .filter-btn, .tab-btn { padding: 10px 14px; min-height: 40px; font-size: 12px; }
  thead th, tbody td { padding: 8px 6px; font-size: 11px; }
  .footer { padding: 16px; flex-direction: column; gap: 8px; text-align: center; }
}
```

Runner: append before `</style>` in each file; exempt productchurn feedback-table.
