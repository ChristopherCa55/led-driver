"""Text edit of a KiCad 10 board COPY: remove / add track segments and vias, keeping the file's line endings and every
other byte. (Same approach as power6_2026-10-01/tools/patch_m7_drive.py.)

    python pcb_text_edit.py SPEC.json IN.kicad_pcb OUT.kicad_pcb        (OUT must not exist)

SPEC.json:
  {"remove_segments": [{"net": N, "layer": L, "seg": [x0, y0, x1, y1]}            exact (either direction, 0.02 mm)
                       | {"net": N, "layer": L, "bbox": [x1, y1, x2, y2]}],       every segment wholly inside
   "remove_vias": [{"net": N, "x": X, "y": Y}],
   "add_segments": [{"net": N, "layer": L, "width": W, "pts": [[x, y], ...]}],
   "add_vias": [{"net": N, "x": X, "y": Y, "size": 0.6, "drill": 0.3}],
   "expect": {"remove_segments": n, "remove_vias": n}}                            optional counts to assert
Zones are not refilled here: run kicad-cli pcb drc --refill-zones --save-board on OUT afterwards (with the
project's .kicad_pro / .kicad_dru beside it).
"""
import json, os, re, sys, uuid


def main():
    spec = json.load(open(sys.argv[1]))
    src, out = sys.argv[2], sys.argv[3]
    if os.path.exists(out):
        sys.exit('OUT exists: %s' % out)
    t = open(src, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    seg_re = re.compile(r'\t\(segment' + nl + r'\t\t\(start ([-\d.]+) ([-\d.]+)\)' + nl + r'\t\t\(end ([-\d.]+) ([-\d.]+)\)'
                        + nl + r'\t\t\(width ([\d.]+)\)' + nl + r'\t\t\(layer "([^"]+)"\)' + nl + r'\t\t\(net "([^"]*)"\)'
                        + nl + r'\t\t\(uuid "[^"]+"\)' + nl + r'\t\)' + nl)
    via_re = re.compile(r'\t\(via' + nl + r'\t\t\(at ([-\d.]+) ([-\d.]+)\)' + nl + r'(?:\t\t[^\r\n]*' + nl + r')*?'
                        + r'\t\t\(net "([^"]*)"\)' + nl + r'\t\t\(uuid "[^"]+"\)' + nl + r'\t\)' + nl)

    def seg_match(m, r):
        x0, y0, x1, y1 = (float(m.group(i)) for i in range(1, 5))
        if m.group(7) != r['net'] or m.group(6) != r['layer']:
            return False
        if 'seg' in r:
            s = r['seg']
            return any(all(abs(u - v) < 0.02 for u, v in zip((x0, y0, x1, y1), c))
                       for c in (s, (s[2], s[3], s[0], s[1])))
        b = r['bbox']
        return all(b[0] <= x <= b[2] for x in (x0, x1)) and all(b[1] <= y <= b[3] for y in (y0, y1))

    rm = []
    for r in spec.get('remove_segments', []):
        hits = [m for m in seg_re.finditer(t) if seg_match(m, r)]
        if not hits:
            sys.exit('no segment matches %s' % r)
        rm += hits
    nseg = len({m.start() for m in rm})
    for r in spec.get('remove_vias', []):
        hits = [m for m in via_re.finditer(t) if m.group(3) == r['net'] and abs(float(m.group(1)) - r['x']) < 0.01
                and abs(float(m.group(2)) - r['y']) < 0.01]
        if len(hits) != 1:
            sys.exit('via %s: %d matches' % (r, len(hits)))
        rm += hits
    nvia = len(spec.get('remove_vias', []))
    exp = spec.get('expect', {})
    if 'remove_segments' in exp and exp['remove_segments'] != nseg:
        sys.exit('expected %d segments, found %d' % (exp['remove_segments'], nseg))
    seen, first = set(), len(t)
    for m in sorted(rm, key=lambda m: -m.start()):
        if m.start() in seen:
            continue
        seen.add(m.start())
        first = min(first, m.start())
        t = t[:m.start()] + t[m.end():]
    add = ''
    for a in spec.get('add_segments', []):
        for p, q in zip(a['pts'], a['pts'][1:]):
            add += ('\t(segment' + nl + '\t\t(start %s %s)' + nl + '\t\t(end %s %s)' + nl + '\t\t(width %s)' + nl +
                    '\t\t(layer "%s")' + nl + '\t\t(net "%s")' + nl + '\t\t(uuid "%s")' + nl + '\t)' + nl) % (
                fmt(p[0]), fmt(p[1]), fmt(q[0]), fmt(q[1]), fmt(a['width']), a['layer'], a['net'], uuid.uuid4())
    for v in spec.get('add_vias', []):
        if v.get('free'):
            # a stitching via with no track or pad: "free" keeps its net (else KiCad re-assigns it from a zone),
            # written like the power board's own GND stitching vias
            # 'remove_unused': true also drops its pads on layers where nothing of the net touches it (no lone pads)
            ru = (('\t\t(remove_unused_layers yes)' + nl + '\t\t(keep_end_layers no)' + nl)
                  if v.get('remove_unused') else '')
            add += ('\t(via' + nl + '\t\t(at %s %s)' + nl + '\t\t(size %s)' + nl + '\t\t(drill %s)' + nl +
                    '\t\t(layers "F.Cu" "B.Cu")' + nl + ru + '\t\t(free yes)' + nl + '\t\t(net "%s")' + nl +
                    '\t\t(uuid "%s")' + nl + '\t)' + nl) % (
                fmt(v['x']), fmt(v['y']), fmt(v['size']), fmt(v['drill']), v['net'], uuid.uuid4())
            continue
        add += ('\t(via' + nl + '\t\t(at %s %s)' + nl + '\t\t(size %s)' + nl + '\t\t(drill %s)' + nl +
                '\t\t(layers "F.Cu" "B.Cu")' + nl + '\t\t(remove_unused_layers yes)' + nl + '\t\t(keep_end_layers no)'
                + nl + '\t\t(net "%s")' + nl + '\t\t(uuid "%s")' + nl + '\t)' + nl) % (
            fmt(v['x']), fmt(v['y']), fmt(v['size']), fmt(v['drill']), v['net'], uuid.uuid4())
    if add:
        i = t.find('\t(segment')
        if i < 0:
            i = t.find('\t(via')
        t = t[:i] + add + t[i:]
    open(out, 'w', encoding='utf-8', newline='').write(t)
    print('removed %d segments and %d vias; added %d segments and %d vias -> %s' % (
        nseg, nvia, sum(len(a['pts']) - 1 for a in spec.get('add_segments', [])), len(spec.get('add_vias', [])), out))


def fmt(v):
    return ('%.6f' % v).rstrip('0').rstrip('.')


if __name__ == '__main__':
    main()
