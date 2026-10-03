"""GND voltage map relative to the battery connector's GND pin (J2.1), full-load DC, per copper layer.

    python gnd_heatmap.py COPPER.json STACK OUTDIR TAG [--h 0.1] [--try N] [--vmax MV]

COPPER.json is an export_copper6.py export (zones refilled on export). The DC currents that leave the board through
J2.1 enter the GND copper at:
  - M1.3 (the boost switch's source): the battery current 18.40 A minus the LED current, 11.03 A average;
  - R52.2 / R53.2 / R7.2 (the LED current-sense resistors' GND ends): 2.63 / 2.37 / 2.37 A.
The other loads (the 12 V and 5 V rails, the drivers) draw well under 1 % of that and are left out.
The network is solve_copper6.py's: every GND cell on a 0.1 mm grid joins its 4 neighbours with sheet conductance
sigma * t, and the via barrels (20 um plating) and THT pins join the layers they flash on. J2.1's copper is held at
0 V, and each source pad's copper is tied together and fed its current. Copper not connected to J2.1 is reported
as floating.

Outputs in OUTDIR:
  TAG_gndV.npz            the potential per layer (mV, NaN off the GND copper), the grid and the via candidates
  TAG_gnd_heatmap.png     one panel per layer on a common scale, with the GND vias and the numbered candidates
  TAG_gnd_report.txt      the GND pins of every part, the via currents and the candidate list
Candidates: points where at least two layers have GND copper and a 0.8 / 0.4 mm GND via fits by this board's rules
(0.65 mm from other-net tracks, pads and vias on every layer, 0.8 mm from any hole, 0.7 mm from the edge, outside
no-via keepouts). Each is ranked by the voltage across the layers it would join (the current it would carry scales
with it); the list is thinned to one point per 2 mm. A candidate inside another net's pour on a layer cuts an
antipad in that pour; the report names those pours, and only candidates that cut no power-net pour are numbered on
the map (the others are listed separately). --try N adds the best N clean candidates and solves again (the
antipads they would cut in other pours are not modelled).
"""
import json, math, os, sys
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse.csgraph import connected_components
from scipy.ndimage import distance_transform_edt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solve_copper6 as SC

SRC = {('M1', '3'): 11.03, ('R52', '2'): 2.63, ('R53', '2'): 2.37, ('R7', '2'): 2.37}
REF = ('J2', '1')
VIA_D, VIA_DRILL = 0.8, 0.4
CLR_OBS, CLR_HOLE, CLR_EDGE = 0.65, 0.8, 0.7
POWER_NETS = {'Vin', 'LX', 'rsense_lo', 'm2_source', 'm3_source', 'm4_source', 'Vout_1', 'Vout_2', 'Vout_3',
              'Output1_drain', 'Output2_drain', 'Output3_drain', 'Net-(M8-S)', 'Net-(M9-S)', 'Net-(M10-S)'}


def seg_mask(segs, x0, y0, nx, ny, h):
    """Cells within half-width of track centre lines: segs = [(x0, y0, x1, y1, halfwidth)]."""
    m = np.zeros((ny, nx), bool)
    for ax, ay, bx, by, r in segs:
        i0 = max(int((min(ax, bx) - r - x0) / h) - 1, 0)
        i1 = min(int((max(ax, bx) + r - x0) / h) + 2, nx)
        j0 = max(int((min(ay, by) - r - y0) / h) - 1, 0)
        j1 = min(int((max(ay, by) + r - y0) / h) + 2, ny)
        if i1 <= i0 or j1 <= j0:
            continue
        X, Y = np.meshgrid(x0 + (np.arange(i0, i1) + 0.5) * h, y0 + (np.arange(j0, j1) + 0.5) * h)
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0, 1) if L2 > 0 else np.zeros_like(X)
        d = np.hypot(X - ax - t * dx, Y - ay - t * dy)
        m[j0:j1, i0:i1] |= d <= r
    return m


def disc_mask(pts, x0, y0, nx, ny, h):
    return seg_mask([(x, y, x, y, r) for x, y, r in pts], x0, y0, nx, ny, h)


