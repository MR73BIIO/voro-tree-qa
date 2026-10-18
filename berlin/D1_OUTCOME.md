# BERLIN D1 — outcome

Prediction: `berlin/D1_PREDICTION.md`,
sha256 `f00cc349e2461a9d78122f434cc59918a1422d40517ea2d8dd0488716cce0187`.
Script: `berlin/d1_diagnose.py`. Results: `berlin/d1/DIAGNOSIS.json`.
Data: frozen M0 harvest, `harvest_sha256 = 844546b7…d7ad25c` (checked by the script).

**Score: 6 / 7 — verdict REFUTED (E07 only). Post gate (≥ 4 / 7) met → DE post from the
facts released in `D0_OUTCOME.md` plus the CONFIRMED D1 facts, as written before the result.**

## Points

| # | Question | Rule | Measured | Verdict |
|---|---|---|---|---|
| E01 | prefix cases among remaining mismatches | ≥ 70 % | 91.06 % (59,054 of 64,851) | CONFIRMED |
| E02 | other street, % of compared trees | ≤ 3 % | 1.36 % (5,797 of 425,337) | CONFIRMED |
| E03 | mismatch trees in fully mismatching care objects | ≥ 90 % | 99.77 % (66,997 of 67,149); 1,283 of 1,285 objects | CONFIRMED |
| E04 | crown-0 trees inside crown-0 objects | ≥ 50 % | 54.04 % (55,863 of 103,372) in 823 of 12,721 objects | CONFIRMED |
| E05 | crown-0 share, highest vs lowest district | ≥ 5 × | **262 ×**: Tempelhof-Schöneberg 60.36 %, Treptow-Köpenick 0.23 % | CONFIRMED |
| E06 | 5 objects with most shared points | ≥ 50 % of 148 | 77.70 % (115 of 148), 31 objects in total | CONFIRMED |
| E07 | shared points with trees from both layers | ≥ 50 % | 0 % (0 of 148) | REFUTED |

## Consequences applied (as written before the result)

- **E01 + E02 CONFIRMED** → B13 is explained: the care-object name is the street plus a
  section label (91 % of the remaining cases); other streets are 1.36 % of the trees
  compared. Fact for the DE plane.
- **E03 CONFIRMED** → the mismatch is a naming rule of care objects (1,283 of 1,285
  objects mismatch for every tree), not tree errors.
- **E04 + E05 CONFIRMED** → crown 0 is stated as a whole-object and district matter:
  823 care objects hold 54 % of all crown-0 trees; the share ranges from 0.23 % to 60.36 %
  between districts (262 ×). No claim about why a district records 0.
- **E06 CONFIRMED** → shared points are concentrated: 5 care objects hold 115 of 148.
- **E07 REFUTED** → all shared points lie inside one layer and one care object; no
  street tree and park tree on one spot. Described with counts only.

## Crown 0 by district (trees, `kronedurch = 0`)

| District | Share | Trees |
|---|---|---|
| Tempelhof-Schöneberg | 60.36 % | 37,625 of 62,334 |
| Neukölln | 29.53 % | 17,094 of 57,881 |
| Reinickendorf | 18.88 % | 17,153 of 90,869 |
| Spandau | 17.31 % | 12,944 of 74,759 |
| Steglitz-Zehlendorf | 10.67 % | 12,315 of 115,424 |
| Mitte | 5.53 % | 3,741 of 67,706 |
| Friedrichshain-Kreuzberg | 1.04 % | 434 of 41,768 |
| Charlottenburg-Wilmersdorf | 0.71 % | 628 of 88,758 |
| Pankow | 0.57 % | 566 of 99,561 |
| Lichtenberg | 0.48 % | 396 of 81,916 |
| Marzahn-Hellersdorf | 0.31 % | 296 of 96,978 |
| Treptow-Köpenick | 0.23 % | 180 of 78,295 |

## Path closed

R0 → M0 9 / 14 → D0 3 / 8 → D1 6 / 7. Berlin is the third city of the DACH plane after
Zürich and Wien.
