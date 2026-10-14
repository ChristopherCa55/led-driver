# Every change, with x / y and layer (review fixes, 2026-10-11; updated 2026-10-13)

KiCad positions are in mm as KiCad shows them (y grows downwards). LTspice positions are LTspice schematic units. Board lists come from comparing the board files themselves (tools/pcb_diff.py).

## Step 1: LTspice documentation (D5, D7, D8)

**Status:** in the copy (LTspice/BOOST.asc 1f008632 -> cc28c9fa)

LTspice (`LTspice/BOOST.asc`):

| change |
|---|
| directive at (-6376, -4352): .ic now V(Out)=0 V(Out-)=1 (removed V(C10)=0 V(C5)=0 V(C2)=0) |
| comment deleted at (-6416, -3488): ;.ic V(Vout_1)=30 V(Vout_2)=38 V(Vout_3)=30 |
| directive added at (-5520, -4024): .model aliases 1N4148W / B5819W / BAV21W / BAT54WS = D |
| note added at (1921, -6383): one-hot from U18: picks Verr1/2/3 |
| note added at (1216, -5927): Q3 resets it: counts Q0-Q2 only / 5V by net name (SpiceModel) |
| note added at (3488, -6096): latch: set- low turns M1 on / RESET- low turns it off |
| note added at (4336, -6600): rc: slow turn on / diode: fast off |
| note added at (-1974, -8524): DT = VCCI: / no dead time |
| note added at (-3584, -6222): ch B unused |
| note added at (672, -3440): same as channel 1 |
| note added at (4176, -3536): same as channel 1 |
| value set at (-2128, -5472): D21 = BAV21W (was the default D) |
| value set at (-1616, -5808): D13 = B5819W (was the default D) |
| value set at (-1616, -5648): D22 = B5819W (was the default D) |
| value set at (-2000, -3296): D26 = BAT54WS (was the default D) |
| value set at (-1616, -8768): D11 = B5819W (was the default D) |
| value set at (-1616, -8608): D2 = B5819W (was the default D) |
| value set at (-2128, -8432): D10 = BAV21W (was the default D) |
| value set at (-1616, -7296): D14 = B5819W (was the default D) |
| value set at (-1616, -7136): D8 = B5819W (was the default D) |
| value set at (-2128, -6960): D9 = BAV21W (was the default D) |
| value set at (1728, -3168): D25 = BAT54WS (was the default D) |
| value set at (5232, -3264): D23 = BAT54WS (was the default D) |
| value set at (432, -6336): D3 = 1N4148W (was the default D) |
| value set at (480, -6304): D4 = 1N4148W (was the default D) |
| value set at (3408, -6352): D6 = 1N4148W (was the default D) |
| value set at (4288, -6768): D20 = 1N4148W (was the default D) |
| value set at (4288, -6432): D7 = 1N4148W (was the default D) |
| value set at (4288, -6128): D5 = 1N4148W (was the default D) |
| value set at (4032, -7600): D24 = 1N4148W (was the default D) |
| value set at (4064, -7408): D1 = 1N4148W (was the default D) |
| value set at (4064, -7296): D15 = 1N4148W (was the default D) |
| value set at (4128, -7040): D27 = 1N4148W (was the default D) |

## Step 2: KiCad documentation: diode part names, Vin+/Vin-/Out1+... labels, title block, U26D (D7, D8)

**Status:** in the copy (label pictures approved by the user 2026-10-12)

KiCad schematics and footprint values:

| file | item | at | change |
|---|---|---|---|
| main page | D27 | (720.09, 90.17) | Value "D" -> "1N4148W" |
| main page | D22 | (265.43, 227.33) | Value "D" -> "B5819W" |
| main page | D1 | (715.01, 60.96) | Value "D" -> "1N4148W" |
| main page | D24 | (712.47, 45.72) | Value "D" -> "1N4148W" |
| main page | D8 | (264.16, 132.08) | Value "D" -> "B5819W" |
| main page | D10 | (223.52, 55.88) | Value "D" -> "BAV21W" |
| main page | D13 | (265.43, 214.63) | Value "D" -> "B5819W" |
| main page | D14 | (264.16, 119.38) | Value "D" -> "B5819W" |
| main page | J7 | (612.14, 457.2) | Value "Conn_01x01_Pin" -> "Out2-" |
| main page | J8 | (612.14, 452.12) | Value "Conn_01x01_Pin" -> "Out2+" |
| main page | D3 | (403.86, 146.05) | Value "D" -> "1N4148W" |
| main page | D7 | (732.79, 138.43) | Value "D" -> "1N4148W" |
| main page | J3 | (298.45, 398.78) | Value "Conn_01x01_Pin" -> "Out1+" |
| main page | D15 | (715.01, 69.85) | Value "D" -> "1N4148W" |
| main page | J5 | (660.4, 281.94) | Value "Conn_01x01_Pin" -> "Out3+" |
| main page | D9 | (223.52, 146.05) | Value "D" -> "BAV21W" |
| main page | D23 | (798.83, 308.61) | Value "D" -> "BAT54WS" |
| main page | J6 | (660.4, 287.02) | Value "Conn_01x01_Pin" -> "Out3-" |
| main page | J4 | (298.45, 403.86) | Value "Conn_01x01_Pin" -> "Out1-" |
| main page | D5 | (732.79, 162.56) | Value "D" -> "1N4148W" |
| main page | D21 | (224.79, 241.3) | Value "D" -> "BAV21W" |
| main page | D11 | (264.16, 29.21) | Value "D" -> "B5819W" |
| main page | D6 | (662.94, 144.78) | Value "D" -> "1N4148W" |
| main page | J2 | (30.48, 191.77) | Value "Conn_01x01_Pin" -> "Vin-" |
| main page | U26 unit 4 | (129.54, 440.69) -> (142.24, 440.69) | moved one slot right; clear of U106D; value placed under it at (142.24, 448.31) |
| main page | D26 | (436.88, 425.45) | Value "D" -> "BAT54WS" |
| main page | D4 | (407.67, 148.59) | Value "D" -> "1N4148W" |
| main page | J1 | (31.75, 168.91) | Value "Conn_01x01_Pin" -> "Vin+" |
| main page | D20 | (732.79, 111.76) | Value "D" -> "1N4148W" |
| main page | D25 | (750.57, 478.79) | Value "D" -> "BAT54WS" |
| main page | D2 | (264.16, 41.91) | Value "D" -> "B5819W" |
| main page | no-connect flag | (121.92, 438.15) -> (134.62, 438.15) | no-connect flag moved with U26D |
| main page | no-connect flag | (121.92, 440.69) -> (134.62, 440.69) | no-connect flag moved with U26D |
| main page | no-connect flag | (121.92, 443.23) -> (134.62, 443.23) | no-connect flag moved with U26D |
| main page | title block | (sheet corner) | added: (title "BOOST LED driver - main schematic (both boards)") / (rev "RC2") / (comment 1 "Parts also drawn on the board schematics BOOST_power_RC2 / BOOST_control_RC2") |
| power board sheet | D22 | (265.43, 227.33) | Value "D" -> "B5819W" |
| power board sheet | D8 | (264.16, 132.08) | Value "D" -> "B5819W" |
| power board sheet | D10 | (223.52, 55.88) | Value "D" -> "BAV21W" |
| power board sheet | D13 | (265.43, 214.63) | Value "D" -> "B5819W" |
| power board sheet | D14 | (264.16, 119.38) | Value "D" -> "B5819W" |
| power board sheet | J7 | (499.11, 146.05) | Value "Conn_01x01_Pin" -> "Out2-" |
| power board sheet | J8 | (359.41, 175.26) | Value "Conn_01x01_Pin" -> "Out2+" |
| power board sheet | J3 | (360.68, 83.82) | Value "Conn_01x01_Pin" -> "Out1+" |
| power board sheet | J5 | (360.68, 269.24) | Value "Conn_01x01_Pin" -> "Out3+" |
| power board sheet | D9 | (223.52, 146.05) | Value "D" -> "BAV21W" |
| power board sheet | J6 | (500.38, 238.76) | Value "Conn_01x01_Pin" -> "Out3-" |
| power board sheet | J4 | (494.03, 71.12) | Value "Conn_01x01_Pin" -> "Out1-" |
| power board sheet | D21 | (224.79, 241.3) | Value "D" -> "BAV21W" |
| power board sheet | D11 | (264.16, 29.21) | Value "D" -> "B5819W" |
| power board sheet | J2 | (30.48, 191.77) | Value "Conn_01x01_Pin" -> "Vin-" |
| power board sheet | J1 | (31.75, 168.91) | Value "Conn_01x01_Pin" -> "Vin+" |
| power board sheet | D2 | (264.16, 41.91) | Value "D" -> "B5819W" |
| card sheet | D27 | (90.17, 344.17) | Value "D" -> "1N4148W" |
| card sheet | D1 | (85.09, 314.96) | Value "D" -> "1N4148W" |
| card sheet | D24 | (82.55, 299.72) | Value "D" -> "1N4148W" |
| card sheet | D3 | (26.67, 67.31) | Value "D" -> "1N4148W" |
| card sheet | D7 | (363.22, 54.61) | Value "D" -> "1N4148W" |
| card sheet | D15 | (85.09, 323.85) | Value "D" -> "1N4148W" |
| card sheet | D23 | (513.08, 222.25) | Value "D" -> "BAT54WS" |
| card sheet | D5 | (363.22, 78.74) | Value "D" -> "1N4148W" |
| card sheet | D6 | (293.37, 60.96) | Value "D" -> "1N4148W" |
| card sheet | D26 | (144.78, 204.47) | Value "D" -> "BAT54WS" |
| card sheet | D4 | (30.48, 69.85) | Value "D" -> "1N4148W" |
| card sheet | D20 | (363.22, 27.94) | Value "D" -> "1N4148W" |
| card sheet | D25 | (365.76, 232.41) | Value "D" -> "BAT54WS" |
| BOOST_power_RC2 (PCB) | D2 | footprint at (74.7629, 57.341), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D8 | footprint at (51.5215, 62.3376), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D11 | footprint at (80.2161, 69.5357), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D13 | footprint at (89.4234, 93.3766), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D14 | footprint at (35.1068, 65.5772), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D22 | footprint at (82.115, 89.9889), B.Cu | Value "D" -> "B5819W" |
| BOOST_power_RC2 (PCB) | D9 | footprint at (81.4924, 76.7564), B.Cu | Value "D" -> "BAV21W" |
| BOOST_power_RC2 (PCB) | D10 | footprint at (89.3136, 66.2458), B.Cu | Value "D" -> "BAV21W" |
| BOOST_power_RC2 (PCB) | D21 | footprint at (94.4546, 66.4421), B.Cu | Value "D" -> "BAV21W" |
| BOOST_power_RC2 (PCB) | J1 | footprint at (98.6162, 83.1393) | Value "Conn_01x01_Pin" -> "Vin+"; label "Vin+" on **F.SilkS** at (93.206, 80.6), 90 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J2 | footprint at (98.5035, 73.9328) | Value "Conn_01x01_Pin" -> "Vin-"; label "Vin-" on **F.SilkS** at (93.206, 73.933), 90 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J3 | footprint at (44.416, 112.935) | Value "Conn_01x01_Pin" -> "Out1+"; label "Out1+" on **F.SilkS** at (44.416, 109.69), 0 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J4 | footprint at (50.916, 112.935) | Value "Conn_01x01_Pin" -> "Out1-"; label "Out1-" on **F.SilkS** at (50.916, 109.69), 0 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J8 | footprint at (32.8047, 111.568) | Value "Conn_01x01_Pin" -> "Out2+"; label "Out2+" on **F.SilkS** at (32.805, 108.323), 0 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J7 | footprint at (39.3047, 111.568) | Value "Conn_01x01_Pin" -> "Out2-"; label "Out2-" on **F.SilkS** at (39.305, 108.323), 0 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J5 | footprint at (62.5742, 113.185) | Value "Conn_01x01_Pin" -> "Out3+"; label "Out3+" on **F.SilkS** at (59.6, 113.185), 90 deg; reference text moved to F.Fab |
| BOOST_power_RC2 (PCB) | J6 | footprint at (56.0742, 113.185) | Value "Conn_01x01_Pin" -> "Out3-"; label "Out3-" on **F.SilkS** at (56.074, 109.94), 0 deg; reference text moved to F.Fab |
| BOOST_control_RC2 (PCB) | D1 | footprint at (55.1541, 77.564), F.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D3 | footprint at (49.7123, 108.904), B.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D4 | footprint at (48.5667, 80.358), F.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D5 | footprint at (66.9943, 112.739), B.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D6 | footprint at (60.715, 71.8115), B.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D7 | footprint at (82.6461, 71.4746), B.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D15 | footprint at (53.988, 73.3501), B.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D20 | footprint at (87.829, 91.101), F.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D24 | footprint at (53.998, 72.6722), F.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D27 | footprint at (52.7606, 77.5629), F.Cu | Value "D" -> "1N4148W" |
| BOOST_control_RC2 (PCB) | D23 | footprint at (51.4339, 89.2436), B.Cu | Value "D" -> "BAT54WS" |
| BOOST_control_RC2 (PCB) | D25 | footprint at (68.3678, 71.3031), F.Cu | Value "D" -> "BAT54WS" |
| BOOST_control_RC2 (PCB) | D26 | footprint at (75.9169, 96.5466), B.Cu | Value "D" -> "BAT54WS" |

