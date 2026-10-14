"""Copy the user's re-arrangement of a group of items from the MAIN page onto the CARD sheet, where the same group sits
at a fixed offset (2026-10-14: the I2C pull-ups R106 / R107, which the user re-placed on the main page).

    python sync_group_to_card.py MAIN_BEFORE.kicad_sch MAIN_NOW.kicad_sch CARD_IN.kicad_sch CARD_OUT.kicad_sch
                                 DX DY X1 Y1 X2 Y2 REF[,REF...] LOG.json

- The group = wires, labels, texts, junctions and no-connects inside the main-page box X1 Y1 X2 Y2 that differ between
  MAIN_BEFORE and MAIN_NOW, plus the symbols REF.
- On the card sheet: every item of MAIN_BEFORE's version of the group, shifted by (DX, DY), must exist exactly once and
  is removed; MAIN_NOW's version is added, shifted, with new uuids; the REF symbols keep their own blocks (instances,
  uuids, pins) and get MAIN_NOW's position, rotation, mirror and field positions, shifted.
- Line endings are kept. CARD_OUT must not exist.
"""
import json, os, re, sys, uuid

NUM = r'(-?[\d.]+)'


def blocks(t):
    """top-level children of (kicad_sch ...): list of (kind, start, end)"""
    out = []
    i = t.index('(kicad_sch') + 1
    depth, start, k, n, in_str = 0, None, i, len(t), False
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
                out.append((re.match(r'\((\w+)', t[start:start + 40]).group(1), start, k + 1))
                start = None
            depth -= 1
            if depth < 0:
                break
        k += 1
    return out


def r3(v):
    return round(float(v), 4)


def sig(kind, blk):
    """a position signature for a non-symbol item (uuid-free)"""
    if kind == 'wire':
        return ('wire', tuple(sorted((r3(a), r3(b)) for a, b in re.findall(r'\(xy ' + NUM + ' ' + NUM + r'\)', blk))))
    if kind in ('global_label', 'label'):
        name = re.match(r'\(\w+ "([^"]*)"', blk).group(1)
        at = re.search(r'\(at ' + NUM + ' ' + NUM + ' ' + NUM + r'\)', blk)
        return (kind, name, r3(at.group(1)), r3(at.group(2)), r3(at.group(3)))
    if kind == 'text':
        txt = re.match(r'\(text "((?:[^"\\]|\\.)*)"', blk).group(1)
        at = re.search(r'\(at ' + NUM + ' ' + NUM, blk)
        return ('text', txt, r3(at.group(1)), r3(at.group(2)))
    if kind in ('junction', 'no_connect'):
        at = re.search(r'\(at ' + NUM + ' ' + NUM + r'\)', blk)
        return (kind, r3(at.group(1)), r3(at.group(2)))
    return None


def shift_sig(s, dx, dy):
    if s[0] == 'wire':
        return ('wire', tuple(sorted((r3(a + dx), r3(b + dy)) for a, b in s[1])))
    if s[0] in ('global_label', 'label'):
        return (s[0], s[1], r3(s[2] + dx), r3(s[3] + dy), s[4])
    if s[0] == 'text':
        return ('text', s[1], r3(s[2] + dx), r3(s[3] + dy))
    return (s[0], r3(s[1] + dx), r3(s[2] + dy))


def fmt(v):
    s = ('%.4f' % v).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def shift_text(blk, dx, dy):
    blk = re.sub(r'\(at ' + NUM + ' ' + NUM, lambda m: '(at %s %s' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy)), blk)
    blk = re.sub(r'\(xy ' + NUM + ' ' + NUM + r'\)', lambda m: '(xy %s %s)' % (fmt(float(m.group(1)) + dx), fmt(float(m.group(2)) + dy)), blk)
    return re.sub(r'\(uuid "[^"]+"\)', lambda m: '(uuid "%s")' % uuid.uuid4(), blk)


def in_box(s, box):
    if s[0] == 'wire':
        pts = s[1]
    elif s[0] in ('global_label', 'label', 'text'):
        pts = [(s[2], s[3])]
    else:
        pts = [(s[1], s[2])]
    return any(box[0] <= x <= box[2] and box[1] <= y <= box[3] for x, y in pts)


def group(t, box):
    out = {}
    for kind, a, b in blocks(t):
        s = sig(kind, t[a:b])
        if s and in_box(s, box):
            out[s] = t[a:b]
    return out


def sym_block(t, ref):
    hits = []
    for kind, a, b in blocks(t):
        if kind == 'symbol' and re.search(r'\(property "Reference" "%s"' % re.escape(ref), t[a:b]):
            hits.append((a, b))
    assert len(hits) == 1, (ref, len(hits))
    return hits[0]


