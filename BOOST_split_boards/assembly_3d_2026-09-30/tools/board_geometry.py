"""work/geometry.json for build_assembly.py: footprint geometry of the two boards (KiCad Python). 2026-09-30.

usage: python.exe tools/board_geometry.py POWER.kicad_pcb CARD.kicad_pcb OUT.json

Per footprint: pos, rot (degrees), side, pad_bbox (union of pad boxes), crt_bbox (courtyard polygon box on the
footprint's side, or null), fab_bbox (union of the Fab-layer shapes, text excluded, or null), value, and npth
([x, y, drill x, drill y] per non-plated hole). Per board: outline_bbox (Edge.Cuts shapes at their centre lines).
Rebuilds the schema of assembly_3d_2026-09-24/work/geometry.json, whose generator was not kept.
"""
import json, sys
import pcbnew

MM = pcbnew.ToMM


def r6(v):
    return round(MM(v), 6)


def union(boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]


def box(bb, shrink=0):
    return [r6(bb.GetX() + shrink), r6(bb.GetY() + shrink), r6(bb.GetRight() - shrink), r6(bb.GetBottom() - shrink)]


def board(path):
    b = pcbnew.LoadBoard(path)
    fps = {}
    for f in b.GetFootprints():
        flip = f.IsFlipped()
        crt = pcbnew.B_CrtYd if flip else pcbnew.F_CrtYd
        fab = pcbnew.B_Fab if flip else pcbnew.F_Fab
        cy = f.GetCourtyard(crt)
        npth = []
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                d = p.GetDrillSize()
                npth.append([r6(p.GetPosition().x), r6(p.GetPosition().y), r6(d.x), r6(d.y)])
        fps[f.GetReference()] = {
            'pos': [r6(f.GetPosition().x), r6(f.GetPosition().y)],
            'rot': f.GetOrientationDegrees(),
            'side': 'bottom' if flip else 'top',
            'pad_bbox': union([box(p.GetBoundingBox()) for p in f.Pads()]),
            'crt_bbox': box(cy.BBox()) if cy.OutlineCount() else None,
            'fab_bbox': union([box(g.GetBoundingBox()) for g in f.GraphicalItems()
                               if g.GetLayer() == fab and g.GetClass() == 'PCB_SHAPE']),
            'value': f.GetValue(),
            'npth': npth,
        }
    edges = [box(d.GetBoundingBox(), d.GetWidth() // 2) for d in b.GetDrawings()
             if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() == 'PCB_SHAPE']
    return {'fps': fps, 'outline_bbox': union(edges)}


out = {'power': board(sys.argv[1]), 'card': board(sys.argv[2])}
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print('wrote %s: power %d footprints, card %d' % (sys.argv[3], len(out['power']['fps']), len(out['card']['fps'])))
