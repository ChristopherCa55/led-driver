# Decisions needed before the fixes (2026-10-11)

Everything below comes from the baseline and the research of FIX_PROMPT sections 4-5. **Nothing in
`BOOST_review_fixes` has been changed yet** (it is a hash-checked copy of BOOST_package plus `NOT_FOR_FAB.txt`).
Pictures are in `img/`; numbers in `work/` (baseline in `work/baseline/`, the full table in `work/METRICS.md`).

You can answer per item ("D3: as recommended", "D7: option b", ...) or just "all as recommended" with exceptions.

---

## The baseline (all tools reproduce the review's numbers)

- **KiCad:** ERC 0 / 0 / 0 (main, power, card). DRC power 0 errors, 0 unconnected, 49 warnings; card 0 / 0 / 1;
  parity 0 on both. sync_check 0. check.py: netlists SAME, gerbers identical.
- **LTspice:** ltspice_equiv E1-E5 PASS. Baseline 30 ms run (`.save` list; same circuit and directives):
  LEDs 2.635 / 2.371 / 2.371 A, Ptvs 11.7 mW, LX steady peak 60.4 V.
- **Power board:** the DC solve and pcb_checks match the review exactly. Loop L 1.49 / 2.00 / 2.77 nH. GND max
  8.06 mV, LED-sense offsets 0.65 / 1.10 / 0.76 mV. Signal over GND 47 %, gate 27 %, sense nets 74 %. U16 Tj 117.8 C.
- **Gate returns (unreturned share):** M1 4 %, M2 42 %, M7 38 %, M3 52 %, M6 33 %, M4 37 %, M5 13 %, M8-M10 0 %.
- **Card:** U2 In+ 65.6 %, V_err 90.4 %, Current 82.4 %.
- **Two tools were rebuilt:** the 10-02 scripts for "sense nets over GND" and the LED-sense offsets are gone.
  - `tools/sense_cover.py` reproduces the 10-02 U3 figures exactly: 74 %, and every per-net value.
  - `tools/sense_offsets.py` reproduces them exactly too: 0.65 / 1.11 / 0.76 mV.

---

## Part data and simulations (D1-D5)

### D1. I2C pull-ups (schematic item 1)
**Facts:**
- **The pot has none.** DS22267A p. 1: "Internal weak pull-up on all digital inputs, except SCL and SDA". So the
  bus has only the Arduino's pull-ups.
- **Arduino side.** The Arduino is a Nano (ATmega328P), per BUILD_NOTES. Its internal pull-up is 20-50 kOhm *from
  memory*, not verified: the ATmega328P data sheet is not on disk.
- **Bus limits.** DS22267A p. 15 allows 1000 ns rise time at 100 kHz and 300 ns at 400 kHz, with Cb up to 400 pF.
  - Rise time = 0.85 R Cb. With about 35 kOhm, that is 1000 ns at only about 34 pF.
  - The card already has about 32 mm of SCL/SDA track, plus J9's wires and the Nano.
  - So the internal pull-ups alone are out of spec at any realistic cable length.
- **No firmware is in the project**, so the bus speed is not known.

**Options:**
- (a) Add 2 x 4.7 kOhm to 5V on the card, next to U26 or J9.
  - The part is 0603 JLC Basic C23162, already on the card.
  - At 100 kHz that is good to about 250 pF; at 400 kHz to about 75 pF.
  - It is a circuit change: LTspice (optional), the main page, the card sheet, card placement and routing,
    BOM/CPL.
- (b) Fit the pull-ups at the Nano end of the J9 wires. Nothing on the boards changes; a BUILD_NOTES line only.
- (c) Rely on the Arduino's internal pull-ups and keep the bus slow (documentation only). Not recommended.

**Recommendation:** (a), unless you prefer to keep the boards frozen; then (b).
**Also:** may I download the ATmega328P data sheet (Microchip DS40002061, about 5 MB) to verify the pull-up value?

### D2. U26 address pins (item 2), and a new finding
**Facts (DS22267A):**
- R_HVC is 16 kOhm *typical only*, at 5.5 V (p. 11). V_IL is at most 0.2 VDD = 1.0 V; V_IH at least 0.45 VDD =
  2.25 V (p. 10).
