"""Offscreen renders of the assembly GLB (VTK, in the boost3d venv). usage: python tools/render_views.py

Imports BOOST_assembly_2026-09-25.glb, hides the lid and the four case walls (cut-away), keeps the floor, and writes
renders/*.png from several angles. Translucent keep-out solids (penetrators, screwdriver access) stay visible.
"""
import os
import vtk

os.makedirs('renders', exist_ok=True)


def scene(show_lid=False, hide_floor=False):
    ren = vtk.vtkRenderer()
    ren.SetBackground(0.97, 0.97, 0.98)
    ren.SetBackground2(0.80, 0.84, 0.90)
    ren.GradientBackgroundOn()
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.AddRenderer(ren)
    win.SetSize(1800, 1300)
    win.SetMultiSamples(8)
    imp = vtk.vtkGLTFImporter()
    imp.SetFileName('BOOST_assembly_2026-09-25.glb')
    imp.SetRenderWindow(win)
    imp.Update()
    ren = imp.GetRenderer()
    hidden = 0
    acts = ren.GetActors()
    acts.InitTraversal()
    for _ in range(acts.GetNumberOfItems()):
        a = acts.GetNextActor()
        b = a.GetBounds()
        dx, dy, dz = b[1] - b[0], b[3] - b[2], b[5] - b[4]
        # glTF frame: metres, Y up (case Z), -Z = case north
        e = 1e-5
        inside = lambda x0, x1, y0, y1, z0, z1: (b[0] >= x0 - e and b[1] <= x1 + e and b[2] >= y0 - e and
                                                  b[3] <= y1 + e and b[4] >= z0 - e and b[5] <= z1 + e)
        lid = inside(-0.003, 0.131, 0.033, 0.036, -0.003, 0.093)
        wall = (inside(-0.003, 0.0, 0.0, 0.033, -0.003, 0.093) or inside(0.128, 0.131, 0.0, 0.033, -0.003, 0.093) or
                inside(-0.003, 0.131, 0.0, 0.033, -0.003, 0.0) or inside(-0.003, 0.131, 0.0, 0.033, 0.090, 0.093))
        floor = inside(-0.003, 0.131, -0.010, 0.0, -0.003, 0.093)
        if (lid and not show_lid) or wall or (floor and hide_floor):
            a.VisibilityOff()
            hidden += 1
    ren.SetBackground(0.97, 0.97, 0.98)
    ren.SetBackground2(0.78, 0.83, 0.90)
    ren.GradientBackgroundOn()
    ren.RemoveAllLights()
    kit = vtk.vtkLightKit()
    kit.SetKeyLightIntensity(1.15)
    kit.SetKeyToFillRatio(2.2)
    kit.SetKeyToHeadRatio(2.4)
    kit.AddLightsToRenderer(ren)
    ren.SetAmbient(0.35, 0.35, 0.35)
    return win, ren, hidden


def g(p):                       # case frame (mm, Z up) -> glTF frame (m, Y up)
    return (p[0] * 0.001, p[2] * 0.001, -p[1] * 0.001)


def shot(name, pos, focal, up=(0, 0, 1), parallel=None, zoom=1.0, show_lid=False, hide_floor=False):
    win, ren, hidden = scene(show_lid, hide_floor)
    cam = ren.GetActiveCamera()
    cam.SetPosition(*g(pos))
    cam.SetFocalPoint(*g(focal))
    cam.SetViewUp(up[0], up[2], -up[1])
    if parallel:
        cam.ParallelProjectionOn()
        cam.SetParallelScale(parallel * 0.001)
    ren.ResetCameraClippingRange()
    cam.Zoom(zoom)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.SetInputBufferTypeToRGB()
    w2i.ReadFrontBufferOff()
    w2i.Update()
    wr = vtk.vtkPNGWriter()
    wr.SetFileName('renders/%s.png' % name)
    wr.SetInputConnection(w2i.GetOutputPort())
    wr.Write()
    print('wrote renders/%s.png (hid %d lid/wall actors)' % (name, hidden))


C = (89.0, -45.0, 14.0)          # middle of the power board, case frame (board 30-104 x 30-116 mm)
shot('iso_southwest', (-10, -200, 150), C, zoom=1.25)
shot('iso_northeast', (230, 110, 140), C, zoom=1.25)
shot('top', (C[0], C[1], 300), (C[0], C[1], 0), up=(0, 1, 0), parallel=50)
shot('side_from_south', (C[0], -400, 15), (C[0], 0, 15), parallel=30, show_lid=True)
shot('side_from_west', (-300, C[1], 15), (0, C[1], 15), parallel=30, show_lid=True)
shot('stack_closeup_H7', (40, -140, 55), (76.5, -78.5, 16), zoom=3.0)
shot('underside_fets', (70, -130, -130), (89, -45, 3), zoom=1.2, hide_floor=True)
