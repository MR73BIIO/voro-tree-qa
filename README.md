# voro-tree-qa

[![DOI](https://zenodo.org/badge/1412075011.svg)](https://doi.org/10.5281/zenodo.23267379)

Quality checks for public tree registers (Baumkataster), tested against what the data owner says about its own data.

Three cities of the DACH region, one method:

| City | Register | Records | Path |
|---|---|---|---|
| Zürich | Baumkataster, Open Data Zurich (CC0) | 81 142 | R0 → M0 11 / 13 |
| Wien | Baumkataster, Stadt Wien (`ogdwien:BAUMKATOGD`) | 233 082 | R0 → M0 8 / 12 → D1 2 / 4 |
| Berlin | Baumbestand, Senatsverwaltung Berlin (WFS, dl-zero-de/2.0) | 962 545 | R0 → M0 9 / 14 → D0 3 / 8 → D1 6 / 7 |

## Method

Every step has the same order:

1. prediction, committed before the code and before the data
2. script with its definitions in the header, committed before the first run
3. run, result, outcome with a verdict per point (CONFIRMED / REFUTED / NO DATA)

A REFUTED point is closed by the consequence written before the result: a diagnosis step
(D0, D1) follows, and nothing from a refuted step is used before it.

Every step with its seal: https://mr73biio.github.io/puls.html

## Zürich

The city describes its own limits: crown diameters partly estimated (8 m where no value exists),
two accuracy classes of tree positions, green spaces not yet complete. This project measures them.

- **R0** reconnaissance (no verdict): the download links of the dataset page return an HTML page;
  the city WFS 1.1.0 delivers the full point layer (81 142 trees). docs/R0_NOTE.md
- **M0** first measurement, 13 points written before the run: **11 CONFIRMED, 2 REFUTED**. docs/M0_OUTCOME.md
  - crown exactly 8 m: 16.2 % of screen-entered trees, 9.3 % of surveyed trees
  - 921 of 9 065 trees planted since 2022 have a crown of 8 m or more
  - 565 records where genus and Latin name disagree (e.g. "Juglas regia" next to "Juglans")
  - 38 pairs of trees closer than 50 cm, 2 at the identical point
  - street trees 87.8 % surveyed, park trees 15.7 %; 2 428 street trees planted since 2001 not marked as surveyed
  - REFUTED: species field vs Latin name agree in 89.75 % only (predicted ≥ 95 %); cause not yet known

Next for Zürich: M0b (why 10 % of species disagree) → B1 golden batch → B2 checks → B3 injected errors → B4 QA report (DE / EN / PL).

## Wien

Folder `wien/`. Predictions: `wien/PREDICTIONS.md`, `wien/D1_PREDICTIONS.md`.

- **M0** 12 points: **8 CONFIRMED, 4 REFUTED**
  - 36.2 % of planting years before 2006 end in 0 or 5 (20 % if evenly spread)
  - crown code and crown text are not one-to-one
- **D1** 4 explanations: **2 CONFIRMED, 2 REFUTED**
  - without planting year: street trees 3.6 %, park trees 24.0 %
  - 3 534 records "Jungbaum wird gepflanzt", 98.9 % of them without year and trunk girth

## Berlin

Folder `berlin/`. Two layers: Straßenbäume (434 765) and Anlagenbäume (527 780), full harvest
of the city WFS, frozen copy outside git (`harvest_sha256 844546b7…d7ad25c`).

- **R0** reconnaissance, sample spread over 10 windows per layer. The sample is a cluster sample
  (one window = one care object); M0 therefore measures the whole set. `berlin/r0/R0_SUMMARY.json`
- **M0** 14 points: **9 CONFIRMED, 5 REFUTED**. `berlin/M0_OUTCOME.md`
  - 6 198 empty records (0.64 %), all in one block of the `gisid` order; the R0 sample had shown 10 %
  - `standalter` = 2026 − `pflanzjahr` in 99.95 % where a planting year exists
  - crown 0 m: 64 782 Anlagenbäume (12.4 %), 38 590 Straßenbäume (8.9 %)
  - 12 district names without variants, no missing geometry, no `pitid` in both layers
- **D0** 8 explanations: **3 CONFIRMED, 5 REFUTED**. `berlin/D0_OUTCOME.md`
  - without planting year `standalter` is empty (99.98 %), except 20 377 trees with "0" (99.7 % Anlagenbäume)
  - 372 trees: age frozen at an older update (326 at 2025)
  - REFUTED: crown 0 is not a young-tree effect (young 5.78 %, older 9.28 %)
- **D1** 7 explanations: **6 CONFIRMED, 1 REFUTED**. `berlin/D1_OUTCOME.md`
  - crown 0 by district: 0.23 % (Treptow-Köpenick) to 60.36 % (Tempelhof-Schöneberg), 262 ×
  - 823 of 12 721 care objects hold 54 % of all crown-0 trees
  - care-object name = street + section label (91 % of remaining mismatches); another street: 1.36 % of trees

What is measured in every city is the public data service, not the internal system.

## Run it

```
# Zürich
python r0/recon_r0.py     # downloads the public data to data/ (not in git), prints SHA-256
python m0/measure_m0.py   # needs geopandas; stops if the input SHA-256 differs

# Wien: wien/r0_recon.py → wien/m0_measure.py → wien/d1_measure.py (usage in each script header)

# Berlin (standard library only)
python3 berlin/r0_recon.py discover
python3 berlin/r0_recon.py recon --sample 2000 --sortby gisid
python3 berlin/m0_measure.py all        # full harvest (~97 pages), --resume after a break
python3 berlin/d0_diagnose.py           # reads the frozen copy only
python3 berlin/d1_diagnose.py
```

Each measuring script checks the SHA-256 of its prediction file and of the frozen data before it counts.

## Cite

All versions: https://doi.org/10.5281/zenodo.23267379 · v0.2 (Zürich, Wien, Berlin): https://doi.org/10.5281/zenodo.23455971 · v0.1 (Zürich): https://doi.org/10.5281/zenodo.23267380

## Data

- Zürich: https://data.stadt-zuerich.ch/dataset/geo_baumkataster (licence CC0)
- Wien: Stadt Wien, data.wien.gv.at, Baumkataster (`ogdwien:BAUMKATOGD`)
- Berlin: https://gdi.berlin.de/services/wfs/baumbestand (Datenlizenz Deutschland – Zero – 2.0)

Downloaded files stay outside git; their SHA-256 is in the results.

Marcin Ruszczak · ORCID 0009-0004-0170-4277 · PL · DE · RU · EN
