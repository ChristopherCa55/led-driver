# Review fixes, 2026-10-11 (work folder)

Fixes for the 2026-10-10 schematic and PCB reviews, run from `review_2026-10-10/FIX_PROMPT.md`.

- **The copy:** `led-driver/BOOST_review_fixes/` = BOOST_package as of 2026-10-11 (12 key files hash-checked against
  all three shipped folders; lock files, `.history` and `.kicad_prl` left out), plus `NOT_FOR_FAB.txt`.
- **The shipped folders are never written.**
- **Status (2026-10-13):** every approved step is in the copy (steps 1-4, 5g, 6b, 7e, 8c, 9, 10) and every output
  was regenerated; the copy stays NOT_FOR_FAB until the user says ship. Read the top of `FIX_REPORT.md`, then
  `CHANGES_XY.md`.
- **Answers:** `ANSWERS.md` (the user's words and how each was applied).

## Layout
- `DECISIONS.md`: the decisions asked in one batch, with numbers, options and recommendations.
- `work/baseline/`: every check on the unmodified copy (run on a scratch copy of its KiCad folder, so no `.kicad_prl`
  lands in the copy).
- `work/METRICS.md`: one row per metric, one column per step; `work/METRICS_final.md`: baseline / the copy now / with
  the pending steps. `work/CHANGELOG.md`: every step, failed tries included. `work/promotions.log`: every file written
  into the copy, old -> new hash.
- `work/stepNN/`: each step's scratch KiCad folder, its spec, gates (`step_checks.log`), metrics outputs and `STEP.md`.
  Failed tries keep their folder with a `FAILED.txt` or `SUPERSEDED.txt`.
- `work/specs/`: the edit specs (pcb_text_edit / route_new / add_footprints jobs).
- `work/final_copy_check/`: the final gates run on the copy's own files.
- `work/pristine/`: untouched copies of the copy's KiCad and LTspice folders, the references for checks.
- `work/proto/*_NOT_FOR_FAB/`: research prototypes on scratch boards. These are not steps of the fix.
- `work/whatif/`: what-if solves on edited copies of the copper export.
- `work/sims/`: LTspice runs (`.save` list; the shipped `.tran`).
- `work/mockups/`, `img/mock/`: note and title mock-ups (scratch schematics only).
- `img/research/`: net maps used for planning.

## Tools (`tools/`)
| Tool | What it does |
|---|---|
| `make_copy.py` | Makes the copy, leaving out lock files and KiCad backups; checks every copied file's hash. |
| `step_checks.sh STEP` | Runs every gate and metric on `STEP/kicad`: ERC x3, DRC with refill and parity, sync, both exports, DC solve, loop L, pcb_checks, plane / sense cover, gate returns, GND heatmap with sense offsets, card sens_check6, and the U16 thermal model (`THERMAL=1`). |
| `collect.py WORK STEP...` | Builds METRICS.md and flags anything worse than the baseline. |
| `sense_cover.py` | Sense nets over GND. Rebuilt; reproduces the 10-02 per-net figures exactly. |
| `sense_offsets.py` | LED-sense GND offsets to the card's GND. Rebuilt; reproduces 10-02 exactly. |
| `gates_all.sh` | gate_return.py for all ten gate paths. |
| `sim_case.py` | One LTspice run on a scratch copy, editing the netlist only (`.save` list, extra `.meas`, `.ic` variants). |
| `d19_cycles.py` | D19 conduction per switching cycle from a run. |
| `pcb_text_edit.py SPEC IN OUT` | Removes / adds segments and vias by text edit (CRLF kept); OUT must not exist. |
| `whatif_vias.py` | Adds vias to a copper export, with antipads and a collision check. |
| `net_map.py` | Plan view of a net on all layers. |
| `mock_notes.py`, `mock_kicad.py` | Note and title mock-ups into new scratch files. |

## Lessons
- **Run heavy jobs one at a time.** Two 9-worker DC solves at once crash (BrokenProcessPool, out of memory). Running
  solves alongside LTspice grew the page file to 46 GB.
- **Headless Edge from Python** writes no screenshot when its output is piped. Log it to a file and wait for the PNG.
- **DC solves run out of memory with 5-9 workers** while the user's apps hold ~20 GB; 3 workers work (~30 min).
- **A via with no track or pad needs `(free yes)`**, or KiCad gives it a zone's net (step 7's first try became 5V).
- **The card's GND is in the Power netclass (0.25 mm clearance)**, not Default (0.2 mm).
- **Never edit a bash script while it runs** (bash reads it as it goes; step 3's make_step.sh broke that way).
- **Git Bash's `grep -c $'\r'` counts every line**: count CRLF in Python.
- **The 6-layer card is saturated:** the longest In1 splitters (0err_hi, SDA) have no route on In2 / F / B.
