"""BOOST assembly in its case: STEP + GLB + clearance table (OCP 8, in the boost3d venv). 2026-09-24.

usage: python tools/build_assembly.py        (run from assembly_3d_2026-09-30/)

Frame (mm): X = board x + 22 and Y = 28 - board y (the case drilling drawing's box coordinates are X = box x,
Y = -box y), Z up from the case floor. Inputs: work/power.step and work/card.step (kicad-cli pcb export step of the
release-candidate boards), work/geometry.json (footprint geometry from the board files). Every dimension that is
not in the board files or the notes is marked ASSUMED where it is set, and listed in SUBSTITUTES.
"""
import json, math, sys, collections
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorType
from OCP.collections import (Sequence_TDF_Label, Map_TCollection_AsciiString,
                             IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString)
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Ax2, gp_Dir
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_Color, Quantity_ColorRGBA, Quantity_TypeOfColor
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.Message import Message_ProgressRange
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder

G = json.load(open('work/geometry.json'))
DX, DY = 22.0, 28.0

# ---------------- the stack (mm above the case floor) ----------------
PAD_T = 0.93            # THERM-A-GAP G579 0.050 in, compressed (BUILD_NOTES)
Z_PWR = 5.50            # power board underside (5.0 stud + 0.5 washer)
T_NOM = 1.60            # nominal board thickness used by the stack; the KiCad models are 1.654 thick
T_MODEL = 1.654
Z_PWR_TOP = Z_PWR + T_MODEL              # parts sit on the model's top: 0.054 mm pessimistic
Z_FF0 = Z_PWR + T_NOM                    # female-female standoff seats on the nominal board top
Z_FF1 = Z_FF0 + 20.0
Z_CARD = Z_FF1 + 1.5                     # three 0.5 mm washers -> 28.60
T_CARD_MODEL = 1.5468           # 2026-10-01: 6 layers, 0.5 oz inner copper: JLC stack 1.5468 thick (was 1.609)
Z_CARD_TOP = Z_CARD + T_CARD_MODEL
Z_LID = 33.0
SUBSTITUTES = []


def sub(what, source):
    SUBSTITUTES.append((what, source))


def cs_xy(bx, by):                        # board coordinates -> case frame
    return bx + DX, DY - by


def box(x0, y0, z0, x1, y1, z1):
    return BRepPrimAPI_MakeBox(gp_Pnt(min(x0, x1), min(y0, y1), min(z0, z1)),
                               gp_Pnt(max(x0, x1), max(y0, y1), max(z0, z1))).Shape()


def cyl(x, y, z0, r, h):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(0, 0, 1)), r, h).Shape()


def ring(x, y, z0, ro, ri, h):
    return BRepAlgoAPI_Cut(cyl(x, y, z0, ro, h), cyl(x, y, z0 - 0.1, ri, h + 0.2)).Shape()


def hexprism(x, y, z0, af, h):
    r = af / math.sqrt(3)                 # across-corners radius
    poly = BRepBuilderAPI_MakePolygon()
    for k in range(6):
        a = math.radians(60 * k)
        poly.Add(gp_Pnt(x + r * math.cos(a), y + r * math.sin(a), z0))
    poly.Close()
    face = BRepBuilderAPI_MakeFace(poly.Wire()).Face()
    return BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, h)).Shape()


# ---------------- load both boards into one document ----------------
doc = TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
ST = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
CT = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())


def name_of(label):
    a = TDataStd_Name()
    return a.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), a) else ''


def set_name(label, n):
    TDataStd_Name.Set_s(label, TCollection_ExtendedString(n))


def load_board(path):
    before = Sequence_TDF_Label()
    ST.GetFreeShapes(before)
    seen = set(before.Value(i).EntryDumpToString() if hasattr(before.Value(i), 'EntryDumpToString') else i
               for i in range(1, before.Length() + 1))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    assert r.ReadFile(path) == 1, path
    r.Transfer(doc)
    after = Sequence_TDF_Label()
    ST.GetFreeShapes(after)
    return after.Value(after.Length())


def components(label):
    seq = Sequence_TDF_Label()
    ST.GetComponents_s(label, seq, False)
    return [seq.Value(i) for i in range(1, seq.Length() + 1)]


