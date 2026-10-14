"""Cross-match an LTspice netlist against a KiCad netlist: python xmatch.py LT.net KICAD.net [out.json]

Parts are paired by (class, value, pin roles -> anchored nets).  Anchors start as the net names both sides share
(plus GND=0, 5V=VDD); every pairing then anchors the unnamed nets on its pins, and the pass repeats until nothing
new pairs.  Interchangeable parts (e.g. several 100n VDD-GND capacitors) pair up in bulk.  Prints the pairs, the
parts left unpaired on each side, and any net conflicts.  Logic gates (A-devices / 74HC00/14), connectors, holes and
net ties are left out (net ties merge their two nets first).
"""
import re, sys, json, collections

KSRC = open(__file__.replace('xmatch2.py', 'kicad_netcompare.py'), encoding='utf-8').read().split('\nca, na = load')[0]
ns = {}; exec(KSRC, ns)
LSRC = open(__file__.replace('xmatch2.py', 'ltnet_compare.py'), encoding='utf-8').read().split('\nea, da = parse')[0]
ns2 = {}; exec(LSRC, ns2)

SI = {'f': 1e-15, 'p': 1e-12, 'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'meg': 1e6, 'g': 1e9, 't': 1e12}


def num(v):
    v = (v or '').strip().lower().replace('µ', 'u').replace('�', 'u').replace('μ', 'u')
    m = re.match(r'^([0-9]*\.?[0-9]+(?:e-?\d+)?)(meg|[fpnumkgt])?', v)
    if not m:
        return v
    return round(float(m.group(1)) * SI.get(m.group(2) or '', 1), 15)


KCLASS = [(r'^MCP6241', 'OPAMP'), (r'^MCP6561', 'CMP'), (r'^UCC21520', 'DRV'), (r'^INA241', 'INA'),
          (r'^LM2940', 'REG12'), (r'^L78L05|^L7805', 'REG5'), (r'^MCP4451', 'POT'), (r'4066', 'SW4066'),
          (r'4051', 'MUX'), (r'4017', 'CNT'), (r'^HYG180N10', 'M'), (r'^74HC00', 'G00'), (r'^74HC14', 'G14')]
# pin-name aliases per side and part class, so both sides use the same role names
K_ALIAS = {'INA': {'+': 'IN+', '-': 'IN-', 'REF1': 'REF', 'REF2': 'REF', '5': 'OUT'},
           'G00': {'A': 'IN', 'B': 'IN', 'VCC': 'NC', 'GND': 'NC'}, 'G14': {'A': 'IN', 'VCC': 'NC', 'GND': 'NC'},
           'MUX': {'A': 'COM', 'VCC': 'VDD'}, 'CNT': {'VSS': 'GND'}}
L_ALIAS = {'INA': {'VS': 'V+', 'REF1': 'REF', 'REF2': 'REF'}, 'DRV': {'VOUTA': 'OUTA', 'VOUTB': 'OUTB'},
           'CNT': {'CPN': 'CKEN', 'CP': 'CLK', 'MR': 'RESET', 'Q59': 'COUT', 'VSS': 'GND'},
           'MUX': dict([('A', 'S0'), ('B', 'S1'), ('C', 'S2'), ('INH', 'E'), ('IOC', 'COM'), ('VSS', 'GND')] +
                       [('IO%d' % i, 'A%d' % i) for i in range(8)])}


def kclass(ref, value):
    p = re.match(r'[A-Za-z#]+', ref).group(0)
    if p == 'Q':
        return 'Q', 0
    if p in ('R', 'C', 'L'):
        return p, num(value)
    if p == 'D':
        return ('TVS', 0) if 'SMDJ' in value or '5KP' in value else ('D', 0)
    if p == 'M':
        return 'M', 0
    for pat, cl in KCLASS:
        if re.search(pat, value or ''):
            return cl, 0
    return None, None


def lclass(name, rest):
    k = name[0].upper()
    tok = rest.split()[0] if rest else ''
    if k in 'RCL':
        return k, num(tok)
    if k == 'D':
        return ('TVS', 0) if 'TVS' in tok else (('LED', 0) if 'LED' in tok else ('D', 0))
    if k == 'Q':
        return 'Q', num('0')
    if k == 'A':
        return ('G00', 0) if tok.upper() == 'AND' else (('G14', 0) if tok.upper() == 'SCHMITT' else ('A', 0))
    if k == 'X' and tok.startswith('CSS4J'):
        m = re.search(r'\bR=(\S+)', rest)
        return 'R', num(m.group(1) if m else '1m')
    if k == 'X':
        for pat, cl in KCLASS:
            if re.search(pat, tok):
                return cl, 0
        return 'X:' + tok, 0
    if k == 'S':
        return 'SW', 0
    return k, 0


def norm_pin(p, alias=None):
    p = re.sub(r'_\d+$', '', p or '').upper()
    p = p.replace('~{', '').replace('}', '')
    return (alias or {}).get(p, p)


def load_kicad(path):
    comps, nets = ns['load'](path)
    t = open(path, encoding='utf-8').read()
    pf = {}
    for n in ns['blocks'](t[t.find('(nets'):], 'net'):
        for r, p, f in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)\s*\(pinfunction\s+"([^"]*)"\)', n):
            pf['%s.%s' % (r, p)] = f
    pin_net = {p: n for n, nodes in nets.items() for p in nodes}
    # net ties merge their nets
    alias = {}
    for r in comps:
        if r.startswith('NT'):
            a, b = pin_net['%s.1' % r], pin_net['%s.2' % r]
            keep, drop = (a, b) if not a.startswith('Net-(') else (b, a)
            alias[drop] = keep
    canon = lambda n: alias.get(n, n)
    parts = {}
    for r, c in comps.items():
        cl, val = kclass(r, c.get('value'))
        if cl is None:
            continue
        pins = []
        for p in sorted(x for x in pin_net if x.split('.')[0] == r):
            net = canon(pin_net[p])
            if net.startswith('unconnected-('):
                continue
            if cl in ('R', 'C', 'L'):
                role = 'p'
            elif cl in ('D', 'TVS'):
                role = 'K' if pf.get(p, '').startswith('-') else 'A'
            else:
                role = norm_pin(pf.get(p) or p.split('.')[1], K_ALIAS.get(cl))
            if role == 'NC':
                continue
            pins.append((role, net))
        if cl == 'MUX':      # the KiCad mux has VCC/GND; the model's VSS maps to GND already
            pass
        if cl == 'SW4066':
            tab = {'A': {1: 'A', 2: 'B', 13: 'CTRL'}, 'B': {3: 'A', 4: 'B', 5: 'CTRL'},
                   'C': {8: 'A', 9: 'B', 6: 'CTRL'}, 'D': {11: 'A', 10: 'B', 12: 'CTRL'}}
            for u, t in tab.items():
                ps = [(role, canon(pin_net['%s.%d' % (r, n)])) for n, role in t.items()]
                ps = [(x, y) for x, y in ps if not y.startswith('unconnected-(')]
                if ps:
                    ps += [('VDD', canon(pin_net['%s.14' % r])), ('VSS', canon(pin_net['%s.7' % r]))]
                    parts[r + u] = (cl, 0, sorted(set(ps)))
            continue
        if cl == 'POT':
            byu = collections.defaultdict(list)
            for role, net in pins:
                m_ = re.match(r'^P([0-3])([AWB])$', role)
                if m_:
                    byu['ABCD'[int(m_.group(1))]].append((m_.group(2), net))
                else:
                    byu['E'].append((role, net))
            for u, ps in byu.items():
                parts[r + u] = (cl, 0, sorted(set(ps)))
            continue
        if cl in ('G00', 'G14'):
            units = G_UNITS[cl]
            byu = collections.defaultdict(list)
            for p in sorted(x for x in pin_net if x.split('.')[0] == r):
                num_ = int(p.split('.')[1])
                u = next((k for k, v in units.items() if num_ in v), None)
                net = canon(pin_net[p])
                if u is None or net.startswith('unconnected-('):
                    continue
                role = 'Y' if num_ == units[u][-1] else 'IN'
                byu[u].append((role, net))
            for u, ps in byu.items():
                parts[r + u] = (cl, 0, sorted(set(ps)))
            continue
        parts[r] = (cl, val, sorted(set(pins)))
    return parts


