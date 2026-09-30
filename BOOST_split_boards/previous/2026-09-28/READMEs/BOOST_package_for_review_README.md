# BOOST LED driver: final package (2026-09-26, reorganised 2026-09-27)

Everything needed to build, order and simulate the BOOST LED driver, in one folder: `KiCad/`, `LTspice/`, and the documents, 3D model and fabrication files at the top level. Status: schematic rev6, boards RC2 (release) with your silkscreen logos (added 2026-09-27), build scenario A (5 bare PCBs of each board, 2 assembled by JLCPCB).

**Before ordering, regenerate the gerbers, fab drawings and 3D model.** The `*_gerbers.zip` files, the fab drawings and the 3D model at this level were made on 2026-09-24/25, before the logos. Uploading these zips as they are gives boards without the logos.

The documents, gerbers and 3D model are copies from the working project. The KiCad boards here are newer than the working copies: they carry the logos.

## What is here

| File | What it is | Open with |
|---|---|---|
| `KiCad/BOOST.kicad_pro`, `KiCad/BOOST.kicad_sch` | **The schematic** (rev6). Open the `.kicad_pro` | KiCad 10 |
| `KiCad/BOOST_power_RC2.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | **Power board**: 74 x 86 mm, 8 layers, with 9 silkscreen logos | KiCad 10: open its `.kicad_pro`, or the `.kicad_pcb` in the PCB editor |
| `KiCad/BOOST_control_RC2.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | **Control card**: 45 x 45 mm, 8 layers, with 2 silkscreen logos | KiCad 10, as above |
| `KiCad/BOOST.pretty/`, `KiCad/CSCF3218-6R8MC.pretty/`, `KiCad/ltspice.kicad_sym`, `KiCad/fp-lib-table`, `KiCad/sym-lib-table` | The project's own footprint and symbol libraries. The two tables use project-relative paths, so the schematic and both boards find them in `KiCad/` | used by KiCad automatically |
| `BOOST_power_RC2_gerbers.zip`, `BOOST_control_RC2_gerbers.zip` | Gerbers and drill files for JLCPCB, **made before the logos: regenerate before ordering** | JLCPCB, or KiCad's GerbView |
| `BOOST_power_RC2_fab_drawing.pdf`, `BOOST_control_RC2_fab_drawing.pdf` | Fab drawings: outline, holes, stackup, copper, notes (all vias epoxy filled and capped) | any PDF reader |
| `BOOST_power_BOM_JLC.csv`, `BOOST_power_CPL_JLC.csv`, `BOOST_control_BOM_JLC.csv`, `BOOST_control_CPL_JLC.csv` | **JLC BOM and pick-and-place** for each board | upload to JLCPCB; any spreadsheet |
| `SOURCING_TABLE.md` | **The BOM**: every part with its refs, value, footprint, LCSC number, stock, price and why it was chosen, plus the parts you fit yourself | any Markdown viewer or text editor |
| `ORDER_CHECKLIST.md` | **What to order and how**: both JLC orders option by option, everything bought elsewhere, the stock to re-check. Total $760.83 (without shipping and tax) | Markdown viewer |
| `COST_SUMMARY.md` | Where every dollar comes from, the thermal-pad comparison, and the buck converter's requirements | Markdown viewer |
| `BUILD_NOTES.md` | **How to build it**: parts you fit, MOSFET orientation, soldering, the case stack, the J9 wiring, the order of work, and the tab-to-case check before power-up | Markdown viewer |
| `case_floor_drilling.html` / `.svg` | Case-floor drilling drawing, rev B (hole positions and tapping) | web browser; print at 100 % for a 1:1 template |
| `BOOST_assembly_2026-09-25.step` | **3D model** of both boards in the case, with all hardware, names and colours | FreeCAD or CAD Assistant (free), or any CAD program |
| `BOOST_assembly_2026-09-25_3D.pdf` | The same model as a 3D PDF | **Adobe Acrobat Reader**: click the model to activate it. Edge and Chrome do not show 3D content |
| `BOOST_assembly_2026-09-25.stl` | The same model as one mesh (boards, parts, fixings, case floor) | Windows 3D Builder / 3D Viewer, PrusaSlicer, Blender |
| `CLEARANCES.md` | Clearances measured in the 3D model (lid, standoffs, screwdriver access, vents). Optional reference; delete it if you do not need it | Markdown viewer |
| `LTspice/` | The LTspice simulation (see below) | LTspice |

## Notes on the copies

- **The documents came from the working project**, and some of their path references still point there. For example
  `bom/BOOST_power_BOM_JLC.csv`, `BOOST_power_RC2/...` and `fab_2026-09-24/...`. The files they name that matter are
  all in this folder under the same file names. The analysis files they mention (pad options, simulation reports,
  status pages) were left out on purpose.
- **The 3D model** still shows the original Essentra floor stud. The final stud (set screw plus a 4.5 mm aluminium
  spacer) is slimmer, so no clearance gets worse.
- **KiCad 3D models:** the boards' parts use KiCad's standard 3D library (`${KICAD10_3DMODEL_DIR}`), which comes with
  KiCad.
- **The board projects:** each board has its own `.kicad_pro`, which carries its net classes and design rules.
  Always open a board through (or beside) its own `.kicad_pro`; without it, DRC falls back to defaults.
