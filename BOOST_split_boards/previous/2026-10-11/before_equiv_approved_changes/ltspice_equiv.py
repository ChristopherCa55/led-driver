"""Electrical checks E1-E5: is CANDIDATE.asc the same circuit as the frozen original?

    python ltspice_equiv.py CANDIDATE.asc [--ref DIR] [--json OUT.json] [--keep]

Both schematics are netlisted by LTspice itself (LTspice.exe -netlist) in fresh temp copies of their folders, so what
is compared is exactly what LTspice simulates. Nothing in the candidate's folder is written.

  E1  netlist identity: same elements (after the approved instance renames), same value/model/parameter text, and the
      same nets judged by PIN POSITION (element, pin index), so pin order is kept. Auto node names (N001, P001, NC_01)
      are ignored. A named net of the original must keep its exact name. A new name is allowed only on a net that was
      auto-named in the original, and is listed.
  E2  name-based connections: U18 (CD4017B) is powered through its SpiceModel text "5V 0", i.e. by the net NAME 5V;
      the labels 4..10 on U18 are explicit names. Both must survive.
  E3  directives and comments: the .asc directive texts (TEXT ... !) are an identical multiset; every original comment
      (TEXT ... ;) is present verbatim unless approved_changes.json lists its replacement.
  E4  identifiers used by directives: every V(node), I(element) and {param} used by .ic/.meas/.param lines and by
      behavioural values resolves in the candidate exactly as it did in the original.
  E5  support files: every non-.asc file of the original LTspice folder (.asy, .lib) is present beside the candidate
      with the same SHA-256.

Exit code 0 only if every check passes. approved_changes.json (next to this script) holds the ONLY allowed
deviations: instance renames and comment rewordings the user has approved. Do not edit it without the user's OK.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_REF = os.path.normpath(os.path.join(HERE, '..', 'reference', 'LTspice_original'))
LTSPICE = r'C:\Program Files\ADI\LTspice\LTspice.exe'
AUTO = re.compile(r'^(N|P)\d{3,}$|^NC_\d+$')
OUTPUT_EXT = ('.raw', '.log', '.net', '.op.raw', '.plt', '.fft', '.bak', '.tmp')


# ----------------------------------------------------------------------------------------------------- netlisting
def netlist(asc):
    """Copy the .asc's folder (inputs only) to a temp dir, run LTspice -netlist there, return the netlist text."""
    src = os.path.dirname(os.path.abspath(asc))
    tmp = tempfile.mkdtemp(prefix='ltequiv_')
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.isfile(p) and not f.lower().endswith(OUTPUT_EXT) and not f.endswith('.asc'):
            shutil.copy2(p, tmp)
    dst = os.path.join(tmp, os.path.basename(asc))
    shutil.copy2(asc, dst)
    try:
        subprocess.run([LTSPICE, '-netlist', dst], timeout=180, check=False)
    except subprocess.TimeoutExpired:
        raise SystemExit('LTspice -netlist timed out on %s (a dialog may be open: a "\u00a7" in a TEXT line is known '
                         'to cause this). Close it and retry.' % asc)
    net = os.path.splitext(dst)[0] + '.net'
    if not os.path.exists(net):
        raise SystemExit('LTspice wrote no netlist for %s' % asc)
    raw = open(net, 'rb').read()
    try:
        txt = raw.decode('utf-8')
    except UnicodeDecodeError:
        txt = raw.decode('latin-1')
    return txt, tmp


def npins(kind, body):
    if kind in 'RCLDVIBEFGH':
        return 2
    if kind in 'SW':
        return 4
    if kind == 'Q':
        return 4 if len(body) > 5 and '=' not in body[4] and not re.match(r'^[A-Za-z]*NP$', body[4] or '') else 3
    if kind == 'M':
        return 4
    if kind == 'A':
        return 8
    if kind == 'X':
        toks = body[1:]
        while toks and '=' in toks[-1]:
            toks.pop()
        return len(toks) - 1          # last non-parameter token is the subcircuit name
    raise SystemExit('unknown element type in line: ' + ' '.join(body))


def parse_net(txt):
    """-> elements {instname: (kind, nodes, rest)}, directives [lines]"""
    lines, cur = [], ''
    for l in txt.split('\n'):
        l = l.rstrip('\r')
        if l.startswith('+'):
            cur += ' ' + l[1:]
            continue
        if cur:
            lines.append(cur)
        cur = l
    if cur:
        lines.append(cur)
    elems, directives = {}, []
    for line in lines:
        s = line.strip()
        if not s or s.startswith('*'):
            continue
        if s.startswith('.'):
            if not s.lower().startswith(('.backanno', '.end')):
                directives.append(s)
            continue
        body = s.split(';')[0].split()
        tok = body[0]
        kind = tok[0].upper()
        inst = tok.split('\u00a7', 1)[1] if '\u00a7' in tok else tok
        n = npins(kind, body)
        elems[inst] = (kind, body[1:1 + n], ' '.join(body[1 + n:]))
    return elems, directives


