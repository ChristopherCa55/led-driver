"""Input capacitor bank current from an LTspice raw file (window 35-39 ms).

  python icap.py icap_14.raw [icap_17.raw ...]

Reports per-cap and bank RMS ripple current, how evenly the three caps share,
the cable's AC current, Vin ripple, and where the bank current's spectrum sits
(the hybrid caps' ripple rating is given at 100 kHz and derated below it).
"""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'handoff_2026-09-14', 'sim', 'scripts'))
from measure import load, window


def rms_ac(t, y):
    span = t[-1] - t[0]
    mean = np.trapezoid(y, t) / span
    return np.sqrt(np.trapezoid((y - mean) ** 2, t) / span), mean


for path in sys.argv[1:]:
    t, v = load(path)
    m = window(t)
    tt = t[m]
    I = lambda n: v["i(%s)" % n][m]
    V = lambda n: v["v(%s)" % n][m]
    print("== %s  (%d points, %.2f-%.2f ms)" % (os.path.basename(path), m.sum(), tt[0] * 1e3, tt[-1] * 1e3))
    span = tt[-1] - tt[0]
    avg = lambda y: np.trapezoid(y, tt) / span
    print("   operating point: Vout %.2f / %.2f / %.2f V; LED %.3f / %.3f / %.3f A (D16/D18/D17); IL peak %.1f A; LX max %.1f V; TVS avg %.1f mW"
          % (avg(V("vout_1")), avg(V("vout_2")), avg(V("vout_3")), avg(I("d16")), avg(I("d18")), avg(I("d17")),
             np.max(np.abs(I("l1"))), np.max(V("lx")), avg(-V("lx") * I("d19")) * 1e3))
    caps = {}
    for c in ("c40", "c69", "c85"):
        r, mean = rms_ac(tt, I(c))
        caps[c] = r
        print("   %-4s ripple %.3f A rms   (mean %.4f A)" % (c.upper(), r, mean))
    bank = I("c40") + I("c69") + I("c85")
    rb, _ = rms_ac(tt, bank)
    vals = np.array(list(caps.values()))
    print("   bank (sum of the three currents) %.3f A rms; per-cap spread %.3f-%.3f A (max/mean %.2f)"
          % (rb, vals.min(), vals.max(), vals.max() / vals.mean()))
    rl1, ml1 = rms_ac(tt, I("l1"))
    rl2, ml2 = rms_ac(tt, I("l2"))
    print("   inductor L1: mean %.2f A, AC %.2f A rms; cable L2: mean %.2f A, AC %.3f A rms" % (ml1, rl1, ml2, rl2))
    vin = V("vin")
    rv, mv = rms_ac(tt, vin)
    print("   Vin: mean %.3f V, ripple %.1f mV rms, %.0f mV p-p" % (mv, rv * 1e3, (vin.max() - vin.min()) * 1e3))
    # spectrum of the bank current on a uniform grid
    n = 2 ** 20
    tu = np.linspace(tt[0], tt[-1], n)
    bu = np.interp(tu, tt, bank)
    bu -= bu.mean()
    spec = np.abs(np.fft.rfft(bu * np.hanning(n))) ** 2
    f = np.fft.rfftfreq(n, tu[1] - tu[0])
    tot = spec[1:].sum()
    bands = [(0, 1e3), (1e3, 5e3), (5e3, 10e3), (10e3, 15e3), (15e3, 20e3), (20e3, 30e3), (30e3, 50e3), (50e3, 100e3), (100e3, 1e9)]
    print("   bank current power by band: " + ", ".join(
        "%s-%s kHz %.0f%%" % (int(a / 1e3), ("inf" if b > 1e8 else int(b / 1e3)), 100 * spec[(f >= a) & (f < b)].sum() / tot)
        for a, b in bands))
    k = np.argmax(spec[1:]) + 1
    print("   strongest component %.1f kHz" % (f[k] / 1e3))
