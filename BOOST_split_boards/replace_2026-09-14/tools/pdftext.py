"""Crude PDF text extraction without third-party packages (zlib + content-stream text operators).

  python pdftext.py FILE.pdf [FILE.pdf ...] [--grep REGEX]

Inflates FlateDecode streams and collects strings from Tj / TJ operators. Works for PDFs whose fonts use
standard encodings (older National Semiconductor / ST datasheets); subset fonts with custom encodings
come out garbled. Writes FILE.pdf.txt next to each input and prints matching lines with context.
"""
import sys, re, zlib

args = [a for a in sys.argv[1:]]
pattern = None
if '--grep' in args:
    i = args.index('--grep')
    pattern = re.compile(args[i + 1], re.I)
    del args[i:i + 2]

TJ_ARRAY = re.compile(rb'\[((?:[^\]\\]|\\.)*)\]\s*TJ', re.S)
TJ_STR = re.compile(rb'\(((?:[^)\\]|\\.)*)\)\s*Tj', re.S)
NEWLINE_OPS = re.compile(rb'(T\*|Td|TD|Tm|ET)\b')
ARRAY_ITEM = re.compile(rb'\(((?:[^)\\]|\\.)*)\)|(-?\d+(?:\.\d+)?)', re.S)
ESCAPE = re.compile(rb'\\([nrtbf()\\]|[0-7]{1,3})')


def unescape(b):
    def rep(m):
        g = m.group(1)
        simple = {b'n': b'\n', b'r': b'', b't': b' ', b'b': b'', b'f': b'', b'(': b'(', b')': b')'}
        if g in simple:
            return simple[g]
        if g == bytes([92]):
            return bytes([92])
        return bytes([int(g, 8) & 0xFF])
    return ESCAPE.sub(rep, b)


def streams(data):
    for m in re.finditer(rb'stream\r?\n', data):
        start = m.end()
        end = data.find(b'endstream', start)
        if end < 0:
            continue
        head = data[max(0, m.start() - 400):m.start()]
        if b'FlateDecode' not in head:
            continue
        try:
            yield zlib.decompressobj().decompress(data[start:end])
        except Exception:
            continue


def text_of(stream):
    events = []
    for m in TJ_ARRAY.finditer(stream):
        chunk = b''
        for s, num in ARRAY_ITEM.findall(m.group(1)):
            if s:
                chunk += unescape(s)
            elif num and float(num) < -200:
                chunk += b' '
        events.append((m.start(), chunk))
    for m in TJ_STR.finditer(stream):
        events.append((m.start(), unescape(m.group(1))))
    for m in NEWLINE_OPS.finditer(stream):
        events.append((m.start(), b'\n'))
    events.sort()
    return b''.join(e[1] for e in events).decode('latin-1', 'replace')


for path in args:
    data = open(path, 'rb').read()
    text = '\n'.join(text_of(s) for s in streams(data))
    open(path + '.txt', 'w', encoding='utf8').write(text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    words = len(re.findall(r'[A-Za-z]{3,}', text))
    print('==== %s: %d lines, %d words' % (path.split('/')[-1].split(chr(92))[-1], len(lines), words))
    if pattern:
        shown = 0
        for i, l in enumerate(lines):
            if pattern.search(l):
                print('   ' + ' | '.join(lines[max(0, i - 1):i + 3])[:260])
                shown += 1
                if shown >= 30:
                    print('   ...')
                    break
