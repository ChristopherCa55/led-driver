# Board sheets from the v3 schematic (2026-10-09)

The user asked for a power-board and a control-card schematic, each holding only that board's part of the main
schematic, made by the same rules. Their choice: the main schematic becomes the root of two board sheets.

`work/` is a copy of `BOOST_stuff/KiCad` (v3 = sch 11504e31). Nothing shipped is touched. Rebuild: `python tools/build.py`;
check: `python tools/check.py`.

## What changed in work/
- `BOOST.kicad_sch`: the root (same uuid). Two sheet symbols and a short note.
- `BOOST_power_RC2.kicad_sch`, `BOOST_control_RC2.kicad_sch`: each board's parts at their v3 positions, D paper.
  - Parts go by the board assignment; GND symbols, PWR_FLAGs, labels, junctions and no-connect marks go with their wire.
  - 9 wires joined parts of both boards (Vout_n, Outputn_drain, IREFn_input). Each was cut half way, on the grid, and
    both ends got that net's global label. No net was renamed.
  - Notes go with the part nearest their text. Titles go to every board with 2+ parts under them, within 55 mm.
- Projects: each board `.kicad_pro` names its own sheet (`top_level_sheets` uuid); `BOOST.kicad_pro` lists both sheets.
- PCBs (metadata only, gerbers identical): every footprint links to its board sheet (36 power and 14 card links
  added), fields synced as Update PCB would (144 / 39), BOM flags on H1-H8, J1, J2, NT1-NT3. U104 Sim.Params is set to
  unit E's text: U104's units disagree on that KiCad-simulation field and KiCad compares unit E.

## Checks (tools/check.py)
- Netlists against the shipped single sheet: system 292 parts / 186 nets, power 126 / 74, card 166 / 133. 0 differences.
- ERC: system 0, power 0, card alone 2 (`power_pin_not_driven`, U18 VDD/VSS: the card gets 5V/GND only through J11).
  PWR_FLAGs on the card would clear those but put 2 errors into the system ERC (flag vs U17's output, two flags on
  GND). Not added; no exclusions.
- DRC with schematic parity: power 49 warnings (as shipped), card 1 (as shipped), 0 unconnected, parity 0 on both.
- Text: no new collisions (the same leftovers as v3).

## 2026-10-10: shipped
- The user re-arranged both sheets (saved state kept in `old/user_saved_2026-10-09/`); all checks still pass.
- Root page (`tools/root_page.py`): filled boxes with a short contents list each and "double-click to open".
- Gate simulation fields (`tools/set_gate_sim.py`, user's OK): every 74HC00 / 74HC14 gate unit, spares included, now
  carries the LTspice v7 values (the old KiCad values were the pre-retune LTspice ones). LTspice's 74HC14 numbers match
  Nexperia 74HC_HCT14 Rev. 10 typicals at 5 V: switching points 2.63 / 1.56 V, about 12 ns delay, 7 ns edges, about
  41 ohm output. The card PCB fields were synced (DRC parity 0).
- Copied to BOOST_stuff, BOOST_package and BOOST_schematic_cleanup (8 files each: root, 2 sheets, 3 .kicad_pro,
  2 .kicad_pcb). Backup (user: only the package): `../previous/2026-10-10/before_board_sheets/`. The three READMEs
  got the new schematic and ERC lines. tools/check.py passes in all three folders.

## 2026-10-10 (later): one main schematic again
The user found that "Switch to PCB Editor" from the system project asks for a new PCB: KiCad 10 allows one board per
project, so it looks for BOOST.kicad_pcb. The user's choice: one main schematic again, plus the board schematics.
- `BOOST.kicad_sch` = the v3 single page again (11504e31), with the gate simulation fields set like the board sheets
  (`tools/flat_main.py`, which builds `work_flat/`). `BOOST.kicad_pro` lists the main page only.
- `BOOST_power_RC2.kicad_sch` / `BOOST_control_RC2.kicad_sch` stay the board projects' own schematics (the user's
  arrangement); their "BOOST" instance entries were removed (508). The PCBs and board projects are unchanged.
- Every part is now drawn twice. `tools/sync_check.py DIR` checks that the main page and the board sheets agree (board,
  symbol, fields, flags); `tools/check.py DIR` checks the netlists, ERC, DRC parity and gerbers.
- Shipped to all three folders (4 files); backup (package only): `../previous/2026-10-10/before_flat_main/`.
  All checks pass in all three folders; the READMEs were updated.

## 2026-10-10 (late): card PWR_FLAGs
- My flag group (tools/add_card_flags.py, right of J11) reached all three folders through a command the user stopped
  part-way (it had copied the file and edited the READMEs; only the checks were cut off). The user did not like the
  spot and placed the flags themselves in BOOST_schematic_cleanup (card f57cae74, wired onto J11's 5V/GND lines),
  and had also re-arranged the power sheet there (88faea82, power .kicad_pro 16d4c3f9 = KiCad save metadata).
- Those three files were copied to BOOST_stuff and BOOST_package; backups of what they replaced:
  `../previous/2026-10-10/before_card_pwr_flags/` (first) and `../previous/2026-10-10/before_user_flags/`.
- All three folders: ERC 0 for the main schematic and both board projects; netlists same; sync_check 0; DRC parity 0;
  gerbers identical.
