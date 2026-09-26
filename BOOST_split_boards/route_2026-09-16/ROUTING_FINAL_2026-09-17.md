# BOOST power board: final pass and freeze (step 6)

2026-09-17, after your acceptance of v15 in principle. This is the single final pass you asked for: the D13 → M4
link routed with the current map (8.1b), the M3, M2 and M6 gate loops hand-routed (8.3b), 8.2(a) and 8.4 accepted
as documented, and the placement mechanical checks re-run after the ten capacitor moves.

**Board: `BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb`** (SHA-256 7aaf6f5752ca794b81ea…), with its `.kicad_pro`
and `.kicad_dru` beside it. Placement is byte-identical to v15 (the same ten capacitors moved, nothing else);
everything was routed again from v11's copper in one pass. **The power board is frozen at v16** — the name keeps
`NOT_FOR_FAB` because there is no fabrication package yet and the control card (step 7) is still to come; say the
word if you want it renamed.

## 1. Checks on the saved file

| Check | v16 |
|---|---|
| DRC (`--severity-all`, refilled, saved, reloaded, refilled, saved) | **0 errors, 0 unconnected, 0 exclusions**; 43 warnings, the same silk warnings as v13 and v15 |
| Rules | unchanged; nothing weakened, no exclusion added |
| Netlist parity vs `BOOST_9-15_rev3.net` | 124 footprints, **0 failures** |
| In1 / In6 GND only, In4 one 5 V outline, no LX on In3 / In5 | **PASS** |
| Untied fill outlines | **0** |
| Router items on their routed nets (`net_flips.py`) | 1967 of 1967; 2 items pruned as dangling (two 5 V vias) |
| Placement mechanical (`pcheck.mechanical`, §4) | washer keep-outs, screwdriver paths, the 25 mm rule, card and corner zones: **pass** |
| Stackup | JLCPCB 8 layers, 1 oz / 1 oz, 1.654 mm |
| Renders | `renders_v16/` |

Routing: 1794 track segments, 1748 mm; 171 new vias, 868 on the board.

## 2. Gate loops (8.3b: hand-routed M3, M2, M6)

I cannot drive the KiCad GUI, so "hand-routed" here means I picked each pair's corridor off the copper and the
solved current map and gave it to the router as a **guide**: inside that corridor it lays legal copper for the
return and the drive, one after the other, and the pair is then kept out of rip-up. The corridors are in
`tools/route_signals.py` (`GATE_GUIDES`), so they are yours to nudge in KiCad.

| FET | Loop area v15 → v16 (mm²) | Forward beside return | driver → R | R → gate | driver → diode | diode → gate | VSS → source |
|---|---|---|---|---|---|---|---|
| M7 (LX side) | 47.5 → **49.1** | 73 % → 69 % | 13.6 | 5.1 | 18.5 | 1.4 | 20.9 |
| M5 (LX side) | 24.5 → **24.2** | 82 % → 82 % | 13.5 | 1.3 | 2.1 | 1.0 | 21.3 |
| M6 (LX side) | 47.7 → **47.7** | 34 % → 34 % | 28.9 | 3.4 | 16.0 | 1.5 | 14.8 |
| M2 (rail side) | 147.4 → **35.8** | 18 % → 56 % | 27.8 | 4.5 | 30.7 | 1.5 | 15.5 |
| M3 (rail side) | 186.5 → **37.8** | 0 % → 0 % | 21.2 | 4.0 | 20.8 | 1.1 | 9.9 |
| M4 (rail side) | 57.0 → **59.7** | 4 % → 1 % | 32.9 | 1.1 | 4.9 | 31.0 | 22.2 |

**All six are at or under your 60 mm² target.** What each corridor does:

- **M2 (147 → 36 mm²):** out of U15 on In5 (a 1.0 mm source track cannot leave the pin row on B.Cu), east along
  the free 1.5 mm channel between the M7/M2 pads and the Vout_1 pour, then down the east side of M2's pin column
  to D11. The return goes first here: the escape beside U15 only takes the wide track one way round.
- **M3 (187 → 38 mm²):** down the cool channel west of the LX vias, then west on **In3** between the Vout_2 via
  holes — those vias are flashed on F and In5 only, so on In3 they are just holes with 0.93 mm gaps — to D14,
  with the return branching into the source pour at M3.3. The drive goes first (it has to fit the whole corridor).
- **M6 (47.7 mm², unchanged):** not guided. Its corridor along y 63.4 runs into the GATE_M6 link, which is drawn
  first, and the router's return-first route already meets the target.

