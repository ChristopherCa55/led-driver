"""Find KiCad's pin transform empirically: for each candidate convention, count pins landing on wire ends, labels,
junctions or no-connects.  python pin_convention.py SCH"""
import sys, os, math, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ksch

sch = ksch.Sch(sys.argv[1])
pts = set()
for w in sch.wires:
    pts.add((ksch.rnd(w['x1']), ksch.rnd(w['y1'])))
    pts.add((ksch.rnd(w['x2']), ksch.rnd(w['y2'])))
for l in sch.labels:
    pts.add((ksch.rnd(l['x']), ksch.rnd(l['y'])))
for n in sch.noconn:
    pts.add((ksch.rnd(n['x']), ksch.rnd(n['y'])))


def place(s, p, rot_sign, mirror_first):
    px, py = p['x'], -p['y']

    def mir(px, py):
        if s['mirror'] == 'x':
            return px, -py
        if s['mirror'] == 'y':
            return -px, py
        return px, py

    def rot(px, py):
        a = math.radians(rot_sign * s['rot'])
        ca, sa = round(math.cos(a)), round(math.sin(a))
        return px * ca - py * sa, px * sa + py * ca

    if mirror_first:
        px, py = rot(*mir(px, py))
    else:
        px, py = mir(*rot(px, py))
    return ksch.rnd(s['x'] + px), ksch.rnd(s['y'] + py)


for rs in (1, -1):
    for mf in (True, False):
        # other symbols' pins count as connection points too (pin-to-pin and power symbols)
        allpins = collections.Counter()
        for s in sch.syms:
            lib = sch.lib.get(s['lib_id'])
            if lib:
                for p in lib['units'].get(0, []) + lib['units'].get(s['unit'], []):
                    allpins[place(s, p, rs, mf)] += 1
        hit = tot = 0
        bad = collections.Counter()
        for s in sch.syms:
            lib = sch.lib.get(s['lib_id'])
            if not lib:
                continue
            for p in lib['units'].get(0, []) + lib['units'].get(s['unit'], []):
                if p['hidden']:
                    continue
                tot += 1
                q = place(s, p, rs, mf)
                if q in pts or allpins[q] > 1:
                    hit += 1
                else:
                    bad[(s['rot'], s['mirror'])] += 1
        print('rot_sign %+d mirror_first %s: %d of %d pins on a connection point; misses by (rot, mirror) %s'
              % (rs, mf, hit, tot, dict(bad.most_common(8))))