def build(cop, stack, h, extra_barrels=()):
    net = 'GND'
    st = SC.STACKS[stack]
    L = cop['layers']
    cu = dict(zip(L, st['cu']))
    z, acc = {}, 0.0
    for i, ln in enumerate(L):
        z[ln] = acc + st['cu'][i] / 2
        acc += st['cu'][i] + (st['gaps'][i] if i < len(st['gaps']) else 0)
    netcu = cop['nets'][net]
    allpts = np.array([p for ln in netcu for poly in netcu[ln] if not isinstance(poly, dict) for p in poly])
    x0, y0 = allpts[:, 0].min() - 2 * h, allpts[:, 1].min() - 2 * h
    nx = int(math.ceil((allpts[:, 0].max() - x0) / h)) + 3
    ny = int(math.ceil((allpts[:, 1].max() - y0) / h)) + 3
    layers = [ln for ln in L if ln in netcu]
    masks = {ln: SC.raster(netcu[ln], x0, y0, nx, ny, h) for ln in layers}
    ids, n = {}, 0
    for ln in layers:
        idx = -np.ones((ny, nx), np.int64)
        cnt = int(masks[ln].sum())
        idx[masks[ln]] = np.arange(n, n + cnt)
        ids[ln] = idx
        n += cnt
    rows, cols, vals = [], [], []
    for ln in layers:
        idx = ids[ln]
        for A, B in ((idx[:, :-1], idx[:, 1:]), (idx[:-1, :], idx[1:, :])):
            ok = (A >= 0) & (B >= 0)
            rows.append(A[ok]); cols.append(B[ok]); vals.append(np.full(int(ok.sum()), SC.SIGMA * cu[ln]))
    nxt = [n]

    def new_node():
        nxt[0] += 1
        return nxt[0] - 1

    def tie(node, cells, g=1e4):
        cells = np.asarray(cells, np.int64)
        rows.append(np.full(len(cells), node)); cols.append(cells); vals.append(np.full(len(cells), g))

    # barrels (vias and THT pins), as in solve_copper6.py
    bar_out = []
    for b in list(cop['barrels']) + list(extra_barrels):
        if b['net'] != net:
            continue
        i, j = int((b['x'] - x0) / h), int((b['y'] - y0) / h)
        r = b['drill'] / 2 + 0.75 * h
        rad = int(math.ceil(r / h)) + 1
        attach = {}
        for ln in b['layers']:
            if ln not in masks:
                continue
            cells = []
            for dj in range(-rad, rad + 1):
                for di in range(-rad, rad + 1):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < nx and 0 <= jj < ny and ids[ln][jj, ii] >= 0 and \
                            math.hypot(x0 + (ii + 0.5) * h - b['x'], y0 + (jj + 0.5) * h - b['y']) <= r:
                        cells.append(int(ids[ln][jj, ii]))
            if cells:
                attach[ln] = cells
        if len(attach) < 2:
            continue
        lns = [ln for ln in L if ln in attach]
        nodes = {}
        for ln in lns:
            nodes[ln] = new_node()
            tie(nodes[ln], attach[ln])
        segs = []
        for la, lb in zip(lns, lns[1:]):
            g = SC.SIGMA * math.pi * (b['drill'] - SC.T_PLATE) * SC.T_PLATE / abs(z[lb] - z[la])
            if b['kind'] == 'tht':
                g *= 20.0
            rows.append(np.array([nodes[la]])); cols.append(np.array([nodes[lb]])); vals.append(np.array([g]))
            segs.append((nodes[la], nodes[lb], g))
        bar_out.append(dict(b=b, segs=segs))
    # terminal pads: one node per pad, tied to all of its copper on every layer
    padmap = {}
    for p in cop['pads']:
        padmap.setdefault((p['ref'], str(p['num'])), []).append(p)

    def pad_cells(key):
        out = []
        for p in padmap.get(key, []):
            for ln, polys in p['polys'].items():
                if ln in masks:
                    pm = SC.raster(polys, x0, y0, nx, ny, h) & masks[ln]
                    if not pm.any():
                        i, j = int((p['x'] - x0) / h), int((p['y'] - y0) / h)
                        if 0 <= i < nx and 0 <= j < ny and masks[ln][j, i]:
                            pm[j, i] = True
                    out.extend(int(c) for c in ids[ln][pm])
        return out

    term = {}
    for key in list(SRC) + [REF]:
        cells = pad_cells(key)
        if not cells:
            raise SystemExit('pad %s.%s has no GND copper' % key)
        node = new_node()
        tie(node, cells)
        term[key] = node
    N = nxt[0]
    r_ = np.concatenate([np.atleast_1d(a) for a in rows])
    c_ = np.concatenate([np.atleast_1d(a) for a in cols])
    v_ = np.concatenate([np.atleast_1d(a) for a in vals])
    G = sp.coo_matrix((v_, (r_, c_)), shape=(N, N)).tocsr()
    G = G + G.T
    Lap = (sp.diags(np.asarray(G.sum(axis=1)).ravel()) - G).tocsr()
    ncomp, lab = connected_components(G, directed=False)
    live = lab == lab[term[REF]]
    for key in SRC:
        if not live[term[key]]:
            raise SystemExit('%s.%s is not connected to %s.%s through GND' % (key + REF))
    I = np.zeros(N)
    for key, a in SRC.items():
        I[term[key]] = a
    free = np.where(live)[0]
    free = free[free != term[REF]]
    V = np.full(N, np.nan)
    V[term[REF]] = 0.0
    V[free] = spla.spsolve(Lap[free][:, free].tocsc(), I[free], permc_spec='MMD_AT_PLUS_A')
    grid = dict(x0=x0, y0=y0, h=h, nx=nx, ny=ny)
    Vl = {}
    for ln in layers:
        a = np.full((ny, nx), np.nan)
        m = ids[ln] >= 0
        a[m] = V[ids[ln][m]] * 1e3            # mV
        Vl[ln] = a
    floating = {ln: float(((ids[ln] >= 0) & ~live[np.maximum(ids[ln], 0)]).sum() * h * h) for ln in layers}
    vias = []
    for bb in bar_out:
        worst = 0.0
        for na, nb, g in bb['segs']:
            if live[na] and live[nb]:
                worst = max(worst, g * abs(V[na] - V[nb]))
        vias.append(dict(x=bb['b']['x'], y=bb['b']['y'], kind=bb['b']['kind'], ref=bb['b'].get('ref'),
                         drill=bb['b']['drill'], I=worst))
    return dict(grid=grid, layers=layers, V=Vl, masks=masks, term={k: V[v] * 1e3 for k, v in term.items()},
                floating=floating, vias=vias, z=z)


