#!/usr/bin/env python3
"""voro-tree-qa R0 - reconnaissance of the Zurich tree register (Baumkataster).

R0 is NOT a life. It makes no prediction and judges nothing. It only answers:
which public endpoint delivers the data, and what is in it (fields, counts, value ranges, CRS)?
Its output is the input for docs/M0_PREDICTION.md, committed before M0 runs ("reconnaissance disclosed").

History (disclosed):
- v1 (308fa80): csv.Sniffer failed.
- v2 (872e555): showed that both download links of the dataset page return the HTML page of the
  city geoportal (an Angular app), not data. GPKG check then failed on that HTML.
- v3 (this file): probes several public endpoints of the same dataset and records every answer.

Source: Open Data Zurich, dataset geo_baumkataster, licence CC0.

Definitions fixed before the run (this file is committed before the run):
- Every candidate endpoint is requested once; status, content type, size, SHA-256 and the first
  200 bytes are recorded, also for failures. Bodies are saved to data/raw/ (outside git).
- Kind of body by its first bytes: zip (PK), sqlite (GeoPackage), html, xml, json, otherwise text.
- html bodies are not data and are only recorded.
- json: GeoJSON FeatureCollection -> number of features, numberMatched/numberReturned/totalFeatures
  if present, crs member, geometry types, coordinate bounds, statistics per property.
- xml from DescribeFeatureType: element names and types are listed.
- Statistics per field: filled / empty (None or empty after strip) / distinct; numeric if >= 95 %
  of filled values convert with float() after "," -> "."; value list if <= 40 distinct (top 15).
- sqlite: layers via pyogrio.list_layers, each layer read with geopandas.
Usage (VPS):  cd /root/voro-tree-qa && /root/gis_qa/.venv/bin/python r0/recon_r0.py
Writes results/r0_recon.json and prints a markdown summary.
"""
import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RES = ROOT / "results"
DL = "https://www.stadt-zuerich.ch/geodaten/download/Baumkataster?format="
WFS = "https://www.ogd.stadt-zuerich.ch/wfs/geoportal/Baumkataster?"
CANDIDATES = [
    ("dl_csv", DL + "10008", "text/csv,application/octet-stream;q=0.9"),
    ("dl_gpkg", DL + "10005", "application/geopackage+sqlite3,application/octet-stream;q=0.9"),
    ("dl_json", DL + "10009", "application/json,application/octet-stream;q=0.9"),
    ("wfs_describe", WFS + "service=WFS&version=1.1.0&request=DescribeFeatureType"
                           "&typename=baumkataster_baumstandorte", "*/*"),
    ("wfs11_standorte", WFS + "service=WFS&version=1.1.0&request=GetFeature"
                              "&typename=baumkataster_baumstandorte&outputFormat=GeoJSON", "*/*"),
    ("wfs20_standorte", WFS + "service=WFS&version=2.0.0&request=GetFeature"
                              "&typeNames=baumkataster_baumstandorte"
                              "&outputFormat=application/vnd.geo%2Bjson", "*/*"),
    ("wfs11_kronen", WFS + "service=WFS&version=1.1.0&request=GetFeature"
                           "&typename=baumkataster_kronendurchmesser&outputFormat=GeoJSON", "*/*"),
]
UA = "voro-tree-qa/0.0 (data quality research; github.com/MR73BIIO)"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def kind_of(b):
    h = b[:512].lstrip().lower()
    if b[:4] == b"PK\x03\x04":
        return "zip"
    if b[:16] == b"SQLite format 3\x00":
        return "sqlite"
    if h.startswith(b"<!doctype html") or h.startswith(b"<html"):
        return "html"
    if h.startswith(b"<?xml") or h.startswith(b"<"):
        return "xml"
    if h[:1] in (b"{", b"["):
        return "json"
    return "text"


def fetch(name, url, accept, day):
    rec = {"name": name, "url": url}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
        with urllib.request.urlopen(req, timeout=600) as r:
            body = r.read()
            rec.update(status=r.status, content_type=r.headers.get("Content-Type"),
                       content_disposition=r.headers.get("Content-Disposition"))
    except Exception as e:
        rec["error"] = repr(e)
        return rec, None
    rec.update(bytes=len(body), sha256=sha(body), kind=kind_of(body),
               head=body[:200].decode("utf-8", "replace"))
    ext = {"sqlite": "gpkg", "zip": "zip", "html": "html", "xml": "xml", "json": "json"}.get(rec["kind"], "txt")
    path = RAW / f"{name}_{day}.{ext}"
    path.write_bytes(body)
    rec["saved"] = str(path.relative_to(ROOT))
    return rec, body


