"""Decide which IC each supply bypass capacitor serves, from the real PCB pad positions.

    "C:/Program Files/KiCad/10.0/bin/python.exe" bypass_match.py [KICAD_DIR] [--out ../bypass_map.json]

KICAD_DIR defaults to led-driver/BOOST_stuff/KiCad. The two boards are copied to a temp folder first (pcbnew.LoadBoard
writes a .kicad_prl beside the board it loads), so nothing in KICAD_DIR is touched.

Method, per board and per rail (5V, analog_5V, 12V):
  1. owners = every U-footprint with a pad on that rail; distance(cap, IC) = shortest distance from the cap's rail pad
     to any of the IC's rail pads.
  2. one-to-one minimum-cost matching (exhaustive Hungarian) gives each IC at most one cap, so a cap is not handed to
     an IC that already has a closer one while a neighbour gets none (the plain nearest-IC rule gave U24 two caps and
     U7 none).
  3. caps left over after every IC has one go to their nearest IC.
  4. a cap is AMBIGUOUS when its owner is more than 6 mm away, or another IC is within 1.25x of the owner's distance.
     Ambiguous owners are for the user to confirm; until then the checker treats them as provisional.
Regulator bulk caps are fixed by design (C30 -> U16, C7 C39 -> U17, C55 C56 -> U1) and not matched.
"""
import json, math, os, shutil, sys, tempfile
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = next((a for a in sys.argv[1:] if not a.startswith('--') and (sys.argv.index(a) == 0 or
             sys.argv[sys.argv.index(a) - 1] != '--out')), None) or os.path.normpath(
    os.path.join(HERE, '..', '..', '..', 'BOOST_stuff', 'KiCad'))
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(HERE, '..', 'bypass_map.json')
RAILS = ('5V', 'analog_5V', '12V')
FIXED = {'C30': 'U16', 'C7': 'U17', 'C39': 'U17', 'C55': 'U1', 'C56': 'U1'}
# U-parts whose supply pins LTspice does not model (ideal gates; U18 is powered by the net name 5V): their caps are
# drawn as one labeled group inside the CONTROL block instead of at a pin
HIDDEN = {'U101', 'U102', 'U103', 'U104', 'U105', 'U18'}


def hungarian(cost):
    """Min-cost assignment for an n x m matrix (n <= m). Returns col index per row."""
    n, m = len(cost), len(cost[0])
    INF = float('inf')
    u, v, p, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, used = [INF] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], INF, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break
    ans = [None] * n
    for j in range(1, m + 1):
        if p[j]:
            ans[p[j] - 1] = j - 1
    return ans


def pads_by_rail(path):
    tmp = tempfile.mkdtemp(prefix='bypass_')
    p = os.path.join(tmp, os.path.basename(path))
    shutil.copy2(path, p)
    b = pcbnew.LoadBoard(p)
    out = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            net = pad.GetNetname()
            if net in RAILS:
                pos = pad.GetPosition()
                out.setdefault(net, {}).setdefault(ref, []).append((pcbnew.ToMM(pos.x), pcbnew.ToMM(pos.y)))
    shutil.rmtree(tmp, ignore_errors=True)
    return out


def main():
    result = {}
    for board in ('BOOST_power_RC2.kicad_pcb', 'BOOST_control_RC2.kicad_pcb'):
        rails = pads_by_rail(os.path.join(KDIR, board))
        for rail, parts in rails.items():
            caps = sorted([r for r in parts if r.startswith('C') and r not in FIXED], key=lambda s: int(s[1:]))
            ics = sorted([r for r in parts if r.startswith('U')])
            # a cap belongs here only if its other pad is GND; checked by the caller's list in blocks.json
            dist = {c: {u: min(math.dist(a, b) for a in parts[c] for b in parts[u]) for u in ics} for c in caps}
            if not caps or not ics:
                continue
            # step 2: one cap per IC (rows = ICs when fewer ICs than caps)
            if len(ics) <= len(caps):
                cost = [[dist[c][u] for c in caps] for u in ics]
                asg = hungarian(cost)
                owner = {caps[asg[i]]: ics[i] for i in range(len(ics)) if asg[i] is not None}
            else:
                cost = [[dist[c][u] for u in ics] for c in caps]
                asg = hungarian(cost)
                owner = {caps[i]: ics[asg[i]] for i in range(len(caps))}
            for c in caps:
                if c not in owner:
                    owner[c] = min(ics, key=lambda u: dist[c][u])
            for c in caps:
                o = owner[c]
                ranked = sorted(ics, key=lambda u: dist[c][u])
                second = next((u for u in ranked if u != o), None)
                d_o, d_s = dist[c][o], dist[c][second] if second else None
                amb = d_o > 6.0 or (d_s is not None and d_s < 1.25 * d_o)
                result[c] = {'rail': rail, 'board': board.split('_')[1], 'owner': o, 'dist_mm': round(d_o, 2),
                             'next': second, 'next_mm': round(d_s, 2) if d_s is not None else None,
                             'nearest': ranked[0], 'ambiguous': amb,
                             'draw': 'LPWR group in CONTROL' if o in HIDDEN else 'at %s supply pin' % o}
    for c, o in FIXED.items():
        result[c] = {'rail': None, 'owner': o, 'fixed_by_design': True, 'ambiguous': False,
                     'draw': 'at %s output (regulator bulk cap)' % o}
    out = dict(sorted(result.items(), key=lambda kv: int(kv[0][1:])))
    json.dump({'_note': 'Generated by bypass_match.py from BOOST_stuff PCB pad positions. "ambiguous": true owners '
                        'must be confirmed by the user (set "confirmed_by_user": true after the check-in).',
               'caps': out}, open(OUT, 'w'), indent=1)
    amb = [c for c, v in out.items() if v.get('ambiguous')]
    for c, v in out.items():
        print('%-5s %-9s -> %-5s %5s mm  (next %s %s mm)%s' % (c, v.get('rail') or '', v['owner'],
              v.get('dist_mm', ''), v.get('next', ''), v.get('next_mm', ''), '  AMBIGUOUS' if v.get('ambiguous') else ''))
    print('%d caps, %d ambiguous: %s' % (len(out), len(amb), ' '.join(amb)))
    print('wrote', os.path.abspath(OUT))


if __name__ == '__main__':
    main()