def pad_potentials(cop, res):
    g, out = res['grid'], {}
    for p in cop['pads']:
        if p['net'] != 'GND':
            continue
        vals = []
        for ln, polys in p['polys'].items():
            if ln in res['V']:
                pm = SC.raster(polys, g['x0'], g['y0'], g['nx'], g['ny'], g['h'])
                v = res['V'][ln][pm]
                vals.extend(v[np.isfinite(v)].tolist())
        if vals:
            out.setdefault(p['ref'], []).append(float(np.mean(vals)))
    return {r: (min(v), max(v)) for r, v in out.items()}


def candidates(cop, res, keep=20, spacing=2.0):
    g = res['grid']
    x0, y0, h, nx, ny = g['x0'], g['y0'], g['h'], g['nx'], g['ny']
    L = cop['layers']
    ok = np.ones((ny, nx), bool)
    # other-net tracks, pads and via pads, per layer
    for ln in L:
        obs = seg_mask([(t['x0'], t['y0'], t['x1'], t['y1'], t['w'] / 2) for t in cop['tracks']
                        if t['layer'] == ln and t['net'] != 'GND'], x0, y0, nx, ny, h)
        obs |= SC.raster([poly for p in cop['pads'] if p['net'] != 'GND' for poly in p['polys'].get(ln, [])],
                         x0, y0, nx, ny, h)
        obs |= disc_mask([(v['x'], v['y'], v['dia'] / 2) for v in cop['vias'] if v['net'] != 'GND' and ln in v['layers']],
                         x0, y0, nx, ny, h)
        ok &= distance_transform_edt(~obs) * h >= CLR_OBS
    holes = disc_mask([(b['x'], b['y'], b['drill'] / 2) for b in cop['barrels']], x0, y0, nx, ny, h)
    ok &= distance_transform_edt(~holes) * h >= CLR_HOLE
    edge = seg_mask([(e[0], e[1], e[2], e[3], 0.01) for e in cop['edge']], x0, y0, nx, ny, h)
    ok &= distance_transform_edt(~edge) * h >= CLR_EDGE
    for k in cop['keepouts']:
        if k.get('no_vias'):
            ok &= ~SC.raster([k['pts']], x0, y0, nx, ny, h)
    V = np.stack([np.where(np.isfinite(res['V'][ln]), res['V'][ln], np.nan) for ln in res['layers']])
    have = np.isfinite(V)
    nl = have.sum(0)
    dv = np.where(nl >= 2, np.nanmax(np.where(have, V, -np.inf), 0) - np.nanmin(np.where(have, V, np.inf), 0), 0.0)
    dv = np.where(ok & (nl >= 2), dv, 0.0)
    # other nets' pours that a via at each point would cut
    zone_m = {}
    for zn in cop['zones']:
        if zn['net'] != 'GND':
            zone_m.setdefault((zn['net'], zn['layer']), []).extend(zn['polys'])
    zone_r = {k: SC.raster(v, x0, y0, nx, ny, h) for k, v in zone_m.items()}
    cut_power = np.zeros((ny, nx), bool)
    for (zn, _), m in zone_r.items():
        if zn in POWER_NETS:
            cut_power |= m
    out = {}
    for kind, allow in (('clean', ~cut_power), ('cuts_power', cut_power)):
        picks = []
        work = np.where(allow, dv, 0.0)
        rad = int(spacing / h)
        while len(picks) < keep and work.max() > 0:
            j, i = np.unravel_index(int(np.argmax(work)), work.shape)
            x, y = x0 + (i + 0.5) * h, y0 + (j + 0.5) * h
            lays = [ln for k, ln in enumerate(res['layers']) if have[k, j, i]]
            cuts = sorted('%s on %s' % k for k, m in zone_r.items() if m[j, i])
            picks.append(dict(x=round(x, 2), y=round(y, 2), dv=float(dv[j, i]), layers=lays, cuts=cuts))
            work[max(j - rad, 0):j + rad + 1, max(i - rad, 0):i + rad + 1] = 0
        out[kind] = picks
    return out, dv


