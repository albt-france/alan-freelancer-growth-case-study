-- 01_market.sql : size, geography, sectors, income and seasonality of French freelancers (PUBLIC DATA only).

-- national headline numbers
CREATE OR REPLACE TABLE out_market_kpis AS
WITH q AS (SELECT SUM(eco_active) eco, SUM(registered) reg, SUM(immat) immat FROM ae_dept WHERE q_end = DATE '2025-12-31'),
ti AS (SELECT MAX(q_end) q_end,
              SUM(n_active) FILTER (WHERE q_end = (SELECT MAX(q_end) FROM ti_national)) AS ti_total,
              SUM(n_active) FILTER (WHERE q_end = (SELECT MAX(q_end) FROM ti_national) AND ti_type = 'Autoentrepreneur') AS ti_ae,
              SUM(n_active) FILTER (WHERE q_end = (SELECT MAX(q_end) FROM ti_national) AND ti_type = 'TI classique') AS ti_classic
       FROM ti_national),
c AS (SELECT AVG(raw) avg_raw_12m, MAX(month) last_month FROM insee WHERE month_start > (SELECT MAX(month_start) FROM insee) - INTERVAL 12 MONTH)
SELECT q.eco AS ae_eco_active_q4_2025, q.reg AS ae_registered_q4_2025, q.immat AS ae_registrations_q4_2025,
       q.eco / q.reg AS active_share, ti.q_end AS ti_quarter, ti.ti_total, ti.ti_ae, ti.ti_classic,
       c.avg_raw_12m AS creations_per_month_12m, c.last_month AS insee_last_month
FROM q, ti, c;

-- departements: last quarter, registrations over 4 quarters, density, income 2025
CREATE OR REPLACE TABLE out_market_dept AS
WITH last AS (SELECT dep, departement, code_region, region, eco_active, registered FROM ae_dept WHERE q_end = DATE '2025-12-31' AND dep <> 'nca'),
reg4 AS (SELECT dep, SUM(immat) immat_4q FROM ae_dept WHERE q_end > DATE '2024-12-31' GROUP BY dep),
inc AS (SELECT dep,
               SUM(income_total) FILTER (WHERE ti_type = 'Autoentrepreneur') / SUM(n_ti) FILTER (WHERE ti_type = 'Autoentrepreneur') AS income_ae
        FROM ti_income WHERE annee = 2025 GROUP BY dep),
j AS (SELECT l.*, r.immat_4q, a.area_km2, l.eco_active / a.area_km2 AS density_km2, i.income_ae,
             l.eco_active * i.income_ae AS market_value
      FROM last l LEFT JOIN reg4 r USING (dep) LEFT JOIN dep_area a USING (dep) LEFT JOIN inc i USING (dep))
SELECT *, RANK() OVER (ORDER BY market_value DESC NULLS LAST) AS value_rank,
       RANK() OVER (ORDER BY market_value DESC NULLS LAST) <= 5 AS target
FROM j ORDER BY dep;

-- regions: registered vs economically active
CREATE OR REPLACE TABLE out_market_region AS
SELECT code_region, region, SUM(registered) registered, SUM(eco_active) eco_active, SUM(eco_active) / SUM(registered) AS active_share
FROM ae_dept WHERE q_end = DATE '2025-12-31' AND dep <> 'nca'
GROUP BY ALL ORDER BY eco_active DESC;

-- sectors and sub-segments, last quarter and growth since 2019 Q4
CREATE OR REPLACE TABLE out_market_sector AS
SELECT s.sector, s.sector_code, COALESCE(m.subsegment, 'Commerce & services') AS subsegment, s.eco_active,
       s.eco_active / SUM(s.eco_active) OVER () AS share
FROM ae_sector s LEFT JOIN sector_map m USING (sector_code)
WHERE s.q_end = DATE '2025-12-31' AND s.sector_code NOT IN ('_calage_', 'UZ') AND s.eco_active > 0
ORDER BY s.eco_active DESC;

CREATE OR REPLACE TABLE out_market_subsegment_q AS
WITH t AS (
  SELECT COALESCE(m.subsegment, 'Commerce & services') AS subsegment, s.q_end, SUM(s.eco_active) eco
  FROM ae_sector s LEFT JOIN sector_map m USING (sector_code)
  WHERE s.sector_code NOT IN ('_calage_', 'UZ') GROUP BY ALL)
SELECT *, 100 * eco / FIRST_VALUE(eco) OVER (PARTITION BY subsegment ORDER BY q_end) AS index_first_q
FROM t ORDER BY subsegment, q_end;

-- INSEE seasonality: seasonal factor = raw / seasonally adjusted (method break in 2022: levels are not compared across it)
CREATE OR REPLACE TABLE out_insee_monthly AS
SELECT month, YEAR(month_start) AS yr, MONTH(month_start) AS mo, raw, sa, raw / sa AS seasonal_factor
FROM insee ORDER BY month;

CREATE OR REPLACE TABLE out_insee_season_profile AS
SELECT mo, AVG(seasonal_factor) AS avg_factor, MIN(seasonal_factor) AS min_factor, MAX(seasonal_factor) AS max_factor
FROM out_insee_monthly GROUP BY mo ORDER BY mo;
