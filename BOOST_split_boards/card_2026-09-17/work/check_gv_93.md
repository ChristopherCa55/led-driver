## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 0
- Outside the card: none
- Inside a mounting-hole keep-out: R100 (0.00 mm)
- SMD parts: 77 on the top (F), 87 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 4.2 mm straight, F side |
| Current: J11.23 -> U5.3 | 3.6 mm straight, B side |
| Current net half-perimeter | 6.1 mm |
| Current pins to 74HC14 U104 | 26.2 mm (U2.4 - U104.8) |
| Current pins to 74HC14 U105 | 24.7 mm (U2.4 - U105.1) |
| Current pins to M1_ON | 12.9 mm (U2.4 - U101.5) |
| Current pins to SCL | 12.0 mm (J11.23 - U26.5) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 9.8 mm (limit 2.5) |
| R105.1 -> D27.2 | 5.1 mm (limit 2.0) |
| R101.1 -> J9.1 | 4.1 mm (limit 6.0) |
| R100.1 -> J9.2 | 4.2 mm (limit 6.0) |
| R77.1 -> J9.3 | 5.9 mm (limit 6.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, net:SCL, net:SDA} | 10.2 mm (J11.23 - J9.8), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 9.5 mm (R11.2 - U101.5), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 39.3 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C53 | 0.7 | F / B |
| U4.5 | 5V | C23 | 2.6 | F / B |
| U5.5 | 5V | C24 | 1.7 | B / B |
| U14.5 | 5V | C96 | 2.0 | F / F |
| U18.16 | 5V | C22 | 1.7 | F / F |
| U21.5 | 5V | C54 | 2.0 | B / B |
| U26.17 | 5V | C58 | 1.9 | B / B |
| U28.16 | 5V | C98 | 2.4 | F / F |
| U101.14 | 5V | C104 | 1.2 | F / B |
| U102.14 | 5V | C29 | 1.8 | B / B |
| U103.14 | 5V | C53 | 1.9 | B / B |
| U104.14 | 5V | C57 | 4.4 | B / B |
| U105.14 | 5V | C57 | 1.0 | F / B |
| U106.14 | 5V | C92 | 2.2 | F / F |
| U3.5 | analog_5V | C38 | 1.9 | F / F |
| U7.5 | analog_5V | C66 | 2.0 | F / F |
| U13.5 | analog_5V | C32 | 1.9 | F / F |
| U22.5 | analog_5V | C36 | 2.0 | F / F |
| U23.5 | analog_5V | C63 | 1.9 | F / F |
| U24.5 | analog_5V | C37 | 2.0 | B / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 4.1 |
| 2 | Vref_2_arduino | R100.1 | 4.2 |
| 3 | Vref_3_arduino | R77.1 | 5.9 |
| 4 | IREF1 | U106.6 | 17.2 |
| 5 | IREF2 | R30.1 | 10.8 |
| 6 | IREF3 | R57.1 | 6.4 |
| 7 | SCL | U26.5 | 23.5 |
| 8 | SDA | U26.6 | 20.3 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 24.3 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 34, tallest 1.75 mm (limit 2.7)
