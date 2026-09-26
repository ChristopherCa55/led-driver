"""Diff two KiCad s-expression netlists: components (value, footprint) and pin -> net (system Python).

usage: python netdiff.py OLD.net NEW.net
"""
import re, sys


def sexpr(text):
    tok = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+', text)
    stack, cur = [], []
    for t in tok:
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur[0]


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def val(node, key):
    f = find(node, key)
    return f[0][1] if f and len(f[0]) > 1 else None


def parse(path):
    root = sexpr(open(path, encoding='utf8').read())
    comps, pins = {}, {}
    for c in find(find(root, 'components')[0], 'comp'):
        comps[val(c, 'ref')] = (val(c, 'value'), val(c, 'footprint'))
    for n in find(find(root, 'nets')[0], 'net'):
        name = val(n, 'name')
        for nd in find(n, 'node'):
            pins[(val(nd, 'ref'), val(nd, 'pin'))] = name
    return comps, pins


c1, p1 = parse(sys.argv[1])
c2, p2 = parse(sys.argv[2])
print('components %d -> %d, connected pins %d -> %d' % (len(c1), len(c2), len(p1), len(p2)))
cc = [(k, c1.get(k), c2.get(k)) for k in sorted(set(c1) | set(c2)) if c1.get(k) != c2.get(k)]
pc = [(k, p1.get(k), p2.get(k)) for k in sorted(set(p1) | set(p2)) if p1.get(k) != p2.get(k)]
print('component changes (%d):' % len(cc))
for x in cc:
    print('  ', x)
print('pin-net changes (%d):' % len(pc))
for x in pc:
    print('  %s.%s: %s -> %s' % (x[0][0], x[0][1], x[1], x[2]))
