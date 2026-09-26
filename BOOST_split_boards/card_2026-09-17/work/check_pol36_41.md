## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 3
  - H3 x U106: 0.655 mm2
  - J11 x U101: 0.032 mm2
  - J11 x U106: 1.105 mm2
- Outside the card: none
- Inside a mounting-hole keep-out: C54 (0.01 mm), U106 (0.15 mm)
- SMD parts: 72 on the top (F), 92 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 2.8 mm straight, B side |
| Current: J11.23 -> U5.3 | 2.6 mm straight, F side |
| Current net half-perimeter | 3.7 mm |
| Current pins to 74HC14 U104 | 9.9 mm (U5.3 - U104.7) |
| Current pins to 74HC14 U105 | 16.6 mm (J11.23 - U105.14) |
| Current pins to M1_ON | 15.7 mm (J11.23 - U101.5) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 2.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.5 mm (limit 2.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, U26, net:SCL, net:SDA} | 9.9 mm (U5.3 - U104.7), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 13.6 mm (U4.4 - J11.3), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 9.4 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C94 | 1.8 | B / B |
| U4.5 | 5V | C53 | 1.9 | F / B |
| U5.5 | 5V | C26 | 1.6 | F / F |
| U14.5 | 5V | C28 | 1.2 | F / B |
| U18.16 | 5V | C29 | 2.0 | F / B |
| U21.5 | 5V | C24 | 1.9 | B / B |
| U26.17 | 5V | C95 | 2.0 | F / F |
| U28.16 | 5V | C52 | 1.9 | B / F |
| U101.14 | 5V | C54 | 1.6 | B / B |
| U102.14 | 5V | C104 | 2.6 | B / B |
| U103.14 | 5V | C22 | 1.7 | F / F |
| U104.14 | 5V | C98 | 2.2 | F / F |
| U105.14 | 5V | C104 | 1.0 | F / B |
| U106.14 | 5V | C99 | 1.0 | F / B |
| U3.5 | analog_5V | C63 | 1.9 | F / F |
| U7.5 | analog_5V | C38 | 1.9 | B / B |
| U13.5 | analog_5V | C37 | 1.8 | F / F |
| U22.5 | analog_5V | C66 | 2.0 | B / B |
| U23.5 | analog_5V | C32 | 1.8 | F / F |
| U24.5 | analog_5V | C36 | 1.0 | F / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 6.7 |
| 2 | Vref_2_arduino | R100.1 | 12.3 |
| 3 | Vref_3_arduino | R77.1 | 27.0 |
| 4 | IREF1 | U106.6 | 12.9 |
| 5 | IREF2 | R30.1 | 4.7 |
| 6 | IREF3 | R57.1 | 9.9 |
| 7 | SCL | U26.5 | 7.5 |
| 8 | SDA | U26.6 | 9.8 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 10.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U103); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 43, tallest 1.80 mm (limit 2.7)
