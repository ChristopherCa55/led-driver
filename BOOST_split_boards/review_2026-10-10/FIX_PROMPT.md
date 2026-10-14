# Task: fix the problems found in the 2026-10-10 schematic and PCB reviews (BOOST LED driver)

Fix the problems listed in the two review documents. Work in a new folder that is a copy of the shipped design.
**Never edit the shipped folders.** Take screenshots and pictures to check your work, and write a report when you are
done.

- You may move parts on the PCBs where that helps, except the fixed parts in section 3.
- You may choose different specs where they help, e.g. larger or more vias for the overloaded ones.
- Take your time. Finish and verify each step before starting the next, so nothing has to be redone.

This is a long, difficult task with many traps. Most of the traps come from facts that are not visible in the review
itself. Those facts are written down below. Read this whole prompt before doing anything, then follow it in order.

Paths: `ROOT` = `C:\Users\bubba\OneDrive\Documents\led-driver`, `BSB` = `ROOT\BOOST_split_boards`.

---

## 1. Read first, in this order

1. **All your memory files**, especially:
   - `no-weakened-drc-rules`
   - `check-in-at-decisions`
   - `verify-part-specs`
   - `shipped-file-handling`
   - `never-rerun-onto-user-files`
   - `schematic-comment-style`
   - `ipc2221-short-necks`
   - `boost-tooling-reference`
   - `boost-routing-status`
