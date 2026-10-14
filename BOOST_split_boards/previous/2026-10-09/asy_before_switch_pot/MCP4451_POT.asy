Version 4
SymbolType CELL
LINE Normal 0 -48 0 -32
LINE Normal 0 32 0 48
LINE Normal -12 -32 12 -32
LINE Normal 12 -32 12 32
LINE Normal 12 32 -12 32
LINE Normal -12 32 -12 -32
LINE Normal 48 0 24 0
LINE Normal 12 0 24 -8
LINE Normal 12 0 24 8
LINE Normal 24 -8 24 8
LINE Normal 14 -1 14 1
LINE Normal 16 -3 16 3
LINE Normal 18 -4 18 4
LINE Normal 20 -5 20 5
LINE Normal 22 -7 22 7
TEXT -16 -40 Right 1 B
TEXT -16 40 Right 1 A
TEXT 36 -12 Center 1 W
WINDOW 0 20 -40 Left 2
WINDOW 3 20 24 Left 1
WINDOW 39 20 48 Left 1
SYMATTR Prefix X
SYMATTR Value MCP4451_POT
SYMATTR SpiceLine CODE=128
SYMATTR Description One potentiometer of the Microchip MCP4451-103 (10k, 257 taps). Pins A W B; parameter CODE 0-256 (0 = wiper at B, 256 = wiper at A; Microchip DS22267A). Requires MCP4451.lib.
SYMATTR ModelFile MCP4451.lib
PIN 0 48 NONE 0
PINATTR PinName A
PINATTR SpiceOrder 1
PIN 48 0 NONE 0
PINATTR PinName W
PINATTR SpiceOrder 2
PIN 0 -48 NONE 0
PINATTR PinName B
PINATTR SpiceOrder 3
