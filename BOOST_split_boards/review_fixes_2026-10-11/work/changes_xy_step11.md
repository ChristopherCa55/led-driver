
## Step 11 (2026-10-14): the card sheet's pull-ups placed as on the main page

**Status:** in the copy. The user re-arranged R106 / R107 on the main page (their own save, 2026-10-14) and asked
for the same on the card sheet. The card sheet's U26E block sits at (+125.73, +113.03) from the main page's, so every
item below is the main page's, shifted by that. Connections unchanged (ERC 0, sync 0, card parity 0).

| item | card sheet before | card sheet now |
|---|---|---|
| R106 | (140.97, 353.06) | (151.13, 349.25) (main page (25.4, 236.22)) |
| R107 | (149.86, 353.06) | (140.97, 347.98) (main page (15.24, 234.95)) |

Removed from the card sheet:

- text I2C pull-ups\n(U26 has none) 140.97 370.84
- wire ((165.1, 367.03), (172.72, 367.03))
- wire ((170.18, 364.49), (172.72, 364.49))
- wire ((142.24, 351.79), (142.24, 354.33))
- wire ((142.24, 360.68), (142.24, 363.22))
- wire ((151.13, 351.79), (151.13, 354.33))
- wire ((151.13, 360.68), (151.13, 363.22))
- global_label SCL 170.18 364.49 180.0
- global_label SDA 165.1 367.03 180.0
- global_label 5V 142.24 351.79 90.0
- global_label SCL 142.24 363.22 270.0
- global_label 5V 151.13 351.79 90.0
- global_label SDA 151.13 363.22 270.0

Added to the card sheet:

- text I2C pull-ups\n(U26 has none) 139.446 339.852
- wire ((152.4, 347.98), (152.4, 350.52))
- wire ((152.4, 364.49), (172.72, 364.49))
- wire ((142.24, 367.03), (172.72, 367.03))
- wire ((142.24, 346.71), (142.24, 349.25))
- wire ((142.24, 355.6), (142.24, 367.03))
- wire ((152.4, 356.87), (152.4, 364.49))
- global_label 5V 142.24 346.71 90.0
- global_label SCL 158.75 364.49 90.0
- global_label 5V 152.4 347.98 90.0
- global_label SDA 146.05 367.03 90.0
