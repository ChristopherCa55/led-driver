## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 4
  - H3 x U28: 1.940 mm2
  - J11 x J9: 2.099 mm2
  - J11 x U28: 0.480 mm2
  - J11 x U3: 1.749 mm2
- Outside the card: none
- Inside a mounting-hole keep-out: U3 (0.37 mm), U24 (0.00 mm), U28 (0.28 mm)
- SMD parts: 71 on the top (F), 93 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 2.6 mm straight, F side |
| Current: J11.23 -> U5.3 | 2.8 mm straight, B side |
| Current net half-perimeter | 2.8 mm |
| Current pins to 74HC14 U104 | 13.3 mm (J11.23 - U104.14) |
| Current pins to 74HC14 U105 | 28.2 mm (J11.23 - U105.7) |
| Current pins to M1_ON | 17.0 mm (J11.23 - U104.2) |
| Current pins to SCL | 12.2 mm (J11.23 - J9.7) |
| Current pins to SDA | 9.9 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 1.2 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.7 mm (limit 2.0) |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 11.1 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C29 | 1.6 | F / B |
| U4.5 | 5V | C91 | 2.0 | F / B |
| U5.5 | 5V | C26 | 1.7 | B / F |
| U14.5 | 5V | C94 | 1.9 | B / F |
| U18.16 | 5V | C98 | 1.7 | F / B |
| U21.5 | 5V | C97 | 0.7 | F / B |
| U26.17 | 5V | C53 | 1.8 | F / B |
| U28.16 | 5V | C58 | 1.9 | F / F |
| U101.14 | 5V | C95 | 2.2 | F / B |
| U102.14 | 5V | C104 | 1.5 | F / B |
| U103.14 | 5V | C92 | 1.1 | F / B |
| U104.14 | 5V | C12 | 1.7 | B / B |
| U105.14 | 5V | C24 | 1.0 | F / B |
| U106.14 | 5V | C23 | 2.2 | B / B |
| U3.5 | analog_5V | C63 | 1.4 | B / F |
| U7.5 | analog_5V | C32 | 2.0 | F / B |
| U13.5 | analog_5V | C36 | 1.7 | B / F |
| U22.5 | analog_5V | C37 | 2.0 | B / F |
| U23.5 | analog_5V | C66 | 1.4 | F / B |
| U24.5 | analog_5V | C38 | 0.2 | F / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 15.5 |
| 2 | Vref_2_arduino | R100.1 | 18.6 |
| 3 | Vref_3_arduino | R77.1 | 20.8 |
| 4 | IREF1 | U106.6 | 27.3 |
| 5 | IREF2 | R30.1 | 19.8 |
| 6 | IREF3 | R57.1 | 25.7 |
| 7 | SCL | U26.5 | 27.7 |
| 8 | SDA | U26.6 | 27.2 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 4.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 39, tallest 1.80 mm (limit 2.7)
