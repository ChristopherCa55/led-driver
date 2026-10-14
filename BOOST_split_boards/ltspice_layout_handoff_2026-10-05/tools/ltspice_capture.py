"""Screenshots of a schematic as LTspice itself draws it: an overview plus every block at a readable zoom.

    python ltspice_capture.py FILE.asc OUTDIR [--blocks PWR,CREG1] [--tile 1400x900] [--no-overview]
    python ltspice_capture.py FILE.asc OUTDIR --region x1,y1,x2,y2 [--name myview]

How: LTspice zooms to fit when it opens a file, so each view is a temporary CROPPED copy of the schematic (only the
symbols, wires, labels and text inside that region, wires clipped at its edge) opened in a new maximized LTspice
window, captured with PrintWindow, and closed. Blocks are found from their frames (RECTANGLE + ";[ID] title"); a block
larger than one tile is split into overlapping tiles. Nothing in FILE's folder is written; temp copies go to %TEMP%.

It opens and closes one LTspice window per view on the desktop (a few seconds each), so ask the user before
running it. The user's own LTspice windows are not touched.
"""
import ctypes, ctypes.wintypes as wt, os, re, shutil, subprocess, sys, tempfile, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from asc_layout_check import Schematic, inside, seg_hits_rect  # noqa: E402

LTSPICE = r'C:\Program Files\ADI\LTspice\LTspice.exe'
user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()


# ----------------------------------------------------------------------------------------------- window capture
def windows_of(pid):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(p))
        if p.value == pid and user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
            found.append(hwnd)
        return True
    user32.EnumWindows(cb, 0)
    return found


