"""Prepare an 8-layer COPY of the power board for routing before the 6-layer conversion (text edit).

    python prep8.py IN.kicad_pcb OUT.kicad_pcb --zone NAME [--zone NAME ...] [--vias-from DRC.json]

--zone NAME        delete the zone with that (name ...) entirely (e.g. "5V plane", "GND planes")
--vias-from FILE   delete every via that FILE (a kicad-cli DRC JSON of the converted board) reports as
                   via_dangling, matched by position (to 0.005 mm) and net
"""
import json, re, sys

BS = chr(92)


def block_end(t, i):
    depth, j = 0, i
    while True:
        c = t[j]
        if c == '"':
            j += 1
            while t[j] != '"':
                j += 2 if t[j] == BS else 1
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1


a = sys.argv[1:]
src, dst = a[0], a[1]
zones = [a[i + 1] for i, x in enumerate(a) if x == '--zone']
drc = a[a.index('--vias-from') + 1] if '--vias-from' in a else None
t = open(src, encoding='utf-8', newline='').read().replace('\r\n', '\n')
for name in zones:
    k = t.index('(name "%s")' % name)
    s = t.rindex('\n\t(zone\n', 0, k) + 1
    e = block_end(t, s)
    t = t[:s] + t[e:].lstrip('\n')
    assert '(name "%s")' % name not in t
    print('deleted zone', name)
if drc:
    want = []
    for v in json.load(open(drc))['violations']:
        if v['type'] == 'via_dangling':
            it = v['items'][0]
            net = re.search(r'\[([^\]]+)\]', it['description']).group(1)
            want.append((it['pos']['x'], it['pos']['y'], net))
    n = 0
    for x, y, net in want:
        hit = None
        for m in re.finditer(r'\n\t\(via\n', t):
            s = m.start() + 1
            e = block_end(t, s)
            v = t[s:e]
            at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', v)
            if abs(float(at.group(1)) - x) < 0.005 and abs(float(at.group(2)) - y) < 0.005 and '(net "%s")' % net in v:
                hit = (s, e)
                break
        assert hit, (x, y, net)
        s, e = hit
        t = t[:s] + t[e:].lstrip('\n')
        n += 1
    print('deleted %d dangling vias' % n)
open(dst, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
print('wrote', dst)