G_UNITS = {'G00': {'A': (1, 2, 3), 'B': (4, 5, 6), 'C': (9, 10, 8), 'D': (12, 13, 11)},
           'G14': {'A': (1, 2), 'B': (3, 4), 'C': (5, 6), 'D': (9, 8), 'E': (11, 10), 'F': (13, 12)}}


def load_lt(path):
    el, _ = ns2['parse'](path)
    t = open(path, 'rb').read().decode('utf-8', 'replace')
    pn = dict(re.findall(r'^(\S+) .*;\S*pnba (.*)$', t, re.M))
    parts = {}
    for name, (nodes, rest) in el.items():
        cl, val = lclass(name, rest)
        if cl in ('A', 'V', 'B'):
            continue
        if cl in ('G00', 'G14'):
            ps = [('IN', n) for n in nodes[:5] if n != '0'] + [('Y', nodes[5])] + ([('YN', nodes[6])] if nodes[6] != '0' else [])
            parts[name] = (cl, 0, ps)
            continue
        if cl in ('R', 'C', 'L'):
            roles = ['p'] * len(nodes)
        elif cl in ('D', 'TVS', 'LED'):
            roles = ['A', 'K']
        elif cl == 'Q':
            roles = ['C', 'B', 'E', 'S'][:len(nodes)]
        elif cl == 'SW':
            roles = ['A', 'B', 'CTRL', 'CTRLREF']
        elif name in pn:
            roles = [norm_pin(x, L_ALIAS.get(cl)) for x in pn[name].split(')')]
            if cl == 'CNT' and len(roles) < len(nodes):
                roles += ['VDD', 'GND'][:len(nodes) - len(roles)]
        else:
            roles = ['%d' % i for i in range(len(nodes))]
        if cl == 'Q':
            roles, nodes = roles[:3], nodes[:3]
        pins = [(r_, n) for r_, n in zip(roles, nodes)]
        parts[name] = (cl, val, pins)
    # pins on nets used by only one pin in the whole netlist (dangling, e.g. unused 4017 outputs) do not count
    cnt = collections.Counter(n for nodes, _ in el.values() for n in nodes)
    for name, (cl, val, pins) in list(parts.items()):
        parts[name] = (cl, val, sorted(set((r_, n) for r_, n in pins if cnt[n] > 1 or n in ('0',) or n in globals().get('KNAMES', ()))))
    return parts


