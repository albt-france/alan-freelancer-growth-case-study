-- 99_tests.sql : automated checks. src/run_sql.py fails if any test returns passed = false.
-- K = keys, Q = data quality and consistency, E1..E8 = the 8 simulated events (each FOUND by a rule),
-- F1 = the false signal is NOT escalated, P = privacy.
CREATE OR REPLACE TABLE tests AS
SELECT 'K01 acq_weekly key (week, region, sub-segment, channel) unique' AS test,
       COUNT(*) = COUNT(DISTINCT (week, region_code, subsegment, channel)) AS passed, COUNT(*) || ' rows' AS detail FROM acq
UNION ALL SELECT 'K02 acq_weekly is complete: 104 weeks x 13 regions x 5 sub-segments x 6 channels',
       COUNT(*) = 104 * 13 * 5 * 6, COUNT(*) || ' rows' FROM acq
UNION ALL SELECT 'K03 organic key unique', COUNT(*) = COUNT(DISTINCT (week, region_code, subsegment)), COUNT(*) || ' rows' FROM organic
UNION ALL SELECT 'K04 creative ids and referrer codes unique',
       (SELECT COUNT(*) = COUNT(DISTINCT creative_id) FROM creatives) AND (SELECT COUNT(*) = COUNT(DISTINCT referrer_code) FROM referrals),
       (SELECT COUNT(*) FROM creatives) || ' creatives, ' || (SELECT COUNT(*) FROM referrals) || ' referrers'
UNION ALL SELECT 'Q01 real sign-ups <= reported on every row', COUNT(*) FILTER (WHERE signups_real > signups_reported) = 0,
       COUNT(*) FILTER (WHERE signups_real > signups_reported) || ' rows break it' FROM acq
UNION ALL SELECT 'Q02 funnel order: impressions >= clicks >= quotes >= real >= active',
       COUNT(*) FILTER (WHERE (impressions IS NOT NULL AND impressions < clicks) OR clicks < quotes OR quotes < signups_real OR active_3m > signups_real) = 0,
       COUNT(*) FILTER (WHERE (impressions IS NOT NULL AND impressions < clicks) OR clicks < quotes OR quotes < signups_real OR active_3m > signups_real) || ' rows break it' FROM acq
UNION ALL SELECT 'Q03 referral totals match between acq_weekly and referrals',
       (SELECT SUM(signups_real) FROM acq WHERE channel = 'Referral') = (SELECT SUM(n_referees) FROM referrals)
       AND (SELECT SUM(active_3m) FROM acq WHERE channel = 'Referral') = (SELECT SUM(n_active_3m) FROM referrals),
       (SELECT SUM(signups_real) FROM acq WHERE channel = 'Referral') || ' vs ' || (SELECT SUM(n_referees) FROM referrals)
UNION ALL SELECT 'Q04 URSSAF Q4 2025 totals as published (1,660,015 economically active)',
       ae_eco_active_q4_2025 = 1660015 AND ae_registered_q4_2025 = 3031447 AND ae_registrations_q4_2025 = 197092,
       ae_eco_active_q4_2025 || ' / ' || ae_registered_q4_2025 || ' / ' || ae_registrations_q4_2025 FROM out_market_kpis
UNION ALL SELECT 'Q05 weekly totals equal the sum of channel and organic rows',
       (SELECT SUM(total_real) FROM out_weekly_total) = (SELECT SUM(signups_real) FROM acq) + (SELECT SUM(signups_real) FROM organic), 'ok'
UNION ALL SELECT 'P01 no column outside the aggregated whitelist (no person, no health data)',
       COUNT(*) FILTER (WHERE column_name NOT IN ('week', 'region_code', 'region', 'subsegment', 'channel', 'spend_eur', 'impressions', 'clicks',
                                                  'quotes', 'signups_reported', 'signups_real', 'active_3m')) = 0,
       COUNT(*) || ' columns' FROM information_schema.columns WHERE table_name = 'acq'
