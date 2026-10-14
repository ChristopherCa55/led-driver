"""List the top-level items of a KiCad 10 schematic inside a box (symbols with fields, wires, labels, texts, junctions,
no-connects), for comparing two versions of a page by content rather than by text lines.

    python sch_items.py FILE.kicad_sch x1 y1 x2 y2 [--json OUT.json]
"""
import json, re, sys


def top_items(t):
    """yield (kind, text) for every child of (kicad_sch ...) at depth 1"""
    i = t.index('(kicad_sch') + 1
    depth = 0
    start = None
    k = i
    n = len(t)
    in_str = False
    while k < n:
        ch = t[k]
        if in_str:
            if ch == '\\':
                k += 2
                continue
            if ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == '(':
            depth += 1
            if depth == 1:
                start = k
        elif ch == ')':
            if depth == 1 and start is not None:
                blk = t[start:k + 1]
                yield re.match(r'\((\w+)', blk).group(1), blk
                start = None
            depth -= 1
            if depth < 0:
                break
        k += 1


def num(s):
    return round(float(s), 3)


def describe(kind, blk):
    if kind == 'symbol':
        lib = re.search(r'\(lib_id "([^"]+)"\)', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        mir = re.search(r'\n\t\t\(mirror (\w+)\)', blk)
        unit = re.search(r'\(unit (\d+)\)', blk)
        props = {}
        for m in re.finditer(r'\(property "([^"]+)" "([^"]*)"\s*\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)(.*?)\(effects(.*?)\n\t\t\t\)', blk, re.S):
            hide = '(hide yes)' in m.group(6) + m.group(7) or 'hide' in m.group(7)
            just = re.search(r'\(justify ([^)]+)\)', m.group(7))
            props[m.group(1)] = dict(text=m.group(2), at=[num(m.group(3)), num(m.group(4)), num(m.group(5))],
                                     hide=bool(hide), justify=just.group(1) if just else None)
        return dict(kind='symbol', lib=lib, at=[num(at.group(1)), num(at.group(2)), num(at.group(3))],
                    mirror=mir.group(1) if mir else None, unit=int(unit.group(1)) if unit else None,
                    ref=props.get('Reference', {}).get('text'), props=props,
                    uuid=re.search(r'\n\t\t\(uuid "([^"]+)"\)', blk).group(1))
    if kind == 'wire':
        pts = [[num(a), num(b)] for a, b in re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', blk)]
        return dict(kind='wire', pts=pts)
    if kind in ('global_label', 'label', 'hierarchical_label'):
        name = re.match(r'\(\w+ "([^"]*)"', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        just = re.search(r'\(justify ([^)]+)\)', blk)
        return dict(kind=kind, name=name, at=[num(at.group(1)), num(at.group(2)), num(at.group(3))],
                    justify=just.group(1) if just else None)
    if kind == 'text':
        txt = re.match(r'\(text "((?:[^"\\]|\\.)*)"', blk).group(1)
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
        just = re.search(r'\(justify ([^)]+)\)', blk)
        return dict(kind='text', text=txt, at=[num(at.group(1)), num(at.group(2)), num(at.group(3))],
                    justify=just.group(1) if just else None)
    if kind in ('junction', 'no_connect'):
        at = re.search(r'\(at ([-\d.]+) ([-\d.]+)\)', blk)
        return dict(kind=kind, at=[num(at.group(1)), num(at.group(2))])
    return None


def in_box(d, b):
    pts = d.get('pts') or [d['at'][:2]]
    return any(b[0] <= x <= b[2] and b[1] <= y <= b[3] for x, y in pts)


def items(path, box):
    t = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    out = []
    for kind, blk in top_items(t):
        d = describe(kind, blk)
        if d and in_box(d, box):
            out.append(d)
    return out


if __name__ == '__main__':
    a = sys.argv[1:]
    box = list(map(float, a[1:5]))
    res = items(a[0], box)
    if '--json' in a:
        json.dump(res, open(a[a.index('--json') + 1], 'w'), indent=1)
    for d in res:
        if d['kind'] == 'symbol':
            print('symbol %-6s unit %s at %s mirror %s %s' % (d['ref'], d['unit'], d['at'], d['mirror'], d['lib']))
            for k, v in d['props'].items():
                if not v['hide']:
                    print('    %s "%s" at %s justify %s' % (k, v['text'], v['at'], v['justify']))
        else:
            print(d)
