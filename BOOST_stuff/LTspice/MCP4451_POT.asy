Version 4
SymbolType CELL
LINE Normal 0 -48 0 -32
LINE Normal 0 32 0 48
RECTANGLE Normal -10 -32 10 32
LINE Normal 48 0 16 0
LINE Normal 16 0 24 -6
LINE Normal 16 0 24 6
TEXT -14 -40 Right 0 B
TEXT -14 40 Right 0 A
TEXT 44 -8 Right 0 W
WINDOW 0 20 -40 Left 2
WINDOW 3 20 24 Left 1
WINDOW 39 20 48 Left 1
SYMATTR Prefix X
SYMATTR Value MCP4451_POT
SYMATTR SpiceLine CODE=128
SYMATTR Description One potentiometer of the Microchip MCP4451-103 (10k, 257 taps). Pins A W B; parameter CODE 0-256 (0 = wiper at B, 256 = wiper at A; Microchip DS22267A). Requires MCP4451.lib.
SYMATTR ModelFile MCP4451.lib
PIN 0 48 BOTTOM 8
PINATTR PinName A
PINATTR SpiceOrder 1
PIN 48 0 RIGHT 8
PINATTR PinName W
PINATTR SpiceOrder 2
PIN 0 -48 TOP 8
PINATTR PinName B
PINATTR SpiceOrder 3
