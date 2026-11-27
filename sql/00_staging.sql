-- 00_staging.sql : typed tables from data/public (PUBLIC DATA) and data/sim (SIMULATED).
-- URSSAF values arrive as text ('2635.0'): read everything as VARCHAR, then TRY_CAST.

CREATE OR REPLACE TABLE ae_dept AS
SELECT code_region, region, code_departement AS dep, departement,
       TRY_CAST(annee AS INT) AS annee, TRY_CAST(trimestre AS INT) AS trimestre,
       CAST(dernier_jour_du_trimestre AS DATE) AS q_end,
       TRY_CAST(immatriculations AS DOUBLE) AS immat, TRY_CAST(radiations AS DOUBLE) AS radiations,
       TRY_CAST(chiffres_d_affaires AS DOUBLE) AS turnover,
       TRY_CAST(economiquement_actifs AS DOUBLE) AS eco_active, TRY_CAST(administrativement_actifs AS DOUBLE) AS registered
FROM read_csv('data/public/urssaf_ae_departement.csv', all_varchar = true);

CREATE OR REPLACE TABLE ae_sector AS
SELECT secteur_d_activite AS sector, split_part(secteur_d_activite, ' - ', 1) AS sector_code,
       CAST(dernier_jour_du_trimestre AS DATE) AS q_end,
       TRY_CAST(economiquement_actifs AS DOUBLE) AS eco_active, TRY_CAST(administrativement_actifs AS DOUBLE) AS registered
FROM read_csv('data/public/urssaf_ae_secteur_national.csv', all_varchar = true);

CREATE OR REPLACE TABLE ti_national AS
SELECT type_de_travailleur_independant AS ti_type, CAST(dernier_jour_du_trimestre AS DATE) AS q_end,
       TRY_CAST(nombre_de_ti_actifs AS DOUBLE) AS n_active
FROM read_csv('data/public/urssaf_ti_national.csv', all_varchar = true);

CREATE OR REPLACE TABLE ti_income AS
SELECT type_de_travailleur_independant AS ti_type, code_region, region, code_departement AS dep, departement,
       TRY_CAST(annee AS INT) AS annee, TRY_CAST(nombre_de_ti AS DOUBLE) AS n_ti, TRY_CAST(revenu AS DOUBLE) AS income_total
FROM read_csv('data/public/urssaf_revenus_departement.csv', all_varchar = true);

CREATE OR REPLACE TABLE insee AS
SELECT month, CAST(month || '-01' AS DATE) AS month_start, TRY_CAST(creations_raw AS DOUBLE) AS raw,
       TRY_CAST(creations_sa AS DOUBLE) AS sa
FROM read_csv('data/public/insee_micro_creations_monthly.csv', all_varchar = true);

CREATE OR REPLACE TABLE dep_area AS
SELECT code_departement AS dep, TRY_CAST(area_km2 AS DOUBLE) AS area_km2
FROM read_csv('data/public/departements_area.csv', all_varchar = true);

-- sector -> sub-segment (docs/assumptions.md); new founders are a cross-cutting group handled in the simulation
CREATE OR REPLACE TABLE sector_map AS
SELECT * FROM (VALUES ('JZ', 'Consulting & IT'), ('M1', 'Consulting & IT'), ('M2', 'Consulting & IT'), ('M3', 'Consulting & IT'),
  ('M4', 'Consulting & IT'), ('M5', 'Consulting & IT'), ('KZ', 'Consulting & IT'), ('LZ', 'Consulting & IT'),
  ('F1', 'Construction & crafts'), ('F2', 'Construction & crafts'), ('F3', 'Construction & crafts'), ('CZ1', 'Construction & crafts'),
  ('CZ2', 'Construction & crafts'), ('S1', 'Construction & crafts'), ('G1', 'Construction & crafts'),
  ('QZ', 'Health & wellbeing'), ('S2', 'Health & wellbeing'), ('R2', 'Health & wellbeing')) t(sector_code, subsegment);

-- simulated tables
CREATE OR REPLACE TABLE acq AS
SELECT * FROM read_csv('data/sim/acq_weekly.csv', types = {'region_code': 'VARCHAR', 'week': 'DATE'});
CREATE OR REPLACE TABLE organic AS
SELECT * FROM read_csv('data/sim/organic_weekly.csv', types = {'region_code': 'VARCHAR', 'week': 'DATE'});
CREATE OR REPLACE TABLE cal AS SELECT * FROM read_csv('data/sim/calendar_weekly.csv', types = {'week': 'DATE'});
CREATE OR REPLACE TABLE curves AS SELECT * FROM read_csv('data/sim/response_curves.csv');
CREATE OR REPLACE TABLE experiments AS SELECT * FROM read_csv('data/sim/experiments.csv');
CREATE OR REPLACE TABLE arms AS SELECT * FROM read_csv('data/sim/experiment_arms.csv', types = {'week': 'DATE'});
CREATE OR REPLACE TABLE geo AS
SELECT * FROM read_csv('data/sim/geo_test_x3.csv', types = {'departement_code': 'VARCHAR', 'week': 'DATE'});
CREATE OR REPLACE TABLE creatives AS SELECT * FROM read_csv('data/sim/creatives.csv');
CREATE OR REPLACE TABLE creative_freq AS SELECT * FROM read_csv('data/sim/creative_frequency.csv');
CREATE OR REPLACE TABLE referrals AS SELECT * FROM read_csv('data/sim/referrals.csv');
