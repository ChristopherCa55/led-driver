# BOM, cost and cost-saving review (2026-09-30 / 10-01)

The user asked for three things:
- a cost review ("ways to make it cheaper, cheaper parts that do the same thing");
- the BOOST_package BOM updated (the card PCB price was stale);
- a `.xlsx` BOM.

**Delivered to `BOOST_package/`** (old copies in `previous/2026-10-01/before_bom_update/`):
- `BOOST_power_BOM_JLC.csv` and `BOOST_power_CPL_JLC.csv`: D28-D30 added and R47 at its new position. The card
  BOM/CPL came out byte-identical and were left alone.
- `SOURCING_TABLE.md`, `COST_SUMMARY.md` (with "Ways to save") and `ORDER_CHECKLIST.md`.
- `BUILD_NOTES.md`: the card's 6-layer line was added.
- `BOOST_BOM.xlsx`, new. It has six sheets: Summary, Power board, Control card, Bought elsewhere, Fees and Ways to
  save. Quantities and costs are live formulas. Checked in Excel through COM: no formula errors, and the total is
  $699.68, matching COST_SUMMARY.

**Recipe** (system Python, run from this folder):
1. `"C:/Program Files/KiCad/10.0/bin/python.exe" tools/parts_from_boards.py work/boards/BOOST_power_RC2.kicad_pcb work/boards/BOOST_control_RC2.kicad_pcb bom/parts_from_boards.json`
   - Run it on copies: KiCad writes `.kicad_prl` files beside any board it opens.
   - Then `kicad-cli pcb export pos ... --side both --use-drill-file-origin` -> `bom/*_pos_all.csv`.
2. `python tools/jlc_parts.py snapshot bom/jlc_snapshot_2026-09-30.json <codes>`. This is JLC's public parts search
   API; it answers plain Python requests.
3. `python tools/build_bom.py`, then `python tools/cost_summary.py` (which execs `tools/savings.py`), then
   `python tools/make_xlsx.py BOOST_BOM.xlsx`.
4. `ORDER_CHECKLIST.md` is written by hand.

**Findings:**
- **EEH-ZU1H221P (C6843593) is short:** 14 in stock, 18 needed.
- Proposed fix: EEH-ZS1H221P (C385885) on the six lightly loaded positions.
  - Panasonic ZS datasheet: 220 uF, 50 V, 13 mOhm, 3.7 A at 100 kHz / 125 C. The ZU part is 10 mOhm and 5.2 A.
  - The 50 V row was read by text position.
- JLC quotes, 2026-10-01, for 5 boards:
  - power board, 8 layers: $124.10;
  - card panel, 6 layers: $73.57; with 0.5 oz inner copper $56.83; with TG135 as well $53.40;
  - card, 5 single 6-layer boards: $68.78;
  - power board at 6 layers: $69.57.
- JLC fees: set-up $25.56 per side ($51.12 for both sides), stencil $8.21 / $16.42. Neither board can go to one-sided
  assembly.
- The candidate-part snapshot is `bom/jlc_candidates_2026-10-01.json`. Search results are in `work/search/`.
- The capacitor datasheets read are under the session's tool-results:
  - Panasonic ZS: read;
  - Lelon HBZ: the 220 uF / 10 x 16.5 row is not in the PDF;
  - Rubycon PJV: the PDF is encrypted and could not be read.

## 2026-10-01, second round (the user's approvals)

**Applied** (cleanup folder, BOOST_package, BOOST_stuff; backups in `previous/2026-10-01/before_cost_changes/`):
- **220 uF caps:** EEH-ZS1H221P (C385885) on C70/C71/C75/C77/C78/C88; EEH-ZU1H221P stays on C74/C86/C87.
  - Applied with `tools/apply_caps.py`: KiCad MPN fields, and LTspice Rser 13 mOhm on those six.
- **Card inner copper 0.5 oz:**
  - Stackup set by `../card05oz_2026-10-01/set_stackup_05oz.py` (JLC 6-layer 1 / 0.5 oz, 1.5468 mm).
  - Card fab outputs regenerated in `../fab_2026-09-30/`; the fab drawing gained a 0.5 oz branch, and the power
    drawing was verified unchanged.
  - The STEP was rebuilt in `../assembly_3d_2026-09-30/` (card screws 0.75 mm and U18/U28 1.09 mm under the lid).
  - Gerber layers and drills are unchanged; only the job file differs.
- **Op-amps:** TLV9001IDBVR (C398363) for the 9 MCP6241 per set.
  - Applied with `tools/apply_opamps.py`: KiCad Value + MPN + Sim.Library, LTspice values and model; TLV9001.lib
    replaces MCP6241.lib.
  - The board files' Fab-layer value text was updated too.
  - The model `TLV9001.lib` is behavioural, in the MCP6241.lib style.
  - Simulations in `sim_2026-10-01/`: 30 ms full power (`cmp_*`), 25 % PWM (`d25_*`) and cold start to 140 ms
    (`cold_*`, stopped there) all match the MCP6241 within 0.05 %. The 10 % runs were stopped unrun.
- **Checks:** ERC 0; both boards DRC 0/0 with schematic parity 0.
- **BOM:**
  - short descriptions (`tools/descriptions.py`);
  - snapshot `bom/jlc_snapshot_2026-10-01.json`;
  - savings APPLIED/OPEN lists (`tools/savings.py`);
  - total $663.24.

**Kept after a search:**
- comparators MCP6561;
- digital pot MCP4451-103;
- L78L05.

