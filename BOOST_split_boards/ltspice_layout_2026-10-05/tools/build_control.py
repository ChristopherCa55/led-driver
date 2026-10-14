"""Redraw the control circuitry (the user's request, 2026-10-07): it sits where the user moved it in v5 (above channel 3,
right of the power section); everything in that area is redrawn by function, left to right:

    LOW-ERROR TIMEOUT -> SEQUENCER / ERROR SELECT (U18 -> U28) -> COMPARATORS (U4, U2, U5) -> M1 LATCH (U101)
    CHANNEL ENABLE x3 (identical rows) to the right of the latch, M1 INHIBIT below the latch.

    python build_control.py            work/BOOST_revised_v5.asc -> work/BOOST_revised_v6.asc (refuses to overwrite)
    python build_control.py --draft    -> work/_draft_control.asc (a scratch file of mine, overwritten each run)

Wired inside each section; named nets that run between sections (VerrGT0, Out-, OUT_n_ENA, M1_ON, 0err_hi,
low_error_timeout) use labels. Bypass caps follow the board (bypass_map.json): U14 C12, U4 C98, U2 C28, U5 C24,
U21 C29 + C53, U28 C96, each at its IC's supply pin. C96 and C98 leave the user's logic-cap row; C22 (U101) and C52 (U18),
whose ICs have no supply pins in LTspice, take their two spots in that row. C21 (U1's analog_5V cap) goes beside C55
at U1's output.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, HANDOFF
from layout_lib import Draw, compare
from board_caps import Ghost, place_like

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised_v5.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v6.asc')
DRAFT = os.path.join(WORK, '_draft_control.asc')
ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')
REGION = (2300, -9000, 8400, -5200)          # the user's control area in v5 (78 parts, nothing crosses its edge)
PIN2 = {'res': (16, 96), 'cap': (0, 64), 'diode': (0, 64)}


def inside(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


class Ctl(Draw):
    """Draw plus the few shapes this sheet needs, all placed by their PIN positions"""

    def two(self, name, pa, pb, side=None, texts=None):
        """2-pin part (res/cap/diode) with its FIRST pin (A, or + for a diode) at pa and the second at pb.
        side: vertical parts 'r'/'l' (texts right/left); horizontal 'ab' (name above, value below), 'a', 'b'."""
        s = self.pool[name]
        a1, a2 = PIN2[s.sym]
        (xa, ya), (xb, yb) = pa, pb
        if xa == xb:
            assert abs(yb - ya) == a2 - a1, (name, pa, pb)
            rot, x, y = ('R0', xa - 16, ya - a1) if yb > ya else ('R180', xa + 16, ya + a1)
            my = (ya + yb) // 2
            side = side or 'r'
            if side == 'r':
                t = {'name': ('Left', xa + 20, my - 16), 'value': ('Left', xa + 20, my + 16)}
            else:
                t = {'name': ('Right', xa - 20, my - 16), 'value': ('Right', xa - 20, my + 16)}
        else:
            assert ya == yb and abs(xb - xa) == a2 - a1, (name, pa, pb)
            rot, x, y = ('R270', xa - a1, ya + 16) if xb > xa else ('R90', xa + a1, ya - 16)
            mx = (xa + xb) // 2
            side = side or 'ab'
            t = {'ab': {'name': ('Bottom', mx, ya - 20), 'value': ('Top', mx, ya + 20)},
                 'a': {'name': ('Bottom', mx, ya - 52), 'value': ('Bottom', mx, ya - 20)},
                 'b': {'name': ('Top', mx, ya + 20), 'value': ('Top', mx, ya + 52)}}[side]
        sym = self.Pa(name, x, y, rot, texts or t)
        got = [(px, py) for _, px, py in self.a.pins(sym)]
        assert got == [pa, pb], (name, got, pa, pb)
        return sym

    def opamp(self, name, X, Y, texts):
        self.Pa(name, X, Y, 'R0', texts)
        return {'in-': (X - 32, Y + 48), 'in+': (X - 32, Y + 80), 'v+': (X, Y + 32), 'v-': (X, Y + 96),
                'out': (X + 32, Y + 64)}

    def gate(self, name, X, Y, name_at=None):
        """NAND drawn with LTspice's 'and' (inputs b, d; output _Q). Returns pin positions."""
        nx, ny = name_at or (X - 8, Y + 20)
        self.Pa(name, X, Y, 'R0', {'name': ('Left', nx, ny), 'value': None})
        return {'b': (X - 32, Y + 48), 'd': (X - 32, Y + 80), 'q': (X + 32, Y + 80)}

    def inv(self, name, X, Y, name_at=None):
        nx, ny = name_at or (X + 4, Y + 32)
        self.Pa(name, X, Y, 'R0', {'name': ('Left', nx, ny), 'value': None})
        self.G((X, Y + 80))                                  # com
        return {'in': (X, Y + 64), 'q': (X + 64, Y + 64)}

    def supply_cap(self, cap, pin, rail='5V', dx=96, flip=False):
        """the user's op-amp bypass drawing: supply pin up 96, across dx to a cap going down to ground; rail label at
        the middle of the top wire"""
        x, y = pin
        top = y - 96
        self.W(pin, (x, top), (x + dx // 2, top), (x + dx, top))
        self.F(x + dx // 2, top, rail)
        if flip:
            self.two(cap, (x + dx, top + 64), (x + dx, top), 'r')
        else:
            self.two(cap, (x + dx, top), (x + dx, top + 64), 'r')
        self.G((x + dx, top + 64))
        return (x + dx, top)

    def title(self, x, y, text):
        self.T(x, y, text, size=3)


def build(a, pool):
    d = Ctl(a, pool)
    W, F, G = d.W, d.F, d.G

    # ================================================================ LOW-ERROR TIMEOUT (U14)  -> U18 clock
    d.title(2624, -8560, 'LOW-ERROR TIMEOUT')
    u14 = d.opamp('U14', 3200, -8352, {'name': ('Left', 3224, -8344), 'value': ('Left', 3224, -8312)})
    d.supply_cap('C12', u14['v+'])
    G(u14['v-'])
    # In+ : R69 from 5V, R68 to ground, R67 hysteresis from the output (drawn under the op-amp)
    n19 = (3120, -8208)
    d.two('R69', n19, (3040, -8208), 'a')
    W((3040, -8208), (3008, -8208))
    F(3008, -8208, '5V')
    d.two('R68', n19, (3120, -8128), 'l')
    G((3120, -8128))
    W(u14['out'], (3264, -8288), (3264, -8208))
    d.two('R67', (3264, -8208), (3184, -8208), 'b')
    W((3184, -8208), (3152, -8208), n19)
    W(u14['in+'], (3152, -8272), (3152, -8208))
    # In- : R66 from 0err_hi charges C14; Q1 (PNP) empties it when 0err_hi is low (through D3, R65)
    n1 = (2944, -8304)
    W(u14['in-'], (3040, -8304), n1)
    d.two('R66', (3040, -8384), (3040, -8304), 'r')
    d.two('C14', n1, (2944, -8240), 'r')
    G((2944, -8240))
    d.Pa('Q1', 2784, -8208, 'M180', {'name': ('Left', 2864, -8272), 'value': ('Left', 2864, -8240)})
    W(n1, (2848, -8304))                                     # Q1 emitter
    G((2848, -8208))                                         # Q1 collector
    base = (2752, -8256)
    W((2784, -8256), base)
    d.two('R65', base, (2672, -8256), 'a')
    d.two('D3', (2672, -8256), (2672, -8320), 'l')
    W((2672, -8320), (2672, -8384), (2800, -8384), (3040, -8384))
    F(2800, -8384, '0err_hi')
    # D4 / C15 / R71: the output pulls Q1's base through C15 when it falls
    W(base, (2752, -8224))
    d.two('D4', (2752, -8224), (2752, -8160), 'l')
    n2 = (2752, -8112)
    W((2752, -8160), n2)
    d.two('C15', n2, (2752, -8048), 'l')
    G((2752, -8048))
    d.two('R71', n2, (2832, -8112), 'a')
    W((2832, -8112), (2880, -8112), (2880, -8016), (3072, -8016), (3264, -8016), (3264, -8208))
    F(3072, -8016, 'low_error_timeout')
    # output -> U18 clock
    W((3264, -8288), (3472, -8288))

    # ================================================================ SEQUENCER (U18) + ERROR SELECT (U28)
    d.title(3456, -8560, 'SEQUENCER / ERROR SELECT')
    d.Pa('U18', 3584, -8416, 'R0', {'name': ('Center', 3584, -8400), 'value': ('Center', 3584, -7872)})
    W((3472, -8352), (3408, -8352))
    F(3408, -8352, '4')                                      # MR <- Q3 (count 0, 1, 2, then reset)
    W((3472, -8320), (3408, -8320))
    F(3408, -8320, 'Out-')                                   # clock enable
    ena = ['OUT_1_ENA', 'OUT_2_ENA', 'OUT_3_ENA']
    for k in range(3):                                       # Q0..Q2 -> U28 A, B, C
        y = -8224 + 32 * k
        W((3696, y), (3840, y), (3984, y))
        F(3840, y, ena[k])
    W((3696, -8128), (3728, -8128))
    F(3728, -8128, '4')
    for k, n in enumerate(['5', '6', '7', '8', '9', '10']):
        y = -8096 + 32 * k
        W((3696, y), (3728, y))
        F(3728, y, n)
    # U28 mirrored: Verr1/Verr2 + select on the left, Verr3 + V_err on the right
    d.Pa('U28', 4320, -8432, 'M0', {'name': ('Center', 4112, -8448), 'value': None})   # the symbol prints 74HC4051
    W((3984, -8384), (3952, -8384), (3952, -8480), (3904, -8480), (3856, -8480))
    F(3904, -8480, '5V')
    d.two('C96', (3856, -8480), (3856, -8416), 'l')
    G((3856, -8416))
    for n, y in (('Verr2', -8352), ('Verr1', -8320)):
        W((3984, y), (3888, y))
        F(3888, y, n, 'In')
    W((3984, -8288), (3952, -8288), (3952, -8272), (3952, -8256), (3984, -8256))     # IO0, IO3 unused
    W((3952, -8272), (3920, -8272))
    G((3920, -8272))
    W((4240, -8384), (4336, -8384))
    F(4336, -8384, 'Verr3', 'In')
    W((4240, -8352), (4272, -8352))                          # IO6 unused
    G((4272, -8352))
    for y in (-8288, -8256, -8224, -8192, -8160):            # IO7, IO5, INH, VEE, VSS
        W((4240, y), (4272, y))
    W((4272, -8288), (4272, -8256), (4272, -8224), (4272, -8192), (4272, -8160), (4272, -8128))
    G((4272, -8128))

    # ================================================================ COMPARATORS
    d.title(4560, -8560, 'M1 ON/OFF LATCH')
    # V_err from U28 to U4 (In-) and down to U5 (In-)
    W((4240, -8320), (4560, -8320), (4688, -8320), (5008, -8320))
    F(4560, -8320, 'V_err')
    W((4688, -8320), (4688, -7648), (5008, -7648))

    def comparator(u, cap, X, Y, rtop, rbot, rhyst, sig=None):
        p = d.opamp(u, X, Y, {'name': ('Left', X + 24, Y + 8), 'value': ('Left', X + 84, Y + 112)})
        d.supply_cap(cap, p['v+'])
        G(p['v-'])
        if rtop:                                             # divider node; In+ joins the hysteresis return
            node = (X - 80, Y + 144)
            d.two(rtop, node, (X - 160, Y + 144), 'a')
            W((X - 160, Y + 144), (X - 192, Y + 144))
            F(X - 192, Y + 144, '5V')
            d.two(rbot, node, (X - 80, Y + 224), 'l')
            G((X - 80, Y + 224))
            W(p['out'], (X + 64, Y + 64), (X + 64, Y + 144))
            d.two(rhyst, (X + 64, Y + 144), (X - 16, Y + 144), 'b')
            W((X - 16, Y + 144), (X - 48, Y + 144), node)
            W(p['in+'], (X - 48, Y + 80), (X - 48, Y + 144))
        if sig:
            W(p[sig[0]], (X - 224, p[sig[0]][1]))
            F(X - 224, p[sig[0]][1], sig[1], 'In')
        return p

    u4 = comparator('U4', 'C98', 5040, -8368, 'R20', 'R19', 'R18')
    u2 = comparator('U2', 'C28', 5040, -8016, 'R17', 'R16', 'R11', ('in-', 'Current'))
    u5 = comparator('U5', 'C24', 5040, -7696, None, None, None, ('in+', 'Current'))
    # U4 -> U104E -> VerrGT0
    W((5104, -8304), (5168, -8304), (5232, -8304))
    F(5168, -8304, '0err_hi')
    d.inv('U104E', 5232, -8368, (5236, -8352))
    W((5296, -8304), (5376, -8304), (5472, -8304))
    F(5376, -8304, 'VerrGT0')

    # ================================================================ M1 LATCH (U101)
    ga = d.gate('U101A', 5504, -8352)
    W((5104, -7952), (5216, -7952), (5312, -7952), (5312, -8272), ga['d'])   # 0A_hi
    F(5216, -7952, '0A_hi')
    d.two('R4', (5616, -8272), ga['q'], 'b')
    W((5616, -8272), (5648, -8272), (5712, -8272), (5744, -8272))
    d.two('D6', (5648, -8272), (5648, -8336), 'l')
    W((5648, -8336), (5648, -8368), (5680, -8368))
    F(5680, -8368, 'low_error_timeout')
    F(5712, -8272, 'set-')
    gc = d.gate('U101C', 5776, -8320)
    gd = d.gate('U101D', 5776, -8160)
    gb = d.gate('U101B', 5504, -8160)
    W((5072, -7632), (5216, -7632), (5344, -7632), (5344, -8112), gb['b'])   # Reset_raw
    F(5216, -7632, 'Reset_raw')
    W(gb['d'], (5376, -8080), (5376, -7984), (5424, -7984))
    F(5424, -7984, 'M1_ON')
    W(gb['q'], (5616, -8080), gd['d'])
    F(5616, -8080, 'RESET-')
    # cross-coupled: Out (C) -> D.b, Out- (D) -> C.d, one crossing
    W(gc['q'], (5840, -8240), (5840, -8176), (5776, -8176), (5712, -8176), (5712, -8112), gd['b'])
    F(5776, -8176, 'Out')
    W(gd['q'], (5872, -8080), (5872, -8208), (5696, -8208), (5696, -8240), gc['d'])
    W((5872, -8080), (5936, -8080))
    F(5936, -8080, 'Out-')

    # ================================================================ CHANNEL ENABLE x3
    d.title(6000, -8752, 'CHANNEL ENABLE')
    rows = [('U102B', 'R80', 'C17', 'R81', 'D20', 'U105A', 'U102A', 'U104B', 'ena_out_1', 'M2_ON'),
            ('U102C', 'R78', 'C9', 'R79', 'D7', 'U104F', 'U102D', 'U104C', 'ena_out_2', 'out_2_on'),
            ('U103A', 'R63', 'C8', 'R64', 'D5', 'U105B', 'U103B', 'U104D', 'ena_out_3', 'out_3_on')]
    for k, (n1, ra, c, rb, dd, i1, n2, i2, ena_o, on_o) in enumerate(rows):
        Y = -8656 + 320 * k
        g1 = d.gate(n1, 6176, Y)
        W(g1['b'], (6048, Y + 48))
        F(6048, Y + 48, ena[k])
        W(g1['d'], (6048, Y + 80))
        F(6048, Y + 80, 'VerrGT0')
        P = (6272, Y + 80)
        W(g1['q'], P)
        d.two(ra, (6352, Y + 80), P, 'a')                   # A at the cap node
        W((6352, Y + 80), (6384, Y + 80), (6416, Y + 80))
        d.two(c, (6384, Y + 144), (6384, Y + 80), texts={'name': ('Right', 6364, Y + 124),
                                                           'value': ('Right', 6364, Y + 152)})   # A on ground
        G((6384, Y + 144))
        Q = (6496, Y + 80)
        d.two(rb, (6416, Y + 80), Q, 'a')
        W(P, (6272, Y - 48), (6352, Y - 48))                # D: fast path around the RC
        d.two(dd, (6352, Y - 48), (6416, Y - 48), 'a')
        W((6416, Y - 48), (6496, Y - 48), Q)
        v1 = d.inv(i1, 6528, Y + 16)
        W(Q, v1['in'])
        J = (6640, Y + 80)
        W(v1['q'], J)
        W(J, (6640, Y + 144), (6672, Y + 144))
        F(6672, Y + 144, ena_o, 'Out')
        g2 = d.gate(n2, 6832, Y)
        if n2 == 'U103B':                                    # this gate has its inputs the other way round
            W(J, (6640, Y + 48), g2['b'])
            W(g2['d'], (6752, Y + 80))
            F(6752, Y + 80, 'Out-')
        else:
            W(J, g2['d'])
            W(g2['b'], (6736, Y + 48))
            F(6736, Y + 48, 'Out-')
        v2 = d.inv(i2, 6928, Y + 16)
        W(g2['q'], v2['in'])
        W(v2['q'], (7056, Y + 80))
        F(7056, Y + 80, on_o, 'Out')

    # ================================================================ M1 INHIBIT
    d.title(5200, -7472, 'M1 INHIBIT')
    p = d.opamp('U21', 5632, -7376, {'name': ('Left', 5656, -7368), 'value': ('Left', 5716, -7264)})
    top = d.supply_cap('C29', p['v+'])
    W(top, (5856, -7440))
    d.two('C53', (5856, -7376), (5856, -7440), 'r')          # netlisted ground-first
    G((5856, -7376))
    G(p['v-'])
    node = (5552, -7232)                                     # In+: R82 from 5V, R85 to ground, R86 hysteresis
    d.two('R82', (5472, -7232), node, 'a')
    W((5472, -7232), (5440, -7232))
    F(5440, -7232, '5V')
    d.two('R85', node, (5552, -7152), 'l')
    G((5552, -7152))
    W(p['out'], (5696, -7312), (5696, -7232))
    d.two('R86', (5696, -7232), (5616, -7232), 'b')
    W((5616, -7232), (5584, -7232), node)
    W(p['in+'], (5584, -7296), (5584, -7232))
    n21 = (5392, -7328)                                      # In-: 12 V divider
    W(p['in-'], n21)
    d.two('R84', (5392, -7408), n21, 'l')
    W((5392, -7408), (5392, -7440), (5440, -7440))
    F(5440, -7440, '12V')
    d.two('R83', n21, (5392, -7248), 'l')
    G((5392, -7248))
    bus = 6112
    W((5696, -7312), (5888, -7312))
    d.two('D24', (5888, -7312), (5952, -7312), 'b')
    W((5952, -7312), (bus, -7312))
    W((5824, -7120), (5920, -7120))
    F(5824, -7120, '0err_hi')
    d.two('D1', (5920, -7120), (5984, -7120), 'a')
    W((5984, -7120), (bus, -7120))
    on = (5792, -7008)                                       # Out-: D15 fast, R51-C19-R26 slow
    W((5760, -7008), on, (5920, -7008))
    F(5760, -7008, 'Out-')
    d.two('D15', (5920, -7008), (5984, -7008), 'a')
    W((5984, -7008), (bus, -7008))
    W(on, (5792, -6928))
    d.two('R51', (5792, -6928), (5872, -6928), 'a')
    W((5872, -6928), (5920, -6928), (5952, -6928))
    W((5920, -6928), (5920, -6896))
    d.two('C19', (5920, -6896), (5920, -6832), 'l')
    G((5920, -6832))
    d.two('R26', (6032, -6928), (5952, -6928), 'b')
    W((6032, -6928), (bus, -6928))
    ard = (5984, -6752)                                      # Arduino inhibit pin (simulation source)
    d.two('D27', ard, (6048, -6752), 'a')
    W((6048, -6752), (bus, -6752))
    W((5664, -6752), (5760, -6752), (5872, -6752), ard)
    F(5872, -6752, 'ARD_M1_INHIBIT')
    d.two('R105', (5664, -6752), (5664, -6672), 'l')
    G((5664, -6672))
    d.Pa('SIM_ARD_INH', 5760, -6768, 'R0', {'name': ('Left', 5784, -6720), 'value': ('Left', 5784, -6688)})
    G((5760, -6672))
    d.T(5784, -6656, 'simulation only - not on the PCB')
    W((bus, -7312), (bus, -7120), (bus, -7056), (bus, -7008), (bus, -6928), (bus, -6752))
    W((bus, -7056), (6192, -7056), (6272, -7056))            # tapped between D1 and D15 (no 4-way junction)
    F(6192, -7056, 'M1_INHIBIT')
    v = d.inv('U104A', 6272, -7120)
    W(v['q'], (6400, -7056))
    F(6400, -7056, 'M1_ON', 'Out')
    return d


def caps_outside(a, pool):
    """C96/C98 left the user's logic-cap row for their ICs; C22 (U101) and C52 (U18) take their two spots; C21 goes
    beside C55 at U1's output"""
    by = a.by()
    for out_, in_ in (('C96', 'C22'), ('C98', 'C52')):
        s = by[out_]
        a.syms.remove(s)
        pool[out_] = s
        t = pool.pop(in_)
        place_like(a, t, Ghost(s), Ghost(s), False)
        a.syms.append(t)
    c55 = by['C55']
    pa = a.pin(c55, 'A')
    t = pool.pop('C21')
    place_like(a, t, Ghost(c55, 64, 0), Ghost(c55, 64, 0), False)
    a.syms.append(t)
    a.wires.append((pa[0], pa[1], pa[0] + 64, pa[1]))
    a.flags.append([pa[0] + 64, pa[1] + 64, '0', None])


def main():
    draft = '--draft' in sys.argv
    a = Asc(SRC)
    pool = {s.name: s for s in a.syms if inside((s.x, s.y), REGION)}
    assert len(pool) == 78, len(pool)
    a.syms = [s for s in a.syms if s.name not in pool]
    a.wires = [w for w in a.wires if not (inside(w[:2], REGION) and inside(w[2:], REGION))]
    assert not any(inside(w[:2], REGION) or inside(w[2:], REGION) for w in a.wires)
    a.flags = [f for f in a.flags if not inside(f[:2], REGION)]
    assert not any(inside((int(t.split()[1]), int(t.split()[2])), REGION) for t in a.texts)
    caps_outside(a, pool)
    build(a, pool)
    if pool:
        raise SystemExit('unplaced: %s' % sorted(pool))
    orig = Asc(ORIG)
    orig.syms = [s for s in orig.syms if s.name != 'R14']
    probs, newnames = compare(orig, a)
    for p in probs:
        print('PROBLEM', p)
    if probs and not draft:
        raise SystemExit('electrical self-check failed; nothing written')
    if draft:
        a.write(DRAFT, overwrite=True)
        print('draft written:', DRAFT, '(%d problems)' % len(probs))
    else:
        a.write(OUT)
        print('electrical self-check OK; wrote', OUT)


if __name__ == '__main__':
    main()
