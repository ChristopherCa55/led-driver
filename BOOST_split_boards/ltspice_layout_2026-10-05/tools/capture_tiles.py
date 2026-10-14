"""Readable LTspice captures of a block wider than one capture tile.

    python capture_tiles.py WORK.asc BLOCK OUTDIR [--tile 1400x900]

ltspice_capture.py keeps every RECTANGLE that touches a view, unclipped, and LTspice zooms to fit everything, so a
tile inside a large block frame is drawn at the zoom of the whole frame. This helper (it does NOT change the tool)
copies the schematic and its symbol/model files to a temp folder, deletes only that block's frame RECTANGLE line from
the copy (a drawing, no netlist effect), and runs the unmodified tool with its --region option on each tile.
The frame itself is checked in the tool's normal block capture.
"""
import os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.normpath(os.path.join(HERE, '..', '..', 'ltspice_layout_handoff_2026-10-05', 'tools'))
sys.path.insert(0, TOOL)
from ltspice_capture import frames_of, tiles          # read-only use of the tool's own helpers
from asc_layout_check import Schematic

a = sys.argv[1:]
asc, block, outdir = os.path.abspath(a[0]), a[1], os.path.abspath(a[2])
tw, th = (int(v) for v in (a[a.index('--tile') + 1] if '--tile' in a else '1400x900').split('x'))
sch = Schematic(asc)
fr = frames_of(sch)[block]
tmp = tempfile.mkdtemp(prefix='captiles_')
for f in os.listdir(os.path.dirname(asc)):
    if f.lower().endswith(('.asy', '.lib')):
        shutil.copy2(os.path.join(os.path.dirname(asc), f), tmp)
want = 'RECTANGLE Normal %d %d %d %d' % fr
lines = open(asc, encoding='latin-1').read().split('\n')
n0 = len(lines)
lines = [l for l in lines if not (l.startswith(want) or
                                  l.startswith('RECTANGLE Normal %d %d %d %d' % (fr[2], fr[3], fr[0], fr[1])))]
assert len(lines) == n0 - 1, 'frame rectangle not found exactly once'
copy = os.path.join(tmp, 'BOOST.asc')
open(copy, 'w', encoding='latin-1', newline='\n').write('\n'.join(lines))
os.makedirs(outdir, exist_ok=True)
for k, r in enumerate(tiles(fr, tw, th)):
    name = '%s_tile%d' % (block, k + 1)
    sub = os.path.join(outdir, '_' + name)
    subprocess.run([sys.executable, os.path.join(TOOL, 'ltspice_capture.py'), copy, sub, '--region',
                    '%d,%d,%d,%d' % r, '--name', name], check=True)
    shutil.move(os.path.join(sub, name + '.png'), os.path.join(outdir, name + '.png'))
    print(name, r)
    shutil.rmtree(sub, ignore_errors=True)
shutil.rmtree(tmp, ignore_errors=True)
