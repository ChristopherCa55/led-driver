# Re-place handoff: verified facts (2026-09-14)

## Datasheets read
- HYG180N10LS1P (HuaYi V1.0, szhxmos.com/d/HYG180N10LS1P.pdf): package code P = "TO-220FB-3L" but the drawing is a standard
  exposed-metal-tab TO-220: A 4.57, tab A1 1.30, hole ΦP 3.60, Q 2.80, H1 6.50, E 10.00, D 15.60, D1 9.10, L 13.50,
  e 2.54, back pad E3 ≥ 7.00 × D2 ≥ 5.50. RθJC 1.6 °C/W. Pins G-D-S = 1-2-3. Tab connection not stated (normally drain).
- KiCad TO-220-3_Horizontal_TabDown: hole at (2.54, -16.66), body y -19.46..0. TabUp: hole (2.54, +16.66), body 0..19.46.
  Board M1 = TabDown flipped to B.Cu (hole local +16.66, model TabDown.step) -> tab faces the PCB.
- Panasonic ZU series (ast-ind-156944.pdf, 01-Sep-25): EEHZU1H221P = SMD vertical, G16, øD 10.0, L 16.5 (V: 16.8),
  A/B 10.3, H 11.0, I 3.2, W 1.2, P 4.6; 5200 mA @125 °C / 3600 @135 °C; 10 mΩ. No land pattern in datasheet.
- 680 µF (SUPERSEDED: EEH-ZU1E681UP does exist, ZU(U) datasheet ast-ind-280898.pdf, see below). EEHZU1V681UP (ZU(U), 35 V, 10 × 16.5, 9 mΩ, 5.8 A @125 °C);
  EEH-ZS1E681UP (ZS(U), 25 V, 10 × 12.5, 14 mΩ, 3.5 A @125 °C / 2.5 A @135 °C). Sim input ripple 3.66 A/cap.
- Bourns CSS4J-4026 (RS mirror docs.rs-online.com/ed1d/0900766b81593767.pdf, 04/16): 2L00 = K material, 4 W @130 °C
  terminal, TCR ≤ +50 ppm/°C (20–60 °C), H 2.94. Body 10.06 ± 0.25 long, 5.00 resistive width, 6.60 incl. sense tabs,
  4.90 ref; force foot 2.00 ± 0.12; sense tabs 0.70 wide × 1.00 long. Recommended pads: overall 10.40, pad height 7.30,
  sense pads 0.80 wide, 5.60 dim. Derates to 0 W at 170 °C.
- LCSC C2076167 (CSS4J-4026K-2L00F): out of stock 2026-09-14, $1.0882.

## Schematic
- BOOST.kicad_sch vs .history/BOOST.kicad_sch: only UUID lines differ (164 lines, 0 non-UUID) -> main file current.
- Netlist diff vs BOOST_9-2_1013.net shows C41/C44/C45 (1 nF IREF wiper caps) removed: NOT my edit. They are absent from the
  pre-edit backup schematic and from the shipped boards' fps json; BOOST_CONTEXT_TRANSFER.md section 13 item 6 recommended deleting them.

## User's saved brief notes (replace_brief_page_saved_2026-09-14.html, brief-state JSON)
- D1 C: asked why package/slower edges help; TVS not clamping in their sim (answered by SIMULATION_REPORT §4).
- D2 B: "reset tripped around 47A" vs 40.5 A.
- D3 C: asked for cost estimates (v2 quote table).
- D4 B: OK with ribbon but wants standoffs.
- D5 A: shrink card, add holes.

## User decisions (check-in 1, 2026-09-14)
- Dividers: both resistors on the control card.
- FET tabs: M1, M8, M9, M10 metal tab to case (insulated) - required. Others: user doesn't care; recommended all
  ten tab-to-case (TabUp on B.Cu) - pending objection. Screws optional, may double as board mounting into tapped box.
- Standoffs: nylon, holes isolated (NPTH + 7 mm keep-out).
- Input caps: user wants smallest area, 25 V ok (Vin max ~17 V), same height as outputs ok, ~11.5 A bank.
- ZUU datasheet (ast-ind-280898.pdf): EEHZU1E681UP 680 uF 10x12.5 G12 5300/3700 mA 10 mOhm; EEHZU1E102UP 1000 uF
  10x16.5 6100/4300 8 mOhm. Freq factor (>=150 uF): 5-10k 0.65, 10-15k 0.75, 15-20k 0.80, 20-50k 0.85, 50-100k 0.90.
  ZT(U) 25 V: ZT1E331UP 8x10.2 2.9 A 22 mOhm; ZT1E561UP 10x10.2 3.5 A 16 mOhm. ZS1E681UP 10x12.5 3.5 A 14 mOhm.
- Panasonic mounting note: >= 2 mm free space above the pressure valve (6.3-16 mm cans); no high-V/high-I pattern above it.

## LTspice input-cap runs (scratchpad/sim_icap, d10 netlist = R15 10 ohm, no D12; 08-31 setpoints)
- 14 V: op point matches SIMULATION_REPORT d10 (Vout 23.21/33.01/33.01, LED 2.631/2.368/2.368, IL pk 37.3 A, LX 62.0 V,
  TVS 37.9 mW). Bank 10.36 A rms, 3.455 A per cap (ideal sharing), Vin ripple 155 mV p-p / 40 mV rms,
  spectrum 88 % 30-50 kHz, 6 % 10-15 kHz, peak 30.8 kHz. Effective derating factor ~0.84.
- 17 V: bank 8.61 A, 2.87 A per cap, Vin ripple 130 mV p-p, peak 36.5 kHz. IL pk 31.4 A.
- 3 x EEHZU1E681UP: 3 x 5.3 x 0.84 = 13.4 A capacity vs 10.4 A (29 % margin; 16 % at 11.5 A).
  2 x EEHZU1E102UP = 10.2 A (fails). 8 mm ZT(U) needs 5 parts (more area).

## Check-in 3 (2026-09-15)
- Evidence shown: best concept p5_1 (24/43 targets); top-only parts 4086 mm2 of 6148 (66 %), + 8 screw circles r 5.5 -> 79 %.
- User: M2-M7 screw distance ~25 mm; limits are prioritized goals (hard: rail FET -> caps, M1/D19/return, sink -> shunt;
  loose: input caps ~20, farthest LX drain ~30); card anywhere except over L1 / lug corner; LED pads may go to the bottom
  edge (left half); lugs may go lower on the right edge.
- Report still uses the brief's targets as the reference column (with a goals column).

## Regulator capacitor facts (verified from datasheet text, 2026-09-15; extracted with scratchpad/pdftext.py)
- TI LM2940 (SNVS769J, Dec 2014), 8.2 design table and 8.1: C_OUT >= 22 uF (may be increased without limit), ESR
  >= 100 mOhm and <= 1 Ohm over the whole operating ambient range; input 0.47 uF (required if far from the supply
  filter). Old National datasheet: ESR "too high or too low" causes instability; solid tantalum has more stable ESR.
  -> C30 (47 uF, U16 12V out) cannot be a plain MLCC; a small solid tantalum >= 22 uF within the ESR window can.
- ST L78L (Doc 2145 Rev 19): electrical characteristics at CI = 0.33 uF, CO = 0.1 uF; no ESR/stability/capacitor
  requirement text found. -> C7/C55 (47 uF on U17/U1 outputs) are design choices, not datasheet requirements.

