import pcbnew
b = pcbnew.LoadBoard('base_p15.kicad_pcb')
ds = b.GetDesignSettings()
st = ds.GetStackupDescriptor()
print([m for m in dir(st) if not m.startswith('_')])
print('items', st.GetCount())
for i in range(st.GetCount()):
    it = st.GetStackupLayer(i)
    print(i, it.GetTypeName(), it.GetLayerName(), it.GetBrdLayerId(), pcbnew.ToMM(it.GetThickness()), it.GetMaterial(), it.GetEpsilonR(), it.GetSublayersCount())
print([m for m in dir(st.GetStackupLayer(0)) if not m.startswith('_')])
print('have stackup', ds.m_HasStackup)
