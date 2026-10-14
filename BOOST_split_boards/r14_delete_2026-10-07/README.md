# R14 deleted from the design (2026-10-07)

**Request (the user's words):** "delete the footprint for the 1meg resistor - delete it on ltspice, kicad schematic,
and kicad pcb", in BOOST_stuff, BOOST_package and BOOST_schematic_cleanup, with backups and every derived file
regenerated.

**Why it could go.** R14 was 1 MOhm from LX to GND. It did nothing useful:
- LX never floats: it is always tied to Vin through L1.
- 1 MOhm is far too high to damp the ringing on LX.
- It cannot discharge the outputs, because the back-to-back FETs and the pre-charge diodes block that direction.

Its only effect was about 14 uA of battery drain.

**Backups:** `../previous/2026-10-07/before_r14_delete/<folder>/`, a full copy of all three folders.

## What changed

**KiCad schematic** (`tools/delete_r14.py`), sha `1b18ea2a`:
- the R14 symbol;
- the GND symbol on its pin 2;
- the junction dot at its LX pin.

The netlist loses only R14 (from nets LX and GND); ERC is 0 / 0.

**Power PCB**, sha `6babee4a`:
- footprint R14;
- the copper that existed only for it: the 1 mm F.Cu stub, a via, 7 B.Cu segments, and the via into the In2 LX pour;
- zones refilled.

DRC: 0 errors, 0 unconnected, the same 49 warnings. Parity: the logo only, as always. The `.kicad_pro` is unchanged.

**LTspice** `BOOST.asc` (`tools/delete_r14_asc.py`), sha `3a85b069`:
- R14 and its ground flag removed, 4 lines; nothing else in the file was touched.
- `ltspice_equiv.py` passes, with R14 listed in `approved_changes.json` "removed_elements".

**Gerbers and fab drawing** (`../fab_2026-10-07/`):
- 9 of the 15 gerber layers and the drill file changed: copper F, B and In1-In4, the front mask, paste and silk.
- 972 vias (was 974; two 0.40/0.80 removed). Every other fab fact is unchanged.
- zip `ff3c1290`, PDF `396fdc86`.

**BOM, CPL and costs** (`../bom_2026-09-30/`, build_bom.py's R14 line removed):
- the power BOM and CPL lose only the R14 line;
- power assembly $204.79 -> $203.17 (one fewer unique part to load);
- total **$600.61 -> $598.99** with the McMaster pad;
- both workbooks were checked in Excel: 0 formula errors, total $598.99;
- `ORDER_CHECKLIST.md` and `JLC_SELECTIONS.md` updated to the new totals and via count.

**3D model** (`../assembly_3d_2026-09-30/`):
- `BOOST_assembly_2026-10-07.step` (`189b2e57`) replaces the 10-02 one in the three folders.
- The geometry differs only by R14. All 67 clearance rows are identical.

**Not changed:** `BOOST_reorg_2026-10-05/` (still has R14; the user left it out) and the BOOST-github master.
