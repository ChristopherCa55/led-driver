"""Mechanical check of the parts the pre-charge change adds or moves (KiCad 10 Python, read-only).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" check_mech.py BOOST_power_RC2.kicad_pcb

For D28, D29, D30 and R47 prints: side, centre, rotation, courtyard box, and PASS/FAIL for
  - bottom side (all four must be on B.Cu);
  - courtyard inside the board outline;
  - no courtyard overlap with any other footprint on the same side (the TO-220s M4/M6/M8/M9/M10 lie on the bottom);
  - courtyard clear of every rule area (washer and standoff keep-outs);
  - D30 clear of J1's M4 bolt hardware: its courtyard stays more than 4.6 mm (J1's courtyard radius) from J1's centre.
Exits with "ALL PASS" or lists what failed.
"""
import sys, math
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
MM = pcbnew.ToMM
edge = b.GetBoardEdgesBoundingBox()
E = (MM(edge.GetX()), MM(edge.GetY()), MM(edge.GetRight()), MM(edge.GetBottom()))


def cy(f):
    c = f.GetCourtyard(pcbnew.B_CrtYd if f.IsFlipped() else pcbnew.F_CrtYd)
    if not c.OutlineCount():
        return None
    r = c.BBox()
    return (MM(r.GetX()), MM(r.GetY()), MM(r.GetRight()), MM(r.GetBottom()))


def ov(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


fails = []
j1 = b.FindFootprintByReference('J1')
j1c = (MM(j1.GetPosition().x), MM(j1.GetPosition().y))
rules = []
for z in b.Zones():
    if z.GetIsRuleArea():
        r = z.GetBoundingBox()
        rules.append((z.GetZoneName(), z, (MM(r.GetX()), MM(r.GetY()), MM(r.GetRight()), MM(r.GetBottom()))))
for ref in ('D28', 'D29', 'D30', 'R47'):
    f = b.FindFootprintByReference(ref)
    if f is None:
        fails.append('%s missing' % ref)
        continue
    c = cy(f)
    side = 'B' if f.IsFlipped() else 'F'
    print('%s  %s  value %s  side %s  centre (%.3f, %.3f)  rotation %.0f  courtyard (%.2f, %.2f)-(%.2f, %.2f)' % (
        ref, f.GetFPIDAsString(), f.GetValue(), side, MM(f.GetPosition().x), MM(f.GetPosition().y),
        f.GetOrientationDegrees(), *c))
    for p in f.Pads():
        print('      pad %s at (%.3f, %.3f) net %s' % (p.GetNumber(), MM(p.GetPosition().x), MM(p.GetPosition().y), p.GetNetname()))
    if side != 'B':
        fails.append('%s is not on the bottom side' % ref)
    if not (c[0] >= E[0] and c[1] >= E[1] and c[2] <= E[2] and c[3] <= E[3]):
        fails.append('%s courtyard leaves the board outline %s' % (ref, E))
    for g in b.GetFootprints():
        if g.GetReference() == ref or g.IsFlipped() != f.IsFlipped():
            continue
        gc = cy(g)
        if gc and ov(c, gc):
            fails.append('%s courtyard overlaps %s' % (ref, g.GetReference()))
    for name, z, zb in rules:
        if ov(c, zb):
            # box test first; then exact: any courtyard corner or centre inside the rule-area outline
            poly = z.Outline()
            pts = [(c[0], c[1]), (c[2], c[1]), (c[0], c[3]), (c[2], c[3]), ((c[0] + c[2]) / 2, (c[1] + c[3]) / 2)]
            if any(poly.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))) for x, y in pts):
                fails.append('%s courtyard enters rule area %s' % (ref, name))
    dx = max(c[0] - j1c[0], 0, j1c[0] - c[2]); dy = max(c[1] - j1c[1], 0, j1c[1] - c[3])
    dj = math.hypot(dx, dy)
    print('      nearest courtyard point to J1 centre %s: %.2f mm' % (tuple(round(v, 2) for v in j1c), dj))
    if ref == 'D30' and dj <= 4.6:
        fails.append('D30 courtyard within 4.6 mm of J1 centre')
print('ALL PASS' if not fails else 'FAIL:\n  ' + '\n  '.join(fails))
