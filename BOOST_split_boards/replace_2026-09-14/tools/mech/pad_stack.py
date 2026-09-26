"""FET pad compression, standoff height and stack budget (round 4).

Pad data, Parker Chomerics THERM-A-GAP catalogue pp. 18-21 (579 column):
  % deflection 22 / 33 / 55 / 68 at 5 / 10 / 25 / 50 psi (ASTM C165 MOD, 0.125 in "G" sample, 0.50 in probe,
  0.025 in/min); typical deflection range approximately 5-40 %; thickness tolerance +/-10 % at <= 2.5 mm;
  3 W/m-K; 0.7 C-in2/W at 10 psi, 0.040 in, "G" version only; 200 Vac/mil; -55 to 200 C; UL 94 V-0.
Gap Pad 1500 (Henkel TDS Oct 2020, PDS_GP_1500_0711): E 310 kPa; 1.62 / 1.50 / 1.33 C-in2/W at 10 / 20 / 30 %;
  no pressure-deflection curve, no deflection limit, no thickness tolerance published.
"""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
A = 4.57                                   # HYG180N10 overall thickness (tolerance not stated in its drawing)
BODY = 0.10                                # user's allowance across the ten FETs
FLAT = json.load(open(os.path.join(HERE, 'fetfix.json')))     # FET -> mm to nearest fixing
BOW = 0.0075                               # IPC-6012 bow/twist limit for SMT boards
TAB_MM2 = 10.0 * 15.6
CURVE = [(0, 0), (22, 5), (33, 10), (55, 25), (68, 50)]        # (% deflection, psi), 579


def flat(f):
    c = FLAT[f]
    return c * c / (2 * 86.0 / (8 * BOW))


def psi(strain):
    s = max(strain, 0.0)
    for (s0, p0), (s1, p1) in zip(CURVE, CURVE[1:]):
        if s <= s1:
            return p0 + (p1 - p0) * (s - s0) / (s1 - s0)
    return CURVE[-1][1]


def strain(gap, t):
    return 100 * (1 - gap / t)


def study(name, t_nom, t_tol, board):
    g0 = board - A
    print('\n%s: pad %.3f mm, board underside %.2f, nominal gap %.3f, nominal strain %.1f %%'
          % (name, t_nom, board, g0, strain(g0, t_nom)))
    lo_all, hi_all = 99, -99
    for f in sorted(FLAT, key=lambda k: -FLAT[k]):
        fl = flat(f)
        # worst case: thin pad + thick body + bow toward the floor gives most strain, and the reverse
        hi = strain(g0 - BODY - fl, t_nom * (1 + t_tol))            # thick pad, small gap
        lo = strain(g0 + BODY + fl, t_nom * (1 - t_tol))            # thin pad, large gap
        # RSS of the three gap terms expressed as strain
        d_body = 100 * BODY / t_nom
        d_flat = 100 * fl / t_nom
        d_pad = 100 * t_tol * (g0 / t_nom)
        r = math.sqrt(d_body ** 2 + d_flat ** 2 + d_pad ** 2)
        s0 = strain(g0, t_nom)
        lo_all, hi_all = min(lo_all, lo), max(hi_all, hi)
        if f in ('M3', 'M1'):
            print('   %-3s bow %.3f: worst case %5.1f .. %5.1f %%   RSS %5.1f .. %5.1f %%   (%.1f .. %.1f psi on the 0.125 in curve)'
                  % (f, fl, lo, hi, s0 - r, s0 + r, psi(s0 - r), psi(s0 + r)))
    print('   all ten FETs, worst case %.1f .. %.1f %%' % (lo_all, hi_all))


study('A  THERM-A-GAP G579 0.040 in, 0.37 mm shim', 1.016, 0.10, 5.37)
study('B  THERM-A-GAP G579 0.050 in, one 0.5 mm washer', 1.270, 0.10, 5.50)
study('C  THERM-A-GAP G579 0.020 in, no shim', 0.508, 0.10, 5.00)

p = psi(26.8)
print('\nB nominal: %.1f psi = %.0f kPa -> %.1f N per FET on %.0f mm2 (0.125 in test sample; a 1.27 mm pad is stiffer)'
      % (p, p * 6.895, p * 6.895e3 * TAB_MM2 * 1e-6, TAB_MM2))
area_in2 = TAB_MM2 / 645.16
for label, z in (('G579 0.040 in at 10 psi (datasheet)', 0.70),
                 ('G579 0.050 in, estimate: 0.70 + 0.25 mm / 3 W/m-K', 0.70 + 0.254e-3 / 3.0 * 1550.0),
                 ('Gap Pad 1500 0.040 in at 20 % (datasheet)', 1.50)):
    # M1 about 6 W warm (user, 2026-09-16: the LTspice model has no temperature dependence; 4.85 W was cold)
    print('   %-52s %.2f C-in2/W -> %.1f K/W -> %.0f K at M1 6 W' % (label, z, z / area_in2, 6.0 * z / area_in2))

print('\nStack B, floor upward (mm):')
board = 5.50
rows = [('Essentra HTSN-M3-5-3 nylon M/M, body', 5.00, 5.00),
        ('M3 nylon washer 0.5', 0.50, 5.50),
        ('Power PCB', 1.60, 7.10),
        ('Essentra HNSM3-20-5.5-1 nylon F/F', 20.00, 27.10),
        ('3 x M3 nylon washer 0.5', 1.50, 28.60),
        ('Control PCB', 1.60, 30.20),
        ('Tallest card part, SOIC', 1.75, 31.95)]
for n, h, top in rows:
    print('   %-40s %6.2f   top %6.2f' % (n, h, top))
gap = 20.0 + 1.5
print('   card gap %.2f: TSW post 5.84 inserted %.2f (ESQ spec 3.68-6.35)' % (gap, 5.84 - (gap - 21.21)))
print('   lid margin %.2f' % (33.0 - rows[-1][2]))
print('   220 uF can 16.8 -> top %.2f, %.2f under the card' % (board + 1.6 + 16.8, board + 1.6 + gap - (board + 1.6 + 16.8)))
print('   L1 19.0 max -> top %.2f' % (board + 1.6 + 19.0))
print('   ESQ-115-44 tail 4.57 -> %.2f above the floor' % (board + 1.6 - 4.57))
print('   D19 SMC 3.20 max on the bottom -> %.2f to the floor' % (board - 3.20))
print('   stud engagement: board joint %.1f mm into a 10 mm female; card screw M3x8 %.1f mm into 10 mm'
      % (6.0 - 0.5 - 1.6, 8.0 - 1.6 - 1.5))
print('   tab screw M2.5 x 12 pan: head on board top at %.2f -> %.2f mm into the floor' % (board + 1.6, 12 - (board + 1.6)))
