# voro-tree-qa

[![DOI](https://zenodo.org/badge/1412075011.svg)](https://doi.org/10.5281/zenodo.23267379)

Quality checks for public tree registers (Baumkataster), tested against what the data owner says about its own data.

First data: the tree register of the City of Zurich (Open Data Zurich, CC0), 81 142 trees.
The city describes its own limits: crown diameters partly estimated (8 m where no value exists),
two accuracy classes of tree positions, green spaces not yet complete. This project measures them.

## Method

Every step has the same order:

1. prediction, committed before the code and before the data
2. script with its definitions in the header, committed before the first run
3. run, result, outcome with a verdict per point (CONFIRMED / REFUTED / NO DATA)

Every step with its seal: https://mr73biio.github.io/puls.html

## Status

- **R0** reconnaissance (no verdict): the download links of the dataset page return an HTML page;
  the city WFS 1.1.0 delivers the full point layer (81 142 trees). docs/R0_NOTE.md
- **M0** first measurement, 13 points written before the run: **11 CONFIRMED, 2 REFUTED**. docs/M0_OUTCOME.md
  - crown exactly 8 m: 16.2 % of screen-entered trees, 9.3 % of surveyed trees
  - 921 of 9 065 trees planted since 2022 have a crown of 8 m or more
  - 565 records where genus and Latin name disagree (e.g. "Juglas regia" next to "Juglans")
  - 38 pairs of trees closer than 50 cm, 2 at the identical point
  - street trees 87.8 % surveyed, park trees 15.7 %; 2 428 street trees planted since 2001 not marked as surveyed
  - REFUTED: species field vs Latin name agree in 89.75 % only (predicted ≥ 95 %); cause not yet known

What is measured is the public WFS of the city, not its internal system.

## Next

M0b (why 10 % of species disagree) → B1 golden batch → B2 checks → B3 injected errors → B4 QA report (DE / EN / PL).

## Run it

```
python r0/recon_r0.py     # downloads the public data to data/ (not in git), prints SHA-256
python m0/measure_m0.py   # needs geopandas; stops if the input SHA-256 differs
```

## Cite

All versions: https://doi.org/10.5281/zenodo.23267379 · v0.1: https://doi.org/10.5281/zenodo.23267380

## Data

Source: https://data.stadt-zuerich.ch/dataset/geo_baumkataster (licence CC0).
Downloaded files stay outside git; their SHA-256 is in the results.

Marcin Ruszczak · ORCID 0009-0004-0170-4277 · PL · DE · RU · EN
