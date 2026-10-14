"""DRC items new / gone between two kicad-cli DRC json reports (same item = type + its items' text and position).

    python drc_diff.py BASE.json NEW.json
"""
import collections, json, sys


def key(v):
    return (v['type'], tuple(sorted((i['description'], round(i['pos']['x'], 2), round(i['pos']['y'], 2))
                                    for i in v['items'])))


def main():
    a, b = (json.load(open(p, encoding='utf-8')) for p in sys.argv[1:3])
    for name, d in (('base', a), ('new', b)):
        c = collections.Counter(v['severity'] for v in d['violations'])
        print('%-4s errors %d warnings %d unconnected %d parity %d' % (
            name, c['error'], c['warning'], len(d.get('unconnected_items', [])), len(d.get('schematic_parity', []))))
    A, B = set(map(key, a['violations'])), set(map(key, b['violations']))
    for k in sorted(B - A):
        print('  + %s %s' % (k[0], k[1]))
    for k in sorted(A - B):
        print('  - %s %s' % (k[0], k[1]))
    print('new %d, gone %d' % (len(B - A), len(A - B)))


if __name__ == '__main__':
    main()
