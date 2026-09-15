#!/bin/sh
# Placement pipeline: big-part layout -> small parts -> KiCad board -> table, plots, DRC summary.
#   sh run_place.sh BIG.json NAME
# BIG.json: optimizer output plus J10, H5-H8 ("layout"), "standoffs", "card", "screwed".
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"
BIG=$1
NAME=$2
K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
KP="/c/Program Files/KiCad/10.0/bin/python.exe"
INK="/c/Program Files/Inkscape/bin/inkscape.exe"

SHIPPED_PRO="C:/Users/Dominick Junior/Downloads/UCSD Stuff/2025-2026/robotx/led-driver/BOOST_split_boards/BOOST_power.kicad_pro"

python psat.py "$BIG" psat_cfg.json "$NAME.full.json"      # exits 3 if any part could not be placed
# the shipped project carries the netclasses, netclass patterns, rules and severities; the synced one lost them
cp "$SHIPPED_PRO" "$NAME.kicad_pro"
"$KP" papply.py wip_NOT_FOR_FAB/power_sync2.kicad_pcb "$NAME.full.json" "$NAME.kicad_pcb"
cp "$SHIPPED_PRO" "$NAME.kicad_pro"      # SaveBoard rewrites the .kicad_pro; restore the shipped rules before DRC
GOALS=${3:-}      # optional optimizer config whose 'goals' add the agreed-goal column
if [ -n "$GOALS" ]; then
    python ptable.py "$NAME.full.json" "$NAME.distances.md" --goals="$GOALS" > /dev/null
else
    python ptable.py "$NAME.full.json" "$NAME.distances.md" > /dev/null
fi
tail -1 "$NAME.distances.md"
"$K" pcb export svg --layers "F.Cu,F.CrtYd,F.Fab,Edge.Cuts,User.Eco1,User.Comments" --mode-single --page-size-mode 2 \
    --exclude-drawing-sheet -o "$NAME.top.svg" "$NAME.kicad_pcb" > /dev/null
"$K" pcb export svg --layers "B.Cu,B.CrtYd,B.Fab,Edge.Cuts,User.Eco1" --mode-single --page-size-mode 2 \
    --exclude-drawing-sheet -o "$NAME.bottom.svg" "$NAME.kicad_pcb" > /dev/null
for s in top bottom; do
    "$INK" "$NAME.$s.svg" --export-type=png --export-filename="$NAME.$s.png" --export-dpi=220 --export-background=white > /dev/null 2>&1
done
"$K" pcb drc --severity-all --format json -o "$NAME.drc.json" "$NAME.kicad_pcb" > /dev/null
python pdrc.py "$NAME.drc.json"
