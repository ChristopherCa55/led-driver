#!/bin/sh
# drc.sh NAME: rules beside work board in4plane/NAME.kicad_pcb, then KiCad DRC -> NAME.drc.json and a summary
cd "$(dirname "$0")"
cp rules.kicad_pro "$1.kicad_pro"; cp rules.kicad_dru "$1.kicad_dru"
"/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" pcb drc --severity-all --format json -o "$1.drc.json" "$1.kicad_pcb" > /dev/null 2>&1
python - "$1.drc.json" <<'PY'
import json, sys, collections
d = json.load(open(sys.argv[1]))
c = collections.Counter((v['severity'], v['type']) for v in d['violations'])
print(sys.argv[1], dict(c), 'unconnected', len(d.get('unconnected_items', [])))
PY
