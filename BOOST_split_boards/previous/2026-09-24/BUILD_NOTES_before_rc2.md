# BOOST: build notes (assembly pack)

Started 2026-09-16, updated 2026-09-24 for the fabrication and assembly package (`fab_2026-09-24/`). Collects the
assembly instructions decided during the re-design. Sources: `replace_2026-09-14/tools/replace_notes.md` (rounds
3-4), the user's instructions of 2026-09-16, -23 and -24, and the 3D assembly model in `assembly_3d_2026-09-24/`.
Part numbers marked "not chosen" still need a decision. The previous version is in
`previous/2026-09-24/BUILD_NOTES_before_fab_pack.md`.

Pack contents: this file, the case drilling drawing rev B (`case_drilling_2026-09-15/case_floor_drilling.svg` and
`.html`, positions re-checked against the release-candidate board on 2026-09-24: all eight match to 0.01 mm), and
the BOM / sourcing table (`fab_2026-09-24/bom/SOURCING_TABLE.md`).

## What you fit yourself

JLCPCB fits every other part. These are DNP in the JLC BOM and pick-and-place files; their pads, holes and silk stay
on the boards.

| Ref | Part | Why |
|---|---|---|
| M1-M10 | HuaYi HYG180N10, TO-220 (power board, underside) | you own ten |
| L1 | Codaca CSCF3218-6R8MC (power board, top) | you own it |
| J10 | Samtec ESQ-115-44-G-D socket (power board, top) | not stocked at LCSC (Samtec / Digi-Key / Mouser) |
| J11 | Samtec TSW-115-07-G-D header (card, underside) | LCSC lists it with 0 in stock |
| R1 | Bourns CSS4J-4026K-2L00F (power board, top), **if** it is still out of stock when you order | see SOURCING_TABLE |

The 680 uF and 220 uF cans are stock-limited at LCSC (10 and 19 on 2026-09-24: 3 and 2 power boards). Beyond that,
you fit them by hand, or JLC pre-orders them.

## Board

- 8 layers, 1.6 mm nominal (JLCPCB stackup 1 oz outer / 1 oz inner, 1.654 mm copper + dielectric), written into
  the board file. ENIG finish; every via epoxy filled and copper capped (fab drawing note 1).
- Every power pad is joined to its copper solidly, with no thermal reliefs: the TO-220 pins, L1, J1-J8, capacitor
  pads and shunts. This is deliberate, because spokes would carry up to 15.8 A.

## MOSFET orientation (M1-M10): do not fit one backwards

- **Pinout: G-D-S = pins 1-2-3** (HuaYi HYG180N10 datasheet: gate, drain, source). The tab is the drain. The
  footprint's pads 1 / 2 / 3 carry each FET's gate / drain / source nets (checked on the board 2026-09-24), and
  **pad 1 is the square pad**.
- The HuaYi datasheet draws an exposed metal tab but does not state what the tab connects to (replace_notes,
  2026-09-14). Before fitting, check one part with a meter: tab to the middle pin should read a short. The
  insulation (compliant pad, shoulder washers, gap spacers) assumes the tab carries the drain voltage.
- **Body flat against the board underside, metal tab facing away from the board, toward the case.** The marked face
  of the part is then against the board.
- Pin 1 (gate) is the left lead when you read the part's marking with the leads pointing down. It must go into the
  square pad. If the tab faces the board, the part is upside down: gate and source swap, and it will fail.
- **Underside (B.SilkS), the side you place from:** each FET's body-and-tab outline, with the tab end drawn dashed
  and the word **TAB** inside it.
- **Top side (F.SilkS), the side you solder from, with the pins coming through:**

  | FET | Marking beside its pins on the top side |
  |---|---|
  | M2, M3, M8, M10 | **G D S** beside pads 1-2-3, and a pin-1 dot |
  | M1, M6, M7 | **G** beside pad 1 and a pin-1 dot (no room for D and S between the neighbouring parts) |
  | M4 | **G** off the corner of pad 1, and a pin-1 dot |
  | M5 | **G** at the pad-1 end of the row and a pin-1 dot; also **G** on the underside beside pad 1 |
  | M9 | **G** and **S** at the two ends of the row and a pin-1 dot; also **G** on the underside |

  Text 1.0 mm, 0.15 mm stroke, nowhere closer than 0.15 mm to a pad. M4/M5 and M6/M3 each share one straight row of
  six pads: read each letter against the pad beside it.
- Before soldering each FET, check from the top that the lead in the **G** pad is the gate.
- The power board change was silk only (v16 -> v17: DRC before / after in
  `route_2026-09-16/work/silk/v16_before_newrules.drc.rpt` and `v17_after.drc.rpt`, renders in
  `route_2026-09-16/renders_v17/`).

## Soldering the hand-fitted parts

- **Preheat the board from below to about 100-120 C with hot air** before soldering the TO-220 pins, **L1**, the
  J10 / J11 GND pins, or the J1/J2 cable joints. All of them join solid planes and pours.
- Use an **80-100 W iron with a 3 mm or larger chisel tip**, and flux.
- **L1 (CSCF3218, 32 x 22.5 x 19 mm, 6.8 uH) is a large SMD part with two J-lead terminals** on 8 x 6 mm pads
  (LX and rsense_lo; the third pad under the body is mechanical). Treat it like the TO-220 pins: preheat, the
  high-power iron, and plenty of flux. Solder it first, while nothing else tall is in the way, and check that the
  body sits flat before the second terminal sets.
- Hold each FET body flat against the board while soldering its pins. On M1, M8, M9 and M10 the M2.5 screw and
  its spacer can act as the jig. Trim the leads that come through the top side.
