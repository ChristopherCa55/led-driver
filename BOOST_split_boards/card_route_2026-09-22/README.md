# Control card routing (handoff step 7), 2026-09-22 to 2026-09-24

**Accepted by the user on 2026-09-24:** placement c3 on the open layer plan
(`ROUTING_CHECKIN_5_2026-09-24.md`), with its 12 V detour and c3's five longer decoupling paths.

| Board | What it is |
|---|---|
| **`BOOST_control_route_c3_NOT_FOR_FAB.kicad_pcb`** | **the accepted card**, byte-identical to `work/card_c3_open_NOT_FOR_FAB.kicad_pcb`. DRC with the rules beside it: nothing at any severity, 0 unconnected (the `fp-lib-table` added here resolves the BOOST footprint library for DRC's library check) |
| `BOOST_control_route_c3_rc_CANDIDATE_NOT_FOR_FAB.kicad_pcb` | waiting for the user: the accepted card with J11's 30 holes at 1.05 mm (the user's 2026-09-15 answer, never applied until now). DRC 0 errors, 0 unconnected, 1 warning (J11 now differs from its library footprint); sensitive nets, layer plan, parity and overlay all unchanged. The fab package `../fab_2026-09-24/` is built from it |

Every board keeps the `.kicad_pro` / `.kicad_dru` from `rules/` beside it. It stays NOT_FOR_FAB until the user
releases the package.

Check-ins: `ROUTING_CHECKIN_3_2026-09-23.md`, `ROUTING_CHECKIN_4_2026-09-23.md`, `ROUTING_CHECKIN_5_2026-09-24.md`.
Tools are in `tools/` (listed in check-in 5 §3 and the memory notes). Re-verify any board with
`OPEN_PLAN=1 sh tools/fr_verify.sh NAME` (a board in `work/`).
