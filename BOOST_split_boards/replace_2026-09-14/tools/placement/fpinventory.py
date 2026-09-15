"""Physical inventory of one board's parts from the schematic netlist (KiCad python).

  fpinventory.py NETLIST.net ASSIGN.json BOARD OUT.json

For every component assigned to BOARD, loads the footprint the schematic names
(project libraries BOOST / CSCF3218-6R8MC, otherwise KiCad's library) and records
courtyard size, pads (number, offset, size, drill, net) and whether it is SMD or THT.
"""
import sys, os, re, json
import pcbnew

NET, ASSIGN, BOARD, OUT = sys.argv[1:5]
KLIB = r'C:\Program Files\KiCad\10.0\share\kicad\footprints'
PROJ = r'C:\Users\Dominick Junior\Downloads\UCSD Stuff\2025-2026\robotx\led-driver\BOOST-github\BOOST'
MM = pcbnew.ToMM

t = open(NET, encoding='utf8').read()
comps = {}
for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)\s*\(footprint\s+"([^"]*)"\)', t):
    comps[m.group(1)] = (m.group(2), m.group(3))
padnet = {}
i = t.find('(nets')
for blk in re.split(r'\(net\s+\(code', t[i:])[1:]:
    name = re.search(r'\(name\s+"([^"]*)"\)', blk).group(1)
    for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', blk):
        padnet[(r, p)] = name
assign = json.load(open(ASSIGN))

out = {}
cache = {}
for ref in sorted(r for r in comps if assign.get(r) == BOARD):
    value, fpid = comps[ref]
    lib, name = fpid.split(':')
    path = os.path.join(PROJ if lib in ('BOOST', 'CSCF3218-6R8MC') else KLIB, lib + '.pretty')
    key = (path, name)
    if key not in cache:
        cache[key] = pcbnew.FootprintLoad(path, name)
    fp = cache[key]
    assert fp is not None, (ref, fpid)
    fp.BuildCourtyardCaches()
    info = {}
    for side, layer in (('F', pcbnew.F_CrtYd), ('B', pcbnew.B_CrtYd)):
        c = fp.GetCourtyard(layer)
        if c.OutlineCount():
            bb = c.BBox()
            info[side] = [MM(bb.GetLeft()), MM(bb.GetTop()), MM(bb.GetRight()), MM(bb.GetBottom())]
    pads = []
    tht = False
    for p in fp.Pads():
        pos = p.GetPosition()
        sz = p.GetSize(pcbnew.F_Cu) if hasattr(p, 'GetSize') else p.GetSize()
        drill = MM(p.GetDrillSizeX()) if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH) else 0.0
        if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            tht = True
        pads.append(dict(num=p.GetNumber(), x=MM(pos.x), y=MM(pos.y), w=MM(sz.x), h=MM(sz.y), drill=drill,
                         net=padnet.get((ref, p.GetNumber()), '')))
    crt = info.get('F') or info.get('B')
    out[ref] = dict(value=value, fp=fpid, tht=tht, courtyard=crt,
                    cw=(crt[2] - crt[0]) if crt else 0, ch=(crt[3] - crt[1]) if crt else 0, pads=pads)

json.dump(out, open(OUT, 'w'), indent=1)
area = sum(v['cw'] * v['ch'] for v in out.values())
print('%s: %d parts, courtyard area %.0f mm2' % (BOARD, len(out), area))
big = sorted(out.items(), key=lambda kv: -kv[1]['cw'] * kv[1]['ch'])[:30]
for ref, v in big:
    print('   %-5s %-26s %-58s %5.1f x %5.1f  %s  pads %d' % (ref, v['value'][:26], v['fp'][:58], v['cw'], v['ch'], 'THT' if v['tht'] else 'SMD', len(v['pads'])))
fams = {}
for ref, v in out.items():
    fams.setdefault(v['fp'].split(':')[1], []).append(ref)
print('footprint groups:')
for k in sorted(fams, key=lambda k: -len(fams[k])):
    print('   %3d x %-45s %s' % (len(fams[k]), k, ' '.join(sorted(fams[k])[:14]) + (' ...' if len(fams[k]) > 14 else '')))
