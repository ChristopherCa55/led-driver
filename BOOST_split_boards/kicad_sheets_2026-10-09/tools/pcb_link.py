"""Link a board's footprints to its own schematic (metadata only; text edit of a COPY).

    python pcb_link.py BOARD.kicad_pcb BOARD_SCHEMATIC.kicad_sch [--rename OLD=NEW ...] [--board-only REF ...]

- Every footprint that has a (path ...) keeps it; its (sheetfile ...) becomes the board schematic's file name.
- A footprint without a path gets (path "/<uuid>") (sheetname "/") (sheetfile ...) from the schematic symbol with the
  same reference (single-unit parts; the symbol uuids are unchanged since the split, so this is the link KiCad's own
  Update PCB would make).
- --rename renames a net everywhere it appears as (net "OLD") (what Update PCB does when a net gets a label).
- --board-only sets the "Not in schematic" attribute on footprints with that reference (logos).
No geometry, pad, track, zone or layer changes.
"""
import sys, re

NL, TAB = chr(10), chr(9)


def main():
    pcb, schp = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    renames = [a.split('=', 1) for a in args[args.index('--rename') + 1:] if '=' in a] if '--rename' in args else []
    board_only = set()
    if '--board-only' in args:
        for a in args[args.index('--board-only') + 1:]:
            if a.startswith('--'):
                break
            board_only.add(a)
    sfile = schp.replace(chr(92), '/').split('/')[-1]
    s = open(schp, encoding='utf-8').read()
    sym = {}
    for b in re.findall(r'\n\t\(symbol\n(.*?)\n\t\)', s, re.S):
        if not re.search(r'\(lib_id "', b):
            continue
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        u = re.search(r'\n\t\t\(uuid "([^"]+)"\)', b).group(1)
        unit = int(re.search(r'\n\t\t\(unit (\d+)\)', b).group(1))
        if ref not in sym or unit < sym[ref][1]:
            sym[ref] = (u, unit)
    sync = '--sync-fields' in args
    symblk = {}
    for b in re.findall(r'\n\t\(symbol\n(.*?)\n\t\)', s, re.S):
        if not re.search(r'\(lib_id "', b):
            continue
        ref = re.search(r'\(property "Reference" "([^"]+)"', b).group(1)
        unit = int(re.search(r'\n\t\t\(unit (\d+)\)', b).group(1))
        if ref not in symblk or unit < symblk[ref][0]:
            symblk[ref] = (unit, b)
    symblk = {r: b for r, (u, b) in symblk.items()}
    fields_fixed = bom_fixed = 0
    t = open(pcb, encoding='utf-8', newline='').read()
    crlf = '\r\n' in t
    t = t.replace('\r\n', NL)
    out, pos, linked, refile, flagged = [], 0, 0, 0, 0
    for m in re.finditer(NL + TAB + r'\(footprint "[^"]*"' + r'.*?' + NL + TAB + r'\)', t, re.S):
        blk = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]*)"', blk)
        ref = ref.group(1) if ref else ''
        new = blk
        if re.search(NL + TAB * 2 + r'\(path "', new):
            new, n = re.subn(r'\(sheetfile "[^"]*"\)', '(sheetfile "%s")' % sfile, new)
            refile += n
        elif ref in sym:
            ins = (NL + TAB * 2 + '(path "/%s")' % sym[ref][0] + NL + TAB * 2 + '(sheetname "/")' + NL + TAB * 2 +
                   '(sheetfile "%s")' % sfile)
            k = new.find(NL + TAB * 2 + '(attr')
            if k < 0:
                k = new.find(NL + TAB * 2 + '(duplicate_pad_numbers_are_jumpers')
            assert k > 0, ref
            new = new[:k] + ins + new[k:]
            linked += 1
        if sync and ref in symblk:
            new, nf, nb = sync_fields(new, symblk[ref])
            fields_fixed += nf
            bom_fixed += nb
        if ref in board_only:
            am = re.search(NL + TAB * 2 + r'\(attr([^)]*)\)', new)
            if am and 'board_only' not in am.group(1):
                new = new[:am.start()] + NL + TAB * 2 + '(attr%s board_only)' % am.group(1) + new[am.end():]
                flagged += 1
            elif not am:
                k = new.find(NL + TAB * 2 + '(duplicate_pad_numbers_are_jumpers')
                new = new[:k] + NL + TAB * 2 + '(attr board_only)' + new[k:]
                flagged += 1
        out.append(t[pos:m.start()])
        out.append(new)
        pos = m.end()
    out.append(t[pos:])
    t = ''.join(out)
    for old, nw in renames:
        t, n = re.subn(r'\(net "%s"\)' % re.escape(old), '(net "%s")' % nw, t)
        print('renamed %s -> %s in %d places' % (old, nw, n))
    if crlf:
        t = t.replace(NL, '\r\n')
    open(pcb, 'w', encoding='utf-8', newline='').write(t)
    print('%s: %d footprints linked, %d sheetfile entries updated, %d set board-only, %d fields synced, %d BOM flags'
          % (pcb, linked, refile, flagged, fields_fixed, bom_fixed))


