# Superseded: v14 (2026-09-17, never handed back)

`BOOST_power_route_v14_NOT_FOR_FAB.kicad_pcb` is the first routed board on `work/base_v14.kicad_pcb` (router run
r30). It is replaced by `../../BOOST_power_route_v15_NOT_FOR_FAB.kicad_pcb` (run r36): v14's repair rounds re-drew
the gate-loop returns on top of themselves, its VCCI fan-out vias could land millimetres from their capacitors,
and its M6 gate loop was routed drive-first (see `ROUTING_REPORT_2026-09-17.md` section 7). Kept for reference only.
