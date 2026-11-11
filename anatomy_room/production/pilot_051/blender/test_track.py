"""舞台だけを確かめる（blender -b -P blender/test_track.py -- test）。work/test/track_N.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import track, time
t0 = time.time(); track.world_hdri(os.environ.get("HDRI", "kloofendal_48d_partly_cloudy_puresky"), exposure=-.4); track.track_scene(-60, 160, 30, True); track.haze()
log("scene built", round(time.time() - t0, 1))
sc.render.resolution_percentage = int(os.environ.get("PCT", "40")); sc.render.use_motion_blur = False
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
VIEWS = [((2.6, -6, 1.2), (0, 20, .6), 28), ((-5, 8, 4.5), (0, 40, 0), 24), ((3.2, 3, .3), (2.0, 7, .25), 35)]
for i, (p, at, lens) in enumerate(VIEWS):
    if os.environ.get("ONLY") and str(i) not in os.environ["ONLY"]:
        continue
    cam.look(p, at, lens); sc.render.filepath = os.path.join(out, f"track_{i}.png"); t1 = time.time(); bpy.ops.render.render(write_still=True); log("view", i, round(time.time() - t1, 1))
