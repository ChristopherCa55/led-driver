#!/bin/bash
# Card plane-splitter experiment (user, 2026-10-12: "place them in the location that would affect other stuff the
# least"): on a scratch copy of PREV_KICAD, remove a span (REMOVE_SPEC, pcb_text_edit), refill so the planes heal,
# re-route it with route_new.py and its fill_cost (ROUTE_JOB), refill again, then card gates (card_checks.sh vs PREV_STEP).
# Nothing is promoted; OUT must not exist.
#
#   bash try_reroute.sh OUT PREV_KICAD PREV_STEP REMOVE_SPEC.json ROUTE_JOB.json
set -u
O="${1:?OUT}"; PK="$(cd "${2:?PREV_KICAD}" && pwd)"; PS="${3:?PREV_STEP}"; RS="${4:?REMOVE_SPEC}"; RJ="${5:?ROUTE_JOB}"
T="$(cd "$(dirname "$0")" && pwd)"
K="/c/Program Files/KiCad/10.0/bin"
w() { cygpath -w "$1"; }
P=BOOST_control_RC2
[ -e "$O" ] && { echo "OUT exists: $O"; exit 1; }
mkdir -p "$O/kicad" "$O/healed"; O="$(cd "$O" && pwd)"
(cd "$PK" && for x in *; do case "$x" in "~"*|*.kicad_prl|*.lck) ;; *) cp -r "$x" "$O/kicad/";; esac; done)
pro0=$(sha256sum "$O/kicad/$P.kicad_pro" | cut -c1-16); dru0=$(sha256sum "$O/kicad/$P.kicad_dru" | cut -c1-16)
cp "$RS" "$O/remove_spec.json"; cp "$RJ" "$O/route_job.json"
cp "$O/kicad/$P.kicad_pro" "$O/kicad/$P.kicad_dru" "$O/healed/"
python "$T/pcb_text_edit.py" "$RS" "$O/kicad/$P.kicad_pcb" "$O/healed/$P.kicad_pcb" || exit 1
"$K/kicad-cli.exe" pcb drc --refill-zones --save-board --severity-all --format json \
    -o "$(w "$O/healed/drc.json")" "$(w "$O/healed/$P.kicad_pcb")" > "$O/healed/drc.log" 2>&1
"$K/python.exe" "$(w "$T/route_new.py")" "$(w "$O/healed/$P.kicad_pcb")" "$(w "$RJ")" "$(w "$O/route_spec.json")" \
    > "$O/route.log" 2>&1 || { cat "$O/route.log"; exit 1; }
cat "$O/route.log"
python "$T/pcb_text_edit.py" "$O/route_spec.json" "$O/healed/$P.kicad_pcb" "$O/routed.kicad_pcb" || exit 1
cp "$O/routed.kicad_pcb" "$O/kicad/$P.kicad_pcb"
"$K/kicad-cli.exe" pcb drc --refill-zones --save-board --schematic-parity --severity-all --format json \
    -o "$(w "$O/drc_save.json")" "$(w "$O/kicad/$P.kicad_pcb")" > "$O/drc_save.log" 2>&1
pro1=$(sha256sum "$O/kicad/$P.kicad_pro" | cut -c1-16); dru1=$(sha256sum "$O/kicad/$P.kicad_dru" | cut -c1-16)
[ "$pro0" = "$pro1" ] && [ "$dru0" = "$dru1" ] || { echo "GUARD: .kicad_pro/.kicad_dru changed"; exit 1; }
cat "$O/drc_save.log" | head -4
bash "$T/card_checks.sh" "$O" "$PS" > "$O/card_checks.log" 2>&1
tail -3 "$O/card_checks.log"
