"""What changed between two KiCad 10 board files? Tracks, arcs and vias added / removed (x, y, layer, net, width),
footprints added / removed / moved / flipped, and footprint text (Reference / Value) changes. Zone fills are ignored
(they follow the copper); zone OUTLINES are compared.

    python pcb_diff.py BEFORE.kicad_pcb AFTER.kicad_pcb [--json OUT.json] [--md OUT.md] [--title TEXT]
"""
import json, re, sys

SEG = re.compile(r'\n\t\((segment|arc)\r?\n\t\t\(start ([-\d.]+) ([-\d.]+)\)\r?\n(?:\t\t\(mid ([-\d.]+) ([-\d.]+)\)\r?\n)?'
                 r'\t\t\(end ([-\d.]+) ([-\d.]+)\)\r?\n\t\t\(width ([\d.]+)\)\r?\n\t\t\(layer "([^"]+)"\)\r?\n'
                 r'\t\t\(net "([^"]*)"\)')
VIA = re.compile(r'\n\t\(via\r?\n\t\t\(at ([-\d.]+) ([-\d.]+)\)\r?\n\t\t\(size ([\d.]+)\)\r?\n\t\t\(drill ([\d.]+)\)'
                 r'\r?\n\t\t\(layers "([^"]+)" "([^"]+)"\)(.*?)\(net "([^"]*)"\)', re.S)
FP = re.compile(r'\n\t\(footprint "([^"]+)"\r?\n(.*?)\r?\n\t\)(?=\r?\n)', re.S)
ZONE = re.compile(r'\n\t\(zone\r?\n(.*?)\r?\n\t\)(?=\r?\n)', re.S)


def r4(v):
    return round(float(v), 4)


def parse(path):
    t = open(path, encoding='utf-8', newline='').read()
    segs = {}
    for m in SEG.finditer(t):
        k = (m.group(1), r4(m.group(2)), r4(m.group(3)), r4(m.group(6)), r4(m.group(7)), r4(m.group(8)), m.group(9),
             m.group(10))
        segs[k] = segs.get(k, 0) + 1
    vias = {}
    for m in VIA.finditer(t):
        k = (r4(m.group(1)), r4(m.group(2)), r4(m.group(3)), r4(m.group(4)), m.group(8))
        vias[k] = vias.get(k, 0) + 1
    fps = {}
    for m in FP.finditer(t):
        b = m.group(2)
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ?([-\d.]*)\)', b)
        side = re.search(r'(?:^|\n)\t\t\(layer "([^"]+)"\)', b).group(1)
        val = re.search(r'\(property "Value" "([^"]*)"', b).group(1)
        texts = {}
        for p in re.finditer(r'\(property "(Reference|Value)" "([^"]*)"\r?\n\t\t\t\(at ([^)]*)\)\r?\n\t\t\t'
                             r'(?:\(unlocked yes\)\r?\n\t\t\t)?\(layer "([^"]+)"\)(\r?\n\t\t\t\(hide yes\))?', b):
            texts[p.group(1)] = (p.group(2), p.group(3), p.group(4), bool(p.group(5)))
        fps[ref] = dict(lib=m.group(1), x=r4(at.group(1)), y=r4(at.group(2)), rot=r4(at.group(3) or 0), side=side,
                        value=val, texts=texts)
    zones = {}
    for m in ZONE.finditer(t):
        b = m.group(1)
        b = re.sub(r'\(filled_polygon.*', '', b, flags=re.S)
        name = (re.search(r'\(net_name "([^"]*)"\)|\(net "([^"]*)"\)', b) or [None])[0]
        lay = re.search(r'\(layers? ([^)]*)\)', b).group(1)
        pts = tuple(re.findall(r'\(xy ([-\d.]+) ([-\d.]+)\)', re.search(r'\(polygon.*', b, re.S).group(0)))
        zones[(name, lay, pts)] = zones.get((name, lay, pts), 0) + 1
    return segs, vias, fps, zones


def diff_counts(a, b):
    rem = [k for k in a for _ in range(a[k] - b.get(k, 0)) if a[k] > b.get(k, 0)]
    add = [k for k in b for _ in range(b[k] - a.get(k, 0)) if b[k] > a.get(k, 0)]
    return sorted(rem), sorted(add)


