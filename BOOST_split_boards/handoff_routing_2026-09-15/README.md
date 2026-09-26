# BOOST power board — place and route handoff

2026-09-15. Start here. Read this file, then `ROUTING_SPEC.md`, then `RUNBOOK.md`, then
`OPEN_QUESTIONS.md`. `PROMPT.md` is the task statement you were given.

All paths are relative to the repository root `C:\Users\bubba\OneDrive\Documents\led-driver`
(called `led-driver/` below), unless they start with `./`, which means this folder.

---

## 1. What you are being asked to do

Produce a **fabricable 8-layer power board**: components placed for the real current paths, every
connection routed in copper, and KiCad's own DRC clean on the saved file.

1. **Placement.** A complete, DRC-legal placement already exists (`p15_b10_k1`, see §3). Use it as the
   baseline. You may keep it, polish it, or re-place from scratch — whichever gets the best numbers
   against the targets in `ROUTING_SPEC.md` §6. You must beat or match the baseline's score
   (38 of 49 agreed goals, 31 of 49 brief targets) and stay mechanically legal.
2. **Routing.** Route **every** net: power copper first (drawn deliberately, path by path), then
   signals. No net left unrouted; a ratsnest is not a deliverable.
3. **Verification.** Prove it with `kicad-cli pcb drc` on the *saved* file: **0 errors, 0 unconnected,
   no DRC exclusions, no weakened rules**. Plus the electrical checks in `ROUTING_SPEC.md` §8.

Second priority, after the power board is done and checked: re-place and re-route the **control card**
at 45 × 45 mm (§2.4). Don't start it until the power board passes.

### Deliverables

| # | Deliverable |
|---|---|
| 1 | Placed + fully routed power board `.kicad_pcb` (+ its `.kicad_pro` carrying the shipped rules) |
| 2 | `kicad-cli pcb drc --severity-all --format json` report from the saved file: 0 errors, 0 unconnected |
| 3 | Distance table vs the targets in `ROUTING_SPEC.md` §6 (regenerate with `ptable.py`, see `RUNBOOK.md`) |
| 4 | Copper solver table at **1 oz** and **2 oz** outer — every neck's IPC-2221 rise, every via's current vs rating (`ROUTING_SPEC.md` §7). The user picks copper weight B (1/1 oz) or C (2/1 oz) from this. |
| 5 | Top and bottom plots/renders of the finished board |
| 6 | A report in the style of `BOOST_split_boards/AUDIT_RESPONSE.md`: what changed, before/after numbers, what is still open |

### Order of work, with user check-ins (★ = stop and ask)

1. Read this folder and the source files in §3. Confirm you can load the board and run DRC.
2. Placement: baseline or improved. ★ **Show the distance table and both-sides plots before drawing any copper.**
3. Netclasses, custom rules (`.kicad_dru`), keep-outs.
4. Draw and solve the power copper. ★ **Show the 1 oz / 2 oz solver table; the user chooses copper weight.**
5. Route signals. Refill zones. Save. Run DRC on the saved file.
6. Write the report. ★ Hand back.
7. Only then: the control card.

---

## 2. The board in one page

### 2.1 What it is

A boost converter driving three high-power LED channels (RGB, ~2.4–2.6 A each) from a battery input,
in a sealed aluminium case. One schematic, split across two boards:

- **Power board** (this job): 74 × 86 mm, 8 copper layers, 124 footprints, 74 nets (355 pad-net assignments). Notched top-right
  corner for the battery cable. Outline x 30–104 mm, y 30–116 mm; the notch removes x 86–104, y 30–42.
- **Control card**: analogue + logic, currently 60 × 60 mm, to shrink to 45 × 45 mm and stack over the
  power board on a 21.21 mm header.

### 2.2 The power path (this is what the layout is *for*)

```
J1/J2 lugs ─┬─ C40/C69/C85 (3 × 680 µF input bank)
            │
            └─ R1 (2 mΩ 4-terminal shunt) ─ L1 (6.8 µH) ─┬─ M1  (main switch, LX → GND)
                                                          ├─ M7 ─ M2 ─ Vout_1 bank ─ J3/J4 ─ M10 ─ R52
                                                          ├─ M6 ─ M3 ─ Vout_2 bank ─ J8/J7 ─ M9  ─ R53
                                                          └─ M5 ─ M4 ─ Vout_3 bank ─ J5/J6 ─ M8  ─ R7
```

Ten HYG180N10 TO-220 FETs, all on **B.Cu**, bodies flat against the board underside, tabs down onto the
aluminium case floor through ~1 mm of compliant thermal pad. M1, M8, M9, M10 are screwed to the floor;
M2–M7 use a no-hole footprint variant.

Each switch pair (M7–M2, M6–M3, M5–M4) shares its source pins 2.54 mm apart, bodies on opposite sides
of one pin row. Each sink FET (M8/M9/M10) has its shunt about 3 mm from its source pin, with a net-tie
(NT1–NT3) on the shunt pad giving the channel op-amp a Kelvin sense point.

