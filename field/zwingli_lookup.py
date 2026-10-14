#!/usr/bin/env python3
"""voro-tree-qa - field check list around the Zwingli monument (Wasserkirche, Limmatquai, Zurich).

Not a life. No prediction, no verdict. It only lists what the Baumkataster says
about the trees near one point, so they can be checked on site one by one.

For every tree within RADIUS metres of the point it prints:
  - distance from the point and its position (WGS84 + OSM link),
  - every field of the record verbatim (baumnummer, baumnamelat, pflanzjahr, ...),
  - in which downloaded snapshots (data/raw/*standorte*.json) this baumnummer appears.

Note on "since when in the register": pflanzjahr is the planting year, not the date
the record was entered. With a single snapshot the first-seen date only says
"present on that download day". It becomes informative once more snapshots exist.

Usage (VPS):
  cd /root/voro-tree-qa && python3 field/zwingli_lookup.py [radius_m] [lat lon]
Default point: 47.36980 N, 8.54330 E (Zwingli-Denkmal, Wasserkirche). Default radius 60 m.
Standard library only.
"""
import glob
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DEFAULT_LAT, DEFAULT_LON, DEFAULT_R = 47.36980, 8.54330, 60.0


def wgs84_to_lv95(lat, lon):
    """swisstopo approximate formula, accuracy about 1 m - enough for a field list."""
    p = (lat * 3600 - 169028.66) / 10000
    l = (lon * 3600 - 26782.5) / 10000
    e = (2600072.37 + 211455.93 * l - 10938.51 * l * p - 0.36 * l * p * p - 44.54 * l ** 3)
    n = (1200147.07 + 308807.95 * p + 3745.25 * l * l + 76.63 * p * p
         - 194.56 * l * l * p + 119.79 * p ** 3)
    return e, n


def lv95_to_wgs84(e, n):
    y = (e - 2600000) / 1e6
    x = (n - 1200000) / 1e6
    lon = (2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3) * 100 / 36
    lat = (16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x
           - 0.0447 * y * y * x - 0.0140 * x ** 3) * 100 / 36
    return lat, lon


def snapshot_date(path):
    m = re.search(r"(20\d{6})", path.name)
    return m.group(1) if m else path.name


def load(path):
    raw = path.read_bytes()
    data = json.loads(raw)
    return hashlib.sha256(raw).hexdigest(), data.get("features", [])


def point_xy(feat):
    """Returns (lv95_e, lv95_n, lat, lon) or None."""
    g = feat.get("geometry") or {}
    c = g.get("coordinates")
    if not c or g.get("type") != "Point":
        return None
    a, b = float(c[0]), float(c[1])
    if a > 100000:            # LV95 already
        lat, lon = lv95_to_wgs84(a, b)
        return a, b, lat, lon
    e, n = wgs84_to_lv95(b, a)  # GeoJSON order: lon, lat
    return e, n, b, a


def main():
    args = sys.argv[1:]
    radius = float(args[0]) if args else DEFAULT_R
    lat0, lon0 = (float(args[1]), float(args[2])) if len(args) >= 3 else (DEFAULT_LAT, DEFAULT_LON)
    e0, n0 = wgs84_to_lv95(lat0, lon0)

    snaps = sorted((Path(p) for p in glob.glob(str(RAW / "*standorte*.json"))), key=snapshot_date)
    if not snaps:
        sys.exit(f"No snapshot found in {RAW} (expected *standorte*.json)")

    seen = {}          # baumnummer -> list of snapshot dates
    latest_hits = []
    for i, path in enumerate(snaps):
        sha, feats = load(path)
        date = snapshot_date(path)
        print(f"snapshot {date}  {path.name}  features={len(feats)}  sha256={sha}")
        for f in feats:
            xy = point_xy(f)
            if xy is None:
                continue
            d = math.hypot(xy[0] - e0, xy[1] - n0)
            if d > radius:
                continue
            props = f.get("properties") or {}
            nr = str(props.get("baumnummer") or props.get("poi_id") or "?").strip()
            seen.setdefault(nr, []).append(date)
            if i == len(snaps) - 1:
                latest_hits.append((d, nr, xy, props))

    latest_hits.sort(key=lambda t: t[0])
    print()
    print(f"point {lat0:.5f} N {lon0:.5f} E  (LV95 {e0:.1f} / {n0:.1f})  radius {radius:.0f} m")
    print(f"trees in latest snapshot within radius: {len(latest_hits)}")
    print("=" * 72)

    for k, (d, nr, xy, props) in enumerate(latest_hits, 1):
        print(f"[{k}] baumnummer {nr}   distance {d:.1f} m")
        print(f"    position {xy[2]:.6f} N {xy[3]:.6f} E   LV95 {xy[0]:.1f} / {xy[1]:.1f}")
        print(f"    https://www.openstreetmap.org/?mlat={xy[2]:.6f}&mlon={xy[3]:.6f}#map=20/{xy[2]:.6f}/{xy[3]:.6f}")
        dates = seen.get(nr, [])
        print(f"    in snapshots: {', '.join(dates)}  (first seen {dates[0] if dates else '-'})")
        for key in sorted(props):
            print(f"    {key:22} {props[key]}")
        print("    FIELD: species seen ______  needles/cones ______  girth at 1 m ______ cm")
        print("-" * 72)

    gone = [nr for nr, ds in seen.items() if snaps and snapshot_date(snaps[-1]) not in ds]
    if gone:
        print(f"in older snapshots but not in latest: {', '.join(sorted(gone))}")
    if len(snaps) == 1:
        print("only one snapshot: 'first seen' = download day, not entry date. pflanzjahr = planting year.")


if __name__ == "__main__":
    main()
