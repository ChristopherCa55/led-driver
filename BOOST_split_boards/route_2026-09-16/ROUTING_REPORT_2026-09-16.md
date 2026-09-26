# BOOST power board: signal routing (handoff step 6)

2026-09-16. This hands back step 6 of `handoff_routing_2026-09-15/README.md`: every signal routed on the step-5
power copper, DRC on the saved file, the `ROUTING_SPEC.md` §10 checks, and the copper solve re-run.

**Board:** `route_2026-09-16/BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb` (SHA-256 f5ed9a175c17d733…), with
`BOOST_power_route_v13_NOT_FOR_FAB.kicad_pro` and `.kicad_dru` beside it (copies of `rules/`). It starts from
v11: the accepted v9 power copper, plus the In4 5 V plane (v10) and the R1 sense channel (v11). No footprint moved,
and the shipped `BOOST_power.kicad_pcb` / `.kicad_pro` are untouched. The name stays `NOT_FOR_FAB` until you have
decided the items in §6.

**Where things stand:**
- **Done and verified on the saved file:**
  - every net routed; DRC 0 errors, 0 unconnected, 0 exclusions;
  - no rule changed;
  - In1/In6 GND only, no LX on In3/In5, In4 one 5 V outline;
  - no untied islands; netlist parity 0 against rev3; stackup in the file.
- **Needs your decision (§6):**
  1. Routes to U19 and U25 narrow the R1 current path. The neck temperatures rise, but every affected neck is
     shorter than 5 mm, and copper loss rises by 79 mW.
  2. A new 0.93 mm throat in the Vout_3 LED path at U6.
  3. Gate return paths are routed separately, not beside the gate tracks as spec §9 asks.
  4. Rail and Gate nets use a narrower track than their netclass default over part of their length.
- **Rejected on the way:** a first fully routed board (v12, moved to `work/rejected_v12/`) passed DRC and parity.
  But its signal tracks cut the pours where the current flows; the worst case put the Vout_1 LED path through a
  0.20 mm neck at 177 °C (§4). v13 was routed with the solved current map to prevent that.

---

## 1. Final checks (ROUTING_SPEC §10, from the saved file)

| Check | Result |
|---|---|
| `kicad-cli pcb drc --severity-all`, file refilled, saved, reloaded, refilled, saved | **0 errors**, **0 unconnected**; 43 warnings, the same 43 silk warnings the unrouted v11 had (20 silk overlap, 22 silk over copper, 1 J8 reference clipped by the edge) |
| DRC exclusions | 0 (`drc_exclusions` is empty) |
| Rules | Board rules and netclasses identical to the shipped `BOOST_power.kicad_pro`, plus the step-5 additions (Sense netclass, sink sources in Power). `.kicad_dru` unchanged since step 5; it only tightens. Silk rule 1.0 / 0.15 mm. DRC lists 5 checks as ignored (missing courtyard, track not centred on via, tuning-profile geometry, footprint filters, footprint type); neither the shipped nor the routing project file sets any severity. |
| Untied copper islands (`tools/plane_checks.py`) | 0; all 49 zones remove islands; every fill outline touches a pad, via, track or zone of its net |
| In1 / In6 | GND only: 0 tracks, 0 zones of another net; one fill outline each |
| In4 | one 5 V outline, 0 tracks |
| LX on In3 / In5 | none (`tools/layer_checks.py` PASS) |
| Netlist parity, `syncboard.py --check` against `BOOST_9-15_rev3.net` | 124 footprints, every library ID, value and pad net: **0 failures** |
| Stackup | JLCPCB 8 layers, 1 oz / 1 oz, 1.654 mm, in the file |
| Solver table on the saved file | §4 (`work/v13_B.json`); the same numbers as the candidate it was finalised from |
| Renders | `renders_v13/v13_render_top.png`, `v13_render_bottom.png`, `v13_routes_by_layer.png` |

## 2. What was added

| | Count |
|---|---|
| Tracks | 1697 segments, 1658 mm: F 447, In2 81, In3 132, In5 316, B 721. None on In1, In4 or In6 |
| Vias | 168 new (127 × 0.6/0.3, 41 × 0.8/0.4); 865 on the board. All drills ≥ 0.30 mm; the high-current nets use 0.8/0.4 |
| Vias centred in an SMD pad of their own net | 45 (16 capacitor, 21 IC, 6 resistor, 2 diode pads). Spec §2: filled, capped vias are free on 6+ layer boards. Step 5 already has 415. |
| Zones | none added or changed; fills refilled round the new copper |

