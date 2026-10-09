#!/usr/bin/env python3
"""voro-tree-qa R0 - reconnaissance of the Zurich tree register (Baumkataster).

R0 is NOT a life. It makes no prediction and judges nothing. It only answers:
what is in the published files (fields, counts, value ranges, layers, CRS)?
Its output is the input for docs/M0_PREDICTION.md, which is committed before M0 runs.
This is disclosed in M0_PREDICTION ("reconnaissance disclosed"), as in B2b.

Source: Open Data Zurich, dataset geo_baumkataster, licence CC0.
  CSV  https://www.stadt-zuerich.ch/geodaten/download/Baumkataster?format=10008
  GPKG https://www.stadt-zuerich.ch/geodaten/download/Baumkataster?format=10005

Definitions fixed before the run (this file is committed before the first run):
- Files are saved to data/raw/ with the download date in the name; SHA-256 of every file is printed.
- A zip is extracted to data/raw/<name>/; every member is listed with size and SHA-256.
- CSV: encoding utf-8-sig, fallback latin-1. Delimiter = the one of , ; TAB | that occurs most often
  in the header line (v2: the csv.Sniffer of v1 failed on this file; disclosed in the commit).
- A file that cannot be read is recorded with its error and its first 300 characters; the run continues.
- Empty = cell empty after strip.
- Numeric column = at least 95 % of non-empty cells convert with float() after "," -> ".".
- Value list printed for columns with at most 40 distinct values (top 15 by count).
- GPKG: every layer read with geopandas; count, CRS, geometry types, columns, bounds, empty geometries.
Usage (VPS, gis_qa venv has geopandas):
  cd /root/voro-tree-qa && /root/gis_qa/.venv/bin/python r0/recon_r0.py
Writes results/r0_recon.json and prints a markdown summary.
"""
import csv
import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RES = ROOT / "results"
SOURCES = {
    "csv": "https://www.stadt-zuerich.ch/geodaten/download/Baumkataster?format=10008",
    "gpkg": "https://www.stadt-zuerich.ch/geodaten/download/Baumkataster?format=10005",
}
UA = {"User-Agent": "voro-tree-qa/0.0 (data quality research; github.com/MR73BIIO)"}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fetch(kind, url, day):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r:
        body = r.read()
        info = {"url": url, "status": r.status, "content_type": r.headers.get("Content-Type"),
                "content_disposition": r.headers.get("Content-Disposition"), "bytes": len(body),
                "sha256": sha(body)}
    is_zip = body[:4] == b"PK\x03\x04"
    name = f"baumkataster_{kind}_{day}" + (".zip" if is_zip else f".{kind}")
    (RAW / name).write_bytes(body)
    info["saved"] = f"data/raw/{name}"
    info["zip"] = is_zip
    files = []
    if is_zip:
        out = RAW / name[:-4]
        out.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(body)) as z:
            for m in z.infolist():
                if m.is_dir():
                    continue
                data = z.read(m)
                p = out / Path(m.filename).name
                p.write_bytes(data)
                files.append({"member": m.filename, "bytes": len(data), "sha256": sha(data),
                              "path": str(p.relative_to(ROOT))})
    else:
        files.append({"member": name, "bytes": len(body), "sha256": info["sha256"],
                      "path": info["saved"]})
    info["files"] = files
    return info


