# Assumptions (simulation, seed 42)

Everything in this file is an assumption of the **simulation**. None of it is Alan data.

## Calendar and volume
- 104 weeks, Monday 2 Dec 2024 to week of 23 Nov 2026.
- Demand = linear trend (+8% a year) x (INSEE raw / seasonally adjusted creations factor)^1.6 x (1 - 6% per weekday public holiday). The exponent 1.6 makes freelancer health-cover sign-ups more seasonal than creations; the SQL estimates it back at 1.64 (R² 0.99). November 2026 is not yet published: the November 2025 factor is reused.
- Geography: 13 metropolitan regions weighted by economically active auto-entrepreneurs (URSSAF, Q4 2025).

## Sub-segments (from URSSAF sector codes)
- Consulting & IT: JZ, M1-M5, KZ, LZ (21% of active AE)
- Construction & crafts: F1-F3, CZ1, CZ2, S1, G1 (21%)
- Health & wellbeing: QZ, S2, R2 (15%)
- Commerce & services: all other sectors (43%)
- New founders (< 6 months): cross-cutting, 55% of the registrations of the last two quarters / active AE (13%); the four sector groups are scaled down accordingly.

## Channels
| Channel | Weekly spend today | Response curve (incremental / week) | Incremental share of deduplicated sign-ups | Platform over-claim |
|---|---|---|---|---|
| Brand search | 10,000 | Hill, V 54, K 2,500, a 1.5 | 12% (planted) | 1.25 x m |
| Non-brand search | 14,000 | Hill, V 312, K 9,000 | 65% | 1.30 x m |
| LinkedIn Ads | 12,000 | Hill, V 568, K 50,000 | 55% | 1.90 x m |
| Partnerships | 6,000 | Hill, V 412, K 20,000 | 80% | 1.35 x m |
| Referral (reward budget) | 4,000 | Hill, V 180, K 8,000 | 75% | none (own system) |
| AI search | none | linear growth 10 to 45 a week | 90% | none |

m is set so that the platforms' sum is 1.40x the deduplicated sign-ups. Organic: 400 a week x demand.

**Analysis side** (what the analyst uses, not the planted truth): brand and LinkedIn incremental shares are measured by X4 and X3; the others are assumed at non-brand 60%, partnerships 80%, referral 70%, AI search 90% until tested.

## Allocation bounds (weekly, EUR)
Brand 2,000-12,000 (defence minimum); non-brand 5,000-24,000; LinkedIn 4,000-30,000; partnerships 2,000-12,000 (deal capacity); referral 1,000-5,000 (member base).

## Funnel
Conversion (sign-ups / clicks) by sub-segment 7.0%, 3.0%, 3.4%, 2.6%, 4.0%, multiplied by channel (brand 2.0, non-brand 1.0, partnerships 0.94, LinkedIn 0.83, referral 4.0, AI search 1.6). Quote-to-sign-up 36-44%. 3-month activity by channel 74% to 85%, adjusted by sub-segment; observed only for weeks at least 91 days old.

## Planted events (hidden file, removed before publication)
E1 over-count 1.40x · E2 brand 12% incremental · E3 X1 split 51.9 / 48.1 · E4 LinkedIn conversion x0.83 within every sub-segment, mix 63% consulting & IT · E5 X2 +40% for 3 weeks then +2% · E6 CTR x0.5 above frequency 4, one winning angle per sub-segment · E7 12 self-referral codes from Feb 2026 · E8 false alert in August 2026.