## Step 3: 12V route, Option A (X1)

**Status:** in the copy

#### Power board

Tracks removed (22):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| In4.Cu | 12V | 0.5 | (71.95, 46.95) | (72.75, 46.15) |
| In4.Cu | 12V | 0.5 | (71.95, 51.85) | (71.95, 46.95) |
| In4.Cu | 12V | 0.5 | (72.75, 46.15) | (75.15, 46.15) |
| In4.Cu | 12V | 0.5 | (74.35, 54.25) | (71.95, 51.85) |
| In4.Cu | 12V | 0.5 | (74.35, 54.35) | (74.35, 54.25) |
| B.Cu | 12V | 0.5 | (74.55, 43.35) | (74.55, 43.55) |
| B.Cu | 12V | 0.5 | (74.55, 43.55) | (74.65, 43.65) |
| B.Cu | 12V | 0.5 | (74.65, 43.65) | (74.65, 43.75) |
| B.Cu | 12V | 0.5 | (74.65, 43.75) | (74.75, 43.85) |
| F.Cu | 12V | 0.5 | (74.75, 43.85) | (74.85, 43.85) |
| F.Cu | 12V | 0.5 | (74.85, 43.85) | (74.85, 45.45) |
| F.Cu | 12V | 0.5 | (74.85, 45.45) | (75.35, 45.95) |
| In4.Cu | 12V | 0.5 | (75.15, 46.15) | (75.35, 45.95) |
| In4.Cu | 12V | 0.5 | (75.25, 55.25) | (74.35, 54.35) |
| In4.Cu | 12V | 0.5 | (75.95, 55.25) | (75.25, 55.25) |
| In4.Cu | 12V | 0.5 | (76, 55.2) | (75.95, 55.25) |
| In4.Cu | 12V | 0.5 | (79, 55.2) | (76, 55.2) |
| In4.Cu | 12V | 0.5 | (81.2, 48.6) | (81.2, 53) |
| In4.Cu | 12V | 0.5 | (81.2, 53) | (79, 55.2) |
| In4.Cu | 12V | 0.5 | (81.45, 48.35) | (81.2, 48.6) |
| In4.Cu | 12V | 0.5 | (81.9, 48.35) | (81.45, 48.35) |
| In4.Cu | 12V | 0.5 | (82, 48.25) | (81.9, 48.35) |

