"""pilot_048（東京に体長500mのポメラニアンが現れたら？）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計の既定。
使い方："C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P anatomy_room/production/pilot_048/blender/scene.py -- [ショット名 ...] [--still] [--samples N] [--every N] [--resume]
前もって python plan.py（blender/plan.json）、python production_script.py voice（work/timeline.json）。地図は pilot_047 の work/maps を使う。

ポメラニアン：本物（体高 21 cm）の寸法で、部品（胴・頭・あご・舌・足 4 本・しっぽ）ごとにメタボールで作ってメッシュにし、
それぞれにパーティクルの毛（Principled Hair BSDF、メラニンでオレンジ）を生やす。毛が部品の継ぎ目を隠す。全体を 2,381 倍（plan.json の sim.scale）。
部品は回転だけで動かす（歩く・しゃがむ・片足を上げる・ブルブル・おじぎ・走る・へそ天・首をかしげる・口を開ける）。
街：ショットごとに、まわり数 km の建物（1 つのメッシュ、窓の模様）を作り、遠くは地面の模様（pilot_047 の関東の人の光で街の濃さ）。
名所（模式）：渋谷のスクランブル交差点・東京ドーム・スカイツリー・東京タワー・代々木公園の森・新宿の高層ビル。
座標：都庁が原点、x が東、y が北（m）。閃光は使わない。血は出さない。人は顔のないピクトグラム。
"""
import sys, os, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import blkit as K
import time as _time
_T0 = _time.time()


def log(*a):
    print(f"[{_time.time() - _T0:7.1f}s]", *a, flush=True)

O = K.args()
sc = K.setup(O["samples"])
sc.cycles_curves.shape = "RIBBONS"   # 毛は平たいリボンで描く（太さのある管より速い）
sc.cycles.volume_step_rate = 12.0; sc.cycles.volume_max_steps = 64; sc.cycles.adaptive_threshold = .05   # 霧と土煙は粗い刻みで（1 コマ 60 秒 → 短縮）
sky = K.Sky(); cam = K.Cam()
PLAN = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8"))
SPLAN = {s["id"]: s for s in PLAN["shots"]}
SIM = PLAN["sim"]
KS = SIM["scale"]                       # 2,381 倍
MAPS = os.path.join(HERE, "..", "..", "pilot_047", "work", "maps")
INFO = json.load(open(os.path.join(MAPS, "maps.json"), encoding="utf-8"))
RND = random.Random(48)

# 名所（都庁からの m。緯度経度から：1 度＝南北 111.0 km・東西 90.4 km）
def ll(lat, lon):
    return Vector(((lon - 139.6917) * 90400, (lat - 35.6896) * 111000, 0))


YOYOGI = ll(35.6717, 139.6949); SHIBUYA = ll(35.6595, 139.7005); DOME = ll(35.7056, 139.7519)
SKYTREE = ll(35.7101, 139.8107); TOWER = ll(35.6586, 139.7454); SHINJUKU = ll(35.6896, 139.7006)

# ---------------------------------------------------------------- 空気のかすみ（pilot_047 と同じ：遠くの物は空の色に）
_wn = sc.world.node_tree; _wbg = _wn.nodes["Background"]
WMIX = _wn.nodes.new("ShaderNodeMix"); WMIX.data_type = "RGBA"; _wn.links.new(sky.node.outputs[0], WMIX.inputs[6]); _wn.links.new(WMIX.outputs[2], _wbg.inputs[0])
HAZE = []


def add_haze(m, d0=800., d1=16000., top=.85):
    n = m.node_tree.nodes; L = m.node_tree.links; out = n["Material Output"]; src = out.inputs["Surface"].links[0].from_socket
    cd = n.new("ShaderNodeCameraData"); mr = n.new("ShaderNodeMapRange"); mr.inputs[1].default_value = d0; mr.inputs[2].default_value = d1; mr.inputs[4].default_value = top
    L.new(cd.outputs["View Distance"], mr.inputs[0])
    em = n.new("ShaderNodeEmission"); ms = n.new("ShaderNodeMixShader"); L.new(mr.outputs[0], ms.inputs[0]); L.new(src, ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2]); L.new(ms.outputs[0], out.inputs["Surface"])
    HAZE.append((em, mr))


def set_haze(col, k, d0=800., d1=16000.):
    WMIX.inputs[7].default_value = (*col, 1); WMIX.inputs[0].default_value = 0.0; _wbg.inputs[1].default_value = 1.0
    for em, mr in HAZE:
        em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = k; mr.inputs[1].default_value = d0; mr.inputs[2].default_value = d1


def clamp(v, a=0., b=1.):
    return max(a, min(b, v))


def ease(u):
    return K.ease(u)


def lerp(a, b, u):
    return a + (b - a) * u


def keyp(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f + 1)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f + 1)
    if scale is not None:
        o.scale = scale if isinstance(scale, tuple) and len(scale) == 3 else (scale,) * 3; o.keyframe_insert("scale", frame=f + 1)


def key_v(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f + 1)


def shake(f, amp, seed=0):
    r = random.Random(f * 7 + seed); return Vector(((r.random() - .5) * amp, (r.random() - .5) * amp, (r.random() - .5) * amp * .6))


MATS = {}


def mat(name, col, rough=.5, metal=0., haze=True):
    if name in MATS:
        return MATS[name]
    m = K.mat(name, col, rough, metal)
    if haze:
        add_haze(m)
    MATS[name] = m; return m


# ---------------------------------------------------------------- 場面ごとに作り直す物（env）
ENV = bpy.data.collections.new("env"); sc.collection.children.link(ENV)


def env_clear():
    for o in list(ENV.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves):
        for m in list(coll):
            if m.users == 0:
                coll.remove(m)


def link(o):
    ENV.objects.link(o); return o


def mesh_obj(name, bm, mats):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    return link(bpy.data.objects.new(name, me))


# ---------------------------------------------------------------- 街の材料
def facade(name, wall, glass, lit=0.0):
    """窓の格子（世界座標のレンガ模様、1 単位＝4 m）。屋根は別の材料"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    geo = t.nodes.new("ShaderNodeNewGeometry"); br = t.nodes.new("ShaderNodeTexBrick")
    br.offset = 0; br.squash = 1; br.inputs["Scale"].default_value = .25
    br.inputs["Mortar Size"].default_value = .3; br.inputs["Brick Width"].default_value = .8; br.inputs["Row Height"].default_value = .95
    br.inputs["Color1"].default_value = (*glass, 1); br.inputs["Color2"].default_value = (*[c * 1.15 for c in glass], 1); br.inputs["Mortar"].default_value = (*wall, 1)
    t.links.new(geo.outputs["Position"], br.inputs["Vector"]); t.links.new(br.outputs["Color"], b.inputs["Base Color"])
    rr = t.nodes.new("ShaderNodeMapRange"); rr.inputs[3].default_value = .12; rr.inputs[4].default_value = .7
    t.links.new(br.outputs["Fac"], rr.inputs[0]); t.links.new(rr.outputs[0], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = .15
    add_haze(m); MATS[name] = m; return m


def city_mats():
    return [facade("fa0", (.34, .34, .35), (.05, .07, .1)), facade("fa1", (.44, .41, .37), (.08, .1, .13)),
            facade("fa2", (.24, .26, .29), (.04, .06, .09)), facade("fa3", (.5, .48, .45), (.1, .12, .15)),
            facade("fa4", (.38, .31, .26), (.06, .07, .09)), mat("roof", (.27, .27, .27), .85)]


def ground_mat(name="ground", ruin=0.0):
    """道路の格子（140 m の街区、道幅 20 m）。ruin：1＝がれきの茶色い灰色"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    geo = t.nodes.new("ShaderNodeNewGeometry"); br = t.nodes.new("ShaderNodeTexBrick")
    br.offset = 0; br.squash = 1; br.inputs["Scale"].default_value = 1 / 140
    br.inputs["Mortar Size"].default_value = .14; br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 1.0
    blk = (.42, .4, .37) if not ruin else (.36, .32, .28); road = (.16, .16, .17) if not ruin else (.3, .27, .24)
    br.inputs["Color1"].default_value = (*blk, 1); br.inputs["Color2"].default_value = (*[c * .85 for c in blk], 1); br.inputs["Mortar"].default_value = (*road, 1)
    L.new(geo.outputs["Position"], br.inputs["Vector"])
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = .002; L.new(geo.outputs["Position"], nz.inputs["Vector"])
    mx = t.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = .6
    L.new(br.outputs["Color"], mx.inputs[6]); L.new(nz.outputs["Color"], mx.inputs[7]); L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .9
    add_haze(m, 1500., 30000., .9); MATS[name] = m; return m


def ground(size=400000., center=(0, 0), ruin=False, z=0.):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    o = mesh_obj("ground", bm, [ground_mat("ground_ruin" if ruin else "ground", 1 if ruin else 0)]); o.location = (center[0], center[1], z); return o


