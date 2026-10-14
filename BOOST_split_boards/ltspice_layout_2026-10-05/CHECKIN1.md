# Check-in 1: pilot (PWR, ISNS, CREG1, REF1, EA1), 2026-10-06

**File:** `work/BOOST.asc`, sha256 `9e58f66a35a6f4123fb31631b732aca6955ad8881ca155b1c1020197ea77c148`.
**Built by:** `tools/build_pilot.py`, using `tools/channel.py`, `tools/layout_lib.py` and `tools/ascmodel.py`.
**Source:** the frozen original `../ltspice_layout_handoff_2026-10-05/reference/LTspice_original/BOOST.asc`.

## What was drawn
- **Pilot position:** the pilot blocks sit above the rest of the sheet (y < −1400). Everything not in the pilot is
  where it was.
  - Wires that served only the moved parts were deleted, and their dangling ends trimmed.
  - Every net cut by the move still carries its name in the old area, so no new flags were needed there.
- **Gap below PWR:** 704 units are left free under PWR for GATEDRV, so that the gate wires can later run straight
  down.
- **PWR** is one wired drawing, flowing left to right:
  - SIM battery → cable R → cable L (dashed SIM frame, with the note "simulation only - not on the PCB");
  - Vin (a flag at the top of the pre-charge riser, right after the cable) → C69, C40, C85 → R1 → rsense_lo → L1 →
    LX;
  - LX → M1, D19, R14;
  - three identical switch columns, each: M7/M2 back to back with both gates pointing down → Vout bus → 5 output
    caps → D28 dropping from the pre-charge rail.
  - One ground bus with one GND symbol, at the battery.
  - The D28-D30 note (verbatim) sits above the diodes.
- **ISNS** sits above R1:
  - U25 unrotated, as in the original. Rotated, its own pin text was even worse.
  - The Kelvin pair rises from R1, spreads apart, and enters IN+/IN- from the left.
  - REF1's ground sits between the two sense wires; GND and REF2 are tied to one ground.
- **CREG1:**
  - Vout_1 (In port) → SIM_LED1 (SIM frame) → drain node → M10 → R52 → GND.
  - U11 is mirrored, so that its inputs face REF1. The sense feedback reaches In− from above, so there are no
    crossings.
  - R56 runs from OUT to the gate; C33 sits on U11's V+ rail; C45 on In+.
- **REF1:**
  - R94/R95 → U106C → integrator U24, with C67 ∥ R98 and its In+ reference divider R96/R97/C68 → SRV1 → D26 →
    .1Vref_1 → EA1.
  - The setpoint chain: SIM_IREF1 → R29 → R54/C100 → pot U26A → IREF1_input → CREG1.
  - C23 and U26E (with C26, R99, R102, R103) sit below the pot, outside the area that has to match channels 2 and 3.
    U26A's A terminal is wired to U26E's ground (the same package).
  - Notes explain C23 and U26E.
- **EA1:**
  - Vout_1 (In) → R9 → .1Vout_1 (R8) → R2 → N022 → U3 In−, with the R3 feedback.
  - .1Vref_1 from REF1 → C46, R6 → U3 In+.
  - SIM_VREF1 → R101 → Vref_1 (C103).
  - OUT → Voltage_err_1 → R27 → Verr1 (R28, C13) → port.

## ELECTRICAL: `tools/ltspice_equiv.py work/BOOST.asc` (performed; output in `checks/equiv.txt`)
| Check | Result | Details |
|---|---|---|
| E1 | PASS | 302 → 302 elements; 152 nets compared, 0 differing. The new name Vbattery is on a previously auto-named net (was P001). The 3 approved renames were applied. |
| E2 | PASS | U18 SpiceModel is "5V 0"; the net 5V is unchanged; labels 4..10 are kept. |
| E3 | PASS | 18 directive texts and 6 original comments, all verbatim. The new comments are block titles and notes. |
| E4 | PASS | V(0A_hi, LX, Out, Out-, SRV1-3, Vref_1-3), I(L1, D19) and the 6 params all resolve as before. V(C10/C5/C2) name no node in the original either. |
| E5 | PASS | All .asy/.lib files are byte-identical. |

## VISUAL, automatic: `asc_layout_check.py --blocks PWR,ISNS,CREG1,REF1,EA1` (performed; output in `checks/layout_pilot.txt`)
- **Rules:** H2, H3, H3b, H4, H5, H6, H7, H8, H9 (estimated), H10, H11 and H12 all PASS.
  - H10 here covers the three PWR switch columns. The CREG, REF and EA copies need channels 2 and 3.
- **Traces:**

| Trace | Label jumps / budget | Result |
|---|---|---|
| T1 | 0 / 0 | PASS |
| T2 | 1 / 1 (Vout_1 into EA1) | PASS |
| T3 | 1 / 1 (Vout_1 into CREG1) | PASS |
| T4 | 0 / 0 | PASS |
| T10 | 0 / 0 | PASS |
| T5–T9 | – | Not evaluated: every step outside the pilot blocks is skipped, so their 0s mean nothing yet. |

- **Crossings per block:** PWR 16, ISNS 0, CREG1 0, REF1 0, EA1 0. The PWR crossings are all single, clean crossings:

