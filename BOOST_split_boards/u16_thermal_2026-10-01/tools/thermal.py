# Steady-state finite-difference heat model of a multilayer PCB (2026-10-01).
# One node per grid cell per copper layer. Conductances:
#   in-plane : copper (only between cells of the same net) + the FR4 half-dielectrics either side of the layer
#   vertical : FR4 between adjacent copper layers (through-plane k)
#   vias/PTH : plated barrel (pi * drill * plating) chained between the layers the via is flashed on
#   surfaces : h * cell area on the top and bottom layers, to a fixed ambient
#   device   : one junction node joined to the cells under its tab by R_jt (spread evenly over those cells)
# Temperatures are rises above ambient.
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

K_CU = 385.0        # W/m-K, copper
K_FR4_XY = 0.8      # W/m-K, FR4 in-plane
K_FR4_Z = 0.3       # W/m-K, FR4 through-plane


class Model:
    def __init__(self, arr, board, a_mm, t_cu_mm, t_diel_mm):
        """arr: int net ids [layer, iy, ix] (0 = no copper); board: bool [iy, ix]; a_mm: cell size;
        t_cu_mm: copper thickness per layer; t_diel_mm: dielectric thickness between layer l and l+1."""
        self.arr, self.board, self.a = arr, board, a_mm * 1e-3
        self.tcu = np.asarray(t_cu_mm) * 1e-3
        self.td = np.asarray(t_diel_mm) * 1e-3
        self.nl, self.ny, self.nx = arr.shape
        self.idx = -np.ones(board.shape, np.int64)
        self.idx[board] = np.arange(board.sum())
        self.nc = int(board.sum())
        self.extra = []          # (node_i, node_j, G) for vias / devices
        self.n_extra_nodes = 0

    def node(self, l, iy, ix):
        return l * self.nc + self.idx[iy, ix]

    def cell(self, x_mm, y_mm, x0, y0):
        return int((y_mm - y0) / (self.a * 1e3)), int((x_mm - x0) / (self.a * 1e3))

    def add_barrel(self, iy, ix, layers, drill_mm, plating_mm=0.018):
        """layers: sorted copper-layer indices the barrel is joined to."""
        if self.idx[iy, ix] < 0 or len(layers) < 2:
            return
        area = np.pi * drill_mm * 1e-3 * plating_mm * 1e-3
        z = np.concatenate([[0], np.cumsum(self.td)])  # depth of each copper layer (dielectric only)
        for l1, l2 in zip(layers[:-1], layers[1:]):
            L = z[l2] - z[l1] + self.tcu[l1 + 1:l2].sum() if l2 > l1 + 1 else z[l2] - z[l1]
            self.extra.append((self.node(l1, iy, ix), self.node(l2, iy, ix), K_CU * area / L))

    def add_device(self, layer, cells, R_jt):
        """cells: list of (iy, ix). Returns the junction node index."""
        j = self.nl * self.nc + self.n_extra_nodes
        self.n_extra_nodes += 1
        cells = [c for c in cells if self.idx[c] >= 0]
        g = 1.0 / R_jt / len(cells)
        for c in cells:
            self.extra.append((j, self.node(layer, *c), g))
        return j

    def build(self, h_top, h_bot):
        a, nl, nc = self.a, self.nl, self.nc
        N = nl * nc + self.n_extra_nodes
        rows, cols, vals = [], [], []

        def link(i, j, g):
            rows.extend([i, j, i, j]); cols.extend([i, j, j, i]); vals.extend([g, g, -g, -g])

        # in-plane
        half = np.zeros(nl)
        for l in range(nl):
            half[l] = (self.td[l - 1] / 2 if l > 0 else 0) + (self.td[l] / 2 if l < nl - 1 else 0)
        for l in range(nl):
            A = self.arr[l]
            g_fr4 = K_FR4_XY * half[l]
            g_cu = K_CU * self.tcu[l]
            for dy, dx in ((0, 1), (1, 0)):
                m = self.board[:self.ny - dy, :self.nx - dx] & self.board[dy:, dx:]
                a1 = A[:self.ny - dy, :self.nx - dx]; a2 = A[dy:, dx:]
                same = (a1 == a2) & (a1 > 0)
                g = g_fr4 + g_cu * same
                iy, ix = np.nonzero(m)
                n1 = l * nc + self.idx[iy, ix]
                n2 = l * nc + self.idx[iy + dy, ix + dx]
                gg = g[iy, ix]
                rows.append(np.concatenate([n1, n2, n1, n2])); cols.append(np.concatenate([n1, n2, n2, n1]))
                vals.append(np.concatenate([gg, gg, -gg, -gg]))
        # vertical through FR4
        for l in range(nl - 1):
            g = K_FR4_Z * a * a / self.td[l]
            n1 = l * nc + np.arange(nc); n2 = (l + 1) * nc + np.arange(nc)
            gg = np.full(nc, g)
            rows.append(np.concatenate([n1, n2, n1, n2])); cols.append(np.concatenate([n1, n2, n2, n1]))
            vals.append(np.concatenate([gg, gg, -gg, -gg]))
        # surfaces
        diag = np.zeros(N)
        diag[:nc] += h_top * a * a
        diag[(nl - 1) * nc:nl * nc] += h_bot * a * a
        # extras
        if self.extra:
            e = np.array(self.extra)
            i, j, g = e[:, 0].astype(np.int64), e[:, 1].astype(np.int64), e[:, 2]
            rows.append(np.concatenate([i, j, i, j])); cols.append(np.concatenate([i, j, j, i]))
            vals.append(np.concatenate([g, g, -g, -g]))
        r = np.concatenate([np.asarray(x, np.int64).ravel() for x in rows])
        c = np.concatenate([np.asarray(x, np.int64).ravel() for x in cols])
        v = np.concatenate([np.asarray(x, float).ravel() for x in vals])
        K = sp.coo_matrix((v, (r, c)), shape=(N, N)).tocsr() + sp.diags(diag)
        self.K = K.tocsc()
        self.N = N
        return self.K

    def solve(self, q):
        """q: heat vector (W) of length N. Returns temperature rises."""
        return spla.spsolve(self.K, q, permc_spec='MMD_AT_PLUS_A')

    def surface_loss(self, T, h_top, h_bot):
        """Heat leaving the top and bottom surfaces (W): must equal the heat put in."""
        a2 = self.a * self.a
        return h_top * a2 * T[:self.nc].sum() + h_bot * a2 * T[(self.nl - 1) * self.nc:self.nl * self.nc].sum()

    def layer_map(self, T, l):
        out = np.full(self.board.shape, np.nan)
        out[self.board] = T[l * self.nc:(l + 1) * self.nc]
        return out
