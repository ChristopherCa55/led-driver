"""What changed between two boards, item by item and layer by layer (KiCad Python).

usage: python.exe board_diff.py OLD.kicad_pcb NEW.kicad_pcb [--silk-only]

Every footprint (position, side, rotation), pad (position, size, shape, drill, net), track, via, zone outline and
board drawing, and every footprint graphic and field, becomes a canonical record keyed by its layer. Records only in
OLD or only in NEW are counted per layer. With --silk-only the exit code is 1 if anything changed off the silkscreen
and Fab layers (the check for a silk-only delta).
"""
import collections, sys
import pcbnew

MM = pcbnew.ToMM


def r(v):
    return round(MM(v), 4)


def xy(p):
    return (r(p.x), r(p.y))


def records(path):
    b = pcbnew.LoadBoard(path)
    ln = b.GetLayerName
    out = collections.Counter()
    for f in b.GetFootprints():
        ref = f.GetReference()
        out[('footprint', ln(f.GetLayer()), ref, xy(f.GetPosition()), round(f.GetOrientationDegrees(), 3),
             f.GetFPIDAsString(), f.GetValue())] += 1
        for p in f.Pads():
            for L in p.GetLayerSet().Seq():
                out[('pad', ln(L), ref, p.GetNumber(), xy(p.GetPosition()), xy(p.GetSize(L)), int(p.GetShape(L)),
                     xy(p.GetDrillSize()), p.GetNetname(), round(p.GetOrientationDegrees(), 3))] += 1
        for g in f.GraphicalItems():
            if g.GetClass() == 'PCB_TEXT':
                out[('fp_text', ln(g.GetLayer()), ref, g.GetText(), xy(g.GetPosition()),
                     round(g.GetTextAngleDegrees(), 2), r(g.GetTextHeight()), r(g.GetTextThickness()))] += 1
            else:
                out[('fp_shape', ln(g.GetLayer()), ref, g.GetShapeStr(), xy(g.GetStart()), xy(g.GetEnd()),
                     r(g.GetWidth()))] += 1
        for fld in f.GetFields():
            out[('field', ln(fld.GetLayer()), ref, fld.GetName(), fld.GetText(), xy(fld.GetPosition()),
                 round(fld.GetTextAngleDegrees(), 2), fld.IsVisible(), r(fld.GetTextHeight()),
                 r(fld.GetTextThickness()))] += 1
        for z in f.Zones():
            out[('fp_zone', ','.join(ln(L) for L in z.GetLayerSet().Seq()), ref, z.GetNetname(),
                 tuple(xy(z.Outline().CVertex(i)) for i in range(z.Outline().TotalVertices())))] += 1
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            out[('via', 'F.Cu-B.Cu', xy(t.GetPosition()), r(t.GetWidth(pcbnew.F_Cu)), r(t.GetDrill()),
                 t.GetNetname())] += 1
        else:
            out[('track', ln(t.GetLayer()), xy(t.GetStart()), xy(t.GetEnd()), r(t.GetWidth()), t.GetNetname())] += 1
    for z in b.Zones():
        out[('zone', ','.join(ln(L) for L in z.GetLayerSet().Seq()), z.GetNetname(), z.GetIsRuleArea(),
             z.GetAssignedPriority(), r(z.GetLocalClearance() or 0),
             tuple(xy(z.Outline().CVertex(i)) for i in range(z.Outline().TotalVertices())))] += 1
    for d in b.GetDrawings():
        if d.GetClass() == 'PCB_TEXT':
            out[('text', ln(d.GetLayer()), d.GetText(), xy(d.GetPosition()), round(d.GetTextAngleDegrees(), 2),
                 r(d.GetTextHeight()), r(d.GetTextThickness()), d.IsMirrored())] += 1
        else:
            out[('shape', ln(d.GetLayer()), d.GetShapeStr(), xy(d.GetStart()), xy(d.GetEnd()), r(d.GetWidth()),
                 d.IsSolidFill() if hasattr(d, "IsSolidFill") else d.GetFillMode())] += 1
    return out


old, new = records(sys.argv[1]), records(sys.argv[2])
gone, added = old - new, new - old
by = collections.defaultdict(lambda: [0, 0])
for k, n in gone.items():
    by[(k[0], k[1])][0] += n
for k, n in added.items():
    by[(k[0], k[1])][1] += n
print('%-10s %-28s %8s %8s' % ('kind', 'layer', 'removed', 'added'))
for (kind, layer), (g, a) in sorted(by.items()):
    print('%-10s %-28s %8d %8d' % (kind, layer, g, a))
if not by:
    print('identical')
off = [(k, l) for (k, l) in by if not any(s in l for s in ('Silkscreen', 'Fab'))]
if '--silk-only' in sys.argv:
    if off:
        print('CHANGES OFF THE SILKSCREEN / FAB LAYERS:', off)
        sys.exit(1)
    print('silk-only delta: nothing changed on copper, mask, paste, courtyard, edge, drill or nets')
