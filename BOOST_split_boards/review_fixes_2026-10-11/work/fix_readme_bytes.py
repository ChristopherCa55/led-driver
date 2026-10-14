"""One-off: undo the CRLF conversion of README.md (it was LF) and turn the stray carriage return back into the text \\r."""
import sys
p = sys.argv[1]
b = open(p, 'rb').read()
b = b.replace(b"$'\r'", b"$'\\r'")
b = b.replace(b'\r\n', b'\n')
assert b'\r' not in b
open(p, 'wb').write(b)
print('fixed', p, b.count(b'\n'), 'lines')
