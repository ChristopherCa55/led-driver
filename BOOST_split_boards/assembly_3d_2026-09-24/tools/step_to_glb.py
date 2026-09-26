"""Assembly STEP -> GLB with the glTF conventions (metres, Y up), keeping names and colours (OCP 8).

usage: python tools/step_to_glb.py [deflection_mm]
Reads BOOST_assembly_2026-09-25.step (written by build_assembly.py), meshes it, and writes
BOOST_assembly_2026-09-25.glb. The case frame's Z (up from the floor) becomes glTF +Y; case +Y (north) becomes -Z.
"""
import sys
from OCP.STEPCAFControl import STEPCAFControl_Reader
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString, TCollection_AsciiString
from OCP.XCAFDoc import XCAFDoc_DocumentTool
from OCP.collections import Sequence_TDF_Label, IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.RWGltf import RWGltf_CafWriter
from OCP.RWMesh import RWMesh_CoordinateSystem
from OCP.Message import Message_ProgressRange

defl = float(sys.argv[1]) if len(sys.argv) > 1 else 0.08
doc = TDocStd_Document(TCollection_ExtendedString('BinXCAF'))
r = STEPCAFControl_Reader()
r.SetColorMode(True)
r.SetNameMode(True)
assert r.ReadFile('BOOST_assembly_2026-09-25.step') == 1
r.Transfer(doc)
st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
free = Sequence_TDF_Label()
st.GetFreeShapes(free)
print('free shapes', free.Length())
for i in range(1, free.Length() + 1):
    BRepMesh_IncrementalMesh(st.GetShape_s(free.Value(i)), defl, False, 0.5, True)
gw = RWGltf_CafWriter(TCollection_AsciiString('BOOST_assembly_2026-09-25.glb'), True)
conv = gw.ChangeCoordinateSystemConverter()
conv.SetInputLengthUnit(0.001)
conv.SetInputCoordinateSystem(RWMesh_CoordinateSystem.RWMesh_CoordinateSystem_Zup)
info = IndexedDataMap_TCollection_AsciiString_TCollection_AsciiString()
print('GLB written', gw.Perform(doc, info, Message_ProgressRange()))
