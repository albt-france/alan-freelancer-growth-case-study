-- 03_attribution.sql : what the platforms report vs deduplicated sign-ups (E1, SIMULATED).

CREATE OR REPLACE TABLE out_attribution AS
SELECT channel, SUM(signups_reported) reported, SUM(signups_real) real_dedup,
       SUM(signups_reported) / SUM(signups_real) AS over_count, SUM(spend_eur) spend
FROM acq GROUP BY channel
UNION ALL
SELECT 'All channels', SUM(signups_reported), SUM(signups_real), SUM(signups_reported) / SUM(signups_real), SUM(spend_eur) FROM acq
ORDER BY real_dedup DESC;

-- E1 rule: flag double counting when the platforms' sum exceeds deduplicated sign-ups by more than 20%
CREATE OR REPLACE TABLE out_attribution_flag AS
SELECT over_count, over_count > 1.2 AS double_counting_flag FROM out_attribution WHERE channel = 'All channels';

-- the same ratio by month, to show it is stable (not a one-off tracking incident)
CREATE OR REPLACE TABLE out_attribution_monthly AS
SELECT DATE_TRUNC('month', week + INTERVAL 3 DAY) AS month, SUM(signups_reported) / SUM(signups_real) AS over_count
FROM acq GROUP BY ALL ORDER BY month;
