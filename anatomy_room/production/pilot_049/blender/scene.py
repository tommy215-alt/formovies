r"""pilot_049（身長50mの怪獣 vs 世界最強のハンマー投げ選手5万人）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計の既定。
使い方："C:\Program Files\Blender Foundation\Blender 5.2lender.exe" -b -P anatomy_room/production/pilot_049/blender/scene.py -- [ショット名 ...] [--still] [--samples N] [--resume]
前もって python plan.py（blender/plan.json）、python production_script.py voice（work/timeline.json）。

怪獣：オリジナルの恐竜型（特定の作品の見た目は借りない。背中は角のようなとげ）。体はメタボールのつながった面、頭・あご・腕は動かすので別。うろこの質感（ボロノイの凹凸）。
人：顔のないピクトグラム（5 万人はインスタンスでまとめて）。ハンマーは代表の数百本を放物線で飛ばす（数は札で出す）。
地形：草原と、怪獣の頭と同じ高さ（43 m）の丘。炎は光る円すい（閃光にしない）。血は出さない。
座標：怪獣が原点、南が -Y（怪獣の前）、m。注意：一部だけ書き換える patch は、失敗するとファイルを空にすることがある（2026-11-10）。直すときは Edit で。
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

O = K.args()
sc = K.setup(O["samples"])
sc.cycles.volume_step_rate = 12.0; sc.cycles.volume_max_steps = 64; sc.cycles.adaptive_threshold = .05
sky = K.Sky(); cam = K.Cam()
PLAN = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8"))
SPLAN = {s["id"]: s for s in PLAN["shots"]}
SIM = PLAN["sim"]


def log(*a):
    print(f"[{_time.time() - _T0:7.1f}s]", *a, flush=True)

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


ENV = bpy.data.collections.new("env"); sc.collection.children.link(ENV)
DYN = []   # コマごとに形を作り直す物（ハンマーの群れ・逃げる人）。描くときに frame_change_pre で呼ぶ（動きのぶれの途中の時刻にも呼ばれる）


def _dyn_handler(scene, depsgraph=None):
    t = (scene.frame_current - 1 + scene.frame_subframe) / K.FPS
    for fn in DYN:
        fn(t)


bpy.app.handlers.frame_change_pre.append(_dyn_handler)


def env_clear():
    DYN.clear()
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




def emat(name, col, rough=.6, emit=None, k=0., haze=True):
    m = mat(name, col, rough, haze=haze); b = m.node_tree.nodes["Principled BSDF"]
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = k
    return m


def esock(m):
    return m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]


def face(a, b):
    """a から b を向く heading（怪獣の前は -Y）"""
    d = Vector(b) - Vector(a); return math.atan2(d.x, -d.y)


def keyhide(o, h, f):
    o.hide_render = h; o.keyframe_insert("hide_render", frame=f + 1)


def cut(u0, u1, u):
    return clamp((u - u0) / max(1e-6, u1 - u0))


# ---------------------------------------------------------------- 地形：草原と丘（丘の上は怪獣の頭と同じ高さ 43 m）。座標は m、怪獣は原点、南が -Y
HILL = Vector((0, -175, 0)); HILL_H = 43.0; HILL_R = 85.0


def hill_z(x, y):
    d = math.hypot(x - HILL.x, y - HILL.y)
    if d < HILL_R:
        return HILL_H
    return HILL_H * math.exp(-((d - HILL_R) / 28.0) ** 2)   # 斜面は急に（怪獣の足もとまで届かない）


def ground_grass():
    if "grass" in MATS:
        return MATS["grass"]
    m = bpy.data.materials.new("grass"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    geo = t.nodes.new("ShaderNodeNewGeometry")
    n1 = t.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = .02; n1.inputs["Detail"].default_value = 8
    n2 = t.nodes.new("ShaderNodeTexNoise"); n2.inputs["Scale"].default_value = .4; n2.inputs["Detail"].default_value = 4
    L.new(geo.outputs["Position"], n1.inputs["Vector"]); L.new(geo.outputs["Position"], n2.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (.06, .1, .03, 1); ramp.color_ramp.elements[1].color = (.2, .23, .09, 1)
    mx = t.nodes.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"; mx.inputs[1].default_value = .5
    L.new(n1.outputs["Fac"], mx.inputs[0]); L.new(n2.outputs["Fac"], mx.inputs[2]); L.new(mx.outputs[0], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"])
    bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .4; L.new(n2.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = .95
    add_haze(m, 600., 9000., .85); MATS["grass"] = m; return m


def terrain(size=8000., res=260):
    """草原（ゆるい起伏、遠くは丘陵）と丘。中心ほど細かい格子"""
    xs = np.linspace(-1, 1, res + 1); xs = np.sign(xs) * np.abs(xs) ** 2 * size / 2
    X, Y = np.meshgrid(xs, xs + (-100))
    D = np.hypot(X, Y)
    Z = np.vectorize(hill_z)(X, Y) + 1.5 * np.sin(X / 230.) * np.cos(Y / 310.) + np.clip((D - 900) / 2000, 0, 1) * (60 * np.sin(X / 700.) * np.cos(Y / 900.) + 40)
    v = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    n = res + 1; faces = [(i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j) for i in range(res) for j in range(res)]
    me = bpy.data.meshes.new("terrain"); me.from_pydata(v.tolist(), [], faces); me.update()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(ground_grass())
    return link(bpy.data.objects.new("terrain", me))


# ---------------------------------------------------------------- 人：顔のないピクトグラム（陸上の選手）
def crowd(points, seed=5, name="crowd"):
    rnd = random.Random(seed); bv, bf = _template("cone"); hv, hf = _template("ico")
    cols = [mat(f"pp{i}", c, .7) for i, c in enumerate([(.85, .85, .82), (.7, .12, .1), (.12, .2, .5), (.9, .75, .15), (.15, .15, .17)])]
    xb, mb, xh = [], [], []
    for (x, y, z) in points:
        h = rnd.uniform(1.75, 1.95)
        xb.append((x, y, z + h * .38, .24, .24, h * .76, 0, 0, 0)); mb.append(rnd.randrange(len(cols)))
        xh.append((x, y, z + h * .88, .12, .12, .13, 0, 0, 0))
    body = instances(name + "_body", bv, bf, xb, cols, np.array(mb))
    head = instances(name + "_head", hv, hf, xh, [mat("skinp", (.55, .4, .3), .7)])
    return body, head


def plain_points(n, seed=1):
    """平地の 5 万人：怪獣の南に、半径 40〜170 m の扇形"""
    rnd = random.Random(seed); pts = []
    while len(pts) < n:
        a = rnd.uniform(math.radians(200), math.radians(340)); r = rnd.uniform(40, 175)
        x, y = math.cos(a) * r, math.sin(a) * r
        if hill_z(x, y) > 2:
            continue
        pts.append((x, y, hill_z(x, y)))
    return pts


HOLES = []   # 群衆を置かない所（カメラのまわり）：[(x, y, 半径)]。ショットごとに決める


def hill_points(n, seed=2):
    rnd = random.Random(seed); pts = []
    while len(pts) < n:
        a = rnd.uniform(0, 2 * math.pi); r = HILL_R * math.sqrt(rnd.random()) * .98
        x, y = HILL.x + math.cos(a) * r, HILL.y + math.sin(a) * r
        if any((x - hx) ** 2 + (y - hy) ** 2 < hr * hr for hx, hy, hr in HOLES):
            continue
        pts.append((x, y, HILL_H))
    return pts


# ---------------------------------------------------------------- 怪獣（オリジナル：恐竜型、背中に角のようなとげ、太い尾。身長 50 m）
MONC = bpy.data.collections.new("monster"); sc.collection.children.link(MONC)


def mlink(o):
    MONC.objects.link(o); return o


def scale_mat():
    m = bpy.data.materials.new("scales"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    tc = t.nodes.new("ShaderNodeTexCoord")
    vo = t.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = .9; L.new(tc.outputs["Object"], vo.inputs["Vector"])
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = .06; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (.012, .015, .013, 1); ramp.color_ramp.elements[1].color = (.055, .062, .052, 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0]); L.new(ramp.outputs[0], b.inputs["Base Color"])
    bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .8; bp.inputs["Distance"].default_value = .4
    L.new(vo.outputs["Distance"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = .55; b.inputs["Specular IOR Level"].default_value = .4
    add_haze(m, 600., 9000., .85); return m


SCALES = scale_mat()


def mpart(name, elems, pivot, parent=None, res=.9):
    mb = bpy.data.metaballs.new("mb_" + name); mb.resolution = res; mb.render_resolution = res * .7; mb.threshold = .05
    ob = bpy.data.objects.new("mb_" + name, mb); sc.collection.objects.link(ob)
    for p, r, kind, s in elems:
        e = mb.elements.new(); e.type = kind; e.co = p; e.radius = r
        if kind == "ELLIPSOID":
            e.size_x, e.size_y, e.size_z = s
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True); bpy.ops.object.convert(target="MESH")
    o = bpy.context.active_object; o.name = name
    for c_ in list(o.users_collection):
        c_.objects.unlink(o)
    mlink(o); pv = Vector(pivot)
    for v in o.data.vertices:
        v.co -= pv
    o.location = pv if parent is None else pv - Vector(parent["pivot"]); o["pivot"] = tuple(pv)
    if parent is not None:
        o.parent = parent
    for p_ in o.data.polygons:
        p_.use_smooth = True
    o.data.materials.append(SCALES); o.rotation_mode = "XYZ"
    return o


def spikes(parent, pts, m):
    """背中のとげ（角のような円すい。特定の作品の背びれの形は使わない）。pts：(x, y, z, 長さ, 前後の傾き)"""
    bm = bmesh.new()
    for (x, y, z, h, tilt) in pts:
        r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=h * .22, radius2=h * .02, depth=h)
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=r_["verts"])
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(tilt, 3, "X"), verts=r_["verts"])
        bmesh.ops.translate(bm, vec=(x, y, z - h * .15), verts=r_["verts"])
    me = bpy.data.meshes.new("spikes_" + parent.name); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = mlink(bpy.data.objects.new("spikes_" + parent.name, me)); o.parent = parent
    o.location = -Vector(parent["pivot"]); return o


def build_monster():
    """身長 50 m。前が -Y。体（胴・腰・足・尾）は 1 つのつながった面、頭と腕は動かすので別"""
    E = "ELLIPSOID"
    root = mlink(bpy.data.objects.new("monster", None)); root["pivot"] = (0, 0, 0); root.rotation_mode = "XYZ"
    body = [((0, 1, 26), 8.0, E, (1, .9, 1.45)), ((0, 0, 33), 5.8, E, (1.05, .95, 1.1)),
            ((0, 3, 17), 8.8, E, (1.1, 1.05, 1.0)),
            ((-5.6, 3.5, 13), 5.2, E, (.95, 1.15, 1.45)), ((5.6, 3.5, 13), 5.2, E, (.95, 1.15, 1.45)),
            ((-6.0, 2.0, 6.5), 3.7, E, (1, 1.05, 1.5)), ((6.0, 2.0, 6.5), 3.7, E, (1, 1.05, 1.5)),
            ((-6.0, -.8, 1.3), 3.3, E, (1.15, 1.9, .5)), ((6.0, -.8, 1.3), 3.3, E, (1.15, 1.9, .5))]
    for i in range(14):   # 尾（腰から地面へ、細く長く）
        k = i / 13; body.append(((0, 8 + 30 * k, 15 - 13.5 * k ** .8), 6.2 * (1 - .78 * k), E, (1, 1.5, .85)))
    torso = mpart("m_torso", body, (0, 3, 16), root, .45)
    head = mpart("m_head", [((0, -.5, 37.5), 4.3, E, (1, 1.05, 1.5)),
                            ((0, -3.2, 43.2), 4.1, E, (1.05, 1.25, .9)),
                            ((0, -8.0, 42.4), 2.9, E, (.9, 1.6, .62)),
                            ((-1.9, -5.0, 44.8), 1.4, E, (1, 1.4, .55)), ((1.9, -5.0, 44.8), 1.4, E, (1, 1.4, .55))],
                 (0, 0, 35), torso, .3)
    jaw = mpart("m_jaw", [((0, -7.4, 40.6), 2.5, E, (.85, 1.55, .42)), ((0, -3.5, 40.6), 2.9, E, (1, 1.1, .5))], (0, -2.5, 41), head, .3)
    tm = mat("m_teeth", (.75, .72, .62), .4, haze=False)
    bm = bmesh.new()
    for i in range(9):   # 歯（口を開けると見える）
        for sx in (-1, 1):
            y = -10.3 + i * .75; r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.18, radius2=.02, depth=.7)
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 3, "X"), verts=r_["verts"]); bmesh.ops.translate(bm, vec=(sx * (1.6 + .05 * i), y, 41.3), verts=r_["verts"])
    me = bpy.data.meshes.new("teeth"); bm.to_mesh(me); bm.free(); me.materials.append(tm)
    th = mlink(bpy.data.objects.new("m_teeth", me)); th.parent = head; th.location = -Vector(head["pivot"])
    eye_m = emat("m_eye", (.6, .35, .05), .12, (1.0, .55, .1), 1.2, haze=False)
    lids = []
    for sx in (-1, 1):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=.6)
        me = bpy.data.meshes.new(f"eye{sx}"); bm.to_mesh(me); bm.free(); me.materials.append(eye_m)
        e = mlink(bpy.data.objects.new(f"m_eye{sx}", me)); e.parent = head; e.location = Vector((sx * 2.55, -5.4, 44.0)) - Vector(head["pivot"])
        for p in me.polygons:
            p.use_smooth = True
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=.68)
        me = bpy.data.meshes.new(f"lid{sx}"); bm.to_mesh(me); bm.free(); me.materials.append(SCALES)
        l_ = mlink(bpy.data.objects.new(f"m_lid{sx}", me)); l_.parent = head; l_.location = Vector((sx * 2.55, -5.35, 44.0)) - Vector(head["pivot"]); l_.scale = (1, 1, .05); lids.append(l_)
    arms = []
    for sx in (-1, 1):
        ar = mpart(f"m_arm{sx}", [((sx * 5.6, -2.4, 31.0), 2.4, E, (1, 1, 1.4)), ((sx * 6.3, -4.4, 27.2), 1.7, E, (1, 1.5, 1.0)), ((sx * 6.5, -6.2, 25.9), 1.2, E, (1.2, 1.2, .6))],
                   (sx * 5.2, -1.5, 32), torso, .3)   # 胸に食いこませて、離れて見えないように
        arms.append(ar)
    sp = mat("m_spike", (.05, .055, .05), .45)
    pts = []
    for i in range(10):
        for sx in ((0,) if i % 2 == 0 else (-1, 1)):
            pts.append((sx * 1.3, 6.5 + .9 * i, 37 - 2.4 * i, 4.6 - .22 * i, .55))
    pts += [(0, 9 + 2.4 * i, 17.5 - 1.05 * i ** 1.05, 3.6 - .2 * i, .9) for i in range(13)]
    spikes(torso, pts, sp)
    gm = emat("m_glow", (.02, .02, .018), .5, (1.0, .35, .05), 0.0, haze=False)   # ふだんは肌と同じ暗さ、炎の前だけ光る
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=2.2); me = bpy.data.meshes.new("glow"); bm.to_mesh(me); bm.free(); me.materials.append(gm)
    glow = mlink(bpy.data.objects.new("m_glow", me)); glow.parent = head; glow.location = Vector((0, -2.2, 38.0)) - Vector(head["pivot"]); glow.scale = (1, 1, 1.5)
    return dict(root=root, torso=torso, head=head, jaw=jaw, arms=arms, lids=lids, glow=gm)


MON = build_monster()
MON_ANIM = [MON["root"], MON["torso"], MON["head"], MON["jaw"]] + MON["arms"] + MON["lids"]
for o in MON_ANIM:
    o.rotation_mode = "XYZ"


def mpose(heading=0.0, torso=(0, 0, 0), head=(0, 0, 0), jaw=0.0, root_rot=None, root_loc=(0, 0, 0), lid=0.05, breathe=0.0, **_):
    R = MON["root"]; R.location = root_loc; R.rotation_euler = root_rot if root_rot is not None else (0, 0, heading)
    MON["torso"].rotation_euler = torso; MON["torso"].scale = (1 + .04 * breathe, 1 + .05 * breathe, 1)
    MON["head"].rotation_euler = head; MON["jaw"].rotation_euler = (jaw, 0, 0)
    for l_ in MON["lids"]:
        l_.scale = (1, 1, max(.05, lid))


def mouth_world():
    bpy.context.view_layer.update(); h = MON["head"]
    return h.matrix_world @ (Vector((0, -10.8, 41.0)) - Vector(h["pivot"])), (h.matrix_world.to_3x3() @ Vector((0, -1, -.15))).normalized()


# ---------------------------------------------------------------- 炎：口から伸びる円すい（光る。閃光にしない）＋煙
def fire_mat(length, r1, r2):
    """体積の炎：中心ほど濃く熱い（オレンジ〜黄色に光る）、外側は黒い煙。4D ノイズの W を毎コマ動かして揺らす"""
    m = bpy.data.materials.new("fire"); m.use_nodes = True; t = m.node_tree; L = t.links
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    tc = t.nodes.new("ShaderNodeTexCoord"); sep = t.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0])
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = .06; nz.inputs["Detail"].default_value = 8; nz.inputs["Roughness"].default_value = .62
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    # 半径方向の割合 r / R(z)（R は根元 r1 → 先 r2）
    ln = t.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    cxy = t.nodes.new("ShaderNodeCombineXYZ"); L.new(sep.outputs["X"], cxy.inputs["X"]); L.new(sep.outputs["Y"], cxy.inputs["Y"]); L.new(cxy.outputs[0], ln.inputs[0])
    rz = t.nodes.new("ShaderNodeMapRange"); rz.inputs[1].default_value = 0; rz.inputs[2].default_value = length; rz.inputs[3].default_value = r1; rz.inputs[4].default_value = r2
    L.new(sep.outputs["Z"], rz.inputs[0])
    dv = t.nodes.new("ShaderNodeMath"); dv.operation = "DIVIDE"; L.new(ln.outputs["Value"], dv.inputs[0]); L.new(rz.outputs[0], dv.inputs[1])
    core = t.nodes.new("ShaderNodeMapRange"); core.inputs[1].default_value = .15; core.inputs[2].default_value = 1.0; core.inputs[3].default_value = 1.0; core.inputs[4].default_value = 0.0
    L.new(dv.outputs[0], core.inputs[0])
    sh = t.nodes.new("ShaderNodeMapRange"); sh.inputs[1].default_value = .38; sh.inputs[2].default_value = .72; L.new(nz.outputs["Fac"], sh.inputs[0])   # ノイズで炎のかたまり
    dens = t.nodes.new("ShaderNodeMath"); dens.operation = "MULTIPLY"; L.new(core.outputs[0], dens.inputs[0]); L.new(sh.outputs[0], dens.inputs[1])
    pv = t.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Color"].default_value = (.35, .25, .18, 1)
    dsc = t.nodes.new("ShaderNodeMath"); dsc.operation = "MULTIPLY"; dsc.inputs[1].default_value = .035; L.new(dens.outputs[0], dsc.inputs[0]); L.new(dsc.outputs[0], pv.inputs["Density"])
    hot = t.nodes.new("ShaderNodeMath"); hot.operation = "POWER"; hot.inputs[1].default_value = 1.6; L.new(dens.outputs[0], hot.inputs[0])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (1.0, .18, .0, 1); ramp.color_ramp.elements[1].color = (1.0, .62, .08, 1)
    L.new(hot.outputs[0], ramp.inputs[0]); L.new(ramp.outputs[0], pv.inputs["Emission Color"])
    es = t.nodes.new("ShaderNodeMath"); es.operation = "MULTIPLY"; es.inputs[1].default_value = 90.0   # 濃いオレンジに強く光る（閃光にはしない）; L.new(hot.outputs[0], es.inputs[0]); L.new(es.outputs[0], pv.inputs["Emission Strength"])
    L.new(pv.outputs[0], t.nodes["Material Output"].inputs["Volume"])
    return m, es.inputs[1], nz.inputs["W"]


CORE_W = {}


def fire_cone(length=160., r1=1.5, r2=28.):
    """炎の入れ物（閉じた円すい、+Z 向き）と、炎のまわりを照らすオレンジの光"""
    bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=r1 * 1.4, radius2=r2 * 1.4, depth=length)
    bmesh.ops.translate(bm, vec=(0, 0, length / 2), verts=r_["verts"])
    me = bpy.data.meshes.new("fire"); bm.to_mesh(me); bm.free()
    m, k, w = fire_mat(length, r1, r2); me.materials.append(m)
    o = link(bpy.data.objects.new("fire", me)); o.rotation_mode = "QUATERNION"
    lt = bpy.data.lights.new("firelight", "POINT"); lt.color = (1.0, .45, .12); lt.energy = 0; lt.shadow_soft_size = 20
    lo = link(bpy.data.objects.new("firelight", lt))
    # 明るい芯（光る面。ノイズで穴をあけて、炎のかたまりに見せる）
    bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=False, segments=32, radius1=r1 * .6, radius2=r2 * .55, depth=length)
    bmesh.ops.translate(bm, vec=(0, 0, length / 2), verts=r_["verts"]); bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
    me2 = bpy.data.meshes.new("firecore"); bm.to_mesh(me2); bm.free()
    cm = bpy.data.materials.new("firecore"); cm.use_nodes = True; t = cm.node_tree; L = t.links
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = .12; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (1.0, .22, .0, 1); ramp.color_ramp.elements[1].color = (1.0, .78, .25, 1); L.new(nz.outputs["Fac"], ramp.inputs[0])
    em = t.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 7.0; L.new(ramp.outputs[0], em.inputs["Color"])
    tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader")
    al = t.nodes.new("ShaderNodeMapRange"); al.inputs[1].default_value = .42; al.inputs[2].default_value = .62; L.new(nz.outputs["Fac"], al.inputs[0])
    L.new(al.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    me2.materials.append(cm); co = link(bpy.data.objects.new("firecore", me2)); co.rotation_mode = "QUATERNION"
    o["light"] = lo.name; o["len"] = length; o["core"] = co.name; o["corew"] = 0
    CORE_W[co.name] = nz.inputs["W"]
    return o, (k, w, lt)


def fire_puff(name, loc, r, k=6.0):
    """地面で燃える炎（体積、光る）。puff と同じ形で、光る"""
    o, dk = puff(name, loc, r, (.05, .04, .03), .02)
    m = o.data.materials[0]; t = m.node_tree; pv = next(n for n in t.nodes if n.type == "PRINCIPLED_VOLUME")
    pv.inputs["Emission Color"].default_value = (1.0, .35, .06, 1)
    src = pv.inputs["Density"].links[0].from_socket
    mm = t.nodes.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; mm.inputs[1].default_value = k * 40
    t.links.new(src, mm.inputs[0]); t.links.new(mm.outputs[0], pv.inputs["Emission Strength"])
    return o, dk


def aim_fire(o, origin, d, f, on=True, scale=1.0, ctl=None, length=None):
    """炎を origin から d の向きへ。length を渡すとその長さまで伸ばす（地面に当たる所まで）"""
    o.location = origin; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    sz = (length / o["len"]) if length else 1.0
    o.scale = (scale, scale, scale * sz) if on else (.001, .001, .001)
    o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_quaternion", frame=f + 1); o.keyframe_insert("scale", frame=f + 1)
    co = bpy.data.objects[o["core"]]
    co.location = o.location; co.rotation_quaternion = o.rotation_quaternion; co.scale = o.scale
    co.keyframe_insert("location", frame=f + 1); co.keyframe_insert("rotation_quaternion", frame=f + 1); co.keyframe_insert("scale", frame=f + 1)
    key_v(CORE_W[co.name], f * .08, f)
    if ctl:
        k, w, lt = ctl; key_v(w, f * .06, f)   # 炎の揺れ
        lo = bpy.data.objects[o["light"]]; keyp(lo, f, loc=tuple(Vector(origin) + d * (length or o["len"]) * .7))
        lt.energy = 6e6 * scale if on else 0; lt.keyframe_insert("energy", frame=f + 1)


# ---------------------------------------------------------------- ハンマー（代表の数百本。見えるように頭を大きめに）
def hammer_objs(n, seed=9, vis=1.6):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=.06 * vis * 4)
    me = bpy.data.meshes.new("hammer"); bm.to_mesh(me); bm.free(); me.materials.append(mat("steel", (.6, .6, .62), .25, .9))
    for p in me.polygons:
        p.use_smooth = True
    return [link(bpy.data.objects.new(f"hm{i}", me)) for i in range(n)]


def parabola(p0, p1, apex_h, u):
    """p0 から p1 へ、頂点の高さが（高い方の端から）apex_h の放物線（u＝0→1）"""
    p = p0.lerp(p1, u); z0, z1 = p0.z, p1.z
    zt = max(z0, z1) + apex_h
    a = 2 * z1 + 2 * z0 - 4 * zt; b = 4 * zt - 3 * z0 - z1
    p.z = a * u * u + b * u + z0; return p


def throw_set(objs, origins, target_fn, t0, t1, t, f, apex=20.0):
    u = cut(t0, t1, t)
    for i, o in enumerate(objs):
        if t < t0:
            keyp(o, f, loc=(0, 0, -1e4))
        else:
            keyp(o, f, loc=tuple(parabola(origins[i], target_fn(i), apex, u)))


# ---------------------------------------------------------------- ハンマーの群れ（本物の形：鉄の球＋ワイヤー＋取っ手。1 つのメッシュをコマごとに作り直す）
def hammer_template(s=1.0):
    """+Z がワイヤーの向き（球は原点、ワイヤーは後ろに伸びる）。本物：球の直径 11 cm、全長 1.2 m"""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=.06 * s)
    r_ = bmesh.ops.create_cone(bm, cap_ends=False, segments=5, radius1=.006 * s * 2, radius2=.006 * s * 2, depth=1.05 * s); bmesh.ops.translate(bm, vec=(0, 0, .58 * s), verts=r_["verts"])
    h_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.045 * s, radius2=.045 * s, depth=.012 * s); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=h_["verts"]); bmesh.ops.translate(bm, vec=(0, 0, 1.13 * s), verts=h_["verts"])   # 取っ手（小さな輪）
    v = np.array([tuple(x.co) for x in bm.verts], float); f = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free()
    return v, f


def _rot_to(d):
    """+Z を d（N×3、正規化済み）へ向ける回転行列（N×3×3）"""
    vx, vy, c = -d[:, 1], d[:, 0], d[:, 2]
    K_ = np.zeros((len(d), 3, 3)); K_[:, 0, 2] = vy; K_[:, 1, 2] = -vx; K_[:, 2, 0] = -vy; K_[:, 2, 1] = vx
    k = 1 / np.maximum(1 + c, 1e-4)
    return np.eye(3)[None] + K_ + np.einsum("nij,njk->nik", K_, K_) * k[:, None, None]


class Swarm:
    """ハンマーの群れ。O（投げた所）→ T（当たる所）を、物語の時刻 s0+delay から tf 秒で放物線（頂点は高い方の端 + apex）。
    当たったあとは跳ね返って落ちる（bounce=True）。clock(t)：ショットの中の秒 → 物語の時刻"""
    def __init__(self, name, O, T, s0, tf, apex, clock, delay=None, scale=1.0, bounce=False, seed=1):
        self.O = np.asarray(O, float); self.T = np.asarray(T, float); N = len(self.O)
        self.s0, self.tf, self.apex, self.clock, self.bounce = s0, tf, np.full(N, apex) if np.isscalar(apex) else np.asarray(apex), clock, bounce
        rnd = np.random.default_rng(seed); self.D = rnd.uniform(0, .04, N) if delay is None else np.asarray(delay)
        self.BV = np.stack([rnd.uniform(-8, 8, N), rnd.uniform(-14, -4, N), rnd.uniform(2, 10, N)], 1)   # 跳ね返る速さ
        self.spin = rnd.uniform(0, 6.28, N)
        tv, tf_ = hammer_template(scale); self.tv = tv; nv = len(tv)
        faces = (np.asarray([list(fc) + [-1] * (4 - len(fc)) if len(fc) < 4 else list(fc) for fc in tf_]))
        allf = [tuple(i * nv + k for k in fc) for i in range(N) for fc in tf_]
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((N * nv, 3)).tolist(), [], allf); me.update()
        me.materials.append(mat("steel", (.62, .62, .64), .22, .95))
        self.me = me; self.obj = link(bpy.data.objects.new(name, me)); DYN.append(self.update)

    def state(self, t):
        s = self.clock(t); u = np.clip((s - self.s0 - self.D) / self.tf, 0, None)
        z0, z1 = self.O[:, 2], self.T[:, 2]; zt = np.maximum(z0, z1) + self.apex
        a = 2 * z1 + 2 * z0 - 4 * zt; b = 4 * zt - 3 * z0 - z1
        uc = np.minimum(u, 1.0)
        P = self.O + (self.T - self.O) * uc[:, None]; P[:, 2] = a * uc * uc + b * uc + z0
        V = (self.T - self.O) / self.tf; V[:, 2] = (2 * a * uc + b) / self.tf
        if self.bounce:
            e = np.maximum(0, (u - 1) * self.tf)[:, None]; hit = (u > 1)[:, None]
            Pb = self.T + self.BV * e + np.array([0, 0, -4.9]) * e * e; Pb[:, 2] = np.maximum(Pb[:, 2], .1)
            Vb = self.BV + np.array([0, 0, -9.8]) * e
            P = np.where(hit, Pb, P); V = np.where(hit, Vb, V)
        else:
            P = np.where((u > 1)[:, None], self.T, P)
        P = np.where((u <= 0)[:, None], self.O, P)
        return P, V, u

    def update(self, t):
        P, V, u = self.state(t)
        d = -V / np.maximum(np.linalg.norm(V, axis=1, keepdims=True), 1e-6)   # ワイヤーは進む向きのうしろへ
        R = _rot_to(d); v = np.einsum("nij,vj->nvi", R, self.tv) + P[:, None, :]
        v[u <= 0] = -1e4   # まだ投げていない
        self.me.vertices.foreach_set("co", v.reshape(-1).astype(np.float32)); self.me.update()


class Runners:
    """逃げる人（顔のないピクトグラム）。P0 から dir の向きへ、t0 から speed m/s で走る。上下に小さく弾む"""
    def __init__(self, name, P0, dirs, t0, speed, seed=3):
        self.P0 = np.asarray(P0, float); self.dirs = np.asarray(dirs, float); N = len(self.P0)
        rnd = np.random.default_rng(seed); self.t0 = t0 + rnd.uniform(0, .5, N); self.sp = speed * rnd.uniform(.8, 1.2, N); self.ph = rnd.uniform(0, 6.28, N)
        bv, bf = _template("cone"); hv, hf = _template("ico")
        bv = bv * np.array([.24, .24, 1.35]) + np.array([0, 0, .68]); hv = hv * .13 + np.array([0, 0, 1.6])
        self.tv = np.concatenate([bv, hv]); nb = len(bv); tf_ = list(bf) + [tuple(k + nb for k in fc) for fc in hf]; nv = len(self.tv)
        allf = [tuple(i * nv + k for k in fc) for i in range(N) for fc in tf_]
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((N * nv, 3)).tolist(), [], allf); me.update()
        cols = [mat(f"pp{i}", c, .7) for i, c in enumerate([(.85, .85, .82), (.7, .12, .1), (.12, .2, .5), (.9, .75, .15), (.15, .15, .17)])]
        for c_ in cols:
            me.materials.append(c_)
        mi = np.repeat(rnd.integers(0, len(cols), N), len(tf_)); me.polygons.foreach_set("material_index", mi.astype(np.int32))
        self.me = me; link(bpy.data.objects.new(name, me)); DYN.append(self.update)

    def update(self, t):
        e = np.maximum(0, t - self.t0)
        P = self.P0 + self.dirs * (self.sp * e)[:, None]
        P[:, 2] = self.P0[:, 2] + .12 * np.abs(np.sin(e * 9 + self.ph)) * (e > 0)
        v = self.tv[None] + P[:, None, :]
        self.me.vertices.foreach_set("co", v.reshape(-1).astype(np.float32)); self.me.update()


def shot_clock(k):
    """ショット k の中の秒 → 物語の時刻（plan.json の c）"""
    s = SPLAN[k]; c = s["c"]; d = s["dur"]
    def f(t):
        u = clamp(t / d)
        for (u0, c0), (u1, c1) in zip(c, c[1:]):
            if u <= u1 or (u1, c1) == tuple(c[-1]):
                return c0 + (c1 - c0) * clamp((u - u0) / max(1e-9, u1 - u0))
        return c[-1][1]
    return f


THROW2, HIT2, FIRE2 = PLAN["throw2"], PLAN["hit2"], PLAN["fire"][1]


def hill_swarm(name, k, n, seed, near=None, scale=2.0, bounce=False):
    """丘の上から頭へ、4 万本の代表 n 本（同時に当たる：2 秒で頭に届く）。near：(点, 本数) その近くからも投げる（カメラのそば）"""
    rnd = random.Random(seed); pts = hill_points(40000, 4); O, T = [], []
    for i in range(n):
        p = Vector(pts[rnd.randrange(len(pts))]); O.append((p.x, p.y, p.z + 1.6))
        T.append(tuple(HEAD_POS + Vector((rnd.uniform(-3.5, 3.5), rnd.uniform(-2.5, 2.5), rnd.uniform(-2.5, 2.5)))))
    if near:
        c, m = near
        for i in range(m):
            O.append((c.x + rnd.uniform(-7, 7), c.y + rnd.uniform(-7, 7), c.z + rnd.uniform(-.5, 1.5)))
            T.append(tuple(HEAD_POS + Vector((rnd.uniform(-3, 3), rnd.uniform(-2, 2), rnd.uniform(-2, 2)))))
    return Swarm(name, O, T, THROW2, HIT2 - THROW2, 6.0, shot_clock(k), scale=scale, bounce=bounce, seed=seed)


# ---------------------------------------------------------------- 場面の土台
def base(sun_el=32, sun_rot=135, haze_col=(.78, .84, .9), haze_k=.9, d0=900., d1=14000., energy=9.0, blur=False):
    sky.set(0, sun_el, sun_rot, energy); set_haze(haze_col, haze_k, d0, d1); sc.render.use_motion_blur = blur; sc.render.motion_blur_shutter = .5


def scorch():
    m = emat("scorch", (.03, .028, .025), .9)
    tv, tf = _template("ico"); rnd = random.Random(4); xf = []
    for i in range(140):
        a = rnd.uniform(math.radians(200), math.radians(250)); r = rnd.uniform(40, 170)
        x, y = math.cos(a) * r, math.sin(a) * r
        xf.append((x, y, hill_z(x, y) - .05, rnd.uniform(6, 14), rnd.uniform(6, 14), .12, 0, 0, 0))   # 焼けあと（平たく）
    instances("scorch", tv, tf, xf, [m])


def world(people="plain", n=50000, holes=()):
    HOLES[:] = list(holes)
    env_clear(); terrain()
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=200000); bmesh.ops.translate(bm, vec=(0, 0, -25), verts=bm.verts)
    mesh_obj("farground", bm, [ground_grass()])   # 地形の外（遠く）も地面に（高いカメラで地平線の下が黒く見えないように）
    if people == "plain":
        crowd(plain_points(n))
    if people in ("hill", "both"):
        crowd(hill_points(40000, 4), 6, "hillcrowd")
    if people == "both":
        scorch()


HEAD_POS = Vector((0, -6, 43))


# ---------------------------------------------------------------- 各ショット
def s_l00():
    base(14, 120, (.95, .8, .65), .9); world("plain")
def a_l00(u, t, f):
    mpose(0.0, head=(.05 * math.sin(t), 0, 0), breathe=.3 * math.sin(t * 1.5), lid=1.0)
    cam.look(tuple(Vector((-95, -40, 3.5)) + Vector((4 * u, 3 * u, 0))), (0, -3, 30), 22)   # 群衆のうしろから見上げる（丘にかからない西側）


def s_l01():
    base(16, 125, (.95, .82, .7), .9); world("plain")
def a_l01(u, t, f):
    mpose(0.0, head=(.05 * math.sin(t), 0, .05 * math.sin(t * .6)), breathe=.3 * math.sin(t * 1.5), lid=1.0)
    cam.look(tuple(Vector((150, -120, 60)) + Vector((-25 * u, 15 * u, -8 * u))), (0, -40, 22), 26)


def s_l02():
    base(18, 130, (.92, .84, .75), .9); world("plain")
    global HM2, ORG2
    HM2 = hammer_objs(900); rnd = random.Random(2); pts = plain_points(50000)
    ORG2 = [Vector(pts[rnd.randrange(len(pts))]) + Vector((0, 0, 1.5)) for _ in HM2]
def a_l02(u, t, f):
    mpose(0.0, head=(.05 * math.sin(t), 0, 0), lid=1.0)
    throw_set(HM2, ORG2, lambda i: Vector((random.Random(i).uniform(-7, 7), random.Random(i + 9).uniform(-6, 0), random.Random(i + 3).uniform(16, 24))), .5, 3.4, t, f, 8.0)
    cam.look(tuple(Vector((-230, -200, 150)) + Vector((25 * u, 0, -15 * u))), (0, -60, 15), 30)


def s_l03():
    base(20, 135, (.9, .85, .8), .9); world("plain")
    global HM3, ORG3
    HM3 = hammer_objs(400, 3); rnd = random.Random(3)
    ORG3 = [Vector((rnd.uniform(-60, 60), rnd.uniform(-70, -45), 1.5)) for _ in HM3]
def a_l03(u, t, f):
    mpose(0.0, head=(.03 * math.sin(t), 0, 0), lid=1.0)
    hit = .6
    for i, o in enumerate(HM3):
        r = random.Random(i); tgt = Vector((r.uniform(-7, 7), -5 + r.uniform(-1, 1), r.uniform(14, 23)))
        if t < hit:
            p = parabola(ORG3[i], tgt, 6.0, .6 + .4 * t / hit)
        else:
            e = t - hit; p = tgt + Vector((r.uniform(-3, 3) * e, -r.uniform(4, 9) * e, r.uniform(2, 5) * e - 4.9 * e * e)); p.z = max(p.z, .2)
        keyp(o, f, loc=tuple(p))
    cam.look(tuple(Vector((-34, -48, 10)) + Vector((4 * u, 3 * u, 1 * u))), (0, -5, 20), 30)


def s_l04():
    """炎 1 回目：低い位置から。頭上を炎が走り、草原に当たって燃え広がる。手前の選手が走って逃げる"""
    base(22, 140, (.92, .8, .7), .9); world("plain")
    global FIRE4, FIRE4C, SMOKE4, SMOKE4K, GF4, RUN4
    FIRE4, FIRE4C = fire_cone(170, 1.6, 24); SMOKE4, SMOKE4K = puff("smoke4", (0, 0, -1e5), 80, (.18, .16, .15), .01)
    GF4 = [fire_puff(f"gf4_{i}", (0, 0, -1e5), 14) for i in range(7)]
    rnd = np.random.default_rng(4); n = 900; P0 = []; D = []
    for i in range(n):   # 炎の当たる所から、カメラの右手前へ逃げる
        x, y = -40 + rnd.uniform(-50, 50), -55 + rnd.uniform(-25, 25)
        if hill_z(x, y) > 1:
            continue
        P0.append((x, y, 0)); d = Vector((95 - x, -40 - y, 0)).normalized(); D.append((d.x, d.y, 0))
    RUN4 = Runners("run4", P0, D, 1.4, 7.0)
FIRE4_G = [Vector((-120, -40, 0)), Vector((-55, -115, 0))]   # 炎が地面をなめる道すじ（はじめ → おわり）
def a_l04(u, t, f):
    turn = ease(cut(0, .2, u)); fire = cut(.25, .88, u)
    mpose(-.6 * turn, head=(.3 * turn, 0, -.2 * turn), jaw=-.55 * (fire > 0) * (1 - cut(.88, 1, u)), breathe=-.6 * fire, lid=1.0)
    org, d0 = mouth_world(); G = FIRE4_G[0].lerp(FIRE4_G[1], ease(fire)); G.z = hill_z(G.x, G.y)
    d = (G - org).normalized(); L_ = (G - org).length
    on = fire > 0 and u < .92
    aim_fire(FIRE4, org, d, f, on=on, scale=min(1, .3 + fire * 3), ctl=FIRE4C, length=L_ * min(1, fire * 5))
    for i, (o, k) in enumerate(GF4):   # 当たった所から燃え広がる
        gi = FIRE4_G[0].lerp(FIRE4_G[1], i / 6); age = fire - i / 7
        keyp(o, f, loc=(gi.x, gi.y, 6) if age > 0 else (0, 0, -1e5), scale=6 + 16 * min(1, age * 3)); key_v(k, .05 * (age > 0), f)
    keyp(SMOKE4, f, loc=(G.x, G.y, 45) if fire > .15 else (0, 0, -1e5), scale=40 + 60 * fire); key_v(SMOKE4K, .01 * (fire > .15), f)
    cx, cy = 92 - 6 * u, -58 + 3 * u
    cam.look(tuple(Vector((cx, cy, hill_z(cx, cy) + 5.5)) + shake(f, .9 * (fire > 0), 4)), tuple(Vector((-22, -38, 24)) + Vector((0, 0, -6 * fire))), 20)   # 逃げる選手の中、低い所から（丘の斜面にもぐらない）


def s_l05():
    base(24, 140, (.88, .86, .82), .9); world("plain", 40000); scorch()
def a_l05(u, t, f):
    mpose(-.3, head=(.1, 0, -.1), lid=1.0)
    cam.look(tuple(Vector((330, -330, 140)) + Vector((-20 * u, 10 * u, 0))), (0, -110, 25), 30)


def s_l06():
    base(26, 145, (.88, .86, .82), .9); world("hill"); scorch()
def a_l06(u, t, f):
    mpose(-.2, head=(.08, 0, -.05), lid=1.0)
    cam.look(tuple(Vector((-320, -380, 260)) + Vector((40 * u, 20 * u, 0))), (0, -150, 30), 30)


def s_l07():
    base(26, 145, (.88, .84, .8), .9); world("hill"); scorch()
def a_l07(u, t, f):
    br = ease(cut(0, .8, u))
    mpose(0.0, head=(-.25 * br, 0, 0), jaw=-.05, breathe=1.0 * br, lid=1.0)
    key_v(esock(MON["glow"]), 25 * br, f)
    cam.look(tuple(Vector((38, -55, 30)) + Vector((-3 * u, 4 * u, 2 * u))), (0, -4, 36), 30)


def spinner(i, x, y, z, s=1.0):
    """回転する選手（ピクトグラム＋本物の形のハンマー）。root を Z まわりに回す"""
    root = link(bpy.data.objects.new(f"sp{i}", None)); root.location = (x, y, z); root.rotation_mode = "XYZ"
    bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=.25, radius2=.2, depth=1.4); bmesh.ops.translate(bm, vec=(0, 0, .7), verts=r_["verts"])
    s_ = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=.13); bmesh.ops.translate(bm, vec=(0, 0, 1.62), verts=s_["verts"])
    a_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.06, radius2=.05, depth=.62); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=a_["verts"]); bmesh.ops.translate(bm, vec=(.3, 0, 1.25), verts=a_["verts"])
    me = bpy.data.meshes.new(f"spm{i}"); bm.to_mesh(me); bm.free(); me.materials.append(mat(f"pp{i % 5}", [(.85, .85, .82), (.7, .12, .1), (.12, .2, .5), (.9, .75, .15), (.15, .15, .17)][i % 5], .7))
    o = link(bpy.data.objects.new(f"spo{i}", me)); o.parent = root
    tv, tf_ = hammer_template(s * 1.0)
    R = np.array(Matrix.Rotation(-math.pi / 2, 3, "Y"))   # ワイヤーを体から外へ（+X）。球が外側
    v = (tv[:, [0, 1, 2]] @ R.T)
    v = v * np.array([-1, 1, 1]) + np.array([1.85, 0, 1.15])
    me2 = bpy.data.meshes.new(f"sph{i}"); me2.from_pydata(v.tolist(), [], tf_); me2.materials.append(mat("steel", (.62, .62, .64), .22, .95))
    h = link(bpy.data.objects.new(f"sph{i}", me2)); h.parent = root
    for p in me2.polygons:
        p.use_smooth = True
    return root


def s_l08():
    """丘の上で選手たちが回転する（スロー）。手前の選手は大きく、奥の怪獣ののどが光る"""
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill", holes=[(HILL.x - 38, HILL.y + HILL_R - 30, 12)]); scorch()
    global SPIN
    SPIN = []; rnd = random.Random(8)
    for i in range(60):
        x = HILL.x + rnd.uniform(-45, 45); y = HILL.y + HILL_R - rnd.uniform(3, 40)
        SPIN.append((spinner(i, x, y, HILL_H), rnd.uniform(0, 6.28), rnd.uniform(.9, 1.1)))
def a_l08(u, t, f):
    mpose(0.0, head=(-.25, 0, 0), jaw=-.05, breathe=1.0, lid=1.0); key_v(esock(MON["glow"]), 25 + 15 * u, f)
    for root, ph, sp in SPIN:   # だんだん速く 3 回転半（スロー）
        keyp(root, f, rot=(0, 0, ph + 2 * math.pi * 3.5 * sp * cut(0, 1, u) ** 1.6))
    c = HILL + Vector((-38, HILL_R - 30, HILL_H + 4.5)) + Vector((3 * u, 2 * u, 0))
    cam.look(tuple(c), tuple(Vector((10, -40, 42))), 26)   # 回る選手の列を斜めうしろから、奥に怪獣


def s_l09():
    """一斉に放す：何千本ものハンマーがカメラの横を抜けて怪獣へ（丘の縁、低い位置）"""
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill", holes=[(HILL.x + 12, HILL.y + HILL_R - 8, 16)]); scorch()
    global SW9
    camp = HILL + Vector((10, HILL_R - 6, HILL_H))
    SW9 = hill_swarm("sw9", "l09", 3500, 9, near=(camp + Vector((0, 6, 0)), 600), scale=2.2)
def a_l09(u, t, f):
    mpose(0.0, head=(-.25, 0, 0), jaw=-.05, breathe=1.0, lid=1.0); key_v(esock(MON["glow"]), 40, f)
    c = HILL + Vector((22, HILL_R - 22, HILL_H + 9)) + Vector((-4 * u, 10 * u, 1.5 * u))
    cam.look(tuple(c + shake(f, .25, 9)), tuple(Vector((0, -45, 46)).lerp(HEAD_POS, u)), 24)


def s_l10():
    """ハンマーと一緒に飛ぶカメラ：群れの中から、迫る怪獣の頭（スロー）"""
    base(26, 150, (.88, .84, .8), .9, blur=False); world("hill"); scorch()
    global SW10, CAM10
    CAM10 = (Vector((2, -110, 45.5)), HEAD_POS + Vector((1, -9, 1)))   # カメラの道すじ（投げた所の近く → 頭の手前）
    SW10 = hill_swarm("sw10", "l10", 3500, 10, near=(CAM10[0] + Vector((0, 4, 0)), 350), scale=2.0)
def a_l10(u, t, f):
    mpose(0.0, head=(-.25, 0, 0), jaw=-.05, breathe=1.0, lid=1.0); key_v(esock(MON["glow"]), 45, f)
    s = shot_clock("l10")(t); k = clamp((s - THROW2) / (HIT2 - THROW2))
    a, b = CAM10; p = a.lerp(b, k); p.z = a.z + 9 * math.sin(math.pi * k) * .8   # 群れと同じ放物線ぎみに
    cam.look(tuple(p + shake(f, .15, 10)), tuple(HEAD_POS + Vector((0, 0, -1))), 24 + 6 * k)


def s_l11():
    """頭に当たる。頭がはじかれ、ハンマーが跳ね返る"""
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill"); scorch()
    global SW11, DUST11, DUST11K
    SW11 = hill_swarm("sw11", "l11", 2500, 11, scale=2.0, bounce=True)
    DUST11, DUST11K = puff("hitdust", (0, 0, -1e5), 6, (.5, .45, .4), .02)
def a_l11(u, t, f):
    s = shot_clock("l11")(t); e = max(0., s - HIT2) * 4   # スロー（物語の 0.6 秒を 2.8 秒で）
    jolt = (1 - math.exp(-e * 6)) * math.exp(-e * .8) if e > 0 else 0
    mpose(0.0, head=(-.25 - .5 * jolt, 0, .15 * jolt), torso=(-.08 * jolt, 0, 0), jaw=-.05 - .35 * jolt, breathe=1.0 - jolt, lid=1.0)
    key_v(esock(MON["glow"]), 45 * (1 - min(1, e * 2)), f)
    keyp(DUST11, f, loc=tuple(HEAD_POS + Vector((0, -5, 0))) if e > 0 else (0, 0, -1e5), scale=6 + 25 * min(1, e)); key_v(DUST11K, .02 * max(0, 1 - e), f)
    cam.look(tuple(Vector((30, -34, 44)) + shake(f, 1.6 * max(0, 1 - e * 1.5), 5)), tuple(HEAD_POS), 32)


def s_l12():
    """ふらつく怪獣が最後の炎を吐く。炎は丘に届き、選手が逃げる（丘の上の低い所から）"""
    base(26, 150, (.88, .84, .8), .9); world("hill"); scorch()
    global FIRE12, FIRE12C, GF12, RUN12, SMOKE12, SMOKE12K
    FIRE12, FIRE12C = fire_cone(150, 1.4, 22); GF12 = [fire_puff(f"gf12_{i}", (0, 0, -1e5), 12) for i in range(6)]
    SMOKE12, SMOKE12K = puff("smoke12", (0, 0, -1e5), 60, (.18, .16, .15), .01)
    rnd = np.random.default_rng(12); n = 900; P0 = []; D = []
    for i in range(n):
        x, y = rnd.uniform(-50, 50), HILL.y + HILL_R - rnd.uniform(0, 45)
        P0.append((x, y, HILL_H)); d = Vector((rnd.uniform(-.4, .4), -1, 0)).normalized(); D.append((d.x, d.y, 0))
    RUN12 = Runners("run12", P0, D, 1.2, 6.5)
FIRE12_G = [Vector((-35, -98, HILL_H)), Vector((30, -112, HILL_H))]
def a_l12(u, t, f):
    w = math.sin(t * 2.2) * (.05 + .05 * u)
    fire = cut(.22, .85, u)
    mpose(0.0, torso=(-.05 + w * .5, w, 0), head=(.05 + .1 * math.sin(t * 1.7), .15 * w, .15 * math.sin(t * 1.3)), jaw=-.55 * (fire > 0), breathe=.3, lid=.6 + .4 * math.cos(t * 3))
    org, d0 = mouth_world(); G = FIRE12_G[0].lerp(FIRE12_G[1], ease(fire)); d = (G - org).normalized(); L_ = (G - org).length
    aim_fire(FIRE12, org, d, f, on=fire > 0 and u < .93, scale=min(1, .3 + fire * 3), ctl=FIRE12C, length=L_ * min(1, fire * 5))
    for i, (o, k) in enumerate(GF12):
        gi = FIRE12_G[0].lerp(FIRE12_G[1], i / 5); age = fire - i / 6
        keyp(o, f, loc=(gi.x, gi.y, HILL_H + 5) if age > 0 else (0, 0, -1e5), scale=5 + 13 * min(1, age * 3)); key_v(k, .05 * (age > 0), f)
    keyp(SMOKE12, f, loc=(G.x, G.y, HILL_H + 35) if fire > .15 else (0, 0, -1e5), scale=30 + 50 * fire); key_v(SMOKE12K, .01 * (fire > .15), f)
    cx, cy = 150 - 8 * u, -95 + 4 * u
    cam.look(tuple(Vector((cx, cy, hill_z(cx, cy) + 6)) + shake(f, .8 * (fire > 0), 12)), tuple(Vector((-5, -60, 36))), 22)   # 丘の横から：怪獣の炎が丘の上に届く


def s_l13():
    """怪獣が倒れる（スロー）。地響き、土煙の輪、飛び散る土"""
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill"); scorch()
    global DUST13, RING13, ROCK13
    DUST13 = [puff(f"fd{i}", (0, 0, -1e5), 30, (.62, .57, .5), .002) for i in range(10)]
    RING13 = [puff(f"ring{i}", (0, 0, -1e5), 20, (.6, .55, .48), .0025) for i in range(16)]


FALL0, FALL1 = .08, .55
def a_l13(u, t, f):
    k = ease(cut(FALL0, FALL1, u)) ** 1.8; tip = (math.pi / 2 - .12) * k   # かかとを支点にあお向けに倒れる（スロー）
    mpose(root_rot=(-tip, 0, 0), root_loc=(0, 4 * k, 0), head=(-.4 + .3 * k, 0, .25), jaw=-.35, lid=.3)
    e = cut(FALL1, 1, u)
    for i, (o, kk) in enumerate(DUST13):   # 体の当たった所に土煙
        y = 8 + i * 5; keyp(o, f, loc=(0, y, 8 + 10 * e) if e > 0 else (0, 0, -1e5), scale=18 + 40 * e); key_v(kk, .004 * (e > 0) * (1 - .4 * e), f)
    for i, (o, kk) in enumerate(RING13):   # 地面を走る土煙の輪
        a = i / 16 * 2 * math.pi; r = 30 + 260 * e
        keyp(o, f, loc=(r * math.cos(a), 25 + r * math.sin(a), 6) if e > 0 else (0, 0, -1e5), scale=15 + 25 * e); key_v(kk, .003 * (e > 0) * (1 - .6 * e), f)
    hit = clamp(1 - abs(u - FALL1) / .12)
    c = Vector((-150, -55, 5)) + Vector((10 * u, 5 * u, 0))
    cam.look(tuple(c + shake(f, 5.0 * hit + .6 * e, 7)), tuple(Vector((0, 12, 22 - 12 * k))), 24)


def s_l14():
    """結果：上空から、倒れた怪獣と丘の 3 万人"""
    base(28, 150, (.86, .84, .82), .9); world("hill"); scorch()
def a_l14(u, t, f):
    mpose(root_rot=(-(math.pi / 2 - .12), 0, 0), root_loc=(0, 4, 0), head=(-.1, 0, .2), jaw=-.3, lid=.05)
    cam.look(tuple(Vector((180, -230, 190)) + Vector((-25 * u, 10 * u, -10 * u))), (0, -40, 5), 30)


def s_l15():
    base(28, 150, (.86, .84, .82), .9); world("hill"); scorch()
def a_l15(u, t, f):
    op = ease(cut(.35, .7, u))
    mpose(root_rot=(-(math.pi / 2 - .12), 0, 0), root_loc=(0, 4, 0), head=(-.1, 0, .2), jaw=-.3, lid=.05 + .95 * op)
    bpy.context.view_layer.update(); eye = MON["lids"][1].matrix_world.translation
    cam.look(tuple(eye + Vector((22, -10, 9))), tuple(eye + Vector((0, 0, -1))), 38)   # 顔の横から、目が開く


NAMES = [s["id"] for s in PLAN["shots"]]


def _wrap(a):
    def w(u, t, f):
        if f % 20 == 0:
            log("anim frame", f)
        a(u, t, f)
        dc = os.environ.get("MONCAM")   # 確認用：怪獣を横（side）・正面（front）・斜め（q）から
        if dc:
            off = {"side": Vector((140, 0, 0)), "front": Vector((0, -140, 0)), "q": Vector((95, -100, 0))}[dc]
            cam.look(tuple(Vector((0, 0, 26)) + off + (Vector((0, 0, 30)) if dc == "front" else Vector())), (0, 0, 24), 32)
        for o in MON_ANIM:
            o.keyframe_insert("scale", frame=f + 1)
    return w


SHOTS = {k: (globals()["s_" + k], _wrap(globals()["a_" + k])) for k in NAMES}
anim = [cam.o] + MON_ANIM
K.render_shots(HERE, SHOTS, NAMES, O, anim)