Tracks added (5):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| B.Cu | 12V | 0.4 | (80.85, 42) | (81.45, 41.4) |
| B.Cu | 12V | 0.4 | (80.85, 46.6) | (80.85, 42) |
| B.Cu | 12V | 0.4 | (81.45, 41.4) | (81.45, 39.75) |
| B.Cu | 12V | 0.4 | (82, 46.6) | (80.85, 46.6) |
| B.Cu | 12V | 0.4 | (82, 48.25) | (82, 46.6) |

Vias removed (7), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| 12V | (74.75, 43.85) | 0.6 / 0.3 |
| 12V | (75.35, 45.95) | 0.6 / 0.3 |
| Vin | (80.85, 42.7) | 0.8 / 0.4 |
| Vin | (80.85, 43.7) | 0.8 / 0.4 |
| Vin | (80.85, 44.7) | 0.8 / 0.4 |
| Vin | (80.85, 45.7) | 0.8 / 0.4 |
| 12V | (82, 48.25) | 0.6 / 0.3 |



## Step 4: ch2 loop vias (D10 option a)

**Status:** in the copy

#### Power board

Vias added (2), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| GND | (33.24, 67.25) | 0.8 / 0.4 |
| GND | (34.44, 67.85) | 0.8 / 0.4 |



## Step 6: three more Vin vias in R1's funnel (X1 follow-up)

**Status:** in the copy

#### Power board

Vias added (3), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| Vin | (72.08, 41.55) | 0.8 / 0.4 |
| Vin | (72.08, 42.4) | 0.8 / 0.4 |
| Vin | (72.08, 43.25) | 0.8 / 0.4 |



- The first try (0.9/0.5 mm at x 72.25, work/step06) broke clearance to U19 pins 15/16 and was dropped.

## Step 5: I2C pull-ups R106 / R107 as 0603 near J9 (D1, the user's 2026-10-12 retry) and R99 / R102 1k (D2)

**Status:** in the copy (placement approved by the user 2026-10-13)

LTspice (`LTspice/BOOST.asc`):

| change |
|---|
| value changed at (-6128, -6416): R102 10k -> 1k |
| value changed at (-6000, -6416): R99 10k -> 1k |
| part added at (-6448, -6672): R106 4.7k, pins (-6432, -6656) to 5V and (-6432, -6576) to SCL; wires (-6432, -6688)-(-6432, -6656) and (-6432, -6576)-(-6432, -6544); flags 5V at (-6432, -6688), SCL at (-6432, -6544) |
| part added at (-6320, -6672): R107 4.7k, pins (-6304, -6656) to 5V and (-6304, -6576) to SDA; wires (-6304, -6688)-(-6304, -6656) and (-6304, -6576)-(-6304, -6544); flags 5V at (-6304, -6688), SDA at (-6304, -6544) |
| note added at (-6480, -6480): I2C pull-ups (U26 has none) |
| directive at (-6376, -4088): .options gmin=100f reltol=0.001 -> .options gmin=100f reltol=0.001 solver=alt (needed once R106 / R107 are in: the normal solver stops at 0.3216 ms) |

KiCad schematics and footprint values:

