"""Copy the remade symbols (remade_symbols.py) into a project symbol library, so the schematic matches its library.

    python update_lib.py SRC.kicad_sym OUT.kicad_sym      (OUT must not exist yet)
"""
import os, sys, copy
from sexpr import parse, dump, find, findall, unq, q
import build_kicad as BK

CHANGED = ['74HC00_conv', '74HC14_conv', 'CD4066_conv', 'LM2940_12', 'OpAmps/opamp2', 'GND']


def main(src, out):
    if os.path.exists(out):
        raise SystemExit('%s exists: not overwritten' % out)
    b = BK.Builder()
    lib = parse(open(src, encoding='utf-8').read())
    done = []
    for i, c in enumerate(lib):
        if isinstance(c, list) and c[0] == 'symbol' and unq(c[1]) in CHANGED:
            name = unq(c[1])
            new = copy.deepcopy(b.libs['ltspice:' + name])
            new[1] = q(name)
            lib[i] = new
            done.append(name)
    missing = set(CHANGED) - set(done)
    if missing:
        raise SystemExit('not in the library: %s' % sorted(missing))
    open(out, 'w', encoding='utf-8', newline='\n').write(dump(lib) + '\n')
    print('replaced', done, '->', out)


if __name__ == '__main__':
    main(*sys.argv[1:3])
