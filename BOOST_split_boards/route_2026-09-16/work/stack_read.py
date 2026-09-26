import pcbnew, sys
b = pcbnew.LoadBoard(sys.argv[1])
ds = b.GetDesignSettings()
print('loaded; board thickness', pcbnew.ToMM(ds.GetBoardThickness()), 'has stackup', ds.m_HasStackup)
pcbnew.SaveBoard(sys.argv[2], b)
