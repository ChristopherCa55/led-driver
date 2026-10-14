# Layout rules

**Priority when goals compete:**

1. Electrical correctness (mandatory).
2. Understandable circuit flow and traceable connections.
3. Legible spacing and consistent repeated blocks.
4. Compactness and fewer crossings.

**A clear, unambiguous wire crossing is better than making the reader search for matching labels.**

Hard rules (H) are checked by `tools/asc_layout_check.py`. Review flags (F) are reported for judgement. Anything the
checker cannot judge is decided by the user at the check-ins.

---

## 1. Floorplan

The schematic is one flat sheet in landscape. Signals flow left to right; supplies are drawn up and ground down.

```
          [ISNS: U25 + C20]  directly above R1, Kelvin wires straight down       Vin pre-charge rail ─┬──────┬──────┐
PWR ┌─SIM (dashed)────────────────────┐                                                             D28    D29    D30
    │SIM_BATTERY─SIM_CABLE_RESISTANCE─│─SIM_CABLE_INDUCTANCE─┬[Vin]─C69 C40 C85─R1─L1─LX bus─┬─M1 D19 R14 ─┬ M7─M2─Vout_1─caps
    │ (+ terminal named, e.g. Vbattery)                     │                               │             ├ M6─M3─Vout_2─caps
    └─────────────────────────────────┘                     │                               │             └ M5─M4─Vout_3─caps
                                                    ════════ one drawn ground-return bus under the whole spine, one GND ════
    [SUP: U16 U17 U1, wired down from the Vin node]   [GATEDRV: U19 under M1 │ U15 under M7/M2 │ U10 under M6/M3 │ U8 under M5/M4]
ch1 row  [CREG1: Vout_1 → SIM_LED1 → M10/R52, U11] ⇄ [REF1: SIM_IREF1, pot U26A, S&H U106C, integrator U24 (+U26E)] → [EA1: SIM_VREF1, U3] ─Verr1──┐
ch2 row  identical, fixed vertical pitch                                                                                                 [CONTROL]
ch3 row  identical                                                                                                                       tall block;
                                                                                                                                         outputs → GATEDRV
SETUP (bottom): libraries/models │ .tran/.options │ .ic + start-up note │ .meas │ .param + notes │ the user's notes
```

**Inside CONTROL, columns run left to right:**

1. Inputs: Verr1–3 as direct wires from the EA blocks; `Current` from ISNS.
2. Mux U28 and the comparators U2, U4 and U5 with their threshold dividers (R11/R16/R17, R18/R19/R20).
3. U104E (0err_hi → VerrGT0); the latch U101A–D with R4 and D6; the low-error timeout (U14, Q1, …); the counter U18,
   with OUT_1/2/3_ENA leaving as a group of three.
4. **The fan-out, three identical rows stacked:**
   - the three NANDs fed by VerrGT0 and OUT_x_ENA, side by side;
   - then the three delay networks;
   - then the three Schmitt inverters → ena_out_1..3;
   - then the three NANDs (Out- · ena_out_x);
   - then the three inverters → M2_ON / out_2_on / out_3_on.
5. M1 inhibit: the 12 V UVLO (U21 and its dividers) and D1/D15/D24/D27 → U104A → M1_ON.
6. The right edge, with outputs grouped:
   - ena_out_1..3;
   - M2_ON/out_2_on/out_3_on;
   - M1_ON;
   - the **logic-supply group**, the bypass caps of U101–U105 and U18, wired as one small bank with a note.

**Feedback paths inside CONTROL** run backwards: OUT_x_ENA → U28 select, M1_ON → U101B, and low_error_timeout →
D6. Draw them as straight wires along the block's top or bottom margin. A few clean crossings are fine.

## 2. Hard rules

