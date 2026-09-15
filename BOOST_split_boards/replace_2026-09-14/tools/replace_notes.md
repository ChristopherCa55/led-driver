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
