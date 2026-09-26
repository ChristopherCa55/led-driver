#!/bin/sh
# Rebuild the card from the schematic netlist after a footprint change (run from card_2026-09-17/):
# J9 footprint -> control_sync4 (from control_sync3) -> parity -> inventory -> frame board.
set -e
K="/c/Program Files/KiCad/10.0/bin/python.exe"
q() { grep -v 'image handler\|memory leak' || true; }
NET=../../../../BOOST-github/BOOST/BOOST_9-23_rev5.net   # rev5 (2026-09-23): J9.9 5V -> 12V
A=../../board_assignment_2026-09-15.json
python tools/make_wirepads_fp.py ../../BOOST-github/BOOST/BOOST.pretty/WirePads_11_Staggered_P1.27mm_Drill1.0mm_TieSlots.kicad_mod
( cd ../replace_2026-09-14/tools/placement
  "$K" syncboard.py wip_NOT_FOR_FAB/control_sync3.kicad_pcb $NET $A CONTROL wip_NOT_FOR_FAB/control_sync4.kicad_pcb 2>&1 | q | tail -1
  cp ../../../BOOST_control.kicad_pro wip_NOT_FOR_FAB/control_sync4.kicad_pro
  "$K" syncboard.py --check wip_NOT_FOR_FAB/control_sync4.kicad_pcb $NET $A CONTROL 2>&1 | q | tail -1
  "$K" fpinventory.py $NET $A CONTROL ../../../card_2026-09-17/work/inv_control4.json 2>&1 | q | grep -c . > /dev/null )
"$K" tools/card_frame.py ../replace_2026-09-14/tools/placement/wip_NOT_FOR_FAB/control_sync4.kicad_pcb work/power_v16_anchor.json work/card_frame4.kicad_pcb 2>&1 | q | tail -1
"$K" tools/update_j9.py work/card_frame4.kicad_pcb ../../BOOST-github/BOOST/BOOST.pretty work/card_frame4.kicad_pcb 2>&1 | q | tail -1   # J9 labels (2026-09-22)
cp ../BOOST_control.kicad_pro work/card_frame4.kicad_pro