| ID | Rule | Checked how |
|---|---|---|
| **H1** | Electrically identical to the original: all of E1–E5 in CHECKS.md | `ltspice_equiv.py` |
| **H2** | Every part sits fully inside its block's frame (BLOCKS.md); frames don't overlap; every directive sits in the `[SETUP]` frame | frames = `RECTANGLE` + title `;[ID] …` |
| **H3** | **One drawing per block:** inside a frame the parts form ONE connected graph through *wires*. Labels, supply flags and ground symbols don't count. Only the logic-supply bank in CONTROL may be its own piece | wire-group union-find |
| **H3b** | **No orphan parts:** no part whose every non-ground pin touches only labels | same |
| **H4** | **No label jumps inside a block:** a signal net never relies on a label to connect pins in the same block. A net may carry at most ONE label per block (its name tag or its exit label) | per net, per block |
| **H5** | **Continuous power path**, inside PWR: the battery chain, Vin, rsense_lo, LX, m2/m3/m4_source and Vout_1–3 are each one wired piece; every PWR ground pin is on one drawn return bus with exactly one GND symbol; a `Vin` name flag sits on the wire after the cable; the battery's + terminal net carries its own name (e.g. `Vbattery`) | wire groups in PWR |
| **H6** | **Block exits.** (a) Adjacent blocks join by a short **direct wire** across the shared edge: gate drives, the Kelvin pair, CREG⇄REF⇄EA, Verrx → CONTROL. (b) Otherwise the net leaves through **one port-typed flag per block** (`IOPIN Out` in the driving block, `In` in the others), on the frame's boundary band (≤ 64 units from the edge), at the end of a wire stub ≥ 16 units. (c) No wire passes through a block it doesn't connect to | interfaces in blocks.json |
| **H7** | Supply rails (`Vin` outside PWR, `12V`, `5V`, `analog_5V`) and ground use **plain** flags, never port-typed. Draw supplies up and ground down (upside-down ones are flagged) | flags |
| **H8** | No 4-way junctions; no pin lying on the middle of a wire (a hidden connection); no overlapping collinear wires; no crossing within 16 units of a junction or pin; no wire through a symbol body | geometry |
| **H9** | **Space:** no text (InstName, Value, attributes, labels, comments) overlaps other text, a symbol or a wire, and text keeps ≥ 16 units from other objects. *Estimated from font size; confirm in LTspice captures* | text boxes, calibrated on LTspice screenshots |
| **H10** | **Matching copies.** In the ch2/ch3 copies of CREG, REF, EA, the channel drivers, the PWR switch columns and the CONTROL fan-out rows, every part, orientation, InstName/Value position and wire sits at the same offset as in ch1. Frames of repeated blocks are the same size | offsets from the first part |
| **H11** | Notes sit beside their subject (the D28–D30 note at the diodes; the simulation notes in SETUP). Every original note is kept verbatim (E3) | blocks.json `notes` |
| **H12** | Each bypass cap is wired to its owner's supply pin (bypass_map.json), within 240 units of it, inside that block. The regulator caps sit at the regulator pins. The logic-supply caps sit inside CONTROL | supply_pins in blocks.json |
| **T1–T10** | Tracing tasks within their label-jump budgets (CHECKS.md §3) | label jumps along each path |

**Allowed differences between copies**, each with a short note at the part:

- **Simulation stimulus:** the SIM_LED colour models, the SIM_VREF pulse widths, and IREFn_DUTY/POTn_CODE.
- **R23, R49, R59, R74:** netlisted with reversed pin order relative to ch1. Rotate them 180° (and shift them) so
  they look the same; the checker compares their body centres.
- **U103B:** its AND inputs are in the other order (`ena_out_3, Out-`). Its two input wires may cross or differ; add
  a note.
- **REF1 only:** it also holds the shared pot control U26E (R99, R102, R103, C26) and C23, the bypass cap of the
  shared 4066. Add a note saying they serve all three channels.

## 3. Forbidden: what the last attempt did

- **Orphan parts:** a capacitor standing alone with a `Vout_2` label on top and ground below; L1 or M1 attached only
  by labels.
- **A block drawn as islands joined by same-name labels**, just to avoid crossings.
- **Labels on pins in the middle of a dense block** for nets that go elsewhere.
- **Moving a note away from what it describes, or deleting one.**
- **Hierarchical sub-sheets.** They rename internal nodes (`SRV1` becomes `X1:…`), which breaks `.ic V(SRV1)` and
  `.meas`.
