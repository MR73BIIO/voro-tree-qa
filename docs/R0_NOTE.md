# R0 — reconnaissance note

R0 is not a life: no prediction, no verdict. It is disclosed here because M0_PREDICTION is written after it.
Script: r0/recon_r0.py (v1 308fa80, v2 872e555, v3 7348dab). Full output: results/r0_recon.json.

## Which endpoint delivers the data

| Endpoint | Answer |
|---|---|
| Download links of the dataset page (CSV 10008, GPKG 10005, JSON 10009) | HTML page of the city geoportal (41.7 kB), not data |
| WFS 1.1.0 GetFeature `baumkataster_baumstandorte`, GeoJSON | **81 142 points, 46.2 MB**, WGS84, sha256 `8c84839fdca98eaf740275b74850b857869b677cf1c3fe6743c4d44114cc4b09` |
| WFS 2.0.0 GetFeature, same layer | HTTP 500 |
| WFS 1.1.0 GetFeature `baumkataster_kronendurchmesser` | 120.7 MB, JSON cut 530 bytes before the end (invalid) |
| WFS DescribeFeatureType | 1.9 kB XML; the parser of v3 found no elements |

Source for M0 onward: the WFS 1.1.0 point layer, downloaded 2026-10-09 15:44 UTC, gated by the SHA-256 above.
The crown layer is not used: the crown diameter is also an attribute of the point layer.

## What R0 already showed (seen before M0, so not predicted in M0)

- 81 142 features, all Point; `objectid` 1…81 142 without a gap; `baumnummer` and `poi_id` 81 142 distinct each.
- 17 attributes; `geometrie_gdo` empty in all features.
- `kronendurchmesser` filled in 81 142 / 81 142; value 8 in 13 815 (17.0 %); 7 in 5 328, 9 in 4 371.
- `genauigkeit`: Bildschirmeingabe 46 654, Eingemessen 29 510, Unbekannte Qualität 4 162, Digitalisierung oder ELTA2 677, Luftbild 128, Eingemessen (Nachpflanzung) 8, (unbekannter Standort) 2, (neuer Baum) 1.
- `kategorie`: Parkbaum 57 878, Strassenbaum 23 264. `status` Strassenbaum 23 257 + Strassenbaum (A) 7 = 23 264.
- `baumtyp` (0–6, empty 1 066) vs `baumtyptext` (6 texts): the counts suggest codes 3 and 4 share one text and empty code = "nicht zugeordnet".
- `pflanzjahr` empty 8 308; min 1665, max 2026.
- `strasse` empty 3 417; `baumartlat` empty 1 640.
- One example row: `baumnamelat` "Juglas regia cv." with `baumgattunglat` "Juglans".