Fill area lost to routing (v11 → v13, mm²):
- **GND fill:** F 3603 → 3121, B 3459 → 2683, In3 2537 → 2324, In5 1911 → 1439.
- **Planes:** In1 and In6 4969 → 4885; In4 4799 → 4713.
- **Power pours:** most lose 0–5 %. The exceptions are Vout_1 on B 148 → 112 and Vout_3 on B 123 → 112.

## 3. How it was routed

Tools are in `tools/`. The pipeline is `route_pipeline.sh` (see `README.md`).

**Router (`route_signals.py`).** A 0.1 mm grid router on F, In2, In3, In5 and B:
- Dijkstra per connection, nearest islands first.
- Obstacles are grown by track half-width + netclass clearance + 0.06 mm.
- Netclass track width first; if the connection doesn't fit, the fallback width; then the 0.6/0.3 via.
- 5 V lands on In4; GND lands on In1/In6.
- Order: sense nets, gate-driver returns, GND fan-out for five pads that routes would otherwise fence in, gate
  drive, op-amp outputs, bootstrap and VDDA, J10's Vout/drain pins, logic, rails, GND.

**Protecting the power current.** `solve_copper.py --jmap` writes, for the unrouted v11 copper, the largest sheet
current any branch puts through each cell (A/mm). The router then applies:
- **Tracks:** may not cut another net's pour or fill where that copper carries more than **0.25 A/mm**. Below
  that, crossing costs (1 + S / 0.08) per cell.
- **Vias:** a via only removes a disc, so the via limit is 2.0 A/mm, with cost S / 0.5 per layer.
- **Threshold:** the 0.25 A/mm limit is calibrated on v12's damage: every spot where v12 hurt the power copper
  carried 0.41–1.5 A/mm.
- **Last resort:** a connection that nothing else routes may cross hotter copper, at that cost. It is logged, and
  every such crossing on v13 is listed in §5.

**Repair.** A failed connection first rips up the nearest routes of other nets (within 2 mm, then 4 mm). Next it
routes on a board with the other routes lifted, and rips up the nets in that path's corridor. Then it re-routes
everything it ripped. After KiCad refills, the board is exported again and routed again until DRC shows nothing
unconnected (3 rounds for v13). Finally, dangling track ends and vias are pruned.

**Bugs DRC found in the router, all fixed before v13:**
- distance fields cut off at the routing window;
- via pads inside pours treated as crossable pour;
- track ends landing off-centre on tracks (KiCad calls them dangling);
- vias touching same-net copper they were never meant to join;
- vias flashed by fills or neighbouring same-net copper without full clearance;
- two layer changes within one via pitch merged into an unchecked via;
- the NT1–NT3 net-tie shapes missing from the export.

## 4. High-current branches, v11 (unrouted) → v13 (1 oz, `solve_copper.py`)

Bold rows got worse by more than 2 °C at the neck or 0.05× on the worst via. Neck lengths are in brackets; per
your step-5 rule, IPC-2221 is reported but is not pass/fail below about 5 mm, or for vias in plane-connected fields.