def plot(cop, res, picks, path, title, vmax=None):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    g = res['grid']
    ext = [g['x0'], g['x0'] + g['nx'] * g['h'], g['y0'] + g['ny'] * g['h'], g['y0']]
    vm = vmax or max(float(np.nanmax(v)) for v in res['V'].values())
    L = res['layers']
    cols = 3
    rows_ = int(math.ceil(len(L) / cols))
    fig, axs = plt.subplots(rows_, cols, figsize=(6.2 * cols, 6.6 * rows_))
    axs = np.atleast_1d(axs).ravel()
    vx = [(b['x'], b['y']) for b in cop['barrels'] if b['net'] == 'GND' and b['kind'] == 'via']
    for ax, ln in zip(axs, L):
        ax.set_facecolor('#d9d9d9')
        im = ax.imshow(res['V'][ln], extent=ext, cmap='turbo', vmin=0, vmax=vm, interpolation='nearest')
        for e in cop['edge']:
            ax.plot([e[0], e[2]], [e[1], e[3]], 'k-', lw=0.6)
        if vx:
            ax.plot(*zip(*vx), 'o', ms=1.6, mfc='none', mec='k', mew=0.4)
        for k, p in enumerate(picks):
            if ln in p['layers']:
                ax.plot(p['x'], p['y'], 'o', ms=7, mfc='none', mec='m', mew=1.2)
                ax.annotate(str(k + 1), (p['x'], p['y']), xytext=(3, 3), textcoords='offset points', color='m',
                            fontsize=7, weight='bold')
        for key in list(SRC) + [REF]:
            for pd in cop['pads']:
                if (pd['ref'], str(pd['num'])) == key:
                    ax.annotate('%s.%s' % key, (pd['x'], pd['y']), fontsize=7, color='w', weight='bold',
                                ha='center', bbox=dict(boxstyle='round,pad=0.1', fc='k', alpha=0.6, lw=0))
                    break
        ax.set_title(ln, fontsize=10)
        ax.set_aspect('equal')
        ax.tick_params(labelsize=7)
    for ax in axs[len(L):]:
        ax.axis('off')
    cb = fig.colorbar(im, ax=axs.tolist(), fraction=0.02, pad=0.01)
    cb.set_label('GND voltage above J2.1 (mV)')
    fig.suptitle(title, fontsize=11)
    fig.savefig(path, dpi=110, bbox_inches='tight')
    plt.close(fig)


