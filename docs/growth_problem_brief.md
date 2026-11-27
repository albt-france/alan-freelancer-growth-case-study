# Growth problem brief: the freelancer segment (M1)

> Market numbers are **public** (URSSAF, INSEE). Everything about the insurer's channels, spend, sign-ups and tests is **simulated** and is not Alan data.

## The fuzzy problem
"We want to grow faster on freelancers." Nobody knows yet how big the reachable market is, which channels bring members who stay, or whether the channels that look best really cause the sign-ups.

## Objective (90 days)
Grow **incremental** freelancer sign-ups that are still active after 3 months, at the same budget.

**North-star metric:** incremental members active at 3 months per euro spent.
Guardrail metrics: 3-month activity rate, cost per incremental sign-up by channel, share of referral sign-ups from flagged codes.

## What the data says (diagnosis)
| Question | Answer | Source |
|---|---|---|
| How big is the market? | 3.63M self-employed (Q2 2026), of which 1.66M auto-entrepreneurs economically active (55% of the 3.03M registered) | URSSAF, public |
| Where? | Five departements (Paris, Rhône, Gironde, Bouches-du-Rhône, Hauts-de-Seine) hold 21% of the market value (active x income) | URSSAF, public |
| When? | Creations peak in January and September-October; August is 20% below trend every year | INSEE, public |
| What do platforms over-claim? | Platforms report 1.40x the deduplicated sign-ups | simulated |
| What is incremental? | 39% of deduplicated sign-ups; brand search only 1% (at most 20%) | simulated tests X3, X4 |

## Constraints
- Same total budget (EUR 46,000 a week in the simulation).
- Partner deals need lead time: partnership spend can at most double in 90 days.
- Brand search keeps a defence budget (competitors bid on the brand name).
- Referral volume is limited by the member base.

## Hypotheses to test
1. Brand search sign-ups would mostly arrive anyway (tested: X4, confirmed).
2. LinkedIn Ads drive fewer incremental sign-ups than the platform reports (X3: direction confirmed, interval wide).
3. A page per sub-segment lifts quote requests (X1: unreadable, sample-ratio mismatch, rerun).
4. A bigger referral reward lifts referrals durably (X2: no, novelty effect only).

## Decision
Move 19% of the weekly budget from brand search to partnerships and LinkedIn Ads (+11% incremental sign-ups in the response-curve model), rerun the tests that could not be read, and review every week. See `plan_90_days.md`.
