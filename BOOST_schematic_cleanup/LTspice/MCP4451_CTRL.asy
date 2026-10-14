Version 4
SymbolType CELL
RECTANGLE Normal -80 -96 80 96
LINE Normal -96 -32 -80 -32
LINE Normal -96 0 -80 0
LINE Normal 96 0 80 0
LINE Normal 0 -112 0 -96
LINE Normal -48 112 -48 96
LINE Normal 0 112 0 96
LINE Normal 48 112 48 96
TEXT -74 -32 Left 1 SCL
TEXT -74 0 Left 1 SDA
TEXT 74 0 Right 1 RESET
LINE Normal 26 -11 74 -11
TEXT 0 -76 VCenter 1 VDD
TEXT -48 76 VCenter 0 HVC/A0
TEXT 0 84 VCenter 0 A1
TEXT 48 82 VCenter 0 VSS
TEXT 0 36 Center 0 digital potentiometer
WINDOW 0 88 -104 Left 2
WINDOW 3 88 104 Left 1
SYMATTR Prefix X
SYMATTR Value MCP4451_CTRL
SYMATTR Description Control and supply unit of the Microchip MCP4451 digital pot (high-impedance loads only; the wiper codes are parameters of the MCP4451_POT units). Requires MCP4451.lib.
SYMATTR ModelFile MCP4451.lib
PIN 0 -112 NONE 0
PINATTR PinName VDD
PINATTR SpiceOrder 1
PIN 48 112 NONE 0
PINATTR PinName VSS
PINATTR SpiceOrder 2
PIN -96 -32 NONE 0
PINATTR PinName SCL
PINATTR SpiceOrder 3
PIN -96 0 NONE 0
PINATTR PinName SDA
PINATTR SpiceOrder 4
PIN -48 112 NONE 0
PINATTR PinName HVC/A0
PINATTR SpiceOrder 5
PIN 0 112 NONE 0
PINATTR PinName A1
PINATTR SpiceOrder 6
PIN 96 0 NONE 0
PINATTR PinName RESET
PINATTR SpiceOrder 7