P_TOP = load_board('work/power.step')
C_TOP = load_board('work/card.step')
ROOT = ST.NewShape()
set_name(ROOT, 'BOOST_assembly')


def trsf(dx, dy, dz):
    t = gp_Trsf()
    t.SetTranslation(gp_Vec(dx, dy, dz))
    return t


# KiCad STEP: X = x, Y = -y, board underside at Z = 0  ->  case frame is a pure translation
T_P = trsf(DX, DY, Z_PWR)
T_C = trsf(DX, DY, Z_CARD)
# the generic KiCad 2x15 socket/header models are the wrong parts: replaced below by Samtec-dimensioned solids
for top, ref in ((P_TOP, 'J10'), (C_TOP, 'J11')):
    for c in components(top):
        if name_of(c) == ref:
            proto = TDF_Label()
            ST.GetReferredShape_s(c, proto)
            ST.RemoveComponent(c)
            ST.RemoveShape(proto, True)          # the model would otherwise stay behind as a free shape
set_name(ST.AddComponent(ROOT, P_TOP, TopLoc_Location(T_P)), 'power_board')
set_name(ST.AddComponent(ROOT, C_TOP, TopLoc_Location(T_C)), 'control_card')

# shapes for the clearance work: (group, name, shape in the case frame)
SH = []
for top, T, grp in ((P_TOP, T_P, 'power'), (C_TOP, T_C, 'card')):
    for c in components(top):
        s = ST.GetShape_s(c).Moved(TopLoc_Location(T))
        n = name_of(c)
        if not n or n.startswith('=>'):
            ref = TDF_Label()
            ST.GetReferredShape_s(c, ref)
            n = name_of(ref)
        SH.append((grp, n, s))

HW = []           # (group, name, shape, rgba)


def add(group, name, shape, rgba):
    HW.append((group, name, shape, rgba))
    SH.append((group, name, shape))


NYLON = (0.93, 0.92, 0.86, 1.0)
STEEL = (0.62, 0.64, 0.66, 1.0)
ALU = (0.78, 0.79, 0.80, 1.0)
PAD = (0.95, 0.55, 0.62, 1.0)
KEEP = (0.90, 0.15, 0.15, 0.25)
ACCESS = (0.95, 0.80, 0.10, 0.22)
PARTC = (0.20, 0.20, 0.22, 1.0)

fp = G['power']['fps']
fc = G['card']['fps']

# ---- standoff stacks at H5-H8 (same x, y as the card's H1-H4) ----
for h in ('H5', 'H6', 'H7', 'H8'):
    x, y = cs_xy(*fp[h]['npth'][0][:2])
    add('hardware', h + ' stud HTSN-M3-5-3 (hex 6 AF x 5.0)', hexprism(x, y, 0.0, 6.0, 5.0), NYLON)
    add('hardware', h + ' stud thread M3 (length ASSUMED 5 mm above the hex)', cyl(x, y, 5.0, 1.5, 5.0), NYLON)
    add('hardware', h + ' washer TR NWE-34815-M3 (7.0 / 3.2 x 0.5)', ring(x, y, 5.0, 3.5, 1.6, 0.5), NYLON)
    add('hardware', h + ' female-female HNSM3-20-5.5-1 (hex 5.5 AF x 20)', hexprism(x, y, Z_FF0, 5.5, 20.0), NYLON)
    add('hardware', h + ' washers 3 x TR NWE-34815-M3', ring(x, y, Z_FF1, 3.5, 1.6, 1.5), NYLON)
    add('hardware', h + ' card screw 97790803211 head (5.5 x 2.1)', cyl(x, y, Z_CARD_TOP, 2.75, 2.1), NYLON)
    add('hardware', h + ' card screw shank M3 x 8', cyl(x, y, Z_CARD_TOP - 8.0, 1.5, 8.0), NYLON)
sub('Standoff stack H5-H8 / H1-H4', 'BUILD_NOTES: Essentra HTSN-M3-5-3 (5 mm body, 6 mm hex), TR NWE-34815-M3 washers '
    '0.50 mm, Essentra HNSM3-20-5.5-1 (20 mm, 5.5 mm hex), Wurth 97790803211 (head 2.1 x 5.5). Washer OD 7.0 / ID 3.2 '
    'from the Farnell / Newark listing (which gives 0.51 mm thick; the stack uses the notes 0.50). Stud thread '
    'length ASSUMED 5 mm')

