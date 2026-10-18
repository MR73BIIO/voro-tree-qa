# BERLIN M0 — Baumbestand Berlin (prediction, before the M0 script)

Source: WFS `https://gdi.berlin.de/services/wfs/baumbestand` (EPSG:25833, dl-zero-de/2.0),
layers `baumbestand:anlagenbaeume` and `baumbestand:strassenbaeume`.
R0: `berlin/r0/R0_SUMMARY.json` (commit `ea1ba84`): 527,780 + 434,765 = 962,545 objects;
sample 2 × 2,000 in 10 windows, `sample_sha256 = b7196dae…8078de1`.

## What R0 showed and why M0 measures the whole set

- The R0 sample is a **cluster sample**: each window of 200 objects mostly comes from a few
  care objects (`kennzeich`), e.g. one window = 200 trees of one object. Shares from R0
  are not estimates of the whole set. M0 harvests **all** objects of both layers.
- In each layer exactly one window of ten (10 %) holds records where nearly every field
  is empty. Their real number is unknown.
- `standalter` looks derived: the most frequent `pflanzjahr` and `standalter` values pair up
  with equal counts and sum to 2026 (e.g. 2001 × 93 ↔ 25 × 93; 1987 × 90 ↔ 39 × 90).
  In Anlagenbäume `standalter` is filled 3.05 % more often than `pflanzjahr`, and
  `standalter = 0` occurs exactly 61 times (3.05 %): age 0 may stand where the year is empty.

## Definitions (fixed before the script)

- **empty value**: `None`, empty or whitespace-only string, `-`, `--`.
  For species fields (`art_dtsch`, `art_bot`, `gattung`, `gattung_deutsch`) also `Unbekannt`.
- **shell**: a record with `pitid`, `art_bot` and `bezirk` all empty.
- **tree**: a record that is not a shell. B04–B14 count trees only, unless stated.
- **number**: `pflanzjahr`, `standalter`, `kronedurch`, `stammumfg`, `baumhoehe` parsed as
  numbers (decimal comma allowed); a non-numeric value counts as empty.
- **same point**: X and Y rounded to 0.01 m are equal.
- **street-name match** (Straßenbäume): `namenr` and `strname` compared after: lower case,
  text in brackets removed, `str.` → `straße`, whitespace collapsed.
- Harvest: WFS 2.0 paging, `sortBy=gisid`, frozen copy in `berlin/data/m0/` (outside git),
  `harvest_sha256` over all pages in order.

## Predictions

| # | Question | Prediction (threshold) |
|---|---|---|
| B01 | Is the harvest complete? | harvested = `numberMatched` in both layers, 0 duplicate `gisid` within a layer |
| B02 | How many shells? | shells ≥ 5 % of all 962,545 records |
| B03 | Are shells one block, not scattered? | ≥ 90 % of shells of a layer lie in one contiguous run of the `gisid` order |
| B04 | Is `standalter` derived from `pflanzjahr`? | where `pflanzjahr` is a number: `pflanzjahr + standalter = 2026` in ≥ 99 % |
| B05 | What does `standalter` say without a planting year? | where `pflanzjahr` is empty: `standalter = 0` in ≥ 95 % |
| B06 | German genus missing next to a botanical one? | `gattung` filled and `gattung_deutsch` empty ≥ 2 % of trees |
| B07 | Is one botanical name always one German name? | ≥ 3 `art_bot` values occur with ≥ 2 different `art_dtsch` |
| B08 | Crown diameter recorded as 0? | `kronedurch = 0` ≥ 5 % of trees in each layer |
| B09 | Implausible values exist but are rare? | `baumhoehe` > 50, `stammumfg` > 1,000, or `pflanzjahr` < 1700 or > 2026: ≥ 1 tree and ≤ 0.1 % of trees |
| B10 | Two trees on the same point? | trees on a shared point ≥ 0.5 % of trees |
| B11 | Same tree in both layers? | ≥ 1 `pitid` present in both layers |
| B12 | District names clean? | exactly 12 distinct non-empty `bezirk` values over both layers |
| B13 | Street name of the care object = street of the tree? | street-name mismatch ≥ 1 % of Straßenbäume trees with both fields filled |
| B14 | Missing or zero geometry? | 0 records without a point or with X = 0 or Y = 0 |

## Consequences (written before the result)

- **B01 REFUTED** → the harvest is not trusted; stop, nothing else from M0 is used until
  a diagnosis (paging, sorting, server limits).
- **B02 CONFIRMED** → shells are reported separately and every other share is given per
  tree, not per record. **B02 REFUTED** → shells are a footnote with their count.
- **B03 CONFIRMED** → shells are described as one block (an export or loading artefact),
  with its size. **REFUTED** → described as scattered records, no cause claimed.
- **B04 + B05 CONFIRMED** → `standalter` is described as a derived field; "age 0" without a
  planting year is a fact for the DE plane: the field looks like data but carries none.
  Either REFUTED → `standalter` is measured as its own field in D0 before any use.
- **B06, B07** → descriptive facts about species naming; a REFUTED is noted, not diagnosed.
- **B08 CONFIRMED** → "0 m crown" reported next to the count; no claim that 0 means
  "not measured" without a D0 check. **REFUTED** → descriptive.
- **B09 CONFIRMED** → the few implausible values are listed as examples (no tree IDs in
  public). **REFUTED** with 0 cases → reported as "no implausible values found by these
  rules"; REFUTED above 0.1 % → D0 before use.
- **B10, B11** → reported with counts; no claim of duplicate trees without a D0 look at
  examples.
- **B12, B14** → data hygiene checks; a REFUTED here goes to D0 first.
- **B13** → descriptive; examples kept outside git.
- **Overall:** B01 CONFIRMED and ≥ 10 / 14 CONFIRMED → DE LinkedIn post (Berlin as the
  third city after Zürich and Wien, only facts not used in earlier DE posts) + Puls.
  Otherwise → D0 before any use.
- Earlier verdicts for Zürich and Wien are not changed by M0 Berlin.
