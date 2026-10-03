"""Apply the user's U16 choice (2026-10-01) to one BOOST folder: LM2940S-12 -> onsemi MC7812BD2TR4G (C231294).

    python apply_u16_mc7812.py FOLDER RELEASE_DIR

Same TO-263 footprint (Package_TO_SOT_SMD:TO-263-3_TabPin2): onsemi case 936 (D2PAK) has pins 1 IN and 3 OUT
at 2.54 mm pitch with the tab on pin 2 (GND); the centre lead is cut, so pad 2 stays empty (it is GND anyway).
- KiCad schematic: U16 Value LM2940_12 -> MC7812, Sim.Library -> ../LTspice/MC7812.lib, Sim.Name -> MC7812_TYP,
  and an MPN field "MC7812BD2TR4G". The symbol (ltspice:LM2940_12: IN/GND/OUT, no graphic text) is kept.
- KiCad power board: the same Value / Sim.Library / Sim.Name on footprint U16 (all hidden, on F.Fab).
- LTspice: U16's symbol LM2940_12 -> MC7812, the directive ".lib LM2940_12.lib" -> ".lib MC7812.lib";
  MC7812.asy and MC7812.lib in, LM2940_12.asy and LM2940_12.lib to the Recycle Bin (backups in
  previous/2026-10-01/before_u16_mc7812/).
- README: the symbol and library lists.
"""
import os, re, shutil, subprocess, sys

folder, rel = sys.argv[1], sys.argv[2]


def block(s, ref, opener):
    """Start and end index of the (symbol / (footprint block holding (property "Reference" "ref")."""
    i = s.find('(property "Reference" "%s"' % ref)
    assert i > 0 and s.find('(property "Reference" "%s"' % ref, i + 10) < 0, ref
    a = s.rfind(opener, 0, i)
    d, k = 0, a
    while True:
        c = s[k]
        if c == '(':
            d += 1
        elif c == ')':
            d -= 1
            if d == 0:
                return a, k + 1
        k += 1


def sub1(blk, old, new):
    assert blk.count(old) == 1, (old, blk.count(old))
    return blk.replace(old, new)


# ---- KiCad schematic ----
p = os.path.join(folder, 'KiCad', 'BOOST.kicad_sch')
s = open(p, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in s else '\n'
a, b = block(s, 'U16', '(symbol')
blk = s[a:b]
blk = sub1(blk, '(property "Value" "LM2940_12"', '(property "Value" "MC7812"')
blk = sub1(blk, '(property "Sim.Library" "LM2940_12.lib"', '(property "Sim.Library" "../LTspice/MC7812.lib"')
blk = sub1(blk, '(property "Sim.Name" "LM2940_12"', '(property "Sim.Name" "MC7812_TYP"')
assert '(property "MPN"' not in blk
k = blk.find('(property "Sim.Device"')
kend = blk.find(nl + '\t\t)', k) + len(nl + '\t\t)')
dev = blk[k:kend]
mpn = dev.replace('(property "Sim.Device" "SUBCKT"', '(property "MPN" "MC7812BD2TR4G"')
assert mpn != dev
blk = blk[:kend] + nl + '\t\t' + mpn + blk[kend:]
s = s[:a] + blk + s[b:]
open(p, 'wb').write(s.encode('utf-8'))
print('KiCad schematic: U16 -> MC7812 (MPN MC7812BD2TR4G)')

# ---- KiCad power board ----
p = os.path.join(folder, 'KiCad', 'BOOST_power_RC2.kicad_pcb')
s = open(p, 'rb').read().decode('utf-8')
a, b = block(s, 'U16', '(footprint')
blk = s[a:b]
blk = sub1(blk, '(property "Value" "LM2940_12"', '(property "Value" "MC7812"')
blk = sub1(blk, '(property "Sim.Library" "LM2940_12.lib"', '(property "Sim.Library" "../LTspice/MC7812.lib"')
blk = sub1(blk, '(property "Sim.Name" "LM2940_12"', '(property "Sim.Name" "MC7812_TYP"')
s = s[:a] + blk + s[b:]
open(p, 'wb').write(s.encode('utf-8'))
print('KiCad power board: U16 fields -> MC7812')

# ---- LTspice ----
lt = os.path.join(folder, 'LTspice')
p = os.path.join(lt, 'BOOST.asc')
t = open(p, 'rb').read().decode('latin-1')
assert t.count('SYMBOL LM2940_12 ') == 1 and t.count('!.lib LM2940_12.lib') == 1
t = t.replace('SYMBOL LM2940_12 ', 'SYMBOL MC7812 ').replace('!.lib LM2940_12.lib', '!.lib MC7812.lib')
assert 'LM2940' not in t
open(p, 'wb').write(t.encode('latin-1'))
for f in ('MC7812.asy', 'MC7812.lib'):
    shutil.copyfile(os.path.join(rel, f), os.path.join(lt, f))
for f in ('LM2940_12.asy', 'LM2940_12.lib'):
    q = os.path.abspath(os.path.join(lt, f))
    if os.path.exists(q):
        subprocess.run(['powershell', '-NoProfile', '-Command',
                        "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::"
                        "DeleteFile('%s', 'OnlyErrorDialogs', 'SendToRecycleBin')" % q], check=True)
        assert not os.path.exists(q)
print('LTspice: U16 symbol and .lib line -> MC7812; MC7812.asy/.lib in, LM2940_12.asy/.lib to the Recycle Bin')

# ---- README ----
p = os.path.join(folder, 'README.md')
r = open(p, 'rb').read().decode('utf-8')
r = sub1(r, '`LM2940_12.asy`', '`MC7812.asy`')
r = sub1(r, '`LM2940_12.lib`', '`MC7812.lib`')
r = sub1(r, '- The INA241A4, CD74HC4066, 74HC4051, MCP4451, L78L05, CSS4J shunt and the 5.0SMDJ54A TVS use custom behavioural\n'
            '  models written for this simulation.',
         '- The INA241A4, CD74HC4066, 74HC4051, MCP4451, L78L05, MC7812, CSS4J shunt and the 5.0SMDJ54A TVS use custom\n'
         '  behavioural models written for this simulation. U16 (MC7812) uses `MC7812_TYP`, the typical dropout from\n'
         '  onsemi\'s curve (about 1.5 V); `MC7812_WC` in the same file is a pessimistic 2 V variant.')
assert 'LM2940' not in r
open(p, 'wb').write(r.encode('utf-8'))
print('README: symbol/library lists and the model note updated')
