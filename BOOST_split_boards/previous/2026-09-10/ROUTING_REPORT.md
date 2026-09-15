# BOOST split boards — final routing report

Generated 2026-09-10 from the saved files in this directory, after closing and
reloading them, refilling all zones, and re-running DRC on what was reloaded.
Every figure below comes from the shipped `.kicad_pcb` files, not from an
in-memory board.

The previous (2026-09-09) files are preserved in `previous/2026-09-09/`.

---

## 1. Results

| | POWER | CONTROL |
|---|---|---|
| Unrouted connections | **0** | **0** |
| Unconnected zone items | **0** | **0** |
| DRC errors | **0** | **0** |
| DRC warnings | **1** (config-only, see §6) | **0** |
| Dangling tracks | **0** | **0** |
| Shorts | **0** | **0** |
| Clearance / hole / drill violations | **0** | **0** |
| Untied copper islands | **0** | **0** |
| Silkscreen violations | **0** | **0** |
| High-current bottlenecks found | 0 remaining | 0 |
| High-current bottlenecks fixed | 13 branches verified in spec | 4 rails verified |
| `.kicad_pro` rule severity overrides | **0** | **0** |
| `.kicad_pro` DRC exclusions | **0** | **0** |
| Custom rules file (`.kicad_dru`) | none | none |

No DRC check was disabled, downgraded or excluded. The "ignored checks" list in
the `.rpt` files is KiCad 10's stock default set, unmodified.

### Verified independently of DRC

Connectivity, dangling ends, isolated copper and plane dedication were each
recomputed from the copper geometry (`audit.py`, `netcomp.py`, `island.py`,
`perlayer.py`, `planecheck.py`) rather than taken from the DRC result:

- POWER GND is **one connected component** — 2351 copper nodes (84 pads,
  1822 tracks, 285 vias, 160 zone islands) joined into a single piece.
- The In1 and In6 ground planes are each **a single filled outline of
  4857.24 mm²**. Nothing but GND appears on either plane layer: 0 tracks,
  0 zones.
- 0 track ends anywhere on either board fail to land on same-net copper.
- 0 filled zone islands on either board have nothing landing on them.

---

## 2. High-current verification

Pad-to-pad resistance solved on a 0.4 mm × 8-layer conductance mesh, then
quoted as the width of a plain single-layer trace of the same span and
resistance ("equivalent width"), which is directly comparable with IPC-2221.

**Assumed copper weight: 2 oz (70 µm), 0.246 mΩ/square.** Requirement column is
IPC-2221 external-layer at a **20 °C rise**.

### POWER

| Net | Branch | A | Span | R | W equiv | W needed | Loss | |
|---|---|---|---|---|---|---|---|---|
| Vin | J1.1 → R1.2 | 18.4 | 48.7 mm | 0.47 mΩ | 25.43 mm | 5.48 mm | 0.16 W | ok |
| Vin | C85.1 → R1.2 | 18.4 | 17.2 mm | 0.26 mΩ | 16.11 mm | 5.48 mm | 0.09 W | ok |
| Vin | C40.1 → R1.2 | 18.4 | 21.2 mm | 0.23 mΩ | 22.71 mm | 5.48 mm | 0.08 W | ok |
| rsense_lo | R1.1 → L1.2 | 20.7 | 10.6 mm | 0.37 mΩ | 7.10 mm | 6.44 mm | 0.16 W | ok |
| LX | L1.1 → M1.2 | 20.7 | 19.1 mm | 0.36 mΩ | 12.88 mm | 6.44 mm | 0.16 W | ok |
| LX | L1.1 → M7.2 | 20.7 | 10.4 mm | 0.22 mΩ | 11.64 mm | 6.44 mm | 0.09 W | ok |
| LX | L1.1 → M6.2 | 20.7 | 31.2 mm | 0.49 mΩ | 15.54 mm | 6.44 mm | 0.21 W | ok |
| LX | L1.1 → M5.2 | 20.7 | 59.3 mm | 0.50 mΩ | 28.91 mm | 6.44 mm | 0.22 W | ok |
| GND | M1.3 → C85.2 | 20.7 | 27.8 mm | 0.16 mΩ | 41.45 mm | 6.44 mm | 0.07 W | ok |
| GND | M1.3 → J2.1 | 20.7 | 43.3 mm | 0.16 mΩ | 67.25 mm | 6.44 mm | 0.07 W | ok |
| GND | M1.3 → C40.2 | 20.7 | 38.8 mm | 0.16 mΩ | 59.64 mm | 6.44 mm | 0.07 W | ok |
| Vout_1 | M2.2 → C86.1 | 4.54 | 34.1 mm | 3.37 mΩ | 2.48 mm | 0.79 mm | 0.07 W | ok |
| Vout_1 | M2.2 → J3.1 | 4.54 | 57.2 mm | 4.87 mΩ | 2.89 mm | 0.79 mm | 0.10 W | ok |
| Vout_2 | M3.2 → C78.1 | 4.54 | 34.4 mm | 5.46 mΩ | 1.55 mm | 0.79 mm | 0.11 W | ok |
| Vout_2 | M3.2 → J8.1 | 4.54 | 23.1 mm | 2.39 mΩ | 2.38 mm | 0.79 mm | 0.05 W | ok |
| Vout_3 | M4.2 → C77.1 | 4.54 | 55.1 mm | 5.67 mΩ | 2.39 mm | 0.79 mm | 0.12 W | ok |
| Vout_3 | M4.2 → J5.1 | 4.54 | 34.5 mm | 3.38 mΩ | 2.51 mm | 0.79 mm | 0.07 W | ok |
| m2_source | M7.3 → M2.3 | 12.0 | 11.2 mm | 0.80 mΩ | 3.46 mm | 3.04 mm | 0.11 W | ok |
| m3_source | M6.3 → M3.3 | 12.0 | 11.2 mm | 0.58 mΩ | 4.74 mm | 3.04 mm | 0.08 W | ok |
| m4_source | M5.3 → M4.3 | 12.0 | 22.0 mm | 0.67 mΩ | 8.06 mm | 3.04 mm | 0.10 W | ok |
| Output1_drain | M10.2 → J4.1 | 2.63 | 48.8 mm | 18.21 mΩ | 0.66 mm | 0.37 mm | 0.13 W | ok |
| Output2_drain | M9.2 → J7.1 | 2.63 | 61.3 mm | 13.67 mΩ | 1.10 mm | 0.37 mm | 0.09 W | ok |
| Output3_drain | M8.2 → J6.1 | 2.63 | 50.8 mm | 8.82 mΩ | 1.41 mm | 0.37 mm | 0.06 W | ok |

