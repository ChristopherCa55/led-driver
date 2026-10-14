"""Stage the v3 KiCad schematic for the three shipped folders (the user's OK, 2026-10-09).

    python ship_stage.py

ship/base/  = BOOST_stuff/KiCad as it is now (for before/after checks)
ship/stage/ = the same, with
    BOOST.kicad_sch             <- work/BOOST_v3.kicad_sch (the user's layout)
    ltspice.kicad_sym           <- work/ltspice.kicad_sym (remade symbols)
    BOOST_control_RC2.kicad_pcb <- the 4 nets renamed like the schematic (copper unchanged)
"""
import os, shutil, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..'))
SRC = os.path.normpath(os.path.join(BASE, '..', '..', 'BOOST_stuff', 'KiCad'))
SHIP = os.path.join(BASE, 'ship')
RENAMES = {'Net-(U102B-A)': 'OUT_1_ENA', 'Net-(U102C-A)': 'OUT_2_ENA', 'Net-(U103A-A)': 'OUT_3_ENA',
           'Net-(U18-Q3)': '4'}
SKIP = ('.history', '-backups', '.kicad_prl', '.lck')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()[:8]


def copy_tree(dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(SRC, dst, ignore=lambda d, names: [n for n in names if any(s in n for s in SKIP)])


def main():
    copy_tree(os.path.join(SHIP, 'base'))
    stage = os.path.join(SHIP, 'stage')
    copy_tree(stage)
    shutil.copy(os.path.join(BASE, 'work', 'BOOST_v3.kicad_sch'), os.path.join(stage, 'BOOST.kicad_sch'))
    shutil.copy(os.path.join(BASE, 'work', 'ltspice.kicad_sym'), os.path.join(stage, 'ltspice.kicad_sym'))
    pcb = os.path.join(stage, 'BOOST_control_RC2.kicad_pcb')
    txt = open(pcb, encoding='utf-8', newline='').read()          # keep the file's CRLF line ends
    for old, new in RENAMES.items():
        assert txt.count('(net "%s")' % new) == 0, ('name already used', new)
        n_all = txt.count('"%s"' % old)
        n = txt.count('(net "%s")' % old)
        assert n and n == n_all, (old, n, n_all)          # every use is a (net "...") reference
        txt = txt.replace('(net "%s")' % old, '(net "%s")' % new)
        print('%-15s -> %-10s %d references' % (old, new, n))
    open(pcb, 'w', encoding='utf-8', newline='').write(txt)
    for f in ('BOOST.kicad_sch', 'ltspice.kicad_sym', 'BOOST_control_RC2.kicad_pcb', 'BOOST_power_RC2.kicad_pcb'):
        print('%-28s base %s  stage %s' % (f, sha(os.path.join(SHIP, 'base', f)), sha(os.path.join(stage, f))))


if __name__ == '__main__':
    main()