**On the "beside" column:** it counts only track that runs within 1.5 mm *on the same layer* (or 0.5 mm on the
In2/In3 pair). M3 scores 0 % because its pair is stacked vertically — drive on In3, return on F — which is why its
loop area collapsed. For M3 the area is the number to read, not the share.

**M7** moved slightly (47.5 → 49.1 mm², 73 → 69 %). You asked me to leave M7 and M5 alone: M5 is unchanged, and
M7's small change comes from one new link (§3). I moved that link to the end of the gate-loop stage to get M7 back
from the 55.4 mm² / 9 % it had when the link was drawn early.

## 3. D13 → M4 with the current map (8.1b), and the one new crossing

| | v15 (direct) | v16 (current map) |
|---|---|---|
| D13 → M4 gate link | 26.6 mm, 2 vias | **31.0 mm, 2 vias** |
| Track in copper above 0.25 A/mm | In2 7.6 mm at 1.12 A/mm, B 5.9 mm at 1.02 | **none** |
| LX L1→M5 resistance | 2.271 mΩ | **2.017 mΩ** (unrouted base: 1.864) |
| LX L1→M5 neck | 84.0 °C (2.42 mm, 0.9 mm, In2) | **57.3 °C** (2.48 mm, 1.3 mm) — base 57.8 |
| ch3 commutation loop | 2.08 nH | **2.04 nH** (v13 2.04, base 1.98) |

That is the regression gone. As you said, the neck figures are IPC numbers on copper 0.1–0.2 mm from a plane, so
treat them as a comparison between routings, not as real temperatures.

**One new hot crossing.** U15's VDDA and VDDB pins are one net, and with the M2 pair now occupying the space beside
U15 the link along the pin row has to go on F.Cu, where it cuts the LX pour for 4.1 mm at up to 1.28 A/mm. The cost
is small: LX L1→M1 0.467 → 0.495 mΩ and its worst via 0.83 → 0.90 × rating, with the neck unchanged (52.3 →
52.4 °C). Everything else in that branch set is unchanged. If you would rather not cut the LX pour there, the
alternatives are a longer path round U15 on B.Cu or moving C51/C18; say so and I will do it as a separate change.

Crossings overall: 18 runs, 39.7 mm (v15: 14 runs, 47.7 mm), 99 new vias in copper above 0.25 A/mm (v15: 96). The
two GATE_M4 runs above 1 A/mm are gone; the longest runs now are 12V on In5 (5.7 mm at 0.68) and the VDDA link.

## 4. Placement mechanical checks after the ten moves

Run on the v16 placement (identical to v15) with `pcheck.mechanical`, baseline = the accepted p15 placement:

| Check | Result |
|---|---|
| Washer keep-outs, 3.75 mm, both sides | **pass** — nothing inside |
| **C89 → H8** (your question) | centre 5.57 mm; **courtyard edge 4.03 mm, nearest pad corner 4.40 mm** — clear of 3.75 mm |
| Screwdriver / nut-driver paths (4.0 mm tab, 5.5 mm standoff) | **pass** |
| 25 mm rule (unscrewed FET body centre to nearest screw) | **pass** |
| Parts under the card, corner zone | **pass** |
| Closest part to any standoff | M2's body 3.70 mm from H6 — **pre-existing** (M2 has not moved since v11); the checker exempts FET bodies on B, where the screw passes beside the tab |

The ten moves did add 11 pairs whose **courtyards now touch**: U19–C31 (0.014 mm), U8–C60 (0.011), C16–C62
(0.027), C50–C62 (0.067), C16–C50 (0.050), C18–R21 (0.051), U19–C48 (0.086), U15–C51 (0.087), U10–C50 (0.089),
U8–C89 (0.079), R60–C51 (0.081). None of them overlap, and KiCad's courtyard-overlap check (which is not among the
five ignored checks) is clean. These courtyards are the KiCad IPC ones, which already carry the assembly margin,
so the bodies stay about 0.5 mm apart — but there is no margin left on the courtyard rule itself. I have not
nudged anything, because you verified this placement; 0.1–0.2 mm of extra spacing is available if you want it.

## 5. Copper solve, v15 → v16

Full tables: `work/v16_vs_v15.md` and `work/v16_vs_v14base.md` (against the unrouted base). Only two rows move by
more than 2 °C or 0.05× against v15:

| Branch | I (A) | R (mΩ) | Neck rise °C (width, length, layer) | Worst via × rating |
|---|---|---|---|---|
| **LX L1→M1** | 15.80 | 0.467 → 0.495 | 52.3 (6.06, 1.2, In2) → 52.4 (5.94, 1.3, In2) | 0.83 → 0.90 |
| **GND ch1 bank→input** | 7.05 | 0.252 → 0.247 | 2.0 (16.37, 2.6, In1) → 2.2 (15.86, 1.9, In1) | 0.81 → 0.89 |

