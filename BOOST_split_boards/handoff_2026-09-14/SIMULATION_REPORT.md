# BOOST: lead-inductance, M1 turn-off and dead-time simulations

2026-09-14. LTspice 26.0.1. All runs are copies of the user's schematic in a scratch folder; the user's
`BOOST.asc` was **not** modified. The only change made to the user's files is the FET model
(`HYG180N10.lib` REV 5, see §2).

## 1. Summary

| Finding | Evidence |
|---|---|
| The clean switch node in the original simulation (LX 35.5 V, TVS 1.26 mW) depended on **zero parasitic inductance**. | FET model had no lead inductance; the only loop inductance in `BOOST.asc` was the capacitors' 4 nH ESL. |
| With typical TO-220 lead inductance alone, **M1's die reaches the 100 V avalanche clamp on every turn-off**. | 124 of 124 turn-offs in 35–39 ms; TVS 1.5 mW → 143 mW; LX at the pins 64.8 V. |
| Adding the audit's copper loop inductance makes it worse. | TVS 315 mW, LX pins 67 V, M1 die 100 V. |
| **M1 turn-off through 10 Ω fixes it** at a cost of +0.73 W in M1. | M1 die 68 V, TVS 38 mW, no avalanche, M1 loss 4.09 → 4.82 W. |
| Deleting D12 and making R15 = 10 Ω gives **identical** results to a split turn-on/turn-off network. | §5, table 3. |
| 47 Ω is too slow: the rail FET turns on while M1 is still fully on (shoot-through). | Reverse current into rail FET drains 7.2–8.3 A (vs 1–2 A). |
| The dead time is **~30 ns, not ~100 ns**. The logic gap is only ~5 ns; the 100 Ω rail-side gate resistors (R13/R23/R47) set the rest. | §6. |
| With M1 at 10 Ω the shoot-through margin shrinks from 21–25 ns to 13–18 ns. | §6. Recommended fix: R13/R23/R47 100 Ω → **150 Ω** (not yet simulated, §8). |

## 2. Model change (the only edit to the user's files)

