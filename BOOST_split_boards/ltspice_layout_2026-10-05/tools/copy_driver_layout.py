"""Copy the user's OUTPUT 3 gate-driver arrangement (U8 and its parts, drawn above M5/M4) to OUTPUT 1 and OUTPUT 2.

    python copy_driver_layout.py   -> work/BOOST_revised_v3.asc   (the user's BOOST_revised_v2.asc is not touched)

Steps:
  1. Shift the whole OUTPUT 1 row 48 units right, so that M7/M2 line up with M6/M3 and M5/M4 (only the LX feed wire
     from the LX bus stretches).
  2. Take U15's group (and U10's) out of the old drawing; wires that served only them go; any old net that loses its
     name gets a plain label at the cut (as in the pilot).
  3. In each target row, delete the old gate/source label stubs above the FET pair, then paste OUTPUT 3's driver
     drawing at the same offset from the FET pair: same part positions, orientations and text positions; labels
     renamed for the channel (out_3_on -> M2_ON / out_2_on, ena_out_3 -> ena_out_1/2, GATE_M4 -> GATE_M2/M3 ...).
     A 2-pin part netlisted with its pins the other way round from its OUTPUT 3 twin is drawn turned 180 degrees on
     exactly the same spot, so it looks identical and stays electrically identical.
  4. Bypass caps follow the user's OUTPUT 3 choice and their KiCad drawing: VCCI gets a 1u + 100n pair
     (U8: C57 C58 -> U15: C91 C92, U10: C62 C48) and the bootstrap's 12V input gets a 1u (U8: C25 -> U10: C6;
     U15 has no such cap in the design, so that spot stays empty).
The user's bootstrap explanation comment at OUTPUT 3 is not duplicated.
"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, Sym, connectivity, partition, HANDOFF
from layout_lib import strip_old, name_cut_groups, compare, RENAME

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised_v2.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v3.asc')
ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')
NET = os.path.normpath(os.path.join(HANDOFF, '..', 'reorg_2026-10-05', 'work', 'orig', 'LTspice', 'BOOST.net'))

T3 = ['U8', 'R47', 'D13', 'R59', 'D22', 'R73', 'R74', 'D21', 'R72', 'C60', 'C61', 'C57', 'C58', 'C25']
TARGETS = {
    'OUTPUT 1': ('M7', ['U15', 'R13', 'D11', 'R60', 'D2', 'R75', 'R76', 'D10', 'R21', 'C18', 'C51', 'C91', 'C92', None]),
    'OUTPUT 2': ('M6', ['U10', 'R23', 'D14', 'R70', 'D8', 'R61', 'R49', 'D9', 'R48', 'C16', 'C50', 'C62', 'C48', 'C6']),
}
ANCHOR3 = 'M5'
REGION = (-792, -728, 218, 48)        # driver drawing relative to the FET-pair anchor (x1, y1, x2, y2)
ROW1_SHIFT = 48
JUSTS = ['Left', 'Right', 'Top', 'Bottom', 'Center', 'VLeft', 'VRight', 'VTop', 'VBottom', 'VCenter']
FLIP = {'R0': 'R180', 'R180': 'R0', 'R90': 'R270', 'R270': 'R90', 'M0': 'M180', 'M180': 'M0', 'M90': 'M270',
        'M270': 'M90'}


def netlist_nodes():
    txt = open(NET, encoding='utf-8').read()
    nodes = {}
    for l in txt.split('\n'):
        t = l.split(';')[0].split()
        if not t or t[0][0] in '*.':
            continue
        name = t[0].split('§')[-1]
        if t[0][0] in 'RCDL':
            nodes[name] = t[1:3]
        elif t[0][0] == 'X' and name.startswith('U'):
            nodes[name] = t[1:13]
    return nodes


def inside(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def inv_xf(px, py, rot):
    """inverse of Asc.xf (rotate k*90 then mirror)"""
    if rot.startswith('M'):
        px = -px
    for _ in range(int(rot[1:]) // 90):
        px, py = py, -px
    return px, py


def main():
    a = Asc(SRC)
    nodes = netlist_nodes()
    by = a.by()

    # ---- 1. shift OUTPUT 1 right by 48 (everything right of the LX bus in the row band)
    m7 = by['M7']
    band = (-790, m7.y - 400, 2400, m7.y + 400)
    bus_x = -800
    for s in a.syms:
        if inside((s.x, s.y), band):
            s.x += ROW1_SHIFT
    new = []
    for w in a.wires:
        e1, e2 = (w[0], w[1]), (w[2], w[3])
        i1, i2 = inside(e1, band), inside(e2, band)
        if i1 and i2:
            new.append((w[0] + ROW1_SHIFT, w[1], w[2] + ROW1_SHIFT, w[3]))
        elif i1 or i2:
            # the LX feed: one end on the bus stays, the other moves
            if not ((w[0] == bus_x and i2) or (w[2] == bus_x and i1)):
                raise SystemExit('wire crosses the row-1 band edge unexpectedly: %s' % (w,))
            new.append((w[0] + (ROW1_SHIFT if i1 else 0), w[1], w[2] + (ROW1_SHIFT if i2 else 0), w[3]))
        else:
            new.append(w)
    a.wires = new
    for f in a.flags:
        if inside((f[0], f[1]), band):
            f[0] += ROW1_SHIFT
    tx = []
    for t in a.texts:
        p = t.split(' ', 5)
        x, y = int(p[1]), int(p[2])
        if inside((x, y), band) and x > bus_x:
            t = 'TEXT %d %d %s %s %s' % (x + ROW1_SHIFT, y, p[3], p[4], p[5])
        tx.append(t)
    a.texts = tx
    print('OUTPUT 1 row shifted right by %d' % ROW1_SHIFT)

    # ---- 2. take the target groups out of the old drawing
    remove = {p for _, (anc, ps) in TARGETS.items() for p in ps if p}
    pool, trimmed = strip_old(a, remove)
    by = a.by()

    # ---- template (OUTPUT 3)
    an3 = by[ANCHOR3]
    R3 = (an3.x + REGION[0], an3.y + REGION[1], an3.x + REGION[2], an3.y + REGION[3])
    t_wires = [w for w in a.wires if inside((w[0], w[1]), R3) and inside((w[2], w[3]), R3)]
    t_flags = [f for f in a.flags if inside((f[0], f[1]), R3)]
    t_syms = {n: by[n] for n in T3}

    for title, (anchor, parts) in TARGETS.items():
        an = by[anchor]
        dx, dy = an.x - an3.x, an.y - an3.y
        Rk = (R3[0] + dx, R3[1] + dy, R3[2] + dx, R3[3] + dy)
        # channel net map from the drivers' pins (template U8 -> target)
        nmap = {}
        for tn, pn in zip(T3, parts):
            if pn and tn in nodes and pn in nodes:
                for x, y in zip(nodes[tn], nodes[pn]):
                    nmap.setdefault(x, y)
        nmap.update({'GATE_M4': 'GATE_M2' if anchor == 'M7' else 'GATE_M3',
                     'GATE_M5': 'GATE_M7' if anchor == 'M7' else 'GATE_M6'})
        # clear the target row's old gate/source stubs and labels in the region
        a.wires = [w for w in a.wires if not (inside((w[0], w[1]), Rk) and inside((w[2], w[3]), Rk))]
        a.flags = [f for f in a.flags if not inside((f[0], f[1]), Rk)]
        # paste wires and renamed flags
        for w in t_wires:
            a.wires.append((w[0] + dx, w[1] + dy, w[2] + dx, w[3] + dy))
        for f in t_flags:
            a.flags.append([f[0] + dx, f[1] + dy, nmap.get(f[2], f[2]), f[3]])
        # place the target parts
        for tn, pn in zip(T3, parts):
            if pn is None:
                continue
            ts = t_syms[tn]
            s = pool.pop(pn)
            tnodes, pnodes = nodes[tn], nodes[pn]
            flipped = len(tnodes) == 2 and [nmap.get(x, x) for x in tnodes] == pnodes[::-1]
            if len(tnodes) == 2 and not flipped and [nmap.get(x, x) for x in tnodes] != pnodes:
                raise SystemExit('%s does not correspond to %s: %s vs %s' % (pn, tn, tnodes, pnodes))
            if not flipped:
                s.x, s.y, s.rot = ts.x + dx, ts.y + dy, ts.rot
                s.windows = dict(ts.windows)
            else:
                rot = FLIP[ts.rot]
                # same body box as the template's twin
                tb = a.body(ts)
                s.rot, s.x, s.y = rot, 0, 0
                b0 = a.body(s)
                s.x, s.y = tb[0] + dx - b0[0], tb[1] + dy - b0[1]
                # pins must land on the twin's pin points, swapped
                tp = [(x + dx, y + dy) for _, x, y in a.pins(ts)]
                sp = [(x, y) for _, x, y in a.pins(s)]
                assert sp == tp[::-1], (pn, sp, tp)
                # text windows giving the same world boxes
                s.windows = {}
                wins = dict(a.asy(ts.sym)['windows'])
                wins.update(ts.windows)
                for num, (lx, ly, j, sz) in wins.items():
                    if j == 'Invisible':
                        s.windows[num] = (0, 0, 'Invisible', sz)
                        continue
                    wx, wy = a.xf(lx, ly, ts.rot)
                    ax, ay = ts.x + wx + dx - s.x, ts.y + wy + dy - s.y
                    nlx, nly = inv_xf(ax, ay, rot)
                    target = world_box(a, ts, (lx, ly, j, sz), dx, dy)
                    for jj in JUSTS:
                        if close(world_box(a, s, (nlx, nly, jj, sz)), target):
                            s.windows[num] = (nlx, nly, jj, sz)
                            break
                    else:
                        raise SystemExit('no text window for %s attr %d' % (pn, num))
            a.syms.append(s)
            print('%s: %-4s at (%d, %d) %s%s' % (title, pn, s.x, s.y, s.rot, '  (turned 180, pins netlisted '
                                                  'the other way round)' if flipped else ''))
    if pool:
        raise SystemExit('parts left unplaced: %s' % sorted(pool))
    # wires and labels pasted for a part this output does not have (OUTPUT 1 has no C25 twin) are left dangling:
    # trim them the same way the old drawing is trimmed
    strip_old(a, set())

    # ---- old drawing: keep every cut net's name
    orig = Asc(ORIG)
    orig.syms = [s for s in orig.syms if s.name != 'R14']        # R14: deletion approved by the user 2026-10-07
    added = name_cut_groups(a, partition(orig, RENAME), trimmed, RENAME)
    for p, n in added:
        print('label %s added in the old drawing at %s' % (n, p))
    probs, newnames = compare(orig, a)
    for p in probs:
        print('PROBLEM', p)
    if probs:
        raise SystemExit('electrical self-check failed; nothing written')
    a.write(OUT)
    print('electrical self-check OK; wrote', OUT)


def world_box(a, s, win, dx=0, dy=0):
    sys.path.insert(0, os.path.join(HANDOFF, 'tools'))
    from asc_layout_check import text_box, xf_box
    import json
    tm = json.load(open(os.path.join(HANDOFF, 'blocks.json')))['text_metrics']
    lx, ly, j, sz = win
    b = text_box(lx, ly, j, sz, 'XXXXXX', tm)
    w = xf_box(b, s, s.rot)
    return (w[0] + dx, w[1] + dy, w[2] + dx, w[3] + dy)


def close(b1, b2):
    return all(abs(u - v) < 1.0 for u, v in zip(b1, b2))


if __name__ == '__main__':
    main()
