"""Layer-plan checks on a saved board (KiCad Python): In1/In6 GND only, no LX on In3/In5, copper area per net per
layer, via drill census.

usage: python.exe layer_checks.py BOARD.kicad_pcb
"""
import sys, collections
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
MM2 = 1e-12      # nm^2 -> mm^2
area = collections.defaultdict(float)
tracks = collections.Counter()
for z in b.Zones():
    if z.GetIsRuleArea():
        continue
    for lid in z.GetLayerSet().CuStack():
        if z.HasFilledPolysForLayer(lid):
            area[(b.GetLayerName(lid), z.GetNetname())] += z.GetFilledPolysList(lid).Area() * MM2
drills = collections.Counter()
for t in b.GetTracks():
    if t.GetClass() == 'PCB_VIA':
        drills[(t.GetNetname() if t.GetNetname() in ('GND', 'LX', 'Vin', 'rsense_lo') else 'other',
                round(pcbnew.ToMM(t.GetDrillValue()), 2))] += 1
    else:
        tracks[(b.GetLayerName(t.GetLayer()), t.GetNetname())] += 1
fail = []
for (ln, net), a in sorted(area.items()):
    if ln in ('In1.Cu', 'In6.Cu') and net != 'GND' and a > 0:
        fail.append('%s carries %s zone copper (%.1f mm2)' % (ln, net, a))
    if ln in ('In3.Cu', 'In5.Cu') and net == 'LX' and a > 0:
        fail.append('%s carries LX zone copper (%.1f mm2)' % (ln, a))
for (ln, net), n in tracks.items():
    if ln in ('In1.Cu', 'In6.Cu') and net != 'GND':
        fail.append('%s carries %d %s tracks' % (ln, n, net))
    if ln in ('In3.Cu', 'In5.Cu') and net == 'LX':
        fail.append('%s carries %d LX tracks' % (ln, n))
print('In1/In6 GND-only and no LX on In3/In5:', 'PASS' if not fail else 'FAIL')
for f in fail:
    print('   ', f)
print('zone copper by layer (mm2):')
for ln in ('F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu'):
    row = {net: a for (l, net), a in area.items() if l == ln and a > 1}
    print('   %-7s %s' % (ln, ', '.join('%s %.0f' % (n, a) for n, a in sorted(row.items(), key=lambda x: -x[1]))))
print('tracks:', sum(tracks.values()))
print('vias by net group and drill:', dict(sorted(drills.items())))
