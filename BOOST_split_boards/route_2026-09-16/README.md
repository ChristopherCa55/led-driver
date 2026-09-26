# Power board copper and routing (handoff steps 5 and 6), 2026-09-16 / 2026-09-17

Work in progress, NOT FOR FABRICATION. Start board: `base_p15.kicad_pcb` = the accepted placement
`replace_2026-09-14/tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.kicad_pcb` (p15_b10_k2, netlist rev3), with
the JLCPCB 1 oz / 1 oz stackup (option B) written in by `tools/set_stackup.py`.

| Board | What it is |
|---|---|
| `BOOST_power_route_v9_NOT_FOR_FAB.kicad_pcb` | step 5 check-in: power copper only |
| `BOOST_power_route_v10_NOT_FOR_FAB.kicad_pcb` | v9 + the In4 5 V plane |
| `BOOST_power_route_v11_NOT_FOR_FAB.kicad_pcb` | v10 + the R1 sense channel (ISNS pair) |
| `work/rejected_v12/` | first fully routed board, rejected: routed without the current map, it cut the power pours |
| `BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb` | step 6, first hand-back: v11 + every signal routed (report: `ROUTING_REPORT_2026-09-16.md`) |
| `BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb` | step 6, second pass (2026-09-17): driver bypass capacitors at their pins, direct gate links (report: `ROUTING_REPORT_2026-09-17.md`) |
| **`BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb`** | **step 6 FROZEN (2026-09-17): v15 plus the D13 -> M4 link routed with the current map and the M3/M2/M6 gate loops hand-routed to <= 60 mm2** (report: `ROUTING_FINAL_2026-09-17.md`) |
| `work/superseded_v14/`, `work/v15_r34/` | earlier boards from the second pass, never handed back (each has a README) |
| **`BOOST_power_route_v17_NOT_FOR_FAB.kicad_pcb`** | **2026-09-24: v16 plus MOSFET orientation silk, silk only** (`tools/fet_silk.py`, `tools/silk_pass.py`; `tools/board_diff.py --silk-only` confirms nothing else changed). Silk warnings 43 -> 2. Before/after DRC in `work/silk/`, renders in `renders_v17/` |
| `BOOST_power_route_v18_CANDIDATE_NOT_FOR_FAB.kicad_pcb` | 2026-09-24, **waiting for the user**: v17 plus 7 via nudges (3 Power-class clearance shortfalls of 0.008-0.014 mm; 4 Vin vias moved outward from J1's lug hole, to meet JLC's 0.45 mm rule for filled vias) and 1.05 mm J10 holes (the user's 2026-09-15 answer). DRC 0 / 0; the fab package `../fab_2026-09-24/` is built from it |

**Netclass priorities (2026-09-24).** `rules/BOOST_power_route.kicad_pro` and the shipped `../BOOST_power.kicad_pro`
now give every netclass a priority and state Default 0.20 / 0.20 (`tools/set_netclass_priority.py`; backups in
`../previous/2026-09-24/power_pro_before_default_0p20/`). Without priorities, KiCad 10 applied its built-in 0.20 to
Default **and to the Power nets**; with them, Power is checked at its stated 0.25. v16/v17 then fail at 3 via-to-pad
spots, which v18 fixes. v16's own `.kicad_pro` is left as it was, so v16 still checks as it did when frozen.

Each board has the `.kicad_pro` and `.kicad_dru` from `rules/` beside it. Step 5 check-in page:
`../copper_review_2026-09-16/` and https://claude.ai/artifact/CsWJraE5Vq7Vkfb1vU2LdR

## Step 5 pipeline (power copper)

    python copper_v11.py                      # spec -> copper_v11.json (zones as rect unions, via fields)
    sh tools/loop_build.sh v11 6              # KiCad: build + fill + save, copy rules, DRC, prune illegal vias, repeat
    "<KiCad python>" tools/export_copper.py BOOST_power_route_v11_NOT_FOR_FAB.kicad_pcb work/v11_cu.json
    python tools/solve_copper.py work/v11_cu.json branches_power.json --stack B --out work/v11_B.json   # 1 oz outer
    python tools/solve_copper.py work/v11_cu.json branches_power.json --stack C --out work/v11_C.json   # 2 oz outer
    python tools/loop_inductance.py work/v11_B.json work/v11_C.json
    python tools/summarise.py work/v11_B.json work/v11_C.json
    "<KiCad python>" tools/layer_checks.py BOOST_power_route_v11_NOT_FOR_FAB.kicad_pcb

The solver needs ~5 GB free for the GND branches (0.2 mm grid); it runs GND two at a time.

## Step 6 pipeline (signals)

    python tools/solve_copper.py work/v11_cu.json branches_power.json --stack B --workers 3 --out work/v11_B.json --jmap work/v11_jmap.npz
    sh tools/route_pipeline.sh BOOST_power_route_v11_NOT_FOR_FAB.kicad_pcb 28 work/v11_jmap.npz
        # export -> tools/route_signals.py (grid router, all signal nets) -> tools/add_routes.py -> DRC,
        # then up to five repair rounds (re-export the refilled board, route again with the earlier routes loaded)
        # until DRC shows 0 errors and 0 unconnected, then tools/prune_dangling.py until no track end dangles
    "<KiCad python>" tools/finalize.py work/sig_28_3.kicad_pcb BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb
    cp rules/BOOST_power_route.kicad_pro BOOST_power_route_v13_NOT_FOR_FAB.kicad_pro   # and the .kicad_dru
    kicad-cli pcb drc --severity-all --format json -o work/v13.drc.json BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb
    "<KiCad python>" tools/layer_checks.py BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb
    "<KiCad python>" tools/plane_checks.py BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb   # planes, untied islands
    "<KiCad python>" tools/export_copper.py BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb work/v13_cu.json
    python tools/route_stats.py work/v13_cu.json work/v11_cu.json work/v13_route_stats.json renders_v13/v13_routes_by_layer.png
    python tools/gate_paths.py work/v13_cu.json work/v13_gate_paths.json
    python tools/solve_copper.py work/v13_cu.json branches_power.json --stack B --workers 2 --out work/v13_B.json
    python tools/crossings.py work/v11_cu.json work/v13_cu.json work/v11_jmap.npz work/v13_crossings.json
    python tools/compare_solves.py work/v11_B.json work/v13_B.json
    # netlist parity (from replace_2026-09-14/tools/placement):
    "<KiCad python>" syncboard.py --check ../../../route_2026-09-16/BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb \
        ../../../../BOOST-github/BOOST/BOOST_9-15_rev3.net ../../board_assignment_2026-09-15.json POWER

A full pipeline run took about 25 minutes (tag 28, three repair rounds).
`tools/plot_region.py` plots any window of an export with chosen nets highlighted (used to debug failures).

## Second pass (2026-09-17): bypass capacitors, gate links, gate loops

    "<KiCad python>" tools/export_courtyards.py <board> work/v11_fp.json     # courtyards + pads for placement
    python tools/place_bypass.py                                            # legal spots beside the driver pins
    "<KiCad python>" tools/move_parts.py BOOST_power_route_v11_NOT_FOR_FAB.kicad_pcb work/bypass_moves_final.json work/base_v14.kicad_pcb
    "<KiCad python>" tools/move_vias.py work/base_v14.kicad_pcb work/via_moves_v14.json work/base_v14.kicad_pcb
    python tools/solve_copper.py work/v14base_cu.json branches_power.json --stack B --workers 2         --out work/v14base_B.json --jmap work/v14base_jmap.npz
    sh tools/route_pipeline.sh work/base_v14.kicad_pcb 36 work/v14base_jmap.npz
    "<KiCad python>" tools/finalize.py work/sig_36_3.kicad_pcb BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb
    # then, as for v13: copy rules, DRC, layer_checks, plane_checks, export_copper, syncboard --check, and
    python tools/gate_paths.py work/v15_cu.json work/v15_gate_paths.json     # + diode paths, pairing, loop area
    python tools/bypass_links.py work/v15_cu.json work/v15_bypass_links.json # routed bypass links, VCCI own vias
    python tools/bypass_table.py work/v15_fp.json work/v11_fp.json           # pad-to-pin distances
    "<KiCad python>" tools/net_flips.py BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb work/g_36_2.json
    python tools/solve_copper.py work/v15_cu.json branches_power.json --stack B --workers 2 --out work/v15_B.json
    python tools/solve_copper.py ... --long 5 --out work/v15_B_long5.json    # worst neck at least 5 mm long

Final pass (v16): `tools/route_signals.py` carries the hand-chosen gate-loop corridors (`GATE_GUIDES`), the
current-map routing for GATE_M4 (`GATE_JMAP`), and the late bypass stage (`LATE_EDGES`, the U15 VDDA pin link).
`tools/free_probe.py` measures a free corridor, `tools/jmap_view.py` plots the solved current map over a window,
and `tools/handroute.py` checks hand-placed pair geometry before it is committed.

`net_flips.py` is worth running on any board built from router output: KiCad can move a new track or via to another
net it thinks the item belongs to (run r35), and DRC does not report that on its own. `add_routes.py` now puts the
routed net back and says so.

## Files

- `copper_v1.py` .. `copper_v11.py`: each copper version's spec; the docstring says what changed and why.
- `branches_power.json`: branch terminals and RMS currents (ROUTING_SPEC 3); `loop ...` branches are for
  the inductance estimate only (they force the whole channel current into the ceramics, so ignore their
  thermal figures).
- `rules/BOOST_power_route.kicad_pro`: shipped project + Sense netclass + sink source nets in Power.
  `rules/BOOST_power_route.kicad_dru`: tightening-only rules. The shipped `../BOOST_power.kicad_pro` is untouched.
- `stackup/`: JLCPCB 8L 1.6 mm stackups (gsuberland/jlcpcb_autogenerated_stackups normalised JSON).
- `renders_v13/`: 3D renders of both sides and the routes-by-netclass overview per layer.
- `work/`: exports, DRC reports, router outputs (`r_N.json` first pass, `g_N_i.json` repair rounds, with logs),
  intermediate boards (`sig_*`), solver results (`vN_B.json`), `work/route_signals_rNN.py` snapshots of the
  router as it was for earlier runs.
