"""Per-event dead time between M1 turning off and the next rail-side FET
(M2/M3/M4) turning on, from runs that save driver outputs and die nodes."""
import sys
import numpy as np
from measure import load, window

VTH = 1.8  # model VTO

def crossings(t, y, level, rising):
    s = np.sign(y - level)
    if rising:
        idx = np.flatnonzero((s[:-1] < 0) & (s[1:] >= 0))
    else:
        idx = np.flatnonzero((s[:-1] > 0) & (s[1:] <= 0))
    # linear interpolation
    y0, y1 = y[idx], y[idx + 1]
    frac = np.where(y1 != y0, (level - y0) / (y1 - y0), 0.0)
    return t[idx] + frac * (t[idx + 1] - t[idx])

def first_after(times, t0, limit):
    k = np.searchsorted(times, t0)
    if k < len(times) and times[k] - t0 <= limit:
        return times[k]
    return np.nan

def analyse(path):
    t, v = load(path)
    m = window(t, 35e-3, 39e-3)
    t = t[m]
    V = lambda n: v[f"v({n})"][m]
    I = lambda n: v[f"i({n})"][m]
    drv_m1 = V("n026")
    vgs_m1 = V("m1_gi") - V("m1_si")
    vds_m1 = V("m1_di") - V("m1_si")
    id_m1 = I("vsense_m1")
    rails = {
        "ch1 M2": (V("n021") - V("m2_source"), V("m2_gi") - V("m2_si"), np.mean(V("vout_1"))),
        "ch2 M3": (V("n035") - V("m3_source"), V("m3_gi") - V("m3_si"), np.mean(V("vout_2"))),
        "ch3 M4": (V("n040") - V("m4_source"), V("m4_gi") - V("m4_si"), np.mean(V("vout_3"))),
    }
    off_cmd = crossings(t, drv_m1, 6.0, rising=False)
    on_cmd = crossings(t, drv_m1, 6.0, rising=True)
    m1_vth_down = crossings(t, vgs_m1, VTH, rising=False)
    i0 = crossings(t, id_m1, 1.0, rising=False)
    rail_cmd = {k: crossings(t, r[0], 5.0, rising=True) for k, r in rails.items()}
    rail_vth = {k: crossings(t, r[1], VTH, rising=True) for k, r in rails.items()}

    rows = []
    for t0 in off_cmd:
        # which rail driver rises next
        cands = {k: first_after(rail_cmd[k], t0, 2e-6) for k in rails}
        cands = {k: x for k, x in cands.items() if not np.isnan(x)}
        if not cands:
            continue
        ch = min(cands, key=cands.get)
        vout = rails[ch][2]
        lx_up = crossings(t, vds_m1, 0.9 * vout, rising=True)
        row = dict(
            ch=ch,
            cmd=cands[ch] - t0,
            m1_vth=first_after(m1_vth_down, t0, 2e-6),
            rail_vth=first_after(rail_vth[ch], t0, 2e-6),
            lx_up=first_after(lx_up, t0, 2e-6),
            i0=first_after(i0, t0, 2e-6),
            t0=t0,
        )
        rows.append(row)

    def stat(name, vals):
        vals = np.array([x for x in vals if not np.isnan(x)]) * 1e9
        if len(vals) == 0:
            return f"  {name:58s} n/a"
        return f"  {name:58s} min {vals.min():7.1f}  median {np.median(vals):7.1f}  max {vals.max():7.1f} ns  (n={len(vals)})"

    print(f"== {path}: {len(rows)} M1 turn-offs in 35-39 ms")
    for ch in rails:
        rs = [r for r in rows if r["ch"] == ch]
        if not rs:
            continue
        print(f" {ch}: {len(rs)} events")
        print(stat("driver outputs: M1 off cmd -> rail on cmd", [r["cmd"] for r in rs]))
        print(stat("M1 off cmd -> M1 die Vgs < 1.8 V", [r["m1_vth"] - r["t0"] for r in rs]))
        print(stat("M1 off cmd -> M1 drain V > 90% of rail", [r["lx_up"] - r["t0"] for r in rs]))
        print(stat("M1 off cmd -> M1 drain current < 1 A", [r["i0"] - r["t0"] for r in rs]))
        print(stat("M1 off cmd -> rail FET die Vgs > 1.8 V", [r["rail_vth"] - r["t0"] for r in rs]))
        print(stat("DEAD TIME: M1 Vgs<1.8 V -> rail Vgs>1.8 V", [r["rail_vth"] - r["m1_vth"] for r in rs]))
        print(stat("margin: M1 drain at rail voltage -> rail Vgs>1.8 V", [r["rail_vth"] - r["lx_up"] for r in rs]))
        print(stat("margin: M1 current <1 A -> rail Vgs>1.8 V", [r["rail_vth"] - r["i0"] for r in rs]))

    # spurious M1 gate rise while it is commanded off (dv/dt-induced turn-on check)
    worst = 0.0
    for t0 in off_cmd:
        k = np.searchsorted(on_cmd, t0)
        if k >= len(on_cmd):
            break
        a, b = t0 + 200e-9, on_cmd[k] - 1e-9
        sel = (t > a) & (t < b)
        if sel.any():
            worst = max(worst, vgs_m1[sel].max())
    print(f"  M1 die Vgs max while held off (>200 ns after off cmd): {worst:.2f} V  (VTO 1.8 V; the model file's low corner is 1.0 V)")
    # current at M1 turn-on
    il = I("l1")
    at_on = [np.interp(x, t, il) for x in on_cmd]
    vds_on = [np.interp(x, t, vds_m1) for x in on_cmd]
    print(f"  inductor current at M1 on cmd: max {max(np.abs(at_on)):.2f} A; M1 Vds at on cmd: median {np.median(vds_on):.1f} V")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyse(p)
