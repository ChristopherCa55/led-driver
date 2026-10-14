"""Apply the 2026-10-07 review edits to the user's BOOST_revised.asc and write a PREVIEW copy.

    python review_edits.py            -> work/BOOST_revised_v2.asc  (the user's file is not touched)

The user approved:
  - horizontal Vin labels at D28-D30;
  - moving "op amp will try..." next to U11, and nudging "digital potentiometer..." clear of U26A's CODE text;
  - hiding SIM_IREF1's PULSE text, with a one-line note instead;
  - brief comments in the user's wording (R1, U25, L1, M1, D19, M7/M2 and the other two pairs, R101/C103, U26A).
The section titles are placed here only to be SEEN; the user approves them after looking.

Every new text is placed at the first candidate spot that is clear of all other text, symbols, labels and wires by
16 units, using the same text-size model as the layout checker.
"""
import os, sys, json, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from ascmodel import Asc, HANDOFF
sys.path.insert(0, os.path.join(HANDOFF, 'tools'))
from asc_layout_check import Schematic, attr_texts, text_box, flag_box, rects_overlap, rect_gap, seg_hits_rect
from collections import defaultdict

WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
SRC = os.path.join(WORK, 'BOOST_revised.asc')
OUT = os.path.join(WORK, 'BOOST_revised_v2.asc')
TM = json.load(open(os.path.join(HANDOFF, 'blocks.json')))['text_metrics']
CLEAR = 16


def sign(v):
    return (v > 0) - (v < 0)


def obstacles(path):
    s = Schematic(path)
    s.dir = WORK                      # symbols live beside the real file, not the temp copy
    ends = defaultdict(list)
    for w in s.wires:
        ends[(w[0], w[1])].append((sign(w[2] - w[0]), sign(w[3] - w[1])))
        ends[(w[2], w[3])].append((sign(w[0] - w[2]), sign(w[1] - w[3])))
    boxes = []
    for n, sy in s.by.items():
        boxes.append(s.body(sy))
        boxes += [b for b, _ in attr_texts(s, sy, TM)]
    for t in s.texts:
        b = text_box(t['x'], t['y'], t['just'], t['size'], t['body'][1:], TM)
        if b:
            boxes.append(b)
    for fl in s.flags:
        boxes.append(flag_box(fl, s, TM, ends)[0])
    return boxes, s.wires


def free(box, boxes, wires):
    grown = (box[0] - CLEAR, box[1] - CLEAR, box[2] + CLEAR, box[3] + CLEAR)
    if any(rects_overlap(grown, b) for b in boxes):
        return False
    return not any(seg_hits_rect(w, grown) for w in wires)


def place(a, body, cands, size=2, just='Left', label=''):
    """add ';body' at the first free candidate (x, y); returns the spot used"""
    tmp = os.path.join(tempfile.gettempdir(), 'review_place.asc')
    a.write(tmp, overwrite=True)
    boxes, wires = obstacles(tmp)
    for (x, y) in cands:
        b = text_box(x, y, just, size, body, TM)
        if free(b, boxes, wires):
            a.texts.append('TEXT %d %d %s %d ;%s' % (x, y, just, size, body))
            print('placed %-28s at (%d, %d)' % (label or body[:28], x, y))
            return (x, y)
    # none of the preferred spots is clear: take the clear spot nearest the first one (16-unit grid, within 480)
    x0, y0 = cands[0]
    spots = sorted(((dx, dy) for dx in range(-480, 481, 16) for dy in range(-480, 481, 16)),
                   key=lambda d: d[0] ** 2 + 2 * d[1] ** 2)
    for dx, dy in spots:
        x, y = x0 + dx, y0 + dy
        if free(text_box(x, y, just, size, body, TM), boxes, wires):
            a.texts.append('TEXT %d %d %s %d ;%s' % (x, y, just, size, body))
            print('placed %-28s at (%d, %d)  (nearest clear spot, moved %d,%d)' % (label or body[:28], x, y, dx, dy))
            return (x, y)
    raise SystemExit('no free spot for: ' + body)


