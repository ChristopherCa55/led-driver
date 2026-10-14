# LTspice re-layout of BOOST.asc: handoff

**Start here.** This folder tells you how to redraw the LTspice schematic of a 3-channel 100 W LED driver so that a
person can read it, and how to prove that you did. It holds the rules, the block plan, and the checking tools. The
tools are calibrated against the original drawing and against a failed earlier attempt.

**Read in this order:** this README → [LAYOUT_RULES.md](LAYOUT_RULES.md) → [BLOCKS.md](BLOCKS.md) →
[CHECKS.md](CHECKS.md). [RESEARCH.md](RESEARCH.md) explains where the rules come from.

---

## 1. The job

Redraw `BOOST.asc` so that a human can follow it. Every connection stays electrically identical.

> **An electrically identical schematic that is harder to follow is a failed result, even if it passes every
> individual check.** The checks are necessary, not sufficient. The user's judgement at the two check-ins decides.

**In scope:**

- the layout of the LTspice schematic only: positions, wires, labels, text placement, block frames and notes;
- three approved instance renames (§5).

**Out of scope:**

- KiCad, the PCBs, and the project structure;
- any change to values, models, directives, `.asy` or `.lib` files.

**The source of truth:** `reference/LTspice_original/BOOST.asc` (sha256 `6492c5d0…`). It is a frozen copy of
`led-driver/BOOST_stuff/LTspice/BOOST.asc` with its 23 symbol and model files.

## 2. Why the last attempt failed (don't repeat it)

On 2026-10-05 another AI produced `reference/reorg_2026-10-05_attempt/BOOST.asc`. It is electrically identical, but
the user found it *less* readable than the original. It removed wire crossings by cutting the circuit into islands
joined by net labels.

Measured with this folder's tools (`calibration/`):

| | Original | 10-05 attempt |
|---|---|---|
| Separate pieces in the power path (one wired drawing wanted) | Vin/LX/rsense_lo/Vout wired; ground in 19 pieces | **16 islands**; Vin 6 pieces, LX 7, Vout_2 7 |
| "Orphan" parts (every pin touches only a label) | 1 (C54) | **30**, including L1, M1, D19 and the 220 µF caps |
| Signal nets split by labels inside a block | 7 | **29** |
| Label jumps tracing battery → R1 → L1 → FETs → outputs | 1 | **13** |
| Label instances: Vin / Vout_2 / LX / Out- | 4 / 1 / 1 / 1 | 9 / 9 / 7 / 8 |
| Text collisions (estimated) | 926: crammed, as the user said | 948 |
| Tracing tasks within budget (of 10) | 8 | 1 |

It also deleted one of the user's notes, and it described its result as passing every check. **This time the
checks are not yours to define:** they are in `tools/`, and they fail that attempt.

## 3. What the user wants (their words, condensed)

- **Blocks of related parts, few and large.** Every block has more than ~5 parts, except the current-sense
  amplifier (its own block, directly above R1) and the voltage regulators.
- **The high-current path is one continuous wired drawing.** It runs: battery and cable → Vin → input caps → R1 →
  L1 → LX → M1 and the three FET pairs → output caps, with the pre-charge diodes.
- **Simulation-only parts sit where they act**, wired to the circuit and named clearly.
  - The battery, cable resistance and cable inductance are three wired parts.
  - `Vin` is labeled *after* the cable, near the battery, so that the battery visibly is not Vin.
- **More space between parts, and no overlapping text.**
- **One block per channel holds the pot, the sample-and-hold and the integrator** that raises `.1Vref_x`.
- **All the control logic is in one block**, organised in groups of three: VerrGT0 fans out to three NANDs side by
  side → three delays → three inverters → ena_out_1..3.
  - If that cannot be made readable, the user pre-approved splitting it into two blocks (BLOCKS.md §3).
- **Connections between blocks leave at the block edge** through a short visible wire and a clear label, never from
  the middle of dense circuitry. A clear wire crossing beats a label hunt.
- **The three channels look identical** wherever they are identical.
- **Bypass capacitors follow industry practice:** each sits at the supply pin of the IC it serves.

## 4. Order of work and the two ★ check-ins

1. **Set up.** Work in a NEW folder: `BOOST_split_boards/ltspice_layout_<date>/work/`.
   - Copy `reference/LTspice_original/*` there.
   - Never write to `BOOST_stuff`, `BOOST_reorg_2026-10-05`, `BOOST_package` or `BOOST_schematic_cleanup`. The user
     has two of these open in LTspice right now.
2. **Read** `bypass_map.json`; it says where each bypass cap goes. Six owners are ambiguous; draw them where the
   map says for now.
3. **Pilot.** Redraw only these blocks, and leave the rest of the sheet where it is:
   - **PWR** (power path), with **ISNS** above R1;
   - the whole **channel-1 row**: CREG1 ⇄ REF1 → EA1.

   Nets from the pilot blocks to parts not yet moved use temporary port labels; list them in your report. The pilot
   must pass:
   - `ltspice_equiv.py` (all of E1–E5);
   - `asc_layout_check.py --blocks PWR,ISNS,CREG1,REF1,EA1` (all rules and T1–T4, T10);
   - LTspice captures of each pilot block, which you look at yourself.
