# M0 — prediction (before the measurement script and before the run)

Question: does the Zurich tree register show, in its own fields, the limits the city declares
(estimated crowns, two accuracy classes, digitised history), and are its fields consistent with each other?

Data: WFS 1.1.0 point layer, sha256 `8c84839fdca98eaf740275b74850b857869b677cf1c3fe6743c4d44114cc4b09`, 81 142 trees.
Reconnaissance disclosed: docs/R0_NOTE.md lists what was already seen. Points below are measured only in M0.
Where a point touches something seen in R0, the line says so.

## Definitions

- Text fields compared after strip, case-insensitive. Empty = None or empty after strip.
- First / second word = split of `baumnamelat` on spaces.
- Measured = `genauigkeit` starts with "Eingemessen".
- Distances in LV95 (EPSG:2056), projected from WGS84 with pyproj (geopandas `to_crs`).
- Close pair = two trees closer than 0.50 m (each pair counted once).

## Points

| # | Measured | Prediction | Note |
|---|---|---|---|
| P1 | `baumgattunglat` = first word of `baumnamelat` | ≥ 98.0 % match **and** ≥ 1 mismatch | one mismatch seen in R0 (Juglas / Juglans) |
| P2 | `baumartlat` = second word of `baumnamelat` (where `baumartlat` filled) | ≥ 95.0 % | |
| P3 | trees with `pflanzjahr` ≥ 2022: share with `kronendurchmesser` ≥ 8 | ≥ 5.0 % | young tree, crown ≥ 8 m = implausible |
| P4a | Strassenbaum: share Measured | ≥ 70.0 % | city: street trees surveyed since 2001 |
| P4b | Parkbaum: share Measured | ≤ 30.0 % | city: green spaces 0.5–2 m |
| P5 | Strassenbaum with `pflanzjahr` ≥ 2001: share Measured | ≥ 85.0 % | |
| P6 | `kategorie` Strassenbaum ⇔ `status` in {Strassenbaum, Strassenbaum (A)} | 0 mismatches | sums matched in R0 |
| P7 | every non-empty `baumtyp` has exactly one `baumtyptext`; codes 3 and 4 share one text; empty code ⇒ "nicht zugeordnet" | all three true | inferred from R0 counts |
| P8 | close pairs (< 0.50 m) | 1 … 811 (≤ 1 % of trees) | |
| P9 | trees with `pflanzjahr` < 1850 | 1 … 100 | min 1665 seen in R0 |
| P10a | `baumnummer` = `poi_id` | 81 142 / 81 142 | |
| P10b | share of `baumnummer` starting "nn-" | ≥ 1.0 % | prefix seen in R0 examples |
| P11 | share of crown exactly 8 m: Bildschirmeingabe vs Eingemessen | Bildschirmeingabe higher | 8 m = the city's default value |

Verdict per point: CONFIRMED / REFUTED / NO DATA. Life verdict = worst point.

## Consequences (fixed now)

- P1, P2 CONFIRMED → name consistency becomes B2 check T3; the mismatches are listed as baseline findings.
  REFUTED → name fields are not a reliable pair; T3 reports the share only.
- P3 CONFIRMED → B2 check T5 (crown vs age). REFUTED → T5 dropped, crown checked only for range.
- P4a, P4b, P5 CONFIRMED → the report states the city's accuracy classes as measured facts.
  Any REFUTED → the data does not show what the city declares; that is a finding for the report.
- P6, P7 CONFIRMED → consistency checks in B2 with baseline 0; codes 3 and 4 with one text = finding (ambiguous code).
- P8 → B2 check T6 (close pairs), threshold 0.50 m; outside the range → threshold reviewed before B2.
- P9 → planting years before 1850 are reported "to verify", never as errors (old trees exist).
- P10 → identifier check T2. P11 CONFIRMED → 8 m treated as a likely default in the report; REFUTED → not.
