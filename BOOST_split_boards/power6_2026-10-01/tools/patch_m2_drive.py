"""Reroute M2's gate drive (Net-(D11--), B.Cu) back along its m2_source return (text edit of a board COPY).

    python patch_m2_drive.py IN.kicad_pcb OUT.kicad_pcb

Removes the diagonal from (68.81, 62.1) to (76.0, 68.2) that the 2026-10-02 edits introduced and replaces it with
the A6-style route: along y = 62.1 (0.75 mm below the m2_source track at y = 60.85), a step to y = 62.525 past the
m2_source jog at x = 74-75.5 (centred between that track and the GND via at (75.1, 63.3): 0.275 mm each side), then down x = 76.0 beside the m2_source link pour to rejoin at (76.0, 68.2).
Width 0.4 mm, as the user's route.
"""
import re, sys, uuid

OLD = [(68.81, 62.1, 70.51, 63.8), (70.51, 63.8, 70.65, 63.8), (70.65, 63.8, 71.4, 64.55), (71.4, 64.55, 71.4, 65.0),
       (71.4, 65.0, 71.15, 65.0), (71.15, 65.0, 71.12, 65.03), (71.12, 65.03, 73.09, 67.0), (73.09, 67.0, 74.8, 67.0),
       (74.8, 67.0, 76.0, 68.2)]
NEW = [(68.810661, 62.1), (73.5, 62.1), (73.925, 62.525), (75.675, 62.525), (76.0, 62.85), (76.0, 68.2)]
t = open(sys.argv[1], encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in t else '\n'
pat = re.compile(r'\t\(segment' + nl + r'\t\t\(start ([\d.]+) ([\d.]+)\)' + nl + r'\t\t\(end ([\d.]+) ([\d.]+)\)' + nl +
                 r'\t\t\(width ([\d.]+)\)' + nl + r'\t\t\(layer "B\.Cu"\)' + nl + r'\t\t\(net "Net-\(D11--\)"\)' + nl +
                 r'\t\t\(uuid "[^"]+"\)' + nl + r'\t\)' + nl)


def match(m):
    x0, y0, x1, y1 = (float(m.group(i)) for i in range(1, 5))
    for a in OLD:
        for s in (a, (a[2], a[3], a[0], a[1])):
            if all(abs(u - v) < 0.02 for u, v in zip((x0, y0, x1, y1), s)):
                return True
    return False


hits = [m for m in pat.finditer(t) if match(m)]
assert len(hits) == len(OLD), 'found %d of %d segments' % (len(hits), len(OLD))
for m in reversed(hits):
    t = t[:m.start()] + t[m.end():]
seg = ''.join(('\t(segment' + nl + '\t\t(start %s %s)' + nl + '\t\t(end %s %s)' + nl + '\t\t(width 0.4)' + nl +
               '\t\t(layer "B.Cu")' + nl + '\t\t(net "Net-(D11--)")' + nl + '\t\t(uuid "%s")' + nl + '\t)' + nl)
              % (a[0], a[1], b[0], b[1], uuid.uuid4()) for a, b in zip(NEW, NEW[1:]))
i = hits[0].start()
t = t[:i] + seg + t[i:]
open(sys.argv[2], 'w', encoding='utf-8', newline='').write(t)
print('removed %d segments, added %d' % (len(hits), len(NEW) - 1))
