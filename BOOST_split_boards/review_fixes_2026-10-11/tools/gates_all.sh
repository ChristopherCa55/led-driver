#!/bin/bash
# gate_return.py for every gate path of the power board (FIX_PROMPT 4.3).
#   bash gates_all.sh CU.json > OUT.txt
# Paths from route_2026-09-16/tools/gate_paths.py's GATES table: driver-side net (the turn-off diode's cathode net,
# or the driver OUT net where there is no diode) + the gate net; return = the FET's source net (GND for M1, M8-M10).
set -u
CU="$1"
G="$(dirname "$0")/../../power6_2026-10-01/tools/gate_return.py"
run() { echo "## $1"; shift; python "$G" "$CU" "$@" | sed 's/^[^:]*: /  /'; }
run M1  GND        "Net-(U19-OUTA)" GATE_M1
run M2  m2_source  "Net-(D11--)" GATE_M2
run M7  m2_source  "Net-(D2--)"  GATE_M7
run M3  m3_source  "Net-(D14--)" GATE_M3
run M6  m3_source  "Net-(D8--)"  GATE_M6
run M4  m4_source  "Net-(D13--)" GATE_M4
run M5  m4_source  "Net-(D22--)" GATE_M5
run M8  GND        "Net-(U6-OUT)"  "Net-(M8-G)"
run M9  GND        "Net-(U12-OUT)" "Net-(M9-G)"
run M10 GND        "Net-(U11-OUT)" "Net-(M10-G)"
