#!/bin/bash
# Loop-via cost / benefit per location (user, 2026-10-12: analysis only, not applied): one DC solve per what-if export,
# one at a time, 3 workers (RAM is short while the user's apps are open). Base = step06b (the copy's power board).
#   bash run_solves.sh            (from this folder)
set -u
H="$(cd "$(dirname "$0")" && pwd)"
B="$(cd "$H/../../.." && pwd)"          # BOOST_split_boards
w() { cygpath -w "$1"; }
cd "$B"
for v in ch1 ch3 vout3; do
  [ -e "$H/${v}_solve.json" ] && { echo "$v: solve exists, skipped"; continue; }
  t0=$(date +%s)
  python power6_2026-10-01/tools/solve_copper6.py "$(w "$H/${v}_cu.json")" "$(w route_2026-09-16/branches_power.json)" \
      --stack JLC061611-7628D --out "$(w "$H/${v}_solve.json")" --workers "${WORKERS:-3}" > "$H/${v}_solve.txt" 2>&1
  echo "$v: exit $? in $(( $(date +%s) - t0 )) s"
done
