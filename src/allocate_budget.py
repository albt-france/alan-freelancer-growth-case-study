"""Budget allocation on the response curves (SIMULATED): same weekly budget, split to maximise incremental sign-ups.

Each channel has a Hill curve of incremental sign-ups per week, inc(S) = V * S^a / (S^a + K^a), with practical bounds
(brand defence minimum, partner capacity...). The optimum equalises the marginal cost per incremental sign-up across
channels inside the bounds (scipy SLSQP). AI search has no spend lever and is left out.
Writes data/output/allocation.csv and data/output/response_grid.csv.
Run from the repository root:  python src/allocate_budget.py
"""
from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from common import OUT, SIM

sys.stdout.reconfigure(encoding="utf-8")


def hill(s, v, k, a):
    s = np.asarray(s, float)
    return v * s ** a / (s ** a + k ** a)


def marginal(s, v, k, a):
    s = np.maximum(np.asarray(s, float), 1.0)
    return v * a * s ** (a - 1) * k ** a / (s ** a + k ** a) ** 2


def optimise(c: pd.DataFrame, budget: float) -> np.ndarray:
    f = lambda x: -sum(hill(x[i], r.v_max, r.k_half, r.hill_a) for i, r in enumerate(c.itertuples()))  # noqa: E731
    res = minimize(f, c.spend_now.to_numpy(float), method="SLSQP",
                   bounds=list(zip(c.min_spend, c.max_spend)), constraints=[{"type": "eq", "fun": lambda x: x.sum() - budget}],
                   options={"maxiter": 500, "ftol": 1e-10})
    return res.x


def main() -> None:
    c = pd.read_csv(SIM / "response_curves.csv")
    budget = c.spend_now.sum()
    opt = optimise(c, budget)
    c["spend_opt"] = opt.round(-2)
    c["inc_now"] = hill(c.spend_now, c.v_max, c.k_half, c.hill_a)
    c["inc_opt"] = hill(c.spend_opt, c.v_max, c.k_half, c.hill_a)
    c["mcpa_now"] = 1 / marginal(c.spend_now, c.v_max, c.k_half, c.hill_a)
    c["mcpa_opt"] = 1 / marginal(c.spend_opt, c.v_max, c.k_half, c.hill_a)
    c["cpa_now"] = c.spend_now / c.inc_now
    c["delta"] = c.spend_opt - c.spend_now
    c.to_csv(OUT / "allocation.csv", index=False)
    grid = []
    for r in c.itertuples():
        for s in np.linspace(0, r.max_spend * 1.25, 60):
            grid.append((r.channel, round(s, 0), hill(s, r.v_max, r.k_half, r.hill_a)))
    pd.DataFrame(grid, columns=["channel", "spend", "incremental"]).to_csv(OUT / "response_grid.csv", index=False)
    moved = c.delta.clip(lower=0).sum()
    print(f"budget {budget:,.0f}/week · moved {moved:,.0f} ({100 * moved / budget:.0f}%) · incremental "
          f"{c.inc_now.sum():.0f} -> {c.inc_opt.sum():.0f}/week (+{100 * (c.inc_opt.sum() / c.inc_now.sum() - 1):.0f}%)")
    print(c[["channel", "spend_now", "spend_opt", "mcpa_now", "mcpa_opt"]].round(0).to_string(index=False))


if __name__ == "__main__":
    main()
