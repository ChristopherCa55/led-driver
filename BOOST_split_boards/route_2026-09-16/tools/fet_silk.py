"""MOSFET orientation silk for the power board, silk only (KiCad Python). The user's item 8, 2026-09-24.

usage: python.exe fet_silk.py BOARD_IN.kicad_pcb BOARD_OUT.kicad_pcb [REPORT.json]

For every TO-220 (M1-M10, all on B.Cu with their pins through the board):
  F.SilkS (the side the pins are soldered from): the letters G, D, S beside pads 1, 2, 3 (HuaYi HYG180N10:
    G-D-S = 1-2-3; the footprint's pads 1/2/3 carry the gate / drain / source nets, checked here) and a filled
    pin-1 dot beside pad 1;
  B.SilkS: the footprint's own body-and-tab outline stays; the word TAB is added inside the tab outline (mirrored,
    B-side text), so the body's orientation reads from the placing side.
Text 1.0 mm high, 0.15 mm stroke, upright. Every new item must keep, on its own side:
  0.15 mm from every pad's mask opening (no silk over pads), 0.30 mm from non-plated holes, 0.10 mm from other silk,
  0.30 mm inside the board outline (the notched polygon, not its bounding box);
and the F-side letters must not sit under another part's courtyard, where the body would hide them.
Candidates step out from the pins on either side of the row; the nearest legal one wins, with all three letters on
the same side. Nothing but new silk items is added; nothing is moved or removed.
"""
import json, math, sys
import pcbnew

MM, FM = pcbnew.ToMM, pcbnew.FromMM
args = [a for a in sys.argv[1:] if not a.startswith('--')]
src, out = args[0], args[1]
rep_path = args[2] if len(args) > 2 else None
# --drc=DRC.json: reference texts that DRC already flags (silk over copper / overlap / edge) are not obstacles here;
# silk_pass moves them afterwards, with these new items as obstacles
IGNORE = set()
for a in sys.argv[1:]:
    if a.startswith('--drc='):
        for v in json.load(open(a[6:]))['violations']:
            if v['type'].startswith('silk'):
                for it in v['items']:
                    if it['description'].startswith('Reference field of '):
                        IGNORE.add(it['description'][len('Reference field of '):].split()[0])
b = pcbnew.LoadBoard(src)
ds = b.GetDesignSettings()
MASK = MM(ds.m_SolderMaskExpansion)

outline = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(outline, False)
EDGE = []
for i in range(outline.OutlineCount()):
    o = outline.Outline(i)
    pts = [(MM(o.CPoint(k).x), MM(o.CPoint(k).y)) for k in range(o.PointCount())]
    EDGE += [(pts[k], pts[(k + 1) % len(pts)]) for k in range(len(pts))]


def seg_dist(p, a, c):
    ax, ay = a
    bx, by = c
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L))
    return math.hypot(p[0] - ax - t * dx, p[1] - ay - t * dy)


def inside_board(bb, margin=0.30):
    corners = [(MM(bb.GetX()), MM(bb.GetY())), (MM(bb.GetRight()), MM(bb.GetY())),
               (MM(bb.GetX()), MM(bb.GetBottom())), (MM(bb.GetRight()), MM(bb.GetBottom()))]
    for c in corners:
        if not outline.Contains(pcbnew.VECTOR2I(FM(c[0]), FM(c[1]))):
            return False
        if min(seg_dist(c, a, e) for a, e in EDGE) < margin:
            return False
    return True


def obstacles(cu, silk_layer, crt_layer):
    pads, holes, silk, crt = [], [], [], []
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                holes.append(p.GetEffectiveHoleShape())
            elif p.IsOnLayer(cu):
                pads.append(p.GetEffectiveShape(cu))
        for g in f.GraphicalItems():
            if g.GetLayer() == silk_layer:
                silk.append(g.GetEffectiveTextShape() if g.GetClass() == 'PCB_TEXT' else g.GetEffectiveShape())
        for fld in f.GetFields():
            if fld.IsVisible() and fld.GetLayer() == silk_layer:
                if fld.IsReference() and f.GetReference() in IGNORE:
                    continue
                silk.append(fld.GetEffectiveTextShape())
        if f.GetLayer() == cu:
            # the part's body as seen from above: its Fab outline's box (the courtyard adds a margin a text may use)
            fab = pcbnew.F_Fab if cu == pcbnew.F_Cu else pcbnew.B_Fab
            bb = None
            for g in f.GraphicalItems():
                if g.GetLayer() == fab and g.GetClass() == 'PCB_SHAPE':
                    gb = g.GetBoundingBox()
                    if bb is None:
                        bb = gb
                    else:
                        bb.Merge(gb)
            if bb is not None:
                crt.append((f.GetReference(), bb))
    for d in b.GetDrawings():
        if d.GetLayer() == silk_layer:
            silk.append(d.GetEffectiveTextShape() if d.GetClass() == 'PCB_TEXT' else d.GetEffectiveShape())
    return pads, holes, silk, crt


