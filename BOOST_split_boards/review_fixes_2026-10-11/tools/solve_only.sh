#!/bin/bash
# Re-run only the DC-solve part of step_checks.sh (solve, loop L, power pcb_checks) for STEP_DIR, whose power_cu.json
# already exists (e.g. after the solve ran out of memory). Same commands as step_checks.sh; old outputs are moved to
# STEP/solve_failed_<n>/ first, never deleted.
#
#   WORKERS=5 bash solve_only.sh STEP_DIR
set -u
S="$(cd "${1:?STEP_DIR}" && pwd)"
T="$(cd "$(dirname "$0")" && pwd)"
B="$(cd "$T/../.." && pwd)"
w() { cygpath -w "$1"; }
[ -f "$S/power_cu.json" ] || { echo "no $S/power_cu.json"; exit 1; }
n=1; while [ -e "$S/solve_failed_$n" ]; do n=$((n + 1)); done
mkdir "$S/solve_failed_$n"
for x in power_solve.txt power_solve.json loopL.txt dumps; do [ -e "$S/$x" ] && mv "$S/$x" "$S/solve_failed_$n/"; done
t0=$(date +%s)
cd "$B"
python power6_2026-10-01/tools/solve_copper6.py "$(w "$S/power_cu.json")" "$(w route_2026-09-16/branches_power.json)" \
    --stack JLC061611-7628D --out "$(w "$S/power_solve.json")" --dump "$(w "$S/dumps")" --workers "${WORKERS:-9}" > "$S/power_solve.txt" 2>&1
python power6_2026-10-01/tools/loop_L6.py "$(w "$S/power_cu.json")" "$(w "$S/dumps")" JLC061611-7628D > "$S/loopL.txt" 2>&1
mkdir -p "$S/checks"
python review_2026-10-10/pcb/pcb_checks.py "$(w "$S/power_cu.json")" power "$(w "$S/checks")" --solve "$(w "$S/dumps")" \
    route_2026-09-16/branches_power.json > /dev/null 2>&1
echo "solve_only done in $(( $(date +%s) - t0 )) s"; tail -2 "$S/power_solve.txt"; cat "$S/loopL.txt"
