#!/bin/bash
LT="/c/Program Files/ADI/LTspice/LTspice.exe"
run() { s=$(date +%s); "$LT" -b "$1.net"; echo "$1 exit $? after $(( $(date +%s) - s )) s: $(grep -a 'Total elapsed\|Simulation Failed' "$1.log" | head -1)"; }
run f2p2 & sleep 15; run f4p7 & sleep 15; run f10 & wait
run f22 & sleep 15; run f47 & wait
echo "sweep2 finished $(date +%T)"