def nets_of(elems, rename):
    d = {}
    for inst, (kind, nodes, _) in elems.items():
        name = rename.get(inst, inst)
        for i, nd in enumerate(nodes):
            d.setdefault(nd, set()).add((name, i))
    return {k: frozenset(v) for k, v in d.items()}


# ----------------------------------------------------------------------------------------------------- .asc texts
def asc_texts(path):
    out = {'!': [], ';': []}
    for l in open(path, encoding='latin-1').read().split('\n'):
        if l.startswith('TEXT '):
            body = l.rstrip('\r').split(' ', 5)[5] if len(l.split(' ', 5)) == 6 else ''
            if body[:1] in out:
                out[body[:1]].append(body[1:])
    return out


def asc_symattr(path, inst, key):
    cur = None
    for l in open(path, encoding='latin-1').read().split('\n'):
        l = l.rstrip('\r')
        if l.startswith('SYMBOL '):
            cur = {}
        elif l.startswith('SYMATTR ') and cur is not None:
            k, _, v = l[8:].partition(' ')
            cur[k] = v
            if cur.get('InstName') == inst and key in cur:
                return cur[key]
        elif not l.startswith('WINDOW '):
            cur = None
    return None


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def asy_electrical(p, ignore_xy=False):
    """What in an .asy affects connectivity or the netlist: every pin (position, name, SpiceOrder) and the electrical
    attributes. Drawing (LINE/RECTANGLE/CIRCLE/ARC/TEXT/WINDOW), pin-label justification and Description are not.
    ignore_xy: for a symbol whose pins the user allowed to move (approved_changes.json "asy_pins_moved"); the pin
    names, their order and the attributes must still match, and E1 then proves every connection."""
    raw = open(p, 'rb').read()
    txt = raw.decode('utf-16') if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else raw.decode('latin-1')
    pins, attrs, cur = [], {}, None
    for l in txt.replace('\r', '').split('\n'):
        t = l.split(' ')
        if t[0] == 'PIN':
            cur = {} if ignore_xy else {'xy': (t[1], t[2])}
            pins.append(cur)
        elif t[0] == 'PINATTR' and cur is not None:
            cur[t[1]] = ' '.join(t[2:])
        elif t[0] == 'SYMATTR' and t[1] != 'Description':
            attrs[t[1]] = ' '.join(t[2:])
        elif t[0] == 'SymbolType':
            attrs['SymbolType'] = ' '.join(t[1:])
    return [sorted(d.items()) for d in pins], attrs