# ---- FET tab screws, spacers, bushings, and the thermal pads ----
FETS = ['M%d' % k for k in range(1, 11)]
SCREWED = ['M1', 'M8', 'M9', 'M10']
for m in FETS:
    f = fp[m]
    fb = f['fab_bbox']
    # body axis: from the pin row (pads) to the far end of the Fab outline
    pads = f['pad_bbox']
    px, py = f['pos']
    cx, cy = (fb[0] + fb[2]) / 2, (fb[1] + fb[3]) / 2
    along_x = abs(cx - px) > abs(cy - py)
    if along_x:
        far = fb[2] if cx > px else fb[0]
        sgn = 1 if cx > px else -1
        bcx, bcy = far - sgn * 7.8, (fb[1] + fb[3]) / 2
        x0, x1, y0, y1 = bcx - 8.0, bcx + 8.0, bcy - 5.0, bcy + 5.0
    else:
        far = fb[3] if cy > py else fb[1]
        sgn = 1 if cy > py else -1
        bcx, bcy = (fb[0] + fb[2]) / 2, far - sgn * 7.8
        x0, x1, y0, y1 = bcx - 5.0, bcx + 5.0, bcy - 8.0, bcy + 8.0
    X0, Y0 = cs_xy(x0, y0)
    X1, Y1 = cs_xy(x1, y1)
    pad = box(X0, Y0, 0.0, X1, Y1, PAD_T)
    if m in SCREWED:
        hx, hy = cs_xy(*f['npth'][0][:2])
        pad = BRepAlgoAPI_Cut(pad, cyl(hx, hy, -0.1, 1.5, PAD_T + 0.2)).Shape()
        add('hardware', m + ' tab screw McMaster 92000A107 M2.5 x 12 pan head (5.0 x 2.1)',
            cyl(hx, hy, Z_PWR_TOP, 2.5, 2.1), STEEL)
        add('hardware', m + ' tab screw shank M2.5', cyl(hx, hy, Z_PWR_TOP - 12.0, 1.25, 12.0), STEEL)
        add('hardware', m + ' gap spacer McMaster 93657A200 nylon 2.0 mm (OD 4.5), 0.25 mm free play below',
            ring(hx, hy, Z_PWR - 2.0, 2.25, 1.3, 2.0), NYLON)
        add('hardware', m + ' shoulder washer 7721-7PPSG flange 1.02 mm (OD ASSUMED 6.35)',
            ring(hx, hy, Z_PWR - 2.25 - 1.02, 3.175, 1.3, 1.02), NYLON)
        top = Z_PWR_TOP + 2.1
        add('keepout', m + ' screwdriver access (4.0 mm radius, head to lid)', cyl(hx, hy, top, 4.0, Z_LID - top),
            ACCESS)
    add('hardware', m + ' thermal pad G579 10 x 16, 0.93 compressed', pad, PAD)
sub('Thermal pads', 'BUILD_NOTES: Parker Chomerics THERM-A-GAP G579 0.050 in, cut ~10 x 16 mm, 3.0 mm hole at the '
    'screwed FETs, 0.93 mm compressed. Centred on the FET body (Fab outline), long side along the body')
sub('FET tab screws M1/M8/M9/M10', 'BUILD_NOTES 2026-09-25: McMaster 92000A107 M2.5 x 12 pan head, head 5.0 x 2.1 '
    '(mcmaster.com); McMaster 93657A200 nylon spacer 2.0 mm long, 4.5 mm OD (mcmaster.com), 0.25 mm short of the '
    'tab-washer stack by design; Aavid 7721-7PPSG flange 1.02 mm (OD ASSUMED 6.35)')

# ---- L1 (no 3D model) ----
fl = fp['L1']['fab_bbox']
X0, Y0 = cs_xy(fl[0], fl[1])
X1, Y1 = cs_xy(fl[2], fl[3])
add('power', 'L1 CSCF3218-6R8MC body 22.5 x 32.0 x 19.0', box(X0, Y0, Z_PWR_TOP, X1, Y1, Z_PWR_TOP + 19.0), PARTC)
for pnum in ('1', '2'):
    pass