- **Checked from `KiCad/`** (2026-09-27, after the logos): ERC gives 0 errors and 0 warnings. DRC on both boards gives
  0 errors and 0 unconnected.
  - The warnings: the two can-outline silk overlaps on the power board, and the J10/J11 1.05 mm drills differing
    from their library footprints on purpose.
  - Also 46 silk-over-copper warnings on the power board, where a top logo under L1 runs over L1's middle
    (mechanical) pad. The logo is hidden under L1 anyway, and you accepted that. The gerber export cuts silk away
    from exposed pads.
- **The logos:**
  - They are silk-only footprints (`G***`) with no pads, excluded from the BOM and pick-and-place files, so JLC's
    placement files are unchanged.
  - The bottom logo by U8 was moved clear of U8's pins: its nearest point is 0.34 mm from pin 8.
  - Two top logos sit under L1 and will be hidden by it.
- **KiCad's own files were removed** (to the Recycle Bin on 2026-09-27): the local history `.history/`, the three
  `*-backups/` autosave folders and the `.kicad_prl` view-settings files. KiCad recreates `.kicad_prl` files the next
  time you open a project; they are safe to delete again.

## LTspice subfolder

`LTspice/BOOST.asc` plus only the files it needs to run:
- 6 custom symbols: `CD4017B.asy`, `CD4051B.asy`, `INA241A3.asy`, `L7805.asy`, `LM2940_12.asy`, `UCC21520.asy`;
- 11 model libraries: `CD4000_v.lib`, `HYG180N10.lib`, `INA241A3.lib`, `L7805.lib`, `LM2940_12.lib`, `LM78L05.lib`,
  `MCP6241.lib`, `MCP6561.lib`, `SwitchAna.lib`, `TVS_5KP.lib`, `UCC21520.lib`.

Everything else it uses (resistors, capacitors, MOSFET and op-amp symbols, logic gates, diode models) is built into
LTspice. The test schematics, results and log files were left out. Open `BOOST.asc` in LTspice and press Run. The
netlist built from this subfolder is identical to the one built from the original LTspice folder.

**This `BOOST.asc` is the 2026-08-31 version, and it predates several design changes.** The final values are in the
KiCad schematic:

| Part | In `BOOST.asc` | In the final design | Why it changed |
|---|---|---|---|
| R13, R23, R47 (rail FET gate resistors) | 100 ohm | 220 ohm | dead-time margin (September simulations) |
| R15 (M1 gate) and D12 | 5.1 ohm with D12 | 10 ohm, D12 deleted | M1 turn-off overshoot |
| R21, R48, R60, R72 | 5 ohm | 5.1 ohm | 5.0 ohm 0805 is not stocked (rev6) |
| R1 and U25 (current sense) | 2 mOhm with INA241A3 | 1 mOhm with INA241A4 | stock; the signal is the same 0.1 V/A (rev6) |

The September simulations (dead time, M1 turn-off) ran from edited netlists that carry the final values. Those
netlists are not part of this package.

**Convergence fix (2026-09-27): it now runs to the end.** Before the fix it stopped at 1.51 ms of the 30 ms run with
"Time step too small ... trouble with node m9:si".
- **The change:** the three LED current-sink FETs **M8, M9 and M10** now use `HYG180N10_NOLEADS` instead of
  `HYG180N10`. Three `SYMATTR Value` lines in `BOOST.asc` changed; nothing else.
- **Why it failed:** `HYG180N10.lib` REV 5 (2026-09-14) added undamped package lead inductance (LD 4.5 nH, LS 7.5 nH,
  LG 7.5 nH) to every FET. Inside each sink's op-amp feedback loop, the 7.5 nH source lead forms an undamped
  high-frequency resonance with the gate capacitance, and LTspice's time step collapses on M9's internal source node.
- **Why this fix:** it is what the September simulations that did converge used. They ran the sinks without leads and
  kept leads on M1-M7, the switching FETs, where lead inductance sets the turn-off overshoot. The sinks run linearly,
  so their lead inductance does not change the result. `HYG180N10_NOLEADS` is the REV 4 model kept in the same library
  for this.
- **Checked** in LTspice 26.0.1: the full 30 ms ran in about 22 minutes with no convergence errors. Over 25-30 ms:
  - Vin 13.9 V; the 12 V rail at 11.99 V; VDD and analog 5 V at 5.00 V;
  - the outputs at about 20.2, 30.3 and 30.3 V;
  - the LX switch node peaks at 62.8 V, against the FETs' 100 V rating;
  - the LED currents settle by about 12 ms and hold at 0.73, 1.14 and 1.07 A (D16, D18, D17) through 30 ms.
- Those LED currents are the brightness setpoints in this August schematic. The September runs used the final
  setpoints (about 2.6 A).
- The original, unfixed file is still in `BOOST_package/LTspice/BOOST.asc`.

**Two things to know before you run it:**
- **The results file is large: about 22 GB** for the 30 ms run. LTspice saves every node at every step, and it writes
  `BOOST.raw` next to `BOOST.asc`. In a OneDrive folder that file will also sync. Run it from a folder outside OneDrive
  with enough free space, and delete `BOOST.raw` afterwards.
- **The `.meas` measurements print no results.** They are written for a 40 ms run (windows "FROM 35m TO 39m"), but the
  `.tran` stops at 30 ms, and one of them names node `N065`, which no longer exists. LTspice stops evaluating
  measurements at that error. This predates the fix; the waveforms themselves are fine to view.

The simulation also contains parts that are not on the boards: the supply, the LEDs, the cable resistance, reference
and ideal-switch models, and the Arduino signals. Its reference designators do not all match the KiCad schematic.