## Placement state before check-in 4 (2026-09-15)
- Best: p6l_1 (33/43 goals, 26/43 brief). Blockers: J10 (THT 2x15) needs a FET-free bottom strip inside the card area;
  top side has zero free spots for C30/C55 (scan). Small conflicts: L1 x M7 pins, H5 x M9/R53, M1/M8 screwdriver,
  M3 25.5 mm. psat placed 72/74 small parts.

## Check-in 4 (2026-09-15)
- User: reserve a FET-free underside strip for J10 (J10 placed first); smaller regulator caps (C30 tantalum >= 22 uF,
  ESR 0.1-1 Ohm; C7/C55 22 uF ceramic), LCSC-stocked.
- Found: J10 courtyard 6.18 x 39.21 mm cannot sit inside a 42 mm card with 2 mm margins (needs >= 43.2) -> card 45 mm
  (brief: "~45 mm if the header needs it"). The in_card penalty had been unsatisfiable.

## Rules source (found 2026-09-15)
- power_sync*.kicad_pro (written by pcbnew.SaveBoard) do NOT carry the shipped BOOST_power.kicad_pro rules: netclass
  patterns (Power: Vin, ...) empty, Default clearance 0.2 vs shipped 0.15, min_copper_edge_clearance 0.5 vs shipped 0.3.
  Shipped rules: min_clearance 0.13, min_copper_edge_clearance 0.3, min_through_hole 0.25, min_via 0.45, min_track 0.13,
  min_text_height 1.0; netclasses Default, Power, Gate, Rail. No .kicad_dru exists.
- Every WIP/final power board must use a copy of the shipped BOOST_power.kicad_pro (copy AFTER SaveBoard, which rewrites
  it), then add the new Power members (Net-(M8/M9/M10-S)) and the sense class.
- Control card confirmed the same: shipped BOOST_control.kicad_pro has netclasses Default 0.15 / Power 0.25 / Gate 0.2 /
  Rail 0.2 and 23 netclass patterns; control_sync2.kicad_pro has only Default 0.2 and no patterns, and different
  min rules (track 0.2 vs 0.13, via 0.5 vs 0.45, hole clearance 0.25 vs 0.2, text 0.8/0.08 vs 1.0/0.15). The shipped
  control .kicad_pro has no rule_severities key (KiCad defaults apply). Build the card on a copy of the shipped .kicad_pro.

## Session 2026-09-15 (afternoon, account bubba; project now at C:\Users\bubba\OneDrive\Documents\led-driver)
- The handoff's path (C:\Users\Dominick Junior\...) does not exist on this machine; tools' hard-coded paths made
  repo-relative (fpinventory, syncboard, run_place.sh, deadtime2, icap). No Inkscape here: run_place.sh now uses
  kicad-cli pcb render for PNGs. Python 3.13 (C:\Python313) has numpy + matplotlib; KiCad python reports pcbnew 10.0.0.
- p7 J10 candidates rerun (seeds R 802, C 803, T 804, B 805). Final costs L 1366.5, R 1372.6, C 1450.6, T 1511.8,
  B 2351.0. Goals met L 36, R 33, C 32, T 35, B 36 of 43; none mechanically legal (all keep L1 over M2/M7 pins, tall
  caps inside a sink screw circle). p7L standoffs were in a line (x 52-64): no card support rule existed.
- C30 stock (LCSC, 2026-09-15): TPSC226K025R0275 = C313069, 2 in stock (not enough). User chose
  Vishay TR3D476K025C0250 (C4979367, LCSC and JLCPCB 107 in stock, $1.16). Vishay TR3 datasheet (doc 40080):
  47 uF case D, DCL 11.8 uA, DF 8 %, ESR max 0.250 ohm @ 25 C 100 kHz, ripple 0.77 A; case D 7343-31 L 7.3 +/- 0.3,
  W 4.3 +/- 0.3, H 2.8 +/- 0.3 mm; -55 to +125 C (25 V to 85 C, 17 V at 125 C); ESR may be 1.25 x limit after mounting.
  ESR versus temperature is not given in the datasheet (not verified).
- KEMET T491 datasheet T2005 (2026-07-08): T491C226K025AT ESR max 1.0 ohm (not 1.4 as noted earlier; 1.4 is AVX TAJC),
  T491D476K025AT 0.7 ohm.
- LM2940 needs >= 22 uF: a 22 uF +/-10 % part can be 19.8 uF, one reason for 47 uF.
- C7/C55 GRM32ER71E226KE15L = JLCPCB C21397, 77,742 in stock, $0.56 (Extended).
- Tantalum footprint Capacitor_Tantalum_SMD:CP_EIA-7343-31_Kemet-D: pad 1 at x -3.12, silk bracket closed on the
  pad-1 side = anode. C30 pin 1 = 12V, so polarity is correct without remapping.
- C41/C44/C45 (user: "decide"): restored as 1 nF on IREF1/2/3_input at the sink op-amp IN+ (U11.3/U12.3/U6.3),
  power board. Reason: the setpoint nets now cross J11/J10 and run beside the power stage into a kilohm source;
  no filter exists on the net (C100-C102 sit upstream at the divider nodes). Time constant depends on the pot's
  unspecified R_AB (MCP4451-xxxx): ~1.6 us (5k) to ~27 us (100k) with 1 nF; DNP at bring-up if low-duty PWM suffers.
- Schematic edit (tools/schematic/capedit.py): C30 -> CP_EIA-7343-31_Kemet-D + MPN/LCSC; C7/C55 -> 22u
  C_1210_3225Metric + MPN/LCSC; C45/C44/C41 added. ERC 0/0 (same four ignored checks), netcheck 0 failures,
  netdiff vs BOOST_9-14_replace.net shows only these changes. New sch SHA-256 de3bf0a7...; netlist BOOST_9-15_caps.net;
  assignment board_assignment_2026-09-15.json (POWER 124, CONTROL 166). Backup: previous/2026-09-15/schematic/.
- 14:26 today KiCad (GUI) opened and closed BOOST_split_boards/BOOST_power: lock files removed, .kicad_prl,
  BOOST_power-backups/ zip, .history touched, and BOOST_power.kicad_pro rewritten WITHOUT the Power/Gate/Rail
  netclasses (Default 0.2). User approved restoring it from git; the rewritten copy is in previous/2026-09-15/.
  Lesson: opening a shipped board in KiCad 10 can also drop netclasses; check the .kicad_pro after any KiCad session.

- L1 land pattern (BOOST_CONTEXT_TRANSFER §13 item 4): Codaca CSCF3218 series datasheet (rev 05/31/2024,
  codaca.com/Private/pdf/CSCF3218.pdf) text gives body 32.0 +/- 1.0 x 22.5 +/- 1.0, 34.5 max overall, height 18.5 +/- 0.5,
  terminal 6.0 +/- 0.3, pitch 12.0 +/- 0.5; reference land pattern numbers 12.0, 6.0, 8.0, 23.5, 33.0, 10.5, 7.0, 6.0,
  17.25, N/C. The project footprint IND_CSCF3218-6R8MC has pads 1/2 8 x 6 at (+/-6, 17.25) and N/C pad 3 6 x 7 at
  (0, -10.5), body fab 32 x 22.5: the numbers match. The drawing's leader lines did not extract, so this is a numeric
  match, not a visual one. Terminals protrude past the body; the 32.6 x 34.8 courtyard is real. Height 18.5 +/- 0.5
  (pmodel uses 19.0).

## Placement search log (2026-09-15 afternoon)
- psa4 + mk8 (ramp x10, standoff corner squares 17 mm) from each p7 result, 30 runs: none legal (best T 7494).
- psa5 (local screw deltas, exact to 1e-10 by tdelta.py; ~9x faster), mk9 random start, card + J10 free, ramp: 30 runs,
  none legal; best mid-run states were better than final (ramp froze the search).
