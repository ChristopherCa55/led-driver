"""Promote an accepted step's files into the copy (BOOST_review_fixes), never into a shipped folder.

    python promote.py STEP_LABEL SRC_DIR DEST_DIR FILE [FILE ...]

For each FILE: the DEST file must exist, there must be no KiCad lock file (~*.lck) in DEST_DIR and no LTspice
process with DEST's .asc open, and DEST's current SHA-256 must equal the last hash this tool recorded for it in
work/promotions.log (or the work/pristine copy's hash if never promoted), so nothing the user changed is overwritten.
DEST is backed up to BOOST_split_boards/previous/2026-10-11/promote_<STEP_LABEL>/ first. Every write is logged with
old and new SHA-256 in work/promotions.log. Line endings are kept as in SRC (bytes are copied).
"""
import glob, hashlib, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.normpath(os.path.join(HERE, '..', 'work'))
BSB = os.path.normpath(os.path.join(HERE, '..', '..'))
FORBIDDEN = [os.path.normpath(os.path.join(BSB, '..', d)).lower() for d in
             ('BOOST_stuff', 'BOOST_package', 'BOOST_schematic_cleanup', 'BOOST-github')]
LOG = os.path.join(WORK, 'promotions.log')


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def last_hash(rel):
    h = None
    if os.path.exists(LOG):
        for line in open(LOG, encoding='utf-8'):
            parts = line.split()
            if len(parts) >= 4 and parts[0] == rel and parts[2] == '->':
                h = parts[3]
    return h


def main():
    label, src, dest = sys.argv[1:4]
    files = sys.argv[4:]
    dest = os.path.normpath(dest)
    assert not any(dest.lower().startswith(f) for f in FORBIDDEN), 'shipped folder: refused'
    assert 'boost_review_fixes' in dest.lower(), dest
    if glob.glob(os.path.join(dest, '~*.lck')):
        sys.exit('lock files in %s: KiCad has the project open. Not promoted.' % dest)
    if any(f.lower().endswith('.asc') for f in files):
        r = subprocess.run(['powershell', '-NoProfile', '-Command',
                            "Get-CimInstance Win32_Process -Filter \"Name='LTspice.exe'\" | "
                            "Select-Object -ExpandProperty CommandLine"], capture_output=True, text=True)
        if any(os.path.basename(f).lower() in (r.stdout or '').lower() for f in files):
            sys.exit('LTspice has the file open. Not promoted.')
    sub = os.path.basename(dest)                          # KiCad / LTspice
    bk = os.path.join(BSB, 'previous', '2026-10-11', 'promote_%s' % label, sub)
    plan = []
    for f in files:
        s, d = os.path.join(src, f), os.path.join(dest, f)
        rel = '%s/%s' % (sub, f)
        cur = sha(d)
        exp = last_hash(rel)
        if exp is None:
            pr = os.path.join(WORK, 'pristine', sub, f)
            exp = sha(pr) if os.path.exists(pr) else None
        if exp is not None and not cur.startswith(exp[:8]):
            sys.exit('%s changed since the last promotion (%s, expected %s): not promoted' % (rel, cur[:8], exp[:8]))
        new = sha(s)
        if new == cur:
            print('%s unchanged' % rel)
            continue
        plan.append((s, d, rel, cur, new))
    os.makedirs(bk, exist_ok=False)
    with open(LOG, 'a', encoding='utf-8') as lg:
        for s, d, rel, cur, new in plan:
            shutil.copy2(d, os.path.join(bk, os.path.basename(d)))
            shutil.copyfile(s, d)
            assert sha(d) == new
            lg.write('%s %s -> %s  (%s, from %s)\n' % (rel, cur[:8], new[:8], label, os.path.relpath(s, WORK)))
            print('%s %s -> %s' % (rel, cur[:8], new[:8]))
    print('backup of the old files:', bk)


if __name__ == '__main__':
    main()
