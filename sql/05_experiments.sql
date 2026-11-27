-- 05_experiments.sql : X1 landing page (E3, sample-ratio mismatch) and X2 referral reward (E5, novelty) (SIMULATED).

-- X1: conversion by arm and the SRM chi-square (1 df; 10.83 = p 0.001)
CREATE OR REPLACE TABLE out_x1 AS
WITH a AS (SELECT arm, SUM(units) n, SUM(conversions) x FROM arms WHERE experiment = 'X1' GROUP BY arm),
w AS (SELECT (SELECT n FROM a WHERE arm = 'test') n_t, (SELECT n FROM a WHERE arm = 'control') n_c,
             (SELECT x FROM a WHERE arm = 'test') x_t, (SELECT x FROM a WHERE arm = 'control') x_c)
SELECT *, n_t / (n_t + n_c) AS share_test, x_t / n_t AS rate_t, x_c / n_c AS rate_c, (x_t / n_t) / (x_c / n_c) - 1 AS lift,
       POWER(n_t - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2) + POWER(n_c - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2) AS srm_chi2,
       (POWER(n_t - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2) + POWER(n_c - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2)) > 10.83 AS srm_flag,
       CASE WHEN (POWER(n_t - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2) + POWER(n_c - (n_t + n_c) / 2, 2) / ((n_t + n_c) / 2)) > 10.83
            THEN 'invalid: sample-ratio mismatch, fix the bot filter and rerun' ELSE 'readable' END AS decision
FROM w;

-- X2: weekly lift and the novelty rule (lift in weeks 1-3 vs weeks 4+)
CREATE OR REPLACE TABLE out_x2_weekly AS
WITH p AS (
  SELECT week_index, week,
         SUM(conversions) FILTER (WHERE arm = 'test') x_t, SUM(units) FILTER (WHERE arm = 'test') n_t,
         SUM(conversions) FILTER (WHERE arm = 'control') x_c, SUM(units) FILTER (WHERE arm = 'control') n_c
  FROM arms WHERE experiment = 'X2' GROUP BY ALL)
SELECT *, (x_t / n_t) / (x_c / n_c) - 1 AS lift FROM p ORDER BY week_index;

CREATE OR REPLACE TABLE out_x2 AS
SELECT SUM(x_t) / SUM(n_t) / (SUM(x_c) / SUM(n_c)) - 1 AS lift_all,
       SUM(x_t) FILTER (WHERE week_index <= 3) / SUM(n_t) FILTER (WHERE week_index <= 3)
         / (SUM(x_c) FILTER (WHERE week_index <= 3) / SUM(n_c) FILTER (WHERE week_index <= 3)) - 1 AS lift_w1_3,
       SUM(x_t) FILTER (WHERE week_index > 3) / SUM(n_t) FILTER (WHERE week_index > 3)
         / (SUM(x_c) FILTER (WHERE week_index > 3) / SUM(n_c) FILTER (WHERE week_index > 3)) - 1 AS lift_w4_plus,
       MIN(week_index) FILTER (WHERE lift < 0.10) AS first_week_below_10pct
FROM out_x2_weekly;
