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


def hill_points(n, seed=2):
    rnd = random.Random(seed); pts = []
    while len(pts) < n:
        a = rnd.uniform(0, 2 * math.pi); r = HILL_R * math.sqrt(rnd.random()) * .98
        pts.append((HILL.x + math.cos(a) * r, HILL.y + math.sin(a) * r, HILL_H))
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
        ar = mpart(f"m_arm{sx}", [((sx * 7.2, -2.5, 30.5), 2.0, E, (1, 1, 1.5)), ((sx * 7.6, -4.6, 26.8), 1.6, E, (1, 1.6, .9)), ((sx * 7.6, -6.6, 25.6), 1.1, E, (1.2, 1.2, .6))],
                   (sx * 6.5, -1.5, 32), torso, .3)
        arms.append(ar)
    sp = mat("m_spike", (.05, .055, .05), .45)
    pts = []
    for i in range(10):
        for sx in ((0,) if i % 2 == 0 else (-1, 1)):
            pts.append((sx * 1.3, 6.5 + .9 * i, 37 - 2.4 * i, 4.6 - .22 * i, .55))
    pts += [(0, 9 + 2.4 * i, 17.5 - 1.05 * i ** 1.05, 3.6 - .2 * i, .9) for i in range(13)]
    spikes(torso, pts, sp)
    gm = emat("m_glow", (.3, .08, .02), .5, (1.0, .35, .05), 0.0, haze=False)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=2.4); me = bpy.data.meshes.new("glow"); bm.to_mesh(me); bm.free(); me.materials.append(gm)
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
def fire_mat():
    m = bpy.data.materials.new("fire"); m.use_nodes = True; t = m.node_tree; L = t.links
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 6
    L.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (1.0, .25, .02, 1); ramp.color_ramp.elements[1].color = (1.0, .85, .4, 1)
    L.new(nz.outputs["Fac"], ramp.inputs[0])
    em = t.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 6.0; L.new(ramp.outputs[0], em.inputs["Color"])
    tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader")
    alpha = t.nodes.new("ShaderNodeMapRange"); alpha.inputs[1].default_value = .35; alpha.inputs[2].default_value = .7; L.new(nz.outputs["Fac"], alpha.inputs[0])
    L.new(alpha.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    return m, em.inputs["Strength"]


def fire_cone(length=160., r1=1.5, r2=28.):
    bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=r1, radius2=r2, depth=length)
    bmesh.ops.translate(bm, vec=(0, 0, length / 2), verts=r_["verts"])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    me = bpy.data.meshes.new("fire"); bm.to_mesh(me); bm.free()
    m, k = fire_mat(); me.materials.append(m)
    o = link(bpy.data.objects.new("fire", me)); o.rotation_mode = "QUATERNION"
    return o, k


def aim_fire(o, origin, d, f, on=True, scale=1.0):
    o.location = origin; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d)
    o.scale = (scale, scale, scale) if on else (.001, .001, .001)
    o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_quaternion", frame=f + 1); o.keyframe_insert("scale", frame=f + 1)


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


# ---------------------------------------------------------------- 場面の土台
def base(sun_el=32, sun_rot=135, haze_col=(.78, .84, .9), haze_k=.9, d0=900., d1=14000., energy=9.0, blur=False):
    sky.set(0, sun_el, sun_rot, energy); set_haze(haze_col, haze_k, d0, d1); sc.render.use_motion_blur = blur


def scorch():
    m = emat("scorch", (.03, .028, .025), .9)
    tv, tf = _template("ico"); rnd = random.Random(4); xf = []
    for i in range(140):
        a = rnd.uniform(math.radians(200), math.radians(250)); r = rnd.uniform(40, 170)
        x, y = math.cos(a) * r, math.sin(a) * r
        xf.append((x, y, hill_z(x, y) - .5, rnd.uniform(6, 14), rnd.uniform(6, 14), .8, 0, 0, 0))
    instances("scorch", tv, tf, xf, [m])


def world(people="plain", n=50000):
    env_clear(); terrain()
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
    cam.look(tuple(Vector((-150, -150, 8)) + Vector((10 * u, 10 * u, 0))), (0, 0, 28), 26)


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
    base(22, 140, (.92, .8, .7), .9); world("plain")
    global FIRE4, FIRE4K, SMOKE4, SMOKE4K
    FIRE4, FIRE4K = fire_cone(); SMOKE4, SMOKE4K = puff("smoke4", (0, 0, -1e5), 80, (.25, .22, .2), .01)
