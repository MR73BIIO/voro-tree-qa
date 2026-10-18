# BERLIN D1 — street names, crown 0 and shared points (prediction, before the D1 script)

Trigger: `berlin/D0_OUTCOME.md` — 3 / 8, REFUTED → D1, with three open questions.
Data: the same frozen M0 harvest `berlin/data/m0/`
(`harvest_sha256 = 844546b7…d7ad25c`, checked by the script). No new download.
M0 and D0 verdicts are not changed by D1.

## What the D0 examples showed (outside git, read before writing this file)

- The 40 most frequent remaining street pairs are mostly `namenr` = street + section or
  local suffix (`Märkische Allee Teil B`, `Fürstenwalder Damm  Fr`, `Seestraße  OT Wedding`,
  `Hohenzollerndamm/Mittelstreifen`); a few are other streets (`MARIENDORFER DAMM` /
  `Hundsteinweg`) or a typo (`Radelandstaße`).
- Shared points: many pairs carry two different species and sit close together
  (X ≈ 378,2xx–378,4xx).

## Definitions (M0 and D0 definitions apply; added here)

- **care object**: layer + `kennzeich` of a tree.
- **remaining mismatch**: a Straßenbäume tree whose street names differ in M0 form and in
  D0 compact form (64,851 trees in D0).
- **prefix case**: a remaining mismatch where the compact `namenr` starts with the compact
  `strname`.
- **other street**: a remaining mismatch that is not a prefix case.
- **crown-0 object**: a care object where ≥ 90 % of trees have `kronedurch = 0`.
- **shared point**: as in M0 B10 (148 points); its object is the care object of the first
  tree on it in harvest order.

## Predictions

| # | Question | Prediction (threshold) |
|---|---|---|
| E01 | Is the remaining mismatch mostly street + suffix? | prefix cases ≥ 70 % of remaining mismatches |
| E02 | How many trees name another street? | other street ≤ 3 % of the 425,337 trees compared |
| E03 | Is the name mismatch a property of the care object, not of single trees? | ≥ 90 % of M0 mismatch trees lie in care objects where every compared tree mismatches |
| E04 | Is crown 0 a whole-object matter? | ≥ 50 % of crown-0 trees lie in crown-0 objects |
| E05 | Does crown 0 differ strongly between districts? | highest district share of crown 0 ≥ 5 × the lowest |
| E06 | Are shared points concentrated? | the 5 objects with most shared points hold ≥ 50 % of the 148 |
| E07 | Is a shared point a street tree and a park tree on one spot? | ≥ 50 % of shared points carry trees from both layers |

## Consequences (written before the result)

- **E01 + E02 CONFIRMED** → B13 is explained: the care-object name is the street plus a
  section label; real other streets are a small, counted rest. Fact for the DE plane.
  **E01 REFUTED** → B13 stays a count with examples, no explanation claimed.
- **E03 CONFIRMED** → the mismatch is described as a naming rule of care objects, not as
  tree errors. **REFUTED** → described as mixed (object and tree level).
- **E04 / E05** → whichever is CONFIRMED is stated (whole objects without crown values,
  and/or district differences, with the measured ratio). Both REFUTED → crown 0 stays a
  count, scattered.
- **E06 / E07** → stated with counts if CONFIRMED; REFUTED → shared points stay a count
  (298 trees on 148 points) with no pattern claimed.
- **Gate for the DE post (Berlin, third city):** D1 closed with ≥ 4 / 7 CONFIRMED → post
  from the facts released in `D0_OUTCOME.md` plus D1 facts that are CONFIRMED; only facts
  not used in the Zürich and Wien posts. Otherwise → D2 before any post.
