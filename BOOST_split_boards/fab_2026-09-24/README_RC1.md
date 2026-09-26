# BOOST fabrication and assembly package, release candidate 1 (2026-09-24)

Both boards, ready for your review. They are **release candidates, still NOT_FOR_FAB**, because two small board
changes are waiting for your yes (see "Waiting for you" below). Everything here was generated from the candidate
boards, and one command regenerates it from whichever boards you release.

| Board | Board file (with its .kicad_pro / .kicad_dru) | What it is |
|---|---|---|
| Power | `../route_2026-09-16/BOOST_power_route_v18_CANDIDATE_NOT_FOR_FAB.kicad_pcb` | v17 plus 7 via nudges (0.02-0.24 mm) and 1.05 mm J10 holes |
| Control card | `../card_route_2026-09-22/BOOST_control_route_c3_rc_CANDIDATE_NOT_FOR_FAB.kicad_pcb` | the accepted c3 board plus 1.05 mm J11 holes |

`../route_2026-09-16/BOOST_power_route_v17_NOT_FOR_FAB.kicad_pcb` is the frozen v16 plus the MOSFET silk (silk only).
`../card_route_2026-09-22/BOOST_control_route_c3_NOT_FOR_FAB.kicad_pcb` is the accepted card, byte-identical to the
board you checked.

## Contents

