"""Connected groups of one net's items on a board (KiCad Python, read-only): prints every group but the largest."""
import sys, pcbnew
MM = pcbnew.ToMM
b = pcbnew.LoadBoard(sys.argv[1])
net = sys.argv[2] if len(sys.argv) > 2 else 'GND'
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.BuildConnectivity()
cn = b.GetConnectivity()
code = b.FindNet(net).GetNetCode()
items = [t for t in b.GetTracks() if t.GetNetCode() == code]
items += [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == code]
items += [z for z in b.Zones() if z.GetNetCode() == code and not z.GetIsRuleArea()]
key = lambda it: it.m_Uuid.AsString()
idx = {key(it): it for it in items}
seen, groups = set(), []
for it in items:
    if key(it) in seen:
        continue
    comp, stack = [], [it]
    seen.add(key(it))
    while stack:
        x = stack.pop(); comp.append(x)
        for y in cn.GetConnectedItems(x):
            k = key(y)
            if k in idx and k not in seen:
                seen.add(k); stack.append(y)
    groups.append(comp)
groups.sort(key=len, reverse=True)
print('%s: %d groups, largest %d items' % (net, len(groups), len(groups[0])))
for g in groups[1:]:
    desc = []
    for x in g[:12]:
        c = x.GetClass()
        if c == 'PAD':
            desc.append('pad %s.%s (%.2f, %.2f) %s' % (x.GetParentFootprint().GetReference(), x.GetNumber(), MM(x.GetPosition().x), MM(x.GetPosition().y), b.GetLayerName(x.GetLayer())))
        elif c == 'ZONE':
            desc.append('zone %s' % x.GetZoneName())
        else:
            desc.append('%s (%.2f, %.2f) %s' % (c, MM(x.GetPosition().x), MM(x.GetPosition().y), b.GetLayerName(x.GetLayer())))
    print('  group of %d: %s' % (len(g), '; '.join(desc)))
