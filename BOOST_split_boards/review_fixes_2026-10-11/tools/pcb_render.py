"""KiCad's own render of a board region: kicad-cli pcb export svg (chosen layers) -> headless Edge PNG.

    python pcb_render.py BOARD.kicad_pcb OUT.png LAYERS x1 y1 x2 y2 [--mirror]
    LAYERS e.g. "F.Cu,F.SilkS,F.Mask,Edge.Cuts"  (region in board mm)
The board is copied to a temp folder with its .kicad_pro / .kicad_dru (nothing is written beside the source).
"""
import glob, os, re, shutil, subprocess, sys, tempfile, time

KICAD = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


def main():
    a = sys.argv[1:]
    pcb, out, layers = a[0], os.path.abspath(a[1]), a[2]
    x1, y1, x2, y2 = map(float, a[3:7])
    tmp = tempfile.mkdtemp(prefix='pcbsvg_')
    base = os.path.splitext(pcb)[0]
    for ext in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
        if os.path.exists(base + ext):
            shutil.copy(base + ext, tmp)
    src = os.path.join(tmp, os.path.basename(pcb))
    svg = os.path.join(tmp, 'b.svg')
    cmd = [KICAD, 'pcb', 'export', 'svg', '--layers', layers, '--mode-single', '--exclude-drawing-sheet',
           '-o', svg, src]
    if '--mirror' in a:
        cmd.insert(4, '--mirror')
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(svg):
        cand = glob.glob(os.path.join(tmp, '*.svg'))
        if not cand:
            sys.exit('kicad-cli made no svg: ' + r.stdout[-300:] + r.stderr[-300:])
        svg = cand[0]
    txt = open(svg, encoding='utf-8').read()
    txt = re.sub(r'viewBox="[^"]*"', 'viewBox="%g %g %g %g"' % (x1, y1, x2 - x1, y2 - y1), txt, count=1)
    w = 1600
    h = int(w * (y2 - y1) / (x2 - x1))
    txt = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', r'\1 width="%dpx"' % w, txt, count=1)
    txt = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', r'\1 height="%dpx"' % h, txt, count=1)
    open(svg, 'w', encoding='utf-8').write(txt)
    html = os.path.join(tmp, 'v.html')
    open(html, 'w').write('<html><body style="margin:0;background:#202020"><img src="%s" style="width:%dpx;height:%dpx">'
                          '</body></html>' % (os.path.basename(svg), w, h))
    if os.path.exists(out):
        os.remove(out)
    for _ in range(3):
        with open(os.path.join(tmp, 'edge.log'), 'w') as lg:
            subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--screenshot=' + out,
                            '--window-size=%d,%d' % (w, h), 'file:///' + html.replace(os.sep, '/')],
                           stdout=lg, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL)
        for _ in range(20):
            if os.path.exists(out):
                break
            time.sleep(0.5)
        if os.path.exists(out):
            break
    print('rendered' if os.path.exists(out) else 'FAILED', out)


if __name__ == '__main__':
    main()