- R102 10k against 16k gives about 1.9 V, inside the undefined band.
- **New: A1 has the same problem.** R99 is also 10 kOhm to GND. Per p. 50 the address pins get the same "smart" weak
  pull-up while VDD is below the brown-out level, which is when the address is latched. So the address can be
  0x2C, 0x2D, 0x2E or 0x2F, not only 0x2C / 0x2D.
- **The documented workaround** (probe 0x2C and 0x2D) is only in an old README
  (`previous/2026-09-30/before_review_readme/README.md`). The current README lost it.

**Options:**
- (a) Documentation only: the README says to probe all four addresses.
- (b) R99 and R102 from 10k to 1k.
  - The pin then sits at about 0.3 V, below V_IL even if the pull-up were 3x stronger.
  - The value is JLC Basic C21190, already on the card, with the same footprint: a value change only.
  - Nothing else moves; the address becomes 0x2C.
- (c) Both (b) and the README note.

**Recommendation:** (c).

### D3. D19 against the LX peaks (item 3)
**Facts:**
- **D19's data** (Littelfuse 5.0SMDJ, rev 04/17/19): VBR 60.0-66.3 V at 1 mA, PD 6.5 W on an infinite heat sink,
  PPPM 5 kW.
- **The model** uses the *minimum* VBR (60.0 V), the pessimistic case.
- **Simulation (steady state, 25-30 ms):**
  - LX peaks 60.4 V. D19 breaks down in 101 of 453 switching cycles (22 %), not every cycle.
  - Average TVS power 9.5 mW, 0.15 % of PD. The shipped `.meas` gives 11.7 mW over 2-13 ms.
  - Most of D19's current each cycle is its junction capacitance at the LX edges, not breakdown.
- **A typical part** (VBR around 63 V) would not conduct at all in steady state.
- The 81.8 V spike at 0.15 ms is the known `.ic` shortcut start, as in the README.

**Recommendation:** no change. Add one README sentence with these numbers.

### D4. M8-M10 heat (item 4)
**Facts:**
- **Simulation:** drains sit at 1.49 / 1.45 / 1.45 V, so M10 / M9 / M8 dissipate **3.9 / 3.4 / 3.4 W**.
- **The earlier estimate** (CHAT_SUMMARY 2026-09-15, decision D8) was 2.8-3.2 W. That is why these three, with M1,
  got tab screws.
- **The pad:** McMaster 1272N32, 3 W/m-K, compressed to 0.93 mm over about 10 x 16 mm, is about 1.9 K/W, so
  roughly 7.5 K across it at 3.9 W. The FET's junction-to-case is not verified (HYG180N10 sheet not on disk).

**Recommendation:** documentation only. Add a README / BUILD_NOTES line with these numbers.

### D5. `.ic` naming nodes that do not exist (item 5)
**Facts:**
- **The terms.** C10 is the 4.7 nF cap on Verr3, but `V(C10)` names a node, and no node C10 exists. C5 and C2 do
  not exist at all.
- **Proof that they do nothing:** the same 30 ms run with the three terms removed gives bit-identical waveforms
  (3,137,079 points, 401,546,112 bytes of data) and identical `.meas` values.
- **The commented-out line.** `;.ic V(Vout_1)=30 ...` is a comment, not a directive.

**Options:**
- (a) Remove the three terms. The directive text changes, so it needs your OK for `approved_changes.json`.
- (b) Also delete the commented-out `.ic` line (an approved comment removal).
- (c) Leave both.

**Recommendation:** (a) + (b).

---

## Schematic presentation (D6-D8)

### D6. Net renames (item 7)
A rename reaches the LTspice file, the main page, both board sheets and both PCBs, and every check must then match.

**Recommendation:** notes only, no renames. If you want some renames, name them; my picks would be `M2_ON` ->
`out_1_on` and U18's "4" -> `U18_RESET`.

### D7. Diode values "D" (item 13) and J1-J8 (item 14)
**Facts:**
- **Sim fields:** every diode has `Sim.Params model="D"` set explicitly. So a Value change does not change KiCad's
  simulation.
- **BOM tools** take part data from their own table, by reference. So the BOM/CPL files do not change either.
- **The footprints'** Value fields on the PCBs must be updated too; parity enforces that.
- **New finding:** D19's KiCad fields disagree with the rest.
  - `Sim.Params` names `TVS_5KP54A`; LTspice uses `TVS_5p0SMDJ54A`.
  - Its `LCSC` field is C20415356 (the Littelfuse alternate); the BOM uses C42394451.

