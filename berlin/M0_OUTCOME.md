# BERLIN M0 — outcome (Baumbestand Berlin)

Prediction: `berlin/M0_PREDICTION.md`, commit `9a86559`, Puls #44,
sha256 `5fbdbeeda17641e8ab652c008e8d2065d9791e3676baf1b614f41633fa13a710`.
Script: `berlin/m0_measure.py` (`2bfd8e2`). Results: `berlin/m0/RESULTS.json`.
Data: full WFS harvest, frozen in `berlin/data/m0/` (outside git),
`harvest_sha256 = 844546b787250e62e2470e9596d2184abbd0a81275586a2c9da72731ec7ad25c`.

**Score: 9 / 14 — verdict REFUTED. Overall rule (B01 CONFIRMED and ≥ 10 / 14) not met →
D0 before any use, as written before the result.**

Records 962,545 = 527,780 Anlagenbäume + 434,765 Straßenbäume; trees 956,347, shells 6,198.

## Points

| # | Question | Rule | Measured | Verdict |
|---|---|---|---|---|
| B01 | harvest complete, no duplicate `gisid` | = numberMatched, 0 dup | 527,780 / 434,765 harvested = matched = R0; 0 dup | CONFIRMED |
| B02 | shells share of all records | ≥ 5 % | **0.644 %** (6,198: 4,609 Anlagen, 1,589 Straßen) | REFUTED |
| B03 | shells in one contiguous `gisid` run | ≥ 90 % per layer | Anlagen 100 % (4,609 / 4,609), Straßen 99.75 % (1,585 / 1,589) | CONFIRMED |
| B04 | `pflanzjahr + standalter = 2026` | ≥ 99 % | 99.947 % (768,105 of 768,513); 408 exceptions | CONFIRMED |
| B05 | `standalter = 0` where `pflanzjahr` is empty | ≥ 95 % | **10.85 %** (20,377 of 187,834) | REFUTED |
| B06 | `gattung` filled, `gattung_deutsch` empty | ≥ 2 % of trees | 2.59 % (24,769) | CONFIRMED |
| B07 | `art_bot` with ≥ 2 different `art_dtsch` | ≥ 3 | **0** of 913 botanical names | REFUTED |
| B08 | `kronedurch = 0` | ≥ 5 % per layer | Anlagen 12.38 % (64,782), Straßen 8.91 % (38,590) | CONFIRMED |
| B09 | implausible height / girth / year | ≥ 1 and ≤ 0.1 % | 149 trees (0.016 %) | CONFIRMED |
| B10 | trees on a shared point | ≥ 0.5 % | 0.031 % (298 trees on 148 points) | REFUTED |
| B11 | `pitid` in both layers | ≥ 1 | 0 | REFUTED |
| B12 | distinct non-empty `bezirk` | = 12 | 12 | CONFIRMED |
| B13 | street-name mismatch (Straßenbäume) | ≥ 1 % | 15.79 % (67,149 of 425,337) | CONFIRMED |
| B14 | missing or zero geometry | = 0 | 0 | CONFIRMED |

## Consequences applied (as written before the result)

- **B01 CONFIRMED** → the harvest is trusted; counts equal R0 and the server.
- **B02 REFUTED** → shells are a footnote with their count: 6,198 records (0.64 %).
  The 10 % seen in R0 was one sample window that fell into the shell block.
- **B03 CONFIRMED** → shells are one block in the `gisid` order (4,609 + 1,585 of 1,589),
  described as one block; no cause claimed.
- **B04 CONFIRMED, B05 REFUTED** → per the rule "either REFUTED", `standalter` goes to D0
  as its own field before any use. B04 alone holds: where a planting year exists,
  `standalter` is 2026 minus that year in 99.95 %.
- **B06** → descriptive: 24,769 trees (2.59 %) have a botanical genus and no German genus.
- **B07 REFUTED** → noted, not diagnosed: every botanical name maps to one German name.
- **B08 CONFIRMED** → "0 m crown" reported with counts; no claim that 0 means "not measured"
  without a D0 check.
- **B09 CONFIRMED** → 149 implausible values; examples outside git, no IDs in public.
- **B10, B11 REFUTED** → reported with counts (298 trees on 148 shared points; no `pitid`
  in both layers); no claim of duplicate trees.
- **B12, B14 CONFIRMED** → district names and geometry pass these checks.
- **B13 CONFIRMED** → descriptive only; examples outside git. Before use, D0 checks how much
  of the 15.79 % is naming form rather than a different street.
- **Overall 9 / 14** → D0 before any use; no DE post from M0 alone.

## Open for D0 (from the consequences)

1. `standalter` where `pflanzjahr` is empty: what does it hold in the 89 % that are not 0?
2. The 408 exceptions to B04.
3. B13: share of mismatches that are naming form (abbreviation, district suffix, added
   description) vs a different street.
4. B08: is `kronedurch = 0` linked to other empty or zero measures of the same tree?
