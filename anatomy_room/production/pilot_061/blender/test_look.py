import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib61 import *
sc = setup(samples=int(os.environ.get("SAMP", "64"))); world(strength=1.2, rot=float(os.environ.get("ROT", "0.8")))
area_light("key", (-3, -4, 6), (0, 0, .5), 4, 900); area_light("rim", (4, 5, 3), (0, 0, .5), 3, 500, (1, .8, .6))
desk()
for i, (x, y, z, rz) in enumerate(pile_slots(40)):
    bar(f"b{i}", (x, y, z), rz)
sphere("ball", .5, (2.2, -.8, .5), gold_mat())
cam = K.Cam(); cam.look((3.2, -6.5, 3.2), (0.4, 0, .7), lens=50); cam_dof(cam, (Vector((3.2, -6.5, 3.2)) - Vector((0.4, 0, .7))).length, 2.8)
sc.render.resolution_percentage = int(os.environ.get("PCT", "50"))
sc.render.filepath = os.path.join(HERE, "..", "work", "test", "look.png"); os.makedirs(os.path.dirname(sc.render.filepath), exist_ok=True)
t = time.time(); bpy.ops.render.render(write_still=True); print("RENDER", round(time.time() - t, 1))
