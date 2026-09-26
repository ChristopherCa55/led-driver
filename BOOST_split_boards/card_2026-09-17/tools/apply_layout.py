"""Apply a placer layout to the card board and verify every pad (KiCad Python).

usage: python.exe apply_layout.py FRAME.kicad_pcb LAYOUT.json INVENTORY.json OUT.kicad_pcb

LAYOUT.json: {"layout": {REF: [x, y, rot, "F"|"B"], ...}} as card_place.py writes it. Locked parts (J11, H1-H4) are
not moved; their layout entry is only checked. After placing, every pad's KiCad position is compared with the
placer's model (inventory pad offset through the side / rotation transform); the worst difference is printed and
the script stops if it exceeds 1 um, so the plan the check-in reports is the board on disk.
Copy the shipped BOOST_control.kicad_pro next to OUT afterwards (SaveBoard rewrites the project file).
"""
import json, math, sys
import pcbnew

FRAME, LAY, INV, OUT = sys.argv[1:5]
lay = json.load(open(LAY))['layout']
inv = json.load(open(INV))
MM, FM = pcbnew.ToMM, pcbnew.FromMM
MATS = [((1, 0), (0, 1)), ((0, -1), (1, 0)), ((-1, 0), (0, -1)), ((0, 1), (-1, 0))]


def model(ref, x, y, rot, side):
    m = MATS[int(round(rot / 90)) % 4]
    out = {}
    for p in inv[ref]['pads']:
        if not p.get('num'):
            continue
        px, py = p['x'], (-p['y'] if side == 'B' else p['y'])
        out[p['num']] = (x + px * m[0][0] + py * m[1][0], y + px * m[0][1] + py * m[1][1])
    return out


b = pcbnew.LoadBoard(FRAME)
fps = {f.GetReference(): f for f in b.GetFootprints()}
worst, worst_ref, moved = 0.0, None, 0
for ref, (x, y, rot, side) in lay.items():
    f = fps[ref]
    if not f.IsLocked():
        if f.IsFlipped() != (side == 'B'):
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        f.SetOrientationDegrees(rot)
        f.SetPosition(pcbnew.VECTOR2I(FM(x), FM(y)))
        moved += 1
    want = model(ref, x, y, rot, side)
    for p in f.Pads():
        if p.GetNumber() in want:
            d = math.hypot(MM(p.GetPosition().x) - want[p.GetNumber()][0], MM(p.GetPosition().y) - want[p.GetNumber()][1])
            if d > worst:
                worst, worst_ref = d, '%s.%s' % (ref, p.GetNumber())
assert worst < 1e-3, 'pad model mismatch: %s off by %.4f mm' % (worst_ref, worst)
pcbnew.SaveBoard(OUT, b)
print('placed %d footprints, %d locked checked in place; worst pad vs model %.6f mm (%s); saved %s' % (
    moved, len(lay) - moved, worst, worst_ref, OUT))
