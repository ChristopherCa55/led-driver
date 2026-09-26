## Legality (placer model; DRC on the saved board is separate)

- Courtyard overlaps: 4
  - H1 x U106: 0.044 mm2
  - H3 x U104: 0.912 mm2
  - J11 x U104: 0.756 mm2
  - U106 x U28: 0.001 mm2
- Outside the card: none
- Inside a mounting-hole keep-out: U105 (0.02 mm), U106 (0.01 mm), U104 (0.21 mm), U7 (0.01 mm)
- SMD parts: 59 on the top (F), 105 on the underside (B)

## Analog constraints

| Item | Value |
|---|---|
| Current: J11.23 -> U2.4 | 20.6 mm straight, F side |
| Current: J11.23 -> U5.3 | 17.6 mm straight, F side |
| Current net half-perimeter | 26.1 mm |
| Current pins to 74HC14 U104 | 6.9 mm (J11.23 - U104.14) |
| Current pins to 74HC14 U105 | 17.7 mm (U5.3 - U105.1) |
| Current pins to M1_ON | 8.4 mm (U5.3 - J11.3) |
| Current pins to SCL | 12.4 mm (J11.23 - J9.7) |
| Current pins to SDA | 10.2 mm (J11.23 - J9.8) |
| D27.1 -> U104.1 | 0.4 mm (limit 2.5) |
| R105.1 -> D27.2 | 1.6 mm (limit 2.0) |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {U104, U105, U26, net:SCL, net:SDA} | 6.9 mm (J11.23 - U104.14), minimum 10.0 |
| apart: {net:Current, net:V_err, net:Net-(U2-In+)} vs {net:M1_ON} | 7.5 mm (U2.3 - J11.3), minimum 8.0 |
| C49 restricted to B | on B |
| C64 restricted to B | on B |
| C67 restricted to B | on B |
| M1_INHIBIT node spread (D1.1, D15.1, D24.1, D27.1, R26.1, U104.1) | 19.6 mm half-perimeter |

## Decoupling (IC supply pin -> nearest capacitor on the rail, pad centre to pad centre)

| Pin | Rail | Nearest cap | mm | Side (IC / cap) |
|---|---|---|---|---|
| U2.5 | 5V | C29 | 1.8 | F / B |
| U4.5 | 5V | C26 | 0.5 | F / B |
| U5.5 | 5V | C91 | 2.3 | F / F |
| U14.5 | 5V | C57 | 1.8 | F / B |
| U18.16 | 5V | C95 | 1.7 | F / B |
| U21.5 | 5V | C53 | 1.8 | F / F |
| U26.17 | 5V | C104 | 1.9 | F / B |
| U28.16 | 5V | C58 | 1.7 | F / F |
| U101.14 | 5V | C12 | 0.6 | F / B |
| U102.14 | 5V | C92 | 1.3 | B / F |
| U103.14 | 5V | C28 | 2.2 | F / F |
| U104.14 | 5V | C52 | 1.7 | F / B |
| U105.14 | 5V | C54 | 0.4 | B / F |
| U106.14 | 5V | C58 | 3.3 | F / F |
| U3.5 | analog_5V | C32 | 2.0 | B / B |
| U7.5 | analog_5V | C37 | 1.6 | B / B |
| U13.5 | analog_5V | C66 | 1.8 | F / F |
| U22.5 | analog_5V | C63 | 1.8 | F / F |
| U23.5 | analog_5V | C38 | 1.9 | F / F |
| U24.5 | analog_5V | C32 | 1.7 | F / B |

## J9 (wire pads) to first load

| J9 pin | Net | Nearest other pin | mm |
|---|---|---|---|
| 1 | Vref_1_arduino | R101.1 | 21.4 |
| 2 | Vref_2_arduino | R100.1 | 6.7 |
| 3 | Vref_3_arduino | R77.1 | 6.9 |
| 4 | IREF1 | U106.6 | 18.2 |
| 5 | IREF2 | R30.1 | 10.0 |
| 6 | IREF3 | R57.1 | 9.0 |
| 7 | SCL | U26.5 | 24.2 |
| 8 | SDA | U26.6 | 22.4 |
| 9 | 5V | (plane) | - |
| 10 | GND | (plane) | - |
| 11 | ARD_M1_INHIBIT | R105.1 | 10.5 |

## Heights (package maxima; card top limit 1.75 mm, underside over a can 2.7 mm)

- Tallest on the top: 1.75 mm (U101); tallest on the underside: 1.80 mm (C49)
- Over the top limit: none
- Underside parts over an output can: 43, tallest 1.80 mm (limit 2.7)
