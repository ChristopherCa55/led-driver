## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 70 on the top (F), 94 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 2.9 mm straight, B side |
| Current: J11.23 -> U5.3 | 3.0 mm straight, F side |
| Current net half-perimeter | 4.1 mm |
| Current pins to 74HC14 U104 | 28.4 mm (J11.23 - U104.7) |
| Current pins to 74HC14 U105 | 29.0 mm (J11.23 - U105.14) |
| Current pins to M1_ON | 16.5 mm (J11.23 - U101.5) |
| Current pins to SCL | 12.1 mm (U2.4 - U26.5) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 15.1 mm (limit 2.5) |
| R105.1 -> D27.2 | 7.3 mm (limit 2.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 8.0 mm (U4.4 - U101.5), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 19.4 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C99 | 1.7 | B / B |
| U4.5 | 5V | C96 | 1.9 | F / F |
| U5.5 | 5V | C104 | 1.7 | F / B |
| U14.5 | 5V | C92 | 1.8 | F / F |
| U18.16 | 5V | C58 | 1.7 | F / F |
| U21.5 | 5V | C98 | 1.8 | F / F |
| U26.17 | 5V | C52 | 1.9 | F / F |
| U28.16 | 5V | C26 | 0.2 | B / F |
| U101.14 | 5V | C97 | 2.0 | B / B |
| U102.14 | 5V | C22 | 1.1 | F / B |
| U103.14 | 5V | C26 | 2.0 | F / F |
| U104.14 | 5V | C53 | 1.9 | F / F |
| U105.14 | 5V | C98 | 6.6 | B / F |
| U106.14 | 5V | C57 | 1.5 | F / B |
| U3.5 | analog_5V | C37 | 1.9 | F / F |
| U7.5 | analog_5V | C32 | 1.9 | F / F |
| U13.5 | analog_5V | C36 | 2.0 | B / B |
| U22.5 | analog_5V | C63 | 3.8 | B / B |
| U23.5 | analog_5V | C66 | 2.0 | F / F |
| U24.5 | analog_5V | C38 | 1.8 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 6.2 |
| 2 | Vref_2_arduino | R100.1 | 8.4 |
| 3 | Vref_3_arduino | R77.1 | 24.2 |
| 4 | IREF1 | R29.1 | 23.0 |
| 5 | IREF2 | R30.1 | 28.1 |
| 6 | IREF3 | R57.1 | 24.2 |
| 7 | SCL | U26.5 | 21.6 |
| 8 | SDA | U26.6 | 20.8 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 15.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U102); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 41, tallest 1.80 mm (limit 2.7)
