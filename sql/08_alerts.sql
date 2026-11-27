-- 08_alerts.sql : monthly sign-up alerts, naive vs deseasonalised with the INSEE creation seasonality (F1 / E8).
-- Weeks are assigned to the month of their Thursday; months are compared on average sign-ups per week.

CREATE OR REPLACE TABLE out_monthly AS
SELECT DATE_TRUNC('month', week + INTERVAL 3 DAY) AS month, AVG(total_real) AS per_week, AVG(insee_seasonal_factor) AS factor,
       COUNT(*) AS weeks
FROM out_weekly_total GROUP BY ALL ORDER BY month;

-- elasticity of sign-ups to the creation seasonality, from month-over-month log changes (the trend cancels out)
CREATE OR REPLACE TABLE out_season_elasticity AS
WITH d AS (SELECT LN(per_week) - LN(LAG(per_week) OVER (ORDER BY month)) dy,
                  LN(factor) - LN(LAG(factor) OVER (ORDER BY month)) dx FROM out_monthly)
SELECT regr_slope(dy, dx) AS beta, regr_r2(dy, dx) AS r2, COUNT(dy) AS n FROM d;

CREATE OR REPLACE TABLE out_alerts AS
WITH s AS (
  SELECT m.*, per_week / POWER(factor, (SELECT beta FROM out_season_elasticity)) AS deseason FROM out_monthly m)
SELECT month, per_week, deseason,
       per_week / LAG(per_week) OVER (ORDER BY month) - 1 AS mom_raw,
       deseason / LAG(deseason) OVER (ORDER BY month) - 1 AS mom_deseason,
       COALESCE(per_week / LAG(per_week) OVER (ORDER BY month) - 1 < -0.15, FALSE) AS naive_alert,
       COALESCE(deseason / LAG(deseason) OVER (ORDER BY month) - 1 < -0.10, FALSE) AS deseason_alert
FROM s ORDER BY month;

-- weekly deseasonalised series for the chart
CREATE OR REPLACE TABLE out_weekly_deseason AS
SELECT week, total_real, total_real / POWER(insee_seasonal_factor, (SELECT beta FROM out_season_elasticity)) AS deseason
FROM out_weekly_total ORDER BY week;
