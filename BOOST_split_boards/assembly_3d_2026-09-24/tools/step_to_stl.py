"""Assembly STEP -> one binary STL (millimetres, Z up from the case floor, the STEP's own frame), OCP 8.

usage: python tools/step_to_stl.py [deflection_mm]
STL has no names, colours or parts: every solid in BOOST_assembly_2026-09-25.step is meshed into one file,
BOOST_assembly_2026-09-25.stl. The case walls, the lid and the keep-out volumes are left out (the floor stays),
so the file opens on the boards instead of a closed box; BOOST_assembly_2026-09-25_with_case.stl keeps everything.
"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_Label
from OCP.collections import Sequence_TDF_Label
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.TopLoc import TopLoc_Location
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.StlAPI import StlAPI_Writer

defl = float(sys.argv[1]) if len(sys.argv) > 1 else 0.08
doc = TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
r = STEPCAFControl_Reader()
r.SetNameMode(True)
assert r.ReadFile('BOOST_assembly_2026-09-25.step') == 1
r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())


def name(lab):
    a = TDataStd_Name()
    return a.Get().ToExtString() if lab.FindAttribute(TDataStd_Name.GetID_s(), a) else ''


def leaves(lab, loc, out, path):
    """Walk the assembly tree, carrying each instance's placement down to its shapes."""
    if st.IsReference_s(lab):
        ref = TDF_Label()
        st.GetReferredShape_s(lab, ref)
        leaves(ref, loc.Multiplied(st.GetLocation_s(lab)), out, path + [name(lab)])
        return
    if st.IsAssembly_s(lab):
        kids = Sequence_TDF_Label()
        st.GetComponents_s(lab, kids, False)
        for i in range(1, kids.Length() + 1):
            leaves(kids.Value(i), loc, out, path + [name(lab)])
        return
    shp = st.GetShape_s(lab)
    out.append(('/'.join(p for p in path + [name(lab)] if p), shp.Moved(loc)))


free = Sequence_TDF_Label()
st.GetFreeShapes(free)
items = []
for i in range(1, free.Length() + 1):
    leaves(free.Value(i), TopLoc_Location(), items, [])
print('solids/shapes found:', len(items))
drop_words = ('case wall', 'lid', 'keep-out', 'screwdriver access')   # tested on each part's own name
for label, keep in (('BOOST_assembly_2026-09-25.stl',
                     lambda n: not any(w in n.split('/')[-1].lower() for w in drop_words)),
                    ('BOOST_assembly_2026-09-25_with_case.stl', lambda n: True)):
    comp = TopoDS_Compound()
    bb = BRep_Builder()
    bb.MakeCompound(comp)
    kept = [n for n, s in items if keep(n)]
    for n, s in items:
        if keep(n):
            bb.Add(comp, s)
    BRepMesh_IncrementalMesh(comp, defl, False, 0.5, True)
    w = StlAPI_Writer()
    w.ASCIIMode = False
    ok = w.Write(comp, label)
    print(label, 'written' if ok else 'FAILED', '-', len(kept), 'shapes')
    if label.endswith('24.stl'):
        dropped = sorted({n.split('/')[-1] for n, s in items if not keep(n)})
        print('   left out of the boards-only STL:', dropped)