SKIP = {'Reference', 'Value', 'Footprint'}


def esc(v):
    return v.replace(chr(92), chr(92) * 2).replace('"', chr(92) + '"')


def sync_fields(fp, sym):
    """Make a footprint's user fields and BOM flag match its schematic symbol (what Update PCB does)."""
    nf = nb = 0
    props = re.findall(r'\n\t\t\(property "([^"]+)" "((?:[^"' + chr(92) + chr(92) + r']|' + chr(92) + chr(92) + r'.)*)"', sym)
    pv = dict(props)
    for name, val in props:
        if name in SKIP:
            continue
        # the PCB holds resolved text (KiCad's parity compares the schematic's resolved value)
        val = val.replace('${VALUE}', pv.get('Value', '')).replace('${REFERENCE}', pv.get('Reference', ''))
        val = val.replace('${FOOTPRINT}', pv.get('Footprint', ''))
        m = re.search(r'(\n\t\t\(property "' + re.escape(name) + r'" ")((?:[^"' + chr(92) + chr(92) + r']|' + chr(92) +
                      chr(92) + r'.)*)(")', fp)
        if m:
            if m.group(2) != val:
                fp = fp[:m.start(2)] + val + fp[m.end(2):]
                nf += 1
        else:
            blk = (NL + TAB * 2 + '(property "%s" "%s"' % (name, val) + NL + TAB * 3 + '(at 0 0 0)' + NL + TAB * 3 +
                   '(layer "F.Fab")' + NL + TAB * 3 + '(hide yes)' + NL + TAB * 3 + '(uuid "%s")' % uuid4() + NL + TAB * 3 +
                   '(effects' + NL + TAB * 4 + '(font' + NL + TAB * 5 + '(size 1.27 1.27)' + NL + TAB * 4 + ')' + NL + TAB * 3 +
                   ')' + NL + TAB * 2 + ')')
            k = fp.find(NL + TAB * 2 + '(path ')
            if k < 0:
                k = fp.find(NL + TAB * 2 + '(attr')
            fp = fp[:k] + blk + fp[k:]
            nf += 1
    in_bom = re.search(r'\n\t\t\(in_bom (yes|no)\)', sym).group(1) == 'yes'
    am = re.search(r'\n\t\t\(attr([^)]*)\)', fp)
    if am:
        flags = am.group(1).split()
        if in_bom and 'exclude_from_bom' in flags:
            flags.remove('exclude_from_bom'); nb += 1
        elif not in_bom and 'exclude_from_bom' not in flags:
            flags.append('exclude_from_bom'); nb += 1
        fp = fp[:am.start()] + NL + TAB * 2 + '(attr%s)' % ''.join(' ' + f for f in flags) + fp[am.end():]
    elif not in_bom:
        k = fp.find(NL + TAB * 2 + '(duplicate_pad_numbers_are_jumpers')
        fp = fp[:k] + NL + TAB * 2 + '(attr exclude_from_bom)' + fp[k:]
        nb += 1
    return fp, nf, nb


def uuid4():
    import uuid
    return str(uuid.uuid4())


if __name__ == '__main__':
    main()
