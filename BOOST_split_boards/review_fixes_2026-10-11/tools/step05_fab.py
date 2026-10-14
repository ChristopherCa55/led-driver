"""Step 5 fab files: the card's JLC BOM and CPL with R99 / R102 = 1k and the new R106 / R107, into a NEW folder.

    python step05_fab.py COPY_DIR CARD_PCB OUT_DIR

- BOM: R99 and R102 leave the 10k line (C25804) and join the card's existing 1k line (C21190); a 4.7k 0402 line
  (0402WGF4701TCE, C25900) is added. Parts: JLC basic, stock and prices read 2026-10-11 (work/jlc/step05_parts.json).
- CPL: rows for R106 / R107 from the PCB (the existing rows' format: X mm, -Y mm, Top/Bottom, the footprint's own
  rotation, as for R99 = Bottom, 90), placed after R105.
Line endings and quoting are kept as in the copy's files.
"""
import csv, io, os, re, sys

NEW_BOM = [('0603WAF1001T5E', ['R99', 'R102'], '0603', 'C21190'),
           ('0402WGF4701TCE', ['R106', 'R107'], '0402', 'C25900')]


def main():
    copy, pcb, out = sys.argv[1:4]
    if os.path.exists(out):
        sys.exit('OUT exists: %s' % out)
    os.makedirs(out)
    # ---- BOM
    raw = open(os.path.join(copy, 'BOOST_control_BOM_JLC.csv'), 'rb').read()
    nl = b'\r\n' if b'\r\n' in raw else b'\n'
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8'))))
    moved = set(r for _, refs, _, _ in NEW_BOM for r in refs if r in ('R99', 'R102'))
    out_rows = []
    for r in rows:
        if len(r) == 4 and r[3] == 'C25804':
            refs = [x for x in r[1].split(',') if x not in moved]
            assert len(refs) == len(r[1].split(',')) - 2, r
            r = [r[0], ','.join(refs), r[2], r[3]]
        assert not (len(r) == 4 and any(x in ('R106', 'R107') for x in r[1].split(','))), r
        out_rows.append(r)
    def natural(r):
        return int(re.sub(r'\D', '', r) or 0)
    for comment, refs, fp, lcsc in NEW_BOM:
        same = [r for r in out_rows if len(r) == 4 and r[3] == lcsc]
        if same:           # the part is already on the card (1k C21190: R4, R54, ...): join its line
            r = same[0]
            r[1] = ','.join(sorted(r[1].split(',') + refs, key=natural))
        else:
            out_rows.append([comment, ','.join(refs), fp, lcsc])
    s = io.StringIO()
    w = csv.writer(s, lineterminator=nl.decode())
    w.writerows(out_rows)
    open(os.path.join(out, 'BOOST_control_BOM_JLC.csv'), 'wb').write(s.getvalue().encode('utf-8'))
    # ---- CPL
    t = open(pcb, encoding='utf-8').read()
    add = []
    for ref in ('R106', 'R107'):
        i = t.find('(property "Reference" "%s"' % ref)
        j = t.rfind('\n\t(footprint ', 0, i)
        blk = t[j:i]
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+) ?([-\d.]*)\)', blk)
        side = re.search(r'\n\t\t\(layer "([^"]+)"\)', blk).group(1)
        rot = float(at.group(3) or 0)
        add.append('%s,%.4fmm,%.4fmm,%s,%g' % (ref, float(at.group(1)), -float(at.group(2)),
                                               'Bottom' if side == 'B.Cu' else 'Top', rot))
    raw = open(os.path.join(copy, 'BOOST_control_CPL_JLC.csv'), 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    lines = raw.decode('utf-8').split(nl)
    k = [n for n, l in enumerate(lines) if l.startswith('R105,')][0]
    lines = lines[:k + 1] + add + lines[k + 1:]
    open(os.path.join(out, 'BOOST_control_CPL_JLC.csv'), 'wb').write(nl.join(lines).encode('utf-8'))
    print('BOM lines:', len(out_rows), '; CPL added:', add)


if __name__ == '__main__':
    main()
