#!/bin/sh
# Freerouting chain on one placement (run from card_route_2026-09-22/):
#   tools/fr_chain.sh TAG PLACE.json PASSES [extra route_card options]
# base board work/base_TAG.kicad_pcb (prep_card.py, set_stackup.py, refilled with the rules beside it) ->
# 1. pre-route with my router (sensitive nets, other comparator inputs, stitching, decoupling, fan-outs, zone nets)
# 2. DSN (make_dsn.py, the 2026-09-24 open layer plan) -> Freerouting headless -> SES import (pre-routes re-added,
#    the sensitive nets checked item by item)
# 3. my router's repair rounds and dangling-end pruning (route_pipeline_opts.sh) from that board
# Options for route_card.py (e.g. --no-verr-block) follow PASSES; --open-plan is always on.
set -e
K="/c/Program Files/KiCad/10.0/bin"
FR="/c/Users/bubba/AppData/Local/freerouting/freerouting.exe"
TAG=$1; PLACE=$2; PASSES=$3; shift 3; EXTRA="$*"
q() { grep -v 'image handler\|memory leak' || true; }
rules() { cp rules/BOOST_control_route.kicad_pro "work/$1.kicad_pro"; cp rules/BOOST_control_route.kicad_dru "work/$1.kicad_dru"; }
drc() { "$K/kicad-cli.exe" pcb drc --severity-all --format json -o "work/$1.drc.json" "work/$1.kicad_pcb" > /dev/null 2>&1 || true; }
echo "== pre-route $TAG ($(date +%H:%M))"
python -u tools/route_card.py "work/base_${TAG}_cu.json" "work/pre_$TAG.json" --pre --open-plan --match "$PLACE" $EXTRA \
    > "work/pre_$TAG.log" 2>&1
tail -1 "work/pre_$TAG.log"
"$K/python.exe" tools/add_routes.py "work/base_$TAG.kicad_pcb" "work/pre_$TAG.json" "work/pre_$TAG.kicad_pcb" 2>&1 | q | tail -1
rules "pre_$TAG"; drc "pre_$TAG"
python tools/drc_summary.py "work/pre_$TAG.drc.json" --brief
echo "== DSN + Freerouting $PASSES passes ($(date +%H:%M))"
"$K/python.exe" tools/make_dsn.py "work/pre_$TAG.kicad_pcb" "work/fr/$TAG.dsn" "work/fr/${TAG}_dsn.json" \
    "work/pre_$TAG.drc.json" --open-plan 2>&1 | q | head -1
( cd work/fr && timeout 9000 "$FR" -de "$TAG.dsn" -do "$TAG.ses" -mp "$PASSES" -da --gui.enabled=false \
    --router.automatic_neckdown=false --router.optimizer.enabled=false > "${TAG}_fr.log" 2>&1 || true )
grep -h "Auto-routing stage completed" "work/fr/${TAG}_fr.log" | cut -c30-200 || true
echo "== import ($(date +%H:%M))"
"$K/python.exe" tools/import_ses.py "work/pre_$TAG.kicad_pcb" "work/fr/$TAG.ses" "work/fr_$TAG.kicad_pcb" \
    "work/fr/${TAG}_import.json" "work/fr/$TAG.dsn" 2>&1 | q | python -c "
import json, sys; r = json.load(sys.stdin)
print({k: r[k] for k in ('session_items_on_sensitive_nets_removed', 'session_tracks_widened_to_0p13', 'net_flips',
                         'sensitive_identical_to_pre')})"
rules "fr_$TAG"; drc "fr_$TAG"
python tools/drc_summary.py "work/fr_$TAG.drc.json" --brief
"$K/python.exe" tools/board_routes.py "work/fr_$TAG.kicad_pcb" "work/pre_$TAG.json" "work/fr/${TAG}_routes.json" 2>&1 | q
echo "== repair ($(date +%H:%M))"
PLACE="$PLACE" ROUTE_OPTS="--open-plan $EXTRA" tools/route_pipeline_opts.sh "work/base_$TAG.kicad_pcb" "${TAG}f" \
    "work/fr/${TAG}_routes.json"
echo "== done ($(date +%H:%M))"