def to_float(v):
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def field_stats(name, vals):
    filled = [str(v).strip() for v in vals if v is not None and str(v).strip()]
    nums = [x for x in (to_float(v) for v in filled) if x is not None]
    c = {"name": name, "filled": len(filled), "empty": len(vals) - len(filled),
         "distinct": len(set(filled))}
    if filled and len(nums) >= 0.95 * len(filled):
        nums.sort()
        c["numeric"] = {"min": nums[0], "p50": nums[len(nums) // 2], "max": nums[-1],
                        "not_numeric": len(filled) - len(nums)}
    cnt = Counter(filled)
    if c["distinct"] <= 40:
        c["values"] = cnt.most_common(15)
    else:
        c["top5"] = cnt.most_common(5)
        c["examples"] = filled[:3]
    return c


def recon_geojson(body):
    d = json.loads(body.decode("utf-8"))
    feats = d.get("features", []) if isinstance(d, dict) else []
    out = {k: d.get(k) for k in ("type", "numberMatched", "numberReturned", "totalFeatures", "crs")
           if isinstance(d, dict) and k in d}
    out["features"] = len(feats)
    gtypes, xs, ys, keys = Counter(), [], [], []
    for f in feats:
        g = f.get("geometry") or {}
        gtypes[g.get("type", "None")] += 1
        c = g.get("coordinates")
        if g.get("type") == "Point" and c and len(c) >= 2:
            xs.append(c[0]); ys.append(c[1])
        for k in (f.get("properties") or {}):
            if k not in keys:
                keys.append(k)
    out["geom_types"] = dict(gtypes)
    out["bounds"] = [min(xs), min(ys), max(xs), max(ys)] if xs else None
    out["fields"] = [field_stats(k, [(f.get("properties") or {}).get(k) for f in feats]) for k in keys]
    return out


def recon_describe(body):
    t = body.decode("utf-8", "replace")
    return {"elements": re.findall(r'<(?:xsd?:)?element[^>]*name="([^"]+)"[^>]*type="([^"]+)"', t)}


def recon_sqlite(path):
    import geopandas as gpd
    from pyogrio import list_layers
    out = []
    for lyr in [str(x[0]) for x in list_layers(path)]:
        g = gpd.read_file(path, layer=lyr)
        out.append({"layer": lyr, "features": len(g), "crs": str(g.crs),
                    "geom_types": dict(Counter(g.geometry.geom_type.fillna("None"))),
                    "columns": [field_stats(c, g[c].tolist()) for c in g.columns if c != g.geometry.name]})
    return out


def recon_text(body):
    text = body.decode("utf-8-sig", "replace")
    first = text.split("\n", 1)[0]
    delim = max(",;\t|", key=first.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    header, data = rows[0], rows[1:]
    return {"delimiter": delim, "rows": len(data),
            "fields": [field_stats(h, [r[i] if i < len(r) else None for r in data])
                       for i, h in enumerate(header)]}


def print_fields(fields):
    for c in fields:
        line = f"- {c['name']}: filled {c['filled']}, empty {c['empty']}, distinct {c['distinct']}"
        if "numeric" in c:
            n = c["numeric"]
            line += f", min {n['min']}, p50 {n['p50']}, max {n['max']}, not numeric {n['not_numeric']}"
        print(line)
        print(f"    values: {c['values']}" if "values" in c
              else f"    top5: {c['top5']} | examples: {c['examples']}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    RES.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y%m%d")
    rep = {"run_utc": now.isoformat(timespec="seconds"), "candidates": []}
    print(f"# R0 v3 reconnaissance - {rep['run_utc']}")
    for name, url, accept in CANDIDATES:
        rec, body = fetch(name, url, accept, day)
        print(f"\n## {name}\n   {url}")
        if body is None:
            print(f"   ERROR {rec['error']}")
            rep["candidates"].append(rec)
            continue
        print(f"   HTTP {rec['status']}, {rec['content_type']}, {rec['bytes']} B, kind {rec['kind']}, sha256 {rec['sha256']}")
        try:
            if rec["kind"] == "json":
                rec["recon"] = r = recon_geojson(body)
                print(f"   {({k: r[k] for k in r if k not in ('fields',)})}")
                print_fields(r["fields"])
            elif rec["kind"] == "xml" and name == "wfs_describe":
                rec["recon"] = r = recon_describe(body)
                print(f"   elements: {r['elements']}")
            elif rec["kind"] == "sqlite":
                rec["recon"] = r = recon_sqlite(ROOT / rec["saved"])
                for l in r:
                    print(f"   layer {l['layer']}: {l['features']} features, {l['crs']}, {l['geom_types']}")
                    print_fields(l["columns"])
            elif rec["kind"] == "zip":
                with zipfile.ZipFile(io.BytesIO(body)) as z:
                    rec["recon"] = [(m.filename, m.file_size) for m in z.infolist()]
                print(f"   zip members: {rec['recon']}")
            elif rec["kind"] == "text":
                rec["recon"] = r = recon_text(body)
                print(f"   rows {r['rows']}, delimiter {r['delimiter']!r}")
                print_fields(r["fields"])
            else:
                print(f"   head: {rec['head']!r}")
        except Exception as e:
            rec["recon_error"] = repr(e)
            print(f"   RECON ERROR {e!r}\n   head: {rec['head']!r}")
        rep["candidates"].append(rec)
    (RES / "r0_recon.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nwritten: results/r0_recon.json")


if __name__ == "__main__":
    sys.exit(main())
