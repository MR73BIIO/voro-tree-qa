# voro-tree-qa

Quality checks for public tree registers (Baumkataster), tested against errors I put in on purpose.

First data: the tree register of the City of Zurich (Open Data Zurich, CC0).
The city describes its own data limits: crown diameters partly estimated (8 m where no value exists),
two accuracy classes of tree positions, green spaces not yet complete. This project measures them.

## Method

Every step has the same order:

1. prediction, committed before the code and before the data
2. script with its definitions in the header, committed before the first run
3. run, result, outcome with a verdict per point (CONFIRMED / REFUTED / NO DATA)

Every step with its seal: https://mr73biio.github.io/puls.html

## Status

- R0: reconnaissance of the published files (no prediction, no verdict)

## Data

Source: https://data.stadt-zuerich.ch/dataset/geo_baumkataster (licence CC0).
Downloaded files stay outside git; their SHA-256 is in the results.

Marcin Ruszczak · ORCID 0009-0004-0170-4277 · PL · DE · RU · EN
