## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 62 on the top (F), 102 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 4.4 mm straight, B side |
| Current: J11.23 -> U5.3 | 4.5 mm straight, F side |
| Current net half-perimeter | 4.7 mm |
| Current pins to 74HC14 U104 | 20.8 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 23.1 mm (U5.3 - U105.14) |
| Current pins to M1_ON | 10.4 mm (U5.3 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 1.9 mm (limit 2.5) |
| R105.1 -> D27.2 | 2.0 mm (limit 2.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 8.3 mm (U2.3 - U101.5), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 15.7 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C53 | 2.0 | B / B |
| U4.5 | 5V | C95 | 1.3 | F / B |
| U5.5 | 5V | C52 | 1.8 | F / F |
| U14.5 | 5V | C57 | 11.6 | B / F |
| U18.16 | 5V | C24 | 1.7 | F / B |
| U21.5 | 5V | C57 | 3.8 | B / F |
| U26.17 | 5V | C23 | 1.4 | B / F |
| U28.16 | 5V | C58 | 1.5 | F / B |
| U101.14 | 5V | C26 | 11.5 | B / F |
| U102.14 | 5V | C57 | 2.4 | F / F |
| U103.14 | 5V | C23 | 2.2 | F / F |
| U104.14 | 5V | C91 | 1.8 | F / B |
| U105.14 | 5V | C104 | 1.6 | F / B |
| U106.14 | 5V | C26 | 2.0 | F / F |
| U3.5 | analog_5V | C36 | 1.8 | B / B |
| U7.5 | analog_5V | C66 | 1.8 | B / B |
| U13.5 | analog_5V | C37 | 1.6 | B / B |
| U22.5 | analog_5V | C38 | 1.8 | F / F |
| U23.5 | analog_5V | C63 | 1.8 | B / B |
| U24.5 | analog_5V | C32 | 1.9 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 14.7 |
| 2 | Vref_2_arduino | R100.1 | 4.5 |
| 3 | Vref_3_arduino | R77.1 | 18.5 |
| 4 | IREF1 | R29.1 | 24.5 |
| 5 | IREF2 | R30.1 | 20.0 |
| 6 | IREF3 | R57.1 | 15.6 |
| 7 | SCL | U26.5 | 22.8 |
| 8 | SDA | U26.6 | 22.8 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 6.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U102); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 43, tallest 1.75 mm (limit 2.7)
