Version 4
SymbolType CELL
RECTANGLE Normal -64 -80 64 80
LINE Normal -96 -32 -64 -32
LINE Normal -96 0 -64 0
LINE Normal 0 -112 0 -80
LINE Normal -48 112 -48 80
LINE Normal 0 112 0 80
LINE Normal 48 112 48 80
LINE Normal 96 0 64 0
TEXT -60 -32 Left 1 SCL
TEXT -60 0 Left 1 SDA
TEXT 0 -68 Center 1 VDD
TEXT 60 0 Right 1 RESET
TEXT -48 70 Center 0 HVC/A0
TEXT 0 70 Center 0 A1
TEXT 48 70 Center 0 VSS
TEXT 0 36 Center 1 MCP4451
WINDOW 0 72 -88 Left 2
WINDOW 3 72 96 Left 1
SYMATTR Prefix X
SYMATTR Value MCP4451_CTRL
SYMATTR Description Control and supply unit of the Microchip MCP4451 digital pot (high-impedance loads only; the wiper codes are parameters of the MCP4451_POT units). Requires MCP4451.lib.
SYMATTR ModelFile MCP4451.lib
PIN 0 -112 TOP 8
PINATTR PinName VDD
PINATTR SpiceOrder 1
PIN 48 112 BOTTOM 8
PINATTR PinName VSS
PINATTR SpiceOrder 2
PIN -96 -32 LEFT 8
PINATTR PinName SCL
PINATTR SpiceOrder 3
PIN -96 0 LEFT 8
PINATTR PinName SDA
PINATTR SpiceOrder 4
PIN -48 112 BOTTOM 8
PINATTR PinName HVC/A0
PINATTR SpiceOrder 5
PIN 0 112 BOTTOM 8
PINATTR PinName A1
PINATTR SpiceOrder 6
PIN 96 0 RIGHT 8
PINATTR PinName RESET
PINATTR SpiceOrder 7
