"""Ship the review copy's design into the three shipped folders (the user, 2026-10-14: "update the 3 folders boost
package, schematic cleanup, and boost stuff to be like they used to be, but with the updated ltspice schematic, updated
kicad main schematic, subschematics, and pcbs ... regenerate gerbers").

    python install.py STAGE_SUBDIR FOLDER[,FOLDER...] FILE [FILE ...]

Copies STAGE/<STAGE_SUBDIR>/<FILE> to ROOT/<FOLDER>/<FILE> for each folder. Refuses if a KiCad lock file exists in the
folder's KiCad/, if LTspice has an .asc of that folder open, or if the target file (when it exists) no longer matches the
hash recorded in checks/before_<FOLDER>.sha256 (the state backed up in previous/2026-10-14/before_ship/). Logs every
write with old and new SHA-256 to ship.log.
"""
import glob, hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # ship_2026-10-14/
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
STAGE = os.path.join(HERE, 'stage')
LOG = os.path.join(HERE, 'ship.log')
ALLOWED = ('BOOST_package', 'BOOST_stuff', 'BOOST_schematic_cleanup')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def before(folder):
    d = {}
    for line in open(os.path.join(HERE, 'checks', 'before_%s.sha256' % folder), encoding='utf-8'):
        h, f = line.strip().split(' ', 1)
        d[f.lstrip('*').replace('./', '', 1)] = h
    return d


def main():
    sub, folders, files = sys.argv[1], sys.argv[2].split(','), sys.argv[3:]
    lt = subprocess.run(['powershell', '-NoProfile', '-Command',
                         "Get-CimInstance Win32_Process -Filter \"Name='LTspice.exe'\" | Select-Object -ExpandProperty CommandLine"],
                        capture_output=True, text=True).stdout or ''
    plan = []
    for fo in folders:
        assert fo in ALLOWED, fo
        dest = os.path.join(ROOT, fo)
        if glob.glob(os.path.join(dest, 'KiCad', '~*.lck')):
            sys.exit('%s: KiCad lock files: not written' % fo)
        if fo.lower() in lt.lower():
            sys.exit('%s: LTspice has a file of this folder open: not written' % fo)
        bh = before(fo)
        for f in files:
            src = os.path.join(STAGE, sub, f)
            d = os.path.join(dest, f)
            if os.path.exists(d):
                cur = sha(d)
                if f.replace('\\', '/') in bh and cur != bh[f.replace('\\', '/')]:
                    sys.exit('%s/%s changed since the backup: not written' % (fo, f))
            else:
                cur = None
            plan.append((src, d, '%s/%s' % (fo, f), cur))
    with open(LOG, 'a', encoding='utf-8') as lg:
        for src, d, rel, cur in plan:
            os.makedirs(os.path.dirname(d), exist_ok=True)
            for attempt in range(6):          # the first write into a folder sometimes gets EINVAL (OneDrive); retry
                try:
                    shutil.copyfile(src, d)
                    break
                except OSError as e:
                    if e.errno != 22 or attempt == 5:
                        raise
                    import time
                    time.sleep(2)
            new = sha(d)
            assert new == sha(src)
            lg.write('%s %s -> %s\n' % (rel, cur[:8] if cur else '(new)', new[:8]))
            print('%s %s -> %s' % (rel, cur[:8] if cur else '(new)', new[:8]))


if __name__ == '__main__':
    main()
