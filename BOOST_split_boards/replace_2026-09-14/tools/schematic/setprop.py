"""Set the Value and add hidden MPN / LCSC properties on placed symbols (text edit, verified).

  python setprop.py SCHEMATIC.kicad_sch REF Value=NEW [MPN=... LCSC=...] [--dry-run]

Finds every symbol block carrying that Reference (a multi-unit symbol has one block per unit and they must
stay identical), replaces each named property where it exists and adds it hidden at the unit's origin where
it does not. Refuses if the reference is missing or a property appears more than once in a block.
Line endings and every other byte are preserved.
"""
import sys, re

args = [a for a in sys.argv[1:] if a != '--dry-run']
dry = '--dry-run' in sys.argv
path, ref = args[0], args[1]
sets = dict(a.split('=', 1) for a in args[2:])
assert sets, 'nothing to set'
txt = open(path, encoding='utf8', newline='').read()

blocks = []
for m in re.finditer(r'\n\t\(symbol\r?\n\t\t\(lib_id ', txt):
    a = m.start() + 1
    depth, k, ins = 0, a, False
    while True:
        c = txt[k]
        if ins:
            if c == '\\':
                k += 1
            elif c == '"':
                ins = False
        elif c == '"':
            ins = True
        elif c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                break
        k += 1
    blocks.append((a, k + 1))

hits = [(a, b) for a, b in blocks if re.search(r'\(property "Reference" "%s"\r?\n' % re.escape(ref), txt[a:b])]
assert hits, '%s: no symbol block' % ref
if len(hits) > 1:
    print('%s: %d units, editing each' % (ref, len(hits)))

out = txt
for a, b in sorted(hits, reverse=True):          # back to front so earlier spans stay valid
    blk = txt[a:b]
    at = re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk)
    for name, value in sets.items():
        found = list(re.finditer(r'\(property "%s" "([^"]*)"' % re.escape(name), blk))
        assert len(found) <= 1, '%s: %d "%s" properties in one unit' % (ref, len(found), name)
        if found:
            old = found[0].group(1)
            if old == value:
                print('   %-5s %-6s already %s' % (ref, name, value))
                continue
            blk = blk.replace('(property "%s" "%s"' % (name, old), '(property "%s" "%s"' % (name, value), 1)
            print('   %-5s %-6s %s -> %s' % (ref, name, old, value))
        else:
            prop = ('\t\t(property "%s" "%s"\n\t\t\t(at %s %s 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n'
                    '\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n'
                    % (name, value, at.group(1), at.group(2)))
            i = blk.find('\t\t(pin ')
            if i < 0:
                i = blk.find('\t\t(instances')
            assert i > 0, 'nowhere to insert the property'
            blk = blk[:i] + prop + blk[i:]
            print('   %-5s + %-4s = %s' % (ref, name, value))
    out = out[:a] + blk + out[b:]

if dry:
    print('dry run: nothing written')
else:
    open(path, 'w', encoding='utf8', newline='').write(out)
    print('wrote %s' % path)
