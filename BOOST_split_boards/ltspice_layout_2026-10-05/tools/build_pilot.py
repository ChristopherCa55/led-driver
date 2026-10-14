"""Pilot re-layout of BOOST.asc: PWR + ISNS + the channel-1 row (CREG1, REF1, EA1).

    python build_pilot.py [--only PWR,ISNS] [--out ../work/BOOST.asc]

Reads the frozen original from the handoff folder, removes the pilot parts from the old drawing (dead wires deleted,
dangling stubs trimmed, cut nets keep their names), draws the pilot blocks above the old drawing, checks the pin
partition against the original, and writes the result.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from layout_lib import *
import channel

A = sys.argv[1:]
ONLY = A[A.index('--only') + 1].split(',') if '--only' in A else ['PWR', 'ISNS', 'CREG1', 'REF1', 'EA1']
OUT = A[A.index('--out') + 1] if '--out' in A else os.path.join(HERE, '..', 'work', 'BOOST.asc')

OWN = block_members()
TEMP_LABELS = []          # (net, block, why) for the report


def temp(d, x, y, net, io, block, why):
    d.F(x, y, net, io)
    TEMP_LABELS.append((net, block, why))


# ===================================================================================================== PWR
def pwr(d, X0, YS):
    YP, YF = YS - 160, YS + 128
    YG, YE = YF + 160, YF + 224
    # ---- simulated battery and cable (dashed SIM frame)
    xB = X0 + 256
    d.P('SIM_BATTERY', xB, YS + 80, 'R0', {'name': ('Left', 48, 40), 'value': ('Left', 48, 72)})
    d.W((xB, YS + 96), (xB, YS))
    d.W((xB, YS), (xB - 48, YS))
    d.F(xB - 48, YS, 'Vbattery')
    xR = xB + 224
    d.P('SIM_CABLE_RESISTANCE', xR, YS - 16, 'R90', {'name': ('Bottom', -56, -8), 'value': ('Top', -56, 40)})
    d.W((xB, YS), (xR - 96, YS))
    xC = xR + 320
    d.P('SIM_CABLE_INDUCTANCE', xC, YS - 16, 'R90', {'name': ('Bottom', -56, -8), 'value': ('Top', -56, 40)})
    d.W((xR - 16, YS), (xC - 96, YS))
    d.frame(X0 + 48, YS - 80, xC + 112, YS + 224)
    d.T(xB + 64, YS + 208, 'simulation only - not on the PCB')
    # ---- Vin node, pre-charge riser, input caps
    xV = xC + 176
    d.W((xC - 16, YS), (xV, YS))
    d.W((xV, YS), (xV, YP))
    d.W((xV, YP), (xV - 48, YP))
    d.F(xV - 48, YP, 'Vin')
    xs = [xV + 96, xV + 224, xV + 352]
    for n, px in zip(['C69', 'C40', 'C85'], xs):
        d.P(n, px - 16, YS, 'R0', {'name': ('Left', 40, 16), 'value': ('Left', 40, 48)})
        d.W((px, YS + 64), (px, YG))
    x1 = xV + 512
    d.W((xV, YS), (xs[0], YS), (xs[1], YS), (xs[2], YS), (x1, YS))
    # ---- R1 (Kelvin shunt), L1
    d.P('R1', x1, YS, 'R0', {'name': ('Top', 40, 24), 'value': ('Top', 40, 52), 'spiceline': ('Top', 40, 80, 1)})
    xl = x1 + 432
    d.W((x1 + 80, YS), (x1 + 208, YS), (xl - 96, YS))
    d.F(x1 + 208, YS, 'rsense_lo')
    d.P('L1', xl, YS - 16, 'R90', {'name': ('Bottom', -56, -8), 'value': ('Top', -56, 40)})
    # ---- LX bus: M1, D19, R14, three switch columns
    xD1 = x1 + 576
    xd, xr = xD1 + 208, xD1 + 496
    cols = [xD1 + 704 + 1088 * k for k in range(3)]
    d.W((xl - 16, YS), (x1 + 464, YS), (xD1, YS), (xd, YS), (xr, YS), *[(xk - 64, YS) for xk in cols])
    d.F(x1 + 464, YS, 'LX')
    d.P('M1', xD1 - 48, YS + 48, 'R0', {'name': ('Left', 64, 32), 'value': ('Left', 64, 64)})
    d.W((xD1, YS), (xD1, YS + 48))
    d.W((xD1, YS + 144), (xD1, YG))
    d.W((xD1 - 48, YS + 128), (xD1 - 96, YS + 128), (xD1 - 96, YE), (xD1 - 128, YE))
    temp(d, xD1 - 128, YE, 'GATE_M1', 'In', 'PWR', 'gate drive from U19 (GATEDRV, not yet redrawn)')
    d.P('D19', xd + 16, YS + 112, 'R180', {'name': ('Left', 16, -48), 'value': ('Left', 16, -16)})
    d.W((xd, YS), (xd, YS + 48))
    d.W((xd, YS + 112), (xd, YG))
    d.P('R14', xr - 16, YS + 32, 'R0', {'name': ('Left', 40, 40), 'value': ('Left', 40, 72)})
    d.W((xr, YS), (xr, YS + 48))
    d.W((xr, YS + 128), (xr, YG))
    colparts = [('M7', 'M2', 'D28', ['C86', 'C70', 'C88', 'C1', 'C72'], 'Vout_1', 'GATE_M7', 'GATE_M2', 'm2_source'),
                ('M6', 'M3', 'D29', ['C87', 'C71', 'C78', 'C73', 'C3'], 'Vout_2', 'GATE_M6', 'GATE_M3', 'm3_source'),
                ('M5', 'M4', 'D30', ['C74', 'C75', 'C77', 'C4', 'C76'], 'Vout_3', 'GATE_M5', 'GATE_M4', 'm4_source')]
    for xk, (ma, mb, dd, caps, vout, ga, gb, src) in zip(cols, colparts):
        d.W((xk - 64, YS), (xk - 64, YF), (xk, YF))
        d.P(ma, xk, YF + 48, 'R270', {'name': ('Bottom', 48, -88), 'value': ('Bottom', 48, -64)})
        d.P(mb, xk + 256, YF + 48, 'M270', {'name': ('Bottom', -48, -88), 'value': ('Bottom', -48, -64)})
        d.W((xk + 96, YF), (xk + 128, YF), (xk + 160, YF))
        d.W((xk + 128, YF), (xk + 128, YE + 48), (xk + 160, YE + 48))
        temp(d, xk + 160, YE + 48, src, 'BiDir', 'PWR', 'source tie to the channel driver (GATEDRV, not yet redrawn)')
        d.W((xk + 80, YF + 48), (xk + 80, YE), (xk + 48, YE))
        temp(d, xk + 48, YE, ga, 'In', 'PWR', 'gate drive (GATEDRV, not yet redrawn)')
        d.W((xk + 176, YF + 48), (xk + 176, YE), (xk + 208, YE))
        temp(d, xk + 208, YE, gb, 'In', 'PWR', 'gate drive (GATEDRV, not yet redrawn)')
        px = [xk + 336 + 112 * i for i in range(5)]
        d.W((xk + 256, YF), *[(p, YF) for p in px], (xk + 880, YF))
        for c, p in zip(caps, px):
            d.P(c, p - 16, YF, 'R0', {'name': ('Left', 40, 16), 'value': ('Left', 40, 48)})
            d.W((p, YF + 64), (p, YG))
        d.P(dd, xk + 864, YF - 64, 'R0', {'name': ('Left', 40, 16), 'value': ('Left', 40, 48)})
        d.W((xk + 880, YF - 64), (xk + 880, YP))
        d.W((xk + 880, YF), (xk + 880, YE), (xk + 848, YE))
        d.F(xk + 848, YE, vout, 'Out')
    d.W((xV, YP), *[(xk + 880, YP) for xk in cols])
    # ---- the one drawn ground return
    d.W((xB, YS + 176), (xB, YG))
    d.W((xB, YG), (cols[2] + 784, YG))
    d.G((xB, YG))
    # ---- frame, title, note
    right = cols[2] + 1008
    d.frame(X0, YP - 96, right, YE + 64)
    d.T(X0 + 16, YP - 72, '[PWR] Power path: battery, input caps, R1, L1, M1, output switches (power board)')
    d.a.texts.append('TEXT %d %d Left 2 %s' % (cols[1] + 400, YP - 32, NOTE_D28))
    return {'x1': x1, 'YP': YP, 'YS': YS, 'top': YP - 96, 'bottom': YE + 64, 'right': right, 'cols': cols}


# ===================================================================================================== ISNS
def isns(d, x1, YS, pwr_top):
    """U25 unrotated (its internal pin text is only legible at R0). The Kelvin pair rises from R1, spreads apart and
    enters IN+/IN- from the left; REF1's ground sits between the two sense wires."""
    xu = x1 + 256
    yu = pwr_top - 48 - 144
    ytop = yu - 240
    d.P('U25', xu, yu, 'R0', {'name': ('Left', 80, 40), 'value': ('Left', 80, 72)})
    d.W((x1 + 16, YS - 32), (x1 + 16, YS - 64), (x1 - 16, YS - 64), (x1 - 48, YS - 64), (x1 - 48, yu - 32),
        (xu - 64, yu - 32))
    d.F(x1 - 16, YS - 64, 'ISNS_P')
    d.W((x1 + 64, YS - 32), (x1 + 64, YS - 64), (x1 + 96, YS - 64), (x1 + 128, YS - 64), (x1 + 128, yu + 32),
        (xu - 64, yu + 32))
    d.F(x1 + 96, YS - 64, 'ISNS_N')
    d.W((xu - 64, yu), (x1 + 32, yu), (x1 + 32, yu + 48))      # REF1 to ground, between the sense wires
    d.G((x1 + 32, yu + 48))
    # supply with its bypass cap
    d.W((xu, yu - 64), (xu, yu - 112), (xu + 48, yu - 112), (xu + 96, yu - 112))
    d.F(xu + 48, yu - 112, 'analog_5V')
    d.P('C20', xu + 80, yu - 112, 'R0', {'name': ('Left', 48, 32), 'value': ('Left', 48, 64)})
    d.G((xu + 96, yu - 48))
    # GND and REF2 tied, one ground
    d.W((xu, yu + 64), (xu, yu + 96), (xu + 16, yu + 96), (xu + 32, yu + 96), (xu + 32, yu + 64))
    d.G((xu + 16, yu + 96))
    # output
    d.W((xu + 64, yu), (xu + 224, yu), (xu + 224, ytop + 64), (xu + 288, ytop + 64))
    d.F(xu + 288, ytop + 64, 'Current', 'Out')
    d.frame(x1 - 112, ytop, xu + 432, yu + 144)
    d.T(x1 - 96, ytop + 24, '[ISNS] Input current sense (power board)')


