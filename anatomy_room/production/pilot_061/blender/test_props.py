import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib61 import *
sc = setup(samples=64); world(strength=1.2, rot=.8)
area_light("key", (-4, -5, 8), (0, 0, 1.5), 5, 1500); area_light("rim", (5, 5, 4), (0, 0, 1.5), 4, 800, (1, .8, .6))
desk()
root, pv, pans = balance("bal", (0, 0, 0)); set_balance(root, pv, pans, .25)
sphere("ball", .45, (pans[0][1].location.x, 0, pans[0][1].location.z + .51), gold_mat())
sphere("ball2", .14, (pans[1][1].location.x, 0, pans[1][1].location.z + .2), gold_mat())
note_stack("n1", "usd", (-3.2, -1.6, 0), .3); note_stack("n2", "jpy", (-3.0, -1.5, .12), .1); card("c1", (3.0, -1.8, 0), (0, 0, -.4)); phone("p1", (3.6, -.8, 0), (0, 0, .3))
figure("f1", (1.2, -2.4, 0), .9); podium("pd", (-1.6, -2.6, 0), 1.0, .8, 1, pbr_mat("plank", "wood_table_001", 1.2, (.9, .8, .7), 1.2, box_proj=True))
cam = K.Cam(); P = Vector((0, -10, 3.4)); A = Vector((0, 0, 1.5)); cam.look(P, A, lens=40); cam_dof(cam, (P - A).length, 4)
sc.render.resolution_percentage = 50; sc.render.filepath = os.path.join(HERE, "..", "work", "test", "props.png")
t = time.time(); bpy.ops.render.render(write_still=True); print("RENDER", round(time.time() - t, 1))