| file | item | at | change |
|---|---|---|---|
| main page | R99 |  | Value "10k" -> "1k" |
| main page | R102 |  | Value "10k" -> "1k" |
| main page | R106 4.7k | (15.24, 240.03) | added; pins (16.51, 241.3) / (16.51, 247.65); wires (16.51, 238.76)-(16.51, 241.3), (16.51, 247.65)-(16.51, 250.19); global labels 5V at (16.51, 238.76), SCL at (16.51, 250.19) |
| main page | R107 4.7k | (24.13, 240.03) | added; pins (25.4, 241.3) / (25.4, 247.65); wires (25.4, 238.76)-(25.4, 241.3), (25.4, 247.65)-(25.4, 250.19); global labels 5V at (25.4, 238.76), SDA at (25.4, 250.19) |
| main page | note | (15.24, 257.81) | added: "I2C pull-ups / (U26 has none)" |
| card sheet | R99 |  | Value "10k" -> "1k" |
| card sheet | R102 |  | Value "10k" -> "1k" |
| card sheet | R106 4.7k | (140.97, 353.06) | added; pins (142.24, 354.33) / (142.24, 360.68); wires (142.24, 351.79)-(142.24, 354.33), (142.24, 360.68)-(142.24, 363.22); global labels 5V at (142.24, 351.79), SCL at (142.24, 363.22) |
| card sheet | R107 4.7k | (149.86, 353.06) | added; pins (151.13, 354.33) / (151.13, 360.68); wires (151.13, 351.79)-(151.13, 354.33), (151.13, 360.68)-(151.13, 363.22); global labels 5V at (151.13, 351.79), SDA at (151.13, 363.22) |
| card sheet | note | (140.97, 370.84) | added: "I2C pull-ups / (U26 has none)" |

#### Control card board

Tracks removed (12):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| F.Cu | 5V | 0.4 | (55.825, 94.225) | (56.025, 94.225) |
| F.Cu | 5V | 0.4 | (56.025, 94.225) | (56.175, 94.075) |
| F.Cu | 5V | 0.4 | (56.175, 94.075) | (57.375, 94.075) |
| F.Cu | 5V | 0.4 | (57.375, 94.075) | (57.775, 93.675) |
| F.Cu | 5V | 0.4 | (57.775, 93.625) | (57.825, 93.575) |
| F.Cu | 5V | 0.4 | (57.775, 93.675) | (57.775, 93.625) |
| F.Cu | 5V | 0.4 | (57.825, 93.525) | (57.875, 93.475) |
| F.Cu | 5V | 0.4 | (57.825, 93.575) | (57.825, 93.525) |
| F.Cu | 5V | 0.4 | (57.875, 93.425) | (57.925, 93.375) |
| F.Cu | 5V | 0.4 | (57.875, 93.475) | (57.875, 93.425) |
| F.Cu | 5V | 0.4 | (57.925, 93.175) | (58.425, 92.675) |
| F.Cu | 5V | 0.4 | (57.925, 93.375) | (57.925, 93.175) |

Tracks added (8):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| F.Cu | 5V | 0.3 | (53.35, 101.45) | (54.2, 101.45) |
| F.Cu | 5V | 0.3 | (55.5, 94.4) | (56.1, 94.4) |
| In2.Cu | SDA | 0.2 | (55.6, 100.7) | (57.25, 100.7) |
| F.Cu | SDA | 0.2 | (55.6, 101.075) | (55.6, 100.7) |
| F.Cu | SDA | 0.2 | (55.975, 101.45) | (55.6, 101.075) |
| In2.Cu | SDA | 0.2 | (57.25, 100.7) | (59.1, 98.85) |
| F.Cu | SCL | 0.2 | (57.975, 94) | (58, 94.45) |
| F.Cu | SCL | 0.2 | (58, 94.45) | (58, 95.25) |

Vias removed (1), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| 5V | (55.825, 94.225) | 0.5 / 0.3 |

Vias added (3), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| 5V | (53.35, 101.45) | 0.5 / 0.3 |
| 5V | (55.5, 94.4) | 0.5 / 0.3 |
| SDA | (55.6, 100.7) | 0.5 / 0.3 |

Footprints (5):

| ref | side | at (x, y) | change |
|---|---|---|---|
| H3 | F.Cu | (54.4567, 106.464) | Reference text: at (0 -4.15 0) F.SilkS -> at (0 -3.8 0) F.SilkS |
| R102 | F.Cu | (52.4011, 84.9123) | value 10k -> 1k |
| R106 | F.Cu | (57.15, 94) | added |
| R107 | F.Cu | (55.15, 101.45) | added |
| R99 | B.Cu | (53.2174, 90.6941) | value 10k -> 1k |



- J9 footprint (board and KiCad/BOOST.pretty): F.CrtYd now 0.15 mm from the pad rows (local y -1.15 .. 3.69; the tie-slot block x -4.5 .. -1.2 kept full height); B.CrtYd unchanged. F.SilkS labels I2 and SCL moved from local y -1.825 to -3.1 (board y 94.075 -> 92.80), x unchanged (I2 56.145, SCL 58.385).
- H3: Reference text on F.SilkS moved from local (0, -4.15) to (0, -3.8), board y 102.31 -> 102.66.
- Card BOM: R99 / R102 move from the 10k line (C25804) to the existing 1k line (C21190); R106 / R107 join the existing 4.7k 0603 line (C23162). CPL: R106 57.1500 / -94.0000 Top 0; R107 55.1500 / -101.4500 Top 0.

