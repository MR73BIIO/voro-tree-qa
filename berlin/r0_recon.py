#!/usr/bin/env python3
"""BERLIN R0 - rozpoznanie Baumbestand Berlin (WFS) przed przewidywaniami M0.

Zrodlo: https://gdi.berlin.de/services/wfs/baumbestand (EPSG:25833, dl-zero-de/2.0).
R0 ustala tylko: jakie warstwy sa w usludze, ile maja obiektow, jakie pola,
jak czesto pola sa wypelnione w probce i jakie wartosci w nich stoja.
Zadnych ocen jakosci - te ida dopiero po M0_PREDICTION (jak w Zurychu i Wiedniu).

Proba jest ROZLOZONA po calym zbiorze (okna w rownych odstepach), nie "pierwsze N":
lekcja z FINA - poczatek kolejnosci serwera potrafi byc zupelnie inny niz calosc.

Uzycie:
  python3 berlin/r0_recon.py discover                 # krok 1: warstwy, formaty, pola
  python3 berlin/r0_recon.py recon --sample 2000      # krok 2: liczby + profil probki

Zapis: berlin/data/r0/ (surowe odpowiedzi, poza gitem) + berlin/r0/R0_SUMMARY.json (do commita).
Tylko biblioteka standardowa.
"""
import argparse
import hashlib
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone

WFS = os.environ.get("BERLIN_WFS", "https://gdi.berlin.de/services/wfs/baumbestand")
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "r0")
OUT = os.path.join(HERE, "r0")
SLEEP_S = 1.0
WINDOWS = 10                      # na ile rownych okien dzielimy probe
EMPTY = {"", "-", "--", "null", "none", "n/a", "unbekannt"}
UA = {"User-Agent": "MR73BIIO-voro-tree-qa-r0/1.0"}


def local(tag):
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def fetch(params, binary=False):
    """Jedno zapytanie do WFS, 6 prob z odstepem. URL bazowy podmienialny przez BERLIN_WFS."""
    url = WFS + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                raw = r.read()
                return raw if binary else raw.decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            body = e.read()[:400].decode("utf-8", "replace")
            if e.code < 500:
                sys.exit(f"STOP: HTTP {e.code} dla {url}\n{body}")
            last = f"HTTP {e.code}"
        except Exception as e:  # URLError, timeout, IncompleteRead
            last = repr(e)
        time.sleep(3 * (attempt + 1))
    sys.exit(f"STOP: brak odpowiedzi po 6 probach ({last}) dla {url}")


def save(name, data):
    os.makedirs(DATA, exist_ok=True)
    p = os.path.join(DATA, name)
    with open(p, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))
    return p


# ---------- discover ----------

def capabilities():
    raw = fetch({"service": "WFS", "version": "2.0.0", "request": "GetCapabilities"}, binary=True)
    save("capabilities.xml", raw)
    root = ET.fromstring(raw)
    types = []
    for ft in root.iter():
        if local(ft.tag) != "FeatureType":
            continue
        d = {local(c.tag): (c.text or "").strip() for c in ft}
        types.append({"name": d.get("Name"), "title": d.get("Title"),
                      "default_crs": d.get("DefaultCRS") or d.get("DefaultSRS")})
    formats = []
    for op in root.iter():
        if local(op.tag) == "Operation" and op.get("name") == "GetFeature":
            for p in op.iter():
                if local(p.tag) == "Parameter" and p.get("name", "").lower() == "outputformat":
                    formats += [(v.text or "").strip() for v in p.iter() if local(v.tag) == "Value"]
    return types, sorted(set(f for f in formats if f))


def describe(type_name):
    raw = fetch({"service": "WFS", "version": "2.0.0", "request": "DescribeFeatureType",
                 "typeNames": type_name}, binary=True)
    save(f"describe_{safe(type_name)}.xsd", raw)
    root = ET.fromstring(raw)
    fields = []
    for ct in root.iter():                      # tylko pola wewnatrz complexType,
        if local(ct.tag) != "complexType":       # bez elementu glownego warstwy
            continue
        for el in ct.iter():
            if local(el.tag) == "element" and el.get("name") and el.get("type"):
                fields.append({"name": el.get("name"), "type": el.get("type").rsplit(":", 1)[-1]})
    return fields


def safe(s):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s or "x")


