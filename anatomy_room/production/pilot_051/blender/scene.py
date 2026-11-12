"""pilot_051「猫 何匹で、新幹線は動く？」の 3D（Blender Cycles）。l08（地図）は画面の図なので 3D はない。
blender -b -P blender/scene.py -- l00 [l01 …] [--still] [--samples N] [--resume]
試し描き：AT="0.5,2.0" で、指定のショットのその秒だけを work/test/<ショット>_<秒>.png に（PCT で解像度 %）。
座標：線路は +Y、新幹線の鼻先は y=0（動く回は y=TRAIN(t)）。猫は鼻先の前（y>0）で、枕木の上（z=Z_CAT）を +Y へ引く。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, train, crowd, cat

Z_CAT = track.BALLAST_H + track.SLEEPER[2]        # 枕木の上の面
V = PLAN["kmh"] / 3.6                             # 引き続けたときの速さ 秒速 0.67 m
NAMES = [s["id"] for s in PLAN["shots"]]
COATS = crowd.COATS

# ---------------------------------------------------------------- 群れの形（柄ごとに 20：歩き 8・引く 8・香箱 1・丸くなる 2・座る 1）
FR = []
for c_ in COATS:
    FR += crowd.bake_poses(c_, "walk", 8) + crowd.bake_poses(c_, "pull", 8) + crowd.bake_poses(c_, "loaf", 1) + crowd.bake_poses(c_, "curl", 2) + crowd.bake_poses(c_, "sit", 1)
track.save_cache()
OFF = dict(walk=0, pull=8, loaf=16, curl=17, sit=19)


def _alive(o):
    try:
        o.name; return True
    except ReferenceError:
        return False


cat.CANIM[:] = [o for o in cat.CANIM if _alive(o)]      # 群れの形を作るのに使った一時の猫（消した）を外す


def fidx(coat_i, mode, k=0):
    return coat_i * 20 + OFF[mode] + k


# ---------------------------------------------------------------- 手前の毛のある猫（はじめに 1 度だけ作り、ショットごとに見せる・隠す）
HERO = {nm: cat.build_cat(f"h_{nm}", nm, seed=i + 3, fur=True, dens=.6) for i, nm in enumerate(["mike", "chatora", "kuro", "shiro", "hachiware"])}
RING = {nm: cat.harness(HERO[nm], col) for nm, col in (("mike", (.75, .08, .06)), ("chatora", (.05, .3, .7)), ("kuro", (.95, .7, .1)))}


def show(names):
    for nm, c in HERO.items():
        on = nm in names
        for o in [c["root"]] + list(c["root"].children_recursive):
            o.hide_render = not on


class Rope:
    """胴輪の環 → 鼻先の連結器の綱（細い円柱。毎コマ位置と向きと長さを決める）"""
    def __init__(self, name):
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=False, segments=8, radius1=.0045, radius2=.0045, depth=1.0); bmesh.ops.translate(bm, vec=(0, 0, .5), verts=bm.verts)
        self.o = mesh_obj(name, bm, [mat("rope", (.72, .62, .45), .8)]); self.o.rotation_mode = "QUATERNION"

    def key(self, a, b, f):
        a, b = Vector(a), Vector(b); d = b - a; self.o.location = a; self.o.rotation_quaternion = d.to_track_quat("Z", "Y"); self.o.scale = (1, 1, d.length)
        for p in ("location", "rotation_quaternion", "scale"):
            self.o.keyframe_insert(p, frame=f + 1)


def nose(ty):
    return Vector((0, ty + .25, track.TOP + .55))


def base(y0=-120., y1=200., side=30., far=True, ncar=16):
    env_clear(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4); track.track_scene(y0, y1, side, far)
    S["T"] = train.build_train(ncar); train.place(S["T"], 0.0, track.TOP); track.haze(); sc.render.use_motion_blur = False
    show([])


S = {}


def grid_cats(n, y0, rows_w=25, dx=.12, dy=.6, seed=1, x0=0.0):
    """n 匹を線路の上に、横 rows_w 匹 × 縦に並べる（位置 N×2、柄 N）"""
    rnd = np.random.default_rng(seed); i = np.arange(n)
    x = x0 + (i % rows_w - (rows_w - 1) / 2) * dx + rnd.uniform(-.03, .03, n); y = y0 + (i // rows_w) * dy + rnd.uniform(-.12, .12, n)
    return np.stack([x, y], 1), rnd.integers(0, 6, n), rnd.uniform(0, 1, n)


def static_crowd(name, P, coat, mode, ks=None, z=Z_CAT, rot=None, hide_fn=None):
    N = len(P); F = np.array([fidx(c, mode, 0 if ks is None else ks[i]) for i, c in enumerate(coat)]); R = np.zeros(N) if rot is None else rot

    def fn(t):
        zz = np.full(N, z) if hide_fn is None else np.where(hide_fn(t), -60.0, z)
        return np.stack([P[:, 0], P[:, 1], zz], 1), R, F
    return crowd.Crowd(name, FR, fn)


# ================================================================ l00 / l10：1 匹で引く（冒頭と最後が同じ）
def s_l00():
    base(-200, 120); show(["mike"]); S["rope"] = Rope("rope0")


def _one_cat(t, f):
    c = HERO["mike"]; cat.cpose(c, pos=(0, 3.3, Z_CAT), heading=0.0, mode="pull", t=t, ph=t * .9, k=1.0, amp=.35, head=(-.08, 0))
    bpy.context.view_layer.update(); S["rope"].key(RING["mike"](), nose(0), f)


C00 = ((1.15, 4.65, 1.05), (0, 3.0, .85), 36)


def a_l00(u, t, f):
    _one_cat(t, f); p, at, l = C00; e = ease(u); cam.look(Vector(p) + Vector((.25, .3, .05)) * e, at, l)


def s_l10():
    base(-200, 120); show(["mike"]); S["rope"] = Rope("rope0")
    P, coat, ph = grid_cats(220, 4.6, 11, .2, .55, 9); S["c"] = static_crowd("cats", P, coat, "walk", ks=(ph * 8).astype(int) % 8, hide_fn=lambda t: np.full(len(P), t > 1.0))


def a_l10(u, t, f):
    _one_cat(t + SPLAN["l00"]["dur"] * 0, f); p, at, l = C00; e = ease(u); cam.look(Vector(p) + Vector((1.2, 2.5, .8)) * (1 - e), at, l)


# ================================================================ l01：猫の顔 → 新幹線を見上げる（大きな札 spec）
def s_l01():
    base(-200, 120); show(["mike"]); S["rope"] = Rope("rope0")


def a_l01(u, t, f):
    _one_cat(t, f); e = ease(cut(.15, .85, u))
    head = Vector((0, 3.3 + .28, Z_CAT + .3))
    p = Vector((.32, 3.3 + .75, Z_CAT + .32)).lerp(Vector((1.7, 6.8, .55)), e); at = head.lerp(Vector((0, 0, 2.6)), e)
    cam.look(p, at, 50 - 26 * e)


# ================================================================ l02：100 匹でもびくともしない（あくび・毛づくろい）
def s_l02():
    base(-200, 120); show(["mike", "chatora", "shiro"]); S["rope"] = Rope("rope0")
    P, coat, ph = grid_cats(100, 4.5, 10, .2, .55, 2); S["c"] = static_crowd("cats", P, coat, "pull", ks=(ph * 8).astype(int) % 8)


def a_l02(u, t, f):
    cat.cpose(HERO["mike"], pos=(.9, 6.2, Z_CAT), heading=-.2, mode="yawn", t=t, k=smooth(.8, 1.6, t) * (1 - smooth(3.4, 4.2, t)))
    cat.cpose(HERO["shiro"], pos=(-.75, 5.6, Z_CAT), heading=.4, mode="groom", t=t)
    cat.cpose(HERO["chatora"], pos=(.2, 3.4, Z_CAT), heading=0.0, mode="pull", t=t, ph=t * .9, amp=.3)
    bpy.context.view_layer.update(); S["rope"].key(RING["chatora"](), nose(0), f)
    e = ease(u); cam.look(Vector((2.4, 9.6, 1.0)).lerp(Vector((2.0, 8.8, .9)), e), (0, 4.6, .8), 30)


# ================================================================ l03：どんどん増やす → 約 1,100 匹で車輪が回る
TC3 = 4.2


def s_l03():
    base(-200, 160); show([])
    N = 1100; P, coat, ph = grid_cats(N, 2.6, 25, .12, .6, 3); order = np.argsort(np.random.default_rng(4).random(N)); born = np.empty(N); born[order] = np.linspace(-.2, 3.2, N) ** 1.0
    S["born"] = born; S["c"] = static_crowd("cats", P, coat, "pull", ks=(ph * 8).astype(int) % 8, hide_fn=lambda t: t < born)


def train_y3(t):
    return .5 * .25 * max(0., t - 3.3) ** 2        # 3.3 秒から、ゆっくり動き出す


def a_l03(u, t, f):
    ty = train_y3(t); train.place(S["T"], ty, track.TOP); keyp(S["T"]["root"], f, loc=tuple(S["T"]["root"].location))
    for w in S["T"]["wheels"]:
        w.keyframe_insert("rotation_euler", frame=f + 1)
    if t < TC3:
        e = ease(t / TC3); cam.look(Vector((5.0, 22, 3.0)).lerp(Vector((6.5, 30, 6.0)), e), (0, 12, 0), 28)
    else:
        cam.look((2.1, -1.0 + ty, .9), (.75, -2.95 + ty, track.TOP + .43), 40)


# ================================================================ l04：2,200 匹で進む（時速 2.4 km）
def s_l04():
    base(-200, 260); show(["mike", "kuro"]); S["ropes"] = [Rope("rope0"), Rope("rope1")]
    N = 2230; P, coat, ph = grid_cats(N, 3.4, 25, .12, .6, 5); S["P"] = P

    def fn(t):
        y = P[:, 1] + V * t; k = ((ph + t * 1.1) % 1 * 8).astype(int)
        return np.stack([P[:, 0], y, np.full(N, Z_CAT)], 1), np.zeros(N), np.array([fidx(c, "pull", kk) for c, kk in zip(coat, k)])
    S["c"] = crowd.Crowd("cats", FR, fn)


def a_l04(u, t, f):
    ty = V * t; train.place(S["T"], ty, track.TOP); keyp(S["T"]["root"], f, loc=tuple(S["T"]["root"].location))
    for w in S["T"]["wheels"]:
        w.keyframe_insert("rotation_euler", frame=f + 1)
    for (nm, x), rp in zip((("mike", 1.0), ("kuro", -1.05)), S["ropes"]):
        cat.cpose(HERO[nm], pos=(x, ty + 3.0, Z_CAT), heading=0.0, mode="pull", t=t, ph=t * 1.1 + (x > 0) * .5, amp=.7)
    bpy.context.view_layer.update()
    for (nm, rp) in zip(("mike", "kuro"), S["ropes"]):
        rp.key(RING[nm](), nose(ty), f)
    cam.look((3.6, ty + 5.0, 1.0), (0, ty + 3.6, .75), 30)


# ================================================================ l05：ひと休み（線路わきの草の上）
def s_l05():
    base(-200, 120); show(["mike", "chatora", "kuro", "shiro", "hachiware"])
    rnd = np.random.default_rng(8); n = 420; side = rnd.choice([-1, 1], n); x = side * rnd.uniform(3.0, 9.0, n); y = rnd.uniform(-60, 40, n)
    keep = ~((x > 1) & (x < 5) & (y > -1) & (y < 9)); P = np.stack([x, y], 1)[keep]; coat = rnd.integers(0, 6, len(P))
    md = rnd.choice(["loaf", "curl", "sit"], len(P)); F = np.array([fidx(c, m) for c, m in zip(coat, md)]); R = rnd.uniform(0, 6.28, len(P))
    S["c"] = crowd.Crowd("cats", FR, lambda t: (np.stack([P[:, 0], P[:, 1], np.zeros(len(P))], 1), R, F))


def a_l05(u, t, f):
    cat.cpose(HERO["mike"], pos=(2.9, 4.6, 0), heading=1.9, mode="loaf", t=t)
    cat.cpose(HERO["chatora"], pos=(3.6, 3.3, 0), heading=2.6, mode="stretch", t=t, k=smooth(.6, 1.6, t) * (1 - smooth(4.0, 5.2, t)))
    cat.cpose(HERO["shiro"], pos=(2.4, 2.4, 0), heading=-1.2, mode="groom", t=t)
    cat.cpose(HERO["kuro"], pos=(4.3, 5.6, 0), heading=2.2, mode="curl", t=t)
    cat.cpose(HERO["hachiware"], pos=(3.1, 6.6, 0), heading=-2.4, mode="sit", t=t, head=(.1, .3 * math.sin(t * .8)))
    e = ease(u); cam.look(Vector((5.4, 1.6, .95)).lerp(Vector((5.0, 2.1, .85)), e), (3.2, 4.4, .15), 32)


# ================================================================ l06：坂。2,230 → 3.7 万匹（線路を埋める猫の帯）
def s_l06():
    base(-120, 1100, 40); show([])
    sh = SPLAN["l06"]; N = PLAN["ng"]; P, coat, ph = grid_cats(int(N), 2.6, 25, .12, .6, 6)
    us = np.array([p[0] for p in sh["n"]]); ns = np.array([p[1] for p in sh["n"]]); dur = sh["dur"]
    idx = np.arange(int(N))
    S["c"] = static_crowd("cats", P, coat, "pull", ks=(ph * 8).astype(int) % 8, hide_fn=lambda t: idx >= np.interp(t / dur, us, ns))


def a_l06(u, t, f):
    e = ease(u); p = Vector((5, -8, 3.5)).lerp(Vector((25, -40, 60)), e ** 1.2); at = Vector((0, 20, 1)).lerp(Vector((0, 260, 0)), e)
    cam.look(p, at, 30 - 4 * e)


# ================================================================ l07：昼寝
def s_l07():
    base(-200, 120); show(["mike", "chatora", "shiro", "hachiware"])
    rnd = np.random.default_rng(9); n = 260; x = rnd.choice([-1, 1], n) * rnd.uniform(2.6, 8.0, n); y = rnd.uniform(-40, 30, n)
    keep = ~((x > 1) & (x < 5) & (y > 0) & (y < 8)); P = np.stack([x, y], 1)[keep]; coat = rnd.integers(0, 6, len(P))
    roof = np.stack([rnd.uniform(-.9, .9, 60), rnd.uniform(-60, -12, 60)], 1); rc = rnd.integers(0, 6, 60)      # 屋根の上でも
    F = np.array([fidx(c, rnd.choice(["curl", "loaf"]), int(rnd.integers(0, 2)) if False else 0) for c in coat]); R = rnd.uniform(0, 6.28, len(P))
    S["c"] = crowd.Crowd("cats", FR, lambda t: (np.stack([P[:, 0], P[:, 1], np.zeros(len(P))], 1), R, F))
    S["c2"] = crowd.Crowd("roofcats", FR, lambda t: (np.stack([roof[:, 0], roof[:, 1], np.full(60, track.TOP + train.H + .02)], 1), rnd.uniform(0, 6.28, 60), np.array([fidx(c, "curl") for c in rc])))


def a_l07(u, t, f):
    cat.cpose(HERO["mike"], pos=(2.8, 4.2, 0), heading=2.0, mode="curl", t=t)
    cat.cpose(HERO["chatora"], pos=(3.25, 4.5, 0), heading=-1.0, mode="curl", t=t + 1.1)
    cat.cpose(HERO["shiro"], pos=(3.6, 5.8, 0), heading=.6, mode="loaf", t=t, lid=1.0, ears=(.25 * smooth(2.4, 2.6, t) * (1 - smooth(2.7, 2.9, t)), 0))
    cat.cpose(HERO["hachiware"], pos=(2.4, 5.5, 0), heading=3.0, mode="curl", t=t + 2.0)
    e = ease(u); cam.look(Vector((4.6, 2.4, 1.0)).lerp(Vector((4.1, 2.9, .85)), e), (3.0, 4.8, .1), 36)


# ================================================================ l09：結果（大きな札 result）
def s_l09():
    base(-200, 260); show([])
    N = 2230; P, coat, ph = grid_cats(N, 3.4, 25, .12, .6, 5); S["c"] = static_crowd("cats", P, coat, "pull", ks=(ph * 8).astype(int) % 8)


def a_l09(u, t, f):
    e = ease(u); cam.look(Vector((10, 52, 8)).lerp(Vector((9, 48, 7)), e), (0, 16, -2), 28)


# ---------------------------------------------------------------- 書き出し
SHOTS3 = [k for k in NAMES if k != "l08"]
ANIM = [cam.o] + cat.CANIM


def _wrap(a):
    def w(u, t, f):
        if f % 20 == 0:
            log("anim frame", f)
        a(u, t, f)
        for o in cat.CANIM:
            o.keyframe_insert("scale", frame=f + 1)
    return w


SHOTS = {k: (globals()["s_" + k], _wrap(globals()["a_" + k])) for k in SHOTS3}

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
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
