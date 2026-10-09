| # | Measured | Value | Prediction | Verdict |
|---|---|---|---|---|
| P1 | baumgattunglat = first word of baumnamelat | 80577/81142 (99.3 %), mismatches 565 | >= 98.0 % and >= 1 mismatch | CONFIRMED |
| P2 | baumartlat = second word of baumnamelat (baumartlat filled) | 71351/79502 (89.75 %) | >= 95.0 % | REFUTED |
| P3 | pflanzjahr >= 2022: share with crown >= 8 m | 921/9065 (10.16 %) | >= 5.0 % | CONFIRMED |
| P4a | Strassenbaum: share Measured | 20435/23264 (87.84 %) | >= 70.0 % | CONFIRMED |
| P4b | Parkbaum: share Measured | 9083/57878 (15.69 %) | <= 30.0 % | CONFIRMED |
| P5 | Strassenbaum, pflanzjahr >= 2001: share Measured | 12076/14504 (83.26 %) | >= 85.0 % | REFUTED |
| P6 | kategorie Strassenbaum <=> status Strassenbaum / Strassenbaum (A) | 0 mismatches | 0 | CONFIRMED |
| P7 | baumtyp -> one text; 3 and 4 share one text; empty -> 'nicht zugeordnet' | one text True, 3=4 True, empty ok True | all true | CONFIRMED |
| P8 | close pairs < 0.50 m (LV95) | 38 pairs (2 at the same point) | 1 ... 811 | CONFIRMED |
| P9 | pflanzjahr < 1850 | 48 trees, years [(1665, 1), (1780, 1), (1796, 1), (1800, 3), (1805, 3), (1806, 8), (1815, 1), (1820, 1), (1822, 1), (1826, 2)] | 1 ... 100 | CONFIRMED |
| P10a | baumnummer = poi_id | 81142/81142 | 81142/81142 | CONFIRMED |
| P10b | share of baumnummer starting 'nn-' | 1568/81142 (1.93 %) | >= 1.0 % | CONFIRMED |
| P11 | crown exactly 8 m: Bildschirmeingabe vs Measured | 16.22 % vs 9.34 % | Bildschirmeingabe higher | CONFIRMED |

Life verdict (worst point): REFUTED (11/13 CONFIRMED)