def main():
    a = Asc(SRC)
    by = a.by()

    # 1. Vin labels at the pre-charge diodes: put each on a short horizontal stub so LTspice writes it horizontally
    for d in ('D28', 'D29', 'D30'):
        ax, ay = a.pin(by[d], '+')
        for f in a.flags:
            if f[2] == 'Vin' and f[0] == ax and f[1] < ay and any(w[0] == w[2] == ax and {w[1], w[3]} == {f[1], ay}
                                                                  for w in a.wires):
                x, y = f[0], f[1]
                a.wires.append((x - 64, y, x, y))
                f[0] = x - 64
                print('Vin label at %s moved onto a horizontal stub at (%d, %d)' % (d, x - 64, y))
                break
        else:
            raise SystemExit('Vin flag above %s not found' % d)

    # 2. move "op amp will try..." from the bottom of the block to directly under U11 (two lines, same words)
    old = ';op amp will try to make its output match the reference current'
    a.texts = [t for t in a.texts if not t.endswith(old)]
    ux, uy = by['U11'].x, by['U11'].y
    place(a, 'op amp will try to make its output\\nmatch the reference current',
          [(ux, uy + 304), (ux, uy + 320), (ux - 32, uy + 304), (ux + 32, uy + 320)], just='Center',
          label='op amp note under U11')

    # 3. nudge "digital potentiometer..." down, clear of U26A's CODE={POT1_CODE}
    for i, t in enumerate(a.texts):
        if t.endswith(';digital potentiometer \\nto control current'):
            p = t.split(' ', 5)
            a.texts[i] = 'TEXT %s %d %s %s %s' % (p[1], int(p[2]) + 32, p[3], p[4], p[5])
            print('nudged "digital potentiometer" down 32')

    # 4. hide SIM_IREF1's PULSE value; one short note instead
    s = by['SIM_IREF1']
    wx, wy, j, sz = s.windows.get(3, (0, 0, 'Left', 2))
    s.windows[3] = (wx, wy, 'Invisible', sz)
    place(a, 'PWM duty = IREF1_DUTY/256 (.param)', [(-944, -2008), (-944, -1992), (-944, -1976)],
          label='SIM_IREF1 duty note')

    # 5. brief comments (the user's wording)
    def near(part, dxdy):
        q = by[part]
        return [(q.x + dx, q.y + dy) for dx, dy in dxdy]
    place(a, '1 mOhm shunt:\\nmeasures inductor current', near('R1', [(40, 136), (40, 152), (40, 168)]),
          just='Center', label='R1')
    place(a, 'amplifies R1 voltage by 100x', near('U25', [(80, 112), (80, 128), (80, 144), (80, -80)]), label='U25')
    place(a, 'inductor', near('L1', [(-40, -64), (-40, -80), (16, -64)]), just='Center', label='L1')
    place(a, 'low side switch', near('M1', [(64, 112), (64, 128), (64, 144)]), label='M1')
    place(a, 'clamps LX spikes', near('D19', [(-52, -32), (-52, -16), (-52, -48)]), just='Right', label='D19')
    for k, (q1, q2) in enumerate((('M7', 'M2'), ('M6', 'M3'), ('M5', 'M4')), 1):
        mx = (by[q1].x + by[q2].x) // 2
        my = by[q1].y
        place(a, 'back-to-back switch:\\nconnects LX to output %d' % k,
              [(mx, my + 152), (mx, my + 168), (mx, my + 184), (mx - 32, my + 168)], just='Center',
              label='%s/%s' % (q1, q2))
    rx = (by['R101'].x + by['C103'].x) // 2
    place(a, 'filters the PWM to DC', [(rx, by['R101'].y - 112), (rx, by['R101'].y - 128), (rx, by['C103'].y + 128),
                                       (rx, by['C103'].y + 144)], just='Center', label='R101/C103')
    place(a, 'U26A: one of the 4 pots inside U26 (MCP4451)',
          near('U26A', [(40, 112), (40, 128), (40, 144), (40, 160)]), label='U26A')

    # 6. section titles: PREVIEW ONLY, for the user to judge
    place(a, 'INPUT SIDE', [(-3088, -5280), (-3088, -5296), (-3088, -5312)], size=3, label='title INPUT SIDE')
    for k, q in enumerate(('M7', 'M6', 'M5'), 1):
        x0, y0 = by[q].x, by[q].y
        place(a, 'OUTPUT %d' % k, [(x0 - 320, y0 - 96), (x0 - 320, y0 - 112), (x0 - 288, y0 - 128),
                                   (x0 - 320, y0 - 144)], size=3, label='title OUTPUT %d' % k)
    place(a, 'CH1 LED CURRENT LIMIT', [(-2776, -2768), (-2776, -2784), (-2800, -2800)], size=3,
          label='title CH1 LED CURRENT LIMIT')
    place(a, 'CH1 HEADROOM SERVO', [(-1488, -2768), (-1488, -2784), (-1488, -2800), (-1520, -2816)], size=3,
          label='title CH1 HEADROOM SERVO')

    a.write(OUT)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
