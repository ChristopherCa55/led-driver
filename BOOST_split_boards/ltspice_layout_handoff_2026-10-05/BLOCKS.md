# Blocks

There are 14 framed blocks plus the `[SETUP]` directives area. Every one of the 302 simulated elements belongs to
exactly one block; this was checked by script against the original netlist.

Bypass caps are listed in §4. Each sits in the block of the IC it serves. `blocks.json` is the machine-readable
version, read by the checker.

## 1. Block table

| ID | Block (board) | Purpose | Members (LTspice names) | Inputs | Outputs |
|---|---|---|---|---|---|
| **PWR** | Power path (power) | Battery-fed boost stage and the three switched outputs, the high-current loop | **SIM chain:** SIM_BATTERY, SIM_CABLE_RESISTANCE, SIM_CABLE_INDUCTANCE (renamed from SIM_VBATT/SIM_RCABLE/SIM_LCABLE). **Input caps:** C69 C40 C85. **Sense resistor:** R1 (4-terminal). **Inductor:** L1. **Boost switch and LX clamp:** M1, D19, R14. **ch1:** M7 M2, D28, C86 C70 C88 C1 C72. **ch2:** M6 M3, D29, C87 C71 C78 C73 C3. **ch3:** M5 M4, D30, C74 C75 C77 C4 C76 | GATE_M1…M7 (direct wires from GATEDRV below) | Vin (wired down into SUP); ISNS_P/N (wired up to ISNS); Vout_1–3 (→ CREGx, EAx); m2/m3/m4_source (↔ GATEDRV) |
| **ISNS** | Input-current sense (power) | Battery-current amplifier on R1's Kelvin taps | U25, C20 | ISNS_P, ISNS_N (direct wires from R1, directly below) | `Current` → CONTROL |
| **SUP** | Voltage regulators (power) | 12 V, 5 V logic, 5 V analog | U16 + C79 C84 (in) + C30 (out); U17 + C80 C82 + C7 C39; U1 + C81 C83 + C55 C56 C21; C6 C25 (12 V rail, provisional) | Vin | 12V, 5V, analog_5V rails |
| **GATEDRV** | Gate drivers (power) | Isolated drivers for M1 and the three FET pairs | **M1 driver:** U19 R15 R104 R62 + C31 C48. **ch1:** U15 R13 D11 R60 D2 R75 R76 D10 R21 C18 C51 + C62. **ch2:** U10 R23 D14 R70 D8 R61 R49 D9 R48 C16 C50 + C90. **ch3:** U8 R47 D13 R59 D22 R73 R74 D21 R72 C60 C61 + C89 | M1_ON, M2_ON, out_2_on, out_3_on, ena_out_1–3 (from CONTROL); 12V, 5V | GATE wires straight up into PWR; source ties |
| **CREG1–3** | LED current regulator (power), ×3 | Linear sink that sets each LED string's current | **ch1:** SIM_LED1, M10 R52 U11 R56 C45 + C33. **ch2:** SIM_LED2, M9 R53 U12 R50 C44 + C34. **ch3:** SIM_LED3, M8 R7 U6 R22 C41 + C35 | Vout_x (label); IREFx_input (direct wire from REFx) | Outputx_drain (direct wire to REFx) |
| **REF1–3** | LED-current setpoint and headroom servo (card), ×3 | Digipot sets the current; the sample-and-hold and integrator raise `.1Vref_x` until the sink has headroom | **ch1:** SIM_IREF1, R29 R54 C100 U26A, R94 R95 U106C, U24 C67 R98 R96 R97 C68, D26 + C32. **Also in REF1 only:** U26E R99 R102 R103 + C26, and C23 (the 4066's bypass). **ch2:** SIM_IREF2, R30 R55 C101 U26B, R25 R36 U106B, U23 C64 R93 R91 R92 C65, D25 + C38. **ch3:** SIM_IREF3, R57 R58 C102 U26C, R87 R88 U106A, U22 C49 R90 R44 R89 C59, D23 + C63 | Outputx_drain; IREFx (its SIM source is inside); POTx_CODE is a `.param`, shown as a note | **.1Vref_x** → EAx; **IREFx_input** → CREGx |
| **EA1–3** | Output-voltage error amp (card), ×3 | Vout_x → Verrx: divider, inverting amp vs `.1Vref_x`, filter | **ch1:** SIM_VREF1, R101 C103, R6 C46, R9 R8, R2 R3 U3, R27 R28 C13 + C66. **ch2:** SIM_VREF2, R100 C93, R33 C43, R35 R34, R31 R32 U7, R37 R38 C11 + C36. **ch3:** SIM_VREF3, R77 C47, R41 C42, R43 R42, R39 R40 U13, R45 R46 C10 + C37 | Vout_x (label); .1Vref_x (direct wire from REFx) | Verrx (direct wire into CONTROL) |
| **CONTROL** | All control logic (card) | Error select, comparators, fault latch, low-error timeout, channel sequencer, channel enables, M1 inhibit | **Error select and comparators:** U28 U2 U4 U5 R11 R16 R17 R18 R19 R20 U104E. **Timeout:** U14 Q1 R65 R66 R67 R68 R69 R71 C14 C15 D3 D4. **Latch and sequencer:** U101A–D R4 D6 U18. **Fan-out ch1:** U102A U104B U102B R80 C17 D20 R81 U105A. **Fan-out ch2:** U102D U104C U102C R78 C9 D7 R79 U104F. **Fan-out ch3:** U103B U104D U103A R63 C8 D5 R64 U105B. **M1 inhibit:** U21 R82–R86 D24 D1 D15 R51 C19 R26 D27 R105 SIM_ARD_INH U104A. **Bypass:** C12 C24 C28 C29 C53 C96 C98 at their ICs; the logic-supply bank (§4) | Verr1–3 (direct wires), Current, 12V | ena_out_1–3, M2_ON, out_2_on, out_3_on, M1_ON (grouped at the right edge) → GATEDRV |
| **SETUP** | Simulation setup (no parts) | All 18 directive texts and the user's notes, grouped by purpose | — | — | — |

## 2. Boundary decisions

| Part(s) | Placed in | Why |
|---|---|---|
| C79–C84 (on Vin) | SUP, not PWR | They are the regulators' input caps; the PCB puts them at U16/U17/U1 |
| R6, C46, R101, C103 | EAx | They form the reference input of the error amp, their only load. `.1Vref_x` is the clean interface to REFx |
| C45/C44/C41 | CREGx | The filter on the sink op-amp's + input |
| D19, R14 | PWR | The LX clamp and bleed, on the high-current node |
| R4, D6 | CONTROL (latch) | They form the latch's set input |
| R75/R76, R61/R49, R73/R74 (gate pull-downs) | GATEDRV | Part of each gate network. Draw them at the edge facing the FETs |
| U26E and its resistors | REF1 | The digipot's shared I²C control; one note says it serves all three pots |
| C23 (4066 bypass) | REF1, at U106C's VDD | LTspice draws a VDD pin on each 4066 switch; one cap serves the package |
| SIM_* sources | at the input they drive | The user's choice: stimulus sits where it acts, in a dashed "simulation only" frame |

**The user's "3 inputs, 1 output" for REF, corrected:** the digipot's wiper (`IREFx_input`) feeds the sink op-amp in
CREGx, not the sample-and-hold. So the block has two outputs, `.1Vref_x` and `IREFx_input`. Both leave by short
direct wires to the adjacent blocks.

## 3. Pre-approved fallback for CONTROL

**When to use it:** if CONTROL cannot be drawn as one readable block, meaning it fails H3, H4 or H8–H10, or T5–T8, or
the captures are crowded.

**What it is:** replace CONTROL with two framed blocks, and run the checker with `--split`:

- **CONTROL_A**, *error detection, sequencing and M1 inhibit*: everything except the three fan-out rows.
- **CONTROL_B**, *channel enables*: the three fan-out rows.

They meet at VerrGT0, Out-, OUT_1_ENA, OUT_2_ENA, OUT_3_ENA and M1_ON. Tell the user you used the fallback.

## 4. Bypass capacitors: owners

Generated by `tools/bypass_match.py` from the PCB pad positions in `BOOST_stuff/KiCad`. For each rail, it uses
minimum-cost one-to-one matching of cap to IC, then gives leftover caps to their nearest IC.

- **"logic-supply group":** LTspice draws the 74HC00/74HC14 gates (U101–U105) without supply pins, and U18 is powered
  by the net name. These caps go together as one small wired bank in CONTROL, with a note listing U101–U105 and U18.
  This mirrors the separate power units in the KiCad symbols.
- **Ambiguous owners** need the user's confirmation at check-in 1. Until then, draw them where the table says.

| Cap | Rail | Owner | Pad distance (mm) | Drawn at | Block | Note |
|---|---|---|---|---|---|---|
| C6 | 12V | U16 | 18.04 | U16.OUT | SUP | **ambiguous**: sits 2.6 mm from C25 and 15–18 mm from U16/D21/D10; a 12 V rail cap |
| C7 | 5V | U17 | – | U17 OUT | SUP | by design (bulk) |
| C12 | 5V | U14 | 1.77 | U14.V+ | CONTROL | |
| C20 | analog_5V | U25 | 2.8 | U25.VS | ISNS | |
| C21 | analog_5V | U1 | 2.44 | U1.OUT | SUP | |
| C22 | 5V | U101 | 4.39 | logic-supply group | CONTROL | **ambiguous** (U104 at 3.03 mm) |
| C23 | 5V | U106 | 1.94 | U106C.VDD | REF1 | |
| C24 | 5V | U5 | 1.77 | U5.V+ | CONTROL | |
| C25 | 12V | U16 | 15.58 | U16.OUT | SUP | **ambiguous**, see C6 |
| C26 | 5V | U26 | 1.8 | U26E.VDD | REF1 | |
| C28 | 5V | U2 | 1.75 | U2.V+ | CONTROL | |
| C29 | 5V | U21 | 5.54 | U21.V+ | CONTROL | |
| C30 | 12V | U16 | – | U16 OUT | SUP | by design (bulk) |
| C31 | 12V | U19 | 2.81 | U19.VDDA | GATEDRV | |
| C32 | analog_5V | U24 | 2.2 | U24.V+ | REF1 | |
| C33 | analog_5V | U11 | 2.4 | U11.V+ | CREG1 | |
| C34 | analog_5V | U12 | 2.4 | U12.V+ | CREG2 | |
| C35 | analog_5V | U6 | 2.68 | U6.V+ | CREG3 | |
| C36 | analog_5V | U7 | 4.34 | U7.V+ | EA2 | **ambiguous** (U13 at 4.9 mm) |
| C37 | analog_5V | U13 | 5.96 | U13.V+ | EA3 | **ambiguous** (U24 at 1.98 mm, but U24 already has C32) |
| C38 | analog_5V | U23 | 3.68 | U23.V+ | REF2 | |
| C39 | 5V | U17 | – | U17 OUT | SUP | by design |
| C48 | 5V | U19 | 2.18 | U19.VCCI | GATEDRV | |
| C52 | 5V | U18 | 2.06 | logic-supply group | CONTROL | |
| C53 | 5V | U21 | 1.76 | U21.V+ | CONTROL | |
| C54 | 5V | U103 | 5.93 | logic-supply group | CONTROL | |
| C55, C56 | analog_5V | U1 | – | U1 OUT | SUP | by design |
| C57 | 5V | U105 | 1.89 | logic-supply group | CONTROL | |
| C58 | 5V | U104 | 1.9 | logic-supply group | CONTROL | |
| C62 | 5V | U15 | 2.9 | U15.VCCI | GATEDRV | |
| C63 | analog_5V | U22 | 1.62 | U22.V+ | REF3 | |
| C66 | analog_5V | U3 | 1.47 | U3.V+ | EA1 | |
| C89 | 5V | U8 | 2.35 | U8.VCCI | GATEDRV | |
| C90 | 5V | U10 | 2.12 | U10.VCCI | GATEDRV | |
| C91 | 5V | U102 | 3.3 | logic-supply group | CONTROL | |
| C92, C94, C99 | 5V | U105 | 2.45 / 5.75 / 5.59 | logic-supply group | CONTROL | |
| C95, C104 | 5V | U103 | 2.64 / 1.6 | logic-supply group | CONTROL | |
| C96 | 5V | U28 | 6.16 | U28.VDD | CONTROL | **ambiguous** (U2 at 3.78 mm, but U2 already has C28) |
| C97 | 5V | U104 | 5.17 | logic-supply group | CONTROL | |
| C98 | 5V | U4 | 1.62 | U4.V+ | CONTROL | |

## 5. Repeated circuits

These were verified identical by script from the original netlist, apart from the listed differences.

| Copies | ch1 / ch2 / ch3 anchor | Topology | Real differences (note them at the part) |
|---|---|---|---|
| PWR switch columns | M7 / M6 / M5 | identical, values identical | — |
| Channel switch drivers | U15 / U10 / U8 | identical | R23, R49 (ch2) and R59, R74 (ch3) are netlisted with reversed pin order: rotate 180° so they look the same. Net names M2_ON vs out_2_on/out_3_on |
| CREG | SIM_LED1 / SIM_LED2 / SIM_LED3 | identical | LED model RED / GREEN / BLUE (simulation only) |
| REF | SIM_IREF1 / 2 / 3 | identical | IREFn_DUTY in the SIM source; POTn_CODE (86 / 103 / 103) on the pot. REF1 also holds U26E, C26, C23 |
| EA | SIM_VREF1 / 2 / 3 | identical, values identical | SIM_VREF pulse width 816 µs / 1.224 ms / 1.224 ms (simulation only) |
| CONTROL fan-out rows | U102A / U102D / U103B | identical | U103B's AND inputs are in the opposite order |

**Interface nets between blocks** (direction for the port flags): see `interfaces` in blocks.json. For example,
Vout_1 is driven by PWR, so it is `Out` in PWR and `In` in CREG1 and EA1.
