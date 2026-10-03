#!/bin/sh
# Fabrication outputs for one board (run from fab_2026-09-30/):  tools/make_fab.sh BOARD.kicad_pcb OUTDIR NAME
# The board's .kicad_pro / .kicad_dru must sit beside it. Refuses to plot unless KiCad DRC on the saved file (stored
# fills, no refill) shows 0 errors and 0 unconnected, and a refill would not change the stored fills.
# Gerbers in JLCPCB's recommended KiCad settings: Protel extensions, no X2 attributes or netlist attributes,
# soldermask subtracted from silkscreen. Drill: Excellon, mm, decimal, PTH and NPTH in separate files, oval holes in
# alternate (G85 slot) mode, plus Gerber X2 and PDF drill maps and a drill report. IPC-D-356 netlist for the test.
set -e
K="/c/Program Files/KiCad/10.0/bin"
B0=$1; O=$2; N=$3
q() { grep -v 'image handler\|memory leak' || true; }
rm -rf "$O/gerbers" "$O/checks" "$O/.src"
mkdir -p "$O/gerbers" "$O/checks" "$O/.src"
# plot from a copy named NAME, so no file name or attribute inside the outputs carries the work-in-progress name
D=$(dirname "$B0"); S=$(basename "$B0" .kicad_pcb)
cp "$D/$S.kicad_pcb" "$O/.src/$N.kicad_pcb"
cp "$D/$S.kicad_pro" "$O/.src/$N.kicad_pro"
cp "$D/$S.kicad_dru" "$O/.src/$N.kicad_dru"
sed 's#${KIPRJMOD}/#${KIPRJMOD}/../../../../BOOST_schematic_cleanup/KiCad/#' "$D/fp-lib-table" > "$O/.src/fp-lib-table"
B="$O/.src/$N.kicad_pcb"
"$K/kicad-cli.exe" pcb drc --severity-all --format json -o "$O/checks/${N}_drc.json" "$B" > /dev/null 2>&1 || true
"$K/kicad-cli.exe" pcb drc --severity-all --format report -o "$O/checks/${N}_drc.rpt" "$B" > /dev/null 2>&1 || true
python - "$O/checks/${N}_drc.json" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
err = [v for v in d['violations'] if v['severity'] == 'error']
unc = d.get('unconnected_items', [])
warn = [v['type'] for v in d['violations'] if v['severity'] == 'warning']
print('DRC on the saved file: %d errors, %d unconnected, warnings %s' % (len(err), len(unc), sorted(set(warn))))
if err or unc:
    sys.exit('refusing to plot')
EOF
"$K/python.exe" ../route_2026-09-16/tools/fill_compare.py "$B" 2>&1 | q | head -1
L="F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
"$K/kicad-cli.exe" pcb export gerbers --layers "$L" --no-x2 --no-netlist --subtract-soldermask -o "$O/gerbers" "$B" 2>&1 | q | tail -1
"$K/kicad-cli.exe" pcb export drill --format excellon --drill-origin absolute --excellon-units mm \
    --excellon-zeros-format decimal --excellon-oval-format alternate --excellon-separate-th \
    --generate-map --map-format gerberx2 -o "$O/gerbers/" "$B" 2>&1 | q | tail -1
"$K/kicad-cli.exe" pcb export drill --format excellon --drill-origin absolute --excellon-units mm \
    --excellon-zeros-format decimal --excellon-oval-format alternate --excellon-separate-th \
    --generate-map --map-format pdf --generate-report --report-path "$O/checks/${N}_drill_report.txt" \
    -o "$O/checks/" "$B" 2>&1 | q | tail -1
rm -f "$O"/checks/*.drl
"$K/kicad-cli.exe" pcb export ipcd356 -o "$O/checks/${N}.ipc356" "$B" 2>&1 | q | tail -1
grep -l -a "NOT_FOR_FAB" "$O"/gerbers/* && echo "WARNING: work-in-progress name inside an output" || echo "outputs clean of the work-in-progress name"
cmp "$B0" "$B" && echo "plotted copy identical to $B0"
( cd "$O/gerbers" && rm -f "../${N}_gerbers.zip" && python -c "
import zipfile, os, sys
z = zipfile.ZipFile('../${N}_gerbers.zip', 'w', zipfile.ZIP_DEFLATED)
for f in sorted(os.listdir('.')):
    z.write(f)
z.close()
print('zip:', len(os.listdir('.')), 'files')
" )
ls "$O/gerbers"
