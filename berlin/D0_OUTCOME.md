# BERLIN D0 — outcome

Prediction: `berlin/D0_PREDICTION.md`, commit `0cbc310`,
sha256 `ce940481c4fd14cf0d296e9c22f8ca2ac867f9e5235372ea3ee7849b0f8dba8b`.
Script: `berlin/d0_diagnose.py` (`072a0aa`). Results: `berlin/d0/DIAGNOSIS.json`.
Data: frozen M0 harvest, `harvest_sha256 = 844546b7…d7ad25c` (checked by the script).

**Score: 3 / 8 — verdict REFUTED. Overall rule (≥ 5 / 8) not met → D1, as written before
the result. No DE post from M0 + D0.**

## Points

| # | Question | Rule | Measured | Verdict |
|---|---|---|---|---|
| D01 | `standalter` empty where no year and not 0 | ≥ 90 % | 99.98 % (167,429 of 167,457) | CONFIRMED |
| D02 | "no year, age 0" in Anlagenbäume | ≥ 95 % | 99.71 % (20,318 of 20,377) | CONFIRMED |
| D03 | B04 exceptions sum to 2021–2025 | ≥ 90 % | 97.38 % (372 of 382); 2025: 326 | CONFIRMED |
| D04 | B13 mismatches resolved by compact form | ≥ 70 % | **3.42 %** (2,298 of 67,149) | REFUTED |
| D05 | mismatches left after compact form | ≤ 3 % | **15.25 %** (64,851 of 425,337) | REFUTED |
| D06 | crown 0 with height 0 or empty | ≥ 50 % | 26.72 % (27,624 of 103,372) | REFUTED |
| D07 | crown 0: young ≥ 3 × older | ratio ≥ 3 | **0.62** (young 5.78 %, older 9.28 %) | REFUTED |
| D08 | shared points with one identical species | ≥ 80 % | 45.27 % (67 of 148) | REFUTED |

## Consequences applied (as written before the result)

- **D01 + D02 CONFIRMED** → fact for the DE plane: where no planting year is known,
  `standalter` is empty, except 20,377 trees (99.7 % in green spaces) where it says "0".
  The field reads like a measured age but carries none there.
- **D03 CONFIRMED** → the B04 exceptions are an age frozen at an older update:
  372 of 382 sum to 2021–2025, 326 of them to 2025.
- **D04 REFUTED** → B13 goes to D1 with examples; no public claim. The examples (outside
  git) show the care-object name `namenr` = street + section or local suffix
  (`Teil B`, `Fr`, `Köp`, `OT Wedding`, `/Mittelstreifen`), and a few different streets
  (`MARIENDORFER DAMM` / `Hundsteinweg`). Not measured yet.
- **D06 + D07 REFUTED** → crown 0 stays a count with no cause. Young trees have crown 0
  *less* often than older ones (5.78 % vs 9.28 %).
- **D08 REFUTED** → shared points are described as different trees recorded on one point
  (55 % carry different species); no claim of double entries.
- **Overall 3 / 8** → D1.

## Released for later use (after D1, DE plane, only new facts)

| Fact | Value |
|---|---|
| empty records, one block | 6,198 (0.64 %) — R0 window showed 10 % |
| `standalter` = 2026 − `pflanzjahr` | 99.95 % where a year exists |
| age frozen at an older update | 372 trees (326 at 2025) |
| no year → `standalter` empty | 99.98 % |
| no year → `standalter` "0" | 20,377 trees, 99.7 % in green spaces |
| crown 0 m | 64,782 Anlagen (12.4 %), 38,590 Straßen (8.9 %); young trees less often |

## Open for D1

1. B13: how much of the 15.25 % is `namenr` starting with `strname` (section / local
   suffix) vs a different street.
2. Crown 0: is it concentrated in a few districts or care objects?
3. Shared points: are the 148 points concentrated in a few care objects?