def title(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def grab(hwnd, out_png):
    from PIL import Image
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    hdc = user32.GetWindowDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    gdi32.SelectObject(mdc, bmp)
    user32.PrintWindow(hwnd, mdc, 2)                     # PW_RENDERFULLCONTENT

    class BIH(ctypes.Structure):
        _fields_ = [('biSize', wt.DWORD), ('biWidth', wt.LONG), ('biHeight', wt.LONG), ('biPlanes', wt.WORD),
                    ('biBitCount', wt.WORD), ('biCompression', wt.DWORD), ('biSizeImage', wt.DWORD),
                    ('biXPelsPerMeter', wt.LONG), ('biYPelsPerMeter', wt.LONG), ('biClrUsed', wt.DWORD),
                    ('biClrImportant', wt.DWORD)]
    bih = BIH(ctypes.sizeof(BIH), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(bih), 0)
    img = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    img.save(out_png)
    return w, h


def capture(asc_path, out_png, settle=3.0):
    p = subprocess.Popen([LTSPICE, '-max', asc_path])
    try:
        hwnd, t0 = None, time.time()
        while time.time() - t0 < 25:
            ws = [h for h in windows_of(p.pid) if os.path.splitext(os.path.basename(asc_path))[0].lower()
                  in title(h).lower() or 'ltspice' in title(h).lower()]
            if ws:
                hwnd = ws[0]
                break
            time.sleep(0.3)
        if hwnd is None:
            raise RuntimeError('no LTspice window for ' + asc_path)
        time.sleep(settle)
        user32.ShowWindow(hwnd, 3)                       # SW_MAXIMIZE
        time.sleep(1.0)
        size = grab(hwnd, out_png)
        return title(hwnd), size
    finally:
        p.kill()
        p.wait(timeout=10)


# ----------------------------------------------------------------------------------------------- cropping
def clip(w, r):
    x1, y1, x2, y2 = w
    if x1 == x2:
        a, b = max(min(y1, y2), r[1]), min(max(y1, y2), r[3])
        return (x1, a, x1, b) if r[0] <= x1 <= r[2] and a < b else None
    if y1 == y2:
        a, b = max(min(x1, x2), r[0]), min(max(x1, x2), r[2])
        return (a, y1, b, y1) if r[1] <= y1 <= r[3] and a < b else None
    return w if inside((x1, y1), r) and inside((x2, y2), r) else None


def crop_lines(sch, r, keep_directives=False):
    out = [l for l in sch.lines[:2] if l.startswith(('Version', 'SHEET'))]
    keep_sym = set()
    for s in sch.syms:
        b = sch.body(s)
        if b[0] < r[2] and r[0] < b[2] and b[1] < r[3] and r[1] < b[3]:
            keep_sym.add(s.line)
    i, L = 0, sch.lines
    while i < len(L):
        l = L[i]
        k = l.split(' ')[0]
        if k == 'WIRE':
            t = [int(v) for v in l.split(' ')[1:5]]
            c = clip(t, r)
            if c:
                out.append('WIRE %d %d %d %d' % c)
        elif k == 'FLAG':
            t = l.split(' ')
            if inside((int(t[1]), int(t[2])), r):
                out.append(l)
                if i + 1 < len(L) and L[i + 1].startswith('IOPIN'):
                    out.append(L[i + 1])
        elif k == 'SYMBOL':
            j = i + 1
            while j < len(L) and L[j].startswith(('SYMATTR', 'WINDOW')):
                j += 1
            if i in keep_sym:
                out += L[i:j]
            i = j
            continue
        elif k == 'TEXT':
            p = l.split(' ', 5)
            if inside((int(p[1]), int(p[2])), r) and (keep_directives or not p[5].startswith('!')):
                out.append(l if not p[5].startswith('!') else 'TEXT %s %s %s %s ;%s' % (p[1], p[2], p[3], p[4],
                                                                                       p[5][1:]))
        elif k in ('RECTANGLE', 'LINE', 'CIRCLE', 'ARC'):
            v = [int(x) for x in l.split(' ')[2:6]]
            if min(v[0], v[2]) < r[2] and r[0] < max(v[0], v[2]) and min(v[1], v[3]) < r[3] and r[1] < max(v[1], v[3]):
                out.append(l)
        i += 1
    # an invisible corner marker pair would change nothing in LTspice's fit; wires at the frame edge already span it
    return out


def frames_of(sch):
    fr = {}
    for t in sch.texts:
        m = re.match(r'^;\s*\[([A-Za-z0-9_.]+)\]', t['body'])
        if m:
            hits = [r for r in sch.rects if inside((t['x'], t['y']), r)]
            if hits:
                fr[m.group(1)] = min(hits, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    return fr


def tiles(r, tw, th, overlap=160):
    out = []
    y = r[1]
    while True:
        x = r[0]
        while True:
            out.append((x, y, min(x + tw, r[2]), min(y + th, r[3])))
            if x + tw >= r[2]:
                break
            x += tw - overlap
        if y + th >= r[3]:
            break
        y += th - overlap
    return out


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        raise SystemExit(__doc__)
    asc, outdir = os.path.abspath(a[0]), os.path.abspath(a[1])
    os.makedirs(outdir, exist_ok=True)
    tw, th = (int(v) for v in (a[a.index('--tile') + 1] if '--tile' in a else '1400x900').split('x'))
    sch = Schematic(asc)
    src = os.path.dirname(asc)
    tmp = tempfile.mkdtemp(prefix='ltcap_')
    for f in os.listdir(src):
        if f.lower().endswith(('.asy', '.lib', '.sub', '.inc')):
            shutil.copy2(os.path.join(src, f), tmp)
    views = []
    if '--region' in a:
        r = tuple(int(v) for v in a[a.index('--region') + 1].split(','))
        views.append((a[a.index('--name') + 1] if '--name' in a else 'region', r, False))
    else:
        if '--no-overview' not in a:
            views.append(('overview', None, True))
        fr = frames_of(sch)
        want = a[a.index('--blocks') + 1].split(',') if '--blocks' in a else sorted(fr)
        for b in want:
            if b not in fr:
                print('no frame for', b)
                continue
            ts = tiles(fr[b], tw, th)
            for k, r in enumerate(ts):
                views.append(('%s%s' % (b, '' if len(ts) == 1 else '_%d' % (k + 1)), r, b == 'SETUP'))
    index = []
    for name, r, keepd in views:
        p = os.path.join(tmp, name + '.asc')
        lines = sch.lines if r is None else crop_lines(sch, r, keepd)
        open(p, 'w', encoding='latin-1', newline='\n').write('\n'.join(lines))
        png = os.path.join(outdir, name + '.png')
        try:
            t, size = capture(p, png)
            index.append('| %s | %s | %dx%d px |' % (name, r if r else 'whole sheet', size[0], size[1]))
            print('captured', name, size)
        except Exception as e:
            index.append('| %s | %s | FAILED: %s |' % (name, r, e))
            print('FAILED', name, e)
    open(os.path.join(outdir, 'index.md'), 'w').write(
        '# LTspice captures of %s\n\n| view | region (schematic units) | image |\n|---|---|---|\n%s\n' % (
            asc, '\n'.join(index)))
    shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
