# Data issues log

| # | Source | Issue | Handling |
|---|---|---|---|
| 1 | URSSAF exports | Numeric fields sometimes arrive as text (`'2635.0'`) | read as text, `TRY_CAST` in `sql/00_staging.sql` |
| 2 | URSSAF | Only 55% of registered auto-entrepreneurs are economically active | the market is sized on economically active ones |
| 3 | URSSAF | Rows with departement `nca` (not classified) | kept in national totals (they are part of the published 1,660,015), excluded from maps and rankings |
| 4 | URSSAF sectors | `_calage_` (calibration) and `UZ` rows | excluded from sector shares |
| 5 | URSSAF | Mayotte (976) absent from the auto-entrepreneur tables | not shown; the four other overseas departements are |
| 6 | URSSAF income | Income is published for auto-entrepreneurs and "classic" self-employed separately | only auto-entrepreneur income is used (the economically active auto-entrepreneurs are the target) |
| 7 | INSEE | Method break in 2022 (`CREATIONS-ENTREPRISES-METHODE-2022`) | seasonality read as raw / seasonally adjusted, no level comparison across 2022 |
| 8 | INSEE | November 2026 not yet published (last month: October 2026) | November 2025 seasonal factor reused in the simulation |
| 9 | Simulation | 3-month activity not observable for the last 13 weeks | `active_3m` left empty; activity rates use mature weeks only |
| 10 | Simulation | AI search impressions not observable | left empty, shown as "not observable" |
| 11 | Etalab | Boundaries file redirects (302) and weighs 2.75 MB | redirect followed once, simplified to about 0.4 MB for the maps |