- mk10 legality weights from the start + teleport 3 %: 30 runs, none legal; best p10_s28 overlap ~0 but L1 over
  screw points (11 mm of intrusion); distance goals worse than p9.
- p11 relaxation variants (random start, mk10 weights): A tab-screw tall clearance 4 mm; B + standoffs anywhere in
  their card quadrant; C + screw distance 30 mm. None legal outright; best p11C_s1 only three cans in tab circles.
- p12 (mk11 rigid INPUT group L1+M1+D19+R1 and three LED-channel groups sink+shunt+LED pads): worse (>= 23,000);
  the channel groups only fit the 37 mm LED zone at one exact pitch and height. Dropped.
- p13 cool polish (mk10 start) from p11 layouts: p13_p11C_s1_s10 legal under C but 24/43 goals (input caps
  40-64 mm from M1); all its unscrewed FETs within 21.8 mm of a screw, so 30 mm was not needed.
- p14 ramp polish under D = tab clearance 4 mm + quadrants + screw distance 25 mm: from p9a_s10 (best goals,
  illegal) 34-35/43 goals with 3-8 mm keep-out intrusion left (cans ~2 mm from tab screws).
- p15 polish with keep-out weight 1000/mm: 13 legal layouts (of 30), best p15_b10_k1 legal under D with 35/43 goals
  (prank.py). Under the original 5.5 mm tab clearance it is not legal: U16 4.05 and C69 4.15 mm from M1's screw,
  C87 5.02 from M8's, C71 4.01 and C78 5.21 from M9's. Standoffs also outside 17 mm corner squares.
- Chosen for the check-in (PENDING USER APPROVAL of D): p15_b10_k1. Card x 45.9-90.9, y 70.0-115.0; J10 pin 1
  (69.48, 74.16) rot 0; standoffs H5 (60.7, 76.5) H6 (75.1, 75.8) H7 (54.5, 106.5) H8 (75.1, 109.0): spread 20.6 x
  32.5 mm, card overhang beyond them left 8.6 / right 15.8 / top 5.7 / bottom 6.0 mm. Tab screws M1 (94.5, 48.5),
  M8 (59.8, 84.0, under the card: fit before the card), M9 (38.7, 70.5), M10 (35.5, 98.6). Unscrewed FETs to nearest
  screw: M2 10.8, M3 17.3, M4 22.6, M5 13.6, M6 11.4, M7 12.1 mm (limit 25). NoHole: M2-M7, no extra screws.

## Schematic, board and WIP build (2026-09-15, after placement)
- NoHole footprint (BOOST:TO-220-3_Horizontal_TabUp_NoHole, pads 1-3 identical to TabUp, drill 1.1, no NPTH)
  set on M2-M7 with setfp.py. Backup of the pre-NoHole schematic: previous/2026-09-15/schematic_before_nohole/.
  ERC 0/0, netcheck 0 failures, netdiff vs BOOST_9-15_caps.net only the six footprints. Netlist BOOST_9-15_nohole.net;
  schematic SHA-256 a1c93a19...
- syncboard: wip_NOT_FOR_FAB/power_sync3.kicad_pcb (124 footprints, parity 0); fpinventory: inv_power3.json (differs
  from inv_power2 only in C30/C7/C55 footprints, C41/C44/C45 added, NoHole FP IDs with identical courtyards).
  p15_b10_k1 scores identically under both inventories.
