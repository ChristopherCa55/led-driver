"""Collect one step's check outputs into metrics JSON and rebuild METRICS.md (one row per metric, one column per
accepted step; the first column is the baseline). A value worse than the baseline beyond its tolerance is flagged.

    python collect.py WORK_DIR STEP [STEP ...]        (each STEP is a folder in WORK_DIR; 'baseline' first)

Reads what step_checks.sh writes: erc_*.rpt, drc_*.json, sync_check.txt, power_solve.json, loopL.txt,
plane_cover.txt, sense_cover.txt, gate_return.txt, heatmap/*_gnd_report.txt, sense_offsets.txt, sens_card.json,
checks/{power,card}_checks.json, thermal_board.txt / thermal_bg.txt, and sims/*.out if present.
"""
import glob, json, os, re, sys, collections

# metric key -> (label, better: 'low' | 'high' | 'eq', tolerance, group)
SPEC = collections.OrderedDict()


def spec(key, label, better, tol, group):
    SPEC[key] = (label, better, tol, group)


def num(s):
    return float(s)


def parse(step_dir):
    m = {}
    # ---- KiCad gates
    for p in ('BOOST', 'BOOST_power_RC2', 'BOOST_control_RC2'):
        f = os.path.join(step_dir, 'erc_%s.rpt' % p)
        if os.path.exists(f):
            m['erc_' + p] = sum(1 for l in open(f, encoding='utf-8') if l.startswith('['))
    for b, t in (('BOOST_power_RC2', 'power'), ('BOOST_control_RC2', 'card')):
        f = os.path.join(step_dir, 'drc_%s.json' % b)
        if os.path.exists(f):
            d = json.load(open(f, encoding='utf-8'))
            m['drc_%s_err' % t] = sum(1 for v in d['violations'] if v['severity'] == 'error')
            m['drc_%s_warn' % t] = sum(1 for v in d['violations'] if v['severity'] == 'warning')
            m['drc_%s_unc' % t] = len(d['unconnected_items'])
            m['drc_%s_parity' % t] = len(d['schematic_parity'])
    f = os.path.join(step_dir, 'sync_check.txt')
    if os.path.exists(f):
        mm = re.search(r'(\d+) differences', open(f).read())
        if mm:
            m['sync'] = int(mm.group(1))
    f = os.path.join(step_dir, 'ltspice_equiv.txt')
    if os.path.exists(f):
        m['lt_equiv'] = 'PASS' if 'ELECTRICAL RESULT: PASS' in open(f).read() else 'FAIL'
    # ---- power DC solve
    f = os.path.join(step_dir, 'power_solve.json')
    if os.path.exists(f):
        for r in json.load(open(f)):
            n = r['name']
            m['br|%s|R' % n] = round(r['R_mohm'], 3)
            m['br|%s|neck' % n] = round(r['neck']['rise'], 1)
            m['br|%s|necklen' % n] = round(r['neck']['length'], 1)
            m['br|%s|long' % n] = round(r['neck_long']['rise'], 1)
            m['br|%s|over' % n] = r['vias_over']
            m['br|%s|worst' % n] = round(r['worst_vias'][0]['ratio'], 2) if r.get('worst_vias') else 0.0
    f = os.path.join(step_dir, 'loopL.txt')
    if os.path.exists(f):
        mm = re.search(r'ch1 ([\d.]+)\s+ch2 ([\d.]+)\s+ch3 ([\d.]+) nH', open(f).read())
        if mm:
            m['loopL_ch1'], m['loopL_ch2'], m['loopL_ch3'] = map(num, mm.groups())
    # ---- GND heatmap and sense offsets
    for f in glob.glob(os.path.join(step_dir, 'heatmap', '*_gnd_report.txt')):
        mm = re.search(r'highest GND voltage per layer \(mV\): (.*)', open(f).read())
        if mm:
            m['gnd_max_mV'] = max(float(x.split()[1]) for x in mm.group(1).split(', '))
    f = os.path.join(step_dir, 'sense_offsets.txt')
    if os.path.exists(f):
        for ref, v in re.findall(r'(R52|R53|R7)\s+GND end [\d.]+ mV, offset to card GND ([-\d.]+) mV', open(f).read()):
            m['offset_' + ref] = float(v)
    # ---- coverage
    f = os.path.join(step_dir, 'plane_cover.txt')
    if os.path.exists(f):
        mm = re.search(r'all\s+signal\s+\d+ mm,\s+(\d+) % over GND\s+\| gate\s+\d+ mm,\s+(\d+) %', open(f).read())
        if mm:
            m['cover_signal'], m['cover_gate'] = int(mm.group(1)), int(mm.group(2))
    f = os.path.join(step_dir, 'sense_cover.txt')
    if os.path.exists(f):
        for n, v in re.findall(r'^\s+(\S+)\s+[\d.]+ mm\s+(\d+) % over GND', open(f).read(), re.M):
            m['sense|' + n] = int(v)
    f = os.path.join(step_dir, 'gate_return.txt')
    if os.path.exists(f):
        # the line starts with spaces (baseline) or with the export's path and ': ' (gates_all.sh in later runs)
        for fet, v in re.findall(r'## (M\d+)\n(?:\s+|[^\n]*?: )drive [\d.]+ mm, (\d+) % with no', open(f).read()):
            m['gate_unret|' + fet] = int(v)
    # ---- U16
    fb, fg = os.path.join(step_dir, 'thermal_board.txt'), os.path.join(step_dir, 'thermal_bg.txt')
    if os.path.exists(fb) and os.path.exists(fg):
        tab = float(re.search(r'tab-to-ambient ([\d.]+) K/W', open(fb).read()).group(1))
        bg = float(re.search(r'total ([\d.]+) K', open(fg).read()).group(1))
        P = (18 - 11.4) * 0.120 + 18 * 0.008        # power6 README: MC7812, 120 mA, 18 V, 11.4 V min out, 8 mA bias
        m['u16_tab'], m['u16_bg'], m['u16_tj'] = tab, bg, round(75 + bg + P * (tab + 5.0), 1)
    # ---- pieces, slices, card returns
    for board in ('power', 'card'):
        f = os.path.join(step_dir, 'checks', '%s_checks.json' % board)
        if not os.path.exists(f):
            continue
        d = json.load(open(f))
        for key, isl in d['islands'].items():
            ln, net = key.split('|')
            if net == 'GND':
                m['pieces|%s|%s' % (board, ln)] = len(isl)
                m['bigpiece|%s|%s' % (board, ln)] = round(max(r['area'] for r in isl), 0)
        sep = [s for s in d['slices'] if s['pour'] == 'GND' and s['joins']]
        m['gnd_split_tracks|' + board] = len(sep)
        m['gnd_slices3mm|' + board] = sum(1 for s in d['slices'] if s['pour'] == 'GND' and s['length'] >= 3.0)
        m['jogs|' + board] = sum(d['jogs'].values())
        if board == 'card':
            ref = d['reference']
            m['card_gap_tracks'] = len(ref)
            m['card_gap_mm'] = round(sum(r['length'] for r in ref), 1)
            stacked = [r for r in ref if any(int(k) >= 0 for k in r['under'])]
            m['card_stacked'] = len(stacked)
    f = os.path.join(step_dir, 'sens_card.json')
    if os.path.exists(f):
        for n in json.load(open(f)):
            key = {'Net-(U2-In+)': 'inp', 'Current': 'cur', 'V_err': 'verr'}[n['net']]
            m['sens_' + key] = n['whole_length_plane_pct_off_own_vias_pads'] if key != 'cur' else n['planes_pct']
            m['sens_%s_fvias' % key] = len(n['foreign_vias_within_2mm'])
    # ---- sims
    for f in glob.glob(os.path.join(step_dir, 'sims', '*.out')):
        tag = os.path.basename(f)[:-4]
        for k, v in re.findall(r'^(\w+): .*?=([-\d.e+]+)', open(f).read(), re.M):
            m['sim|%s|%s' % (tag, k)] = float(v)
    return m


