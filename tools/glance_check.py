"""Glance check for a report PDF: can each page be read in 10 seconds?

Per page (text read from the PDF with PyMuPDF spans: size and position):
  * words: counted outside the page title, the subtitle (the line block right under the title), the footer band,
    source tags (PUBLIC DATA / SIMULATED ...) and big numbers (spans larger than the title, e.g. KPI values);
    a word = a whitespace token containing a letter. FAIL above --max-words (pages 0 to n-2) or --max-words-last (last page);
  * charts: number of images; FAIL if a page 0 to n-2 has fewer than --min-charts;
  * chart area: image area / content area (between the subtitle and the footer, across the used width);
    FAIL below --min-area on pages 0 to n-2;
  * page count: FAIL if not --pages.
Then renders every page to PNG (60 dpi) in --preview (default: <site>/_preview, never published) so a person (or the
assistant) can look at each page and simplify what does not read in 10 seconds.
Usage:  python tools/glance_check.py site/report/<name>.pdf
Exit code 1 on any FAIL.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pymupdf as fitz

TAGS = {"PUBLIC DATA", "SIMULATED", "PUBLIC + SIMULATED", "ILLUSTRATIVE", "REAL", "PUBLIC"}


def analyse(page) -> dict:
    W, H = page.rect.width, page.rect.height
    spans = [s for b in page.get_text("dict")["blocks"] if b.get("type") == 0
             for ln in b["lines"] for s in ln["spans"] if s["text"].strip()]
    top = [s for s in spans if s["bbox"][1] < 0.15 * H]
    t_size = min(top, key=lambda s: s["bbox"][1])["size"] if top else 0     # the title is the first line of the page
    title = [s for s in top if abs(s["size"] - t_size) < 0.3]
    cut = (max(s["bbox"][3] for s in title) + 1.2 * t_size) if title else 0      # end of the subtitle zone
    foot = 0.965 * H
    body = [s for s in spans if s["bbox"][1] >= cut and s["bbox"][1] < foot and s["text"].strip().upper() not in TAGS
            and s["size"] <= t_size + 0.3 and s not in title]
    words = sum(1 for s in body for tok in s["text"].split() if re.search(r"[A-Za-z]", tok))
    imgs = [i["bbox"] for i in page.get_image_info()]
    boxes = [s["bbox"] for s in spans if cut <= s["bbox"][1] < foot] + [b for b in imgs]
    x0 = min((b[0] for b in boxes), default=0); x1 = max((b[2] for b in boxes), default=W)
    content = max((x1 - x0) * (foot - cut), 1)
    area = sum(max(0, min(b[2], x1) - max(b[0], x0)) * max(0, min(b[3], foot) - max(b[1], cut)) for b in imgs)
    return {"words": words, "charts": len(imgs), "area": area / content}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--max-words", type=int, default=90)
    ap.add_argument("--max-words-last", type=int, default=250)
    ap.add_argument("--min-area", type=float, default=0.70)
    ap.add_argument("--min-charts", type=int, default=3)
    ap.add_argument("--pages", type=int, default=7)
    ap.add_argument("--preview", default=None)
    ap.add_argument("--dpi", type=int, default=60)
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    pdf = Path(a.pdf).resolve()
    doc = fitz.open(pdf)
    fails = []
    if len(doc) != a.pages:
        fails.append(f"{len(doc)} pages, expected {a.pages}")
    last = len(doc) - 1
    print(f"{'page':>4} {'words':>6} {'charts':>6} {'area':>6}")
    for i, pg in enumerate(doc):
        r = analyse(pg)
        lim = a.max_words_last if i == last else a.max_words
        flags = []
        if r["words"] > lim:
            flags.append(f"words {r['words']} > {lim}")
        if i < last and r["charts"] < a.min_charts:
            flags.append(f"charts {r['charts']} < {a.min_charts}")
        if i < last and r["area"] < a.min_area:
            flags.append(f"chart area {100 * r['area']:.0f}% < {100 * a.min_area:.0f}%")
        fails += [f"page {i}: {f}" for f in flags]
        print(f"{i:>4} {r['words']:>6} {r['charts']:>6} {100 * r['area']:>5.0f}%  {'FAIL ' + '; '.join(flags) if flags else 'ok'}")
    out = Path(a.preview) if a.preview else pdf.parent.parent / "_preview"
    out.mkdir(parents=True, exist_ok=True)
    for i, pg in enumerate(doc):
        pg.get_pixmap(dpi=a.dpi).save(out / f"page_{i}.png")
    print(f"previews: {out} (look at each page: is the message readable in 10 seconds?)")
    print(f"{len(fails)} FAIL" + ("".join(f"\n  FAIL {f}" for f in fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
