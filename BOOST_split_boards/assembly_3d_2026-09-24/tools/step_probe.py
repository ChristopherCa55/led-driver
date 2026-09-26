"""List the named parts in a KiCad STEP export with their bounding boxes (OCP). usage: python step_probe.py FILE.step"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label as TDF_LabelSequence
from OCP.TDataStd import TDataStd_Name
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib


def load(path):
    doc = TDocStd_Document(TCollection_ExtendedString('XmlOcaf'))
    r = STEPCAFControl_Reader()
    r.SetColorMode(True)
    r.SetNameMode(True)
    assert r.ReadFile(path) == 1
    r.Transfer(doc)
    return doc


def name_of(label):
    a = TDataStd_Name()
    if label.FindAttribute(TDataStd_Name.GetID_s(), a):
        return a.Get().ToExtString()
    return '?'


def walk(st, label, depth, out, loc=None):
    from OCP.TopLoc import TopLoc_Location
    comps = TDF_LabelSequence()
    st.GetComponents_s(label, comps)
    for i in range(1, comps.Length() + 1):
        c = comps.Value(i)
        ref = st.GetReferredShape_s  # noqa
        from OCP.TDF import TDF_Label
        tgt = TDF_Label()
        st.GetReferredShape_s(c, tgt)
        shape = st.GetShape_s(c)
        out.append((depth, name_of(c), name_of(tgt), shape))
        if st.IsAssembly_s(tgt) and depth < 1:
            walk(st, tgt, depth + 1, out)


if __name__ == '__main__':
    doc = load(sys.argv[1])
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    free = TDF_LabelSequence()
    st.GetFreeShapes(free)
    print('free shapes', free.Length())
    for i in range(1, free.Length() + 1):
        lab = free.Value(i)
        print('top:', name_of(lab), 'assembly' if st.IsAssembly_s(lab) else '')
        out = []
        walk(st, lab, 0, out)
        for d, n, tn, s in out[:400]:
            bb = Bnd_Box()
            BRepBndLib.Add_s(s, bb)
            if bb.IsVoid():
                print('  ' * d, n, tn, 'void')
                continue
            a, b = bb.CornerMin(), bb.CornerMax(); x0, y0, z0, x1, y1, z1 = a.X(), a.Y(), a.Z(), b.X(), b.Y(), b.Z()
            print('  ' * d, '%-22s %-40s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (n[:22], tn[:40], x0, x1, y0, y1, z0, z1))
        print('components listed:', len(out))