| Branch | I (A) | R (mΩ) | Neck rise °C (width mm, length mm, layer) | Worst via × rating (vias over) |
|---|---|---|---|---|
| **Vin J1->R1 (DC)** | 18.40 | 0.993 → 1.034 | 23.6 (10.04, 11.2, In3) → 38.5 (5.30, 3.6, In2) | 1.50 (4) → 1.65 (4) |
| **Vin caps->R1 (ripple)** | 9.50 | 0.310 → 0.346 | 5.0 (8.46, 5.0, In2) → 9.1 (5.44, 3.4, In2) | 0.81 (0) → 0.85 (0) |
| **rsense_lo R1->L1** | 20.70 | 0.205 → 0.259 | 20.0 (9.50, 7.0, In2) → 59.0 (4.94, 2.5, In2) | 1.34 (9) → 1.53 (9) |
| LX L1->M1 | 15.80 | 0.437 → 0.467 | 52.4 (5.98, 1.3, In2) → 51.2 (5.98, 1.3, In2) | 0.80 (0) → 0.85 (0) |
| LX L1->M7 | 7.05 | 0.452 → 0.507 | 19.6 (4.68, 0.9, In2) → 20.2 (4.78, 1.0, In2) | 0.42 (0) → 0.44 (0) |
| LX L1->M6 | 7.69 | 0.667 → 0.747 | 35.5 (5.30, 0.3, In2) → 34.7 (5.40, 0.2, In2) | 0.78 (0) → 0.79 (0) |
| LX L1->M5 | 8.35 | 1.860 → 2.001 | 58.1 (2.50, 1.2, In2) → 57.5 (2.49, 1.2, In2) | 0.58 (0) → 0.57 (0) |
| m2/m3/m4_source (shared FET sources) | 7.05–8.35 | 0.037–0.042, unchanged | 4.0–7.0 °C, unchanged | no vias |
| **Vout_1 M2->bank+J3** | 7.05 | 0.198 → 0.206 | 13.2 (1.67, 0.0, F) → 15.4 (2.82, 0.1, In3) | 0.85 (0) → 0.85 (0) |
| Vout_2 M3->bank+J8 | 7.69 | 0.299 → 0.309 | 7.9 (4.96, 0.7, In5) → 8.5 (5.07, 0.8, In5) | 0.41 (0) → 0.40 (0) |
| Vout_3 M4->bank+J5 | 8.35 | 0.118 → 0.120 | 4.9 (5.07, 1.2, In3) → 4.8 (3.01, 1.1, In2) | 0.53 (0) → 0.54 (0) |
| Vout_1 M2->J3 (LED DC) | 2.63 | 7.929 → 8.110 | 17.7 (2.45, 2.4, In3) → 17.8 (2.44, 2.3, In3) | 0.26 (0) → 0.26 (0) |
| Vout_2 M3->J8 (LED DC) | 2.37 | 2.968 → 3.029 | 5.5 (4.33, 4.7, In5) → 5.5 (4.32, 5.7, In5) | 0.11 (0) → 0.11 (0) |
| **Vout_3 M4->J5 (LED DC)** | 2.37 | 1.447 → 1.813 | 1.1 (5.26, 9.6, In5) → 13.7 (0.93, 0.9, In5) | 0.10 (0) → 0.10 (0) |
| Output1/2/3_drain, M8/M9/M10-S | 2.37–2.63 | +0.00 to +0.13 | within 0.2 °C of v11 | no vias |
| **GND M1->input caps+J2** | 15.80 | 0.120 → 0.129 | 19.1 (7.33, 0.2, In1) → 21.9 (6.97, 0.2, In1) | 1.14 (1) → 1.19 (1) |
| **GND ch1 / ch2 / ch3 bank->input** | 7.05–8.35 | +16 to +28 % | 1.4–1.5 → 1.8–2.1 °C | ch1 0.65 → 0.85, ch2 0.85 → 1.00, ch3 1.02 → 1.19 (1) |
| GND R52 / R53 / R7 returns | 2.37–2.63 | +26 to +37 % | ≤ 0.4 °C | ≤ 0.66 |

- **Copper loss** over the thermal branches: 0.896 → 0.975 W.
- **Commutation-loop copper inductance**, over-plane model: ch1 0.70 → 0.73 nH, ch2 1.13 → 1.20 nH,
  ch3 1.98 → 2.04 nH. The audit method gives 0.82 / 1.37 / 1.78 nH; the simulated values were 4.85 / 12.74 / 7.91.
- **GND resistance** rises through the planes (the new via holes). All GND vias are in plane-connected fields.

**Why v12 was rejected.** v12 was routed without the current map. It passed DRC and parity, but:
- Vout_1 M2->J3 (LED DC): 17.7 → 177.3 °C, a 0.20 mm neck, one via at 2.71× its rating;
- Vout_1 bank: worst via 0.85× → 1.44×;
- Vin J1->R1: 23.6 → 41.0 °C;
- rsense_lo: 20.0 → 33.4 °C.

It crossed hot copper with 23 track runs (80.9 mm); v13 has 18 (30.8 mm). v13 fixes the Vout_1 damage but not
the R1 area (§6.1).

## 5. Signal-routing rules (ROUTING_SPEC §9)

| Rule | v13 |
|---|---|
| `ISNS_P` / `ISNS_N` tight pair, R1 sense pads to U25.8 / U25.1, no pour | ISNS_P 9.4 mm on F. ISNS_N 8.5 mm: F, plus a 1.5 mm B.Cu crossing under ISNS_P on two vias, because R1 has N above P while U25 has P (pin 8) above N (pin 1). Centre spacing along ISNS_N: median 0.70 mm, 90th percentile 0.78, maximum 1.52. Both run in the v11 sense channel, clear of L1 and LX. |
| `SNS_CH1/2/3` short, no pour | 7.0 / 7.7 / 14.7 mm. SNS_CH3 uses In2 for 10 mm, with 2 vias. |
| Gate loops: driver → R → gate, return beside | See the table below. The return (driver VSS pin → FET source pour) is routed separately, **not beside** the gate track (§6.3). |
| J10 pinout; analog pins keep their GND neighbours | Pinout unchanged; the GND pins are through-hole into both planes |
| GND: planes In1/In6, bank returns ≥ 2 vias | Step-5 via fields unchanged. 15 GND vias added: 5 fan-outs for U11.2, U15.4, U15.5, U19.9 and R62.2, and 10 stitches for fill pieces the routes cut off. |

