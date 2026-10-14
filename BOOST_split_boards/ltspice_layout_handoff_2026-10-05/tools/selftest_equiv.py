"""Self-test for ltspice_equiv.py: build deliberately damaged copies of the original and confirm each is caught.

    python selftest_equiv.py

Each case is written to a temp folder (with the original .asy/.lib files), checked, and deleted. The approved
battery/cable rename must PASS; every other case must FAIL on the named check.
"""
import os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.normpath(os.path.join(HERE, '..', 'reference', 'LTspice_original'))
sys.path.insert(0, HERE)
from ascgeo import Asc


def load():
    return open(os.path.join(REF, 'BOOST.asc'), encoding='latin-1').read().split('\n')


def swap_resistor_pins(lines):
    """Re-place a vertical R0 resistor as R180 shifted so its two pins trade places (same points, reversed order)."""
    for i, l in enumerate(lines):
        if l.startswith('SYMBOL res ') and l.endswith(' R0') and 'InstName R3' in lines[i + 1:i + 4].__str__():
            _, sym, x, y, rot = l.split(' ')
            lines[i] = 'SYMBOL res %d %d R180' % (int(x) + 32, int(y) + 112)
            return lines, 'R3 pin order reversed'
    for i, l in enumerate(lines):
        if l.startswith('SYMBOL res ') and l.endswith(' R0'):
            _, sym, x, y, rot = l.split(' ')
            lines[i] = 'SYMBOL res %d %d R180' % (int(x) + 32, int(y) + 112)
            name = next(t.split()[-1] for t in lines[i + 1:i + 6] if t.startswith('SYMATTR InstName'))
            return lines, '%s pin order reversed' % name
    raise SystemExit('no R0 resistor found')


def rename_label(lines):
    for i, l in enumerate(lines):
        if l.startswith('FLAG ') and l.endswith(' SRV1'):
            lines[i] = l[:-4] + 'SRV_1'
            return lines, 'label SRV1 renamed SRV_1'


def delete_comment(lines):
    for i, l in enumerate(lines):
        if l.startswith('TEXT ') and ';Start-up state' in l:
            del lines[i]
            return lines, 'start-up comment deleted'


def change_value(lines):
    for i, l in enumerate(lines):
        if l == 'SYMATTR InstName R3':
            for j in range(i, i + 4):
                if lines[j] == 'SYMATTR Value 620k':
                    lines[j] = 'SYMATTR Value 621k'
                    return lines, 'R3 620k -> 621k'
    raise SystemExit('R3 value line not found')


def approved_rename(lines):
    m = {'SIM_VBATT': 'SIM_BATTERY', 'SIM_RCABLE': 'SIM_CABLE_RESISTANCE', 'SIM_LCABLE': 'SIM_CABLE_INDUCTANCE'}
    for i, l in enumerate(lines):
        if l.startswith('SYMATTR InstName ') and l.split()[-1] in m:
            lines[i] = 'SYMATTR InstName ' + m[l.split()[-1]]
    return lines, 'approved battery/cable renames'


def rename_5v(lines):
    for i, l in enumerate(lines):
        if l.startswith('FLAG ') and l.endswith(' 5V'):
            lines[i] = l[:-2] + '5V_D'
    return lines, 'every 5V label renamed 5V_D (U18 would lose its supply)'


CASES = [(approved_rename, 'PASS', None), (swap_resistor_pins, 'FAIL', 'E1'), (rename_label, 'FAIL', 'E1'),
         (delete_comment, 'FAIL', 'E3'), (change_value, 'FAIL', 'E1'), (rename_5v, 'FAIL', 'E2')]

ok_all = True
for fn, want, check in CASES:
    tmp = tempfile.mkdtemp(prefix='eqtest_')
    for f in os.listdir(REF):
        if f != 'BOOST.asc':
            shutil.copy2(os.path.join(REF, f), tmp)
    lines, what = fn(load())
    open(os.path.join(tmp, 'BOOST.asc'), 'w', encoding='latin-1', newline='\n').write('\n'.join(lines))
    p = subprocess.run([sys.executable, os.path.join(HERE, 'ltspice_equiv.py'), os.path.join(tmp, 'BOOST.asc')],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = p.stdout
    got = 'PASS' if p.returncode == 0 else 'FAIL'
    failed = re.findall(r'^(E\d) .*FAIL$', out, re.M)
    good = got == want and (check is None or check in failed)
    ok_all &= good
    print('%-4s %-62s expected %s%s, got %s %s' % ('ok' if good else 'BAD', what, want,
          ' on ' + check if check else '', got, ','.join(failed)))
    shutil.rmtree(tmp, ignore_errors=True)
print('SELF-TEST', 'PASSED' if ok_all else 'FAILED')
sys.exit(0 if ok_all else 1)