- Removing a FET later will be difficult: the pins are joined solidly to two GND planes and several pours.
- **J10 (power board top) and J11 (card underside):** 1.05 mm holes. Solder J11 from the card's top side. Its
  tails stand about 0.9 mm above the card, under the 1.75 mm top-side limit. The mated pair seats at 21.21 mm; the
  standoffs hold 21.50, so the posts insert 5.55 mm (Samtec: 3.68-6.35).

## Stack in the case (floor upward)

Case floor tapped per `case_drilling_2026-09-15/` rev B (M3: 7.0 mm full thread; M2.5: 6.0 mm full thread;
10 mm floor, blind holes).

1. Thermal pad under every FET: Parker Chomerics THERM-A-GAP G579, 0.050 in (1.27 mm), sheet
   61-05-0909-G579, cut about 10 x 16 mm per FET, with a 3.0 mm hole at M1/M8/M9/M10. Compressed to about
   0.93 mm (27 % nominal) at a 5.50 mm board height. Do not cut them larger: in the 3D model, 10 x 16 pads
   centred on the bodies leave 0.54 mm between M6's and M8's, 0.56 mm to M9's and 0.86 mm between M1's and M7's.
2. FET tab screws (M1, M8, M9, M10): M2.5 x 12 pan head, through the board, a 2.25 mm insulating gap spacer
   (part not chosen), the Aavid/Boyd 7721-7PPSG shoulder washer in the tab hole, the tab and the pad, into the
   floor. **Tighten only until the head seats.** The column rests on the compliant pad, so torque pulls the
   board down and crushes those four pads.
3. Board standoffs at H5-H8, **hand-tight only, no tools on nylon threads**:
   Essentra HTSN-M3-5-3 nylon male-male stud (5 mm body, 6 mm hex) into the floor until its hex seats;
   one TR Fastenings TR NWE-34815-M3 nylon washer (0.50 mm; 7.0 mm OD, 3.2 mm ID); the power board; Essentra
   HNSM3-20-5.5-1 nylon female-female (20 mm) screwed onto the stud to clamp the board; three TR NWE-34815-M3
   washers (1.50 mm); the control card; Wurth Elektronik 97790803211 (WA-SCRW M3 x 8 nylon 66 pan head, UL94 V-0,
   head 2.1 +/- 0.2 mm, head dia 5.5 +/- 0.3 mm, rated -30 to +85 C; accepted by the user 2026-09-17). Card gap
   21.50 mm (ESQ/TSW header seats at 21.21). Head top 32.30 mm, 0.70 mm under the lid (33.00); 0.50 mm at the
   maximum head height, about 0.2 mm with the washers (+0.05 each; the distributor lists them at 0.51 mm) and a card
   10 % thick as well.
   Before fitting the board, measure stud hex + washer on all four: target 5.50 +/- 0.10 mm (Essentra publishes no
   length tolerance).
4. **Screwdriver access:** M8's tab screw is under the control card, so fit it before the card. M1, M9 and M10 stay
   reachable afterwards. The 3D model puts M9's screwdriver path 3.2 mm clear of the card edge, which corrects the
   earlier note that M9 was under the card. Nothing on the boards taller than 3 mm comes within 4.0 mm of any tab
   screw; the closest are cans C69 (M1) and C71 (M9), 0.7 mm outside that radius.

## Clearances measured in the 3D model (2026-09-24)

Full table in `assembly_3d_2026-09-24/CLEARANCES.md`. The items under 1 mm:

- Lid to the card screw heads 0.65 mm, and to the SOIC-16 packages on the card top (U18, U28) 0.98 mm. The model uses
  the board files' 1.654 mm thickness, 0.054 mm more than the nominal 1.6; nominal gives 0.70 and 1.03.
- The standoff washers under the card come within 0.40-0.73 mm of card parts D6 (H1), R94 (H2), D3 (H3) and R84 (H4).
  They clear, but centre the washers on the screw.
- The J9 wire bundle passes 0.39 mm from M10's screwdriver path (see the J9 routing note below).

Every can clears the 2 mm vent rule at its datasheet maximum height (closest: 2.80 mm under U104 / U106 on the card).

## J9 (Arduino) wires

J9 is 11 soldered wires, 26-28 AWG stranded:
- in from the card's underside, soldered on the top side and trimmed flush (fillet under the 1.75 mm top-side
  limit);
- run along the underside to the west edge;
- one cable tie through the two slots beside the pads, head on the underside;
- the plug goes on the Nano's pins.

**Route the bundle clear of M10's tab screw.** Where the wires leave the card's west edge (board y 92.8-101.6), they
head straight over M10's screw (board (35.5, 98.6), case (57.5, 70.6)). Fit M10's screw first. Take the bundle
north or south of that point, so the screw stays reachable.

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
- On the card, 12 V reaches J9.9 by a long route (88 mm, 0.3 mm track): about 0.1 ohm, 12-20 mV at 200 mA. Accepted
  2026-09-24.

## Order

1. JLCPCB assembles both boards, both sides, except the parts listed under "What you fit yourself".
2. Power board, by hand, board preheated: L1 first, then R1 if you are fitting it, then J10, then the ten FETs,
   checking each one's orientation.
3. Control card: J11 from the underside, soldered on top; then the J9 wires, the PTC and the tie.
4. Lay the thermal pads on the floor, fit the board, and fit the M1/M8/M9/M10 tab screws and H5-H8 stand-offs.
   **M8's screw goes in before the control card**, because it sits under the card. Fit M10's screw before the J9
   bundle is dressed.
5. Fit the control card on the header and stand-offs, then the washers and screws, hand-tight.
6. Battery cable: strain relief on the case near the penetrator (boss or P-clip), not on the board.
