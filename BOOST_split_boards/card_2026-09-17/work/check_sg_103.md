## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: R101 (0.01 mm)
- SMD parts: 70 on the top (F), 94 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 3.0 mm straight, B side |
| Current: J11.23 -> U5.3 | 8.0 mm straight, F side |
| Current net half-perimeter | 11.3 mm |
| Current pins to 74HC14 U104 | 21.9 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 12.0 mm (J11.23 - U105.1) |
| Current pins to M1_ON | 9.2 mm (U5.3 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 3.0 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.4 mm (limit 2.0) |
| R101.1 -> J9.1 | 6.7 mm (limit 6.0) |
| R100.1 -> J9.2 | 5.3 mm (limit 6.0) |
| R77.1 -> J9.3 | 7.5 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 7.1 mm (U5.4 - U101.5), minimum 8.0 |
| route proxy: Current vs SCL | 12.4 mm (J11.23-U2.4 / J9.7-U26.5), minimum 8.0 |
| route proxy: Current vs SDA | 10.2 mm (J11.23-U2.4 / J9.8-U26.6), minimum 8.0 |
| route proxy: Current vs M1_ON | 5.7 mm (U2.4-U5.3 / J11.3-U101.5), minimum 8.0 **short** |
| route proxy: Current vs M2_ON | 21.8 mm (U2.4-U5.3 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 19.7 mm (U2.4-U5.3 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 17.5 mm (U2.4-U5.3 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 8.8 mm (U2.4-U5.3 / U101.1-U103.2), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 16.3 mm (U2.4-U5.3 / J11.7-U102.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 13.1 mm (J11.23-U2.4 / J11.5-U105.2), minimum 8.0 |
| route proxy: Current vs ena_out_3 | 14.0 mm (U2.4-U5.3 / J11.9-U105.4), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 17.8 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C94 | 1.9 | B / B |
| U4.5 | 5V | C104 | 1.8 | B / F |
| U5.5 | 5V | C53 | 1.5 | F / B |
| U14.5 | 5V | C29 | 1.9 | B / B |
| U18.16 | 5V | C58 | 1.1 | F / B |
| U21.5 | 5V | C92 | 1.9 | F / F |
| U26.17 | 5V | C22 | 2.2 | F / F |
| U28.16 | 5V | C26 | 2.1 | F / F |
| U101.14 | 5V | C91 | 9.2 | B / B |
| U102.14 | 5V | C57 | 4.3 | B / B |
| U103.14 | 5V | C98 | 0.6 | B / F |
| U104.14 | 5V | C57 | 2.5 | B / B |
| U105.14 | 5V | C99 | 2.6 | F / B |
| U106.14 | 5V | C57 | 6.5 | F / B |
| U3.5 | analog_5V | C66 | 2.0 | F / F |
| U7.5 | analog_5V | C66 | 1.7 | B / F |
| U13.5 | analog_5V | C36 | 1.8 | F / F |
| U22.5 | analog_5V | C32 | 1.8 | F / F |
| U23.5 | analog_5V | C38 | 6.1 | B / B |
| U24.5 | analog_5V | C37 | 1.6 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 6.7 |
| 2 | Vref_2_arduino | R100.1 | 5.3 |
| 3 | Vref_3_arduino | R77.1 | 7.5 |
| 4 | IREF1 | R29.1 | 8.8 |
| 5 | IREF2 | R30.1 | 22.7 |
| 6 | IREF3 | U106.13 | 22.3 |
| 7 | SCL | U26.5 | 12.9 |
| 8 | SDA | U26.6 | 16.3 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 17.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U105); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 35, tallest 1.80 mm (limit 2.7)
