"""3D PDF of the assembly (2026-09-25). KiCad exports 3D PDFs only from a board, so this writes a throwaway board,
work/pdf3d/BOOST_assembly_3dpdf.kicad_pcb, whose one footprint carries the assembly STEP as its 3D model, then runs
kicad-cli pcb export 3dpdf on it. No real board file is touched.

usage: "<KiCad python>" tools/make_3dpdf.py
"""
import os, subprocess
import pcbnew

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STEP = os.path.join(HERE, 'work', 'pdf3d', 'BOOST_assembly_2026-09-25_flat.step').replace(os.sep, '/')
PCB = os.path.join(HERE, 'work', 'pdf3d', 'BOOST_assembly_3dpdf.kicad_pcb')
OUT = os.path.join(HERE, 'BOOST_assembly_2026-09-25_3D.pdf')
b = pcbnew.BOARD()
fp = pcbnew.FOOTPRINT(b)
fp.SetReference('ASSY')
fp.SetFPID(pcbnew.LIB_ID('BOOST', 'ASSEMBLY_MODEL'))
fp.SetAttributes(pcbnew.FP_SMD)
fp.SetValue('BOOST assembly 2026-09-25')
m = pcbnew.FP_3DMODEL()
m.m_Filename = STEP
m.m_Show = True
fp.Models().push_back(m)
b.Add(fp)
# a small outline so the file is a valid board; the board body is left out of the PDF
for (x0, y0), (x1, y1) in (((0, 0), (1, 0)), ((1, 0), (1, 1)), ((1, 1), (0, 1)), ((0, 1), (0, 0))):
    s = pcbnew.PCB_SHAPE(b)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pcbnew.VECTOR2I_MM(x0, y0)); s.SetEnd(pcbnew.VECTOR2I_MM(x1, y1))
    s.SetLayer(pcbnew.Edge_Cuts)
    b.Add(s)
pcbnew.SaveBoard(PCB, b)
cli = os.path.join(os.path.dirname(os.path.abspath(pcbnew.__file__)), '..', '..', 'bin', 'kicad-cli.exe')
if not os.path.exists(cli):
    cli = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
r = subprocess.run([cli, 'pcb', 'export', '3dpdf', '-f', '-o', OUT, PCB], capture_output=True, text=True)
print(r.stdout[-2000:], r.stderr[-2000:])
print('exists', os.path.exists(OUT), os.path.getsize(OUT) if os.path.exists(OUT) else 0)
