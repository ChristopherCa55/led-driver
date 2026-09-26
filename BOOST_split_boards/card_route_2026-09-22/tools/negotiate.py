"""Negotiation by priority over whole routing passes (system Python).

usage: python negotiate.py COPPER.json TAG [MAX_PASSES] [extra route_card options...]

Pass k routes every net with the nets that failed in passes 1..k-1 moved to the front (route_card.py --first),
in the order they first failed. Stops at the first pass with no failed connection, or after MAX_PASSES (default 8).
Writes work/n_TAG_k.json / .log per pass, work/n_TAG_first.txt, and prints the failure count per pass; the pass
with the fewest failures is copied to work/n_TAG_best.json.
"""
import json, re, shutil, subprocess, sys

cop, tag = sys.argv[1], sys.argv[2]
maxp = int(sys.argv[3]) if len(sys.argv) > 3 else 8
extra = sys.argv[4:]
first = [x for x in open(sys.argv[sys.argv.index('--seed') + 1]).read().split()] if '--seed' in sys.argv else []
if '--seed' in sys.argv:
    i = sys.argv.index('--seed')
    del sys.argv[i:i + 2]
    extra = sys.argv[4:]
best = None
firstf = 'work/n_%s_first.txt' % tag
for k in range(1, maxp + 1):
    open(firstf, 'w').write('\n'.join(first) + '\n')
    out, log = 'work/n_%s_%d.json' % (tag, k), 'work/n_%s_%d.log' % (tag, k)
    cmd = [sys.executable, '-u', 'tools/route_card.py', cop, out, '--match', '../card_2026-09-17/work/place_c2.json',
           '--first', firstf] + extra
    with open(log, 'w') as fh:
        subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
    txt = open(log).read()
    failed = []
    for line in txt.splitlines():
        if not line.startswith('FAIL '):
            continue
        tok = line.split()
        n = tok[1][:-1] if tok[1].endswith(':') else tok[2]      # 'FAIL net: island ..' or 'FAIL tag net pad -> ..'
        if n not in failed:
            failed.append(n)
    nfail = json.load(open(out))['failures']
    print('pass %d: %d failed connections in %d nets: %s' % (k, nfail, len(failed), ' '.join(failed)), flush=True)
    if best is None or nfail < best[0]:
        best = (nfail, k)
        shutil.copy(out, 'work/n_%s_best.json' % tag)
    if nfail == 0:
        break
    first += [n for n in failed if n not in first]
print('best pass %d with %d failed connections -> work/n_%s_best.json' % (best[1], best[0], tag))