RULES = [  # (regex on key, label prefix, better, tolerance)
    (r'^erc_', 'ERC', 'low', 0), (r'^drc_.*_(err|unc|parity)$', 'DRC', 'low', 0), (r'^drc_.*_warn$', 'DRC', 'low', 0),
    (r'^sync$', 'sync', 'low', 0), (r'^br\|.*\|R$', 'R mOhm', 'low', 0.005), (r'^br\|.*\|(neck|long)$', 'rise C', 'low', 0.25),
    (r'^br\|.*\|necklen$', 'neck length mm (info)', 'info', 0),
    (r'^br\|.*\|over$', 'vias over', 'low', 0), (r'^br\|.*\|worst$', 'worst via x', 'low', 0.02),
    (r'^loopL_', 'loop L nH', 'low', 0.02), (r'^gnd_max_mV$', 'GND max mV', 'low', 0.03),
    (r'^offset_', 'sense offset mV', 'low', 0.02), (r'^cover_', 'over GND %', 'high', 0), (r'^sense\|', 'over GND %', 'high', 0),
    (r'^gate_unret\|', 'unreturned %', 'low', 0), (r'^u16_tab$', 'K/W', 'low', 0.05), (r'^u16_bg$', 'K', 'low', 0.1),
    (r'^u16_tj$', 'C', 'low', 0.2), (r'^pieces\|', 'GND pieces', 'low', 0), (r'^bigpiece\|', 'largest GND piece mm2', 'high', 2),
    (r'^gnd_split_tracks', 'tracks splitting GND', 'low', 0), (r'^gnd_slices3mm', 'GND slices >= 3 mm', 'low', 0),
    (r'^jogs', 'jogs', 'low', 0), (r'^card_gap_tracks$', 'tracks over plane gaps', 'low', 0),
    (r'^card_gap_mm$', 'mm over plane gaps', 'low', 0.5), (r'^card_stacked$', 'stacked track pairs', 'low', 0),
    (r'^sens_(inp|cur|verr)$', 'plane %', 'high', 0.05), (r'^sens_.*_fvias$', 'foreign vias < 2 mm', 'low', 0),
    (r'^sim\|.*\|iled', 'A', 'eq', 0.002), (r'^sim\|', '', 'eq', 0.0),
]


