"""pilot_050「ティラノサウルスがマラソン大会に出たら」の 3D（Blender Cycles）。
blender -b -P blender/scene.py -- l00 [l01 …] [--still] [--samples N] [--resume]
試し描き：環境変数 AT="0.5,2.0" で、指定のショットのその秒だけを work/test/<ショット>_<秒>.png に（解像度 50%）。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stage import *
trex.init()
import shots_a, shots_b, shots_c

NAMES = [s["id"] for s in PLAN["shots"]]
FN = {}
for m_ in (shots_a, shots_b, shots_c):
    FN.update({k: getattr(m_, k) for k in dir(m_) if k[:3] in ("s_l", "a_l")})


def _wrap(a):
    def w(u, t, f):
        if f % 20 == 0:
            log("anim frame", f)
        a(u, t, f)
        for o in trex.TANIM:
            o.keyframe_insert("scale", frame=f + 1)
    return w


SHOTS = {k: (FN["s_" + k], _wrap(FN["a_" + k])) for k in NAMES}
ANIM = [cam.o] + trex.TANIM

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "50"))
    for name in O["shots"]:
        setup, anim = SHOTS[name]; n = int(math.ceil(SPLAN[name]["dur"] * K.FPS)) + 2
        for o in ANIM:
            o.animation_data_clear()
        setup()
        for f in range(n):
            anim(f / max(1, n - 3), f / K.FPS, f)
            for o in ANIM:
                for path in ("location", "rotation_quaternion" if o.rotation_mode == "QUATERNION" else "rotation_euler"):
                    o.keyframe_insert(path, frame=f + 1)
                if o.type == "CAMERA":
                    o.data.keyframe_insert("lens", frame=f + 1)
        for at in ats:
            sc.frame_set(int(round(at * K.FPS)) + 1); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            bpy.ops.render.render(write_still=True); log("test", name, at)
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
