"""Remove the vias and track stubs a kicad-cli DRC JSON reports as via_dangling / track_dangling (text edit).

    python drop_dangling.py BOARD.kicad_pcb DRC.json

Vias are matched by position (0.005 mm) and net; a dangling track by its net, layer and an end point at the reported
position (0.005 mm). Only what the DRC names is removed.
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


p, drc = sys.argv[1], sys.argv[2]
t = open(p, encoding='utf-8', newline='').read().replace('\r\n', '\n')
todo = []
for v in json.load(open(drc))['violations']:
    if v['type'] in ('via_dangling', 'track_dangling'):
        it = v['items'][0]
        net = re.search(r'\[([^\]]+)\]', it['description']).group(1)
        lay = re.search(r' on (\S+\.Cu)', it['description'])
        todo.append((v['type'], it['pos']['x'], it['pos']['y'], net, lay.group(1) if lay else None))
n = {'via_dangling': 0, 'track_dangling': 0}
for kind, x, y, net, lay in todo:
    hit = None
    tag = '\n\t(via\n' if kind == 'via_dangling' else '\n\t(segment\n'
    for m in re.finditer(re.escape(tag), t):
        s = m.start() + 1
        e = block_end(t, s)
        b = t[s:e]
        if '(net "%s")' % net not in b:
            continue
        if kind == 'via_dangling':
            at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', b)
            ok = abs(float(at.group(1)) - x) < 0.005 and abs(float(at.group(2)) - y) < 0.005
        else:
            if '(layer "%s")' % lay not in b:
                continue
            ends = re.findall(r'\((?:start|end) ([\d.\-]+) ([\d.\-]+)\)', b)
            ok = any(abs(float(a) - x) < 0.005 and abs(float(c) - y) < 0.005 for a, c in ends)
        if ok:
            hit = (s, e)
            break
    assert hit, (kind, x, y, net, lay)
    s, e = hit
    t = t[:s] + t[e:].lstrip('\n')
    n[kind] += 1
open(p, 'w', encoding='utf-8', newline='').write(t.replace('\n', '\r\n'))
print('removed %d dangling vias, %d dangling tracks' % (n['via_dangling'], n['track_dangling']))
