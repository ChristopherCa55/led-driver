## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 4
  - H3 x U106: 1.640 mm2
  - J11 x J9: 2.099 mm2
  - J11 x U106: 0.861 mm2
  - J11 x U5: 0.001 mm2
- Outside the card: none
- Inside a mounting-hole keep-out: C46 (0.00 mm), R77 (0.00 mm), U106 (0.24 mm)
- SMD parts: 72 on the top (F), 92 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 2.8 mm straight, F side |
| Current: J11.23 -> U5.3 | 2.7 mm straight, B side |
| Current net half-perimeter | 3.6 mm |
| Current pins to 74HC14 U104 | 14.5 mm (J11.23 - U104.1) |
| Current pins to 74HC14 U105 | 11.0 mm (U2.4 - U105.12) |
| Current pins to M1_ON | 8.9 mm (U5.3 - U101.5) |
| Current pins to SCL | 12.2 mm (J11.23 - J9.7) |
| Current pins to SDA | 9.9 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 2.5 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.5 mm (limit 2.0) |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 19.0 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C104 | 2.0 | F / B |
| U4.5 | 5V | C95 | 1.6 | B / F |
| U5.5 | 5V | C54 | 1.5 | B / F |
| U14.5 | 5V | C94 | 2.0 | B / F |
| U18.16 | 5V | C58 | 1.7 | B / B |
| U21.5 | 5V | C12 | 1.8 | F / B |
| U26.17 | 5V | C99 | 2.0 | B / B |
| U28.16 | 5V | C57 | 1.5 | F / B |
| U101.14 | 5V | C97 | 1.0 | B / F |
| U102.14 | 5V | C26 | 1.2 | F / B |
| U103.14 | 5V | C28 | 1.8 | F / F |
| U104.14 | 5V | C22 | 1.4 | F / B |
| U105.14 | 5V | C52 | 1.9 | F / B |
| U106.14 | 5V | C23 | 2.0 | F / B |
| U3.5 | analog_5V | C66 | 1.5 | F / B |
| U7.5 | analog_5V | C38 | 1.2 | B / F |
| U13.5 | analog_5V | C63 | 1.6 | B / F |
| U22.5 | analog_5V | C37 | 2.0 | F / B |
| U23.5 | analog_5V | C32 | 1.7 | B / F |
| U24.5 | analog_5V | C36 | 1.8 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 17.2 |
| 2 | Vref_2_arduino | R100.1 | 19.5 |
| 3 | Vref_3_arduino | R77.1 | 11.5 |
| 4 | IREF1 | R29.1 | 6.7 |
| 5 | IREF2 | R30.1 | 4.8 |
| 6 | IREF3 | R57.1 | 8.1 |
| 7 | SCL | U26.5 | 12.0 |
| 8 | SDA | U26.6 | 13.9 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 5.6 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.80 mm (C49); tallest on the underside: 1.80 mm (C64)
- Over the top limit: C49 (C_1206_3216Metric, 1.80 mm on top)
- Underside parts over an output can: 35, tallest 1.75 mm (limit 2.7)
