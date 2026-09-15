"""Dead-time margin between M1 turning off and the next rail-side FET turning on,
with the threshold as a parameter (for the VTO = 1.0 V corner) and the
SIMULATION_REPORT margin definition: M1 die Vds > 5 V -> rail FET die Vgs > Vth.

  python deadtime2.py RUN.raw [--vth 1.8]
"""
import sys
import numpy as np
sys.path.insert(0, r"C:\Users\Dominick Junior\Downloads\UCSD Stuff\2025-2026\robotx\led-driver\BOOST_split_boards\handoff_2026-09-14\sim\scripts")
from measure import load, window


def crossings(t, y, level, rising):
    s = np.sign(y - level)
    idx = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0)) if rising else np.flatnonzero((s[:-1] > 0) & (s[1:] <= 0))
    y0, y1 = y[idx], y[idx + 1]
    frac = np.where(y1 != y0, (level - y0) / (y1 - y0), 0.0)
    return t[idx] + frac * (t[idx + 1] - t[idx])


def first_after(times, t0, limit=2e-6):
    k = np.searchsorted(times, t0)
    return times[k] if k < len(times) and times[k] - t0 <= limit else np.nan


def stat(vals):
    v = np.array([x for x in vals if not np.isnan(x)]) * 1e9
    return (v.min(), np.median(v), v.max(), len(v)) if len(v) else (np.nan, np.nan, np.nan, 0)


path = sys.argv[1]
vth = float(sys.argv[sys.argv.index('--vth') + 1]) if '--vth' in sys.argv else 1.8
t, v = load(path)
m = window(t)
t = t[m]
V = lambda n: v["v(%s)" % n][m]
I = lambda n: v["i(%s)" % n][m]
drv_m1 = V("n026")
vgs_m1 = V("m1_gi") - V("m1_si")
vds_m1 = V("m1_di") - V("m1_si")
rails = {"ch1 M2": (V("n021") - V("m2_source"), V("m2_gi") - V("m2_si"), "vsense_m2"),
         "ch2 M3": (V("n035") - V("m3_source"), V("m3_gi") - V("m3_si"), "vsense_m3"),
         "ch3 M4": (V("n040") - V("m4_source"), V("m4_gi") - V("m4_si"), "vsense_m4")}
off_cmd = crossings(t, drv_m1, 6.0, rising=False)
vds5 = crossings(t, vds_m1, 5.0, rising=True)
m1_vth = crossings(t, vgs_m1, vth, rising=False)
rail_cmd = {k: crossings(t, r[0], 5.0, rising=True) for k, r in rails.items()}
rail_vth = {k: crossings(t, r[1], vth, rising=True) for k, r in rails.items()}
rows = []
for t0 in off_cmd:
    c = {k: first_after(rail_cmd[k], t0) for k in rails}
    c = {k: x for k, x in c.items() if not np.isnan(x)}
    if not c:
        continue
    ch = min(c, key=c.get)
    rows.append(dict(ch=ch, t0=t0, cmd=c[ch] - t0, vds5=first_after(vds5, t0) - t0,
                     m1vth=first_after(m1_vth, t0) - t0, railvth=first_after(rail_vth[ch], t0) - t0))
print("== %s  (threshold %.1f V, %d M1 turn-offs in 35-39 ms)" % (path, vth, len(rows)))
allm = []
for ch in rails:
    rs = [r for r in rows if r["ch"] == ch]
    if not rs:
        continue
    marg = [r["railvth"] - r["vds5"] for r in rs]
    allm += marg
    print(" %s: %d events" % (ch, len(rs)))
    for label, key in (("rail driver output rises", "cmd"), ("M1 die Vds > 5 V", "vds5"),
                       ("rail FET die Vgs > Vth", "railvth"), ("M1 die Vgs < Vth", "m1vth")):
        a, b, c_, n = stat([r[key] for r in rs])
        print("   %-34s min %6.1f  median %6.1f  max %6.1f ns" % (label, a, b, c_))
    a, b, c_, n = stat(marg)
    print("   %-34s min %6.1f  median %6.1f  max %6.1f ns" % ("MARGIN (Vds>5 V -> rail Vgs>Vth)", a, b, c_))
a, b, c_, n = stat(allm)
print(" all channels: margin min %.1f ns, median %.1f ns (pass >= ~20 ns)" % (a, b))
for ch, r in rails.items():
    i = I(r[2])
    print(" reverse current into %s drain: peak %.2f A (pass <= ~2 A)" % (ch.split()[1], np.max(i)))
vdie = V("m1_di") - V("m1_si")
print(" M1 die Vds peak %.1f V; LX pin peak %.1f V; TVS avg %.1f mW"
      % (np.max(vdie), np.max(V("lx")), np.trapezoid(-V("lx") * I("d19"), t) / (t[-1] - t[0]) * 1e3))
