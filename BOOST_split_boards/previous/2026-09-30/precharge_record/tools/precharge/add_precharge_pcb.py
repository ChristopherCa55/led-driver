"""Place and route the pre-charge diodes D28-D30 on BOOST_power_RC2.kicad_pcb, in place (KiCad 10 Python).

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" add_precharge_pcb.py PATH\\TO\\BOOST_power_RC2.kicad_pcb

What it does (every coordinate is in mm, board coordinates, as KiCad shows them):
  1. Refuses to run if a KiCad lock file is next to the board, if D28/D29/D30 already exist, or if any item it expects
     to find (the 4 segments, the logo, R47, the Vin/Vout nets) is missing.
  2. Text edit, before KiCad loads the file (KiCad 10's BOARD.Remove is unreliable from Python):
       - deletes the 4 B.Cu segments of net Net-(D13--) that ran from R47's old pad 2 down the right edge;
       - deletes the B.Cu logo footprint at (48.12, 88.66) (uuid 1317deff-...) - the user allowed removing logos.
  3. Loads the stripped copy with the project rules next to it (.kicad_pro/.kicad_dru copied alongside; without them
     KiCad fills the zones with default clearances), then
       - adds D28, D29, D30: Diode_SMD:D_SOD-123F, value S2MW, bottom side, pad 1 = cathode, pad 2 = anode, linked
         to the schematic symbols by path so a later "Update PCB from Schematic" keeps them;
       - puts their reference labels on B.Fab like every other small part (D30's at its body centre, because the
         library spot is past the board edge);
       - moves R47 to (102.85, 99.50), bottom side, rotated so pad 1 (GATE_M4) is on top;
       - adds the tracks and vias listed in ADD below;
       - rebuilds connectivity, refills every zone, saves over the input board.
  4. SaveBoard rewrites the project file and drops the netclasses: the original .kicad_pro bytes are written back.
"""
import sys, os, re, math, shutil

BOARD = os.path.abspath(sys.argv[1])
STEM = BOARD[:-len('.kicad_pcb')]
DIR, NAME = os.path.split(BOARD)
LIB = r'C:\Program Files\KiCad\10.0\share\kicad\footprints\Diode_SMD.pretty'

for f in os.listdir(DIR):
    if f.startswith('~') and f.endswith('.lck'):
        sys.exit('STOP: lock file %s - KiCad has the project open. Ask the user to close KiCad.' % f)

# ---------------------------------------------------------------- what gets deleted
DELETE = [  # (net, start, end) - B.Cu, width 0.2
    ('Net-(D13--)', (102.65, 89.35), (102.65, 89.55)),
    ('Net-(D13--)', (102.65, 89.55), (102.75, 89.65)),
    ('Net-(D13--)', (102.75, 89.65), (102.75, 98.55)),
    ('Net-(D13--)', (102.75, 98.55), (100.45, 100.85)),
]
LOGO_UUID = '1317deff-735a-4193-978a-f3484107ac56'       # B.Cu logo at (48.122601, 88.661485), rotated 90

