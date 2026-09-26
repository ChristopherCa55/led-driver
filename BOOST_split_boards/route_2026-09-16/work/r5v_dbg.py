import json, sys
sys.path.insert(0, 'tools')
import route_signals as R
import numpy as np
cop = json.load(open('work/v11_cu.json'))
bd = R.Board(cop)
n = bd.nid['5V']
for it in range(4):
    isl, labels = bd.islands(n)
    print('attempt', it, 'islands', len(isl))
    log = []
    # replicate one step
    from scipy import ndimage
    proj = []
    for members in isl:
        m = np.zeros((R.NY, R.NX), bool)
        for (l, k) in members:
            m |= labels[l] == k
        proj.append(m)
    d0 = ndimage.distance_transform_edt(~proj[0]) * R.H
    ds = [float(d0[proj[b]].min()) for b in range(1, len(proj))]
    print('   dists from island 0:', [round(x, 1) for x in ds[:8]])
    b = 1 + int(np.argmin(ds))
    res = bd.route_edge(n, isl[0], isl[b], labels)
    print('   route to', b, 'result', None if res is None else len(res[0]))
    if res is None:
        break
    g = bd.commit(n, *res)
    print('   geoms', [x[0] for x in g][:10], [x[4] if x[0] == 'via' else x[6] for x in g][:10])
