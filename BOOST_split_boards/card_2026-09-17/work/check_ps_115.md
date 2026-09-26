## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 68 on the top (F), 96 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 13.6 mm straight, B side |
| Current: J11.23 -> U5.3 | 2.9 mm straight, B side |
| Current net half-perimeter | 14.2 mm |
| Current pins to 74HC14 U104 | 16.1 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 18.5 mm (J11.23 - U105.8) |
| Current pins to M1_ON | 16.4 mm (J11.23 - U104.2) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 1.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 0.8 mm (limit 2.0) |
| R101.1 -> J9.1 | 7.1 mm (limit 6.0) |
| R100.1 -> J9.2 | 6.6 mm (limit 6.0) |
| R77.1 -> J9.3 | 4.1 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 16.4 mm (J11.23 - U104.2), minimum 8.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U101, U102, U103, U18, U28.9, U28.10, U28.11, U106.5, U106.6, U106.12, U106.13} | 3.5 mm (U2.4 - U28.10), minimum 4.0 |
| route proxy: Current vs SCL | 12.4 mm (J11.23-U5.3 / J9.7-U26.5), minimum 8.0 |
| route proxy: Current vs SDA | 10.2 mm (J11.23-U5.3 / J9.8-U26.6), minimum 8.0 |
| route proxy: Current vs M1_ON | 16.3 mm (J11.23-U5.3 / J11.3-U104.2), minimum 8.0 |
| route proxy: Current vs M2_ON | 16.4 mm (U5.3-U2.4 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 16.4 mm (U5.3-U2.4 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 20.4 mm (J11.23-U5.3 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 14.6 mm (U5.3-U2.4 / U102.5-U103.2), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 18.2 mm (U5.3-U2.4 / U104.12-U102.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 17.5 mm (U5.3-U2.4 / J11.5-U102.2), minimum 8.0 |
| route proxy: Current vs ena_out_3 | 13.9 mm (U5.3-U2.4 / J11.9-U103.4), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 7.8 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C99 | 1.7 | B / B |
| U4.5 | 5V | C52 | 1.6 | F / B |
| U5.5 | 5V | C26 | 2.0 | B / B |
| U14.5 | 5V | C58 | 1.8 | B / B |
| U18.16 | 5V | C95 | 2.0 | F / F |
| U21.5 | 5V | C104 | 1.9 | F / F |
| U26.17 | 5V | C22 | 2.2 | B / B |
| U28.16 | 5V | C29 | 1.8 | F / F |
| U101.14 | 5V | C98 | 1.7 | B / B |
| U102.14 | 5V | C24 | 1.7 | F / B |
| U103.14 | 5V | C54 | 2.6 | F / F |
| U104.14 | 5V | C96 | 1.6 | F / B |
| U105.14 | 5V | C94 | 2.0 | F / B |
| U106.14 | 5V | C54 | 1.8 | B / F |
| U3.5 | analog_5V | C32 | 1.7 | F / F |
| U7.5 | analog_5V | C66 | 1.9 | F / F |
| U13.5 | analog_5V | C63 | 1.8 | B / B |
| U22.5 | analog_5V | C37 | 1.7 | F / B |
| U23.5 | analog_5V | C36 | 2.0 | B / B |
| U24.5 | analog_5V | C38 | 2.0 | F / F |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 7.1 |
| 2 | Vref_2_arduino | R100.1 | 6.6 |
| 3 | Vref_3_arduino | R77.1 | 4.1 |
| 4 | IREF1 | R29.1 | 9.0 |
| 5 | IREF2 | R30.1 | 9.5 |
| 6 | IREF3 | R57.1 | 10.5 |
| 7 | SCL | U26.5 | 19.5 |
| 8 | SDA | U26.6 | 22.1 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 9.8 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U102); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 44, tallest 1.80 mm (limit 2.7)
