## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 59 on the top (F), 105 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 15.7 mm straight, B side |
| Current: J11.23 -> U5.3 | 2.9 mm straight, B side |
| Current net half-perimeter | 16.5 mm |
| Current pins to 74HC14 U104 | 16.1 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 18.6 mm (J11.23 - U105.8) |
| Current pins to M1_ON | 16.4 mm (J11.23 - U104.2) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 1.2 mm (limit 2.5) |
| R105.1 -> D27.2 | 0.7 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.2 mm (limit 6.0) |
| R100.1 -> J9.2 | 6.6 mm (limit 6.0) |
| R77.1 -> J9.3 | 4.2 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 16.3 mm (U5.4 - U104.2), minimum 8.0 |
| route proxy: Current vs SCL | 12.4 mm (J11.23-U5.3 / J9.7-U26.5), minimum 8.0 |
| route proxy: Current vs SDA | 10.2 mm (J11.23-U5.3 / J9.8-U26.6), minimum 8.0 |
| route proxy: Current vs M1_ON | 16.3 mm (J11.23-U5.3 / J11.3-U104.2), minimum 8.0 |
| route proxy: Current vs M2_ON | 16.4 mm (U5.3-U2.4 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 16.4 mm (U5.3-U2.4 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 20.4 mm (J11.23-U5.3 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 14.3 mm (U5.3-U2.4 / U102.5-U103.2), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 18.5 mm (U5.3-U2.4 / U104.12-U102.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 17.4 mm (U5.3-U2.4 / J11.5-U102.2), minimum 8.0 |
| route proxy: Current vs ena_out_3 | 13.9 mm (U5.3-U2.4 / J11.9-U103.4), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 7.8 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C99 | 4.7 | B / B |
| U4.5 | 5V | C52 | 2.0 | F / B |
| U5.5 | 5V | C26 | 2.1 | B / B |
| U14.5 | 5V | C58 | 2.0 | B / B |
| U18.16 | 5V | C95 | 2.2 | F / F |
| U21.5 | 5V | C104 | 1.8 | F / F |
| U26.17 | 5V | C22 | 2.5 | B / B |
| U28.16 | 5V | C29 | 1.7 | F / F |
| U101.14 | 5V | C98 | 1.7 | B / B |
| U102.14 | 5V | C24 | 1.6 | F / B |
| U103.14 | 5V | C54 | 2.9 | F / F |
| U104.14 | 5V | C97 | 1.0 | F / B |
| U105.14 | 5V | C94 | 3.3 | F / B |
| U106.14 | 5V | C54 | 1.7 | B / F |
| U3.5 | analog_5V | C32 | 1.7 | F / F |
| U7.5 | analog_5V | C66 | 1.9 | F / F |
| U13.5 | analog_5V | C63 | 1.8 | B / B |
| U22.5 | analog_5V | C37 | 1.8 | F / B |
| U23.5 | analog_5V | C36 | 1.9 | B / B |
| U24.5 | analog_5V | C38 | 11.4 | F / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.2 |
| 2 | Vref_2_arduino | R100.1 | 6.6 |
| 3 | Vref_3_arduino | R77.1 | 4.2 |
| 4 | IREF1 | R29.1 | 12.8 |
| 5 | IREF2 | R30.1 | 9.8 |
| 6 | IREF3 | R57.1 | 13.2 |
| 7 | SCL | U26.5 | 19.5 |
| 8 | SDA | U26.6 | 22.1 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 9.9 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U102); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 43, tallest 1.80 mm (limit 2.7)
