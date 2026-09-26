# M1 turn-off re-check with the routed loop inductances (2026-09-24)

The optional re-check from the open list: M1 with R15 = 10 ohm, the rail FETs with R13/R23/R47 = 220 ohm (as built),
and the commutation loops set from the routed power board instead of the pre-layout estimates.

## What changed from the 2026-09-14 runs (s220 / s220lv)

| Loop element | s220 (pre-layout) | routed (this run) | pessimistic (this run) |
|---|---|---|---|
| Lcu_ch1, M1 to Vout_1 caps | 4.85 nH | 1.73 nH (0.73 routed + 1.0 via barrels) | 3.46 nH (2x) |
| Lcu_ch2 | 12.74 nH | 2.17 nH (1.17 + 1.0) | 4.34 nH (2x) |
| Lcu_ch3 | 7.91 nH | 3.04 nH (2.04 + 1.0) | 6.08 nH (2x) |
| HYG180N10 package LD / LS / LG | 4.5 / 7.5 / 7.5 nH | same | 5.5 / 8.5 / 7.5 nH |

Everything else is the s220 netlist: the same models, drive, loads, and a 35-39 ms measurement window with about 123 M1
turn-offs. The runs still carry rev5's R1 = 2 mOhm with INA241A3. Rev6's 1 mOhm with INA241A4 gives the same 0.1 V/A
and the same 1.1 MHz bandwidth (TI SBOSA30D), so the current loop is unchanged.

Threshold corners: nominal VTO 1.8 V, and the 1.0 V low-threshold corner (`_lv`). The analysis is
`../replace_2026-09-14/tools/sim/deadtime2.py`, and the full output is in `deadtime_results.txt`. The netlists' own
`.meas` lines report FAIL in LTspice 26 batch mode, so every number here comes from the raw files.

## Results

| Run | M1 die Vds peak | LX pin peak | TVS D19 average | TVS energy per turn-off | Dead-time margin min / median | Reverse current into rail drains |
|---|---|---|---|---|---|---|
| s220 (2026-09-14, nominal) | 68.0 V | | 38.3 mW | 1.25 uJ | 40.8 / 46.3 ns | 1.34 A |
| **routed, nominal** | **67.6 V** | 60.8 V | 10.0 mW | 0.33 uJ | **41.0 / 46.4 ns** | 1.06 A |
| pessimistic, nominal | 67.9 V | 61.3 V | 22.3 mW | 0.73 uJ | 39.9 / 45.4 ns | 1.20 A |
| s220lv (2026-09-14, 1.0 V corner) | 66.0 V | | 13.1 mW | 0.43 uJ | 18.3 / 24.4 ns | |
| **routed, 1.0 V corner** | **64.7 V** | 59.4 V | 1.7 mW | 0.06 uJ | **18.6 / 24.0 ns** | 1.06 A |
| pessimistic, 1.0 V corner | 66.3 V | 60.5 V | 4.1 mW | 0.13 uJ | 18.6 / 24.1 ns | 1.05 A |

Energy per turn-off is the average power divided by the turn-off rate: 123 turn-offs in 4 ms is 30.75 kHz.

**Reading it:**
- **Die peak: at or under the 68 V from before**, in all four runs, and 32 V under the 100 V BVDSS. The layout's
  shorter loops remove about 0.4 V at nominal, and the pessimistic case (twice the routed copper, package plus 1 nH)
  still lands at 67.9 V.
- **The TVS does very little.** It averages 1.7-22 mW, or 0.06-0.73 uJ per turn-off, against a 5 kW (10/1000 us)
  part. That is lower than the 38 mW in s220, because less loop energy is left to clamp.
- **Dead-time margins are unchanged.** They are set by the gate drive, not by the loop:
  - nominal: 41.0 ns minimum, against the ~20 ns pass line;
  - 1.0 V corner: 18.6 ns minimum on channel 1 (M2), against 18.3 ns before. Channels 2 and 3 are 24.0-24.6 ns.
- Channel 1 at the low-threshold corner stays **1.4 ns under the ~20 ns guideline**, as it was in s220lv. That is the
  pre-existing corner result, and the routed layout neither causes nor fixes it.
- The reverse current into the rail drains peaks at 1.20 A worst case, under the ~2 A pass line.

**Verdict:** the routed layout does not change the turn-off picture. No change to R15, the TVS or the gate resistors
is indicated.

## Files

| File | What |
|---|---|
| `m1_routed_nom.net`, `m1_routed_lv.net`, `m1_pess_nom.net`, `m1_pess_lv.net` | netlists (cp1252; LTspice 26 `-b`) |
| `*.log` | LTspice logs (about 8-12 min per run, four in parallel) |
| `*.raw` | waveforms, about 120 MB each |
| `run_all.sh`, `run_all.out` | runner (staggered 15 s) and timings |
| `deadtime_results.txt` | full `deadtime2.py` output |
| `*.lib` | model libraries copied next to the netlists |
