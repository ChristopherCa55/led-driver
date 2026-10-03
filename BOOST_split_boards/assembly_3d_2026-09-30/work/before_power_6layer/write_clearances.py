"""CLEARANCES.md from work/clearances.json (system Python). usage: python tools/write_clearances.py"""
import json

d = json.load(open('work/clearances.json'))
S = d['stack']
out = ['# BOOST assembly: clearances and substitutions (2026-09-30)', '',
       'From `tools/build_assembly.py`: the two release-candidate boards (KiCad STEP export) in the case, with every '
       'part that has no 3D model replaced by a dimensioned solid. Distances are exact solid-to-solid minimums '
       '(OpenCASCADE BRepExtrema), in mm. **Under 1 mm is flagged.**', '',
       '## Stack used (height above the case floor, mm)', '',
       '| Item | Z |', '|---|---|',
       '| Thermal pad top = FET tab | %.2f |' % S['pad'],
       '| Power board underside (5.0 stud + 0.5 washer) | %.2f |' % S['power_underside'],
       '| Power board top as modelled (board files: 1.654 thick) | %.3f |' % S['power_top_model'],
       '| Female-female standoff, on the nominal 1.6 mm board | %.2f - %.2f |' % tuple(S['ff_standoff']),
       '| J10 ESQ body top | %.3f |' % S['esq_top'],
       '| J11 TSW insulator underside | %.2f |' % S['tsw_bottom'],
       '| Control card underside (+1.5 mm of washers) | %.2f |' % S['card_underside'],
       '| Control card top as modelled (board file: 1.547 thick, 6 layers, 0.5 oz inner) | %.3f |' % S['card_top_model'],
       '| Lid underside | %.2f |' % S['lid'], '',
       'The boards are modelled at their board-file thickness (copper + dielectric): the 8-layer power board 1.654 mm, '
       'the 6-layer card 1.547 mm (0.5 oz inner copper, from 2026-10-01). The stack uses the nominal 1.6. So '
       'everything on the power board sits 0.054 mm higher than nominal, which makes the clearances to the card '
       'pessimistic by that much. The card top sits 0.053 mm lower than nominal; the lid-to-card-part clearances '
       'below use the modelled 1.547 mm.', '']
groups = []
for r in d['rows']:
    if not groups or groups[-1][0] != r['check']:
        groups.append((r['check'], []))
    groups[-1][1].append(r)
out += ['## Clearance table', '']
for check, rows in groups:
    out += ['### ' + check[0].upper() + check[1:], '', '| Item | Nearest | mm | Flag | Note |', '|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: (r['mm'] if r['mm'] is not None else 1e9)):
        out.append('| %s | %s | %s | %s | %s |' % (r['a'], r['b'], '%.2f' % r['mm'] if r['mm'] is not None else '-',
                                                   ('**' + r['flag'].strip() + '**') if r['flag'].strip() else '',
                                                   r['note']))
    out.append('')
out += ['## What was substituted, and from which source', '', '| Item | Source |', '|---|---|']
for w, s in d['substitutes']:
    out.append('| %s | %s |' % (w, s))
out += ['', 'Also substituted: the KiCad generic 2x15 socket/header models on J10 and J11 were removed (they are 8.5 mm '
        'parts, not the Samtec pair). Everything else is the KiCad library model on its footprint. R1 and L1 had no '
        'model. J1-J8 and J9 are wire pads (no part), and H1-H8 are holes.', '']
open('CLEARANCES.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('wrote CLEARANCES.md,', len(d['rows']), 'rows')