- run_place.sh (PMODEL_INV=inv_power3.json) -> tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.*: psat placed 77/77.
  Fixes found on the way: (1) placement/fp-lib-table pointed at the old account -> ${KIPRJMOD}-relative (was the cause
  of 17 lib_footprint_issues); (2) net-ties have no courtyard, psat put NT1 on M10's source pin (shorting_items) ->
  pnettie.py puts each tie on its shunt's top pad end (tie pad 2 overlapping the pad end, sense pad 0.575 mm clear);
  (3) psat ignored the tall-part tool radius (C30, 3.1 mm, landed 3.83 mm from M1's screw) -> psat now reads
  tall_tab_mm / tall_standoff_mm from the layout file.
- Result: brief targets 31/49, agreed goals 38/49 (op-amp paths now counted). Every distance recomputed from the
  KiCad board's saved pad centres matches the model to 0.0000 mm (50 rows). Mechanical check 0 messages under D.
- DRC (kicad-cli, shipped BOOST_power.kicad_pro rules, no exclusions): 0 errors; warnings silk_over_copper 20,
  silk_overlap 18, silk_edge_clearance 1; 270 unconnected (no copper). No courtyard, keep-out, clearance or edge
  violations.
- D19 value "TVS_5KP54A" but footprint Diode_SMD:D_SMC: the 5KP series is (to my knowledge) an axial P600 part;
  not verified which part is intended. Raise with the user.

## User review of the placement check-in (2026-09-15 evening): accepted with changes

Decisions: placement p15_b10_k1 accepted as the base for copper; standoffs may sit anywhere in their card
quadrant AND become board-to-case fixings; the 4.0 mm tab-screw clearance is NOT yet accepted (hardware first);
no global re-place; cap-to-rail assignment confirmed optimal by the user over all 1,680 permutations: leave it.

1. Gate loops. New pcheck stage 6: series gate resistor, gate pulldown and the anti-parallel turn-off diode
   within 5 mm of the gate pin (GATE_PARTS table). psat now has 'place_first' (ordered) and 'either_side'.
   Order that won: per channel the rail ceramic (100 nF), then the LX FET's gate parts, then the rail FET's,
   then the 4.7 uF. Before -> after: R60 21.1 -> 5.2, R76 16.4 -> 9.8 (was 4.8 with gate-only priority),
   R70 22.8 -> 4.2 mm. Over 5 mm now: R75 5.3, R23 5.3, R60 5.2, D13 9.7 (M4's diode, the slowest edge).
   Interleaving matters: gate-parts-first gave 59/72 goals but pushed the rail ceramics out to 23.8 mm and
   the ch3 loop to 116.6 mm; ceramics-first gave 55/72; interleaved gives 57/72 with both tight.
2. Standoffs H5-H8 are board-to-case fixings (male-female nylon standoff through the board into a tapped boss,
   ~5.6 mm insulating spacer under the board to clear the 5.57 mm FET gap). pcheck/psa5 already counted them as
   screws, so the 25 mm rule result is unchanged (worst unscrewed FET 22.6 mm). H8 moved (75.1, 109.0) ->
   (85.1, 109.5), the farthest legal point toward the bottom-right corner: corner support 29.7 -> 20.0 mm.
   Corner to nearest fixing now: TL 41.4 (M9), TR notch 10.7 (M1), BR 20.0 (H8), BL 18.3 (M10). No fifth fixing
   fits in the top-left: the nearest legal point is (83.5, 34.0), 53.6 mm from that corner, because L1 covers
   x 30.3-65.1, y 30.3-62.8. M3's body (x 36.4-46.9, y 45.4-63.8) sits under L1 on its 1 mm pad and carries it.
3. Commutation loop: new pcheck stage 7 (report only): M1 drain -> LX drain, rail drain -> nearest loop ceramic,
   and the loop total M1 drain -> LX -> rail -> ceramic -> GND -> M1 source. Now 38.0 / 89.4 / 90.6 mm
   (ch1/ch2/ch3); M1 drain to LX drain 10.9 / 33.1 / 41.9 mm matches the user's own figures. My totals run about
   8 mm longer than the user's ~29/82/82 because the return segment is measured straight-line from the ceramic's
   GND pad to M1's source pad.
4. Tab-screw hardware (decision 1 evidence): Aavid/Boyd 7721-7PPSG TO-220 shoulder washer, PPS 40 % glass:
   shoulder 3.43 mm (HYG180N10 tab hole 3.60), flange 5.46 mm, thickness 1.02 mm, bore 2.95 mm (so a #4-40 or
   M2.5 screw, not M3). Flange radius 2.73 mm and it sits UNDER the board, as does the ~3.3 mm gap spacer, so
   neither touches the top-side keep-out. Top side needs only the screw head (M3 DIN 7985 pan is 6.0 mm -> 3.0 mm
   radius; M2.5 is 5.0 -> 2.5 mm) plus driver shaft. 5.5 mm is still not solvable: p16b (5.5 mm, 17 movable
   parts, 12 seeds) left 4.23 mm of intrusion, and ~180 global runs at 5.5 mm never produced a legal layout.
5. Battery cable: at board level the right strip is blocked by U16 (reaches x 103.7 of 104) and by the lug
   bodies; over U16 there is 21 mm of headroom to the lid (13 mm over the 12.8 mm input cans), so 10 AWG runs
   over U16 from the notch to the lugs. FINDING: J1 (Vin) and J2 (GND) pads are only 9.2 mm apart, and a 10 AWG
   M4 ring terminal is ~10-12 mm across: two opposite-polarity rings would clash. U16 blocks spreading them
   (J2 cannot go above y 73.9, J1 not below ~85.5 because of C74). Raised with the user.
6. Not changed at the user's instruction: input-cap distances, M9 drain -> J7 (24.4 mm), sink op-amp paths.

## Routing rules for step 5 (agreed 2026-09-15)
- In1 and In6 stay continuous under the ENTIRE LX and Vout path: no splits, no single-via chokepoints
  (multiple vias/via arrays at every return transition).
- After routing, estimate the per-channel commutation-loop inductance and re-check ch3 against the simulation,
  which assumed 4.85 / 12.74 / 7.91 nH and gave 68 V at the M1 die.
- Carried over from the brief: sink current nets in the Power class; R1 and sink sense nets in their own narrow
  class, routed as pairs, never joining a pour; via drill >= 0.3 mm; through-hole annular ring >= 0.254 mm;
  0.15 mm minimum track/space so 2 oz outer stays possible; silk 1.0 / 0.15 mm, DRC 0/0 with no exclusions.

## Third review round (2026-09-15 late): loop ceramic, hardware, lugs, TVS, pot, drilling

1. Loop ceramic corrected. Each rail has a 4.7 uF 1210 (C1/C73/C4) and a 100 nF 0805 (C72/C3/C76); the earlier
   "nearest ceramic" rule always picked the 100 nF. Commutating ~25 A in 20 ns moves ~500 nC = 5 V on 100 nF but
   0.1 V on 4.7 uF, so pcheck's COMMUTATION table now names the bulk cap explicitly and the loop closes through
   it; both ceramics are targeted at 6 mm (stage 6). psat 'place_first' per channel: 4.7 uF, 100 nF, LX gate
   parts, rail gate parts. Result: C1 3.8, C72 5.5; C73 8.0, C3 8.9 (MISS); C4 4.8, C76 7.6 (MISS).
   Loops 37.7 / 92.2 / 89.7 mm. ch2 cannot do better: within 6 mm of M3's drain sit L1 (2.29), M9 body (2.36),
   C78 (2.59) and M6 body (2.68).
2. Standoffs H5-H8 ARE board-to-case fixings (user instruction). Stack per fixing, floor upward: tapped M3 boss
   in the floor; nylon M/F standoff 6 mm (nominal 5.57 mm needed; the 1 mm compliant pads take the 0.43 mm);
   board; nylon M/F standoff 22 mm whose male thread passes through the board hole into the lower standoff,
   clamping the board between the two shoulders; M3 nylon screw at the card (H1-H4). 22 mm rather than 20 mm:
   the ESQ/TSW pair sets a 21.21 mm gap, so 22 mm lets the pins insert 0.79 mm less (insertion depth spec
   3.68-6.35 mm) while 20 mm would bottom the connector and bow the card.
   Contingency if they ever revert to board-to-card: the four tab screws alone leave M4 40.0 and M5 29.5 mm from
   a screw, and no fifth tab screw can simply be added - every unscrewed FET's tab-hole position now has parts
   over it (nearest part 0.00 mm), so it would need a local re-place plus the M2.5-hole footprint on that FET.
   M4's tab hole (96.15, 105.65) is the useful one, 13.0 mm from the bottom-right corner.
3. Decision 1 approved at 4.0 mm. Board tab hole shrunk 3.5 -> 2.9 mm (new footprint
   BOOST:TO-220-3_Horizontal_TabUp_M2.5 on M1/M8/M9/M10), giving a 1.05 mm bearing ring under an M2.5 pan head
   instead of 0.75; chosen over adding a washer to avoid another loose part under the board. Gap spacer is
   2.25 mm, not 3.3: the 1.02 mm bushing flange (Aavid 7721-7PPSG) sits in the 3.27 mm board-to-tab gap.
4. Lugs. 12 mm pitch is impossible with U16 on top: the lug pins collide with M7/M4 bodies underneath, and with
   a 12 mm pair placed, U16 has NO legal position anywhere on the board (0.5 mm grid, 4 rotations). 21 mm is
   worse. With U16 moved to the BOTTOM side the 12 mm pitch is legal and the overall miss improves 76.7 -> 68.2
   (p20_s6). U16 on the bottom is now geometrically possible because the stack gives 5.57 mm under the board
   (1 mm pad + 4.57 TO-220) against the TO-263's 4.83 mm: 0.74 mm clearance - but that is tight against 1 mm
   compliant pads and would put a GND tab 0.74 mm from the case floor. User decision pending.
   Strain-relief hole: no room near the lugs. The nearest legal 3.2 mm hole is 36 mm away, and even a 2.5 mm
   hole is 27-34 mm away. Recommend anchoring the cable to the case (boss or P-clip near the penetrator).
5. D19 = 5.0SMDJ54A (user's option B). Bourns 5.0SMDJ datasheet: VRWM 54.0, VBR 60.00-66.30, Vc 87.1 V at
   Ipp 57.5 A, 5 kW - identical to the 5KP54A the user quoted. SMC (DO-214AB) package A 6.60-7.11, B 5.59-6.22,
   C 2.90-3.20 (height), E 7.75-8.13 overall; recommended footprint A (max) 4.69 gap, B (min) 3.07 pad width,
   C (min) 1.53 pad length. KiCad Diode_SMD:D_SMC has a 4.30 mm gap, 3.3 mm pad width, 2.5 mm pad length: inside
   every limit, so the footprint is unchanged. Height 3.20 max on the bottom side leaves 2.37 mm to the floor.
   Stock: Littelfuse C20415356 only 2; R+O C42394451 11,110 at $0.40 (same ratings, Asian brand) as the
   assembly alternate.
6. U26 = MCP4451-103E/ST (10 k), LCSC C145613, 51 in stock. The 5 k TSSOP part (C638705) is 0 in stock, as is
   the 50 k; 100 k has 56. With 10 k the IREF filter time constant is about 3.6 us.
7. Case floor drilling drawing delivered: BOOST_split_boards/case_drilling_2026-09-15/ (svg + html + the
   generator and case_floor_holes.json). Eight blind tapped holes in box coordinates (box = board + 22, -28):
   M2.5 at M1 (116.53, 20.52), M8 (81.77, 55.99), M9 (60.67, 42.49), M10 (57.50, 70.56); M3 at H5 (82.68,
   48.51), H6 (97.07, 47.75), H7 (76.46, 78.46), H8 (107.12, 81.51). These do not move with the lug/U16 choice.

Schematic after this round: D19 5.0SMDJ54A (+MPN/LCSC), U26 MCP4451-103E/ST (+MPN/LCSC, all five units),
M1/M8/M9/M10 -> TO-220-3_Horizontal_TabUp_M2.5. ERC 0/0, netcheck 0 failures, netdiff shows only those six
components, nets 186 unchanged. SHA-256 9e5b4e97...; netlist BOOST_9-15_rev2.net; board power_sync4.kicad_pcb
(124 footprints, parity 0); inventory inv_power4.json. Backup: previous/2026-09-15/schematic_before_review/.
Board rebuilt: brief 53/79, agreed goals 60/79, mechanical 0 messages, DRC 0 errors (44 silk warnings,
270 unconnected).

## Fourth review round (2026-09-16): thermal pad, standoff hardware, lug pads, drilling rev B

1. Lugs (user decision): U16 stays; J1/J2 stay at 9.2 mm pitch with both pads shrunk 8.6 -> 7.0 mm, new footprint
   BOOST:MountingHole_4.3mm_M4_Pad7.0_TopBottom (KiCad MountingHole_4.3mm_M4_Pad_TopBottom with both connect pads
   7 x 7; courtyard unchanged, so placement is unaffected). Copper gap 2.21 mm, annulus 1.35 mm. Cable strain
   relief goes on the case near the penetrator. ERC 0/0 (ERC_9-15_rev3), netcheck 0, netdiff shows only J1/J2;
   netlist BOOST_9-15_rev3.net; board power_sync5 + inv_power5.json; schematic SHA-256 c6d034d6...
   WIP rebuilt: brief 53/79, goals 60/79, mechanical 0, DRC 0 errors (43 silk warnings, 270 unconnected).
   The round-3 schematic was not copied separately (BOOST_9-15_rev2.net records it; the shipped original is in
   previous/2026-09-15/schematic/).
2. Correction (user): the lower standoff must be SHORTER than the FET stack, height = A 4.57 + compressed pad.
   Round 3's 6 mm left 1.43 mm over a 1.0 mm pad, so the pads never touched the floor.
3. Pad: Parker Chomerics THERM-A-GAP G579, 0.050 in (1.27 mm); 9 x 9 in sheet without PSA = 61-05-0909-G579,
   cut about 10 x 16 mm per FET with a 3.0 mm hole at M1/M8/M9/M10.
   Why not Gap Pad 1500: the Henkel TDS (Oct 2020) and PDS_GP_1500_0711 give only E = 310 kPa and impedance at
   10/20/30 % deflection (1.62/1.50/1.33 C-in2/W); no pressure-deflection curve, no deflection limit, no thickness
   tolerance. The TGP 2000/3000/HC3000/5000/HC5000/A2000 TDSs are the same (HC3000: E 110 kPa, 0.57/0.49/0.44).
   Laird Tflex 300 has a curve but no limit and no breakdown rating.
   G579 (THERM-A-GAP catalogue pp. 17-21, 579 column): deflection 22/33/55/68 % at 5/10/25/50 psi (ASTM C165 MOD,
   0.125 in "G" sample, 0.50 in probe, 0.025 in/min); "typical deflection range is approximately 5-40%";
   thickness tolerance +/-10 % at 2.5 mm or less; 3 W/m-K; 0.7 C-in2/W at 10 psi, 0.040 in, "G" only;
   200 Vac/mil; -55 to 200 C; UL 94 V-0; Shore 00 30. The curve is for a 3.2 mm sample: a 1.27 mm pad under a
   10 x 15.6 mm tab is more constrained, so the pressures below are lower bounds.
4. Tolerance per FET: body A +/-0.10 (user allowance; the HYG180N10 drawing gives no tolerance on A); pad
   thickness +/-10 %; board bow at the IPC-6012 0.75 % limit as c^2 / 2R with R = 86 / (8 x 0.0075) = 1433 mm and
   c = FET body centre to the nearest fixing: M3 17.3 mm -> 0.10, M4 0.07, M5 0.06, M7 0.05, M6 0.05, M2 0.04,
   screwed FETs 0.01. Options (board underside; nominal strain; worst case; RSS at M3):
   A 0.040 in at 5.37 (0.37 mm shim, not a stock part): 21.3 %; -9.8..46.7 %; 5.0..37.5 % - loses contact.
   B 0.050 in at 5.50 (5.0 mm stud + one 0.5 mm washer): 26.8 %; 0.7..48.1 %; 13.2..40.3 % - always touching.
   C 0.020 in at 5.00 (user's alternative): 15.4 %; -38.8..59.6 % - the +/-0.1 body allowance alone is +/-20 %.
   Chosen: B. Nominal ~7 psi (50 kPa), ~8 N per FET on the 3.2 mm curve; worst case 48 % ~20 psi, ~22 N.
   Thermal: 0.7 C-in2/W at 1.0 mm (datasheet); ~0.83 at 1.27 mm (estimate: + 0.25 mm / 3 W/m-K) = 3.4 K/W over
   156 mm2. Gap Pad 1500 1.0 mm at 20 %: 1.50 C-in2/W = 6.2 K/W.
   Correction (user, 2026-09-16): use about 6 W for M1, not 4.85. The LTspice model has no temperature dependence,
   so M1's conduction loss rises from 3.0 W to about 4.2 W when warm. That puts about 21-22 K across the pad
   (Gap Pad 1500 would have been about 37 K). The other FETs dissipate less on the same pad: M1 sets the limit.
   Scripts: tools/mech/fetfix.py (placement p15_b10_k2_st) then tools/mech/pad_stack.py.
5. Standoff hardware, per H5-H8, floor upward. Hand-tight only, no tools on nylon threads.
   - Essentra HTSN-M3-5-3: nylon 6/6 hex male-male, L 5, hex 6 AF, 6 mm M3 thread each end. Bottom stud into the
     floor (hex seats on the floor), top stud through the washer and the board.
   - TR Fastenings TR NWE-34815-M3: nylon 66 washer, ID 3.2 +0.18/0, OD 7.0 +0/-0.36, thickness 0.50 +/-0.05.
   - Power board (3.2 mm NPTH).
   - Essentra HNSM3-20-5.5-1: hex female-female, L 20, hex 5.5 AF, 10 mm thread depth each end; catalogue says
     black nylon 6 25 % glass filled, DigiKey lists it natural nylon - check on receipt. Screws onto the stud:
     6 - 0.5 - 1.6 = 3.9 mm engaged, clamping the board between the stud hex (via the washer) and the F/F face.
   - 3 x TR NWE-34815-M3 (1.50 mm) on top of the F/F; control card; M3 x 8 nylon pan head, 8 - 1.6 - 1.5 = 4.9 mm
     engaged.
   Why not male-female below and above: Essentra's 5 mm M/F (HTSN-M3-5-5.5-2) has an 8 mm male and only 3 mm of
   female thread (catalogue P2 = 3), so the upper standoff's 8 mm male would bottom before clamping, and its own
   8 mm male needs 8.5 mm of thread in a 10 mm floor. Keystone nylon M/F (25501-25506: hex 5.0, male 8.0, female
   8.0) starts at 10 mm. Essentra's 20 mm M/F with an 8 mm hex (HTSN-M3-20-8-2) does not fit (H6: 3.78 mm to J10).
   Hex fit, nearest courtyard top/bottom: H5 4.45/4.27, H6 3.78/3.51, H7 4.05/4.05, H8 5.51/5.83 mm. Across-corner
   radius: stud hex 3.46, washer 3.50, F/F hex 3.18. Tightest is H6 bottom against M2 (body edge 0.25 mm further).
   Card gap 21.50: the ESQ/TSW pair seats fully at 21.21; the TSW post (5.84) is inserted 5.55 (ESQ 3.68-6.35).
   Round 3's 22 mm M/F is withdrawn: neither Keystone nor Essentra makes it in nylon, and it left 0.05 mm to the lid.
   Not published: Essentra length tolerance on either part. At assembly, measure stud hex + washer on all four
   (target 5.50 +/-0.10) before fitting the board.
   Tab screws M1/M8/M9/M10: M2.5 x 12 pan head; the head sits at 7.10, so 4.9 mm goes into the floor. Tighten only
   until the head seats: the board/spacer/bushing/tab column rests on the compliant pad, so torque pulls the board
   down and over-compresses those four pads.
6. Stack, floor upward: pad 0.93 compressed; board underside 5.50, top 7.10; card underside 28.60, top 30.20;
   SOIC top 31.95; lid margin 1.05 (round 3: 0.05). Output cans top 23.90, 4.70 under the card. L1 top 26.10 max.
   ESQ-44 tails 2.53 above the floor. D19 (SMC, 3.20 max) 2.30 above the floor. Against round 3 (6.0 + 22): board
   0.50 lower, card-top parts 1.00 lower. Against the original 5.57 budget: board 0.07 lower.
7. Drilling drawing rev B (positions unchanged): tap depth "5 mm minimum" -> M3 7.0 / M2.5 6.0 mm full thread,
   drill 8.5 mm max, bottoming tap, light countersink. Rev A was also clipped (hole table after row 2, notes off
   the right edge) and had overlapping labels; fixed and checked (95 text boxes, none overlapping or outside).
   Rev A: previous/2026-09-16/case_drilling_2026-09-15/. Artifact republished (version 2).
8. APPROVED by the user 2026-09-16: THERM-A-GAP G579 0.050 in (1.27 mm) at a 5.50 mm board height, and the
   M/M + F/F standoff stack in item 5. User's M1 thermal budget: about 78 C at 25 C water, about 118-125 C with
   every conservative assumption stacked; the 1.27 mm pad costs about 2 C over 1.0 mm.

## Step 5: power copper (2026-09-16), check-in at copper v9

Folder `BOOST_split_boards/route_2026-09-16/` (README there has the pipeline). Board
`BOOST_power_route_v9_NOT_FOR_FAB.kicad_pcb` on the accepted placement p15_b10_k2; check-in page
`BOOST_split_boards/copper_review_2026-09-16/` (artifact https://claude.ai/artifact/CsWJraE5Vq7Vkfb1vU2LdR).

- Copper is zones (rect unions per net per layer, priorities) plus through-via fields with unused annuli removed;
  no tracks yet. Every zone connects to pads solidly (no thermal reliefs). Builder adds fields, KiCad DRC flags
  illegal vias, they are blacklisted by position and the board rebuilt until DRC is clean.
- v9 facts: DRC 0 errors on the saved file (43 silk warnings from placement), 149 unconnected (signals plus
  low-current power pins: J10 sense pins, regulator inputs, driver VSS/bootstrap parts, R14); 702 vias, drills
  0.3 (2) / 0.4 / 0.5 mm; In1/In6 GND only and no LX on In3/In5 (tools/layer_checks.py); netlist rev3 parity 0.
- Layer use: In2 = LX (L1 -> M1/M7, west to M6 with a loop round M6's pin row, two paths to M5) + Vin/rsense_lo
  corners; In3/In5 = Vin (J1 north to R1), rsense_lo, Vout_1 -> J3, Vout_2 -> J8, Vout_3 -> J5, GND fill;
  F.Cu = input loop pads, LX strip beside M1/M7, banks, shunt links, GND fill; B.Cu = D19-M1, LX under M5/M6,
  Vout under M2/M3/M4, LED drain runs, rsense_lo above U19, lug pads; In4 empty (5 V plane in step 6).
- Rules (WIP project copy only, `route_2026-09-16/rules/`): Sense netclass (ISNS_P/N, SNS_CH1-3; 0.2/0.2,
  via 0.6/0.3); Net-(M8/M9/M10-S) into Power; .kicad_dru tightening only: every via drill >= 0.30, high-current
  vias >= 0.40, Power tracks >= 0.5, high-current tracks >= 1.0 mm. Shipped BOOST_power.kicad_pro unchanged.
- Stackups (JLCPCB 8L 1.6 mm, no impedance requirement; gsuberland/jlcpcb_autogenerated_stackups):
  B 0.035/0.030x6/0.035, gaps 0.109/0.25/0.218/0.25/0.218/0.25/0.109; C 0.070 outer, gaps 0.203/0.2/0.138/...
  JLCPCB's inner "1 oz" is 0.030 mm finished, not 0.035.
- Solver (tools/solve_copper.py): raster 0.1 mm (0.05 shunt links, 0.2 GND), 20 um barrels, THT pins x20,
  SuperLU (MMD_AT_PLUS_A), co-area necks averaged over 5 bands, IPC-2221 k 0.048/0.024, via rating 0.97 A at
  0.4 mm scaled by drill^0.725. Validated: strip within 0.5 %, via current exact, known 1x1 mm neck 55.8 C vs
  53.4 C expected (unsmoothed bands read 78.8 C, so v1/v2 figures before the fix were biased high).
  Vin split into J1 -> R1 DC (18.4 A) and caps -> R1 ripple (9.5 A); the audit's all-sources-at-1 V model makes
  C69 supply everything.
- v9 results, neck C (length mm) / worst via:
  1 oz: Vin DC 23.9 (11) / 1.46x (4 over); rsense_lo 19.6 / 1.34x (9 over); LX L1->M1 52.4 (1.3); L1->M6 35.5 (0.3);
  L1->M5 58.1 (1.2); L1->M7 19.6; GND M1 19.1 / 1.14x; GND ch3 1.02x; everything else under 18 C and 1.0x.
  2 oz: Vin DC 23.7 (10) / 1.39x (5 over, R1.1 field NE column); rsense_lo 16.5 / 1.22x (6 over, L1.2 and R1.4
  fields); LX L1->M1 24.4 (1.1), L1->M6 22.2 (1.7), L1->M5 26.9 (1.3) - long-neck values 15.2 / 16.1 / 20.9;
  everything else under 18 C and 1.0x. Rule result: C (2 oz outer / 1 oz inner).
- Loop inductance, copper only (tools/loop_inductance.py): coupled over-plane model ch1/ch2/ch3 0.70/1.13/1.98 nH
  (1 oz stack), 0.75/1.23/1.71 (2 oz); audit's method (mu0 x 0.221 mm x squares, four legs) 0.74/1.24/1.67 nH;
  the simulations used 4.85/12.74/7.91 nH. For the sim side's M1 turn-off re-check.
- Found and fixed on the way: C86's GND/Vout vias walled In2 LX between L1 and M1; GND via walls (U16 tab,
  C85.2) across the inner Vin column; LX via fields perforating that column; via fields placed under other nets'
  pads on the opposite side (re-netted by KiCad, then pruned, which had stripped ceramic GND vias); C4/C76 (ch3
  ceramics) were isolated from M4.2 by J1's pad, M4.3 and an equal-priority Vin zone.
- Tried and rejected: 0.6 mm drills on field edges (larger barrels draw more, crowding worse); no-pour baffle NE
  of R1.1 (made a 3.7 mm Vin neck, 76 C); moving C69.2 GND vias and an F.Cu GND field south of M1's washer
  (Vin neck and M1 return worse).
- Open with the user (page): copper weight C; FET-pin throats at 2 oz (accept by long-neck value, or allow small
  LX islands on In3/In5 at M1.2/M5.2/M6.2); via crowding at R1/L1.2 (move U19 ~4 mm west, or accept up to 1.4x);
  Vin on In4 in the north-east corner; solid pad connections need preheat for hand soldering.

### User decisions on the step-5 check-in (2026-09-16)

1. Copper weight **B (1 oz outer / 1 oz inner)**. Reason (user): IPC-2221 models a long conductor cooling into air;
   every failure here is a 1-2 mm throat conducting into wide copper, or copper/vias 0.1-0.2 mm from a solid
   plane. On the solver's widths/shares/lengths the real local rise is under 1 C (M5 throat ~0.5, M1 ~0.3,
   M6 ~0.2, Vin 11 mm neck ~0.6), and a 0.4 mm barrel at 1.6 A rises under 0.1 C; 2 oz only takes total copper
   loss from 1.00 to 0.89 W and does not improve loop inductance. **Keep reporting IPC figures, but they are not
   pass/fail for necks shorter than about 5 mm or for vias in plane-connected fields.** Stackup B written into
   `route_2026-09-16/base_p15.kicad_pcb` and the v9 board (tools/set_stackup.py; KiCad round-trip checked,
   board thickness 1.654 mm, copper finish left "None" - not decided). DRC unchanged (0 errors).
2. FET-pin throats: accepted. No LX islands on In3/In5.
3. Via crowding at R1 / L1.2: accepted as solved. U19 stays.
4. In4 stays a single 5 V plane (no Vin on In4).
5. Solid zone connections kept; soldering instructions added to the new `BOOST_split_boards/BUILD_NOTES.md`
   (preheat from below to 100-120 C, 80-100 W iron with >= 3 mm chisel and flux for TO-220 pins and J1/J2 cable
   joints, FET body held flat - M2.5 screw and spacer as jig on M1/M8/M9/M10 - FET removal will be difficult),
   together with the pad, tab-screw and stand-off hardware and the assembly order.
6. Loop inductance: with 0.7/1.2/1.7 nH copper the FET leads dominate, so M1's overshoot can only come in below
   the simulated 68 V; the M1 turn-off re-check is confirmation, not a blocker. If run, add the LX copper's
   capacitance to GND. Parallel-plate estimate on v9 (stack B, no fringing): In2 LX 1392 mm2 -> In1 (0.25 mm core,
   er 4.23) 209 pF + -> In3 pours (0.218 mm prepreg, er 4.16; GND fill, Vin, Vout - all AC ground) 235 pF;
   F.Cu LX 235 mm2 -> In1 (0.109 mm) 79 pF; B.Cu LX 237 mm2 -> In6 80 pF; total about 600 pF.
Next: handoff step 6, signal routing.

## Step 6: signal routing (2026-09-16), hand-back at v13
- Board `route_2026-09-16/BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb` (SHA-256 f5ed9a175c17d733...), report
  `route_2026-09-16/ROUTING_REPORT_2026-09-16.md`.
  - v11 (v9 copper + In4 5 V plane + R1 sense channel) + 1697 tracks (1658 mm) + 168 vias (127 x 0.6/0.3,
    41 x 0.8/0.4; 45 centred in SMD pads).
  - Saved-file DRC: 0 errors / 0 unconnected / 0 exclusions; 43 silk warnings, the same as v11.
  - Layer checks, planes, islands and netlist parity (rev3) all pass.
- Router `route_2026-09-16/tools/route_signals.py` (0.1 mm grid Dijkstra), pipeline `tools/route_pipeline.sh`.
  - Repair: rip-up (nearest nets, then ghost-path corridor) and re-export/re-route rounds until DRC is clean.
  - Current protection: `solve_copper.py --jmap` on v11. Tracks may not cut another net's copper above
    0.25 A/mm; vias above 2.0 A/mm are refused; below the limits crossings cost more with current. A connection
    nothing else routes may cross hotter copper (logged).
- Rejected v12 (`work/rejected_v12/`): routed without the current map; DRC-clean, but Vout_1 M2->J3 LED neck
  177 C at 0.20 mm and Vout_1 bank via 1.44x.
- v13 vs v11 at 1 oz:
  - Vin J1->R1: 23.6 -> 38.5 C (10.0 -> 5.3 mm wide, neck 3.6 mm long).
  - rsense_lo: 20.0 -> 59.0 C (9.5 -> 4.9 mm, 2.5 mm long); vias 1.34 -> 1.53x.
  - Vout_3 M4->J5 LED: 1.1 -> 13.7 C (0.93 mm throat, 0.9 mm long).
  - GND returns +16-37 % R; copper loss 0.896 -> 0.975 W; loop L 0.73/1.20/2.04 nH (was 0.70/1.13/1.98).
- Decisions put to the user (report section 6):
  1. R1 path versus U19/U25 escapes: accept / escape channels in the power copper / placement.
  2. Vout_3 LED throat at U6: accept / keep the corridor free and re-route.
  3. Gate return paths not beside the gate tracks; rail-side gates 30-35 mm.
  4. Rail/Gate fallback widths: analog_5V 114 mm and 12V 55 mm at 0.4 mm; GATE_M4 30 mm at 0.3 mm.
- Tooling notes:
  - `solve_copper.py` needs `--workers 2` or 3 when other programs hold memory (8 workers broke the pool
    with about 4 GB free).
  - KiCad reports clearance "Local override 0.2 mm" on some pads that have no local clearance in the file
    (not explained; router margins cover it).

## Delivery cautions
- 2026-09-15: lock files ~BOOST_power.kicad_pcb.lck / ~BOOST_control.kicad_pcb.lck (and .kicad_pro.lck) exist in
  BOOST_split_boards: the shipped boards may be open in KiCad. Ask the user to close them before replacing files.
- Boards need a project fp-lib-table (BOOST, CSCF3218-6R8MC) or DRC warns lib_footprint_issues on L1, R1 and the 16.5 mm cans.

## Tools
- LTspice 24.0.12: C:/Users/Dominick Junior/AppData/Local/Programs/ADI/LTspice/LTspice.exe (netlists cp1252); KiCad 10.0.6 kicad-cli + python.exe (no matplotlib; anaconda python has it).

## Check-in 2 (2026-09-14)
- R13/R23/R47 = 220 ohm. Nominal sim s220: margin min 40.8 / median 46.3 ns; M1 die 68.0 V, TVS 38.3 mW, M1 4.85 W,
  reverse into rail drains 1.34 A, no avalanche, LEDs 2.631/2.368/2.368 A. Corner s220lv: 18.3 ns min.
- Tab screws: M1, M8, M9, M10; 15 mm rule for unscrewed FETs (body centre to nearest screw); unscrewed may drop the hole.
  1 mm compliant pad under tabs -> board underside ~5.6 mm above floor. Board-to-tab gap at the hole = A - A1 = 3.27 mm.
- Card gap 16.13: ESQ-115-23-G-D + TSW-115-07-G-D. VERIFIED from Samtec drawings (octopart copies, F-218 / F-219):
  TSW straight: A = tail, B = overall, C = post; insulator 2.54; -07 A 2.54 / B 10.92 / C 5.84; hole 1.02 +/- 0.03; 0.64 sq.
  ESQ: A = tail, B = height; -23 A 4.83 B 13.59; -33 A 2.29 B 16.13; -44 A 4.57 B 18.67; -13 A 7.36 B 11.05;
  insertion depth 3.68-6.35; 5.7 A/pin with TSW; tail 0.64 sq. Mated gap = ESQ B + 2.54 (post 5.84 seats fully).
  Gaps: 13.59 (-12/-13) 16.13 (-23) 18.67 (-33) 21.21 (-44). Card top parts max ~1.75 (SOIC) + J9 RA 2.54.
- 2026-09-15 user decision: 21.21 mm. ESQ-115-44-G-D on the power board (tail 4.57 -> 2.97 below board, 2.6 above floor),
  TSW-115-07-G-D under the card (tail 0.94 above card top). Card over cans OK, not over L1 (Codaca CSCF3218 32 x 22.5 x 19.0).
  J9 RA on the card underside at the board's left edge. Stack 5.57 + 1.6 + 21.21 + 1.6 + 1.75 = 31.7.
  Evidence for dropping 16.13: optimizer with card-over-low-parts never removed overlaps (cost 5510, 18/44 targets);
  over-cans run reached zero overlap. Hand analysis: L1 + 9 cans cluster ~60 x 55 leaves <= 31 mm strips.
- Chirality: L1 pads 12 mm apart on one edge; LX at local x -6. rsense_lo toward the lugs (top-right) forces L1 pads-down
  at the top or pads-right at the left. Stage 4 (3 caps <= 15 mm per rail) conflicts with Stage 2 when rails sit in one row.
- Case: board x 52-126 box = pcb x + 22, y - 28. Penetrator (118.5, 3.5) box = pcb (96.5, 31.5), Ø15 keep-out;
  notch pcb x 86-104, y 30-42. LED box x 0-50 y 40-90 (left of board, pcb y 68-118). Arduino box y 11-40 (pcb y 39-68).

## Step 6 second pass (2026-09-17)
- Driver bypass caps moved to the driver pins (placement only, 10 caps); 3 Vout_1 vias moved 0.6 mm to clear C51.
  Board `route_2026-09-16/BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb`, report `ROUTING_REPORT_2026-09-17.md`.
- UCC21520 (SLUSCJ9F): VCCI pin 8 is internally shorted to pin 3; VDDx quiescent 1.0 mA typ / 2.5 max per channel,
  VCCI 1.4 / 2.0 mA. INA241A (SBOSA30D) IQ 2.5 / 3.0 mA (3.2 over temperature). MCP6241 (DS21882D) 50 / 70 uA.
  12V on the power board ~9 mA typ / 21 mA max, analog_5V ~2.7 / 3.2 mA; the control-card load is not on this board.
- KiCad gotcha: building a board from router output can silently move a track or via to another net (a GND stub
  inside the Vout_1 bank came back as Vout_1). `tools/add_routes.py` now restores the routed net and prints it;
  `tools/net_flips.py` checks a saved board against the router output.
- DRC applies a 0.2 mm clearance to pads that carry a footprint-level override (J10's through-hole pads, U10's NC
  pads), so the router keeps 0.2 mm from every pad.

## Step 6 frozen (2026-09-17, v16)
- Gate loops are hand-routed through chosen corridors: `GATE_GUIDES` in `route_signals.py` holds the polylines,
  the router lays legal copper inside them (return first for M2, drive first for M3). Loop area is measured in
  plan view by `gate_paths.py`; a vertically stacked pair (M3: drive In3, return F) scores 0 % "beside" but has a
  small loop, so read the area, not the share.
- M9's washer keep-out (3.75 mm at 38.67, 70.49) blocks any pair passing south of M3; the Vout_2 vias beside M3
  are flashed on F and In5 only, so In3 threads between their holes (0.93 mm gaps).
- Order matters near U15: the VDDA pin-row link has to come after the gate loops (`LATE_EDGES`), or it takes the
  space M7's pair needs (M7 beside 73 % -> 9 %).

## Step 7 control card (2026-09-17)
- Card screw accepted: Wurth Elektronik 97790803211 (WA-SCRW M3 x 8 nylon 66 pan head, UL94 V-0), head 2.1 +/- 0.2,
  dia 5.5 +/- 0.3, rated -30..+85 C (the user expects 55-75 C in-case air; it only holds the card). Stack budget:
  card top 30.20, head top 32.30 -> lid margin 0.70 nominal, 0.50 at max head, about 0.2 with 3 washers +0.05 each
  and a card 10 % thick. Datasheet rev 001.002 2022-04-28 (read online).
- J9 -> soldered wire pads (user decision): BOOST:WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots, 11 PTH (drill
  1.0, pad 2.0) in two staggered columns 2.54 apart, 1.27 step (block 4.5 x 14.7 mm), two NPTH 2.8 x 1.4 tie slots
  (3.0 in the first draft; shortened so J9's courtyard clears J11's), origin at (51.065, 95.90) on the card.
  Schematic backup previous/2026-09-17/schematic_before_j9_wirepads/ (rev3 SHA c6d034d6...); new sch SHA 33f6fc85...;
  netlist BOOST_9-17_rev4.net; ERC_9-17_rev4 0/0 (same four ignored checks); netdiff vs rev3 only J9's footprint;
  netcheck 0 failures; control_sync4 parity 0 (CONTROL), frozen v16 parity 0 (POWER) against rev4.
- Why the wire pads: a 1x11 RA plug hung ~2.75 mm below the card, 0.05 mm short of the 2 mm vent rule over the
  cans, in a stack whose standoff tolerances are unpublished; an extra washer pushed the screw heads into the lid;
  the only legal connector (JST GH) faced the east wall. See card_2026-09-17/CARD_CHECKIN_1_2026-09-17.md.
- The schematic lock ~BOOST.kicad_sch.lck dates from 2026-09-02; three edits on 09-15 went through it, so it is stale.
- Placement c2 (2026-09-18), card_2026-09-17/CARD_CHECKIN_2_2026-09-18.md:
  - Placer config work/place_c2_cfg.json. Its terms:
    - near: D27 at U104.1, R105 at D27, and R101/R100/R77 within 6 mm of J9;
    - apart (pins): comparator inputs 10 mm from U104/U105/I2C, 8 mm from M1_ON, 4 mm from logic-edge pins;
    - apart_seg: MST route proxy, Current at least 8 mm from I2C, M1_ON and the 74HC14 outputs;
    - C49/C64/C67 underside only;
    - weights V_err 15 and U2 In+ 15.
  - Lessons:
    - Pin distances alone missed an I2C span crossing 1.9 mm from the Current stub, hence apart_seg.
    - Polishing at low temperature cannot move SOICs across the card: V_err stayed at 61 mm until fresh global
      runs.
    - The random legalizer could not seat a SOIC at about 55 % fill; a whole-card "shove" that may cover passives
      fixed it.
  - Result:
    - v16 overlay 13/13; DRC 0 errors (27 silk warnings); 68 top / 92 underside.
    - Current 2.8 / 3.0 mm; V_err 4.0 mm HPWL; U2 In+ 11.2 mm (open with the user).
    - Five decaps under their IC on the other side; U101's cap at 4.4 mm.
  - The DRC needs work/fp-lib-table (BOOST library); without it KiCad reports lib_footprint_issues for J9.