-- the 8 events
UNION ALL SELECT 'E1 attribution double counting flagged (platform sum / deduplicated in 1.35-1.45)',
       double_counting_flag AND over_count BETWEEN 1.35 AND 1.45, ROUND(over_count, 3) || 'x' FROM out_attribution_flag
UNION ALL SELECT 'E2 brand search mostly not incremental (X4: incremental share < 25%)',
       brand_incremental_share BETWEEN 0 AND 0.25 AND organic_gain > 0, ROUND(100 * brand_incremental_share, 1) || '% incremental' FROM out_x4
UNION ALL SELECT 'E3 X1 sample-ratio mismatch detected (chi2 > 10.83, test declared invalid)',
       srm_flag AND decision LIKE 'invalid%', 'share test ' || ROUND(100 * share_test, 1) || '%, chi2 ' || ROUND(srm_chi2, 0) FROM out_x1
UNION ALL SELECT 'E4 Simpson: LinkedIn Ads best conversion in total, worst in every sub-segment',
       linkedin_best_total AND linkedin_worst_in_n_segments = n_segments, linkedin_worst_in_n_segments || ' of ' || n_segments || ' sub-segments' FROM out_simpson_flags
UNION ALL SELECT 'E5 X2 novelty: lift weeks 1-3 > 25%, weeks 4+ < 10%, drops below 10% in week 4',
       lift_w1_3 > 0.25 AND lift_w4_plus < 0.10 AND first_week_below_10pct = 4,
       ROUND(100 * lift_w1_3, 0) || '% then ' || ROUND(100 * lift_w4_plus, 0) || '%' FROM out_x2
UNION ALL SELECT 'E6 creative fatigue: CTR at frequency 5-6 about half of 1-4; winning angle differs by sub-segment',
       (SELECT ctr_ratio_5_6_vs_1_4 BETWEEN 0.4 AND 0.65 AND first_freq_below_60pct = 5 FROM out_creative_fatigue_rule)
       AND (SELECT COUNT(DISTINCT angle) FROM out_creative_angle_seg WHERE winner) >= 3,
       (SELECT ROUND(ctr_ratio_5_6_vs_1_4, 2) FROM out_creative_fatigue_rule) || ' ratio, ' ||
       (SELECT COUNT(DISTINCT angle) FROM out_creative_angle_seg WHERE winner) || ' different winners'
UNION ALL SELECT 'E7 self-referral: flagged codes are above the 99th percentile and never active',
       (SELECT flagged_codes BETWEEN 5 AND 30 AND min_flagged_referees > p99_referees FROM out_referral_summary)
       AND (SELECT MAX(n_active_3m) = 0 FROM out_referral_flags),
       (SELECT flagged_codes || ' codes, ' || flagged_referees || ' referees' FROM out_referral_summary)
UNION ALL SELECT 'E8 August 2026 drop flagged by the naive rule (about -22%)',
       naive_alert AND mom_raw BETWEEN -0.26 AND -0.18, ROUND(100 * mom_raw, 1) || '%' FROM out_alerts WHERE month = DATE '2026-08-01'
UNION ALL SELECT 'F1 August 2026 NOT escalated once deseasonalised (no deseasonalised alert at all)',
       (SELECT NOT deseason_alert FROM out_alerts WHERE month = DATE '2026-08-01') AND (SELECT COUNT(*) FILTER (WHERE deseason_alert) = 0 FROM out_alerts),
       (SELECT ROUND(100 * mom_deseason, 1) || '% deseasonalised' FROM out_alerts WHERE month = DATE '2026-08-01')
UNION ALL SELECT 'X3 LinkedIn geo test: incremental sign-ups well below what the platform reports',
       incremental > 0 AND incremental < 0.6 * reported_extra, ROUND(incremental, 0) || ' incremental vs ' || ROUND(reported_extra, 0) || ' reported' FROM out_x3
;