def a_l04(u, t, f):
    turn = ease(cut(0, .25, u)); fire = cut(.28, .85, u)
    mpose(-.55 * turn, head=(.25 * turn, 0, -.15 * turn), jaw=-.5 * (fire > 0) * (1 - cut(.85, 1, u)), breathe=-.5 * fire, lid=1.0)
    org, d = mouth_world(); sweep = -.35 + .7 * fire
    d = (Matrix.Rotation(sweep, 3, "Z") @ d).normalized()
    aim_fire(FIRE4, org, d, f, on=fire > 0 and u < .9, scale=.4 + .6 * min(1, fire * 4)); key_v(FIRE4K, 6.0, f)
    gp = org + d * 150; keyp(SMOKE4, f, loc=tuple(Vector((gp.x, gp.y, 25))) if fire > .1 else (0, 0, -1e5), scale=60 + 60 * fire); key_v(SMOKE4K, .012 * (fire > .1), f)
    cam.look(tuple(Vector((170, -110, 35)) + Vector((-10 * u, 0, 0)) + shake(f, .8 * (fire > 0), 4)), (-20, -60, 22), 24)


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


def s_l08():
    base(26, 150, (.88, .84, .8), .9); world("hill"); scorch()
    global SPIN
    SPIN = []   # 手前の選手：回転して投げる
    rnd = random.Random(8)
    for i in range(36):
        x = HILL.x + rnd.uniform(-60, 60); y = HILL.y + HILL_R - rnd.uniform(2, 30)
        root = link(bpy.data.objects.new(f"sp{i}", None)); root.location = (x, y, HILL_H); root.rotation_mode = "XYZ"
        bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.24, radius2=.2, depth=1.4); bmesh.ops.translate(bm, vec=(0, 0, .7), verts=r_["verts"])
        s_ = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=.13); bmesh.ops.translate(bm, vec=(0, 0, 1.6), verts=s_["verts"])
        a_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.012, radius2=.012, depth=1.2); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=a_["verts"]); bmesh.ops.translate(bm, vec=(.75, 0, 1.15), verts=a_["verts"])
        h_ = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=.11); bmesh.ops.translate(bm, vec=(1.45, 0, 1.1), verts=h_["verts"])
        me = bpy.data.meshes.new(f"spm{i}"); bm.to_mesh(me); bm.free(); me.materials.append(mat(f"pp{i % 5}", (.85, .85, .82), .7))
        o = link(bpy.data.objects.new(f"spo{i}", me)); o.parent = root; SPIN.append((root, rnd.uniform(0, 6.28)))
def a_l08(u, t, f):
    mpose(0.0, head=(-.25, 0, 0), jaw=-.05, breathe=1.0, lid=1.0); key_v(esock(MON["glow"]), 25 + 10 * u, f)
    for root, ph in SPIN:   # 3 回転して離す（スロー）
        keyp(root, f, rot=(0, 0, ph + 2 * math.pi * 3 * ease(cut(0, .8, u))))
    c = HILL + Vector((-20, HILL_R - 45, HILL_H + 3)); cam.look(tuple(c), tuple(HEAD_POS + Vector((0, 0, -2))), 24)


def s_l09():
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill"); scorch()
    global HM9, ORG9
    HM9 = hammer_objs(1500, 11); rnd = random.Random(9); pts = hill_points(40000, 4)
    ORG9 = [Vector(pts[rnd.randrange(len(pts))]) + Vector((0, 0, 1.5)) for _ in HM9]
def a_l09(u, t, f):
    mpose(0.0, head=(-.25, 0, 0), jaw=-.05, breathe=1.0, lid=1.0); key_v(esock(MON["glow"]), 35, f)
    throw_set(HM9, ORG9, lambda i: HEAD_POS + Vector((random.Random(i).uniform(-3, 3), random.Random(i + 1).uniform(-2, 2), random.Random(i + 2).uniform(-2, 2))), 0, 1.0, u, f, 24.0)
    cam.look(tuple(Vector((90, -60, 55)) + Vector((-6 * u, 0, 0))), tuple(HEAD_POS.lerp(HILL + Vector((0, 0, HILL_H)), .45)), 30)


def s_l10():
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill"); scorch()
    global HM10, DUST10, DUST10K
    HM10 = hammer_objs(500, 12); DUST10, DUST10K = puff("hitdust", (0, 0, -1e5), 6, (.5, .45, .4), .02)
