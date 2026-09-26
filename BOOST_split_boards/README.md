# BOOST LED driver — two-board split, routed (KiCad 10)

## Current state (2026-09-25): start here

**The release package is `FINAL_2026-09-25/`** (scenario A: 5 bare PCBs of each board, 2 complete sets assembled
by JLCPCB). Start with `FINAL_2026-09-25/README.md` and its `7_docs/ORDER_CHECKLIST.md`.

**Schematic rev6 is in `BOOST-github/BOOST/BOOST.kicad_sch`** (written 2026-09-25 on the user's OK).
- Rev5 is backed up in `previous/2026-09-25/schematic_rev5/`.
- ERC 0/0, the same report as rev5; netlist `BOOST_9-25_rev6.net`.
- Netdiff: six values only. Parity 0 on both boards. DRC 0 errors, 0 unconnected.
- Nothing is open before ordering; follow `fab_2026-09-24/ORDER_CHECKLIST.md`.

The re-designed boards are not the `BOOST_power.kicad_pcb` / `BOOST_control.kicad_pcb` in this folder. Those are the
older routing described below, kept as shipped. The current boards (working copies keep `_NOT_FOR_FAB`; the release
copies are in `FINAL_2026-09-25/2_boards/`):

| | Board | Status |
|---|---|---|
| Power | `route_2026-09-16/BOOST_power_route_v19_NOT_FOR_FAB.kicad_pcb` | **release (RC2)**: v18 + rev6 values |
| Power | `route_2026-09-16/BOOST_power_route_v18_NOT_FOR_FAB.kicad_pcb` | v17 + via moves + J10 1.05 mm (approved 2026-09-24) |
| Power | `route_2026-09-16/BOOST_power_route_v17_NOT_FOR_FAB.kicad_pcb` | frozen v16 + MOSFET orientation silk |
| Card | `card_route_2026-09-22/BOOST_control_route_c3b_NOT_FOR_FAB.kicad_pcb` | **release (RC2)**: c3 + J11 1.05 mm |
| Card | `card_route_2026-09-22/BOOST_control_route_c3_NOT_FOR_FAB.kicad_pcb` | accepted 2026-09-24 |

- Fabrication + assembly package: `fab_2026-09-24/README.md` (RC2), `COST_SUMMARY.md`, `ORDER_CHECKLIST.md`.
- Assembly pack: `BUILD_NOTES.md` and `case_drilling_2026-09-15/` (rev B).
- 3D model and clearances: `assembly_3d_2026-09-24/` (rebuilt 2026-09-25 with the chosen hardware).
- M1 turn-off re-check with the routed loop: `sim_m1_2026-09-24/README.md` (accepted 2026-09-25).
- `BOOST_power.kicad_pro` carries netclass priorities (2026-09-24; backup in `previous/2026-09-24/`).

The rest of this file describes the older routing and is kept for reference.

| file | what |
|---|---|
| `BOOST_power.kicad_pcb` + `.kicad_pro` | 74 × 86 mm, 8 layers, 121 footprints |
| `BOOST_control.kicad_pcb` + `.kicad_pro` | 60 × 60 mm, 8 layers, 154 footprints |
| `DRC_power.rpt`, `DRC_control.rpt` | KiCad 10 DRC, run on these exact files |
| `power_routed.png`, `control_routed.png` | layer-coloured plots |
| `previous/` | the boards as they were before this pass |

Keep the `.kicad_pro` beside each board — it carries the net classes, and without
it DRC falls back to defaults and reports differently.

## Final state, measured by KiCad 10 DRC on the delivered files

| | POWER | CONTROL |
|---|---|---|
| unconnected **pads** | **0** | **0** |
| unconnected items (zone fill) | 2 | **0** |
| clearance | **0** | **0** |
| shorting items | **0** | **0** |
| hole-to-hole / hole clearance | **0** | **0** |
| solder-mask bridges | **0** | **0** |
| silkscreen | **0** | **0** |
| isolated copper | **0** | **0** |
| dangling track/via | 1 | **0** |
| library warning | 1 | 0 |
| track segments / vias / zones | 4630 / 305 / 16 | 3061 / 357 / 4 |

Every pad-to-pad connection on both boards is routed. The two remaining items on
the power board are between two *zones* — a fragment of the F.Cu ground pour that
does not reach the B.Cu ground pour across the surface. Both boards keep solid
ground planes on In1 and In6 with hundreds of stitching vias, so those fragments
are grounded through the stack; the ratsnest line is KiCad noting that no surface
copper joins them directly.

The `lib_footprint_issues` warning says the footprint library `CSCF3218-6R8MC`
(the inductor L1) is not in your footprint library table. The footprint itself is
embedded in the board and is correct — this is about your library configuration,
not the layout, and it goes away once that library is registered.

## Stackup (8 layers, both boards)

```
F.Cu    components, signal, high-current pours (2 oz)
In1.Cu  solid GND plane        <- no tracks, verified 0
In2.Cu  signal
In3.Cu  signal
In4.Cu  5V plane + signal
In5.Cu  signal
In6.Cu  solid GND plane        <- no tracks, verified 0
B.Cu    components, gate drive, signal (2 oz)
```

## Net classes (in the .kicad_pro, enforced by DRC)

| class | track | clearance | via | nets |
|---|---|---|---|---|
| Power | 2.0 mm | 0.25 mm | 0.8/0.4 | Vin, rsense_lo, LX, m2/3/4_source, Vout_1/2/3, Output1/2/3_drain, GND |
| Gate | 0.5 mm | 0.20 mm | 0.6/0.3 | GATE_M1…M7 |
| Rail | 0.8 mm | 0.20 mm | 0.6/0.3 | 12V, 5V, analog_5V |
| Default | 0.15 mm | 0.15 mm | 0.45/0.25 | everything else |

## High-current copper — measured, not assumed

The check erodes each net's copper by a disc and asks whether its power pads are
still joined; the largest disc that survives is the narrowest continuous path
between them. Only pads at least 1.5 mm across count as power terminals — an
0805 bypass cap taps the rail, it does not carry the rail current. Compared
against IPC-2221, 2 oz external, 30 °C rise.

```
net              A rms    need   narrowest continuous path
m3_source         12.0    2.37mm     2.99 mm   ok
Vout_1             3.3    0.40mm     0.45 mm   ok
Vout_3             2.7    0.30mm     0.45 mm   ok
Output1_drain      2.6    0.29mm     0.45 mm   ok
Output2_drain      2.6    0.29mm     0.45 mm   ok
Output3_drain      2.6    0.29mm     0.45 mm   ok
12V                0.5    0.03mm     0.40 mm   ok
5V                 0.3    0.01mm     0.20 mm   ok
analog_5V          0.1    0.00mm     0.45 mm   ok

Vin               20.7    5.04mm     4.59 mm   91% of requirement
m2_source         12.0    2.37mm     2.04 mm   86%
m4_source         12.0    2.37mm     1.59 mm   67%
Vout_2             3.7    0.47mm     0.40 mm   85%
rsense_lo         20.7    5.04mm     0.45 mm   path crosses a via
LX                20.7    5.04mm     0.45 mm   path crosses a via
GND               20.7    5.04mm     0.40 mm   path crosses a via
```

Read the last three carefully. 0.45 mm is a via barrel: the single best path
between those power terminals goes through one via. The measure follows one path
and does not add up parallel ones, so real capacity is higher — GND in particular
has two solid inner planes and hundreds of stitching vias. But for rsense_lo and
LX at 20.7 A it is a real finding, and the cause is placement: R1 (the 2 mΩ
shunt), L1 and the TO-220 drains sit far enough apart that no single-layer pour
can join them at 5 mm. Two ways to close it, both needing a change you asked me
not to make on my own:

* move R1, L1 and M1/M5/M6/M7 into one cluster so a single F.Cu pour spans them —
  which is what a 20 A switching loop wants anyway; or
* keep the placement and add deliberate via arrays (15–20 barrels in parallel) at
  each F.Cu-to-B.Cu crossing on Vin, rsense_lo and LX.

## Design changes made in this pass

1. **All routing rebuilt, escape vias first.** The old boards left ~37 pads that
   nothing could reach; mapping the copper around them showed the same cause
   every time — by the time the router got there, no legal via site was left near
   the pad. Giving every signal pad its own escape via while the board was still
   empty (368 of them, 100% placed) removed that class of failure outright.
2. **High-current pours rebuilt as non-overlapping regions.** The twelve pours
   were convex hulls totalling 9300 mm² on a 6170 mm² board, so zone priority
   carved most of them away: rsense_lo was filling 3% of its own outline,
   m3_source 1.9%. Each net now grows outward from its own pads and stops where
   it meets another, so the regions tile instead of fighting. rsense_lo went from
   15.6 mm² of copper to 212 mm², Vout_1 from 56 mm² to 442 mm².
3. **Two ineffective rail pours dropped.** On In4 the 5V zone outranked 12V and
   analog_5V, which were left filling 1.0 mm² and 5.0 mm² — stranded rings around
   their own pads that showed up as unconnected zones. Those two rails now route
   as 0.8 mm tracks, about 25× what 0.5 A and 0.1 A need.
4. **Zone fill parameters set to the net class.** Local clearance was 0.3 mm
   where the class asks 0.25 mm, and the extra 0.05 mm a side stopped the fill
   squeezing past tracks, stranding pours around pads. DRC still enforces
   0.25 mm.
5. **D19 moved onto the board.** The TVS was at x = 119 mm with the board ending
   at x = 104 — 15 mm off the edge, so its LX and GND pins could never be
   reached. It now sits at (83.0, 49.8) on the underside, the nearest free spot
   clearing every courtyard, mounting hole and silkscreen. **This one wants your
   eye**: it ended up 25 mm from the switching node, and a TVS belongs close to
   what it protects. If you can free space near L1/M1, move it there.
6. **Denser ground stitching**, and stitching vias driven into pour islands that
   held a pad but no via.

Board outline, layer count, stackup, schematic, netlist, footprints and every
other component's position are unchanged.

## What I did not do

No DRC rule was disabled, no violation was marked as an exclusion, and no net
class was weakened. Nothing above is hidden — the two zone items and the one
dangling stub are in `DRC_power.rpt` with coordinates.
