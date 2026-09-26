## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 72 on the top (F), 92 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 2.8 mm straight, B side |
| Current: J11.23 -> U5.3 | 3.0 mm straight, B side |
| Current net half-perimeter | 4.4 mm |
| Current pins to 74HC14 U104 | 23.8 mm (J11.23 - U104.7) |
| Current pins to 74HC14 U105 | 17.5 mm (U2.4 - U105.7) |
| Current pins to M1_ON | 18.9 mm (J11.23 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 2.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.7 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.3 mm (limit 6.0) |
| R100.1 -> J9.2 | 4.4 mm (limit 6.0) |
| R77.1 -> J9.3 | 5.9 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 18.9 mm (J11.23 - U101.5), minimum 8.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U101, U102, U103, U18, U28.9, U28.10, U28.11, U106.5, U106.6, U106.12, U106.13} | 3.8 mm (U4.4 - U28.11), minimum 4.0 |
| route proxy: Current vs IREF1 | 8.2 mm (J11.23-U2.4 / J9.4-R29.1), minimum 8.0 |
| route proxy: Current vs IREF2 | 12.8 mm (J11.23-U2.4 / R30.1-U106.5), minimum 8.0 |
| route proxy: Current vs IREF3 | 2.0 mm (J11.23-U2.4 / R57.1-U106.13), minimum 8.0 **short** |
| route proxy: Current vs ARD_M1_INHIBIT | 8.4 mm (J11.23-U2.4 / R105.1-J9.11), minimum 8.0 |
| route proxy: Current vs Vref_1_arduino | 19.4 mm (J11.23-U2.4 / J9.1-R101.1), minimum 8.0 |
| route proxy: Current vs Vref_2_arduino | 17.5 mm (J11.23-U2.4 / J9.2-R100.1), minimum 8.0 |
| route proxy: Current vs Vref_3_arduino | 17.0 mm (J11.23-U2.4 / J9.3-R77.1), minimum 8.0 |
| route proxy: Current vs M1_INHIBIT | 29.8 mm (J11.23-U2.4 / D1.1-U104.1), minimum 8.0 |
| route proxy: V_err vs SCL | 16.4 mm (U28.3-U5.4 / J9.7-U26.5), minimum 4.0 |
| route proxy: V_err vs SDA | 14.2 mm (U28.3-U5.4 / J9.8-U26.6), minimum 4.0 |
| route proxy: V_err vs M1_ON | 22.4 mm (U28.3-U5.4 / J11.3-U101.5), minimum 4.0 |
| route proxy: V_err vs Net-(U103A-A) | 4.9 mm (U5.4-U4.4 / U103.1-U28.9), minimum 4.0 |
| route proxy: V_err vs Net-(U102C-A) | 1.1 mm (U5.4-U4.4 / U18.2-U28.10), minimum 4.0 **short** |
| route proxy: V_err vs Net-(U102B-A) | 1.4 mm (U5.4-U4.4 / U18.3-U28.11), minimum 4.0 **short** |
| route proxy: V_err vs IREF1 | 11.0 mm (U28.3-U5.4 / J9.4-R29.1), minimum 4.0 |
| route proxy: V_err vs IREF2 | 14.2 mm (U28.3-U5.4 / R30.1-U106.5), minimum 4.0 |
| route proxy: V_err vs IREF3 | 4.7 mm (U28.3-U5.4 / R57.1-U106.13), minimum 4.0 |
| route proxy: Net-(U2-In+) vs SCL | 16.9 mm (R11.2-U2.3 / J9.7-U26.5), minimum 4.0 |
| route proxy: Net-(U2-In+) vs SDA | 14.9 mm (R11.2-U2.3 / J9.8-U26.6), minimum 4.0 |
| route proxy: Net-(U2-In+) vs M1_ON | 21.8 mm (R11.2-U2.3 / J11.3-U101.5), minimum 4.0 |
| route proxy: Net-(U2-In+) vs Net-(U103A-A) | 4.4 mm (R11.2-R17.1 / U103.1-U28.9), minimum 4.0 |
| route proxy: Net-(U2-In+) vs Net-(U102C-A) | 2.4 mm (R11.2-U2.3 / U18.2-U28.10), minimum 4.0 **short** |
| route proxy: Net-(U2-In+) vs Net-(U102B-A) | 2.9 mm (R11.2-U2.3 / U18.3-U28.11), minimum 4.0 **short** |
| route proxy: Net-(U2-In+) vs IREF1 | 9.5 mm (R11.2-U2.3 / J9.4-R29.1), minimum 4.0 |
| route proxy: Net-(U2-In+) vs IREF2 | 12.6 mm (R11.2-U2.3 / R30.1-U106.5), minimum 4.0 |
| route proxy: Net-(U2-In+) vs IREF3 | 3.2 mm (R11.2-U2.3 / R57.1-U106.13), minimum 4.0 **short** |
| route proxy: Net-(U2-In+) vs 0A_hi | 0.5 mm (R11.2-U2.3 / R11.1-U2.1), minimum 4.0 **short** |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 6.2 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C28 | 1.7 | B / B |
| U4.5 | 5V | C98 | 1.6 | B / B |
| U5.5 | 5V | C24 | 1.8 | B / B |
| U14.5 | 5V | C12 | 1.8 | F / F |
| U18.16 | 5V | C52 | 2.1 | F / F |
| U21.5 | 5V | C53 | 1.8 | B / B |
| U26.17 | 5V | C26 | 1.8 | B / F |
| U28.16 | 5V | C99 | 1.5 | F / B |
| U101.14 | 5V | C22 | 4.4 | F / F |
| U102.14 | 5V | C94 | 0.4 | F / B |
| U103.14 | 5V | C104 | 1.6 | F / F |
| U104.14 | 5V | C58 | 1.9 | B / B |
| U105.14 | 5V | C57 | 2.0 | F / B |
| U106.14 | 5V | C23 | 1.9 | B / B |
| U3.5 | analog_5V | C66 | 1.9 | F / B |
| U7.5 | analog_5V | C36 | 2.0 | B / B |
| U13.5 | analog_5V | C32 | 1.9 | B / B |
| U22.5 | analog_5V | C63 | 1.6 | F / F |
| U23.5 | analog_5V | C38 | 1.9 | B / B |
| U24.5 | analog_5V | C37 | 2.0 | F / F |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.3 |
| 2 | Vref_2_arduino | R100.1 | 4.4 |
| 3 | Vref_3_arduino | R77.1 | 5.9 |
| 4 | IREF1 | R29.1 | 28.0 |
| 5 | IREF2 | R30.1 | 10.8 |
| 6 | IREF3 | R57.1 | 5.4 |
| 7 | SCL | U26.5 | 10.2 |
| 8 | SDA | U26.6 | 12.9 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 18.9 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 46, tallest 1.80 mm (limit 2.7)
