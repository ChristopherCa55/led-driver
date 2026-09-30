# BOOST LED driver: design files for review (2026-09-28)

The KiCad design, the LTspice simulation and the fabrication files of the BOOST LED driver:
- the schematic is rev6;
- both boards are RC2 with the silkscreen logos (added 2026-09-27).

**The gerbers, fab drawings and 3D model here were made on 2026-09-24/25, before the logos.** Regenerate them from
the boards in `KiCad/` before ordering; uploading these zips as they are gives boards without the logos.

## What is here

| File | What it is | Open with |
|---|---|---|
| `KiCad/BOOST.kicad_pro`, `KiCad/BOOST.kicad_sch` | **The schematic** (rev6). Open the `.kicad_pro` | KiCad 10 |
| `KiCad/BOOST_power_RC2.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | **Power board**: 74 x 86 mm, 8 layers, 9 silkscreen logos | KiCad 10: open its `.kicad_pro` |
| `KiCad/BOOST_control_RC2.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | **Control card**: 45 x 45 mm, 8 layers, 2 silkscreen logos | KiCad 10, as above |
| `KiCad/BOOST.pretty/`, `KiCad/CSCF3218-6R8MC.pretty/`, `KiCad/ltspice.kicad_sym`, `KiCad/fp-lib-table`, `KiCad/sym-lib-table` | The project's own footprint and symbol libraries. The tables use project-relative paths | used by KiCad automatically |
| `BOOST_power_RC2_gerbers.zip`, `BOOST_control_RC2_gerbers.zip` | Gerbers and drill files, **made before the logos** | JLCPCB, or KiCad's GerbView |
| `BOOST_power_RC2_fab_drawing.pdf`, `BOOST_control_RC2_fab_drawing.pdf` | Fab drawings: outline, holes, stackup, copper, notes (all vias epoxy filled and capped) | any PDF reader |
| `BOOST_assembly_2026-09-25.step` | 3D model of both boards in the case, **made before the logos** | FreeCAD, CAD Assistant or any CAD program |
| `LTspice/` | The LTspice simulation (see below) | LTspice 26 |

## KiCad notes
- **The schematic layout was reorganized on 2026-09-28**, and checked against rev6's original layout:
  - all 290 parts match on every field, and all 322 symbol units and 201 power symbols are unchanged;
  - all 186 nets have the same pins and the same names;
  - ERC is 0, and both boards' parity is unchanged.
  - The LTspice schematic was reorganized too; its connections were identical. It was then edited to match KiCad
    (see below).
- **Each board has its own `.kicad_pro`**, which carries its net classes and design rules. Open a board through (or
  beside) its own `.kicad_pro`; without it, DRC falls back to the defaults.
- **3D models:** the parts use KiCad's standard 3D library (`${KICAD10_3DMODEL_DIR}`), which comes with KiCad.
- **Checked 2026-09-27, after the logos:**
  - ERC: 0 errors, 0 warnings.
  - DRC on both boards: 0 errors, 0 unconnected.
  - Warnings: the two can-outline silk overlaps on the power board, and the J10/J11 1.05 mm drills that differ from
    their library footprints on purpose.
  - 46 silk-over-copper warnings where a top logo under L1 crosses L1's middle (mechanical) pad. It is hidden under L1,
    and the gerber export cuts silk away from exposed pads.
- **The logos** are silk-only footprints (`G***`) with no pads, excluded from the BOM and pick-and-place files.
- KiCad recreates `.kicad_prl` files, `.history/` and `*-backups/` folders when a project is opened. They are safe to
  delete.

## LTspice subfolder

**Updated 2026-09-28 (evening): the LTspice schematic now matches the KiCad schematic part for part.** Every
electrical KiCad part (286, counting each gate, switch and pot unit) has an LTspice part with the same designator,
value and connections; a structural netlist comparison finds no differences. Only mounting holes, connectors and net
ties have no LTspice part. The previous `.asc` is backed up in
`BOOST_split_boards/previous/2026-09-28/before_ltspice_kicad_match/`.

`LTspice/BOOST.asc` uses:
- custom symbols: `74HC4051.asy`, `CD4017B.asy`, `CD74HC4066.asy`, `CSS4J_4026.asy`, `INA241A4.asy`, `L78L05.asy`,
  `LM2940_12.asy`, `MCP4451_CTRL.asy`, `MCP4451_POT.asy`, `UCC21520.asy`;
- model libraries: `74HC4051.lib`, `CD4000_v.lib`, `CD74HC4066.lib`, `CSS4J.lib`, `HYG180N10.lib`, `INA241A4.lib`,
  `L78L05.lib`, `LM2940_12.lib`, `MCP4451.lib`, `MCP6241.lib`, `MCP6561.lib`, `TVS_5p0SMDJ.lib`, `UCC21520.lib`.
- **No longer used:** `CD4051B.asy`, `INA241A3.asy`, `INA241A3.lib`, `L7805.asy`, `L7805.lib`. `LM78L05.lib`,
  `SwitchAna.lib` and `TVS_5KP.lib` are still named by `.lib` lines but nothing uses them. They are kept until you
  decide to remove them (remove their `.lib` lines too).

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
| Logic gates keep LTspice's fast built-in models, retuned to 74HC00/74HC14 typical delays, edges and thresholds | U101-U105 |

**Parameters** (a `.param` line near the other directives):
- `IREF1_DUTY`, `IREF2_DUTY`, `IREF3_DUTY`: the Arduino's IREF PWM duty in 256ths at 490 Hz. 256 = always on (the
  default), 128 = 50 %, 0 = off.
- `POT1_CODE`, `POT2_CODE`, `POT3_CODE`: the MCP4451 wiper codes of U26A/B/C (0-256). The defaults 86/103/103 give
  2.635/2.371/2.371 A LED peaks. **Code 0 is full current and 256 is zero** on this board (A is grounded), assuming
  Microchip's usual convention; the MCP4451 data sheet was not checked.
- Parts named `SIM_...` exist only in the simulation: the battery, cable, LEDs and the Arduino outputs.

**Checked (LTspice 26.0.1, 2026-09-28):**
- 30 ms at full duty: no convergence errors, about 7 minutes.
- Over 25-30 ms, the LEDs hold 2.635, 2.371 and 2.371 A; the outputs sit at 23.30, 33.13 and 33.11 V.
- LX peaks at 61 V (M1 die 63.6 V); the current-sense output reads 0.1006 V/A.
- 74HC timing: the retuned built-in gates match 74HC00/74HC14 models within 4 ns, with output levels within 0.5 mV.
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

**Models that are not from the part makers** (behavioural, built from data sheets where they could be read):
- INA241A4, CD74HC4066, 74HC4051 (TI CD74HC4051 figures; its address delay is assumed), MCP4451 (wiper resistance
  and code direction assumed), L78L05 (TI LM78L05 figures), 5.0SMDJ54A (copied from the 5KP54A; not checked).

**Before you run it:** the results file is large, about 22 GB for the 30 ms run, because LTspice saves every node.
- Run it from a folder outside OneDrive with enough free space, and delete `BOOST.raw` afterwards.
- Or add a `.save` line that lists only the signals you want.
