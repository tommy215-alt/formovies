"""人だけを確かめる（blender -b -P blender/test_people.py -- test）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import people
sky.set(0, 55, 150, 6.0); sc.view_settings.exposure = -4.5; set_haze((.8, .86, .93), .9, 150., 4000.)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=200)
mesh_obj("ground", bm, [mat("g", (.2, .2, .21), .9)])
R = people.People("run", people.grid(40, -5, 5, 0, 12, 3), 0.0, np.random.default_rng(1).uniform(2.5, 5.8, 40), 0, 4)
C = people.People("cheer", [(-7 + .7 * i * 0, 1 + .8 * i) for i in range(12)] , -1.57, 0, 1, 5)
S = people.People("far", people.grid(3000, -15, 15, 14, 80, 6), 0.0, 3.0, 0, 7, lod=1)
sc.render.resolution_percentage = 70
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
for i, (t, p, at, lens) in enumerate([(.3, (-3, -6, 1.5), (0, 6, 1.2), 35), (.55, (4, 1, 1.0), (-1, 4.5, .95), 50)]):
    sc.frame_set(int(t * 30) + 1); cam.look(p, at, lens); sc.render.filepath = os.path.join(out, f"people_{i}.png"); bpy.ops.render.render(write_still=True); log("view", i)