## Step 7: two GND stitching vias in the one-via In1 piece (C1)

**Status:** in the copy

#### Control card board

Vias added (2), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| GND | (72.34, 84.823) | 0.5 / 0.3 |
| GND | (74.34, 85.673) | 0.5 / 0.3 |



## Step 8: Net-(U101A-Y) from In1 to In2 (C1)

**Status:** in the copy

#### Control card board

Tracks removed (14):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.625, 79.125) | (50.625, 79.675) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.625, 79.675) | (50.925, 79.975) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.675, 78.975) | (50.675, 79.075) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.675, 79.075) | (50.625, 79.125) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.725, 76.475) | (50.725, 78.925) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.725, 78.925) | (50.675, 78.975) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.925, 79.975) | (50.925, 83.225) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (50.925, 83.225) | (51.625, 83.925) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.625, 83.925) | (51.625, 83.975) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.625, 83.975) | (51.675, 84.025) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.675, 75.175) | (51.675, 75.525) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.675, 75.525) | (50.725, 76.475) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.675, 84.025) | (51.675, 84.475) |
| In1.Cu | Net-(U101A-Y) | 0.2 | (51.675, 84.475) | (55.125, 87.925) |

Tracks added (5):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| In2.Cu | Net-(U101A-Y) | 0.2 | (51.675, 75.175) | (52.25, 75.75) |
| In2.Cu | Net-(U101A-Y) | 0.2 | (52.25, 75.75) | (52.25, 82.85) |
| In2.Cu | Net-(U101A-Y) | 0.2 | (52.25, 82.85) | (54.95, 85.55) |
| In2.Cu | Net-(U101A-Y) | 0.2 | (54.95, 85.55) | (54.95, 87.7) |
| In2.Cu | Net-(U101A-Y) | 0.2 | (54.95, 87.7) | (55.125, 87.925) |



## Step 9: Net-(D5--) re-routed so it no longer cuts the card's In4 GND in two (the user, 2026-10-12: longest GND splitters)

**Status:** in the copy (approved by the user 2026-10-13)

#### Control card board

