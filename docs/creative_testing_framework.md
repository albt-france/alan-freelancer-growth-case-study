# Creative testing framework (M5)

Based on 120 **simulated** LinkedIn Ads creatives (5 angles x 4 formats, each written for one sub-segment). No creative was generated or published for this study: variants are described by their angle.

## Naming
`<channel>-<sub-segment>-<angle>-<format>-<number>`, e.g. `LI-CON-PRICE-VID-007` (LinkedIn, Consulting & IT, price angle, video, 7th variant). The name carries everything needed to read results by angle, sub-segment and format without a lookup table.

## Angles
Price · Prevention · Fast reimbursement · App experience · Made for freelancers.

## Producing variants at scale with AI workflows
1. Brief per sub-segment x angle (25 cells): the promise, one proof, one call to action.
2. Generate 4 to 6 variants per cell (text and visual), human review for claims and tone before anything ships.
3. Launch in batches of one cell at a time so the angle effect is not confused with the week.

## Reading results
- Compare creatives at **equal frequency** (frequency 1-4): later impressions are worn out.
- CTR index = CTR of the cell / average CTR of the sub-segment. Winners in the simulation: Consulting & IT - App experience (1.40), Construction & crafts - Fast reimbursement (1.35), Health & wellbeing - Prevention (1.37), Commerce & services - Price (1.45), New founders - Made for freelancers (1.38).
- Judge on sign-ups per impression when volume allows; CTR is the early signal.

## Rotation and fatigue
- CTR falls **48%** between frequencies 1-4 and 5-6 (simulated). **Rotate at frequency 4**: cap frequency at 4 per person per creative, refresh with a new variant of the **same winning angle**.
- Kill a variant whose CTR index stays below 0.9 after 50,000 impressions.
- Keep 20% of budget on new angles to keep learning.