def json_format(formats):
    for f in formats:
        if "json" in f.lower():
            return f
    return None


def cmd_discover(_args):
    types, formats = capabilities()
    print(f"WFS            : {WFS}")
    print(f"warstwy        : {len(types)}")
    for t in types:
        print(f"  - {t['name']}  |  {t['title']}  |  {t['default_crs']}")
    print(f"formaty        : {', '.join(formats) or '(brak listy)'}")
    print(f"JSON wybrany   : {json_format(formats) or 'BRAK -> recon uzyje GML'}")
    for t in types:
        fl = describe(t["name"])
        print(f"\npola {t['name']} ({len(fl)}):")
        print("  " + ", ".join(f"{f['name']}:{f['type']}" for f in fl))
        time.sleep(SLEEP_S)
    print(f"\nSurowe odpowiedzi: {DATA}")


# ---------- recon ----------

def hits(type_name):
    raw = fetch({"service": "WFS", "version": "2.0.0", "request": "GetFeature",
                 "typeNames": type_name, "resultType": "hits"}, binary=True)
    root = ET.fromstring(raw)
    for key in ("numberMatched", "numberOfFeatures"):
        v = root.get(key)
        if v and v.isdigit():
            return int(v)
    raw = fetch({"service": "WFS", "version": "1.1.0", "request": "GetFeature",
                 "typeName": type_name, "resultType": "hits"}, binary=True)
    v = ET.fromstring(raw).get("numberOfFeatures")
    return int(v) if v and v.isdigit() else None


def page(type_name, start, count, fmt, sortby):
    q = {"service": "WFS", "version": "2.0.0", "request": "GetFeature", "typeNames": type_name,
         "count": count, "startIndex": start}
    if sortby:
        q["sortBy"] = sortby
    if fmt:
        q["outputFormat"] = fmt
        raw = fetch(q, binary=True)
        gj = json.loads(raw)
        feats = [{"props": f.get("properties") or {},
                  "geom": (f.get("geometry") or {}).get("type"),
                  "xy": first_xy((f.get("geometry") or {}).get("coordinates"))}
                 for f in gj.get("features", [])]
        return raw, feats
    raw = fetch(q, binary=True)
    return raw, parse_gml(raw)


def first_xy(c):
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    return c[:2] if isinstance(c, list) and len(c) >= 2 else None


def parse_gml(raw):
    root = ET.fromstring(raw)
    feats = []
    for m in root.iter():
        if local(m.tag) not in ("member", "featureMember"):
            continue
        for f in m:
            props, geom, xy = {}, None, None
            for c in f:
                kids = list(c)
                if kids and local(kids[0].tag) in ("Point", "MultiPoint", "Polygon", "MultiSurface",
                                                    "LineString", "MultiPolygon"):
                    geom = local(kids[0].tag)
                    pos = next((p.text for p in kids[0].iter() if local(p.tag) in ("pos", "coordinates")), None)
                    if pos:
                        nums = re.split(r"[ ,]+", pos.strip())
                        xy = [float(nums[0]), float(nums[1])] if len(nums) >= 2 else None
                else:
                    props[local(c.tag)] = (c.text or "").strip() if c.text is not None else None
            feats.append({"props": props, "geom": geom, "xy": xy})
    return feats


def num(v):
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", ".")
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return float(s)
    return None


def is_empty(v):
    return v is None or (isinstance(v, str) and v.strip().lower() in EMPTY)


def profile(feats, field_order):
    n = len(feats)
    names = list(field_order) + sorted({k for f in feats for k in f["props"]} - set(field_order))
    out = {}
    for k in names:
        vals = [f["props"].get(k) for f in feats]
        present = sum(1 for f in feats if k in f["props"])
        filled = [v for v in vals if not is_empty(v)]
        nums = [x for x in (num(v) for v in filled) if x is not None]
        cnt = Counter(str(v) for v in filled)
        p = {"present_pct": pct(present, n), "filled_pct": pct(len(filled), n),
             "empty_markers": dict(Counter(str(v) for v in vals if v is not None and is_empty(v))),
             "distinct_in_sample": len(cnt)}
        if nums and len(nums) >= 0.8 * len(filled):
            p["numeric"] = {"n": len(nums), "min": min(nums), "median": statistics.median(nums),
                            "max": max(nums), "zero": sum(1 for x in nums if x == 0)}
        if len(cnt) <= 60:
            p["values"] = dict(cnt.most_common(15))
        else:
            p["top5"] = dict(cnt.most_common(5))
        out[k] = p
    return out