Currents used: Vin 18.4 A average; LX 20.7 A RMS; GND 20.7 A return;
Vout_n 4.54 A (2.63 A DC and 3.7 A RMS ripple combined in quadrature);
m*_source 12 A; Output*_drain 2.63 A.

**Nothing implies more than a 20 °C rise.** The tightest margin is rsense_lo at
7.10 mm equivalent against 6.44 mm required (1.10×); every other branch is
1.5× to 10× its requirement. Worst single-branch loss is 0.22 W (LX to M5).

The 40.5 A LX peak is a switching transient, not a thermal load — RMS heating is
covered by the 20.7 A row above, and the peak is treated as a voltage/inductance
question in §3.

### CONTROL

| Net | Branch | A | Span | R | W equiv | W needed | |
|---|---|---|---|---|---|---|---|
| 12V | J11.19 → R84.1 | 0.5 | 33.3 mm | 20.02 mΩ | 0.41 mm | 0.04 mm | ok |
| 5V | U106.14 → R69.2 | 0.3 | 47.0 mm | 2.38 mΩ | 4.84 mm | 0.02 mm | ok |
| GND | C68.2 → R68.2 | 0.5 | 54.0 mm | 2.09 mΩ | 6.36 mm | 0.04 mm | ok |
| analog_5V | R96.1 → C38.2 | 0.1 | 52.1 mm | 19.30 mΩ | 0.66 mm | 0.00 mm | ok |

---

## 3. D19 clamp loop — acceptance test

D19 is a 5KP54A (54 V standoff, 5 kW) from LX to GND, protecting M1
(HYG180N10, 100 V BVDSS).

Measured, from the shipped file:

| Leg | Span | R | W equiv | Effective loop area | L |
|---|---|---|---|---|---|
| LX: M1.2 → D19.1 | 29.2 mm | 0.87 mΩ | 8.22 mm | 29.2 × 0.2 = 5.84 mm² | 0.89 nH |
| GND: D19.2 → M1.3 | 26.5 mm | 0.53 mΩ | 12.39 mm | 26.5 × 0.2 = 5.30 mm² | 0.54 nH |
| **Copper total** | | | | **11.1 mm²** | **1.43 nH** |

The loop area that matters is not the 29 mm lateral run — it is the thin
dielectric gap between the LX/GND pour and the plane directly beneath it. Both
legs are wide plane-like copper (8.2 mm and 12.4 mm equivalent) over a solid
GND plane 0.2 mm below, so `L ≈ µ₀·h·span/width` gives 1.43 nH of copper.

Adding a conservative 3 nH for the SMC package and its pads:

**L_loop ≈ 4.4 nH**, against the 8 nH budget.

### Test

At 8 A/ns (M1 desaturating at ~40 A):

