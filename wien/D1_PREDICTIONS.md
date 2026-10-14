# voro-tree-qa · Wien · D1 predictions (diagnosis of M0, Puls #35)

Source: `ogdwien:BAUMKATOGD`, same cached data as M0 (233 082 records).
Thresholds are frozen with this commit. The D1 script is written after this commit.

## What was already seen before writing this

D0 (`wien/d0/DIAGNOSIS.json`, commit 8714c0c) was descriptive, without predictions. It showed:

- P03 was a false confirmation: 4 144 of 4 154 hits are *Pyrus calleryana 'Chanticleer'*
  ("leer" inside the cultivar name), 7 are *Juniperus 'Keteleeri'*, 3 are "Baumgruppe".
- 3 534 records carry "Jungbaum wird gepflanzt" in `GATTUNG_ART`.
- P10: 121 906 addresses have no district prefix (format); 1 203 have a prefix that differs from `BEZIRK`,
  mostly neighbouring districts (22/21, 18/17).
- P11: all 595 non-agreements are records without `BEZIRK` or geometry.
- P09: 17 records with crown code and crown text in conflict.
- P07: 257 records, species and planting years; one trunk of 6 060 cm.
- P06: last-digit shares of planting years before and from 2006.

The predictions below cover only things D0 did not measure.

## Predictions

| ID | Explains | Claim | Measure | Confirmed if |
|----|----------|-------|---------|--------------|
| H1 | P04 | Street trees have a planting year more often than park trees | share `PFLANZJAHR = 0` in `GEBIETSGRUPPE = 'MA 28 - Straße, Grünanlage'` vs `'MA 42 - Parkanlage'` | MA 28 share is lower by ≥ 10 percentage points |
| H2 | P10 | Prefix/district conflicts are border streets | among the 1 203 records whose address prefix differs from `BEZIRK`, distance from the point to the boundary of the prefix district | ≥ 80 % within 200 m |
| H3 | P07 | Young thick-trunk trees are site clusters, not scattered errors | the 257 records with `PFLANZJAHR ≥ 2016` and `STAMMUMFANG ≥ 80` cm, grouped by `OBJEKT_STRASSE` | ≥ 50 % on at most 10 distinct `OBJEKT_STRASSE` values |
| H4 | P03/P12 | "Jungbaum wird gepflanzt" are placeholders, not measured trees | the 3 534 records with that `GATTUNG_ART` | ≥ 95 % have `PFLANZJAHR = 0` and `STAMMUMFANG` 0 or null |

## Rules

- Distances in metres, local equirectangular approximation around Vienna (48.2° N).
- A result exactly on the threshold counts as confirmed.
- M0 verdicts do not change. D1 explains them; it does not re-score them.