| Count | Crossing | Why it stays |
|---|---|---|
| 10 | Gate and source wires cross the ground bus | GATE_M1, plus 3 per switch column. These become the direct wires into GATEDRV below. |
| 2 | The Vout_1 and Vout_2 exits cross the ground bus | Vout_3 does not, because the bus ends before it. |
| 2 | The Kelvin pair crosses the pre-charge rail | The rail must start at Vin, left of R1, and ISNS sits directly above R1. |
| 2 | The D28 and D29 drops cross the LX bus | Inherent with three side-by-side columns. |

## VISUAL, LTspice captures (performed; `captures/pilot/`)
- **How they were taken:**
  - The tool's normal views: `overview.png`, `ISNS.png`, `CREG1_*.png`, `REF1_*.png`, `EA1_*.png`.
  - The tool's PWR tiles (`PWR_1..5.png`) are unusable. The tool keeps the whole 5968-unit PWR frame in every tile,
    so LTspice zooms out to the full frame.
  - Readable PWR tiles: `PWR_tile1..5.png`, made with `tools/capture_tiles.py`. It runs the unmodified tool with
    `--region` on a temporary copy whose only change is that the PWR frame rectangle (graphics) is removed.
- **Checked on each capture:**
  - No text of mine overlaps another text, a wire or a symbol.
  - Junction dots only at real joints.
  - Supplies up, grounds down. One of my ground flags was first drawn sideways, at a horizontal wire end in ISNS; it
    is now fixed with a vertical drop.
  - Port labels sit at the block edges, and SIM frames carry their note.
- **Found and not fixable under the rules:** four custom symbols draw their own pin names on top of each other. This
  is the same as in the original, and changing it needs .asy edits.
  - INA241A4 (U25);
  - CSS4J_4026 (R1: S1/S2/F1/F2/"Kelvin");
  - CD74HC4066 (U106C: A/B/VDD/VSS/CTRL);
  - MCP4451_CTRL/POT (U26E, U26A).
- **SIM_IREF1's 104-character PULSE value** is kept at size 0, as in the original. It is legible only when zoomed in.

## HUMAN tracing T1–T4: for the user at this check-in

## TEMPORARY LABELS (pilot only)
All 11 go away when GATEDRV and CONTROL are drawn and the wires run straight in.

| Net | Block | Why |
|---|---|---|
| GATE_M1 | PWR | gate drive from U19 (GATEDRV, not yet redrawn) |
| GATE_M7, GATE_M2, m2_source | PWR | channel-1 switch driver U15 |
| GATE_M6, GATE_M3, m3_source | PWR | channel-2 switch driver U10 |
| GATE_M5, GATE_M4, m4_source | PWR | channel-3 switch driver U8 |
| Verr1 | EA1 | to U28 in CONTROL |

## EXCEPTIONS requested
EXCEPTIONS.md row 1 (H10): C38, C36, C37 and C90 are netlisted with pin 1 on the opposite net to their channel-1
twins, so they must be drawn turned 180°. The request is to treat them like the `flip_ok` resistors.

## QUESTIONS
1. **Ambiguous bypass owners.** The proposals are below. Footprint-centre distances are from
   BOOST_power_RC2/BOOST_control_RC2.

| Cap | Rail | Map owner | Fact | Proposal |
|---|---|---|---|---|
| C6 | 12V | U16 | 8–11 mm from U16, 2.6 mm from C25, near C81; no other 12 V IC nearby | U16 output, beside C30 in SUP |
| C25 | 12V | U16 | same | U16 output |
| C22 | 5V | U101 (U104 nearer) | Both are 74HC packages without supply pins in LTspice, so the drawing is the same either way | U101: its only cap (U104 already has C58 and C97) |
| C36 | analog_5V | U7 (U13 at 4.9 mm) | – | U7: then each EA op-amp has exactly one bypass cap, so EA1/2/3 match |
| C37 | analog_5V | U13 (U24 nearer, but U24 has C32) | – | U13, for the same reason |
| C96 | 5V | U28 (U2 nearer, but U2 has C28) | – | U28: the 4051 has no other cap |

2. **New wording for the capacitor note.** It moves from SETUP to the logic-supply bank in CONTROL. After your OK
   I would add the pair to `approved_changes.json` `comment_changes`.
   - Line 1: "Bypass caps of U101-U105 (74HC gates) and U18 (CD4017B), grouped here because LTspice draws these parts
     without supply pins."
   - Line 2: "All other bypass caps from the KiCad design sit at their IC's supply pin."
3. **Exception 1:** approve or refuse.
4. **The custom symbols' own overlapping pin text:** leave it as in the original (my recommendation), or allow .asy
   edits? Such edits break E5 and would need the reference updated too.
5. **SIM_IREF1's long value:**
   - keep it at size 0 (as now);
   - show it at size 1 (about 1000 units wide, on its own line);
   - or hide it behind a one-line note.
6. **The REF frames are 1440 tall.** U26E must sit outside the area compared with channels 2 and 3, so REF2 and REF3
   get the same frame with an empty bottom. Is that OK, or would you rather U26E sat to the right (wider REF blocks)?
