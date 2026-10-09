# M0 — outcome

Prediction: docs/M0_PREDICTION.md, committed before the script. Script: m0/measure_m0.py (0580d1d), committed before the run.
Reconnaissance disclosed: docs/R0_NOTE.md. Input: WFS 1.1.0 point layer, sha256 `8c84839f…59fc0f1`, 81 142 trees.
Run: 2026-10-09 on the VPS. Results: results/m0_results.json, results/m0_results.md.

## Results

| # | Measured | Value | Prediction | Verdict |
|---|---|---|---|---|
| P1 | `baumgattunglat` = first word of `baumnamelat` | 80 577 / 81 142 (99.30 %), 565 mismatches | ≥ 98.0 % and ≥ 1 mismatch | CONFIRMED |
| P2 | `baumartlat` = second word of `baumnamelat` | 71 351 / 79 502 (89.75 %) | ≥ 95.0 % | **REFUTED** |
| P3 | `pflanzjahr` ≥ 2022: crown ≥ 8 m | 921 / 9 065 (10.16 %) | ≥ 5.0 % | CONFIRMED |
| P4a | Strassenbaum: Measured | 20 435 / 23 264 (87.84 %) | ≥ 70.0 % | CONFIRMED |
| P4b | Parkbaum: Measured | 9 083 / 57 878 (15.69 %) | ≤ 30.0 % | CONFIRMED |
| P5 | Strassenbaum, `pflanzjahr` ≥ 2001: Measured | 12 076 / 14 504 (83.26 %) | ≥ 85.0 % | **REFUTED** |
| P6 | `kategorie` ⇔ `status` | 0 mismatches | 0 | CONFIRMED |
| P7 | `baumtyp` ↔ `baumtyptext` | one text per code; 3 and 4 share "Höhe:10-20m, Breite:<10m"; empty → "nicht zugeordnet" | all true | CONFIRMED |
| P8 | close pairs < 0.50 m | 38 (2 at the same point) | 1 … 811 | CONFIRMED |
| P9 | `pflanzjahr` < 1850 | 48 (1665 ×1 … 1836 ×21) | 1 … 100 | CONFIRMED |
| P10a | `baumnummer` = `poi_id` | 81 142 / 81 142 | 81 142 / 81 142 | CONFIRMED |
| P10b | `baumnummer` starting "nn-" | 1 568 / 81 142 (1.93 %) | ≥ 1.0 % | CONFIRMED |
| P11 | crown exactly 8 m: Bildschirmeingabe vs Measured | 16.22 % vs 9.34 % | Bildschirmeingabe higher | CONFIRMED |

**Life verdict: REFUTED, 11/13 CONFIRMED.** Both REFUTED points have consequences written before the run (section "Consequences" of the prediction); they are applied below.

## Consequences applied

- P1 CONFIRMED → B2 check T3 (genus vs Latin name); the 565 mismatches are baseline findings (results/m0_results.json, first 200 listed).
- P2 REFUTED → the species field and the second word of the name are not a reliable pair; T3 reports the species share only, no finding per record.
  Not yet known: how much of the 10.25 % comes from naming conventions (hybrids "x", cultivars, subspecies) and how much from real errors. Diagnosis = next life (M0b).
- P3 CONFIRMED → B2 check T5 (crown vs age): 921 trees planted 2022 or later carry a crown of 8 m or more.
- P4a, P4b CONFIRMED → the report states as measured facts: street trees 87.8 % surveyed, park trees 15.7 %.
- P5 REFUTED → finding for the report: 2 428 street trees planted 2001 or later are not marked as surveyed (city statement: surveyed since 2001).
- P6, P7 CONFIRMED → consistency checks in B2 with baseline 0; codes 3 and 4 with one text = finding (ambiguous code, 15 248 trees).
- P8 → B2 check T6, threshold 0.50 m stays.
- P9 → years before 1850 reported "to verify" (48 trees; 21 with year 1836).
- P10 → identifier check T2 (unique, = poi_id). P11 CONFIRMED → 8 m is reported as a likely default value (16.2 % on screen-entered trees, 9.3 % on surveyed trees).

## Facts for the DE plane (usable after this commit)

- 81 142 trees in the public register of the City of Zurich (WFS, 9.10.2026).
- 8 m crown: 16.2 % of screen-entered trees, 9.3 % of surveyed trees.
- 921 of 9 065 trees planted since 2022 have a crown of 8 m or more.
- 565 records where genus and Latin name disagree, e.g. "Juglas regia" next to genus "Juglans".
- 38 pairs of trees closer than 50 cm, 2 at the identical point.
- Street trees 87.8 % surveyed, park trees 15.7 %; 2 428 street trees planted since 2001 not marked as surveyed.

What is measured is the public WFS of the city, not the city's internal system.
