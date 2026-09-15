"""Set the Footprint field of the given references in a KiCad schematic (text edit, verified).

  python setfp.py SCHEMATIC.kicad_sch LIB:FOOTPRINT REF [REF ...] [--dry-run]

Finds each placed symbol block by its Reference property, checks the block holds exactly one
Footprint property, replaces only that value, and refuses to write if any reference is missing,
duplicated, or would be left unchanged for a reason other than already having the footprint.
Line endings and every other byte are preserved.
"""
import sys, re

args = [a for a in sys.argv[1:] if a != '--dry-run']
dry = '--dry-run' in sys.argv
path, fp, refs = args[0], args[1], args[2:]
assert ':' in fp and refs, 'usage: setfp.py SCH LIB:FOOTPRINT REF [REF ...]'
txt = open(path, encoding='utf8', newline='').read()

# top-level placed symbols: "\n\t(symbol\n\t\t(lib_id ..." up to the matching close paren
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

edits = []
for ref in refs:
    hits = [(a, b) for a, b in blocks if re.search(r'\(property "Reference" "%s"\r?\n' % re.escape(ref), txt[a:b])]
    assert len(hits) == 1, '%s: %d symbol blocks' % (ref, len(hits))
    a, b = hits[0]
    blk = txt[a:b]
    fps = list(re.finditer(r'\(property "Footprint" "([^"]*)"', blk))
    assert len(fps) == 1, '%s: %d Footprint properties' % (ref, len(fps))
    old = fps[0].group(1)
    if old == fp:
        print('%-5s already %s' % (ref, fp))
        continue
    s, e = a + fps[0].start(1), a + fps[0].end(1)
    edits.append((s, e, ref, old))
for s, e, ref, old in sorted(edits, reverse=True):
    txt = txt[:s] + fp + txt[e:]
    print('%-5s %s -> %s' % (ref, old, fp))
if dry:
    print('dry run: nothing written')
elif edits:
    open(path, 'w', encoding='utf8', newline='').write(txt)
    print('wrote %s (%d footprints changed)' % (path, len(edits)))