def main():
    a = sys.argv[1:]
    mb_p, mn_p, ci_p, co_p = a[:4]
    dx, dy = float(a[4]), float(a[5])
    box = list(map(float, a[6:10]))
    refs = a[10].split(',')
    logp = a[11]
    assert not os.path.exists(co_p), 'CARD_OUT exists'
    rd = lambda p: open(p, encoding='utf-8', newline='').read()
    mb, mn = rd(mb_p).replace('\r\n', '\n'), rd(mn_p).replace('\r\n', '\n')
    raw = rd(ci_p)
    crlf = '\r\n' in raw
    c = raw.replace('\r\n', '\n')
    gb, gn = group(mb, box), group(mn, box)
    old = [s for s in gb if s not in gn]           # the version on the card now (shifted)
    new = [s for s in gn if s not in gb]
    log = dict(removed=[], added=[], symbols=[])
    # remove the old items from the card
    cmap = {}
    for kind, s0, e0 in blocks(c):
        s = sig(kind, c[s0:e0])
        if s:
            cmap.setdefault(s, []).append((s0, e0))
    cut = []
    for s in old:
        ss = shift_sig(s, dx, dy)
        assert len(cmap.get(ss, [])) == 1, ('card item not found exactly once', ss, len(cmap.get(ss, [])))
        cut.append(cmap[ss][0])
        log['removed'].append(list(map(str, ss)))
    # symbols: position, rotation, mirror and field positions from MAIN_NOW, shifted
    edits = []
    for ref in refs:
        ma, mb_ = sym_block(mn, ref)
        msym = mn[ma:mb_]
        ca, cb = sym_block(c, ref)
        csym = c[ca:cb]
        mat = re.search(r'\n\t\t\(at ' + NUM + ' ' + NUM + ' ' + NUM + r'\)', msym)
        cat = re.search(r'\n\t\t\(at ' + NUM + ' ' + NUM + ' ' + NUM + r'\)', csym)
        nsym = csym[:cat.start()] + '\n\t\t(at %s %s %s)' % (fmt(float(mat.group(1)) + dx), fmt(float(mat.group(2)) + dy), mat.group(3)) + csym[cat.end():]
        mm = re.search(r'\n\t\t\(mirror (\w+)\)', msym)
        cm = re.search(r'\n\t\t\(mirror (\w+)\)', nsym)
        assert bool(mm) == bool(cm) and (not mm or mm.group(1) == cm.group(1)), (ref, 'mirror differs: not handled')
        for pm in re.finditer(r'\(property "([^"]+)" "[^"]*"\n\t\t\t\(at ' + NUM + ' ' + NUM + ' ' + NUM + r'\)', msym):
            name = pm.group(1)
            pc = re.search(r'(\(property "%s" "[^"]*"\n\t\t\t\(at )' % re.escape(name) + NUM + ' ' + NUM + ' ' + NUM + r'\)', nsym)
            if not pc:
                continue
            nsym = nsym[:pc.start(2)] + '%s %s %s' % (fmt(float(pm.group(2)) + dx), fmt(float(pm.group(3)) + dy), pm.group(4)) + nsym[pc.end(4):]
        edits.append((ca, cb, nsym))
        log['symbols'].append(dict(ref=ref, card_at_old=[float(cat.group(1)), float(cat.group(2))],
                                   card_at_new=[r3(float(mat.group(1)) + dx), r3(float(mat.group(2)) + dy)],
                                   main_at=[float(mat.group(1)), float(mat.group(2))]))
    # apply removals and symbol edits from the end of the file backwards
    ops = [(s0, e0, '') for s0, e0 in cut] + edits
    for s0, e0, rep in sorted(ops, key=lambda o: -o[0]):
        if rep == '':
            # remove the block and its leading newline + tab
            lead = c.rfind('\n', 0, s0)
            c = c[:lead] + c[e0:]
        else:
            c = c[:s0] + rep + c[e0:]
    # add the new items after the last item of the same kind
    for s in new:
        blk = shift_text(gn[s], dx, dy)
        kinds = [b0 for b0 in blocks(c) if b0[0] == s[0]]
        pos = kinds[-1][2] if kinds else blocks(c)[-1][2]
        c = c[:pos] + '\n\t' + blk + c[pos:]
        log['added'].append(list(map(str, shift_sig(s, dx, dy))))
    if crlf:
        c = c.replace('\n', '\r\n')
    open(co_p, 'w', encoding='utf-8', newline='').write(c)
    json.dump(log, open(logp, 'w'), indent=1)
    print('removed %d, added %d, symbols %s' % (len(log['removed']), len(log['added']),
                                               [(s['ref'], s['card_at_new']) for s in log['symbols']]))


if __name__ == '__main__':
    main()
