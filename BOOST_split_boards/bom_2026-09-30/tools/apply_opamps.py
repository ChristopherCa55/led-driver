"""Apply the approved op-amp change (2026-10-01) to one BOOST folder: the 9 MCP6241 become TI TLV9001IDBVR.

    python apply_opamps.py FOLDER TLV9001.lib

U3, U6, U7, U11, U12, U13, U22, U23, U24.
- KiCad: Value MCP6241 -> TLV9001, Sim.Library -> ../LTspice/TLV9001.lib, and an MPN field "TLV9001IDBVR" is added.
  The MPN matters: TI's TLV9001U (also SOT-23-5) has a different pinout; TLV9001IDBVR has the MCP6241's
  (1 OUT, 2 V-, 3 IN+, 4 IN-, 5 V+).
- LTspice: the 9 symbols' Value MCP6241 -> TLV9001, the directive ".lib MCP6241.lib" -> ".lib TLV9001.lib", the
  TLV9001.lib model is copied in and MCP6241.lib is removed (it is backed up in previous/2026-10-01/).
- README: the model-library list names TLV9001.lib instead of MCP6241.lib.
"""
import os, re, shutil, sys

folder, model = sys.argv[1], sys.argv[2]
REFS = ['U3', 'U6', 'U7', 'U11', 'U12', 'U13', 'U22', 'U23', 'U24']

# ---- KiCad ----
p = os.path.join(folder, 'KiCad', 'BOOST.kicad_sch')
s = open(p, 'rb').read().decode('utf-8')
nl = '\r\n' if '\r\n' in s else '\n'
n = 0
for ref in REFS:
    i = s.find('(property "Reference" "%s"' % ref)
    assert i > 0, ref
    a = s.rfind('\t(symbol', 0, i)
    end = s.find('(property "Reference"', i + 10)
    blk = s[a:end]
    assert blk.count('(property "Value" "MCP6241"') == 1, ref
    new = blk.replace('(property "Value" "MCP6241"', '(property "Value" "TLV9001"')
    m = re.search(r'\(property "Sim\.Library" "[^"]*MCP6241\.lib"', new)
    assert m, ref
    new = new[:m.start()] + '(property "Sim.Library" "../LTspice/TLV9001.lib"' + new[m.end():]
    # add an MPN property right after the Sim.Device property block, copying its indentation and hidden effects
    k = new.find('(property "Sim.Device"')
    kend = new.find(nl + '\t\t)', k) + len(nl + '\t\t)')
    dev = new[k:kend]
    mpn = dev.replace('(property "Sim.Device" "SUBCKT"', '(property "MPN" "TLV9001IDBVR"')
    assert mpn != dev, ref
    new = new[:kend] + nl + '\t\t' + mpn + new[kend:]
    s = s[:a] + new + s[end:]
    n += 1
open(p, 'wb').write(s.encode('utf-8'))
print('KiCad: %d op-amps changed' % n)

# ---- LTspice ----
lt = os.path.join(folder, 'LTspice')
p = os.path.join(lt, 'BOOST.asc')
t = open(p, 'rb').read().decode('latin-1')
c = t.count('SYMATTR Value MCP6241\n')
assert c == 9, c
t = t.replace('SYMATTR Value MCP6241\n', 'SYMATTR Value TLV9001\n')
assert t.count('!.lib MCP6241.lib') == 1
t = t.replace('!.lib MCP6241.lib', '!.lib TLV9001.lib')
open(p, 'wb').write(t.encode('latin-1'))
shutil.copyfile(model, os.path.join(lt, 'TLV9001.lib'))
if os.path.exists(os.path.join(lt, 'MCP6241.lib')):
    os.remove(os.path.join(lt, 'MCP6241.lib'))
print('LTspice: 9 values and the .lib line changed; TLV9001.lib in, MCP6241.lib out')

# ---- README ----
p = os.path.join(folder, 'README.md')
r = open(p, 'rb').read().decode('utf-8')
if '`MCP6241.lib`' in r:
    r = r.replace('`MCP6241.lib`, `MCP6561.lib`, `TVS_5p0SMDJ.lib`, `UCC21520.lib`',
                  '`MCP6561.lib`, `TLV9001.lib`, `TVS_5p0SMDJ.lib`, `UCC21520.lib`')
    assert '`MCP6241.lib`' not in r
    open(p, 'wb').write(r.encode('utf-8'))
    print('README: library list updated')
