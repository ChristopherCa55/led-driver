"""Flatten the assembly STEP into one level (every leaf shape with its placement baked in, colour kept) for
KiCad's 3D-model loader, which drops the nested assembly (used only for the 3D PDF). OCP 8.

usage: python tools/flatten_step.py   ->  work/pdf3d/BOOST_assembly_2026-09-25_flat.step
"""
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen, XCAFDoc_ColorSurf
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.collections import Sequence_TDF_Label
from OCP.TopLoc import TopLoc_Location
from OCP.Quantity import Quantity_Color

src = TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
r = STEPCAFControl_Reader(); r.SetColorMode(True); r.SetNameMode(True)
assert r.ReadFile('BOOST_assembly_2026-09-25.step') == 1
r.Transfer(src)
st = XCAFDoc_DocumentTool.ShapeTool_s(src.Main()); ct = XCAFDoc_DocumentTool.ColorTool_s(src.Main())
dst = TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
dst_st = XCAFDoc_DocumentTool.ShapeTool_s(dst.Main()); dst_ct = XCAFDoc_DocumentTool.ColorTool_s(dst.Main())


def name(lab):
    a = TDataStd_Name()
    return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else ''


def colour(labs):
    c = Quantity_Color()
    for lab in labs:
        for kind in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
            if ct.GetColor_s(lab, kind, c):
                return c
    return None


n = 0
def walk(lab, loc, chain):
    global n
    if st.IsReference_s(lab):
        ref = TDF_Label(); st.GetReferredShape_s(lab, ref)
        walk(ref, loc.Multiplied(st.GetLocation_s(lab)), chain + [lab]); return
    if st.IsAssembly_s(lab):
        kids = Sequence_TDF_Label(); st.GetComponents_s(lab, kids, False)
        for i in range(1, kids.Length() + 1):
            walk(kids.Value(i), loc, chain + [lab])
        return
    new = dst_st.AddShape(st.GetShape_s(lab).Moved(loc), False)
    TDataStd_Name.Set_s(new, TCollection_ExtendedString(name(lab) or 'part'))
    c = colour([lab] + chain[::-1])
    if c is not None:
        dst_ct.SetColor(new, c, XCAFDoc_ColorSurf)
    n += 1


free = Sequence_TDF_Label(); st.GetFreeShapes(free)
for i in range(1, free.Length() + 1):
    walk(free.Value(i), TopLoc_Location(), [])
w = STEPCAFControl_Writer(); w.SetColorMode(True); w.SetNameMode(True)
w.Transfer(dst, STEPControl_AsIs)
print(n, 'shapes; written', w.Write('work/pdf3d/BOOST_assembly_2026-09-25_flat.step'))
