# Sources and licences

All public sources were read on 27/11/2026, at most one request per second, downloaded once and cached. No account, key, form or message was used.

| Source | URL | Use | Licence |
|---|---|---|---|
| URSSAF · auto-entrepreneurs by departement (quarterly, 2009-2025) | https://open.urssaf.fr/explore/dataset/auto-entrepreneurs-par-departement/ | market size, active share, registrations, map | ODbL |
| URSSAF · auto-entrepreneurs by departement and sector | https://open.urssaf.fr/explore/dataset/auto-entrepreneurs-par-departement-secteur/ | sub-segment weights, treemap, sector growth | ODbL |
| URSSAF · active self-employed workers, national (quarterly) | https://open.urssaf.fr/explore/dataset/travailleurs-independants-actifs-trimestriels/ | 3.63M self-employed (Q2 2026) | ODbL |
| URSSAF · self-employed income by departement | https://open.urssaf.fr/explore/dataset/les-revenus-des-travailleurs-independants-par-departement/ | average auto-entrepreneur income 2025 | ODbL |
| INSEE BDM · micro-entrepreneur creations, raw (010755410) and seasonally adjusted (010755411) | https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/010755410 | seasonality, simulation calibration | Licence Ouverte / Etalab 2.0 |
| Etalab · departement boundaries 2025 | https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/2025/geojson/departements-100m.geojson | maps (simplified) | Licence Ouverte / Etalab 2.0 |
| Nager.Date · French public holidays 2024-2026 | https://date.nager.at/api/v3/PublicHolidays/2026/FR | holiday weeks in the simulation | MIT (API) |
| Job posting "Growth Marketer" | https://jobs.ashbyhq.com/alan/06e3db02-9cbc-4595-90f8-085b5358c538 (published 18/11/2026) | scope of the role | quoted facts only |
| SIRENE (recherche-entreprises.api.gouv.fr) | ALAN, SIREN 818 353 070; ALAN INSURANCE, SIREN 908 311 103 | identity check of the employer | Licence Ouverte |

## ODbL share-alike
The derived tables in `data/public/` and `data/output/` built from URSSAF data are published under the **ODbL** (Open Database License), as the source requires. Attribution: "URSSAF, open.urssaf.fr".

## Method notes
- INSEE changed its creation-counting method in 2022 (`CREATIONS-ENTREPRISES-METHODE-2022`): levels before and after are not compared; seasonality is read as raw / seasonally adjusted.
- URSSAF values arrive as text: cast with `TRY_CAST`.
- Latest quarter by departement: Q4 2025; income: 2025.