def pct(a, n):
    return round(100.0 * a / n, 2) if n else None


def cmd_recon(args):
    types, formats = capabilities()
    fmt = json_format(formats)
    summary = {"r0": "Baumbestand Berlin", "wfs": WFS, "measured_utc": now(),
               "output_format": fmt or "GML", "windows": WINDOWS, "sample_per_type": args.sample,
               "sortby": args.sortby, "layers": []}
    h = hashlib.sha256()
    for t in types:
        name = t["name"]
        fields = describe(name)
        print(f"{name}: licze obiekty (resultType=hits)...", flush=True)
        total = hits(name)
        print(f"{name}: {total} obiektow", flush=True)
        time.sleep(SLEEP_S)
        feats = []
        if total:
            per = max(1, args.sample // WINDOWS)
            starts = sorted({int(i * max(0, total - per) / max(1, WINDOWS - 1)) for i in range(WINDOWS)})
            for k, s in enumerate(starts, 1):
                print(f"  {name}: okno {k}/{len(starts)} (startIndex {s}, {per} obiektow)", flush=True)
                raw, got = page(name, s, per, fmt, args.sortby)
                h.update(raw)
                save(f"sample_{safe(name)}_{s:08d}.{'json' if fmt else 'xml'}", raw)
                for g in got:
                    g["window"] = s
                feats += got
                time.sleep(SLEEP_S)
        xs = [f["xy"][0] for f in feats if f["xy"]]
        ys = [f["xy"][1] for f in feats if f["xy"]]
        summary["layers"].append({
            "name": name, "title": t["title"], "default_crs": t["default_crs"],
            "number_matched": total, "fields_declared": fields, "sample_size": len(feats),
            "windows_start_index": sorted({f["window"] for f in feats}),
            "geometry_types": dict(Counter(f["geom"] for f in feats)),
            "sample_bbox": [min(xs), min(ys), max(xs), max(ys)] if xs else None,
            "fields": profile(feats, [f["name"] for f in fields if f["type"] not in
                                      ("GeometryPropertyType", "PointPropertyType", "MultiPointPropertyType",
                                       "SurfacePropertyType", "MultiSurfacePropertyType")]),
        })
        print(f"{name}: {total} obiektow, proba {len(feats)} z {len(summary['layers'][-1]['windows_start_index'])} okien")
    summary["sample_sha256"] = h.hexdigest()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "R0_SUMMARY.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2)
    report(summary)
    print(f"\nZapisano: {path}\nSurowe odpowiedzi (poza gitem): {DATA}")


def report(s):
    print(f"\nWFS: {s['wfs']}  format: {s['output_format']}  sample_sha256: {s['sample_sha256']}")
    for L in s["layers"]:
        print(f"\n=== {L['name']}  ({L['title']})")
        print(f"obiekty: {L['number_matched']}  proba: {L['sample_size']}  CRS: {L['default_crs']}")
        print(f"geometrie: {L['geometry_types']}  bbox proby: {L['sample_bbox']}")
        print(f"{'pole':<18}{'wypeln.%':>9}{'rozne':>7}  wartosci / liczby")
        for k, p in L["fields"].items():
            extra = ""
            if "numeric" in p:
                q = p["numeric"]
                extra = f"min {q['min']:g} med {q['median']:g} max {q['max']:g} zer {q['zero']}  "
            vals = p.get("values") or p.get("top5") or {}
            extra += "; ".join(f"{v}×{c}" for v, c in list(vals.items())[:5])
            if p["empty_markers"]:
                extra += f"  [puste: {p['empty_markers']}]"
            print(f"{k:<18}{p['filled_pct']!s:>9}{p['distinct_in_sample']:>7}  {extra[:150]}")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover")
    r = sub.add_parser("recon")
    r.add_argument("--sample", type=int, default=2000, help="obiektow na warstwe (rozlozone na okna)")
    r.add_argument("--sortby", default=None, help="np. gisid - stabilna kolejnosc stronicowania")
    a = ap.parse_args()
    {"discover": cmd_discover, "recon": cmd_recon}[a.cmd](a)


if __name__ == "__main__":
    main()
