-- 04_incrementality.sql : geo tests. X4 brand search holdout (E2), X3 LinkedIn Ads geo test, then the
-- reported -> deduplicated -> incremental waterfall (SIMULATED). Point estimates here; confidence intervals in src/stats.py.

-- ------------------------------------------------------------------ X4: brand search off in 6 regions for 8 weeks
CREATE OR REPLACE TABLE x4_design AS
SELECT DATE '2026-05-04' AS test_start, DATE '2026-06-28' AS test_end, DATE '2026-03-09' AS pre_start,
       ['27', '28', '52', '53', '75', '76'] AS holdout;

CREATE OR REPLACE TABLE out_x4_region_week AS
WITH tot AS (
  SELECT week, region_code, SUM(signups_real) AS paid, SUM(signups_real) FILTER (WHERE channel = 'Brand search') AS brand
  FROM acq GROUP BY ALL),
org AS (SELECT week, region_code, SUM(signups_real) organic FROM organic GROUP BY ALL)
SELECT t.week, t.region_code, list_contains(d.holdout, t.region_code) AS holdout,
       CASE WHEN t.week >= d.test_start AND t.week <= d.test_end THEN 'test' ELSE 'pre' END AS period,
       t.paid + o.organic AS total, t.brand, o.organic
FROM tot t JOIN org o USING (week, region_code), x4_design d
WHERE t.week >= d.pre_start AND t.week <= d.test_end
ORDER BY week, region_code;

CREATE OR REPLACE TABLE out_x4 AS
WITH s AS (
  SELECT SUM(total) FILTER (WHERE holdout AND period = 'pre') h_pre, SUM(total) FILTER (WHERE holdout AND period = 'test') h_post,
         SUM(total) FILTER (WHERE NOT holdout AND period = 'pre') c_pre, SUM(total) FILTER (WHERE NOT holdout AND period = 'test') c_post,
         SUM(brand) FILTER (WHERE holdout AND period = 'pre') b_h_pre, SUM(brand) FILTER (WHERE NOT holdout AND period = 'pre') b_c_pre,
         SUM(brand) FILTER (WHERE NOT holdout AND period = 'test') b_c_post, SUM(brand) FILTER (WHERE holdout AND period = 'test') b_h_post,
         SUM(organic) FILTER (WHERE holdout AND period = 'pre') o_h_pre, SUM(organic) FILTER (WHERE holdout AND period = 'test') o_h_post,
         SUM(organic) FILTER (WHERE NOT holdout AND period = 'pre') o_c_pre, SUM(organic) FILTER (WHERE NOT holdout AND period = 'test') o_c_post
  FROM out_x4_region_week)
SELECT *, h_pre * c_post / c_pre AS expected_total, h_pre * c_post / c_pre - h_post AS lost_total,
       b_h_pre * b_c_post / b_c_pre AS expected_brand,
       (h_pre * c_post / c_pre - h_post) / (b_h_pre * b_c_post / b_c_pre) AS brand_incremental_share,
       o_h_post - o_h_pre * o_c_post / o_c_pre AS organic_gain,
       h_post / (h_pre * c_post / c_pre) - 1 AS total_lift
FROM s;

-- ------------------------------------------------------------------ X3: LinkedIn Ads spend x3 in 20 test departements, 8 weeks
CREATE OR REPLACE TABLE out_x3 AS
WITH s AS (
  SELECT SUM(signups_total) FILTER (WHERE grp = 'test' AND period = 'pre') t_pre, SUM(signups_total) FILTER (WHERE grp = 'test' AND period = 'test') t_post,
         SUM(signups_total) FILTER (WHERE grp = 'control' AND period = 'pre') c_pre, SUM(signups_total) FILTER (WHERE grp = 'control' AND period = 'test') c_post,
         SUM(linkedin_reported) FILTER (WHERE grp = 'test' AND period = 'pre') lt_pre, SUM(linkedin_reported) FILTER (WHERE grp = 'test' AND period = 'test') lt_post,
         SUM(linkedin_reported) FILTER (WHERE grp = 'control' AND period = 'pre') lc_pre, SUM(linkedin_reported) FILTER (WHERE grp = 'control' AND period = 'test') lc_post,
         SUM(linkedin_spend_eur) FILTER (WHERE grp = 'test' AND period = 'test') - SUM(linkedin_spend_eur) FILTER (WHERE grp = 'test' AND period = 'pre') AS extra_spend
  FROM geo),
dd AS (SELECT over_count AS li_over_count FROM out_attribution WHERE channel = 'LinkedIn Ads')
SELECT s.*, t_post - t_pre * c_post / c_pre AS incremental, t_post / (t_pre * c_post / c_pre) - 1 AS lift,
       lt_post - lt_pre * lc_post / lc_pre AS reported_extra,
       extra_spend / (t_post - t_pre * c_post / c_pre) AS cost_per_incremental,
       extra_spend / (lt_post - lt_pre * lc_post / lc_pre) AS cost_per_reported,
       (t_post - t_pre * c_post / c_pre) / ((lt_post - lt_pre * lc_post / lc_pre) / dd.li_over_count) AS linkedin_incremental_share
FROM s, dd;

-- weekly view for the chart (test vs control, indexed on the pre-period)
CREATE OR REPLACE TABLE out_x3_weekly AS
WITH w AS (SELECT week, grp, period, SUM(signups_total) s FROM geo GROUP BY ALL)
SELECT week, grp, period, s, 100 * s / AVG(s) FILTER (WHERE period = 'pre') OVER (PARTITION BY grp) AS idx FROM w ORDER BY week, grp;

-- ------------------------------------------------------------------ waterfall: reported -> deduplicated -> incremental
-- incremental share: measured for brand search (X4) and LinkedIn Ads (X3); assumed for the others until tested
CREATE OR REPLACE TABLE inc_share AS
SELECT 'Brand search' AS channel, (SELECT brand_incremental_share FROM out_x4) AS share, 'measured (X4)' AS source
UNION ALL SELECT 'LinkedIn Ads', (SELECT linkedin_incremental_share FROM out_x3), 'measured (X3)'
UNION ALL SELECT 'Non-brand search', 0.60, 'assumed'
UNION ALL SELECT 'Partnerships', 0.80, 'assumed'
UNION ALL SELECT 'Referral', 0.70, 'assumed'
UNION ALL SELECT 'AI search', 0.90, 'assumed';

CREATE OR REPLACE TABLE out_incremental_channel AS
SELECT a.channel, a.reported, a.real_dedup, i.share AS incremental_share, i.source, a.real_dedup * i.share AS incremental, a.spend,
       a.spend / NULLIF(a.real_dedup * i.share, 0) AS cost_per_incremental, a.spend / NULLIF(a.reported, 0) AS cost_per_reported
FROM out_attribution a JOIN inc_share i USING (channel) ORDER BY a.real_dedup DESC;

CREATE OR REPLACE TABLE out_waterfall AS
SELECT 1 AS step, 'Reported by platforms' AS label, SUM(reported) AS signups FROM out_incremental_channel
UNION ALL SELECT 2, 'Deduplicated', SUM(real_dedup) FROM out_incremental_channel
UNION ALL SELECT 3, 'Incremental', SUM(incremental) FROM out_incremental_channel
ORDER BY step;
