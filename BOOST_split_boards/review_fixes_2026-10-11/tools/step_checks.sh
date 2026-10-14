#!/bin/bash
# Every gate and metric for one step (FIX_PROMPT 4.3 / 8.2), on the KiCad folder STEP/kicad (a scratch copy; KiCad
# writes .kicad_prl files there). Outputs go into STEP/. Then: python collect.py ... to update METRICS.md.
#
#   bash step_checks.sh STEP_DIR            env: SKIP_SOLVE=1, SKIP_HEAT=1, THERMAL=1 (U16 model, ~6 min),
#                                            WORKERS=n (DC solve processes, default 9; fewer when RAM is short)
#
# Tools (headers read before use): kicad-cli ERC/DRC, kicad_sheets_2026-10-09/tools/sync_check.py (via sync_check_rf.py),
# power6_2026-10-01/tools/{export_copper6,solve_copper6,loop_L6,plane_cover,gnd_heatmap,thermal6}.py,
# review_2026-10-10/pcb/pcb_checks.py, card6_2026-09-30/tools/sens_check6.py, and this folder's sense_cover.py,
# gates_all.sh, sense_offsets.py.
set -u
S="$(cd "${1:?STEP_DIR}" && pwd)"
T="$(cd "$(dirname "$0")" && pwd)"
B="$(cd "$T/../.." && pwd)"                       # BOOST_split_boards
K="/c/Program Files/KiCad/10.0/bin"
w() { cygpath -w "$1"; }
KD="$S/kicad"
[ -f "$KD/BOOST_power_RC2.kicad_pcb" ] || { echo "no $KD/BOOST_power_RC2.kicad_pcb"; exit 1; }
t0=$(date +%s)
echo "== ERC"
for p in BOOST BOOST_power_RC2 BOOST_control_RC2; do
  "$K/kicad-cli.exe" sch erc --severity-all -o "$(w "$S/erc_$p.rpt")" "$(w "$KD/$p.kicad_sch")" 2>&1 | grep -i "violations"
done
echo "== DRC (refill, parity)"
for b in BOOST_power_RC2 BOOST_control_RC2; do
  "$K/kicad-cli.exe" pcb drc --refill-zones --schematic-parity --severity-all --format json -o "$(w "$S/drc_$b.json")" \
      "$(w "$KD/$b.kicad_pcb")" > /dev/null 2>&1
done
echo "== sync"
python "$(w "$T/sync_check_rf.py")" "$(w "$KD")" > "$S/sync_check.txt" 2>&1; head -1 "$S/sync_check.txt"
echo "== exports (scratch copies, zones refilled in memory)"
for b in power control; do
  mkdir -p "$S/scratch_$b"
  f=BOOST_${b}_RC2; [ "$b" = power ] || f=BOOST_control_RC2
  cp "$KD/$f.kicad_pcb" "$KD/$f.kicad_pro" "$KD/$f.kicad_dru" "$KD/fp-lib-table" "$S/scratch_$b/"
  cp -r "$KD"/*.pretty "$S/scratch_$b/"
done
"$K/python.exe" "$(w "$B/power6_2026-10-01/tools/export_copper6.py")" "$(w "$S/scratch_power/BOOST_power_RC2.kicad_pcb")" "$(w "$S/power_cu.json")" | tail -1
"$K/python.exe" "$(w "$B/power6_2026-10-01/tools/export_copper6.py")" "$(w "$S/scratch_control/BOOST_control_RC2.kicad_pcb")" "$(w "$S/card_cu.json")" | tail -1
cd "$B"
if [ -z "${SKIP_SOLVE:-}" ]; then
  echo "== DC solve"
  python power6_2026-10-01/tools/solve_copper6.py "$(w "$S/power_cu.json")" "$(w route_2026-09-16/branches_power.json)" \
      --stack JLC061611-7628D --out "$(w "$S/power_solve.json")" --dump "$(w "$S/dumps")" --workers "${WORKERS:-9}" > "$S/power_solve.txt" 2>&1
  python power6_2026-10-01/tools/loop_L6.py "$(w "$S/power_cu.json")" "$(w "$S/dumps")" JLC061611-7628D > "$S/loopL.txt" 2>&1
  mkdir -p "$S/checks"
  python review_2026-10-10/pcb/pcb_checks.py "$(w "$S/power_cu.json")" power "$(w "$S/checks")" --solve "$(w "$S/dumps")" \
      route_2026-09-16/branches_power.json > /dev/null 2>&1
fi
mkdir -p "$S/checks"
python review_2026-10-10/pcb/pcb_checks.py "$(w "$S/card_cu.json")" card "$(w "$S/checks")" > /dev/null 2>&1
echo "== cover, sense, gates"
python power6_2026-10-01/tools/plane_cover.py "$(w "$S/power_cu.json")" > "$S/plane_cover.txt"
python "$(w "$T/sense_cover.py")" "$(w "$S/power_cu.json")" > "$S/sense_cover.txt"
bash "$T/gates_all.sh" "$(w "$S/power_cu.json")" > "$S/gate_return.txt"
if [ -z "${SKIP_HEAT:-}" ]; then
  echo "== GND heatmap"
  mkdir -p "$S/heatmap"
  python power6_2026-10-01/tools/gnd_heatmap.py "$(w "$S/power_cu.json")" JLC061611-7628D "$(w "$S/heatmap")" step --vmax 8.3 \
      > "$S/heatmap/step.log" 2>&1
  python "$(w "$T/sense_offsets.py")" "$(w "$S/power_cu.json")" "$(w "$S/heatmap/step_gndV.npz")" > "$S/sense_offsets.txt"
fi
echo "== card sensitive nets"
(cd card6_2026-09-30 && "$K/python.exe" tools/sens_check6.py "$(w "$S/scratch_control/BOOST_control_RC2.kicad_pcb")" \
    "$(w "$S/sens_card.json")" 6now > "$S/sens_card.txt" 2>&1)
if [ -n "${THERMAL:-}" ]; then
  echo "== U16 thermal"
  (cd u16_thermal_2026-10-01 && "$K/python.exe" tools/export_copper.py "$(w "$S/scratch_power/BOOST_power_RC2.kicad_pcb")" \
      "$(w "$S/power_th.json")" > /dev/null 2>&1 && \
   python ../power6_2026-10-01/tools/thermal6.py board "$(w "$S/power_th.json")" JLC061611-7628D 10 > "$S/thermal_board.txt" 2>&1 && \
   python ../power6_2026-10-01/tools/thermal6.py background "$(w "$S/power_th.json")" JLC061611-7628D 10 > "$S/thermal_bg.txt" 2>&1)
fi
echo "done in $(( $(date +%s) - t0 )) s"
