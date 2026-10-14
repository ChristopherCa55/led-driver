"""Render a KiCad schematic (or a region of it) to PNG: kicad-cli -> SVG -> headless Edge screenshot.

    python render.py SCH.kicad_sch OUT.png [x1 y1 x2 y2]      (region in sheet mm; whole sheet if omitted)
    python render.py SCH.kicad_sch OUT.png --lt x1 y1 x2 y2   (region in LTspice units of the v7 layout)
"""
import os, re, sys, subprocess, tempfile, shutil, glob, time

KICAD = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
S, OX, OY = 0.079375, 629.92, 805.18


def render(sch, out_png, region=None, width=1900, height=1150):
    out_png = os.path.abspath(out_png)
    if os.path.exists(out_png):
        os.remove(out_png)
    tmp = tempfile.mkdtemp(prefix='ksvg_')
    src_dir = os.path.dirname(os.path.abspath(sch))
    for f in glob.glob(os.path.join(src_dir, '*')):
        if os.path.isfile(f) and not f.endswith('.kicad_prl'):
            shutil.copy(f, tmp)
    sch_copy = os.path.join(tmp, os.path.basename(sch))
    subprocess.run([KICAD, 'sch', 'export', 'svg', '--exclude-drawing-sheet', '-o', tmp, sch_copy],
                   check=True, capture_output=True)
    own = os.path.join(tmp, os.path.splitext(os.path.basename(sch))[0] + '.svg')   # a root also plots its sheets
    svg = own if os.path.exists(own) else glob.glob(os.path.join(tmp, '*.svg'))[0]
    txt = open(svg, encoding='utf-8').read()
    if region:
        x1, y1, x2, y2 = region
        txt = re.sub(r'viewBox="[^"]*"', 'viewBox="%g %g %g %g"' % (x1, y1, x2 - x1, y2 - y1), txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r'\1 width="%dpx"' % width, txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r'\1 height="%dpx"' % height, txt, count=1)
    open(svg, 'w', encoding='utf-8').write(txt)
    html = os.path.join(tmp, 'v.html')
    open(html, 'w').write('<html><body style="margin:0;background:white"><img src="%s" style="width:%dpx;height:%dpx;'
                          'object-fit:contain"></body></html>' % (os.path.basename(svg), width, height))
    prof = os.path.join(tempfile.gettempdir(), 'edge_render_prof')
    url = 'file:///' + html.replace(os.sep, '/')
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--user-data-dir=' + prof,
                    '--screenshot=' + out_png, '--window-size=%d,%d' % (width, height), url], capture_output=True)
    for _ in range(120):                       # msedge.exe hands off to a browser process and may return early
        if os.path.exists(out_png) and os.path.getsize(out_png) > 0:
            time.sleep(1)
            break
        time.sleep(0.5)
    shutil.rmtree(tmp, ignore_errors=True)
    return os.path.exists(out_png)


if __name__ == '__main__':
    a = sys.argv[1:]
    region = None
    if '--lt' in a:
        i = a.index('--lt')
        x1, y1, x2, y2 = map(float, a[i + 1:i + 5])
        region = (S * x1 + OX, S * y1 + OY, S * x2 + OX, S * y2 + OY)
        a = a[:i]
    elif len(a) >= 6:
        region = tuple(map(float, a[2:6]))
    ok = render(a[0], a[1], region)
    print('wrote' if ok else 'FAILED', a[1])