Tracks removed (62):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| In4.Cu | Net-(D5--) | 0.2 | (70.125, 113.825) | (69.575, 114.375) |
| In4.Cu | Net-(D5--) | 0.2 | (70.725, 113.825) | (70.125, 113.825) |
| In4.Cu | Net-(D5--) | 0.2 | (70.775, 113.775) | (70.725, 113.825) |
| In4.Cu | Net-(D5--) | 0.2 | (72.425, 113.775) | (70.775, 113.775) |
| In4.Cu | Net-(D5--) | 0.2 | (72.475, 113.825) | (72.425, 113.775) |
| In4.Cu | Net-(D5--) | 0.2 | (73.425, 113.825) | (72.475, 113.825) |
| In4.Cu | Net-(D5--) | 0.2 | (73.475, 113.775) | (73.425, 113.825) |
| In4.Cu | Net-(D5--) | 0.2 | (73.675, 113.775) | (73.475, 113.775) |
| In4.Cu | Net-(D5--) | 0.2 | (73.725, 113.725) | (73.675, 113.775) |
| In4.Cu | Net-(D5--) | 0.2 | (73.875, 113.725) | (73.725, 113.725) |
| In4.Cu | Net-(D5--) | 0.2 | (73.925, 113.675) | (73.875, 113.725) |
| In4.Cu | Net-(D5--) | 0.2 | (74.025, 113.675) | (73.925, 113.675) |
| In4.Cu | Net-(D5--) | 0.2 | (74.075, 113.625) | (74.025, 113.675) |
| In4.Cu | Net-(D5--) | 0.2 | (74.125, 113.625) | (74.075, 113.625) |
| In4.Cu | Net-(D5--) | 0.2 | (74.175, 113.575) | (74.125, 113.625) |
| In4.Cu | Net-(D5--) | 0.2 | (74.225, 113.575) | (74.175, 113.575) |
| In4.Cu | Net-(D5--) | 0.2 | (74.275, 113.525) | (74.225, 113.575) |
| In4.Cu | Net-(D5--) | 0.2 | (74.325, 113.525) | (74.275, 113.525) |
| In4.Cu | Net-(D5--) | 0.2 | (74.375, 113.475) | (74.325, 113.525) |
| In4.Cu | Net-(D5--) | 0.2 | (74.425, 113.475) | (74.375, 113.475) |
| In4.Cu | Net-(D5--) | 0.2 | (74.525, 113.375) | (74.425, 113.475) |
| In4.Cu | Net-(D5--) | 0.2 | (74.575, 113.375) | (74.525, 113.375) |
| In4.Cu | Net-(D5--) | 0.2 | (74.675, 113.275) | (74.575, 113.375) |
| In4.Cu | Net-(D5--) | 0.2 | (74.725, 113.275) | (74.675, 113.275) |
| In4.Cu | Net-(D5--) | 0.2 | (74.975, 113.025) | (74.725, 113.275) |
| In4.Cu | Net-(D5--) | 0.2 | (75.025, 113.025) | (74.975, 113.025) |
| In4.Cu | Net-(D5--) | 0.2 | (75.125, 112.925) | (75.025, 113.025) |
| In4.Cu | Net-(D5--) | 0.2 | (75.175, 112.925) | (75.125, 112.925) |
| In4.Cu | Net-(D5--) | 0.2 | (75.275, 112.825) | (75.175, 112.925) |
| In4.Cu | Net-(D5--) | 0.2 | (75.325, 112.825) | (75.275, 112.825) |
| In4.Cu | Net-(D5--) | 0.2 | (78.475, 109.675) | (75.325, 112.825) |
| In4.Cu | Net-(D5--) | 0.2 | (78.675, 109.675) | (78.475, 109.675) |
| In4.Cu | Net-(D5--) | 0.2 | (78.725, 109.625) | (78.675, 109.675) |
| In4.Cu | Net-(D5--) | 0.2 | (78.775, 109.625) | (78.725, 109.625) |
| In4.Cu | Net-(D5--) | 0.2 | (79.325, 108.975) | (79.325, 109.075) |
| In4.Cu | Net-(D5--) | 0.2 | (79.325, 109.075) | (78.775, 109.625) |
| In4.Cu | Net-(D5--) | 0.2 | (79.375, 108.875) | (79.375, 108.925) |
| In4.Cu | Net-(D5--) | 0.2 | (79.375, 108.925) | (79.325, 108.975) |
| In4.Cu | Net-(D5--) | 0.2 | (79.425, 108.775) | (79.425, 108.825) |
| In4.Cu | Net-(D5--) | 0.2 | (79.425, 108.825) | (79.375, 108.875) |
| In4.Cu | Net-(D5--) | 0.2 | (79.475, 108.675) | (79.475, 108.725) |
| In4.Cu | Net-(D5--) | 0.2 | (79.475, 108.725) | (79.425, 108.775) |
| In4.Cu | Net-(D5--) | 0.2 | (79.575, 108.575) | (79.475, 108.675) |
| In4.Cu | Net-(D5--) | 0.2 | (79.625, 108.525) | (79.625, 108.575) |
| In4.Cu | Net-(D5--) | 0.2 | (79.625, 108.575) | (79.575, 108.575) |
| In4.Cu | Net-(D5--) | 0.2 | (79.725, 108.475) | (79.725, 108.525) |
| In4.Cu | Net-(D5--) | 0.2 | (79.725, 108.525) | (79.625, 108.525) |
| In4.Cu | Net-(D5--) | 0.2 | (79.775, 108.475) | (79.725, 108.475) |
| In4.Cu | Net-(D5--) | 0.2 | (80.025, 107.925) | (80.025, 108.225) |
| In4.Cu | Net-(D5--) | 0.2 | (80.025, 108.225) | (79.775, 108.475) |
| In4.Cu | Net-(D5--) | 0.2 | (80.775, 106.175) | (80.775, 107.175) |
| In4.Cu | Net-(D5--) | 0.2 | (80.775, 107.175) | (80.025, 107.925) |
| In4.Cu | Net-(D5--) | 0.2 | (80.825, 106.075) | (80.825, 106.125) |
| In4.Cu | Net-(D5--) | 0.2 | (80.825, 106.125) | (80.775, 106.175) |
| In4.Cu | Net-(D5--) | 0.2 | (80.875, 105.975) | (80.875, 106.025) |
| In4.Cu | Net-(D5--) | 0.2 | (80.875, 106.025) | (80.825, 106.075) |
| In4.Cu | Net-(D5--) | 0.2 | (82.125, 95.575) | (82.125, 102.275) |
| In4.Cu | Net-(D5--) | 0.2 | (82.125, 102.275) | (82.575, 102.725) |
| In4.Cu | Net-(D5--) | 0.2 | (82.575, 102.725) | (82.575, 102.775) |
| In4.Cu | Net-(D5--) | 0.2 | (82.575, 102.775) | (82.625, 102.825) |
| In4.Cu | Net-(D5--) | 0.2 | (82.625, 102.825) | (82.625, 104.225) |
| In4.Cu | Net-(D5--) | 0.2 | (82.625, 104.225) | (80.875, 105.975) |

Tracks added (38):