| Path | What |
|---|---|
| `BOOST_power_RC1/BOOST_power_RC1_gerbers.zip`, `BOOST_control_RC1/BOOST_control_RC1_gerbers.zip` | **Upload these.** 8 copper layers, mask, paste, silk, Edge.Cuts (Protel extensions), Excellon drills (PTH and NPTH separate; J9's two NPTH slots as G85 routes), drill maps, Gerber job file |
| `*/..._fab_drawing.pdf` (+ .png) | Fab drawing: dimensioned outline, every hole by drill size, stackup, drill table, fabrication notes. Note 1: **all vias epoxy filled and copper capped** |
| `*/checks/` | KiCad DRC of the plotted file (json + report), drill report, PDF drill maps, IPC-D-356 netlist |
| `bom/SOURCING_TABLE.md` (+ .csv) | Every BOM line: refs, value, footprint, side, LCSC part, Basic/Extended, stock, price, how many sets the stock covers, and why that part |
| `bom/BOOST_*_BOM_JLC.csv`, `bom/BOOST_*_CPL_JLC.csv` | JLC BOM and pick-and-place: the decided JLC parts only |
| `bom/BOOST_*_BOM_JLC_with_proposals.csv`, `..._CPL_JLC_with_proposals.csv` | the same plus my proposals for the undecided lines |
| `bom/jlc_snapshot_2026-09-24.json` | the stock and prices as read from JLC's parts library that day |
| `tools/` | `fab_facts.py`, `make_fab.sh`, `fab_drawing.py`, `build_bom.py`, `set_drill.py` |

Regenerate after a change: `sh tools/make_fab.sh BOARD.kicad_pcb OUTDIR NAME`, then
`"<KiCad python>" tools/fab_facts.py OUTDIR/.src/NAME.kicad_pcb work/<power|card>_facts.json`,
`python tools/fab_drawing.py power|card`, and `python tools/build_bom.py` (after a new `kicad-cli pcb export pos`).
`make_fab.sh` refuses to plot unless KiCad DRC on the saved file shows 0 errors and 0 unconnected.

## Board facts (measured from the plotted files)

| | Power | Control card |
|---|---|---|
| Size | 74.0 x 86.0 mm (notched 18 x 12 corner) | 45.0 x 45.0 mm |
| Layers / thickness | 8 / 1.6 mm (stackup 1.654 copper + dielectric) | 8 / 1.6 mm |
| Copper | 1 oz outer, 1 oz inner | 1 oz outer, 1 oz inner |
| Min track / space | 0.20 / 0.20 mm | 0.15 / 0.20 mm |
| Vias | 868: 0.30/0.60 x122, 0.40/0.80 x628, 0.50/0.90 x118 | 393: 0.30/0.50 |
| Vias in pads | 476 touch a pad (454 with the centre in the pad) | 188 touch a pad (150 with the centre in the pad) |
| Min drill | 0.30 mm (vias); pad holes 1.05 (J10), 1.10 (TO-220), 2.00, 4.30 | 0.30 (vias); pad holes 1.00 (J9), 1.05 (J11) |
| Non-plated | 4 x 3.20 (standoffs), 4 x 2.90 (tab screws) | 4 x 3.20, 2 slots 2.80 x 1.40 (J9 tie) |
| Filled via to nearest pad hole | 0.48 mm (JLC asks > 0.45 for filled via-in-pad) | 0.87 mm |
| KiCad DRC | 0 errors, 0 unconnected; warnings: 2 silk overlaps (can outlines touching), 1 library mismatch (J10's new drill) | 0 errors, 0 unconnected; 1 library mismatch (J11's new drill) |

## JLCPCB order settings (checked on the quote page, 2026-09-24)

| Option | Setting |
|---|---|
| Base material / layers | FR-4, 8 |
| Thickness | 1.6 mm |
| Material type | FR4 TG155 (the stackup in the board files is Nan Ya NP-155F) |
| Surface finish | **ENIG** (JLC does not offer HASL at 6+ layers) |
| Outer / inner copper | 1 oz / **1 oz** (inner defaults to 0.5 oz: change it) |
| Specify stackup | No (the default 8-layer build is the one in the drawing) |
| **Via covering** | **Epoxy Filled & Capped** (the default at 8 layers, $0.00) |
| Min via hole / diameter | 0.3 mm / (0.4 / 0.45 mm) |
| Mark on PCB | Remove Mark |
| Electrical test | Flying probe, full |
| Delivery (card, if JLC assembles it) | **Panel by JLCPCB**: standard assembly needs at least 70 x 70 mm |

**Filled and capped vias: included, at no charge.** On the 2026-09-24 quote at 8 layers, "Epoxy Filled & Capped" is the
default selection and adds $0.00. By comparison, "Copper paste Filled & Capped" added $336.09. JLC's own
announcement says via-in-pad on 6-20 layer boards is upgraded to plated-over filled vias (POFV) for free. It lists a
hole range of 0.2-0.5 mm, and every via here is 0.30-0.50 mm.

Quotes, 5 bare boards, 10-11 day build, before $29.45 DHL shipping:
- **Power board: $124.10.** $90.00 base, $17.30 ENIG, $16.80 1 oz inner, $0.00 via covering.
- **Control card: $123.42.** $90.00 base, $16.80 ENIG, $16.62 1 oz inner, $0.00 via covering.

## Assembly at JLCPCB (estimate)

Both boards need **Standard PCBA**: Economic handles 2/4/6-layer, single-sided boards only. These rates come from
JLC's price help page; the parts use JLC's quantity-1 prices, before attrition spares.
- Setup $51.12 and stencil $16.42 per design (double-sided).
- Feeder loading **$1.53 per unique part**, Basic or Extended: in Standard PCBA the Basic/Extended split does not
  change the loading fee.
- $0.0016 per solder joint.

| 2 boards of each, JLC-fit lines plus my proposals | Power | Card |
|---|---|---|
| Unique parts (Extended / Basic) | 27 (15 / 12) | 41 (16 / 25) |
| Feeder loading | $41.31, of which Extended $22.95 | $62.73, of which Extended $24.48 |
| Setup + stencil | $67.54 | $67.54 |
| Solder joints | $0.89 | $1.51 |
| Parts (2 boards) | $111.66 | $29.64 |
| **Assembly total** | **about $221** | **about $161**, plus the panel for the card |

Parts on the power board are dominated by the nine 220 uF cans ($25.50) and three 680 uF cans ($7.62) per board.

## Waiting for you

1. **Power board v18 (a copper change on the frozen board).** Setting the netclass priorities made KiCad enforce the
   Power class's 0.25 mm. Before that fix, KiCad had been checking Power nets at 0.20 mm. Under 0.25 mm, v16/v17 fail
   in 3 places, 0.008-0.014 mm short: two Vout_1 vias next to U15 and one Vin via next to U19.
   - v18 moves those 3 vias by 0.02-0.03 mm.
   - It also moves 4 Vin vias beside J1's lug hole outward by 0.08-0.24 mm, to meet JLC's 0.45 mm rule for filled
     vias near plated holes.
   - It sets J10's holes to the 1.05 mm you asked for on 2026-09-15. That answer was never applied.
   - DRC: 0 errors, 0 unconnected; parity 0; layer and plane checks unchanged.
2. **Card: J11 holes to 1.05 mm** (same 2026-09-15 answer). Everything else on the card is byte-for-byte the board you
   accepted, and all its checks are unchanged.
3. **Sourcing decisions:** see `bom/SOURCING_TABLE.md` "Unresolved". In short:
   - no diode or PNP type was ever chosen in the schematic;
   - 5 ohm 0805 is not stocked;
   - the LED shunts R7/R52/R53 need a TCR choice;
   - R1 is out of stock.
4. Stock limits: 2 power boards (EEH-ZU1H221P 19, LM2940S-12 2), 3 (EEH-ZU1E681UP 10), 4 sets (MCP6241 38).
