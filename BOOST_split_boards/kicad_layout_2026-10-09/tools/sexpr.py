"""Minimal S-expression reader/writer for KiCad files. Atoms are kept as their raw text (quoted strings keep their
quotes and escapes), so whatever is not edited is written back unchanged."""
import re

TOK = re.compile(r'\s*(\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+)', re.S)


def parse(text):
    stack, cur = [], []
    pos, n = 0, len(text)
    while pos < n:
        m = TOK.match(text, pos)
        if not m:
            if text[pos:].strip() == '':
                break
            raise ValueError('bad token at %d: %r' % (pos, text[pos:pos + 40]))
        t = m.group(1)
        pos = m.end()
        if t == '(':
            stack.append(cur)
            cur = []
        elif t == ')':
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    assert not stack
    return cur[0]


def q(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def unq(a):
    if isinstance(a, str) and a.startswith('"'):
        return re.sub(r'\\(.)', r'\1', a[1:-1])
    return a


def dump(node, indent=0):
    """KiCad-like layout: lists whose children are all atoms go on one line"""
    if isinstance(node, str):
        return node
    if all(isinstance(c, str) for c in node):
        return '(' + ' '.join(node) + ')'
    pad = '\t' * (indent + 1)
    parts = ['(' + node[0]]
    i = 1
    while i < len(node) and isinstance(node[i], str):
        parts[0] += ' ' + node[i]
        i += 1
    for c in node[i:]:
        if isinstance(c, list) and c and c[0] == 'xy':
            parts.append(pad + dump(c, indent + 1))
        else:
            parts.append(pad + dump(c, indent + 1))
    return '\n'.join(parts) + '\n' + '\t' * indent + ')'


def find(node, head):
    return next((c for c in node if isinstance(c, list) and c and c[0] == head), None)


def findall(node, head):
    return [c for c in node if isinstance(c, list) and c and c[0] == head]


def prop(node, name):
    for c in findall(node, 'property'):
        if unq(c[1]) == name:
            return c
    return None
