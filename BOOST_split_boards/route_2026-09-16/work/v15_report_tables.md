| FET (channel) | driver OUT → series R | series R → gate | driver OUT → turn-off diode | diode → gate | driver VSS → source copper | paired path | beside the return | loop area (mm²) |
|---|---|---|---|---|---|---|---|---|
| M1 (boost switch) | 1.5 | 1.2 | – | – | GND plane | – | – | – |
| M7 (LX side, 5 Ω) | 13.6 | 5.1 | 18.5 | 1.4 | 21.3 | driver->R->gate | 73 % (yes) | 47.5 |
| M5 (LX side, 5 Ω) | 13.5 | 1.3 | 2.1 | 1.0 | 22.2 | driver->R->gate | 82 % (yes) | 24.5 |
| M6 (LX side, 5 Ω) | 28.9 | 3.4 | 16.0 | 1.5 | 14.8 | driver->R->gate | 34 % (no) | 47.7 |
| M2 (rail side, 220 Ω) | 25.9 | 4.5 | 30.5 | 1.5 | 19.5 | driver->diode->gate | 18 % (no) | 147.4 |
| M3 (rail side, 220 Ω) | 30.3 | 4.0 | 30.1 | 1.1 | 9.9 | driver->diode->gate | 0 % (no) | 186.5 |
| M4 (rail side, 220 Ω) | 32.9 | 1.1 | 4.9 | 26.6 | 16.2 | driver->diode->gate | 4 % (no) | 57.0 |
| M10 (sink) | 2.1 | 1.4 | – | – | GND plane | – | – | – |
| M9 (sink) | 12.5 | 1.1 | – | – | GND plane | – | – | – |
| M8 (sink) | 17.5 | 1.0 | – | – | GND plane | – | – | – |

| FET | Part → gate pin | Role | Routed (mm) | Pad centres (mm) | Vias |
|---|---|---|---|---|---|
| M1 | R104.1 | pull-down to GND | 1.3 | 3.0 | 0 |
| M1 | R15.2 | series R | 1.2 | 2.6 | 0 |
| M7 | D2.2 | turn-off diode | 1.4 | 2.9 | 0 |
| M7 | R60.2 | series R | **5.1** | 5.2 | 0 |
| M7 | R76.2 | pull-down to m2_source | 3.5 | 4.8 | 1 |
| M5 | D22.2 | turn-off diode | 1.0 | 2.4 | 0 |
| M5 | R59.1 | series R | 1.3 | 2.6 | 0 |
| M5 | R74.2 | pull-down to m4_source | 1.3 | 2.9 | 0 |
| M6 | D8.2 | turn-off diode | 1.5 | 3.1 | 0 |
| M6 | R49.1 | pull-down to m3_source | 1.1 | 2.2 | 0 |
| M6 | R70.2 | series R | 3.4 | 4.2 | 0 |
| M2 | D11.2 | turn-off diode | 1.5 | 3.2 | 0 |
| M2 | R13.1 | series R | 4.5 | 4.8 | 0 |
| M2 | R75.2 | pull-down to m2_source | **6.3** | 5.3 | 0 |
| M3 | D14.2 | turn-off diode | 1.1 | 2.4 | 0 |
| M3 | R23.2 | series R | 4.0 | 5.3 | 0 |
| M3 | R61.2 | pull-down to m3_source | **5.2** | 6.9 | 0 |
| M4 | D13.2 | turn-off diode | **26.6** | 9.7 | 2 |
| M4 | R47.1 | series R | 1.1 | 2.2 | 0 |
| M4 | R73.2 | pull-down to m4_source | 2.5 | 3.8 | 1 |
| M10 | R56.1 | series R | 1.4 | 2.9 | 0 |
| M9 | R50.1 | series R | 1.1 | 2.3 | 0 |
| M8 | R22.1 | series R | 1.0 | 2.4 | 0 |

| Link | Net | Pad centres (mm) | Routed (mm) | Vias |
|---|---|---|---|---|
| C31.1 → U19.16 VDDA 12V | 12V | 2.8 | 2.9 | 2 |
| C31.2 → U19.14 VSSA GND | GND | 2.5 | 0.9 | 0 |
| C51.1 → U15.11 VDDB | Net-(U15-VDDA) | 5.5 | 7.3 | 2 |
| C51.2 → U15.9 VSSB | m2_source | 6.4 | 36.0 | 4 |
| C51.1 → U15.16 VDDA | Net-(U15-VDDA) | 2.4 | 1.2 | 0 |
| C51.2 → U15.14 VSSA | m2_source | 2.1 | 0.7 | 0 |
| C18.1 → U15.11 VDDB | Net-(U15-VDDA) | 6.1 | 7.8 | 0 |
| C18.2 → U15.9 VSSB | m2_source | 6.7 | 5.4 | 2 |
| C50.1 → U10.11 VDDB | Net-(U10-VDDA) | 2.4 | 1.0 | 0 |
| C50.2 → U10.9 VSSB | m3_source | 3.0 | 1.9 | 2 |
| C16.1 → U10.11 VDDB | Net-(U10-VDDA) | 4.8 | 2.2 | 0 |
| C16.2 → U10.9 VSSB | m3_source | 4.6 | 2.6 | 2 |
| C61.1 → U8.11 VDDB | Net-(U8-VDDA) | 2.2 | 0.9 | 0 |
| C61.2 → U8.9 VSSB | m4_source | 2.2 | 1.0 | 0 |
| C60.1 → U8.11 VDDB | Net-(U8-VDDA) | 4.3 | 4.6 | 0 |
| C60.2 → U8.9 VSSB | m4_source | 3.6 | 2.2 | 0 |
| C48.1 → U19.3 VCCI | 5V | 3.8 | – | – |
| C48.1 → U19.8 VCCI (pin 8, shorted to 3 inside) | 5V | 3.8 | 3.8 | 0 |
| C48.2 → U19.4 GND | GND | 4.0 | – | – |
| C90.1 → U10.3 VCCI | 5V | 2.1 | 0.8 | 0 |
| C90.2 → U10.4 GND | GND | 2.1 | 0.9 | 0 |
| C89.2 → U8.3 VCCI | 5V | 2.3 | 0.8 | 0 |
| C89.1 → U8.4 GND | GND | 2.4 | 1.0 | 0 |
| C62.2 → U15.3 VCCI | 5V | 2.9 | 1.4 | 0 |
| C62.1 → U15.4 GND | GND | 4.8 | – | – |

| Pad | Net | Via | From pad centre (mm) | Track (mm) | Own via |
|---|---|---|---|---|---|
| C48.1 | 5V | (65.05, 34.05) | 4.4 | 3.8 | no, through U19.6, U19.8 |
| C48.2 | GND | (62.25, 35.55) | 0.4 | 0.0 | yes |
| C90.1 | 5V | (49.95, 42.55) | 0.5 | 0.0 | yes |
| C90.2 | GND | (51.45, 43.35) | 0.5 | 0.0 | yes |
| C89.2 | 5V | (83.05, 103.85) | 0.8 | 0.0 | yes |
| C89.1 | GND | (82.15, 106.85) | 2.3 | 1.5 | yes |
| C62.2 | 5V | (56.65, 56.75) | 0.5 | 0.0 | yes |
| C62.1 | GND | (57.35, 58.25) | 1.3 | 0.8 | yes |
