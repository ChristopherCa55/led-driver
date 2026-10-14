#!/bin/bash
# Step 5g (= 5f with R106's 5V via at (55.5, 94.4) and a hand-written SDA link): the user's 2026-10-12 retry of the D1 pull-ups as 0603 near J9, on OUT_DIR/kicad (a fresh copy of the
# review copy's KiCad files, made before this runs; nothing else may be in OUT_DIR yet):
#   - schematics: step05e_kicad_sch.py (R99 / R102 1k; R106 / R107 4.7k 0603 with 5V / SCL / SDA labels, the note)
#   - J9: F courtyard = the pad rows' F.Fab outline (board and BOOST.pretty), I2 / SCL F labels up; H3's ref text down
#   - 5V: the F.Cu stretch between the two 5V vias removed, the (55.825, 94.225) via 0.325 mm left + a stub into R106.1,
#         a new via + stub for R107.1 (step05g_5v.json)
#   - R106 / R107 R_0603_1608Metric on F.Cu (make_fp_block.py, add_footprints.py, which also sets R99 / R102 to 1k)
#   - route_new.py: R106.2 -> J9.7 on F; R107.2 -> SDA by step05g_sda.json (F stub, via, In2 to J9.8); kicad-cli
#     refill + save; card_checks.sh vs PREV_STEP
#
#   bash step05g_card.sh OUT_DIR PREV_STEP_DIR
set -u
O="$(cd "${1:?OUT_DIR}" && pwd)"; PV="${2:?PREV_STEP_DIR}"
T="$(cd "$(dirname "$0")" && pwd)"; W="$(cd "$T/../work" && pwd)"
K="/c/Program Files/KiCad/10.0/bin"
w() { cygpath -w "$1"; }
KD="$O/kicad"; P=BOOST_control_RC2
[ -d "$KD" ] || { echo "no $KD"; exit 1; }
[ -e "$O/sch_changes.json" ] && { echo "already built: $O"; exit 1; }
pro0=$(sha256sum "$KD/$P.kicad_pro" | cut -c1-16); dru0=$(sha256sum "$KD/$P.kicad_dru" | cut -c1-16)
rules() { cp "$KD/$P.kicad_pro" "$KD/$P.kicad_dru" "$1/"; }

python "$T/step05e_kicad_sch.py" "$KD" "$O/sch_changes.json" > "$O/sch_changes.log" || exit 1
python "$T/fp_text_edit.py" "$W/specs/step05f_fp_text.json" "$KD" "$O/fp_text.json" > "$O/fp_text.log" || exit 1
mkdir -p "$O/pcb_5v"; rules "$O/pcb_5v"
python "$T/pcb_text_edit.py" "$W/specs/step05g_5v.json" "$KD/$P.kicad_pcb" "$O/pcb_5v/$P.kicad_pcb" || exit 1
"$K/python.exe" "$(w "$T/make_fp_block.py")" "$(w "$W/specs/step05f_fp0603.json")" "$(w "$O/blocks")" || exit 1
python - "$W/specs/step05e_fp_blocks.json" "$O" <<'EOF'
import json, sys
j = json.load(open(sys.argv[1]))
for b in j['blocks']:
    b['block'] = sys.argv[2] + '/blocks/' + b['ref'] + '.block.txt'
json.dump(j, open(sys.argv[2] + '/fp_job.json', 'w'), indent=1)
EOF
mkdir -p "$O/pcb_fp"; rules "$O/pcb_fp"
python "$T/add_footprints.py" "$O/fp_job.json" "$O/pcb_5v/$P.kicad_pcb" "$O/pcb_fp/$P.kicad_pcb" || exit 1
prev="$O/pcb_fp"
for n in scl; do
  "$K/python.exe" "$(w "$T/route_new.py")" "$(w "$prev/$P.kicad_pcb")" "$(w "$W/specs/step05f_route_$n.json")"       "$(w "$O/route_$n.json")" > "$O/route_$n.log" 2>&1 || { cat "$O/route_$n.log"; exit 1; }
  cat "$O/route_$n.log"
  mkdir -p "$O/pcb_$n"; rules "$O/pcb_$n"
  python "$T/pcb_text_edit.py" "$O/route_$n.json" "$prev/$P.kicad_pcb" "$O/pcb_$n/$P.kicad_pcb" || exit 1
  prev="$O/pcb_$n"
done
mkdir -p "$O/pcb_sda"; rules "$O/pcb_sda"
python "$T/pcb_text_edit.py" "$W/specs/step05g_sda.json" "$prev/$P.kicad_pcb" "$O/pcb_sda/$P.kicad_pcb" || exit 1
prev="$O/pcb_sda"
cp "$prev/$P.kicad_pcb" "$KD/$P.kicad_pcb"
"$K/kicad-cli.exe" pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json \
    -o "$(w "$O/drc_save.json")" "$(w "$KD/$P.kicad_pcb")" > "$O/drc_save.log" 2>&1
pro1=$(sha256sum "$KD/$P.kicad_pro" | cut -c1-16); dru1=$(sha256sum "$KD/$P.kicad_dru" | cut -c1-16)
[ "$pro0" = "$pro1" ] && [ "$dru0" = "$dru1" ] || { echo "GUARD: .kicad_pro/.kicad_dru changed"; exit 1; }
python -c "import sys; b=open(sys.argv[1],'rb').read(); print('card PCB lines', b.count(b'\n'), 'CRLF', b.count(b'\r\n'))" \
    "$(w "$KD/$P.kicad_pcb")"
bash "$T/card_checks.sh" "$O" "$PV" > "$O/card_checks.log" 2>&1
cat "$O/card_checks.log"
