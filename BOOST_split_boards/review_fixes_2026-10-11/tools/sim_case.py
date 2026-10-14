"""One LTspice batch run of a BOOST LTspice folder, on a scratch copy (system Python + LTspice 26).

    python sim_case.py SRC_LTSPICE_DIR OUT_DIR [--ic asis|clean|drop] [--extra FILE] [--tran TEXT]

1. Copies SRC_LTSPICE_DIR (inputs only: .asc/.asy/.lib) to OUT_DIR, which must not exist.
2. Netlists BOOST.asc there with `LTspice.exe -netlist` (so the run uses exactly LTspice's own netlist).
3. Edits the NETLIST only (never the .asc):
   - adds a .save list (the shipped .meas lines need V(LX) and I(D19); the rest are for the review checks), so a 30 ms
     run writes about 0.3 GB instead of about 22 GB, and `.options plotwinsize=0` (no waveform compression, so peaks
     are exact). Both runs of any comparison use the same list;
   - adds the extra .meas lines below (the shipped .meas lines stay as they are);
   - --ic asis (default) keeps `.ic V(Out)=0 V(Out-)=1 V(C10)=0 V(C5)=0 V(C2)=0`; clean removes the three terms that
     name no node; drop deletes that whole .ic line;
   - --extra FILE appends that file's lines before .end; --tran replaces the .tran line.
4. Runs `LTspice.exe -b BOOST.net` in OUT_DIR and prints the .meas results from BOOST.log.
"""
import os, re, shutil, subprocess, sys, time

LTSPICE = r'C:\Program Files\ADI\LTspice\LTspice.exe'
SAVE = ('.save V(LX) I(D19) V(Vin) V(Vout_1) V(Vout_2) V(Vout_3) I(SIM_LED1) I(SIM_LED2) I(SIM_LED3) I(L1) '
        'V(12V) V(5V) V(SRV1) V(SRV2) V(SRV3) V(Verr1) V(Verr2) V(Verr3) V(Out) V(Out-) V(Vref_1) V(Vref_2) V(Vref_3) '
        'V(Output1_drain) V(Output2_drain) V(Output3_drain) V(m2_source) V(m3_source) V(m4_source)')
MEAS = '''.options plotwinsize=0
.meas TRAN ILED1 AVG I(SIM_LED1) FROM 25m TO 30m
.meas TRAN ILED2 AVG I(SIM_LED2) FROM 25m TO 30m
.meas TRAN ILED3 AVG I(SIM_LED3) FROM 25m TO 30m
.meas TRAN VOUT1 AVG V(Vout_1) FROM 25m TO 30m
.meas TRAN VOUT2 AVG V(Vout_2) FROM 25m TO 30m
.meas TRAN VOUT3 AVG V(Vout_3) FROM 25m TO 30m
.meas TRAN VD1 AVG V(Output1_drain) FROM 25m TO 30m
.meas TRAN VD2 AVG V(Output2_drain) FROM 25m TO 30m
.meas TRAN VD3 AVG V(Output3_drain) FROM 25m TO 30m
.meas TRAN LXmax MAX V(LX)
.meas TRAN LXmax1 MAX V(LX) FROM 1m TO 30m
.meas TRAN LXss MAX V(LX) FROM 25m TO 30m
.meas TRAN ID19min MIN I(D19) FROM 25m TO 30m
.meas TRAN Ptvs_ss AVG (-1)*V(LX)*I(D19) FROM 25m TO 30m
.meas TRAN IL1avg AVG I(L1) FROM 25m TO 30m
'''


def main():
    a = sys.argv[1:]
    src, out = a[0], a[1]
    ic = a[a.index('--ic') + 1] if '--ic' in a else 'asis'
    extra = open(a[a.index('--extra') + 1]).read() if '--extra' in a else ''
    tran = a[a.index('--tran') + 1] if '--tran' in a else None
    if os.path.exists(out):
        sys.exit('OUT_DIR exists: %s' % out)
    os.makedirs(out)
    for f in os.listdir(src):
        if f.lower().endswith(('.asc', '.asy', '.lib')):
            shutil.copy2(os.path.join(src, f), out)
    asc = os.path.join(out, 'BOOST.asc')
    subprocess.run([LTSPICE, '-netlist', asc], timeout=300)
    net = os.path.join(out, 'BOOST.net')
    s = open(net, encoding='utf-8').read()
    ic_line = '.ic V(Out)=0 V(Out-)=1 V(C10)=0 V(C5)=0 V(C2)=0'
    if ic != 'keep':        # 'keep': the file's own .ic lines as they are (for edited files)
        assert s.count(ic_line) == 1, 'the shipped .ic line is not in the netlist'
    if ic == 'clean':
        s = s.replace(ic_line, '.ic V(Out)=0 V(Out-)=1')
    elif ic == 'drop':
        s = s.replace(ic_line + '\n', '')
    if tran:
        s, n = re.subn(r'^\.tran .*$', tran, s, flags=re.M)
        assert n == 1
    assert '\n.save' not in s
    s = s.replace('\n.end', '\n' + SAVE + '\n' + MEAS + extra + '.end')
    open(net, 'w', encoding='utf-8').write(s)
    t0 = time.time()
    r = subprocess.run([LTSPICE, '-b', 'BOOST.net'], cwd=out, timeout=4 * 3600)
    print('exit %d in %.0f s' % (r.returncode, time.time() - t0))
    log = os.path.join(out, 'BOOST.log')
    raw = open(log, 'rb').read()
    try:
        txt = raw.decode('utf-16-le') if raw[1:2] == b'\x00' else raw.decode('utf-8')
    except UnicodeDecodeError:
        txt = raw.decode('latin-1')
    meas = [l for l in txt.splitlines() if re.match(r'^\s*\w+\s*[:=]', l) and ('=' in l)]
    for l in txt.splitlines():
        if re.match(r'^(ptvs|etvs|iled|vout|vd\d|lxm|lxss|id19|ptvs_ss|il1)', l.strip(), re.I):
            print(l.strip())
    print('raw %.0f MB' % (os.path.getsize(os.path.join(out, 'BOOST.raw')) / 1e6 if os.path.exists(os.path.join(out, 'BOOST.raw')) else 0))


if __name__ == '__main__':
    main()
