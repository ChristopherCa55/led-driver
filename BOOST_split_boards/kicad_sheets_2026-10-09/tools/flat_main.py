"""One main schematic again (the user's request, 2026-10-10): BOOST.kicad_sch = the v3 single page (like LTspice,
connectors included); BOOST_power_RC2.kicad_sch / BOOST_control_RC2.kicad_sch stay as the board projects' own
schematics (linked to their PCBs). The board sheets are no longer sheets of BOOST, so their "BOOST" instance
entries go.

    python flat_main.py          BOOST_package/KiCad (as shipped) -> ../work_flat/
"""
import os, sys, re, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..'))
SB = os.path.normpath(os.path.join(BASE, '..'))
sys.path.insert(0, os.path.join(SB, 'kicad_layout_2026-10-09', 'tools'))
from sexpr import parse, dump, find, findall, unq

SRC = os.path.normpath(os.path.join(SB, '..', 'BOOST_package', 'KiCad'))
V3 = os.path.join(SB, 'kicad_layout_2026-10-09', 'work', 'BOOST_v3.kicad_sch')
OUT = os.path.join(BASE, 'work_flat')
SKIP = ('.history', '-backups', '.kicad_prl', '.lck')
ROOT_UUID = 'dc4aa17e-0995-4bac-889e-471ae16ef44e'


def main():
    if os.path.exists(OUT):
        raise SystemExit('%s exists' % OUT)
    shutil.copytree(SRC, OUT, ignore=lambda d, names: [n for n in names if any(s in n for s in SKIP)])
    # the main page: v3, with the gate simulation fields the board sheets now carry
    shutil.copy(V3, os.path.join(OUT, 'BOOST.kicad_sch'))
    subprocess.run([sys.executable, os.path.join(HERE, 'set_gate_sim.py'), os.path.join(OUT, 'BOOST.kicad_sch')],
                   check=True)
    # BOOST.kicad_pro: the sheets list back to the root alone
    p = os.path.join(OUT, 'BOOST.kicad_pro')
    d = json.load(open(p, encoding='utf-8'))
    assert d['sheets'][0][0] == ROOT_UUID, d['sheets']
    t = open(p, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    i = t.index('"sheets": [')
    j = t.index(nl + '  ]', i)
    t = t[:i] + '"sheets": [' + nl + '    [' + nl + '      "%s",' % ROOT_UUID + nl + '      ""' + nl + '    ]' + t[j:]
    d2 = json.loads(t)
    assert d2['sheets'] == [[ROOT_UUID, '']] and d2['schematic']['top_level_sheets'][0]['uuid'] == ROOT_UUID
    open(p, 'w', encoding='utf-8', newline='').write(t)
    # board sheets: drop the instance entries of project "BOOST" (keep their own project's)
    for f in ('BOOST_power_RC2', 'BOOST_control_RC2'):
        sp = os.path.join(OUT, f + '.kicad_sch')
        root = parse(open(sp, encoding='utf-8').read())
        n = 0
        for s in findall(root, 'symbol'):
            inst = find(s, 'instances')
            if not inst:
                continue
            keep = [c for c in inst if not (isinstance(c, list) and c[0] == 'project' and unq(c[1]) == 'BOOST')]
            n += len(inst) - len(keep)
            assert any(isinstance(c, list) and c[0] == 'project' and unq(c[1]) == f for c in keep), f
            inst[:] = keep
        open(sp, 'w', encoding='utf-8', newline='\n').write(dump(root) + '\n')
        print('%s: %d "BOOST" instance entries removed' % (f, n))
    print('wrote', OUT)


if __name__ == '__main__':
    main()
