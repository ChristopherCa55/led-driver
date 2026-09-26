## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 63 on the top (F), 101 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 4.4 mm straight, F side |
| Current: J11.23 -> U5.3 | 4.6 mm straight, B side |
| Current net half-perimeter | 6.4 mm |
| Current pins to 74HC14 U104 | 18.2 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 21.1 mm (U5.3 - U105.7) |
| Current pins to M1_ON | 10.9 mm (U5.3 - U101.5) |
| Current pins to SCL | 9.3 mm (J11.23 - U26.5) |
| Current pins to SDA | 9.9 mm (J11.23 - U26.6) |
| D27.1 -> U104.1 | 2.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.0 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.8 mm (limit 6.0) |
| R100.1 -> J9.2 | 4.2 mm (limit 6.0) |
| R77.1 -> J9.3 | 5.7 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 9.3 mm (J11.23 - U26.5), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 8.1 mm (U28.3 - U101.5), minimum 8.0 |
| route proxy: Current vs SCL | 3.8 mm (J11.23-U2.4 / J9.7-U26.5), minimum 8.0 **short** |
| route proxy: Current vs SDA | 4.4 mm (J11.23-U2.4 / J9.8-U26.6), minimum 8.0 **short** |
| route proxy: Current vs M1_ON | 7.7 mm (U2.4-U5.3 / J11.3-U101.5), minimum 8.0 **short** |
| route proxy: Current vs M2_ON | 19.7 mm (U2.4-U5.3 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 19.6 mm (U2.4-U5.3 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 17.5 mm (U2.4-U5.3 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 9.1 mm (U2.4-U5.3 / U103.2-U102.5), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 16.9 mm (U2.4-U5.3 / J11.7-U102.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 17.9 mm (U2.4-U5.3 / J11.5-U102.2), minimum 8.0 |
| route proxy: Current vs ena_out_3 | 13.5 mm (U2.4-U5.3 / U105.4-U103.4), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 19.9 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C104 | 1.9 | F / B |
| U4.5 | 5V | C92 | 2.0 | B / B |
| U5.5 | 5V | C94 | 1.8 | B / B |
| U14.5 | 5V | C24 | 1.8 | B / B |
| U18.16 | 5V | C97 | 1.9 | F / B |
| U21.5 | 5V | C98 | 1.9 | F / F |
| U26.17 | 5V | C28 | 1.9 | F / B |
| U28.16 | 5V | C52 | 0.8 | F / B |
| U101.14 | 5V | C26 | 2.0 | F / B |
| U102.14 | 5V | C99 | 0.9 | F / B |
| U103.14 | 5V | C91 | 1.2 | B / F |
| U104.14 | 5V | C12 | 2.6 | F / B |
| U105.14 | 5V | C53 | 1.0 | B / F |
| U106.14 | 5V | C96 | 0.9 | F / B |
| U3.5 | analog_5V | C38 | 1.6 | F / F |
| U7.5 | analog_5V | C32 | 1.9 | F / B |
| U13.5 | analog_5V | C37 | 2.0 | F / F |
| U22.5 | analog_5V | C63 | 1.7 | F / F |
| U23.5 | analog_5V | C36 | 2.0 | F / F |
| U24.5 | analog_5V | C66 | 2.0 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.8 |
| 2 | Vref_2_arduino | R100.1 | 4.2 |
| 3 | Vref_3_arduino | R77.1 | 5.7 |
| 4 | IREF1 | R29.1 | 12.9 |
| 5 | IREF2 | R30.1 | 11.0 |
| 6 | IREF3 | R57.1 | 6.8 |
| 7 | SCL | U26.5 | 20.3 |
| 8 | SDA | U26.6 | 18.0 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 10.0 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 41, tallest 1.80 mm (limit 2.7)
