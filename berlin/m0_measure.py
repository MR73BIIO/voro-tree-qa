#!/usr/bin/env python3
"""BERLIN M0 - 14 punktow z berlin/M0_PREDICTION.md (commit 9a86559, Puls #44).

Najpierw sprawdza pieczec przewidywania (sha256), potem:
  harvest  - pobiera CALE obie warstwy WFS (stronicowanie, sortBy=gisid), kopia zamrozona
             w berlin/data/m0/ (gzip, poza gitem) + harvest_meta.json z harvest_sha256
  measure  - liczy B01-B14 WYLACZNIE z zamrozonej kopii, bez sieci
  all      - harvest + measure
Opcje: --resume (dokoncz przerwane pobieranie), --page 10000.

Wynik: berlin/m0/RESULTS.json (do commita) + tabela na stdout,
       berlin/data/m0_examples.txt (przyklady z id, poza gitem).
Tylko biblioteka standardowa.
"""
import argparse
import glob
import gzip
import hashlib
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone

WFS = os.environ.get("BERLIN_WFS", "https://gdi.berlin.de/services/wfs/baumbestand")
HERE = os.path.dirname(os.path.abspath(__file__))
PRED = os.path.join(HERE, "M0_PREDICTION.md")
PREDICTION_SHA256 = os.environ.get(
    "BERLIN_PRED_SHA", "5fbdbeeda17641e8ab652c008e8d2065d9791e3676baf1b614f41633fa13a710")
DATA = os.path.join(HERE, "data", "m0")
META = os.path.join(DATA, "harvest_meta.json")
STATE = os.path.join(DATA, "harvest_state.json")
OUT = os.path.join(HERE, "m0")
EXAMPLES = os.path.join(HERE, "data", "m0_examples.txt")
LAYERS = ["baumbestand:anlagenbaeume", "baumbestand:strassenbaeume"]
SHORT = {"baumbestand:anlagenbaeume": "anlagen", "baumbestand:strassenbaeume": "strassen"}
R0_COUNTS = {"baumbestand:anlagenbaeume": 527780, "baumbestand:strassenbaeume": 434765}
EMPTY = {"", "-", "--"}
SPECIES = ("art_dtsch", "art_bot", "gattung", "gattung_deutsch")
REF_YEAR = 2026
SLEEP_S = 1.0
UA = {"User-Agent": "MR73BIIO-voro-tree-qa-m0/1.0"}


def die(msg):
    sys.exit("STOP: " + msg)


def check_prediction():
    if not os.path.exists(PRED):
        die("brak berlin/M0_PREDICTION.md")
    h = hashlib.sha256(open(PRED, "rb").read()).hexdigest()
    if h != PREDICTION_SHA256:
        die(f"M0_PREDICTION.md ma inny sha256 ({h[:12]}...) niz zapieczetowany ({PREDICTION_SHA256[:12]}...)")
    return h


# ---------------- harvest ----------------

def fetch(params):
    url = WFS + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code < 500:
                die(f"HTTP {e.code} dla {url}\n{e.read()[:400].decode('utf-8', 'replace')}")
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, ConnectionError, OSError) as e:
            last = repr(e)
        wait = 5 * (attempt + 1)
        print(f"    ponawiam za {wait} s ({last})", flush=True)
        time.sleep(wait)
    die(f"brak odpowiedzi po 6 probach ({last})")


def number_matched(layer):
    raw = fetch({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                 "typeNames": layer, "resultType": "hits"})
    v = ET.fromstring(raw).get("numberMatched")
    if not (v and v.isdigit()):
        die(f"{layer}: serwer nie podal numberMatched")
    return int(v)


def page_path(layer, k):
    return os.path.join(DATA, f"{SHORT[layer]}_{k:04d}.json.gz")


def read_page(path):
    with gzip.open(path, "rb") as fh:
        return fh.read()


