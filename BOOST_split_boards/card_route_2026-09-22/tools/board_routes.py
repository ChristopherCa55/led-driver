"""Dump a routed board's tracks and vias as route_card.py routes JSON (KiCad Python), for repair rounds on top of a
Freerouting result.

usage: python.exe board_routes.py BOARD.kicad_pcb PRE_ROUTES.json OUT.json

Items found in PRE_ROUTES.json (same net and geometry to 1 um) keep its 'keep' flag (the sensitive nets and their
escapes stay fixed); everything else is loaded rip-able.
"""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
pre = json.load(open(sys.argv[2]))
MM = pcbnew.ToMM
q = lambda v: round(v, 3)


def tkey(net, layer, x0, y0, x1, y1):
    p = sorted([(q(x0), q(y0)), (q(x1), q(y1))])
    return (net, layer, p[0], p[1])


keep_t = {tkey(t['net'], t['layer'], t['x0'], t['y0'], t['x1'], t['y1']) for t in pre['tracks'] if t.get('keep')}
keep_v = {(v['net'], q(v['x']), q(v['y'])) for v in pre['vias'] if v.get('keep')}
pre_layers = {(v['net'], q(v['x']), q(v['y'])): v['layers'] for v in pre['vias']}
# a via's 'layers' are the layers it joins (route_card flashes its annulus there): the pre-route's own list, else
# every layer where a track of its net ends on it or an SMD pad of its net holds it (via-in-pad)
TR = [t for t in b.GetTracks() if t.GetClass() != 'PCB_VIA']
PADS = [(p, f.IsFlipped()) for f in b.GetFootprints() for p in f.Pads()]


def joined(v):
    n, pos, r = v.GetNetname(), v.GetPosition(), v.GetWidth(pcbnew.F_Cu) / 2 + 1000
    ls = set()
    for t in TR:
        if t.GetNetname() == n and min((t.GetStart() - pos).EuclideanNorm(), (t.GetEnd() - pos).EuclideanNorm()) <= r:
            ls.add(b.GetLayerName(t.GetLayer()))
    for p, flipped in PADS:
        if p.GetNetname() == n and p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.HitTest(pos):
            ls.add('B.Cu' if flipped else 'F.Cu')
    order = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'In5.Cu', 'In6.Cu', 'B.Cu']
    return [l for l in order if l in ls] or ['F.Cu', 'B.Cu']


out = dict(tracks=[], vias=[], log=['from %s' % sys.argv[1]], failures=[])
for t in b.GetTracks():
    n = t.GetNetname()
    if t.GetClass() == 'PCB_VIA':
        x, y = MM(t.GetPosition().x), MM(t.GetPosition().y)
        out['vias'].append(dict(net=n, x=x, y=y, dia=MM(t.GetWidth(pcbnew.F_Cu)), drill=MM(t.GetDrillValue()),
                                layers=pre_layers.get((n, q(x), q(y))) or joined(t), keep=(n, q(x), q(y)) in keep_v))
    else:
        ln = b.GetLayerName(t.GetLayer())
        x0, y0, x1, y1 = MM(t.GetStart().x), MM(t.GetStart().y), MM(t.GetEnd().x), MM(t.GetEnd().y)
        out['tracks'].append(dict(net=n, layer=ln, w=MM(t.GetWidth()), x0=x0, y0=y0, x1=x1, y1=y1,
                                  keep=tkey(n, ln, x0, y0, x1, y1) in keep_t))
json.dump(out, open(sys.argv[3], 'w'))
print('%d tracks, %d vias (%d / %d kept fixed) -> %s' % (
    len(out['tracks']), len(out['vias']), sum(t['keep'] for t in out['tracks']), sum(v['keep'] for v in out['vias']),
    sys.argv[3]))
