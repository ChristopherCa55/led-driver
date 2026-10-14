"""v7 from the user's v6 (2026-10-07):

    python build_v7.py          work/BOOST_revised_v6.asc -> work/BOOST_revised_v7.asc (refuses to overwrite)

1. VerrGT0 drawn as wires (the user: "I don't really like how there are not any wires for the verrgt0 and out-"):
   from the latch, over the top of the latch, down a short bus left of the channel-enable rows into each first NAND.
   The rows move 192 right to make room.
2. Out- drawn as wires from the latch to the three channel-enable rows: down from the latch, along under the rows and
   up a bus on their right, into each second NAND from above (rows 1, 2) or below (row 3, whose NAND has its inputs
   the other way round). Out- keeps its label at U18 (far left) and at the M1 inhibit (now above the rows): wiring
   those would need a long detour around other sections.
3. U18 (CD4017B) and U28 (74HC4051) redrawn for their new KiCad-style pin layouts (make_symbols.py; user OK to move
   their pins). U28 no longer needs mirroring: select lines come straight from U18, and V_err leaves over the top.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, HANDOFF
from layout_lib import Draw, compare

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised_v6.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v7.asc')
ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')

ROWS = (5990, -6840, 7720, -5860)        # the three channel-enable rows in the user's v6
SEQ = (3380, -6720, 4620, -5780)         # U18 + U28 and their wiring in the user's v6
SHIFT = 192
ROW_Y = (-6720, -6400, -6080)


def inside(p, r):
    return r[0] <= p[0] <= r[2] and r[1] <= p[1] <= r[3]


def tpos(t):
    p = t.split(' ', 3)
    return int(p[1]), int(p[2])


def move_text(a, old_prefix, x, y):
    i = next(i for i, t in enumerate(a.texts) if t.startswith(old_prefix))
    p = a.texts[i].split(' ', 3)
    a.texts[i] = 'TEXT %d %d %s' % (x, y, p[3])


def drop_wire(a, w):
    w2 = (w[2], w[3], w[0], w[1])
    n = len(a.wires)
    a.wires = [v for v in a.wires if v != w and v != w2]
    assert len(a.wires) == n - 1, ('wire not found', w)


def drop_flag(a, x, y, name):
    n = len(a.flags)
    a.flags = [f for f in a.flags if not (f[0] == x and f[1] == y and f[2] == name)]
    assert len(a.flags) == n - 1, ('flag not found', x, y, name)


def shift_rows(a):
    for s in a.syms:
        if inside((s.x, s.y), ROWS):
            s.x += SHIFT
    assert not any(inside(w[:2], ROWS) != inside(w[2:], ROWS) for w in a.wires)
    a.wires = [(w[0] + SHIFT, w[1], w[2] + SHIFT, w[3]) if inside(w[:2], ROWS) else w for w in a.wires]
    for f in a.flags:
        if inside(f[:2], ROWS):
            f[0] += SHIFT
    for i, t in enumerate(a.texts):
        if inside(tpos(t), ROWS):
            p = t.split(' ', 3)
            a.texts[i] = 'TEXT %d %s %s' % (int(p[1]) + SHIFT, p[2], p[3])


def wire_verrgt0(d):
    a, W = d.a, d.W
    for Y in ROW_Y:                                    # the label stubs go; a tap from the bus takes their place
        drop_flag(a, 6048 + SHIFT, Y + 80, 'VerrGT0')
        drop_wire(a, (6144 + SHIFT, Y + 80, 6048 + SHIFT, Y + 80))
    W((5376, -6368), (5376, -6528), (6080, -6528))
    W((6080, -6640), (6080, -6528), (6080, -6320), (6080, -6000))
    for Y in ROW_Y:
        W((6080, Y + 80), (6144 + SHIFT, Y + 80))


def wire_out(d):
    a, W = d.a, d.W
    x2 = 6800 + SHIFT                                  # the second NAND's input pins
    drop_flag(a, 6736 + SHIFT, -6720 + 48, 'Out-')
    drop_wire(a, (x2, -6672, 6736 + SHIFT, -6672))
    drop_flag(a, 6736 + SHIFT, -6400 + 48, 'Out-')
    drop_wire(a, (x2, -6352, 6736 + SHIFT, -6352))
    drop_flag(a, 6752 + SHIFT, -6080 + 80, 'Out-')
    drop_wire(a, (x2, -6000, 6752 + SHIFT, -6000))
    # row 3's ena_out_3 output label moves down a step, under the Out- branch
    j = 6640 + SHIFT
    drop_wire(a, (j, -6000, j, -5936))
    drop_wire(a, (j, -5936, j + 32, -5936))
    drop_flag(a, j + 32, -5936, 'ena_out_3')
    W((j, -6000), (j, -5904), (j + 32, -5904))
    d.F(j + 32, -5904, 'ena_out_3', 'Out')
    # latch output: label moves onto the short horizontal, the wire continues down, along and up the right bus
    drop_flag(a, 5936, -6144, 'Out-')
    drop_wire(a, (5872, -6144, 5936, -6144))
    W((5872, -6144), (5904, -6144), (5936, -6144))
    d.F(5904, -6144, 'Out-')
    xr = 7680
    W((5936, -6144), (5936, -5840), (xr, -5840), (xr, -5952), (xr, -6416), (xr, -6736))
    for Y in ROW_Y[:2]:                                # into b from above
        W((xr, Y - 16), (x2 - 32, Y - 16), (x2 - 32, Y + 48), (x2, Y + 48))
    W((xr, -5952), (x2 - 32, -5952), (x2 - 32, -6000), (x2, -6000))   # row 3: into d from below


def redraw_sequencer(a, d):
    W, F, G = d.W, d.F, d.G
    pool = d.pool
    for n in ('U18', 'U28', 'C96'):
        s = next(s for s in a.syms if s.name == n)
        a.syms.remove(s)
        pool[n] = s
    drop_wire(a, (4688, -6384, 4560, -6384))
    a.wires = [w for w in a.wires if not (inside(w[:2], SEQ) and inside(w[2:], SEQ))]
    assert not any(inside(w[:2], SEQ) != inside(w[2:], SEQ) and w != (3472, -6352, 3264, -6352) for w in a.wires)
    a.flags = [f for f in a.flags if not inside(f[:2], SEQ)]
    move_text(a, 'TEXT 3456 -6624 ', 3456, -6704)
    move_text(a, 'TEXT 4560 -6624 ', 4560, -6704)
    # U18: CLK stays where the timeout's output wire arrives
    s = d.Pa('U18', 3472, -6384, 'R0')
    s.windows = {}
    W((3456, -6320), (3408, -6320))
    F(3408, -6320, 'Out-')                             # CKEN (active low)
    W((3472, -6256), (3408, -6256))
    F(3408, -6256, '4')                                # Reset <- Q3: counts 0, 1, 2 then resets
    ena = ['OUT_1_ENA', 'OUT_2_ENA', 'OUT_3_ENA']
    for k in range(3):                                 # Q0..Q2 -> S0..S2
        y = -6352 + 32 * k
        W((3600, y), (3728, y), (3856, y))
        F(3728, y, ena[k])
    W((3600, -6256), (3632, -6256))
    F(3632, -6256, '4')
    for k, n in enumerate(['5', '6', '7', '8', '9', '10']):
        y = -6224 + 32 * k
        W((3600, y), (3632, y))
        F(3632, y, n)
    # U28
    s = d.Pa('U28', 3856, -6448, 'R0')
    s.windows = {}
    W((3920, -6448), (3920, -6544), (3968, -6544), (4016, -6544))     # VCC + C96
    F(3968, -6544, '5V')
    d.Pa('C96', 4000, -6544, 'R0')
    G((4016, -6480))
    W((3856, -6224), (3824, -6224), (3824, -6192))                    # E (active low) on
    G((3824, -6192))
    G((3904, -6160))                                                  # GND
    G((3936, -6160))                                                  # VEE
    # channels: Verr1 on A1, Verr2 on A2, Verr3 on A4, the rest grounded
    for n, y in (('Verr1', -6384), ('Verr2', -6352), ('Verr3', -6288)):
        W((3984, y), (4080, y))
        F(4080, y, n, 'In')
    for y in (-6416, -6320):                                          # A0, A3
        W((3984, y), (4016, y))
        G((4016, y))
    for y in (-6256, -6224, -6192):                                   # A5..A7
        W((3984, y), (4016, y))
    W((4016, -6256), (4016, -6224), (4016, -6192), (4016, -6160))
    G((4016, -6160))
    # common A -> V_err, over the top of U28 to the comparators' V_err junction
    W((3856, -6416), (3792, -6416), (3792, -6608), (4240, -6608), (4688, -6608), (4688, -6384))
    F(4240, -6608, 'V_err')


def main():
    a = Asc(SRC)
    shift_rows(a)
    d = Draw(a, {})
    wire_verrgt0(d)
    wire_out(d)
    redraw_sequencer(a, d)
    if d.pool:
        raise SystemExit('unplaced: %s' % sorted(d.pool))
    orig = Asc(ORIG)
    orig.syms = [s for s in orig.syms if s.name != 'R14']
    probs, newnames = compare(orig, a)
    for p in probs:
        print('PROBLEM', p)
    if probs:
        if '--draft' in sys.argv:
            a.write(os.path.join(WORK, '_draft_v7.asc'), overwrite=True)
        raise SystemExit('electrical self-check failed; nothing written')
    if '--draft' in sys.argv:
        a.write(os.path.join(WORK, '_draft_v7.asc'), overwrite=True)
        print('draft written')
        return
    a.write(OUT)
    print('electrical self-check OK; wrote', OUT)


if __name__ == '__main__':
    main()
