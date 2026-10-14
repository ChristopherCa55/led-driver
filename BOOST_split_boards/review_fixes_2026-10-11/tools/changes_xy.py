"""CHANGES_XY.md: every changed item with its x / y and layer, step by step, for the user's review.

    python changes_xy.py WORK_DIR STEPS.json OUT.md

STEPS.json: [{"step": "Step 3", "title": "...", "status": "in the copy" | "waiting for your OK" | ...,
              "ltspice": "path/to/changes.txt" (lines 'what at (x, y): ...'),
              "sch": "path/to/changes.json" (step02_kicad / step05_kicad_sch logs),
              "pcb": [["power" | "card", "BEFORE.kicad_pcb", "AFTER.kicad_pcb"], ...]}, ...]
Board items come from tools/pcb_diff.py (the files themselves, not the specs). Units: KiCad mm, y downwards, as in
KiCad's status bar; LTspice items are in LTspice schematic units, as LTspice shows them.
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def sch_lines(log):
    out = []
    for r in log:
        f = r.get('file', '')
        page = {'BOOST.kicad_sch': 'main page', 'BOOST_power_RC2.kicad_sch': 'power board sheet',
                'BOOST_control_RC2.kicad_sch': 'card sheet'}.get(f, f)
        w = r['what']
        if w == 'Value':
            if 'silk' in r:
                s = r['silk']
                out.append('| %s (PCB) | %s | footprint at (%g, %g) | Value "%s" -> "%s"; label "%s" on **F.SilkS** at '
                           '(%g, %g), %g deg; reference text moved to F.Fab |' % (
                               f.replace('.kicad_pcb', ''), r['ref'], r['at'][0], r['at'][1], r['old'], r['new'],
                               s['text'], s['board_xy'][0], s['board_xy'][1], s['angle']))
            elif f.endswith('.kicad_pcb'):
                out.append('| %s (PCB) | %s | footprint at (%g, %g), %s | Value "%s" -> "%s" |' % (
                    f.replace('.kicad_pcb', ''), r['ref'], r['at'][0], r['at'][1], r.get('side', ''), r['old'],
                    r['new']))
            else:
                at = ('(%g, %g)' % tuple(r['at'])) if 'at' in r else ''
                out.append('| %s | %s%s | %s | Value "%s" -> "%s" |' % (
                    page, r['ref'], (' unit %s' % r['unit']) if r.get('unit', 1) != 1 else '', at, r['old'],
                    r['new']))
        elif w == 'symbol moved':
            out.append('| %s | U26 unit %s | (%g, %g) -> (%g, %g) | moved one slot right; %s |' % (
                page, r['unit'], r['old'][0], r['old'][1], r['new'][0], r['new'][1], r['note']))
        elif w.startswith('no-connect'):
            out.append('| %s | no-connect flag | (%g, %g) -> (%g, %g) | %s |' % (
                page, r['old'][0], r['old'][1], r['new'][0], r['new'][1], w))
        elif w == 'title block added':
            out.append('| %s | title block | (sheet corner) | added: %s |' % (page, r['new'].replace('\t', '')))
        elif w == 'part added':
            out.append('| %s | %s %s | (%g, %g) | added; pins (%g, %g) / (%g, %g); wires %s; global labels %s |' % (
                page, r['ref'], r['value'], r['at'][0], r['at'][1], r['pins'][0][0], r['pins'][0][1],
                r['pins'][1][0], r['pins'][1][1],
                ', '.join('(%g, %g)-(%g, %g)' % tuple(x) for x in r['wires']),
                ', '.join('%s at (%g, %g)' % tuple(x) for x in r['labels'])))
        elif w == 'note added':
            out.append('| %s | note | (%g, %g) | added: "%s" |' % (page, r['at'][0], r['at'][1],
                                                                 r['text'].replace('\\n', ' / ')))
        else:
            out.append('| %s | %s | | %s |' % (page, r.get('ref', ''), json.dumps(r)))
    return out


def main():
    work, stepsp, outp = sys.argv[1:4]
    steps = json.load(open(stepsp))
    md = ['# Every change, with x / y and layer (review fixes, 2026-10-11)', '',
          'KiCad positions are in mm as KiCad shows them (y grows downwards). LTspice positions are LTspice '
          'schematic units. Board lists come from comparing the board files themselves (tools/pcb_diff.py).', '']
    for s in steps:
        md += ['## %s: %s' % (s['step'], s['title']), '', '**Status:** %s' % s['status'], '']
        if s.get('ltspice'):
            md += ['LTspice (`LTspice/BOOST.asc`):', '', '| change |', '|---|']
            for l in open(os.path.join(work, s['ltspice']), encoding='utf-8'):
                l = l.strip()
                if l and not l.startswith('wrote'):
                    md.append('| %s |' % l.replace('|', '/'))
            md.append('')
        if s.get('sch'):
            md += ['KiCad schematics and footprint values:', '', '| file | item | at | change |', '|---|---|---|---|']
            md += sch_lines(json.load(open(os.path.join(work, s['sch']))))
            md.append('')
        for board, a, b in s.get('pcb', []):
            r = subprocess.run([sys.executable, os.path.join(HERE, 'pcb_diff.py'), os.path.join(work, a),
                                os.path.join(work, b), '--title', '%s board' % board], capture_output=True, text=True)
            md += [r.stdout.replace('### ', '#### '), '']
        for extra in s.get('notes', []):
            md.append('- ' + extra)
        if s.get('notes'):
            md.append('')
    open(outp, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('wrote', outp)


if __name__ == '__main__':
    main()
