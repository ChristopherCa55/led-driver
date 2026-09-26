"""Distance table for the placement check-in: target, shipped board ("now", from REPLACE_BRIEF_v2) and new layout.

  python ptable.py LAYOUT.json [OUT.md] [--goals=CONFIG.json]

With --goals, a second limit column shows the goals agreed at check-in 3 (config 'goals' entries,
substring of the path label -> [limit, weight]; later matches win).
"""
import sys, json
import pmodel as M
import pcheck as C

NOW = {
    'C40 Vin -> R1 Vin force pad': 21, 'C69 Vin -> R1 Vin force pad': 31, 'C85 Vin -> R1 Vin force pad': 17,
    'C40 GND -> M1 source': 39, 'C69 GND -> M1 source': 37, 'C85 GND -> M1 source': 28,
    'R1 rsense_lo pad -> L1.2': 10.6, 'J1 -> R1 Vin pad (report)': 49,
    'D19 LX -> M1 drain': 29, 'D19 GND -> M1 source': 27, 'U19 OUTA -> M1 gate': 15,
    'U25 IN+ -> R1 sense P': 41, 'U25 IN- -> R1 sense N': 41,
    'L1 LX pad -> M1 drain': 19, 'L1 LX pad -> M7 drain': 10, 'L1 LX pad -> M6 drain': 31, 'L1 LX pad -> M5 drain': 59,
    'M7 source <-> M2 source': 11, 'M6 source <-> M3 source': 11, 'M5 source <-> M4 source': 22,
    'U15 OUTA -> M2 gate': 13, 'U15 OUTB -> M7 gate': 18, 'U10 OUTA -> M3 gate': 20, 'U10 OUTB -> M6 gate': 27,
    'U8 OUTA -> M4 gate': 11, 'U8 OUTB -> M5 gate': 28,
    'M2 drain -> C70': 34, 'M2 drain -> C86': 45, 'M2 drain -> C88': 55,
    'M3 drain -> C71': 32, 'M3 drain -> C78': 34, 'M3 drain -> C87': 48,
    'M4 drain -> C74': 30, 'M4 drain -> C75': 55, 'M4 drain -> C77': 67,
    'LED pads J3-J4': 6, 'LED pads J8-J7': 41, 'LED pads J5-J6': 6,
    'M10 source -> R52': 48, 'M9 source -> R53': 33, 'M8 source -> R7': 39,
    'M10 drain -> J4': 49, 'M9 drain -> J7': 61, 'M8 drain -> J6': 51,
    'U11 IN- -> NT1 (net tie)': 25, 'U12 IN- -> NT2 (net tie)': 24, 'U6 IN- -> NT3 (net tie)': 13,
    'U11 OUT -> M10 gate': 27, 'U12 OUT -> M9 gate': 29, 'U6 OUT -> M8 gate': 42,
}
STAGE = {1: 'Input loop and M1', 2: 'LX node', 3: 'Switch pairs', 4: 'Output banks and LED pads', 5: 'LED sinks',
         6: 'Gate loops', 7: 'Commutation loop (report)', 8: 'Driver bypass'}

args = [a for a in sys.argv[1:] if not a.startswith('--goals=')]
goals = {}
for a in sys.argv[1:]:
    if a.startswith('--goals='):
        goals = json.load(open(a.split('=', 1)[1])).get('goals', {})
res = json.load(open(args[0]))
L = {k: tuple(v) for k, v in res['layout'].items()}
rows = C.distances(L)
out = ['| Stage | Path | Brief target (mm) | Agreed goal (mm) | Shipped (mm) | New (mm) | vs brief | vs goal |',
       '|---|---|---|---|---|---|---|---|']
met = met_goal = 0
for st, label, val, lim, kind, ok in rows:
    if lim >= 90:
        out.append('| %d %s | %s | - | - | %s | %.1f | | |' % (st, STAGE[st], label, NOW.get(label, '-'), val))
        continue
    glim = lim
    for key, (gl, gw) in goals.items():          # later matches win, as in the optimizer
        if key in label:
            glim = gl
    ok_goal = val <= glim
    met += ok
    met_goal += ok_goal
    out.append('| %d %s | %s | <= %g | <= %g | %s | %.1f | %s | %s |' % (
        st, STAGE[st], label, lim, glim, NOW.get(label, '-'), val, 'ok' if ok else 'MISS', 'ok' if ok_goal else 'MISS'))
n = sum(1 for r in rows if r[3] < 90)
out.append('')
out.append('Brief targets met: %d of %d. Agreed goals met: %d of %d.' % (met, n, met_goal, n))
text = '\n'.join(out)
print(text)
if len(args) > 1:
    open(args[1], 'w', encoding='utf8').write(text + '\n')