def why_not(shape, bb, obst, extra, check_crt=True, skip=None):
    pads, holes, silk, crt = obst
    if not inside_board(bb):
        return 'edge'
    if any(shape.Collide(p, FM(0.15 + MASK)) for p in pads):
        return 'pad'
    if any(shape.Collide(h, FM(0.30)) for h in holes):
        return 'hole'
    if any(shape.Collide(s, FM(0.10)) for s in silk + extra):
        return 'silk'
    if check_crt:
        for r, c in crt:
            if r != skip and c.Intersects(bb):
                return 'under ' + r
    return None


def legal(shape, bb, obst, extra, check_crt=True, skip=None):
    return why_not(shape, bb, obst, extra, check_crt, skip) is None


def make_text(txt, layer, x, y, mirrored=False):
    t = pcbnew.PCB_TEXT(b)
    t.SetText(txt)
    t.SetLayer(layer)
    t.SetTextSize(pcbnew.VECTOR2I(FM(1.0), FM(1.0)))
    t.SetTextThickness(FM(0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER)
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetMirrored(mirrored)
    t.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
    return t


def make_dot(layer, x, y, r=0.30):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetLayer(layer)
    s.SetCenter(pcbnew.VECTOR2I(FM(x), FM(y)))
    s.SetEnd(pcbnew.VECTOR2I(FM(x + r), FM(y)))
    s.SetFilled(True)
    s.SetWidth(FM(0.15))
    return s


EXPECT = {'1': 'gate', '2': 'drain', '3': 'source'}
fets = sorted([f for f in b.GetFootprints() if 'TO-220' in f.GetFPIDAsString()],
              key=lambda f: int(f.GetReference()[1:]))
F_obst = obstacles(pcbnew.F_Cu, pcbnew.F_SilkS, pcbnew.F_CrtYd)
B_obst = obstacles(pcbnew.B_Cu, pcbnew.B_SilkS, pcbnew.B_CrtYd)
F_new, B_new = [], []
report = {}
KEEP = []
for f in fets:
    ref = f.GetReference()
    pads = {p.GetNumber(): p for p in f.Pads() if p.GetNumber() in ('1', '2', '3')}
    P = {n: (MM(p.GetPosition().x), MM(p.GetPosition().y)) for n, p in pads.items()}
    nets = {n: p.GetNetname() for n, p in pads.items()}
    ux, uy = P['3'][0] - P['1'][0], P['3'][1] - P['1'][1]
    L = math.hypot(ux, uy)
    ux, uy = ux / L, uy / L
    nx, ny = -uy, ux
    # the body lies on one side of the pin row (its B.SilkS outline's centroid says which); its far end is the tab
    silkB = [g for g in f.GraphicalItems() if g.GetLayer() == pcbnew.B_SilkS and g.GetClass() == 'PCB_SHAPE']
    xs = [MM(v) for g in silkB for v in (g.GetStart().x, g.GetEnd().x)]
    ys = [MM(v) for g in silkB for v in (g.GetStart().y, g.GetEnd().y)]
    cxo, cyo = sum(xs) / len(xs), sum(ys) / len(ys)
    proj = (cxo - P['2'][0]) * nx + (cyo - P['2'][1]) * ny
    bx, by = (nx, ny) if proj > 0 else (-nx, -ny)
    extent = max((x - P['2'][0]) * bx + (y - P['2'][1]) * by for x, y in zip(xs, ys))
    D_OFF = [1.65, 1.8, 1.95, 2.1, 2.3, 2.5, 2.75, 3.0]
    ROW_END = [1.6, 1.8, 2.0, 2.3]

    def place(layer, items, obst, new, mirrored=False):
        texts = []
        for ch, x, y in items:
            t = make_text(ch, layer, x, y, mirrored)
            if not legal(t.GetEffectiveTextShape(), t.GetBoundingBox(), obst,
                         new + [tt.GetEffectiveTextShape() for tt in texts], skip=ref):
                return None
            texts.append(t)
        return texts

    def perp(chars, s, d):
        return [(ch, P[n][0] + s * d * nx, P[n][1] + s * d * ny) for n, ch in chars]

    # F.SilkS, in the order of preference: G D S beside the pads (one side); G and S at the two ends of the row;
    # G beside pad 1; G at the pad-1 end of the row
    texts, mode = None, None
    tries = [('G D S', perp((('1', 'G'), ('2', 'D'), ('3', 'S')), s_, d_)) for d_ in D_OFF for s_ in (1, -1)]
    tries += [('G .. S at the row ends', [('G', P['1'][0] - k * ux, P['1'][1] - k * uy),
                                          ('S', P['3'][0] + k * ux, P['3'][1] + k * uy)]) for k in ROW_END]
    tries += [('G', perp((('1', 'G'),), s_, d_)) for d_ in D_OFF for s_ in (1, -1)]
    tries += [('G at the row end', [('G', P['1'][0] - k * ux, P['1'][1] - k * uy)]) for k in ROW_END]
    # G off the corner of pad 1, nearer pad 1 than any other pad
    tries += [('G at the corner of pad 1', [('G', P['1'][0] - a_ * ux + s_ * c_ * nx, P['1'][1] - a_ * uy + s_ * c_ * ny)])
              for a_ in (0.8, 1.0, 1.2, 1.4) for c_ in (1.3, 1.5, 1.7) for s_ in (1, -1)]
    for m, items in tries:
        texts = place(pcbnew.F_SilkS, items, F_obst, F_new)
        if texts:
            mode = m
            break
    for t in texts or []:
        b.Add(t)
        KEEP.append(t)
        F_new.append(t.GetEffectiveTextShape())
    # pin-1 dot on F.SilkS: on the row axis beyond pad 1 (beyond the G if the G is there), else beside pad 1
    cands = [(P['1'][0] - k * ux, P['1'][1] - k * uy) for k in (1.6, 1.8, 2.0, 2.3, 2.8, 3.0, 3.2)]
    cands += [(P['1'][0] + s_ * d_ * nx, P['1'][1] + s_ * d_ * ny) for d_ in (1.4, 1.6, 1.8, 2.0, 2.3)
              for s_ in (1, -1)]
    if texts and mode in ('G D S', 'G'):
        g = texts[0].GetPosition()
        cands = [(MM(g.x) - k * ux, MM(g.y) - k * uy) for k in (0.95, 1.1, 1.3)] + cands
    dot = None
    for x, y in cands:
        c = make_dot(pcbnew.F_SilkS, x, y)
        if legal(c.GetEffectiveShape(), c.GetBoundingBox(), F_obst, F_new, skip=ref):
            dot = c
            break
    if dot:
        b.Add(dot)
        KEEP.append(dot)
        F_new.append(dot.GetEffectiveShape())
    # B.SilkS G D S, where F.SilkS has less than all three: on the side of the row away from the body
    btexts = None
    if mode != 'G D S':
        sa = -1 if (bx * nx + by * ny) > 0 else 1
        for d_ in D_OFF:
            btexts = place(pcbnew.B_SilkS, perp((('1', 'G'), ('2', 'D'), ('3', 'S')), sa, d_), B_obst, B_new,
                           mirrored=True)
            if btexts:
                break
        if not btexts:
            for d_ in D_OFF:
                btexts = place(pcbnew.B_SilkS, perp((('1', 'G'),), sa, d_), B_obst, B_new, mirrored=True)
                if btexts:
                    break
        for t in btexts or []:
            b.Add(t)
            KEEP.append(t)
            B_new.append(t.GetEffectiveTextShape())
    # B.SilkS: TAB inside the tab end of the body outline
    tab = None
    for back in (1.3, 1.6, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0):
        for side in (0.0, 2.6, -2.6, 3.4, -3.4):
            x = P['2'][0] + (extent - back) * bx + side * ux
            y = P['2'][1] + (extent - back) * by + side * uy
            t = make_text('TAB', pcbnew.B_SilkS, x, y, mirrored=True)
            if abs(ux) < 0.5:          # row runs along y: the body runs along x, turn the word to lie along the tab
                t.SetTextAngleDegrees(90)
            if legal(t.GetEffectiveTextShape(), t.GetBoundingBox(), B_obst, B_new, check_crt=False):
                tab = t
                break
        if tab:
            break
    if tab:
        b.Add(tab)
        KEEP.append(tab)
        B_new.append(tab.GetEffectiveTextShape())
    pos = lambda t: (t.GetText(), round(MM(t.GetPosition().x), 3), round(MM(t.GetPosition().y), 3))
    report[ref] = {
        'pads': {n: {'xy': P[n], 'net': nets[n], 'role': EXPECT[n]} for n in ('1', '2', '3')},
        'F_mode': mode or 'none', 'F_letters': [pos(t) for t in texts or []],
        'F_pin1_dot': (round(MM(dot.GetCenter().x), 3), round(MM(dot.GetCenter().y), 3)) if dot else None,
        'B_letters': [pos(t) for t in btexts or []],
        'B_tab_text': pos(tab) if tab else None,
    }
    print('%-4s F: %-24s dot %-3s | B: %-6s TAB %s | pads 1/2/3 = %s' % (
        ref, mode or 'NONE', 'yes' if dot else 'NO', ' '.join(t.GetText() for t in btexts or []) or '-',
        'yes' if tab else 'NO', ' / '.join(nets[n] for n in ('1', '2', '3'))))
pcbnew.SaveBoard(out, b)
if rep_path:
    json.dump(report, open(rep_path, 'w'), indent=1)
print('saved', out)
