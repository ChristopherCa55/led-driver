"""KiCad mock-ups for D8 (pictures only): a NEW copy of the main schematic with
  - item 12: a title block like the board schematics' (title, rev, comment 1);
  - item 15: U26D moved one 12.7 mm slot right, clear of U106D, with its value under it;
then two renders (kicad-cli SVG with the drawing sheet, screenshot by headless Edge).

    python mock_kicad.py SRC.kicad_sch OUT_DIR
"""
import glob, os, re, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..',
                                                 'kicad_layout_2026-10-09', 'tools')))
from sexpr import parse, dump, find, findall, unq
import kgeo

KICAD = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
TITLE = ('(title_block\n\t\t(title "BOOST LED driver - main schematic (both boards)")\n\t\t(rev "RC2")\n'
         '\t\t(comment 1 "Parts also drawn on the board schematics BOOST_power_RC2 / BOOST_control_RC2")\n\t)')


def shift_symbol(s, dx, dy):
    a = find(s, 'at')
    a[1], a[2] = '%g' % (float(a[1]) + dx), '%g' % (float(a[2]) + dy)
    for p in findall(s, 'property'):
        pa = find(p, 'at')
        pa[1], pa[2] = '%g' % (float(pa[1]) + dx), '%g' % (float(pa[2]) + dy)


def render(sch, out_png, region, width=1900, height=1150):
    tmp = tempfile.mkdtemp(prefix='ksvgm_')
    shutil.copy(sch, tmp)
    c = os.path.join(tmp, os.path.basename(sch))
    subprocess.run([KICAD, 'sch', 'export', 'svg', '-o', tmp, c], check=True, capture_output=True)
    svg = glob.glob(os.path.join(tmp, '*.svg'))[0]
    txt = open(svg, encoding='utf-8').read()
    x1, y1, x2, y2 = region
    txt = re.sub(r'viewBox="[^"]*"', 'viewBox="%g %g %g %g"' % (x1, y1, x2 - x1, y2 - y1), txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r'\1 width="%dpx"' % width, txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r'\1 height="%dpx"' % height, txt, count=1)
    open(svg, 'w', encoding='utf-8').write(txt)
    html = os.path.join(tmp, 'v.html')
    open(html, 'w').write('<html><body style="margin:0;background:white"><img src="%s" style="width:%dpx;height:%dpx;'
                          'object-fit:contain"></body></html>' % (os.path.basename(svg), width, height))
    # Edge exits before the PNG lands, and fails silently when its output is piped: log to a file and wait
    import time
    for _ in range(3):
        with open(os.path.join(tmp, 'edge.log'), 'w') as lg:
            subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                            '--screenshot=' + os.path.abspath(out_png), '--window-size=%d,%d' % (width, height),
                            'file:///' + html.replace(os.sep, '/')], stdout=lg, stderr=subprocess.STDOUT,
                           stdin=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(out_png):
                break
            time.sleep(0.5)
        if os.path.exists(out_png):
            break
    print('rendered' if os.path.exists(out_png) else 'FAILED', out_png)


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    dst = os.path.join(out, 'BOOST_mock_NOT_FOR_FAB.kicad_sch')
    if os.path.exists(dst):
        sys.exit('exists: ' + dst)
    text = open(src, encoding='utf-8').read()
    r = parse(text)
    for s in findall(r, 'symbol'):
        i = kgeo.inst_info(s)
        if i['ref'] == 'U26' and i['unit'] == 4:
            shift_symbol(s, 12.7, 0)
            for p in findall(s, 'property'):
                if unq(p[1]) == 'Value':
                    pa = find(p, 'at')
                    pa[1], pa[2] = find(s, 'at')[1], '%g' % (float(find(s, 'at')[2]) + 7.62)
    # title block goes after (paper ...)
    body = dump(r)
    body = body.replace('(paper "D")', '(paper "D")\n\t' + TITLE, 1)
    open(dst, 'w', encoding='utf-8').write(body)
    render(src, os.path.join(out, 'k1_spares_before.png'), (20, 395, 175, 470))
    render(dst, os.path.join(out, 'k1_spares_after.png'), (20, 395, 175, 470))
    render(dst, os.path.join(out, 'k2_title_block.png'), (600, 500, 870, 565))


if __name__ == '__main__':
    main()
