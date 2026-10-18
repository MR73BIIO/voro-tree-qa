#!/usr/bin/env python3
"""BERLIN D1 - 7 punktow z berlin/D1_PREDICTION.md.

Liczy WYLACZNIE z zamrozonej kopii M0 (berlin/data/m0/), bez sieci.
Najpierw sprawdza: pieczec D1_PREDICTION.md (sha256) i harvest_sha256 kopii M0.
Uzycie:  python3 berlin/d1_diagnose.py
Wynik:   berlin/d1/DIAGNOSIS.json (do commita) + tabela na stdout,
         berlin/data/d1_examples.txt (przyklady, poza gitem).
Tylko biblioteka standardowa.
"""
import gzip
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
PRED = os.path.join(HERE, "D1_PREDICTION.md")
PREDICTION_SHA256 = os.environ.get(
    "BERLIN_D1_PRED_SHA", "f00cc349e2461a9d78122f434cc59918a1422d40517ea2d8dd0488716cce0187")
M0_HARVEST_SHA256 = os.environ.get(
    "BERLIN_M0_SHA", "844546b787250e62e2470e9596d2184abbd0a81275586a2c9da72731ec7ad25c")
DATA = os.path.join(HERE, "data", "m0")
META = os.path.join(DATA, "harvest_meta.json")
OUT = os.path.join(HERE, "d1")
EXAMPLES = os.path.join(HERE, "data", "d1_examples.txt")
LAYERS = ["baumbestand:anlagenbaeume", "baumbestand:strassenbaeume"]
SHORT = {"baumbestand:anlagenbaeume": "anlagen", "baumbestand:strassenbaeume": "strassen"}
EMPTY = {"", "-", "--"}


def die(msg):
    sys.exit("STOP: " + msg)


def empty(v, species=False):
    if v is None:
        return True
    s = str(v).strip()
    return s.lower() in EMPTY or (species and s.lower() == "unbekannt")


def num(v):
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?", s) else None


def street(s):
    s = re.sub(r"\([^)]*\)", " ", str(s).lower())
    s = re.sub(r"str\.", "straße", s)
    return re.sub(r"\s+", " ", s).strip()


def compact(s):
    return re.sub(r"[\s\-.]+", "", street(s))


def first_xy(g):
    c = (g or {}).get("coordinates")
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    return (c[0], c[1]) if isinstance(c, list) and len(c) >= 2 else None


def pct(a, n):
    return round(100.0 * a / n, 3) if n else None


