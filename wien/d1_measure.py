#!/usr/bin/env python3
"""
voro-tree-qa · Wien · D1 (diagnosis of M0 with predictions)

Measures H1–H4 exactly as frozen in wien/D1_PREDICTIONS.md (commit c376497).
M0 verdicts are not re-scored.

Usage:  python3 wien/d1_measure.py <report.txt>
Reads:  wien/data/*.json (M0 cache; fetched again if missing)
Writes: wien/d1/RESULTS.json
"""
import hashlib
import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m0_measure import DISTRICTS, TREES, RE_LEAD, fetch, num, s, pct  # noqa: E402

D1 = HERE / "d1"
KX = math.cos(math.radians(48.2)) * 111320.0  # metres per degree lon at 48.2° N
KY = 110540.0                                 # metres per degree lat


def to_m(lon, lat):
    return lon * KX, lat * KY


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def boundary_dist(lon, lat, geom):
    px, py = to_m(lon, lat)
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    best = float("inf")
    for poly in polys:
        for ring in poly:
            pts = [to_m(c[0], c[1]) for c in ring]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                best = min(best, seg_dist(px, py, ax, ay, bx, by))
    return best


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: d1_measure.py <report.txt>")
    out = Path(sys.argv[1])
    D1.mkdir(parents=True, exist_ok=True)
    log = []
    trees = fetch(TREES, "baumkatogd.json", log)
    dist = fetch(DISTRICTS, "bezirksgrenzen.json", log)
    P = [f.get("properties") or {} for f in trees]
    res = []

    def rec(hid, measure, value, threshold, ok, extra=None):
        res.append({"id": hid, "measure": measure, "value": value, "threshold": threshold,
                    "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED"),
                    **({"extra": extra} if extra else {})})

    # H1
    def share0(group):
        g = [p for p in P if s(p.get("GEBIETSGRUPPE")) == group]
        z = sum(1 for p in g if num(p.get("PFLANZJAHR")) == 0)
        return (z / len(g) if g else None), len(g), z
    s28, n28, z28 = share0("MA 28 - Straße, Grünanlage")
    s42, n42, z42 = share0("MA 42 - Parkanlage")
    diff = None if s28 is None or s42 is None else s42 - s28
    rec("H1", "share PFLANZJAHR=0: MA 42 minus MA 28", diff, ">= 0.10",
        None if diff is None else diff >= 0.10,
        {"MA28": {"n": n28, "zero": z28, "share": s28}, "MA42": {"n": n42, "zero": z42, "share": s42}})

    # H2 — same selection as D0: prefix present and not equal to BEZIRK
    key = next(k for k in ("BEZNR", "BEZ") if k in (dist[0].get("properties") or {}))
    polys = {int(num(x["properties"][key])): x["geometry"] for x in dist}
    dists, no_poly, no_geom = [], 0, 0
    for f, p in zip(trees, P):
        m = RE_LEAD.match(s(p.get("OBJEKT_STRASSE")))
        b = num(p.get("BEZIRK"))
        if not m or (b is not None and int(m.group(1)) == int(b)):
            continue
        lead, g = int(m.group(1)), f.get("geometry")
        if not g:
            no_geom += 1
        elif lead not in polys:
            no_poly += 1
        else:
            dists.append(boundary_dist(g["coordinates"][0], g["coordinates"][1], polys[lead]))
    n2 = len(dists) + no_poly + no_geom
    w200 = sum(1 for d in dists if d <= 200)
    sd = sorted(dists)
    rec("H2", "prefix != BEZIRK: share within 200 m of prefix-district boundary",
        w200 / n2 if n2 else None, ">= 0.80", None if not n2 else w200 / n2 >= 0.80,
        {"n": n2, "within_200m": w200, "no_geometry": no_geom, "prefix_not_a_district": no_poly,
         "median_m": round(sd[len(sd) // 2], 1) if sd else None,
         "p90_m": round(sd[int(len(sd) * 0.9)], 1) if sd else None,
         "max_m": round(sd[-1], 1) if sd else None})

    # H3
    young = [p for p in P if (num(p.get("PFLANZJAHR")) or 0) >= 2016 and (num(p.get("STAMMUMFANG")) or 0) >= 80]
    c = Counter(s(p.get("OBJEKT_STRASSE")) for p in young)
    top10 = sum(v for _, v in c.most_common(10))
    rec("H3", "PFLANZJAHR>=2016 & STAMMUMFANG>=80: share on top 10 OBJEKT_STRASSE",
        top10 / len(young) if young else None, ">= 0.50",
        None if not young else top10 / len(young) >= 0.50,
        {"n": len(young), "on_top10": top10, "distinct_sites": len(c), "top10": c.most_common(10)})

    # H4
    jb = [p for p in P if s(p.get("GATTUNG_ART")).strip() == "Jungbaum wird gepflanzt"]
    ok = sum(1 for p in jb if num(p.get("PFLANZJAHR")) == 0
             and (num(p.get("STAMMUMFANG")) is None or num(p.get("STAMMUMFANG")) == 0))
    rec("H4", "'Jungbaum wird gepflanzt': share with PFLANZJAHR=0 and STAMMUMFANG 0/null",
        ok / len(jb) if jb else None, ">= 0.95", None if not jb else ok / len(jb) >= 0.95,
        {"n": len(jb), "placeholder": ok,
         "pflanzjahr_top10": Counter(int(num(p.get("PFLANZJAHR")) or 0) for p in jb).most_common(10),
         "stammumfang_zero_or_null": sum(1 for p in jb if not num(p.get("STAMMUMFANG")))})

    pred = (HERE / "D1_PREDICTIONS.md").read_bytes()
    results = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "explains": "Puls #35 (M0 OUTCOME be2a9c9)",
               "predictions_sha256": hashlib.sha256(pred).hexdigest(),
               "fetch_log": log, "results": res}
    body = json.dumps(results, ensure_ascii=False, indent=2)
    (D1 / "RESULTS.json").write_text(body, encoding="utf-8")

    conf = sum(r["verdict"] == "CONFIRMED" for r in res)
    lines = ["voro-tree-qa · Wien · D1", f"Run (UTC): {results['run_utc']}", *log,
             f"D1_PREDICTIONS.md sha256: {results['predictions_sha256']}",
             f"RESULTS.json      sha256: {hashlib.sha256(body.encode('utf-8')).hexdigest()}", ""]
    for r in res:
        v = r["value"]
        lines.append(f"{r['id']}  {r['verdict']:<9}  {pct(v) if isinstance(v, float) else v}"
                     f"  (threshold {r['threshold']})  {r['measure']}")
        for k, x in (r.get("extra") or {}).items():
            lines.append(f"       {k}: {json.dumps(x, ensure_ascii=False)}")
    lines += ["", f"SUMMARY: {conf} CONFIRMED / {len(res)}"]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{conf}/{len(res)} confirmed. Report: {out}")


if __name__ == "__main__":
    main()
