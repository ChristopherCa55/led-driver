#!/bin/bash
# Step 5, KiCad side of the user's D1 / D2 answers, on a fresh scratch copy (OUT must not exist):
#   - schematics: step05_kicad_sch.py (R99 / R102 1k; R106 / R107 4.7k pull-ups with 5V / SCL / SDA labels, a note)
#   - card PCB:   R106 / R107 0402 footprints from KiCad's library (make_fp_block.py, add_footprints.py, which also sets
#                 R99 / R102 to 1k), routed by route_new.py, applied by pcb_text_edit.py, refilled and saved by kicad-cli
#   - then every gate (step_checks.sh; the power board is untouched in this step, so SKIP_SOLVE / SKIP_HEAT may be set)
#
#   bash step05_card.sh PREV_KICAD_DIR OUT_DIR        (env passed on to step_checks.sh)
set -u
P="$(cd "${1:?PREV_KICAD_DIR}" && pwd)"; O="${2:?OUT_DIR}"
T="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$T/../work" && pwd)"
K="/c/Program Files/KiCad/10.0/bin"
[ -e "$O" ] && { echo "OUT exists: $O"; exit 1; }
mkdir -p "$O/kicad"; O="$(cd "$O" && pwd)"
(cd "$P" && for x in *; do case "$x" in "~"*|*.kicad_prl|*.lck) ;; *) cp -r "$x" "$O/kicad/";; esac; done)
pro0=$(sha256sum "$O/kicad/BOOST_control_RC2.kicad_pro" | cut -c1-16); dru0=$(sha256sum "$O/kicad/BOOST_control_RC2.kicad_dru" | cut -c1-16)
python "$T/step05_kicad_sch.py" "$O/kicad" "$O/sch_changes.json" > "$O/sch_changes.log" || exit 1
"$K/python.exe" "$(cygpath -w "$T/make_fp_block.py")" "$(cygpath -w "$W/specs/step05_fp0402.json")" "$(cygpath -w "$O/blocks")" || exit 1
python - "$W/specs/step05_fp_blocks.json" "$O" <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
for b in j['blocks']:
    b['block'] = sys.argv[2] + '/blocks/' + b['ref'] + '.block.txt'
json.dump(j, open(sys.argv[2] + '/fp_job.json', 'w'), indent=1)
EOF
mkdir -p "$O/pcb_fp"; cp "$O/kicad/BOOST_control_RC2.kicad_pro" "$O/kicad/BOOST_control_RC2.kicad_dru" "$O/pcb_fp/"
python "$T/add_footprints.py" "$O/fp_job.json" "$O/kicad/BOOST_control_RC2.kicad_pcb" "$O/pcb_fp/BOOST_control_RC2.kicad_pcb" || exit 1
"$K/python.exe" "$(cygpath -w "$T/route_new.py")" "$(cygpath -w "$O/pcb_fp/BOOST_control_RC2.kicad_pcb")" \
    "$(cygpath -w "$W/specs/step05_route.json")" "$(cygpath -w "$O/route_spec.json")" > "$O/route.log" 2>&1 || { cat "$O/route.log"; exit 1; }
cat "$O/route.log"
python "$T/pcb_text_edit.py" "$O/route_spec.json" "$O/pcb_fp/BOOST_control_RC2.kicad_pcb" "$O/routed.kicad_pcb" || exit 1
cp "$O/routed.kicad_pcb" "$O/kicad/BOOST_control_RC2.kicad_pcb"
"$K/kicad-cli.exe" pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json \
    -o "$(cygpath -w "$O/drc_save.json")" "$(cygpath -w "$O/kicad/BOOST_control_RC2.kicad_pcb")" > "$O/drc_save.log" 2>&1
pro1=$(sha256sum "$O/kicad/BOOST_control_RC2.kicad_pro" | cut -c1-16); dru1=$(sha256sum "$O/kicad/BOOST_control_RC2.kicad_dru" | cut -c1-16)
[ "$pro0" = "$pro1" ] && [ "$dru0" = "$dru1" ] || { echo "GUARD: .kicad_pro/.kicad_dru changed"; exit 1; }
python -c "import sys; b=open(sys.argv[1],'rb').read(); print('card PCB lines', b.count(b'\n'), 'CRLF', b.count(b'\r\n'))" \
    "$(cygpath -w "$O/kicad/BOOST_control_RC2.kicad_pcb")"
bash "$T/step_checks.sh" "$O" > "$O/step_checks.log" 2>&1
cat "$O/step_checks.log"
