"""kicad_sheets_2026-10-09/tools/sync_check.py, unchanged, with the parts added by these review fixes assigned to
their board (sync_check reads the 2026-09-30 part -> board assignment, which predates them). The assignment file
itself is not touched: a temp copy with the extra entries is used.

    python sync_check_rf.py DIR
"""
import json, os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', 'kicad_sheets_2026-10-09', 'tools')))
import sync_check as SC

EXTRA = {'R106': 'CONTROL', 'R107': 'CONTROL'}   # step 5: I2C pull-ups (user's D1 answer)

a = json.load(open(SC.SS.ASSIGN))
for k, v in EXTRA.items():
    assert a.get(k, v) == v, k
    a[k] = v
tmp = os.path.join(tempfile.mkdtemp(prefix='syncrf_'), 'assign.json')
json.dump(a, open(tmp, 'w'))
SC.SS.ASSIGN = tmp
sys.exit(1 if SC.main(sys.argv[1]) else 0)
