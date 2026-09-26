#!/bin/sh
# Checks on a routed card board (run from card_route_2026-09-22/):  tools/fr_verify.sh NAME   (work/NAME.kicad_pcb)
# OPEN_PLAN=1 in the environment checks the layer plan of 2026-09-24 instead of check-in 2's.
# rules copied next to the board -> KiCad DRC -> sensitive-net rules -> layer plan -> netlist parity against the rev5
# schematic -> overlay against the frozen power board v16.
K="/c/Program Files/KiCad/10.0/bin"
q() { grep -v 'image handler\|memory leak' || true; }
N=$1
cp rules/BOOST_control_route.kicad_pro "work/$N.kicad_pro"
cp rules/BOOST_control_route.kicad_dru "work/$N.kicad_dru"
echo "== DRC"
"$K/kicad-cli.exe" pcb drc --severity-all --format json -o "work/$N.drc.json" "work/$N.kicad_pcb" > /dev/null 2>&1
python tools/drc_summary.py "work/$N.drc.json" --brief
echo "== sensitive nets"
"$K/python.exe" tools/sens_check.py "work/$N.kicad_pcb" "work/${N}_sens.json" 2>&1 | q
echo "== layer plan"
"$K/python.exe" tools/card_route_checks.py "work/$N.kicad_pcb" "work/${N}_checks.json" ${OPEN_PLAN:+--open-plan} 2>&1 | q
echo "== parity (rev5 netlist)"
( cd ../replace_2026-09-14/tools/placement &&
  "$K/python.exe" syncboard.py --check "../../../card_route_2026-09-22/work/$N.kicad_pcb" \
      ../../../../BOOST-github/BOOST/BOOST_9-23_rev5.net ../../board_assignment_2026-09-15.json CONTROL 2>&1 | q | tail -1 )
echo "== overlay (power v16)"
"$K/python.exe" ../card_2026-09-17/tools/card_overlay.py "work/$N.kicad_pcb" \
    ../route_2026-09-16/BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb "work/${N}_overlay.json" 2>&1 | q | tail -2
