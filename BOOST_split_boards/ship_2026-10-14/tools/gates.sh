#!/bin/bash
# Gates on one shipped folder's KiCad files, run on a scratch copy (KiCad writes .kicad_prl beside what it opens).
#   bash gates.sh FOLDER          (FOLDER = BOOST_package | BOOST_stuff | BOOST_schematic_cleanup)
set -u
F="${1:?FOLDER}"
H="$(cd "$(dirname "$0")/.." && pwd)"; ROOT="$(cd "$H/../.." && pwd)"
K="/c/Program Files/KiCad/10.0/bin"; w() { cygpath -w "$1"; }
O="$H/checks/$F"
[ -e "$O" ] && { echo "exists: $O"; exit 1; }
mkdir -p "$O/kicad"
(cd "$ROOT/$F/KiCad" && for x in *; do case "$x" in "~"*|*.kicad_prl|*.lck|*-backups|.history) ;; *) cp -r "$x" "$O/kicad/";; esac; done)
for p in BOOST BOOST_power_RC2 BOOST_control_RC2; do
  "$K/kicad-cli.exe" sch erc --severity-all -o "$(w "$O/erc_$p.rpt")" "$(w "$O/kicad/$p.kicad_sch")" 2>&1 | grep -i "violations" | sed "s/^/ERC $p: /"
done
for b in power control; do
  "$K/kicad-cli.exe" pcb drc --refill-zones --schematic-parity --severity-all --format json \
      -o "$(w "$O/drc_$b.json")" "$(w "$O/kicad/BOOST_${b}_RC2.kicad_pcb")" > /dev/null 2>&1
done
python - "$O" <<'EOF'
import json, sys
from collections import Counter
for b in ('power', 'control'):
    d = json.load(open('%s/drc_%s.json' % (sys.argv[1], b)))
    v = d['violations']
    print('DRC %s: errors %d, warnings %d %s, unconnected %d, parity %d' % (b, sum(1 for x in v if x['severity'] == 'error'),
          sum(1 for x in v if x['severity'] == 'warning'), dict(Counter(x['type'] for x in v)),
          len(d.get('unconnected_items', [])), len(d.get('schematic_parity', []))))
EOF
python "$(w "$H/../review_fixes_2026-10-11/tools/sync_check_rf.py")" "$(w "$O/kicad")" > "$O/sync_check.txt" 2>&1
echo "sync: $(head -1 "$O/sync_check.txt")"
