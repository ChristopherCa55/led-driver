"""Compute the switch-node / TVS measurements from an uncompressed LTspice raw
file (time as float64, other vectors float32). Window 35-39 ms absolute."""
import sys
import numpy as np

def load(path):
    b = open(path, "rb").read()
    marker = "Binary:\n".encode("utf-16-le")
    i = b.find(marker)
    h = b[:i].decode("utf-16-le")
    offset = float(h.split("Offset:")[1].split()[0])
    names = [l.split("\t")[2] for l in h.split("\nVariables:")[1].splitlines() if l.count("\t") >= 3]
    nv = len(names)
    dt = np.dtype([("time", "<f8")] + [(f"v{k}", "<f4") for k in range(1, nv)])
    data = np.frombuffer(b[i + len(marker):], dtype=dt)
    t = np.abs(data["time"]) + offset
    vec = {names[k].lower(): data[f"v{k}"].astype(np.float64) for k in range(1, nv)}
    return t, vec

def window(t, lo=35e-3, hi=39e-3):
    return (t >= lo) & (t <= hi)

def avg(t, y, m):
    return np.trapezoid(y[m], t[m]) / (t[m][-1] - t[m][0])

def integ(t, y, m):
    return np.trapezoid(y[m], t[m])

def run(path):
    t, v = load(path)
    m = window(t)
    V = lambda n: v[f"v({n})"]
    I = lambda n: v[f"i({n})"]
    r = {}
    r["points in window"] = int(m.sum())
    r["IL_pk (A)"] = np.max(np.abs(I("l1")[m]))
    r["Verr_max (V)"] = np.max(V("v_err")[m])
    for k in (1, 2, 3):
        r[f"Vout_{k} avg (V)"] = avg(t, V(f"vout_{k}"), m)
    r["Iled1/2/3 avg (A)"] = tuple(round(avg(t, I(d), m), 4) for d in ("d16", "d18", "d17"))
    r["VLX_max pin (V)"] = np.max(V("lx")[m])
    r["VLX_min pin (V)"] = np.min(V("lx")[m])
    ptvs = -V("lx") * I("d19")
    r["TVS avg power (mW)"] = avg(t, ptvs, m) * 1e3
    r["TVS energy in window (mJ)"] = integ(t, ptvs, m) * 1e3
    r["TVS max conduction power (W)"] = np.max(ptvs[m])
    r["TVS peak current, clamp direction (A)"] = -np.min(I("d19")[m])
    pins = {"M2": ("vout_1", "m2_source"), "M3": ("vout_2", "m3_source"), "M4": ("vout_3", "m4_source"),
            "M7": ("lx", "m2_source"), "M6": ("lx", "m3_source"), "M5": ("lx", "m4_source")}
    for fet, (d, s) in pins.items():
        r[f"Vds pin max {fet} (V)"] = np.max((V(d) - V(s))[m])
    for fet in ("m2", "m3", "m4"):
        i = I(f"vsense_{fet}")
        r[f"reverse current into {fet.upper()} drain: peak (A)"] = np.max(i[m])
        r[f"reverse charge into {fet.upper()} drain (uC over 4 ms)"] = integ(t, np.maximum(i, 0), m) * 1e6
    if "v(m1_di)" in v:
        for fet in ("m1", "m2", "m3", "m4", "m5", "m6", "m7"):
            vd = V(f"{fet}_di") - V(f"{fet}_si")
            r[f"Vds DIE max {fet.upper()} (V)"] = np.max(vd[m])
        vls = np.abs(V("m1_si")[m])
        r["M1 source-lead voltage max (V)"] = np.max(vls)
        r["M1 peak di/dt from LS=7.5 nH (A/ns)"] = np.max(vls) / 7.5e-9 / 1e9
    if "i(vsense_m1)" in v and "v(m1_di)" in v:
        vdie = V("m1_di") - V("m1_si")
        p = vdie * I("vsense_m1")
        r["M1 average loss, die (W)"] = avg(t, p, m)
        aval = m & (vdie > 98.0)
        r["M1 energy while die >98 V (uJ per 4 ms)"] = np.trapezoid(np.where(aval, p, 0.0)[m], t[m]) * 1e6
        r["M1 avalanche-region power (W)"] = np.trapezoid(np.where(aval, p, 0.0)[m], t[m]) / (t[m][-1] - t[m][0])
        span = t[m][-1] - t[m][0]
        cond = vdie < 2.0
        r["M1 loss while Vds<2 V, conduction (W)"] = np.trapezoid(np.where(cond, p, 0.0)[m], t[m]) / span
        r["M1 loss while Vds>=2 V, switching (W)"] = np.trapezoid(np.where(~cond, p, 0.0)[m], t[m]) / span
        idr = I("vsense_m1")
        r["M1 drain current RMS (A)"] = np.sqrt(np.trapezoid(idr[m] ** 2, t[m]) / span)
        # split switching energy into turn-off (die voltage rising) and turn-on (falling)
        dv = np.gradient(vdie, t)
        sw = m & ~cond
        r["  of which Vds rising (turn-off) (W)"] = np.trapezoid(np.where(sw & (dv > 0), p, 0.0)[m], t[m]) / span
        r["  of which Vds falling (turn-on) (W)"] = np.trapezoid(np.where(sw & (dv <= 0), p, 0.0)[m], t[m]) / span
    return r

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"== {p}")
        for k, val in run(p).items():
            print(f"  {k:48s} {val:.4g}" if isinstance(val, float) else f"  {k:48s} {val}")
