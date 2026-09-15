"""Build a work-in-progress split board from the new schematic netlist (KiCad python).

  syncboard.py SRC_BOARD.kicad_pcb NETLIST.net ASSIGN.json BOARD OUT.kicad_pcb
  syncboard.py --check BOARD_FILE.kicad_pcb NETLIST.net ASSIGN.json BOARD

Build mode keeps SRC's outline, stackup and design settings. KiCad 10's Python
cannot remove board items reliably (proxies break after BOARD.Remove), so all
removals are done on the file text before KiCad loads it:
  - every track, arc, via and zone;
  - every footprint no longer on this board, or whose library ID changed.
KiCad then loads the stripped file, adds the missing footprints in a staging
column right of the board (the re-place moves them anyway), sets every value and
pad net from the netlist, and saves. --check verifies a saved file in a fresh
process: every footprint, library ID, value and pad net against the netlist.
"""
import sys, os, re, json


def parse_netlist(path):
    t = open(path, encoding='utf8').read()
    comps = {}
    for m in re.finditer(r'\(comp\s+\(ref\s+"([^"]+)"\)\s*\(value\s+"([^"]*)"\)\s*\(footprint\s+"([^"]*)"\)', t):
        comps[m.group(1)] = (m.group(2), m.group(3))
    padnet = {}
    i = t.find('(nets')
    for blk in re.split(r'\(net\s+\(code', t[i:])[1:]:
        name = re.search(r'\(name\s+"([^"]*)"\)', blk).group(1)
        for r, p in re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s*\(pin\s+"([^"]+)"\)', blk):
            padnet[(r, p)] = name
    return comps, padnet


def top_blocks(txt, heads):
    """Yield (start, end, head) for top-level blocks '\n\t(head ...)'."""
    pat = re.compile(r'\n\t\((%s)[\s)]' % '|'.join(heads))
    pos = 0
    while True:
        m = pat.search(txt, pos)
        if not m:
            return
        a = m.start() + 2
        d, k, ins = 0, a, False
        while True:
            c = txt[k]
            if ins:
                if c == chr(92):
                    k += 1
                elif c == '"':
                    ins = False
            elif c == '"':
                ins = True
            elif c == '(':
                d += 1
            elif c == ')':
                d -= 1
                if d == 0:
                    break
            k += 1
        yield m.start(), k + 1, m.group(1)
        pos = k + 1


if sys.argv[1] == '--check':
    import pcbnew
    BFILE, NET, ASSIGN, BOARD = sys.argv[2:6]
    comps, padnet = parse_netlist(NET)
    assign = json.load(open(ASSIGN))
    want = sorted(r for r in comps if assign.get(r) == BOARD)
    c = pcbnew.LoadBoard(BFILE)
    fails = []
    got = {}
    for f in c.GetFootprints():
        got[f.GetReference()] = f
    for ref in want:
        f = got.get(ref)
        if f is None:
            fails.append('missing %s' % ref)
            continue
        value, fpid = comps[ref]
        if f.GetFPIDAsString() != fpid or f.GetValue() != value:
            fails.append('%s fp/value %s/%s != %s/%s' % (ref, f.GetFPIDAsString(), f.GetValue(), fpid, value))
        nums = set()
        for p in f.Pads():
            nums.add(p.GetNumber())
            if p.GetNumber() == '':
                continue
            if p.GetNetname() != padnet.get((ref, p.GetNumber()), ''):
                fails.append('%s.%s net %r != %r' % (ref, p.GetNumber(), p.GetNetname(), padnet.get((ref, p.GetNumber()), '')))
        missing = {p for (r, p) in padnet if r == ref} - nums
        if missing:
            fails.append('%s has no pad for pins %s' % (ref, sorted(missing)))
    extra = sorted(set(got) - set(want))
    if extra:
        fails.append('extra footprints %s' % extra)
    print('check %s: %d footprints (want %d), %d tracks/vias, %d zones; parity failures %d'
          % (os.path.basename(BFILE), len(got), len(want), len(list(c.GetTracks())), c.GetAreaCount(), len(fails)))
    for x in fails[:40]:
        print('   ' + x)
    sys.exit(0)

SRC, NET, ASSIGN, BOARD, OUT = sys.argv[1:6]
KLIB = r'C:\Program Files\KiCad\10.0\share\kicad\footprints'
PROJ = r'C:\Users\Dominick Junior\Downloads\UCSD Stuff\2025-2026\robotx\led-driver\BOOST-github\BOOST'
comps, padnet = parse_netlist(NET)
assign = json.load(open(ASSIGN))
want = sorted(r for r in comps if assign.get(r) == BOARD)

# ---- text pass: strip routing and footprints to drop or replace
txt = open(SRC, encoding='utf8').read()
cut = []
counts = {}
xs, ys = [], []
kept = set()
for a, b, head in top_blocks(txt, ('segment', 'arc', 'via', 'zone', 'footprint')):
    blk = txt[a:b]
    if head != 'footprint':
        cut.append((a, b))
        counts[head] = counts.get(head, 0) + 1
        continue
    ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
    fpid = re.match(r'\s*\(footprint "([^"]+)"', blk).group(1)
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)', blk)
    if at:
        xs.append(float(at.group(1)))
        ys.append(float(at.group(2)))
    if ref not in want:
        cut.append((a, b))
        print('removed footprint %-5s %s' % (ref, fpid))
    elif comps[ref][1] != fpid:
        cut.append((a, b))
        print('replaced footprint %-5s %s -> %s (goes to staging)' % (ref, fpid, comps[ref][1]))
    else:
        kept.add(ref)
for a, b in sorted(cut, reverse=True):
    txt = txt[:a] + txt[b:]
print('stripped from text: %s' % counts)
stripped = OUT + '.stripped.kicad_pcb'
open(stripped, 'w', encoding='utf8', newline='').write(txt)

# ---- KiCad pass: add missing footprints, set values and nets
import pcbnew
MM, FM = pcbnew.ToMM, pcbnew.FromMM
b = pcbnew.LoadBoard(stripped)
stage_x, stage_y = max(xs) + 30.0, min(ys)


def net(name):
    n = b.FindNet(name)
    if n is None:
        n = pcbnew.NETINFO_ITEM(b, name)
        b.Add(n)
    return n


existing = {}
for f in b.GetFootprints():
    existing[f.GetReference()] = f
for ref in want:
    value, fpid = comps[ref]
    f = existing.get(ref)
    if f is None:
        lib, name = fpid.split(':')
        path = os.path.join(PROJ if lib in ('BOOST', 'CSCF3218-6R8MC') else KLIB, lib + '.pretty')
        f = pcbnew.FootprintLoad(path, name)
        assert f is not None, (ref, fpid)
        f.SetFPID(pcbnew.LIB_ID(lib, name))
        f.SetReference(ref)
        f.SetPosition(pcbnew.VECTOR2I(FM(stage_x), FM(stage_y)))
        stage_y += 12.0
        b.Add(f)
        print('added   %-5s %s (staging)' % (ref, fpid))
    f.SetValue(value)
    for p in f.Pads():
        nm = padnet.get((ref, p.GetNumber()))
        if nm:
            p.SetNet(net(nm))
        else:
            p.SetNetCode(0)
pcbnew.SaveBoard(OUT, b)
os.remove(stripped)
print('saved %s (kept in place %d, added %d)' % (OUT, len(kept), len(want) - len(kept)))
