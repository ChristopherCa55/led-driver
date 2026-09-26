# BOOST fabrication and assembly package, release candidate 2 (2026-09-24, updated 2026-09-25)

**RC2 is the package for scenario A** (chosen 2026-09-25): 5 bare PCBs of each board, 2 complete sets assembled by
JLCPCB. What to order, option by option, is in `ORDER_CHECKLIST.md`; the money is in `COST_SUMMARY.md`.

**Schematic rev6 is written into `BOOST-github/BOOST/BOOST.kicad_sch` (2026-09-25).** Rev5 is backed up in
`../previous/2026-09-25/schematic_rev5/`. RC2's boards and BOM use the rev6 values, and all of
its checks pass against the prepared rev6 copy (below). The board files keep their `_NOT_FOR_FAB` names in the
working folders; the release copies are in `../FINAL_2026-09-25/`.

| Board | Source (with its .kicad_pro / .kicad_dru) | What it is |
|---|---|---|
| Power | `../route_2026-09-16/BOOST_power_route_v19_NOT_FOR_FAB.kicad_pcb` | v18 plus the rev6 values in the Fab fields: R1 1m, U25 INA241A4xD, R21/R48/R60/R72 5.1 |
| Control card | `../card_route_2026-09-22/BOOST_control_route_c3b_NOT_FOR_FAB.kicad_pcb` | the accepted c3 board plus 1.05 mm J11 holes |

Change history:
- v17 is the frozen v16 plus the MOSFET silk.
- v18 adds 7 via nudges, J10 drilled 1.05 mm, and 4 J1 vias moved to meet JLC's 0.45 mm filled-via rule. You
  approved it on 2026-09-24.
- v19 adds the values only. `board_diff.py` shows just the six Fab fields; no footprint moved, rotated or changed
  pads.

## Contents