def rule(k):
    for rx, lab, better, tol in RULES:
        if re.search(rx, k):
            return lab, better, tol
    return '', 'eq', 0


def worse(k, base, v):
    if base is None or v is None or isinstance(v, str) or isinstance(base, str):
        return False
    _, better, tol = rule(k)
    if better == 'info':
        return False
    if better == 'low':
        return v > base + tol
    if better == 'high':
        return v < base - tol
    return abs(v - base) > tol


def fmt(v):
    if v is None:
        return ''
    if isinstance(v, float):
        return ('%.3f' % v).rstrip('0').rstrip('.') if abs(v) < 100 else '%.1f' % v
    return str(v)


def main():
    work, steps = sys.argv[1], sys.argv[2:]
    os.makedirs(os.path.join(work, 'metrics'), exist_ok=True)
    data = {}
    for s in steps:
        data[s] = parse(os.path.join(work, s))
        json.dump(data[s], open(os.path.join(work, 'metrics', s + '.json'), 'w'), indent=1)
    keys = []
    for s in steps:
        for k in data[s]:
            if k not in keys:
                keys.append(k)
    base = data[steps[0]]
    L = ['# Metrics (review fixes, 2026-10-11)', '',
         'One row per metric, one column per accepted step; the first column is the baseline (the unmodified copy).',
         'A value marked **(worse)** is worse than the baseline beyond its tolerance: it needs a reason the user accepts, or',
         'a revert. Rises are IPC-2221 figures: per the short-neck rule they are reported, not judged, for necks under',
         'about 5 mm and plane-connected vias. Generated by `tools/collect.py`.', '',
         '| Metric | unit / better | ' + ' | '.join(steps) + ' |', '|---|---|' + '---|' * len(steps)]
    bad = []
    for k in keys:
        lab, better, _ = rule(k)
        cells = []
        for s in steps:
            v = data[s].get(k)
            c = fmt(v)
            if s != steps[0] and worse(k, base.get(k), v):
                c += ' **(worse)**'
                bad.append((s, k, base.get(k), v))
            cells.append(c)
        L.append('| %s | %s, %s | %s |' % (k, lab, better, ' | '.join(cells)))
    L += ['', '## Regressions', '']
    L += ['- %s: %s %s -> %s' % b for b in bad] or ['None.']
    open(os.path.join(work, 'METRICS.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('METRICS.md: %d metrics, %d steps, %d flagged' % (len(keys), len(steps), len(bad)))


if __name__ == '__main__':
    main()
