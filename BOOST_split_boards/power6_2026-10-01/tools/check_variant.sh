#!/bin/bash
# Check an edited power board against the moved 6-layer board (A6) and the 8-layer board (L8), on a copy.
#
#   bash check_variant.sh KICAD_DIR TAG [STACK]
#
# KICAD_DIR holds the edited BOOST_power_RC2.kicad_pcb (e.g. BOOST_stuff/KiCad). Everything runs on a copy in
# work/TAG (KiCad writes .kicad_prl files beside any board it loads). STACK defaults to JLC061611-7628D.
# Outputs in work/: TAG/drc.json, TAG_parity.txt, TAG_diff.txt, TAG_area.txt, TAG_cu.json, TAG_solve.json/.txt,
# dumps_TAG/, TAG_compare.txt, TAG_loopL.txt, TAG_cover.txt, TAG_gates.txt, TAG_vialayers.txt, and the heatmap in
# ../heatmap/TAG_*. QUICK=1 stops before the copper solve.
set -u
SRC="$1"; TAG="$2"; STACK="${3:-JLC061611-7628D}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
W="$HERE/work"; T="$HERE/tools"
K="/c/Program Files/KiCad/10.0/bin"
NET="$W/BOOST_now.net"
ASG="$HERE/../previous/2026-09-30/precharge_record/tools/precharge/board_assignment_2026-09-29_precharge.json"
w() { cygpath -w "$1"; }
cd "$W" || exit 1
t0=$(date +%s)
mkdir -p "$TAG"
for f in BOOST_power_RC2.kicad_pcb BOOST_power_RC2.kicad_pro BOOST_power_RC2.kicad_dru BOOST.kicad_sch BOOST.kicad_pro \
         fp-lib-table sym-lib-table ltspice.kicad_sym; do cp "$SRC/$f" "$TAG/"; done
cp -r "$SRC/BOOST.pretty" "$SRC/CSCF3218-6R8MC.pretty" "$TAG/"
sha256sum "$TAG/BOOST_power_RC2.kicad_pcb" | cut -c1-8 > "${TAG}_sha.txt"
echo "== DRC (zones refilled in memory)"
"$K/kicad-cli.exe" pcb drc --refill-zones --severity-all --format json -o "$(w "$TAG/drc.json")" \
    "$(w "$TAG/BOOST_power_RC2.kicad_pcb")" 2>&1 | grep -i 'violation\|unconnected'
python - "$(w "$TAG/drc.json")" "$(w A6/drc_final.json)" <<'EOF'
import json, sys, collections
def sig(p):
    d = json.load(open(p))
    return collections.Counter((v['severity'], v['type']) for v in d['violations']), d['unconnected_items'], d['violations']
n, un, vio = sig(sys.argv[1]); o, _, _ = sig(sys.argv[2])
print('  new:', dict(n), 'unconnected', len(un)); print('  A6 :', dict(o))
for k in sorted(set(n) | set(o)):
    if n[k] != o[k]:
        print('  CHANGED %s: %d -> %d' % (k, o[k], n[k]))
for v in vio:
    if v['severity'] == 'error':
        print('  ERROR', v['type'], v['description'], [i.get('description') for i in v['items']][:2])
for u in un[:20]:
    print('  UNCONNECTED', [i.get('description') for i in u['items']])
EOF
echo "== parity"
"$K/python.exe" "$(w "$HERE/../replace_2026-09-14/tools/placement/syncboard.py")" --check "$(w "$TAG/BOOST_power_RC2.kicad_pcb")" \
    "$(w "$NET")" "$(w "$ASG")" POWER 2>&1 | tail -3 | tee "${TAG}_parity.txt"
echo "== diff vs A6"
"$K/python.exe" "$(w "$HERE/../route_2026-09-16/tools/board_diff.py")" "$(w A6/BOOST_power_RC2.kicad_pcb)" \
    "$(w "$TAG/BOOST_power_RC2.kicad_pcb")" > "${TAG}_diff.txt" 2>&1; tail -40 "${TAG}_diff.txt"
echo "== export"
"$K/python.exe" "$(w "$T/export_copper6.py")" "$(w "$TAG/BOOST_power_RC2.kicad_pcb")" "$(w "${TAG}_cu.json")" 2>&1 | tail -1
python "$(w "$T/area_diff.py")" "$(w A6_cu.json)" "$(w "${TAG}_cu.json")" > "${TAG}_area.txt"; cat "${TAG}_area.txt"
echo "== GND via layers"
"$K/python.exe" "$(w "$T/gnd_via_layers.py")" "$(w "$TAG/BOOST_power_RC2.kicad_pcb")" --list > "${TAG}_vialayers.txt" 2>&1; cat "${TAG}_vialayers.txt"
echo "== signal over GND"
python "$(w "$T/plane_cover.py")" "$(w L8_cu.json)" "$(w A6_cu.json)" "$(w "${TAG}_cu.json")" > "${TAG}_cover.txt" 2>&1; cat "${TAG}_cover.txt"
python "$(w "$T/gate_vertical.py")" "$(w L8_gates.json)" "$(w L8_cu.json)" L8 "$(w A6_cu.json)" JLC061611-7628D \
    "$(w "${TAG}_cu.json")" "$STACK" > "${TAG}_gates.txt" 2>&1
if [ -n "${QUICK:-}" ]; then echo "QUICK: stopping before the solve ($(( $(date +%s) - t0 )) s)"; exit 0; fi
echo "== copper solve (all branches)"
python "$(w "$T/solve_copper6.py")" "$(w "${TAG}_cu.json")" "$(w "$HERE/../route_2026-09-16/branches_power.json")" \
    --stack "$STACK" --out "$(w "${TAG}_solve.json")" --dump "$(w "dumps_${TAG}")" --workers ${WORKERS:-9} > "${TAG}_solve.txt" 2>&1
python "$(w "$T/compare_solves6.py")" L8="$(w L8_solve.json)" A6="$(w A6_solve.json)" "$TAG=$(w "${TAG}_solve.json")" > "${TAG}_compare.txt"
cat "${TAG}_compare.txt"
python "$(w "$T/loop_L6.py")" "$(w "${TAG}_cu.json")" "$(w "dumps_${TAG}")" "$STACK" > "${TAG}_loopL.txt" 2>&1; tail -5 "${TAG}_loopL.txt"
echo "== GND heatmap"
python "$(w "$T/gnd_heatmap.py")" "$(w "${TAG}_cu.json")" "$STACK" "$(w "$HERE/heatmap")" "$TAG" --try 10 --vmax 8.3 \
    > "$HERE/heatmap/${TAG}.log" 2>&1; head -8 "$HERE/heatmap/${TAG}.log"
echo "done in $(( $(date +%s) - t0 )) s"