**Options for the diodes:**
- (a) Value = the part number: 1N4148W / B5819W / BAV21W / BAT54WS, as D19 and D28-D30 already do.
- (b) Keep "D" and add a visible MPN field.

**Options for J1-J8:**
- (a) Net names: J1 Vin, J2 GND, J3 Vout_1, J4 Output1_drain, J5 Vout_3, J6 Output3_drain, J7 Output2_drain,
  J8 Vout_2.
- (b) Wiring names: BAT+, BAT-, LED1+, LED1-, LED3+, LED3-, LED2-, LED2+.

**Recommendation:** diodes (a); J1-J8 (b). Also fix D19's two fields (it touches only those fields).

### D8. Notes, titles and their placement (items 6, 8-11, 12, 15, 16, 19)
Mock-ups were drawn into **scratch copies only**. Pictures in `img/mock/`:

| Picture | Proposed note (very brief, next to its part) | Item |
|---|---|---|
| `m1_sequencer_v2.png` | right of Verr1/2/3: "one-hot from U18: picks Verr1/2/3"; under U18: "Q3 resets it: counts Q0-Q2 only / 5V by net name (SpiceModel)" | 8, 11 |
| `m2_latch_enable_v4.png` | under U101D: "latch: set- low turns M1 on / RESET- low turns it off"; at C17: "rc: slow turn on / diode: fast off" (your M1 INHIBIT wording) | 9 |
| `g1_U15_v4.png` | at U15's DT pin: "DT = VCCI: no dead time" | 9 |
| `g2_U19_v4.png` | at U19's INB: "ch B unused" | 9 |
| `m3_ch2_titles_v2.png` | "same as channel 1" under CH2 / CH3 HEADROOM SERVO, as under the current-limit titles | 11 |
| `kicad_v4/k1_spares_after.png` (before: `k1_spares_before.png`) | U26D moved one slot right, clear of U106D, value under it | 15 |
| `kicad_v4/k2_title_block.png` | main-page title block: "BOOST LED driver - main schematic (both boards)", rev RC2, comment "Parts also drawn on the board schematics ..." | 12 |

**Two corrections to the schematic review:**
- **Item 9 is imprecise.** U15's two outputs are driven by *different* signals: INA = M2_ON (rail FET M2, through
  R13 220 Ohm / D11) and INB = ena_out_1 (LX-side FET M7, through R60 5.1 Ohm / D2). So "both FETs switch
  together" was wrong. DT = VCCI only disables the driver's own interlock. That fact comes from my earlier UCC21520
  model notes; TI's data sheet was not re-read, and I can download it if you want it verified.
- **The 220 Ohm vs 5.1 Ohm gate resistors:** I found no recorded reason. If you want a note there, tell me the reason
  in your words.

**Still to decide:**
- **Item 6 (overview / board split):** add "(card)" or "(power)" after each LTspice section title? Or no change?
- **Item 10 (directives):**
  - regroup the directive texts into one tidy column (geometry only; equivalence still passes);
  - merge the split POTn note (a comment change);
  - a one-line comment on the unused LED_RED/GREEN/BLUE models.
- **Item 16 (your bypass-cap note):** keep your sentence, or reword to e.g. "bypass caps, one per IC (placed at
  its IC on the PCB)"?
- **Item 19 (README):** one line saying the main schematic and the board schematics are kept identical by
  sync_check.py, and which one is the master. Which do you want as the master?
- **Do you want to place any of these yourself instead?**

---

## Power board (12V route, D10-D12, P2-P9)

### X1. The 12V route (P1, P7, P8)
It touches your 10-02 hand routing (12V on B.Cu and In4 in U1-U3), so it needs your OK (D11).

**What I found:**
- **No B.Cu-only feed to U19 exists without opening the Vin via array.** The array between the notch and the M1
  washer is 4 x 11 Vin vias at 1.05 mm pitch, and it blocks every east-west passage.
- **U19.16 still needs one layer hop.** It sits under U19.15's OUTA track on B.Cu.

