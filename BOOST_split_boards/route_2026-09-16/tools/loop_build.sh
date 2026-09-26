#!/bin/sh
# usage: sh tools/loop_build.sh VERSION [passes]   (expects copper_VERSION.json, writes BOOST_power_route_VERSION_NOT_FOR_FAB)
V=$1; N=${2:-5}
K="/c/Program Files/KiCad/10.0/bin"
OUT=BOOST_power_route_${V}_NOT_FOR_FAB
BL=work/${V}_black.json
[ -f "$BL" ] || echo '[]' > "$BL"
i=0
while [ $i -lt $N ]; do
  "$K/python.exe" tools/build_copper.py base_p15.kicad_pcb copper_${V}.json $OUT.kicad_pcb $BL 2>&1 | grep -v 'image handler'
  cp rules/BOOST_power_route.kicad_pro $OUT.kicad_pro
  cp rules/BOOST_power_route.kicad_dru $OUT.kicad_dru
  "$K/kicad-cli.exe" pcb drc --severity-all --format json -o work/${V}.drc.json $OUT.kicad_pcb > /dev/null 2>&1
  before=$(python -c "import json;print(len(json.load(open('$BL'))))")
  python tools/drc_prune.py work/${V}.drc.json $BL
  after=$(python -c "import json;print(len(json.load(open('$BL'))))")
  [ "$before" = "$after" ] && break
  i=$((i+1))
done
