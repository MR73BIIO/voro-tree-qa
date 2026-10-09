#!/usr/bin/env python3
"""voro-tree-qa M0 - measurement. Implements docs/M0_PREDICTION.md (committed before this file).

Definitions fixed before the run (this file is committed before the first run):
- Input: the WFS 1.1.0 point layer saved by R0 v3, data/raw/wfs11_standorte_*.json.
  Gate: SHA-256 must be 8c84839fdca98eaf740275b74850b857869b677cf1c3fe6743c4d44114cc4b09, else stop.
- Text compared after strip, case-insensitive. Empty = None or empty after strip.
- First / second word = baumnamelat.split() [0] / [1]; a missing word counts as mismatch.
- Measured = genauigkeit starts with "Eingemessen".
- Numbers: float(str(v).replace(",", ".")); a value that does not convert counts as empty.
- P3 base = trees with pflanzjahr >= 2022 and a crown value.
- P8: WGS84 -> LV95 (EPSG:2056) with geopandas to_crs; pairs i<j with distance < 0.50 m via STRtree dwithin.
- P11: share of crown == 8 among Bildschirmeingabe vs among Measured.
- Verdict per point, life verdict = worst point (REFUTED > NO DATA > CONFIRMED).
Usage (VPS): cd /root/voro-tree-qa && /root/gis_qa/.venv/bin/python m0/measure_m0.py
Writes results/m0_results.json and results/m0_results.md.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"
GATE = "8c84839fdca98eaf740275b74850b857869b677cf1c3fe6743c4d44114cc4b09"
N_EXPECTED = 81142


def txt(v):
    return "" if v is None else str(v).strip()


def num(v):
    try:
        return float(txt(v).replace(",", "."))
    except ValueError:
        return None


def pct(a, b):
    return round(100.0 * a / b, 2) if b else None


def measured(p):
    return txt(p.get("genauigkeit")).startswith("Eingemessen")


def load():
    files = sorted((ROOT / "data" / "raw").glob("wfs11_standorte_*.json"))
    for f in files:
        b = f.read_bytes()
        if hashlib.sha256(b).hexdigest() == GATE:
            return f, json.loads(b.decode("utf-8"))
    sys.exit(f"GATE: no file with sha256 {GATE} among {[x.name for x in files]}")


def close_pairs(feats):
    import geopandas as gpd
    from shapely.geometry import shape
    geoms = [shape(f["geometry"]) for f in feats]
    g = gpd.GeoSeries(geoms, crs=4326).to_crs(2056)
    left, right = g.sindex.query(g, predicate="dwithin", distance=0.5)
    pairs = sorted({(int(a), int(b)) for a, b in zip(left, right) if a < b})
    exact = sum(1 for a, b in pairs if g.iloc[a].distance(g.iloc[b]) == 0)
    return pairs, exact


def main():
    path, d = load()
    feats = d["features"]
    P = [f.get("properties") or {} for f in feats]
    n = len(P)
    rows = []

    def add(pid, what, value, pred, ok):
        rows.append({"id": pid, "measured": what, "value": value, "prediction": pred,
                     "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED")})

    # P1 genus vs first word
    mism1 = []
    for p in P:
        w = txt(p.get("baumnamelat")).split()
        if not w or w[0].lower() != txt(p.get("baumgattunglat")).lower():
            mism1.append((txt(p.get("baumnummer")), txt(p.get("baumgattunglat")), txt(p.get("baumnamelat"))))
    m1 = n - len(mism1)
    add("P1", "baumgattunglat = first word of baumnamelat", f"{m1}/{n} ({pct(m1, n)} %), mismatches {len(mism1)}",
        ">= 98.0 % and >= 1 mismatch", pct(m1, n) >= 98.0 and len(mism1) >= 1)

    # P2 species vs second word
    base2 = [p for p in P if txt(p.get("baumartlat"))]
    mism2 = []
    for p in base2:
        w = txt(p.get("baumnamelat")).split()
        if len(w) < 2 or w[1].lower() != txt(p.get("baumartlat")).lower():
            mism2.append((txt(p.get("baumnummer")), txt(p.get("baumartlat")), txt(p.get("baumnamelat"))))
    m2 = len(base2) - len(mism2)
    add("P2", "baumartlat = second word of baumnamelat (baumartlat filled)",
        f"{m2}/{len(base2)} ({pct(m2, len(base2))} %)", ">= 95.0 %",
        None if not base2 else pct(m2, len(base2)) >= 95.0)

    # P3 young trees with large crown
    young = [p for p in P if (num(p.get("pflanzjahr")) or 0) >= 2022 and num(p.get("kronendurchmesser")) is not None]
    big = [p for p in young if num(p.get("kronendurchmesser")) >= 8]
    add("P3", "pflanzjahr >= 2022: share with crown >= 8 m", f"{len(big)}/{len(young)} ({pct(len(big), len(young))} %)",
        ">= 5.0 %", None if not young else pct(len(big), len(young)) >= 5.0)

    # P4, P5 accuracy by category
    def share_measured(sub):
        k = sum(1 for p in sub if measured(p))
        return k, len(sub), pct(k, len(sub))
    street = [p for p in P if txt(p.get("kategorie")) == "Strassenbaum"]
    park = [p for p in P if txt(p.get("kategorie")) == "Parkbaum"]
    k, t, s = share_measured(street)
    add("P4a", "Strassenbaum: share Measured", f"{k}/{t} ({s} %)", ">= 70.0 %", None if not t else s >= 70.0)
    k, t, s = share_measured(park)
    add("P4b", "Parkbaum: share Measured", f"{k}/{t} ({s} %)", "<= 30.0 %", None if not t else s <= 30.0)
    s01 = [p for p in street if (num(p.get("pflanzjahr")) or 0) >= 2001]
    k, t, s = share_measured(s01)
    add("P5", "Strassenbaum, pflanzjahr >= 2001: share Measured", f"{k}/{t} ({s} %)", ">= 85.0 %",
        None if not t else s >= 85.0)

    # P6 kategorie vs status
    st_set = {"Strassenbaum", "Strassenbaum (A)"}
    mism6 = [(txt(p.get("baumnummer")), txt(p.get("kategorie")), txt(p.get("status"))) for p in P
             if (txt(p.get("kategorie")) == "Strassenbaum") != (txt(p.get("status")) in st_set)]
    add("P6", "kategorie Strassenbaum <=> status Strassenbaum / Strassenbaum (A)", f"{len(mism6)} mismatches",
        "0", len(mism6) == 0)

    # P7 baumtyp vs baumtyptext
    m = defaultdict(Counter)
    for p in P:
        m[txt(p.get("baumtyp"))][txt(p.get("baumtyptext"))] += 1
    one_text = all(len(v) == 1 for c, v in m.items() if c)
    t3 = set(m.get("3", {})) | set()
    t4 = set(m.get("4", {}))
    shared = len(t3) == 1 and t3 == t4
    empty_ok = set(m.get("", {})) <= {"nicht zugeordnet"} and bool(m.get(""))
    mapping = {c: dict(v) for c, v in sorted(m.items())}
    add("P7", "baumtyp -> one text; 3 and 4 share one text; empty -> 'nicht zugeordnet'",
        f"one text {one_text}, 3=4 {shared}, empty ok {empty_ok}", "all true", one_text and shared and empty_ok)

    # P8 close pairs
    pairs, exact = close_pairs(feats)
    add("P8", "close pairs < 0.50 m (LV95)", f"{len(pairs)} pairs ({exact} at the same point)", "1 ... 811",
        1 <= len(pairs) <= 811)

    # P9 old planting years
    old = sorted(int(num(p.get("pflanzjahr"))) for p in P if num(p.get("pflanzjahr")) is not None
                 and num(p.get("pflanzjahr")) < 1850)
    add("P9", "pflanzjahr < 1850", f"{len(old)} trees, years {sorted(Counter(old).items())[:10]}", "1 ... 100",
        1 <= len(old) <= 100)

    # P10 identifiers
    eq = sum(1 for p in P if txt(p.get("baumnummer")) == txt(p.get("poi_id")))
    add("P10a", "baumnummer = poi_id", f"{eq}/{n}", f"{N_EXPECTED}/{N_EXPECTED}", eq == n == N_EXPECTED)
    nn = sum(1 for p in P if txt(p.get("baumnummer")).startswith("nn-"))
    add("P10b", "share of baumnummer starting 'nn-'", f"{nn}/{n} ({pct(nn, n)} %)", ">= 1.0 %", pct(nn, n) >= 1.0)

    # P11 crown 8 m by accuracy class
    bild = [p for p in P if txt(p.get("genauigkeit")) == "Bildschirmeingabe"]
    meas = [p for p in P if measured(p)]
    s_b = pct(sum(1 for p in bild if num(p.get("kronendurchmesser")) == 8), len(bild))
    s_m = pct(sum(1 for p in meas if num(p.get("kronendurchmesser")) == 8), len(meas))
    add("P11", "crown exactly 8 m: Bildschirmeingabe vs Measured", f"{s_b} % vs {s_m} %",
        "Bildschirmeingabe higher", None if s_b is None or s_m is None else s_b > s_m)

    order = {"CONFIRMED": 0, "NO DATA": 1, "REFUTED": 2}
    worst = max(rows, key=lambda r: order[r["verdict"]])["verdict"]
    nconf = sum(r["verdict"] == "CONFIRMED" for r in rows)
    extra = {"input": path.name, "features": n, "baumtyp_mapping": mapping,
             "p1_mismatches": mism1[:200], "p2_mismatches_first50": mism2[:50],
             "p6_mismatches": mism6[:50], "p9_years": old,
             "p8_pairs_first50": [[txt(P[a].get("baumnummer")), txt(P[b].get("baumnummer"))] for a, b in pairs[:50]],
             "genauigkeit_by_kategorie": {c: dict(Counter(txt(p.get("genauigkeit")) for p in P
                                                         if txt(p.get("kategorie")) == c)) for c in ("Strassenbaum", "Parkbaum")}}
    RES.mkdir(exist_ok=True)
    out = {"rows": rows, "life_verdict": worst, "confirmed": f"{nconf}/{len(rows)}", **extra}
    (RES / "m0_results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["| # | Measured | Value | Prediction | Verdict |", "|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['measured']} | {r['value']} | {r['prediction']} | {r['verdict']} |" for r in rows]
    md.append(f"\nLife verdict (worst point): {worst} ({nconf}/{len(rows)} CONFIRMED)")
    (RES / "m0_results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\ninput {path.name}, {n} features")
    print(f"baumtyp mapping: {mapping}")
    print(f"P1 mismatches ({len(mism1)}), first 15: {mism1[:15]}")
    print(f"P9 years: {sorted(Counter(old).items())}")
    print(f"genauigkeit by kategorie: {extra['genauigkeit_by_kategorie']}")


if __name__ == "__main__":
    main()
