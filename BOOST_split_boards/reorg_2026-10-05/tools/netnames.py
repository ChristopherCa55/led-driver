"""Shared label names for the LTspice nets, taken from the matching KiCad net (2026-10-05).

    python netnames.py IN.asc KICAD.net OUT.json

KiCad name rule (also used by relayout_kicad.py): a named net keeps its name; an auto name 'Net-(U19-OUTA)' becomes
'U19_OUTA' ('+' -> P, '-' -> N, 'Pad' dropped). An LTspice net is matched to the KiCad net with the same multiset of
part references on it (gate units U101A -> U101; KiCad net ties merged; parts present on one side only ignored).
OUT maps the LTspice net's sorted 'INST:pin' terminals (joined by '|') to the name.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ascgeo import Asc
import relayout_core as RC
import knet

KICAD_ONLY = re.compile(r'^(J9|J10|J11|NT\d+|H\d+|#.*)$')


def kname(n):
    m = re.match(r'^Net-\((.+)\)$', n)
    if not m:
        return n
    body = m.group(1)
    ref, _, pin = body.partition('-')
    pin = pin.replace('Pad', '')
    pin = pin.replace('+', 'P').replace('-', 'N')
    return re.sub(r'[^A-Za-z0-9_]', '_', '%s_%s' % (ref, pin))


def main():
    a = Asc(sys.argv[1])
    comps, kpins, knets = knet.load(sys.argv[2])
    # KiCad nets, net ties merged
    uf = RC.UF()
    for n in knets:
        uf.f(n)
    for r, ps in kpins.items():
        if r.startswith('NT'):
            ns = [n for _, n in ps]
            for n in ns[1:]:
                uf.u(ns[0], n)
    groups = collections.defaultdict(list)
    for n in knets:
        groups[uf.f(n)].append(n)
    ksig = collections.defaultdict(list)
    for root, ns in groups.items():
        refs = collections.Counter(r for n in ns for r, p in knets[n] if not KICAD_ONLY.match(r))
        name = sorted(ns, key=lambda n: (n.startswith('Net-('), n))[0]       # a real name first
        ksig[tuple(sorted(refs.elements()))].append(name)
    # LTspice nets
    m = RC.Model()
    for i, s in enumerate(a.syms):
        for name, x, y in a.pins(s):
            m.pins.append(RC.Pin(i, name, (x, y), (1, 0)))
    uf2 = RC.UF()
    pts = {p.pt for p in m.pins}
    for (ln, x1, y1, x2, y2) in a.wires:
        pts.add((x1, y1)); pts.add((x2, y2))
    for (ln, x, y, n) in a.flags:
        pts.add((x, y))
    for p in pts:
        uf2.f(p)
    byx, byy = collections.defaultdict(list), collections.defaultdict(list)
    for p in pts:
        byx[p[0]].append(p); byy[p[1]].append(p)
    for (ln, x1, y1, x2, y2) in a.wires:
        uf2.u((x1, y1), (x2, y2))
        if x1 == x2:
            for p in byx[x1]:
                if min(y1, y2) < p[1] < max(y1, y2):
                    uf2.u(p, (x1, y1))
        elif y1 == y2:
            for p in byy[y1]:
                if min(x1, x2) < p[0] < max(x1, x2):
                    uf2.u(p, (x1, y1))
    for (ln, x, y, n) in a.flags:      # flags join same-named nets
        uf2.u((x, y), ('name', n))
    term = collections.defaultdict(set)
    refs = collections.defaultdict(collections.Counter)
    for p in m.pins:
        inst = a.syms[p.owner]['attr'].get('InstName', '')
        root = uf2.f(p.pt)
        term[root].add('%s:%s' % (inst, p.pid))
        if not inst.startswith('SIM_'):
            refs[root][re.sub(r'^(U\d+)[A-H]$', r'\1', inst)] += 1
    out, unmatched, amb = {}, 0, 0
    for root, ts in term.items():
        sig = tuple(sorted(refs[root].elements()))
        cands = ksig.get(sig, [])
        if len(cands) == 1:
            out['|'.join(sorted(ts))] = kname(cands[0])
        elif len(cands) > 1:
            amb += 1
        else:
            unmatched += 1
    json.dump(out, open(sys.argv[3], 'w'), indent=0)
    print('LTspice nets %d: named from KiCad %d, ambiguous %d, unmatched %d' % (len(term), len(out), amb, unmatched))


if __name__ == '__main__':
    main()
