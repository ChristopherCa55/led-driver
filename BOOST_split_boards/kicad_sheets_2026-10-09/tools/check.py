"""All checks on a copy of a finished KiCad folder (default ../work); nothing in the folder is written.

    python check.py [DIR]

  netlists: system (root) against the shipped single-sheet netlist (ref.xml), and each board project alone against
            the same netlist restricted to that board's parts (values, footprints, fields, pin groups, net names)
  ERC:      system, power project, card project
  DRC:      both boards with --schematic-parity
  gerbers:  both boards against before_link/ (the boards as shipped), fab options, date lines ignored
"""
import os, sys, json, shutil, subprocess, tempfile, glob, collections, filecmp
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(BASE, '..', 'kicad_layout_2026-10-09', 'tools'))
import knet
import split_sheets as SS

K = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'work')


def cli(*a):
    subprocess.run([K] + list(a), capture_output=True)


def main():
    T = tempfile.mkdtemp(prefix='sheetchk_')
    for f in glob.glob(os.path.join(D, '*')):
        (shutil.copytree if os.path.isdir(f) else shutil.copy)(f, os.path.join(T, os.path.basename(f)))
    A = json.load(open(SS.ASSIGN))
    c1, n1 = knet.read(os.path.join(BASE, 'ref.xml'))
    ok = True
    for proj, board in (('BOOST', None), ('BOOST_power_RC2', 'POWER'), ('BOOST_control_RC2', 'CONTROL')):
        x = os.path.join(T, proj + '.xml')
        cli('sch', 'export', 'netlist', '--format', 'kicadxml', '-o', x, os.path.join(T, proj + '.kicad_sch'))
        c2, n2 = knet.read(x)
        refs = {r for r in c1 if board is None or A.get(r) == board}
        s1 = {}
        for k, v in n1.items():
            ms = frozenset((r, p) for r, p, _, _ in v if r in refs)
            if ms:
                s1.setdefault(ms, set()).add(k)
        s2 = {frozenset((r, p) for r, p, _, _ in v): k for k, v in n2.items()}
        bad = [k for k in set(s1) | set(s2) if s2.get(k) not in (s1.get(k) or {None})]
        fields = [r for r in c2 if c1.get(r) != c2[r]]
        same = set(c2) == refs and not fields and not bad
        ok &= same
        rpt = os.path.join(T, proj + '_erc.rpt')
        cli('sch', 'erc', '--severity-all', '-o', rpt, os.path.join(T, proj + '.kicad_sch'))
        erc = [l.strip() for l in open(rpt, encoding='utf-8') if l.startswith('[')]
        print('%-18s parts %d/%d, nets %d/%d, differing nets %d, differing fields %d -> %s | ERC %d %s'
              % (proj, len(c2), len(refs), len(s2), len(s1), len(bad), len(fields), 'SAME' if same else 'DIFFERENT',
                 len(erc), dict(collections.Counter(e.split(']')[0] + ']' for e in erc))))
    for b in ('BOOST_power_RC2', 'BOOST_control_RC2'):
        j = os.path.join(T, b + '_drc.json')
        cli('pcb', 'drc', '--severity-all', '--schematic-parity', '--format', 'json', '-o', j, os.path.join(T, b + '.kicad_pcb'))
        d = json.load(open(j, encoding='utf-8'))
        print('%-18s DRC %d %s, unconnected %d, parity %d' % (b, len(d['violations']),
              dict(collections.Counter(v['type'] for v in d['violations'])), len(d['unconnected_items']),
              len(d['schematic_parity'])))
        old = os.path.join(BASE, 'before_link', b + '.kicad_pcb')
        if os.path.exists(old):
            res = []
            for tag, src in (('old', old), ('new', os.path.join(T, b + '.kicad_pcb'))):
                o = os.path.join(T, 'g_%s_%s' % (tag, b))
                s = os.path.join(T, 's_%s_%s' % (tag, b))
                os.makedirs(o)
                os.makedirs(s)
                for f in (src, os.path.join(T, b + '.kicad_pro'), os.path.join(T, b + '.kicad_dru')):
                    shutil.copy(f, s)
                cli('pcb', 'export', 'gerbers', '--no-x2', '--no-netlist', '--subtract-soldermask', '-o', o,
                    os.path.join(s, b + '.kicad_pcb'))
                res.append(o)
            files = sorted(os.listdir(res[0]))
            strip = lambda p: [l for l in open(p, encoding='utf-8', errors='replace') if 'CreationDate' not in l and
                               'G04 Created' not in l]
            diff = [f for f in files if strip(os.path.join(res[0], f)) != strip(os.path.join(res[1], f))]
            print('%-18s gerbers: %d files, %d differ %s' % (b, len(files), len(diff), diff))
    shutil.rmtree(T, ignore_errors=True)
    print('NETLISTS', 'SAME' if ok else 'DIFFERENT')


if __name__ == '__main__':
    main()