- **Renaming any existing net, or editing values, models, directives, `.asy` or `.lib` files.**
- **Offering frames, titles or documentation instead of cleaning up inside the blocks.**
- **Changing a checker or its thresholds, or "allow-listing" findings, without the user's OK.**

## 4. Drawing guidance

**The power path:**

- Run it as one horizontal spine with current flowing left to right.
- Put the input caps on short vertical drops from the Vin part of the spine.
- Put L1 in line, and drop M1 from the LX bus.
- Give each FET pair its own column with the same spacing, and its output caps as a row of identical drops.
- Run the pre-charge rail above the spine: it starts at the Vin node and drops through each diode to its Vout.

**The battery chain:**

- Draw SIM_BATTERY (vertical, + up), then SIM_CABLE_RESISTANCE, then SIM_CABLE_INDUCTANCE, in series and wired.
- Draw a dashed frame with the comment `simulation only – not on the PCB` around these three parts, inside PWR.
- Put a `Vin` name flag right after the inductor, and a name flag on the battery's + terminal (e.g. `Vbattery`).

**The other SIM parts:**

- **SIM_LEDx:** in CREGx, drawn in series between the `Vout_x` input and the sink FET's drain, with the same dashed
  "simulation only" frame and note.
- **SIM_IREFx and SIM_VREFx:** at the left edge of the block whose input they drive, in a small dashed frame.
- **SIM_ARD_INH:** next to D27 in CONTROL.

**Spacing:**

- Start roomy: at least 64 units between unrelated symbols and 32 between a text and anything else.
- Then tighten only where the LTspice capture still reads cleanly. The user asked for *more* space than the original
  had.

**Text:**

- Place InstName and Value with instance `WINDOW` lines, so that both are readable and away from wires.
- Use the same `WINDOW` offsets in every copy.
- Horizontal resistors (R90) read best with `WINDOW 0 0 56 VBottom 2` and `WINDOW 3 32 56 VTop 2`.

**Labels:**

- Exit labels go on the frame's edge, facing the block they go to, on a short stub.
- Add a short comment beside an exit label naming its destination when that block is not adjacent (e.g.
  `→ GATEDRV`).
- Never put two labels of the same net in one block.

**Bypass caps:** draw each one vertically at its IC's supply pin: the rail flag on the pin side, ground below.

**Notes:**

- Restore the user's note about the capacitors **verbatim**, and propose a new wording at check-in 1.
- Keep the D28–D30 note at the diodes.

## 5. LTspice file details

| Element | `.asc` syntax | Notes |
|---|---|---|
| Block frame | `RECTANGLE Normal x1 y1 x2 y2 2` | Style 2 is drawn dashed/dotted. Graphics only: no netlist effect (LTspice help, *Basic Schematic Editing*) |
| Block title | `TEXT x y Left 2 ;[PWR] Power path (power board)` | Must sit inside its frame; the `[ID]` must match blocks.json |
| Port-typed label | `FLAG x y Vout_1` then `IOPIN x y Out` | `In` / `Out` / `BiDir`. Drawn as an arrow, no netlist effect (LTspice help, *Label a Node Name*) |
| Plain label | `FLAG x y 5V` | Supplies; also name tags on wires |
| Ground | `FLAG x y 0` | |
| Instance rename | `SYMATTR InstName SIM_BATTERY` | Only the three approved renames |
| Text window | `WINDOW 0 dx dy Left 2` after the SYMBOL line | 0 = InstName, 3 = Value; offsets are in the symbol's own frame |

**Grid and coordinates:**

- Wire ends and pins sit on a 16-unit grid.
- Pin positions come from the `.asy`, transformed by rotation **then** mirror. `tools/ascgeo.py` has the verified
  transform.

**How LTspice connects things:**

- It connects a wire end or a pin lying anywhere *on* another wire. That is why H8 forbids pins on a wire's middle.
- Wires that merely cross don't connect.

**Encoding:** write the `.asc` as latin-1. Keep `µ` as the single byte 0xB5; never write `§`.
