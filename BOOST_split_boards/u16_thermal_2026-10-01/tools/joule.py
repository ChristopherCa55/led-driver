# DC current flow on one net's copper (all layers, vias, plated holes) and the resulting Joule heat per cell.
# Same grid and indexing as thermal.Model, so the heat map drops straight into the thermal solve.
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

SIGMA_CU = 1 / (1.72e-8 * (1 + 0.00393 * (85 - 20)))  # S/m at 85 C


def solve_net(m, netid, barrels, injections, sinks):
    """m: thermal.Model (for arr, board, idx, tcu, td, a). netid: the net's raster id.
    barrels: list of (iy, ix, layers, drill_mm) for this net's vias and plated holes.
    injections: list of (list of node cells [(l, iy, ix)], current A) - current spread evenly over the cells.
    sinks: list of node cells held at 0 V.
    Returns (heat per thermal node [W], total Joule power [W], max voltage drop [V])."""
    nl, nc, a = m.nl, m.nc, m.a
    on = (m.arr == netid) & m.board[None]
    gid = -np.ones(on.shape, np.int64)
    gid[on] = np.arange(on.sum())
    n = int(on.sum())
    edges = []  # (i, j, G, thermal node i, thermal node j)
    for l in range(nl):
        g = SIGMA_CU * m.tcu[l]
        for dy, dx in ((0, 1), (1, 0)):
            mm = on[l, :m.ny - dy, :m.nx - dx] & on[l, dy:, dx:]
            iy, ix = np.nonzero(mm)
            edges.append((gid[l, iy, ix], gid[l, iy + dy, ix + dx], np.full(len(iy), g),
                          l * nc + m.idx[iy, ix], l * nc + m.idx[iy + dy, ix + dx]))
    z = np.concatenate([[0], np.cumsum(m.td)])
    bi, bj, bg, ti, tj = [], [], [], [], []
    for iy, ix, layers, drill in barrels:
        layers = [l for l in layers if on[l, iy, ix]]
        area = np.pi * drill * 1e-3 * 0.018e-3
        for l1, l2 in zip(layers[:-1], layers[1:]):
            L = z[l2] - z[l1] + m.tcu[l1 + 1:l2].sum()
            bi.append(gid[l1, iy, ix]); bj.append(gid[l2, iy, ix]); bg.append(SIGMA_CU * area / L)
            ti.append(l1 * nc + m.idx[iy, ix]); tj.append(l2 * nc + m.idx[iy, ix])
    if bi:
        edges.append((np.array(bi), np.array(bj), np.array(bg), np.array(ti), np.array(tj)))
    I = np.concatenate([e[0] for e in edges]); J = np.concatenate([e[1] for e in edges])
    G = np.concatenate([e[2] for e in edges])
    TI = np.concatenate([e[3] for e in edges]); TJ = np.concatenate([e[4] for e in edges])
    K = sp.coo_matrix((np.concatenate([G, G, -G, -G]), (np.concatenate([I, J, I, J]), np.concatenate([I, J, J, I]))),
                      shape=(n, n)).tocsr()
    big = np.full(n, 1e-6)  # ties floating copper islands to 0 V; leaks well under 1 mA in total
    for l, iy, ix in sinks:
        if on[l, iy, ix]:
            big[gid[l, iy, ix]] = 1e6
    K = (K + sp.diags(big)).tocsc()
    rhs = np.zeros(n)
    for cells, cur in injections:
        cells = [c for c in cells if on[c]]
        for c in cells:
            rhs[gid[c]] += cur / len(cells)
    V = spla.spsolve(K, rhs, permc_spec='MMD_AT_PLUS_A')
    P = G * (V[I] - V[J]) ** 2
    q = np.zeros(nl * nc)
    np.add.at(q, TI, P / 2)
    np.add.at(q, TJ, P / 2)
    return q, P.sum(), V.max() - V.min()


def pad_cells(m, x0, y0, x, y, r_mm, layers):
    """Cells within r_mm of (x, y) on the given layers."""
    out = []
    a = m.a * 1e3
    k = int(r_mm / a) + 1
    cy, cx = int((y - y0) / a), int((x - x0) / a)
    for l in layers:
        for iy in range(cy - k, cy + k + 1):
            for ix in range(cx - k, cx + k + 1):
                if 0 <= iy < m.ny and 0 <= ix < m.nx and ((iy - cy) ** 2 + (ix - cx) ** 2) * a * a <= r_mm ** 2:
                    out.append((l, iy, ix))
    return out
