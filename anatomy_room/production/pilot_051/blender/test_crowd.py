"""群れの猫を確かめる（blender -b -P blender/test_crowd.py -- test）。work/test/crowd_N.png"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import track, train, crowd, time
t0 = time.time(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4); track.track_scene(-460, 120, 30, False)
T = train.build_train(4); train.place(T, 20, track.TOP)
F = crowd.walk_frames(); NF = 8; log("frames", len(F), round(time.time() - t0, 1))
N = int(os.environ.get("N", "2200")); rnd = np.random.default_rng(3)
col = rnd.integers(0, 6, N); ph0 = rnd.uniform(0, 1, N)
x = np.clip(rnd.normal(0, .5, N), -1.0, 1.0) + rnd.choice([-.0, 0.0], N); row = np.arange(N) // 25; y0 = 21.5 + row * .6 + rnd.uniform(-.15, .15, N)
x = (np.arange(N) % 25 - 12) * .12 + rnd.uniform(-.03, .03, N)
def fn(t):
    y = y0 + .67 * t; P = np.stack([x, y, np.full(N, track.TOP + .0)], 1)
    k = ((ph0 + t * 1.6) % 1 * NF).astype(int); return P, np.zeros(N), col * NF + k
C = crowd.Crowd("cats", F, fn); track.haze(); log("built", round(time.time() - t0, 1))
sc.render.resolution_percentage = int(os.environ.get("PCT", "40")); sc.render.use_motion_blur = False
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
VIEWS = [((3.0, 12, 1.4), (0, 24, .9), 30), ((9, 60, 9), (0, 30, 0), 26), ((.9, 19.5, 1.25), (0, 22.3, 1.1), 50)]
for i, (p, at, lens) in enumerate(VIEWS):
    if os.environ.get("ONLY") and str(i) not in os.environ["ONLY"]:
        continue
    cam.look(p, at, lens); sc.render.filepath = os.path.join(out, f"crowd_{i}.png"); t1 = time.time(); bpy.ops.render.render(write_still=True); log("view", i, round(time.time() - t1, 1))
