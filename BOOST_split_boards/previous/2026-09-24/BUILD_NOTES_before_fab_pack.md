# BOOST power board: build notes

Started 2026-09-16. Collects assembly instructions decided during the re-design; sources are
`replace_2026-09-14/tools/replace_notes.md` (rounds 3-4) and the user's instructions of 2026-09-16.
Part numbers marked "not chosen" still need a decision.

## Board

- 8 layers, 1.6 mm nominal (JLCPCB stackup 1 oz outer / 1 oz inner, 1.654 mm copper + dielectric), written into
  the board file.
- Every power pad is joined to its copper solidly, with no thermal reliefs: the TO-220 pins, J1-J8, capacitor
  pads and shunts. This is deliberate, because spokes would carry up to 15.8 A.

## Soldering the power parts

- Preheat the board from below to about 100-120 C with hot air before soldering the TO-220 pins or the J1/J2
  cable joints.
- Use an 80-100 W iron with a 3 mm or larger chisel tip, and flux.
- Hold each FET body flat against the board while soldering its pins. On M1, M8, M9 and M10 the M2.5 screw and
  its spacer can act as the jig.
- Removing a FET later will be difficult: the pins are joined solidly to two GND planes and several pours.

## Stack in the case (floor upward)

Case floor tapped per `case_drilling_2026-09-15/` rev B (M3: 7.0 mm full thread; M2.5: 6.0 mm full thread;
10 mm floor, blind holes).

1. Thermal pad under every FET: Parker Chomerics THERM-A-GAP G579, 0.050 in (1.27 mm), sheet
   61-05-0909-G579, cut about 10 x 16 mm per FET, with a 3.0 mm hole at M1/M8/M9/M10. Compressed to about
   0.93 mm (27 % nominal) at a 5.50 mm board height.
2. FET tab screws (M1, M8, M9, M10): M2.5 x 12 pan head, through the board, a 2.25 mm insulating gap spacer
   (part not chosen), the Aavid/Boyd 7721-7PPSG shoulder washer in the tab hole, the tab and the pad, into the
   floor. **Tighten only until the head seats.** The column rests on the compliant pad, so torque pulls the
   board down and crushes those four pads.
3. Board standoffs at H5-H8, **hand-tight only, no tools on nylon threads**:
   Essentra HTSN-M3-5-3 nylon male-male stud (5 mm body, 6 mm hex) into the floor until its hex seats;
   one TR Fastenings TR NWE-34815-M3 nylon washer (0.50 mm); the power board; Essentra HNSM3-20-5.5-1
   nylon female-female (20 mm) screwed onto the stud to clamp the board; three TR NWE-34815-M3 washers
   (1.50 mm); the control card; Wurth Elektronik 97790803211 (WA-SCRW M3 x 8 nylon 66 pan head, UL94 V-0, head
   2.1 +/- 0.2 mm, head dia 5.5 +/- 0.3 mm, rated -30 to +85 C; accepted by the user 2026-09-17). Card gap 21.50 mm
   (ESQ/TSW header seats at 21.21). Head top 32.30 mm, 0.70 mm under the lid (33.00); 0.50 mm at the maximum head
   height, about 0.2 mm with the washers (+0.05 each) and a card 10 % thick as well.
4. J9 (Arduino) is 11 soldered wires, 26-28 AWG stranded: in from the card's underside, soldered on the top side
   and trimmed flush (fillet under the 1.75 mm top-side limit), run along the underside to the west edge; one
   cable tie through the two slots beside the pads, head on the underside. The plug goes on the Nano's pins.
   Before fitting the board, measure stud hex + washer on all four: target 5.50 +/- 0.10 mm (Essentra
   publishes no length tolerance).

### J9 wire table (control card)

Each pad is named on both sides of the card: odd pins in the row above the pads, even pins in the row below.
Pin 1 has a square pad and a silk dot beside it. The pads are staggered 1.27 mm apart, so check each wire against its
label before soldering. Colours accepted by the user 2026-09-23 (pin 9 red for 12 V).

| Pin | Label | Net | Function | Wire colour |
|---|---|---|---|---|
| 1 | V1 | Vref_1_arduino | PWM brightness, channel 1 | brown |
| 2 | V2 | Vref_2_arduino | PWM brightness, channel 2 | orange |
| 3 | V3 | Vref_3_arduino | PWM brightness, channel 3 | yellow |
| 4 | I1 | IREF1 | channel 1 enable | green |
| 5 | I2 | IREF2 | channel 2 enable | blue |
| 6 | I3 | IREF3 | channel 3 enable | violet |
| 7 | SCL | SCL | I2C clock to U26 | white |
| 8 | SDA | SDA | I2C data | grey |
| 9 | 12V | 12V | card 12 V out, to power the Arduino end (schematic rev5, 2026-09-23; see below) | red |
| 10 | GND | GND | common ground (pad has thermal-relief spokes for hand soldering) | black |
| 11 | INH | ARD_M1_INHIBIT | drive high to hold M1 off | pink (or white with a red marker) |

**Pin 9 is 12 V** (from J11.19, the power board's 12 V LM2940 rail; schematic rev5). It powers the Arduino end:
- It feeds a **12 V -> 5 V buck module at the Arduino**, and that buck makes the Arduino's 5 V. **Do not wire it to the
  Nano's VIN pin.**
- Fit an **inline 200 mA PTC fuse at the card end** of the pin-9 wire.
- **Twist the 12 V (pin 9, red) and GND (pin 10, black) wires together** along the run.
- Why: the card's own 5 V comes from a 100 mA L78L05 (SOT-89) dropping 14 V. It cannot also carry an Arduino plus a
  CAN transceiver (about 50 mA average, 120 mA peak) without overheating. The 12 V LM2940 (TO-263, 1 A) carries about
  20 mA today, and adding 120 mA costs it about 0.24 W (user, 2026-09-23).

## Order

1. Solder the power board, FETs included (above).
2. Lay the thermal pads on the floor, fit the board, and fit the M1/M8/M9/M10 tab screws and H5-H8 stand-offs.
   **M8's and M9's screws go in before the control card**: they sit under it.
3. Fit the control card on the header and stand-offs.
4. Battery cable: strain relief on the case near the penetrator (boss or P-clip), not on the board.
