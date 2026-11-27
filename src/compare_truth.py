"""Local check: compare what the analysis found with the planted truth (data/_hidden_truth.csv, never published).
Skipped silently when the file is absent (published copy). Run:  python src/compare_truth.py
"""
from __future__ import annotations

import sys

import pandas as pd

from common import DATA, OUT

sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    f = DATA / "_hidden_truth.csv"
    if not f.exists():
        print("no hidden truth file (published copy): skipped")
        return 0
    t = pd.read_csv(f)
    v = lambda e, i: t[(t.event == e) & (t["item"] == i)].value.iloc[0]  # noqa: E731
    ex = pd.read_csv(OUT / "experiment_results.csv").set_index("experiment")
    checks = [
        ("E1 over-count", float(v("E1", "reported_to_real_ratio")), pd.read_csv(OUT / "attribution_flag.csv").over_count[0], 0.05),
        ("E3 X1 test share", float(v("E3", "x1_test_share")), pd.read_csv(OUT / "x1.csv").share_test[0], 0.01),
    ]
    bad = 0
    for name, truth, found, tol in checks:
        ok = abs(truth - found) <= tol
        bad += not ok
        print(f"{'OK ' if ok else 'BAD'} {name}: truth {truth:.3f}, found {found:.3f}")
    x4 = ex.loc["X4"]
    ok = x4.brand_share_lo <= float(v("E2", "brand_incremental_fraction")) <= x4.brand_share_hi
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} E2 brand incremental share: truth {float(v('E2', 'brand_incremental_fraction')):.2f} "
          f"in CI [{x4.brand_share_lo:.2f}, {x4.brand_share_hi:.2f}]")
    flagged = set(pd.read_csv(OUT / "referral_flags.csv").referrer_code)
    planted = set(str(v("E7", "self_referral_codes")).split("|"))
    ok = flagged == planted
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} E7 self-referral codes: {len(flagged & planted)}/{len(planted)} found, {len(flagged - planted)} false positives")
    win = pd.read_csv(OUT / "creative_angle_seg.csv").query("winner").set_index("subsegment").angle
    planted_w = t[t.event == "E6_WINNER"].set_index("item").value
    ok = all(win.get(s) == a for s, a in planted_w.items())
    bad += not ok
    print(f"{'OK ' if ok else 'BAD'} E6 winning angle per sub-segment ({sum(win.get(s) == a for s, a in planted_w.items())}/5)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
