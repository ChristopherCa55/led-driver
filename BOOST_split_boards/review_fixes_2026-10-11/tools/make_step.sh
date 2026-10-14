#!/bin/bash
# One copper step on a fresh scratch copy (FIX_PROMPT: one change at a time, then every gate).
#
#   bash make_step.sh STEP_DIR PREV_KICAD_DIR BOARD SPEC.json [SPEC2.json ...]      env passed on to step_checks.sh
#
# BOARD = power | control. STEP_DIR must not exist. PREV_KICAD_DIR is the previous step's kicad/ folder (lock files
# and .kicad_prl are not copied). Each spec is applied with pcb_text_edit.py into a NEW file (STEP/edited_N.kicad_pcb),
# the result is refilled and saved by kicad-cli (DRC --refill-zones --save-board), then the guards run:
# .kicad_pro / .kicad_dru unchanged (SaveBoard drops netclasses), every line CRLF, and step_checks.sh.
set -u
S="${1:?STEP_DIR}"; P="${2:?PREV_KICAD_DIR}"; BRD="${3:?power|control}"; shift 3
T="$(cd "$(dirname "$0")" && pwd)"
K="/c/Program Files/KiCad/10.0/bin/kicad-cli.exe"
[ -e "$S" ] && { echo "STEP_DIR exists: $S"; exit 1; }
[ -f "$P/BOOST_power_RC2.kicad_pcb" ] || { echo "no board in $P"; exit 1; }
f=BOOST_${BRD}_RC2; [ "$BRD" = power ] || f=BOOST_control_RC2
mkdir -p "$S/kicad"
S="$(cd "$S" && pwd)"; P="$(cd "$P" && pwd)"
(cd "$P" &&for x in *; do case "$x" in "~"*|*.kicad_prl|*.lck) ;; *) cp -r "$x" "$S/kicad/";; esac; done)
pro0=$(sha256sum "$S/kicad/$f.kicad_pro" | cut -c1-16); dru0=$(sha256sum "$S/kicad/$f.kicad_dru" | cut -c1-16)
cur="$S/kicad/$f.kicad_pcb"; n=0
for spec in "$@"; do
  n=$((n + 1))
  cp "$spec" "$S/spec_$n.json"
  python "$T/pcb_text_edit.py" "$spec" "$cur" "$S/edited_$n.kicad_pcb" || { echo "edit $n failed"; exit 1; }
  cur="$S/edited_$n.kicad_pcb"
done
cp "$cur" "$S/kicad/$f.kicad_pcb"
"$K" pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json \
    -o "$(cygpath -w "$S/drc_save.json")" "$(cygpath -w "$S/kicad/$f.kicad_pcb")" > "$S/drc_save.log" 2>&1
pro1=$(sha256sum "$S/kicad/$f.kicad_pro" | cut -c1-16); dru1=$(sha256sum "$S/kicad/$f.kicad_dru" | cut -c1-16)
[ "$pro0" = "$pro1" ] && [ "$dru0" = "$dru1" ] || { echo "GUARD: .kicad_pro/.kicad_dru changed ($pro0 $pro1 $dru0 $dru1)"; exit 1; }
# (Git Bash's grep -c $'\r' counts every line, so count bytes in Python)
read -r crlf lines < <(python -c "import sys; b=open(sys.argv[1],'rb').read(); print(b.count(b'\r\n'), b.count(b'\n'))" \
    "$(cygpath -w "$S/kicad/$f.kicad_pcb")" | tr -d '\r')
[ "$lines" = "$crlf" ] || echo "WARNING: $crlf of $lines lines CRLF"
echo "saved $f: $lines lines ($crlf CRLF), .kicad_pro/.kicad_dru unchanged"
if [ -n "${NO_CHECKS:-}" ]; then echo "NO_CHECKS: run step_checks.sh or card_checks.sh yourself"; exit 0; fi
bash "$T/step_checks.sh" "$S" > "$S/step_checks.log" 2>&1
cat "$S/step_checks.log"
