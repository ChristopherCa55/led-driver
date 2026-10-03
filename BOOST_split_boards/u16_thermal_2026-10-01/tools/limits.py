# Junction temperature and the largest continuous 12 V load for U16, from the modelled thermal resistances.
#   P(I) = (Vin - Vout) * I + Vin * Ig(I)
#   Vout = 11.64 V (UTC LM2940-12 minimum: the largest drop), Vin = 18 V (your margin case) or 16.8 V (4S full)
#   Ig(I) = 20 mA + 40 mA * I / 1 A: TI LM2940-N maximum over temperature (20 mA at 5 mA load, 60 mA at 1 A),
#           straight line between. UTC publishes only 15 mA max at 5 mA, 25 C.
#   Tj = T_air + background + theta_JA * P;  theta_JA = tab-to-air (model) + R_jt
#   R_jt = 15 K/W (UTC theta_JC for SOT-223; TI's RthetaJB is 8.1)
# Usage: python tools/limits.py
import sys

T_AIR = float(__import__("os").environ.get("T_AIR", "75"))       # your top in-case air figure (replace_notes, 2026-09-17: "55-75 C in-case air")
R_JT = {'SOT-223': 15.0, 'TO-263': 0.8}   # SOT-223: UTC theta_JC; TO-263: TI RthetaJC(bot) (the TI LM2940S now on the board)

# tab-to-air thermal resistances (K/W) and background rises at the tab (K), filled in from the model runs
CASES = [
    # name, package, h, tab-to-air, background
]


def P(I, vin):
    return (vin - 11.64) * I + vin * (0.020 + 0.040 * I)


def tj(theta, bg, I, vin):
    return T_AIR + bg + theta * P(I, vin)


def imax(theta, bg, vin, limit):
    lo, hi = 0.0, 1.0
    if tj(theta, bg, 0, vin) > limit:
        return 0.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if tj(theta, bg, mid, vin) <= limit else (lo, mid)
    return lo


def table(cases, loads=(0.05, 0.12)):
    print('| Case | h (W/m2K) | theta_JA (K/W) | background (K) | ' +
          ' | '.join('Tj at %.0f mA, 18 V' % (I * 1e3) for I in loads) +
          ' | max I for Tj 125 C (18 V / 16.8 V) | max I for Tj 150 C (18 V / 16.8 V) |')
    print('|---' * (6 + len(loads)) + '|')
    for name, pkg, h, tab, bg in cases:
        th = tab + R_JT[pkg]
        cols = ['%.0f C' % tj(th, bg, I, 18.0) for I in loads]
        i125 = [imax(th, bg, v, 125) for v in (18.0, 16.8)]
        i150 = [imax(th, bg, v, 150) for v in (18.0, 16.8)]
        print('| %s | %.0f | %.1f | %.1f | %s | %s | %s |' % (
            name, h, th, bg, ' | '.join(cols),
            ' / '.join('%.0f mA' % (i * 1e3) for i in i125), ' / '.join('%.0f mA' % (i * 1e3) for i in i150)))


if __name__ == '__main__':
    import json
    table(json.load(open(sys.argv[1])))
