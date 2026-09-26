"""Build the power-copper check-in page from the solver results (system Python).

usage: python build_review.py VERSION   (reads work/VERSION_B.json, work/VERSION_C.json, work/VERSION_L.json)
writes ../copper_review_2026-09-16/BOOST_power_copper_review.html
"""
import json, sys, os, html

V = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(ROOT), 'copper_review_2026-09-16', 'BOOST_power_copper_review.html')
B = {r['name']: r for r in json.load(open(os.path.join(ROOT, 'work', V + '_B.json')))}
C = {r['name']: r for r in json.load(open(os.path.join(ROOT, 'work', V + '_C.json')))}
L = json.load(open(os.path.join(ROOT, 'work', V + '_L.json')))

GROUPS = [
    ('Input loop', ['Vin J1->R1 (DC)', 'Vin caps->R1 (ripple)', 'rsense_lo R1->L1', 'GND M1->input caps+J2']),
    ('Switch node', ['LX L1->M1', 'LX L1->M7', 'LX L1->M6', 'LX L1->M5']),
    ('Channel pairs and output banks', ['m2_source M7->M2', 'm3_source M6->M3', 'm4_source M5->M4', 'Vout_1 M2->bank+J3',
                                        'Vout_2 M3->bank+J8', 'Vout_3 M4->bank+J5', 'GND ch1 bank->input',
                                        'GND ch2 bank->input', 'GND ch3 bank->input']),
    ('LED current (DC)', ['Vout_1 M2->J3 (LED DC)', 'Vout_2 M3->J8 (LED DC)', 'Vout_3 M4->J5 (LED DC)',
                          'Output1_drain J4->M10', 'Output2_drain J7->M9', 'Output3_drain J6->M8', 'M10-S M10->R52',
                          'M9-S M9->R53', 'M8-S M8->R7', 'GND R52 return', 'GND R53 return', 'GND R7 return']),
]
NICE = {'Vin J1->R1 (DC)': 'Vin: J1 lug → R1 (DC)', 'Vin caps->R1 (ripple)': 'Vin: C40/C69/C85 → R1 (ripple)',
        'rsense_lo R1->L1': 'rsense_lo: R1 → L1', 'GND M1->input caps+J2': 'GND: M1 source → input caps + J2',
        'LX L1->M1': 'LX: L1 → M1', 'LX L1->M7': 'LX: L1 → M7', 'LX L1->M6': 'LX: L1 → M6', 'LX L1->M5': 'LX: L1 → M5',
        'm2_source M7->M2': 'm2_source: M7 ↔ M2', 'm3_source M6->M3': 'm3_source: M6 ↔ M3',
        'm4_source M5->M4': 'm4_source: M5 ↔ M4', 'Vout_1 M2->bank+J3': 'Vout_1: M2 → bank + J3',
        'Vout_2 M3->bank+J8': 'Vout_2: M3 → bank + J8', 'Vout_3 M4->bank+J5': 'Vout_3: M4 → bank + J5',
        'GND ch1 bank->input': 'GND: ch1 bank → input', 'GND ch2 bank->input': 'GND: ch2 bank → input',
        'GND ch3 bank->input': 'GND: ch3 bank → input', 'Vout_1 M2->J3 (LED DC)': 'Vout_1: M2 → J3 LED pad',
        'Vout_2 M3->J8 (LED DC)': 'Vout_2: M3 → J8 LED pad', 'Vout_3 M4->J5 (LED DC)': 'Vout_3: M4 → J5 LED pad',
        'Output1_drain J4->M10': 'Output1_drain: J4 → M10', 'Output2_drain J7->M9': 'Output2_drain: J7 → M9',
        'Output3_drain J6->M8': 'Output3_drain: J6 → M8', 'M10-S M10->R52': 'M10 source → R52 shunt',
        'M9-S M9->R53': 'M9 source → R53 shunt', 'M8-S M8->R7': 'M8 source → R7 shunt',
        'GND R52 return': 'GND: R52 return', 'GND R53 return': 'GND: R53 return', 'GND R7 return': 'GND: R7 return'}


def cells(r):
    nk = r.get('neck', {})
    rise, ln = nk.get('rise', 0.0), nk.get('length', 0.0)
    wv = r['worst_vias'][0] if r.get('worst_vias') else None
    ratio = wv['ratio'] if wv else 0.0
    cls = 'fail' if rise > 20 else ''
    vcls = 'fail' if ratio > 1.0 else ''
    where = '%s (%.0f, %.0f)' % (nk.get('layer', '').replace('.Cu', ''), nk.get('x', 0), nk.get('y', 0)) if rise else ''
    return ('<td class="num %s">%.1f</td><td class="num dim">%.1f</td><td class="num %s">%s</td>'
            % (cls, rise, ln, vcls, ('%.2f×' % ratio) if wv else '—')), where, rise > 20, ratio > 1.0


rows = []
fails = {'B': [0, 0], 'C': [0, 0]}
for gname, names in GROUPS:
    rows.append('<tr class="stage"><th colspan="10">%s</th></tr>' % gname)
    for n in names:
        b, c = B[n], C[n]
        cb, wb, fnb, fvb = cells(b)
        cc, wc, fnc, fvc = cells(c)
        fails['B'][0] += fnb; fails['B'][1] += fvb
        fails['C'][0] += fnc; fails['C'][1] += fvc
        flag = ' class="missrow"' if (fnb or fvb or fnc or fvc) else ''
        rows.append('<tr%s><td class="path">%s</td><td class="num">%.2f</td><td class="num">%.3f</td>%s'
                    '<td class="num">%.3f</td>%s<td class="dim where">%s</td></tr>'
                    % (flag, html.escape(NICE.get(n, n)), b['I'], b['R_mohm'], cb, c['R_mohm'], cc, wc or wb))

lrows = []
for ch, lab in (('ch1', 'ch1 · M7 / M2'), ('ch2', 'ch2 · M6 / M3'), ('ch3', 'ch3 · M5 / M4')):
    d = L[ch]
    lrows.append('<tr><td>%s</td><td class="num">%.2f</td><td class="num">%.2f</td><td class="num">%.2f</td>'
                 '<td class="num">%.1f</td><td class="num dim">%.2f</td></tr>'
                 % (lab, d['overplane_B'], d['overplane_C'], d['audit_method'], d['squares'], d['sim']))

tmpl = open(os.path.join(HERE, 'review_template.html'), encoding='utf8').read()
page = (tmpl.replace('{{ROWS}}', '\n'.join(rows)).replace('{{LROWS}}', '\n'.join(lrows))
        .replace('{{FAIL_B_NECK}}', str(fails['B'][0])).replace('{{FAIL_B_VIA}}', str(fails['B'][1]))
        .replace('{{FAIL_C_NECK}}', str(fails['C'][0])).replace('{{FAIL_C_VIA}}', str(fails['C'][1]))
        .replace('{{VERSION}}', V))
open(OUT, 'w', encoding='utf8').write(page)
print('wrote', OUT, 'fails', fails)
