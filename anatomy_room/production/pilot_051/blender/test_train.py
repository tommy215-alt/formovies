"""新幹線と舞台を確かめる（blender -b -P blender/test_train.py -- test）。work/test/train_N.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import track, train, time
t0 = time.time(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4); track.track_scene(-460, 120, 30, True)
T = train.build_train(16); train.place(T, 20, track.TOP); track.haze(); log("built", round(time.time() - t0, 1))
sc.render.resolution_percentage = int(os.environ.get("PCT", "40")); sc.render.use_motion_blur = False
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
VIEWS = [((5.5, 34, 1.2), (0, 14, 2.2), 28), ((14, 26, 6), (0, -40, 1.5), 30), ((2.2, 30, .6), (0, 20, 1.8), 24), ((3.2, 9, .7), (1.0, 13.6, .8), 40)]
for i, (p, at, lens) in enumerate(VIEWS):
    if os.environ.get("ONLY") and str(i) not in os.environ["ONLY"]:
        continue
    cam.look(p, at, lens); sc.render.filepath = os.path.join(out, f"train_{i}.png"); t1 = time.time(); bpy.ops.render.render(write_still=True); log("view", i, round(time.time() - t1, 1))
