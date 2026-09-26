## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 5
  - C52 x R6: 0.003 mm2
  - D1 x D27: 0.256 mm2
  - J11 x J9: 2.099 mm2
  - J9 x U3: 0.002 mm2
  - R6 x U26: 0.001 mm2
- Outside the card: none
- Inside a mounting-hole keep-out: R100 (0.00 mm)
- SMD parts: 68 on the top (F), 96 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 19.7 mm straight, B side |
| Current: J11.23 -> U5.3 | 19.7 mm straight, F side |
| Current net half-perimeter | 27.3 mm |
| Current pins to 74HC14 U104 | 6.1 mm (U5.3 - U104.7) |
| Current pins to 74HC14 U105 | 7.4 mm (J11.23 - U105.1) |
| Current pins to M1_ON | 8.7 mm (U5.3 - U104.2) |
| Current pins to SCL | 7.5 mm (U2.4 - J9.7) |
| Current pins to SDA | 9.9 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 4.4 mm (limit 2.5) |
| R105.1 -> D27.2 | 2.0 mm (limit 2.0) |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 18.2 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C23 | 2.2 | B / B |
| U4.5 | 5V | C95 | 1.9 | F / F |
| U5.5 | 5V | C52 | 1.8 | F / F |
| U14.5 | 5V | C99 | 1.5 | F / B |
| U18.16 | 5V | C26 | 1.7 | B / B |
| U21.5 | 5V | C91 | 2.0 | F / B |
| U26.17 | 5V | C23 | 1.6 | F / B |
| U28.16 | 5V | C29 | 2.0 | F / B |
| U101.14 | 5V | C53 | 1.6 | F / B |
| U102.14 | 5V | C96 | 1.0 | F / B |
| U103.14 | 5V | C104 | 0.5 | F / B |
| U104.14 | 5V | C94 | 1.7 | F / F |
| U105.14 | 5V | C54 | 0.9 | B / F |
| U106.14 | 5V | C24 | 1.0 | F / B |
| U3.5 | analog_5V | C36 | 1.8 | B / B |
| U7.5 | analog_5V | C66 | 1.8 | F / B |
| U13.5 | analog_5V | C32 | 1.8 | B / B |
| U22.5 | analog_5V | C37 | 1.6 | B / B |
| U23.5 | analog_5V | C38 | 1.3 | F / B |
| U24.5 | analog_5V | C63 | 0.9 | B / F |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 6.6 |
| 2 | Vref_2_arduino | R100.1 | 4.7 |
| 3 | Vref_3_arduino | R77.1 | 7.6 |
| 4 | IREF1 | R29.1 | 15.2 |
| 5 | IREF2 | R30.1 | 14.7 |
| 6 | IREF3 | R57.1 | 26.1 |
| 7 | SCL | U26.5 | 17.2 |
| 8 | SDA | U26.6 | 20.4 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 8.1 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.80 mm (C64); tallest on the underside: 1.80 mm (C49)
- Over the top limit: C64 (C_1206_3216Metric, 1.80 mm on top)
- Underside parts over an output can: 38, tallest 1.80 mm (limit 2.7)
