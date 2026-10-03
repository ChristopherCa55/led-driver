# Rasterize the exported copper (export_copper.py JSON) onto a square grid: one int array of net ids per layer.
import json
import numpy as np
from matplotlib.path import Path


def load(fn):
    return json.load(open(fn))


def rasterize(d, a, box=None):
    """a: cell size (mm). box: (x0, y0, x1, y1) or None for the board outline bbox.
    Returns (x centres, y centres, net names list, int array [layer, iy, ix], board mask)."""
    if box is None:
        pts = np.array([p for ol in d['outline'] for p in ol])
        box = (pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())
    x0, y0, x1, y1 = box
    nx, ny = int(round((x1 - x0) / a)), int(round((y1 - y0) / a))
    xs = x0 + a * (np.arange(nx) + 0.5)
    ys = y0 + a * (np.arange(ny) + 0.5)
    X, Y = np.meshgrid(xs, ys)
    P = np.column_stack([X.ravel(), Y.ravel()])
    nets = ['']
    netid = {'': 0}
    arr = np.zeros((len(d['layers']), ny, nx), np.int32)

    def fill(poly, target, val):
        poly = np.asarray(poly)
        bx0, by0 = poly.min(0)
        bx1, by1 = poly.max(0)
        ix0, ix1 = max(0, int((bx0 - x0) / a) - 1), min(nx, int((bx1 - x0) / a) + 2)
        iy0, iy1 = max(0, int((by0 - y0) / a) - 1), min(ny, int((by1 - y0) / a) + 2)
        if ix0 >= ix1 or iy0 >= iy1:
            return
        sub = np.column_stack([X[iy0:iy1, ix0:ix1].ravel(), Y[iy0:iy1, ix0:ix1].ravel()])
        m = Path(poly).contains_points(sub).reshape(iy1 - iy0, ix1 - ix0)
        target[iy0:iy1, ix0:ix1][m] = val

    for li, ln in enumerate(d['layers']):
        for net, pl in d['copper'][ln].items():
            if net not in netid:
                netid[net] = len(nets)
                nets.append(net)
            for poly in pl:
                fill(poly, arr[li], netid[net])
    board = np.zeros((ny, nx), bool)
    for ol in d['outline']:
        fill(ol, board, True)
    return xs, ys, nets, arr, board
