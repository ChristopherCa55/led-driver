#!/bin/sh
# Card placement check (run from card_2026-09-17/): apply a layout, then overlay against the frozen power board,
# DRC and the distance / height report. Stops at the first failing stage.
#
# usage: tools/check_card.sh CONFIG.json LAYOUT.json NAME
# writes work/NAME.kicad_pcb (+ the shipped BOOST_control.kicad_pro), work/NAME_overlay.json, work/NAME.drc.json,
# work/NAME_check.md, work/NAME_check.png
set -e -o pipefail
CFG=$1; LAY=$2; NAME=$3
K="/c/Program Files/KiCad/10.0/bin/python.exe"
CLI="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
V16=../route_2026-09-16/BOOST_power_route_v16_NOT_FOR_FAB.kicad_pcb
q() { grep -v 'image handler\|memory leak' || true; }
echo "== apply"
"$K" tools/apply_layout.py work/card_frame4.kicad_pcb "$LAY" work/inv_control4.json work/$NAME.kicad_pcb 2>&1 | q
cp ../BOOST_control.kicad_pro work/$NAME.kicad_pro
echo "== overlay against v16"
"$K" tools/card_overlay.py work/$NAME.kicad_pcb $V16 work/${NAME}_overlay.json 2>&1 | q
"$K" -c "import json,sys; r = json.load(open('work/${NAME}_overlay.json')); print('overlay: %d of %d pass' % (len(r['rows']) - r['failed'], len(r['rows']))); sys.exit(1 if r['failed'] else 0)"
echo "== DRC"
"$CLI" pcb drc --format json --severity-all -o work/$NAME.drc.json work/$NAME.kicad_pcb > /dev/null 2>&1 || true
python tools/drc_place.py work/$NAME.drc.json
echo "== distances and heights"
PYTHONIOENCODING=utf-8 python tools/card_check.py "$CFG" "$LAY" work/${NAME}_check.md work/${NAME}_check.png > /dev/null
echo "check report: work/${NAME}_check.md"