**Open, the user's choice:** the 12 V regulator U16.
- Candidates: UTC LM2940G-12-AA3-R (C127023) or TI LM2940IMPX-12 (C2866640), both SOT-223.
- `tools/swap_u16_sot223.py` is tested on a copy (`work/u16/`). The existing Vin and 12 V vias land in pads 1 and
  3, and the DRC is identical.
- Loads (`sim_2026-10-01/loads_r`): 12 V rail 16 mA average (+ about 0.1 A for the Arduino buck, not modelled), 5 V
  8 mA, analog_5V 3 mA.
- Heat at 18 V in, with an assumed 50 C air and 40-60 C/W:
  - Arduino on 12 V: 0.9-1.2 W, junction 87-123 C;
  - Arduino on Vin: 0.3-0.5 W, 61-78 C.
- 12 V dropout simulations (`drop_*`, regulator off 15-25 ms):
  - it always shuts down cleanly (U21 at 9.8 V);
  - with the Arduino on Vin, the restart reaches LX 62 V at 16.8 V and 82.2 V / 10 mJ TVS at 18 V;
  - with the Arduino on 12 V, the restart is a cold start.
- Arduino on Vin needs:
  - a 1206 PTC (for example TECHFUSE nSMD020-60V C50766766, or a 0.35 A part);
  - a new net to J10.19, tapped near the via at (82.05, 82.35);
  - cutting the 26 mm 12 V branch at D9. The Vin 1.0 mm track rule rules out simply re-labelling the branch.

## 2026-10-01, U16 in TO-263: cheaper options (the user asked; nothing applied)
Same footprint and pinout as the LM2940S-12 (1 IN, 2 + tab GND, 3 OUT), searched in the JLC parts library
(`work/search/q263*`). Temperatures use the U16 thermal model (`../u16_thermal_2026-10-01/`; 75 C air, 18 V, h = 10).
- **onsemi MC7812BD2TR4G** (C231294, $0.53, 2024 in stock): saves $8.10 per order. onsemi MC7800 data sheet: 35 V
  input, -40 to +125 C (B), bias current 3.4 typ / 8 mA max, R_jc 5 K/W. Dropout is not guaranteed; figure 14
  gives about 1.6 V at 200 mA and 25 C, 1.3-1.4 V hot. U21 stops M1 at a 9.77 V rail (worst case about 10.7 V with
  the L78L05 +4 %, 1 % resistors and 10 mV offset), so the LEDs stop at about 11.3 V battery typical and about
  12.3 V worst case (LDO: about 10.0 / 11.0 V). Tj 115 C at 120 mA (LM2940S: 117 C).
- **Microchip MIC2940A-12WU-TR** (C632742, $2.60, 10 in stock): saves $3.96. Micrel data sheet M9999-102705
  (2005; the LCSC copy is encrypted): 26 V operating, -20 V / +60 V, Tj -40 to +125 C, dropout 0.32 V max at
  250 mA, ground current 6 mA max at 250 mA, R_jc 2 K/W, needs >= 10 uF tantalum or aluminium on the output (C30 is
  47 uF tantalum). Tj 109 C at 120 mA.
- Rejected: ST L4940D2T12 (17 V maximum operating input); XBLW XBL29150S-12 (no data sheet on JLC/LCSC); LM2941 and
  TLE4276/NCV4276 (5-pin); LM1085/LM1084 (tab is OUT); L7912/MC7912/LM2990 (negative regulators).

## 2026-10-01, U16 = MC7812BD2TR4G applied (the user's choice after the low-battery simulation)
- Design files changed by `../mc7812_lowbatt_2026-10-01/tools/apply_u16_mc7812.py` in all three folders (backups in
  `previous/2026-10-01/before_u16_mc7812/`). ERC clean; DRC and parity unchanged; every gerber layer identical.
- BOM tooling: `build_bom.py` U16 line (C231294; alternates C38744, C2877347), `descriptions.py`, `cost_summary.py`
  (PTC and buck text; C2877347 out of LIMITED), `savings.py` (APPLIED $8.10; the regulator OPEN items removed; kept
  list rewritten). C231294 and C38744 were added to `bom/jlc_snapshot_2026-10-01.json` (`_added` key).
  `work/boards/` now holds the current shipped boards; `parts_from_boards.json` and the pos files were re-exported
  (only values differ). Before-copies are in `work/before_u16/`.
- To BOOST_package: power BOM (only the U16 line differs; CPL unchanged), SOURCING_TABLE.md, COST_SUMMARY.md,
  BOOST_BOM.xlsx (Excel check: no formula errors, total $655.14), ORDER_CHECKLIST.md and BUILD_NOTES.md (by hand).

## 2026-10-02: the 6-layer power board

- **The tools:**
  - `cost_summary.py`: the power PCB is $69.57, 6 layers, JLC061611-7628D.
  - `savings.py`: "Power board: 6 layers instead of 8" is now APPLIED, saving $54.53, and it was removed from the
    rejected list.
  - `make_xlsx.py`: the power description and the summary line.
- **Re-run** on the final boards (power e3e92c26, card 5df474e9):
  - the BOM is unchanged;
  - the CPL changed only at R70 (55.0252 -> 54.7125 mm).
- **Totals:**
  - the power board order is $274.36;
  - the overall total is **$600.61** (it was $655.14);
  - with the G579 pad, $702.45.
- **The workbook**, checked in Excel through COM: total $600.61, and no formula errors. The two "#" hits are the A1
  header text.
- **Copied to BOOST_package:** the power CPL, COST_SUMMARY.md and BOOST_BOM.xlsx.
- The previous outputs are in `work/before_power6/`.