**Option A** (scratch board, real DRC; `work/proto/p12v_A_NOT_FOR_FAB/`):
- **Removed:**
  - the In4 loop round M1;
  - three 12V vias: (75.35, 45.95), (74.75, 43.85) and (82.0, 48.25);
  - four Vin array vias in the column x = 80.85.
- **Added:** one 0.4 mm B.Cu track from (82.0, 48.25) through that column to C30's via (81.45, 39.75).
- **Kept:** U19.16's short In4 hop: the vias (74.85, 43.05) and (76.95, 42.15).
- **Checks:** DRC 0 errors, 0 unconnected, the same 49 warnings, parity 0.

**Results of Option A:**
- **Improved:**
  - Vin J1->R1 1.031 -> 1.013 mOhm, worst neck 38.8 -> **29.7 C**;
  - Vin ripple path 9.2 -> 6.9 C;
  - every GND branch 1-3 % lower R;
  - In4 GND pieces 16 -> 15 (M1's island joins: 707 -> 774 mm2).
- **Worse (needs your OK):**
  - Vin vias over rating 4 -> 5. The array's west column takes more: (79.8, 42.7) 1.13x -> 1.28x, and (79.8, 43.7)
    reaches 1.01x;
  - a few short-neck rises: GND ch2 bank 6.1 -> 7.9 C; loop GND ch2 12.1 -> 19.5 C on a 0.1 mm In4 sliver, 14 %
    share;
  - B.Cu GND pieces 17 -> 18.
- **Unchanged:** the B.Cu loop round the washer stays (the washer forces it), so its 51 mm detour stays.

**Options:**
- (a) Option A as is.
- (b) Option A plus a Vin via added in a freed funnel spot, to win back the west-column load (I would test it first).
- (c) Leave the 12V route.

**Recommendation:** (b), falling back to (a).

### D10. Loop vias over the IPC rating
Each "worst" via is identified:
- **ch2:** inside C3.2's pad (via-in-pad already).
- **ch3:** inside C76.2's pad.
- **ch1:** at C1.2's edge, with two more GND vias.
- **Vout_3:** the outermost of three Vout_3 vias on C4.1.

**Fab facts:** ORDER_CHECKLIST already selects "Epoxy Filled & Capped" (free at 6 layers), so via-in-pad costs
nothing extra. A larger drill helps much less than an extra via (rating scales with area^0.725). DRC rules: via
drill at least 0.3 mm, and Vout vias at least 0.4 mm.

What-if solves (every branch; `work/whatif/`):

| Variant | Worst loop via (ch2 / ch3 / ch1 / Vout_3) | Main cost |
|---|---|---|
| baseline | 3.60x / 2.72x / 2.06x / 2.80x | - |
| ch2 only (2 vias at C3.2) | **1.72x** / 2.72x / 2.06x / 2.80x | Vout_2 bank path 0.312 -> 0.316 mOhm (+1.2 %); antipads in In4 Vout_2 only |
| ch2 + ch1 (3 vias) | 1.72x / 2.72x / **1.59x** / 2.80x | also Vout_1 bank path 0.219 -> 0.227 mOhm (+3.7 %); antipads in In2 LX and In3 / In4 Vout_1 |
| all 7 vias (2 at C3.2, 2 at C76.2, 1 at C1.2, 2 at C4.1) | 1.72x / **1.69x** / 1.59x / **1.82x** | also LX L1->M5 1.969 -> 2.051 mOhm (+4 %), long-neck 25.8 -> 34.2 C (the ch3 / Vout_3 vias cut LX on In2 and B.Cu in M5's funnel) |

These are plane-connected vias, so per your rule they are reported, not judged.

**Options:**
- (a) ch2 only;
- (b) ch2 + ch1;
- (c) all 7, accepting the LX L1->M5 cost;
- (d) none.

**Recommendation:** (a). ch2 is the worst via (3.6x), and the fix costs only 1.2 % on Vout_2. Add ch1 (b) if you
accept +3.7 % on the Vout_1 bank path. For ch3, moving GATE_M4's via first (X3) may free a spot that does not cut
LX; I would test that before proposing ch3 vias.

### D11. Your hand-placed copper
The 10-02 edits U1-U4 rerouted most of the tracks the review names:
- 12V (B.Cu, In4);
- Current (B.Cu, F.Cu);
- analog_5V, M1_ON, out_3_on, Net-(D13-), Net-(D8-), U10-VDDA;
- the M2 / M7 drives and m2_source;
- the LX In3/In4 zone;
- 122 GND vias, including the 4 at the J4 entry.

**May I re-route any of them where a fix needs it?** The gates would stay: DRC/parity clean, no metric worse
without your OK, and gate returns not worse. Or do you want to approve each one separately?

**Recommendation:** a general OK under those gates, with each change shown before/after in the report. The J4
stitching vias stay unless you say otherwise.

### D12. LX to M5 (P3)
Moving its neck vias gains 3 %. A second LX layer is not available (In3/In4 are Vin there).

**Recommendation:** leave it as a known item.

### X2. Output 1's path to J3 (P2) and the western Vin feed (P5): review corrections
- **The review was wrong about the feed.** It is not only the pre-charge feed: it is also the **input supply of
  both 5 V regulators**, U17.3 (5V) and U1.3 (analog_5V). So it carries DC all the time.
- **Moving the In3 bar** (the 3 mm Vin crossing under `ena_out_2` inside the Vout_1 pour) only takes Output 1's
  path from 8.459 to **8.346 mOhm (-1.3 %)**.
  - The real limit is a 2.4 mm neck at (54.7, 72.3) and the 70 mm length.
  - B.Cu at that crossing is taken by M2_ON and U10-VDDA (DRC: 2 crossings).
- **Only a second Vout_1 layer to J3 would reach the other outputs' level.** On In4, J3 sits inside the Vout_2
  pour, so that is a big re-layout.

**Options:**
- (a) Leave both as known items. 22 mV at 2.6 A does not change the LED current, which the sense resistor sets.
- (b) Re-route the western Vin trunk off the three GND layers (a large job; GND gains only, In1 is already solid).

**Recommendation:** (a).

### X3. Switching nodes and gate tracks in pours (P6), Current (P9), drain strips (P4)
Each one is a separate small reroute, prototyped and solved one at a time:
- m4_source through the In4 Vout_3 pour (kept beside GATE_M4/M5);
- D13- splitting B.Cu Vout_3;
- GATE_M7 splitting an In4 LX piece;
- GATE_M4 / m4_source cutting the In3 GND under the ch3 caps (this joins up with D10's ch3 vias);
- Current, 46 mm on F.Cu: shorter and over GND;
- the three analog_5V vias in the Output2_drain strip.

**Recommendation:** try them in that order and keep only those that pass every gate.

---

## Control card, outputs, housekeeping (D9, D13, D14)

### D9. Card strategy (C1-C3)
**Option (a): the 8-layer card** (sha 3335e701).
- It has 47 parity differences from today's schematic: 26 fields, 11 net names (the 10-09 renames) and 10
  attribute/values. All are the kind Update-PCB fixes.
- Cost: 8 layers was $123.42 for 5 (1 oz inner, 09-30 quote) against $56.83 today (6 layers, 0.5 oz inner).
- An 8-layer quote at 0.5 oz inner is not known. I would read it on JLC's quote page if you want this option.

**Option (b): move parts to open the U101-U2/U5 corridor and re-route with planes.** This is a large job.

**Option (c): targeted fixes on the 6-layer card:**
- move the tracks that alone split GND (79 listed; the longest first: 0err_hi / D5- on In4, then 0err_hi /
  U101A-Y / SDA on In1);
- stitch the one-via pieces;
- pull the stacked pairs apart.

**Recommendation:** (c), the gates being GND piece counts and areas, the return-gap list, and sens_check6 not worse.

### D13. Cosmetic cleanup
Covers the 674 / 2600 short jogs and the duplicate tracks out of vias.

**Recommendation:** only on routes already being touched, or not at all.

### D14. Fab outputs
**Recommendation:** after you approve the result, generate gerbers, drill, fab drawings, BOM/CPL, cost files and
the STEP (if parts moved) in the copy, still marked NOT_FOR_FAB until you say ship.

### Downloads I would like
Each only if you say yes:
- the ATmega328P data sheet (D1);
- TI's UCC21520 data sheet (to verify the DT note);
- the HYG180N10 data sheet (junction-to-case, for D4);
- reading JLC's quote page for an 8-layer card at 0.5 oz inner (D9a).

### Housekeeping
The page file grew to 46 GB while the heavy runs overlapped (21 GB free on C:). I now run solves and simulations
one at a time.