### 2.3 Currents (RMS unless noted) — the whole reason this is hard

| Net / path | Current |
|---|---|
| `Vin`, `rsense_lo` (J1 → R1 → L1) | **20.7 A** (18.4 A from the lugs, the rest from the input caps) |
| `LX` L1 → M1 | 15.8 A (IL peak ≈ 37.3 A; M1 instantaneous 40.5 A) |
| `LX` L1 → M7 / M6 / M5 | 7.05 / 7.69 / 8.35 A |
| `m2_source` / `m3_source` / `m4_source` | 7.05 / 7.69 / 8.35 A |
| `Vout_1` / `Vout_2` / `Vout_3` (bank AC) | 6.54 / 7.22 / 7.92 A |
| `Output1/2/3_drain` (LED cathode → sink FET) | 2.63 / 2.37 / 2.37 A |
| `Net-(M8-S)`, `Net-(M9-S)`, `Net-(M10-S)` (sink source → shunt) | 2.63 / 2.37 / 2.37 A |
| `GND` M1 source → input caps / J2 | 20.7 A (M1's own share 15.8 A) |
| Input-bank ripple | 10.36 A RMS at 14 V |

The previous layout ran 2.63 A on 0.15 mm tracks (they fuse) and hung 7 A branches on single Ø0.25 mm
vias. That is the failure mode to avoid.

### 2.4 Mechanical

Aluminium case, 128 × 90 × 33 mm inside, 10 mm floor. Stack from the floor up:

| Item | mm | Top above floor |
|---|---|---|
| Thermal pad + TO-220 body (4.57) | 1.00 + 4.57 | 5.57 = power board underside |
| Power PCB | 1.60 | 7.17 |
| Card gap (Samtec ESQ-115-44-G-D at J10 ↔ TSW-115-07-G-D at J11) | 21.21 | 28.38 = card underside |
| Control PCB + tallest top part (SOIC 1.75) | 1.60 + 1.75 | 31.73 (lid at 33.00) |

- 220 µF output cans (16.8 mm max) top out at 23.97 mm — the card **may** sit over them (4.4 mm clear;
  Panasonic needs 2 mm above the vent, so any card-underside part over a can must be ≤ 2.4 mm).
- L1 (Codaca CSCF3218, 19.0 mm) tops out at 26.17 mm — the card must **never** sit over L1.
- Every screwed TO-220 tab hole gets a **3.75 mm-radius washer keep-out on all copper layers**, and
  nothing taller than 3 mm within **4.0 mm** of the screw centre so a screwdriver reaches it.
- Four M3 standoffs (H5–H8) carry the card: non-plated, copper keep-out on all layers.

Baseline geometry (from `p15_b10_k1`): card x 45.9–90.9, y 70.0–115.0; J10 pin 1 at (69.48, 74.16)
rot 0; standoffs H5 (60.7, 76.5), H6 (75.1, 75.8), H7 (54.5, 106.5), H8 (75.1, 109.0); tab screws
M1 (94.5, 48.5), M8 (59.8, 84.0 — under the card, fitted before the card), M9 (38.7, 70.5),
M10 (35.5, 98.6).

---

## 3. The files you need

### Start from these

| Path | What it is |
|---|---|
| `BOOST_split_boards/replace_2026-09-14/tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb` | **The placed board.** 124 footprints, 74 nets / 355 pad-net assignments, **0 tracks, 0 copper zones**, 8 keep-out zones (4 washer + 4 standoff). Marked NOT FOR FABRICATION. This is your input. |
| `…/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pro` | A copy of the shipped project: netclasses, netclass patterns, DRC rules, severities. Use these rules; never weaken them. |
| `…/BOOST_power_p15_WIP_NOT_FOR_FAB.full.json` | The layout as data: every part's x/y/rotation/side, card rectangle, standoffs, screwed FETs, tall-part clearances. |
| `…/BOOST_power_p15_WIP_NOT_FOR_FAB.distances.md` | Baseline distance table vs brief targets and agreed goals (31/49 and 38/49). |
| `…/BOOST_power_p15_WIP_NOT_FOR_FAB.drc.json` | Baseline DRC: 0 errors, 39 silk warnings, 270 unconnected (no copper yet). |
| `…/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb.pads.json` | Every pad's saved position, for checking your own geometry against KiCad. |
| `…/.render_top.png`, `.render_bottom.png`, `.model.png`, `.top.svg`, `.bottom.svg` | Views of the baseline. |
| `BOOST-github/BOOST/BOOST_9-15_nohole.net` | **Current netlist.** The schematic is frozen; the board must match this exactly. |
| `BOOST-github/BOOST/BOOST.kicad_sch` | The schematic (one schematic, both boards). |
| `BOOST_split_boards/replace_2026-09-14/board_assignment_2026-09-15.json` | Which board each part belongs to. |
| `BOOST_split_boards/BOOST_power.kicad_pro` | The shipped project file — the authority on netclasses and rules. |

### Read for context (do not skip the first two)

| Path | Why |
|---|---|
| `BOOST_split_boards/BOOST_AUDIT.md` | Independent copper audit of the previous layout: 13 checks, 5 stop-ship findings, with method and numbers. **Your board must pass these.** |
| `BOOST_split_boards/AUDIT_RESPONSE.md` | The previous AI's response; §1 documents the field-solver method you should reuse for the copper solve. |
| `BOOST_split_boards/replace_2026-09-14/HANDOFF_SUMMARY_2026-09-15.md` | Live state of the whole project: decisions, schematic changes, part choices, what is open. |
| `BOOST_split_boards/handoff_2026-09-14/REPLACE_BRIEF_v2.md` | The placement brief, stages 1–6, with the original targets. |
| `BOOST_split_boards/handoff_2026-09-14/HANDOFF_PROMPT.md` | The previous handoff: why the re-place happened, part decisions, §3.7 copper-weight economics and JLCPCB rules. |
| `BOOST_split_boards/replace_2026-09-14/tools/replace_notes.md` | Running log of verified facts: datasheet numbers, part choices, what was tried and failed. |
| `BOOST_split_boards/replace_2026-09-14/tools/README.md` | What every tool script does. |
| `BOOST_split_boards/replace_2026-09-14/tools/placement/checkin_notes.md` | Stack budget, tab-screw mechanics, R1 land pattern, delivery cautions. |
| `BOOST_split_boards/placement_review_2026-09-15/BOOST_power_placement_review.html` | The placement check-in page: decisions, both sides, distance table, DRC. Open in a browser. |
| `BOOST-github/BOOST_CONTEXT_TRANSFER.md` | Design decisions, thresholds, cautions (§5, §6, §13). |
| `BOOST_split_boards/ROUTING_REPORT.md` | How the previous board was routed, and its own account of what went wrong. |
| `BOOST_split_boards/handoff_2026-09-14/SIMULATION_REPORT.md` | LTspice results: gate drive, dead time, where the currents come from. |

### Tools that already exist — use them, don't rewrite them

`BOOST_split_boards/replace_2026-09-14/tools/placement/` holds a working placement pipeline:
geometry model (`pmodel.py`), mechanical checks (`pcheck.py`), simulated-annealing placer
(`psa5.py` with config builders `mk8`–`mk11`), small-part placer (`psat.py`), board writer
(`papply.py`), distance table (`ptable.py`), DRC summary (`pdrc.py`), plots (`sa_view.py`),
net-tie placer (`pnettie.py`), result ranking (`prank.py`), and the whole pipeline in `run_place.sh`.
Commands are in `RUNBOOK.md`.

There is **no routing tooling yet.** That is yours to build.

---

## 4. Ground rules (non-negotiable)

1. **Never weaken a DRC rule, and never add a DRC exclusion.** Keep the 1.0 mm / 0.15 mm silk text
   rule. If something cannot pass, say so; don't make the check pass by changing the check.
2. **Verify from saved files**, not from what you think you wrote. Save, reload, refill zones, save
   again, then run DRC on the file on disk.
3. **Back up before replacing** anything shipped: copy to `BOOST_split_boards/previous/<date>/` first.
4. **Mark work in progress.** Any board not ready to fabricate keeps `NOT_FOR_FAB` in its filename and
   a "NOT FOR FABRICATION" note on the board.
5. **Don't guess part specs or pinouts.** Read the datasheet; if you can't verify something, say so
   rather than assuming.
6. **Keep the schematic fixed.** Netlist `BOOST_9-15_nohole.net` is the contract. If routing forces a
   schematic change, stop and ask.
7. **Hard electrical constraints:** In1 and In6 are GND-only; no LX copper on In3 or In5 (they face the
   In4 5 V plane — the old pours coupled 232 pF); every via ≥ 0.3 mm drill; ≥ 0.254 mm annular ring on
   through-hole pads; design to 0.15/0.15 mm track/space so 2 oz outer stays possible.
8. **Close KiCad before writing shipped files.** Lock files (`~BOOST_power.kicad_pcb.lck`) have been
   present; ask the user to close the project rather than writing under a lock.
9. **Don't run `sed -i` on the `.kicad_pro` files** — they are CRLF and it corrupts them.
10. **`pcbnew.SaveBoard` silently rewrites `.kicad_pro` without the netclasses.** Copy the shipped
    `.kicad_pro` back next to the board after every save, before running DRC.

---

## 5. How this will be judged

In order:

1. `kicad-cli pcb drc --severity-all` on the saved file: **0 errors, 0 unconnected, 0 exclusions**,
   under the shipped rules. Pass/fail.
2. Every high-current path meets its thermal and via targets at the chosen copper weight
   (`ROUTING_SPEC.md` §7).
3. The audit's 13 checks (`ROUTING_SPEC.md` §8), in particular the five stop-ship items.
4. Placement distance table vs the targets — at least the baseline's 38/49 agreed goals.
5. Mechanical checks clean: washer keep-outs, screwdriver access, card and standoff zones, stack height.
6. A report that states plainly what is still open.

Honest reporting beats a good-looking number. If a branch does not meet its target, say which, by how
much, and what would fix it.