# 一度に組み立てる（bmesh で 1 つずつ足すと、物が増えるほど遅くなる）
CUBE_V = np.array([(x, y, z) for z in (-.5, .5) for y in (-.5, .5) for x in (-.5, .5)], float)
CUBE_F = np.array([(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)])   # 下・上・南・北・西・東
CUBE_TOP = np.array([0, 1, 0, 0, 0, 0], bool)


def _template(kind):
    bm = bmesh.new()
    if kind == "ico":
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    elif kind == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=1.0, radius2=.8, depth=1.0)
    v = np.array([tuple(x.co) for x in bm.verts], float); f = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free(); return v, f


def instances(name, tv, tf, xf, mats, mi=None):
    """tv（頂点）・tf（面）の型を、xf：N×(位置3・大きさ3・Z の回転・傾き X・傾き Y) の分だけ並べた 1 つのメッシュ。mi：N の材料番号（面ごとなら N×F）"""
    xf = np.asarray(xf, float); N = len(xf)
    if N == 0:
        return None
    v = tv[None] * xf[:, None, 3:6]
    for col, axis in ((7, 0), (8, 1)):
        a = xf[:, col][:, None]; c, s_ = np.cos(a), np.sin(a)
        if axis == 0:
            y, z = v[..., 1].copy(), v[..., 2].copy(); v[..., 1] = y * c - z * s_; v[..., 2] = y * s_ + z * c
        else:
            x, z = v[..., 0].copy(), v[..., 2].copy(); v[..., 0] = x * c + z * s_; v[..., 2] = -x * s_ + z * c
    a = xf[:, 6][:, None]; c, s_ = np.cos(a), np.sin(a); x, y = v[..., 0].copy(), v[..., 1].copy(); v[..., 0] = x * c - y * s_; v[..., 1] = x * s_ + y * c
    v += xf[:, None, 0:3]
    nv = len(tv); faces = [tuple(i * nv + k for k in fc) for i in range(N) for fc in tf]
    me = bpy.data.meshes.new(name); me.from_pydata(v.reshape(-1, 3).tolist(), [], faces); me.update()
    for m in mats:
        me.materials.append(m)
    if mi is not None:
        mi = np.asarray(mi)
        idx = (mi[:, None].repeat(len(tf), 1) if mi.ndim == 1 else mi).reshape(-1)
        me.polygons.foreach_set("material_index", idx.astype(np.int32))
    return link(bpy.data.objects.new(name, me))


def city(cx, cy, R, seed=1, hfn=None, hole=None, ruin=False, dens=1.0):
    """まわり R m の建物を 1 つのメッシュに。hfn(x, y, rnd)→高さ。hole：[(x, y, r)] の円には建てない"""
    rnd = random.Random(seed); ms = city_mats() if not ruin else [mat("rubble", (.34, .31, .28), .95), mat("rubble2", (.26, .25, .24), .95)]
    B = 140.0; i0, i1 = int((cx - R) // B), int((cx + R) // B) + 1; j0, j1 = int((cy - R) // B), int((cy + R) // B) + 1
    xf, mi = [], []
    for i in range(i0, i1):
        for j in range(j0, j1):
            bx, by = (i + .5) * B, (j + .5) * B
            if (bx - cx) ** 2 + (by - cy) ** 2 > R * R or rnd.random() > dens:
                continue
            if hole and any((bx - hx) ** 2 + (by - hy) ** 2 < hr * hr for hx, hy, hr in hole):
                continue
            n = rnd.choice((1, 2, 2, 3, 4, 4, 6))
            for _ in range(n):
                w = rnd.uniform(14, 52); d = rnd.uniform(14, 52)
                x = bx + rnd.uniform(-60 + w / 2, 60 - w / 2); y = by + rnd.uniform(-60 + d / 2, 60 - d / 2)
                h = rnd.uniform(1.5, 9) if ruin else (hfn(x, y, rnd) if hfn else rnd.lognormvariate(math.log(16), .55))
                rz = rnd.choice((0, 0, 0, rnd.uniform(-.3, .3)))
                tx, ty = (rnd.uniform(-.4, .4), rnd.uniform(-.4, .4)) if ruin else (0, 0)
                xf.append((x, y, h / 2 - (1.0 if ruin else 0), w, d, h, rz, tx, ty))
                m_ = rnd.randrange(len(ms) - (0 if ruin else 1))
                mi.append(np.where(CUBE_TOP & (not ruin), len(ms) - 1, m_))
    log("city", len(xf), "buildings")
    return instances("city", CUBE_V, CUBE_F, xf, ms, np.array(mi))


def downtown(cores):
    """cores：[(x, y, 半径, 最高の高さ)]。中心ほど高いビルが多い"""
    def h(x, y, rnd):
        base = rnd.lognormvariate(math.log(15), .5)
        for cx, cy, r, hm in cores:
            k = math.exp(-((x - cx) ** 2 + (y - cy) ** 2) / (r * r))
            if rnd.random() < .55 * k:
                base = max(base, rnd.uniform(.3, 1.0) * hm * (.4 + .6 * k))
        return base
    return h


def trees(cx, cy, w, h, n, seed=2):
    """森（低い球を散らす。1 つのメッシュ）"""
    rnd = random.Random(seed); tv, tf = _template("ico"); xf = []
    for _ in range(n):
        x, y = cx + rnd.uniform(-w / 2, w / 2), cy + rnd.uniform(-h / 2, h / 2); r = rnd.uniform(4, 9)
        xf.append((x, y, r * .9, r, r, r * rnd.uniform(.8, 1.3), 0, 0, 0))
    bm2 = bmesh.new(); bmesh.ops.create_grid(bm2, x_segments=1, y_segments=1, size=.5); bmesh.ops.scale(bm2, vec=(w, h, 1), verts=bm2.verts); bmesh.ops.translate(bm2, vec=(cx, cy, .3), verts=bm2.verts)
    mesh_obj("lawn", bm2, [mat("lawn", (.12, .2, .08), .9)])
    return instances("trees", tv, tf, xf, [mat("leaf", (.05, .14, .05), .8)])


def lathe(name, prof, m, segs=64, loc=(0, 0, 0), rot=0.0):
    bm = bmesh.new(); vs = [bm.verts.new((r, 0, z)) for r, z in prof]
    for a, b_ in zip(vs, vs[1:]):
        bm.edges.new((a, b_))
    bmesh.ops.spin(bm, geom=bm.verts[:] + bm.edges[:], cent=(0, 0, 0), axis=(0, 0, 1), angle=2 * math.pi, steps=segs, use_duplicate=False)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=.01)
    o = mesh_obj(name, bm, [m]); o.location = loc; o.rotation_euler = (0, 0, rot)
    for p in o.data.polygons:
        p.use_smooth = segs > 8
    return o


def skytree(p):
    prof = [(34, 0), (31, 80), (26, 180), (21, 300), (18.5, 340), (22, 342), (22, 372), (17, 376), (15, 440), (18, 443), (18, 455), (13, 460), (8, 500), (4.5, 590), (2.2, 634), (0, 634.5)]
    m = MATS.get("skyt") or facade("skyt", (.8, .84, .88), (.55, .6, .66))
    return lathe("skytree", prof, m, 48, tuple(p))


def tokyo_tower(p):
    m = MATS.get("ttower")
    if not m:
        m = bpy.data.materials.new("ttower"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
        geo = t.nodes.new("ShaderNodeNewGeometry"); sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(geo.outputs["Position"], sep.inputs[0])
        mth = t.nodes.new("ShaderNodeMath"); mth.operation = "PINGPONG"; mth.inputs[1].default_value = 16.0; t.links.new(sep.outputs[2], mth.inputs[0])
        ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
        ramp.color_ramp.elements[0].position = 0; ramp.color_ramp.elements[0].color = (.85, .2, .05, 1)
        ramp.color_ramp.elements[1].position = .62 / 16 * 16 / 16 if False else .5; ramp.color_ramp.elements[1].color = (.9, .9, .88, 1)
        dv = t.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 16.0; t.links.new(mth.outputs[0], dv.inputs[0]); t.links.new(dv.outputs[0], ramp.inputs[0])
        t.links.new(ramp.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .5; b.inputs["Metallic"].default_value = .3
        add_haze(m); MATS["ttower"] = m
    prof = [(48, 0), (32, 40), (20, 100), (14, 140), (19, 142), (19, 156), (11, 158), (7, 220), (9, 222), (9, 228), (4.5, 232), (2, 300), (.8, 333), (0, 333.5)]
    root = link(bpy.data.objects.new("tower_root", None)); root.location = tuple(p)
    o = lathe("tower", prof, m, 4, (0, 0, 0), math.pi / 4); o.parent = root
    return root


def dome(p):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -.01], context="VERTS")
    bmesh.ops.scale(bm, vec=(105, 105, 56), verts=bm.verts)
    o = mesh_obj("dome", bm, [mat("dome", (.86, .86, .84), .5)]); o.location = tuple(p)
    for pl in o.data.polygons:
        pl.use_smooth = True
    base = bmesh.new(); r_ = bmesh.ops.create_cone(base, cap_ends=True, segments=64, radius1=112, radius2=110, depth=14)
    bmesh.ops.translate(base, vec=(0, 0, 7), verts=r_["verts"]); b = mesh_obj("dome_base", base, [mat("dome_base", (.55, .55, .56), .6)]); b.location = tuple(p)
    return o