# ---------------------------------------------------------------- what gets added
SCH_ROOT_FILE = 'BOOST.kicad_sch'
DIODES = [  # ref, cathode net, cathode pad 1 (x, y), anode pad 2 (x, y), schematic symbol uuid
    ('D28', 'Vout_1', (44.60, 91.50), (47.40, 91.50), 'c399746a-53eb-4c48-a735-e8265130f622'),
    ('D29', 'Vout_2', (50.60, 87.25), (53.40, 87.25), 'ad541492-5975-4a76-baf7-2fb8e76d43fb'),
    ('D30', 'Vout_3', (102.85, 91.00), (102.85, 88.20), '68d2cdfe-4062-478b-951b-a3c5578ea96a'),
]
R47_PADS = {'1': (102.85, 98.675), '2': (102.85, 100.325)}    # pad 1 GATE_M4, pad 2 Net-(D13--); centre (102.85, 99.50)
# Reference labels go on B.Fab like every other small part (not silkscreen). D30's library label spot lies past the
# board edge, so its labels go to the body centre.
REF_AT_CENTRE = {'D30'}
ADD = [  # ('T', net, layer, width, [points...])  or  ('V', net, x, y, diameter, drill)
    # D28 (Vout_1): anode onto the existing B.Cu Vin diagonal (its centre line is x + y = 139.00)
    ('T', 'Vin', 'B', 1.0, [(47.40, 91.50), (47.70, 91.30)]),
    # D28 cathode -> one new via into the In3.Cu Vout_1 strip (x 43.0-47.2)
    ('T', 'Vout_1', 'B', 1.0, [(44.60, 91.50), (45.90, 91.00)]),
    ('V', 'Vout_1', 45.90, 91.00, 0.8, 0.4),
    # D29 (Vout_2): anode -> existing Vin via at (56.45, 87.65); cathode -> existing Vout_2 via at (49.90, 84.00)
    ('T', 'Vin', 'B', 1.0, [(53.40, 87.25), (56.45, 87.65)]),
    ('T', 'Vout_2', 'B', 1.0, [(50.60, 87.25), (49.90, 84.00)]),
    # D30 (Vout_3): anode -> existing Vin via at (102.36, 87.00) in the "Vin J1 bottom" pour
    ('T', 'Vin', 'B', 1.0, [(102.85, 88.20), (102.36, 87.00)]),
    # D30 cathode -> two new vias into the Vout_3 pours on In2/In3/In5
    ('T', 'Vout_3', 'B', 1.0, [(102.85, 91.00), (100.60, 91.60), (100.60, 92.50)]),
    ('V', 'Vout_3', 100.60, 91.60, 0.8, 0.4),
    ('V', 'Vout_3', 100.60, 92.50, 0.8, 0.4),
    # GATE_M4: close the gap left by R47's old pad 1 (keeps R73 pad 2 / via (101.65, 88.05) joined to M4's gate pin)
    ('T', 'GATE_M4', 'B', 0.3, [(101.05, 88.65), (100.55, 88.65)]),
    # GATE_M4: R47's new pad 1 -> up the right edge on B.Cu -> via -> F.Cu -> R73 pad 2 at (102.51, 89.00)
    ('T', 'GATE_M4', 'B', 0.3, [(102.85, 98.675), (103.10, 98.425), (103.10, 92.90)]),
    ('V', 'GATE_M4', 103.10, 92.90, 0.6, 0.3),
    ('T', 'GATE_M4', 'F', 0.3, [(103.10, 92.90), (103.10, 89.60), (102.51, 89.00)]),
    # Net-(D13--): R47's new pad 2 -> the kept end of the old track at (100.45, 100.85)
    ('T', 'Net-(D13--)', 'B', 0.2, [(102.85, 100.325), (100.45, 100.85)]),
]

# ---------------------------------------------------------------- 1-2. text pass
raw = open(BOARD, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in raw else '\n'
txt = raw.replace('\r\n', '\n')
for ref, *_ in DIODES:
    if '(property "Reference" "%s"' % ref in txt:
        sys.exit('STOP: %s is already on the board - this script has run before. Nothing changed.' % ref)
cuts = []
for m in re.finditer(r'\t\(segment\n(?:\t\t.*\n)*?\t\)\n', txt):
    b = m.group(0)
    s = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', b); e = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', b)
    n = re.search(r'\(net "([^"]*)"\)', b)
    if not (s and e and n):
        continue
    S = (float(s.group(1)), float(s.group(2))); E = (float(e.group(1)), float(e.group(2)))
    for net, a, c in DELETE:
        same = lambda p, q: abs(p[0] - q[0]) < 1e-3 and abs(p[1] - q[1]) < 1e-3
        if n.group(1) == net and ((same(S, a) and same(E, c)) or (same(S, c) and same(E, a))):
            cuts.append(m.span())
if len(cuts) != len(DELETE):
    sys.exit('STOP: found %d of the %d Net-(D13--) segments to delete - the board is not the expected one.' % (len(cuts), len(DELETE)))
i = txt.find('(uuid "%s")' % LOGO_UUID)
if i < 0:
    sys.exit('STOP: logo %s not found.' % LOGO_UUID)
a = txt.rindex('\n\t(footprint "LOGO"', 0, i) + 1
d, k, ins = 0, a + 1, False
while True:
    ch = txt[k]
    if ins:
        if ch == '\\':
            k += 1
        elif ch == '"':
            ins = False
    elif ch == '"':
        ins = True
    elif ch == '(':
        d += 1
    elif ch == ')':
        d -= 1
        if d == 0:
            break
    k += 1
if '(at 48.122601 88.661485 90)' not in txt[a:k] or '(layer "B.Cu")' not in txt[a:k]:
    sys.exit('STOP: the logo block is not the expected B.Cu logo at (48.12, 88.66).')
cuts.append((a, k + 2))
for s0, s1 in sorted(cuts, reverse=True):
    txt = txt[:s0] + txt[s1:]
tmp = STEM + '_precharge_tmp.kicad_pcb'
open(tmp, 'w', encoding='utf-8', newline='').write(txt)
for ext in ('.kicad_pro', '.kicad_dru'):
    shutil.copyfile(STEM + ext, tmp[:-len('.kicad_pcb')] + ext)
pro_bytes = open(STEM + '.kicad_pro', 'rb').read()
print('text pass: deleted %d segments and the logo' % len(DELETE))

# ---------------------------------------------------------------- 3. KiCad pass
import pcbnew
brd = pcbnew.LoadBoard(tmp)
ds = brd.GetDesignSettings()
if abs(pcbnew.ToMM(ds.m_CopperEdgeClearance) - 0.3) > 1e-6:
    sys.exit('STOP: project rules did not load (copper-edge clearance %.3f, expected 0.300).' % pcbnew.ToMM(ds.m_CopperEdgeClearance))
