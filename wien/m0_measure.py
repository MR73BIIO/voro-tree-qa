#!/usr/bin/env python3
"""
voro-tree-qa · Wien · M0 (measurement)

Measures P01–P12 exactly as frozen in wien/PREDICTIONS.md (commit 7165d7c).
Thresholds are hard-coded from that file and are not changed after the run.

Usage:  python3 wien/m0_measure.py <report.txt>
Writes: wien/m0/RESULTS.json (committed), wien/data/*.json (raw, not committed)
Stdlib only.
"""
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data.wien.gv.at/daten/geo"
TREES = "ogdwien:BAUMKATOGD"
DISTRICTS = "ogdwien:BEZIRKSGRENZEOGD"
HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
M0 = HERE / "m0"
UA = {"User-Agent": "voro-tree-qa M0 (MR73BIIO)"}


# ---------- fetch ----------

def get(params, timeout=900):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def hits(type_name):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(get({"service": "WFS", "request": "GetFeature", "version": "1.1.0",
                              "typeName": type_name, "resultType": "hits"}, timeout=180))
    return int(root.get("numberOfFeatures") or root.get("numberMatched"))


def fetch(type_name, cache_name, log):
    cache = DATA / cache_name
    if cache.exists():
        feats = json.loads(cache.read_text(encoding="utf-8"))["features"]
        log.append(f"{type_name}: {len(feats)} features from cache {cache.name}")
        return feats
    expected = hits(type_name)
    feats = json.loads(get({"service": "WFS", "request": "GetFeature", "version": "1.1.0",
                            "typeName": type_name, "srsName": "EPSG:4326",
                            "outputFormat": "json"}))["features"]
    if len(feats) < expected:  # server capped the response -> page with WFS 2.0
        log.append(f"{type_name}: single request gave {len(feats)} of {expected}, paging")
        by_id, start, step = {}, 0, 50000
        while start < expected:
            page = json.loads(get({"service": "WFS", "request": "GetFeature", "version": "2.0.0",
                                   "typeNames": type_name, "srsName": "EPSG:4326",
                                   "outputFormat": "json", "sortBy": "OBJECTID",
                                   "count": str(step), "startIndex": str(start)}))["features"]
            if not page:
                break
            for f in page:
                by_id[f["properties"].get("OBJECTID", id(f))] = f
            start += step
        feats = list(by_id.values())
    DATA.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"features": feats}, ensure_ascii=False), encoding="utf-8")
    log.append(f"{type_name}: hits={expected}, fetched={len(feats)}")
    return feats


# ---------- geometry ----------

