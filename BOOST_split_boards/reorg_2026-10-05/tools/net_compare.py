"""Compare two KiCad netlists: parts (value, footprint, fields) and the pin partition (net names may differ).

    python net_compare.py ORIG.net NEW.net [--only REF,REF,...|--refs-from FILE.json:BOARD]

With --refs-from, only the parts assigned to BOARD in the board-assignment JSON are compared (a board project's
netlist holds one board only). Prints differences; exit code 1 if any.
"""
import sys, os, re, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import knet


def parts(path):
    t = open(path, encoding='utf-8').read()
    out = {}
    for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)(.*?)\n\t\t\)', t, re.S):
        body = m.group(2)
        val = re.search(r'\(value "([^"]*)"\)', body)
        fp = re.search(r'\(footprint "([^"]*)"\)', body)
        fields = dict(re.findall(r'\(field\s+\(name "([^"]+)"\)\s+"([^"]*)"\)', body))
        props = dict(re.findall(r'\(property\s+\(name "([^"]+)"\)\s+\(value "([^"]*)"\)', body))
        out[m.group(1)] = (val.group(1) if val else None, fp.group(1) if fp else None,
                           tuple(sorted(fields.items())), tuple(sorted((k, v) for k, v in props.items()
                                                                        if k not in ('Sheetname', 'Sheetfile'))))
    return out


def main():
    a, b = sys.argv[1], sys.argv[2]
    keep = None
    if '--refs-from' in sys.argv:
        path, board = sys.argv[sys.argv.index('--refs-from') + 1].rsplit(':', 1)
        asg = json.load(open(path))
        keep = {r for r, bd in asg.items() if bd == board}
    pa, pb = parts(a), parts(b)
    if keep is not None:
        pa = {r: v for r, v in pa.items() if r in keep}
    bad = 0
    for r in sorted(set(pa) | set(pb)):
        if r not in pb:
            print('only in ORIG:', r); bad += 1
        elif r not in pa:
            print('only in NEW:', r); bad += 1
        elif pa[r] != pb[r]:
            print('part differs:', r, pa[r], pb[r]); bad += 1
    _, _, na = knet.load(a)
    _, _, nb = knet.load(b)
    refs = set(pa) & set(pb)
    part = lambda nets: {frozenset((r, p) for r, p in v if r in refs) for v in nets.values()} - {frozenset()}
    sa, sb = part(na), part(nb)
    only_a, only_b = sa - sb, sb - sa
    for s in sorted(only_a, key=lambda s: sorted(s))[:15]:
        print('net only in ORIG:', sorted(s)[:8])
    for s in sorted(only_b, key=lambda s: sorted(s))[:15]:
        print('net only in NEW :', sorted(s)[:8])
    bad += len(only_a) + len(only_b)
    print('parts %d / %d, nets %d / %d, differences %d' % (len(pa), len(pb), len(sa), len(sb), bad))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
