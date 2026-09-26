#!/bin/bash
# M1 turn-off re-check with the routed loop inductances (2026-09-24). Runs the four netlists in LTspice batch mode,
# staggered 15 s apart (two batch runs started in the same second can fail silently).
LT="/c/Program Files/ADI/LTspice/LTspice.exe"
cd "$(dirname "$0")"
run() { s=$(date +%s); "$LT" -b "$1.net"; echo "$1 exit $? after $(( $(date +%s) - s )) s: $(grep -a 'Total elapsed\|Simulation Failed' "$1.log" | head -1)"; }
run m1_routed_nom & sleep 15; run m1_routed_lv & sleep 15; run m1_pess_nom & sleep 15; run m1_pess_lv & wait
echo "all finished $(date +%T)"
