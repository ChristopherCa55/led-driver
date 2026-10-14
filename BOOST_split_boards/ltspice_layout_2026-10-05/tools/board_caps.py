"""Put the gate drivers' bypass caps where the PCB has them (the user's request, 2026-10-07).

    python board_caps.py       work/BOOST_revised_v3.asc -> work/BOOST_revised_v4.asc

On the power board each driver's VCCI has ONE cap within 2-3 mm of its pads (bypass_map.json):
    U15 <- C62 (1u)   U10 <- C90 (100n)   U8 <- C89 (1u)   U19 <- C48 (100n);   U19's 12 V (VDDA) <- C31 (stays).
C6 and C25 (1u, 12 V) sit beside the 12 V regulator U16, not at any driver.
C57, C58, C91, C92 are on the control card next to the logic chips (U105, U104, U102): they go back to the logic
bypass row in the not-yet-redrawn part of the sheet, until the control block is drawn.

So each output driver keeps one VCCI cap, always in the inner position next to VCCI (the outer position and its
wiring go), turned 180 degrees where its pins are netlisted the other way round, so the three outputs look the same.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, on_interior, partition, HANDOFF
from layout_lib import compare, RENAME
from copy_driver_layout import inv_xf, world_box, close, JUSTS, FLIP, netlist_nodes

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised_v3.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v4.asc')
ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')


def remove_with_stubs(a, name):
    """remove a part, plus only the wires and ground flags that served nothing but its pins; returns the Sym"""
    s = next(x for x in a.syms if x.name == name)
    todo = [(x, y) for _, x, y in a.pins(s)]
    a.syms.remove(s)
    while todo:
        p = todo.pop()
        ends = [w for w in a.wires if (w[0], w[1]) == p or (w[2], w[3]) == p]
        pins = {(x, y) for t in a.syms for _, x, y in a.pins(t)}
        flags = [f for f in a.flags if (f[0], f[1]) == p]
        if p in pins or any(on_interior(p, w) for w in a.wires) or len(ends) > 1:
            continue
        if any(f[2] != '0' for f in flags):
            continue                                  # never drop a named label
        for f in flags:
            a.flags.remove(f)
        if ends:
            w = ends[0]
            a.wires.remove(w)
            todo.append((w[2], w[3]) if (w[0], w[1]) == p else (w[0], w[1]))
    return s


def place_like(a, s, ref, ref_win_sym, flip):
    """put Sym s on exactly the body box of `ref` (a Sym already placed or a recorded copy); turned 180 degrees if
    flip. Text windows give the same on-screen text boxes as `ref_win_sym`."""
    if not flip:
        s.x, s.y, s.rot = ref.x, ref.y, ref.rot
        s.windows = dict(ref_win_sym.windows)
        return
    rot = FLIP[ref.rot]
    tb = a.body(ref)
    s.rot, s.x, s.y = rot, 0, 0
    b0 = a.body(s)
    s.x, s.y = tb[0] - b0[0], tb[1] - b0[1]
    assert [(x, y) for _, x, y in a.pins(s)] == [(x, y) for _, x, y in a.pins(ref)][::-1], s.name
    s.windows = {}
    wins = dict(a.asy(ref_win_sym.sym)['windows'])
    wins.update(ref_win_sym.windows)
    for num, (lx, ly, j, sz) in wins.items():
        if j == 'Invisible':
            s.windows[num] = (0, 0, 'Invisible', sz)
            continue
        wx, wy = a.xf(lx, ly, ref_win_sym.rot)
        dx, dy = ref.x - ref_win_sym.x, ref.y - ref_win_sym.y
        ax, ay = ref_win_sym.x + wx + dx - s.x, ref_win_sym.y + wy + dy - s.y
        nlx, nly = inv_xf(ax, ay, rot)
        target = world_box(a, ref_win_sym, (lx, ly, j, sz), dx, dy)
        for jj in JUSTS:
            if close(world_box(a, s, (nlx, nly, jj, sz)), target):
                s.windows[num] = (nlx, nly, jj, sz)
                break
        else:
            raise SystemExit('no text window for %s' % s.name)


class Ghost:
    """a recorded position/orientation/windows of a part that has been taken away"""
    def __init__(self, s, dx=0, dy=0):
        self.sym, self.x, self.y, self.rot, self.windows = s.sym, s.x + dx, s.y + dy, s.rot, dict(s.windows)


def main():
    a = Asc(SRC)
    nodes = netlist_nodes()
    order = lambda n: nodes[n]

    # ---- the three output drivers: drop the outer VCCI cap, swap the inner one for the board's cap
    plan = [('OUTPUT 1', 'C91', 'C92', 'C62'), ('OUTPUT 2', 'C62', 'C48', 'C90'), ('OUTPUT 3', 'C57', 'C58', 'C89')]
    inner_ghost, pool = {}, {}
    for title, outer, inner, board in plan:
        inner_ghost[title] = Ghost(next(s for s in a.syms if s.name == inner))
    for title, outer, inner, board in plan:
        pool[outer] = remove_with_stubs(a, outer)            # outer position and its wiring go
    for title, outer, inner, board in plan:
        s = next(x for x in a.syms if x.name == inner)
        a.syms.remove(s)                                      # inner slot freed (pins stay wired)
        pool[inner] = s
    # U19: C90 out (C48 takes its place); C89 out with its stub
    c90 = next(s for s in a.syms if s.name == 'C90')
    u19_c90 = Ghost(c90)
    a.syms.remove(c90)
    pool['C90'] = c90
    pool['C89'] = remove_with_stubs(a, 'C89')
    # 12 V caps off the bootstrap feeds
    pool['C6'] = remove_with_stubs(a, 'C6')
    pool['C25'] = remove_with_stubs(a, 'C25')

    def put(name, ghost, ref_order_name):
        s = pool.pop(name) if name in pool else None
        if s is None:
            raise SystemExit('%s not in pool' % name)
        flip = order(name) != order(ref_order_name)
        place_like(a, s, ghost, ghost, flip)
        a.syms.append(s)
        print('%-4s at (%d, %d) %s%s' % (name, s.x, s.y, s.rot, '  turned 180' if flip else ''))

    put('C62', inner_ghost['OUTPUT 1'], 'C92')
    put('C90', inner_ghost['OUTPUT 2'], 'C48')
    put('C89', inner_ghost['OUTPUT 3'], 'C58')
    put('C48', u19_c90, 'C90')

    # ---- C6, C25 beside C30 at U16's 12 V output (old drawing, until the regulator block is drawn)
    c30 = next(s for s in a.syms if s.name == 'C30')
    xa = a.pin(c30, 'A')
    for k, name in enumerate(('C6', 'C25'), 1):
        g = Ghost(c30, 64 * k, 0)
        put(name, g, 'C30')
        prev = (xa[0] + 64 * (k - 1), xa[1])
        a.wires.append((prev[0], prev[1], xa[0] + 64 * k, xa[1]))
        a.flags.append([xa[0] + 64 * k, xa[1] + 64, '0', None])

    # ---- C57, C58, C91, C92 back in the logic bypass row (left of C94), as C94 is drawn
    c94 = next(s for s in a.syms if s.name == 'C94')
    a94 = a.pin(c94, 'A')
    flag5 = next(f for f in a.flags if f[2] == '5V' and f[1] == a94[1] and f[0] < a94[0])
    left = flag5[0]
    for k, name in enumerate(('C58', 'C57', 'C92', 'C91')):
        px = left - 64 * k                                   # first one sits where the row's 5V label was
        put(name, Ghost(c94, px - a94[0], 0), 'C94')
        if k:
            a.wires.append((px, a94[1], px + 64, a94[1]))
        a.flags.append([px, a94[1] + 64, '0', None])
    # the 5V label moves one step left of the new left end of the row
    flag5[0] = left - 64 * 4
    a.wires.append((left - 64 * 4, a94[1], left - 64 * 3, a94[1]))
    if pool:
        raise SystemExit('unplaced: %s' % sorted(pool))

    orig = Asc(ORIG)
    orig.syms = [s for s in orig.syms if s.name != 'R14']
    probs, newnames = compare(orig, a)
    for p in probs:
        print('PROBLEM', p)
    if probs:
        raise SystemExit('electrical self-check failed; nothing written')
    a.write(OUT)
    print('electrical self-check OK; wrote', OUT)


if __name__ == '__main__':
    main()
