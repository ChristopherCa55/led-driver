# Step 5g completion work — 2026-10-12

**Status: ready for placement review; not promoted; NOT FOR FAB.**

This continues `../step05g/STEP.md`. Its LTspice approval-record and BOM/CPL tasks are now complete. The original step05g PCB and schematics have not been regenerated or changed. The current chat has asked the user to approve the placement picture; no answer has been received as of this record.

## Candidate

- PCB and schematics: `../step05g/kicad/`.
- R106: 4.7k, 0603, F.Cu, centre (57.15, 94.00), rotation 0; pad 1 = 5V, pad 2 = SCL.
- R107: 4.7k, 0603, F.Cu, centre (55.15, 101.45), rotation 0; pad 1 = 5V, pad 2 = SDA.
- Front picture: `../../img/step05e/j9_F_after_5g.png`.
- In2 picture: `../../img/step05e/j9_In2_after_5g.png`.
- Placement includes raised I2/SCL text, H3 reference text 0.35 mm lower, the smaller J9 front courtyard, and the 5V via adjustment. J9's back courtyard is unchanged.
- The user's saved U26D move is preserved in the candidate card schematic.

## Work completed in this continuation

1. Recorded the already-approved `solver=alt` directive in `../../../ltspice_layout_handoff_2026-10-05/tools/approved_changes.json`, with the user's words from handoff section 5.2. Recorded the other carried-forward decisions in `../../ANSWERS.md`. Originals are backed up in `../../../previous/2026-10-12/before_step05g_completion_records/`.
2. Ran `ltspice_equiv.py` against `../step05b_lt/LTspice/BOOST.asc`: **E1–E5 PASS**. See `ltspice_equiv.json` and `ltspice_equiv_retry.txt`. No transient simulation was rerun. The temporary reference/candidate netlist copies were retained under `tmp/` using `--keep`.
3. Authored the candidate card BOM/CPL using Artifact Tool in `step05g_fab.mjs`, preserving the source CSV quoting and CRLF endings. Outputs are in `fab/`; exact edits and hashes are in `fab/CHECKS.json`.
   - R106/R107 join existing 4.7k 0603 C23162.
   - R99/R102 move from 10k C25804 to the already-approved 1k 0603 C21190.
   - CPL gains R106 and R107 on Top, rotation 0, with coordinates read from the candidate PCB. All existing CPL rows are unchanged.
4. Rechecked the unchanged step05g validation reports: card DRC 0 errors, 0 unconnected, parity 0, one existing J11 library warning; ERC 0 on all three schematics; schematic sync 0 differences across 326 units. These are the existing 2026-10-12 09:39 reports, not a newly executed KiCad gate run.
5. Read the PCB through KiCad's Python API to confirm both pull-up values, 0603 footprints, pad nets, positions, front side, and rotations; also confirmed R99/R102 = 1k.

The initial equivalence invocation could not write its system temporary folder. Retrying with TEMP/TMP inside this new workspace folder completed successfully. The failed attempt did not change the design.

## Next actions

1. Obtain the placement approval requested in the chat, as required by `HANDOFF_2026-10-12.md` section 5.4. If the user requests a different placement, make a new candidate folder and regenerate its dependent outputs.
2. Rebuild approved card steps 7 and 8 on step05g in fresh folders, using the commands in handoff section 5.4, and run their gates.
3. Immediately before promotion, recheck working-copy hashes and locks. Preserve and acknowledge the user's U26D edit; reconcile its expected old hash in `promotions.log` as described in handoff section 5.3. Do not bypass `promote.py`.
4. Promote approved source files only through `tools/promote.py`, then run final gates on the working copy in a new folder. Candidate CSVs here have not been copied into the working copy.
5. Full manufacturing/STEP/BOM workbook/cost regeneration remains pending the wider approved review work. The working copy's current fab outputs remain old; do not use them for manufacture.

No files in `BOOST_review_fixes`, `BOOST_package`, `BOOST_stuff`, `BOOST_schematic_cleanup`, or `BOOST-github` were changed by this continuation.
