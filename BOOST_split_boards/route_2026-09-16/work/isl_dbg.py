import json, sys
sys.path.insert(0, 'tools')
import route_signals as R
import numpy as np
cop = json.load(open('work/v11_cu.json'))
bd = R.Board(cop)
for net in ('5V', '12V', 'analog_5V', 'm2_source'):
    isl, labels = bd.islands(bd.nid[net])
    print(net, 'islands', len(isl), [len(m) for m in isl][:25])
