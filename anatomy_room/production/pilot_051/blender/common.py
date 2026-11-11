"""pilot_050 の 3D の共通部品（pilot_049 の scene.py から。霧・材質・群れのメッシュ・体積・メタボールの部品）。"""
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
sc.cycles.volume_step_rate = 6.0; sc.cycles.volume_max_steps = 128   # 品質のため adaptive_threshold はゆるめない（blkit の .03）
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


MONC = bpy.data.collections.new("actors"); sc.collection.children.link(MONC)


def mlink(o):
    MONC.objects.link(o); return o


def smooth(a, b, v):
    u = np.clip((v - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)


def ch(a, b, r0, r1, n):
    """a → b に並べた球（メタボールの手足）"""
    a = np.array(a, float); b = np.array(b, float)
    n = max(n, int(math.ceil(np.linalg.norm(b - a) / (.42 * min(r0, r1)))) + 1)      # 間が半径の半分より広いと数珠になる
    return [(tuple(a + (b - a) * i / (n - 1)), r0 + (r1 - r0) * i / (n - 1), "BALL", None) for i in range(n)]


def mpart(name, elems, pivot, parent=None, res=.08, m=None, paint=None, subd=1):
    """メタボール → メッシュ。pivot を原点にずらして親につなぐ。paint(mesh)：変換した直後（置いた姿勢の座標）に頂点の色を塗る"""
    mb = bpy.data.metaballs.new("mb_" + name); mb.resolution = res; mb.render_resolution = res; mb.threshold = .05
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
    if paint:
        paint(o.data)
    for v in o.data.vertices:
        v.co -= pv
    o.location = pv if parent is None else pv - Vector(parent["pivot"]); o["pivot"] = tuple(pv)
    if parent is not None:
        o.parent = parent
    for p_ in o.data.polygons:
        p_.use_smooth = True
    if m is not None:
        o.data.materials.append(m)
    if subd:
        sd = o.modifiers.new("sd", "SUBSURF"); sd.levels = subd; sd.render_levels = subd
    o.rotation_mode = "XYZ"
    return o


def child_mesh(name, bm, m, parent, smooth_=True):
    """置いた姿勢の座標で作ったメッシュを、parent（mpart の部品）の子にする"""
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for mm in (m if isinstance(m, (list, tuple)) else [m]):
        me.materials.append(mm)
    for p_ in me.polygons:
        p_.use_smooth = smooth_
    o = mlink(bpy.data.objects.new(name, me)); o.parent = parent; o.location = -Vector(parent["pivot"]); return o


def wpos(part, p):
    """部品の、置いた姿勢での点 p の、いまの世界座標（先に view_layer.update()）"""
    return part.matrix_world @ (Vector(p) - Vector(part["pivot"]))


TEX = os.path.join(HERE, "tex")


def img_mat(name, rough=.7, emit=.0):
    """blender/tex/<name>.png を貼る材質（make_tex.py）"""
    if "img_" + name in MATS:
        return MATS["img_" + name]
    m = bpy.data.materials.new("img_" + name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    tx = t.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(TEX, name + ".png")); tx.extension = "EXTEND"
    t.links.new(tx.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit:
        t.links.new(tx.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    add_haze(m, 150., 4000., .8); MATS["img_" + name] = m; return m


def quad(name, P, m, flip=False):
    """4 点（左下・右下・右上・左上）の板。UV は 0〜1。flip：左右を逆に貼る"""
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in P]; f = bm.faces.new(vs); uv = bm.loops.layers.uv.new("UVMap")
    for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = (1 - u if flip else u, v)
    return bm
