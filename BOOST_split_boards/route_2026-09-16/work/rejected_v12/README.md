# Rejected: v12 (first fully routed board, 2026-09-16)

DRC-clean (0 errors, 0 unconnected), netlist parity 0, layer checks passed, but the copper re-solve showed the signal
routes had cut the power pours where the current flows: Vout_1 M2->J3 LED path neck 17.7 -> 177 C (0.20 mm wide,
one via at 2.71x rating), Vin J1->R1 neck 23.6 -> 41 C (10.0 -> 3.9 mm), rsense_lo 20 -> 33 C, Vout_1 bank via 0.85x
-> 1.44x, GND returns +20-40 % resistance. Router tag 21 (`work/route_signals_r21.py` is the router as it was).
Replaced by v13, routed with the solved sheet-current map (`--jmap work/v11_jmap.npz`) so tracks do not cut copper
carrying more than 0.25 A/mm. Solver tables: `work/v11_B.json` (before) and `work/v12_B.json` (this board).
