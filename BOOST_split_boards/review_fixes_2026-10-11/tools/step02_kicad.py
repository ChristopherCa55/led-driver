"""Step 2, KiCad documentation fixes (ANSWERS.md), in place on a SCRATCH KiCad folder. Text edits only: every
untouched byte stays as KiCad (or the user) saved it; the files' line endings are kept.

    python step02_kicad.py KICAD_DIR LOG.json

- D7: the 22 diodes valued "D" get their part name as Value (main page, board sheets, both PCBs). Their Sim.Params
  model="D" stays, so KiCad's simulation does not change.
- D7: J1-J8 Values become the wire labels Vin+ / Vin- / Out1+ ... (main page, power sheet, power PCB). On the PCB the
  label goes on F.SilkS at the JPOS spot (clear of pads), and the reference moves to F.Fab (kept for the BOM).
- D8: main-page title block (like the board sheets'); U26D (spare pot unit) one 12.7 mm slot right, clear of U106D,
  with its value under it.
"""
import json, math, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from step01_ltspice import PARTS

DIODES = {d: p for p, ds in PARTS.items() for d in ds}
JLAB = {'J1': 'Vin+', 'J2': 'Vin-', 'J3': 'Out1+', 'J4': 'Out1-', 'J8': 'Out2+', 'J7': 'Out2-', 'J5': 'Out3+',
        'J6': 'Out3-'}
NEWVAL = dict(DIODES, **JLAB)
# where each label sits on F.SilkS: board x, y (mm), text angle; None = exactly where the reference text was (J2 at
# (93.21, 73.93) 90, J3 (44.42, 109.69), J7 (39.3, 108.32), J8 (32.8, 108.32)). J1 moves up clear of C4 pad 2 (in
# line with Vin-), J4 goes above its own pad (its reference sat above J6), J6 goes above its pad, J5 stays vertical
# in the J6-J5 gap but hugs J5 (img/step02/silk_*_v1.png = before, _v2 = these spots).
# A string is the footprint-relative (at ...) itself: J4/J6 3.245 mm above the pad centre like J3, J5 2.974 mm left
# of its centre, J1 at x = Vin-'s x (93.205985) and y 80.6.
JPOS = {'J1': '-5.410222 -2.53933 90', 'J2': None, 'J3': None, 'J4': '3.245 0 0',
        'J5': '0 2.974 90', 'J6': '-3.245 0 0', 'J7': None, 'J8': None}
U26D_NC = [(121.92, 438.15), (121.92, 440.69), (121.92, 443.23)]   # no-connect flags on U26D's pins, move with it
TITLE = ['(title_block', '\t(title "BOOST LED driver - main schematic (both boards)")', '\t(rev "RC2")',
         '\t(comment 1 "Parts also drawn on the board schematics BOOST_power_RC2 / BOOST_control_RC2")', ')']


def fmt(v):
    return ('%.4f' % v).rstrip('0').rstrip('.')


def edit_sch(path, log, main=False):
    t = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    n = 0
    out, pos = [], 0
    for m in re.finditer(r'%s\t\(symbol%s(.*?)%s\t\)' % (re.escape(nl), re.escape(nl), re.escape(nl)), t, re.S):
        blk = m.group(1)
        rm = re.search(r'\(property "Reference" "([^"]+)"', blk)
        um = re.search(r'%s\t\t\(unit (\d+)\)' % re.escape(nl), blk)
        am = re.search(r'%s\t\t\(at ([-\d.]+) ([-\d.]+)' % re.escape(nl), blk)
        if not rm or not am:
            continue
        ref, unit = rm.group(1), int(um.group(1)) if um else 1
        new = blk
        if ref in NEWVAL:
            vm = re.search(r'\(property "Value" "([^"]*)"', new)
            if vm.group(1) != NEWVAL[ref]:
                log.append(dict(file=os.path.basename(path), what='Value', ref=ref, unit=unit,
                                at=[float(am.group(1)), float(am.group(2))], old=vm.group(1), new=NEWVAL[ref]))
                new = new[:vm.start(1)] + NEWVAL[ref] + new[vm.end(1):]
                n += 1
        if main and ref == 'U26' and unit == 4:
            sx, sy = float(am.group(1)), float(am.group(2))
            def sh(mm):
                return '%s(at %s %s' % (mm.group(1), fmt(float(mm.group(2)) + 12.7), mm.group(3))
            new = re.sub(r'(%s\t\t\t?)\(at ([-\d.]+) ([-\d.]+)' % re.escape(nl), sh, new)
            vm = re.search(r'(\(property "Value" "[^"]*"%s\t\t\t)\(at [-\d.]+ [-\d.]+' % re.escape(nl), new)
            new = new[:vm.start()] + vm.group(1) + '(at %s %s' % (fmt(sx + 12.7), fmt(sy + 7.62)) + new[vm.end():]
            log.append(dict(file=os.path.basename(path), what='symbol moved', ref='U26', unit=4, old=[sx, sy],
                            new=[sx + 12.7, sy], note='clear of U106D; value placed under it at (%s, %s)' % (
                                fmt(sx + 12.7), fmt(sy + 7.62))))
        if new != blk:
            out.append(t[pos:m.start(1)])
            out.append(new)
            pos = m.end(1)
    out.append(t[pos:])
    t = ''.join(out)
    if main:
        for x, y in U26D_NC:
            old = '(no_connect%s\t\t(at %s %s)' % (nl, fmt(x), fmt(y))
            assert t.count(old) == 1, old
            t = t.replace(old, '(no_connect%s\t\t(at %s %s)' % (nl, fmt(x + 12.7), fmt(y)))
            log.append(dict(file=os.path.basename(path), what='no-connect flag moved with U26D', old=[x, y],
                            new=[round(x + 12.7, 4), y]))
        assert '(title_block' not in t
        pm = re.search(r'%s(\t)\(paper "D"\)' % re.escape(nl), t)
        ind = pm.group(1)
        block = nl.join(ind + l for l in TITLE)
        t = t[:pm.end()] + nl + block + t[pm.end():]
        log.append(dict(file=os.path.basename(path), what='title block added', new=' / '.join(TITLE[1:4])))
    open(path, 'w', encoding='utf-8', newline='').write(t)
    return n