4. **★ Check-in 1:** stop and show the user. Send:
   - the LTspice captures;
   - the checker output;
   - the trace table;
   - the list of temporary labels;
   - the 6 ambiguous bypass owners, each with a proposed answer;
   - a proposed new wording for the user's note "I added a lot of capacitors … which are all put here", which no
     longer matches the drawing. The note's text may only change with their OK.

   **Revise the pilot** if the user finds anything hard to follow, or if any check fails. Re-plan with the user after
   two failed revisions.
5. **Copy the channel-1 geometry to channels 2 and 3.** The parts keep their own names and values; only the drawing
   is copied, so the copies stay exact (H10).
6. **Lay out the remaining blocks:** SUP, GATEDRV and CONTROL.
   - If CONTROL fails H3, H4 or H8–H10, or T5–T8, use the pre-approved split and say so.
7. **Clean up inside every block.** Align, space and orient everything, and place every text window, using the
   LTspice captures. Frames, labels and passing checks do **not** replace this step.
8. **Run every check on the saved file and write the report** (template in CHECKS.md §5). **★ Check-in 2.**
9. **Copy the result into the user's folders only after their own-words OK**, backing up what you replace to
   `BOOST_split_boards/previous/<date>/`.

## 5. Ground rules

- **The tools are not yours to change.** Do not edit:
  - `tools/*`;
  - `blocks.json`;
  - `bypass_map.json` (except setting `confirmed_by_user` after the user answers);
  - `approved_changes.json`.

  If a rule seems wrong for a real layout, write it in `EXCEPTIONS.md` with the reason and a screenshot, and ask at a
  check-in.
- **Approved deviations, the only ones:**
  - instance renames `SIM_VBATT`→`SIM_BATTERY`, `SIM_RCABLE`→`SIM_CABLE_RESISTANCE` and
    `SIM_LCABLE`→`SIM_CABLE_INDUCTANCE`;
  - new names on nets that were auto-named (e.g. the battery terminal);
  - new comments (block titles, short notes).
- **Never rename an existing net.** `.ic` and `.meas` lines and U18's supply depend on the names. U18 is powered by
  the net **name** `5V`.
- **Verify the saved file, not what you think you wrote.** Every reported result must come from running the tools on
  the file on disk.
- **Report honestly.** Separate electrical from visual results, and performed from not performed. Name anything you
  could not check.
- **Before running `ltspice_capture.py`,** tell the user it will open and close LTspice windows. They approved this
  for the calibration run on 2026-10-05; ask again in your session.

## 6. Files

| Path | What |
|---|---|
| `LAYOUT_RULES.md` | Floorplan, hard rules H2–H12, forbidden patterns, LTspice drawing details |
| `BLOCKS.md` | Every block: members, purpose, inputs and outputs, boundary decisions, copies, bypass owners |
| `CHECKS.md` | How to run each check, what it proves, the report template |
| `RESEARCH.md` | Published guidance and manufacturer examples behind the rules |
| `PROMPT.md` | The task statement that started this handoff |
| `EXCEPTIONS.md` | Where you ask for an exception (empty) |
| `blocks.json` | Machine-readable blocks, copies, interfaces, traces and thresholds (read by the checker) |
| `bypass_map.json` | Owner IC of every bypass cap, from PCB pad positions (`tools/bypass_match.py`) |
| `tools/ltspice_equiv.py` | Electrical checks E1–E5 (runs LTspice `-netlist` on temp copies) |
| `tools/asc_layout_check.py` | Layout rules H2–H12, review flags, tracing tasks T1–T10 |
| `tools/ltspice_capture.py` | Screenshots as LTspice draws them: overview + each block |
| `tools/bypass_match.py` | Regenerates `bypass_map.json` (run with KiCad's Python) |
| `tools/selftest_equiv.py` | Proves E1–E5 catch damage (6 cases) |
| `tools/approved_changes.json` | The only deviations the electrical check accepts |
| `tools/ascgeo.py` | Pin geometry helper (rotate-then-mirror transform, verified) |
| `reference/` | The frozen original and the failed attempt, each with their symbol and model files |
| `calibration/` | Both checkers run on the original and on the attempt; self-test; LTspice captures |

## 7. Environment (verified 2026-10-05)

| Tool | Path / note |
|---|---|
| LTspice | `C:\Program Files\ADI\LTspice\LTspice.exe` 26.0.1. `-netlist` works in batch; local help is in `LTspiceHelp\` beside it |
| Python | `python` = C:/Python313 (numpy, matplotlib, Pillow); runs every tool except `bypass_match.py` |
| KiCad Python | `C:/Program Files/KiCad/10.0/bin/python.exe` (has `pcbnew`), for `bypass_match.py` only |
| LTspice symbols | beside the `.asc`, plus `C:\Users\bubba\AppData\Local\LTspice\lib\sym` |

**`.asc` files are latin-1.** Netlists from LTspice 26 are UTF-8 (`X§M1`, `µ`). A `§` in a TEXT line makes
`-netlist` hang behind a dialog, so never write one.
