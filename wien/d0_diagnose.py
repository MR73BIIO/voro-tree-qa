#!/usr/bin/env python3
"""
voro-tree-qa · Wien · D0 (diagnosis after M0)

Describes what lies behind the M0 verdicts. Changes no verdict:
RESULTS.json from commit be2a9c9 stays as it is.

Usage:  python3 wien/d0_diagnose.py <report.txt>
Reads:  wien/data/*.json (M0 cache; fetched again if missing)
Writes: wien/d0/DIAGNOSIS.json
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from m0_measure import DISTRICTS, TREES, RE_LEAD, fetch, in_geom, num, s  # noqa: E402

D0 = HERE / "d0"


def shape(text, n=14):
    """Digits -> 9, letters -> a, keeps punctuation: shows the format, not the content."""
    t = re.sub(r"\d", "9", text[:n])
    return re.sub(r"[^\W\d_]", "a", t)


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: d0_diagnose.py <report.txt>")
    out = Path(sys.argv[1])
    D0.mkdir(parents=True, exist_ok=True)
    log = []
    trees = fetch(TREES, "baumkatogd.json", log)
    dist = fetch(DISTRICTS, "bezirksgrenzen.json", log)
    P = [f.get("properties") or {} for f in trees]
    d = {}

    # P10: format of OBJEKT_STRASSE vs real district mismatch
    no_lead, real_mismatch, fail_samples = Counter(), Counter(), []
    lead_ok = lead_bad = lead_none = 0
    for p in P:
        b, os_ = num(p.get("BEZIRK")), s(p.get("OBJEKT_STRASSE"))
        m = RE_LEAD.match(os_)
        if not m:
            lead_none += 1
            no_lead[shape(os_)] += 1
            if len(fail_samples) < 25:
                fail_samples.append(os_)
        elif b is not None and int(m.group(1)) == int(b):
            lead_ok += 1
        else:
            lead_bad += 1
            real_mismatch[(None if b is None else int(b), int(m.group(1)))] += 1
    d["P10"] = {"lead_number_matches": lead_ok, "no_lead_number": lead_none,
                "lead_number_differs": lead_bad,
                "no_lead_shapes_top15": no_lead.most_common(15),
                "no_lead_samples": fail_samples,
                "differs_pairs_BEZIRK_vs_lead_top15": [[list(k), v] for k, v in real_mismatch.most_common(15)]}

    # P03: what the keyword hits really are
    kw = Counter(s(p.get("GATTUNG_ART")) for p in P
                 if any(k in s(p.get("GATTUNG_ART")).lower() for k in ("leer", "pflanzstandort", "baumgruppe")))
    d["P03"] = {"values_top30": kw.most_common(30), "distinct": len(kw)}

    # P09: crown code/text pairs
    pairs = Counter((s(p.get("KRONENDURCHMESSER")), s(p.get("KRONENDURCHMESSER_TXT"))) for p in P)
    d["P09"] = {"crown_code_text_pairs": [[list(k), v] for k, v in sorted(pairs.items())]}

    # P11: points outside their own district — where are they?
    key = next(k for k in ("BEZNR", "BEZ") if k in (dist[0].get("properties") or {}))
    polys = {int(num(x["properties"][key])): x["geometry"] for x in dist}
    moved, outside_gg = Counter(), Counter()
    for f, p in zip(trees, P):
        b, g = num(p.get("BEZIRK")), f.get("geometry")
        if b is None or not g or int(b) not in polys:
            moved[("no BEZIRK/geometry", None)] += 1
            continue
        x, y = g["coordinates"][:2]
        if in_geom(x, y, polys[int(b)]):
            continue
        actual = next((k for k, gm in polys.items() if in_geom(x, y, gm)), "outside Wien")
        moved[(int(b), actual)] += 1
        outside_gg[s(p.get("GEBIETSGRUPPE"))] += 1
    d["P11"] = {"BEZIRK_to_actual_top20": [[list(k), v] for k, v in moved.most_common(20)],
                "GEBIETSGRUPPE_top10": outside_gg.most_common(10)}

    # P07: young trees with thick trunks
    young = [p for p in P if (num(p.get("PFLANZJAHR")) or 0) >= 2016 and (num(p.get("STAMMUMFANG")) or 0) >= 80]
    d["P07"] = {"n": len(young),
                "species_top10": Counter(s(p.get("GATTUNG_ART")) for p in young).most_common(10),
                "pflanzjahr": sorted(Counter(int(num(p.get("PFLANZJAHR"))) for p in young).items()),
                "stammumfang_cm_buckets": sorted(Counter(int(num(p.get("STAMMUMFANG")) // 20 * 20)
                                                         for p in young).items())}

    # P06: last digit of planting years, before 2006 vs from 2006
    def digits(cond):
        c = Counter(int(v) % 10 for v in (num(p.get("PFLANZJAHR")) for p in P) if v and cond(v))
        n = sum(c.values())
        return {"n": n, "last_digit_share": {k: round(c[k] / n, 4) for k in range(10)} if n else {}}
    d["P06"] = {"before_2006": digits(lambda v: 1 <= v < 2006), "from_2006": digits(lambda v: v >= 2006)}

    # P12: values not matching 'Latin (German)'
    from m0_measure import RE_SPECIES
    d["P12"] = {"non_matching_top20": Counter(s(p.get("GATTUNG_ART")) for p in P
                                              if not RE_SPECIES.match(s(p.get("GATTUNG_ART")).strip())).most_common(20)}

    result = {"run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "based_on": "wien/m0/RESULTS.json (commit be2a9c9); verdicts unchanged",
              "fetch_log": log, "diagnosis": d}
    body = json.dumps(result, ensure_ascii=False, indent=1)
    (D0 / "DIAGNOSIS.json").write_text(body, encoding="utf-8")
    out.write_text(body, encoding="utf-8")
    print(f"Diagnosis written: {out}")


if __name__ == "__main__":
    main()
