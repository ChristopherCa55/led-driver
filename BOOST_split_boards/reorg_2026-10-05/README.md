# Schematic reorganization for the reviewer (2026-10-05)

**The trigger:** a reviewer declined to review until the schematic was cleaned up. He also found only one PCB, and did
not know what to look at in the SPICE file.

**The user's choices:**
- work on a copy;
- I restructure and the user tidies;
- keep the project layout, but give each board project its own (sub-)schematic;
- organize LTspice first, then make KiCad match it (the same parts in the same areas).

**Result:** `../../BOOST_reorg_2026-10-05/`, a copy of BOOST_stuff. The three original folders are unchanged
(sch c9f30e24, power e3e92c26, card 5df474e9, asc 6492c5d0).

## What changed in the copy

**KiCad:**
- `BOOST.kicad_sch` is now a system root: two sheet symbols, notes and a title block (root uuid kept).
- `BOOST_power_RC2.kicad_sch` and `BOOST_control_RC2.kicad_sch` are the board sheets, A2. They are also each board
  project's own schematic: KiCad 10 `top_level_sheets` in the board `.kicad_pro` now points at them.
- **Symbols:** every symbol keeps its uuid and fields. Its instance data carries project "BOOST"
  (`/<root>/<sheet>`) and its board project (`/<board file uuid>`).
- **Blocks:** 23 titled, dashed boxes, from `work/blocks.json`.
- **Wires:**
  - Wires between blocks, and wiring spanning more than 50.8 mm, became global labels.
  - GND cut points got power:GND symbols.
  - 3 unnamed nets got names: `Net-(U102B-A)` -> `U102B_A`, `Net-(U102C-A)` -> `U102C_A`, `Net-(U103A-A)` -> `U103A_A`.

**PCBs** (metadata only; gerbers and drills byte-identical apart from the date lines):
- 36 power and 14 card footprints that had no symbol link got their link (`path` = the symbol uuid).
- Every footprint's sheetfile now names its board schematic.
- The schematic fields were synced as KiCad's Update PCB would (resolved `${VALUE}`), and 13 BOM flags were fixed.
- The 3 nets were renamed.
- Tool: `tools/pcb_link.py`.

**LTspice:** `BOOST.asc` was re-laid out in the same blocks.
- The power board is on the left and the control card on the right; the SIM_* test bench and all directives are at
  the bottom.
- Labels use the same names as in KiCad (`work/lt_netnames.json`).
- The note "I added a lot of capacitors ... all put here" was dropped, because each cap now sits in its IC's block.

**Docs:** README (schematics table, how to open, ERC/DRC, the LTspice layout and what to plot), `BOOST_schematic.pdf`
(3 pages), and `TIDY_GUIDE.md` (for the user; delete before sending).

## Checks (on a fresh copy of the finished folder)
- **KiCad netlists against the original:**
  - system: 293 parts and 186 nets, 0 differences (values, footprints, fields, pin partition);
  - the power project alone: 127 / 74, 0 differences;
  - the card project alone: 166 / 133, 0 differences.
- **ERC:**
  - system 0; power alone 0;
  - card alone 2 "power input not driven" on U18 VDD/VSS. The card is supplied through J11. A PWR_FLAG there clashes
    with U17 in the system ERC, so it was left out; no exclusions.
- **DRC with native schematic parity** (now possible because each board has its own schematic):
  - power: 49 warnings (as before), 0 unconnected, 0 parity;
  - card: 1 warning, 0 unconnected, 0 parity.
- **LTspice** `-netlist`: 302 parts, 0 nets differing (`tools/ltnet_compare.py`); directives unchanged.
- `syncboard.py`: logo only, as always.

## Tools (`tools/`)
- **Readers:**
  - `ksch.py`: the KiCad reader. Pin transform: rotate by -angle, then mirror; all 1048 pins verified.
  - `check_kgeom.py`: checks `ksch.py`'s connectivity against KiCad's netlist (865 pins, 0 differences).
  - `knet.py`: the KiCad 10 netlist parser.
- **Blocks and names:**
  - `blocks.py`: block seeds and overrides (shared by both schematics).
  - `netnames.py`: shared names (`kname()`; LTspice nets matched to KiCad nets by the parts on them).
- **Re-layout:**
  - `relayout_core.py`: a per-net Steiner tree per block; edges in exactly one block's tree are kept. Labels are kept
    if they are reachable within 25.4 mm. Points are split per block, and islands are shelf-packed.
  - `relayout_asc.py` and `relayout_kicad.py`: the two adapters. The block rows are the same in both; the KiCad
    connector blocks sit at the row ends.
- **Projects and PCBs:** `fix_projects.py` and `pcb_link.py`.
- **Render and compare:**
  - `render_asc.py`: renders an `.asc` with its own .asy graphics.
  - `svg_shot.py`: screenshots KiCad SVGs with headless Edge.
  - `net_compare.py` and `ltnet_compare.py`.
- `ascgeo.py` is a copy with the **M90 fix**: rotate first, then mirror. The old order left R8/R34/R42 floating.
