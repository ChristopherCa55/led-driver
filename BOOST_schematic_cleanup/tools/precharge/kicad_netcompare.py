"""Compare two KiCad netlists (kicad-cli sch export netlist) completely: python kicad_netcompare.py REF.net NEW.net

Per component (by reference): value, footprint, datasheet, description, every (field ...), every (property ...),
the library symbol (libsource lib/part) and the symbol UUID (tstamps) that links it to its board footprint.
Per net: the set of ref.pin nodes; a net with the same pins under a new name is reported as a rename.
"""
import re, sys


def blocks(text, head):
    """Top-level '(head ...' s-expression blocks, balanced by parentheses."""
    out, i = [], 0
    key = '(' + head
    while True:
        i = text.find(key, i)
        if i < 0:
            return out
        if not re.match(r'\(%s[\s)]' % head, text[i:i + len(head) + 2]):
            i += 1
            continue
        depth, j = 0, i
        while True:
            c = text[j]
            if c == '"':
                j += 1
                while text[j] != '"':
                    j += 2 if text[j] == '\\' else 1
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append(text[i:j + 1])
        i = j + 1


def fields_of(comp):
    d = {}
    for k in ('ref', 'value', 'footprint', 'datasheet', 'description'):
        m = re.search(r'\(%s\s+"((?:[^"\\]|\\.)*)"\)' % k, comp)
        d[k] = m.group(1) if m else None
    for n, v in re.findall(r'\(field\s+\(name\s+"((?:[^"\\]|\\.)*)"\)\s*"((?:[^"\\]|\\.)*)"\)', comp):
        d['field:' + n] = v
    for n, v in re.findall(r'\(property\s+\(name\s+"((?:[^"\\]|\\.)*)"\)\s*\(value\s+"((?:[^"\\]|\\.)*)"\)\)', comp):
        d['property:' + n] = v
    for n in re.findall(r'\(property\s+\(name\s+"((?:[^"\\]|\\.)*)"\)\)', comp):
        d['property:' + n] = '(set)'
    m = re.search(r'\(libsource\s+\(lib\s+"([^"]*)"\)\s*\(part\s+"([^"]*)"\)', comp)
    d['libsource'] = '%s:%s' % m.groups() if m else None
    m = re.search(r'\(sheetpath\s+\(names\s+"([^"]*)"\)\s*\(tstamps\s+"([^"]*)"\)\)', comp)
    d['sheetpath'] = '%s %s' % m.groups() if m else None
    rest = comp[:m.start()] + comp[m.end():] if m else comp
    d['uuid'] = ' '.join(re.findall(r'\(tstamps\s+"([^"]*)"\)', rest)) or None
    return d


def load(path):
    t = open(path, encoding='utf-8').read()
    comps = {}
    cb = t[t.find('(components'):t.find('(libparts') if '(libparts' in t else t.find('(nets')]
    for c in blocks(cb, 'comp'):
        f = fields_of(c)
        comps[f['ref']] = f
    nets = {}
    nb = t[t.find('(nets'):]
    for n in blocks(nb, 'net'):
        name = re.search(r'\(name\s+"((?:[^"\\]|\\.)*)"\)', n).group(1)
        nodes = frozenset('%s.%s' % p for p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', n))
        nets[name] = nodes
    return comps, nets


ca, na = load(sys.argv[1])
cb_, nb = load(sys.argv[2])
issues = 0
print('components: %d -> %d' % (len(ca), len(cb_)))
for r in sorted(set(ca) - set(cb_)):
    issues += 1; print('  REMOVED', r, ca[r].get('value'))
for r in sorted(set(cb_) - set(ca)):
    issues += 1; print('  ADDED  ', r, cb_[r].get('value'))
field_changes = 0
for r in sorted(set(ca) & set(cb_)):
    a, b = ca[r], cb_[r]
    for k in sorted(set(a) | set(b)):
        if a.get(k) != b.get(k):
            field_changes += 1
            print('  %-6s %-22s %r -> %r' % (r, k, a.get(k), b.get(k)))
print('field differences: %d' % field_changes)
issues += field_changes
print('nets: %d -> %d' % (len(na), len(nb)))
by_nodes_b = {v: k for k, v in nb.items()}
matched, renamed, changed = set(), 0, 0
for name, nodes in sorted(na.items()):
    if nb.get(name) == nodes:
        matched.add(name); continue
    if nodes in by_nodes_b:
        renamed += 1; print('  net renamed: %s -> %s (%d pins, same pins)' % (name, by_nodes_b[nodes], len(nodes)))
        matched.add(by_nodes_b[nodes]); continue
    changed += 1
    best = max(nb.items(), key=lambda kv: len(kv[1] & nodes))
    print('  NET CHANGED %s -> %s: added %s removed %s' % (name, best[0], sorted(best[1] - nodes), sorted(nodes - best[1])))
    matched.add(best[0])
for name in sorted(set(nb) - matched):
    changed += 1; print('  NEW NET %s %s' % (name, sorted(nb[name])))
print('nets with the same pins: %d; renamed: %d; changed/new: %d' % (len(na) - renamed - changed, renamed, changed))
issues += changed
print('RESULT:', 'IDENTICAL CONNECTIONS AND FIELDS' if issues == 0 and renamed == 0 else
      ('same connections and fields; %d net renames' % renamed if issues == 0 else '%d differences' % issues))
