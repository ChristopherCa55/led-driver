#!/bin/bash
# Gates for a CARD-ONLY step (the power board must be byte-identical to PREV_STEP's): ERC x3, card DRC with refill and
# parity, sync, card export, card pcb_checks and sens_check6. The power board's DRC and every power metric are COPIED
# from PREV_STEP (POWER_CARRIED_OVER.txt says so). Lighter than step_checks.sh, so it can run beside a DC solve.
#
#   bash card_checks.sh STEP_DIR PREV_STEP_DIR
set -u
S="$(cd "${1:?STEP_DIR}" && pwd)"; PV="$(cd "${2:?PREV_STEP_DIR}" && pwd)"
T="$(cd "$(dirname "$0")" && pwd)"
B="$(cd "$T/../.." && pwd)"
K="/c/Program Files/KiCad/10.0/bin"
w() { cygpath -w "$1"; }
KD="$S/kicad"
cmp -s "$KD/BOOST_power_RC2.kicad_pcb" "$PV/kicad/BOOST_power_RC2.kicad_pcb" || { echo "power board differs from $PV: use step_checks.sh"; exit 1; }
t0=$(date +%s)
echo "== ERC"
for p in BOOST BOOST_power_RC2 BOOST_control_RC2; do
  "$K/kicad-cli.exe" sch erc --severity-all -o "$(w "$S/erc_$p.rpt")" "$(w "$KD/$p.kicad_sch")" 2>&1 | grep -i "violations"
done
echo "== DRC card (refill, parity)"
"$K/kicad-cli.exe" pcb drc --refill-zones --schematic-parity --severity-all --format json \
    -o "$(w "$S/drc_BOOST_control_RC2.json")" "$(w "$KD/BOOST_control_RC2.kicad_pcb")" > /dev/null 2>&1
echo "== sync"
python "$(w "$T/sync_check_rf.py")" "$(w "$KD")" > "$S/sync_check.txt" 2>&1; head -1 "$S/sync_check.txt"
echo "== card export"
mkdir -p "$S/scratch_control"
cp "$KD/BOOST_control_RC2.kicad_pcb" "$KD/BOOST_control_RC2.kicad_pro" "$KD/BOOST_control_RC2.kicad_dru" "$KD/fp-lib-table" "$S/scratch_control/"
cp -r "$KD"/*.pretty "$S/scratch_control/"
"$K/python.exe" "$(w "$B/power6_2026-10-01/tools/export_copper6.py")" "$(w "$S/scratch_control/BOOST_control_RC2.kicad_pcb")" "$(w "$S/card_cu.json")" | tail -1
cd "$B"
mkdir -p "$S/checks"
python review_2026-10-10/pcb/pcb_checks.py "$(w "$S/card_cu.json")" card "$(w "$S/checks")" > /dev/null 2>&1
echo "== card sensitive nets"
(cd card6_2026-09-30 && "$K/python.exe" tools/sens_check6.py "$(w "$S/scratch_control/BOOST_control_RC2.kicad_pcb")" \
    "$(w "$S/sens_card.json")" 6now > "$S/sens_card.txt" 2>&1)
echo "== power results carried over from $(basename "$PV")"
for x in drc_BOOST_power_RC2.json power_cu.json power_solve.json power_solve.txt loopL.txt plane_cover.txt sense_cover.txt \
         gate_return.txt sense_offsets.txt thermal_board.txt thermal_bg.txt power_th.json; do
  [ -e "$PV/$x" ] && cp "$PV/$x" "$S/$x"
done
cp "$PV"/checks/power_checks.* "$S/checks/" 2>/dev/null
[ -d "$PV/heatmap" ] && cp -r "$PV/heatmap" "$S/heatmap"
echo "Power-board results (DRC, copper export, solve, loop L, cover / sense / gates, heatmap, power checks) are COPIED from $(basename "$PV"): this step leaves BOOST_power_RC2.kicad_pcb byte-for-byte identical to it (cmp)." > "$S/POWER_CARRIED_OVER.txt"
echo "done in $(( $(date +%s) - t0 )) s"
