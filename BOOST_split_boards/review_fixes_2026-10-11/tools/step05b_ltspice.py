"""Step 5b (LTspice): the step-5 file plus solver=alt on the existing .options line, into a NEW file.

    python step05b_ltspice.py SRC.asc OUT.asc

Why: with R106 / R107 in the netlist, LTspice's normal solver stops at t = 0.3216 ms ("Time step too small",
node m7:di; with the pull-ups listed first, m1:di at the same time). The values-only change runs normally. With
solver=alt the step-5 file runs to 30 ms and every .meas result matches the shipped file within solver noise
(work/sims/*.out). The file's own note already gives solver=alt as the fix for its dimming-run stalls.
NEEDS THE USER'S OK: it changes a directive (and runs take about 3x longer).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_2026-10-05', 'tools')))
import ascmodel as A

OLD = 'TEXT -6376 -4088 Left 2 !.options gmin=100f reltol=0.001'
NEW = 'TEXT -6376 -4088 Left 2 !.options gmin=100f reltol=0.001 solver=alt'

a = A.Asc(sys.argv[1])
i = a.texts.index(OLD)
a.texts[i] = NEW
a.write(sys.argv[2])
print('directive at (-6376, -4088): .options gmin=100f reltol=0.001 -> + solver=alt; wrote', sys.argv[2])
