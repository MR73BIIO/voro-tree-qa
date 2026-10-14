# voro-tree-qa · Wien · Predictions (before M0)

Source: `ogdwien:BAUMKATOGD`, https://data.wien.gv.at/daten/geo (WFS 1.1.0)
Written after R0 (schema, record count, one sample record). No value distributions seen.
Thresholds are frozen with this commit. M0 measures them unchanged.

## R0 observation (not a prediction)

- WFS returns **233 082** records. The city states "über 393 000 Bäume" in the Baumkataster
  (wien.gv.at/umwelt/stadtbaeume). Ratio ≈ 59 %. The cause is not checked yet.
- Crown diameter and height are **classes** (code + text), not metres.
- `PFLANZJAHR = 0` is used together with `PFLANZJAHR_TXT = 'nicht definiert'`.

## Self-statements of the city used as reference

- S1: "über 99 000 Straßenbäume" (wien.gv.at/umwelt/stadtbaeume)
- S2: tree age is estimated from trunk circumference; exact planting year known only from 2006
  (wien.gv.at/statistik/lebensraum/stadtgebiet)

## Predictions

| ID | Claim | Measure | Threshold | Confirmed if |
|----|-------|---------|-----------|--------------|
| P01 | OGD contains the street trees the city declares (S1) | records with `GEBIETSGRUPPE` containing "straße"/"strasse" (case-insensitive) | 99 000 | count ≥ 99 000 |
| P02 | `DATENFUEHRUNG` is dominated by one value | share of `'magistrat'` | 90 % | share ≥ 90 % |
| P03 | The catalogue holds records that are not trees | `GATTUNG_ART` containing "leer", "pflanzstandort" or "baumgruppe" (case-insensitive) | 1 000 | count ≥ 1 000 |
| P04 | Most planting years are unknown (S2) | share of `PFLANZJAHR = 0` | 50 % | share ≥ 50 % |
| P05 | Planting year 0 and text "nicht definiert" always go together | agreement in both directions | 99.9 % | agreement ≥ 99.9 % |
| P06 | Known planting years before 2006 are rounded (S2) | among `1 ≤ PFLANZJAHR < 2006`, share of years ending in 0 or 5 (uniform = 20 %) | 30 % | share ≥ 30 % |
| P07 | Young trees have plausible trunks | among `PFLANZJAHR ≥ 2016`, share with `STAMMUMFANG ≥ 80` cm | 0.5 % | share ≤ 0.5 % |
| P08 | Trunk circumference is mostly filled | share with `STAMMUMFANG` = 0 or null | 10 % | share ≤ 10 % |
| P09 | Code and text fields agree | `STAMMUMFANG` = number in `STAMMUMFANG_TXT`; each `BAUMHOEHE` and `KRONENDURCHMESSER` code maps to exactly one text | 99.5 % / 1:1 | both hold |
| P10 | District attribute agrees with the address | `BEZIRK` = leading number of `OBJEKT_STRASSE` | 99 % | agreement ≥ 99 % |
| P11 | District attribute agrees with the geometry | point inside the district polygon (`ogdwien:BEZIRKSGRENZEOGD`) of its `BEZIRK` | 98 % | agreement ≥ 98 % |
| P12 | Species field follows one pattern | `GATTUNG_ART` matches `Latin name (German name)` | 95 % | share ≥ 95 % |

## Rules

- Denominator: all 233 082 records unless the row says otherwise.
- A result exactly on the threshold counts as confirmed.
- Nothing is re-thresholded after measuring. A wrong prediction stays wrong in the report.
