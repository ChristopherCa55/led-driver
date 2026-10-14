# Output regeneration: dry run on the candidate boards (2026-10-13)

The user approved regenerating every output (D14, 2026-10-12: "regenerate all the files like the gerbers, drill, fab,
bom etc..."). The real run waits until the pending design steps are approved and promoted into the copy. This dry
run proves the whole chain on the candidate (card = step 9, power = step 6b = the copy's), in scratch folders only.
**Nothing in the copy or the shipped folders was written.**

## Results
| Output | Dry-run folder | Result |
|---|---|---|
| Gerbers + drill + IPC-356, both boards | `fab_dryrun/BOOST_power_RC2/`, `fab_dryrun/BOOST_control_RC2/` | DRC on the saved files 0 errors / 0 unconnected (warnings: power the baseline 49 types, card J11 only); fills current; 18 files per zip; no work-in-progress names inside |
| Fab drawings | same folders, `*_fab_drawing.pdf/.png` | dated 2026-10-13; power 970 vias (was 972: the 12V route removed some, steps 4 / 6b added 5), card 398 vias (was 393) |
| BOM / CPL CSVs, SOURCING_TABLE, COST_SUMMARY | `bom_dryrun/bom/`, `bom_dryrun/COST_SUMMARY.md` | power BOM / CPL unchanged; card: R99 / R102 on the 1k line, R106 / R107 on the 4.7k line (C23162), CPL +2 rows (Top, rot 0); identical to `step05g_completion/fab/` (made independently). **Total $598.99 -> $599.01** |
| BOOST_BOM.xlsx (full) and the reviewer copy (`--review`) | `bom_dryrun/*.xlsx` | Excel (COM): 0 formula errors, total 599.01 in Summary!B8 |
| 3D STEP + clearances | `assembly_dryrun/BOOST_assembly_2026-10-13.step`, `CLEARANCES.md` | all 67 clearance rows identical to 2026-10-07 |

## The real run (after promotion), from `BOOST_split_boards/`
1. Fab, per board, into a new folder (e.g. `review_fixes_2026-10-11/work/fab_final/`), from the COPY's boards:
   `bash review_fixes_2026-10-11/tools/make_fab_copy.sh ../BOOST_review_fixes/KiCad/<B>.kicad_pcb <B> <B>` (run inside
   the new folder; the libraries default to `BOOST_review_fixes/KiCad`), then
   `"<KiCad python>" fab_2026-10-07/tools/fab_facts.py <B>/.src/<B>.kicad_pcb work/<power|card>_facts.json` and
   `FAB_DATE=<date> python review_fixes_2026-10-11/tools/fab_drawing_copy.py power|card`.
2. BOM: a fresh copy of `work/bom_dryrun/` (its `tools/build_bom.py` already has the R99 / R102 / R106 / R107 lines)
   with the copy's boards in `work/boards/`; `parts_from_boards.py`, `kicad-cli pcb export pos --side both
   --use-drill-file-origin --format csv --units mm`, `build_bom.py`, `cost_summary.py`, `make_xlsx.py BOOST_BOM.xlsx`
   (and `--review`), then `r14_delete_2026-10-07/tools/xlsx_check.ps1 -Path <abs> -Total <total>`.
3. 3D: a fresh copy of `work/assembly_dryrun/` (output names already 2026-10-13); `kicad-cli pcb export step
   --subst-models` of the two plotted `.src` boards into `work/`, `board_geometry.py`, then the boost3d venv's python
   on `tools/build_assembly.py` and `tools/write_clearances.py`.
4. Into the copy with `tools/promote.py`: the gerber zips, fab PDFs, the 4 CSVs, COST_SUMMARY.md, SOURCING_TABLE.md,
   BOOST_BOM.xlsx, CLEARANCES.md, the new STEP (the old STEPs: ask). ORDER_CHECKLIST.md by hand (total, via counts).
   Keep NOT_FOR_FAB.txt until the user says ship.