MM = pcbnew.FromMM
P = lambda x, y: pcbnew.VECTOR2I(MM(x), MM(y))
at = lambda p: (pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))


def net(n):
    ni = brd.FindNet(n)
    if ni is None:
        sys.exit('STOP: net %s not found.' % n)
    return ni


def orient(fp, targets):
    """Rotate fp (already on its side) so each pad number lands on its target; returns the rotation."""
    best = None
    for rot in (0, 90, 180, 270):
        fp.SetOrientationDegrees(rot)
        err = sum(math.hypot(at(p.GetPosition())[0] - targets[p.GetNumber()][0],
                             at(p.GetPosition())[1] - targets[p.GetNumber()][1]) for p in fp.Pads())
        if best is None or err < best[0]:
            best = (err, rot)
    fp.SetOrientationDegrees(best[1])
    if best[0] > 0.01:
        sys.exit('STOP: could not orient %s' % fp.GetReference())
    return best[1]


io = pcbnew.PCB_IO_KICAD_SEXPR()
for ref, kn, k, an, su in DIODES:
    fp = io.FootprintLoad(LIB, 'D_SOD-123F')
    fp.SetFPID(pcbnew.LIB_ID('Diode_SMD', 'D_SOD-123F'))
    brd.Add(fp)
    fp.SetReference(ref)
    fp.SetValue('S2MW')
    fp.SetPath(pcbnew.KIID_PATH('/' + su))
    fp.SetSheetname('/')
    fp.SetSheetfile(SCH_ROOT_FILE)
    fp.SetPosition(P((k[0] + an[0]) / 2, (k[1] + an[1]) / 2))
    fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)        # to the bottom side
    rot = orient(fp, {'1': k, '2': an})
    for p in fp.Pads():
        p.SetNet(net(kn) if p.GetNumber() == '1' else net('Vin'))
    print('%s: bottom, rotation %d, centre (%.2f, %.2f), pad 1 (K) %s = %s, pad 2 (A) %s = Vin'
          % (ref, rot, (k[0] + an[0]) / 2, (k[1] + an[1]) / 2, k, kn, an))
for ref, *_ in DIODES:
    fp = brd.FindFootprintByReference(ref)
    fab = [g for g in fp.GraphicalItems() if g.GetClass() == 'PCB_TEXT' and g.GetText() == '${REFERENCE}']
    if len(fab) != 1:
        sys.exit('STOP: %s has no single ${REFERENCE} fab text' % ref)
    if ref in REF_AT_CENTRE:
        fab[0].SetPosition(fp.GetPosition())
    fp.Reference().SetLayer(pcbnew.B_Fab)
    fp.Reference().SetPosition(fab[0].GetPosition())

r47 = brd.FindFootprintByReference('R47')
if r47 is None or not r47.IsFlipped():
    sys.exit('STOP: R47 missing or not on the bottom side.')
print('R47 was at (%.3f, %.3f) rotation %.0f' % (at(r47.GetPosition()) + (r47.GetOrientationDegrees(),)))
r47.SetPosition(P(102.85, 99.50))
rot = orient(r47, R47_PADS)
print('R47 now at (102.85, 99.50) rotation %d, pad 1 %s, pad 2 %s' % (rot, R47_PADS['1'], R47_PADS['2']))

LAYER = {'F': pcbnew.F_Cu, 'B': pcbnew.B_Cu}
for item in ADD:
    if item[0] == 'T':
        _, n, lay, w, pts = item
        for p0, p1 in zip(pts, pts[1:]):
            t = pcbnew.PCB_TRACK(brd)
            t.SetStart(P(*p0)); t.SetEnd(P(*p1)); t.SetWidth(MM(w)); t.SetLayer(LAYER[lay]); t.SetNet(net(n))
            brd.Add(t)
    else:
        _, n, x, y, dia, drill = item
        v = pcbnew.PCB_VIA(brd)
        v.SetPosition(P(x, y)); v.SetWidth(MM(dia)); v.SetDrill(MM(drill)); v.SetNet(net(n))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        brd.Add(v)
print('added %d track runs and %d vias' % (sum(1 for i in ADD if i[0] == 'T'), sum(1 for i in ADD if i[0] == 'V')))

brd.BuildConnectivity()                       # via/pad layer flashing must be known before the fill
pcbnew.ZONE_FILLER(brd).Fill(brd.Zones())
pcbnew.SaveBoard(BOARD, brd)
open(STEM + '.kicad_pro', 'wb').write(pro_bytes)          # SaveBoard dropped the netclasses: restore the project file
for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '.kicad_prl'):
    f = tmp[:-len('.kicad_pcb')] + ext
    if os.path.exists(f):
        os.remove(f)
print('saved %s (zones refilled, project file restored)' % BOARD)