def a_l10(u, t, f):
    hit = .12; e = max(0., t - hit)
    jolt = (1 - math.exp(-e * 6)) * math.exp(-e * .8) if t > hit else 0
    mpose(0.0, head=(-.25 - .45 * jolt, 0, .12 * jolt), torso=(-.08 * jolt, 0, 0), jaw=-.05 - .3 * jolt, breathe=1.0 - jolt, lid=1.0)
    key_v(esock(MON["glow"]), 35 * (1 - min(1, e * 2)), f)
    for i, o in enumerate(HM10):
        r = random.Random(i); tgt = HEAD_POS + Vector((r.uniform(-3, 3), r.uniform(-2, 2), r.uniform(-2, 2)))
        if t < hit:
            p = tgt + Vector((0, -40 * (hit - t) / hit, 0))
        else:
            p = tgt + Vector((r.uniform(-6, 6) * e, -r.uniform(3, 9) * e, r.uniform(2, 6) * e - 4.9 * e * e))
        keyp(o, f, loc=tuple(p))
    keyp(DUST10, f, loc=tuple(HEAD_POS + Vector((0, -5, 0))) if t > hit else (0, 0, -1e5), scale=6 + 25 * min(1, e)); key_v(DUST10K, .02 * max(0, 1 - e), f)
    cam.look(tuple(Vector((28, -32, 44)) + shake(f, 1.2 * max(0, 1 - e * 2), 5)), tuple(HEAD_POS), 34)


def s_l11():
    base(26, 150, (.88, .84, .8), .9); world("hill"); scorch()
    global FIRE11, FIRE11K
    FIRE11, FIRE11K = fire_cone(120, 1.2, 18)
def a_l11(u, t, f):
    w = math.sin(t * 2.2) * (.06 + .05 * u)
    mpose(0.0, torso=(-.05 + w * .5, w, 0), head=(-.55 + .3 * math.sin(t * 1.7), .2 * w, .3 * math.sin(t * 1.3)), jaw=-.45, breathe=.3, lid=.6 + .4 * math.cos(t * 3))
    org, d = mouth_world(); up = (d + Vector((0, 0, 2.2))).normalized()
    fire = cut(.35, .9, u)
    aim_fire(FIRE11, org, up, f, on=fire > 0, scale=.5 + .5 * fire); key_v(FIRE11K, 4.0, f)
    cam.look(tuple(Vector((140, -100, 30))), (0, -5, 28), 26)


def s_l12():
    base(26, 150, (.88, .84, .8), .9, blur=True); world("hill"); scorch()
    global DUST12, DUST12K
    DUST12, DUST12K = puff("falldust", (0, 0, -1e5), 40, (.55, .5, .45), .004)
def a_l12(u, t, f):
    k = ease(cut(.05, .55, u)) ** 1.7; tip = (math.pi / 2 - .12) * k   # かかとを支点にあお向けに倒れる
    mpose(root_rot=(-tip, 0, 0), root_loc=(0, 4 * k, 0), head=(-.4 + .3 * k, 0, .2), jaw=-.3, lid=.3)
    e = cut(.5, 1, u)
    keyp(DUST12, f, loc=(0, 25, 12) if e > 0 else (0, 0, -1e5), scale=30 + 90 * e); key_v(DUST12K, .006 * (e > 0) * (1 - .5 * e), f)
    cam.look(tuple(Vector((-200, -60, 25)) + shake(f, 2.5 * clamp(1 - abs(u - .55) / .1), 7)), (0, 15, 15), 24)


def s_l13():
    base(28, 150, (.86, .84, .82), .9); world("hill"); scorch()
def a_l13(u, t, f):
    mpose(root_rot=(-(math.pi / 2 - .12), 0, 0), root_loc=(0, 4, 0), head=(-.1, 0, .2), jaw=-.3, lid=.05)
    cam.look(tuple(Vector((150, -330, 160)) + Vector((-20 * u, 0, -10 * u))), (0, -60, 10), 28)


def s_l14():
    base(28, 150, (.86, .84, .82), .9); world("hill"); scorch()
def a_l14(u, t, f):
    op = ease(cut(.35, .7, u))
    mpose(root_rot=(-(math.pi / 2 - .12), 0, 0), root_loc=(0, 4, 0), head=(-.1, 0, .2), jaw=-.3, lid=.05 + .95 * op)
    bpy.context.view_layer.update(); eye = MON["lids"][1].matrix_world.translation
    cam.look(tuple(eye + Vector((10, -14, 6))), tuple(eye), 40)


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
