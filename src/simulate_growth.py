"""Simulated acquisition of a health insurer on the French freelancer segment (seed 42). Everything here is SIMULATED:
no Alan data is used or implied. The volume is anchored on public data only:
  * seasonality  = INSEE monthly micro-entrepreneur creations (raw / seasonally adjusted factor), elasticity 1.6
  * geography    = URSSAF economically active auto-entrepreneurs by region (13 metropolitan regions)
  * sub-segments = URSSAF sectors grouped in 4 sectors + new founders (< 6 months)
  * holidays     = Nager.Date French public holidays
Outputs (data/sim/): acq_weekly, organic_weekly, response_curves, experiments, experiment_arms, geo_test_x3,
creatives, creative_frequency, referrals. Hidden truth of the 8 planted events: data/_hidden_truth.csv (never pushed).
Run from the repository root:  python src/simulate_growth.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from common import DATA, PUBLIC, SIM

sys.stdout.reconfigure(encoding="utf-8")
rng = np.random.default_rng(42)

WEEKS = pd.date_range("2024-12-02", periods=104, freq="7D")          # Mondays, 12/2024 -> 11/2026
BETA = 1.6                                                             # sign-up seasonality = creations seasonality ^ 1.6
SEGS = ["Consulting & IT", "Construction & crafts", "Health & wellbeing", "Commerce & services", "New founders (<6 months)"]
SEG_OF = {"JZ": 0, "M1": 0, "M2": 0, "M3": 0, "M4": 0, "M5": 0, "KZ": 0, "LZ": 0,
          "F1": 1, "F2": 1, "F3": 1, "CZ1": 1, "CZ2": 1, "S1": 1, "G1": 1, "QZ": 2, "S2": 2, "R2": 2}
CH = ["Brand search", "Non-brand search", "LinkedIn Ads", "Partnerships", "Referral", "AI search"]
# weekly spend today (EUR), Hill curve of INCREMENTAL sign-ups: V * S^a / (S^a + K^a)
CURVES = pd.DataFrame({
    "channel": CH[:5], "spend_now": [10_000, 14_000, 12_000, 6_000, 4_000],
    "v_max": [54.0, 312.0, 568.0, 412.0, 180.0], "k_half": [2_500, 9_000, 50_000, 20_000, 8_000], "hill_a": [1.5, 1.0, 1.0, 1.0, 1.0],
    "min_spend": [2_000, 5_000, 4_000, 2_000, 1_000], "max_spend": [12_000, 24_000, 30_000, 12_000, 5_000]})
INC_FRAC = {"Brand search": 0.12, "Non-brand search": 0.65, "LinkedIn Ads": 0.55, "Partnerships": 0.80, "Referral": 0.75, "AI search": 0.90}
CLAIM = {"Brand search": 1.25, "Non-brand search": 1.30, "LinkedIn Ads": 1.90, "Partnerships": 1.35, "Referral": 1.0, "AI search": 1.0}
TILT = {"Brand search": [1.5, .8, 1, .9, 1], "Non-brand search": [1, 1.2, 1, 1, 1.4], "LinkedIn Ads": [5, .5, .8, .6, 1],
        "Partnerships": [1.5, .8, .9, 1, 2], "Referral": [1.6, .9, 1.1, .8, .8], "AI search": [3, .4, .8, .6, 1.2]}
CONV_SEG = np.array([0.07, 0.03, 0.034, 0.026, 0.04])                  # sign-ups / clicks, by sub-segment
CONV_CH = {"Brand search": 2.0, "Non-brand search": 1.0, "LinkedIn Ads": 0.83, "Partnerships": 0.94, "Referral": 4.0, "AI search": 1.6}
CTR = {"Brand search": 0.08, "Non-brand search": 0.035, "LinkedIn Ads": 0.006, "Partnerships": 0.012, "Referral": 0.30, "AI search": np.nan}
RET_CH = {"Brand search": .80, "Non-brand search": .74, "LinkedIn Ads": .77, "Partnerships": .85, "Referral": .83, "AI search": .81}
RET_SEG = np.array([1.03, .97, 1.0, .96, .95])
X4_REGIONS, X4_WEEKS = ["27", "28", "52", "53", "75", "76"], pd.date_range("2026-05-04", periods=8, freq="7D")
X3_PRE, X3_TEST = pd.date_range("2026-01-05", periods=8, freq="7D"), pd.date_range("2026-03-02", periods=8, freq="7D")
FAKE_FROM, FAKE_SHARE, N_FAKE = pd.Timestamp("2026-02-02"), 0.10, 12
MATURE_BEFORE = WEEKS[-1] - pd.Timedelta(days=91)                       # 3-month activity observed only before this


def hill(s, v, k, a):
    s = np.asarray(s, float)
    return v * s ** a / (s ** a + k ** a)


def season_and_weights():
    ins = pd.read_csv(PUBLIC / "insee_micro_creations_monthly.csv")
    ins["factor"] = ins.creations_raw / ins.creations_sa
    fac = dict(zip(ins.month, ins.factor))
    thu = WEEKS + pd.Timedelta(days=3)
    months = thu.strftime("%Y-%m")
    s = np.array([fac.get(m, fac.get(f"{int(m[:4]) - 1}{m[4:]}")) for m in months])
    hol = pd.to_datetime(pd.read_csv(PUBLIC / "holidays_fr.csv").date)
    n_hol = np.array([((hol >= w) & (hol < w + pd.Timedelta(days=5))).sum() for w in WEEKS])
    level = (1 + 0.08 * np.arange(104) / 52) * s ** BETA * (1 - 0.06 * n_hol)

    ae = pd.read_csv(PUBLIC / "urssaf_ae_departement.csv", dtype={"code_region": str, "code_departement": str})
    last = ae[ae.dernier_jour_du_trimestre == "2025-12-31"]
    metro = last[~last.code_region.isin(["01", "02", "03", "04", "06"]) & (last.code_departement != "nca")]
    reg = metro.groupby(["code_region", "region"], as_index=False).economiquement_actifs.sum()
    reg["w"] = reg.economiquement_actifs / reg.economiquement_actifs.sum()

    sec = pd.read_csv(PUBLIC / "urssaf_ae_secteur_national.csv")
    sec = sec[sec.dernier_jour_du_trimestre == "2025-12-31"].copy()
    sec["code"] = sec.secteur_d_activite.str.split(" - ").str[0]
    sec = sec[~sec.code.isin(["_calage_", "UZ"])]
    sec["seg"] = sec.code.map(SEG_OF).fillna(3).astype(int)
    w4 = sec.groupby("seg").economiquement_actifs.sum().reindex(range(4)).to_numpy()
    recent = ae[ae.dernier_jour_du_trimestre.isin(["2025-09-30", "2025-12-31"])].immatriculations.sum()
    w_new = 0.55 * recent / last.economiquement_actifs.sum()
    seg_w = np.append(w4 / w4.sum() * (1 - w_new), w_new)
    return s, n_hol, level, reg, seg_w, metro


def main() -> None:
    SIM.mkdir(parents=True, exist_ok=True)
    s, n_hol, level, reg, seg_w, metro = season_and_weights()
    R, W = len(reg), len(WEEKS)
    region_codes = reg.code_region.to_numpy()
    x4_mask_r = np.isin(region_codes, X4_REGIONS)
    x4_mask_w = WEEKS.isin(X4_WEEKS)

    # national weekly expected real sign-ups per channel
    exp_real, spend_nat = {}, {}
    for _, c in CURVES.iterrows():
        sp = c.spend_now * rng.normal(1, 0.04, W)
        spend_nat[c.channel] = sp
        inc = hill(sp, c.v_max, c.k_half, c.hill_a) * level
        exp_real[c.channel] = inc / INC_FRAC[c.channel]
    exp_real["AI search"] = (10 + 35 * np.arange(W) / (W - 1)) * level
    spend_nat["AI search"] = np.zeros(W)
    organic_nat = 400 * level

    # platform over-claim multiplier so that sum(reported) / sum(real) = 1.40 (E1)
    tot_real = sum(exp_real[c].sum() for c in CH)
    plat = [c for c in CH if CLAIM[c] > 1]
    m = (1.40 * tot_real - sum(exp_real[c].sum() for c in CH if c not in plat)) / sum(exp_real[c].sum() * CLAIM[c] for c in plat)
    claim = {c: (CLAIM[c] * m if c in plat else 1.0) for c in CH}

    rows, org_rows = [], []
    fake_total = np.zeros((W, R, 5), int)
    for c in CH:
        mix = seg_w * np.array(TILT[c]); mix /= mix.sum()
        lam = exp_real[c][:, None, None] * reg.w.to_numpy()[None, :, None] * mix[None, None, :]
        spend = spend_nat[c][:, None, None] * reg.w.to_numpy()[None, :, None] * mix[None, None, :]
        if c == "Brand search":  # X4: brand search switched off in 3 holdout regions for 6 weeks
            lost = lam.copy(); lost[~x4_mask_w] = 0; lost[:, ~x4_mask_r] = 0
            org_extra = (1 - INC_FRAC[c]) * lost.sum(axis=2)        # the non-incremental part comes back as organic
            lam = lam - lost; spend[x4_mask_w[:, None, None] & x4_mask_r[None, :, None] & np.ones((1, 1, 5), bool)] = 0
        real = rng.poisson(lam)
        if c == "Referral":  # E7: self-referral from Feb 2026, extra sign-ups that never become active
            fk = rng.poisson(lam * FAKE_SHARE * (WEEKS >= FAKE_FROM)[:, None, None])
            fake_total = fk; real = real + fk
        genuine = real - (fake_total if c == "Referral" else 0)
        conv = CONV_SEG[None, None, :] * CONV_CH[c] * rng.normal(1, 0.03, real.shape)
        clicks = np.maximum(real, np.round(lam / conv * rng.normal(1, 0.05, real.shape))).astype(int)
        quotes = np.minimum(clicks, np.maximum(real, np.round(lam / rng.uniform(0.36, 0.44, real.shape))).astype(int))
        impr = np.round(clicks / CTR[c] * rng.normal(1, 0.05, real.shape)) if not np.isnan(CTR[c]) else np.full(real.shape, np.nan)
        reported = real + rng.poisson(lam * (claim[c] - 1)) if claim[c] > 1 else real
        ret = np.clip(RET_CH[c] * RET_SEG, 0, 0.97)
        active = rng.binomial(genuine, ret[None, None, :]).astype(float)
        active[WEEKS >= MATURE_BEFORE] = np.nan
        for wi, wk in enumerate(WEEKS):
            for ri in range(R):
                for si in range(5):
                    rows.append((wk.date(), region_codes[ri], SEGS[si], c, round(float(spend[wi, ri, si]), 2), impr[wi, ri, si],
                                 int(clicks[wi, ri, si]), int(quotes[wi, ri, si]), int(reported[wi, ri, si]), int(real[wi, ri, si]),
                                 active[wi, ri, si]))
    org_lam = organic_nat[:, None, None] * reg.w.to_numpy()[None, :, None] * seg_w[None, None, :] \
        + org_extra[:, :, None] * seg_w[None, None, :]
    org = rng.poisson(org_lam)
    org_act = rng.binomial(org, 0.79).astype(float); org_act[WEEKS >= MATURE_BEFORE] = np.nan
    for wi, wk in enumerate(WEEKS):
        for ri in range(R):
            for si in range(5):
                org_rows.append((wk.date(), region_codes[ri], SEGS[si], int(org[wi, ri, si]), org_act[wi, ri, si]))

    acq = pd.DataFrame(rows, columns=["week", "region_code", "subsegment", "channel", "spend_eur", "impressions", "clicks",
                                      "quotes", "signups_reported", "signups_real", "active_3m"])
    acq["impressions"] = acq.impressions.astype("Int64"); acq["active_3m"] = acq.active_3m.astype("Int64")
    acq = acq.merge(reg[["code_region", "region"]].rename(columns={"code_region": "region_code"}), on="region_code")
    acq.to_csv(SIM / "acq_weekly.csv", index=False)
    orgdf = pd.DataFrame(org_rows, columns=["week", "region_code", "subsegment", "signups_real", "active_3m"])
    orgdf["active_3m"] = orgdf.active_3m.astype("Int64")
    orgdf.to_csv(SIM / "organic_weekly.csv", index=False)
    CURVES.to_csv(SIM / "response_curves.csv", index=False)
    pd.DataFrame({"week": WEEKS.date, "insee_seasonal_factor": s.round(4), "holiday_weekdays": n_hol}).to_csv(SIM / "calendar_weekly.csv", index=False)

    # ---------------------------------------------------------------- experiments
    exps = pd.DataFrame([
        ("X1", "Landing page by sub-segment", "A page written for each sub-segment lifts quote requests", "quote-request rate per visitor", "visitor", "2026-09-07", "2026-10-04", 0.5),
        ("X2", "Referral reward EUR 100 vs EUR 50", "A larger reward makes more members invite a freelancer", "share of members shown the offer who send an invitation", "member-week", "2026-06-15", "2026-08-09", 0.5),
        ("X3", "LinkedIn Ads geo test (spend x3)", "Extra LinkedIn spend brings incremental sign-ups", "total sign-ups per departement-week", "departement", "2026-03-02", "2026-04-26", 0.5),
        ("X4", "Brand search holdout", "Brand search sign-ups would mostly arrive anyway", "total sign-ups per region-week", "region", "2026-05-04", "2026-06-28", 0.36),
    ], columns=["experiment", "name", "hypothesis", "metric", "unit", "start_week", "end_week", "planned_share_test"])
    exps.to_csv(SIM / "experiments.csv", index=False)
    arms = []
    for i, wk in enumerate(pd.date_range("2026-09-07", periods=4, freq="7D")):     # X1: 51.9 / 48.1 split (E3)
        n = int(rng.normal(26_000, 800)); n_t = rng.binomial(n, 0.519); n_c = n - n_t
        arms += [("X1", "test", wk.date(), i + 1, n_t, int(rng.binomial(n_t, 0.040 * 1.08))),
                 ("X1", "control", wk.date(), i + 1, n_c, int(rng.binomial(n_c, 0.040)))]
    for i, wk in enumerate(pd.date_range("2026-06-15", periods=8, freq="7D")):     # X2: novelty, lift gone after 3 weeks (E5)
        lift = 0.40 if i < 3 else 0.02
        for arm, l in (("test", lift), ("control", 0.0)):
            n = int(rng.normal(20_000, 300))
            arms.append(("X2", arm, wk.date(), i + 1, n, int(rng.binomial(n, 0.032 * (1 + l)))))
    pd.DataFrame(arms, columns=["experiment", "arm", "week", "week_index", "units", "conversions"]).to_csv(SIM / "experiment_arms.csv", index=False)

    # X3 geo test: 20 matched pairs of departements (log economically active AE, AE income 2025)
    rev = pd.read_csv(PUBLIC / "urssaf_revenus_departement.csv", dtype={"code_departement": str})
    rev = rev[(rev.annee == 2025) & (rev.type_de_travailleur_independant == "Autoentrepreneur")]
    d = metro[["code_departement", "departement", "economiquement_actifs"]].merge(
        rev.assign(income=rev.revenu / rev.nombre_de_ti)[["code_departement", "income"]], on="code_departement")
    d = d[~d.code_departement.isin(["75", "92", "93", "94", "13", "69", "59"])].copy()   # largest markets kept out of the test
    z = np.c_[np.log(d.economiquement_actifs), d.income]; z = (z - z.mean(0)) / z.std(0)
    free, pairs = list(range(len(d))), []
    order = np.argsort(-d.economiquement_actifs.to_numpy())
    for i in order:
        if i not in free or len(pairs) == 20:
            continue
        free.remove(i)
        j = min(free, key=lambda k: np.sum((z[i] - z[k]) ** 2)); free.remove(j)
        pairs.append((i, j) if rng.random() < 0.5 else (j, i))
    tot_eco = metro.economiquement_actifs.sum()
    li = CURVES.set_index("channel").loc["LinkedIn Ads"]
    nat_total = sum(exp_real[c] for c in CH) + organic_nat
    geo = []
    for p, (t, cidx) in enumerate(pairs):
        for grp, idx in (("test", t), ("control", cidx)):
            row = d.iloc[idx]; share = row.economiquement_actifs / tot_eco
            for wk in X3_PRE.append(X3_TEST):
                wi = WEEKS.get_loc(wk); test = grp == "test" and wk in X3_TEST
                base = nat_total[wi] * share * rng.gamma(400, 1 / 400)
                extra_inc = share * (hill(3 * li.spend_now, li.v_max, li.k_half, 1) - hill(li.spend_now, li.v_max, li.k_half, 1)) * level[wi] if test else 0.0
                li_spend = li.spend_now * share * (3 if test else 1)
                li_rep = (exp_real["LinkedIn Ads"][wi] * share + extra_inc / INC_FRAC["LinkedIn Ads"]) * claim["LinkedIn Ads"]
                geo.append((row.code_departement, row.departement, grp, f"P{p + 1:02d}", wk.date(), "test" if wk in X3_TEST else "pre",
                            round(li_spend, 2), int(rng.poisson(base + extra_inc)), int(rng.poisson(li_rep))))
    pd.DataFrame(geo, columns=["departement_code", "departement", "grp", "pair", "week", "period", "linkedin_spend_eur",
                               "signups_total", "linkedin_reported"]).to_csv(SIM / "geo_test_x3.csv", index=False)

    # ---------------------------------------------------------------- creatives (LinkedIn Ads), E6
    angles = ["Price", "Prevention", "Fast reimbursement", "App experience", "Made for freelancers"]
    formats = ["Single image", "Carousel", "Video", "Document"]
    winner = {0: 3, 1: 2, 2: 1, 3: 0, 4: 4}           # sub-segment -> winning angle
    fmt_mult = {"Single image": 1.0, "Carousel": 1.08, "Video": 1.15, "Document": 0.92}
    cells = [(si, ai) for si in range(5) for ai in range(5)] * 4 + [tuple(x) for x in rng.integers(0, 5, (20, 2))]
    cre, freq = [], []
    for n, (si, ai) in enumerate(cells):
        fmt = formats[rng.integers(0, 4)]
        cid = f"LI-{SEGS[si][:3].upper()}-{angles[ai].split()[0][:5].upper()}-{fmt[:3].upper()}-{n + 1:03d}"
        launch = WEEKS[rng.integers(0, 90)]
        base = 0.006 * (1.45 if winner[si] == ai else rng.uniform(0.82, 1.05)) * fmt_mult[fmt]
        cre.append((cid, "LinkedIn Ads", SEGS[si], angles[ai], fmt, launch.date(), int(rng.integers(2, 15))))
        for f in range(1, 11):
            fat = (1 - 0.04 * (f - 1)) if f <= 4 else 0.5 * (1 - 0.02 * (f - 5))
            imp = int(rng.normal(60_000, 6_000) * 0.82 ** (f - 1))
            freq.append((cid, f, imp, int(rng.binomial(imp, base * fat))))
    pd.DataFrame(cre, columns=["creative_id", "channel", "subsegment", "angle", "format", "launch_week", "weeks_live"]).to_csv(SIM / "creatives.csv", index=False)
    pd.DataFrame(freq, columns=["creative_id", "frequency", "impressions", "clicks"]).to_csv(SIM / "creative_frequency.csv", index=False)

    # ---------------------------------------------------------------- referrals by referrer code (E7)
    ref = acq[acq.channel == "Referral"].copy()
    wk = pd.to_datetime(ref.week)
    n_gen = int(ref.signups_real.sum() - fake_total.sum())
    n_act = int(ref.active_3m.fillna(0).sum())
    matured = wk < MATURE_BEFORE
    gen_mat = int((ref.signups_real[matured]).sum() - fake_total[WEEKS < MATURE_BEFORE].sum())
    # genuine referees: popularity-weighted assignment to ~0.65 x n referrers
    n_ref = int(n_gen * 0.62)
    pop = rng.lognormal(0, 0.6, n_ref)
    owner = rng.choice(n_ref, n_gen, p=pop / pop.sum())
    is_mat = np.zeros(n_gen, bool); is_mat[rng.choice(n_gen, gen_mat, replace=False)] = True
    is_act = np.zeros(n_gen, bool); is_act[rng.choice(np.flatnonzero(is_mat), n_act, replace=False)] = True
    delay = rng.gamma(2.2, 4.5, n_gen)
    g = pd.DataFrame({"o": owner, "m": is_mat, "a": is_act, "d": delay})
    agg = g.groupby("o").agg(n_referees=("m", "size"), n_matured=("m", "sum"), n_active_3m=("a", "sum"), median_days=("d", "median"))
    agg["first_week"] = [WEEKS[int(x)].date() for x in rng.integers(0, 100, len(agg))]
    # fake referees: 12 codes, sign up within a day, never active
    fk_w = np.repeat(np.arange(W), fake_total.sum(axis=(1, 2)))
    fk_owner = rng.choice(N_FAKE, len(fk_w), p=rng.dirichlet(np.ones(N_FAKE) * 3))
    fk = pd.DataFrame({"o": fk_owner, "m": WEEKS[fk_w] < MATURE_BEFORE, "d": rng.uniform(0, 1.2, len(fk_w)), "w": fk_w})
    fagg = fk.groupby("o").agg(n_referees=("m", "size"), n_matured=("m", "sum"), median_days=("d", "median"), fw=("w", "min"))
    fagg["n_active_3m"] = 0; fagg["first_week"] = [WEEKS[int(x)].date() for x in fagg.fw]
    allr = pd.concat([agg, fagg.drop(columns="fw")], ignore_index=True)
    allr = allr.sample(frac=1, random_state=42).reset_index(drop=True)
    allr["referrer_code"] = [f"REF{i + 1:04d}" for i in range(len(allr))]
    allr["median_days"] = allr.median_days.round(1)
    allr[["referrer_code", "first_week", "n_referees", "n_matured", "n_active_3m", "median_days"]].to_csv(SIM / "referrals.csv", index=False)
    fake_codes = allr.loc[(allr.n_active_3m == 0) & (allr.median_days <= 1.2) & (allr.n_referees >= 10), "referrer_code"].tolist()

    # ---------------------------------------------------------------- hidden truth (never pushed)
    truth = [("E1", "reported_to_real_ratio", 1.40), ("E2", "brand_incremental_fraction", INC_FRAC["Brand search"]),
             ("E3", "x1_test_share", 0.519), ("E4", "linkedin_conv_multiplier_vs_nonbrand", CONV_CH["LinkedIn Ads"]),
             ("E5", "x2_lift_weeks_1_3", 0.40), ("E5", "x2_lift_after", 0.02), ("E6", "ctr_factor_above_freq_4", 0.5),
             ("E7", "self_referral_codes", "|".join(fake_codes)), ("E8", "false_alert_month", "2026-08"),
             ("X3", "linkedin_incremental_fraction", INC_FRAC["LinkedIn Ads"])]
    truth += [("CLAIM", c, round(claim[c], 4)) for c in CH] + [("INC_FRAC", c, v) for c, v in INC_FRAC.items()]
    truth += [("E6_WINNER", SEGS[k], angles[v]) for k, v in winner.items()]
    pd.DataFrame(truth, columns=["event", "item", "value"]).to_csv(DATA / "_hidden_truth.csv", index=False)
    print(f"acq_weekly {len(acq):,} rows · real {acq.signups_real.sum():,} · reported/real {acq.signups_reported.sum() / acq.signups_real.sum():.3f}"
          f" · organic {orgdf.signups_real.sum():,} · geo {len(geo)} · creatives {len(cre)} · referrers {len(allr):,} (fake {len(fake_codes)})")


if __name__ == "__main__":
    main()
