"""psa5 config with the input loop and each LED channel as rigid groups.

  python mk11.py BASE_CONFIG.json OUT.json [iters] [T0]

BASE_CONFIG: an mk10/p11 config (weights, goals, zones, card handling, tall-part clearances come from it).
Every earlier search ended with L1 over a screw point (M1's tab hole under L1's body) or the sinks far from
their LED pads. These groups hold the arrangement that avoids both, so the annealer only places the groups:

INPUT (L1 at the origin, rot 0, pads toward +y):
  M1  (-3.46, 22.5) rot 180 bottom: pin row just past L1's pads, body pointing away from L1, drain under the
      LX pad (5.3 mm), tab screw at (-6.0, 39.2), 18.6 mm beyond L1's pad edge
  D19 (-7.27, 17.5) rot 180 bottom: LX pad by M1's drain, GND pad by M1's source (5.4 mm each)
  R1  (12, 25.3) rot 180 top: rsense_lo force pad 7.1 mm from L1's rsense_lo pad
CHANNEL n (sink FET at the origin, rot 0 bottom: body toward -y, pins G D S left to right):
  shunt (5.08, -5.94) rot 90 top, over the sink body: pad 1 2.98 mm from the source pin
  LED cathode pad (4.0, 4.5), anode pad (-2.5, 4.5): cathode 4.7 mm from the drain; pads 6.5 mm apart
  (channel 1 M10 R52 J4 J3, channel 2 M9 R53 J7 J8, channel 3 M8 R7 J6 J5)
The script checks these distances and that no two members of a group overlap, then writes the config.
"""
import sys, json, math, copy
import pmodel as M

base = json.load(open(sys.argv[1]))
out = sys.argv[2]
iters = int(sys.argv[3]) if len(sys.argv) > 3 else base.get('iters', 800000)
T0 = float(sys.argv[4]) if len(sys.argv) > 4 else base.get('T0', 3000.0)

INPUT = [['L1', 0, 0, 0, 'F'], ['M1', -3.46, 22.5, 180, 'B'], ['D19', -7.27, 17.5, 180, 'B'], ['R1', 12.0, 25.3, 180, 'F']]
CH = {'CH_1': ('M10', 'R52', 'J4', 'J3'), 'CH_2': ('M9', 'R53', 'J7', 'J8'), 'CH_3': ('M8', 'R7', 'J6', 'J5')}


def ch_members(sink, shunt, cath, anode):
    return [[sink, 0, 0, 0, 'B'], [shunt, 5.08, -5.94, 90, 'F'], [cath, 4.0, 4.5, 0, 'F'], [anode, -2.5, 4.5, 0, 'F']]


def check(members, rules):
    L = {m[0]: (m[1], m[2], m[3], m[4]) for m in members}
    for a, pa, b, pb, lim in rules:
        dd = M.d(L, a, pa, b, pb)
        assert dd <= lim, (a, pa, b, pb, dd, lim)
        print('   %s.%s -> %s.%s %.2f mm (<= %g)' % (a, pa, b, pb, dd, lim))
    refs = list(L)
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            for s1, r1, k1 in M.areas(L, refs[i]):
                for s2, r2, k2 in M.areas(L, refs[j]):
                    assert not (s1 == s2 and M.overlap(r1, r2)), ('group overlap', refs[i], k1, refs[j], k2, s1)
    return L


print('INPUT group:')
Li = check(INPUT, [('L1', '1', 'M1', '2', 15), ('D19', '1', 'M1', '2', 5.5), ('D19', '2', 'M1', '3', 5.5),
                   ('R1', '4', 'L1', '2', 10)])
hx, hy = M.tab_hole(Li, 'M1')
print('   M1 tab hole (%.2f, %.2f); L1 pad edge at y 20.25' % (hx, hy))
for name, (sink, shunt, cath, anode) in CH.items():
    print('%s:' % name)
    check(ch_members(sink, shunt, cath, anode), [(sink, '3', shunt, '1', 5), (sink, '2', cath, '1', 15)])

cfg = copy.deepcopy(base)
drop_singles = {'L1', 'M1', 'D19', 'R1'}
cfg['singles'] = {k: v for k, v in cfg['singles'].items() if k not in drop_singles}
for k in drop_singles:
    cfg['init'].pop(k, None)
macros = {k: v for k, v in cfg['macros'].items() if not (k.startswith('SINK_') or k.startswith('LED_'))}
macros['INPUT'] = dict(members=INPUT, init=[70.0, 45.0, 0])
for i, (name, refs) in enumerate(CH.items()):
    macros[name] = dict(members=ch_members(*refs), init=[36.0 + 12.4 * i, 108.0, 0])
cfg['macros'] = macros
groups = []
for g in cfg.get('swap_groups', []):
    if any(n.startswith('SINK_') or n.startswith('LED_') for n in g):
        continue
    groups.append(g)
groups.append(['CH_1', 'CH_2', 'CH_3'])
cfg['swap_groups'] = groups
cfg.update(iters=iters, T0=T0)
json.dump(cfg, open(out, 'w'), indent=1)
print('mk11: %s, %d singles, macros %s, iters %d, T0 %g' % (out, len(cfg['singles']), sorted(macros), iters, T0))