def crossing(p):
    """スクランブル交差点：広い交差点と白い横断歩道（斜めも）"""
    bm = bmesh.new(); white = []
    def stripe_row(a, b_, wdt=4.0, gap=1.0, length=6.0):
        a, b_ = Vector(a), Vector(b_); d = (b_ - a); n = int(d.length / (wdt * .5 + gap)); u = d.normalized(); v = Vector((-u.y, u.x, 0))
        for k in range(n):
            c = a + u * (k + .5) * (d.length / n)
            r_ = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=.5); vs = r_["verts"]
            bmesh.ops.scale(bm, vec=(wdt * .5, length, 1), verts=vs)
            ang = math.atan2(u.y, u.x); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(ang, 3, "Z"), verts=vs)
            bmesh.ops.translate(bm, vec=(c.x, c.y, .15), verts=vs)
    S = 26
    for a, b_ in (((-S, S), (S, S)), ((-S, -S), (S, -S)), ((-S, -S), (-S, S)), ((S, -S), (S, S)), ((-S, -S), (S, S)), ((-S, S), (S, -S))):
        stripe_row(a, b_)
    o = mesh_obj("zebra", bm, [mat("zebra", (.85, .85, .82), .6)]); o.location = tuple(p)
    pv = bmesh.new(); bmesh.ops.create_grid(pv, x_segments=1, y_segments=1, size=60); bmesh.ops.translate(pv, vec=(0, 0, .1), verts=pv.verts)
    a = mesh_obj("asphalt", pv, [mat("asphalt", (.1, .1, .11), .8)]); a.location = tuple(p)
    return o


def people(cx, cy, R, n, seed=5, run_dir=None):
    """顔のないピクトグラム（胴のカプセル＋頭）。1 つのメッシュ"""
    rnd = random.Random(seed); bm = bmesh.new(); cols = [mat(f"pp{i}", c, .7) for i, c in enumerate([(.1, .12, .2), (.5, .5, .52), (.7, .2, .15), (.85, .85, .8), (.2, .35, .5)])]
    for _ in range(n):
        x, y = cx + rnd.uniform(-R, R), cy + rnd.uniform(-R, R); h = rnd.uniform(1.5, 1.8)
        r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.22, radius2=.18, depth=h * .75); bmesh.ops.translate(bm, vec=(x, y, h * .375), verts=r_["verts"])
        mi = rnd.randrange(len(cols))
        for fc in {fc for v in r_["verts"] for fc in v.link_faces}:
            fc.material_index = mi
        s = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=.13); bmesh.ops.translate(bm, vec=(x, y, h * .87), verts=s["verts"])
    return mesh_obj("people", bm, cols)


def cars(cx, cy, R, n, seed=6):
    rnd = random.Random(seed); objs = []
    cols = [mat(f"car{i}", c, .3, .5) for i, c in enumerate([(.8, .8, .82), (.1, .1, .12), (.6, .05, .05), (.15, .2, .45), (.5, .5, .5)])]
    for i in range(n):
        bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(4.5, 1.8, 1.5), verts=r_["verts"])
        o = mesh_obj(f"car{i}", bm, [rnd.choice(cols)]); o.location = (cx + rnd.uniform(-R, R), cy + rnd.uniform(-R, R), .75); o.rotation_euler = (0, 0, rnd.choice((0, math.pi / 2)))
        objs.append(o)
    return objs


def volume_box(name, loc, size, dens, col=(.85, .85, .9), aniso=.3):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True; t = m.node_tree
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    pv = t.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Density"].default_value = dens; pv.inputs["Color"].default_value = (*col, 1); pv.inputs["Anisotropy"].default_value = aniso
    t.links.new(pv.outputs[0], t.nodes["Material Output"].inputs["Volume"])
    bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=r_["verts"])
    o = mesh_obj(name, bm, [m]); o.location = loc; return o, pv