# J-lead terminals: from the body edge over the two 8 x 6 mm pads (x 57.84-65.84), height ASSUMED 3 mm
for yc in (40.54, 52.54):
    a0, b0 = cs_xy(fl[2], yc - 3.0)
    a1, b1 = cs_xy(65.84, yc + 3.0)
    add('power', 'L1 terminal (height ASSUMED 3 mm)', box(a0, b0, Z_PWR_TOP, a1, b1, Z_PWR_TOP + 3.0), STEEL)
sub('L1 CSCF3218-6R8MC', 'notes (Codaca): body 32.0 x 22.5 x 19.0 mm, placed on its footprint\'s Fab outline; the two '
    'J-lead terminals drawn as 3 mm blocks over their pads (terminal height ASSUMED)')

# ---- R1 (no 3D model) ----
fr = fp['R1']['fab_bbox']
X0, Y0 = cs_xy(fr[0], fr[1])
X1, Y1 = cs_xy(fr[2], fr[3])
add('power', 'R1 CSS4J-4026R-1L00F (H 2.70 max)', box(X0, Y0, Z_PWR_TOP, X1, Y1, Z_PWR_TOP + 2.70), STEEL)
sub('R1 CSS4J-4026R-1L00F (rev6)', 'Bourns CSS4J-4026 datasheet: the 1 mOhm R version is 2.70 mm max (the 2 mOhm K '
    'version of rev5 was 2.93); plan from the footprint\'s Fab outline')

# ---- J10 / J11 Samtec pair ----
jp = fp['J10']['pad_bbox']
jcx, jcy = (jp[0] + jp[2]) / 2, (jp[1] + jp[3]) / 2
W_ENV, L_ENV = 5.08, 38.10          # ASSUMED envelope: 2 rows x 2.54 by 15 x 2.54
X0, Y0 = cs_xy(jcx - W_ENV / 2, jcy - L_ENV / 2)
X1, Y1 = cs_xy(jcx + W_ENV / 2, jcy + L_ENV / 2)
ESQ_TOP = Z_PWR_TOP + 18.67
add('power', 'J10 Samtec ESQ-115-44-G-D socket body (18.67 tall)', box(X0, Y0, Z_PWR_TOP, X1, Y1, ESQ_TOP), PARTC)
TSW_BOT = Z_CARD - 2.54
add('card', 'J11 Samtec TSW-115-07-G-D insulator (2.54)', box(X0, Y0, TSW_BOT, X1, Y1, Z_CARD), PARTC)
jc = fc['J11']['pad_bbox']
for i in range(15):
    for j in range(2):
        px = jc[0] + 0.85 + j * 2.54
        py = jc[1] + 0.85 + i * 2.54
        X, Y = cs_xy(px, py)
        add('card', 'J11 post', box(X - 0.32, Y - 0.32, TSW_BOT - 5.84, X + 0.32, Y + 0.32, TSW_BOT),
            (0.85, 0.72, 0.30, 1.0))
        add('card', 'J11 tail above the card', box(X - 0.32, Y - 0.32, Z_CARD_TOP, X + 0.32, Y + 0.32,
                                                    Z_CARD + 2.54 + 0.0), (0.85, 0.72, 0.30, 1.0))
sub('J10 / J11 mated pair', 'notes (Samtec F-218 / F-219): ESQ -44 body 18.67 mm, TSW -07 insulator 2.54, post '
    '5.84, tail 2.54; plan envelope 5.08 x 38.10 ASSUMED from the 2.54 mm pitch (2 x 15), not from the Samtec drawing')

# ---- J9 wire bundle and the cable tie under the card ----
j9 = fc['J9']['pad_bbox']
X0, Y0 = cs_xy(G['card']['outline_bbox'][0] - 6.0, j9[1])
X1, Y1 = cs_xy(j9[2], j9[3])
add('card', 'J9 wires (11 x 26-28 AWG, bundle 1.5 mm deep ASSUMED)', box(X0, Y0, Z_CARD - 1.5, X1, Y1, Z_CARD),
    (0.75, 0.15, 0.10, 1.0))
slot = fc['J9']['npth']
tx, ty = (slot[0][0] + slot[1][0]) / 2, (slot[0][1] + slot[1][1]) / 2
X0, Y0 = cs_xy(tx - 2.5, ty - 2.25)
X1, Y1 = cs_xy(tx + 2.5, ty + 2.25)
add('card', 'J9 cable-tie head (5.0 x 4.5 x 3.5 ASSUMED)', box(X0, Y0, Z_CARD - 3.5, X1, Y1, Z_CARD),
    (0.10, 0.10, 0.10, 1.0))