def main():
    a = sys.argv[1:]
    sa, va, fa, za = parse(a[0])
    sb, vb, fb, zb = parse(a[1])
    out = dict(before=a[0], after=a[1])
    rs, ads = diff_counts(sa, sb)
    rv, av = diff_counts(va, vb)
    rz, az = diff_counts(za, zb)
    key = ('kind', 'x0', 'y0', 'x1', 'y1', 'width', 'layer', 'net')
    out['tracks_removed'] = [dict(zip(key, k)) for k in rs]
    out['tracks_added'] = [dict(zip(key, k)) for k in ads]
    vkey = ('x', 'y', 'size', 'drill', 'net')
    out['vias_removed'] = [dict(zip(vkey, k)) for k in rv]
    out['vias_added'] = [dict(zip(vkey, k)) for k in av]
    out['zones_removed'] = [dict(net=k[0], layers=k[1], points=len(k[2])) for k in rz]
    out['zones_added'] = [dict(net=k[0], layers=k[1], points=len(k[2])) for k in az]
    fpc = []
    for ref in sorted(set(fa) | set(fb)):
        x, y = fa.get(ref), fb.get(ref)
        if x is None or y is None:
            fpc.append(dict(ref=ref, change='added' if x is None else 'removed', **(y or x)))
            continue
        ch = []
        if (x['x'], x['y']) != (y['x'], y['y']):
            ch.append('moved (%g, %g) -> (%g, %g)' % (x['x'], x['y'], y['x'], y['y']))
        if x['rot'] != y['rot']:
            ch.append('rotated %g -> %g' % (x['rot'], y['rot']))
        if x['side'] != y['side']:
            ch.append('side %s -> %s' % (x['side'], y['side']))
        if x['value'] != y['value']:
            ch.append('value %s -> %s' % (x['value'], y['value']))
        for k in ('Reference', 'Value'):
            if x['texts'].get(k) != y['texts'].get(k) and k in x['texts'] and k in y['texts']:
                o, n = x['texts'][k], y['texts'][k]
                if o[1:] != n[1:]:
                    ch.append('%s text: at (%s) %s%s -> at (%s) %s%s' % (k, o[1], o[2], ' hidden' if o[3] else '',
                                                                       n[1], n[2], ' hidden' if n[3] else ''))
        if ch:
            fpc.append(dict(ref=ref, change='; '.join(ch), x=y['x'], y=y['y'], side=y['side']))
    out['footprints'] = fpc
    if '--json' in a:
        json.dump(out, open(a[a.index('--json') + 1], 'w'), indent=1)
    md = ['### %s' % (a[a.index('--title') + 1] if '--title' in a else 'Board changes'), '']
    for name, rows in (('removed', out['tracks_removed']), ('added', out['tracks_added'])):
        if rows:
            md += ['Tracks %s (%d):' % (name, len(rows)), '', '| layer | net | width | from (x, y) | to (x, y) |',
                   '|---|---|---|---|---|']
            md += ['| %s | %s | %g | (%g, %g) | (%g, %g) |' % (r['layer'], r['net'], r['width'], r['x0'], r['y0'],
                                                             r['x1'], r['y1']) for r in rows]
            md.append('')
    for name, rows in (('removed', out['vias_removed']), ('added', out['vias_added'])):
        if rows:
            md += ['Vias %s (%d), through F.Cu-B.Cu:' % (name, len(rows)), '', '| net | x, y | size / drill |',
                   '|---|---|---|']
            md += ['| %s | (%g, %g) | %g / %g |' % (r['net'], r['x'], r['y'], r['size'], r['drill']) for r in rows]
            md.append('')
    if fpc:
        md += ['Footprints (%d):' % len(fpc), '', '| ref | side | at (x, y) | change |', '|---|---|---|---|']
        md += ['| %s | %s | (%g, %g) | %s |' % (r['ref'], r['side'], r['x'], r['y'], r['change']) for r in fpc]
        md.append('')
    if out['zones_removed'] or out['zones_added']:
        md += ['Zone outlines: %d removed, %d added (%s)' % (len(rz), len(az), ', '.join(
            '%s %s' % (z['net'], z['layers']) for z in out['zones_removed'] + out['zones_added'])), '']
    txt = '\n'.join(md)
    if '--md' in a:
        open(a[a.index('--md') + 1], 'w', encoding='utf-8').write(txt + '\n')
    print(txt)


if __name__ == '__main__':
    main()
