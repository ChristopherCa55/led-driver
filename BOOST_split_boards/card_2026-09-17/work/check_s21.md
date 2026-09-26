## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: none
- SMD parts: 79 on the top (F), 85 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 3.2 mm straight, F side |
| Current: J11.23 -> U5.3 | 3.7 mm straight, F side |
| Current net half-perimeter | 5.1 mm |
| Current pins to 74HC14 U104 | 11.3 mm (U5.3 - U104.1) |
| Current pins to 74HC14 U105 | 17.4 mm (U5.3 - U105.1) |
| Current pins to M1_ON | 9.7 mm (U5.3 - U101.5) |
| Current pins to SCL | 7.4 mm (U5.3 - U26.5) |
| Current pins to SDA | 8.1 mm (U5.3 - U26.6) |
| D27.1 -> U104.1 | 3.2 mm (limit 2.5) |
| R105.1 -> D27.2 | 2.0 mm (limit 2.0) |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 9.6 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C92 | 0.6 | F / B |
| U4.5 | 5V | C23 | 1.8 | B / B |
| U5.5 | 5V | C58 | 1.7 | F / B |
| U14.5 | 5V | C95 | 1.9 | F / B |
| U18.16 | 5V | C24 | 1.3 | F / B |
| U21.5 | 5V | C53 | 1.9 | F / F |
| U26.17 | 5V | C54 | 2.0 | B / B |
| U28.16 | 5V | C94 | 2.1 | F / F |
| U101.14 | 5V | C29 | 0.4 | F / B |
| U102.14 | 5V | C28 | 2.0 | F / B |
| U103.14 | 5V | C97 | 1.0 | F / B |
| U104.14 | 5V | C96 | 1.7 | B / B |
| U105.14 | 5V | C104 | 1.9 | B / F |
| U106.14 | 5V | C26 | 1.7 | B / F |
| U3.5 | analog_5V | C66 | 2.0 | B / B |
| U7.5 | analog_5V | C38 | 1.8 | F / F |
| U13.5 | analog_5V | C63 | 2.0 | B / F |
| U22.5 | analog_5V | C36 | 2.0 | F / F |
| U23.5 | analog_5V | C37 | 1.8 | B / B |
| U24.5 | analog_5V | C32 | 1.9 | F / F |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 6.6 |
| 2 | Vref_2_arduino | R100.1 | 5.3 |
| 3 | Vref_3_arduino | R77.1 | 7.7 |
| 4 | IREF1 | U106.6 | 9.8 |
| 5 | IREF2 | R30.1 | 8.3 |
| 6 | IREF3 | R57.1 | 17.0 |
| 7 | SCL | U26.5 | 14.0 |
| 8 | SDA | U26.6 | 13.9 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | D27.2 | 18.4 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.80 mm (C64); tallest on the underside: 1.80 mm (C49)
- Over the top limit: C64 (C_1206_3216Metric, 1.80 mm on top)
- Underside parts over an output can: 29, tallest 1.75 mm (limit 2.7)
