# BERLIN D0 — why M0 missed, and what four M0 facts mean (prediction, before the D0 script)

Trigger: `berlin/M0_OUTCOME.md` — 9 / 14, REFUTED → D0 before any use.
Data: the same frozen M0 harvest `berlin/data/m0/`
(`harvest_sha256 = 844546b7…d7ad25c`, checked by the script). No new download.
M0 verdicts are not changed by D0.

## What the M0 examples showed (outside git, read before writing this file)

- The 20 listed B04 exceptions sum to years before 2026 (e.g. 1995 + 29 = 2024,
  1952 + 69 = 2021): `standalter` may be frozen at an older update.
- The 40 listed B13 mismatches are spelling forms of the same street:
  `Haeseler Straße` / `Haeselerstraße`, `Karolinger Platz` / `Karolingerplatz`,
  `Gothaallee` / `Gotha-Allee`, `Roland-Krüger Straße` / `Roland-Krüger-Straße`.

## Definitions (M0 definitions apply; added here)

- **young tree**: `pflanzjahr` is a number from 2020 to 2026.
- **compact form** of a street name: the M0 street-name normalisation, then all spaces,
  hyphens and dots removed.
- **no year**: `pflanzjahr` empty or not a number (as in M0 B05).

## Predictions

| # | Question | Prediction (threshold) |
|---|---|---|
| D01 | What does `standalter` hold where there is no year and it is not 0? | `standalter` empty in ≥ 90 % of these trees |
| D02 | Where is "no year, age 0"? | ≥ 95 % of these trees are Anlagenbäume |
| D03 | Are the B04 exceptions an older reference year? | for ≥ 90 % of exceptions with `pflanzjahr` ≥ 1700: `pflanzjahr + standalter` between 2021 and 2025 |
| D04 | Is the B13 mismatch mostly spelling form? | ≥ 70 % of the 67,149 mismatches disappear in compact form |
| D05 | How many real street differences remain? | mismatches left after compact form ≤ 3 % of the 425,337 trees compared |
| D06 | Is crown 0 part of an empty measurement? | among trees with `kronedurch = 0`: `baumhoehe` 0 or empty in ≥ 50 % |
| D07 | Is crown 0 a young-tree effect? | share of `kronedurch = 0` among young trees ≥ 3 × the share among trees with a year before 2020 |
| D08 | Are trees on a shared point the same tree twice? | ≥ 80 % of the 148 shared points have one identical non-empty `art_bot` for all trees on them |

## Consequences (written before the result)

- **D01 + D02 CONFIRMED** → fact for the DE plane: where no planting year is known,
  `standalter` is empty, except a block of trees in green spaces where it says "0".
  The field reads like a measured age but carries none there.
  Either REFUTED → `standalter` without a year is described only with counts.
- **D03 CONFIRMED** → the B04 exceptions are described as an age frozen at an older update
  (with the count). **REFUTED** → described as 408 inconsistent pairs, no cause claimed.
- **D04 + D05 CONFIRMED** → B13 is a spelling-form effect. This is the same error type as
  the PL plane ("Krzyżacy": one film, two titles), so it is **not** used as a DE headline;
  it stays in the report. **D04 REFUTED** → B13 goes to D1 with examples; no public claim.
- **D06 / D07** → whichever is CONFIRMED is the stated explanation for crown 0 (empty
  measurement and/or young trees); both REFUTED → crown 0 stays a count with no cause.
- **D08 CONFIRMED** → shared points described as probable double entries, count only.
  **REFUTED** → described as different trees recorded on one point.
- **Overall:** ≥ 5 / 8 CONFIRMED → DE LinkedIn post from M0 + D0 facts
  (only facts not used in the Zürich and Wien posts) + Puls. Otherwise → D1.
