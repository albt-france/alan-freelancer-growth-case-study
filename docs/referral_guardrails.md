# Referral guardrails (E7)

Simulated data: 3,973 referrer codes (`REF0001`...), 9,298 referees. Codes only; no person is identified.

## What the data shows
- 99% of codes have 8 referees or fewer.
- 12 codes have between 11 and 54 referees each (361 in total, 3.9% of referral sign-ups), and their referees sign up within a day of the invitation (median under 1 day vs about 9 days for the other codes); **none** of their matured referees is active after 3 months.
- 3-month activity of referral sign-ups: 79.5% with them, 82.1% without them.

## Rule (in `sql/07_referrals.sql`, checked by test E7)
Flag a code when it has **10 or more referees** and **under 10% of its matured referees active** after 3 months.

## Guardrails
1. Pay the reward **on activation** (still a member after 3 months), not on sign-up.
2. Cap rewarded referrals at 10 per code per year; above that, manual review.
3. Block same device / same payment details between referrer and referee (to build with the fraud team).
4. Weekly report: flagged codes, flagged share, rewards saved.
5. Keep the EUR 50 reward (X2: EUR 100 only adds a 3-week novelty spike).