```
V_L   = 4.4 nH × 8×10⁹ A/s  = 35.2 V
V_pk  = 35.2 + 35.5         = 70.7 V   against 100 V BVDSS
```

**PASS**, with 29.3 V of margin, using 55 % of the 8 nH budget.

Sensitivity — the conclusion does not depend on the assumptions:

| Assumption | L_loop | V_pk | |
|---|---|---|---|
| 0.2 mm dielectric, 3 nH package (nominal) | 4.4 nH | 70.7 V | pass |
| 0.3 mm dielectric, 3 nH package | 5.2 nH | 76.7 V | pass |
| 0.3 mm dielectric, 5 nH package (pessimistic) | 7.2 nH | 92.7 V | pass |

**D19 was not relocated, and M1, U19 and J10 were not displaced.** No local
snubber across M1's drain-source is required.

For the record, had it been needed: the nearest free 9.4 × 4.4 mm window to M1
anywhere on the bottom side is 27 mm away — which is where D19 already sits.
The area around M1 is taken by M1's own TO-220 horizontal courtyard, U19
(SOIC-16W, 7.5 × 10.3 mm) and J10 (2 × 15 header). Relocating D19 nearer was
therefore not possible without displacing one of those, and the measurement
shows it was not necessary.

---

## 4. Components moved

Six on POWER; none on CONTROL. Connector locations were preserved.

| Ref | Value | From | To | Why |
|---|---|---|---|---|
| R1 | 12 mΩ shunt | (98.75, 57.00) top | (50.88, 51.25) rot 90, **bottom** | Was 48 mm away at the connector. Moved into the switching loop between Vin and L1 so the 20.7 A shunt path is short. |
| D19 | TVS 5KP54A | (83.01, 49.80) — **15 mm outside the board outline** | (43.13, 51.25) bottom | Was off-board entirely. Now on-board near the switch node; loop verified in §3. |
| C84 | 100 n Vin bypass | (46.75, 69.75) | (32.125, 69.625) | Cleared from the LX high-current corridor. |
| D12 | SOD-123 | (51.25, 69.25) | (43.263, 88.50) | Cleared from the LX corridor. |
| R104 | 10 k | (55.75, 69.25) | (44.125, 91.125) | Cleared from the LX corridor. |
| R14 | 1 MΩ LX bleeder | (59.75, 69.50) | (40.88, 91.62) | First moved out of the LX corridor, which landed it inside a GND stitching-via field 20 mm from any LX copper with no legal escape on any layer. Moved again to sit beside existing LX copper. Carries microamps, so placement is electrically free. |

---

## 5. Via arrays and pour structure

**1050 vias on POWER**, in three classes:

| Diameter / drill | Count | Purpose |
|---|---|---|
| 0.80 / 0.40 mm | 709 | high-current stitching arrays |
| 0.45 / 0.25 mm | 260 | signal routing and pocket ties |
| 0.60 / 0.30 mm | 81 | pre-existing signal vias |

0.80 mm stitching arrays, by net:

| Net | Barrels | | Net | Barrels |
|---|---|---|---|---|
| Vin | 246 | | m4_source | 18 |
| GND | 190 | | Vout_1 | 11 |
| LX | 65 | | m2_source | 11 |
| Vout_2 | 63 | | Output2_drain | 9 |
| Vout_3 | 37 | | Output3_drain | 7 |
| m3_source | 26 | | Output1_drain | 7 |
| rsense_lo | 19 | | | |

Every barrel is 0.40 mm drill — at or above the board's 0.25 mm minimum
through-hole diameter, with the annular ring rule satisfied.

### Copper pours

Each high-current net is a **non-overlapping tiling region** on both outer
layers, grown outward from its own pads and along its current branches so the
regions meet rather than overlap. Overlapping full-board hulls were the original
defect: priority carved the loser away and rsense_lo filled 3 % of its outline.
LX and rsense_lo additionally get inner-layer copper.

| Net | Zones | Filled | Layers (priority) |
|---|---|---|---|
| GND | 3 | 12191.4 mm² | F.Cu p3; B.Cu p2; **In1+In6 p10 (planes)** |
| LX | 5 | 3652.2 mm² | F.Cu p88; B.Cu p70; In2 p58; In3 p57; In5 p56 |
| 5V | 1 | 3623.5 mm² | In4 p40 |
| Vin | 2 | 2148.8 mm² | F.Cu p90; B.Cu p66 |
| rsense_lo | 5 | 1064.0 mm² | F.Cu p89; B.Cu p59; In2 p55; In3 p54; In5 p53 |
| Vout_3 | 2 | 797.1 mm² | F.Cu p82; B.Cu p63 |
| m3_source | 2 | 545.8 mm² | F.Cu p86; B.Cu p61 |
| Vout_2 | 2 | 453.9 mm² | F.Cu p83; B.Cu p64 |
| m4_source | 2 | 259.0 mm² | F.Cu p85; B.Cu p60 |
| Vout_1 | 2 | 202.2 mm² | F.Cu p84; B.Cu p65 |
| Output3_drain | 2 | 179.1 mm² | F.Cu p79; B.Cu p67 |
| Output2_drain | 2 | 160.6 mm² | F.Cu p80; B.Cu p68 |
| m2_source | 2 | 105.6 mm² | F.Cu p87; B.Cu p62 |
| Output1_drain | 2 | 68.3 mm² | F.Cu p81; B.Cu p69 |

