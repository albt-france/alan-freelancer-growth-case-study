-- 02_funnel.sql : funnel by channel and the Simpson check (SIMULATED).
-- 3-month activity is only observed for weeks at least 91 days before the last week (active_3m is NULL after).

CREATE OR REPLACE TABLE out_funnel_channel AS
WITH m AS (SELECT MAX(week) - INTERVAL 91 DAY AS cut FROM acq)
SELECT channel, SUM(spend_eur) spend, SUM(impressions) impressions, SUM(clicks) clicks, SUM(quotes) quotes,
       SUM(signups_reported) signups_reported, SUM(signups_real) signups_real,
       SUM(active_3m) active_3m,
       SUM(signups_real) FILTER (WHERE week < (SELECT cut FROM m)) AS real_matured,
       SUM(active_3m) / SUM(signups_real) FILTER (WHERE week < (SELECT cut FROM m)) AS retention_3m,
       SUM(spend_eur) / NULLIF(SUM(signups_real), 0) AS cost_per_real,
       SUM(spend_eur) / NULLIF(SUM(signups_reported), 0) AS cost_per_reported,
       SUM(signups_real) / SUM(clicks) AS conv_click
FROM acq GROUP BY channel ORDER BY signups_real DESC;

-- Simpson (E4): conversion (real sign-ups / clicks) by channel, in total and by sub-segment, prospecting paid channels
CREATE OR REPLACE TABLE out_simpson AS
WITH base AS (SELECT channel, subsegment, SUM(signups_real) s, SUM(clicks) c FROM acq
              WHERE channel IN ('Non-brand search', 'LinkedIn Ads', 'Partnerships') GROUP BY ALL)
SELECT channel, subsegment, s / c AS conv, c AS clicks, c / SUM(c) OVER (PARTITION BY channel) AS click_mix FROM base
UNION ALL
SELECT channel, 'All sub-segments', SUM(s) / SUM(c), SUM(c), 1.0 FROM base GROUP BY channel
ORDER BY subsegment, channel;

CREATE OR REPLACE TABLE out_simpson_flags AS
WITH r AS (SELECT subsegment, channel, conv, RANK() OVER (PARTITION BY subsegment ORDER BY conv DESC) AS rk_best,
                  RANK() OVER (PARTITION BY subsegment ORDER BY conv ASC) AS rk_worst FROM out_simpson)
SELECT (SELECT rk_best FROM r WHERE subsegment = 'All sub-segments' AND channel = 'LinkedIn Ads') = 1 AS linkedin_best_total,
       (SELECT COUNT(*) FROM r WHERE subsegment <> 'All sub-segments' AND channel = 'LinkedIn Ads' AND rk_worst = 1) AS linkedin_worst_in_n_segments,
       (SELECT COUNT(DISTINCT subsegment) - 1 FROM r) AS n_segments;

-- weekly totals (all channels + organic), used by the alerts and the charts
CREATE OR REPLACE TABLE out_weekly_total AS
WITH a AS (SELECT week, SUM(signups_real) paid_real, SUM(signups_reported) reported, SUM(spend_eur) spend FROM acq GROUP BY week),
o AS (SELECT week, SUM(signups_real) organic FROM organic GROUP BY week)
SELECT a.week, a.paid_real, o.organic, a.paid_real + o.organic AS total_real, a.reported, a.spend,
       c.insee_seasonal_factor, c.holiday_weekdays
FROM a JOIN o USING (week) JOIN cal c USING (week) ORDER BY week;
