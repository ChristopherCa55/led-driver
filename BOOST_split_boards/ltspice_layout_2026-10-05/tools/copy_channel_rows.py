"""Copy the user's channel-1 section (LED current limit, headroom servo, voltage error amp) to channels 2 and 3.

    python copy_channel_rows.py      work/BOOST_revised_v4.asc -> work/BOOST_revised_v5.asc

The user's choices (2026-10-07):
  - channels 2 and 3 go to the right of channel 1, same height, in order;
  - the explanation comments stay on channel 1 only. A copy gets its titles (channel number changed; the error-amp
    title keeps the user's wording), "same as channel 1", the simulation-only notes on its SIM parts, the PWM-duty
    line with its own parameter, and the "U26x: one of the 4 pots inside U26" note.
Every part, wire, label and text window is placed at the same offset as in channel 1. A 2-pin part netlisted the
other way round from its channel-1 twin is drawn turned 180 degrees on the same spot. Parts that exist only in
channel 1 (C23, the 4066's bypass) leave no stub in the copies. C104 (a logic-chip bypass that sat in the way) moves
to the logic bypass row.
"""
import os, sys, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, on_interior, HANDOFF
from layout_lib import strip_old, name_cut_groups, compare, partition, RENAME
from copy_driver_layout import inv_xf, world_box, close, JUSTS, FLIP, NET, inside
from board_caps import remove_with_stubs, place_like, Ghost

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised_v4.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v5.asc')
ORIG = os.path.join(HANDOFF, 'reference', 'LTspice_original', 'BOOST.asc')

CH = {
    1: 'SIM_LED1 M10 R52 U11 R56 C45 C33 SIM_IREF1 R29 R54 C100 U26A R94 R95 U106C U24 C67 R98 R96 R97 C68 D26 C32 '
       'SIM_VREF1 R101 C103 R6 C46 R9 R8 R2 R3 U3 R27 R28 C13 C66',
    2: 'SIM_LED2 M9 R53 U12 R50 C44 C34 SIM_IREF2 R30 R55 C101 U26B R25 R36 U106B U23 C64 R93 R91 R92 C65 D25 C38 '
       'SIM_VREF2 R100 C93 R33 C43 R35 R34 R31 R32 U7 R37 R38 C11 C36',
    3: 'SIM_LED3 M8 R7 U6 R22 C41 C35 SIM_IREF3 R57 R58 C102 U26C R87 R88 U106A U22 C49 R90 R44 R89 C59 D23 C63 '
       'SIM_VREF3 R77 C47 R41 C42 R43 R42 R39 R40 U13 R45 R46 C10 C37',
}
CH1_ONLY = ['C23']                       # drawn in channel 1's region, no twin in channels 2 and 3
REGION = (-3100, -3700, -150, -1900)     # channel 1's drawing (U26E and its parts lie below it and stay)
DX = {2: 4224, 3: 8448}
GLOBAL = {'0', '5V', 'analog_5V', '12V', 'Vin'}


def all_nodes():
    nodes = {}
    for l in open(NET, encoding='utf-8').read().split('\n'):
        t = l.split(';')[0].split()
        if not t or t[0][0] in '*.':
            continue
        name = t[0].split('§')[-1]
        k = t[0][0]
        if k in 'RCDLV':
            nodes[name] = t[1:3]
        elif k == 'X':
            body = t[1:]
            while body and '=' in body[-1]:
                body.pop()
            nodes[name] = body[:-1]
    return nodes


def channel_map(nodes, t_parts, p_parts):
    nmap = {g: g for g in GLOBAL}
    pairs = list(zip(t_parts, p_parts))
    for tn, pn in pairs:                                  # multi-pin parts fix the map
        if len(nodes[tn]) > 2:
            for x, y in zip(nodes[tn], nodes[pn]):
                assert nmap.setdefault(x, y) == y, (tn, pn, x, y, nmap[x])
    changed = True
    while changed:                                        # 2-pin parts: extend from a known end
        changed = False
        for tn, pn in pairs:
            if len(nodes[tn]) != 2:
                continue
            (a, b), (c, d) = nodes[tn], nodes[pn]
            for (x1, y1), (x2, y2) in (((a, c), (b, d)), ((a, d), (b, c))):
                if nmap.get(x1) == y1 and x2 not in nmap:
                    nmap[x2] = y2
                    changed = True
                elif nmap.get(x2) == y2 and x1 not in nmap:
                    nmap[x1] = y1
                    changed = True
    return nmap


def trim_points(a, pts):
    """remove dead-end wires and lone ground flags reaching out from points where a (missing) part's pins would be"""
    todo = list(pts)
    while todo:
        p = todo.pop()
        ends = [w for w in a.wires if (w[0], w[1]) == p or (w[2], w[3]) == p]
        pins = {(x, y) for t in a.syms for _, x, y in a.pins(t)}
        flags = [f for f in a.flags if (f[0], f[1]) == p]
        if p in pins or any(on_interior(p, w) for w in a.wires) or len(ends) > 1:
            continue
        if any(f[2] != '0' for f in flags):
            continue
        for f in flags:
            a.flags.remove(f)
        if ends:
            w = ends[0]
            a.wires.remove(w)
            todo.append((w[2], w[3]) if (w[0], w[1]) == p else (w[0], w[1]))