In1 and In6 carry GND and nothing else.

---

## 6. Routing changes made in this pass

Starting point: POWER had 7 open connections, 2 unconnected GND zone items,
10 dangling stubs, and a set of via defects introduced by the pad-escape router.

| Change | Detail |
|---|---|
| Ground pockets closed | U8.4/U8.5 and C3.2/C76.2 sat in B.Cu ground puddles fenced off from the rest of GND. Each is now tied by a short B.Cu run to the main pour — 9 grid cells each — at a cost of two `Net-(U12-OUT)` segments, which were re-routed. |
| Stacked barrels merged | 26 barrels sat on 7 coordinates (paths that stepped to a layer and back). Merged into one barrel per coordinate spanning the union of their layer ranges; nothing was disconnected. |
| Illegal drills opened | 16 barrels had a 0.2475 mm drill, below the board's 0.25 mm minimum. Opened to 0.25 mm with the annular ring rule re-checked. |
| Pads freed from stitching arrays | C84.1 (Vin), C83.1 (Vin), D12.2 (GATE_M1), C60.2 (m4_source) and R14.1 (LX) had been ringed by 0.80 mm GND barrels. Only the barrels actually in the corridor were removed, then each pad routed. |
| R14 relocated and routed | See §4. |
| Signals re-routed after the tie | `Net-(U12-OUT)` (2 segments), plus 12 V, 5 V, GATE_M5 and an LX inner-layer link — 7 pairs closed by the stitch router, 0 failed. |
| Dangling stubs cleared | 24 stubs removed across 9 iterations, re-running DRC each time. The unconnected count stayed at 0 throughout, confirming the removed copper was redundant. |
| Reference designators restored | See §7. |

Two defects in the tooling were found and fixed along the way, both of which had
been producing bad copper:

- `PAD::GetLayer()` reports F.Cu for a flipped footprint's B.Cu pad. The escape
  router had been searching the wrong layer for such pads; keyed off
  `IsOnLayer()` instead.
- The ground-tie pass chose which copper to move aside using the *track*
  clearance radius, but then placed a *barrel*, which is wider and blocks every
  layer. It now uses the barrel radius across the whole stack at the cells where
  a barrel will go.

---

## 7. Silkscreen

Reference designators are back on silkscreen for the parts a person has to
identify with the board in their hand: **every through-hole part and connector,
plus L1**. Fine-pitch SMD designators stay on F.Fab/B.Fab, where they do not
collide with copper.

- POWER — 20 restored: J1–J8, J10 (F.SilkS), L1 (F.SilkS), M1–M10 (B.SilkS).
- CONTROL — 2 restored: J9 (F.SilkS), J11 (B.SilkS). These are the only
  through-hole parts on that board.

Every restored designator was then placed clear of exposed copper (the
solder-mask opening of every pad on that side), clear of other silkscreen, and
inside the board outline. 18 were stepped around their part; one (J3) was set to
0.80 mm text, the board's minimum text height, to fit. All sit between 0.12 mm
and 3.45 mm clear of their own part's outline.

Three rounds of this were needed. The first produced 7 `silk_edge_clearance`
violations — text pushed past the board edge — which were fixed by adding an
outline constraint to the placement search, not by suppressing the check. The
second left J4 with no legal spot; adding corner positions and 90° rotation to
the search placed it.

**Final silkscreen violation count on both boards: 0.**

---

## 8. The one remaining warning

```
[lib_footprint_issues]: The current configuration does not include the
footprint library 'CSCF3218-6R8MC'   @(48.5, 46.875): Footprint L1
```

This is configuration-only and safe to leave. Verified against the original
`BOOST-github/BOOST/BOOST.kicad_pcb`:

- 19 graphic shapes — **identical**
- 3 pads (position, size, layers, solder-mask margin) — **identical**
- `(attr smd)` — **identical**

The project has no `fp-lib-table` at all, so the nickname `CSCF3218-6R8MC`
cannot resolve; the board carries the complete footprint definition inline and
KiCad uses that. The warning would clear by adding the library to the footprint
library table, which is an environment change, not a board change.
