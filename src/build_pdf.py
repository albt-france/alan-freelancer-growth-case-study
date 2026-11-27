"""Build site/report/alan_freelancer_growth_case_study.pdf: 7 pages (0 to 6), readable at a glance.
Style of the bank-forecasting reference (1600 x 900 px, #F4F4F2 background, flat white cards with a 1px #E1E0D9 border,
8px radius, source tag in the corner of each card, 3-zone footer). Rendered by Edge headless through pdf_kit.render(),
which fails the build if a card overflows or the page count is not 7.
Each chart card title is the finding (searchable text); the detail lives in the README and docs/.
Run from the repository root:  python src/build_pdf.py
"""
from __future__ import annotations

import sys

import pandas as pd

import charts
import pdf_kit
from common import AI, COMPANY, FOOT, OUT, TITLE, key_numbers

sys.stdout.reconfigure(encoding="utf-8")
K = key_numbers()
LABEL = f"{COMPANY} · Growth Marketer case study"

pdf_kit.CSS = """
@page { size: 1600px 900px; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Segoe UI', Arial, sans-serif; color: #0B0B0B; background: #F4F4F2; }
.page { width: 1600px; height: 900px; padding: 24px 44px 14px; display: flex; flex-direction: column; page-break-after: always;
        overflow: hidden; background: #F4F4F2; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 25px; margin: 0 0 4px; font-weight: 700; line-height: 1.15; }
.sub { margin: 0; color: #52514E; font-size: 14.5px; }
main { flex: 1; display: flex; flex-direction: column; gap: 10px; margin-top: 10px; min-height: 0; }
footer { display: flex; justify-content: space-between; gap: 20px; font-size: 11px; color: #898781; margin-top: 6px; }
footer span:nth-child(2) { text-align: center; flex: 1; }
.grid { display: grid; gap: 10px; flex: 1; min-height: 0; }
.col { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.card { position: relative; background: #FFFFFF; border: 1px solid #E1E0D9; border-radius: 8px; padding: 7px 9px 5px;
        min-height: 0; overflow: hidden; display: flex; flex-direction: column; }
.card h2 { font-size: 15px; margin: 0 0 3px; padding-right: 95px; line-height: 1.25; }
.card img { width: 100%; flex: 1; min-height: 0; object-fit: contain; }
.ctag { position: absolute; top: 7px; right: 9px; font-size: 9.5px; font-weight: 700; letter-spacing: .08em; padding: 2px 6px; border-radius: 4px; }
.pub { background: #E3EEFB; color: #1C5CAB; } .sim { background: #FBE9E0; color: #9A3B12; } .mix { background: #ECE6F6; color: #5B3A9A; }
.kpi { position: relative; background: #FFFFFF; border: 1px solid #E1E0D9; border-radius: 8px; padding: 6px 14px; overflow: hidden; }
.kpi b { display: block; font-size: 33px; font-weight: 700; line-height: 1.1; margin-top: 0; }
.kpi span.t { font-size: 13.5px; color: #52514E; }
.so { background: #FFFFFF; }
.so h2 { color: #2A78D6; }
.so li { font-size: 14px; line-height: 1.35; margin: 2px 0; color: #2B2A27; }
.so ul { margin: 2px 0 0; padding-left: 18px; }
.txt p, .txt li { font-size: 13px; line-height: 1.38; margin: 2px 0; color: #2B2A27; }
.txt ul { margin: 2px 0; padding-left: 17px; }
"""
pdf_kit.TAG = {"pub": '<span class="ctag pub">PUBLIC DATA</span>', "sim": '<span class="ctag sim">SIMULATED</span>',
               "mix": '<span class="ctag mix">PUBLIC + SIMULATED</span>', "": ""}


def o(name):
    return pd.read_csv(OUT / f"{name}.csv")


def card(title: str, img: str, tag: str, style: str = "") -> str:
    return f'<div class="card" style="{style}">{pdf_kit.TAG[tag]}<h2>{title}</h2><img src="{img}"></div>'


