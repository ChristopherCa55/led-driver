# Routing specification — BOOST power board

Everything the copper has to satisfy. Numbers come from `BOOST_AUDIT.md`, the shipped
`BOOST_power.kicad_pro`, `SIMULATION_REPORT.md` and the verified-facts log
`replace_2026-09-14/tools/replace_notes.md`. Where a number is assumed rather than measured, it says so.

---

## 1. Stackup and layer plan

8 copper layers, 1.6 mm board. KiCad layer names in the file: `F.Cu`, `In1.Cu` … `In6.Cu`, `B.Cu`
(note the file's layer order is F, In1…In6, B).

| Layer | Role | Rule |
|---|---|---|
| F.Cu | High-current outer copper: input loop, LX, rail/bank pours | Outer weight decides B vs C |
| In1.Cu | **GND plane** | **GND only** — no other net, no exceptions |
| In2.Cu | Power / signal | |
| In3.Cu | Power / signal | **No LX copper** |
| In4.Cu | 5 V plane | Sits between In3 and In5 |
| In5.Cu | Power / signal | **No LX copper** |
| In6.Cu | **GND plane** | **GND only** |
| B.Cu | High-current outer copper + the ten TO-220s + small parts | |

Why In3/In5 carry no LX: they face the In4 5 V plane. The previous board's LX pours there coupled
232 pF into the logic supply; removing them took it to 20 pF. Keep it that way.

**The stackup is not yet written into the board file.** Once the user picks the copper weight, write it
in so the gerber job matches the order (audit check 2 failed because nothing in the files stated the
copper weight).

---

## 2. Netclasses and design rules

These come from the shipped `BOOST_power.kicad_pro`. Copy that file next to any board you save.

### Existing netclasses

| Class | Clearance | Track | Via Ø / drill |
|---|---|---|---|
| Default | 0.15 | 0.15 | 0.45 / 0.25 |
| Power | 0.25 | 2.00 | 0.80 / 0.40 |
| Gate | 0.20 | 0.50 | 0.60 / 0.30 |
| Rail | 0.20 | 0.80 | 0.60 / 0.30 |

Existing patterns — Power: `Vin`, `rsense_lo`, `LX`, `m2_source`, `m3_source`, `m4_source`,
`Vout_1`, `Vout_2`, `Vout_3`, `Output1_drain`, `Output2_drain`, `Output3_drain`, `GND`.
Gate: `GATE_M1` … `GATE_M7`. Rail: `12V`, `5V`, `analog_5V`.

### Board rules (`design_settings.rules`)

`min_clearance` 0.13 · `min_copper_edge_clearance` 0.30 · `min_hole_clearance` 0.20 ·
`min_hole_to_hole` 0.25 · `min_through_hole_diameter` 0.25 · `min_track_width` 0.13 ·
`min_via_annular_width` 0.10 · `min_via_diameter` 0.45 · `min_text_height` **1.00** ·
`min_text_thickness` **0.15**.

Predefined track widths 0.15 / 0.25 / 0.5 / 0.8 / 1.5 / 2.0 / 3.0 / 4.0 mm.
Predefined vias 0.45/0.25, 0.60/0.30, 0.80/0.40 mm.

### What you must add

1. **Sink current nets into the Power class:** `Net-(M8-S)`, `Net-(M9-S)`, `Net-(M10-S)` carry
   2.37–2.63 A. On the previous board they were Default class on 0.15 mm track and would have fused —
   stop-ship item 1. Add them as netclass patterns.
2. **A sense netclass** for `ISNS_P`, `ISNS_N`, `SNS_CH1`, `SNS_CH2`, `SNS_CH3`: narrow, routed as
   tight pairs, **never joined to a pour**, kept away from L1 and LX.
3. **A `.kicad_dru` custom rule file** enforcing minimum via drill ≥ 0.30 mm and minimum track width on
   Power nets, so nothing can quietly place a Ø0.25 mm via on a power branch. A `.kicad_dru` that only
   *tightens* rules is welcome; one that loosens any rule is not.

### Fabrication limits to design to (JLCPCB, so option C stays possible)

- Track / space ≥ **0.15 / 0.15 mm** (2 oz outer limit).
- Through-hole pad annular ring ≥ **0.254 mm** (2 oz). The previous board had 0.175 mm on 29 pads of
  J10 — audit check 13.
- Every via drill ≥ **0.30 mm**. Ø0.25 mm drills add $16.94 plus a $16.84 Kelvin test.
- Copper to board edge ≥ 0.30 mm (already the rule).
- Silk text ≥ 1.0 mm high / 0.15 mm stroke — already the rule, keep it.
- Epoxy-filled, capped vias are free on 6+ layer boards, so via-in-pad costs nothing extra.

---

## 3. Currents each net must carry

RMS unless stated. Source: `BOOST_AUDIT.md` §5 and the LTspice runs in `SIMULATION_REPORT.md`.

| Net | Current | Notes |
|---|---|---|
| `Vin` (J1 + input caps → R1) | 20.7 A | 18.4 A of it from the lugs |
| `rsense_lo` (R1 → L1) | 20.7 A | |
| `LX` L1 → M1 | 15.8 A | = √(20.7² − Σ channel²) |
| `LX` L1 → M7 / M6 / M5 | 7.05 / 7.69 / 8.35 A | |
| `m2_source` / `m3_source` / `m4_source` | 7.05 / 7.69 / 8.35 A | shared source pins, 2.54 mm apart |
| `Vout_1` / `Vout_2` / `Vout_3` | 6.54 / 7.22 / 7.92 A (bank AC) | plus DC to the LED pads |
| `Output1_drain` / `Output2_drain` / `Output3_drain` | 2.63 / 2.37 / 2.37 A | LED cathode → sink FET drain |
| `Net-(M10-S)` / `Net-(M9-S)` / `Net-(M8-S)` | 2.63 / 2.37 / 2.37 A | sink source → shunt |
| `GND` M1 source → input caps + J2 | 20.7 A total, 15.8 A of it M1's own | the worst return path |
| `GND` per output bank return | 6.54–7.92 A | |
| Input bank ripple | 10.36 A RMS at 14 V (8.61 A at 17 V) | 3 × EEH-ZU1E681UP ≈ 13.4 A usable |

Peaks: inductor peak ≈ 37.3 A; M1 instantaneous 40.5 A; reverse current into the rail drains ≤ 1.34 A.

---

## 4. Thermal and via targets

### Track width for a 20 °C rise (IPC-2221, long conductor)

| Current / layer | 0.5 oz | 1 oz | 2 oz |
|---|---|---|---|
| 20.7 A, outer | — | 12.9 mm | 6.4 mm |
| 8.35 A, inner | 19.2 mm | 9.6 mm | 4.8 mm |
| 8.35 A, outer | — | 3.7 mm | 1.8 mm |
| 2.63 A, inner | 3.9 mm | 1.9 mm | 1.0 mm |
| 2.63 A, outer | — | 0.75 mm | 0.37 mm |

IPC-2221 treats the neck as an infinitely long conductor, so it is conservative for short necks.
Figures above ~200 °C only mean "this fuses".

### Via barrel ratings (20 µm plating, 10 °C rise)

| Drill | Rating |
|---|---|
| Ø0.40 mm | ≤ 0.97 A |
| Ø0.30 mm | ≤ 0.80 A |
| Ø0.25 mm | ≤ 0.71 A |

**Never let one barrel carry a whole branch.** The previous board hung eight power connections on a
single Ø0.25 mm via each, at 2.6–7.2 A against 0.71 A capacity — stop-ship item 2. Use via *fields*:
size each array so no barrel exceeds its rating with margin, and check that the field is genuinely in
parallel in the solved field, not in series through a bottleneck.

### Surface-mount pads carrying > 10 A

This is where 1 oz and 2 oz really differ, because all the current enters on the outer layer:

- R1's current pads (CSS4J-4026, ≤ ~6 mm wide) at 20.7 A: ~70 °C rise at 1 oz vs ~23 °C at 2 oz.
  R1 also dissipates 0.85 W there.
- L1's pads (8 mm): ~44 °C vs ~14 °C.
- Filled vias in R1's pad do not rescue 1 oz: a row of ~3 Ø0.3 mm vias carries ~2.4 A of the 20.7 A.
- Through-hole parts (TO-220s, J1/J2 lugs) spread current over all layers, so B and C are about equal
  there.

---

## 5. Keep-outs and mechanical constraints

Already present in the baseline board as 8 keep-out zones (tracks, vias, pads, copper pours not
allowed, all 8 layers). Keep them, and add anything else you need.

| Keep-out | Rule |
|---|---|
| TO-220 washer, at each screwed tab hole (M1, M8, M9, M10) | 3.75 mm radius from the hole centre, **all copper layers**. Previous board had live copper 0.2 mm from every tab hole — audit check 10. |
| Screwdriver access | Nothing taller than 3 mm within **4.0 mm** of a tab-screw centre (this is the relaxed value the user was asked to approve at the placement check-in; confirm it still stands — see `OPEN_QUESTIONS.md`). |
| Standoffs H5–H8 | M3 non-plated, copper keep-out all layers, clear of power pours |
| Control-card outline | Nothing taller than the stack budget allows underneath; **never over L1** |
| J10's GND pins | Outside M1's return-current field. On the previous board they sat 7–19 mm from M1's source, giving up to 8.5 mV of setpoint offset — audit check 9. |
| U16 (LM2940, TO-263) | On F.Cu. It is 4.83 mm tall against a 4.6 mm gap under the board. |
| Case penetrator | Board notch x 86–104, y 30–42 already in the outline |

Unscrewed FETs (M2–M7) use `BOOST:TO-220-3_Horizontal_TabUp_NoHole` and must be within 25 mm of the
nearest screw point (tab screw or card standoff) so the board is held flat. Baseline distances:
M2 10.8, M3 17.3, M4 22.6, M5 13.6, M6 11.4, M7 12.1 mm.

---

## 6. Placement targets

The full table, with the baseline's numbers in the "New" column, is
`replace_2026-09-14/tools/placement/BOOST_power_p15_WIP_NOT_FOR_FAB.distances.md` (49 rows,
regenerate with `ptable.py`). Two target columns: the **brief target** (the original ideal) and the
**agreed goal** (what the user accepted after the placement proved over-constrained).

### Hard goals — these must hold

- Each rail FET within 15 mm of **its own** three output caps.
- M1 within 5.5 mm of D19 (both the LX and the GND leg).
- Each sink FET's source within 5 mm of its own shunt.
- Each switch pair's shared source adjacent (≤ 11.25 mm; baseline achieves 2.5 mm).
- U25 within 10 mm of R1's two sense pads.

### Loose goals

Input caps ~20 mm to R1's Vin pad and to M1's source; farthest switch-node drains 22–30 mm;
LED pads paired within 8 mm; sink op-amp within 10 mm of its shunt and its FET gate.

### Where the baseline misses (your chance to do better)

| Path | Baseline | Goal |
|---|---|---|
| M2 drain → C70 | 20.1 mm | ≤ 15 |
| M3 drain → C87 | 18.8 mm | ≤ 15 |
| L1 LX pad → M1 drain | 16.5 mm | ≤ 15 |
| M9 drain → J7 | 24.4 mm | ≤ 15 |
| U12 OUT → M9 gate | 14.7 mm | ≤ 10 |
| U6 IN− → NT3 | 11.7 mm | ≤ 10 |
| U6 OUT → M8 gate | 15.3 mm | ≤ 10 |
| C40 Vin → R1 Vin force pad | 37.2 mm | ≤ 20 |
| C85 Vin → R1 Vin force pad | 20.3 mm | ≤ 20 |
| R1 rsense_lo → L1.2 | 11.2 mm | ≤ 10 |
| L1 LX → M5 drain | 45.2 mm | ≤ 22 |

Score: 31 of 49 brief targets, 38 of 49 agreed goals.

### Geometry facts that constrain any placement

- **L1's two pads are 12 mm apart on one edge** (LX and rsense_lo), so no input cap can be within 10 mm
  of both R1 and M1. This is why the input-loop goals are loose.
- Top-side-only parts already take 4,086 of 6,148 mm² (66 %); eight screw points each needing an 11 mm
  tall-part-free circle bring it to 79 %, before ~72 small parts.
- J10 is a 39.2 mm through-hole part needing a FET-free strip on the underside, and must sit inside the
  45 mm card.
- ~250 annealing runs found no layout that was both legal and close on every hard goal under the
  original rules. If you find one, that is a genuine improvement — show the numbers.

---

## 7. The copper solve (deliverable 4)

Reuse the method documented in `AUDIT_RESPONSE.md` §1, which reproduced the audit's numbers within
1–3 % on most branches:

> Load the saved board in KiCad 10 Python and refill every zone. Export each net's copper per layer:
> zone fill, tracks, via pads and pads. Join layers through plated barrels (20 µm). Solve a
> conductance mesh on a 0.1 mm grid (0.2 mm for GND, 0.05 mm for the sink-source nets) with the
> terminal pads held as equipotentials. The neck is the co-area integral of |∇φ| over every
> equipotential band.

For every high-current branch report: resistance, minimum cross-section, where the neck is, average
current density there, IPC-2221 rise, and the current in every via barrel against its rating — **at
1 oz and at 2 oz outer**.

**Decision rule (the user's):** choose **B (1 oz outer / 1 oz inner, ~$106.68 for 5)** only if every
neck is ≤ 20 °C rise and every via is within rating at 1 oz. Otherwise **C (2 oz outer / 1 oz inner,
~$141.68)**. Never 0.5 oz inner — inner layers carry rail currents. Quote is JLCPCB, 2026-09-14,
5 boards, 74 × 86 mm, 8 layers, 1.6 mm, before ~$28 shipping.

---

## 8. The audit's checks — your board must clear these

`BOOST_AUDIT.md` ran 13 checks on the previous layout; 10 failed, 5 were stop-ship. The five
stop-ship items exist to be fixed by this placement + routing:

| # | Stop-ship finding | What clears it |
|---|---|---|
| 1 | Sink current (2.63 A) on 0.15 mm track, 50–101 mm long; op-amps sensing 42–270 mΩ upstream, so LEDs got 45–84 % less current | Sink nets in Power class, shunt within 5 mm of the FET source, net-ties NT1–NT3 giving a true Kelvin sense point |
| 2 | Eight power connections on a single Ø0.25 mm via each, at 2.6–7.2 A | Via fields, every barrel within rating, ≥ 0.30 mm drill |
| 3 | Commutation loop: 74 / 137 / 99 V copper-only at 8 A/ns (budget ≤ 4.31 nH for 70 V) | Minimise each M1 → LX FET → rail FET → bank → GND loop area. Note the packages alone exceed the budget, so report the copper-only figure and say so honestly |
| 4 | Current sense read 32 % high (INA241 46 mm from R1, tapping the pours) | 4-terminal R1 + `ISNS_P`/`ISNS_N` routed as a pair to U25's inputs, touching no pour |
| 5 | Stack didn't fit (36.5 mm against 33 mm), no mounting holes on the card | The 21.21 mm header stack and H1–H8 holes already in the schematic |

The other failed checks to re-verify on your board: 2 (copper weight stated in the file),
5 (current density / necks), 7 (vias in the current path), 8 (J10/J11 pinout, GND beside every analog
pin, mateable, annular ring), 9 (ground return and measurement integrity), 10 (TO-220 mounting
keep-outs), 12 (mechanical fit), 13 (JLCPCB limits).

Checks 6 (capacitor current sharing — worst part must stay under 4.5 A per output cap, 5.4 A per input
part) and 11 (PCB ↔ schematic netlist equivalence: 0 splits, 0 merges, 0 mismatches) passed before and
must still pass.

---

## 9. Signal routing rules

- **`ISNS_P` / `ISNS_N`** (R1 Kelvin): routed together as a tight pair, away from L1 and the LX node,
  touching no pour, terminating only on R1's two sense pads and U25 pins 8 (IN+) and 1 (IN−).
- **`SNS_CH1/2/3`**: from the net-tie on each shunt's top pad to its op-amp IN− (U11.4, U12.4, U6.4).
  Same treatment: no pour, short, no shared return with the 2.4–2.6 A sink current.
- **Gate loops** (`GATE_M1`…`GATE_M7`, plus the sink gates): driver → gate resistor → FET gate, with
  the return path beside the forward path. Gate resistors are R13/R23/R47 = **220 Ω** (rail side),
  R59/R60/R70 ≈ 5 Ω (LX side), R15 = **10 Ω** (M1, D12 deleted), R22/R50/R56 = 100 Ω (sinks).
- **J10 header pinout** is fixed in the schematic: 1 GND, 2 GND, 3 M1_ON, 4 M2_ON, 5 ena_out_1,
  6 out_2_on, 7 ena_out_2, 8 out_3_on, 9 ena_out_3, 10 5V, 11 GND, 12 GND, 13 Vout_1,
  14 Output1_drain, 15 Vout_2, 16 Output2_drain, 17 Vout_3, 18 Output3_drain, 19 12V, 20 GND, 21 GND,
  22 analog_5V, 23 Current, 24 GND, 25 GND, 26 IREF1_input, 27 IREF2_input, 28 GND, 29 GND,
  30 IREF3_input. Every analog pin already has a GND neighbour; route so it stays a real return.
- **GND** is the trickiest net: In1 and In6 are the planes, and M1's 15.8 A return must reach the input
  caps and J2 without forcing plane current through a narrow ring around M1's source pin (the previous
  board's neck: 0.284 mm², > 200 °C). Give the bank returns multiple vias each (≥ 2 per shunt return)
  and keep the analog reference away from the high-current field.

---

## 10. Final checks before you hand back

On the **saved** file, after a fresh load and zone refill:

1. `kicad-cli pcb drc --severity-all --format json`: 0 errors, 0 unconnected, 0 exclusions.
2. No `.kicad_dru` rule that loosens anything; silk rule still 1.0 / 0.15.
3. No untied copper islands.
4. In1 and In6 carry GND only (0 tracks, 0 zones of any other net).
5. No LX copper on In3 or In5.
6. Netlist parity against `BOOST_9-15_nohole.net`: every footprint, library ID, value and pad net.
7. The solver table re-run on the shipped file, matching what you report.
8. Stackup written into the board file once the copper weight is chosen.
9. Both sides plotted/rendered.
