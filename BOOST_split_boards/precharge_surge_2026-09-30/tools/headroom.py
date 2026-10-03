"""Surge headroom of the S2MW pre-charge diodes against the data-sheet IFSM (50 A, 8.3 ms half sine).

Method: junction temperature rise by superposition, dT(t) = sum P(t - k dt) * [Z((k+1) dt) - Z(k dt)], with the die's
transient thermal impedance taken as a power law Z(t) = k * t^n (k cancels in every ratio).
  - P = VF(I) * I with the same diode model the simulation used (LTspice 1N4007 scaled to a 2 A die).
  - n is calibrated on the only short-pulse figure available for this die class: Wild Goose S2MF (2 A, 1000 V glass
    passivated, same 50 A / 8.3 ms rating) is also rated 100 A for a 1 ms half sine. n is chosen so both data-sheet
    pulses give the same peak dT. n = 0.5 (pure 1-D diffusion) and n = 0.25 are shown as bounds.
Headroom is given two ways:
  - dT ratio: peak dT of the rated pulse / peak dT of the simulated pulse;
  - current factor: how far the simulated current waveform could be scaled up before it heats the die as much as the
    rated pulse.

usage: python headroom.py CASE ...   (CASE = LTspice raw name in this folder, diode current I(DPRE3))
"""
import os, sys
import numpy as np
sys.path.insert(0, r'C:/Users/bubba/AppData/Local/Temp/claude/C--Users-bubba-OneDrive-Documents-led-driver/'
                   r'14c8a43e-d3bb-4a1c-bb90-a19d4b04633d/scratchpad/tools')
from analyze_edges import read_raw, Sig

HERE = os.path.dirname(os.path.abspath(__file__))
VT = 0.025852 * 300.15 / 300.0     # kT/q at 27 C
IS, N, RS = 14e-9, 1.8, 0.017      # the S2MW model used in the simulations


def vf(i, rs=RS):
    i = np.maximum(i, 0.0)
    return N * VT * np.log1p(i / IS) + i * rs


def peak_dt(i, dt, n, rs=RS):
    p = vf(i, rs) * i
    k = np.arange(len(p) + 1) * dt
    h = np.diff(k ** n)
    return np.convolve(p, h)[:len(p)].max()


def half_sine(ipk, dur, dt):
    t = np.arange(0, dur * 1.5, dt)
    return np.where(t < dur, ipk * np.sin(np.pi * t / dur), 0.0)


def sim_wave(case, dt):
    mm, idx = read_raw(os.path.join(HERE, case + '.raw'))
    s = Sig(mm, idx)
    t = s.t
    ok = np.flatnonzero(np.diff(t) > 0)
    m = ok[-1] + 1
    t = t[:m].astype(np.float64)
    i = s('i(dpre3)')[:m].astype(np.float64)
    tg = np.arange(t[0], t[-1], dt)
    return np.interp(tg, t, i)


DT = 1e-6
RATED = half_sine(50.0, 8.333e-3, DT)
WG1MS = half_sine(100.0, 1e-3, DT)

# calibrate n: equal peak dT for the two data-sheet pulses (Wild Goose S2MF: 50 A 8.3 ms and 100 A 1 ms)
lo, hi = 0.05, 0.95
for _ in range(40):
    mid = (lo + hi) / 2
    if peak_dt(WG1MS, DT, mid) > peak_dt(RATED, DT, mid):
        lo = mid           # 1 ms pulse too hot: Z must grow faster with time (larger n) to make the long pulse hotter
    else:
        hi = mid
NFIT = (lo + hi) / 2
print('calibrated n = %.3f (Wild Goose S2MF: 100 A / 1 ms half sine heats the die as much as 50 A / 8.3 ms)' % NFIT)
print('rated pulse: 50 A, 8.33 ms half sine, I2t %.1f A2s, VF at 50 A %.2f V (model)' % (
    np.sum(RATED ** 2) * DT, vf(np.array(50.0))))
print()
for case in sys.argv[1:]:
    i = sim_wave(case, DT)
    pk = i.max()
    i2t = np.sum(i ** 2) * DT
    w10 = np.sum(i > 0.1 * pk) * DT
    w50 = np.sum(i > 0.5 * pk) * DT
    print('%s: peak %.1f A, I2t %.3f A2s, width above 50 %% of peak %.0f us, above 10 %% %.0f us; I2t ratio %.1fx' % (
        case, pk, i2t, w50 * 1e6, w10 * 1e6, np.sum(RATED ** 2) * DT / i2t))
    for n in (NFIT, 0.5, 0.25):
        r = peak_dt(RATED, DT, n) / peak_dt(i, DT, n)
        lo, hi = 1.0, 20.0
        target = peak_dt(RATED, DT, n)
        for _ in range(40):
            mid = (lo + hi) / 2
            if peak_dt(i * mid, DT, n) < target:
                lo = mid
            else:
                hi = mid
        print('   n = %.3f%s: dT ratio %.1fx; the current could be %.2fx larger (peak %.0f A) before matching the rated '
              'pulse' % (n, ' (fit)' if n == NFIT else '       ', r, lo, lo * pk))
