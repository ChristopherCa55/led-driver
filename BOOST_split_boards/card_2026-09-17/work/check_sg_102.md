## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 69 on the top (F), 95 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 3.7 mm straight, F side |
| Current: J11.23 -> U5.3 | 3.7 mm straight, B side |
| Current net half-perimeter | 5.3 mm |
| Current pins to 74HC14 U104 | 17.1 mm (J11.23 - U104.7) |
| Current pins to 74HC14 U105 | 7.4 mm (J11.23 - U105.8) |
| Current pins to M1_ON | 19.3 mm (J11.23 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 4.0 mm (limit 2.5) |
| R105.1 -> D27.2 | 2.1 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.2 mm (limit 6.0) |
| R100.1 -> J9.2 | 4.5 mm (limit 6.0) |
| R77.1 -> J9.3 | 4.3 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 7.4 mm (J11.23 - U105.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 12.7 mm (U28.3 - J11.3), minimum 8.0 |
| route proxy: Current vs SCL | 12.4 mm (J11.23-U2.4 / J9.7-U26.5), minimum 8.0 |
| route proxy: Current vs SDA | 10.2 mm (J11.23-U2.4 / J9.8-U26.6), minimum 8.0 |
| route proxy: Current vs M1_ON | 19.3 mm (J11.23-U2.4 / U104.2-U101.5), minimum 8.0 |
| route proxy: Current vs M2_ON | 19.7 mm (J11.23-U2.4 / J11.4-U104.4), minimum 8.0 |
| route proxy: Current vs out_2_on | 17.9 mm (J11.23-U2.4 / J11.6-U104.6), minimum 8.0 |
| route proxy: Current vs out_3_on | 17.9 mm (U2.4-U5.3 / J11.8-U104.8), minimum 8.0 |
| route proxy: Current vs VerrGT0 | 8.6 mm (U2.4-U5.3 / U104.10-U103.2), minimum 8.0 |
| route proxy: Current vs ena_out_2 | 17.9 mm (U2.4-U5.3 / J11.7-U104.12), minimum 8.0 |
| route proxy: Current vs ena_out_1 | 3.0 mm (J11.23-U2.4 / J11.5-U105.2), minimum 8.0 **short** |
| route proxy: Current vs ena_out_3 | 7.1 mm (J11.23-U2.4 / U103.4-U105.4), minimum 8.0 **short** |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 20.2 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C94 | 2.1 | F / F |
| U4.5 | 5V | C26 | 2.0 | B / B |
| U5.5 | 5V | C94 | 1.9 | B / F |
| U14.5 | 5V | C92 | 1.9 | F / B |
| U18.16 | 5V | C54 | 1.0 | F / B |
| U21.5 | 5V | C99 | 0.4 | F / B |
| U26.17 | 5V | C28 | 1.8 | B / B |
| U28.16 | 5V | C58 | 2.0 | F / F |
| U101.14 | 5V | C24 | 1.9 | F / F |
| U102.14 | 5V | C52 | 3.9 | B / F |
| U103.14 | 5V | C23 | 1.4 | F / B |
| U104.14 | 5V | C24 | 2.9 | B / F |
| U105.14 | 5V | C29 | 0.9 | B / F |
| U106.14 | 5V | C104 | 5.5 | F / B |
| U3.5 | analog_5V | C32 | 2.0 | B / B |
| U7.5 | analog_5V | C38 | 1.8 | F / F |
| U13.5 | analog_5V | C63 | 1.7 | B / B |
| U22.5 | analog_5V | C66 | 1.9 | F / F |
| U23.5 | analog_5V | C37 | 1.8 | B / B |
| U24.5 | analog_5V | C36 | 2.0 | F / F |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.2 |
| 2 | Vref_2_arduino | R100.1 | 4.5 |
| 3 | Vref_3_arduino | R77.1 | 4.3 |
| 4 | IREF1 | R29.1 | 12.0 |
| 5 | IREF2 | R30.1 | 9.2 |
| 6 | IREF3 | R57.1 | 7.8 |
| 7 | SCL | U26.5 | 13.5 |
| 8 | SDA | U26.6 | 14.9 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 7.4 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 41, tallest 1.80 mm (limit 2.7)
