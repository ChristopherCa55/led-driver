"""Copy BOOST_package to BOOST_review_fixes (FIX_PROMPT 4.1), leaving out lock files, KiCad backups/history and
.kicad_prl files. Refuses to run if the destination exists. Reads the source only.

    python make_copy.py SRC DST
"""
import hashlib, os, shutil, sys

src, dst = sys.argv[1], sys.argv[2]
if os.path.exists(dst):
    sys.exit('destination exists: %s (stop and ask)' % dst)


def skip(name):
    return (name.startswith('~$') or name.endswith('.lck') or name.endswith('-backups') or name == '.history'
            or name.endswith('.kicad_prl'))


copied, skipped = [], []
for root, dirs, files in os.walk(src):
    rel = os.path.relpath(root, src)
    for d in list(dirs):
        if skip(d):
            skipped.append(os.path.join(rel, d) + '/')
            dirs.remove(d)
    os.makedirs(os.path.join(dst, rel), exist_ok=True)
    for f in files:
        r = os.path.normpath(os.path.join(rel, f))
        if skip(f):
            skipped.append(r)
            continue
        shutil.copy2(os.path.join(src, r), os.path.join(dst, r))
        copied.append(r)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


bad = [r for r in copied if sha(os.path.join(src, r)) != sha(os.path.join(dst, r))]
print('copied %d files, skipped %d: %s' % (len(copied), len(skipped), skipped))
print('hash mismatches: %d %s' % (len(bad), bad))
