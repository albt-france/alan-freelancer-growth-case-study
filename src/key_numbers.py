"""Compute every key number once and write data/output/key_numbers.json (common.save_key_numbers).
The README and the PDF copy these display strings word for word (checked before release).
Run from the repository root after stats.py and allocate_budget.py:  python src/key_numbers.py
"""
from __future__ import annotations

import sys

import pandas as pd

from common import OUT, save_key_numbers

sys.stdout.reconfigure(encoding="utf-8")


def r(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT / f"{name}.csv")


def pct(x: float, signed: bool = False) -> str:
    return f"{100 * x:+.0f}%" if signed else f"{100 * x:.0f}%"


def main() -> None:
    m = r("market_kpis").iloc[0]
    att = r("attribution").set_index("channel")
    inc = r("incremental_channel")
    al = r("allocation")
    ex = r("experiment_results").set_index("label")
    x1, x4, x3 = r("x1").iloc[0], ex.loc["X4 brand search holdout"], ex.loc["X3 LinkedIn Ads geo test (spend x3)"]
    aug = r("alerts").assign(month=lambda d: d.month.str[:7]).set_index("month").loc["2026-08"]
    fat = r("creative_fatigue_rule").iloc[0]
    ref = r("referral_summary").iloc[0]
    spend = att.loc["All channels", "spend"]
    moved = al.delta.clip(lower=0).sum() / al.spend_now.sum()
    k = {
        "freelancers": f"{m.ti_total / 1e6:.2f}M",
        "eco_active": f"{m.ae_eco_active_q4_2025 / 1e6:.2f}M",
        "active_share": pct(m.active_share),
        "creations_month": f"{round(m.creations_per_month_12m, -2):,.0f}",
        "overcount": f"{att.loc['All channels', 'over_count']:.2f}x",
        "cpa_reported": f"EUR {spend / att.loc['All channels', 'reported']:.0f}",
        "cpa_incremental": f"EUR {spend / inc.incremental.sum():.0f}",
        "budget_moved": pct(moved),
        "inc_gain": pct(al.inc_opt.sum() / al.inc_now.sum() - 1, True),
        "brand_share": pct(x4.brand_share),
        "brand_share_hi": pct(x4.brand_share_hi),
        "aug_raw": pct(aug.mom_raw, True),
        "aug_deseason": pct(aug.mom_deseason, True),
        "srm_split": f"{100 * x1.share_test:.1f} / {100 * (1 - x1.share_test):.1f}",
        "x1_lift": pct(ex.loc["X1 landing page by sub-segment", "effect"], True),
        "x2_early": pct(ex.loc["X2 referral reward, weeks 1-3", "effect"], True),
        "x2_late": pct(ex.loc["X2 referral reward, weeks 4-8", "effect"], True),
        "x3_reported": f"{x3.reported_extra:,.0f}",
        "x3_incremental": f"{x3.incremental:,.0f}",
        "x3_incremental_hi": f"{x3.incremental_hi:,.0f}",
        "fatigue": pct(fat.ctr_ratio_5_6_vs_1_4 - 1, True),
        "selfref_codes": f"{ref.flagged_codes:.0f}",
        "selfref_referees": f"{ref.flagged_referees:,.0f}",
    }
    k["aug_raw"] = k["aug_raw"].replace("+-", "-")
    save_key_numbers(k)
    print(" · ".join(f"{a}={b}" for a, b in k.items()))


if __name__ == "__main__":
    main()
