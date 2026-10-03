"""Survey for the In4-plane re-route (KiCad Python, read-only): In4 tracks by net; U2 In+ run geometry; copper of other
nets within 2 mm (plan view) of the In+ run on In2 and In3; netclasses and clearances."""
import sys, collections, pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
L = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
by = collections.defaultdict(lambda: [0.0, 0, set()])
for t in b.GetTracks():
    if t.GetClass() == 'PCB_TRACK' and t.GetLayer() == L['In4.Cu']:
        r = by[t.GetNetname()]; r[0] += MM(t.GetLength()); r[1] += 1; r[2].add(t.GetNetClassName())
print('In4 tracks: %d nets, %.0f mm' % (len(by), sum(v[0] for v in by.values())))
for n, (mm, k, nc) in sorted(by.items(), key=lambda kv: -kv[1][0]):
    print('  %-28s %6.1f mm %3d seg  class %s' % (n, mm, k, ','.join(nc)))
inp = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'Net-(U2-In+)']
print('\nU2 In+ tracks:')
for t in inp:
    print('  %-6s (%.2f,%.2f)-(%.2f,%.2f) w %.2f' % (b.GetLayerName(t.GetLayer()), MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y), MM(t.GetWidth())))
run = [t for t in inp if t.GetLayer() == L['In4.Cu']]
for ln in ('In1.Cu', 'In2.Cu', 'In3.Cu'):
    near = collections.Counter()
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != L[ln] or t.GetNetname() in ('GND', 'Net-(U2-In+)'):
            continue
        s = t.GetEffectiveShape(L[ln])
        if any(s.Collide(r.GetEffectiveShape(L['In4.Cu']), pcbnew.FromMM(2.0)) for r in run):
            near[t.GetNetname()] += 1
    print('  other-net tracks on %s within 2 mm (plan) of the In+ run: %s' % (ln, dict(near)))
ds = b.GetDesignSettings()
print('\nnetclasses:')
for name, nc in b.GetAllNetClasses().items():
    print('  %-12s clearance %.3f track %.3f via %.2f/%.2f' % (name, MM(nc.GetClearance()), MM(nc.GetTrackWidth()), MM(nc.GetViaDiameter()), MM(nc.GetViaDrill())))