sub('J9 wire exit', 'BUILD_NOTES: 11 wires 26-28 AWG in from the card underside, along the underside to the west edge, '
    'one cable tie through the two slots, head on the underside. Bundle depth 1.5 mm and tie head 5.0 x 4.5 x 3.5 '
    'ASSUMED')

# ---- case, lid, penetrator keep-outs ----
WALL = 3.0                                  # ASSUMED; only the inside is specified
add('case', 'case floor (10 mm)', box(-WALL, -90 - WALL, -10.0, 128 + WALL, WALL, 0.0), ALU)
for n, s in (('case wall west', box(-WALL, -90 - WALL, 0, 0, WALL, Z_LID)),
             ('case wall east', box(128, -90 - WALL, 0, 128 + WALL, WALL, Z_LID)),
             ('case wall north', box(0, 0, 0, 128, WALL, Z_LID)),
             ('case wall south', box(0, -90 - WALL, 0, 128, -90, Z_LID))):
    add('case', n, s, ALU)
add('lid', 'lid (underside at 33.0)', box(-WALL, -90 - WALL, Z_LID, 128 + WALL, WALL, Z_LID + 3.0),
    (0.78, 0.79, 0.80, 0.18))
for bx, by in ((9.5, 3.5), (118.5, 3.5)):
    add('keepout', 'penetrator keep-out box (%.1f, %.1f), 15 x 10' % (bx, by), cyl(bx, -by, 0.0, 7.5, 10.0), KEEP)
sub('Case and lid', 'notes: inside 128 x 90 x 33 mm, 10 mm floor, lid underside at 33.0; wall and lid thickness 3 mm '
    'ASSUMED (not in the notes); penetrators at box (9.5, 3.5) and (118.5, 3.5) with 15 mm x 10 mm keep-outs')

# ---- can envelopes at the datasheet maximum height (clearance only, not drawn) ----
ENV = []
for r, f in fp.items():
    v = f['value']
    if '220' in v and r.startswith('C') and f['crt_bbox'] and 'CP' not in v:
        pass
for r in ('C70', 'C71', 'C74', 'C75', 'C77', 'C78', 'C86', 'C87', 'C88'):
    x, y = cs_xy(*fp[r]['pos'])
    ENV.append((r, 'EEH-ZU1H221P 16.8 max', cyl(x, y, Z_PWR_TOP, 5.0, 16.8), Z_PWR_TOP + 16.8))
for r in ('C40', 'C69', 'C85'):
    x, y = cs_xy(*fp[r]['pos'])
    ENV.append((r, 'EEH-ZU1E681UP 12.8 max', cyl(x, y, Z_PWR_TOP, 5.0, 12.8), Z_PWR_TOP + 12.8))
sub('Can heights for the clearance checks', 'JLC/LCSC listings of 2026-09-24: EEH-ZU1H221P seated height 16.8 mm max '
    '(the KiCad model is 16.45); EEH-ZU1E681UP 12.5 max listed, package D10 x 12.8, 12.8 used. Diameter 10.0')

# ---------------- write the substitutes into the document ----------------
HWLAB = ST.NewShape()
set_name(HWLAB, 'hardware_case_and_keepouts')
for group, name, shape, rgba in HW:
    lab = ST.AddShape(shape, False)
    set_name(lab, name)
    CT.SetColor(lab, Quantity_ColorRGBA(Quantity_Color(rgba[0], rgba[1], rgba[2], Quantity_TypeOfColor.Quantity_TOC_RGB),
                                        rgba[3]), XCAFDoc_ColorType.XCAFDoc_ColorSurf)
    set_name(ST.AddComponent(HWLAB, lab, TopLoc_Location()), name)
set_name(ST.AddComponent(ROOT, HWLAB, TopLoc_Location()), 'hardware_case_and_keepouts')
ST.UpdateAssemblies()

# ---------------- clearances ----------------


def bbox(s):
    b = Bnd_Box()
    BRepBndLib.AddOptimal_s(s, b, False, False)
    a, c = b.CornerMin(), b.CornerMax()
    return (a.X(), a.Y(), a.Z(), c.X(), c.Y(), c.Z())