def text_for_copy(t, k):
    """channel-1 TEXT line -> the line for channel k, or None (explanations stay on channel 1)"""
    p = t.split(' ', 5)
    body = p[5][1:]
    new = None
    if body == 'CH1 LED CURRENT LIMIT':
        new = 'CH%d LED CURRENT LIMIT' % k
    elif body == 'CH1 HEADROOM SERVO':
        new = 'CH%d HEADROOM SERVO' % k
    elif body == 'Channel 1 output-voltage error amplifier, Vout_1 -> Verr1':
        new = 'Channel %d output-voltage error amplifier, Vout_%d -> Verr%d' % (k, k, k)
    elif body.startswith('actual led diode'):
        new = body
    elif body.startswith('simulation only - not on the PCB'):
        new = 'simulation only - not on the PCB'
    elif body.startswith('PWM duty = IREF1_DUTY'):
        new = body.replace('IREF1_DUTY', 'IREF%d_DUTY' % k)
    elif body.startswith('0-5V PWM to set minimum voltage reference'):
        new = 'simulation only - not on the PCB'
    elif body.startswith('U26A: one of the 4 pots'):
        new = body.replace('U26A', 'U26' + {2: 'B', 3: 'C'}[k])
    if new is None:
        return None
    y = int(p[2])
    if body.startswith('PWM duty'):
        y = -2024          # one line under its single-line "simulation only" note (channel 1's has two lines)
    elif body.startswith('U26A: one of'):
        y = -1968          # just under the pot, clear of the PWM-duty line
    return 'TEXT %d %d %s %s ;%s' % (int(p[1]) + DX[k], y, p[3], p[4], new)


def main():
    a = Asc(SRC)
    nodes = all_nodes()
    t_parts = CH[1].split()

    # C104 out of the way, into the logic bypass row (left end, the 5V label moves one step further left)
    c104 = remove_with_stubs(a, 'C104')
    for f in [f for f in a.flags if f[2] == '5V']:          # its 5V label is left touching nothing: drop it
        p = (f[0], f[1])
        if not any(p in ((w[0], w[1]), (w[2], w[3])) or on_interior(p, w) for w in a.wires) and \
                not any(p == (x, y) for t in a.syms for _, x, y in a.pins(t)):
            a.flags.remove(f)
            print('dropped the 5V label left alone at', p)
    c94 = next(s for s in a.syms if s.name == 'C94')
    a94 = a.pin(c94, 'A')
    flag5 = next(f for f in a.flags if f[2] == '5V' and f[1] == a94[1] and f[0] < a94[0] - 200)
    px = flag5[0]
    place_like(a, c104, Ghost(c94, px - a94[0], 0), Ghost(c94, px - a94[0], 0), False)
    a.syms.append(c104)
    a.flags.append([px, a94[1] + 64, '0', None])
    flag5[0] = px - 64
    a.wires.append((px - 64, a94[1], px, a94[1]))

    # the target regions must be empty
    for k, dx in DX.items():
        r = (REGION[0] + dx, REGION[1], REGION[2] + dx, REGION[3])
        busy = [s.name for s in a.syms if inside((s.x, s.y), r)] + \
               [w for w in a.wires if inside((w[0], w[1]), r) or inside((w[2], w[3]), r)] + \
               [f for f in a.flags if inside((f[0], f[1]), r)] + \
               [t[:40] for t in a.texts if inside((int(t.split()[1]), int(t.split()[2])), r)]
        if busy:
            raise SystemExit('channel %d area is not empty: %s' % (k, busy[:10]))

    # take channels 2 and 3 out of the old drawing
    remove = set(CH[2].split()) | set(CH[3].split())
    pool, trimmed = strip_old(a, remove)
    by = a.by()

    t_wires = [w for w in a.wires if inside((w[0], w[1]), REGION) and inside((w[2], w[3]), REGION)]
    t_flags = [f for f in a.flags if inside((f[0], f[1]), REGION)]
    t_texts = [t for t in a.texts if inside((int(t.split()[1]), int(t.split()[2])), REGION)]
    only_pins = [(x, y) for n in CH1_ONLY for _, x, y in a.pins(by[n])]

    for k in (2, 3):
        dx = DX[k]
        p_parts = CH[k].split()
        nmap = channel_map(nodes, t_parts, p_parts)
        for w in t_wires:
            a.wires.append((w[0] + dx, w[1], w[2] + dx, w[3]))
        for f in t_flags:
            name = f[2] if f[2] in GLOBAL else nmap.get(f[2])
            if name is None:
                raise SystemExit('no channel-%d name for label %s' % (k, f[2]))
            a.flags.append([f[0] + dx, f[1], name, f[3]])
        for t in t_texts:
            nt = text_for_copy(t, k)
            if nt:
                a.texts.append(nt)
        # "same as channel 1" under the current-limit title
        title = next(t for t in t_texts if t.endswith(';CH1 LED CURRENT LIMIT')).split(' ', 5)
        a.texts.append('TEXT %d %d Left 2 ;same as channel 1' % (int(title[1]) + dx, int(title[2]) + 48))
        for tn, pn in zip(t_parts, p_parts):
            ts = by[tn]
            s = pool.pop(pn)
            mapped = [nmap.get(x, x) for x in nodes[tn]]
            flip = len(nodes[tn]) == 2 and mapped == nodes[pn][::-1] and mapped != nodes[pn]
            if not flip and mapped != nodes[pn]:
                raise SystemExit('%s does not correspond to %s: %s vs %s' % (pn, tn, mapped, nodes[pn]))
            g = Ghost(ts, dx, 0)
            place_like(a, s, g, g, flip)
            a.syms.append(s)
            if flip:
                print('channel %d: %s turned 180 (pins netlisted the other way round from %s)' % (k, pn, tn))
        trim_points(a, [(x + dx, y) for x, y in only_pins])
    if pool:
        raise SystemExit('unplaced: %s' % sorted(pool))

    orig = Asc(ORIG)
    orig.syms = [s for s in orig.syms if s.name != 'R14']
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


if __name__ == '__main__':
    main()
