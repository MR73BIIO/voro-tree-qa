#!/usr/bin/env python3
"""voro-tree-qa - social preview image (1280 x 640) from the real data.

Not a life: no prediction, no verdict. Every number on the image is computed here from the
same input as M0 (SHA-256 gate below); nothing is typed by hand.
- Input: data/raw/wfs11_standorte_*.json with sha256 8c84839f...59fc0f1 (else stop).
- Points: lon/lat as given (WGS84), x scaled by cos(mean latitude) so the city is not stretched.
- Colour: surveyed (genauigkeit starts with "Eingemessen"), screen-entered ("Bildschirmeingabe"), other.
- Numbers: trees; share surveyed; share of crown exactly 8 m among screen-entered and among surveyed;
  trees planted >= 2022 with crown >= 8 m; records where genus != first word of the Latin name.
Usage (VPS): cd /root/voro-tree-qa && python3 viz/social_preview.py
Writes results/social_preview_en.png and results/social_preview_de.png.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GATE = "8c84839fdca98eaf740275b74850b857869b677cf1c3fe6743c4d44114cc4b09"
BG, PANEL, FG, MUTED = "#0d1117", "#161b22", "#e6edf3", "#8b949e"
C_SURV, C_SCREEN, C_OTHER, ACCENT = "#3fb950", "#d29922", "#6e7681", "#58a6ff"

TEXT = {
    "en": {"title": "Zurich tree register", "trees": "trees", "sub": "Checked against what the city says about its own data",
           "surv": "surveyed", "screen": "screen-entered", "other": "other / unknown",
           "f8": "crown exactly 8 m: {a} % screen-entered vs {b} % surveyed",
           "fy": "{y} trees planted since 2022 with a crown of 8 m or more",
           "fg": "{g} records: genus and Latin name disagree",
           "fs": "{s} % of positions surveyed",
           "foot": "voro-tree-qa · M0: 13 points written before the run, 11 confirmed · open data CC0, 9.10.2026"},
    "de": {"title": "Baumkataster Zürich", "trees": "Bäume", "sub": "Geprüft an dem, was die Stadt selbst über ihre Daten sagt",
           "surv": "eingemessen", "screen": "Bildschirmeingabe", "other": "andere / unbekannt",
           "f8": "Krone genau 8 m: {a} % Bildschirmeingabe vs {b} % eingemessen",
           "fy": "{y} Bäume seit 2022 gepflanzt, Krone 8 m oder mehr",
           "fg": "{g} Datensätze: Gattung und lateinischer Name widersprechen sich",
           "fs": "{s} % der Standorte eingemessen",
           "foot": "voro-tree-qa · M0: 13 Punkte vor dem Lauf festgelegt, 11 bestätigt · Open Data CC0, 9.10.2026"},
}


def txt(v):
    return "" if v is None else str(v).strip()


def num(v):
    try:
        return float(txt(v).replace(",", "."))
    except ValueError:
        return None


def fmt(n, lang):
    s = f"{n:,}"
    return s.replace(",", " ") if lang == "en" else s.replace(",", " ")


def pct(a, b, lang):
    s = f"{100.0 * a / b:.1f}"
    return s.replace(".", ",") if lang == "de" else s


def load():
    for f in sorted((ROOT / "data" / "raw").glob("wfs11_standorte_*.json")):
        b = f.read_bytes()
        if hashlib.sha256(b).hexdigest() == GATE:
            return json.loads(b.decode("utf-8"))
    sys.exit(f"GATE: no input with sha256 {GATE}")


def facts(feats):
    P = [f.get("properties") or {} for f in feats]
    n = len(P)
    surv = [p for p in P if txt(p.get("genauigkeit")).startswith("Eingemessen")]
    scr = [p for p in P if txt(p.get("genauigkeit")) == "Bildschirmeingabe"]
    eight = lambda sub: sum(1 for p in sub if num(p.get("kronendurchmesser")) == 8)
    young = sum(1 for p in P if (num(p.get("pflanzjahr")) or 0) >= 2022
                and (num(p.get("kronendurchmesser")) or 0) >= 8)
    genus = 0
    for p in P:
        w = txt(p.get("baumnamelat")).split()
        if not w or w[0].lower() != txt(p.get("baumgattunglat")).lower():
            genus += 1
    return {"n": n, "surv": len(surv), "scr": len(scr), "e_scr": eight(scr), "e_surv": eight(surv),
            "young": young, "genus": genus}


def draw(feats, F, lang, out):
    T = TEXT[lang]
    groups = {"surv": ([], []), "screen": ([], []), "other": ([], [])}
    lats = []
    for f in feats:
        c = (f.get("geometry") or {}).get("coordinates")
        if not c:
            continue
        g = txt((f.get("properties") or {}).get("genauigkeit"))
        k = "surv" if g.startswith("Eingemessen") else ("screen" if g == "Bildschirmeingabe" else "other")
        groups[k][0].append(c[0]); groups[k][1].append(c[1]); lats.append(c[1])
    k = math.cos(math.radians(sum(lats) / len(lats)))

    fig = plt.figure(figsize=(12.8, 6.4), dpi=100, facecolor=BG)
    ax = fig.add_axes([0.01, 0.02, 0.45, 0.96], facecolor=BG)
    for key, col, size, z in (("other", C_OTHER, 0.35, 1), ("screen", C_SCREEN, 0.35, 2), ("surv", C_SURV, 0.35, 3)):
        xs, ys = groups[key]
        ax.scatter([x * k for x in xs], ys, s=size, c=col, linewidths=0, alpha=0.85, zorder=z, rasterized=True)
    ax.set_aspect("equal"); ax.axis("off"); ax.margins(0.04)

    tx = 0.49
    fig.text(tx, 0.87, T["title"], color=FG, fontsize=30, fontweight="bold", va="top")
    big = fig.text(tx, 0.74, fmt(F["n"], lang), color=ACCENT, fontsize=54, fontweight="bold", va="top")
    fig.canvas.draw()
    bb = big.get_window_extent().transformed(fig.transFigure.inverted())
    fig.text(bb.x1 + 0.015, bb.y0 + 0.012, T["trees"], color=FG, fontsize=22, va="bottom")
    fig.text(tx, 0.585, T["sub"], color=MUTED, fontsize=12.5, va="top")
    lines = [T["f8"].format(a=pct(F["e_scr"], F["scr"], lang), b=pct(F["e_surv"], F["surv"], lang)),
             T["fy"].format(y=fmt(F["young"], lang)),
             T["fg"].format(g=fmt(F["genus"], lang)),
             T["fs"].format(s=pct(F["surv"], F["n"], lang))]
    y = 0.50
    for ln in lines:
        fig.text(tx, y, "■", color=ACCENT, fontsize=10, va="center")
        fig.text(tx + 0.02, y, ln, color=FG, fontsize=12.5, va="center")
        y -= 0.068
    ly = 0.185
    for key, col in (("surv", C_SURV), ("screen", C_SCREEN), ("other", C_OTHER)):
        fig.text(tx, ly, "●", color=col, fontsize=14, va="center")
        fig.text(tx + 0.02, ly, T[key], color=MUTED, fontsize=11.5, va="center")
        ly -= 0.045
    fig.text(tx, 0.045, T["foot"], color=MUTED, fontsize=8.8, va="center")
    fig.text(0.985, 0.955, "MR73BIIO · PL · DE · RU · EN", color=MUTED, fontsize=9.5, ha="right", va="center")
    fig.savefig(out, dpi=100, facecolor=BG)
    plt.close(fig)


def main():
    feats = load()["features"]
    F = facts(feats)
    (ROOT / "results").mkdir(exist_ok=True)
    for lang in ("en", "de"):
        out = ROOT / "results" / f"social_preview_{lang}.png"
        draw(feats, F, lang, out)
        print(f"{out.relative_to(ROOT)}  {out.stat().st_size} B")
    print(json.dumps(F))


if __name__ == "__main__":
    main()
