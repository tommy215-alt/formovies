import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import track, hamster
track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=2); g = mesh_obj("floor", bm, [track.pbr("brushed_concrete", 2.0, 0.0, tint=(.75, .6, .45), name="floor")])
H = hamster.Hamster("h0"); W = hamster.Wheel("w0"); W.place((.3, 0, 0), -math.pi / 2); W.spin(.4); bpy.context.view_layer.update()
H2 = hamster.Hamster("h1"); H3 = hamster.Hamster("h2")
H.pose((0, 0, 0), 0.0, "sit", 0.5); H2.pose(tuple(W.runner_pos()), -math.pi / 2, "run", .3); H3.pose((-.2, 0, 0), .6, "curl", .5)
sc.render.resolution_x, sc.render.resolution_y = 1200, 700; sc.render.use_motion_blur = False
cam.look((0, .55, .12), (0.05, 0, .05), 40); sc.render.filepath = os.path.join(HERE, "..", "work", "test", "ham_0.png"); bpy.ops.render.render(write_still=True)
cam.look((.3, .55, .14), (.3, 0, .1), 40); sc.render.filepath = os.path.join(HERE, "..", "work", "test", "ham_1.png"); bpy.ops.render.render(write_still=True)