def bb_gap(a, b):
    dx = max(0, max(a[0], b[0]) - min(a[3], b[3]))
    dy = max(0, max(a[1], b[1]) - min(a[4], b[4]))
    dz = max(0, max(a[2], b[2]) - min(a[5], b[5]))
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def dist(a, b):
    d = BRepExtrema_DistShapeShape(a, b)
    d.Perform()
    return d.Value() if d.IsDone() else float('nan')


BB = [(g, n, s, bbox(s)) for g, n, s in SH]
BBENV = [(r, n, s, zt, bbox(s)) for r, n, s, zt in ENV]


def nearest(shape, candidates, limit=25.0):
    b0 = bbox(shape)
    best = (float('inf'), None)
    cands = sorted(((bb_gap(b0, b), g, n, s) for g, n, s, b in candidates), key=lambda t: t[0])
    for gap, g, n, s in cands:
        if gap > min(best[0], limit):
            break
        d = dist(shape, s)
        if d < best[0]:
            best = (d, '%s %s' % (g, n))
    return best


def is_pcb(n):
    return 'PCB' in n.upper() or n in ('power', 'card') or n.endswith('_PCB')


ROWS = []


def row(check, a, b, value, limit, note=''):
    ROWS.append({'check': check, 'a': a, 'b': b, 'mm': round(value, 2) if value == value else None,
                 'limit': limit, 'flag': ('UNDER 1 mm' if value < 1.0 else '') +
                 (' FAILS ' + limit if (limit and value < float(limit.split()[0])) else ''), 'note': note})


card_all = [(g, n, s, b) for g, n, s, b in BB if g == 'card']
card_names = set(n for g, n, s, b in card_all)
power_parts = [(g, n, s, b) for g, n, s, b in BB if g == 'power' and not is_pcb(n)]
# 1. card (board + everything on it) to each tall power-board part (top more than 5 mm above the board)
for g, n, s, b in power_parts:
    if b[5] - Z_PWR_TOP < 5.0 or n.startswith('J10'):
        continue
    d, who = nearest(s, card_all)
    row('card to tall power part', n, who, d, '', 'part top %.2f' % b[5])
# 2. vent rule: 2 mm above every can's vent, at the datasheet maximum height
for r, n, s, zt, b in BBENV:
    x0, y0, x1, y1 = b[0], b[1], b[3], b[4]
    top = cyl((x0 + x1) / 2, (y0 + y1) / 2, zt, 5.0, 0.01)
    d, who = nearest(top, card_all + [(g, n2, s2, b2) for g, n2, s2, b2 in BB if g == 'hardware'])
    row('vent clearance above can (max height)', '%s %s' % (r, n), who, d, '2.0 mm')
# 3. card vs L1 in plan (the card must never sit over L1)
l1 = [x for x in BB if x[1].startswith('L1 CSCF')][0]
cb = [x for x in BB if x[0] == 'card' and is_pcb(x[1])][0]
plan = max(l1[3][0] - cb[3][3], cb[3][0] - l1[3][3], l1[3][1] - cb[3][4], cb[3][1] - l1[3][4])
row('card outline to L1 body, in plan', 'card board', 'L1', plan, '', 'positive = not overlapping')
d, who = nearest(l1[2], card_all)
row('card to L1, 3D', 'L1 body', who, d, '')
# 4. J9 wire exit and tie head to power-board parts
for g, n, s, b in BB:
    if n.startswith('J9 '):
        d, who = nearest(s, [x for x in BB if x[0] in ('power', 'hardware') and not is_pcb(x[1])] +
                         [(r, nn, ss, bb) for r, nn, ss, zt, bb in BBENV])
        row('J9 wire exit', n, who, d, '')
# 5. lid to the tallest card-top part and the screw heads
tops = sorted(((b[5], n) for g, n, s, b in BB if g in ('card', 'hardware') and b[5] < Z_LID + 0.001 and b[2] > Z_CARD),
              reverse=True)
for z, n in tops[:6]:
    row('lid (33.0) to', n, 'lid underside', Z_LID - z, '')
