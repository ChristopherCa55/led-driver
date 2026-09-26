# BOOST: final package, scenario A (2026-09-25)

Everything needed to order and build **scenario A**: 5 bare PCBs of each board, 2 complete sets assembled by
JLCPCB, 3 spare bare boards of each. These are copies; the working folders are unchanged.

**Status: ready to order.**
- Schematic rev6 is written into `BOOST-github/BOOST/BOOST.kicad_sch` (2026-09-25). Folder 1 is a byte-identical
  copy.
- On the file in place: ERC 0/0, the same report as rev5. Netdiff against rev5 shows the six values only. Parity
  is 0 on both boards, and DRC 0 errors, 0 unconnected.
- Rev5 is backed up in `previous/2026-09-25/schematic_rev5/`.
- The boards, gerbers and BOM here already use the rev6 values: R1 = Bourns CSS4J-4026R-1L00F (1 mOhm) and
  U25 = INA241A4.

**Start with `7_docs/ORDER_CHECKLIST.md`.**

## What is where

| Folder | Contents |
|---|---|
| `1_schematic_rev6/` | KiCad schematic project, rev6 (rev5 + R1 1m, U25 INA241A4xD, R21/R48/R60/R72 5.1), identical to the shipped schematic: `BOOST.kicad_sch`/`.kicad_pro`, the project libraries (`BOOST.pretty`, `CSCF3218-6R8MC.pretty`, `ltspice.kicad_sym`), netlist `BOOST_9-25_rev6.net`, ERC report `ERC_9-25_rev6` (0 errors, 0 warnings) |
| `2_boards/power/`, `2_boards/card/` | the exact board files the gerbers were plotted from: `BOOST_power_RC2.kicad_pcb` (power v19) and `BOOST_control_RC2.kicad_pcb` (card c3b), each with its `.kicad_pro` (net classes) and `.kicad_dru` (custom rules). `fp-lib-table` points to folder 1's libraries |
| `3_fab/power/`, `3_fab/card/` | **`*_gerbers.zip`: upload these to JLCPCB.** 8 copper layers, mask, paste, silk, outline, drills (PTH / NPTH separate, J9 slots), drill maps, job file. Plus the fab drawing (`.pdf`, `.png`) and `checks/` (DRC, drill report, drill maps, IPC-D-356) |
| `4_bom_and_placement/` | **JLC BOM and pick-and-place** for each board (`*_BOM_JLC.csv`, `*_CPL_JLC.csv`), the full sourcing table, JLC stock on 2026-09-25 |
| `5_assembly/` | `BUILD_NOTES.md` (what you fit, FET orientation, soldering, stack, order of work, J9 wiring), the case-floor drilling drawing rev B (`case_floor_drilling.svg` / `.html` / hole list) |
| `6_3d_model/` | the assembly: STEP, STL, GLB, 3D PDF, renders, `CLEARANCES.md`, `3D_README.md` |
| `7_docs/` | `ORDER_CHECKLIST.md`, `COST_SUMMARY.md`, `FAB_README.md` (board facts, rev6 checks, JLC settings), `thermal_pad_options.txt`, `M1_TURNOFF_RECHECK.md` + `M1_deadtime_results.txt` |

## Which file to open with what (Windows)

| File | Open with |
|---|---|
| `*.kicad_sch`, `*.kicad_pcb` | **KiCad 10** (open the `.kicad_pro` in the same folder) |
| `*_gerbers.zip` | upload as-is to JLCPCB; to look inside, KiCad's **GerbView** (or JLC's online viewer after upload) |
| `*_fab_drawing.pdf`, drill maps | any PDF reader |
| `*.csv` | Excel or any spreadsheet (upload as-is to JLC) |
| `*.md` | any text editor; VS Code or a Markdown viewer shows the tables |
| `case_floor_drilling.html` / `.svg` | any web browser (print at 100 % for a 1:1 template) |
| `6_3d_model/BOOST_assembly_2026-09-25_3D.pdf` | **Adobe Acrobat Reader** (free). Click the model to activate it; if blank, turn on Edit > Preferences > 3D & Multimedia > "Enable playing of 3D content". **Edge and Chrome do not show 3D PDF content** |
| `6_3d_model/BOOST_assembly_2026-09-25.step` | **FreeCAD** or **CAD Assistant** (both free), or any CAD program. Full assembly with names and colours |
| `6_3d_model/BOOST_assembly_2026-09-25.stl` | Windows **3D Builder** / **3D Viewer** if installed, PrusaSlicer, FreeCAD or Blender. One mesh: boards, parts, fixings and floor. `_with_case.stl` adds the walls and lid |
| `6_3d_model/BOOST_assembly_2026-09-25.glb` | Windows 3D Viewer if installed, Blender, any glTF viewer |
| `6_3d_model/renders/*.png` | any image viewer |

