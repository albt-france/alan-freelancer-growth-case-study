"""Build site/dashboard/index.html: a one-page growth planner (self-contained, Plotly embedded, works offline).
Three stacked blocks a recruiter can play with:
  1. Budget allocator   one slider per channel (monthly budget); response curves, forecast incremental sign-ups,
                        marginal cost per incremental sign-up, 'Optimal split' button (same total budget)   SIMULATED
  2. Experiment calculator  baseline, minimum detectable effect, power, weekly traffic -> sample size and duration;
                        sample-ratio mismatch alert from an observed split                                  ILLUSTRATIVE maths
  3. Market map         departements of metropolitan France: active auto-entrepreneurs, income, registrations  PUBLIC DATA
Style and footer from dash_kit (no tabs). Run from the repository root:  python src/build_dashboard.py
"""
from __future__ import annotations

import json
import sys

import pandas as pd
from plotly.offline import get_plotlyjs

from common import FOOT, OUT, PUBLIC, SIM, SITE, TITLE
from dash_kit import CSS

sys.stdout.reconfigure(encoding="utf-8")
WEEKS_PER_MONTH = 4.33

EXTRA_CSS = """
.row { display:grid; grid-template-columns: 1.5fr 1fr; gap:12px; }
@media (max-width: 900px) { .row { grid-template-columns: 1fr; } }
.sl { display:grid; grid-template-columns: 150px 1fr 90px; align-items:center; gap:8px; margin:6px 0; font-size:13px; }
.sl input { width:100%; accent-color: var(--accent); }
.sl b { text-align:right; font-variant-numeric: tabular-nums; }
button.act { border:1px solid var(--accent); background:var(--accent); color:#fff; padding:7px 12px; border-radius:6px; cursor:pointer; font:inherit; font-size:13px; margin:6px 6px 0 0; }
button.ghost { background:transparent; color:var(--accent); }
.out { display:grid; grid-template-columns: repeat(3, 1fr); gap:8px; margin-top:8px; }
.out div { border:1px solid var(--line); border-radius:6px; padding:6px 8px; } .out b { display:block; font-size:20px; }
.calc label { display:grid; grid-template-columns: 1fr 120px; align-items:center; gap:8px; font-size:13px; margin:5px 0; color:var(--muted); }
.calc input, .calc select, .map select { font:inherit; font-size:13px; padding:4px 6px; border:1px solid var(--line); border-radius:4px; background:var(--card); color:var(--ink); }
.alert { padding:8px 10px; border-radius:6px; font-size:13px; margin-top:8px; }
.alert.ok { background:#E1F4EC; color:#0E7A52; } .alert.bad { background:#FBE3E3; color:#A32626; }
section.block { margin-bottom:14px; }
h3 { font-size:17px; margin:18px 0 8px; }
"""

