# Experiment log (M3, M6)

All four experiments are **simulated**. Statistics: `src/stats.py`; SQL point estimates: `sql/04_incrementality.sql`, `sql/05_experiments.sql`. Intervals are 95%.

## X1 · Landing page by sub-segment
- **Hypothesis:** a page written for each sub-segment (consultants, builders, health professionals...) lifts quote requests.
- **Metric:** quote-request rate per visitor. **Unit:** visitor, planned 50 / 50. **Duration:** 4 weeks (7 Sep - 4 Oct 2026).
- **Sample size needed:** 61,116 visitors per arm to detect +8% on a 4% base at 80% power.
- **Result:** 4.23% vs 3.96%, lift +6.9% [+0.6%, +13.2%], p = 0.03. **But** the split is 51.7 / 48.3 (chi-square 120, p < 0.000001).
- **Decision:** invalid, do not ship. Cause found: the bot filter ran on the control arm only. **Rerun** with one filter applied before assignment.
- **Lesson:** check the split before reading any lift; a "winning" test with a broken split is not a win.

## X2 · Referral reward EUR 100 vs EUR 50
- **Hypothesis:** a larger reward makes more members invite a freelancer.
- **Metric:** share of members shown the offer who send an invitation. **Unit:** member-week. **Duration:** 8 weeks.
- **Result:** weeks 1-3 +40% [+32%, +49%]; weeks 4-8 -0.5% [-5.3%, +4.3%].
- **Decision:** keep EUR 50. The lift is a novelty effect: it disappears after week 3.
- **Lesson:** plot the lift week by week; a test stopped at week 3 would have shipped a cost with no lasting effect.

## X3 · LinkedIn Ads geo test (spend x3)
- **Hypothesis:** extra LinkedIn spend brings incremental sign-ups.
- **Design:** 20 test departements, 20 controls matched on URSSAF data (log active auto-entrepreneurs, average income); 8 weeks pre-period, 8 weeks test; Paris and the six largest markets kept out.
- **Read:** difference-in-differences on total sign-ups, bootstrap over the 20 pairs.
- **Result:** +5.8% [-1.2%, +12.8%], i.e. 243 incremental sign-ups [-49, 535] for EUR 55,537 of extra spend (EUR 229 per incremental sign-up). LinkedIn reported 1,268 extra sign-ups (EUR 44 each).
- **Decision:** inconclusive at 95%, but the platform claim is far outside the interval. Hold LinkedIn near today's level; retest at x2 spend for 12 weeks to narrow the interval.
- **Lesson:** a platform's conversion count is not an incrementality measure.

## X4 · Brand search holdout
- **Hypothesis:** brand search sign-ups would mostly arrive anyway (organic, direct).
- **Design:** brand search off in 6 of 13 regions for 8 weeks (4 May - 28 Jun 2026); the other 7 regions as control; 8-week pre-period.
- **Result:** total sign-ups -0.4% [-5.2%, +4.7%]. Of 1,226 expected brand sign-ups, 16 were lost: **1% incremental, at most 20%**. Organic sign-ups rose by 1,146 in the holdout regions.
- **Decision:** cut brand search to a defence budget (about EUR 2,900 a week) and move the rest.
- **Lesson:** the cheapest-looking channel can be the least incremental.

## Learning loop
Every Monday: one page with the north-star metric, the guardrails, each live test (split check, interval, decision rule fixed in advance). Every month: re-fit the response curves with the new test results and re-run `src/allocate_budget.py`.