def in_ring(x, y, ring):
    inside, j = False, len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def in_geom(x, y, geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    for poly in polys:
        if in_ring(x, y, poly[0]) and not any(in_ring(x, y, h) for h in poly[1:]):
            return True
    return False


# ---------- helpers ----------

def num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None


def s(v):
    return "" if v is None else str(v)


def share(a, b):
    return a / b if b else None


def pct(x):
    return "n/a" if x is None else f"{100 * x:.2f} %"


RE_LEAD = re.compile(r"^\s*(\d+)\.")
RE_NUM = re.compile(r"(\d+)")
RE_SPECIES = re.compile(r"^[A-Z][a-z-]+(\s.+?)?\s\([^()]+\)$")


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: m0_measure.py <report.txt>")
    out = Path(sys.argv[1])
    M0.mkdir(parents=True, exist_ok=True)
    log = []

    trees = fetch(TREES, "baumkatogd.json", log)
    P = [f.get("properties") or {} for f in trees]
    N = len(P)

    res = []

    def rec(pid, measure, value, threshold, ok, extra=None):
        res.append({"id": pid, "measure": measure, "value": value, "threshold": threshold,
                    "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED"),
                    **({"extra": extra} if extra else {})})

    # P01
    c = sum(1 for p in P if any(k in s(p.get("GEBIETSGRUPPE")).lower() for k in ("straße", "strasse")))
    rec("P01", "GEBIETSGRUPPE contains straße/strasse", c, ">= 99000", c >= 99000)

    # P02
    c = sum(1 for p in P if p.get("DATENFUEHRUNG") == "magistrat")
    rec("P02", "share DATENFUEHRUNG == 'magistrat'", share(c, N), ">= 0.90", share(c, N) >= 0.90,
        {"count": c})

    # P03
    c = sum(1 for p in P if any(k in s(p.get("GATTUNG_ART")).lower()
                                for k in ("leer", "pflanzstandort", "baumgruppe")))
    rec("P03", "GATTUNG_ART contains leer/pflanzstandort/baumgruppe", c, ">= 1000", c >= 1000)

    # P04
    pj = [num(p.get("PFLANZJAHR")) for p in P]
    c0 = sum(1 for v in pj if v == 0)
    rec("P04", "share PFLANZJAHR == 0", share(c0, N), ">= 0.50", share(c0, N) >= 0.50,
        {"count": c0, "null": sum(1 for v in pj if v is None)})

    # P05
    agree = sum(1 for p, v in zip(P, pj)
                if (v == 0) == (s(p.get("PFLANZJAHR_TXT")).strip() == "nicht definiert"))
    rec("P05", "PFLANZJAHR==0 <=> PFLANZJAHR_TXT=='nicht definiert'", share(agree, N), ">= 0.999",
        share(agree, N) >= 0.999, {"disagree": N - agree})

    # P06
    old = [int(v) for v in pj if v is not None and 1 <= v < 2006]
    c = sum(1 for y in old if y % 5 == 0)
    rec("P06", "1<=PFLANZJAHR<2006: share of years ending 0 or 5", share(c, len(old)), ">= 0.30",
        None if not old else share(c, len(old)) >= 0.30, {"n": len(old), "count": c})

    # P07
    young = [num(p.get("STAMMUMFANG")) for p, v in zip(P, pj) if v is not None and v >= 2016]
    c = sum(1 for u in young if u is not None and u >= 80)
    rec("P07", "PFLANZJAHR>=2016: share STAMMUMFANG>=80 cm", share(c, len(young)), "<= 0.005",
        None if not young else share(c, len(young)) <= 0.005, {"n": len(young), "count": c})

    # P08
    su = [num(p.get("STAMMUMFANG")) for p in P]
    c = sum(1 for u in su if u is None or u == 0)
    rec("P08", "share STAMMUMFANG == 0 or null", share(c, N), "<= 0.10", share(c, N) <= 0.10,
        {"count": c})

    # P09
    # Interpretation fixed before the run: if the text holds no number, the record agrees
    # only when the numeric field is 0 or null.
    def su_agree(p):
        u, m = num(p.get("STAMMUMFANG")), RE_NUM.search(s(p.get("STAMMUMFANG_TXT")))
        return (u is not None and int(u) == int(m.group(1))) if m else (u is None or u == 0)
    a = sum(1 for p in P if su_agree(p))
    maps = {}
    for code, txt in (("BAUMHOEHE", "BAUMHOEHE_TXT"), ("KRONENDURCHMESSER", "KRONENDURCHMESSER_TXT")):
        m = defaultdict(set)
        for p in P:
            m[s(p.get(code))].add(s(p.get(txt)))
        maps[code] = {k: sorted(v) for k, v in sorted(m.items())}
    one_to_one = all(len(v) == 1 for mm in maps.values() for v in mm.values())
    rec("P09", "STAMMUMFANG == number in TXT; height/crown code->text 1:1",
        {"stammumfang_agree": share(a, N), "codes_1to1": one_to_one}, ">= 0.995 and 1:1",
        share(a, N) >= 0.995 and one_to_one, {"code_maps": maps})

    # P10
    def lead(p):
        m = RE_LEAD.match(s(p.get("OBJEKT_STRASSE")))
        return int(m.group(1)) if m else None
    a = sum(1 for p in P if num(p.get("BEZIRK")) is not None and lead(p) == int(num(p.get("BEZIRK"))))
    rec("P10", "BEZIRK == leading number of OBJEKT_STRASSE", share(a, N), ">= 0.99",
        share(a, N) >= 0.99, {"disagree": N - a})

    # P11
    try:
        dist = fetch(DISTRICTS, "bezirksgrenzen.json", log)
        key = next(k for k in ("BEZNR", "BEZ") if k in (dist[0].get("properties") or {}))
        polys = {int(num(d["properties"][key])): d["geometry"] for d in dist}
        a = 0
        for f, p in zip(trees, P):
            b, g = num(p.get("BEZIRK")), f.get("geometry")
            if b is not None and g and int(b) in polys:
                x, y = g["coordinates"][:2]
                a += in_geom(x, y, polys[int(b)])
        rec("P11", "point inside own district polygon", share(a, N), ">= 0.98",
            share(a, N) >= 0.98, {"disagree": N - a, "district_key": key, "districts": len(polys)})
    except Exception as e:
        rec("P11", "point inside own district polygon", None, ">= 0.98", None,
            {"error": f"{type(e).__name__}: {e}"})

    # P12
    a = sum(1 for p in P if RE_SPECIES.match(s(p.get("GATTUNG_ART")).strip()))
    rec("P12", "GATTUNG_ART matches 'Latin (German)'", share(a, N), ">= 0.95", share(a, N) >= 0.95,
        {"non_matching": N - a})

    # Description after measuring (not scored)
    desc = {
        "records": N,
        "DATENFUEHRUNG": Counter(s(p.get("DATENFUEHRUNG")) for p in P).most_common(),
        "GEBIETSGRUPPE_top25": Counter(s(p.get("GEBIETSGRUPPE")) for p in P).most_common(25),
        "PFLANZJAHR_TXT_non_numeric": Counter(s(p.get("PFLANZJAHR_TXT")) for p in P
                                              if not RE_NUM.search(s(p.get("PFLANZJAHR_TXT")))).most_common(),
    }

    pred = (HERE / "PREDICTIONS.md").read_bytes()
    results = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "source": f"{BASE} {TREES}", "predictions_sha256": hashlib.sha256(pred).hexdigest(),
               "fetch_log": log, "results": res, "description_not_scored": desc}
    body = json.dumps(results, ensure_ascii=False, indent=2)
    (M0 / "RESULTS.json").write_text(body, encoding="utf-8")

    conf = sum(r["verdict"] == "CONFIRMED" for r in res)
    lines = ["voro-tree-qa · Wien · M0", f"Run (UTC): {results['run_utc']}",
             f"Records: {N}", *log,
             f"PREDICTIONS.md sha256: {results['predictions_sha256']}",
             f"RESULTS.json  sha256: {hashlib.sha256(body.encode('utf-8')).hexdigest()}", ""]
    for r in res:
        v = r["value"]
        vs = ", ".join(f"{k}={pct(x) if isinstance(x, float) else x}" for k, x in v.items()) \
            if isinstance(v, dict) else (pct(v) if isinstance(v, float) else v)
        lines.append(f"{r['id']}  {r['verdict']:<9}  {vs}  (threshold {r['threshold']})  {r['measure']}")
        for k, x in (r.get("extra") or {}).items():
            if k != "code_maps":
                lines.append(f"       {k}: {x}")
    lines += ["", f"SUMMARY: {conf} CONFIRMED / {len(res)}", "",
              "== P09 code maps ==", json.dumps(next(r for r in res if r['id'] == 'P09')["extra"]["code_maps"],
                                                  ensure_ascii=False, indent=1),
              "", "== Description after measuring (not scored) ==",
              json.dumps(desc, ensure_ascii=False, indent=1)]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{conf}/{len(res)} confirmed. Report: {out}")


if __name__ == "__main__":
    main()