# ===================================================================================================== main
def main():
    orig = Asc(ORIG)
    a = Asc(ORIG)
    a.dir = os.path.dirname(os.path.abspath(OUT))
    pilot = {p for p, b in OWN.items() if b in ONLY}
    pool, trimmed = strip_old(a, pilot)
    for s in pool.values():                                     # the three approved renames
        n = s.name
        if n in RENAME:
            s.attrs = [(k, RENAME[n] if k == 'InstName' else v) for k, v in s.attrs]
    pool = {s.name: s for s in pool.values()}
    # the D28-D30 note moves to the diodes (verbatim)
    global NOTE_D28
    note = [t for t in a.texts if ';D28-D30: pre-charge diodes' in t]
    assert len(note) == 1
    NOTE_D28 = note[0].split(' ', 5)[5]
    a.texts = [t for t in a.texts if t not in note]
    d = Draw(a, pool)
    info = None
    if 'PWR' in ONLY:
        info = pwr(d, -2880, -4032)
    if 'ISNS' in ONLY:
        isns(d, info['x1'], info['YS'], info['top'])
    if 'CREG1' in ONLY:
        c = channel.CH[1]
        Y = info['bottom'] + 704
        tf = lambda x, y, net, io, block, why: temp(d, x, y, net, io, block, why)
        X1 = -2880
        cr = channel.creg(d, X1, Y, c, tf)
        X2 = X1 + channel.CREG_W + 96
        rf = channel.ref(d, X2, Y, c, cr, tf, extras=True)
        X3 = X2 + channel.REF_W + 96
        channel.ea(d, X3, Y, c, rf, tf)
    if pool:
        raise SystemExit('parts not placed: %s' % sorted(pool))
    added = name_cut_groups(a, partition(orig, RENAME), trimmed, RENAME)
    probs, newnames = compare(orig, a)
    print('old-area flags added:', added)
    print('new names on auto nets:', newnames)
    print('ELECTRICAL SELF-CHECK:', 'OK' if not probs else '%d problems' % len(probs))
    for p in probs[:40]:
        print('  ', p)
    a.write(OUT)
    print('wrote', OUT, len(a.syms), 'symbols', len(a.wires), 'wires', len(a.flags), 'flags')
    print('temporary labels:', len(TEMP_LABELS))


if __name__ == '__main__':
    main()
