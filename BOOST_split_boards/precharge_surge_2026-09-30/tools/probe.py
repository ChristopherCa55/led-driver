"""Which net's copper is at each point, per layer (zone fills, tracks, pads, vias). KiCad Python, read-only.
usage: python.exe probe.py BOARD x,y [x,y ...]"""
import sys, pcbnew
MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(sys.argv[1])
layers = [l for l in b.GetEnabledLayers().CuStack()]
for xy in sys.argv[2:]:
    x, y = map(float, xy.split(','))
    p = pcbnew.VECTOR2I(FM(x), FM(y))
    out = []
    for l in layers:
        nets = set()
        for z in b.Zones():
            if not z.GetIsRuleArea() and z.IsOnLayer(l) and z.GetFilledPolysList(l).Contains(p):
                nets.add(z.GetNetname())
        for t in b.GetTracks():
            if t.IsOnLayer(l) and t.HitTest(p, 0):
                nets.add(t.GetNetname() + ('(via)' if t.GetClass() == 'PCB_VIA' else '(trk)'))
        out.append('%s:%s' % (b.GetLayerName(l), ','.join(sorted(nets)) or '-'))
    print('(%.2f, %.2f)  %s' % (x, y, '  '.join(out)))
