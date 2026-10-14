"""Find legal GND stitching-via spots inside given GND fill pieces (KiCad's python.exe; the board is only read).

    python.exe stitch_vias.py BOARD.kicad_pcb JOB.json OUT_SPEC.json

JOB.json: {"via": [0.5, 0.3], "clearance": 0.2, "net": "GND",
           "pieces": [{"layer": "In1.Cu", "x": 73.2, "y": 86.9, "n": 2}, ...]}      (a point inside each piece)
For each piece: the GND filled polygon of that layer that contains (x, y); candidate centres inside it, a via radius
+ clearance in from its edge, clear (by the same rules as route_new.py) of every other-net pad / track / via on every
layer, of every hole (hole to hole 0.25 mm), of rule areas and of the board edge. Picks n spots: the first as far as
possible from the piece's existing vias, the next as far as possible from those. Writes a pcb_text_edit.py spec.
"""
import json, math, os, sys
import numpy as np
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from route_new import Grid, polys, mm, G, MARGIN


def main():
    board, jobp, outp = sys.argv[1:4]
    job = json.load(open(jobp))
    b = pcbnew.LoadBoard(board)
    net = job.get('net', 'GND')
    vdia, vdrill = job.get('via', [0.5, 0.3])
    vr, clr = vdia / 2, job.get('clearance', 0.2)
    bb = b.GetBoardEdgesBoundingBox()
    ex1, ey1, ex2, ey2 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
    g = Grid(ex1, ey1, ex2, ey2)
    layers = {pcbnew.BOARD.GetLayerName(b, l): l for l in b.GetEnabledLayers().CuStack()}
    vblk = g.empty()
    vblk |= (g.X < ex1 + 0.3 + vr) | (g.X > ex2 - 0.3 - vr) | (g.Y < ey1 + 0.3 + vr) | (g.Y > ey2 - 0.3 - vr)
    gvias = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            c = p.GetPosition()
            if p.GetDrillSizeX() > 0:
                g.disc(vblk, mm(c.x), mm(c.y), mm(max(p.GetDrillSizeX(), p.GetDrillSizeY())) / 2 + 0.3 + vdrill / 2 + MARGIN)
            for ln, l in layers.items():
                if p.IsOnLayer(l) and p.FlashLayer(l) and p.GetNetname() != net:
                    ps = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(ps, l, pcbnew.FromMM(clr + vr + MARGIN), pcbnew.FromMM(0.005),
                                              pcbnew.ERROR_OUTSIDE)
                    for pts in polys(ps):
                        g.poly(vblk, pts)
            # SMD pads of any net: no via in a pad
            if p.GetDrillSizeX() == 0:
                ps = pcbnew.SHAPE_POLY_SET()
                p.TransformShapeToPolygon(ps, p.GetLayer(), pcbnew.FromMM(vr + 0.05), pcbnew.FromMM(0.005),
                                          pcbnew.ERROR_OUTSIDE)
                for pts in polys(ps):
                    g.poly(vblk, pts)
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            c = t.GetPosition()
            x, y = mm(c.x), mm(c.y)
            g.disc(vblk, x, y, mm(t.GetDrillValue()) / 2 + 0.25 + vdrill / 2 + MARGIN)
            if t.GetNetname() != net:
                g.disc(vblk, x, y, mm(t.GetWidth(pcbnew.F_Cu)) / 2 + clr + vr + MARGIN)
            else:
                gvias.append((x, y))
        elif t.GetNetname() != net:
            s, e = t.GetStart(), t.GetEnd()
            g.capsule(vblk, mm(s.x), mm(s.y), mm(e.x), mm(e.y), mm(t.GetWidth()) / 2 + clr + vr + MARGIN)
    for z in b.Zones():
        if z.GetIsRuleArea() and z.GetDoNotAllowVias():
            for pts in polys(z.Outline()):
                g.poly(vblk, pts)
    out = []
    for pc in job['pieces']:
        lid = layers[pc['layer']]
        piece = None
        for z in b.Zones():
            if z.GetNetname() == net and not z.GetIsRuleArea() and z.IsOnLayer(lid):
                for pts in polys(z.GetFilledPolysList(lid)):
                    m = g.empty()
                    g.poly(m, pts)
                    i, j = g.cell(pc['x'], pc['y'])
                    if m[i, j]:
                        piece = m
        if piece is None:
            print('no GND fill piece at', pc)
            continue
        inner = piece.copy()
        k = int(math.ceil((vr + clr) / G))
        for dy in range(-k, k + 1):
            for dx in range(-k, k + 1):
                if dx * dx + dy * dy <= k * k:
                    inner &= np.roll(np.roll(piece, dy, 0), dx, 1)
        cand = inner & ~vblk
        ys, xs = np.nonzero(cand)
        if not len(xs):
            print('no legal spot in piece', pc)
            continue
        X, Y = g.X[ys, xs], g.Y[ys, xs]
        have = [(vx, vy) for vx, vy in gvias if piece[g.cell(vx, vy)]]
        print('piece', pc, 'existing GND vias in it:', have, 'legal cells:', len(xs))
        for n in range(pc.get('n', 1)):
            if have:
                d = np.min([np.hypot(X - hx, Y - hy) for hx, hy in have], axis=0)
            else:
                d = -np.hypot(X - pc['x'], Y - pc['y'])
            if not len(d) or (have and d.max() < vdrill + 0.25 + 0.1):
                break
            k_ = int(np.argmax(d))
            x, y = round(float(X[k_]), 3), round(float(Y[k_]), 3)
            out.append(dict(net=net, x=x, y=y, size=vdia, drill=vdrill))
            have.append((x, y))
            print('   via at (%g, %g), %.2f mm from the nearest GND via' % (x, y, d[k_] if have[:-1] else 0))
    json.dump(dict(_why=job.get('_why', 'stitch_vias.py'), add_vias=out), open(outp, 'w'), indent=1)
    print('wrote', outp, len(out), 'vias')


if __name__ == '__main__':
    main()
