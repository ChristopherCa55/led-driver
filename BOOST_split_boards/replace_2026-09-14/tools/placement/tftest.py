import pcbnew, math
KL = r'C:/Program Files/KiCad/10.0/share/kicad/footprints/Package_TO_SOT_THT.pretty'
b = pcbnew.BOARD()
out = []
for side in ('F', 'B'):
    for rot in (0, 90, 180, 270):
        f = pcbnew.FootprintLoad(KL, 'TO-220-3_Horizontal_TabUp')
        b.Add(f)
        f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(50), pcbnew.FromMM(60)))
        if side == 'B':
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(rot)
        ps = sorted((p.GetNumber(), round(pcbnew.ToMM(p.GetPosition().x), 3), round(pcbnew.ToMM(p.GetPosition().y), 3)) for p in f.Pads())
        hole = [q for q in ps if q[0] == '']
        print(side, rot, 'layer', f.GetLayerName(), 'orient', f.GetOrientationDegrees(), ps)
