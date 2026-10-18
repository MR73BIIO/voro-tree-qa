#!/usr/bin/env python3
"""BERLIN D0 - 8 punktow z berlin/D0_PREDICTION.md.

Liczy WYLACZNIE z zamrozonej kopii M0 (berlin/data/m0/), bez sieci.
Najpierw sprawdza: pieczec D0_PREDICTION.md (sha256) i harvest_sha256 kopii M0.
Uzycie:  python3 berlin/d0_diagnose.py
Wynik:   berlin/d0/DIAGNOSIS.json (do commita) + tabela na stdout,
         berlin/data/d0_examples.txt (przyklady, poza gitem).
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
PRED = os.path.join(HERE, "D0_PREDICTION.md")
PREDICTION_SHA256 = os.environ.get(
    "BERLIN_D0_PRED_SHA", "ce940481c4fd14cf0d296e9c22f8ca2ac867f9e5235372ea3ee7849b0f8dba8b")
M0_HARVEST_SHA256 = os.environ.get(
    "BERLIN_M0_SHA", "844546b787250e62e2470e9596d2184abbd0a81275586a2c9da72731ec7ad25c")
DATA = os.path.join(HERE, "data", "m0")
META = os.path.join(DATA, "harvest_meta.json")
OUT = os.path.join(HERE, "d0")
EXAMPLES = os.path.join(HERE, "data", "d0_examples.txt")
LAYERS = ["baumbestand:anlagenbaeume", "baumbestand:strassenbaeume"]
SHORT = {"baumbestand:anlagenbaeume": "anlagen", "baumbestand:strassenbaeume": "strassen"}
EMPTY = {"", "-", "--"}
REF_YEAR = 2026


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
        die("brak berlin/D0_PREDICTION.md")
    ph = hashlib.sha256(open(PRED, "rb").read()).hexdigest()
    if ph != PREDICTION_SHA256:
        die(f"D0_PREDICTION.md ma inny sha256 ({ph[:12]}...) niz zapieczetowany")
    print(f"prediction_sha256: {ph}  (OK)")
    if not os.path.exists(META):
        die("brak kopii M0 (harvest_meta.json)")
    meta = json.load(open(META))
    h = hashlib.sha256()
    c = Counter()
    ex = defaultdict(list)
    pts = defaultdict(list)
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
                gid = str(p.get("gisid"))
                pj, sa = num(p.get("pflanzjahr")), num(p.get("standalter"))
                # D01 / D02
                if pj is None:
                    if sa == 0:
                        c["D02_n"] += 1
                        if layer.endswith("anlagenbaeume"):
                            c["D02_ok"] += 1
                    else:
                        c["D01_n"] += 1
                        if empty(p.get("standalter")) or sa is None:
                            c["D01_ok"] += 1
                        elif len(ex["D01"]) < 30:
                            ex["D01"].append(f"{SHORT[layer]} {gid} pflanzjahr={p.get('pflanzjahr')!r} standalter={p.get('standalter')!r}")
                # D03
                elif not (sa is not None and pj + sa == REF_YEAR) and pj >= 1700:
                    c["D03_n"] += 1
                    s = pj + sa if sa is not None else None
                    c[f"D03_sum_{int(s) if s is not None else 'none'}"] += 1
                    if s is not None and 2021 <= s <= 2025:
                        c["D03_ok"] += 1
                # D04 / D05
                if layer.endswith("strassenbaeume") and not empty(p.get("namenr")) and not empty(p.get("strname")):
                    c["D05_n"] += 1
                    if street(p["namenr"]) != street(p["strname"]):
                        c["D04_n"] += 1
                        if compact(p["namenr"]) == compact(p["strname"]):
                            c["D04_ok"] += 1
                        else:
                            c["D05_left"] += 1
                            key = f"{p['namenr']!r} / {p['strname']!r}"
                            c["D05_pair:" + key] += 1
                # D06 / D07
                kd = num(p.get("kronedurch"))
                if kd == 0:
                    c["D06_n"] += 1
                    bh = num(p.get("baumhoehe"))
                    if bh is None or bh == 0:
                        c["D06_ok"] += 1
                if pj is not None and 2020 <= pj <= REF_YEAR:
                    c["D07_young"] += 1
                    c["D07_young0"] += kd == 0
                elif pj is not None and pj < 2020:
                    c["D07_old"] += 1
                    c["D07_old0"] += kd == 0
                # D08
                xy = first_xy(f.get("geometry"))
                if xy is not None:
                    pts[(round(xy[0], 2), round(xy[1], 2))].append(
                        None if empty(p.get("art_bot"), True) else str(p["art_bot"]).strip())
    if h.hexdigest() != M0_HARVEST_SHA256:
        die("kopia M0 ma inny hash niz zmierzona w M0")
    shared = {k: v for k, v in pts.items() if len(v) > 1}
    same = sum(1 for v in shared.values() if v[0] is not None and len(set(v)) == 1)
    for (x, y), v in list(shared.items())[:30]:
        ex["D08"].append(f"{x:.2f} {y:.2f}: {v}")
    pairs = sorted(((n, k[9:]) for k, n in c.items() if k.startswith("D05_pair:")), reverse=True)[:40]
    ex["D05"] = [f"{n:>6}  {k}" for n, k in pairs]
    sums = {k[8:]: n for k, n in c.items() if k.startswith("D03_sum_")}

    P = {}

    def put(key, q, value, rule, ok):
        P[key] = {"question": q, "value": value, "rule": rule,
                  "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED")}

    put("D01", "standalter empty where no year and not 0",
        {"pct": pct(c["D01_ok"], c["D01_n"]), "ok": c["D01_ok"], "n": c["D01_n"]}, ">= 90",
        pct(c["D01_ok"], c["D01_n"]) >= 90 if c["D01_n"] else None)
    put("D02", "'no year, age 0' in Anlagenbaeume",
        {"pct": pct(c["D02_ok"], c["D02_n"]), "ok": c["D02_ok"], "n": c["D02_n"]}, ">= 95",
        pct(c["D02_ok"], c["D02_n"]) >= 95 if c["D02_n"] else None)
    put("D03", "B04 exceptions: pflanzjahr + standalter in 2021-2025",
        {"pct": pct(c["D03_ok"], c["D03_n"]), "ok": c["D03_ok"], "n": c["D03_n"],
         "sums": dict(sorted(sums.items(), key=lambda kv: -kv[1])[:12])}, ">= 90",
        pct(c["D03_ok"], c["D03_n"]) >= 90 if c["D03_n"] else None)
    put("D04", "B13 mismatches resolved by compact form",
        {"pct": pct(c["D04_ok"], c["D04_n"]), "ok": c["D04_ok"], "n": c["D04_n"]}, ">= 70",
        pct(c["D04_ok"], c["D04_n"]) >= 70 if c["D04_n"] else None)
    put("D05", "mismatches left after compact form % of compared trees",
        {"pct": pct(c["D05_left"], c["D05_n"]), "left": c["D05_left"], "compared": c["D05_n"]}, "<= 3",
        pct(c["D05_left"], c["D05_n"]) <= 3 if c["D05_n"] else None)
    put("D06", "kronedurch = 0: baumhoehe 0 or empty",
        {"pct": pct(c["D06_ok"], c["D06_n"]), "ok": c["D06_ok"], "n": c["D06_n"]}, ">= 50",
        pct(c["D06_ok"], c["D06_n"]) >= 50 if c["D06_n"] else None)
    yp, op = pct(c["D07_young0"], c["D07_young"]), pct(c["D07_old0"], c["D07_old"])
    put("D07", "kronedurch = 0 share: young (2020-2026) vs year before 2020",
        {"young_pct": yp, "young_n": c["D07_young"], "old_pct": op, "old_n": c["D07_old"],
         "ratio": round(yp / op, 2) if yp is not None and op else None}, "young >= 3 x old",
        (yp >= 3 * op) if (yp is not None and op) else None)
    put("D08", "shared points with one identical non-empty art_bot",
        {"pct": pct(same, len(shared)), "same": same, "shared_points": len(shared)}, ">= 80",
        pct(same, len(shared)) >= 80 if shared else None)

    v = Counter(x["verdict"] for x in P.values())
    conf = v.get("CONFIRMED", 0)
    decision = "DE LinkedIn post from M0 + D0 facts (only new facts) + Puls" if conf >= 5 else "D1"
    overall = "REFUTED" if v.get("REFUTED") else "NO DATA" if v.get("NO DATA") else "CONFIRMED"
    os.makedirs(OUT, exist_ok=True)
    res = {"d0": "Baumbestand Berlin", "measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "prediction_sha256": ph, "harvest_sha256": h.hexdigest(), "score": f"{conf}/{len(P)}",
           "verdict_overall": overall, "decision": decision, "points": P}
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
