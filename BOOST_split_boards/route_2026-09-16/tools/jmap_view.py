"""Plot the solved sheet current (A/mm) over a window, per layer (system Python).

usage: python jmap_view.py SHEET_CURRENT.npz OUT.png X0 Y0 X1 Y1 [LAYER,LAYER...]

White is copper carrying nothing; the colour scale stops at the router's track limit (J_FORBID 0.25 A/mm), so
anything coloured at full scale is copper a signal track may not cut.
"""
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

X0 = Y0 = 29.0
H = 0.1
d = np.load(sys.argv[1])
out = sys.argv[2]
x0, y0, x1, y1 = map(float, sys.argv[3:7])
layers = sys.argv[7].split(',') if len(sys.argv) > 7 else ['F_Cu', 'In2_Cu', 'In3_Cu', 'In5_Cu', 'B_Cu']
i0, i1 = int((x0 - X0) / H), int((x1 - X0) / H)
j0, j1 = int((y0 - Y0) / H), int((y1 - Y0) / H)
fig, axs = plt.subplots(1, len(layers), figsize=(5.5 * len(layers), 5.5 * (y1 - y0) / (x1 - x0) + 0.8), squeeze=False)
for ax, ln in zip(axs[0], layers):
    a = d[ln][j0:j1, i0:i1]
    im = ax.imshow(a, extent=(x0, x1, y1, y0), vmin=0, vmax=0.25, cmap='inferno_r')
    ax.set_title('%s (max %.2f A/mm here)' % (ln, a.max()))
    ax.grid(True, lw=0.3, alpha=0.4)
    ax.set_xticks(np.arange(round(x0), x1, 2))
    ax.set_yticks(np.arange(round(y0), y1, 2))
fig.colorbar(im, ax=axs[0], shrink=0.8, label='A/mm (scale stops at the 0.25 track limit)')
fig.savefig(out, dpi=110, bbox_inches='tight')
print('wrote', out)