Improvements over v15: LX L1→M5 84.0 → 57.3 °C (§3), rsense_lo R1→L1 27.4 → 25.0 °C, Vout_3 M4→J5 4.6 → 2.3 °C.

**Copper loss** over the 29 non-loop branches: 1.097 → **1.084 W** (v13 1.089, unrouted base 1.006).

**Commutation-loop copper inductance:** ch1 0.73 nH (unchanged), ch2 1.18 → **1.17**, ch3 2.08 → **2.04**
(unrouted base 0.70 / 1.13 / 1.98; the simulations used 4.85 / 12.74 / 7.91).

**Necks at least 5 mm long** (`--long 5`, worst neck on each branch that stays above half its rise for 5 mm):

| Branch | I (A) | base | v15 | v16 |
|---|---|---|---|---|
| LX L1->M1 | 15.80 | 22.3 (6.1) | 29.8 (5.0) | 32.1 (5.0) |
| Vin J1->R1 (DC) | 18.40 | 23.6 (11.2) | 30.8 (5.0) | 30.1 (5.1) |
| LX L1->M5 | 8.35 | 21.6 (15.1) | 27.0 (5.1) | 26.9 (13.1) |
| rsense_lo R1->L1 | 20.70 | 20.1 (7.0) | 27.4 (6.9) | 25.0 (6.9) |
| LX L1->M6 | 7.69 | 16.3 (5.0) | 18.8 (5.2) | 19.4 (5.3) |
| Vout_1 M2->J3 (LED DC) | 2.63 | 10.2 (15.4) | 11.0 (18.8) | 13.0 (7.8) |
| Vin caps->R1 (ripple) | 9.50 | 5.0 (5.0) | 6.7 (5.1) | 6.9 (5.0) |
| Vout_2 M3->J8 (LED DC) | 2.37 | 5.0 (5.0) | 5.4 (5.7) | 5.5 (5.7) |
| Output3_drain J6->M8 | 2.37 | 4.6 (10.0) | 4.6 (10.0) | 4.6 (10.0) |
| Vout_2 M3->bank+J8 | 7.69 | 3.8 (6.3) | 3.9 (6.2) | 4.5 (6.0) |
| LX L1->M7 | 7.05 | 2.7 (5.8) | 3.3 (7.7) | 3.5 (5.1) |
| the remaining 11 branches | 2.37–15.80 | ≤ 1.8 | ≤ 2.3 | ≤ 2.2 |

## 6. What else changed in this pass

Everything routes in one pass now (the first pass had 0 failed connections, against 4 in v15), and two connection
problems the new copper created were fixed at the source:

- **C84.2** (a Vin capacitor's GND pad): the M2 pair's vias cut its small F.Cu fill piece off, and by the time the
  GND fan-out ran there was no room for a via. It now takes its plane via in the bypass stage, before the pairs.
- **U15 VDDA/VDDB pin link:** unconnected once the M2 pair took the space; now drawn in a late bypass stage, after
  the gate loops (§2, §3).

Unchanged from v15 and still true: the bypass capacitor distances and links (C31 2.8 / 2.5 mm to U19 pins 16/14),
the VCCI capacitors' own vias, C51 tied to pins 16/14 (8.2a), C48.1's 5 V via at U19.8 (8.4), and the datasheet
current figures.

## 7. Files

- **Board:** `BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb` / `.kicad_pro` / `.kicad_dru`; base `work/base_v14.kicad_pcb`.
- **Checks:** `work/v16.drc.json`; exports `work/v16_cu.json`, `work/v16_fp.json`.
- **Measurements:** `work/v16_gate_paths.json`, `work/v16_bypass_links.json`, `work/v16_bypass_table.md`,
  `work/v16_route_stats.json`, `work/v16_crossings.json`, `work/v16_report_tables.md`.
- **Solver:** `work/v16_B.json`, `work/v16_B_long5.json`; comparisons `work/v16_vs_v15.md`,
  `work/v16_vs_v14base.md`, `work/v16_necks5.md`.
- **Router run:** `work/r_42.json`, `work/g_42_1.json` with logs; snapshot `work/route_signals_r42.py`; board built
  from `work/sig_42p.kicad_pcb`.
- **Renders:** `renders_v16/`.
- **New tools this pass:** `handroute.py` (check hand-placed pair geometry against the board and the current map),
  `free_probe.py` (measure a free corridor), `jmap_view.py` (plot the solved current map over a window).
- **Previous:** v15 and its report stay in place; `ROUTING_REPORT_2026-09-17.md` still documents the bypass work.

Next: step 7, the 45 mm control card (`control_sync3` has to be built first).
