"""Find legal B-side spots for bypass capacitors next to given IC pins (system Python).

usage: python place_bypass.py FOOTPRINTS.json COPPER.json SPEC.json OUT_MOVES.json [SHEET_CURRENT.npz]

FOOTPRINTS.json from export_courtyards.py (movers already on the side they will stay on), COPPER.json from
export_copper.py (vias, holes, board edge) of the same unrouted board. SPEC.json is an ordered list:
  [{"ref": "C51", "targets": {"NET": [["U15", "11"], ...], ...}, "radius": 7, "region": [x0, y0, x1, y1]}, ...]
("radius": search window round the pins, mm, default 7; "region": optional box the footprint origin must lie in)
Each capacitor pad on NET must sit next to one of that net's target pins; the score is the larger of the two
pad-centre to pin-centre distances (the way the check-in measures). Candidates: 0.1 mm steps within 7 mm of the
pins, rotations in 90 degree steps. Legal means: courtyard clear of every other courtyard on the same side and of
the board edge (0.25 mm inset), pads and courtyard at least 3.75 mm from every tab screw and standoff centre, and
pad copper at least 0.25 mm from any via or hole of another net. Each placed capacitor becomes an obstacle for the
next. With SHEET_CURRENT.npz, pads over copper carrying power current (>0.25 A/mm on B.Cu) are penalised.
"""
import json, math, sys
import numpy as np
from scipy import ndimage, signal
from PIL import Image, ImageDraw

G = 0.05                      # raster step, mm
X0, Y0, NX, NY = 29.0, 29.0, int(76 / G), int(88 / G)
fps = {f['ref']: f for f in json.load(open(sys.argv[1]))}
cop = json.load(open(sys.argv[2]))
spec = json.load(open(sys.argv[3]))
jmap = None
if len(sys.argv) > 5:
    d = np.load(sys.argv[5])
    jmap = d['B_Cu'] if 'B_Cu' in d.files else None          # 0.1 mm grid from X0 = Y0 = 29


def raster(polys, shape=(NY, NX), x0=X0, y0=Y0):
    img = Image.new('1', (shape[1], shape[0]), 0)
    dr = ImageDraw.Draw(img)
    for pl in polys:
        if len(pl) >= 3:
            dr.polygon([((x - x0) / G, (y - y0) / G) for x, y in pl], fill=1, outline=1)
    return np.array(img, dtype=bool)


movers = {s['ref'] for s in spec}
side = 'B'
occ = raster([c for f in fps.values() if f['side'] == side and f['ref'] not in movers for c in f['courtyard']])
edge = cop['edge']
# board outline polygon from the edge segments
segs = [((e[0], e[1]), (e[2], e[3])) for e in edge]
pts = [segs[0][0], segs[0][1]]
used = {0}
while len(used) < len(segs):
    for k, (a, b) in enumerate(segs):
        if k in used:
            continue
        if math.dist(a, pts[-1]) < 1e-3:
            pts.append(b); used.add(k); break
        if math.dist(b, pts[-1]) < 1e-3:
            pts.append(a); used.add(k); break
    else:
        break
inside = ndimage.binary_erosion(raster([pts]), iterations=int(round(0.25 / G)))
occ |= ~inside
screws = [(p['x'], p['y']) for f in fps.values() for p in f['pads'] if p['net'] == '' and p['drill'] >= 2.5]
yy, xx = np.mgrid[0:NY, 0:NX]
cx, cy = X0 + (xx + 0.5) * G, Y0 + (yy + 0.5) * G
screw_zone = np.zeros((NY, NX), bool)
for sx, sy in screws:
    screw_zone |= (cx - sx) ** 2 + (cy - sy) ** 2 < 3.75 ** 2
occ_all = occ | screw_zone
holes = [(v['x'], v['y'], v['dia'] / 2, v['net']) for v in cop['vias']]
holes += [(b['x'], b['y'], b['drill'] / 2 + 0.3, b['net']) for b in cop['barrels'] if b['kind'] == 'tht']


def foreign_mask(net):
    m = np.zeros((NY, NX), bool)
    for x, y, r, n in holes:
        if n != net:
            rr = r + 0.25
            i0, i1 = int((x - rr - X0) / G) - 1, int((x + rr - X0) / G) + 2
            j0, j1 = int((y - rr - Y0) / G) - 1, int((y + rr - Y0) / G) + 2
            sub = (cx[j0:j1, i0:i1] - x) ** 2 + (cy[j0:j1, i0:i1] - y) ** 2 < rr * rr
            m[j0:j1, i0:i1] |= sub
    return m


def pin_xy(ref, num):
    for p in fps[ref]['pads']:
        if p['num'] == num:
            return p['x'], p['y']
    raise KeyError((ref, num))