# ----------------------------------------------------------------------------------------------------- main
def main():
    args = sys.argv[1:]
    if not args or args[0].startswith('-'):
        raise SystemExit(__doc__)
    cand = os.path.abspath(args[0])
    ref_dir = args[args.index('--ref') + 1] if '--ref' in args else DEFAULT_REF
    out_json = args[args.index('--json') + 1] if '--json' in args else None
    keep = '--keep' in args
    ref = os.path.join(ref_dir, 'BOOST.asc')
    appr = json.load(open(os.path.join(HERE, 'approved_changes.json')))
    rename = appr.get('instance_renames', {})            # original name -> new name
    comment_changes = appr.get('comment_changes', {})     # original comment text -> approved new text

    res = {'candidate': cand, 'reference': ref, 'checks': {}}
    fails = []

    def report(check, ok, lines):
        res['checks'][check] = {'pass': ok, 'details': lines}
        if not ok:
            fails.append(check)

    rtxt, rtmp = netlist(ref)
    ctxt, ctmp = netlist(cand)
    ea, da = parse_net(rtxt)
    eb, db = parse_net(ctxt)
    # parts the user has approved deleting from the design: compare as if the original never had them
    removed = [n for n in appr.get('removed_elements', []) if n in ea and n not in eb]
    for n in removed:
        del ea[n]
    # an approved rename is allowed, not required: apply it only where the candidate actually uses the new name
    rename = {o: n for o, n in rename.items() if o in ea and n in eb and o not in eb}
    # approved swaps of interchangeable inputs (e.g. the two inputs of a NAND): allowed, not required. The candidate's
    # two pins are swapped back only when that makes each of them land on the net the original had for the other.
    swaps_done = []
    for sw in appr.get('pin_swaps', []):
        el, (i, j) = sw['element'], sw['pins']
        if el not in ea or el not in eb:
            continue
        def others(elems, node, ren):
            return frozenset((ren.get(k, k), x) for k, (_, nds, _) in elems.items() if k != el
                             for x, nd in enumerate(nds) if nd == node)
        a_i, a_j = others(ea, ea[el][1][i], rename), others(ea, ea[el][1][j], rename)
        b_i, b_j = others(eb, eb[el][1][i], {}), others(eb, eb[el][1][j], {})
        if (b_i, b_j) == (a_j, a_i) and (a_i, a_j) != (b_i, b_j):
            kind, nds, rest = eb[el]
            nds = list(nds)
            nds[i], nds[j] = nds[j], nds[i]
            eb[el] = (kind, nds, rest)
            swaps_done.append('approved input swap applied: %s pins %d and %d (%s)' % (el, i, j, sw.get('why', '')))

    # ---------------- E1
    e1 = []
    ea_r = {rename.get(k, k): v for k, v in ea.items()}
    missing = sorted(set(ea_r) - set(eb))
    extra = sorted(set(eb) - set(ea_r))
    for n in missing:
        e1.append('element missing from candidate: %s' % n)
    for n in extra:
        e1.append('element only in candidate: %s' % n)
    for n in sorted(set(ea_r) & set(eb)):
        ka, _, ra = ea_r[n]
        kb, _, rb = eb[n]
        if ka != kb:
            e1.append('element %s changed type %s -> %s' % (n, ka, kb))
        if ra != rb:
            e1.append('element %s value/model text changed: %r -> %r' % (n, ra, rb))
    na, nb = nets_of(ea, rename), nets_of(eb, {})
    inv_b = {v: k for k, v in nb.items()}
    new_names, net_diffs = [], 0
    for name, pins in sorted(na.items()):
        if pins in inv_b:
            nb_name = inv_b[pins]
            if nb_name != name:
                if AUTO.match(name) and AUTO.match(nb_name):
                    continue
                if AUTO.match(name):
                    new_names.append('%s (was auto %s)' % (nb_name, name))
                else:
                    e1.append('named net %r renamed to %r' % (name, nb_name))
            continue
        net_diffs += 1
        best = max(nb.items(), key=lambda kv: len(kv[1] & pins))
        e1.append('net %s differs; closest candidate net %s; only in original %s; only in candidate %s' % (
            name, best[0], sorted(pins - best[1]), sorted(best[1] - pins)))
    report('E1 netlist identity', not e1,
           e1 + ['elements %d -> %d, nets compared %d, differing %d' % (len(ea), len(eb), len(na), net_diffs)] +
           ['new net name on a previously auto-named net: ' + s for s in new_names] +
           swaps_done + ['approved instance rename applied: %s -> %s' % kv for kv in rename.items() if kv[0] in ea] +
           ['approved deletion: %s (absent from the candidate, as approved)' % n for n in removed])

    # ---------------- E2
    e2 = []
    sm = asc_symattr(cand, 'U18', 'SpiceModel')
    if sm is None or sm.split() != ['5V', '0']:
        e2.append('U18 SpiceModel is %r; it must stay "5V 0" (U18 is powered by the net NAME 5V)' % sm)
    if '5V' not in nb:
        e2.append('no net named 5V in the candidate')
    elif nb['5V'] != na.get('5V'):
        e2.append('the net named 5V no longer holds the same pins (%d -> %d): U18 is powered by this NAME, so a '
                  'renamed or split 5V rail leaves U18 unpowered' % (len(na.get('5V', ())), len(nb['5V'])))
    for lbl in [str(i) for i in range(4, 11)]:
        if lbl in na and nb.get(lbl) != na[lbl]:
            e2.append('U18 output label %r lost or moved' % lbl)
    report('E2 name-based connections', not e2, e2 or ['U18 SpiceModel "5V 0"; net 5V present; labels 4..10 kept'])

    # ---------------- E3
    e3 = []
    ta, tb = asc_texts(ref), asc_texts(cand)
    ca, cb = Counter(ta['!']), Counter(tb['!'])
    for t, k in (ca - cb).items():
        e3.append('directive missing or edited (%dx): %r' % (k, t[:160]))
    for t, k in (cb - ca).items():
        e3.append('directive added or edited (%dx): %r' % (k, t[:160]))
    cmt_b = Counter(tb[';'])
    for t in ta[';']:
        want = comment_changes.get(t, t)
        if cmt_b[want] > 0:
            cmt_b[want] -= 1
        else:
            e3.append('original comment missing or reworded without approval: %r' % t[:160])
    extra_cmt = [t for t, k in cmt_b.items() for _ in range(k)]
    if Counter(da) != Counter(db):
        for t, k in (Counter(da) - Counter(db)).items():
            e3.append('netlist directive missing: %r' % t[:160])
        for t, k in (Counter(db) - Counter(da)).items():
            e3.append('netlist directive added: %r' % t[:160])
    report('E3 directives and comments', not e3,
           e3 + ['%d directive texts, %d original comments checked' % (len(ta['!']), len(ta[';']))] +
           ['new comment (allowed: block titles, notes): %r' % t[:100] for t in extra_cmt])

    # ---------------- E4
    e4 = []
    used_v, used_i, used_p = set(), set(), set()
    src = ' '.join(ta['!']) + ' ' + ' '.join(r for _, _, r in ea.values())
    for m in re.finditer(r'\b[Vv]\(([^)]+)\)', src):
        used_v.update(x.strip() for x in m.group(1).split(','))
    for m in re.finditer(r'\b[Ii]\(([^)]+)\)', src):
        used_i.add(m.group(1).strip())
    params = set()
    for d in ta['!']:
        for line in d.split('\\n'):
            if line.lower().startswith('.param'):
                params.update(k for k, _ in re.findall(r'(\w+)\s*=\s*([^\s]+)', line[6:]))
    for m in re.finditer(r'\{([^}]*)\}', src):
        used_p.update(w for w in re.findall(r'[A-Za-z_]\w*', m.group(1)) if w in params)
    for v in sorted(used_v):
        a_has, b_has = v in na, v in nb
        if a_has and (not b_has or nb[v] != na[v]):
            e4.append('V(%s) is used by a directive but the node is gone or moved in the candidate' % v)
        elif not a_has:
            e4.append('note: V(%s) names no node in the ORIGINAL either (pre-existing, left as is)' % v) \
                if not b_has else e4.append('V(%s) now names a node that did not exist before' % v)
    for i in sorted(used_i):
        nm = rename.get(i, i)
        if i in ea and nm not in eb:
            e4.append('I(%s) is used by a directive but the element is gone' % i)
    for p in sorted(used_p):
        if not any(re.search(r'\b%s\s*=' % p, line) for d in tb['!'] for line in d.split('\\n')):
            e4.append('param %s is used but no longer defined' % p)
    real = [x for x in e4 if not x.startswith('note:')]
    report('E4 referenced identifiers', not real,
           e4 + ['checked V(): %s' % ', '.join(sorted(used_v)), 'checked I(): %s' % ', '.join(sorted(used_i)),
                 'checked params: %s' % ', '.join(sorted(used_p))])

    # ---------------- E5
    e5, e5_info = [], []
    graphics_only = set(appr.get('asy_graphics_only', []))
    pins_moved = set(appr.get('asy_pins_moved', []))
    cdir = os.path.dirname(cand)
    for f in sorted(os.listdir(ref_dir)):
        p = os.path.join(ref_dir, f)
        if not os.path.isfile(p) or f.endswith('.asc') or f.lower().endswith(OUTPUT_EXT):
            continue
        q = os.path.join(cdir, f)
        if not os.path.exists(q):
            e5.append('support file missing beside candidate: %s' % f)
        elif sha(p) != sha(q):
            if f in graphics_only and asy_electrical(p) == asy_electrical(q):
                e5_info.append('%s: drawing changed (approved graphics-only); pins, pin order and electrical '
                               'attributes identical' % f)
            elif f in pins_moved and asy_electrical(p, True) == asy_electrical(q, True):
                e5_info.append('%s: drawing and pin positions changed (approved); pin names, pin order and electrical '
                               'attributes identical, connections proven by E1' % f)
            elif f in graphics_only or f in pins_moved:
                e5.append('%s: approved for drawing changes only, but its pins or electrical attributes changed' % f)
            else:
                e5.append('support file changed: %s' % f)
    report('E5 support files', not e5, e5 + e5_info if (e5 or e5_info) else
           ['all .asy/.lib files identical to the original'])

    if not keep:
        shutil.rmtree(rtmp, ignore_errors=True)
        shutil.rmtree(ctmp, ignore_errors=True)
    else:
        res['temp_dirs'] = [rtmp, ctmp]

    for name, r in res['checks'].items():
        print('%-28s %s' % (name, 'PASS' if r['pass'] else 'FAIL'))
        for d in r['details'][:60]:
            print('    ' + d)
        if len(r['details']) > 60:
            print('    ... %d more' % (len(r['details']) - 60))
    res['pass'] = not fails
    print('ELECTRICAL RESULT:', 'PASS' if not fails else 'FAIL (%s)' % ', '.join(fails))
    if out_json:
        json.dump(res, open(out_json, 'w'), indent=1)
    sys.exit(0 if not fails else 1)


if __name__ == '__main__':
    main()