def puff(name, loc, r, col=(.55, .5, .45), dens=.004):
    """土煙・湯気の球（体積）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    pv = t.nodes.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (*col, 1); pv.inputs["Density"].default_value = dens
    # 球の縁ほど薄く＋ノイズ
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.5; nz.inputs["Detail"].default_value = 6
    t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ln = t.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; t.links.new(tc.outputs["Object"], ln.inputs[0])
    edge = t.nodes.new("ShaderNodeMapRange"); edge.inputs[1].default_value = .5; edge.inputs[2].default_value = 1.0; edge.inputs[3].default_value = 1.0; edge.inputs[4].default_value = 0.0
    t.links.new(ln.outputs["Value"], edge.inputs[0])
    m1 = t.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; t.links.new(edge.outputs[0], m1.inputs[0]); t.links.new(nz.outputs["Fac"], m1.inputs[1])
    m2 = t.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.inputs[1].default_value = dens * 2.2; t.links.new(m1.outputs[0], m2.inputs[0])
    t.links.new(m2.outputs[0], pv.inputs["Density"])
    t.links.new(pv.outputs[0], t.nodes["Material Output"].inputs["Volume"])
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    o = mesh_obj(name, bm, [m]); o.location = loc; o.scale = (r, r, r); return o, m2.inputs[1]


# ---------------------------------------------------------------- ポメラニアン（本物の寸法、m。前が -Y、上が Z）
DOGC = bpy.data.collections.new("dog"); sc.collection.children.link(DOGC)


def dlink(o):
    DOGC.objects.link(o); return o


def hair_mat(name, mel, red):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    hb.parametrization = "MELANIN"
    hb.inputs["Melanin"].default_value = mel; hb.inputs["Melanin Redness"].default_value = red
    hb.inputs["Roughness"].default_value = .36; hb.inputs["Radial Roughness"].default_value = .55
    hb.inputs["Random Color"].default_value = .12; hb.inputs["Random Roughness"].default_value = .2
    nt.links.new(hb.outputs[0], out.inputs[0])
    return m


HAIR = hair_mat("hair", .32, .72)
HAIR_L = hair_mat("hair_light", .24, .66)     # えり・しっぽ・おなかは少し明るい
SKIN = K.mat("skin", (.36, .19, .1), .7)   # 毛の短い所から見える肌は毛に近い色


def part(name, elems, pivot, parent=None, fur=.05, count=3000, lenfn=None, hmat=None, child=60):
    """elems：[(位置, 半径, 種類, 大きさ)]（犬の座標）。pivot：回転の中心（犬の座標）。毛つきのメッシュを返す（原点＝pivot）"""
    # 寸法は本物の犬で書き、ここで KS 倍して実寸（500 m）で作る（毛の長さは物の拡大で伸びないため）
    mb = bpy.data.metaballs.new("mb_" + name); mb.resolution = .004 * KS; mb.render_resolution = .0028 * KS; mb.threshold = .05   # 部品ごとに作るので低く（.6 だと半径の 4 割に縮む）
    ob = bpy.data.objects.new("mb_" + name, mb); sc.collection.objects.link(ob)
    for p, r, kind, s in elems:
        e = mb.elements.new(); e.type = kind; e.co = Vector(p) * KS; e.radius = r * KS
        if kind == "ELLIPSOID":
            e.size_x, e.size_y, e.size_z = s
    for o in list(bpy.context.view_layer.objects):
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.convert(target="MESH")
    me_o = bpy.context.active_object; me_o.name = name
    sc.collection.objects.unlink(me_o); dlink(me_o)
    pv = Vector(pivot) * KS; fur *= KS
    for v in me_o.data.vertices:
        v.co -= pv
    me_o.location = pv if parent is None else pv - Vector(parent["pivot"])
    me_o["pivot"] = tuple(pv)
    if parent is not None:
        me_o.parent = parent
    for p_ in me_o.data.polygons:
        p_.use_smooth = True
    me_o.data.materials.append(SKIN)
    if fur > 0:
        md = me_o.modifiers.new("fur", "PARTICLE_SYSTEM"); ps = md.particle_system; st = ps.settings
        st.type = "HAIR"; st.count = count; st.hair_length = fur; st.use_advanced_hair = False
        st.emit_from = "FACE"; st.use_emit_random = True
        st.child_type = "INTERPOLATED"; st.child_percent = 4; st.rendered_child_count = child
        st.clump_factor = .35; st.clump_shape = -.2
        st.roughness_1 = fur * .24; st.roughness_1_size = 1.0; st.roughness_endpoint = fur * .16; st.roughness_2 = fur * .2
        st.kink = "CURL"; st.kink_amplitude = fur * .04; st.kink_frequency = 2.0
        st.radius_scale = .00009 * KS; st.tip_radius = 0.0; st.use_close_tip = True
        st.display_step = 3; st.render_step = 3
        me_o.data.materials.append(hmat or HAIR); st.material_slot = (hmat or HAIR).name
        if lenfn:
            vg = me_o.vertex_groups.new(name="len")
            for v in me_o.data.vertices:
                vg.add([v.index], max(.04, min(1., lenfn((v.co + pv) / KS))), "REPLACE")
            vd = me_o.vertex_groups.new(name="dens")   # 毛の密度は短い所でも半分以上（はげに見えないように）
            for v in me_o.data.vertices:
                vd.add([v.index], max(.55, min(1., lenfn((v.co + pv) / KS) + .3)), "REPLACE")
            ps.vertex_group_length = "len"; ps.vertex_group_density = "dens"
        # 毛を動かない曲線（Curves）に一度だけ変えて、部品に付ける。パーティクルのままだと毎コマ CPU で毛を作り直して遅い（1 コマ 60 秒）
        st.child_percent = child   # 曲線に変えるときは表示の本数が使われるので、描画と同じ本数に
        bpy.context.view_layer.update()
        for o in list(bpy.context.selected_objects):
            o.select_set(False)
        bpy.context.view_layer.objects.active = me_o; me_o.select_set(True)
        bpy.ops.curves.convert_from_particle_system()
        cv = next(o for o in bpy.context.selected_objects if o.type == "CURVES")
        for c_ in list(cv.users_collection):
            c_.objects.unlink(cv)
        dlink(cv); cv.name = name + "_fur"
        cd = cv.data; cd.materials.append(hmat or HAIR)
        n = len(cd.points); nc = len(cd.curves); ln = np.zeros(nc, np.int32); cd.curves.foreach_get("points_length", ln)
        k = np.concatenate([np.linspace(1, .08, m) for m in np.unique(ln)]) if len(np.unique(ln)) == 1 else None
        k = np.tile(k, nc) if k is not None else np.concatenate([np.linspace(1, .08, m) for m in ln])
        ra = cd.attributes.get("radius") or cd.attributes.new("radius", "FLOAT", "POINT")
        ra.data.foreach_set("value", (k[:n] * .00009 * KS * 1.2).astype(np.float32))
        cv.parent = me_o; cv.matrix_parent_inverse = me_o.matrix_world.inverted()
        me_o.modifiers.remove(md)
    return me_o


def solid(name, loc, r, m, s=(1, 1, 1), parent=None, seg=32):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r * KS); loc = Vector(loc) * KS
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); o = dlink(bpy.data.objects.new(name, me))
    o.data.materials.append(m); o.scale = s
    for p in o.data.polygons:
        p.use_smooth = True
    if parent is not None:
        o.parent = parent; o.location = Vector(loc) - Vector(parent["pivot"])
    else:
        o.location = loc
    return o


def wet_mat(name, col, rough, bump=.3, scale=900., coat=.6):
    m = K.mat(name, col, rough); t = m.node_tree; b = t.nodes["Principled BSDF"]
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump
    t.links.new(nz.outputs["Fac"], bp.inputs["Height"]); t.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = .12
    return m


def build_dog():
    root = dlink(bpy.data.objects.new("dog", None)); root["pivot"] = (0, 0, 0)
    E, B = "ELLIPSOID", "BALL"

    def body_len(p):   # 胴の毛：首のえりは長く、おなかの下と足の付け根は短め
        ruff = max(0., 1 - (Vector(p) - Vector((0, -.075, .17))).length / .09)
        under = max(0., 1 - (p.z - .07) / .05)
        return 1.0 + .45 * ruff - .5 * under
    torso = part("torso", [((0, .025, .145), .078, E, (.95, 1.25, .9)), ((0, -.055, .155), .072, E, (1, .9, 1)), ((0, .08, .15), .06, E, (1, 1, .95))],
                 (0, .01, .14), root, .052, 9000, body_len, child=45)

    def head_len(p):
        q = Vector(p)
        nose = clamp(1.6 * (1 - (q - Vector((0, -.15, .215))).length / .055))       # 鼻先は短い毛
        eye = clamp(1.6 * (1 - (Vector((abs(q.x), q.y, q.z)) - Vector((.027, -.14, .24))).length / .03))
        face = clamp((-.11 - q.y) / .03) * clamp((q.z - .19) / .02)                 # 顔の前は短く
        ear = clamp(1.5 * (1 - (Vector((abs(q.x), q.y, q.z)) - Vector((.034, -.08, .31))).length / .03))
        cheek = max(0., 1 - (Vector((abs(q.x), q.y, q.z)) - Vector((.05, -.08, .19))).length / .045)
        return (1 - .95 * max(nose, eye, .8 * face) - .9 * ear) * (1 + .35 * cheek)
    head = part("head", [((0, -.09, .225), .058, B, None), ((0, -.142, .213), .025, E, (.9, 1.2, .8)),
                         ((.034, -.08, .305), .022, E, (.7, .42, 1.7)), ((-.034, -.08, .305), .022, E, (.7, .42, 1.7))],
                (0, -.06, .19), torso, .04, 4500, head_len, child=45)
    eye_m = wet_mat("eye", (.03, .014, .007), .25, .0, 900., .35)   # 濃い茶色の目、つやは控えめ
    for sx in (-1, 1):
        solid(f"eye{sx}", (sx * .027, -.139, .241), .0078, eye_m, (1.1, .7, .85), head)
    solid("nose", (0, -.17, .219), .0068, wet_mat("nose", (.012, .01, .01), .45, .8, 2500., .25), (1.3, .9, .85), head)
    solid("mouth_in", (0, -.145, .2), .012, K.mat("mouth_in", (.12, .02, .03), .5), (1, 1.3, .6), head)
    jaw = part("jaw", [((0, -.148, .196), .016, E, (.9, 1.3, .5))], (0, -.125, .205), head, .012, 400, None, child=40)
    tongue = solid("tongue", (0, -.147, .199), .009, wet_mat("tongue", (.75, .26, .3), .3, .15, 600.), (1, 1.3, .35), jaw)
    tongue.rotation_mode = "XYZ"

    def leg_len(p):
        return .55 + .45 * clamp((p.z - .03) / .08)
    legs = []
    pad_m = wet_mat("pad", (.03, .022, .02), .55, .6, 1500.)
    for k, (sx, y) in enumerate(((-1, -.05), (1, -.05), (-1, .075), (1, .075))):
        fx = .03 if y < 0 else .033
        lg = part(f"leg{k}", [((sx * fx, y, .066), .02, E, (1, 1, 2.6)), ((sx * fx, y - .004, .016), .017, E, (1.1, 1.35, .8))],
                  (sx * fx, y, .11), torso, .026, 1000, leg_len, child=32)
        # 肉球：大きな肉球 1 つと指の肉球 4 つ（足の裏）
        solid(f"pad{k}", (sx * fx, y - .002, .0015), .006, pad_m, (1.1, .9, .35), lg)
        for i, (dx, dy) in enumerate(((-.008, -.009), (-.003, -.013), (.003, -.013), (.008, -.009))):
            solid(f"toe{k}{i}", (sx * fx + dx, y + dy, .002), .0032, pad_m, (1, 1, .4), lg)
        legs.append(lg)
    tail = part("tail", [((0, .1, .225), .028, E, (1, 1.7, .75)), ((0, .06, .25), .022, E, (1, 1.3, .7))], (0, .12, .2), torso, .07, 2600, None, HAIR_L, child=45)
    return dict(root=root, torso=torso, head=head, jaw=jaw, tongue=tongue, legs=legs, tail=tail)


log("build_dog start"); DOG = build_dog(); log("build_dog done")
if os.environ.get("DOGDUMP"):
    bpy.context.view_layer.update()
    for o in DOGC.objects:
        if o.type == "MESH":
            bb = [o.matrix_world @ Vector(c) for c in o.bound_box]; lo = [min(v[i] for v in bb) / KS for i in range(3)]; hi = [max(v[i] for v in bb) / KS for i in range(3)]
            print("DUMP", o.name, "parent", o.parent.name if o.parent else None, "loc", tuple(round(x, 3) for x in o.location), "bb", [round(x, 3) for x in lo], [round(x, 3) for x in hi], "nv", len(o.data.vertices), flush=True)
    sys.exit(0)
DOG_ANIM = [DOG["root"], DOG["torso"], DOG["head"], DOG["jaw"], DOG["tongue"], DOG["tail"]] + DOG["legs"]
for o in DOG_ANIM:
    o.rotation_mode = "XYZ"
REST = {o.name: tuple(o.location) for o in DOG_ANIM}


def dog_hide(h):
    for o in DOGC.objects:
        o.hide_render = h


def pose(pos, heading=0.0, up=0.0, torso=(0, 0, 0), head=(0, 0, 0), jaw=0.0, tongue=0.0, legs=None, tail=(0, 0, 0), root_rot=None, tz=0.0):
    """pos：足もとの位置（m）。heading：向き（ラジアン、0＝南〔-Y〕を向く）。角度はラジアン（x＝前後に振る、y＝横に倒す、z＝ひねる）。
    up：体の持ち上げ（犬の m）。tz：胴の上下（犬の m）"""
    R = DOG["root"]; R.location = (pos[0], pos[1], pos[2] if len(pos) > 2 else 0.0)
    R.rotation_euler = root_rot if root_rot is not None else (0, 0, heading)
    t = DOG["torso"]; t.location = Vector(REST[t.name]) + Vector((0, 0, (up + tz) * KS)); t.rotation_euler = torso
    DOG["head"].rotation_euler = head; DOG["jaw"].rotation_euler = (jaw, 0, 0)
    tg = DOG["tongue"]; tg.location = Vector(REST[tg.name]) + Vector((0, -.02 * tongue, -.006 * tongue)) * KS; tg.scale = (1, 1 + 1.6 * tongue, 1); tg.rotation_euler = (.5 * tongue, 0, 0)
    for lg, r in zip(DOG["legs"], legs or [(0, 0, 0)] * 4):
        lg.rotation_euler = r
    DOG["tail"].rotation_euler = tail


def walk_legs(ph, amp=.42):
    s = math.sin
    return [(amp * s(ph), 0, 0), (amp * s(ph + math.pi), 0, 0), (amp * s(ph + math.pi), 0, 0), (amp * s(ph), 0, 0)]


def gallop_legs(ph, amp=.95):
    s = math.sin
    return [(amp * s(ph), 0, 0), (amp * s(ph + .5), 0, 0), (-amp * s(ph + 2.4), 0, 0), (-amp * s(ph + 2.9), 0, 0)]


def dogpt(local):
    """犬の座標の点（m）を世界の座標に（いまのポーズ、胴の回転は無視）"""
    R = DOG["root"]; return R.matrix_world @ Vector(local)


# ---------------------------------------------------------------- 場面の土台
def base(sun_el, sun_rot, haze_col, haze_k=1.0, d0=900., d1=18000., energy=9.0, alt=0, blur=False):
    sky.set(alt, sun_el, sun_rot, energy); set_haze(haze_col, haze_k, d0, d1)
    sc.render.use_motion_blur = blur   # 動きのぶれは速く走るショットだけ（毛のぶれは重い）


def face(a, b):
    """a から b を向く heading（犬の前は -Y）"""
    d = Vector(b) - Vector(a); return math.atan2(d.x, -d.y)


def keyhide(o, h, f):
    o.hide_render = h; o.keyframe_insert("hide_render", frame=f + 1)


def cut(u0, u1, u):
    return clamp((u - u0) / max(1e-6, u1 - u0))


# 時刻の色（夜明け → 朝）
DAWN = (.95, .72, .55); MORN = (.78, .82, .9)

# ---------------------------------------------------------------- l00 / l16：新宿の高層ビルの向こうに座る（冒頭と最後が同じ構図）
SIT_POS = YOYOGI + Vector((0, 600, 0))
SIT_CAM = SIT_POS + Vector((-900, 2900, 230)); SIT_AT = SIT_POS + Vector((0, 0, 330))


def sit_pose(tilt=0.0, ear=0.0):
    return dict(torso=(-.62, 0, 0), up=-.035, head=(.55, 0, tilt), legs=[(.62, 0, 0), (.62, 0, 0), (-1.0, 0, 0), (-1.0, 0, 0)], tail=(-.2, 0, 0))


def s_l00():
    env_clear(); dog_hide(False); base(6, 105, DAWN, 1.0, 1500, 22000)
    ground(); city(SHINJUKU.x, SHINJUKU.y, 6500, 3, downtown([(SHINJUKU.x - 600, SHINJUKU.y, 900, 240), (SHIBUYA.x, SHIBUYA.y, 600, 180)]), hole=[(SIT_POS.x, SIT_POS.y, 700)])
    trees(YOYOGI.x, YOYOGI.y, 900, 1100, 2500)
def a_l00(u, t, f):
    p = sit_pose(.08 * math.sin(t * .8)); pose(SIT_POS, face(SIT_POS, SIT_CAM), **p)
    cam.look(tuple(SIT_CAM + Vector((40 * u, -150 * u, 0))), tuple(SIT_AT), 32)


def s_l16():
    env_clear(); dog_hide(False); base(28, 140, MORN, .9, 1500, 22000)
    ground(ruin=True); city(SHINJUKU.x, SHINJUKU.y, 6500, 3, ruin=True, dens=.7)
    puff("dust16", tuple(SIT_POS + Vector((0, 0, -300))), 1400, (.6, .55, .5), .00012)
def a_l16(u, t, f):
    tilt = .35 * ease(cut(.15, .55, u)); p = sit_pose(tilt); pose(SIT_POS, face(SIT_POS, SIT_CAM), **p)
    cam.look(tuple(SIT_CAM + Vector((40, -150, 0)) * (1 - u)), tuple(SIT_AT), 32)


# ---------------------------------------------------------------- l01：夜明けの代々木公園、霧の中の影
def s_l01():
    env_clear(); dog_hide(False); base(3, 105, (.9, .62, .5), 1.0, 600, 9000)
    ground(); trees(YOYOGI.x, YOYOGI.y, 1100, 1300, 4000, 7); city(YOYOGI.x, YOYOGI.y, 4000, 4, hole=[(YOYOGI.x, YOYOGI.y, 750)])
    volume_box("fog01", (YOYOGI.x, YOYOGI.y, 120), (5000, 5000, 240), .0012, (.95, .85, .8))
def a_l01(u, t, f):
    pose(YOYOGI, face(YOYOGI, YOYOGI + Vector((150, -640, 0))) + .3, torso=(.03 * math.sin(t), 0, 0), head=(-.1 + .15 * ease(u), 0, .1 * math.sin(t * .7)), tail=(0, 0, .15 * math.sin(t * 2)))
    c = YOYOGI + Vector((150, -640, 26)); cam.look(tuple(c + Vector((0, 40 * u, 2 * u))), tuple(YOYOGI + Vector((0, 0, 330 + 40 * u))), 18)


# ---------------------------------------------------------------- l02：スクランブル交差点に前足が下りる（下から見上げる）
def s_l02():
    env_clear(); dog_hide(False); base(10, 110, DAWN, 1.0, 800, 12000)
    ground(); crossing(SHIBUYA); city(SHIBUYA.x, SHIBUYA.y, 3000, 5, downtown([(SHIBUYA.x, SHIBUYA.y, 500, 150)]), hole=[(SHIBUYA.x, SHIBUYA.y, 230), (SHIBUYA.x - 90, SHIBUYA.y - 500, 320), (SHIBUYA.x + 70, SHIBUYA.y + 130, 330)])
    global CARS2; CARS2 = cars(SHIBUYA.x, SHIBUYA.y, 40, 14)
    global DUST2, DUST2K; DUST2, DUST2K = puff("dust02", tuple(SHIBUYA), 60, (.6, .55, .48), .02)
def a_l02(u, t, f):
    # カメラのほう（南）へ歩いてくる犬の左前足（leg0）。前に振り上げた足の裏（肉球）が下からよく見え → 交差点に下りる
    land = .58; up_ = ease(cut(0, .3, u)) * (1 - ease(cut(.38, land, u)))
    rot0 = -1.15 * up_
    root = SHIBUYA + Vector((.03 * KS, .054 * KS, 0))
    pose(root, 0.0, legs=[(rot0, 0, 0), (.1, 0, 0), (-.1, 0, 0), (.1, 0, 0)], torso=(-.08 * up_, 0, 0), head=(.15, 0, 0))
    e = u - land
    sink = 6 * ease(clamp(e / .15)) if e > 0 else 0
    DOG["root"].location.z -= sink
    if e > 0:
        keyp(DUST2, f, scale=60 + 260 * ease(clamp(e / .4)), loc=tuple(SHIBUYA + Vector((0, 0, 10))))
        key_v(DUST2K, .03 * (1 - .6 * clamp(e / .45)), f)
        for i, c in enumerate(CARS2):
            r = random.Random(i); d = Vector((r.uniform(-1, 1), r.uniform(-1, 1), 0)).normalized(); s_ = clamp(e / .3)
            keyp(c, f, loc=tuple(SHIBUYA + d * (40 + 140 * s_) + Vector((0, 0, .75 + 60 * s_ * (1 - s_)))), rot=(s_ * r.uniform(2, 6), s_ * 3, i))
    else:
        keyp(DUST2, f, scale=1.0, loc=(0, 0, -1e5))
    sh = shake(f, 3.0 * clamp(1 - abs(e) / .12), 2) if e > -0.02 else Vector()
    bpy.context.view_layer.update(); pw = DOGC.objects["pad0"].matrix_world.translation
    tgt = pw.lerp(SHIBUYA + Vector((0, 0, 40)), ease(cut(.3, .6, u)))
    cam.look(tuple(SHIBUYA + Vector((-90, -560, 8)) + sh), tuple(tgt + Vector((0, 0, 20))), 20)


# ---------------------------------------------------------------- l03：くんくん（ビルの屋上の高さの鼻）、鼻息で車と街路樹が飛ぶ
def s_l03():
    env_clear(); dog_hide(False); base(12, 112, DAWN, 1.0, 800, 12000)
    ground(); city(SHIBUYA.x, SHIBUYA.y + 800, 3500, 6, downtown([(SHIBUYA.x, SHIBUYA.y, 600, 150)]), hole=[(SHIBUYA.x + 300, SHIBUYA.y + 700, 420)])
    global CARS3; CARS3 = cars(SHIBUYA.x + 300, SHIBUYA.y + 150, 120, 30, 9)
    global GUST3, GUST3K; GUST3, GUST3K = puff("gust03", tuple(SHIBUYA), 80, (.75, .72, .7), .01)
def a_l03(u, t, f):
    P = SHIBUYA + Vector((300, 700, 0))
    sn = math.sin(t * 9) * .02 * (u < .55)
    pose(P, face(P, SHIBUYA + Vector((520, 80, 0))) - .5, torso=(.5, 0, 0), up=-.02, head=(.55 + sn, 0, .05), legs=[(-.4, 0, 0), (-.4, 0, 0), (.1, 0, 0), (.1, 0, 0)])
    nose = dogpt((0, -.17, .22)) if False else None
    bpy.context.view_layer.update(); nz = DOG["head"].matrix_world @ (Vector((0, -.172, .219)) * KS - Vector(DOG["head"]["pivot"]))
    ex = cut(.55, 1, u)     # 吐く（ふんっ）
    for i, c in enumerate(CARS3):
        r = random.Random(i + 30); base_ = Vector((SHIBUYA.x + 300 + r.uniform(-120, 120), SHIBUYA.y + 150 + r.uniform(-120, 120), .75))
        d = (base_ - Vector((nz.x, nz.y, 0))).normalized(); s_ = ease(ex) * r.uniform(.6, 1.0)
        keyp(c, f, loc=tuple(base_ + d * 260 * s_ + Vector((0, 0, 80 * s_ * (1.2 - s_)))), rot=(s_ * r.uniform(3, 8), s_ * r.uniform(2, 5), s_ * 3))
    keyp(GUST3, f, loc=tuple(nz + (Vector((0, -1, -.6)).normalized()) * (40 + 280 * ex)), scale=20 + 160 * ex)
    key_v(GUST3K, .02 * (1 - ex) * (ex > 0), f)
    cam.look(tuple(SHIBUYA + Vector((520, 80, 95)) + shake(f, 1.2 * ex * (1 - ex) * 4, 3)), tuple(nz + Vector((0, 0, -30))), 26)


# ---------------------------------------------------------------- l04：「ワン」（正面から）、人々が走り出す
def s_l04():
    env_clear(); dog_hide(False); base(14, 115, DAWN, 1.0, 1000, 16000)
    ground(); city(SHIBUYA.x, SHIBUYA.y, 4000, 8, downtown([(SHIBUYA.x, SHIBUYA.y - 900, 500, 160)]), hole=[(SHIBUYA.x, SHIBUYA.y + 400, 420), (SHIBUYA.x + 80, SHIBUYA.y - 700, 260)])
    global PPL4; PPL4 = people(SHIBUYA.x + 80, SHIBUYA.y - 640, 30, 90)
def a_l04(u, t, f):
    P = SHIBUYA + Vector((0, 400, 0)); b = cut(.2, .32, u); bk = math.sin(math.pi * b)
    pose(P, face(P, SHIBUYA + Vector((80, -700, 0))), head=(-.15 * bk + .05, 0, 0), jaw=.6 * bk, torso=(-.05 * bk, 0, 0), legs=[(-.1 * bk, 0, 0), (-.1 * bk, 0, 0), (0, 0, 0), (0, 0, 0)])
    keyp(PPL4, f, loc=(0, -25 * cut(.35, 1, u) ** 1.2, 0))
    c = SHIBUYA + Vector((80, -700, 6)); cam.look(tuple(c + shake(f, .4 * bk, 4)), tuple(P + Vector((0, 0, 400))), 20)


# ---------------------------------------------------------------- l05：散歩（明治通り。空から横に並んで追う）
def s_l05():
    env_clear(); dog_hide(False); base(18, 118, MORN, .9, 1500, 20000)
    ground(); city(2500, -1500, 6000, 10, downtown([(SHIBUYA.x, SHIBUYA.y, 500, 150), (SHINJUKU.x, SHINJUKU.y, 700, 200)]), hole=[(x, y, 260) for x, y in [(1500 + 200 * i, -2600 + 330 * i) for i in range(12)]])
def a_l05(u, t, f):
    a = Vector((1500, -2600, 0)); b = Vector((1500 + 200 * 11, -2600 + 330 * 11, 0)); d = (b - a).normalized(); P = a + (b - a) * (.15 + .5 * u)
    hd = math.atan2(d.x, -d.y) + math.pi   # 南が 0：北東へ向く
    ph = t * 2 * math.pi * .9
    pose(P, face(a, b), legs=walk_legs(ph), tz=.004 * math.cos(2 * ph), head=(.05 * math.sin(2 * ph), 0, 0), tail=(0, 0, .2 * math.sin(ph)))
    side = Vector((d.y, -d.x, 0))
    cam.look(tuple(P + side * 2600 + Vector((0, 0, 700)) - d * 300), tuple(P + Vector((0, 0, 260))), 35)


# ---------------------------------------------------------------- l06：うんち（東京ドームのとなり）
def s_l06():
    env_clear(); dog_hide(False); base(20, 122, MORN, .9, 1500, 20000)
    ground(); dome(DOME); city(DOME.x, DOME.y, 4500, 11, downtown([(DOME.x, DOME.y - 500, 500, 120)]), hole=[(DOME.x, DOME.y, 260), (DOME.x - 700, DOME.y + 150, 480)])
    global POOP, STEAM, STEAMK
    P = DOME + Vector((-700, 150, 0)); h = face(P, P + Vector((1, -.3, 0))); fw = Vector((math.sin(h), -math.cos(h), 0))
    POOP = poop_pile(P - fw * (.22 * KS))   # お尻の毛の外に出る位置
    STEAM, STEAMK = puff("steam06", (0, 0, -1e5), 60, (.9, .9, .9), .004)


def poop_pile(p):
    """とぐろの山（つぶした球を少しずつずらして重ねる。本物の 1 回分の形を k 倍：高さ 71 m）"""
    tv, tf = _template("ico"); xf = []
    for i in range(14):
        a = i * 1.1; r = 44 - i * 2.6; z = 6 + i * 4.6
        xf.append((math.cos(a) * 12, math.sin(a) * 12, z, r, r * .9, r * .42, a, 0, 0))
    o = instances("poop", tv, tf, xf, [wet_mat("poop", (.16, .08, .035), .45, .5, .05)])
    for pl in o.data.polygons:
        pl.use_smooth = True
    sub = o.modifiers.new("smooth", "SUBSURF"); sub.levels = sub.render_levels = 2
    o.location = p; return o


def a_l06(u, t, f):
    P = DOME + Vector((-700, 150, 0)); sq = ease(cut(.05, .3, u)); out = cut(.38, .78, u)
    pose(P, face(P, P + Vector((1, -.3, 0))), up=-.055 * sq, torso=(-.5 * sq, 0, 0), head=(.4 * sq, 0, 0),
         legs=[(.45 * sq, 0, 0), (.45 * sq, 0, 0), (-1.25 * sq, 0, 0), (-1.25 * sq, 0, 0)], tail=(-.5 * sq, 0, 0))
    keyp(POOP, f, scale=(1, 1, max(.02, ease(out))))
    if out > .6:
        keyp(STEAM, f, loc=tuple(POOP.location + Vector((0, 0, 70 + 40 * u))), scale=40 + 30 * u); key_v(STEAMK, .004, f)
    else:
        keyp(STEAM, f, loc=(0, 0, -1e5)); key_v(STEAMK, 0., f)
    fw = Vector((math.sin(DOG["root"].rotation_euler.z), -math.cos(DOG["root"].rotation_euler.z), 0))
    pp = P - fw * (.22 * KS)   # 山の位置（お尻のうしろ）。カメラは山の側（南西）から、手前に山・奥に犬とドーム
    zi = ease(cut(.5, .95, u))   # 後半は山に寄る（まわりの 20 階建てのビルと比べる）
    c0 = pp + Vector((-1100, -1500, 260)); c1 = pp + Vector((-260, -330, 70))
    a0 = pp.lerp(P, .45) + Vector((0, 0, 120)); a1 = pp + Vector((0, 0, 35))
    cam.look(tuple(c0.lerp(c1, zi)), tuple(a0.lerp(a1, zi)), 26 + 6 * zi)


# ---------------------------------------------------------------- l07：スカイツリーにマーキング → 川があふれる
def s_l07():
    env_clear(); dog_hide(False); base(22, 125, MORN, .9, 1500, 20000)
    ground(); skytree(SKYTREE); city(SKYTREE.x, SKYTREE.y, 4500, 12, hole=[(SKYTREE.x, SKYTREE.y, 120), (SKYTREE.x + 380, SKYTREE.y + 60, 380), (SKYTREE.x - 900, SKYTREE.y, 140)])
    global RIVER; bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=.5); bmesh.ops.scale(bm, vec=(260, 9000, 1), verts=bm.verts)
    RIVER = mesh_obj("river", bm, [river_mat()]); RIVER.location = (SKYTREE.x - 900, SKYTREE.y, .5)


def river_mat():
    m = K.mat("river", (.18, .22, .2), .05); b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = 0; add_haze(m); return m
def a_l07(u, t, f):
    P = SKYTREE + Vector((380, 60, 0)); lift = ease(cut(.1, .35, u)); fl = ease(cut(.45, 1, u))
    pose(P, math.pi, torso=(0, .12 * lift, 0), legs=[(0, 0, 0), (0, 0, 0), (0, 0, 0), (-.3 * lift, -1.25 * lift, 0)], head=(.1, 0, -.2), tail=(-.2, 0, 0))
    keyp(RIVER, f, scale=(1 + 9 * fl, 1, 1), loc=(SKYTREE.x - 900 + 600 * fl, SKYTREE.y, .5 + 4 * fl))
    cam.look(tuple(SKYTREE + Vector((-1400, -2300, 160))), tuple(SKYTREE + Vector((200, 0, 250))), 30)


# ---------------------------------------------------------------- l08：ブルブル → 毛が雪のように降る
def s_l08():
    env_clear(); dog_hide(False); base(24, 128, MORN, .9, 1500, 20000)
    ground(); city(4000, 0, 5000, 13, downtown([(4000, 300, 600, 140)]), hole=[(4000, 0, 450)])
    global FLY; FLY = []
    rnd = random.Random(8); m = mat("fly_hair", (.75, .42, .2), .6)
    for i in range(160):   # 抜け毛（1 本 119 m。細い曲線）
        cu = bpy.data.curves.new(f"fh{i}", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = .35; sp = cu.splines.new("NURBS"); sp.points.add(5)
        for j, pt in enumerate(sp.points):
            pt.co = (j * 24 * math.cos(j * .5), j * 8 * math.sin(j * .9), 6 * math.sin(j), 1)
        sp.use_endpoint_u = True; cu.materials.append(m)
        o = link(bpy.data.objects.new(f"fh{i}", cu)); o["v"] = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(.2, 1.0), rnd.uniform(0, 6.3)); FLY.append(o)
def a_l08(u, t, f):
    P = Vector((4000, 0, 0)); sh = cut(.05, .55, u); a = .45 * math.sin(t * 2 * math.pi * 3.2) * math.sin(math.pi * sh)
    pose(P, face(P, P + Vector((-2300, -2600, 0))) + .4, torso=(0, a, 0), head=(0, a * 1.4, .1 * a), tail=(0, a * 1.2, 0))
    for o in FLY:
        vx, vy, vz, ph = o["v"]; e = max(0., u - .1)
        p = P + Vector((vx * 2600 * e, vy * 2600 * e, 380 + 900 * vz * e - 500 * e * e * 2))
        keyp(o, f, loc=tuple(p), rot=(ph + t * .7, t * .3, ph))
        keyhide(o, u < .1, f)
    cam.look(tuple(P + Vector((-2300, -2600, 520))), tuple(P + Vector((0, 0, 330))), 30)


# ---------------------------------------------------------------- l09：ハァハァ（口のアップ）
def s_l09():
    env_clear(); dog_hide(False); base(26, 130, MORN, .9, 1500, 20000)
    ground(); city(4000, 0, 4000, 14, downtown([(4000, -300, 500, 130)]), hole=[(4000, 0, 450)])
    global BR9, BR9K; BR9, BR9K = puff("breath09", (0, 0, -1e5), 40, (.95, .95, .95), .01)
def a_l09(u, t, f):
    P = Vector((4000, 0, 0)); pn = math.sin(t * 2 * math.pi * 1.6)
    pose(P, face(P, P + Vector((-220, -420, 0))), jaw=.45 + .08 * pn, tongue=.9 + .1 * pn, torso=(.02 * pn, 0, 0), up=.003 * pn, head=(-.08, 0, .05))
    bpy.context.view_layer.update(); mo = DOG["head"].matrix_world @ (Vector((0, -.16, .2)) * KS - Vector(DOG["head"]["pivot"]))
    keyp(BR9, f, loc=(0, 0, -1e5))   # 息のもやは顔を隠すので出さない（湯気の音だけ）
    cam.look(tuple(mo + Vector((-220, -420, -40))), tuple(mo + Vector((0, 0, 10))), 32)


# ---------------------------------------------------------------- l10：遊びのおじぎ
def s_l10():
    env_clear(); dog_hide(False); base(27, 132, MORN, .9, 1500, 20000)
    ground(); city(4000, -800, 5000, 15, downtown([(4000, -2500, 600, 150)]), hole=[(4000, 0, 450), (4380, -1900, 380)])
def a_l10(u, t, f):
    P = Vector((4000, 0, 0)); b = ease(cut(.05, .35, u)); wag = math.sin(t * 2 * math.pi * 2.2)
    pose(P, face(P, P + Vector((380, -1900, 0))) - .9, torso=(.55 * b, 0, 0), up=-.03 * b, head=(-.45 * b, 0, .15 * math.sin(t * 3) * b),
         legs=[(-1.35 * b, 0, 0), (-1.35 * b, 0, 0), (-.15 * b, 0, 0), (-.15 * b, 0, 0)], tail=(.3 * b, 0, .5 * wag * b))
    cam.look(tuple(P + Vector((380, -1900, 60))), tuple(P + Vector((0, 0, 200))), 26)


# ---------------------------------------------------------------- l11：走り出す。衝撃波で窓が一斉に割れる
def s_l11():
    env_clear(); dog_hide(False); base(28, 135, MORN, .9, 1500, 20000, blur=True)
    ground(); city(4000, 0, 6000, 16, downtown([(4000, 600, 700, 140)]), hole=[(4000 + x, 0, 280) for x in range(-3000, 3001, 250)] + [(4000, -900, 260)])
    global GLASS, CONE, CONEK
    rnd = random.Random(11); GLASS = []
    gm = K.mat("glass_sh", (.6, .7, .75), .05, .0); gm.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = .7
    xf = []
    for i in range(1800):   # ガラスの破片（1 つのメッシュの粒を、通り沿いのビルの高さに）
        q = rnd.uniform(.8, 2.4); xf.append((4000 + rnd.uniform(-2200, 2200), rnd.choice((-1, 1)) * rnd.uniform(300, 700), rnd.uniform(5, 60), q, q * .6, q * .1, rnd.uniform(0, 6), rnd.uniform(0, 3), rnd.uniform(0, 3)))
    GLASS = instances("glass", CUBE_V, CUBE_F, xf, [gm])
    CONE, CONEK = puff("cone", (0, 0, -1e5), 300, (.92, .92, .95), .003)
def a_l11(u, t, f):
    x = 4000 - 2600 + 5200 * ease(cut(.1, .75, u)) ** 1.0; P = Vector((x, 0, 0)); ph = t * 2 * math.pi * 2.6
    run = cut(.05, .2, u)
    pose(P, math.pi / 2, legs=gallop_legs(ph, .95 * run), torso=(.12 * math.sin(ph) * run, 0, 0), tz=.01 * abs(math.sin(ph)) * run, head=(-.1 * run, 0, 0), tail=(.5 * run, 0, 0), jaw=.25 * run, tongue=.6 * run)
    gl = cut(.35, 1, u); keyp(GLASS, f, loc=(0, 0, -22 * gl * gl), scale=(1, 1 + .6 * gl, 1))
    keyhide(GLASS, u < .33, f)
    keyp(CONE, f, loc=tuple(P + Vector((-300, 0, 250))), scale=(500, 260, 260)); key_v(CONEK, .002 * run, f)
    cam.look(tuple(Vector((4000, -900, 25)) + shake(f, 2.5 * cut(.3, .5, u) * (1 - cut(.6, 1, u)), 6)), tuple(Vector((P.x * .6 + 4000 * .4, 0, 220))), 18)


# ---------------------------------------------------------------- l12：空から：23 区に走った跡が増えていく
def zoomie_path(n=900, seed=12):
    """23 区（中心は皇居の少し西、半径 12 km の目安）の中をぐるぐる走る道すじ（m）"""
    rnd = random.Random(seed); pts = []; c = Vector((5000, -1500, 0)); a = 0.0; r = 2000.0
    for i in range(n):
        a += rnd.uniform(.12, .32); r = clamp(r + rnd.uniform(-500, 650), 600, 12000)
        pts.append(c + Vector((math.cos(a) * r, math.sin(a) * r * .8, 0)))
    return pts


def s_l12():
    env_clear(); dog_hide(True); base(30, 140, MORN, .7, 20000, 140000)
    # 地面：関東の街の濃さ（pilot_047 の地図、±200 km）と海
    bm = bmesh.new(); bm.loops.layers.uv.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200000, calc_uvs=True); g = mesh_obj("kanto", bm, [kanto_mat()])
    pts = zoomie_path(); cu = bpy.data.curves.new("track", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 200; cu.bevel_resolution = 0
    sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts):
        sp.points[i].co = (p.x, p.y, 30, 1)
    cu.materials.append(mat("track", (.25, .2, .16), .95, haze=False))
    global TRACK; TRACK = link(bpy.data.objects.new("track", cu)); TRACK.scale = (1, 1, .02)
    global HEADP, HEADK; HEADP, HEADK = puff("head12", (0, 0, -1e5), 900, (.6, .55, .5), .0008)


def kanto_mat():
    m = bpy.data.materials.new("kanto"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    tc = t.nodes.new("ShaderNodeTexCoord")
    pop = t.nodes.new("ShaderNodeTexImage"); pop.image = bpy.data.images.load(os.path.abspath(os.path.join(MAPS, "kanto_pop.png"))); pop.image.colorspace_settings.name = "Non-Color"
    land = t.nodes.new("ShaderNodeTexImage"); land.image = bpy.data.images.load(os.path.abspath(os.path.join(MAPS, "kanto_land.png"))); land.image.colorspace_settings.name = "Non-Color"
    L.new(tc.outputs["UV"], pop.inputs[0]); L.new(tc.outputs["UV"], land.inputs[0])
    city_c = t.nodes.new("ShaderNodeMix"); city_c.data_type = "RGBA"; city_c.inputs[6].default_value = (.17, .2, .12, 1); city_c.inputs[7].default_value = (.42, .41, .39, 1)
    L.new(pop.outputs["Color"], city_c.inputs[0])
    sea = t.nodes.new("ShaderNodeMix"); sea.data_type = "RGBA"; sea.inputs[6].default_value = (.03, .07, .1, 1); L.new(city_c.outputs[2], sea.inputs[7]); L.new(land.outputs["Color"], sea.inputs[0])
    L.new(sea.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8
    return m
def a_l12(u, t, f):
    e = ease(u) * .62 + .08     # 走った跡の割合（7:26〜7:58、23 区の半分ほどまで）
    TRACK.data.bevel_factor_end = e; TRACK.data.keyframe_insert("bevel_factor_end", frame=f + 1)
    pts = zoomie_path(); hp = pts[min(len(pts) - 1, int(e * (len(pts) - 1)))]
    keyp(HEADP, f, loc=tuple(hp + Vector((0, 0, 300))), scale=900); key_v(HEADK, .002, f)
    c = Vector((5000, -1500, 0)); cam.look(tuple(c + Vector((0, -24000 + 4000 * u, 42000))), tuple(c + Vector((0, 1500, 0))), 32)


# ---------------------------------------------------------------- l13：東京タワーがなぎ倒される
def s_l13():
    env_clear(); dog_hide(False); base(31, 142, MORN, .9, 1500, 20000, blur=True)
    ground(); global TT; TT = tokyo_tower(TOWER); city(TOWER.x, TOWER.y, 4500, 17, hole=[(TOWER.x, TOWER.y, 90), (TOWER.x - 300, TOWER.y - 1700, 320)] + [(TOWER.x - 2500 + 250 * i, TOWER.y + 260, 260) for i in range(21)])
    global DUST13, DUST13K; DUST13, DUST13K = puff("dust13", (0, 0, -1e5), 400, (.6, .55, .5), .002)
def a_l13(u, t, f):
    x = TOWER.x - 2000 + 4000 * u; P = Vector((x, TOWER.y + 260, 0)); ph = t * 2 * math.pi * 2.6
    pose(P, math.pi / 2, legs=gallop_legs(ph), torso=(.12 * math.sin(ph), 0, 0), tz=.01 * abs(math.sin(ph)), head=(-.1, 0, 0), tail=(.5, 0, 0), jaw=.25, tongue=.6)
    hit = cut(.44, .8, u); TT.rotation_euler = (0, 0, 0); keyp(TT, f, rot=(-1.5 * ease(hit) ** 1.4, 0, .25 * hit))
    keyp(DUST13, f, loc=tuple(TOWER + Vector((0, -150 * hit, 60))), scale=100 + 500 * hit); key_v(DUST13K, .003 * (hit > 0), f)
    cam.look(tuple(TOWER + Vector((-300, -1700, 90))), tuple(TOWER + Vector((0, 250, 230))), 22)


# ---------------------------------------------------------------- l14：へそ天（平らになった新宿の上で）
def s_l14():
    env_clear(); dog_hide(False); base(34, 145, MORN, .9, 1500, 22000)
    ground(ruin=True); city(SHINJUKU.x, SHINJUKU.y, 5000, 18, ruin=True, dens=.8)
    puff("dust14", tuple(SHINJUKU + Vector((0, 0, -400))), 1500, (.62, .57, .52), .00012)
def a_l14(u, t, f):
    P = SHINJUKU + Vector((0, 0, 0)); wig = math.sin(t * 2 * math.pi * 1.3)
    pose(P + Vector((0, 0, .19 * KS)), root_rot=(0, math.pi * .97, math.radians(20)), torso=(0, .1 * wig, 0), head=(.3, 0, .25 + .1 * wig),
         legs=[(-.9 + .3 * wig, 0, 0), (-.9 - .3 * wig, 0, 0), (.8 + .2 * wig, 0, 0), (.8 - .2 * wig, 0, 0)], tail=(0, .3 * wig, 0), jaw=.25, tongue=.7)
    cam.look(tuple(P + Vector((1000, -1300, 900))), tuple(P + Vector((0, 0, 150))), 30)


# ---------------------------------------------------------------- l15：真上から、平らになった東京
def s_l15():
    env_clear(); dog_hide(False); base(36, 150, MORN, .8, 4000, 60000)
    ground(size=200000, ruin=True); city(4000, -1000, 7000, 19, ruin=True, dens=.55)

def a_l15(u, t, f):
    P = SHINJUKU + Vector((0, 0, 0))
    pose(P + Vector((0, 0, .19 * KS)), root_rot=(0, math.pi * .97, math.radians(20)), torso=(0, 0, 0), head=(.3, 0, .25), legs=[(-.9, 0, 0), (-.9, 0, 0), (.8, 0, 0), (.8, 0, 0)], jaw=.25, tongue=.7)
    c = SHINJUKU + Vector((0, 0, 0)); cam.look(tuple(c + Vector((0, -10, 7000 + 5000 * u))), tuple(c), 30, roll=.15 * u)


NAMES = [s["id"] for s in PLAN["shots"]]
def _wrap(a):
    def w(u, t, f):
        if f % 20 == 0:
            log("anim frame", f)
        a(u, t, f); DOG["tongue"].keyframe_insert("scale", frame=f + 1)
        if os.environ.get("DOGPROBE") and f in (0, 30, 60):
            bpy.context.view_layer.update(); lg = DOG["legs"][0]
            print("PROBE", f, "leg0 rot", tuple(round(x, 2) for x in lg.rotation_euler), "pad0", tuple(round(x) for x in DOGC.objects["pad0"].matrix_world.translation),
                  "leg1pad", tuple(round(x) for x in DOGC.objects["pad1"].matrix_world.translation), "cam", tuple(round(x) for x in cam.o.location), flush=True)
            sys.exit(0) if f == 60 else None
        if os.environ.get("DOGPOSE") == "stand":
            pose(tuple(DOG["root"].location), DOG["root"].rotation_euler.z)
        dc = os.environ.get("DOGCAM")   # 確認用：犬を横（side）・正面（front）から近くで見る
        if dc:
            R = DOG["root"]; c = R.location.copy(); hd = R.rotation_euler.z
            fw = Vector((math.sin(hd), -math.cos(hd), 0)); sd = Vector((math.cos(hd), math.sin(hd), 0))
            if dc == "face":
                cam.look(tuple(c + (fw * 1.0 + sd * .35).normalized() * 1100 + Vector((0, 0, 560))), tuple(c + fw * 300 + Vector((0, 0, 540))), 50)
            else:
                off = {"side": sd * 1700, "front": fw * 1700, "q": (fw + sd).normalized() * 1700}[dc]
                cam.look(tuple(c + off + Vector((0, 0, 260))), tuple(c + Vector((0, 0, 280))), 45)
            if os.environ.get("DOGSUN"):
                sky.set(0, 25, math.degrees(math.atan2(off_dir.x, off_dir.y)) if False else 30, 9.0)
    return w


SHOTS = {k: (globals()["s_" + k], _wrap(globals()["a_" + k])) for k in NAMES}
anim = [cam.o] + DOG_ANIM
K.render_shots(HERE, SHOTS, NAMES, O, anim)
