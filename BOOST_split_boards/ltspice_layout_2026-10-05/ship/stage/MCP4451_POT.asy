Version 4
SymbolType CELL
RECTANGLE Normal -24 -48 48 48
LINE Normal 0 -48 0 -28
LINE Normal 0 28 0 48
LINE Normal -8 -28 8 -28
LINE Normal 8 -28 8 28
LINE Normal 8 28 -8 28
LINE Normal -8 28 -8 -28
LINE Normal 48 0 20 0
LINE Normal 8 0 20 -8
LINE Normal 8 0 20 8
LINE Normal 20 -8 20 8
LINE Normal 10 -1 10 1
LINE Normal 12 -3 12 3
LINE Normal 14 -4 14 4
LINE Normal 16 -5 16 5
LINE Normal 18 -7 18 7
TEXT 14 -36 Left 1 B
TEXT 14 36 Left 1 A
TEXT 44 -12 Right 1 W
WINDOW 0 -32 -32 Right 2
WINDOW 3 -32 0 Right 1
WINDOW 39 -32 24 Right 1
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
