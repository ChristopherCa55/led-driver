"""Add footprints to a board COPY by copying an existing footprint block (text edit, line endings kept; OUT must not
exist). Every uuid inside the copy is renewed; position, rotation, reference, value, Sim.Params, the schematic link
(path) and the pad nets are set from the job. The template must be on the side wanted (B.Cu template for a B part).

    python add_footprints.py JOB.json IN.kicad_pcb OUT.kicad_pcb

JOB.json: {"footprints": [{"ref": "R106", "template": "R99", "x": 57.3, "y": 106.5, "rot": 0, "value": "4.7k",
                           "path": "/<symbol uuid>", "nets": {"1": "5V", "2": "SCL"}}, ...],
           "values": [{"ref": "R99", "value": "1k"}, ...]}          (value / Sim.Params changes of existing parts)
"""
import json, os, re, sys, uuid


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def block_of(t, ref, nl):
    i = t.find('(property "Reference" "%s"' % ref)
    assert i >= 0, ref
    j = t.rfind(nl + '\t(footprint ', 0, i)
    k = t.find(nl + '\t)' + nl, i)
    return j, k + len(nl) + 2


def main():
    job = json.load(open(sys.argv[1]))
    src, out = sys.argv[2], sys.argv[3]
    if os.path.exists(out):
        sys.exit('OUT exists: %s' % out)
    t = open(src, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    log = []
    for v in job.get('values', []):
        j, k = block_of(t, v['ref'], nl)
        b = t[j:k]
        old = re.search(r'\(property "Value" "([^"]*)"', b).group(1)
        b2 = b.replace('(property "Value" "%s"' % old, '(property "Value" "%s"' % v['value'], 1)
        b2 = b2.replace('(property "Sim.Params" "R=%s"' % old, '(property "Sim.Params" "R=%s"' % v['value'], 1)
        t = t[:j] + b2 + t[k:]
        log.append('%s value %s -> %s (Value and Sim.Params)' % (v['ref'], old, v['value']))
    for f in job.get('blocks', []):
        # a ready-made footprint block (make_fp_block.py), inserted after the footprint f['after']
        assert '(property "Reference" "%s"' % f['ref'] not in t, f['ref']
        blk = open(f['block'], encoding='utf-8', newline='').read().replace('\r\n', '\n').replace('\n', nl)
        assert '(property "Reference" "%s"' % f['ref'] in blk, f['block']
        j, k = block_of(t, f['after'], nl)
        t = t[:k] + nl + blk + t[k:]
        log.append('%s added from %s (after %s)' % (f['ref'], os.path.basename(f['block']), f['after']))
    for f in job.get('footprints', []):
        assert '(property "Reference" "%s"' % f['ref'] not in t, f['ref']
        j, k = block_of(t, f['template'], nl)
        b = t[j:k]
        b = re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uuid.uuid4(), b)
        # text and pad angles in a footprint are absolute: turn them with the footprint, then set its own (at)
        tm = re.search(r'%s\t\t\(at [-\d.]+ [-\d.]+ ?([-\d.]*)\)' % re.escape(nl), b)
        d = f['rot'] - float(tm.group(1) or 0)
        if d:
            def turn(m):
                return '%s%s %s %s)' % (m.group(1), m.group(2), m.group(3), fmt((float(m.group(4)) + d) % 360))
            b = re.sub(r'(\(at )([-\d.]+) ([-\d.]+) ([-\d.]+)\)', turn, b)
        b = re.sub(r'(%s\t\t\(at )[-\d.]+ [-\d.]+(?: [-\d.]+)?\)' % re.escape(nl),
                   lambda m: '%s%s %s%s)' % (m.group(1), fmt(f['x']), fmt(f['y']),
                                             (' ' + fmt(f['rot'])) if f['rot'] else ''), b, count=1)
        b = b.replace('(property "Reference" "%s"' % f['template'], '(property "Reference" "%s"' % f['ref'], 1)
        old = re.search(r'\(property "Value" "([^"]*)"', b).group(1)
        b = b.replace('(property "Value" "%s"' % old, '(property "Value" "%s"' % f['value'], 1)
        b = re.sub(r'\(property "Sim.Params" "R=[^"]*"', '(property "Sim.Params" "R=%s"' % f['value'], b, count=1)
        b = re.sub(r'\(path "[^"]*"\)', '(path "%s")' % f['path'], b, count=1)
        for num, net in f['nets'].items():
            pm = re.search(r'\(pad "%s" .*?\(net "([^"]*)"\)' % re.escape(num), b, re.S)
            assert pm, (f['ref'], num)
            b = b[:pm.start(1)] + net + b[pm.end(1):]
        t = t[:k] + b + t[k:]
        log.append('%s added (copy of %s) at (%s, %s) rot %s, value %s, nets %s, path %s' % (
            f['ref'], f['template'], fmt(f['x']), fmt(f['y']), fmt(f['rot']), f['value'], f['nets'], f['path']))
    open(out, 'w', encoding='utf-8', newline='').write(t)
    print('\n'.join(log))


if __name__ == '__main__':
    main()
