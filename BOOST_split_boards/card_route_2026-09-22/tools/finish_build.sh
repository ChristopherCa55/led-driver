#!/bin/sh
# Build a finishing-stage board (run from card_route_2026-09-22/):  tools/finish_build.sh ROUTES.json NAME
# base_c3o + routes -> link vias/track ends KiCad would not count as joined (fix_tangent.py) -> prune dangling copper
# until none is left -> work/NAME.kicad_pcb with the rules beside it and its DRC report.
K="/c/Program Files/KiCad/10.0/bin"
q() { grep -v 'image handler\|memory leak' || true; }
rules() { cp rules/BOOST_control_route.kicad_pro "work/$1.kicad_pro"; cp rules/BOOST_control_route.kicad_dru "work/$1.kicad_dru"; }
drc() { "$K/kicad-cli.exe" pcb drc --severity-all --format json -o "work/$1.drc.json" "work/$1.kicad_pcb" > /dev/null 2>&1; }
R=$1; N=$2
"$K/python.exe" tools/add_routes.py work/base_c3o.kicad_pcb "$R" "work/$N.kicad_pcb" 2>&1 | q | tail -1
rules "$N"; drc "$N"
"$K/python.exe" tools/fix_tangent.py "work/$N.kicad_pcb" "work/${N}_links.json" "work/$N.drc.json" 2>&1 | q | tail -1
"$K/python.exe" tools/edit_copper.py "work/$N.kicad_pcb" "work/${N}_links.json" "work/$N.kicad_pcb" 2>&1 | q | tail -1
rules "$N"; drc "$N"
for i in $(seq 1 20); do
  n=$(python -c "import json; print(sum(v['type'] in ('track_dangling','via_dangling') for v in json.load(open('work/$N.drc.json'))['violations']))")
  [ "$n" = "0" ] && break
  "$K/python.exe" tools/prune_dangling.py "work/$N.kicad_pcb" "work/$N.drc.json" "work/$N.kicad_pcb" 2>&1 | q > /dev/null
  rules "$N"; drc "$N"
done
python tools/drc_summary.py "work/$N.drc.json"