JS = r"""
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const ACC = css('--accent'), GREY = css('--grey'), MUTED = css('--muted'), LINE = css('--line');
const lay = (x) => Object.assign({margin:{l:55,r:15,t:10,b:45}, paper_bgcolor:'rgba(0,0,0,0)', plot_bgcolor:'rgba(0,0,0,0)',
  font:{family:'Segoe UI, Arial', size:12, color:MUTED}, xaxis:{gridcolor:LINE, zeroline:false}, yaxis:{gridcolor:LINE, zeroline:false},
  showlegend:false}, x||{});
const cfg = {displayModeBar:false, responsive:true};
const fmt = (v, d=0) => Number(v).toLocaleString('en', {maximumFractionDigits:d, minimumFractionDigits:d});
const W = D.weeks_per_month;
// ---------------------------------------------------------------- 1. budget allocator (weekly curves shown per month)
const hill = (c, s) => c.v_max * Math.pow(s, c.hill_a) / (Math.pow(s, c.hill_a) + Math.pow(c.k_half, c.hill_a));
const marg = (c, s) => { s = Math.max(s, 1); return c.v_max * c.hill_a * Math.pow(s, c.hill_a - 1) * Math.pow(c.k_half, c.hill_a) / Math.pow(Math.pow(s, c.hill_a) + Math.pow(c.k_half, c.hill_a), 2); };
const CH = D.curves;
const box = document.getElementById('sliders');
CH.forEach((c, i) => {
  box.insertAdjacentHTML('beforeend', `<div class="sl"><span>${c.channel}</span><input type="range" id="s${i}" min="${c.min_spend*W}" max="${c.max_spend*W}" step="500" value="${c.spend_now*W}"><b id="v${i}"></b></div>`);
});
const spends = () => CH.map((c, i) => +document.getElementById('s' + i).value / W);   // weekly
function optimal(total) {
  const s = CH.map(c => c.min_spend); let left = total - s.reduce((a, b) => a + b, 0); const step = 100;
  while (left >= step) {
    let best = -1, gain = 0;
    CH.forEach((c, i) => { if (s[i] + step <= c.max_spend) { const g = hill(c, s[i] + step) - hill(c, s[i]); if (g > gain) { gain = g; best = i; } } });
    if (best < 0) break; s[best] += step; left -= step;
  }
  return s;
}
function draw() {
  const s = spends(), tot = s.reduce((a, b) => a + b, 0), opt = optimal(tot);
  const tr = [];
  CH.forEach((c, i) => {
    const xs = [], ys = [];
    for (let k = 0; k <= 60; k++) { const x = c.max_spend * 1.25 * k / 60; xs.push(x * W / 1000); ys.push(hill(c, x) * W); }
    const col = i === D.hi ? ACC : GREY;
    tr.push({x: xs, y: ys, mode:'lines', line:{color: col, width: 2}, name: c.channel, hovertemplate: c.channel + ': %{y:.0f} sign-ups/month at EUR %{x:.0f}k<extra></extra>'});
    tr.push({x:[s[i]*W/1000], y:[hill(c, s[i])*W], mode:'markers', marker:{size:11, color:'white', line:{color: ACC, width:2}}, hovertemplate:'your split<extra></extra>'});
    tr.push({x:[opt[i]*W/1000], y:[hill(c, opt[i])*W], mode:'markers', marker:{size:8, color: ACC}, hovertemplate:'optimal split<extra></extra>'});
    tr.push({x:[xs[60]], y:[ys[60]], mode:'text', text:[c.channel], textposition:'middle right', textfont:{size:11, color: MUTED}, hoverinfo:'skip'});
  });
  Plotly.react('p_curves', tr, lay({xaxis:{title:'Monthly spend, EUR thousands', gridcolor:LINE, range:[0, 175]},
    yaxis:{title:'Incremental sign-ups per month', gridcolor:LINE}}), cfg);
  const inc = CH.reduce((a, c, i) => a + hill(c, s[i]), 0) * W, incOpt = CH.reduce((a, c, i) => a + hill(c, opt[i]), 0) * W;
  document.getElementById('o_budget').textContent = 'EUR ' + fmt(tot * W / 1000, 0) + 'k';
  document.getElementById('o_inc').textContent = fmt(inc) + ' / month';
  document.getElementById('o_cpa').textContent = 'EUR ' + fmt(tot / (inc / W));
  document.getElementById('o_opt').textContent = incOpt - inc < 1 ? 'This split is already optimal for this budget.' : '+' + fmt(incOpt - inc) + ' incremental sign-ups / month with the optimal split';
  let rows = '';
  CH.forEach((c, i) => { document.getElementById('v' + i).textContent = 'EUR ' + fmt(s[i] * W / 1000, 1) + 'k';
    rows += `<tr><td>${c.channel}</td><td>${fmt(s[i]*W/1000,1)}k</td><td>${fmt(opt[i]*W/1000,1)}k</td><td>${fmt(hill(c, s[i])*W)}</td><td>EUR ${fmt(1/marg(c, s[i]))}</td></tr>`; });
  document.getElementById('t_alloc').innerHTML = '<tr><th>Channel</th><th>Your split</th><th>Optimal</th><th>Incr. sign-ups / month</th><th>Cost of the next sign-up</th></tr>' + rows;
}
CH.forEach((c, i) => document.getElementById('s' + i).oninput = draw);
document.getElementById('b_opt').onclick = () => { const s = spends(), o = optimal(s.reduce((a, b) => a + b, 0)); o.forEach((v, i) => document.getElementById('s' + i).value = Math.round(v * W / 500) * 500); draw(); };
document.getElementById('b_reset').onclick = () => { CH.forEach((c, i) => document.getElementById('s' + i).value = c.spend_now * W); draw(); };
draw();
// ---------------------------------------------------------------- 2. experiment calculator
const zq = p => { // inverse normal CDF (Acklam)
  const a=[-39.6968302866538,220.946098424521,-275.928510446969,138.357751867269,-30.6647980661472,2.50662827745924],
        b=[-54.4760987982241,161.585836858041,-155.698979859887,66.8013118877197,-13.2806815528857],
        c=[-0.00778489400243029,-0.322396458041136,-2.40075827716184,-2.54973253934373,4.37466414146497,2.93816398269878],
        d=[0.00778469570904146,0.32246712907004,2.445134137143,3.75440866190742]; const pl=0.02425;
  if (p < pl) { const q=Math.sqrt(-2*Math.log(p)); return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1); }
  if (p > 1-pl) { const q=Math.sqrt(-2*Math.log(1-p)); return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5])/((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1); }
  const q=p-0.5, r=q*q; return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q/(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1);
};
const erfc = x => { const t = 1/(1+0.5*Math.abs(x)); const y = t*Math.exp(-x*x-1.26551223+t*(1.00002368+t*(0.37409196+t*(0.09678418+t*(-0.18628806+t*(0.27886807+t*(-1.13520398+t*(1.48851587+t*(-0.82215223+t*0.17087277))))))))); return x >= 0 ? y : 2 - y; };
function calc() {
  const p = +document.getElementById('c_base').value / 100, mde = +document.getElementById('c_mde').value / 100,
        pw = +document.getElementById('c_pow').value, al = +document.getElementById('c_alpha').value / 100, tr = +document.getElementById('c_traffic').value;
  const p2 = p * (1 + mde), z = zq(1 - al / 2) + zq(pw);
  const n = Math.ceil(z * z * (p * (1 - p) + p2 * (1 - p2)) / Math.pow(p2 - p, 2));
  const weeks = Math.ceil(2 * n / tr);
  document.getElementById('c_n').textContent = fmt(n) + ' per arm';
  document.getElementById('c_w').textContent = weeks + (weeks === 1 ? ' week' : ' weeks') + (weeks < 2 ? ' (run 2 full weeks anyway)' : '');
  const nt = +document.getElementById('c_nt').value, nc = +document.getElementById('c_nc').value, N = nt + nc;
  const chi = Math.pow(nt - N/2, 2)/(N/2) + Math.pow(nc - N/2, 2)/(N/2), pv = erfc(Math.sqrt(chi/2));
  const el = document.getElementById('c_srm');
  el.className = 'alert ' + (pv < 0.001 ? 'bad' : 'ok');
  el.textContent = (pv < 0.001 ? 'Sample-ratio mismatch: ' : 'Split looks fine: ') + (100*nt/N).toFixed(1) + ' / ' + (100*nc/N).toFixed(1) +
    ', chi-square ' + chi.toFixed(1) + ', p = ' + (pv < 1e-6 ? '< 0.000001' : pv.toPrecision(2)) + (pv < 0.001 ? '. Do not read the result: find the cause (bot filter, redirect, caching) and rerun.' : '.');
}
document.querySelectorAll('.calc input, .calc select').forEach(e => e.oninput = calc);
calc();
// ---------------------------------------------------------------- 3. market map
const M = D.map;
const logTicks = z => { const lo = Math.floor(Math.min(...z) * 2) / 2, hi = Math.ceil(Math.max(...z) * 2) / 2, tv = [];
  for (let v = lo; v <= hi + 1e-9; v += 0.5) tv.push(v);
  return {tickvals: tv, ticktext: tv.map(v => { const x = Math.pow(10, v); return x >= 1000 ? fmt(x / 1000, x < 10000 ? 1 : 0) + 'k' : fmt(x, x < 10 ? 1 : 0); })}; };
function drawMap() {
  const k = document.getElementById('m_var').value, lab = {eco_active:'Active auto-entrepreneurs', income_ae:'Average AE income (EUR, 2025)',
    immat_4q:'Registrations, last 4 quarters', density_km2:'Active AE per km²'}[k];
  const vals = M.rows.map(r => r[k]);
  const z = (k === 'eco_active' || k === 'immat_4q' || k === 'density_km2') ? vals.map(v => Math.log10(Math.max(v, 0.1))) : vals;
  Plotly.react('p_map', [{type:'choropleth', geojson: M.geo, featureidkey:'properties.code', locations: M.rows.map(r => r.dep), z: z,
    colorscale:'Blues', reversescale:true, marker:{line:{color:'white', width:0.4}},
    customdata: M.rows.map(r => [r.departement, fmt(r.eco_active), fmt(r.income_ae), fmt(r.immat_4q), fmt(r.density_km2, 1), r.value_rank]),
    hovertemplate:'<b>%{customdata[0]}</b><br>Active AE %{customdata[1]}<br>Avg AE income EUR %{customdata[2]}<br>Registrations (4 q) %{customdata[3]}<br>Active AE / km² %{customdata[4]}<br>Market value rank %{customdata[5]}<extra></extra>',
    colorbar:Object.assign({title:{text: lab, side:'right'}, thickness:12}, z === vals ? {} : logTicks(z))}],
    lay({geo:{fitbounds:'locations', visible:false, bgcolor:'rgba(0,0,0,0)'}, margin:{l:0,r:0,t:0,b:0}}), cfg);
}
document.getElementById('m_var').onchange = drawMap;
drawMap();
"""


