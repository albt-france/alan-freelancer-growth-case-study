# Measurement plan: attribution vs incrementality

## Three numbers, three meanings
| Number | Question it answers | In the simulation (104 weeks) |
|---|---|---|
| Platform-reported sign-ups | What each platform claims | 173,933 |
| Deduplicated sign-ups | How many people really signed up, last touch in the CRM | 123,855 (platforms over-count 1.40x) |
| Incremental sign-ups | How many would not have signed up without the spend | about 48,000 (39%) |

Budget decisions use the third number only. Cost per sign-up: EUR 27 as reported, EUR 98 per incremental sign-up.

## How incrementality is measured
- **Geo tests** (X3, X4): treat whole departements or regions, compare with matched controls, read by difference-in-differences: effect = test after - test before x (control after / control before). Intervals by bootstrap over matched pairs (X3) or Poisson resampling of the totals (X4).
- **Matching:** departements are paired on public URSSAF data (log active auto-entrepreneurs, average income) before the test; the largest markets are kept out so one city cannot drive the result.
- **Power:** decide duration before the test. Rule of thumb from X3: a +6% effect on about 525 sign-ups a week in the test group needs more than 8 weeks to clear zero; plan 12.
- **Channels without a test** use an assumed incremental share (non-brand 60%, partnerships 80%, referral 70%, AI search 90%), shown as "assumed" everywhere, replaced as soon as a test reads.

## Reading rules (fixed before every test)
1. Check the split first (chi-square; alert below p = 0.001). A mismatch invalidates the test.
2. Plot the effect week by week; a lift that fades is novelty.
3. Read conversion within sub-segments, not only in total (Simpson's paradox).
4. Deseasonalise before alerting: weekly sign-ups move 1.6x the INSEE creation seasonality; the naive month-over-month rule raised 7 alerts in two years, all seasonal, and none after deseasonalising.

## Cadence
Weekly: north-star, guardrails, live tests. Monthly: refit response curves, reallocate. Quarterly: one holdout per major channel.