def edit_pcb(path, log):
    t = open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in t else '\n'
    N = re.escape(nl)
    n = 0
    for ref, val in NEWVAL.items():
        i = t.find('(property "Reference" "%s"' % ref)
        if i < 0:
            continue
        j = t.rfind(nl + '\t(footprint ', 0, i)
        k = t.find(nl + '\t\t(pad ', i)
        blk = t[j:k]
        at = re.search(N + r'\t\t\(at ([-\d.]+) ([-\d.]+)', blk)
        side = re.search(N + r'\t\t\(layer "([^"]+)"\)', blk).group(1)
        m = re.search(r'\(property "Value" "([^"]*)"', blk)
        old = m.group(1)
        blk = blk[:m.start(1)] + val + blk[m.end(1):]
        rec = dict(file=os.path.basename(path), what='Value', ref=ref, at=[float(at.group(1)), float(at.group(2))],
                   side=side, old=old, new=val)
        if ref in JLAB:
            rm = re.search(r'\(property "Reference" "%s"%s\t\t\t\(at ([^)]*)\)%s\t\t\t\(layer "F\.SilkS"\)' % (
                ref, N, N), blk)
            assert rm, ref
            blk = blk[:rm.start()] + rm.group(0).replace('(layer "F.SilkS")', '(layer "F.Fab")') + blk[rm.end():]
            vm = re.search(r'(\(property "Value" "%s"%s\t\t\t)\(at [^)]*\)(%s\t\t\t)\(layer "F\.Fab"\)(%s\t\t\t\(hide yes\))?' % (
                re.escape(val), N, N, N), blk)
            assert vm, ref
            # board position -> footprint-relative (KiCad: board = fp + R(rot) local, y down; text angle is absolute)
            fx, fy = float(at.group(1)), float(at.group(2))
            rot = float(re.search(N + r'\t\t\(at [-\d.]+ [-\d.]+ ?([-\d.]*)\)', blk).group(1) or 0)
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            if JPOS[ref] is None or isinstance(JPOS[ref], str):   # reference's own spot, or a given local (at)
                loc = rm.group(1) if JPOS[ref] is None else JPOS[ref]
                lx, ly, ang = (list(map(float, loc.split())) + [0.0])[:3]
                bx, by = round(fx + lx * c + ly * s, 3), round(fy - lx * s + ly * c, 3)
            else:
                bx, by, ang = JPOS[ref]
                dx, dy = bx - fx, by - fy
                lx, ly = dx * c - dy * s, dx * s + dy * c
                loc = '%s %s %s' % (fmt(lx), fmt(ly), fmt(ang))
            blk = blk[:vm.start()] + vm.group(1) + '(at %s)' % loc + vm.group(2) + '(layer "F.SilkS")' + blk[vm.end():]
            rec['silk'] = dict(text=val, layer='F.SilkS', board_xy=[bx, by], angle=ang, local=loc,
                               note='reference %s moved to F.Fab (kept for the BOM/assembly drawing)' % ref)
        t = t[:j] + blk + t[k:]
        n += 1
        log.append(rec)
    open(path, 'w', encoding='utf-8', newline='').write(t)
    return n


def main():
    d, logp = sys.argv[1], sys.argv[2]
    log = []
    print('main page values:', edit_sch(os.path.join(d, 'BOOST.kicad_sch'), log, main=True))
    print('power sheet values:', edit_sch(os.path.join(d, 'BOOST_power_RC2.kicad_sch'), log))
    print('card sheet values:', edit_sch(os.path.join(d, 'BOOST_control_RC2.kicad_sch'), log))
    print('power PCB:', edit_pcb(os.path.join(d, 'BOOST_power_RC2.kicad_pcb'), log))
    print('card PCB:', edit_pcb(os.path.join(d, 'BOOST_control_RC2.kicad_pcb'), log))
    json.dump(log, open(logp, 'w'), indent=1)


if __name__ == '__main__':
    main()
