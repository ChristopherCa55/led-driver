"""KiCad python: dump every footprint's courtyard bounding boxes (F and B) and its reference / value text boxes.
    python.exe dump_crt.py BOARD OUT.json"""
import json, sys
import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
mm = pcbnew.ToMM
out = {}
for fp in b.GetFootprints():
    fp.BuildCourtyardCaches()
    d = {'side': 'B' if fp.IsFlipped() else 'F', 'x': mm(fp.GetPosition().x), 'y': mm(fp.GetPosition().y),
         'rot': fp.GetOrientationDegrees()}
    for name, lay in (('F', pcbnew.F_CrtYd), ('B', pcbnew.B_CrtYd)):
        poly = fp.GetCourtyard(lay)
        if poly.OutlineCount():
            bb = poly.BBox()
            d['crt_' + name] = [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())]
    texts = []
    for it in fp.GraphicalItems():
        if it.GetClass() in ('PCB_TEXT', 'PCB_FIELD') and it.IsVisible():
            bb = it.GetBoundingBox()
            texts.append([it.GetText(), b.GetLayerName(it.GetLayer()),
                          [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())]])
    for f in fp.GetFields():
        if f.IsVisible():
            bb = f.GetBoundingBox()
            texts.append([f.GetText(), b.GetLayerName(f.GetLayer()),
                          [mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())]])
    d['texts'] = texts
    out[fp.GetReference()] = d
json.dump(out, open(sys.argv[2], 'w'), indent=0)
print(len(out), 'footprints')
