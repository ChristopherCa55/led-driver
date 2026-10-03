"""Copper on B.Cu and In3 near the U2 In+ In4 run, and GND coverage of B.Cu under it (KiCad Python, read-only)."""
import sys, collections, math, pcbnew
MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
L = {b.GetLayerName(l): l for l in b.GetEnabledLayers().CuStack()}
run = [t for t in b.GetTracks() if t.GetClass() == 'PCB_TRACK' and t.GetNetname() == 'Net-(U2-In+)' and t.GetLayer() == L['In4.Cu']]
for ln in ('B.Cu', 'In3.Cu'):
    near = collections.defaultdict(float)
    for t in b.GetTracks():
        if t.GetClass() != 'PCB_TRACK' or t.GetLayer() != L[ln] or t.GetNetname() in ('GND', 'Net-(U2-In+)'):
            continue
        s = t.GetEffectiveShape(L[ln])
        for d in (0.5, 1.0, 2.0):
            if any(s.Collide(r.GetEffectiveShape(L['In4.Cu']), FM(d)) for r in run):
                near[(t.GetNetname(), d)] += MM(t.GetLength()); break
    pads = set()
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(L[ln]) and p.GetNetname() not in ('GND', 'Net-(U2-In+)') and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                if any(p.GetEffectiveShape(L[ln]).Collide(r.GetEffectiveShape(L['In4.Cu']), FM(1.0)) for r in run):
                    pads.add('%s.%s %s' % (f.GetReference(), p.GetNumber(), p.GetNetname()))
    print('%s: other-net tracks near the In+ In4 run (net, within mm): %s' % (ln, {k: round(v, 1) for k, v in near.items()}))
    print('%s: other-net SMD pads within 1 mm: %s' % (ln, sorted(pads)))
g = pcbnew.SHAPE_POLY_SET()
for z in b.Zones():
    if z.GetNetname() == 'GND' and z.IsOnLayer(L['B.Cu']) and z.HasFilledPolysForLayer(L['B.Cu']):
        g.BooleanAdd(z.GetFilledPolysList(L['B.Cu']))
tot = hit = 0
for t in run:
    a, c = t.GetStart(), t.GetEnd(); n = max(1, int(t.GetLength() / FM(0.1)))
    for k in range(n):
        p = pcbnew.VECTOR2I(int(a.x + (c.x - a.x) * (k + .5) / n), int(a.y + (c.y - a.y) * (k + .5) / n)); tot += 1; hit += g.Contains(p)
print('B.Cu GND fill under the In+ In4 run: %.0f %% of %d points' % (100.0 * hit / tot, tot))
for f in b.GetFootprints():
    if f.GetReference() in ('U2', 'J11', 'R1'):
        print(f.GetReference(), f.GetValue(), 'bottom' if f.IsFlipped() else 'top', '(%.2f, %.2f)' % (MM(f.GetPosition().x), MM(f.GetPosition().y)))
