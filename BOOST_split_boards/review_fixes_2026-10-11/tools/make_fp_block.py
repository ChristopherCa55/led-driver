"""Make a board footprint block (KiCad's own s-expression) from a KiCad library footprint, for add_footprints.py.
KiCad's python.exe. A throwaway board holds the one footprint; KiCad saves it, and the footprint block is cut out.

    python.exe make_fp_block.py JOB.json OUT_DIR

JOB.json: {"lib": "C:/Program Files/KiCad/10.0/share/kicad/footprints/Resistor_SMD.pretty",
           "name": "R_0402_1005Metric",
           "parts": [{"ref": "R106", "value": "4.7k", "x": 59.3, "y": 106.6, "rot": 0, "side": "B",
                      "path": "/<symbol uuid>", "sheetfile": "BOOST_control_RC2.kicad_sch",
                      "nets": {"1": "5V", "2": "SCL"}, "fields": {"Sim.Device": "R", "Sim.Params": "R=4.7k"},
                      "ref_layer": "Fab"}]}
Writes OUT_DIR/<ref>.block.txt (CRLF) for each part.
"""
import json, os, re, sys, tempfile
import pcbnew


def main():
    job = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for p in job['parts']:
        b = pcbnew.BOARD()
        fp = pcbnew.FootprintLoad(job['lib'], job['name'])
        assert fp, job['name']
        fp.SetParent(b)
        b.Add(fp)
        nets = {}
        for n in set(p['nets'].values()):
            ni = pcbnew.NETINFO_ITEM(b, n)
            b.Add(ni)
            nets[n] = ni
        for pad in fp.Pads():
            if pad.GetNumber() in p['nets']:
                pad.SetNet(nets[p['nets'][pad.GetNumber()]])
        nick = os.path.splitext(os.path.basename(job['lib'].rstrip('/\\')))[0]      # "Resistor_SMD"
        fp.SetFPID(pcbnew.LIB_ID(nick, job['name']))
        fp.SetReference(p['ref'])
        fp.SetValue(p['value'])
        fp.Value().SetVisible(False)         # as on every other part of the card
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(p['x']), pcbnew.FromMM(p['y'])))
        if p.get('side', 'F') == 'B':
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
        fp.SetOrientationDegrees(p['rot'])
        fp.SetPath(pcbnew.KIID_PATH(p['path']))
        fp.SetSheetname('/')
        fp.SetSheetfile(p['sheetfile'])
        for k, v in p.get('fields', {}).items():
            fp.SetField(k, v)
            f = fp.GetField(k)
            f.SetVisible(False)
            f.SetLayer(pcbnew.B_Fab if p.get('side') == 'B' else pcbnew.F_Fab)
        if p.get('ref_layer') == 'Fab':
            fp.Reference().SetLayer(pcbnew.B_Fab if p.get('side') == 'B' else pcbnew.F_Fab)
        tmp = os.path.join(tempfile.mkdtemp(prefix='fpblk_'), 't.kicad_pcb')
        pcbnew.SaveBoard(tmp, b)
        t = open(tmp, encoding='utf-8').read().replace('\r\n', '\n')
        m = re.search(r'\n\t\(footprint .*?\n\t\)\n', t, re.S)
        blk = m.group(0)[1:-1]            # from "\t(footprint" to "\t)"
        open(os.path.join(out, '%s.block.txt' % p['ref']), 'w', encoding='utf-8', newline='').write(
            blk.replace('\n', '\r\n'))
        print('wrote', os.path.join(out, '%s.block.txt' % p['ref']), [(pd.GetNumber(), round(pcbnew.ToMM(pd.GetPosition().x), 3),
               round(pcbnew.ToMM(pd.GetPosition().y), 3), pd.GetNetname()) for pd in fp.Pads()])


if __name__ == '__main__':
    main()
