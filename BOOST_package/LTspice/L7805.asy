Version 4
SymbolType CELL
RECTANGLE Normal -64 -32 64 32
TEXT 0 -8 Center 2 L7805
TEXT 0 12 Center 1 5V 1.5A
WINDOW 0 0 -40 Bottom 2
WINDOW 3 0 40 Top 2
SYMATTR Prefix X
SYMATTR Value L7805
SYMATTR Description Behavioural ST L7805CV 5V 1.5A regulator. Dropout modelled at datasheet worst case 2.0V. Requires L7805.lib.
SYMATTR ModelFile L7805.lib
PIN -64 0 LEFT 8
PINATTR PinName IN
PINATTR SpiceOrder 1
PIN 64 0 RIGHT 8
PINATTR PinName OUT
PINATTR SpiceOrder 2
PIN 0 32 BOTTOM 8
PINATTR PinName GND
PINATTR SpiceOrder 3
