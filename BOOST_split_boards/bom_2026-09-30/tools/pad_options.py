"""FET thermal-pad options at the fixed 5.50 mm board height (compressed pad 0.93 mm). Updated 2026-09-25 (second
pass) for the pads that can actually be bought:
- Parker 61-06-0909-G579 (0.060 in = 1.524 mm): the 0.050 in sheet is not sold at Digi-Key; the user read $128.75.
- McMaster-Carr 1272N32 (0.060 in, 3 W/m-K, 40 Shore 00, no compression curve, no dielectric rating): $26.91.
- t-Global TG-AD30 (3.0 W/m-K, 20 Shore 00, dielectric >= 5 kV/mm): datasheet with a compression curve; price not read.

For each: strain at 0.93 mm, pressure and force per FET (10 x 15.6 mm tab), worst case (FET body +/-0.10, board bow
0.10, pad thickness +/-10 %), thermal resistance and M1's junction temperature against the 2026-09-16 budget (about
78 C at 25 C water, of which the pad was taken as 20.6 K at 6 W).

  python tools/pad_options.py > cost/pad_options.txt
"""
GAP = 0.93
TAB_CM2 = 1.56
P_M1 = 6.0
BUDGET_TJ = 78.0
IN2 = 6.4516
G579_DT_BUDGET = 6.0 * 0.83 / (TAB_CM2 / IN2)      # 20.6 K, the 2026-09-16 estimate
PSI = 6.895
BODY, BOW, TOL = 0.10, 0.10, 0.10


def interp(x, pts):
    if x <= pts[0][0]:
        return pts[0][1] * x / pts[0][0] if pts[0][0] else pts[0][1]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def bulk(t_mm, k):
    return (t_mm / 10.0) / (k / 100.0)       # K-cm2/W


def N(psi):
    return psi * PSI * TAB_CM2 * 0.1          # kPa x cm2 -> N


def report(name, t, curve, contact, k, note, scale=1.0):
    """curve: [(deflection %, psi)]; contact: K-cm2/W added to the bulk at 0.93 mm; scale: stiffness vs the curve."""
    s = 100 * (1 - GAP / t)
    lo = 100 * (1 - (GAP + BODY + BOW) / (t * (1 - TOL)))
    hi = 100 * (1 - (GAP - BODY - BOW) / (t * (1 + TOL)))
    p, p_hi = interp(s, curve), interp(hi, curve)
    z = bulk(GAP, k) + contact
    r = z / TAB_CM2
    dt = P_M1 * r
    print('\n' + name)
    print('   %.3f mm -> 0.93 mm: %.1f %% nominal, worst case %.1f .. %.1f %%' % (t, s, lo, hi))
    if p is not None:
        print('   nominal %.1f psi -> %.1f N per FET (x10 FETs = %.0f N)%s' % (p * scale, N(p * scale), 10 * N(p * scale),
              '' if scale == 1.0 else '  [scaled x%.2f from the G579 curve by durometer]' % scale))
    print('   worst-case high end: %s' % ('%.0f psi, %.0f N per FET' % (p_hi * scale, N(p_hi * scale)) if p_hi is not None
                                         else 'beyond the published curve'))
    print('   %.2f K-cm2/W -> %.2f K/W -> %.1f K at %.0f W -> M1 Tj about %.0f C at 25 C water (budget %.0f C)'
          % (z, r, dt, P_M1, BUDGET_TJ - G579_DT_BUDGET + dt, BUDGET_TJ))
    print('   ' + note)
    return dict(name=name, strain=s, lo=lo, hi=hi, n_per_fet=N(p * scale) if p else None, tj=BUDGET_TJ - G579_DT_BUDGET + dt)


# Parker THERM-A-GAP G579 (catalogue 579 column): 22/33/55/68 % at 5/10/25/50 psi on a 0.125 in sample; 30 Shore 00;
# 3.0 W/m-K; 4.5 C-cm2/W at 10 psi on the 0.040 in sample -> contact share at most 2.23 K-cm2/W; 200 Vac/mil
# (7.9 kV/mm); typical deflection range 5-40 %; thickness tolerance +/-10 % at <= 2.5 mm.
G579 = [(0, 0), (22, 5), (33, 10), (55, 25), (68, 50)]
C_G579 = max(4.5 - bulk(1.016, 3.0), 4.5 - bulk(0.68, 3.0))
report('Parker G579 0.050 in (1.27 mm)  [the approved design; not sold at Digi-Key]', 1.27, G579, C_G579, 3.0,
       'Reference: 27 % at the 5.50 mm stack.')
report('Parker 61-06-0909-G579, 0.060 in (1.524 mm), $128.75 for 9 x 9 in', 1.524, G579, C_G579, 3.0,
       'Same stack. 39 % nominal is at the top of Parker\'s "typical 5-40 %"; the worst case goes to 56 %.')

# Durometer scaling (ASTM D2240 type 00: spring force 0.203 + 0.0444 H N, indentation 2.5 mm x (100 - H) / 100):
# E ~ F / d^1.5, so 40 Shore 00 is about 1.62x as stiff as 30 Shore 00, and 20 Shore 00 about 0.58x. Crude (+/-50 %).
def dur(h):
    return (0.203 + 0.0444 * h) / (2.5 * (100 - h) / 100) ** 1.5
k40 = dur(40) / dur(30)
report('McMaster-Carr 1272N32, 0.060 in (1.524 mm), 3 W/m-K, 40 Shore 00, $26.91 for 4 x 4 in', 1.524, G579, C_G579, 3.0,
       'No compression curve published: force estimated from its 40 Shore 00 against G579\'s 30 (x%.2f, +/-50 %%). '
       'Contact resistance assumed equal to G579\'s. No dielectric strength published.' % k40, scale=k40)

# t-Global TG-AD30 (datasheet 2024-05): 3.0 W/m-K (ISO 22007-2), 20 Shore 00, >= 5 kV/mm (ASTM D149), -50..150 C;
# 1.0 mm: 31/65/73 % at 10/30/50 psi and 0.41/0.26/0.20 C-in2/W; 3.0 mm: 54/76/82 %. A 1.5 mm pad is read between them
# (a quarter of the way from 1.0 to 3.0 mm). Contact share from the 1.0 mm point at ~12 psi: 0.395 C-in2/W total minus
# the bulk of 0.66 mm -> about 0.35 K-cm2/W.
t10 = [(0, 0), (31, 10), (65, 30), (73, 50)]
t30 = [(0, 0), (54, 10), (76, 30), (82, 50)]
t15 = [(0, 0)] + [(a[0] + 0.25 * (b[0] - a[0]), a[1]) for a, b in zip(t10[1:], t30[1:])]
c_ad30 = 0.395 * IN2 - bulk(0.66, 3.0)
report('t-Global TG-AD30, 1.5 mm, 3.0 W/m-K, 20 Shore 00, >= 5 kV/mm  [price not read]', 1.5, t15, c_ad30, 3.0,
       'Softest of the three, lowest impedance; curve read between the published 1.0 and 3.0 mm curves.')

print('\nRejected on data: t-Global TG-A3500F (27 % needs 50 psi at 1.0 mm), Wurth WE-TGF 3 W/m-K (100 x 100 mm only in '
      '1.0 mm = 7 % or 2.0 mm = 54 %; Wurth recommends 10-30 %).')
