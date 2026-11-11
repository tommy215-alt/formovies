"""ティラノサウルスだけを確かめる（blender -b -P blender/test_trex.py -- test）。work/test/trex_N.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import trex
trex.init()
sky.set(0, 55, 150, 6.0); sc.view_settings.exposure = -4.5; set_haze((.8, .86, .93), .9, 150., 4000.)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=200)
mesh_obj("ground", bm, [mat("g", (.3, .3, .3), .9)])
sc.render.resolution_percentage = 70
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
VIEWS = [(dict(ph=.28), (11, 7, 2.6), (0, 0.6, 2.7), 30), (dict(ph=.0), (-10, 3, 1.5), (0, 0.5, 2.6), 30), (dict(ph=.75, jaw=.35), (2.2, 9.5, 4.4), (0, 4.3, 4.4), 50),
         (dict(ph=.1, sit=1, amp=0, jaw=.25), (8, 6, 2), (0, 1.5, 1.8), 35), (dict(ph=.6), (0.5, 14, 3.5), (0, 2, 3.0), 35), (dict(amp=0, jaw=.2, head=(.1, .3)), (4.5, 11, 2.6), (0, 3, 3.5), 40), (dict(amp=0), (3.2, 7.5, 2.6), (0, 3.2, 3.5), 50)]
for i, (kw, p, at, lens) in enumerate(VIEWS):
    if os.environ.get("ONLY") and str(i) not in os.environ["ONLY"]:
        continue
    trex.medal(i >= 5); trex.tpose(**kw); cam.look(p, at, lens); sc.render.filepath = os.path.join(out, f"trex_{i}.png"); bpy.ops.render.render(write_still=True); log("view", i)
