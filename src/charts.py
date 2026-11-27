"""Matplotlib charts for the PDF (PNG, 200 dpi, in data/raw/report_build/img/). Style of the bank-forecasting reference:
white background, light grid, one accent colour (blue), the rest in grey, direct labels instead of legends.
Chart titles (the findings) are written by build_pdf.py in the card, so they stay searchable text.
Every function reads data/output or data/public and returns the PNG path.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LogNorm, TwoSlopeNorm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from common import OUT, PUBLIC, RAW  # noqa: E402

IMG = RAW / "report_build" / "img"
BLUE, GREY, RED, INK, MUTED, GRID, LIGHT, PALE = "#2A78D6", "#A3A19A", "#D03B3B", "#0B0B0B", "#52514E", "#E1E0D9", "#C9DDF5", "#D9D8D2"
plt.rcParams.update({
    "font.family": "Segoe UI", "font.size": 9.5, "axes.edgecolor": GRID, "axes.labelcolor": MUTED,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "legend.frameon": False,
})
# slot sizes in px (image area inside the cards of build_pdf.py)
HERO, SMALL, MAIN, SIDE, WIDE, HALF, P6 = (1490, 318), (480, 268), (895, 712), (571, 262), (733, 262), (356, 262), (733, 470)
SEGS = ["Consulting & IT", "Construction & crafts", "Health & wellbeing", "Commerce & services", "New founders (<6 months)"]


def o(name: str, **kw) -> pd.DataFrame:
    return pd.read_csv(OUT / f"{name}.csv", **kw)


def fig(size, **kw):
    return plt.subplots(figsize=(size[0] / 100, size[1] / 100), dpi=100, **kw)


def save(f, name: str) -> str:
    IMG.mkdir(parents=True, exist_ok=True)
    f.tight_layout(pad=0.6)
    p = IMG / f"{name}.png"
    f.savefig(p, dpi=200)
    plt.close(f)
    return p.as_uri()


def k(x: float) -> str:
    if abs(x) >= 1_000_000:
        return f"{x / 1e6:.1f}M"
    return f"{x / 1000:.0f}k" if abs(x) >= 10_000 else f"{x:,.0f}"


# ================================================================ page 0
def waterfall() -> str:
    w = o("waterfall").signups.to_numpy()
    spend = o("attribution").set_index("channel").loc["All channels", "spend"]
    f, ax = fig(HERO)
    xs = [0, 1, 2, 3, 4]
    bars = [(0, w[0], GREY, "Reported by\nplatforms"), (w[1], w[0] - w[1], RED, "Double counted"),
            (0, w[1], GREY, "Deduplicated\nsign-ups"), (w[2], w[1] - w[2], PALE, "Would have come\nanyway"), (0, w[2], BLUE, "Incremental\nsign-ups")]
    for x, (b, h, c, lab) in zip(xs, bars):
        ax.bar(x, h, bottom=b, color=c, width=0.62)
        ax.text(x, b + h + w[0] * 0.02, (f"-{h:,.0f}" if c in (RED, PALE) else f"{h:,.0f}"), ha="center", va="bottom",
                fontsize=11.5, fontweight="bold", color=INK)
    for x, tot in ((0, w[0]), (2, w[1]), (4, w[2])):
        ax.text(x, tot / 2, f"EUR {spend / tot:.0f}\nper sign-up", ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")
    for x in (0.31, 2.31):
        ax.plot([x, x + 0.38], [w[1] if x > 1 else w[0], w[1] if x > 1 else w[0]], color=GREY, lw=0.8, ls=":")
    ax.annotate(f"{w[0] / w[1]:.2f}x over-count", xy=(1, w[1] + (w[0] - w[1]) / 2), xytext=(1.45, w[0] * 0.98),
                fontsize=10.5, color=RED, fontweight="bold", arrowprops=dict(arrowstyle="->", color=RED, lw=1))
    ax.annotate(f"{100 * w[2] / w[1]:.0f}% of real sign-ups\nare caused by the spend", xy=(4, w[2]), xytext=(3.25, w[0] * 0.78),
                fontsize=10.5, color=BLUE, fontweight="bold", arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))
    ax.set_xticks(xs, [b[3] for b in bars], fontsize=10)
    ax.set_ylim(0, w[0] * 1.12)
    ax.yaxis.set_major_formatter(lambda v, _: k(v))
    ax.set_ylabel("Sign-ups, 104 weeks")
    ax.grid(axis="x", visible=False)
    return save(f, "p0_waterfall")


def response_curves(size=SMALL, name="p0_curves") -> str:
    g, a = o("response_grid"), o("allocation")
    f, ax = fig(size)
    for r in a.itertuples():
        gg = g[g.channel == r.channel]
        up = r.delta > 500
        col = BLUE if up else GREY
        ax.plot(gg.spend / 1000, gg.incremental, color=col, lw=1.8 if up else 1.1)
        ax.scatter(r.spend_now / 1000, r.inc_now, s=22, color="white", edgecolor=col, zorder=3, lw=1.3)
        ax.scatter(r.spend_opt / 1000, r.inc_opt, s=26, color=col, zorder=4)
        if abs(r.delta) > 500:
            ax.annotate("", xy=(r.spend_opt / 1000, r.inc_opt), xytext=(r.spend_now / 1000, r.inc_now),
                        arrowprops=dict(arrowstyle="->", color=RED if r.delta < 0 else BLUE, lw=1))
        dy = {"Non-brand search": 22, "LinkedIn Ads": -14}.get(r.channel, 0)
        ax.text(r.max_spend * 1.25 / 1000 + 0.6, gg.incremental.iloc[-1] + dy, r.channel.replace(" search", ""), fontsize=8.3, color=col,
                va="center")
    ax.set_xlabel("Weekly spend (EUR k)  ·  hollow = today, solid = optimal")
    ax.set_ylabel("Incremental sign-ups / week")
    ax.set_xlim(0, g.spend.max() / 1000 + 8)
    return save(f, name)


def forest(size=MAIN, name="p4_forest", compact=False) -> str:
    e = o("experiment_results")
    order = ["X4 brand search holdout", "X3 LinkedIn Ads geo test (spend x3)", "X2 referral reward, weeks 4-8",
             "X2 referral reward, weeks 1-3", "X1 landing page by sub-segment"]
    e = e.set_index("label").loc[order].reset_index()
    f, ax = fig(size)
    for i, r in e.iterrows():
        invalid = not r.valid
        col = GREY if invalid or "1-3" in r.label else BLUE
        ax.plot([100 * r.lo, 100 * r.hi], [i, i], color=col, lw=2.6 if not compact else 2, solid_capstyle="round")
        ax.scatter(100 * r.effect, i, s=70 if not compact else 34, color="white" if invalid else col, edgecolor=col, zorder=3, lw=1.6)
        if not compact:
            ax.text(100 * r.hi + 1.5, i, f"{100 * r.effect:+.1f}%  [{100 * r.lo:+.1f}, {100 * r.hi:+.1f}]", va="center", fontsize=10, color=col)
            ax.text(92, i, r.decision.replace("Invalid (sample-ratio mismatch): fix the bot filter, rerun", "Invalid (SRM): fix bot filter, rerun"),
                    va="center", fontsize=10.5, color=RED if invalid else INK, fontweight="bold")
    ax.axvline(0, color=INK, lw=0.9)
    lab = ["X4 brand search off", "X3 LinkedIn spend x3", "X2 reward, weeks 4-8", "X2 reward, weeks 1-3", "X1 landing page"]
    ax.set_yticks(range(len(e)), lab if not compact else ["X4", "X3", "X2 w4-8", "X2 w1-3", "X1"], fontsize=10.5 if not compact else 8.5)
    ax.set_xlabel("Effect on the test metric, % (95% confidence interval)")
    ax.grid(axis="y", visible=False)
    if compact:
        ax.set_xlim(-12, 55)
        ax.text(100 * e.iloc[4].hi + 2, 4, "invalid (SRM)", fontsize=8, color=RED, va="center")
        ax.text(100 * e.iloc[3].lo - 2, 3, "novelty", fontsize=8, color=GREY, va="center", ha="right")
    else:
        ax.set_xlim(-12, 160)
        ax.axvspan(88, 160, color="#F7F7F5", zorder=0)
        ax.text(92, len(e) - 0.35, "Decision", fontsize=10, color=MUTED)
        ax.set_xticks([-10, 0, 10, 20, 30, 40, 50, 60])
        x1 = o("x1").iloc[0]
        ax.annotate(f"split {100 * x1.share_test:.1f} / {100 * (1 - x1.share_test):.1f}\ninstead of 50 / 50", xy=(100 * e.iloc[4].effect, 4),
                    xytext=(18, 3.35), fontsize=9.5, color=RED, arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
    return save(f, name)


def signups_vs_insee(size=SMALL, name="p0_f1") -> str:
    w = o("weekly_total", parse_dates=["week"])
    ins = o("insee_monthly")
    ins["d"] = pd.to_datetime(ins.month) + pd.Timedelta(days=14)
    ins = ins[(ins.d >= w.week.min()) & (ins.d <= w.week.max() + pd.Timedelta(days=30))]
    f, ax = fig(size)
    ax.plot(w.week, 100 * w.total_real / w.total_real.mean(), color=GREY, lw=1, label="Sign-ups (weekly)")
    ax.plot(ins.d, 100 * ins.raw / ins.raw.mean(), color=BLUE, lw=2, marker="o", ms=3)
    a = ins[ins.month == "2026-08"].iloc[0]
    ax.annotate("Aug 2026: the yearly\ncreation trough", xy=(a.d, 100 * a.raw / ins.raw.mean()), xytext=(pd.Timestamp("2025-09-15"), 55),
                fontsize=8.5, color=BLUE, arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.9))
    ax.text(ins.d.iloc[2], 100 * ins.raw.iloc[2] / ins.raw.mean() + 22, "INSEE creations", color=BLUE, fontsize=8.5, fontweight="bold")
    ax.text(w.week.iloc[60], 140, "Sign-ups", color=GREY, fontsize=8.5, fontweight="bold")
    ax.set_ylabel("Index, average = 100")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
    ax.set_ylim(40, 160)
    return save(f, name)


# ================================================================ page 1 (PUBLIC)
def market_map() -> str:
    import geopandas as gpd  # noqa: PLC0415
    g = gpd.read_file(PUBLIC / "departements_simplified.geojson")
    d = o("market_dept", dtype={"dep": str})
    g = g.merge(d, left_on="code", right_on="dep", how="left")
    norm = LogNorm(vmin=1500, vmax=100_000)
    f, ax = fig(MAP)
    metro = g[~g.code.str.startswith("97")]
    metro.plot(column="eco_active", cmap="Blues", norm=norm, ax=ax, edgecolor="white", linewidth=0.4)
    ax.set_aspect(1 / np.cos(np.radians(46.5)))
    ax.set_axis_off()
    cent = metro.set_index("code").representative_point()
    offs = {"75": (3.2, 1.6), "92": (-4.6, 0.9), "69": (3.0, 0.2), "13": (1.2, -1.6), "33": (-4.2, 0.6)}
    for r in d[d.target].itertuples():
        p = cent[r.dep]
        dx, dy = offs.get(r.dep, (2, 1))
        ax.annotate(f"{r.departement}\n{r.eco_active / 1000:.0f}k active", xy=(p.x, p.y), xytext=(p.x + dx, p.y + dy), fontsize=9.5,
                    color=INK, fontweight="bold", arrowprops=dict(arrowstyle="-", color=INK, lw=0.8),
                    bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.85))
    for i, code in enumerate(["971", "972", "973", "974"]):
        ins = ax.inset_axes([0.0 + i * 0.11, 0.0, 0.1, 0.1])
        sub = g[g.code == code]
        sub.plot(column="eco_active", cmap="Blues", norm=norm, ax=ins, edgecolor="white", linewidth=0.3)
        ins.set_axis_off()
        ins.set_title(sub.nom.iloc[0], fontsize=7, color=MUTED, pad=1)
    sm = plt.cm.ScalarMappable(cmap="Blues", norm=norm)
    cb = f.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.035, pad=0.01, aspect=40, shrink=0.55)
    cb.set_label("Economically active auto-entrepreneurs, Q4 2025 (log scale)", fontsize=9)
    cb.outline.set_visible(False)
    return save(f, "p1_map")


MAP = (733, 712)


def dumbbell() -> str:
    r = o("market_region", dtype={"code_region": str})
    over = r[r.code_region.isin(["01", "02", "03", "04", "06"])]
    r = r[~r.code_region.isin(["01", "02", "03", "04", "06"])].copy()
    r = pd.concat([r, pd.DataFrame([{"region": "Overseas (4)", "registered": over.registered.sum(), "eco_active": over.eco_active.sum(),
                                     "active_share": over.eco_active.sum() / over.registered.sum()}])])
    r = r.sort_values("registered")
    f, ax = fig(WIDE)
    y = np.arange(len(r))
    ax.hlines(y, r.eco_active / 1000, r.registered / 1000, color=PALE, lw=3)
    ax.scatter(r.registered / 1000, y, color=GREY, s=22, zorder=3)
    ax.scatter(r.eco_active / 1000, y, color=BLUE, s=22, zorder=3)
    for yy, row in zip(y, r.itertuples()):
        ax.text(row.registered / 1000 + 12, yy, f"{100 * row.active_share:.0f}%", va="center", fontsize=8,
                color=RED if row.active_share < 0.5 else MUTED)
    ax.set_yticks(y, [x.replace("Provence-Alpes-Côte d'Azur", "PACA").replace("Auvergne-Rhône-Alpes", "Auvergne-R.-Alpes")
                      .replace("Bourgogne-Franche-Comté", "Bourgogne-F.-Comté") for x in r.region], fontsize=7.6)
    top = r.iloc[-1]
    ax.text(top.eco_active / 1000, len(r) - 1 + 0.55, "active", color=BLUE, fontsize=8.5, ha="center", fontweight="bold")
    ax.text(top.registered / 1000, len(r) - 1 + 0.55, "registered", color=GREY, fontsize=8.5, ha="center", fontweight="bold")
    ax.set_xlabel("Auto-entrepreneurs, thousands (Q4 2025)  ·  label = share economically active")
    ax.set_ylim(-0.7, len(r) + 0.2)
    ax.grid(axis="y", visible=False)
    return save(f, "p1_dumbbell")


def scatter_targets() -> str:
    d = o("market_dept", dtype={"dep": str})
    d = d[~d.dep.str.startswith("97")]
    f, ax = fig(HALF)
    ax.scatter(d.density_km2, d.income_ae / 1000, s=d.eco_active / 1200, color=PALE, edgecolor=GREY, lw=0.4)
    t = d[d.target]
    ax.scatter(t.density_km2, t.income_ae / 1000, s=t.eco_active / 1200, color=BLUE, edgecolor="white", lw=0.6, zorder=3)
    pos = {"75": (-60, -6), "92": (-45, 10), "69": (6, 6), "13": (6, -12), "33": (6, -4)}
    for r in t.itertuples():
        ax.annotate(r.dep, xy=(r.density_km2, r.income_ae / 1000), xytext=pos.get(r.dep, (5, 5)), textcoords="offset points",
                    fontsize=8, color=BLUE, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlabel("Active AE per km² (log)")
    ax.set_ylabel("Avg AE income, EUR k (2025)")
    return save(f, "p1_scatter")


def treemap() -> str:
    import squarify  # noqa: PLC0415
    s = o("market_sector")
    grp = s.groupby("subsegment").eco_active.sum().sort_values(ascending=False)
    f, ax = fig(HALF)
    W, H = 100, 100
    rects = squarify.squarify(squarify.normalize_sizes(grp.to_numpy(), W, H), 0, 0, W, H)
    for (seg, tot), r in zip(grp.items(), rects):
        sub = s[s.subsegment == seg].sort_values("eco_active", ascending=False)
        inner = squarify.squarify(squarify.normalize_sizes(sub.eco_active.to_numpy(), r["dx"], r["dy"]), r["x"], r["y"], r["dx"], r["dy"])
        col = BLUE if seg == "Consulting & IT" else GREY
        for ir in inner:
            ax.add_patch(Rectangle((ir["x"], ir["y"]), ir["dx"], ir["dy"], fc=col, ec="white", lw=0.5, alpha=0.9))
        ax.add_patch(Rectangle((r["x"], r["y"]), r["dx"], r["dy"], fc="none", ec="white", lw=2.2))
        label = seg.replace(" & ", " &\n") + f"\n{100 * tot / grp.sum():.0f}%"
        ax.text(r["x"] + 1.5, r["y"] + r["dy"] - 2, label, va="top", fontsize=8,
                color="white", fontweight="bold")
    ax.set_xlim(0, W); ax.set_ylim(0, H); ax.set_axis_off()
    return save(f, "p1_treemap")


# ================================================================ page 2
def calendar_heatmap() -> str:
    m = o("insee_monthly")
    p = m.pivot(index="yr", columns="mo", values="seasonal_factor")
    v = 100 * (p - 1)
    f, ax = fig(MAIN)
    ax.imshow(v.to_numpy(), cmap="RdBu", norm=TwoSlopeNorm(0, -28, 28), aspect="auto")
    for i in range(v.shape[0]):
        for j in range(v.shape[1]):
            x = v.iat[i, j]
            if pd.notna(x):
                ax.text(j, i, f"{x:+.0f}", ha="center", va="center", fontsize=10, color="white" if abs(x) > 14 else INK)
    ax.set_xticks(range(12), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], fontsize=11)
    ax.set_yticks(range(len(v)), v.index, fontsize=10.5)
    ax.tick_params(length=0)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.add_patch(Rectangle((6.5, -0.5), 1, len(v), fc="none", ec=INK, lw=2))
    prof = o("insee_season_profile").set_index("mo").avg_factor
    ax.text(7, -0.75, f"August {100 * (prof[8] - 1):+.0f}% on average", ha="center", fontsize=11, fontweight="bold", color=RED)
    ax.set_ylim(len(v) - 0.5, -1.1)
    ax.set_xlabel("Monthly creations vs seasonally adjusted level, % (INSEE, micro-entrepreneurs)", fontsize=10)
    return save(f, "p2_calendar")


def subsegment_multiples() -> str:
    q = o("market_subsegment_q", parse_dates=["q_end"])
    segs = q.groupby("subsegment").index_first_q.last().sort_values(ascending=False).index
    f, axs = fig(SIDE, ncols=4, sharey=True)
    for ax, s in zip(axs, segs):
        d = q[q.subsegment == s]
        top = s == segs[0]
        ax.fill_between(d.q_end, 100, d.index_first_q, color=BLUE if top else PALE, alpha=0.9 if top else 1, lw=0)
        ax.plot(d.q_end, d.index_first_q, color=BLUE if top else GREY, lw=1.4)
        ax.set_title(s.replace(" & ", " &\n"), fontsize=8.5, loc="left", color=INK)
        ax.text(d.q_end.iloc[-1], d.index_first_q.iloc[-1] + 6, f"x{d.index_first_q.iloc[-1] / 100:.1f}", ha="right", fontsize=9,
                fontweight="bold", color=BLUE if top else MUTED)
        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("'%y"))
        ax.set_xticks([pd.Timestamp("2019-06-30"), pd.Timestamp("2025-06-30")])
    axs[0].set_ylabel("Active AE, Q1 2019 = 100", fontsize=8)
    axs[0].set_ylim(90, 230)
    return save(f, "p2_multiples")


def deseason_line() -> str:
    a = o("alerts", parse_dates=["month"])
    f, ax = fig(SIDE)
    ax.plot(a.month, a.per_week, color=GREY, lw=1.2, marker="o", ms=2.5)
    ax.plot(a.month, a.deseason * a.per_week.mean() / a.deseason.mean(), color=BLUE, lw=2)
    aug = a[a.month == "2026-08-01"].iloc[0]
    ax.scatter(aug.month, aug.per_week, s=160, facecolor="none", edgecolor=RED, lw=1.5, zorder=4)
    ax.text(aug.month, aug.per_week - 230, "naive alert\n" + f"{100 * aug.mom_raw:+.0f}%", color=RED, ha="center", fontsize=8.5,
            fontweight="bold")
    ax.plot([aug.month - pd.Timedelta(days=25), aug.month + pd.Timedelta(days=25)], [aug.per_week - 60, aug.per_week + 60], color=RED, lw=1.6)
    ax.text(a.month.iloc[1], a.deseason.iloc[1] * a.per_week.mean() / a.deseason.mean() + 140, "deseasonalised", color=BLUE, fontsize=8.5,
            fontweight="bold")
    ax.text(a.month.iloc[3], a.per_week.iloc[3] - 300, "raw", color=GREY, fontsize=8.5, fontweight="bold")
    ax.set_ylabel("Sign-ups per week (monthly avg)")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
    return save(f, "p2_deseason")


# ================================================================ page 3
def funnels() -> str:
    fc = o("funnel_channel").set_index("channel")
    order = ["Brand search", "Non-brand search", "LinkedIn Ads", "Partnerships", "Referral", "AI search"]
    stages = ["impressions", "clicks", "quotes", "signups_real", "active_3m"]
    names = ["Impressions", "Clicks", "Quotes", "Sign-ups", "Active 3 m"]
    f, axs = fig(MAIN, nrows=3, ncols=2)
    for ax, ch in zip(axs.flat, order):
        r = fc.loc[ch]
        vals = [r[s] for s in stages]
        best = ch == "Partnerships"
        for i, v in enumerate(vals):
            if pd.isna(v) or v == 0:
                ax.barh(i, 1, left=-0.5, color="white", edgecolor=PALE, hatch="///", height=0.72)
                ax.text(0, i, "not observable", ha="center", va="center", fontsize=8.5, color=MUTED)
                continue
            wdt = np.log10(v) / 7.5
            col = (BLUE if best else GREY) if i == 4 else (LIGHT if best else PALE)
            ax.barh(i, wdt, left=-wdt / 2, color=col, height=0.72)
            ax.text(wdt / 2 + 0.02, i, f"{k(v)}", va="center", fontsize=8.5, color=INK)
            if i > 0 and pd.notna(vals[i - 1]) and vals[i - 1] > 0:
                ax.text(-wdt / 2 - 0.02, i, f"{100 * v / vals[i - 1]:.0f}%" if i != 4 else f"{100 * r.retention_3m:.0f}%", va="center",
                        ha="right", fontsize=8.5, color=BLUE if (best and i == 4) else MUTED, fontweight="bold" if i == 4 else "normal")
        ax.set_title(f"{ch}  ·  EUR {r.cost_per_real:.0f} per sign-up" if r.spend > 0 else f"{ch}  ·  no paid spend", fontsize=10,
                     loc="left", color=BLUE if best else INK, fontweight="bold")
        ax.set_yticks(range(5), names, fontsize=8.5)
        ax.invert_yaxis()
        ax.set_xlim(-0.75, 0.75)
        ax.set_xticks([])
        ax.grid(False)
        for sp in ("left", "bottom"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0)
    f.text(0.995, 0.005, "Bar width on log scale · left = step conversion; Active = share still active after 3 months", ha="right",
           fontsize=8, color=MUTED)
    return save(f, "p3_funnels")


def simpson_slope() -> str:
    s = o("simpson")
    seg = s[s.subsegment != "All sub-segments"]
    mix = seg.groupby("subsegment").clicks.sum() / seg.clicks.sum()
    std = seg.assign(w=seg.subsegment.map(mix)).assign(x=lambda d: d.conv * d.w).groupby("channel").x.sum()
    tot = s[s.subsegment == "All sub-segments"].set_index("channel").conv
    f, ax = fig(SIDE)
    for ch in tot.index:
        col = BLUE if ch == "LinkedIn Ads" else GREY
        ax.plot([0, 1], [100 * tot[ch], 100 * std[ch]], color=col, lw=2.4 if col == BLUE else 1.4, marker="o", ms=5)
        dy = {"Non-brand search": 0.06, "Partnerships": -0.06}.get(ch, 0)
        ax.text(-0.04, 100 * tot[ch] + dy, f"{ch}  {100 * tot[ch]:.1f}%", ha="right", va="center", fontsize=8.5, color=col)
        ax.text(1.04, 100 * std[ch], f"{100 * std[ch]:.1f}%", ha="left", va="center", fontsize=8.5, color=col)
    li = seg[seg.channel == "LinkedIn Ads"]
    ax.text(0.5, 100 * tot.max() + 0.25, f"LinkedIn: {100 * li.click_mix[li.subsegment == 'Consulting & IT'].iloc[0]:.0f}% of clicks "
            "from consulting & IT", ha="center", fontsize=8.3, color=BLUE)
    ax.set_xticks([0, 1], ["As reported (total)", "Same sub-segment mix"], fontsize=9)
    ax.set_xlim(-0.75, 1.25)
    ax.set_ylabel("Sign-ups per click, %")
    ax.grid(axis="x", visible=False)
    return save(f, "p3_slope")


def bubbles() -> str:
    fc = o("funnel_channel").merge(o("incremental_channel")[["channel", "cost_per_incremental", "source"]], on="channel")
    fc = fc[fc.spend > 0].copy()
    f, ax = fig(SIDE)
    for r in fc.itertuples():
        best = r.cost_per_incremental == fc.cost_per_incremental.min()
        col = BLUE if best else (RED if r.channel == "Brand search" else GREY)
        ax.scatter(r.cost_per_incremental, 100 * r.retention_3m, s=r.spend / 2500, color=col, alpha=0.75, edgecolor="white")
        dx, dy, ha = {"Partnerships": (0, 2.2, "center"), "Referral": (8, 1.2, "left"), "Non-brand search": (10, -3.2, "left"),
                      "LinkedIn Ads": (22, 1.6, "left"), "Brand search": (0, 2.6, "center")}[r.channel]
        ax.text(r.cost_per_incremental + dx, 100 * r.retention_3m + dy,
                f"{r.channel.replace(' search', '')}  EUR {r.cost_per_incremental:,.0f}  ({r.source})", ha=ha, fontsize=8,
                color=col, fontweight="bold" if best or col == RED else "normal")
    ax.set_xscale("log")
    ax.set_xlabel("Cost per incremental sign-up, EUR (log)  ·  bubble = spend")
    ax.set_ylabel("Active after 3 months, %")
    ax.set_xlim(35, 4000)
    ax.set_ylim(66, 92)
    return save(f, "p3_bubbles")


# ================================================================ page 4
def geo_dots() -> str:
    w = o("x3_weekly", parse_dates=["week"])
    x3 = o("x3").iloc[0]
    claim = x3.reported_extra / (x3.t_pre * x3.c_post / x3.c_pre)
    e = o("experiment_results").set_index("experiment").loc["X3"]
    f, ax = fig(SIDE)
    test_start = w[w.period == "test"].week.min()
    ax.axvspan(test_start - pd.Timedelta(days=3), w.week.max() + pd.Timedelta(days=3), color="#EEF4FC", zorder=0)
    for g, col in (("control", GREY), ("test", BLUE)):
        d = w[w.grp == g]
        ax.plot(d.week, d.idx, color=col, lw=0.8, alpha=0.6)
        ax.scatter(d.week, d.idx, color=col, s=18, zorder=3)
        ax.text(d.week.iloc[-1] + pd.Timedelta(days=4), d.idx.iloc[-1], g, color=col, fontsize=8.5, va="center", fontweight="bold")
    lo_, hi_ = ax.get_ylim()
    ax.set_ylim(lo_, hi_ + 14)
    ax.text(test_start + pd.Timedelta(days=2), hi_ + 13, f"LinkedIn spend x3\nmeasured {100 * e.effect:+.0f}%  ·  claimed {100 * claim:+.0f}%",
            fontsize=8.5, va="top", color=BLUE, fontweight="bold")
    ax.set_ylabel("Sign-ups, pre-period = 100")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    return save(f, "p4_geo")


def novelty_ribbon() -> str:
    w = o("x2_weekly_ci")
    f, ax = fig(SIDE)
    ax.fill_between(w.week_index, 100 * w.lo, 100 * w.hi, color=LIGHT, lw=0)
    ax.plot(w.week_index, 100 * w.lift, color=BLUE, lw=2, marker="o", ms=4)
    ax.axhline(0, color=INK, lw=0.9)
    ax.axvline(3.5, color=GREY, ls="--", lw=1)
    ax.text(3.6, 100 * w.hi.max() * 0.92, "novelty wears off\nafter week 3", fontsize=8.5, color=MUTED)
    ax.set_xticks(w.week_index)
    ax.set_xlabel("Week of the test")
    ax.set_ylabel("Lift, % (95% CI band)")
    return save(f, "p4_novelty")


# ================================================================ page 5
def fatigue() -> str:
    a = o("creative_fatigue")
    tot = a.groupby("frequency").apply(lambda d: (d.ctr * d.impressions).sum() / d.impressions.sum(), include_groups=False)
    f, ax = fig(MAIN)
    for ang, d in a.groupby("angle"):
        ax.plot(d.frequency, 100 * d.ctr, color=PALE, lw=1.4)
    ax.plot(tot.index, 100 * tot.to_numpy(), color=BLUE, lw=3.2, marker="o", ms=6)
    ax.text(10.15, 100 * tot.iloc[-1], "All creatives", fontsize=10.5, color=BLUE, va="center", fontweight="bold")
    ax.text(6, 100 * tot[5] * 1.1, "grey: one line per angle (5)", fontsize=9.5, color=GREY)
    ax.axvline(4.5, color=RED, ls="--", lw=1.4)
    r = o("creative_fatigue_rule").iloc[0]
    ax.annotate(f"CTR {100 * (r.ctr_ratio_5_6_vs_1_4 - 1):+.0f}% after\nthe 4th exposure", xy=(5, 100 * tot[5]), xytext=(6.3, 100 * tot[1] * 0.98),
                fontsize=12.5, color=RED, fontweight="bold", arrowprops=dict(arrowstyle="->", color=RED, lw=1.2))
    ax.text(4.4, 100 * tot[5] * 1.03, "rotate here", ha="right", fontsize=10.5, color=RED, fontweight="bold")
    ax.set_xticks(range(1, 11))
    ax.set_xlim(0.7, 11.6)
    ax.set_xlabel("Exposure frequency (times the same person saw the creative)", fontsize=10.5)
    ax.set_ylabel("Click-through rate, %", fontsize=10.5)
    return save(f, "p5_fatigue")


def angle_heatmap() -> str:
    a = o("creative_angle_seg")
    p = a.pivot(index="subsegment", columns="angle", values="ctr_index").loc[SEGS]
    win = a.pivot(index="subsegment", columns="angle", values="winner").loc[SEGS]
    f, ax = fig(SIDE)
    ax.imshow(p.to_numpy(), cmap="Blues", vmin=0.7, vmax=1.5, aspect="auto")
    for i in range(p.shape[0]):
        for j in range(p.shape[1]):
            ax.text(j, i, f"{p.iat[i, j]:.2f}", ha="center", va="center", fontsize=8.5,
                    color="white" if p.iat[i, j] > 1.25 else INK, fontweight="bold" if win.iat[i, j] else "normal")
            if win.iat[i, j]:
                ax.add_patch(Rectangle((j - 0.48, i - 0.46), 0.96, 0.92, fc="none", ec=INK, lw=1.6))
    ax.set_xticks(range(5), [c.replace(" ", "\n", 1) for c in p.columns], fontsize=8)
    ax.set_yticks(range(5), [s.replace(" (<6 months)", "") for s in p.index], fontsize=8)
    ax.tick_params(length=0)
    ax.grid(False)
    for sp in ax.spines.values():
        sp.set_visible(False)
    return save(f, "p5_heatmap")


def referral_hist() -> str:
    d = o("referral_dist")
    s = o("referral_summary").iloc[0]
    f, ax = fig(SIDE)
    flag = d.n_referees >= s.min_flagged_referees
    ax.bar(d.n_referees[~flag], d.referrers[~flag], color=GREY, width=0.8)
    ax.bar(d.n_referees[flag], d.referrers[flag], color=RED, width=0.8)
    ax.set_yscale("log")
    ax.axvline(s.p99_referees + 0.5, color=MUTED, ls=":", lw=1)
    ax.text(s.p99_referees + 1, d.referrers.max() * 0.5, "99th percentile", fontsize=8, color=MUTED)
    ax.annotate(f"{s.flagged_codes:.0f} codes, {s.flagged_referees:.0f} referees,\n0 active after 3 months", xy=(d.n_referees[flag].median(), 1.1),
                xytext=(d.n_referees.max() * 0.38, 60), fontsize=8.5, color=RED, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=0.9))
    ax.set_xlabel("Referees per referrer code")
    ax.set_ylabel("Referrers (log)")
    return save(f, "p5_hist")


# ================================================================ page 6
def gantt() -> str:
    tasks = [("Cut brand search to a defence budget", 1, 2, BLUE), ("Shift budget to Partner A/B/C (deals, then live)", 1, 13, BLUE),
             ("Referral: cap rewards, self-referral rule", 1, 3, GREY), ("Creative rotation at frequency 4, by angle", 2, 13, GREY),
             ("Rerun X1 with one bot filter for both arms", 3, 7, GREY), ("LinkedIn geo retest (x2 spend, 12 weeks)", 2, 13, GREY),
             ("AI search: monthly question panel", 2, 13, PALE), ("Weekly learning review + monthly reallocation", 1, 13, PALE)]
    f, ax = fig(P6)
    for i, (t, s, e, c) in enumerate(tasks):
        ax.barh(i, e - s + 1, left=s - 0.5, color=c, height=0.6)
        ax.text(0.3, i, t, ha="right", va="center", fontsize=8.6, color=INK)
    ax.set_yticks([])
    ax.invert_yaxis()
    ax.set_xlim(0.5, 13.5)
    ax.set_xticks(range(1, 14), [f"W{w}" for w in range(1, 14)], fontsize=8)
    for x in (4.5, 8.5):
        ax.axvline(x, color=GRID, lw=1)
    ax.text(2.5, -0.9, "Days 1-30", ha="center", fontsize=8.5, color=MUTED); ax.text(6.5, -0.9, "31-60", ha="center", fontsize=8.5, color=MUTED)
    ax.text(11, -0.9, "61-90", ha="center", fontsize=8.5, color=MUTED)
    ax.grid(axis="y", visible=False)
    ax.spines["left"].set_visible(False)
    return save(f, "p6_gantt")


def stacked_budget() -> str:
    a = o("allocation").set_index("channel")
    order = ["Brand search", "Non-brand search", "LinkedIn Ads", "Partnerships", "Referral"]
    cols = {"Brand search": "#6E6C66", "Non-brand search": GREY, "LinkedIn Ads": LIGHT, "Partnerships": BLUE, "Referral": PALE}
    f, ax = fig(P6)
    for y, col in ((1, "spend_now"), (0, "spend_opt")):
        left = 0
        for ch in order:
            v = a.loc[ch, col]
            ax.barh(y, v / 1000, left=left, color=cols[ch], height=0.55, edgecolor="white")
            if v > 2500:
                ax.text(left + v / 2000, y, f"{ch.replace(' search', '').replace(' Ads', '')}\n{v / 1000:.1f}k", ha="center", va="center",
                        fontsize=8.2, color="white" if ch in ("Brand search", "Partnerships") else INK)
            left += v / 1000
    ax.set_yticks([1, 0], ["Today", "Recommended"], fontsize=10)
    ax.set_xlabel("Weekly budget, EUR thousands (same total)")
    ax.set_ylim(-0.6, 1.6)
    ax.grid(axis="y", visible=False)
    return save(f, "p6_stacked")


def build_all() -> dict[str, str]:
    return {"waterfall": waterfall(), "curves": response_curves(), "forest_small": forest(SMALL, "p0_forest", compact=True),
            "f1": signups_vs_insee(), "map": market_map(), "dumbbell": dumbbell(), "scatter": scatter_targets(), "treemap": treemap(),
            "calendar": calendar_heatmap(), "multiples": subsegment_multiples(), "deseason": deseason_line(), "funnels": funnels(),
            "slope": simpson_slope(), "bubbles": bubbles(), "forest": forest(), "geo": geo_dots(), "novelty": novelty_ribbon(),
            "fatigue": fatigue(), "heatmap": angle_heatmap(), "hist": referral_hist(), "gantt": gantt(), "stacked": stacked_budget()}


if __name__ == "__main__":
    out = build_all()
    print(len(out), "charts in", IMG)
