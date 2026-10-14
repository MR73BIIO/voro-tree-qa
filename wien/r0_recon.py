#!/usr/bin/env python3
"""
voro-tree-qa · Wien · R0 (rozpoznanie)

Co robi:   GetCapabilities -> DescribeFeatureType -> liczba rekordów (hits) -> 1 rekord próbny.
Czego NIE robi: nie liczy rozkładów, braków ani wartości pól.
           Profil wartości dopiero w M0, PO zacommitowaniu przewidywań z progami.

Użycie:    python3 wien/r0_recon.py <ścieżka_raportu.txt>
Zależności: tylko biblioteka standardowa.
"""
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://data.wien.gv.at/daten/geo"
TYPE = "ogdwien:BAUMKATOGD"
HERE = Path(__file__).resolve().parent
RAW = HERE / "r0"
UA = {"User-Agent": "voro-tree-qa R0 (MR73BIIO)"}


def get(params, timeout=180):
    url = BASE + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return url, r.read()


def local(tag):
    return tag.rsplit("}", 1)[-1]


def step_capabilities(lines):
    url, body = get({"service": "WFS", "request": "GetCapabilities", "version": "1.1.0"})
    root = ET.fromstring(body)
    found = []
    for el in root.iter():
        if local(el.tag) != "FeatureType":
            continue
        name = title = ""
        for ch in el:
            if local(ch.tag) == "Name":
                name = (ch.text or "").strip()
            elif local(ch.tag) == "Title":
                title = (ch.text or "").strip()
        if "BAUM" in name.upper() or "baum" in title.lower():
            found.append((name, title))
    lines.append(f"URL: {url}")
    lines.append(f"Warstwy z 'Baum' w nazwie/tytule: {len(found)}")
    for n, t in found:
        lines.append(f"  - {n} | {t}")
    lines.append(f"{TYPE} obecny: {'TAK' if any(n == TYPE for n, _ in found) else 'NIE'}")


def step_schema(lines):
    url, body = get({"service": "WFS", "request": "DescribeFeatureType",
                     "version": "1.1.0", "typeName": TYPE})
    (RAW / "describe_feature_type.xsd").write_bytes(body)
    root = ET.fromstring(body)
    fields = [(e.get("name"), e.get("type"), e.get("nillable"), e.get("minOccurs"))
              for e in root.iter() if local(e.tag) == "element" and e.get("type")]
    lines.append(f"URL: {url}")
    lines.append(f"Liczba pól: {len(fields)}")
    lines.append(f"{'pole':<28}{'typ':<26}{'nillable':<10}minOccurs")
    for n, t, nl, mo in fields:
        lines.append(f"{n:<28}{t:<26}{str(nl):<10}{mo}")


def step_hits(lines):
    url, body = get({"service": "WFS", "request": "GetFeature", "version": "1.1.0",
                     "typeName": TYPE, "resultType": "hits"})
    root = ET.fromstring(body)
    n = root.get("numberOfFeatures") or root.get("numberMatched")
    lines.append(f"URL: {url}")
    lines.append(f"Liczba rekordów (hits): {n}")


def step_sample(lines):
    url, body = get({"service": "WFS", "request": "GetFeature", "version": "1.1.0",
                     "typeName": TYPE, "maxFeatures": "1",
                     "srsName": "EPSG:4326", "outputFormat": "json"})
    data = json.loads(body)
    (RAW / "sample_1.json").write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    feats = data.get("features") or []
    lines.append(f"URL: {url}")
    if not feats:
        lines.append("Brak rekordu w odpowiedzi.")
        return
    f = feats[0]
    lines.append(f"geometry: {json.dumps(f.get('geometry'), ensure_ascii=False)}")
    for k, v in (f.get("properties") or {}).items():
        lines.append(f"  {k} = {v!r}")


def main():
    if len(sys.argv) < 2:
        sys.exit("Podaj ścieżkę raportu .txt")
    out = Path(sys.argv[1])
    RAW.mkdir(parents=True, exist_ok=True)

    lines = [
        "voro-tree-qa · Wien · R0",
        f"Czas (UTC): {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"Źródło: {BASE}  typeName={TYPE}",
        "Licencja do potwierdzenia w metadanych data.gv.at (oczekiwane CC BY 4.0, Quelle: Stadt Wien – data.wien.gv.at)",
        "",
        "== Selbstauskunft der Stadt (do przepisania przed przewidywaniami) ==",
        "wien.gv.at/umwelt/stadtbaeume: ponad 393 000 drzew w katastrze, w tym ponad 99 000 Straßenbäume;",
        "  pola dla obywateli: Baumart, Stammumfang, Kronendurchmesser, Höhe, Pflanzjahr 'falls vorhanden'.",
        "wien.gv.at/statistik/lebensraum/stadtgebiet: wiek drzew szacowany ze Stammumfang;",
        "  dokładny Pflanzjahr znany dopiero od 2006.",
        "",
    ]
    for title, fn in [("1. GetCapabilities", step_capabilities),
                      ("2. DescribeFeatureType", step_schema),
                      ("3. Liczba rekordów", step_hits),
                      ("4. Rekord próbny", step_sample)]:
        lines.append(f"== {title} ==")
        try:
            fn(lines)
        except Exception as e:  # raport ma powstać nawet przy błędzie jednego kroku
            lines.append(f"BŁĄD: {type(e).__name__}: {e}")
        lines.append("")

    lines.append("STOP: bez profilowania wartości. Następny krok: przewidywania z progami -> commit -> M0.")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"Raport: {out}")


if __name__ == "__main__":
    main()
