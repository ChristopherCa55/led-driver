import pcbnew
b = pcbnew.LoadBoard('base_p15.kicad_pcb')
nets = b.GetNetsByName()
for name in ('LX', 'GND', 'Vin'):
    a = nets[name]
    f = b.FindNet(name)
    print(name, 'map ->', a.GetNetname(), a.GetNetCode(), '| FindNet ->', f.GetNetname(), f.GetNetCode())
v = pcbnew.PCB_VIA(b)
v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(40), pcbnew.FromMM(40)))
v.SetWidth(pcbnew.FromMM(0.8)); v.SetDrill(pcbnew.FromMM(0.4)); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
v.SetNet(b.FindNet('LX'))
b.Add(v)
print('before save', v.GetNetname())
pcbnew.SaveBoard('work/nettest.kicad_pcb', b)
b2 = pcbnew.LoadBoard('work/nettest.kicad_pcb')
for t in b2.GetTracks():
    print('after reload', t.GetNetname())