def sowhat(*bullets: str, style: str = "") -> str:
    return f'<div class="card so" style="{style}"><h2>So what</h2><ul>{"".join(f"<li>{b}</li>" for b in bullets)}</ul></div>'


def kpi(value: str, text: str, tag: str) -> str:
    return f'<div class="kpi">{pdf_kit.TAG[tag]}<b>{value}</b><span class="t">{text}</span></div>'


def page(n: int, title: str, sub: str, body: str, sources: str) -> str:
    return (f'<section class="page"><header><h1>{title}</h1><p class="sub">{sub}</p></header><main>{body}</main>'
            f'<footer><span>{FOOT}</span><span>{sources}</span><span>{LABEL} · page {n} / 6</span></footer></section>')


def main() -> None:
    C = charts.build_all()
    w = o("waterfall").signups
    inc_share = f"{100 * w[2] / w[1]:.0f}%"
    dep = o("market_dept")
    top5 = f"{100 * dep[dep.target].market_value.sum() / dep.market_value.sum():.0f}%"
    sec = o("market_sector").groupby("subsegment").share.sum()
    prof = o("insee_season_profile").set_index("mo").avg_factor
    q = o("market_subsegment_q").groupby("subsegment").index_first_q.last() / 100
    fc = o("funnel_channel").set_index("channel")
    ic = o("incremental_channel").set_index("channel")
    sm = o("simpson")
    li_tot = 100 * sm[(sm.subsegment == "All sub-segments") & (sm.channel == "LinkedIn Ads")].conv.iloc[0]
    al = o("allocation").set_index("channel")
    S_PUB = "Sources: URSSAF open data (ODbL), INSEE BDM (Licence Ouverte), Etalab boundaries"
    S_SIM = "Simulated data (seed 42), calibrated on INSEE seasonality and URSSAF geography"

    pages = []
    # ------------------------------------------------------------------ page 0
    body = ('<div class="grid" style="grid-template-columns: repeat(4, 1fr); flex: 0 0 98px;">'
            + kpi(K["freelancers"], "active freelancers in France (URSSAF, Q2 2026)", "pub")
            + kpi(K["creations_month"], "new micro-businesses per month (INSEE, last 12 months)", "pub")
            + kpi(K["cpa_incremental"], f"per incremental sign-up, vs {K['cpa_reported']} as platforms report", "sim")
            + kpi(K["budget_moved"], f"of the weekly budget to move, for {K['inc_gain']} incremental sign-ups", "sim") + "</div>"
            + card(f"Platforms over-count {K['overcount']}; only {inc_share} of real sign-ups are caused by the spend", C["waterfall"], "sim",
                   "flex: 0 0 352px;")
            + '<div class="grid" style="grid-template-columns: 1fr 1fr 1fr;">'
            + card(f"{K['budget_moved']} of budget moved: {K['inc_gain']} incremental sign-ups", C["curves"], "sim")
            + card("Only the brand search test gives a clear answer", C["forest_small"], "sim")
            + card(f"August {K['aug_raw']}: the yearly creation trough", C["f1"], "mix") + "</div>")
    pages.append(page(0, f"{K['freelancers']} freelancers in France; the next euro should move from brand search to partnerships and LinkedIn",
                      f"Market sized on URSSAF and INSEE public data; acquisition, tests and budgets are simulated for a health insurer, not {COMPANY}'s figures.",
                      body, "Public: URSSAF, INSEE · everything else simulated"))
    # ------------------------------------------------------------------ page 1
    body = ('<div class="grid" style="grid-template-columns: 1fr 1fr;">'
            + card(f"Five departements hold {top5} of the market value (active AE x income)", C["map"], "pub")
            + '<div class="col">' + card(f"Only {K['active_share']} of registered auto-entrepreneurs are economically active", C["dumbbell"], "pub", "flex: 0 0 300px;")
            + '<div class="grid" style="grid-template-columns: 1fr 1fr; flex: 0 0 300px;">'
            + card("Targets: dense and better paid", C["scatter"], "pub")
            + card(f"Commerce {100 * sec['Commerce & services']:.0f}%, consulting & IT {100 * sec['Consulting & IT']:.0f}%", C["treemap"], "pub") + "</div>"
            + sowhat(f"Size the market on the {K['eco_active']} active, not the 3.03M registered.",
                     "Start local tests in the five lead departements.",
                     "Consulting & IT: one active in five, easy to target by job title.") + "</div></div>")
    pages.append(page(1, f"{K['eco_active']} auto-entrepreneurs actually trade ({K['active_share']} of those registered); five departements lead",
                      "URSSAF auto-entrepreneurs by departement and sector (Q4 2025) and self-employed income (2025).", body, S_PUB))
    # ------------------------------------------------------------------ page 2
    body = ('<div class="grid" style="grid-template-columns: 1.55fr 1fr;">'
            + card(f"Every August sits {100 * (1 - prof[8]):.0f}% below trend; October is {100 * (prof[10] - 1):+.0f}%", C["calendar"], "pub")
            + '<div class="col">'
            + card(f"Active AE grew {q.min():.1f}x to {q.max():.1f}x since 2019 in every group", C["multiples"], "pub", "flex: 0 0 300px;")
            + card(f"Deseasonalised, August 2026 is {K['aug_deseason']}, not {K['aug_raw']}: no alert", C["deseason"], "mix", "flex: 0 0 300px;")
            + sowhat("Push budget in January and September-October.", "Read sign-ups deseasonalised, never month over month.",
                     "Do not cut spend on an August dip.") + "</div></div>")
    pages.append(page(2, "Demand is seasonal: creations peak in January and autumn and drop about 20% every August",
                      "INSEE monthly micro-entrepreneur creations 2015-2026 (method break in 2022) and simulated weekly sign-ups.", body,
                      "INSEE series 010755410 / 010755411 (Licence Ouverte) · URSSAF (ODbL) · simulated sign-ups"))
    # ------------------------------------------------------------------ page 3
    body = ('<div class="grid" style="grid-template-columns: 1.55fr 1fr;">'
            + card(f"Partnerships keep {100 * fc.loc['Partnerships', 'retention_3m']:.0f}% of members after 3 months, non-brand search "
                   f"{100 * fc.loc['Non-brand search', 'retention_3m']:.0f}%", C["funnels"], "sim")
            + '<div class="col">'
            + card(f"LinkedIn converts best in total ({li_tot:.1f}%), worst at equal mix", C["slope"], "sim", "flex: 0 0 300px;")
            + card(f"Per incremental sign-up: brand search EUR {ic.loc['Brand search', 'cost_per_incremental']:,.0f}, partnerships "
                   f"EUR {ic.loc['Partnerships', 'cost_per_incremental']:.0f}", C["bubbles"], "sim", "flex: 0 0 300px;")
            + sowhat("Judge channels on incremental, retained members.", "Compare conversion within each sub-segment.",
                     "Keep brand search at a defence budget.") + "</div></div>")
    pages.append(page(3, "Channels differ in quality more than in volume: brand search looks cheap but is barely incremental",
                      "Simulated funnel over 104 weeks, 6 channels, 5 sub-segments; 3-month activity observed for mature weeks only.", body, S_SIM))
    # ------------------------------------------------------------------ page 4
    body = ('<div class="grid" style="grid-template-columns: 1.55fr 1fr;">'
            + card("One test invalid, one novelty, one inconclusive, one clear: cut brand search", C["forest"], "sim")
            + '<div class="col">'
            + card(f"LinkedIn claims {K['x3_reported']} extra sign-ups; the geo test finds {K['x3_incremental']} (at most {K['x3_incremental_hi']})",
                   C["geo"], "sim", "flex: 0 0 300px;")
            + card(f"The bigger reward lifts invitations {K['x2_early']} for 3 weeks, then {K['x2_late']}", C["novelty"], "sim", "flex: 0 0 300px;")
            + sowhat(f"Brand search: {K['brand_share']} incremental (at most {K['brand_share_hi']}): cut.",
                     f"X1 split {K['srm_split']}: invalid, rerun.", "X2: keep the EUR 50 reward.") + "</div></div>")
    pages.append(page(4, f"Read tests before shipping: the {K['x1_lift']} landing page is invalid and the reward lift is novelty",
                      "Four simulated experiments, 95% confidence intervals; geo tests read by difference-in-differences.", body, S_SIM))
    # ------------------------------------------------------------------ page 5
    body = ('<div class="grid" style="grid-template-columns: 1.55fr 1fr;">'
            + card(f"CTR falls {K['fatigue']} after the 4th exposure: rotate at frequency 4", C["fatigue"], "sim")
            + '<div class="col">'
            + card("Five sub-segments, five different winning angles (CTR index)", C["heatmap"], "sim", "flex: 0 0 300px;")
            + card(f"{K['selfref_codes']} codes bring {K['selfref_referees']} referees, none active after 3 months", C["hist"], "sim", "flex: 0 0 300px;")
            + sowhat("Cap frequency at 4; refresh by angle.", "Generate AI variants per sub-segment angle; cut below index 0.9.",
                     "Pay referral rewards on activation; cap per code.") + "</div></div>")
    pages.append(page(5, f"Creatives wear out after four exposures, angles differ by sub-segment, and {K['selfref_codes']} referral codes game rewards",
                      "120 simulated LinkedIn Ads creatives (5 angles x 4 formats); referrers as codes only, no personal data.", body, S_SIM))
    # ------------------------------------------------------------------ page 6
    method = ("<ul><li>SQL (DuckDB): 9 scripts, 20 automated tests (E1-E8 events, F1 false signal).</li>"
              "<li>Python: seeded simulation, z-tests, chi-square SRM check, difference-in-differences with bootstrap intervals, "
              "budget optimiser on response curves.</li><li>Re-run: python run_all.py</li></ul>")
    sources = ("<ul><li>URSSAF open data (ODbL): auto-entrepreneurs, self-employed, income.</li>"
               "<li>INSEE BDM 010755410 / 010755411, Etalab boundaries 2025 (Licence Ouverte).</li>"
               "<li>Nager.Date holidays. Job posting (Ashby, 18/11/2026). Read 27/11/2026.</li></ul>")
    limits = (f"<ul><li>{COMPANY}'s channels, spend, sign-ups and tests are simulated: the method transfers, the numbers do not.</li>"
              "<li>Untested channels use assumed incremental shares.</li><li>No AI assistant was queried: AI search is a proposed protocol.</li></ul>")
    body = ('<div class="grid" style="grid-template-columns: 1fr 1fr; flex: 0 0 540px;">'
            + card("90 days: reallocate in month 1, prove it with geo tests after", C["gantt"], "sim")
            + card(f"Same budget: brand EUR {al.loc['Brand search', 'spend_now'] / 1000:.0f}k to {al.loc['Brand search', 'spend_opt'] / 1000:.1f}k a week, "
                   f"partnerships doubled", C["stacked"], "sim") + "</div>"
            + '<div class="grid" style="grid-template-columns: 1fr 1fr 1fr 1fr;">'
            + f'<div class="card txt"><h2>Method</h2>{method}</div>'
            + f'<div class="card txt"><h2>Sources and licences</h2>{sources}</div>'
            + f'<div class="card txt"><h2>Limits</h2>{limits}</div>'
            + f'<div class="card txt"><h2>AI note</h2><p>{AI}</p></div></div>')
    pages.append(page(6, "Plan, method and limits: reallocate in 30 days, measure for 60, review every week",
                      "Budget from the simulated optimiser; every public number is reproducible from the sources below.", body,
                      "Details: README and docs/ in the repository"))
    out = pdf_kit.render(pages, TITLE)
    import pymupdf  # noqa: PLC0415  (page 0 as an image for the README)
    img = OUT.parents[1] / "docs" / "img" / "report_page0.png"
    img.parent.mkdir(parents=True, exist_ok=True)
    pymupdf.open(out)[0].get_pixmap(dpi=80).save(img)


if __name__ == "__main__":
    main()