| layer | net | width | from (x, y) | to (x, y) |
|---|---|---|---|---|
| In2.Cu | Net-(D5--) | 0.2 | (70.2, 113.8) | (69.575, 114.375) |
| In2.Cu | Net-(D5--) | 0.2 | (70.85, 113.8) | (70.2, 113.8) |
| In2.Cu | Net-(D5--) | 0.2 | (72.4, 112.25) | (70.85, 113.8) |
| In2.Cu | Net-(D5--) | 0.2 | (73.6, 112.25) | (72.4, 112.25) |
| In2.Cu | Net-(D5--) | 0.2 | (74.05, 111.8) | (73.6, 112.25) |
| In2.Cu | Net-(D5--) | 0.2 | (74.15, 111.8) | (74.05, 111.8) |
| In2.Cu | Net-(D5--) | 0.2 | (74.5, 111.45) | (74.15, 111.8) |
| In2.Cu | Net-(D5--) | 0.2 | (79.45, 111.45) | (74.5, 111.45) |
| In2.Cu | Net-(D5--) | 0.2 | (80.05, 112.05) | (79.45, 111.45) |
| In4.Cu | Net-(D5--) | 0.2 | (80.2, 99.65) | (80.2, 103.25) |
| In4.Cu | Net-(D5--) | 0.2 | (80.2, 103.25) | (80.3, 103.35) |
| In4.Cu | Net-(D5--) | 0.2 | (80.3, 103.35) | (80.3, 104.1) |
| In4.Cu | Net-(D5--) | 0.2 | (80.3, 104.1) | (81.3, 105.1) |
| In4.Cu | Net-(D5--) | 0.2 | (80.35, 98.55) | (80.35, 99.5) |
| In4.Cu | Net-(D5--) | 0.2 | (80.35, 99.5) | (80.2, 99.65) |
| In2.Cu | Net-(D5--) | 0.2 | (80.55, 112.05) | (80.05, 112.05) |
| In4.Cu | Net-(D5--) | 0.2 | (80.95, 96.8) | (80.95, 97.95) |
| In4.Cu | Net-(D5--) | 0.2 | (80.95, 97.95) | (80.35, 98.55) |
| In2.Cu | Net-(D5--) | 0.2 | (81, 111.6) | (80.55, 112.05) |
| In4.Cu | Net-(D5--) | 0.2 | (81.3, 105.1) | (81.3, 105.45) |
| In4.Cu | Net-(D5--) | 0.2 | (81.3, 105.45) | (81.95, 106.1) |
| In4.Cu | Net-(D5--) | 0.2 | (81.6, 108.9) | (81.6, 110.15) |
| In4.Cu | Net-(D5--) | 0.2 | (81.6, 110.15) | (81.7, 110.25) |
| In4.Cu | Net-(D5--) | 0.2 | (81.7, 108.5) | (81.7, 108.8) |
| In4.Cu | Net-(D5--) | 0.2 | (81.7, 108.8) | (81.6, 108.9) |
| In4.Cu | Net-(D5--) | 0.2 | (81.7, 110.25) | (81.7, 110.6) |
| In4.Cu | Net-(D5--) | 0.2 | (81.7, 110.6) | (81.85, 110.75) |
| In4.Cu | Net-(D5--) | 0.2 | (81.8, 95.95) | (80.95, 96.8) |
| In4.Cu | Net-(D5--) | 0.2 | (81.8, 108.15) | (81.8, 108.4) |
| In4.Cu | Net-(D5--) | 0.2 | (81.8, 108.4) | (81.7, 108.5) |
| In4.Cu | Net-(D5--) | 0.2 | (81.85, 110.75) | (81.85, 111.05) |
| In4.Cu | Net-(D5--) | 0.2 | (81.85, 111.05) | (82.15, 111.35) |
| In4.Cu | Net-(D5--) | 0.2 | (81.95, 106.1) | (81.95, 108) |
| In4.Cu | Net-(D5--) | 0.2 | (81.95, 108) | (81.8, 108.15) |
| In4.Cu | Net-(D5--) | 0.2 | (82.125, 95.575) | (81.8, 95.95) |
| In4.Cu | Net-(D5--) | 0.2 | (82.15, 111.35) | (82.15, 111.45) |
| In4.Cu | Net-(D5--) | 0.2 | (82.15, 111.45) | (82.3, 111.6) |
| In2.Cu | Net-(D5--) | 0.2 | (82.3, 111.6) | (81, 111.6) |

Vias added (1), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| Net-(D5--) | (82.3, 111.6) | 0.5 / 0.3 |



- 0err_hi and SDA were tried too and left where they are: every alternative split more plane (work/CARD_SPLITTERS.md).

## Step 10: two Vout_3 loop vias at C4.1 (the user, 2026-10-13: Vout_3 only, not ch3 / ch1)

**Status:** in the copy

#### Power board

Vias added (2), through F.Cu-B.Cu:

| net | x, y | size / drill |
|---|---|---|
| Vout_3 | (92.38, 85.8) | 0.8 / 0.4 |
| Vout_3 | (92.38, 87) | 0.8 / 0.4 |