def cmd_harvest(a):
    os.makedirs(DATA, exist_ok=True)
    state = {}
    if a.resume and os.path.exists(STATE):
        state = json.load(open(STATE))
        print(f"wznowienie: {STATE}")
    elif glob.glob(os.path.join(DATA, "*.json.gz")):
        die("w berlin/data/m0/ sa juz strony. Uzyj --resume albo usun katalog swiadomie.")
    for layer in LAYERS:
        st = state.setdefault(layer, {})
        if "matched" not in st:
            st["matched"] = number_matched(layer)
            st["page"] = a.page
        total, per = st["matched"], st["page"]
        pages = (total + per - 1) // per
        print(f"{layer}: {total} obiektow, {pages} stron po {per}", flush=True)
        for k in range(pages):
            p = page_path(layer, k)
            expect = min(per, total - k * per)
            if os.path.exists(p):
                try:
                    n = len(json.loads(read_page(p))["features"])
                    if n == expect:
                        continue
                except Exception:
                    pass
                os.remove(p)
            raw = fetch({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                         "typeNames": layer, "count": per, "startIndex": k * per,
                         "sortBy": "gisid", "outputFormat": "application/json"})
            n = len(json.loads(raw)["features"])
            if n != expect:
                die(f"{layer} strona {k}: {n} obiektow zamiast {expect} (limit serwera?)")
            tmp = p + ".tmp"
            with gzip.open(tmp, "wb") as fh:
                fh.write(raw)
            os.replace(tmp, p)
            print(f"  {SHORT[layer]} {k + 1}/{pages}  ({n})", flush=True)
            json.dump(state, open(STATE, "w"), indent=1)
            time.sleep(SLEEP_S)
    h = hashlib.sha256()
    for layer in LAYERS:
        for k in range((state[layer]["matched"] + state[layer]["page"] - 1) // state[layer]["page"]):
            h.update(read_page(page_path(layer, k)))
    meta = {"wfs": WFS, "finished_utc": now(), "layers": state, "harvest_sha256": h.hexdigest(),
            "order": "layers as listed, pages ascending, raw JSON bytes before gzip"}
    json.dump(meta, open(META, "w"), indent=1)
    print(f"\nharvest_sha256: {h.hexdigest()}\nZapisano: {META}")


# ---------------- measure ----------------

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


def first_xy(g):
    c = (g or {}).get("coordinates")
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    return (c[0], c[1]) if isinstance(c, list) and len(c) >= 2 else None


def pct(a, n):
    return round(100.0 * a / n, 3) if n else None


def longest_run(flags):
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return best


def cmd_measure(_a):
    if not os.path.exists(META):
        die("brak harvest_meta.json - najpierw harvest")
    meta = json.load(open(META))
    h = hashlib.sha256()
    total_records = 0
    L = {}                                   # dane per warstwa
    points = Counter()
    pit = defaultdict(set)
    art_map = defaultdict(set)
    bezirk = Counter()
    ex = defaultdict(list)
    c = Counter()                            # liczniki wspolne (drzewa)
    for layer in LAYERS:
        st = meta["layers"][layer]
        pages = (st["matched"] + st["page"] - 1) // st["page"]
        d = L[layer] = {"matched": st["matched"], "harvested": 0, "gisid": Counter(), "order": [],
                        "shells": 0, "trees": 0, "krone0": 0}
        for k in range(pages):
            raw = read_page(page_path(layer, k))
            h.update(raw)
            for f in json.loads(raw)["features"]:
                p = f.get("properties") or {}
                d["harvested"] += 1
                total_records += 1
                gid = str(p.get("gisid"))
                d["gisid"][gid] += 1
                xy = first_xy(f.get("geometry"))
                if xy is None or xy[0] == 0 or xy[1] == 0:
                    c["B14_bad_geom"] += 1
                    if len(ex["B14"]) < 20:
                        ex["B14"].append(f"{SHORT[layer]} {gid} {xy}")
                shell = empty(p.get("pitid")) and empty(p.get("art_bot"), True) and empty(p.get("bezirk"))
                d["order"].append((gid, shell))
                if shell:
                    d["shells"] += 1
                    continue
                d["trees"] += 1
                c["trees"] += 1
                if not empty(p.get("pitid")):
                    pit[layer].add(str(p["pitid"]).strip())
                if xy is not None:
                    points[(round(xy[0], 2), round(xy[1], 2))] += 1
                if not empty(p.get("bezirk")):
                    bezirk[str(p["bezirk"]).strip()] += 1
                pj, sa = num(p.get("pflanzjahr")), num(p.get("standalter"))
                if pj is not None:
                    c["B04_n"] += 1
                    if sa is not None and pj + sa == REF_YEAR:
                        c["B04_ok"] += 1
                    elif len(ex["B04"]) < 20:
                        ex["B04"].append(f"{SHORT[layer]} {gid} pflanzjahr={p.get('pflanzjahr')} standalter={p.get('standalter')}")
                elif empty(p.get("pflanzjahr")) or num(p.get("pflanzjahr")) is None:
                    c["B05_n"] += 1
                    if sa == 0:
                        c["B05_ok"] += 1
                if not empty(p.get("gattung"), True) and empty(p.get("gattung_deutsch"), True):
                    c["B06"] += 1
                if not empty(p.get("art_bot"), True) and not empty(p.get("art_dtsch"), True):
                    art_map[str(p["art_bot"]).strip()].add(str(p["art_dtsch"]).strip())
                if num(p.get("kronedurch")) == 0:
                    d["krone0"] += 1
                bh, su = num(p.get("baumhoehe")), num(p.get("stammumfg"))
                if (bh is not None and bh > 50) or (su is not None and su > 1000) or \
                        (pj is not None and (pj < 1700 or pj > REF_YEAR)):
                    c["B09"] += 1
                    if len(ex["B09"]) < 30:
                        ex["B09"].append(f"{SHORT[layer]} {gid} baumhoehe={p.get('baumhoehe')} "
                                         f"stammumfg={p.get('stammumfg')} pflanzjahr={p.get('pflanzjahr')} "
                                         f"art={p.get('art_bot')}")
                if layer.endswith("strassenbaeume") and not empty(p.get("namenr")) and not empty(p.get("strname")):
                    c["B13_n"] += 1
                    if street(p["namenr"]) != street(p["strname"]):
                        c["B13"] += 1
                        if len(ex["B13"]) < 40:
                            ex["B13"].append(f"{gid}  namenr={p['namenr']!r}  strname={p['strname']!r}")
    if h.hexdigest() != meta["harvest_sha256"]:
        die("kopia M0 ma inny hash niz zapisany w harvest_meta.json")

    P = {}

    def put(key, q, value, rule, ok):
        P[key] = {"question": q, "value": value, "rule": rule,
                  "verdict": "NO DATA" if ok is None else ("CONFIRMED" if ok else "REFUTED")}

    dup = {l: sum(n - 1 for n in L[l]["gisid"].values() if n > 1) for l in LAYERS}
    put("B01", "harvest complete, no duplicate gisid",
        {SHORT[l]: {"matched": L[l]["matched"], "harvested": L[l]["harvested"], "dup_gisid": dup[l],
                    "r0_count": R0_COUNTS[l]} for l in LAYERS},
        "harvested = numberMatched, dup 0",
        all(L[l]["harvested"] == L[l]["matched"] and dup[l] == 0 for l in LAYERS))
    shells = sum(L[l]["shells"] for l in LAYERS)
    put("B02", "shells % of all records",
        {"pct": pct(shells, total_records), "shells": shells, "records": total_records,
         **{SHORT[l]: L[l]["shells"] for l in LAYERS}}, ">= 5", pct(shells, total_records) >= 5)
    runs = {}
    for l in LAYERS:
        if L[l]["shells"]:
            order = sorted(L[l]["order"])
            runs[l] = (longest_run(s for _, s in order), L[l]["shells"])
    put("B03", "share of shells in the longest contiguous gisid run, per layer",
        {SHORT[l]: {"longest_run": r, "shells": s, "pct": pct(r, s)} for l, (r, s) in runs.items()},
        ">= 90 in each layer with shells",
        all(pct(r, s) >= 90 for r, s in runs.values()) if runs else None)
    put("B04", "pflanzjahr + standalter = 2026 where pflanzjahr is a number",
        {"pct": pct(c["B04_ok"], c["B04_n"]), "ok": c["B04_ok"], "n": c["B04_n"]}, ">= 99",
        pct(c["B04_ok"], c["B04_n"]) >= 99 if c["B04_n"] else None)
    put("B05", "standalter = 0 where pflanzjahr is empty",
        {"pct": pct(c["B05_ok"], c["B05_n"]), "ok": c["B05_ok"], "n": c["B05_n"]}, ">= 95",
        pct(c["B05_ok"], c["B05_n"]) >= 95 if c["B05_n"] else None)
    put("B06", "gattung filled, gattung_deutsch empty % of trees",
        {"pct": pct(c["B06"], c["trees"]), "n": c["B06"]}, ">= 2", pct(c["B06"], c["trees"]) >= 2)
    multi = {k: sorted(v) for k, v in art_map.items() if len(v) >= 2}
    put("B07", "art_bot values with >= 2 different art_dtsch",
        {"n": len(multi), "art_bot_values": len(art_map)}, ">= 3", len(multi) >= 3)
    for k, v in sorted(multi.items())[:40]:
        ex["B07"].append(f"{k}  ->  {' | '.join(v)}")
    put("B08", "kronedurch = 0 % of trees, per layer",
        {SHORT[l]: {"pct": pct(L[l]["krone0"], L[l]["trees"]), "n": L[l]["krone0"]} for l in LAYERS},
        ">= 5 in each layer", all(pct(L[l]["krone0"], L[l]["trees"]) >= 5 for l in LAYERS))
    put("B09", "implausible height / girth / planting year",
        {"n": c["B09"], "pct": pct(c["B09"], c["trees"])}, ">= 1 and <= 0.1 %",
        c["B09"] >= 1 and pct(c["B09"], c["trees"]) <= 0.1)
    shared = sum(n for n in points.values() if n > 1)
    put("B10", "trees on a shared point % of trees",
        {"pct": pct(shared, c["trees"]), "trees": shared, "points": sum(1 for n in points.values() if n > 1)},
        ">= 0.5", pct(shared, c["trees"]) >= 0.5)
    for (x, y), n in points.most_common(15):
        if n > 1:
            ex["B10"].append(f"{n} trees at {x:.2f} {y:.2f}")
    both = pit[LAYERS[0]] & pit[LAYERS[1]]
    put("B11", "pitid present in both layers", {"n": len(both)}, ">= 1", len(both) >= 1)
    ex["B11"] = sorted(both)[:20]
    put("B12", "distinct non-empty bezirk values", {"n": len(bezirk), "values": dict(bezirk.most_common())},
        "== 12", len(bezirk) == 12)
    put("B13", "street-name mismatch % (Strassenbaeume, both fields filled)",
        {"pct": pct(c["B13"], c["B13_n"]), "n": c["B13"], "of": c["B13_n"]}, ">= 1",
        pct(c["B13"], c["B13_n"]) >= 1 if c["B13_n"] else None)
    put("B14", "records without point or with X/Y = 0", {"n": c["B14_bad_geom"]}, "== 0", c["B14_bad_geom"] == 0)

    v = Counter(x["verdict"] for x in P.values())
    conf = v.get("CONFIRMED", 0)
    if P["B01"]["verdict"] != "CONFIRMED":
        decision = "STOP: harvest not trusted (B01) - diagnosis first, nothing used"
    elif conf >= 10:
        decision = "DE LinkedIn post (third city, only new facts) + Puls"
    else:
        decision = "D0 before any use"
    overall = "REFUTED" if v.get("REFUTED") else "NO DATA" if v.get("NO DATA") else "CONFIRMED"
    os.makedirs(OUT, exist_ok=True)
    res = {"m0": "Baumbestand Berlin", "measured_utc": now(), "prediction_sha256": PREDICTION_SHA256,
           "harvest_sha256": meta["harvest_sha256"], "records": total_records, "trees": c["trees"],
           "score": f"{conf}/{len(P)}", "verdict_overall": overall, "decision": decision, "points": P}
    path = os.path.join(OUT, "RESULTS.json")
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(EXAMPLES, "w", encoding="utf-8") as fh:
        for k in sorted(ex):
            fh.write(f"## {k}\n" + "\n".join(ex[k]) + "\n\n")
    print(f"records        : {total_records}  (trees {c['trees']}, shells {shells})")
    print(f"harvest_sha256 : {meta['harvest_sha256']}")
    print(f"score          : {conf}/{len(P)}   overall: {overall}")
    print(f"decision       : {decision}\n")
    for k, x in P.items():
        print(f"{k}  {x['verdict']:<9}  {x['question']}  [{x['rule']}]")
        print(f"      {json.dumps(x['value'], ensure_ascii=False)[:300]}")
    print(f"\nZapisano: {path}\nPrzyklady (poza gitem): {EXAMPLES}")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["harvest", "measure", "all"])
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--page", type=int, default=10000)
    a = ap.parse_args()
    print(f"prediction_sha256: {check_prediction()}  (OK)")
    if a.cmd in ("harvest", "all"):
        cmd_harvest(a)
    if a.cmd in ("measure", "all"):
        cmd_measure(a)


if __name__ == "__main__":
    main()
