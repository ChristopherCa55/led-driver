# BOOST 3D assembly (rebuilt 2026-09-25)

The two release boards (RC2) in the case, at their real heights, with every part and fixing that has no 3D model
drawn as a dimensioned solid. The model shows the assembly and was used to check collisions.

**2026-09-25 rebuild.** The boards are the RC2 plotted files: power v19 and card c3b, re-exported. They are
mechanically identical to the RC1 files used on 2026-09-24. The hardware is now the chosen parts:
- tab screws: McMaster 92000A107 (head 5.0 x 2.1 mm, was 1.75 from ISO maximums);
- tab-screw spacer: McMaster 93657A200 (2.0 mm, 4.5 mm OD, was a 2.25 mm placeholder);
- R1: the rev6 CSS4J-4026R-1L00F (2.70 mm tall, was 2.93).

Against 2026-09-24, only two clearances moved: C69's top to M1's screw head went from 11.27 to 10.92 mm, and M8's
screwdriver path from 1.6 to 1.8 mm. Nothing new is under 1 mm. The 2026-09-24 files are kept (`*_2026-09-24.*`,
`renders_2026-09-24/`, `work/2026-09-24/`).

## Which file to open with what (Windows)

| File | Open with | What you get |
|---|---|---|
| `BOOST_assembly_2026-09-25_3D.pdf` (1.3 MB) | **Adobe Acrobat Reader** (free). Click the model to activate it. If it stays blank, turn on Edit > Preferences > 3D & Multimedia > "Enable playing of 3D content". **Browser PDF viewers (Edge, Chrome) do not show 3D content.** | the whole assembly, rotatable, with the preset views. A 1 x 1 mm placeholder board sits at the origin (KiCad will not write a 3D PDF without one) |
| `BOOST_assembly_2026-09-25.step` (14 MB) | **FreeCAD** (free) or **CAD Assistant** (free, from Open Cascade), or any CAD program (Fusion, SolidWorks, Onshape) | the full assembly with part names and colours; measure anything |
| `BOOST_assembly_2026-09-25.stl` (8 MB) | Windows **3D Builder** or **3D Viewer** if installed, PrusaSlicer, FreeCAD, Blender | one mesh, no names or colours: boards, parts, fixings and the case floor; walls, lid and keep-out volumes left out |
| `BOOST_assembly_2026-09-25_with_case.stl` | the same | everything, including the case walls, the lid and the keep-out volumes (a closed box: use a section view) |
| `BOOST_assembly_2026-09-25.glb` (3.9 MB) | Windows 3D Viewer if installed, Blender, or any glTF viewer | named, coloured parts (metres, Y up) |
| `renders/*.png` | any image viewer | iso from the south-west and north-east, top, side from the south and the west, the H7 standoff close-up, the underside with FETs and pads |
| `CLEARANCES.md` | any text or Markdown viewer | every clearance check, the nearest part, the distance, flags under 1 mm; the stack; the substitutions |

The online viewer https://claude.ai/artifact/D7rRHCERjoWhTUFZzMJg9P still shows the 2026-09-24 model. The
differences are the three hardware items listed above.

## Frame

X = board x + 22 and Y = 28 - board y (the case drilling drawing's box coordinates are X = box x, Y = -box y),
Z up from the case floor. The case inside is 0..128 x -90..0 x 0..33.

## How it was built

1. `kicad-cli pcb export step --subst-models` on each plotted RC2 board, into `work/power.step` and `work/card.step`.
2. `tools/build_assembly.py` (OpenCASCADE 8 through `cadquery-ocp`):
   - places the boards at 5.50 mm (power underside) and 28.60 mm (card underside);
   - replaces the generic 2x15 socket/header models with the Samtec pair;
   - adds the substitutes listed in CLEARANCES.md;
   - measures the clearances with BRepExtrema (exact solid-to-solid distance);
   - writes the STEP.
3. `tools/step_to_glb.py` writes the GLB (run it after step 2: the builder's own GLB lacks the unit and axis
   conversion). `tools/render_views.py` renders it (VTK, offscreen). `tools/write_clearances.py` writes
   CLEARANCES.md.
4. `tools/step_to_stl.py` writes the two STLs (OCC StlAPI_Writer, 0.08 mm deflection).
5. `tools/flatten_step.py` writes a one-level copy of the STEP, `work/pdf3d/BOOST_assembly_2026-09-25_flat.step`.
   KiCad's model loader drops the nested assembly.
6. `tools/make_3dpdf.py` (KiCad's Python) builds a throwaway board carrying that STEP as its only 3D model, then runs
   `kicad-cli pcb export 3dpdf` on it. No real board file is touched.

Installed for this, in its own venv:
- `cadquery-ocp` 8.0.1: the OpenCASCADE Python bindings;
- its dependencies `vtk` 9.6.2, `numpy`, `matplotlib`, `pillow`;
- `pypdf` (reading datasheet text).

The venv sits at `C:\Users\bubba\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\boost3d-venv`, about
620 MB; the app's sandbox redirected it from `C:\Users\bubba\AppData\Local\boost3d-venv`. Run the tools with that
venv's `python.exe`, except `make_3dpdf.py`, which needs KiCad's. No board file was changed to make the model.