# 6. standoffs to nearby parts on both boards
others = [x for x in BB if x[0] in ('power', 'card') and not is_pcb(x[1]) and not x[1].startswith('H')]
for h in ('H5', 'H6', 'H7', 'H8'):
    stack = [x for x in BB if x[0] == 'hardware' and x[1].startswith(h + ' ')]
    comp = TopoDS_Compound()
    bld = BRep_Builder()
    bld.MakeCompound(comp)
    for x in stack:
        bld.Add(comp, x[2])
    d, who = nearest(comp, others)
    row('standoff stack to nearest part', h + ' (with H%d on the card)' % (int(h[1]) - 4), who, d, '')
# 7. screwdriver access to the four tab screws
for m in SCREWED:
    acc = [x for x in BB if x[1].startswith(m + ' screwdriver')][0]
    tall = [x for x in BB if x[0] in ('power', 'card') and not is_pcb(x[1]) and x[3][5] > Z_PWR_TOP + 3.0
            and x[1] != m]                       # the FET's own body sits under its screw
    d, who = nearest(acc[2], tall + [x for x in BB if x[0] == 'card' and is_pcb(x[1])] +
                     [(r, nn, ss, bb) for r, nn, ss, zt, bb in BBENV])
    row('screwdriver access (r 4.0 above the head, to the lid)', m, who, d, '', 'touching = 0.00')
    d2, who2 = nearest(acc[2], [x for x in tall if x[0] == 'power'] +
                       [(r, nn, ss, bb) for r, nn, ss, zt, bb in BBENV])
    row('screwdriver access, power-board parts only', m, who2, d2, '', 'the 4.0 mm / 3 mm rule')
    dc = dist(acc[2], cb[2])
    row('screwdriver access blocked by the card?', m, 'card board', dc, '',
        'card over the screw: fit this screw before the card' if dc < 1e-6 else 'card clear of the access cylinder')
# 8. penetrator keep-outs
for g, n, s, b in BB:
    if n.startswith('penetrator'):
        d, who = nearest(s, [x for x in BB if x[0] in ('power', 'card', 'hardware')])
        if d == float('inf'):
            d, who = 25.0, 'nothing within 25 mm (the Arduino, CAN module and LED are not modelled)'
        row('penetrator keep-out', n, who, d, '')

# 9. (2026-09-30) the parts added or moved on the power board's underside since RC2: nearest part, fixing or case
for ref in ('D28', 'D29', 'D30', 'R47'):
    me = [x for x in BB if x[0] == 'power' and x[1] == ref]
    if not me:
        row('added or moved underside part', ref, 'NOT FOUND in the power STEP', float('nan'), '')
        continue
    g, n, s, b = me[0]
    d, who = nearest(s, [x for x in BB if x[0] in ('power', 'hardware', 'case') and not is_pcb(x[1]) and x[1] != ref])
    row('added or moved underside part', ref, who, d, '', 'part bottom %.2f above the floor' % b[2])

json.dump({'rows': ROWS, 'substitutes': SUBSTITUTES,
           'stack': {'pad': PAD_T, 'power_underside': Z_PWR, 'power_top_model': Z_PWR_TOP, 'ff_standoff': [Z_FF0, Z_FF1],
                     'card_underside': Z_CARD, 'card_top_model': Z_CARD_TOP, 'esq_top': ESQ_TOP, 'tsw_bottom': TSW_BOT,
                     'lid': Z_LID}},
          open('work/clearances.json', 'w'), indent=1)
for r in ROWS:
    print('%-52s %-58s %-60s %6s %s %s' % (r['check'][:52], str(r['a'])[:58], str(r['b'])[:60], r['mm'], r['flag'],
                                          r['note']))

# ---------------- write STEP and GLB ----------------
if '--no-write' not in sys.argv:
    w = STEPCAFControl_Writer()
    w.SetColorMode(True)
    w.SetNameMode(True)
    w.Transfer(doc, STEPControl_AsIs)
    w.Write('BOOST_assembly_2026-09-30.step')
    print('STEP written')
    free = Sequence_TDF_Label()
    ST.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        BRepMesh_IncrementalMesh(ST.GetShape_s(free.Value(i)), 0.08, False, 0.5, True)
    gw = RWGltf_CafWriter(TCollection_AsciiString('BOOST_assembly_2026-09-30.glb'), True)
    info = IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString()
    ok = gw.Perform(doc, info, Message_ProgressRange())
    print('GLB written', ok)
