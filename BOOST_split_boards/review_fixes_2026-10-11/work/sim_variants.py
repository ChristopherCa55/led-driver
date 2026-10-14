"""Isolation variants of the step-5 LTspice change (scratch .asc files only).

    python sim_variants.py SRC.asc OUTDIR VARIANT      VARIANT = pullups | values | pullups_first
"""
import os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_2026-10-05', 'tools')))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 'tools')))
import ascmodel as A
import step05_ltspice as S

src, out, var = sys.argv[1:4]
os.makedirs(out)
for f in os.listdir(os.path.dirname(src)):
    if f.lower().endswith(('.asy', '.lib')):
        shutil.copy2(os.path.join(os.path.dirname(src), f), out)
a = A.Asc(src)
if var in ('values',):
    for s in a.syms:
        if s.name in S.VALUES:
            i = [k for k, _ in s.attrs].index('Value')
            s.attrs[i] = ('Value', S.VALUES[s.name][1])
if var in ('pullups', 'pullups_first'):
    new = []
    for ref, x, y, net in S.PULLUPS:
        px = x + 16
        new.append(A.Sym('res', x, y, 'R0', [('InstName', ref), ('Value', '4.7k')],
                         {0: (-16, 40, 'Right', 2), 3: (-16, 72, 'Right', 2)}))
        a.wires += [(px, y - 16, px, y + 16), (px, y + 96, px, y + 128)]
        a.flags += [[px, y - 16, '5V', None], [px, y + 128, net, None]]
    a.syms = (new + a.syms) if var == 'pullups_first' else (a.syms + new)
a.write(os.path.join(out, 'BOOST.asc'))
print('wrote', out, var)
