"""Text edit of footprint graphics on a SCRATCH board (and, for J9, the matching BOOST.pretty library footprint), keeping
each file's line endings and every other byte.

    python fp_text_edit.py SPEC.json KICAD_DIR LOG.json

SPEC.json:
  {"board": "BOOST_control_RC2.kicad_pcb",
   "footprints": [
     {"ref": "J9", "library": "BOOST.pretty/WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots.kicad_mod",
      "courtyard": {"layer": "F.CrtYd", "pts": [[x, y], ...]},      replaces every fp_line on that layer by the closed outline
      "texts": [{"text": "I2", "layer": "F.SilkS", "at": [x, y]}]},   moves an fp_text user (footprint-local mm)
     {"ref": "H3", "fields": [{"name": "Reference", "at": [x, y]}]}]}  moves a property (footprint-local mm)
Board and library get the same geometry; the library keeps its 3-decimal style and gets no uuids.
"""
import json, os, re, sys, uuid


def num(v, lib):
    if lib:
        return '%.3f' % v
    s = ('%.6f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def block_of(t, ref):
    i = t.find('(property "Reference" "%s"' % ref)
    assert i > 0, ref
    s = t.rfind('\t(footprint ', 0, i)
    e = t.find('\n\t(footprint ', i)
    e = len(t) if e < 0 else e
    return s, e


def edit_fp(b, spec, nl, lib, log, fname):
    """b = footprint text (board block or whole .kicad_mod); returns the edited text."""
    ind = '\t' if lib else '\t\t'                     # indent of a footprint child item
    if 'courtyard' in spec:
        lay = spec['courtyard']['layer']
        line_re = re.compile(re.escape(ind) + r'\(fp_line' + nl + r'(?:' + re.escape(ind) + r'\t[^\r\n]*' + nl + r')*?'
                             + re.escape(ind) + r'\)' + nl)
        hits = [m for m in line_re.finditer(b) if '(layer "%s")' % lay in m.group(0)]
        assert len(hits) == 4, (fname, len(hits))
        old = [re.findall(r'\((?:start|end) ([-\d.]+) ([-\d.]+)\)', m.group(0)) for m in hits]
        pts = spec['courtyard']['pts']
        new = ''
        for k in range(len(pts)):
            (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % len(pts)]
            new += (ind + '(fp_line' + nl + ind + '\t(start %s %s)' % (num(x0, lib), num(y0, lib)) + nl
                    + ind + '\t(end %s %s)' % (num(x1, lib), num(y1, lib)) + nl
                    + ind + '\t(stroke' + nl + ind + '\t\t(width 0.05)' + nl + ind + '\t\t(type solid)' + nl
                    + ind + '\t)' + nl + ind + '\t(layer "%s")' % lay + nl
                    + ('' if lib else ind + '\t(uuid "%s")' % uuid.uuid4() + nl) + ind + ')' + nl)
        first = hits[0].start()
        for m in reversed(hits):
            b = b[:m.start()] + b[m.end():]
        b = b[:first] + new + b[first:]
        log.append(dict(file=fname, what='courtyard', layer=lay, old=old, new=pts))
    for tx in spec.get('texts', []):
        pat = re.compile(r'\(fp_text user "%s"' % re.escape(tx['text']) + nl + r'(\t+)\(at ([-\d.]+) ([-\d.]+)( [-\d.]+)?\)'
                         + nl + r'\t+\(layer "%s"\)' % re.escape(tx['layer']))
        hits = list(pat.finditer(b))
        assert len(hits) == 1, (fname, tx, len(hits))
        m = hits[0]
        x, y = tx['at']
        b = b[:m.start(2)] + num(x, lib) + ' ' + num(y, lib) + b[m.end(3):]
        log.append(dict(file=fname, what='text moved', text=tx['text'], layer=tx['layer'],
                        old=[float(m.group(2)), float(m.group(3))], new=[x, y]))
    for fd in spec.get('fields', []):
        pat = re.compile(r'\(property "%s" "[^"]*"' % re.escape(fd['name']) + nl + r'\t+\(at ([-\d.]+) ([-\d.]+)')
        m = pat.search(b)
        assert m, (fname, fd)
        x, y = fd['at']
        b = b[:m.start(1)] + num(x, lib) + ' ' + num(y, lib) + b[m.end(2):]
        log.append(dict(file=fname, what='field moved', field=fd['name'],
                        old=[float(m.group(1)), float(m.group(2))], new=[x, y]))
    return b


def main():
    spec = json.load(open(sys.argv[1]))
    d, logp = sys.argv[2], sys.argv[3]
    log = []
    bp = os.path.join(d, spec['board'])
    t = open(bp, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    for fp in spec['footprints']:
        s, e = block_of(t, fp['ref'])
        blk = edit_fp(t[s:e], fp, nl, False, log, '%s:%s' % (spec['board'], fp['ref']))
        t = t[:s] + blk + t[e:]
        if fp.get('library'):
            lp = os.path.join(d, fp['library'])
            lt = open(lp, encoding='utf-8', newline='').read()
            lnl = '\r\n' if '\r\n' in lt else '\n'
            lt = edit_fp(lt, fp, lnl, True, log, fp['library'])
            open(lp, 'w', encoding='utf-8', newline='').write(lt)
    open(bp, 'w', encoding='utf-8', newline='').write(t)
    json.dump(log, open(logp, 'w'), indent=1)
    for r in log:
        print(r)


if __name__ == '__main__':
    main()
