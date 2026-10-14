Version 4
SymbolType CELL
RECTANGLE Normal -64 -32 64 32
TEXT 0 -8 Center 2 MC7812
TEXT 0 12 Center 1 12V 1A 78xx
WINDOW 0 0 -40 Bottom 2
WINDOW 3 0 40 Top 2
SYMATTR Prefix X
SYMATTR Value MC7812_TYP
SYMATTR Description Behavioural onsemi MC7812 (D2PAK) 12V 1A regulator, typical dropout. Set Value to MC7812_WC for the pessimistic dropout. Requires MC7812.lib.
SYMATTR ModelFile MC7812.lib
PIN -64 0 LEFT 8
PINATTR PinName IN
PINATTR SpiceOrder 1
PIN 64 0 RIGHT 8
PINATTR PinName OUT
PINATTR SpiceOrder 2
PIN 0 32 BOTTOM 8
PINATTR PinName GND
PINATTR SpiceOrder 3