def main():
    if not os.path.exists(PRED):
        die("brak berlin/D1_PREDICTION.md")
    ph = hashlib.sha256(open(PRED, "rb").read()).hexdigest()
    if ph != PREDICTION_SHA256:
        die(f"D1_PREDICTION.md ma inny sha256 ({ph[:12]}...) niz zapieczetowany")
    print(f"prediction_sha256: {ph}  (OK)")
    if not os.path.exists(META):
        die("brak kopii M0 (harvest_meta.json)")
    meta = json.load(open(META))
    h = hashlib.sha256()
    c = Counter()
    ex = defaultdict(list)
    obj_cmp = Counter()            # (layer,kennz) -> compared trees (Strassen)
    obj_mis = Counter()            # (layer,kennz) -> M0 mismatch trees
    other_pairs = Counter()
    obj_n = Counter()              # all trees per object
    obj_k0 = Counter()             # crown-0 trees per object
    bez_n, bez_k0 = Counter(), Counter()
    first_at = {}                  # point -> (layer, object)
    shared = defaultdict(list)     # point -> [(layer, object), ...] incl. first
    for layer in LAYERS:
        st = meta["layers"][layer]
        for k in range((st["matched"] + st["page"] - 1) // st["page"]):
            path = os.path.join(DATA, f"{SHORT[layer]}_{k:04d}.json.gz")
            with gzip.open(path, "rb") as fh:
                raw = fh.read()
            h.update(raw)
            for f in json.loads(raw)["features"]:
                p = f.get("properties") or {}
                if empty(p.get("pitid")) and empty(p.get("art_bot"), True) and empty(p.get("bezirk")):
                    continue                                   # shell (M0 definition)
                obj = (SHORT[layer], str(p.get("kennzeich") or "").strip() or "?")
                obj_n[obj] += 1
                kd0 = num(p.get("kronedurch")) == 0
                if kd0:
                    c["k0"] += 1
                    obj_k0[obj] += 1
                if not empty(p.get("bezirk")):
                    b = str(p["bezirk"]).strip()
                    bez_n[b] += 1
                    bez_k0[b] += kd0
                if layer.endswith("strassenbaeume") and not empty(p.get("namenr")) and not empty(p.get("strname")):
                    c["cmp"] += 1
                    obj_cmp[obj] += 1
                    if street(p["namenr"]) != street(p["strname"]):
                        c["mis"] += 1
                        obj_mis[obj] += 1
                        cn, cs = compact(p["namenr"]), compact(p["strname"])
                        if cn != cs:
                            c["rem"] += 1
                            if cn.startswith(cs):
                                c["prefix"] += 1
                            else:
                                c["other"] += 1
                                other_pairs[f"{p['namenr']!r} / {p['strname']!r}"] += 1
                xy = first_xy(f.get("geometry"))
                if xy is not None:
                    pt = (round(xy[0], 2), round(xy[1], 2))
                    if pt in first_at:
                        if pt not in shared:
                            shared[pt].append(first_at[pt])
                        shared[pt].append((SHORT[layer], obj))
                    else:
                        first_at[pt] = (SHORT[layer], obj)
    if h.hexdigest() != M0_HARVEST_SHA256:
        die("kopia M0 ma inny hash niz zmierzona w M0")

    full_mis = sum(n for o, n in obj_mis.items() if n == obj_cmp[o])
    k0_objs = {o for o, n in obj_n.items() if obj_k0[o] >= 0.9 * n}
    k0_in = sum(obj_k0[o] for o in k0_objs)
    bez_share = {b: pct(bez_k0[b], n) for b, n in bez_n.items()}
    lo, hi = min(bez_share.values()), max(bez_share.values())
    sp_obj = Counter(v[0][1] for v in shared.values())
    top5 = sum(n for _, n in sp_obj.most_common(5))
    mixed = sum(1 for v in shared.values() if len({lay for lay, _ in v}) > 1)

    ex["E02"] = [f"{n:>6}  {k}" for k, n in other_pairs.most_common(40)]
    ex["E04"] = [f"{n:>6} crown-0 of {obj_n[o]:>6}  {o}" for o, n in
                 sorted(((o, obj_k0[o]) for o in k0_objs), key=lambda x: -x[1])[:30]]
    ex["E05"] = [f"{b:<30} {bez_share[b]:>7} %  ({bez_k0[b]} of {bez_n[b]})"
                 for b in sorted(bez_share, key=lambda b: -bez_share[b])]
    ex["E06"] = [f"{n:>4}  {o}" for o, n in sp_obj.most_common(15)]
    ex["E07"] = [f"{x:.2f} {y:.2f}: {v}" for (x, y), v in list(shared.items())[:30]]

    P = {}

    def put(key, q, value, rule, ok):
        P[key] = {"question": q, "value": value, "rule": rule,
                  "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED")}

    put("E01", "prefix cases among remaining mismatches",
        {"pct": pct(c["prefix"], c["rem"]), "prefix": c["prefix"], "remaining": c["rem"]}, ">= 70",
        pct(c["prefix"], c["rem"]) >= 70 if c["rem"] else None)
    put("E02", "other street % of compared trees",
        {"pct": pct(c["other"], c["cmp"]), "other": c["other"], "compared": c["cmp"]}, "<= 3",
        pct(c["other"], c["cmp"]) <= 3 if c["cmp"] else None)
    put("E03", "M0 mismatch trees in fully mismatching care objects",
        {"pct": pct(full_mis, c["mis"]), "in_full_objects": full_mis, "mismatch": c["mis"],
         "objects_with_mismatch": len(obj_mis),
         "fully_mismatching_objects": sum(1 for o, n in obj_mis.items() if n == obj_cmp[o])}, ">= 90",
        pct(full_mis, c["mis"]) >= 90 if c["mis"] else None)
    put("E04", "crown-0 trees inside crown-0 objects",
        {"pct": pct(k0_in, c["k0"]), "in_objects": k0_in, "crown0": c["k0"], "crown0_objects": len(k0_objs),
         "objects": len(obj_n)}, ">= 50", pct(k0_in, c["k0"]) >= 50 if c["k0"] else None)
    put("E05", "crown-0 share: highest vs lowest district",
        {"max_pct": hi, "min_pct": lo, "ratio": round(hi / lo, 2) if lo else None, "districts": len(bez_share)},
        "max >= 5 x min", (hi >= 5 * lo) if lo else (hi > 0))
    put("E06", "5 objects with most shared points hold share of 148",
        {"pct": pct(top5, len(shared)), "top5": top5, "shared_points": len(shared),
         "objects": len(sp_obj)}, ">= 50", pct(top5, len(shared)) >= 50 if shared else None)
    put("E07", "shared points with trees from both layers",
        {"pct": pct(mixed, len(shared)), "mixed": mixed, "shared_points": len(shared)}, ">= 50",
        pct(mixed, len(shared)) >= 50 if shared else None)

    v = Counter(x["verdict"] for x in P.values())
    conf = v.get("CONFIRMED", 0)
    decision = ("DE post: facts released in D0_OUTCOME + CONFIRMED D1 facts (only new facts)"
                if conf >= 4 else "D2 before any post")
    overall = "REFUTED" if v.get("REFUTED") else "NO DATA" if v.get("NO DATA") else "CONFIRMED"
    os.makedirs(OUT, exist_ok=True)
    res = {"d1": "Baumbestand Berlin", "measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "prediction_sha256": ph, "harvest_sha256": h.hexdigest(), "score": f"{conf}/{len(P)}",
           "verdict_overall": overall, "decision": decision, "points": P,
           "crown0_by_district_pct": bez_share}
    path = os.path.join(OUT, "DIAGNOSIS.json")
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(EXAMPLES, "w", encoding="utf-8") as fh:
        for k in sorted(ex):
            fh.write(f"## {k}\n" + "\n".join(ex[k]) + "\n\n")
    print(f"harvest_sha256 : {h.hexdigest()}")
    print(f"score          : {conf}/{len(P)}   overall: {overall}")
    print(f"decision       : {decision}\n")
    for k, x in P.items():
        print(f"{k}  {x['verdict']:<9}  {x['question']}  [{x['rule']}]")
        print(f"      {json.dumps(x['value'], ensure_ascii=False)[:400]}")
    print(f"\nZapisano: {path}\nPrzyklady (poza gitem): {EXAMPLES}")


if __name__ == "__main__":
    main()