def main() -> None:
    c = pd.read_csv(SIM / "response_curves.csv")
    al = pd.read_csv(OUT / "allocation.csv")
    hi = int(al.delta.idxmax())
    x1 = pd.read_csv(OUT / "x1.csv").iloc[0]
    x1_nt, x1_nc = int(x1.n_t), int(x1.n_c)
    d = pd.read_csv(OUT / "market_dept.csv", dtype={"dep": str})
    d = d[~d.dep.str.startswith("97")][["dep", "departement", "eco_active", "income_ae", "immat_4q", "density_km2", "value_rank"]].round(1)
    geo = json.loads((PUBLIC / "departements_simplified.geojson").read_text(encoding="utf-8"))
    geo["features"] = [f for f in geo["features"] if not f["properties"]["code"].startswith("97")]
    data = {"curves": c.to_dict("records"), "weeks_per_month": WEEKS_PER_MONTH, "hi": hi,
            "map": {"rows": d.to_dict("records"), "geo": geo}}
    tag = lambda t: {"pub": '<span class="tag pub">PUBLIC DATA</span>', "sim": '<span class="tag sim">SIMULATED</span>',  # noqa: E731
                     "ill": '<span class="tag ill">ILLUSTRATIVE</span>'}[t]
    body = f"""
<h3>1 · Budget allocator: where does the next euro go?</h3>
<div class="row">
 <div class="card"><h2>Response curves: incremental sign-ups per month by channel {tag('sim')}</h2><div id="p_curves" class="plot" style="height:380px"></div>
  <p>Hollow = your split, solid = best split of the same total. Curves are simulated (diminishing returns, Hill shape), anchored on the geo tests of the report.</p></div>
 <div class="card"><h2>Monthly budget by channel {tag('sim')}</h2><div id="sliders"></div>
  <button class="act" id="b_opt">Optimal split</button><button class="act ghost" id="b_reset">Reset to today</button>
  <div class="out"><div>Total budget<b id="o_budget"></b></div><div>Incremental sign-ups<b id="o_inc"></b></div><div>Cost per incremental<b id="o_cpa"></b></div></div>
  <p id="o_opt"></p><table id="t_alloc"></table><p>AI search has no paid lever: it is measured with a monthly question panel (see docs/channel_playbook.md).</p></div>
</div>
<h3>2 · Experiment calculator: how long must a test run?</h3>
<div class="row calc">
 <div class="card"><h2>Sample size and duration {tag('ill')}</h2>
  <label>Baseline conversion, %<input id="c_base" type="number" value="4" step="0.1" min="0.1"></label>
  <label>Minimum detectable effect, relative %<input id="c_mde" type="number" value="8" step="1" min="1"></label>
  <label>Power<select id="c_pow"><option value="0.8" selected>80%</option><option value="0.9">90%</option></select></label>
  <label>Significance level, %<input id="c_alpha" type="number" value="5" step="1" min="1"></label>
  <label>Visitors per week (both arms)<input id="c_traffic" type="number" value="26000" step="1000" min="100"></label>
  <div class="out"><div>Sample size<b id="c_n"></b></div><div style="grid-column: span 2">Duration<b id="c_w"></b></div></div>
  <p>Two-sided z-test on two proportions, 50/50 split.</p></div>
 <div class="card"><h2>Sample-ratio mismatch check {tag('ill')}</h2>
  <label>Units in test<input id="c_nt" type="number" value="{x1_nt}"></label>
  <label>Units in control<input id="c_nc" type="number" value="{x1_nc}"></label>
  <div id="c_srm" class="alert"></div>
  <p>Pre-filled with the simulated landing-page test X1 of the report. Chi-square, 1 degree of freedom; alert below p = 0.001.</p></div>
</div>
<h3>3 · Market map: where are the freelancers?</h3>
<div class="card map"><h2>Departements of metropolitan France {tag('pub')}</h2>
 <label style="font-size:13px; color:var(--muted)">Show <select id="m_var"><option value="eco_active">Active auto-entrepreneurs (Q4 2025)</option>
 <option value="income_ae">Average AE income (2025)</option><option value="immat_4q">Registrations, last 4 quarters</option>
 <option value="density_km2">Active AE per km²</option></select></label>
 <div id="p_map" class="plot" style="height:560px"></div>
 <p>URSSAF open data (ODbL) and Etalab boundaries (Licence Ouverte). Hover a departement for all numbers.</p></div>
"""
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>Growth planner · {TITLE}</title><style>{CSS}{EXTRA_CSS}</style></head><body><div class="wrap">'
            f'<h1>Freelancer growth planner</h1><p class="sub">Move the budget, size a test, explore the market. Market data are public; '
            f'channels, curves and tests are simulated and are not Alan data.</p>{body}<footer>{FOOT}</footer></div>'
            f'<script>{get_plotlyjs()}</script><script>const D = {json.dumps(data)};{JS}</script></body></html>')
    out = SITE / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"written site/dashboard/index.html {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
