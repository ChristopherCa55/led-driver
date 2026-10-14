"""Exact text extents of a KiCad schematic, measured from kicad-cli's SVG export (every text is drawn as a
<g class="stroked-text"><desc>TEXT</desc> paths </g> group in sheet millimetres)."""
import os, re, glob, shutil, subprocess, tempfile, html

KICAD = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
GROUP = re.compile(r'<g class="stroked-text"><desc>(.*?)</desc>(.*?)</g>', re.S)
NUM = re.compile(r'[ML]\s*(-?[\d.]+)\s+(-?[\d.]+)')


def export_svg(sch):
    tmp = tempfile.mkdtemp(prefix='ksvgt_')
    src = os.path.dirname(os.path.abspath(sch))
    for f in glob.glob(os.path.join(src, '*')):
        if os.path.isfile(f) and not f.endswith('.kicad_prl'):
            shutil.copy(f, tmp)
    subprocess.run([KICAD, 'sch', 'export', 'svg', '--exclude-drawing-sheet', '-o', tmp,
                    os.path.join(tmp, os.path.basename(sch))], check=True, capture_output=True)
    own = os.path.join(tmp, os.path.splitext(os.path.basename(sch))[0] + '.svg')   # a root also plots its sheets
    svg = own if os.path.exists(own) else glob.glob(os.path.join(tmp, '*.svg'))[0]
    txt = open(svg, encoding='utf-8').read()
    shutil.rmtree(tmp, ignore_errors=True)
    return txt


def text_boxes(svg_txt):
    """[(text, (x1, y1, x2, y2))] for every drawn text (fields, labels, comments, pin numbers and names)"""
    out = []
    for m in GROUP.finditer(svg_txt):
        pts = [(float(a), float(b)) for a, b in NUM.findall(m.group(2))]
        if not pts:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        out.append((html.unescape(m.group(1)), (min(xs), min(ys), max(xs), max(ys))))
    return out
