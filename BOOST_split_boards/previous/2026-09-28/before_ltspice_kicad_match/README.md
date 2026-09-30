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
  - The LTspice schematic was reorganized too; its connections are identical.
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

`LTspice/BOOST.asc` plus only the files it needs:
- 6 custom symbols: `CD4017B.asy`, `CD4051B.asy`, `INA241A3.asy`, `L7805.asy`, `LM2940_12.asy`, `UCC21520.asy`;
- 11 model libraries: `CD4000_v.lib`, `HYG180N10.lib`, `INA241A3.lib`, `L7805.lib`, `LM2940_12.lib`, `LM78L05.lib`,
  `MCP6241.lib`, `MCP6561.lib`, `SwitchAna.lib`, `TVS_5KP.lib`, `UCC21520.lib`.

Everything else it uses is built into LTspice.

**Updated 2026-09-28: it runs the full 30 ms and carries the final values of the KiCad schematic.**

| Change from the 2026-08-31 file | Why |
|---|---|
| M8, M9, M10 (LED current sinks) use `HYG180N10_NOLEADS` | The REV 5 model's undamped lead inductance inside the sink loops stopped the run at 1.51 ms ("time step too small"). The sinks run linearly, so their leads do not matter; M1-M7 keep their leads |
| R13, R23, R47: 220 ohm. R15: 10 ohm, D12 removed. R21, R48, R60, R72: 5.1 ohm | The final values, as in the KiCad schematic (rev6) |
| Servo outputs labelled `SRV1`-`SRV3`, with `.ic V(SRV1)=2.89 V(SRV2)=3.86 V(SRV3)=3.86` | The headroom servos take about 0.25 s to settle; this starts them settled. The old `.ic` pointed at nodes that had been renumbered |
| Reference filters `R_VREF1`-`R_VREF3` (10 k) and `C_VREF1`-`C_VREF3` (10 uF); the `Reference_Vn` sources now drive `Vref_n_arduino` with 0-5 V, 490 Hz PWM like the Arduino's pins (40, 60 and 60 % duty, averaging 2, 3 and 3 V); `.ic V(Vref_1)=2 V(Vref_2)=3 V(Vref_3)=3` | Board parts the model lacked: R101/C103, R100/C93 and R77/C47. They have new names because R77 and C47 are other parts in the `.asc` |
| `D27` and a source `ARD_M1_INHIBIT` (0 V) on the `M1_INHIBIT` OR node | The board's Arduino M1-inhibit input (J9 pin 11). Set the source to 5 V to hold M1 off |
| Most `.meas` lines removed | Only the TVS power and energy measurements remain |

**Checked (LTspice 26.0.1, 2026-09-28):**
- The 30 ms run finishes in about 5.5 minutes with no convergence errors.
- Over 25-30 ms, the LEDs hold 2.631, 2.368 and 2.368 A (the setpoints), the same as with DC references.
- The PWM leaves 6-8 mV of ripple on the error amplifiers' reference inputs (`.1Vref_n`). The 62-76 mA peak-to-peak LED ripple is the boost's own and is the same with DC references.
- The outputs sit at 23.3, 33.1 and 33.1 V; the 12 V rail at 11.99 V.
- LX peaks at 61 V (M1 die 63.6 V) against the FETs' 100 V rating.
- With `ARD_M1_INHIBIT` at 5 V, M1 stays off.

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

**Still different from the KiCad schematic:**
- R1/U25 are 2 mOhm with an INA241A3. The board has 1 mOhm with an INA241A4, giving the same 0.1 V/A; there is no
  INA241A4 model.
- The IREF references come from ideal sources rather than the U26 digital potentiometer.
- The supply, cable resistance, LEDs and Arduino sources exist only in the simulation.
- The reference designators do not all match the KiCad schematic.

**Before you run it:** the results file is large, about 22 GB for the 30 ms run, because LTspice saves every node.
- Run it from a folder outside OneDrive with enough free space, and delete `BOOST.raw` afterwards.
- Or add a `.save` line that lists only the signals you want.