Gate paths, shortest routed copper (`tools/gate_paths.py`, `work/v13_gate_paths.json`):

| FET (gate R) | Driver → R | R → gate | Total | Return, VSS pin → source copper |
|---|---|---|---|---|
| M1 (R15 10 Ω) | 1.5 | 1.2 | **2.7 mm** | GND |
| M7 (R60 5 Ω) | 10.0 | 14.5 | 24.5 | 21.4 |
| M6 (R70 5.1 Ω) | 10.3 | 3.9 | 14.2 | 17.8 |
| M5 (R59 5.1 Ω) | 13.7 | 1.3 | 15.0 | 24.1 |
| M2 (R13 220 Ω) | 30.5 | 3.3 | 33.8 | 14.4 |
| M3 (R23 220 Ω) | 22.4 | 7.7 | 30.1 | 10.1 |
| M4 (R47 220 Ω) | 34.3 | 1.1 | 35.4 | 16.2 |
| M10 / M9 / M8 (100 Ω, sinks) | 2.1 / 12.5 / 18.7 | 1.4 / 1.1 / 1.1 | 3.5 / 13.6 / 19.8 | GND |

The 220 Ω gate resistors sit next to their FETs, 15–19 mm from the drivers, so the rail-side paths are long by
placement. Between them, the source pours and the via fields add the rest.

Where routes do cut power copper above 0.25 A/mm (`tools/crossings.py`, `work/v13_crossings.json`):

- **Tracks:** 18 runs, 30.8 mm.
  - 12V on In5 near U19 and the M1 area: 5.7 mm up to 0.68 A/mm at (78.8, 52.2); 4.3 mm at (72.7, 46.2); and
    six runs of 0.3–1.3 mm up to 0.84 A/mm.
  - analog_5V: to U25, 2.0, 2.2 and 0.5 mm on In5 up to 0.64 A/mm, and 1.1 mm on B up to 0.73 A/mm; near U6,
    3.4 mm at 0.26 A/mm.
  - The other five runs are 2.1 mm or less, at 0.37 A/mm or less: Vin, Current, 5V, SNS_CH1 and m2_source.
- **Vias:** 95 new vias pierce copper above 0.25 A/mm. The most are analog_5V 13, 5V 11, 12V 10 and GND 9. The
  peak is 1.74 A/mm (Net-(U15-VDDA)).

## 6. Needs a decision