def main():
    a = sys.argv[1:]
    cop_path, stack, outdir, tag = a[:4]
    h = float(a[a.index('--h') + 1]) if '--h' in a else 0.1
    ntry = int(a[a.index('--try') + 1]) if '--try' in a else 0
    vmax = float(a[a.index('--vmax') + 1]) if '--vmax' in a else None
    os.makedirs(outdir, exist_ok=True)
    cop = json.load(open(cop_path))
    SC.LAYERS[:] = cop['layers']
    res = build(cop, stack, h)
    allp, dv = candidates(cop, res)
    picks = allp['clean']
    pads = pad_potentials(cop, res)
    lines = ['GND voltage above J2.1, full-load DC (%s, %s, grid %.2f mm)' % (os.path.basename(cop_path), stack, h),
             'currents in: ' + ', '.join('%s.%s %.2f A' % (k + (v,)) for k, v in SRC.items()) +
             '; out at J2.1 %.2f A' % sum(SRC.values()), '']
    lines.append('terminal pads (mV): ' + ', '.join('%s.%s %.2f' % (k + (v,)) for k, v in res['term'].items()))
    lines.append('highest GND voltage per layer (mV): ' + ', '.join(
        '%s %.2f' % (ln, float(np.nanmax(res['V'][ln]))) for ln in res['layers']))
    fl = {ln: v for ln, v in res['floating'].items() if v > 0}
    lines.append('floating GND copper (mm2): %s' % (fl or 'none'))
    lines += ['', 'GND pins per part, lowest-highest pad (mV), highest first:']
    for r, (lo, hi) in sorted(pads.items(), key=lambda kv: -kv[1][1]):
        lines.append('  %-6s %6.2f - %6.2f' % (r, lo, hi))
    vv = sorted([v for v in res['vias'] if v['kind'] == 'via'], key=lambda v: -v['I'])
    lines += ['', 'GND vias carrying the most current (IPC 10 C rating %.2f A for 0.4 mm):' % SC.via_rating(0.4)]
    for v in vv[:15]:
        lines.append('  (%6.2f, %6.2f) drill %.2f  %.2f A  %.2fx' % (v['x'], v['y'], v['drill'], v['I'],
                                                                     v['I'] / SC.via_rating(v['drill'])))
    for kind, head in (('clean', 'new GND via candidates that cut no power pour (numbered on the map)'),
                       ('cuts_power', 'stronger spots that would cut a power pour (not on the map)')):
        lines += ['', head + ', ranked by the voltage across the layers they would join:']
        for k, p in enumerate(allp[kind]):
            lines.append('  %2d (%6.2f, %6.2f)  %.3f mV  joins %s%s' % (k + 1, p['x'], p['y'], p['dv'], ' '.join(
                l.replace('.Cu', '') for l in p['layers']), ('  cuts ' + ', '.join(p['cuts'])) if p['cuts'] else ''))
    title = '%s: GND voltage above J2.1 at full load (18.4 A DC); circles = GND vias, magenta = candidates' % tag
    plot(cop, res, picks, os.path.join(outdir, tag + '_gnd_heatmap.png'), title, vmax)
    if ntry:
        add = [dict(net='GND', x=p['x'], y=p['y'], drill=VIA_DRILL, dia=VIA_D, kind='via', layers=p['layers'])
               for p in picks[:ntry]]
        r2 = build(cop, stack, h, add)
        lines += ['', 'with the best %d candidates added: terminal pads (mV) ' % ntry + ', '.join(
            '%s.%s %.2f' % (k + (v,)) for k, v in r2['term'].items())]
        p2 = pad_potentials(cop, r2)
        lines.append('  largest part GND pin: %.2f mV (was %.2f)' % (max(v[1] for v in p2.values()),
                                                                    max(v[1] for v in pads.values())))
    np.savez_compressed(os.path.join(outdir, tag + '_gndV.npz'), layers=np.array(res['layers']),
                        **{k: v for k, v in res['grid'].items()},
                        **{'V_' + ln.replace('.', '_'): res['V'][ln].astype(np.float32) for ln in res['layers']},
                        cand=np.array([[p['x'], p['y'], p['dv']] for p in picks]))
    open(os.path.join(outdir, tag + '_gnd_report.txt'), 'w').write('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
