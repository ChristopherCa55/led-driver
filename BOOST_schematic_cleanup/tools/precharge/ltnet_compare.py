"""Compare two LTspice netlists by connectivity: python ltnet_compare.py A.net B.net

Auto node names (N001...) are ignored: each net is the set of (element, pin position) it touches.  Reports elements
added/removed/changed (value or model text), nets whose pin sets differ, and named nets that changed name.
Directives (.ic/.tran/...) are compared as text.
"""
import re, sys

TWO = set('RCLDVIBEFGH')


def parse(path):
    raw = open(path, 'rb').read()
    try:
        t = raw.decode('utf-8')
    except UnicodeDecodeError:
        t = raw.decode('latin-1')
    elems, directives = {}, []
    for line in t.split('\n'):
        line = line.strip()
        if not line or line.startswith('*'):
            continue
        if line.startswith('.'):
            if not line.startswith(('.backanno', '.end')):
                directives.append(line)
            continue
        body = line.split(';')[0].split()
        name = body[0]
        k = name[0].upper()
        if k in TWO:
            n = 2
        elif k in 'SW':
            n = 4
        elif k == 'Q':
            n = 4 if len(body) > 5 and '=' not in body[4] and not re.match(r'^[A-Za-z]*NP$', body[4] or '') else 3
        elif k == 'M':
            n = 4
        elif k == 'A':
            n = 8
        elif k == 'X':
            toks = body[1:]
            while toks and '=' in toks[-1]:
                toks.pop()
            n = len(toks) - 1          # last non-parameter token is the subcircuit name
        else:
            raise SystemExit('unknown element ' + line)
        nodes = body[1:1 + n]
        rest = ' '.join(body[1 + n:])
        elems[name] = (nodes, rest)
    return elems, directives


def nets(elems):
    d = {}
    for name, (nodes, _) in elems.items():
        for i, nd in enumerate(nodes):
            d.setdefault(nd, set()).add((name, i))
    return {k: frozenset(v) for k, v in d.items()}


ea, da = parse(sys.argv[1])
eb, db = parse(sys.argv[2])
print('elements: %d -> %d' % (len(ea), len(eb)))
for n in sorted(set(ea) - set(eb)):
    print('  removed', n, ea[n])
for n in sorted(set(eb) - set(ea)):
    print('  added  ', n, eb[n])
for n in sorted(set(ea) & set(eb)):
    if ea[n][1] != eb[n][1]:
        print('  changed', n, repr(ea[n][1]), '->', repr(eb[n][1]))
na, nb = nets(ea), nets(eb)
common = set(ea) & set(eb)
restrict = lambda s: frozenset(p for p in s if p[0] in common)
ra = {k: restrict(v) for k, v in na.items() if restrict(v)}
rb = {k: restrict(v) for k, v in nb.items() if restrict(v)}
inv_b = {v: k for k, v in rb.items()}
auto = re.compile(r'^(N|P)\d{3}$')
diffs = 0
for k, v in sorted(ra.items()):
    if v in inv_b:
        kb = inv_b[v]
        if kb != k and not (auto.match(k) and auto.match(kb)):
            print('  net renamed %s -> %s' % (k, kb))
        continue
    diffs += 1
    best = max(rb.items(), key=lambda kv: len(kv[1] & v))
    print('  net %s (common pins) differs; closest in B: %s  only-A %s  only-B %s' % (
        k, best[0], sorted(v - best[1]), sorted(best[1] - v)))
print('nets among common elements differing: %d' % diffs)
sa, sb = set(da), set(db)
for x in sorted(sa - sb):
    print('  directive only in A:', x[:150])
for x in sorted(sb - sa):
    print('  directive only in B:', x[:150])