| Path | What |
|---|---|
| `BOOST_power_RC2/BOOST_power_RC2_gerbers.zip`, `BOOST_control_RC2/BOOST_control_RC2_gerbers.zip` | **Upload these.** 8 copper layers, mask, paste, silk, Edge.Cuts (Protel extensions); Excellon drills with PTH and NPTH separate (J9's two NPTH slots as G85 routes); drill maps; Gerber job file |
| `BOOST_*_RC2/..._fab_drawing.pdf` (+ .png) | Fab drawing: dimensioned outline, every hole by drill size, stackup, copper weights, thickness, minimum track/space/drill, notes. Note 1: **every via epoxy filled and copper capped** |
| `BOOST_*_RC2/checks/` | KiCad DRC of the plotted file (json + report), drill report, PDF drill maps, IPC-D-356 netlist |
| `BOOST_*_RC2/.src/` | the exact board files that were plotted (DRC-gated copies of the sources above) |
| `bom/BOOST_power_BOM_JLC.csv`, `bom/BOOST_power_CPL_JLC.csv` | **Power board BOM and pick-and-place for JLC** (27 unique parts, 97 placements) |
| `bom/BOOST_control_BOM_JLC.csv`, `bom/BOOST_control_CPL_JLC.csv` | **Card BOM and pick-and-place for JLC** (41 unique parts, 160 placements) |
| `bom/SOURCING_TABLE.md` (+ .csv) | every BOM line: refs, value, footprint, side, LCSC part, Basic/Extended, stock, price, why that part; the parts you fit |
| `bom/jlc_stock_2026-09-25.json` | stock and prices read from JLC's parts library on 2026-09-25 (all 61 lines covered for 2 sets) |
| `COST_SUMMARY.md` | scenario A costs: PCBs, assembly, parts elsewhere, hardware, the thermal-pad options, your buck's requirements |
| `ORDER_CHECKLIST.md` | one page: the two JLC orders, every option, what to buy elsewhere, the stock to re-check |
| `cost/` | `cost_summary.json`, `pad_options.txt`, the dropped scenario-B files (kept, not developed) |
| `tools/` | `make_fab.sh`, `fab_facts.py`, `fab_drawing.py`, `build_bom.py`, `set_drill.py`, `cost_summary.py`, `pad_options.py`, `hole_isolation.py` (copper around the mounting holes) |
| `BOOST_*_RC1/`, `README_RC1.md` | the superseded RC1 package, kept for reference |

The `*_with_proposals` BOM/CPL files are identical to the plain ones now that every part is decided.

Regenerate after a change:
1. `sh tools/make_fab.sh BOARD.kicad_pcb OUTDIR NAME`. It refuses to plot unless KiCad DRC on the saved file shows 0
   errors and 0 unconnected.
2. `"<KiCad python>" tools/fab_facts.py OUTDIR/.src/NAME.kicad_pcb work/<power|card>_facts.json`
3. `python tools/fab_drawing.py power|card`
4. After a new `kicad-cli pcb export pos`: `python tools/build_bom.py`, then `python tools/cost_summary.py`.

## Board facts (measured from the plotted RC2 files)

| | Power | Control card |
|---|---|---|
| Size | 74.0 x 86.0 mm (notched 18 x 12 corner) | 45.0 x 45.0 mm, ordered on a 70 x 70 mm carrier |
| Layers / thickness | 8 / 1.6 mm (stackup 1.654 copper + dielectric) | 8 / 1.6 mm |
| Copper | 1 oz outer, 1 oz inner | 1 oz outer, 1 oz inner |
| Min track / space | 0.20 / 0.20 mm | 0.15 / 0.20 mm |
| Vias | 868: 0.30/0.60 x122, 0.40/0.80 x628, 0.50/0.90 x118 | 393: 0.30/0.50 |
| Vias in pads | 476 | 188 |
| Plated holes | 1.05 (J10) x30, 1.10 (TO-220) x30, 2.00 x6, 4.30 (lugs) x2 | 1.00 (J9) x11, 1.05 (J11) x30 |
| Non-plated | 4 x 3.20 (standoffs), 4 x 2.90 (tab screws) | 4 x 3.20, 2 slots 2.80 x 1.40 (J9 tie) |
| Filled via to nearest plated hole | 0.481 mm (JLC asks > 0.45 for filled via-in-pad) | 0.866 mm |
| KiCad DRC | 0 errors, 0 unconnected; 3 warnings: 2 silk overlaps (can outlines touching), 1 library mismatch (J10's 1.05 mm drill) | 0 errors, 0 unconnected; 1 warning: library mismatch (J11's 1.05 mm drill) |

## Rev6 checks (2026-09-25, against the prepared copy `../rev6_prep_2026-09-24/BOOST/`)

| Check | Result |
|---|---|
| ERC (`ERC_9-24_rev6.rpt`) | 0 errors, 0 warnings; the report is identical to rev5's apart from its timestamp |
| Netdiff rev5 -> rev6 | 290 -> 290 components, 186 -> 186 nets, no pin changes. Six value changes: R1 2m -> 1m, U25 INA241A3xD -> INA241A4xD, R21/R48/R60/R72 5 -> 5.1. Footprints unchanged |
| Parity (`syncboard.py --check`) | power v19: 124 footprints, 0 failures; card c3b: 166 footprints, 0 failures |
| Footprints v18 -> v19 | 124 = 124, none moved, rotated, flipped or re-footprinted; every pad identical; only the six values differ |
| DRC (RC2) | as in the table above |

Rev6 facts:
- **0.1 V/A is unchanged**: 1 mOhm x 100 V/V against 2 mOhm x 50 V/V.
- **Same pinout and package**: TI SBOSA30D gives one SOIC-8 pinout for every gain, and 1.1 MHz for every gain.
- **Same land pattern**: Bourns' CSS4J-4026 series drawing; the R version is 2.70 mm tall against the K version's 2.93.
- **Orderable**: stock on 2026-09-25 is 116 for the INA241A4IDR and 385 for the CSS4J-4026R-1L00F.

## JLCPCB order settings

Both boards, on the quote page (2026-09-24). Step by step in `ORDER_CHECKLIST.md`.

| Option | Setting |
|---|---|
| Base material / layers | FR-4, 8 |
| Dimensions | power 74 x 86 mm; card 45 x 45 mm with **Panel by JLCPCB**: 1 column x 1 row, rails on four sides, 12.5 mm wide (70 x 70 mm panel) |
| Quantity | 5 (power: 5 boards; card: 5 panels = 5 cards) |
| Thickness | 1.6 mm |
| Material type | FR4 TG155 |
| Surface finish | **ENIG** (JLC offers no HASL at 6+ layers) |
| Outer / inner copper | 1 oz / **1 oz** (inner defaults to 0.5 oz: change it) |
| Specify stackup | No (the default 8-layer build is the one in the drawing) |
| **Via covering** | **Epoxy Filled & Capped** (the default at 8 layers, $0.00) |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Mark on PCB | Remove Mark |
| Electrical test | Flying Probe Fully Test |
| PCB Assembly | on: Standard, both sides, quantity 2 |

**Filled and capped vias are included, at no charge.** On the 2026-09-24 quote at 8 layers:
- "Epoxy Filled & Capped" is the default selection and adds $0.00.
- "Copper paste Filled & Capped" added $336.09, for comparison.
- JLC's own announcement says via-in-pad on 6-20 layer boards is upgraded to plated-over filled vias (POFV) for free,
  for holes of 0.2-0.5 mm. Every via here is 0.30-0.50 mm.

Prices for 5 bare boards, 10-11 day build, before shipping:
- **power $124.10**;
- **card $137.04** on the carrier panel ($123.42 as single boards, which JLC will not assemble).

Assembly of 2 of each: power $225.42, card $167.31. **Scenario A grand total $760.83** with the McMaster 1272N32
pad, or $862.67 with the 0.060 in G579. Shipping and tax are not included. Every hardware price is now read,
except two Farnell UK prices converted from GBP. See COST_SUMMARY.md and ORDER_CHECKLIST.md (final, 2026-09-25).