def rot_pts(pl, fx, fy, k):
    """Rotate board points about the footprint origin by k * 90 degrees in KiCad's positive (screen CCW) sense."""
    out = []
    for x, y in pl:
        dx, dy = x - fx, y - fy
        for _ in range(k):
            dx, dy = dy, -dx
        out.append((dx, dy))
    return out


moves, report = {}, []
for task in spec:
    f = fps[task['ref']]
    fx, fy = f['x'], f['y']
    targets = {net: [pin_xy(r, n) for r, n in pins] for net, pins in task['targets'].items()}
    allpins = [p for v in targets.values() for p in v]
    mx, my = sum(p[0] for p in allpins) / len(allpins), sum(p[1] for p in allpins) / len(allpins)
    best = None
    for k in range(4):
        cy_ = [rot_pts(c, fx, fy, k) for c in f['courtyard']]
        pads = [(p['net'], rot_pts(pl, fx, fy, k), rot_pts([(p['x'], p['y'])], fx, fy, k)[0]) for p in f['pads'] for pl in p['polys']]
        allx = [x for c in cy_ for x, _ in c]
        ally = [y for c in cy_ for _, y in c]
        px0, py0 = min(allx) - 2 * G, min(ally) - 2 * G
        pw, ph = int((max(allx) - px0) / G) + 3, int((max(ally) - py0) / G) + 3
        cmask = raster([[(x - px0 + X0, y - py0 + Y0) for x, y in c] for c in cy_], (ph, pw))
        R = float(task.get('radius', 7.0))
        wi0, wi1 = int((mx - R - X0) / G), int((mx + R - X0) / G)
        wj0, wj1 = int((my - R - Y0) / G), int((my + R - Y0) / G)
        win = occ_all[wj0:wj1 + ph, wi0:wi1 + pw].astype(np.float32)
        ov = signal.fftconvolve(win, cmask[::-1, ::-1].astype(np.float32), mode='valid')
        legal = ov < 0.5
        pad_ok = np.ones_like(legal)
        for net, pl, _ in pads:
            pm = raster([[(x - px0 + X0, y - py0 + Y0) for x, y in pl]], (ph, pw)).astype(np.float32)
            fm = foreign_mask(net)[wj0:wj1 + ph, wi0:wi1 + pw].astype(np.float32)
            sm = screw_zone[wj0:wj1 + ph, wi0:wi1 + pw].astype(np.float32)
            pad_ok &= signal.fftconvolve(fm, pm[::-1, ::-1], mode='valid') < 0.5
            pad_ok &= signal.fftconvolve(sm, pm[::-1, ::-1], mode='valid') < 0.5
        legal &= pad_ok
        js, is_ = np.nonzero(legal)
        step = int(round(0.1 / G))
        for j, i in zip(js, is_):
            if j % step or i % step:
                continue
            # footprint origin for this offset: patch top-left at board cell (wi0 + i, wj0 + j)
            ox = X0 + (wi0 + i) * G - px0
            oy = Y0 + (wj0 + j) * G - py0
            if 'region' in task:
                rx0, ry0, rx1, ry1 = task['region']
                if not (rx0 <= ox <= rx1 and ry0 <= oy <= ry1):
                    continue
            ds = []
            pen = 0.0
            for net, pl, (cx0, cy0) in pads:
                px, py = ox + cx0, oy + cy0
                if net in targets:
                    ds.append(min(math.hypot(px - tx, py - ty) for tx, ty in targets[net]))
                if jmap is not None:
                    gi, gj = int((px - 29.0) / 0.1), int((py - 29.0) / 0.1)
                    if 0 <= gj < jmap.shape[0] and 0 <= gi < jmap.shape[1]:
                        pen += max(0.0, float(jmap[gj, gi]) - 0.25)
            if len(ds) < len(targets):
                continue
            score = max(ds) + 0.05 * sum(ds) + 2.0 * pen
            if best is None or score < best[0]:
                best = (score, ox, oy, k, ds, pen, [(net, pl, (ox + c0, oy + c1)) for net, pl, (c0, c1) in pads],
                        [[(x + ox, y + oy) for x, y in c] for c in cy_])
    if best is None:
        report.append('%s: no legal spot within %.0f mm' % (task['ref'], float(task.get('radius', 7.0))))
        continue
    score, ox, oy, k, ds, pen, pads_out, cy_out = best
    rot = (f['rot'] + 90 * k) % 360
    moves[task['ref']] = [round(ox, 3), round(oy, 3), rot, side]
    occ_all |= raster(cy_out)
    report.append('%s -> (%.2f, %.2f) rot %d: pad-pin distances %s mm, power-copper penalty %.2f; pads %s' % (
        task['ref'], ox, oy, rot, ', '.join('%.2f' % x for x in ds), pen,
        ', '.join('%s (%.2f, %.2f)' % (n, c[0], c[1]) for n, _, c in pads_out)))
json.dump(moves, open(sys.argv[4], 'w'), indent=1)
print('\n'.join(report))
