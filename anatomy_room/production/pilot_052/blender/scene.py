"""pilot_052「ハムスターの回し車で、東京の電気をまかなうには何匹？」の 3D（Blender Cycles）。l08（広さの図）は画面の図。
blender -b -P blender/scene.py -- l00 [l01 …] [--still] [--samples N] [--resume]
試し描き：AT="0.5,2.0" で、指定のショットのその秒だけを work/test/<ショット>_<秒>.png に（PCT で解像度 %）。
部品：hamster.py（Sketchfab の CC BY のハムスター・自作の回し車）、track.py・train.py・crowd.py（051）、city.py（050）。
霞の発光は照明として扱わない（common.add_haze、2026-11-12：1 コマ約 6 倍速）。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, train, crowd, hamster, city

NAMES = [s["id"] for s in PLAN["shots"]]
DECK = .45                                    # 縁側の床の高さ
S = {}


# ---------------------------------------------------------------- 群れ：回し車＋走るハムスターを 8 コマ分の形に固める（051 の群れの仕組み）
def bake_runner(n=8):
    names = [f"hw_run_{k}" for k in range(n)]; c_ = track.cached(names)
    if c_:
        return c_
    W = hamster.Wheel("tmpw"); H = hamster.Hamster("tmph"); W.place((0, 0, 0), math.pi / 2); out = []
    for k in range(n):
        W.spin(-k / n * (2 * math.pi / 30) * 4); bpy.context.view_layer.update()
        H.pose(tuple(W.runner_pos()), -math.pi / 2, "run", k / n / 6.0); bpy.context.view_layer.update()
        objs = [o for o in bpy.data.objects if o.type == "MESH" and (o.name.startswith("tmpw") or any(p.name.startswith("tmph") for p in o.children_recursive) or _under(o, H.root))]
        o = crowd._join_eval(objs, names[k]); track._patch_col().objects.link(o); out.append(o)
    for o in list(bpy.data.objects):
        if o.name.startswith(("tmpw", "tmph")) or _under(o, H.root) or _under(o, W.root):
            bpy.data.objects.remove(o, do_unlink=True)
    track.DIRTY[0] = True; track.save_cache(); return out


def _under(o, root):
    p = o
    while p is not None:
        if p == root:
            return True
        p = p.parent
    return False


FR = bake_runner()


def wheels_crowd(name, P, heading, born=None, scale=1.0, z=0.0):
    """回し車の群れ（P：N×2、heading：向き、born：見え始める時刻）。形は 8 コマを時刻でずらして回す"""
    N = len(P); ph = np.random.default_rng(len(P)).uniform(0, 8, N); R = np.full(N, heading)

    def fn(t):
        zz = np.full(N, z) if born is None else np.where(t < born, -60.0, z)
        return np.stack([P[:, 0], P[:, 1], zz], 1), R, ((ph + t * 24) % 8).astype(int)
    return crowd.Crowd(name, FR, fn, scale=np.full(N, scale))


# ---------------------------------------------------------------- 縁側（自作：木の床・柱・障子、庭は 051 の草の区画）
def engawa():
    track.world_hdri("kloofendal_48d_partly_cloudy_puresky", rot=float(os.environ.get("HROT", "150")), exposure=.15)
    deck = track.pbr("wood_floor_deck", 1.2, 0.0, tint=(1.0, .85, .65), name="deck")
    track.plane("deck", -4, 4, -.3, 2.2, DECK, deck, 4, 2); city.box("deck_edge", -4, 4, -.36, -.3, 0, DECK, deck)
    wall = track.pbr("plastered_wall", 1.0, 0.0, tint=(.95, .92, .85), name="wall"); wood = track.pbr("weathered_planks", 2.0, 0.0, tint=(.55, .4, .28), name="beam")
    city.box("wall", -4, 4, 2.2, 2.3, DECK, DECK + 2.4, wall)
    for x in np.arange(-3.6, 4, .9):                         # 障子の桟（白い紙の上に木の格子）
        city.box(f"shoji_v{x:.1f}", x - .015, x + .015, 2.15, 2.2, DECK, DECK + 1.9, wood)
    for zz in np.arange(DECK + .3, DECK + 1.9, .32):
        city.box(f"shoji_h{zz:.2f}", -4, 4, 2.15, 2.2, zz - .012, zz + .012, wood)
    for x in (-3.9, -1.9, 1.9, 3.9):
        city.box(f"post{x}", x - .06, x + .06, 1.55, 1.67, 0, DECK + 2.6, wood)
    city.box("eave", -4, 4, 1.5, 2.3, DECK + 2.6, DECK + 2.7, wood)      # 軒は短く：回し車に日が当たる（画面は昼のように明るく）
    track.field(-30, 30, -40, -.36, 120., 7, "garden"); track.trees([(x, y) for x, y in ((-9, -14), (6, -18), (14, -9), (-16, -25), (2, -30))], 8)
    plane_far = track.plane("garden_far", -800, 800, -900, -40, -.02, track.pbr("grass_path_2", .08, 0.0, tint=(.6, .8, .45), name="far_grass2", spec=.1))
    track.haze()


def bulb(name, pos):
    """豆電球（ガラス球の中にフィラメント）。返り値：フィラメントの光の強さの socket"""
    g = mat(name + "_glass", (.95, .95, .95), .02); b = g.node_tree.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.45
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.012); o = mesh_obj(name, bm, [g]); o.location = Vector(pos) + Vector((0, 0, .03))
    fil = emat(name + "_fil", (1, .55, .2), .5, (1, .62, .25), 0.0, haze=False)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.0012, radius2=.0012, depth=.008); f_ = mesh_obj(name + "_f", bm, [fil]); f_.location = Vector(pos) + Vector((0, 0, .03)); f_.rotation_euler = (0, math.pi / 2, 0)
    base_m = mat(name + "_brass", (.8, .6, .3), .3, 1.0)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=.007, radius2=.007, depth=.014); bmesh.ops.translate(bm, vec=(0, 0, .012), verts=bm.verts)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=.025, radius2=.025, depth=.006); s_ = mesh_obj(name + "_base", bm, [base_m]); s_.location = Vector(pos)
    lt = bpy.data.lights.new(name + "_light", "POINT"); lt.energy = 0.0; lt.color = (1, .7, .4); lt.shadow_soft_size = .01; lo = link(bpy.data.objects.new(name + "_light", lt)); lo.location = Vector(pos) + Vector((0, 0, .03))
    return esock(fil), lt


def key_bulb(b, k, f):
    sock, lt = b; key_v(sock, 40.0 * k, f); lt.energy = 2.5 * k; lt.keyframe_insert("energy", frame=f + 1)


def hero_wheel(name, x, y=.45):
    W = hamster.Wheel(name); W.place((x, y, DECK), math.pi / 2); H = hamster.Hamster(name + "_h"); return W, H


def run_hero(W, H, t, f, on=1.0, ph0=0.0):
    a = -(t + ph0) * 5.0 * on; W.spin(a); W.ring.keyframe_insert("rotation_euler", frame=f + 1); bpy.context.view_layer.update()
    H.pose(tuple(W.runner_pos()), -math.pi / 2, "run" if on > 0 else "curl", t + ph0, 1.0)


def base_common():
    env_clear(); sc.render.use_motion_blur = False
    for o in list(MONC.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    S.clear()


# ================================================================ l00 / l10：縁側の 1 匹
def s_l00():
    base_common(); engawa(); S["W"], S["H"] = hero_wheel("w0", -.05); S["b"] = bulb("bulb", (.17, .62, DECK))


C00 = ((.07, 1.15, .62), (.04, .52, .57), 34)


def a_l00(u, t, f):
    run_hero(S["W"], S["H"], t, f); key_bulb(S["b"], .015, f)
    e = ease(u); p, at, l = C00; cam.look(Vector(p) + Vector((-.04, -.08, 0)) * e, at, l)


def s_l10():
    s_l00()


def a_l10(u, t, f):
    run_hero(S["W"], S["H"], t, f); key_bulb(S["b"], .015, f)
    e = ease(u); p, at, l = C00; cam.look(Vector(p) + Vector((.25, .35, .08)) * (1 - e), at, l)


# ================================================================ l01：走るハムスターの寄り（大きな札 spec）
def s_l01():
    s_l00()


def a_l01(u, t, f):
    run_hero(S["W"], S["H"], t, f); key_bulb(S["b"], .015, f)
    e = ease(u); cam.look(Vector((.12, .95, .56)).lerp(Vector((.2, 1.25, .62)), e), Vector((0, .45, .54)), 70 - 25 * e)


# ================================================================ l02：4 台で豆電球がつく
TB2 = 2.3


def s_l02():
    base_common(); engawa(); S["b"] = bulb("bulb", (.0, .25, DECK)); S["WH"] = [hero_wheel(f"w{i}", x, .6) for i, x in enumerate((-.55, -.2, .2, .55))]


def a_l02(u, t, f):
    for i, (W, H) in enumerate(S["WH"]):
        a = clamp((t - (0, .35, .7, 1.05)[i]) / .3)      # 1 台ずつ現れる（下から）
        W.root.scale = (a, a, a) if a > 0 else (.001, .001, .001); keyp(W.root, f, scale=tuple(W.root.scale))
        H.root.scale = W.root.scale; keyp(H.root, f, scale=tuple(H.root.scale))
        run_hero(W, H, t, f, 1.0, i * .37)
    key_bulb(S["b"], .015 + .985 * smooth(TB2, TB2 + .25, t), f)
    e = ease(u); cam.look(Vector((0, 2.2, .9)).lerp(Vector((0, 1.95, .8)), e), (0, .4, .58), 26)


# ================================================================ l03：地方の一軒家（古民家）と、庭・あぜを埋める回し車
def minka(pos, rot=0.0, h=11.0, name="minka"):
    new, meshes, lo, hi = hamster._import("minka_juoda"); r = hamster._holder(name, new, lo, hi, h); r.location = Vector(pos); r.rotation_euler = (0, 0, rot); return r


def s_l03():
    base_common(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4)
    track.field(-60, 60, -60, 60, 25., 11, "yard"); track.plane("far3", -3000, 3000, -3000, 3000, -.03, track.paddy_mat()); track.hills()
    track.trees([(x, y) for x, y in ((-30, 25), (-35, 18), (28, 30), (34, 22), (-20, -40), (40, -35))], 12); minka((0, 0, 0), .3); track.haze()
    rnd = np.random.default_rng(5); n = int(PLAN["nh"]); P = []
    while len(P) < n:                                         # 家のまわりの庭とあぜ（家の上には置かない）
        x, y = rnd.uniform(-34, 34), rnd.uniform(-34, 34)
        if abs(x) < 9 and abs(y) < 12:
            continue
        P.append((round(x / .34) * .34, round(y / .34) * .34))
    P = np.unique(np.array(P), axis=0)[:n]; d = np.hypot(P[:, 0], P[:, 1]); born = .3 + 3.6 * (d - d.min()) / (d.max() - d.min())
    S["c"] = wheels_crowd("wheels", P, math.pi / 2, born)


def a_l03(u, t, f):
    e = ease(u); ang = .6 + .5 * e; r = 46 - 8 * e
    cam.look((r * math.cos(ang), -r * math.sin(ang), 26 - 6 * e), (0, 0, 2), 30)


# ================================================================ l04：ひと休み（丸くなって寝る → 隣が回り出す）
def s_l04():
    base_common(); engawa(); S["WH"] = [hero_wheel(f"w{i}", x, .55) for i, x in enumerate((-.32, .0, .32))]


def a_l04(u, t, f):
    for i, (W, H) in enumerate(S["WH"]):
        if i == 2:                                            # 交代の組：3 秒から走り出す
            on = smooth(3.0, 3.6, t); a = -max(0., t - 3.0) ** 1.4 * 5.0 * on; W.spin(a); W.ring.keyframe_insert("rotation_euler", frame=f + 1); bpy.context.view_layer.update()
            H.pose(tuple(W.runner_pos()), -math.pi / 2, "run" if t > 3.0 else "sit", t, 1.0)
        else:
            W.spin(.2 * i); W.ring.keyframe_insert("rotation_euler", frame=f + 1); bpy.context.view_layer.update()
            H.pose(tuple(W.runner_pos()), -math.pi / 2 + .5 * i, "curl", t + i, 1.0)
    e = ease(u); cam.look(Vector((-.25, 1.05, .62)).lerp(Vector((.1, 1.15, .66)), e), (0, .55, .52), 40)


# ================================================================ l05：町全体（田んぼと空き地を埋める回し車）
def s_l05():
    base_common(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4)
    track.plane("far5", -4000, 4000, -4000, 4000, -.03, track.paddy_mat()); track.hills(); track.haze()
    rnd = np.random.default_rng(6)
    for i in range(14):
        minka((rnd.uniform(-160, 160), rnd.uniform(-60, 260), 0), rnd.uniform(0, 6.28), rnd.uniform(9, 12), f"minka{i}")
    track.trees([(rnd.uniform(-250, 250), rnd.uniform(-80, 400)) for _ in range(90)], 13)
    P = []; g = .34                                             # 田んぼの区画（30×20 m）を順に埋める：近い区画から
    for by in range(-2, 9):
        for bx in range(-6, 7):
            if rnd.random() < .25:
                continue
            x0, y0 = bx * 32, by * 22
            xs = np.arange(x0 + 1, x0 + 30, g * 1.0); ys = np.arange(y0 + 1, y0 + 20, g * 1.0)
            X, Y = np.meshgrid(xs, ys); P.append(np.stack([X.ravel(), Y.ravel()], 1))
    P = np.concatenate(P); d = np.hypot(P[:, 0] * .8, P[:, 1] + 30); born = .2 + 4.4 * (d - d.min()) / (d.max() - d.min())
    log("l05 wheels", len(P)); S["c"] = wheels_crowd("wheels", P, math.pi / 2, born)


def a_l05(u, t, f):
    e = ease(u); cam.look(Vector((-30, -120, 60)).lerp(Vector((-10, -150, 95)), e), Vector((0, 60, 0)), 30)


# ================================================================ l06：上京（田園を走る新幹線、051 の部品）
def s_l06():
    base_common(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4); track.track_scene(-600, 400, 30, True)
    S["T"] = train.build_train(16); track.haze()      # 動きのぶれは入れない（入れると 1 コマ約 100 秒）


def a_l06(u, t, f):
    ty = -40 + 32 * t; train.place(S["T"], ty, track.TOP); keyp(S["T"]["root"], f, loc=tuple(S["T"]["root"].location))
    cam.look((9, 40, 2.2), (0, 10, 2.4), 28)


# ================================================================ l07 / l09：東京（ビル街の道と屋上を埋める回し車）
def s_l07():
    base_common(); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.4); city.street(y0=-200, y1=1600, far=True); track.haze()
    g = .34; xs = np.arange(-14.6, 14.6, g); ys = np.arange(-180, 1500, g); X, Y = np.meshgrid(xs, ys); P = np.stack([X.ravel(), Y.ravel()], 1)
    rnd = np.random.default_rng(7); P = P[rnd.random(len(P)) < .9]; born = .2 + 4.0 * (P[:, 1] - P[:, 1].min()) / (P[:, 1].max() - P[:, 1].min()) ** 1.0
    log("l07 wheels", len(P)); S["c"] = wheels_crowd("wheels", P, math.pi / 2, born)


def a_l07(u, t, f):
    e = ease(u); cam.look(Vector((0, -60, 30)).lerp(Vector((20, -120, 140)), e), Vector((0, 200, 0)).lerp(Vector((0, 600, 0)), e), 28)


def s_l09():
    s_l07()


def a_l09(u, t, f):
    e = ease(u); cam.look(Vector((20, -120, 140)).lerp(Vector((22, -130, 150)), e), Vector((0, 600, 0)), 28)


# ---------------------------------------------------------------- 書き出し
SHOTS3 = [k for k in NAMES if k not in ("l08", "l06")]      # l06・l08 は画面の図（l06 は 3D だと 1 コマ 38 秒かかったため図に）
ANIM = [cam.o]
SHOTS = {k: (globals()["s_" + k], (lambda a: (lambda u, t, f: (log("anim frame", f) if f % 30 == 0 else None, a(u, t, f), _keyham(f))))(globals()["a_" + k])) for k in SHOTS3}


def _keyham(f):
    for o in MONC.objects:
        if o.type == "EMPTY" or o.name.endswith(("_lid-1", "_lid1")):
            for p in ("location", "rotation_euler", "scale"):
                o.keyframe_insert(p, frame=f + 1)


if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
    for name in O["shots"]:
        setup, anim = SHOTS[name]; n = int(math.ceil(SPLAN[name]["dur"] * K.FPS)) + 2
        cam.o.animation_data_clear(); setup()
        for f in range(n):
            anim(f / max(1, n - 3), f / K.FPS, f)
            for path in ("location", "rotation_quaternion"):
                cam.o.keyframe_insert(path, frame=f + 1)
            cam.o.data.keyframe_insert("lens", frame=f + 1)
        for at in ats:
            sc.frame_set(int(round(at * K.FPS)) + 1); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            bpy.ops.render.render(write_still=True); log("test", name, at)
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
