# BOOST 3D assembly (2026-09-24)

The two release-candidate boards in the case, at their real heights, with every part and fixing that has no 3D model
drawn as a dimensioned solid. The model shows the assembly and was used to check collisions.

| File | What |
|---|---|
| `BOOST_assembly_2026-09-24.step` | STEP assembly (19 MB): power board, control card, hardware, case, lid, keep-outs; named and coloured |
| `BOOST_assembly_2026-09-24.glb` | the same as GLB (glTF 2.0, metres, Y up), 3.9 MB |
| **Viewer**: https://claude.ai/artifact/D7rRHCERjoWhTUFZzMJg9P | opens in a browser, nothing to install: orbit, layer toggles, a height cut-away, and the clearance list (click a row to light its two parts). Source in `viewer/` |
| `CLEARANCES.md` | the clearance table: every check, the nearest part, the distance, flags under 1 mm; the stack; what was substituted and from where |
| `renders/` | iso from the south-west and north-east, top, side from the south and the west (lid shown), a close-up of the H7 standoff stack, and the underside with the FETs and thermal pads |
| `work/power.step`, `work/card.step` | the KiCad STEP exports of the two plotted boards |
| `work/clearances.json`, `work/geometry.json` | the numbers behind CLEARANCES.md, and the footprint geometry read from the board files |

## Frame

X = board x + 22 and Y = 28 - board y (the case drilling drawing's box coordinates are X = box x, Y = -box y),
Z up from the case floor. The case inside is 0..128 x -90..0 x 0..33.

## How it was built

1. `kicad-cli pcb export step --subst-models` on each plotted board.
2. `tools/build_assembly.py` (OpenCASCADE 8 through `cadquery-ocp`):
   - places the boards at 5.50 mm (power underside) and 28.60 mm (card underside);
   - replaces the generic 2x15 socket/header models with the Samtec pair;
   - adds the substitutes listed in CLEARANCES.md;
   - measures the clearances with BRepExtrema (exact solid-to-solid distance);
   - writes the STEP.
3. `tools/step_to_glb.py` meshes the STEP and writes the GLB; `tools/render_views.py` renders it (VTK, offscreen).
4. `tools/write_clearances.py` writes CLEARANCES.md; `viewer/viewer_template.html` plus the clearance data make the
   viewer page.

Installed for this, in its own venv:
- `cadquery-ocp` 8.0.1: the OpenCASCADE Python bindings, used to read and write STEP, build solids, measure distances
  and write glTF;
- its dependencies `vtk` 9.6.2 (renders), `numpy`, `matplotlib`, `pillow`.

The venv sits at `C:\Users\bubba\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\boost3d-venv`, about
620 MB; the app's sandbox redirected it from `C:\Users\bubba\AppData\Local\boost3d-venv`. Run the tools with that
venv's `python.exe`. No board file was changed to make the model.