2. **The two reviews** and everything they point to:
   - `BSB\review_2026-10-10\SCHEMATIC_REVIEW.md`: 19 items, with screenshots in `lt\` and `kicad\`.
   - `BSB\review_2026-10-10\PCB_REVIEW.md`: power items P1-P9, card items C1-C6, and the open 10-02 items, with
     pictures in `img_pcb\`. It was corrected after it was first written; read the corrected text.
   - `BSB\review_2026-10-10\pcb\checks\power_checks.txt` and `card_checks.txt`: every island, slice, neck, hot spot
     and return gap, with coordinates.
   - `BSB\review_2026-10-10\pcb\solve\now_solve.txt`: the DC solve of the shipped power board.
3. **The design's own documents:**
   - `ROOT\BOOST_package\README.md`, `BUILD_NOTES.md`, `CLEARANCES.md`, `ORDER_CHECKLIST.md`, `SOURCING_TABLE.md`.
   - `BSB\power6_2026-10-01\README.md`: how every power-board check was run, and the 10-02 readiness review.
   - `BSB\card6_2026-09-30\README.md` and `BSB\card6_2026-09-30\in4plane\README.md`: why the card has no solid plane.
4. **The header and docstring of every tool you will use** (section 6). Never run a tool you have not read.

**Many review items touch earlier decisions.** For each item, search the project's READMEs and memory for an earlier
decision before proposing a fix. For example, the pot address (item 2) already has a documented firmware workaround,
the card's plane situation was the user's choice, and M8-M10 are screwed to the case floor through thermal pads.

## 2. Ground rules (none of these may be broken)

**The shipped files.**
- Never write to `ROOT\BOOST_stuff`, `ROOT\BOOST_package`, `ROOT\BOOST_schematic_cleanup` or `ROOT\BOOST-github`.
- Never delete anything there either, including the `~$BOOST_BOM.xlsx` lock files.

**DRC and electrical checks.**
- Never loosen a DRC rule or a netclass value, and never add a DRC exclusion or a "Rule area" exception to make
  something pass. Tightening is fine.
- Every saved board must end with DRC 0 errors and 0 unconnected, with refilled zones and `--schematic-parity`
  clean.
- The warning count must not rise above the baseline you record in 4.3. If it does, explain each new warning.
- ERC must be 0 on all three KiCad projects (main, power, card), and `sync_check.py` must pass.

**Part data.**
- Use datasheets only, and cite the source for every part figure.
- Say clearly when something could not be verified.
- Ask before downloading anything. Never bypass a bot check.

**Decisions belong to the user** (section 5). These include:
- circuit or part changes;
- net renames;
- accepting any regression in any measured number;
- moving a fixed part;
- changing anything the user wrote or placed themselves: their notes, their GND vias, their placement;
- the card strategy.

Ask with numbers, 2-3 options and a recommendation. When unsure, ask; do not guess.

**New items on a schematic.** Every new note, label or symbol, and every moved symbol, needs the user's OK on a
picture before it is final. The user wants notes very brief, right next to their part, and never stating the obvious.

**Never re-run a generator onto a file that already exists.**
- Every result gets a new name.
- Check that the output path does not exist before writing.
- `ascmodel.Asc.write` refuses to overwrite; keep it that way.

**Scripts.**
- Write scripts with the Write tool. Heredocs mangle backslashes.
- Never run `rm` on an unguarded variable. Use `mktemp -d` or `${VAR:?}`, or move things aside instead of deleting.

**If a command is interrupted,** check what it actually did before saying it did nothing.

**Open files.**
- Before writing any KiCad file, check for lock files (`~*.lck`).
- Before writing an `.asc`, check that LTspice does not have it open (look at the process command lines).
- If either is open, ask the user to close it.

**KiCad Python traps:**
- `pcbnew.SaveBoard` drops the netclasses from `.kicad_pro`. Copy the project's `.kicad_pro` and `.kicad_dru` back
  beside the board before any DRC. Never `sed -i` a `.kicad_pro`.
- Prefer `kicad-cli pcb drc --refill-zones --save-board` for refills. It saves the board without touching the
  `.kicad_pro`.
- Preserve the file's line endings (CRLF) when editing text-format KiCad files.
- After a few rounds of `BOARD.Remove`, `GetTracks()` and `GetConnectivity()` return bare SwigPyObjects. Keep your own
  item list, save, and reload.
- A via or track end joins a pad only when one centre lies inside the other.
- `kicad-cli sch export netlist` writes a `.kicad_prl` beside the schematic.

**Freerouting 2.4.1 quirks** (if you use it): it ignores `-inc`; the SES omits fixed wiring; it treats a track as
connected only at the pad centre; it necks tracks down to 0.12 mm. See `boost-tooling-reference`.

**LTspice:**
- The `.asc` is latin-1; LTspice netlists are UTF-8.
- A full-save 30 ms run writes about 1 GB. Run no more than 3-4 in parallel, and watch the disk.

**Do not trust the review blindly.** Verify every item on the files before fixing it. The review already had one
wrong suggestion, since corrected: R53's GND vias looked movable but are its LED-current return. If the review and the
files disagree, the files win; note it in the report.

## 3. Parts that are mechanically fixed (do not move without asking)

From `BUILD_NOTES.md`, `CLEARANCES.md` and the case drilling (`BSB\case_drilling_2026-09-15\`):

- **J10 (power board, top) and J11 (card, underside).** These are the board-to-board stack connector. Their pin
  positions must stay aligned.
- **H5-H8.** The four standoffs: floor studs plus 20 mm card standoffs. The power board's keepouts and the card's
  holes match them.
- **M1, M8, M9 and M10, and their tab-screw holes and washer keepouts.**
  - The screws go into tapped holes in the case floor (rev B drilling), and the FETs sit on thermal pads.
  - Screwdriver access matters: M8's screw is under the card, and the J9 bundle passes near M10's screw.
- **Both board outlines, the corner notch and all mounting holes.**
- **J1-J8** (the battery and LED wire pads) and **J9** (the card's wire pads).
- **Heights and clearances in `CLEARANCES.md`:**
  - the lid clearance over the card's top parts (U18 and U28 have 1.11 mm);
  - the standoff washers under the card near D6, R94, D3 and R84.

Any other part may move if courtyards, DRC and those clearances all still pass. Every move changes the CPL, so it must
be regenerated at the end. If a move might affect the 3D clearances, re-run the clearance check in
`BSB\assembly_3d_2026-09-30\` (`write_clearances.py`; read its README first) and report it.

## 4. Setup and baseline (do this completely before changing anything)

### 4.1 Make the copy

1. Copy `ROOT\BOOST_package` (the most complete folder: KiCad, LTspice, BOM/CPL CSVs, cost and order docs) to
   `ROOT\BOOST_review_fixes\`. If that folder already exists, stop and ask.
   - Do not copy lock files (`~$*`, `*.lck`), `*-backups\` folders or `.kicad_prl` files.
2. Put a `NOT_FOR_FAB.txt` in the copy until the user approves the result.
3. Create a work folder `BSB\review_fixes_<today's date>\` for tools, scratch boards, pictures, logs and the report.
   - Name scratch boards `*_NOT_FOR_FAB`.
   - Inside the copy, the project files keep their names, so the schematic-to-board links still work.

