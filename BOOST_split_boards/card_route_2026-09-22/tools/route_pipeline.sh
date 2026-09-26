#!/bin/sh
# Control card routing pipeline (run from card_route_2026-09-22/):
#   tools/route_pipeline.sh BASE_BOARD TAG [FIRST_ROUTES.json]
# 1. export BASE_BOARD copper and route every net -> work/r_TAG.json (or take FIRST_ROUTES.json)
# 2. up to six repair rounds: add the routes to BASE_BOARD, refill, DRC; while anything is unconnected or in error,
#    export the routed board and route again with the earlier routes loaded (rip-able) and all zone shapes taken from
#    the refilled routed board, so fill fragments cut by routes show up as islands to join -> work/g_TAG_i.json
# 3. prune dangling track ends and vias, re-checking DRC
# Every board written here gets the rules (shipped .kicad_pro, tightening .kicad_dru) copied next to it before DRC.
set -e
K="/c/Program Files/KiCad/10.0/bin"
BASE=$1; TAG=$2
MATCH="--match ../card_2026-09-17/work/place_c2.json"
q() { grep -v 'image handler\|memory leak' || true; }
rules() { cp rules/BOOST_control_route.kicad_pro "work/$1.kicad_pro"; cp rules/BOOST_control_route.kicad_dru "work/$1.kicad_dru"; }
drc() { "$K/kicad-cli.exe" pcb drc --severity-all --format json -o "work/$1.drc.json" "work/$1.kicad_pcb" > /dev/null 2>&1 || true; }
count() { python -c "import json; r=json.load(open('work/$1.drc.json')); print(sum(v['severity']=='error' for v in r['violations']) + len(r['unconnected_items']))"; }

"$K/python.exe" tools/export_copper.py "$BASE" "work/base_${TAG}_cu.json" 2>&1 | q
if [ -n "$3" ]; then
  R="$3"
else
  python -u tools/route_card.py "work/base_${TAG}_cu.json" "work/r_${TAG}.json" $MATCH > "work/r_${TAG}.log" 2>&1
  tail -1 "work/r_${TAG}.log"
  R="work/r_${TAG}.json"
fi
for i in 1 2 3 4 5 6; do
  B="sig_${TAG}_$i"
  "$K/python.exe" tools/add_routes.py "$BASE" "$R" "work/$B.kicad_pcb" 2>&1 | q
  rules "$B"; drc "$B"
  python tools/drc_summary.py "work/$B.drc.json" --brief
  [ "$(count "$B")" = "0" ] && break
  "$K/python.exe" tools/export_copper.py "work/$B.kicad_pcb" "work/${B}_cu.json" 2>&1 | q
  python -u tools/route_card.py "work/base_${TAG}_cu.json" "work/g_${TAG}_$i.json" $MATCH \
      --routes "$R" --zones "work/${B}_cu.json" > "work/g_${TAG}_$i.log" 2>&1
  tail -1 "work/g_${TAG}_$i.log"
  R="work/g_${TAG}_$i.json"
done
cur="$B"
python tools/drc_summary.py "work/$cur.drc.json"
for i in 1 2 3 4 5; do
  n=$(python -c "import json; print(sum(v['type'] in ('track_dangling', 'via_dangling') for v in json.load(open('work/$cur.drc.json'))['violations']))")
  [ "$n" = "0" ] && break
  "$K/python.exe" tools/prune_dangling.py "work/$cur.kicad_pcb" "work/$cur.drc.json" "work/sig_${TAG}p.kicad_pcb" 2>&1 | q
  cur="sig_${TAG}p"
  rules "$cur"; drc "$cur"
  python tools/drc_summary.py "work/$cur.drc.json"
done
echo "routes: $R"
echo "final: work/$cur.kicad_pcb"