def to_float(s):
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def recon_csv(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    first = text.split("\n", 1)[0]
    delim = max(",;\t|", key=first.count)
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    header, body = rows[0], rows[1:]
    cols = []
    for i, h in enumerate(header):
        vals = [(r[i].strip() if i < len(r) else "") for r in body]
        filled = [v for v in vals if v]
        nums = [x for x in (to_float(v) for v in filled) if x is not None]
        c = {"name": h, "filled": len(filled), "empty": len(vals) - len(filled),
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
        cols.append(c)
    widths = Counter(len(r) for r in body)
    return {"encoding": enc, "delimiter": delim, "header_line": first[:300], "rows": len(body),
            "row_widths": dict(widths), "columns": cols}


def recon_gpkg(path):
    import geopandas as gpd
    try:
        from pyogrio import list_layers
        layers = [str(x[0]) for x in list_layers(path)]
    except Exception:
        import fiona
        layers = list(fiona.listlayers(path))
    out = []
    for lyr in layers:
        g = gpd.read_file(path, layer=lyr)
        geom = g.geometry
        out.append({
            "layer": lyr, "features": len(g), "crs": str(g.crs),
            "geom_types": dict(Counter(geom.geom_type.fillna("None"))),
            "empty_or_null": int(geom.isna().sum() + geom.is_empty.sum()),
            "bounds": [round(float(x), 2) for x in geom.total_bounds] if len(g) else None,
            "columns": [f"{c}:{t}" for c, t in g.dtypes.astype(str).items() if c != g.geometry.name],
        })
    return out


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    RES.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y%m%d")
    rep = {"run_utc": now.isoformat(timespec="seconds"), "downloads": {}, "csv": [], "gpkg": []}
    for kind, url in SOURCES.items():
        try:
            rep["downloads"][kind] = fetch(kind, url, day)
        except Exception as e:  # recorded, not hidden
            rep["downloads"][kind] = {"url": url, "error": repr(e), "files": []}
    for f in rep["downloads"]["csv"]["files"]:
        if f["path"].lower().endswith(".csv"):
            try:
                rep["csv"].append({"path": f["path"], **recon_csv(ROOT / f["path"])})
            except Exception as e:
                head = (ROOT / f["path"]).read_bytes()[:300].decode("utf-8", "replace")
                rep["csv"].append({"path": f["path"], "error": repr(e), "head": head})
    for f in rep["downloads"]["gpkg"]["files"]:
        if f["path"].lower().endswith(".gpkg"):
            try:
                rep["gpkg"].append({"path": f["path"], "layers": recon_gpkg(ROOT / f["path"])})
            except Exception as e:
                rep["gpkg"].append({"path": f["path"], "error": repr(e), "layers": []})
    (RES / "r0_recon.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"# R0 reconnaissance - {rep['run_utc']}\n")
    for kind, d in rep["downloads"].items():
        if "error" in d:
            print(f"## download {kind}: ERROR {d['error']}")
            continue
        print(f"## download {kind}: HTTP {d['status']}, {d['bytes']} B, zip={d['zip']}, sha256 {d['sha256']}")
        print(f"   type: {d['content_type']} | {d['content_disposition']}")
        for f in d["files"]:
            print(f"   - {f['member']}  {f['bytes']} B  {f['sha256']}")
    for c in rep["csv"]:
        if "error" in c:
            print(f"\n## CSV {c['path']}: ERROR {c['error']}\n   head: {c['head']!r}")
            continue
        print(f"\n## CSV {c['path']}: rows {c['rows']}, encoding {c['encoding']}, delimiter '{c['delimiter']}', row widths {c['row_widths']}")
        print(f"   header: {c['header_line']!r}")
        for col in c["columns"]:
            line = f"- {col['name']}: filled {col['filled']}, empty {col['empty']}, distinct {col['distinct']}"
            if "numeric" in col:
                n = col["numeric"]
                line += f", min {n['min']}, p50 {n['p50']}, max {n['max']}, not numeric {n['not_numeric']}"
            print(line)
            if "values" in col:
                print(f"    values: {col['values']}")
            else:
                print(f"    top5: {col['top5']} | examples: {col['examples']}")
    for g in rep["gpkg"]:
        print(f"\n## GPKG {g['path']}" + (f": ERROR {g['error']}" if "error" in g else ""))
        for l in g["layers"]:
            print(f"- layer {l['layer']}: {l['features']} features, {l['crs']}, {l['geom_types']}, "
                  f"empty/null {l['empty_or_null']}, bounds {l['bounds']}")
            print(f"    columns: {l['columns']}")
    if not rep["csv"]:
        print("\nWARNING: no .csv file found in the CSV download")
    if not rep["gpkg"]:
        print("\nWARNING: no .gpkg file found in the GPKG download")
    print("\nwritten: results/r0_recon.json")


if __name__ == "__main__":
    sys.exit(main())
