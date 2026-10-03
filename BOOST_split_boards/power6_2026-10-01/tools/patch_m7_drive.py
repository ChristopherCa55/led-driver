"""Reroute M7's R60.1 -> D2.1 drive link (Net-(D2--)) beside its m2_source return (text edit of a board COPY).

    python patch_m7_drive.py IN.kicad_pcb OUT.kicad_pcb

Removes the LX via at (73.776, 59.847) (no tracks; flashed F/In2/In3/In4), the straight R60.1 -> D2.1 link along
y = 58.3 on B.Cu and In4 and its two Net-(D2--) vias, and adds a 0.3 mm B.Cu route from the existing y = 59.85
track: along y = 59.8 (0.35 mm to the LX via hole at (73.7, 59.1), 0.40 mm to the m2_source track), then up into
D2.1.
"""
import re, sys, uuid

SEGS = {'B.Cu': [(72.271158, 58.506799, 72.48, 58.3), (72.48, 58.3, 74.07, 58.3), (74.07, 58.3, 74.76289, 58.991042)],
        'In4.Cu': [(72.55, 58.35, 72.6, 58.3), (72.6, 58.3, 74.164875, 58.3), (74.16, 58.3, 74.24, 58.38),
                   (74.24, 58.38, 74.38, 58.38), (74.377815, 58.377815, 74.65, 58.65)]}
VIAS = [('LX', 73.77639, 59.846563), ('Net-(D2--)', 72.55, 58.35), ('Net-(D2--)', 74.65, 58.65)]
NEW = [(70.95, 59.85), (71.0, 59.8), (74.3, 59.8), (74.76289, 59.337109), (74.76289, 58.991042)]
t = open(sys.argv[1], encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in t else '\n'
seg_re = re.compile(r'\t\(segment' + nl + r'\t\t\(start ([\d.]+) ([\d.]+)\)' + nl + r'\t\t\(end ([\d.]+) ([\d.]+)\)' + nl +
                    r'\t\t\(width [\d.]+\)' + nl + r'\t\t\(layer "([^"]+)"\)' + nl + r'\t\t\(net "Net-\(D2--\)"\)' + nl +
                    r'\t\t\(uuid "[^"]+"\)' + nl + r'\t\)' + nl)
via_re = re.compile(r'\t\(via' + nl + r'\t\t\(at ([\d.]+) ([\d.]+)\)' + nl + r'(?:\t\t[^\n]*' + nl + r')*?' +
                    r'\t\t\(net "([^"]+)"\)' + nl + r'\t\t\(uuid "[^"]+"\)' + nl + r'\t\)' + nl)


def seg_hit(m):
    x0, y0, x1, y1, ln = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), m.group(5)
    for a in SEGS.get(ln, []):
        for s in (a, (a[2], a[3], a[0], a[1])):
            if all(abs(u - v) < 0.02 for u, v in zip((x0, y0, x1, y1), s)):
                return True
    return False


def via_hit(m):
    return any(m.group(3) == n and abs(float(m.group(1)) - x) < 0.01 and abs(float(m.group(2)) - y) < 0.01
               for n, x, y in VIAS)


segs = [m for m in seg_re.finditer(t) if seg_hit(m)]
vias = [m for m in via_re.finditer(t) if via_hit(m)]
assert len(segs) == sum(len(v) for v in SEGS.values()), 'segments found %d' % len(segs)
assert len(vias) == len(VIAS), 'vias found %d' % len(vias)
first = min(m.start() for m in segs)
for m in sorted(segs + vias, key=lambda m: -m.start()):
    t = t[:m.start()] + t[m.end():]
add = ''.join(('\t(segment' + nl + '\t\t(start %s %s)' + nl + '\t\t(end %s %s)' + nl + '\t\t(width 0.3)' + nl +
               '\t\t(layer "B.Cu")' + nl + '\t\t(net "Net-(D2--)")' + nl + '\t\t(uuid "%s")' + nl + '\t)' + nl)
              % (a[0], a[1], b[0], b[1], uuid.uuid4()) for a, b in zip(NEW, NEW[1:]))
first = min(first, len(t))
i = t.rfind('\t(segment', 0, first + 1)
i = first if i < 0 else i
t = t[:i] + add + t[i:]
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(t)
print('removed %d segments and %d vias, added %d segments' % (len(segs), len(vias), len(NEW) - 1))