kc = load_kicad(sys.argv[2])
KNAMES = {n for _, _, ps in kc.values() for _, n in ps if not n.startswith('Net-(')}
lt = load_lt(sys.argv[1])
lt_nets = {n for _, _, ps in lt.values() for _, n in ps}
kc_nets = {n for _, _, ps in kc.values() for _, n in ps}
anchor = {}                     # kicad net -> lt net
low = {n.lower(): n for n in lt_nets}
for n in kc_nets:
    if not n.startswith('Net-(') and n.lower() in low:
        anchor[n] = low[n.lower()]
for k, l in (('GND', '0'), ('5V', 'VDD')):
    if k in kc_nets and l in lt_nets:
        anchor[k] = l
rev = {v: k for k, v in anchor.items()}
pairs, conflicts = {}, []


def sig(cl, val, pins, side):
    if side == 'k':
        m = [(r, anchor[n] if n in anchor else '?') for r, n in pins]
    else:
        m = [(r, n if n in rev else '?') for r, n in pins]
    return (cl, val, tuple(sorted(m)))


for rnd in range(30):
    new = 0
    ks = collections.defaultdict(list)
    ls = collections.defaultdict(list)
    for r, (cl, val, pins) in kc.items():
        if r not in pairs:
            ks[sig(cl, val, pins, 'k')].append(r)
    done_l = set(pairs.values())
    for n, (cl, val, pins) in lt.items():
        if n not in done_l:
            ls[sig(cl, val, pins, 'l')].append(n)
    for s, kr in ks.items():
        lr = ls.get(s)
        if not lr:
            continue
        if all(x[1] == '?' for x in s[2]) and (len(kr) > 1 or len(lr) > 1):
            continue                              # nothing anchored and ambiguous: wait
        if any(x[1] == '?' for x in s[2]) and (len(kr) > 1 or len(lr) > 1):
            continue                              # partly unanchored and ambiguous: wait
        for a, b in zip(sorted(kr), sorted(lr)):
            pairs[a] = b
            new += 1
            kp, lp = list(kc[a][2]), list(lt[b][2])
            if kc[a][0] in ('R', 'C', 'L') and len(kp) == len(lp) == 2:
                # symmetric parts: align the anchored pin first
                if kp[0][1] in anchor and anchor[kp[0][1]] == lp[1][1] or kp[1][1] in anchor and anchor[kp[1][1]] == lp[0][1]:
                    lp = [lp[1], lp[0]]
                zipped = list(zip(kp, lp))
            else:
                zipped = list(zip(sorted(kp), sorted(lp)))
            for (rk, nk), (rl, nl) in zipped:
                if nk in anchor:
                    if anchor[nk] != nl:
                        conflicts.append((a, b, rk, nk, anchor[nk], nl))
                elif nl in rev:
                    conflicts.append((a, b, rk, nk, '(anchored to %s)' % rev[nl], nl))
                else:
                    anchor[nk] = nl
                    rev[nl] = nk
    if not new:
        break

print('paired: %d of KiCad %d / LTspice %d simulated parts (after %d rounds)' % (len(pairs), len(kc), len(lt), rnd + 1))
uk = sorted(r for r in kc if r not in pairs)
ul = sorted(n for n in lt if n not in set(pairs.values()))
print('\nKiCad parts with no LTspice match (%d):' % len(uk))
for r in uk:
    cl, val, pins = kc[r]
    print('  %-6s %-7s %-10s %s' % (r, cl, val, ' '.join('%s=%s' % (a, anchor.get(b, b)) for a, b in pins)))
print('\nLTspice parts with no KiCad match (%d):' % len(ul))
for n in ul:
    cl, val, pins = lt[n]
    print('  %-12s %-7s %-10s %s' % (n, cl, val, ' '.join('%s=%s' % (a, rev.get(b, b)) for a, b in pins)))
print('\npaired parts whose designators differ:')
for k_, l_ in sorted(pairs.items()):
    ln = re.sub(r'^[A-Z]\W', '', l_)
    if ln != k_:
        print('  KiCad %-8s LTspice %s' % (k_, l_))
print('\nnet conflicts (%d):' % len(conflicts))
for c in conflicts[:40]:
    print('  KiCad %s / LT %s pin %s: KiCad net %s is anchored to %s but LT pin is on %s' % c)
if len(sys.argv) > 3:
    json.dump({'pairs': pairs, 'anchor': anchor, 'unmatched_kicad': uk, 'unmatched_lt': ul}, open(sys.argv[3], 'w'), indent=1)
