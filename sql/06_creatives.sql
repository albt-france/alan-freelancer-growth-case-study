-- 06_creatives.sql : creative fatigue by exposure frequency and winning angle by sub-segment (E6, SIMULATED).

CREATE OR REPLACE TABLE out_creative_fatigue AS
SELECT c.angle, f.frequency, SUM(f.clicks) / SUM(f.impressions) AS ctr, SUM(f.impressions) impressions
FROM creative_freq f JOIN creatives c USING (creative_id) GROUP BY ALL ORDER BY angle, frequency;

CREATE OR REPLACE TABLE out_creative_fatigue_rule AS
WITH f AS (SELECT frequency, SUM(clicks) / SUM(impressions) ctr FROM creative_freq GROUP BY frequency)
SELECT (SELECT SUM(ctr) FILTER (WHERE frequency BETWEEN 5 AND 6) / 2 FROM f) / (SELECT SUM(ctr) FILTER (WHERE frequency BETWEEN 1 AND 4) / 4 FROM f) AS ctr_ratio_5_6_vs_1_4,
       (SELECT MIN(frequency) FROM f WHERE ctr < 0.6 * (SELECT ctr FROM f WHERE frequency = 1)) AS first_freq_below_60pct;

-- angle x sub-segment, frequencies 1-4 only (before fatigue), winner per sub-segment
CREATE OR REPLACE TABLE out_creative_angle_seg AS
WITH t AS (SELECT c.subsegment, c.angle, SUM(f.clicks) / SUM(f.impressions) ctr, COUNT(DISTINCT c.creative_id) n_creatives
           FROM creative_freq f JOIN creatives c USING (creative_id) WHERE f.frequency <= 4 GROUP BY ALL)
SELECT *, ctr / AVG(ctr) OVER (PARTITION BY subsegment) AS ctr_index,
       RANK() OVER (PARTITION BY subsegment ORDER BY ctr DESC) = 1 AS winner
FROM t ORDER BY subsegment, angle;