### 6.1 R1 current path versus the U19 / U25 connections
U19 (M1's driver) and U25 (the current-sense amplifier) sit beside R1. The rsense_lo and Vin current runs under
them on In2, In3 and In5. Their 12V, 5V and analog_5V pins cannot reach their rails without crossing that copper:
- With tracks and vias both limited to 0.25 A/mm, 53 connections failed.
- With vias allowed up to 1.0 A/mm, 12V and analog_5V at U19 and U25 still failed.
- U19.16 (12 V) has no path at all under the track limit, even with vias allowed up to 2.0 A/mm
  (`work/dbg_u19_reach.png`).

As routed, the crossings cost:
- **rsense_lo neck:** 9.5 → 4.9 mm wide, 7.0 → 2.5 mm long, IPC 20 → 59 °C. The cause is the vias of 5V, GND,
  ISNS_N and analog_5V within 4 mm.
- **Vin neck:** 10.0 → 5.3 mm wide, 11.2 → 3.6 mm long, 23.6 → 38.5 °C.
- **Vias:** worst 1.34 → 1.53× and 1.50 → 1.65×, in plane-connected fields.
- **Loss:** +23 mW in rsense_lo and +14 mW in Vin.

Options:
- **(a) Accept.** Every affected neck is under 5 mm long, and the vias are in plane-connected fields.
- **(b) Escape channels.** Cut small channels in the step-5 copper for U19's 12 V / 5 V and U25's analog 5 V, as
  v11 did for the ISNS pair, where the current map is lowest. Then route again. This changes power copper you
  accepted, so it needs your go-ahead.
- **(c) Placement.** Move U19's and U25's supply decoupling so the supplies enter from the cool side.

### 6.2 Vout_3 LED path throat at U6
Near U6 (67.3, 113.8) on In5, an analog_5V track (the last-resort crossing at 0.26 A/mm) plus IREF3, SNS_CH3 and
analog_5V vias leave the Vout_3 → J5 LED current (2.37 A) a throat 0.93 mm wide and 0.9 mm long:
- IPC 1.1 → 13.7 °C; the long-neck figure is 7.5 °C over 2.0 mm;
- R 1.45 → 1.81 mΩ.

Options:
- **(a) Accept** (short throat).
- **(b) Keep that corridor free:** I mark it as no-route for signals and re-route. This needs no rule change.

### 6.3 Gate loops (spec §9)
- **Return path:** the returns are routed pin to source pour, so they don't run beside the gate tracks.
- **Lengths:** the LX-side gates (M5/M6/M7, about 5 Ω) are 14–25 mm; the rail-side gates (M2/M3/M4, 220 Ω) are
  30–35 mm.

Options:
- **(a) Accept.**
- **(b) Pair-route** each gate with its return, which may need more pour crossings.
- **(c) Move** R13/R23/R47 and D11/D13/D14 next to the drivers, which is a placement change.

M1's loop is 2.7 mm.

### 6.4 Tracks narrower than the netclass default
KiCad netclass widths are defaults, not DRC minimums, and the `.kicad_dru` minimums (Power ≥ 0.5 mm,
high-current nets ≥ 1.0 mm) are all met. But some Rail and Gate tracks use the fallback width:
- analog_5V: 114 of 162 mm at 0.4 mm (class 0.8);
- 12V: 55 of 135 mm at 0.4 mm;
- 5V: 1 mm at 0.4 mm;
- GATE_M4: 30 of 33 mm at 0.3 mm (class 0.5).

I have not checked these nets' supply currents against the U19, U15, U10, U8 or op-amp datasheets, so I can't
say how much margin the narrow sections leave.

Options:
- **(a) Accept.**
- **(b) Widen** them, which means more crossings of power copper.

### 6.5 Long analog routes (placement)
- Current (U25.5 → J10.23): 93 mm.
- analog_5V: 162 mm in total, feeding U25, U11, U12, U6 and J10.22.
- IREF1/2/3: 15–32 mm.

These follow from U25 sitting at R1 and J10 in the middle of the board.

## 7. What was tried and rejected

| Attempt | Result |
|---|---|
| v12: no current map | DRC-clean but damaged the pours (§4). Moved to `work/rejected_v12/` with a note. |
| Current map with vias limited to 1.0 A/mm | 53 failed connections: U19, U25 and the U15 gate drive could not get out |
| No via-in-pad on signal pads | 29 failed connections; spec §2 says filled vias are free, and step 5 already uses them |
| The same, plus a GND fan-out via on every small GND pad before signals | 36 fan-out vias placed, 36 failed connections. The fan-out is kept only for the five pads that routes otherwise fence in |
| Merging two close layer changes into one via | Put a via 0.18 mm from J10.4 on a layer it was never checked on; now the second via spot is banned and the connection routed again |

## 8. Files

- **Board:** `BOOST_power_route_v13_NOT_FOR_FAB.kicad_pcb` / `.kicad_pro` / `.kicad_dru`.
- **DRC:** `work/v13.drc.json`.
- **Checks:** `work/v13_layer_checks.txt`, `work/v13_plane_checks.txt`, `work/v13_parity.txt`.
- **Solver:** `work/v11_B.json` → `work/v13_B.json` (compare with `tools/compare_solves.py`); current map
  `work/v11_jmap.npz`; loop inductance `work/v13_L.json`.
- **Routes:**
  - statistics `work/v13_route_stats.json`;
  - gate paths `work/v13_gate_paths.json`;
  - crossings `work/v13_crossings.json`;
  - router output `work/r_28.json` and `work/g_28_1.json`, `g_28_2.json` (with logs); the board was built from
    `work/sig_28_3.kicad_pcb`.
- **Renders:** `renders_v13/`.
- **Tools:**
  - routing: `route_signals.py`, `route_pipeline.sh`, `add_routes.py`, `prune_dangling.py`, `finalize.py`;
  - checks: `plane_checks.py`, `crossings.py`, `gate_paths.py`, `route_stats.py`, `compare_solves.py`,
    `plot_region.py`, `drc_summary.py`;
  - `solve_copper.py` gained `--jmap` and `--workers` (results unchanged: all 38 branches identical with and
    without `--jmap`);
  - `export_copper.py` now exports footprint copper graphics.

Not started: step 7, the control card (`control_sync3` still has to be built). The M1 turn-off re-check with the
LX pour capacitance remains optional, as you said.
