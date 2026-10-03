"""What an edit changed, by net: track length and vias per layer, moved footprints, and zone settings (KiCad Python,
on COPIES: LoadBoard writes .kicad_prl files).

    python.exe edit_detail.py OLD.kicad_pcb NEW.kicad_pcb
"""
import collections, sys
import pcbnew

MM = pcbnew.ToMM


def load(p):
    b = pcbnew.LoadBoard(p)
    cu = list(b.GetEnabledLayers().CuStack())
    tr, vi = collections.Counter(), {}
    seg = set()
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            vi[(round(MM(t.GetPosition().x), 3), round(MM(t.GetPosition().y), 3))] = (
                t.GetNetname(), round(MM(t.GetDrillValue()), 2), round(MM(t.GetWidth(pcbnew.F_Cu)), 2))
        else:
            k = (t.GetNetname(), b.GetLayerName(t.GetLayer()), round(MM(t.GetWidth()), 3),
                 tuple(sorted([(round(MM(t.GetStart().x), 3), round(MM(t.GetStart().y), 3)),
                               (round(MM(t.GetEnd().x), 3), round(MM(t.GetEnd().y), 3))])))
            seg.add(k)
    fps = {f.GetReference(): (round(MM(f.GetPosition().x), 3), round(MM(f.GetPosition().y), 3),
                              round(f.GetOrientationDegrees(), 1), f.IsFlipped(), f.GetValue()) for f in b.GetFootprints()}
    zones = []
    for z in b.Zones():
        o = z.Outline()
        bb = o.BBox()
        lays = [b.GetLayerName(l) for l in cu if z.IsOnLayer(l)]
        zones.append(dict(
            name=z.GetZoneName(), net=z.GetNetname(), layers=lays, rule=z.GetIsRuleArea(),
            prio=z.GetAssignedPriority(), area=round(o.Area() / 1e12, 1),
            bbox=(round(MM(bb.GetX()), 2), round(MM(bb.GetY()), 2), round(MM(bb.GetRight()), 2), round(MM(bb.GetBottom()), 2)),
            clr=round(MM(z.GetLocalClearance() or 0), 3), minw=round(MM(z.GetMinThickness()), 3),
            pad=int(z.GetPadConnection()), island=int(z.GetIslandRemovalMode()),
            pts=o.FullPointCount()))
    return seg, vi, fps, zones


so, vo, fo, zo = load(sys.argv[1])
sn, vn, fn, zn = load(sys.argv[2])
print('== tracks (length removed / added, mm) by net and layer')
acc = collections.defaultdict(lambda: [0.0, 0.0, 0, 0])
for s, k in ((so - sn, 0), (sn - so, 1)):
    for net, ln, w, ((x0, y0), (x1, y1)) in s:
        a = acc[(net, ln)]
        a[k] += ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        a[k + 2] += 1
for (net, ln), (r, a, nr, na) in sorted(acc.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    print('  %-18s %-7s -%6.1f (%3d)  +%6.1f (%3d)' % (net, ln, r, nr, a, na))
print('== vias')
for k in sorted(set(vo) - set(vn)):
    print('  removed %-14s at (%7.3f, %7.3f) drill %.2f dia %.2f' % ((vo[k][0],) + k + vo[k][1:]))
for k in sorted(set(vn) - set(vo)):
    print('  added   %-14s at (%7.3f, %7.3f) drill %.2f dia %.2f' % ((vn[k][0],) + k + vn[k][1:]))
for k in sorted(set(vn) & set(vo)):
    if vn[k] != vo[k]:
        print('  changed at (%7.3f, %7.3f): %s -> %s' % (k + (vo[k], vn[k])))
print('== footprints')
for r in sorted(set(fo) | set(fn)):
    if fo.get(r) != fn.get(r):
        print('  %-6s %s -> %s' % (r, fo.get(r), fn.get(r)))
print('== zones (removed / added / changed records)')
key = lambda z: (z['net'], tuple(z['layers']), z['bbox'], z['area'], z['prio'], z['clr'], z['minw'], z['pad'],
                 z['island'], z['pts'], z['name'], z['rule'])
ko, kn = collections.Counter(map(key, zo)), collections.Counter(map(key, zn))
for k in sorted(ko - kn):
    print('  OLD', k)
for k in sorted(kn - ko):
    print('  NEW', k)
