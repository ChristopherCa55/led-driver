"""Screenshot a KiCad SVG export with headless Edge: an overview and optional tiles.

    python svg_shot.py FILE.svg OUT_PREFIX [--tiles C R] [--px 2000]
"""
import sys, os, re, subprocess

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'


def shot(svg_text, png, wpx, hpx, tmpdir):
    tmp = os.path.join(tmpdir, '_shot.svg')
    open(tmp, 'w', encoding='utf-8').write(svg_text)
    url = 'file:///' + os.path.abspath(tmp).replace(os.sep, '/')
    subprocess.run([EDGE, '--headless=new', '--disable-gpu', '--no-first-run', '--hide-scrollbars',
                    '--user-data-dir=' + os.path.join(tmpdir, 'edgeprof'), '--window-size=%d,%d' % (wpx, hpx),
                    '--screenshot=' + os.path.abspath(png), url], capture_output=True, timeout=180)


def main():
    path, prefix = sys.argv[1], sys.argv[2]
    px = int(sys.argv[sys.argv.index('--px') + 1]) if '--px' in sys.argv else 2000
    s = open(path, encoding='utf-8').read()
    m = re.search(r'width="([\d.]+)mm" height="([\d.]+)mm" viewBox="([-\d. ]+)"', s)
    W, H = float(m.group(1)), float(m.group(2))
    head = m.group(0)
    s = s.replace('<svg\n', '<svg style="background:white"\n', 1)
    tmpdir = os.path.dirname(os.path.abspath(prefix)) or '.'
    hpx = int(px * H / W)
    shot(s.replace(head, 'width="%dpx" height="%dpx" viewBox="0 0 %s %s"' % (px, hpx, W, H)), prefix + '_overview.png',
         px, hpx, tmpdir)
    if '--tiles' in sys.argv:
        i = sys.argv.index('--tiles')
        C, R = int(sys.argv[i + 1]), int(sys.argv[i + 2])
        tw, th = W / C, H / R
        for r in range(R):
            for c in range(C):
                vb = '%.2f %.2f %.2f %.2f' % (c * tw - 3, r * th - 3, tw + 6, th + 6)
                h2 = int(px * (th + 6) / (tw + 6))
                shot(s.replace(head, 'width="%dpx" height="%dpx" viewBox="%s"' % (px, h2, vb)),
                     '%s_r%dc%d.png' % (prefix, r, c), px, h2, tmpdir)
    try:
        os.remove(os.path.join(tmpdir, '_shot.svg'))
    except OSError:
        pass


if __name__ == '__main__':
    main()
