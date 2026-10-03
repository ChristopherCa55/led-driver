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
- **The schematic layout was reorganized on 2026-09-28**, and checked against rev6's original layout:
  - all 290 parts match on every field, and all 322 symbol units and 201 power symbols are unchanged;
  - all 186 nets have the same pins and the same names;
  - ERC is 0, and both boards' parity is unchanged.
  - The LTspice schematic was reorganized too; its connections were identical. It was then edited to match KiCad
    (see below).
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

**Updated 2026-09-28 (evening): the LTspice schematic now matches the KiCad schematic part for part.** Every
electrical KiCad part (286, counting each gate, switch and pot unit) has an LTspice part with the same designator,
value and connections; a structural netlist comparison finds no differences. Only mounting holes, connectors and net
ties have no LTspice part. The previous `.asc` is backed up in
`BOOST_split_boards/previous/2026-09-28/before_ltspice_kicad_match/`.

**2026-09-29:** after you reorganized the layout, the connections were re-checked against KiCad. R73 and R74 had
ended up on the driver side of their gate resistors again; they now sit on `GATE_M4`/`GATE_M5` (each moved 16 units,
with a gate label on its freed end). All 286 parts match KiCad. The model values were checked against the part makers'
data sheets (below), the gates were retuned to Nexperia's figures, and the unused files and their `.lib` lines were
removed. Your reorganized `.asc` from before these edits is in `BOOST_split_boards/previous/2026-09-29/before_lib_cleanup/`.
The same LTspice files are in `BOOST_package`, `BOOST_package_for_review` and `BOOST_schematic_cleanup`.

`LTspice/BOOST.asc` uses:
- custom symbols: `74HC4051.asy`, `CD4017B.asy`, `CD74HC4066.asy`, `CSS4J_4026.asy`, `INA241A4.asy`, `L78L05.asy`,
  `LM2940_12.asy`, `MCP4451_CTRL.asy`, `MCP4451_POT.asy`, `UCC21520.asy`;
- model libraries: `74HC4051.lib`, `CD4000_v.lib`, `CD74HC4066.lib`, `CSS4J.lib`, `HYG180N10.lib`, `INA241A4.lib`,
  `L78L05.lib`, `LM2940_12.lib`, `MCP4451.lib`, `MCP6241.lib`, `MCP6561.lib`, `TVS_5p0SMDJ.lib`, `UCC21520.lib`.
- Removed on 2026-09-29 as unused: `CD4051B.asy`, `INA241A3.asy/.lib`, `L7805.asy/.lib`, `LM78L05.lib`,
  `SwitchAna.lib`, `TVS_5KP.lib`, their `.lib` lines, SwitchAna's `.param Vcc=5 Vel=0.2` and the unused
  `.model SW`. The `LED_RED`/`LED_GREEN`/`LED_BLUE` models are kept on purpose (the LEDs use the `100W_` models).

| Change | KiCad part |
|---|---|
| 4-terminal 1 mOhm Kelvin shunt; the INA's inputs now sense `ISNS_P`/`ISNS_N` | R1 (CSS4J-4026) |
| INA241A4 (gain 100, REF1 and REF2 grounded) instead of the INA241A3 | U25 |
| IREF chains: Arduino PWM `IREFn` -> 22k -> 1k + 1 nF -> digital pot (A = GND, W = `IREFn_input`) | R29/R54/C100/U26A, R30/R55/C101/U26B, R57/R58/C102/U26C |
| Digital-pot control pins: HVC/A0 and A1 10k to GND, RESET 10k to 5 V | U26E, R102, R99, R103 |
| Servo sample switches are CD74HC4066 channels gated by `IREF3`/`IREF2`/`IREF1` (were ideal switches on analog 5 V) | U106A/B/C |
| Error mux is a 74HC4051; its unused inputs IO0, IO3, IO5, IO6, IO7 go to ground (IO0 was on Verr1) | U28 |
| M1 gate pull-down on `GATE_M1`; M4/M5 pull-downs on `GATE_M4`/`GATE_M5` (were on the driver side) | R104, R73, R74 |
| 100k pull-down on `ARD_M1_INHIBIT` | R105 |
| L78L05 regulators; 22 uF on each 5 V rail; seven more 100 nF on 5 V | U1, U17, C7, C55, C92, C94-C99 |
| TVS model named for the board's 5.0SMDJ54A | D19 |
| All designators as in KiCad (the gates are U101A-U105B); the digital rail is named `5V` | - |
| Logic gates keep LTspice's fast built-in models, set to Nexperia 74HC00/74HC14 typical delays, edges and thresholds | U101-U105 |