## Checksums (SHA-256)

| File | SHA-256 |
|---|---|
| `3_fab/power/BOOST_power_RC2_gerbers.zip` | `4fc0688c9ff3500135d68a8ba963d59667132d752dd878e72ea48a83f0faeed4` |
| `3_fab/card/BOOST_control_RC2_gerbers.zip` | `82b4a6d133dd863a58cdb024bbe37d20b83345eb63c83c0a7d4970ee9f040383` |
| `2_boards/power/BOOST_power_RC2.kicad_pcb` | `18bcd8c6e1583a45104c0302d4abccc22af1bc9ee5b5d10b18372e777df18d90` |
| `2_boards/card/BOOST_control_RC2.kicad_pcb` | `1037e2266c96024a2e335a994cb5258b8c12008d5defa60bc3ddf5eaaeaadef4` |
| `1_schematic_rev6/BOOST.kicad_sch` | `25a5eaf9d740ee3ff585dff8066fda81a68d199a338f6515af342ef9e4ebd658` |
| `4_bom_and_placement/BOOST_power_BOM_JLC.csv` | `c13a1d65e4e9512630677dfe72f9985ce686da00083d533e19c24674fb846275` |
| `4_bom_and_placement/BOOST_power_CPL_JLC.csv` | `02eea99cc5787e20a1ec78b3a7a9011e830f99366faaa4d5750ea58287d8b4cc` |
| `4_bom_and_placement/BOOST_control_BOM_JLC.csv` | `a8a78ec73502603c1912bbf7b789f99dfaaf4744881a3472151a447e4f55085a` |
| `4_bom_and_placement/BOOST_control_CPL_JLC.csv` | `5b7a2d14a18f5e5b24d962d2ac0e944acb37cdb64b62869a629131c11af1a7b4` |

## Checks on these files (2026-09-25)

- **KiCad DRC** on the two board copies here: 0 errors, 0 unconnected.
  - Power has 3 warnings: two silk overlaps where can outlines touch, and a library mismatch on J10's 1.05 mm drill.
  - The card has 1 warning: a library mismatch on J11's 1.05 mm drill.
  - The gerbers were plotted only after that DRC passed.
- **Rev6**: ERC is clean. Netdiff against rev5 shows only the six values. Parity is 0 on both boards. No footprint
  moved. Details in `7_docs/FAB_README.md`.
- **Stock** on 2026-09-25 covers all 61 JLC lines for 2 sets. The tight ones: 220 uF cans 19 against 18 needed,
  LM2940S-12 2 against 2 (the CS grade is the fallback).
- **M1 turn-off** with the routed loop: die peak 67.6 V, TVS at most 0.73 uJ per turn-off, dead time unchanged. You
  accepted this on 2026-09-25.

## Money

**Scenario A: $760.83** with the McMaster 1272N32 thermal pad. The alternatives are $862.67 with the Parker
0.060 in G579, or $733.92 plus the price of a t-Global TG-AD30 1.5 mm sheet.
- Bare PCBs $261.14, JLC assembly $392.73, parts elsewhere $24.91, hardware $55.14 plus the pad.
- Shipping and tax are not included.
- Every price is read, except two Farnell UK prices converted from GBP.
- `7_docs/ORDER_CHECKLIST.md` is the final version to order from.

Hardware changed on 2026-09-25:
- Floor stud: M3 x 20 set screw plus a 5.00 mm aluminium spacer, replacing the Essentra HTSN-M3-5-3, which is sold
  only in bulk.
- PTC: MF-R050.
- FET pad: 1.52 mm (39 % at the same 0.93 mm gap).
- `5_assembly/BUILD_NOTES.md` has the new steps, including the mandatory tab-to-case check before first power-up.
