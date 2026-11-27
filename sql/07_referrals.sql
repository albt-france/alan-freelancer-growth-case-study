-- 07_referrals.sql : referral distribution and the self-referral guardrail (E7, SIMULATED; referrers are codes only).

-- distribution of referees per referrer
CREATE OR REPLACE TABLE out_referral_dist AS
SELECT n_referees, COUNT(*) AS referrers FROM referrals GROUP BY n_referees ORDER BY n_referees;

-- guardrail: 10+ referees and under 10% of matured referees active after 3 months
CREATE OR REPLACE TABLE out_referral_flags AS
SELECT referrer_code, first_week, n_referees, n_matured, n_active_3m, n_active_3m / NULLIF(n_matured, 0) AS active_rate, median_days
FROM referrals
WHERE n_referees >= 10 AND n_matured >= 5 AND n_active_3m / NULLIF(n_matured, 0) < 0.10
ORDER BY n_referees DESC;

CREATE OR REPLACE TABLE out_referral_summary AS
SELECT COUNT(*) AS referrers, SUM(n_referees) AS referees,
       (SELECT COUNT(*) FROM out_referral_flags) AS flagged_codes,
       (SELECT SUM(n_referees) FROM out_referral_flags) AS flagged_referees,
       (SELECT SUM(n_referees) FROM out_referral_flags) / SUM(n_referees) AS flagged_share,
       quantile_cont(n_referees, 0.99) AS p99_referees,
       (SELECT MIN(n_referees) FROM out_referral_flags) AS min_flagged_referees,
       SUM(n_active_3m) / SUM(n_matured) AS active_rate_all,
       (SELECT SUM(n_active_3m) / SUM(n_matured) FROM referrals WHERE referrer_code NOT IN (SELECT referrer_code FROM out_referral_flags)) AS active_rate_clean
FROM referrals;