**Parameters** (a `.param` line near the other directives):
- `IREF1_DUTY`, `IREF2_DUTY`, `IREF3_DUTY`: the Arduino's IREF PWM duty in 256ths at 490 Hz. 256 = always on (the
  default), 128 = 50 %, 0 = off.
- `POT1_CODE`, `POT2_CODE`, `POT3_CODE`: the MCP4451 wiper codes of U26A/B/C (0-256). The defaults 86/103/103 give
  2.635/2.371/2.371 A LED peaks. **Code 0 is full current and 256 is zero** on this board (A is grounded); Microchip's
  data sheet DS22267A confirms code 0 puts the wiper at terminal B. At power-up the pot sits at mid-scale (128, about
  1.98 A) until the firmware writes a code.
- Parts named `SIM_...` exist only in the simulation: the battery, cable, LEDs and the Arduino outputs.

**Checked (LTspice 26.0.1, 2026-09-28, repeated 2026-09-29 after the edits above):**
- 30 ms at full duty: no convergence errors, about 5-7 minutes.
- Over 25-30 ms, the LEDs hold 2.635, 2.371 and 2.371 A; the outputs sit at 23.30, 33.13 and 33.11 V.
- LX peaks at 61 V (M1 die 63.6 V); the current-sense output reads 0.1006 V/A.
- 74HC timing: the built-in gates match 74HC00/74HC14 models built from Nexperia's figures within 4 ns, with output
  levels within 0.5 mV.
- The CD74HC4066 model and the old ideal switch give the same servo voltages within 0.25 mV.

**PWM dimming (IREFn_DUTY below 256):**
- The headroom servo keeps the full set current in every pulse down to about 19 % duty on red and 25 % on green and
  blue (full circuit at 25 %, 50 % and 100 %; a servo test bench matched to it for longer times).
- Below that, the servo cannot keep up: R98/R93/R90 (10 MOhm) bleed its capacitor faster than the short pulses can
  charge it. The reference then falls back to the Arduino's Vref, and the pulses carry less current. At 10 % duty
  in the full circuit: red 0.81 A, green 1.25 A, blue 1.19 A (31-53 % of set).
- **Dimming runs can stall** while all three LEDs are off (the log fills with "tolerance relaxed" at one time point).
  Adding `solver=alt` to the `.options` line got past it, about 2-3 times slower.

**Start-up:**
- The two `.ic` lines start the servos and the reference filters settled, so the LEDs reach full brightness within
  about 15 ms.
- Delete both lines for a true cold start. Full brightness then takes about half a second, which a 30 ms run will not
  reach.

**Known issue** (edge-case simulations, 2026-09-28):
- During a cold start, while an output is still below the battery voltage, a channel can be switched off with current
  flowing in L1.
- LX then spikes to 80-87 V into the TVS D19. The FETs are rated 100 V.
- Fixes are being considered; the design is unchanged so far.

**Models written for this simulation** (behavioural; values checked against the makers' data sheets on 2026-09-29):
- INA241A4 (TI SBOSA30), CD74HC4066 (TI SCHS208E: 25 ohm on-resistance near the rails), 74HC4051 (Nexperia Rev 12:
  90 ohm, 20 ns), MCP4451 (Microchip DS22267A: 10 k +/-20 %, 75 ohm wiper, 75/120/75 pF), L78L05 (ST Doc 2145 Rev 19:
  1.7 V dropout), 5.0SMDJ54A (Littelfuse 04/17/19: 60.0-66.3 V breakdown, 87.1 V at 57.5 A).
- Not in the data sheets: the L78L05's typical quiescent current (ST gives only 6 mA max; 3 mA used).
- The TVS model follows the 10/1000 us clamp figure. The data sheet's 8/20 us figure (112.5 V at 431 A) implies a
  lower dynamic resistance, so for nanosecond LX spikes the real clamp is probably lower than simulated.
- The CD74HC4066's off-leakage is 0.1 uA max at 25 C but 1 uA max over -55 to 85 C; it is not modelled. Hot, a
  worst-case part could move a servo capacitor by up to about 10 V/s while its switch is open.
- The MCP4451's A0 address bit is latched at power-up while a weak internal pull-up is on. The data sheet rates it
  (16 kOhm) only at 5.5 V, so it does not guarantee that R102 (10 k) latches A0 low. Probe both I2C addresses 0x2C and
  0x2D in firmware.

**Before you run it:** the results file is large, about 22 GB for the 30 ms run, because LTspice saves every node.
- Run it from a folder outside OneDrive with enough free space, and delete `BOOST.raw` afterwards.
- Or add a `.save` line that lists only the signals you want.
