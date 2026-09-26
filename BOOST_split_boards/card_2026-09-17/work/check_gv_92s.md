## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 67 on the top (F), 97 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 4.6 mm straight, F side |
| Current: J11.23 -> U5.3 | 4.6 mm straight, B side |
| Current net half-perimeter | 6.5 mm |
| Current pins to 74HC14 U104 | 18.2 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 21.2 mm (U2.4 - U105.7) |
| Current pins to M1_ON | 10.1 mm (U5.3 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 2.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 0.6 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.8 mm (limit 6.0) |
| R100.1 -> J9.2 | 4.6 mm (limit 6.0) |
| R77.1 -> J9.3 | 4.3 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 7.8 mm (U28.3 - U101.5), minimum 8.0 |
| route proxy: Current vs SCL | 1.9 mm (J11.23-U2.4 / J9.7-U26.5), minimum 8.0 **short** |
| route proxy: Current vs SDA | 2.3 mm (J11.23-U2.4 / J9.8-U26.6), minimum 8.0 **short** |
| route proxy: Current vs M1_ON | 7.2 mm (U2.4-U5.3 / J11.3-U101.5), minimum 8.0 **short** |
| route proxy: Current vs M2_ON | 19.6 mm (J11.23-U2.4 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 19.5 mm (J11.23-U2.4 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 17.4 mm (J11.23-U2.4 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 9.0 mm (J11.23-U2.4 / U103.2-U102.5), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 16.8 mm (J11.23-U2.4 / J11.7-U102.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 17.7 mm (J11.23-U2.4 / J11.5-U102.2), minimum 8.0 |
| route proxy: Current vs ena_out_3 | 13.0 mm (U2.4-U5.3 / U105.4-U103.4), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 19.9 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C104 | 1.9 | F / B |
| U4.5 | 5V | C92 | 2.0 | B / B |
| U5.5 | 5V | C94 | 1.9 | B / B |
| U14.5 | 5V | C24 | 1.6 | B / B |
| U18.16 | 5V | C22 | 2.0 | F / F |
| U21.5 | 5V | C98 | 1.8 | F / F |
| U26.17 | 5V | C97 | 1.9 | F / F |
| U28.16 | 5V | C52 | 0.9 | F / B |
| U101.14 | 5V | C26 | 1.9 | F / B |
| U102.14 | 5V | C99 | 0.6 | F / B |
| U103.14 | 5V | C91 | 1.4 | B / F |
| U104.14 | 5V | C12 | 2.6 | F / B |
| U105.14 | 5V | C53 | 1.7 | B / F |
| U106.14 | 5V | C54 | 1.1 | F / B |
| U3.5 | analog_5V | C38 | 1.8 | F / F |
| U7.5 | analog_5V | C32 | 1.8 | F / B |
| U13.5 | analog_5V | C37 | 1.8 | F / F |
| U22.5 | analog_5V | C63 | 1.9 | F / F |
| U23.5 | analog_5V | C36 | 2.0 | F / F |
| U24.5 | analog_5V | C66 | 2.0 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.8 |
| 2 | Vref_2_arduino | R100.1 | 4.6 |
| 3 | Vref_3_arduino | R77.1 | 4.3 |
| 4 | IREF1 | R29.1 | 12.5 |
| 5 | IREF2 | R30.1 | 11.6 |
| 6 | IREF3 | R57.1 | 12.5 |
| 7 | SCL | U26.5 | 24.8 |
| 8 | SDA | U26.6 | 21.9 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 10.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 43, tallest 1.80 mm (limit 2.7)
