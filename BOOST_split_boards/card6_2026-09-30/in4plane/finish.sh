#!/bin/sh
# In4-plane finishing (run from card6_2026-09-30/):  sh in4plane/finish.sh ROUTES.json NAME
# base2 + routes -> join via / track-end links KiCad would not count (fix_tangent) -> prune dangling copper -> DRC
K="/c/Program Files/KiCad/10.0/bin"
q() { grep -v 'image handler\|memory leak' || true; }
R=$1; N=$2; W=in4plane
"$K/python.exe" tools/add_routes.py $W/base2.kicad_pcb "$R" "$W/$N.kicad_pcb" 2>&1 | q | tail -1
sh $W/drc.sh "$N"
"$K/python.exe" tools/fix_tangent.py "$W/$N.kicad_pcb" "$W/${N}_links.json" "$W/$N.drc.json" 2>&1 | q | tail -1
"$K/python.exe" tools/edit_copper.py "$W/$N.kicad_pcb" "$W/${N}_links.json" "$W/$N.kicad_pcb" 2>&1 | q | tail -1
sh $W/drc.sh "$N"
for i in $(seq 1 12); do
  n=$(python -c "import json; print(sum(v['type'] in ('track_dangling','via_dangling') for v in json.load(open('$W/$N.drc.json'))['violations']))")
  [ "$n" = "0" ] && break
  "$K/python.exe" tools/prune_dangling.py "$W/$N.kicad_pcb" "$W/$N.drc.json" "$W/$N.kicad_pcb" 2>&1 | q > /dev/null
  sh $W/drc.sh "$N"
done