File: `led-driver/BOOST-github/LTspice/BOOST/HYG180N10.lib` (git-tracked, **uncommitted**). Copy in
this folder: `sim/HYG180N10_REV5.lib`. The identical copy in
`Documents/LTspice/BOOST-github/LTspice/BOOST/` (the one the user's open LTspice session uses) is
**unchanged**.

- `HYG180N10` (3-terminal) now has package lead inductance: **LD 4.5 nH, LS 7.5 nH, LG 7.5 nH**.
  These are typical TO-220 values (lead measured 6 mm from the package to the die), not from the
  HYG180N10 datasheet, which lists none. D, G, S are the pins; Di, Gi, Si are the die. The body
  diode and avalanche clamp sit on the die, inside the leads.
- The REV 4 model without leads is kept in the same file as **`HYG180N10_NOLEADS`**.
- `HYG180N10_4T` is unchanged.

**Warning for the user's own schematic:** with REV 5 on the LED sink FETs M8–M10, the full
schematic stalls at ~0.13–0.33 ms (tried: plain leads, leads damped with Rpar = 50 Ω, no gate lead).
Until that is understood, set M8, M9 and M10's Value to `HYG180N10_NOLEADS`.

## 3. Test bench (applied to netlist copies only)

| # | Change from `BOOST.asc` (2026-08-31) | Why |
|---|---|---|
| 1 | Servo `.ic` corrected: `.ic V(N064)=2.7 V(N065)=3.7 V(N058)=3.7` → `.ic V(N061)=2.89 V(N062)=3.86 V(N055)=3.90` | After later edits LTspice renumbered the nodes. N058 is now M9's drain-sense divider; the servo integrator outputs are now N061 (ch1, U24), N062 (ch2, U23), N055 (ch3, U22). With the stale `.ic` the servos start cold (~220 ms to settle) and a 40 ms run measures a half-power circuit (LEDs 0.73 / 1.14 / 1.07 A). Values are the settled servo voltages from the 2026-08-27 run. **Recommend net labels on these nodes in `BOOST.asc`** so the `.ic` survives renumbering. |
| 2 | M8–M10 use `HYG180N10_NOLEADS` | Convergence (§2). Sinks are not in the commutation loop. |
| 3 | M1–M7 use `HYG180N10_PROBE` | Identical to REV 5 but with the die nodes (Di, Si, and in d0/d10 also Gi) brought out as pins, because `.save` cannot reach subcircuit internals. |
| 4 | 0 V current probes: `Vsense_m1` in M1's drain; `Vsense_m2/m3/m4` in the rail FET drains | Positive `I(Vsense_m2)` = current flowing from Vout into M2's drain, i.e. the reverse / shoot-through direction. |
| 5 | Copper loop inductance (runs c0, f*, d*): `Lcu_ch1` 4.85 nH (Vout_1 → M2 drain), `Lcu_ch2` 12.74 nH (Vout_2 → M3), `Lcu_ch3` 7.91 nH (Vout_3 → M4) | The audit's copper-only commutation-loop inductance for the **current** layout, lumped into each rail path. D19 stays directly on the LX pins, i.e. the best-case TVS placement. |
| 6 | M1 gate networks (see table 2/3) | Current: R15 5.1 Ω (turn-on) with D12 bypassing it at turn-off. Split (f*): D12 reversed in series with R15 for turn-on, `Roff_M1` from GATE_M1 to U19's output (N026) for turn-off. Single (d10): R15 = 10 Ω, D12 deleted. |
| 7 | `.tran 0 40m 34.5m startup uic`, `.options plotwinsize=0`, small `.save` set | Measurements over 35–39 ms, computed in Python (`sim/scripts/measure.py`, `deadtime.py`). LTspice's own `.meas FROM/TO` failed because the saved time axis is offset when Tstart is used. |

Operating point in every run: Vin 14 V; LEDs 2.631 / 2.368 / 2.368 A (the 08-31 schematic has
Iref1 = 2.5 V, Iref2 = Iref3 = 2.25 V); Vout 23.2 / 33.0 / 33.0 V; inductor peak ~37 A; ~31 kHz
M1 turn-offs (124 in 4 ms).

**Gotcha found while building the sweep:** LTspice node names are case-insensitive. A node named
`m1_on` silently merged with the `M1_ON` logic net and invalidated the first attempt (M1's gate never
exceeded ~7.7 V). Those runs were discarded and re-run with `m1_ton`.

## 4. Lead inductance only (no copper), current gate drive

| | Without leads (`base2`) | With leads (`leads3`) |
|---|---|---|
| LX at the pins, peak | 34.8 V | 64.8 V |
| M1 die Vds, peak | 34.8 V | **100.3 V** (avalanche clamp, 124/124 turn-offs) |
| TVS average power | 1.5 mW | **143 mW** (~6 µJ per turn-off) |
| TVS peak current | 5.2 A (junction capacitance) | 9.8 A |
| M7 die | 13.7 V | 55.6 V |
| M5 / M6 die | 10.6 V | 41.6 / 41.4 V |
| M2 / M3 / M4 die | 23.2 / 33.2 / 33.2 V | 28.2 / 37.5 / 37.4 V |
| M1 turn-off di/dt (LS voltage / 7.5 nH) | — | 3.8 A/ns peak |
| LED currents, rails | unchanged | unchanged |

## 5. M1 turn-off resistor sweep (leads + copper)

Table 2: split network (turn-on R15 5.1 Ω + diode, turn-off `Roff_M1`).

| M1 turn-off | M1 die peak | LX pins | TVS avg | M1 di/dt | M1 total loss | of which conduction | Reverse current into rail FET drains, peak |
|---|---|---|---|---|---|---|---|
| Current circuit (`c0`) | **100 V (avalanche)** | 67.0 V | 315 mW | 3.9 A/ns | 4.09 W | 2.99 W | 1.6–2.2 A |
| 2.2 Ω (`f2p2`) | **100 V (avalanche)** | 65.6 V | 224 mW | 5.9 A/ns | 4.73 W | 3.02 W | 1.5–2.1 A (gate rings to 14.7 V) |
| 4.7 Ω (`f4p7`) | 77.5 V | 62.7 V | 57 mW | 2.7 A/ns | 4.74 W | 3.02 W | 1.3–1.5 A |
| **10 Ω (`f10`)** | **68.0 V** | 62.0 V | **38 mW** | 0.84 A/ns | **4.82 W** | 3.01 W | 1.1–1.3 A |
| 22 Ω (`f22`) | 66.7 V | 61.4 V | 20 mW | 0.71 A/ns | 5.18 W | 3.03 W | 0.9–1.1 A |
| 47 Ω (`f47`) | 64.3 V | 59.2 V | 1.5 mW | 0.58 A/ns | 6.60 W | 3.09 W | **7.2–8.3 A (shoot-through)** |

Table 3: deleting D12 (single R15 = 10 Ω) vs the split network.

| | Current (`d0`) | Split 10 Ω (`f10`) | **R15 = 10 Ω, no D12 (`d10`)** |
|---|---|---|---|
| M1 die peak | 100 V | 68 V | **68 V** |
| LX pins | 67 V | 62 V | 62 V |
| M7 die peak | 60.4 V | 51.7 V | 51.7 V |
| TVS average | 315 mW | 38.1 mW | **37.9 mW** |
| M1 total loss | 4.09 W | 4.82 W | 4.82 W |
| M1 avalanche-region power | 0.36 W | 0 | 0 |

Checks on `d10`:
- Inductor current when M1 is commanded on: ≤ 0.30 A (M1 Vds ≈ 9 V from DCM ringing). Slow turn-on is harmless.
- M1's die Vgs while held off (> 200 ns after the off command): max **0.18 V** (threshold 1.8 V; datasheet low corner 1.0 V). No dv/dt-induced turn-on with only 10 Ω holding the gate low.

## 6. Dead time (M1 off → rail-side FET on)

Signal path: the same logic edge (`Out-` high) turns M1 off (D15 → U104 74HC14 → U19 → R15/D12) and
turns the rail FET on (74HC00 NAND → U104 inverter → U15/U10/U20 → R13/R23/R47 100 Ω with
D11/D14/D13 for fast turn-off). Medians over 123 turn-offs; times after U19's output (N026) falls
through 6 V. "ch1" = M2, "ch2/ch3" = M3/M4.

| Event | Current circuit (`d0`) | R15 = 10 Ω, no D12 (`d10`) |
|---|---|---|
| Rail FET's driver output rises | 5 ns | 5 ns |
| M1 drain starts rising (Vds > 5 V) | ~10 ns | ~23–26 ns |
| M1 drain at 90 % of the rail | 11 ns | 33–35 ns |
| **Rail FET die Vgs > 1.8 V** | **31–34 ns** | **39–41 ns** |
| M1 die Vgs < 1.8 V | 39–45 ns | 109–125 ns |
| M1 drain current < 1 A | 42–55 ns | 99–115 ns |
| **Margin: M1 Vds > 5 V → rail Vgs > 1.8 V** | **21–25 ns** (min 21.1) | **13–18 ns** (min 13.1) |
| M1 die Vgs when the rail FET reaches 1.8 V | 3.6–4.0 V | 3.9–4.2 V |
| M1 die Vgs plateau during turn-off | 4.4 V | 4.5 V |
| M1 current above inductor current (0–300 ns) | ≤ 0.85 A | ≤ 0.42 A |
| Current from Vout into rail FET drain (0–300 ns) | ≤ 0.10 A | ≤ 0.06 A |

Interpretation:
- Shoot-through needs the rail FET to turn on while M1 is still **fully on** (above its plateau). In
  both circuits M1 is already on/below its plateau (current-limited) and its drain is rising when
  the rail FET reaches threshold, and M1 never carries more than the inductor current. **No
  shoot-through.**
- The textbook "both gates below threshold" dead time is negative in both (M1's gate lingers above
  1.8 V while its current falls). That is harmless here.
- The 47 Ω run shows real shoot-through (7–8 A).
- **Margin concern with 10 Ω:** the margin drops to 13 ns minimum. A rail FET at the 1.0 V threshold
  corner (datasheet range 1.0–3.0 V) reaches threshold ~14 ns sooner (RC estimate with 100 Ω +
  2.38 Ω internal and 1.606 nF: ~30 ns to 1.8 V, ~16 ns to 1.0 V, from a ~10.7 V bootstrap), and the
  model notes that the real part holds current ~2.4 ns longer than the model.
- **Fix:** R13/R23/R47 100 Ω → 150 Ω. RC estimate: rail FET reaches 1.8 V at ~45 ns (1.0 V corner
  ~24 ns), restoring about today's margin. Cost: a few ns more rail-FET body-diode conduction, ~10 mW.
  Raising these resistors is the safe direction (the context document's warning is against
  *reducing* them).

## 7. Caveats

- LEVEL=1 MOSFET core: about half the real Miller charge (Qgd 1.8 vs 3.7 nC). The real part will
  probably switch slower at the same resistor (less overshoot, less dead-time margin). Put
  footprints that accept 4.7–22 Ω for R15 and tune on the bench.
- Lead values are typical. Tab-down leads bent for the underside are longer (roughly +1 nH/mm).
- Copper inductance is the **current** layout's. The re-placed board should be lower; re-run with its
  extracted loop inductance.
- The avalanche model is a hard clamp (no energy/thermal limit). Treat any avalanche as a failure.
- D19 is modelled directly on the M1 pins with zero trace inductance (best case).
- LX at the pins reaches 59–62 V in every case, right at D19's 60 V breakdown (5KP54A).

## 8. Pending simulations (not done yet)

1. **R15 = 10 Ω (no D12) + R13/R23/R47 = 150 Ω**, nominal and with the rail FETs (and M1) at the
   VTO = 1.0 V corner. Pass: margin (M1 Vds > 5 V → rail Vgs > 1.8 V) ≥ ~20 ns and reverse current
   into rail drains ≤ ~2 A.
2. Re-run tables 2/3 with the re-placed board's loop inductance.
3. Sink FETs with lead inductance: why the simulation stalls (numerical, or a real parasitic
   oscillation of the MCP6241 + FET linear sinks; gate resistors are R22/R50/R56 = 100 Ω).
4. Apply to `BOOST.asc` (both copies): R15 = 10 Ω, delete D12, R13/R23/R47 = 150 Ω, M8–M10 Value
   `HYG180N10_NOLEADS`, fix the servo `.ic` with net labels, copy REV 5 `HYG180N10.lib` to the
   `Documents/LTspice` copy, and optionally the Arduino M1-inhibit diode.

## 9. Reproducing

1. `LTspice.exe -netlist BOOST.asc` (generates `BOOST.net`; the 08-31 export is
   `sim/netlists/BOOST_asc_2026-08-31_as_exported.net`).
2. Put the netlists from `sim/netlists/` next to the `.lib` files (with REV 5 `HYG180N10.lib`) and run
   `LTspice.exe -b <name>.net`. Don't launch two batch runs in the same second (one silently failed to
   start); stagger by ~15 s. Each 40 ms run takes 4–16 min.
3. `python measure.py <name>.raw` and `python deadtime.py d0.raw d10.raw` (NumPy required). Raw files
   are 30–120 MB and are not included.

| Netlist | M1 gate | Leads | Copper L | Extra saves |
|---|---|---|---|---|
| `base2` | current | no | no | — |
| `leads3` | current | M1–M7 | no | die Vds |
| `c0` | current | M1–M7 | yes | + M1 drain current, gate |
| `f2p2`…`f47` | split, Roff 2.2 / 4.7 / 10 / 22 / 47 Ω | M1–M7 | yes | same as c0 |
| `d0` | current | M1–M7 | yes | + driver outputs, die Vgs |
| `d10` | R15 = 10 Ω, no D12 | M1–M7 | yes | same as d0 |
