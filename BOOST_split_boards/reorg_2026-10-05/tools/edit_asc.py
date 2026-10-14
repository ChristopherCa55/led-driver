"""Edit the cleanup BOOST.asc to match the KiCad rev6 schematic (2026-09-28).
usage: python edit_asc.py IN.asc OUT.asc   (symbols are looked up next to IN.asc and in newlib/)
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ascgeo import Asc

SRC, DST = sys.argv[1], sys.argv[2]
NEWLIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'newlib')
MU = '\xb5'          # the micro sign as stored in the latin-1 .asc
log = []


class Ed:
    def __init__(self, path):
        self.a = Asc(path, symdirs=[NEWLIB])
        self.L = list(self.a.lines)
        self.new_w, self.new_f, self.new_s, self.new_t = [], [], [], []

    # ---- state
    def refresh(self):
        L = [l for l in self.L if l is not None]
        body = []
        # insert new items after the last line of their kind
        lastw = max((i for i, l in enumerate(L) if l.startswith('WIRE ')), default=1)
        lastf = max((i for i, l in enumerate(L) if l.startswith('FLAG ')), default=lastw)
        firstt = min((i for i, l in enumerate(L) if l.startswith('TEXT ')), default=len(L))
        for i, l in enumerate(L):
            if i == firstt:
                body += self.new_s
            body.append(l)
            if i == lastw:
                body += ['WIRE %d %d %d %d' % w for w in self.new_w]
            if i == lastf:
                body += ['FLAG %d %d %s' % f for f in self.new_f]
        if firstt == len(L):
            body += self.new_s
        trail = []
        while body and body[-1] == '':
            trail.append(body.pop())
        body += self.new_t + trail
        self.new_w, self.new_f, self.new_s, self.new_t = [], [], [], []
        body = [x for l in body for x in l.split(chr(10))]
        self.L = body
        a = Asc.__new__(Asc)
        a.path, a.lines, a.symdirs, a._asy = self.a.path, list(body), self.a.symdirs, self.a._asy
        a.parse()
        self.a = a

    # ---- symbols
    def sym(self, name):
        return self.a.byname[name]

    def set_attr(self, name, key, val):
        s = self.sym(name)
        for i in range(s['line'] + 1, s['end'] + 1):
            if self.L[i] is not None and self.L[i].startswith('SYMATTR %s ' % key):
                self.L[i] = 'SYMATTR %s %s' % (key, val) if val is not None else None
                return
        if val is not None:
            self.L[s['end']] = self.L[s['end']] + '\nSYMATTR %s %s' % (key, val)

    def set_symline(self, name, sym, x, y, rot):
        s = self.sym(name)
        self.L[s['line']] = 'SYMBOL %s %d %d %s' % (sym, x, y, rot)

    def drop_windows(self, name):
        s = self.sym(name)
        for i in range(s['line'] + 1, s['end'] + 1):
            if self.L[i] is not None and self.L[i].startswith('WINDOW '):
                self.L[i] = None

    def delete_sym(self, name):
        s = self.sym(name)
        pins = [(x, y) for _, x, y in self.a.pins(s)]
        for i in range(s['line'], s['end'] + 1):
            self.L[i] = None
        log.append('deleted %s (%s)' % (name, s['sym']))
        return pins

    def add_sym(self, sym, x, y, rot, attrs, windows=()):
        blk = ['SYMBOL %s %d %d %s' % (sym, x, y, rot)] + list(windows) + ['SYMATTR %s %s' % kv for kv in attrs]
        self.new_s.append('\n'.join(blk))

    # ---- wires / flags
    def del_wire(self, x1, y1, x2, y2):
        for i, xa, ya, xb, yb in self.a.wires:
            if {(xa, ya), (xb, yb)} == {(x1, y1), (x2, y2)} and self.L[i] is not None:
                self.L[i] = None
                return
        raise KeyError('wire %s' % ((x1, y1, x2, y2),))

    def cut_at(self, x, y, toward):
        """delete the wire(s) with an end at (x,y) whose other end lies in direction toward; return the far ends"""
        far = []
        for i, xa, ya, xb, yb in self.a.wires:
            if self.L[i] is None:
                continue
            for (p, q) in (((xa, ya), (xb, yb)), ((xb, yb), (xa, ya))):
                if p == (x, y):
                    d = {'down': q[1] > y, 'up': q[1] < y, 'left': q[0] < x, 'right': q[0] > x}[toward]
                    if d:
                        self.L[i] = None
                        far.append(q)
        if not far:
            raise KeyError('nothing to cut at %s %s' % ((x, y), toward))
        return far

    def flag_at(self, x, y):
        return [f for f in self.a.flags if (f[1], f[2]) == (x, y) and self.L[f[0]] is not None]

    def rename_flag(self, x, y, old, new):
        for i, fx, fy, n in self.a.flags:
            if (fx, fy) == (x, y) and n == old:
                self.L[i] = 'FLAG %d %d %s' % (x, y, new)
                return
        raise KeyError('flag %s at %s' % (old, (x, y)))

    def rename_all_flags(self, old, new):
        k = 0
        for i, fx, fy, n in self.a.flags:
            if n == old:
                self.L[i] = 'FLAG %d %d %s' % (fx, fy, new)
                k += 1
        return k

    def add_flag(self, x, y, n):
        self.new_f.append((x, y, n))

    def add_wire(self, x1, y1, x2, y2):
        self.new_w.append((x1, y1, x2, y2))

    # ---- pruning (call after refresh)
    def prune(self, seeds):
        pts_pins = set()
        for s in self.a.syms:
            for _, x, y in self.a.pins(s):
                pts_pins.add((x, y))
        wires = {i: (xa, ya, xb, yb) for i, xa, ya, xb, yb in self.a.wires}
        stack = list(seeds)
        while stack:
            p = stack.pop()
            if p in pts_pins:
                continue
            ends = [i for i, (xa, ya, xb, yb) in wires.items() if (xa, ya) == p or (xb, yb) == p]
            through = [i for i, (xa, ya, xb, yb) in wires.items()
                       if (xa == xb == p[0] and min(ya, yb) < p[1] < max(ya, yb)) or
                       (ya == yb == p[1] and min(xa, xb) < p[0] < max(xa, xb))]
            fl = self.flag_at(*p)
            if through:
                continue
            if not ends:
                for f in fl:
                    self.L[f[0]] = None
                    log.append('  removed orphan flag %s at %s' % (f[3], p))
                continue
            if len(ends) == 1:
                if fl:
                    log.append('  STOP at flag %s %s (left the stub)' % ([f[3] for f in fl], p))
                    continue
                i = ends[0]
                xa, ya, xb, yb = wires.pop(i)
                self.L[i] = None
                log.append('  pruned wire %s' % ((xa, ya, xb, yb),))
                stack.append((xb, yb) if (xa, ya) == p else (xa, ya))


# ====================================================================== placement helpers
def occupied(a):
    occ = []
    for _, x1, y1, x2, y2 in a.wires:
        occ.append((min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)))
    for _, x, y, n in a.flags:
        occ.append((x - 24, y - 24, x + 24 + 9 * len(n), y + 32))
    for s in a.syms:
        ps = a.pins(s)
        xs = [p[1] for p in ps] + [s['x']]
        ys = [p[2] for p in ps] + [s['y']]
        occ.append((min(xs) - 24, min(ys) - 24, max(xs) + 24, max(ys) + 24))
    for _, l in a.texts:
        t = l.split(' ', 5)
        x, y = int(t[1]), int(t[2])
        body = t[5] if len(t) > 5 else ''
        lines = body.split('\\n')
        occ.append((x, y - 16, x + 11 * max(len(q) for q in lines), y + 28 * len(lines)))
    return occ


def group_bbox(a, items):
    xs, ys = [], []
    for it in items:
        if it[0] == 'sym':
            _, sym, x, y, rot, _attrs = it[:6]
            for p in a.asy_pins(sym):
                dx, dy = Asc.xform(p['x'], p['y'], rot)
                xs.append(x + dx); ys.append(y + dy)
            xs.append(x); ys.append(y)
        elif it[0] == 'flag':
            _, x, y, n = it
            xs += [x - 24, x + 24 + 9 * len(n)]; ys += [y - 24, y + 32]
        elif it[0] == 'wire':
            _, x1, y1, x2, y2 = it
            xs += [x1, x2]; ys += [y1, y2]
    return min(xs) - 24, min(ys) - 24, max(xs) + 24, max(ys) + 24


def find_spot(a, items, tx, ty, extra=(), gap=32, rmax=2400):
    occ = occupied(a) + list(extra)
    bx0, by0, bx1, by1 = group_bbox(a, items)
    best = None
    for r in range(0, rmax, 16):
        cands = []
        for dx in range(-r, r + 1, 16):
            for dy in (-r, r) if abs(dx) != r else range(-r, r + 1, 16):
                cands.append((dx, dy))
        for dx, dy in sorted(cands, key=lambda d: d[0] ** 2 + d[1] ** 2):
            ox, oy = tx + dx, ty + dy
            b = (bx0 + ox - gap, by0 + oy - gap, bx1 + ox + gap, by1 + oy + gap)
            if all(b[2] < o[0] or b[0] > o[2] or b[3] < o[1] or b[1] > o[3] for o in occ):
                d = dx * dx + dy * dy
                if best is None or d < best[0]:
                    best = (d, ox, oy)
        if best is not None and best[0] <= (r + 16) ** 2:
            break
    if best is None:
        raise RuntimeError('no spot near %s' % ((tx, ty),))
    return best[1], best[2], (bx0 + best[1], by0 + best[2], bx1 + best[1], by1 + best[2])


def place(ed, items, ox, oy):
    for it in items:
        if it[0] == 'sym':
            _, sym, x, y, rot, attrs = it[:6]
            win = it[6] if len(it) > 6 else ()
            ed.add_sym(sym, x + ox, y + oy, rot, attrs, win)
        elif it[0] == 'flag':
            ed.add_flag(it[1] + ox, it[2] + oy, it[3])
        elif it[0] == 'wire':
            ed.add_wire(it[1] + ox, it[2] + oy, it[3] + ox, it[4] + oy)


RES_H = ('WINDOW 0 0 56 VBottom 2', 'WINDOW 3 32 56 VTop 2')      # label windows of a horizontal (R90) resistor/source


def vres(name, val, x, y, top, bot):
    """vertical resistor with pins (x+16, y+16) and (x+16, y+96), flags on both ends"""
    return [('sym', 'res', x, y, 'R0', [('InstName', name), ('Value', val)]),
            ('flag', x + 16, y + 16, top), ('flag', x + 16, y + 96, bot)]


# ====================================================================== the edit
ed = Ed(SRC)
a = ed.a
S = lambda n: ed.sym(n)
pin = lambda n, p: next((x, y) for q, x, y in a.pins(S(n)) if q == p)
seeds = []

# ---- 1. R1 -> 4-terminal 1 mOhm Kelvin shunt, sense wires relabelled ISNS_P / ISNS_N
r1 = S('R1')
assert (r1['sym'], r1['x'], r1['y'], r1['rot']) == ('res', -448, 256, 'R90')
ed.set_symline('R1', 'CSS4J_4026', -544, 272, 'R0')
ed.drop_windows('R1')
ed.set_attr('R1', 'Value', 'CSS4J_4026')
ed.set_attr('R1', 'SpiceLine', 'R=1m')
for w in ((-576, 272, -576, 208), (-448, 272, -448, 208)):
    ed.del_wire(*w)
for w in ((-576, 208, -576, 240), (-576, 240, -528, 240), (-448, 208, -448, 240), (-448, 240, -480, 240)):
    ed.add_wire(*w)
ed.rename_flag(-576, 208, 'rsense_hi', 'ISNS_P')
ed.rename_flag(-448, 208, 'rsense_lo', 'ISNS_N')
ed.add_flag(-448, 272, 'rsense_lo')
log.append('R1 -> CSS4J_4026 1m, Kelvin sense to ISNS_P/ISNS_N')

# ---- 2. U1 INA241A3 -> U25 INA241A4 (REF2 to ground)
u1 = S('U1')
assert u1['sym'] == 'INA241A3'
ed.set_symline('U1', 'INA241A4', u1['x'], u1['y'], u1['rot'])
ed.add_flag(u1['x'] + 32, u1['y'] + 64, '0')

# ---- 3. S1-S3 AGATE -> CD74HC4066 channels (U106A = ch3 / IREF3, U106B = ch2 / IREF2, U106C = ch1 / IREF1)
for s, ctrl in (('S1', 'IREF3'), ('S2', 'IREF2'), ('S3', 'IREF1')):
    sw = S(s)
    assert sw['sym'] == 'sw' and sw['rot'] == 'R270'
    ax, ay = sw['x'] + 16, sw['y']
    cx, cy = ax + 64, ay + 48
    seeds += ed.cut_at(cx, cy, 'down')
    ed.set_symline(s, 'CD74HC4066', ax, ay, 'R0')
    ed.drop_windows(s)
    ed.set_attr(s, 'Value', 'CD74HC4066')
    ed.add_flag(cx, cy, ctrl)
    ed.add_flag(ax + 48, ay - 32, '5V')
    log.append('%s -> CD74HC4066 at %s, CTRL=%s' % (s, (ax, ay), ctrl))

# ---- 4. U9 CD4051B -> U28 74HC4051; IO0, IO3, IO5, IO6, IO7 to ground
u9 = S('U9')
assert u9['sym'] == 'CD4051B'
io0 = pin('U9', 'IO0')
ed.cut_at(io0[0], io0[1], 'right')
ed.set_symline('U9', '74HC4051', u9['x'], u9['y'], u9['rot'])
for p in ('IO0', 'IO3', 'IO5', 'IO6', 'IO7'):
    ed.add_flag(*pin('U9', p), '0')

# ---- 5. regulators -> L78L05; C7/C55 22u; D19 -> 5.0SMDJ54A
for u in ('U17', 'U18'):
    s = S(u)
    assert s['sym'] == 'L7805'
    ed.set_symline(u, 'L78L05', s['x'], s['y'], s['rot'])
for c in ('C7', 'C55'):
    ed.set_attr(c, 'Value', '22' + MU)
ed.set_attr('D19', 'Value', 'TVS_5p0SMDJ54A')

# ---- 6. old IREF chains out (sources, dividers); their op-amp input nodes keep C45/C44/C41
old_pins = {}
for n in ('Iref1', 'R57', 'R58', 'Iref2', 'R54', 'R55', 'Iref3', 'R10', 'R29', 'R5', 'R73', 'R74'):
    old_pins[n] = ed.delete_sym(n)
    seeds += old_pins[n]

# ---- 7. gate-drive parameters (tuned to 74HC00 / 74HC14 typical)
NAND_OLD = 'Vhigh=5 Vlow=0 Vt=2.5 Td=5n Trise=2n Tfall=2n Rhigh=25 Rlow=15'
NAND_NEW = 'Vhigh=5 Vlow=0 Vt=2.5 Td=3.8n Trise=9.4n Tfall=9.4n Rhigh=50 Rlow=42'
SCH_OLD = ('Vhigh=5 Vlow=0 Vt=2.5 Vh=0.5 Td=4.5n Trise=2n Tfall=2n Rout=20',
           'Vhigh=5 Vlow=0 Vt=2.5 Vh=0.45 Td=15n Trise=7n Tfall=7n Rout=50')
SCH_NEW = 'Vhigh=5 Vlow=0 Vt=2.245 Vh=0.52 Td=6.8n Trise=9.4n Tfall=9.4n Rout=45'
ng = 0
for s in a.syms:
    if s['sym'].startswith('Digital'):
        for i in range(s['line'] + 1, s['end'] + 1):
            l = ed.L[i]
            if l and l.startswith('SYMATTR '):
                l2 = l.replace(NAND_OLD, NAND_NEW)
                for o in SCH_OLD:
                    l2 = l2.replace(o, SCH_NEW)
                if l2 != l:
                    ed.L[i] = l2
                    ng += 1
assert ng == 18, ng
log.append('retuned %d gates' % ng)

# ---- 8. directives
for i, l in a.texts:
    if l.endswith('!.lib INA241A3.lib'):
        ed.L[i] = l.replace('INA241A3.lib', 'INA241A4.lib')
    elif l.endswith('!.lib L7805.lib'):
        ed.L[i] = l.replace('L7805.lib', 'L78L05.lib')
    elif '!.model AGATE' in l:
        ed.L[i] = None

# ---- 9. net labels: 5 V rail name as in KiCad; sink sense nodes; op-amp IREF inputs
k = ed.rename_all_flags('VDD', '5V')
log.append('renamed %d VDD flag(s) to 5V' % k)
# the CD4017B symbol reaches its supply by net NAME (SpiceModel "VDD 0"): point this instance at the renamed rail
assert S('U8')['sym'] == 'CD4017B'
ed.set_attr('U8', 'SpiceModel', '5V 0')
ed.add_flag(*pin('C45', 'A'), 'IREF1_input')
ed.add_flag(*pin('C44', 'A'), 'IREF2_input')
ed.add_flag(*pin('C41', 'A'), 'IREF3_input')
for r, n in (('R52', 'SNS_CH1'), ('R53', 'SNS_CH2'), ('R7', 'SNS_CH3')):
    top = min(((x, y) for _, x, y in a.pins(S(r))), key=lambda p: p[1])
    ed.add_flag(top[0], top[1], n)

ed.refresh()
ed.prune(seeds)
ed.refresh()

# ---- 10. new parts, each group placed in free space near a target point
placed = []


def put(items, tx, ty, what):
    ox, oy, box = find_spot(ed.a, items, tx, ty, extra=placed)
    place(ed, items, ox, oy)
    placed.append(box)
    log.append('placed %s at %s (target %s)' % (what, (ox, oy), (tx, ty)))
    return ox, oy


# R104 (was R5, now on GATE_M1), R73/R74 on the gates, R105 on ARD_M1_INHIBIT
put(vres('R104', '10k', 0, 0, 'GATE_M1', '0'), 2560 - 16, 384 - 16, 'R104')
put(vres('R73', '10k', 0, 0, 'GATE_M4', 'm4_source'), 2112, 1232, 'R73')
put(vres('R74', '10k', 0, 0, 'GATE_M5', 'm4_source'), 1792, 1184, 'R74')
put(vres('R105', '100k', 0, 0, 'ARD_M1_INHIBIT', '0'), 3344, 128, 'R105')

# 7 x 100n on the 5 V rail (KiCad C92, C94-C99)
dec = []
names = ['C92', 'C94', 'C95', 'C96', 'C97', 'C98', 'C99']
for j, n in enumerate(names):
    dec += [('sym', 'cap', 64 * j, 0, 'R0', [('InstName', n), ('Value', '100n')]), ('flag', 64 * j + 16, 64, '0')]
dec += [('wire', 16, 0, 64 * 6 + 16, 0), ('flag', 16, 0, '5V')]
put(dec, -2600, 320, 'C92-C99')

# IREF / digital-pot block: SIM_IREFn (Arduino PWM) -> R 22k -> node (R 1k, C 1n) -> pot B; pot A = GND; W = IREFn_input
chan = [('1', 'R29', 'R54', 'C100', 'U26A', 'POT1_CODE'), ('2', 'R30', 'R55', 'C101', 'U26B', 'POT2_CODE'),
        ('3', 'R57', 'R58', 'C102', 'U26C', 'POT3_CODE')]
blk = []
for j, (n, r22, r1k, c1n, pot, code) in enumerate(chan):
    y = 208 * j
    duty = 'IREF%s_DUTY' % n
    pulse = ('PULSE({if(%s>=256,5,0)} {if(%s<=0,0,5)} 0 1n 1n {max(%s/256*2.04m-2n,1n)} 2.04m)' % (duty, duty, duty))
    blk += [('sym', 'voltage', 96, y, 'R90', [('InstName', 'SIM_IREF' + n), ('Value', pulse)],
             ('WINDOW 0 -32 56 VBottom 2', 'WINDOW 3 32 56 VTop 0')),
            ('flag', 0, y, '0'), ('flag', 80, y, 'IREF' + n), ('wire', 80, y, 96, y),
            ('sym', 'res', 192, y - 16, 'R90', [('InstName', r22), ('Value', '22k')], RES_H),
            ('wire', 176, y, 288, y),
            ('sym', 'res', 208, y - 16, 'R0', [('InstName', r1k), ('Value', '1k')]), ('flag', 224, y + 80, '0'),
            ('sym', 'cap', 272, y, 'R0', [('InstName', c1n), ('Value', '1n')]), ('flag', 288, y + 64, '0'),
            ('wire', 288, y, 352, y),
            ('sym', 'MCP4451_POT', 352, y + 48, 'R0', [('InstName', pot), ('SpiceLine', 'CODE={%s}' % code)]),
            ('flag', 352, y + 96, '0'), ('flag', 400, y + 48, 'IREF%s_input' % n)]
ox, oy = put(blk, -700, 2200, 'IREF block')

# pot control unit U26E with R102 (HVC/A0), R99 (A1), R103 (RESET) - after renaming the cable resistor R99
ctl = [('sym', 'MCP4451_CTRL', 0, 0, 'R0', [('InstName', 'U26E')]),
       ('flag', 0, -112, '5V'), ('flag', 48, 112, '0'), ('flag', -96, -32, 'SCL'), ('flag', -96, 0, 'SDA'),
       ('sym', 'res', -64, 96, 'R0', [('InstName', 'R102'), ('Value', '10k')]), ('flag', -48, 192, '0'),
       ('sym', 'res', -16, 96, 'R0', [('InstName', 'R99_NEW'), ('Value', '10k')]), ('flag', 0, 192, '0'),
       ('sym', 'res', 80, -96, 'R0', [('InstName', 'R103'), ('Value', '10k')]), ('flag', 96, -80, '5V')]
put(ctl, ox + 700, oy + 160, 'U26E')

ed.refresh()

# ---- 11. designators -> KiCad (two phases so no name is ever used twice)
REN = {'U1': 'U25', 'U17': 'U1', 'U18': 'U17', 'U8': 'U18', 'U20': 'U8', 'U9': 'U28',
       'S1': 'U106A', 'S2': 'U106B', 'S3': 'U106C',
       'C47': 'C104', 'C5': 'C90', 'C2': 'C89', 'C27': 'C91',
       'C_VREF1': 'C103', 'C_VREF2': 'C93', 'C_VREF3': 'C47',
       'R_VREF1': 'R101', 'R_VREF2': 'R100', 'R_VREF3': 'R77', 'R77': 'R62',
       'R99': 'SIM_RCABLE', 'L2': 'SIM_LCABLE', 'V1': 'SIM_VBATT', 'R99_NEW': 'R99',
       'D16': 'SIM_LED1', 'D18': 'SIM_LED2', 'D17': 'SIM_LED3',
       'Reference_V1': 'SIM_VREF1', 'Reference_V2': 'SIM_VREF2', 'Reference_V3': 'SIM_VREF3',
       'ARD_M1_INHIBIT': 'SIM_ARD_INH',
       'A4': 'U101A', 'A1': 'U101B', 'set': 'U101C', 'reset': 'U101D',
       'A8': 'U102A', 'A14': 'U102B', 'A3': 'U102C', 'A10': 'U102D',
       'A7': 'U103A', 'A12': 'U103B',
       'A17': 'U104A', 'A9': 'U104B', 'A11': 'U104C', 'A18': 'U104D', 'A2': 'U104E', 'A6': 'U104F',
       'A13': 'U105A', 'A20': 'U105B'}
names_now = set(ed.a.byname)
missing = [k for k in REN if k not in names_now]
assert not missing, missing
for phase in (0, 1):
    for old, new in REN.items():
        src = old if phase == 0 else '__TMP_' + old
        dst = '__TMP_' + old if phase == 0 else new
        s = ed.a.byname[src]
        for i in range(s['line'] + 1, s['end'] + 1):
            if ed.L[i] == 'SYMATTR InstName %s' % src:
                ed.L[i] = 'SYMATTR InstName %s' % dst
    ed.refresh()
final = [s['attr'].get('InstName') for s in ed.a.syms]
dups = sorted({n for n in final if final.count(n) > 1})
assert not dups, dups

# ---- 12. directives for the new models and parameters (placed in free space near the other directives)
txt = ('!.lib CD74HC4066.lib\\n.lib 74HC4051.lib\\n.lib MCP4451.lib\\n.lib CSS4J.lib\\n.lib TVS_5p0SMDJ.lib\\n'
       '.param IREF1_DUTY=256 IREF2_DUTY=256 IREF3_DUTY=256\\n.param POT1_CODE=86 POT2_CODE=103 POT3_CODE=103')
cmt = (';IREFn_DUTY: Arduino PWM duty on IREFn (J9) in 256ths, 490 Hz: 256 = always on, 128 = 50 %, 0 = off.\\n'
       'POTn_CODE: MCP4451 wiper code of U26A/B/C, 0-256 (0 = wiper at B = full current, 256 = at A = 0 A;\\n'
       'Microchip convention, not checked against the data sheet). 86/103/103 give 2.63/2.37/2.37 A peaks.\\n'
       'Parts named SIM_ exist only in the simulation (battery, cable, LEDs, Arduino outputs).\\n'
       'Dimming runs (IREFn_DUTY below 256) can stop advancing while all LEDs are off (log fills with\\n'
       '"tolerance relaxed" at one time). Adding solver=alt to the .options line got past it (2-3x slower).')
occ = occupied(ed.a)
y = max(o[3] for o in occ if o[0] < -2500) + 48
ed.new_t.append('TEXT -2880 %d Left 2 %s' % (y, txt))
ed.new_t.append('TEXT -2880 %d Left 2 %s' % (y + 7 * 34 + 32, cmt))
ed.refresh()

ed.a.write(DST)
print('\n'.join(log))
print('symbols:', len(ed.a.syms), 'wires:', len(ed.a.wires), 'flags:', len(ed.a.flags))