### 4.2 Check the starting point

Before copying, check these SHA-256 prefixes in BOOST_package (they are identical in all three shipped folders):

| File | SHA-256 prefix |
|---|---|
| `KiCad\BOOST.kicad_sch` | 899c761c |
| `KiCad\BOOST.kicad_pro` | 6ac4b763 |
| `KiCad\BOOST_power_RC2.kicad_sch` | 88faea82 |
| `KiCad\BOOST_power_RC2.kicad_pro` | 16d4c3f9 |
| `KiCad\BOOST_power_RC2.kicad_pcb` | 01703432 |
| `KiCad\BOOST_power_RC2.kicad_dru` | 0ad32cac |
| `KiCad\BOOST_control_RC2.kicad_sch` | f57cae74 |
| `KiCad\BOOST_control_RC2.kicad_pro` | 85455735 |
| `KiCad\BOOST_control_RC2.kicad_pcb` | d34d1202 |
| `KiCad\BOOST_control_RC2.kicad_dru` | cb97d38c |
| `LTspice\BOOST.asc` | 1f008632 |
| `README.md` | b9a14fbb |

If any of them differ, stop and tell the user. The reviews were made on exactly these files, and the user may have
edited since; review coordinates could then be wrong.

### 4.3 Record the baseline

Run every check below on the **unmodified copy** and save the outputs in `work\baseline\`. Each tool must reproduce the
review's numbers before you rely on it as a gate.

**KiCad checks:**
- ERC on all three projects.
- DRC with `--refill-zones --schematic-parity --severity-all` on both boards: errors, unconnected and the warning list.
- `sync_check.py`.
- `kicad_sheets_2026-10-09\tools\check.py` on a copy of the KiCad folder. Note which parts of it still apply; its
  reference netlist predates any circuit change you make.

**LTspice checks:**
- `ltspice_equiv.py` with `--ref` pointing at a pristine copy of the shipped LTspice folder. The unmodified copy must
  pass E1-E5. If it does not, find out why before using it.
- One baseline simulation with the shipped `.tran`, saving the `.meas` results. You need these only if you change a
  directive or the circuit.

**Power-board checks** (the commands are in section 6):
- The copper export.
- The DC solve. It must match `review_2026-10-10\pcb\solve\now_solve.txt`.
- `pcb_checks.py` with `--solve`. It must match `power_checks.txt`.
- `loop_L6.py`, the commutation-loop inductance.
- `gnd_heatmap.py`, the GND voltage and the LED sense offsets.
- `plane_cover.py`, sense nets over GND. The 10-02 figure was 74 %.
- `gate_return.py` for every gate path. Known: M2 42 % unreturned, M7 38 %. Identify the rest (M1, M3/M6, M4/M5,
  M8-M10) from the board: each gate net, its driver-side net, and its return net.
- `thermal6.py` for U16 Tj (about 118 °C). See the U16 section of `power6_2026-10-01\README.md` for how it was run.

**Card checks:**
- The export and `pcb_checks.py ... card`.
- `card6_2026-09-30\tools\sens_check6.py`. The kept values: U2 In+ 65.6 %, V_err 90.4 %, Current 82.4 %.

**The metrics table.** Put the numbers in `work\METRICS.md`, one row per metric and one column per accepted step. The
first column is the baseline. Every later step adds a column. Any number that gets worse is flagged and needs either a
reason the user accepts or a revert.

## 5. Decisions to get from the user before editing

Do the research first: datasheets (ask before each download), simulations and what-ifs. Then ask **all** of these in
one batch, each with the numbers, 2-3 options and your recommendation. Do not start the matching work until the user
answers. You may start the work that needs no decision while you wait.

**D1. I2C pull-ups (schematic item 1).** SCL and SDA have no pull-ups, so the bus relies on the Arduino's internal
ones.
- Find the actual Arduino board in the README / BUILD_NOTES J9 section, and the bus speed and capacitance the firmware
  will use.
- Adding two resistors on the card is a circuit change: LTspice (optional), the main KiCad page, the card sheet, card
  placement and routing, and the BOM/CPL. Prefer JLC Basic parts.

**D2. U26 HVC/A0 with R102 (item 2).** A firmware workaround (probe 0x2C and 0x2D) is already documented. Options:
documentation only, or a stronger pull-down whose value comes from the MCP4451 datasheet (DS22267A).

**D3. D19 against the LX peaks (item 3).** Check the 5.0SMDJ54A breakdown from its datasheet against the simulated LX
peak and the `.meas Ptvs` result. Is D19 conducting every cycle? Propose a change only if the numbers say so.

**D4. M8-M10 heat (item 4).** They are screwed to the case floor through thermal pads. Look for an earlier thermal
estimate. This is probably a documentation item; say what the numbers are.

**D5. `.ic` with non-existent nodes (item 5).** Removing or correcting the C10/C5/C2 terms changes a directive.
- Show the simulated difference: the key `.meas` values before and after.
- The new directive text must be added to `approved_changes.json`, which needs the user's OK first.

**D6. Net renames (item 7)** versus notes only:
- M2_ON vs out_2_on / out_3_on;
- the U18 nets named "4" to "10";
- Out / Out-;
- IREF1 vs IREF1_input;
- the terse names (0err_hi, 0A_hi, VerrGT0, set-, RESET-).

A rename ripples into the LTspice file, the main KiCad page, the board schematic(s) and the PCB net names, and every
check must then match. Recommend notes unless the user wants the renames.

**D7. Diode values "D" (item 13) and J1-J8 values (item 14).**
- Decide how to show the part numbers: change Value, or add a visible field.
- First check what the KiCad simulation fields (`Sim.*`) and the BOM tools read.
- Changing Value changes the footprint values on the PCBs; parity will catch a mismatch.
- Propose J1-J8 names from the nets: J1 Vin, J2 GND, J3 Vout_1, J4 Output1_drain, J5 Vout_3, J6 Output3_drain,
  J7 Output2_drain, J8 Vout_2.

**D8. Wording and placement of every new or changed note and title** (items 6, 8-11, 12, 15, 16, 19).
- Show pictures.
- Item 16's note is the user's own sentence; ask before rewording it.
- Item 17 (re-arranging the KiCad page to match LTspice, and a MOSFET symbol with a body diode) is out of scope
  unless the user asks.

**D9. The card strategy (C1-C3).** The card lost its two solid GND planes when the user chose 6 layers over 8 on
2026-09-30 (about $55 cheaper for 5 cards). A solid In4 plane was tried and abandoned the same day: the card needs all
six layers, and the 2 mm rules around U2 In+, V_err and Current block the corridor between U101 and U2/U5. Options:
- (a) go back to the 8-layer card (`BSB\previous\2026-09-30\before_card_6layer\`, sha 3335e701), re-checked against
  today's schematic;
- (b) move parts to open the corridor, then re-route with solid planes;
- (c) targeted fixes on the 6-layer card. Recommend (c) unless the user wants to pay for (a).

"In1 and In4 as solid GND with signals on In2/In3" hits the same routing limit. In2 and In3 are also only 0.12 mm
apart and 0.55 mm from the planes, so they would couple strongly to each other.

**D10. The loop-via fix (10-02 items).**
- **Options:** more vias next to the cap pads; larger drills; via-in-pad (filled, extra cost at JLC).
- **The trade-off:** every extra or larger GND via cuts antipads into the LX/Vin/Vout pours on In2-In4. That is why
  these vias were never added. Show the solve for every branch.
- **Check the fab limits:** the drill and annular ring sizes JLC allows on this stackup, and any price change.

**D11. User-placed copper:**
- the four GND stitching vias at the J4 entry (48-49, 109.4-110.2), added by the user on 10-02, which raised
  Output1_drain from 1.75 to 1.97 mΩ;
- the user's earlier gate reroutes;
- anything else the user placed by hand.

Do not move any of it without asking.

**D12. LX to M5 (P3).** The what-if showed that moving the vias in its necks gains only 3 %. Recommend leaving it as
a known item unless a second LX layer along the route becomes possible.

**D13. Cosmetic cleanup.** This covers the 674 / 2600 short jog segments and the duplicate tracks out of vias.
Recommend doing it only with a tool that proves connectivity is unchanged, only on routes already being touched, or
not at all.

**D14. Fab outputs at the end:** gerbers, drill, fab drawings, BOM/CPL, cost files, and the STEP if parts moved.
Generate them in the copy, still marked NOT_FOR_FAB, or wait for approval first.

## 6. Tools and exact commands

KiCad 10 lives in `C:\Program Files\KiCad\10.0\bin\` (`kicad-cli.exe`, and `python.exe` with `pcbnew`); it is not on
the Git Bash PATH. System Python has numpy, scipy, matplotlib and Pillow.

**Copper export** (refills the zones in memory):
```bash
"C:/Program Files/KiCad/10.0/bin/python.exe" BSB/power6_2026-10-01/tools/export_copper6.py BOARD.kicad_pcb OUT_cu.json
```

**DC solve of the power board**, about 6 min with 9 workers. `--only "BRANCH NAME"` solves a single branch in under a
minute. Run from BSB:
```bash
python power6_2026-10-01/tools/solve_copper6.py CU.json route_2026-09-16/branches_power.json --stack JLC061611-7628D --out SOLVE.json --dump DUMPDIR --workers 9
```

**Compare two solves:**
```bash
python power6_2026-10-01/tools/compare_solves6.py BASE=a.json NEW=b.json
```

**Pour and routing checks:**
```bash
python review_2026-10-10/pcb/pcb_checks.py CU.json power OUTDIR --solve DUMPDIR route_2026-09-16/branches_power.json
```
For the card, use `card` instead of `power` and leave out `--solve`.

**Pictures:**
- `python review_2026-10-10/pcb/make_crops.py CU.json OUTDIR/TAG_grid.npz IMGDIR SPEC.json`
- Reuse the review's `spec_power*.json` and `spec_card.json` for before/after pictures of the same areas.
- `render_layers.py` draws full layers.

**Other power checks:** `loop_L6.py`, `gnd_heatmap.py`, `plane_cover.py`, `gate_return.py` and `thermal6.py`, all
in `power6_2026-10-01\tools\`. Read each header.

**`check_variant.sh` was written for the 10-02 boards.** Its parity step uses an old netlist and an assignment file
that predate R14's removal and the new board schematics, so do not trust its parity line. Run its steps one by one, and
do parity with `kicad-cli pcb drc --schematic-parity` inside the copy's own project.

**What-if testing (cheap and safe).** Edit a copy of the export JSON: add or remove copper polygons there, then re-solve
one branch. That is how the review got its P1 and P3 numbers; see the `whatif_*` files in
`review_2026-10-10\pcb\solve\`. Test an idea this way before editing a board.

**Board editing:** scripted `pcbnew` on scratch copies in the work folder. Templates that were applied successfully
before:
- `power6_2026-10-01\tools\patch_m2_drive.py` and `patch_m7_drive.py`;
- `route_2026-09-16\tools\handroute.py`, `move_vias.py`, `move_parts.py`, `add_routes.py`, `fill_compare.py`;
- `card_route_2026-09-22\tools\` and `card6_2026-09-30\tools\` for the card: `fix_tangent.py`, `prune_dangling.py`,
  `stitch_island.py`, `route_card.py`, `sens_check6.py`.

**Schematic editing:**
- KiCad: `kicad_layout_2026-10-09\tools\` (`sexpr.py`, `kgeo.py`, `kwrite.py`; `render.py` and `svgtext.py` for
  pictures) and `kicad_sheets_2026-10-09\tools\` (`sync_check.py`, `check.py`, `pcb_set_field.py`).
- **Every part is drawn twice:** on the main page `BOOST.kicad_sch` and on its board sheet. Any change goes into both,
  then `sync_check.py`.

**LTspice:**
- Editing: `ltspice_layout_2026-10-05\tools\ascmodel.py`.
- Equivalence: `ltspice_layout_handoff_2026-10-05\tools\ltspice_equiv.py`. Do not edit `approved_changes.json`
  without the user's OK.
- Screenshots: `ltspice_layout_handoff_2026-10-05\tools\ltspice_capture.py`, plus
  `review_2026-10-10\capture_with_directives.py` when the directives must show.

**Fab:**
- `fab_2026-10-07\tools\make_fab.sh`. It refuses to plot unless DRC is clean and the stored fills are current. Its
  `fp-lib-table` line points at `BOOST_schematic_cleanup\KiCad\`; change that to the copy's KiCad folder in a copy of
  the script, not the original.
- BOM / cost: `fab_2026-09-24\tools\build_bom.py` and `cost_summary.py`, and `bom_2026-09-30\tools\jlc_parts.py` for
  stock.

## 7. Facts per item that the review does not spell out

### Power board

**12V route: P1 (the R1 funnel), P7 (M1's GND islands) and P8 (B.Cu / In4 slices).** One fix covers all three.
- **Today's route:**
  1. U16 and C25/C6;
  2. B.Cu around the M1 washer: (88, 48) - (98.7, 52) - (98.7, 59) - y = 65;
  3. a via at (82.0, 48.25);
  4. the In4 loop round M1's source (25.7 mm to cover 7 mm);
  5. the vias at (75.35, 45.95), (74.75, 43.85), (74.85, 43.05) and (76.95, 42.15);
  6. U19.16 / U19.11 and C30/C31.

  12V also feeds D9/D10/D21 and J10.19. Derive the exact topology from the board.
- **U19 (M1's gate driver) sits on B.Cu inside the R1 Vin funnel**, so 12V must still reach it. The goal is to get
  there with fewer or no vias through the Vin layers in the funnel (x 71-78, y 38-47 on F/In2/In3/In4): for example on
  B.Cu, without walling off M1's GND islands on In3/In4 and without looping round the washer.
- **The GND via (76.35, 39.45) is U25.2 / C31.2's ground.** It may shift slightly but must stay at those pads.
- **Target:** the Vin J1->R1 worst neck drops from 38.8 °C toward the what-if value of 28.9 °C. That figure assumed
  all five vias gone; keeping the GND via gives back part of it. Also: no new GND pieces, and the B.Cu 12V detour
  gone.

**D28/D29 Vin feed and Output 1's path to J3: P2 and P5.**
- **The feed:** a 1.0 mm Vin track (1.0 mm is the minimum for Vin; never narrower). It carries current only during
  pre-charge.
- **Today:** it slices GND on F.Cu, In3 and B.Cu, and sits inside the In3 Vout_1 pour, causing the Vout_1 pinch at
  (55-60, 68-72).
- **Re-route it, then improve Output 1:**
  - Today Output 1's only path to J3 is one ~70 mm In3 path, 8.46 mΩ, against 3.08 and 1.62 mΩ for outputs 2 and 3.
  - For example, extend the In4 Vout_1 pour (now 65-82, 55-90) toward J3.
  - Target about the other outputs' level, without making any other branch worse.
- **The pre-charge surge path:** report the feed's resistance before and after. You can add a branch in a new copy
  of the branch file. Any meaningful change goes back to the surge numbers in `BSB\precharge_surge_2026-09-30\`.

**Gate drive pairing (P6 and the 10-02 gate items).**
- Every gate track must stay close to its return: m2_source for M2/M7, m3_source for M3/M6, m4_source for M4/M5.
- **The m4_source track through the In4 Vout_3 pour is ch3's high-side drive return.** Moving it out of the pour must
  keep it alongside GATE_M4/GATE_M5.
- Check `gate_return.py` before and after every gate-area change. M2 (42 %) and M7 (38 %) must not get worse;
  improving them is one of the open items.
- **The D11- via (75.6, 70.4)** is on M2's gate drive (R13). Leave it.

**Loop vias over the IPC rating** (from 10-02):

| Loop via | Rating | Pad it serves |
|---|---|---|
| ch2 (33.9, 67.5) | 3.6x | probably C3.2 |
| ch3 (88.9, 84.6) | 2.7x | C76.2 |
| ch1 (73.4, 66.0) | 2.1x | probably C1/C72 |
| Vout_3 (92.8, 86.4) | 2.8x | probably C4.1 |

Identify each pad from the board.
- The GATE_M4 via at (90.55, 84.75) takes the spot next to C76.2. Moving it, while keeping GATE_M4 paired, frees room
  for a second C76 GND via.
- `via_rating()` in `solve_copper6.py` gives each drill's rating. The current scales with barrel area^0.725, so a
  larger drill alone helps much less than an extra via.
- These are plane-connected vias: report the ratings, but the memory rule says they are not pass/fail. The goal is to
  bring them down where the antipad cost is acceptable (D10).

**Drain strips (P4).**
- **R53's four GND vias** at (40.1-42.3, 96.05) are its pad vias, carrying its 2.37 A return. They stay.
- **The three analog_5V vias** (U12.5's supply) in the Output2_drain strip may move.
- **The two IREF1_input vias** in the Output1_drain pour are C45.1's connection; they move only if C45 moves.
- **The J4 stitching vias** are D11.

**Sense routing (P9 and the 10-02 sense-over-GND item).**
- **The `Current` track** (U25 out to J10) runs 46 mm for 27 mm on F.Cu and slices F.Cu GND. Re-route it shorter,
  over GND.
- `plane_cover.py` must not drop. Improving SNS_CH3, ISNS_N and IREF3_input is part of the open item.

**U16 Tj (about 118 °C, limit 125).** Copper and vias around U16's TO-263 tab are the layout options. A part change
is a decision.

**LX to M5 (P3).** See D12.

### Control card

- **Respect `BOOST_control_RC2.kicad_dru`:**
  - no foreign via within 2 mm of U2 In+ or Current copper (GND stitching vias excepted);
  - via drill at least 0.3 mm;
  - NPTH hole clearance 0.3 mm.

  The 2026-09-30 notes add: logic stays 2 mm from In+ and V_err on F and B.
- **`sens_check6.py` must not get worse.**
- **For option (c):**
  - `card_checks.txt` lists every track that alone keeps two GND pieces apart: the lines marked "SEPARATES". Fix the
    longest first. Examples: 0err_hi and D5- on In4, which split it into 627 + 318 mm², and 0err_hi, U101A-Y and SDA
    on In1.
  - Stitch the one-via pieces, e.g. In1's 31 mm² piece at (73.2, 86.9).
  - Separate the stacked pairs in C5, e.g. Reset_raw over SDA and IREF1 over SDA.
- **The card is low-current.** The goal is GND continuity under signals, measured by the piece count and area per
  layer, the return-gap list and `sens_check6.py`.

### Schematic

- **ERC, parity and sync after every change.** The PCB footprints must carry the same values; use
  `pcb_set_field.py` or the board's update-from-schematic in a scratch copy.
- **LTspice edits:**
  - Geometry-only edits (moving directives into a group, adding comments) must pass `ltspice_equiv.py`.
  - Anything that changes a directive (the `.ic` line, deleting the commented-out `.ic`, deleting the unused LED
    models) is an approved change (D5/D8).
- **U18 (CD4017B) gets its supply by the net name `5V` in its SpiceModel.** Do not rename that rail.

## 8. How to work

1. **One change at a time.**
2. **For each step:**
   1. snapshot the accepted state in `work\stepNN\`;
   2. make the change on a scratch copy;
   3. refill, and restore `.kicad_pro` / `.kicad_dru` if Python saved the board;
   4. run DRC with parity, and ERC/sync for schematic steps;
   5. export the copper;
   6. run the solve, `pcb_checks` and the other metrics that apply;
   7. update `METRICS.md` and `CHANGELOG.md` (what, why, numbers);
   8. look at the before/after pictures.
3. **Promote the change into `ROOT\BOOST_review_fixes\`** only when every gate passes and no metric got worse
   without the user's OK.
4. **Order:**
   1. the schematic documentation fixes that need no decision;
   2. the power board: 12V route, then the D28/D29 feed and the Vout_1 path, then the loop vias, then gate pairing
      and sense routing, then the drain strips, then the other slices;
   3. the card;
   4. the approved circuit changes, through every layer: LTspice, KiCad main, board sheet, PCB, BOM/CPL;
   5. the outputs (D14).

   Re-check earlier steps' metrics after each later step; later steps can undo earlier gains.
5. **Look at every picture you make.** Open the PNG and check it; generating it is not enough. For PCB changes, use
   the same crop before and after, plus KiCad's own render of the area (`kicad-cli pcb export svg` for the layer).
   For schematics, use KiCad's SVG export and LTspice captures.
6. **If an item cannot be fixed** without breaking a rule, moving a fixed part or causing a regression, stop working
   on it. Record why, with numbers, and move on. Do not force it.

## 9. The report

Write `BSB\review_fixes_<date>\FIX_REPORT.md` and add a short "what changed" section to the copy's README.

**For every review item** (schematic items 1-19, P1-P9, C1-C6 and the 10-02 items):
- the status: fixed, partly fixed, not fixed (and why), or waiting for a decision;
- what changed, with coordinates;
- the before/after numbers;
- the before/after pictures.

**Also include:**
- the full `METRICS.md` table (baseline against final), with every regression and who accepted it;
- DRC (errors, unconnected, warnings), ERC, parity, sync and `ltspice_equiv` results for the final files;
- every changed file with its old and new SHA-256;
- everything you could not verify;
- every place where the review was wrong or out of date.

**Do not copy anything into the shipped folders.** The user will decide what to ship after reading the report.
