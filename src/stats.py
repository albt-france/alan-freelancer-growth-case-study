"""Experiment statistics (SIMULATED data): confidence intervals and decisions for X1-X4.

  prop_test        difference of two proportions: z-test, 95% CI on the relative lift (delta method)
  srm_test         sample-ratio mismatch: chi-square goodness of fit
  sample_size_prop users per arm to detect a relative lift (used by the planner's experiment calculator)
  did_pairs        geo difference-in-differences, 95% CI by bootstrap over matched pairs (X3)
  did_poisson      region holdout difference-in-differences, 95% CI by Poisson parametric bootstrap (X4)
Writes data/output/experiment_results.csv and data/output/x2_weekly_ci.csv.
Run from the repository root after src/run_sql.py:  python src/stats.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy import stats

from common import OUT, SIM

sys.stdout.reconfigure(encoding="utf-8")
Z = stats.norm.ppf
rng = np.random.default_rng(7)


def prop_test(x_t, n_t, x_c, n_c, alpha=0.05):
    p_t, p_c = x_t / n_t, x_c / n_c
    p_pool = (x_t + x_c) / (n_t + n_c)
    z = (p_t - p_c) / np.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    rel_se = np.sqrt((p_t * (1 - p_t) / n_t) / p_c ** 2 + p_t ** 2 * (p_c * (1 - p_c) / n_c) / p_c ** 4)
    zc = Z(1 - alpha / 2)
    rel = p_t / p_c - 1
    return dict(rate_t=p_t, rate_c=p_c, lift=rel, lo=rel - zc * rel_se, hi=rel + zc * rel_se, p=2 * stats.norm.sf(abs(z)))


def srm_test(n_t, n_c, expected_t=0.5):
    n = n_t + n_c
    chi2 = (n_t - n * expected_t) ** 2 / (n * expected_t) + (n_c - n * (1 - expected_t)) ** 2 / (n * (1 - expected_t))
    return dict(share_t=n_t / n, chi2=chi2, p=stats.chi2.sf(chi2, 1))


def sample_size_prop(p_base, rel_mde, alpha=0.05, power=0.80):
    p2 = p_base * (1 + rel_mde)
    num = (Z(1 - alpha / 2) + Z(power)) ** 2 * (p_base * (1 - p_base) + p2 * (1 - p2))
    return int(np.ceil(num / (p2 - p_base) ** 2))


def _did(t_pre, t_post, c_pre, c_post):
    exp = t_pre * c_post / c_pre
    return t_post - exp, t_post / exp - 1


def did_pairs(geo: pd.DataFrame, n_boot: int = 4000):
    """X3: incremental sign-ups and lift; bootstrap resamples the 20 matched pairs."""
    g = geo.pivot_table(index="pair", columns=["grp", "period"], values="signups_total", aggfunc="sum")
    r = geo.pivot_table(index="pair", columns=["grp", "period"], values="linkedin_reported", aggfunc="sum")

    def est(idx):
        s, q = g.iloc[idx].sum(), r.iloc[idx].sum()
        inc, lift = _did(s["test", "pre"], s["test", "test"], s["control", "pre"], s["control", "test"])
        rep, _ = _did(q["test", "pre"], q["test", "test"], q["control", "pre"], q["control", "test"])
        return inc, lift, rep
    point = est(np.arange(len(g)))
    boots = np.array([est(rng.integers(0, len(g), len(g))) for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5], axis=0)
    return point, lo, hi


def did_poisson(x4: pd.Series, n_boot: int = 20000):
    """X4: lost sign-ups, brand incremental share and total lift; each total is redrawn as Poisson."""
    keys = ["h_pre", "h_post", "c_pre", "c_post", "b_h_pre", "b_c_pre", "b_c_post"]
    draw = {k: rng.poisson(x4[k], n_boot) for k in keys}
    exp = draw["h_pre"] * draw["c_post"] / draw["c_pre"]
    lost = exp - draw["h_post"]
    share = lost / (draw["b_h_pre"] * draw["b_c_post"] / draw["b_c_pre"])
    lift = draw["h_post"] / exp - 1
    return {k: np.percentile(v, [2.5, 97.5]) for k, v in (("lost", lost), ("share", share), ("lift", lift))}


def main() -> None:
    arms = pd.read_csv(SIM / "experiment_arms.csv")
    rows = []
    # X1 landing page: lift looks positive, but the split is broken
    a = arms[arms.experiment == "X1"].groupby("arm")[["units", "conversions"]].sum()
    t = prop_test(a.loc["test", "conversions"], a.loc["test", "units"], a.loc["control", "conversions"], a.loc["control", "units"])
    srm = srm_test(a.loc["test", "units"], a.loc["control", "units"])
    rows.append(dict(experiment="X1", label="X1 landing page by sub-segment", effect=t["lift"], lo=t["lo"], hi=t["hi"], p=t["p"],
                     srm_share=srm["share_t"], srm_p=srm["p"], valid=srm["p"] >= 0.001,
                     decision="Invalid (sample-ratio mismatch): fix the bot filter, rerun"))
    # X2 referral reward: novelty effect
    b = arms[arms.experiment == "X2"]
    wk = []
    for w, d in b.groupby("week_index"):
        d = d.set_index("arm")
        r = prop_test(d.loc["test", "conversions"], d.loc["test", "units"], d.loc["control", "conversions"], d.loc["control", "units"])
        wk.append(dict(week_index=w, lift=r["lift"], lo=r["lo"], hi=r["hi"]))
    pd.DataFrame(wk).to_csv(OUT / "x2_weekly_ci.csv", index=False)
    for lab, sel in (("X2 referral reward, weeks 1-3", b.week_index <= 3), ("X2 referral reward, weeks 4-8", b.week_index > 3)):
        d = b[sel].groupby("arm")[["units", "conversions"]].sum()
        r = prop_test(d.loc["test", "conversions"], d.loc["test", "units"], d.loc["control", "conversions"], d.loc["control", "units"])
        rows.append(dict(experiment="X2", label=lab, effect=r["lift"], lo=r["lo"], hi=r["hi"], p=r["p"], valid=True,
                         decision="Novelty only: keep EUR 50" if "4-8" in lab else "Early lift (novelty)"))
    # X3 LinkedIn geo test
    geo = pd.read_csv(SIM / "geo_test_x3.csv", dtype={"departement_code": str})
    (inc, lift, rep), lo, hi = did_pairs(geo)
    x3 = pd.read_csv(OUT / "x3.csv").iloc[0]
    rows.append(dict(experiment="X3", label="X3 LinkedIn Ads geo test (spend x3)", effect=lift, lo=lo[1], hi=hi[1], valid=True,
                     incremental=inc, incremental_lo=lo[0], incremental_hi=hi[0], reported_extra=rep,
                     cost_per_incremental=x3.extra_spend / inc, cost_per_incremental_lo=x3.extra_spend / hi[0],
                     cost_per_incremental_hi=x3.extra_spend / max(lo[0], 1e-9), cost_per_reported=x3.extra_spend / rep,
                     decision="Inconclusive: hold spend, retest longer"))
    # X4 brand search holdout
    x4 = pd.read_csv(OUT / "x4.csv").iloc[0]
    ci = did_poisson(x4)
    rows.append(dict(experiment="X4", label="X4 brand search holdout", effect=x4.total_lift, lo=ci["lift"][0], hi=ci["lift"][1], valid=True,
                     incremental=x4.lost_total, incremental_lo=ci["lost"][0], incremental_hi=ci["lost"][1],
                     brand_share=x4.brand_incremental_share, brand_share_lo=ci["share"][0], brand_share_hi=ci["share"][1],
                     decision="Cut brand search to a defence budget"))
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "experiment_results.csv", index=False)
    for r in res.itertuples():
        print(f"{r.label:40s} {100 * r.effect:+6.1f}%  [{100 * r.lo:+.1f}, {100 * r.hi:+.1f}]  {r.decision}")
    print(f"X4 brand incremental share {100 * x4.brand_incremental_share:.1f}% [{100 * ci['share'][0]:.1f}, {100 * ci['share'][1]:.1f}]")


if __name__ == "__main__":
    main()
