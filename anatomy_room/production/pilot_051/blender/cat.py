"""pilot_051 の猫（本物の寸法、m。前が +Y、上が Z、原点＝胴の真下の地面）。
メタボールの部品をつなぎ、毛は numpy で表面から生やした動かない曲線（Curves）。毛の色は曲線ごとの属性（mel・red）で、
柄（三毛・茶トラ・黒・白・サバトラ・ハチワレ）は猫の「置いた姿勢の座標」から計算するので、動いても柄はずれない。

使い方：
    import cat
    c = cat.build_cat("c1", "mike", seed=1)          # 部品の dict
    cat.cpose(c, pos=(0, 0), heading=0, mode="pull", t=1.2, ph=.3)
    ring = cat.harness(c, (.75, .08, .06))          # 胴輪。ring() で綱をつなぐ点（世界座標、先に view_layer.update()）
    cat.CANIM                                        # 動かす部品の一覧（全部の猫）
"""
from common import *
from mathutils.bvhtree import BVHTree
import zlib
import time as _time

E, B = "ELLIPSOID", "BALL"
DBG = []            # 足が届かなかった量（調整用）
CANIM = []          # 動かす部品（location・rotation_euler・scale にキーを打つ）
CATS = {}
HAIR_DENS = 1.0     # 毛の本数の倍率（群れのショットでは下げる：build_cat(..., dens=.5)）
_M = {}


# ---------------------------------------------------------------- 雑音（numpy、値ノイズ）
def _hash(ix, iy, iz, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (iz * 83492791) ^ (seed * 2654435761 + 977)
    h = h & 0xffffffff
    h = ((h ^ (h >> 15)) * 2246822519) & 0xffffffff
    h = ((h ^ (h >> 13)) * 3266489917) & 0xffffffff
    h = h ^ (h >> 16)
    return (h & 0xffff) / 65535.0


def vnoise(P, scale, seed=0):
    Q = np.asarray(P, float) * scale; i0 = np.floor(Q).astype(np.int64); f = Q - i0; u = f * f * (3 - 2 * f)
    acc = np.zeros(len(Q))
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                acc += wx * wy * wz * _hash(i0[:, 0] + dx, i0[:, 1] + dy, i0[:, 2] + dz, seed)
    return acc


def fbm(P, scale, seed=0, octv=4):
    s, a, t = 0., 1., 0.
    for o in range(octv):
        s += a * vnoise(P, scale * 2 ** o, seed + 17 * o); t += a; a *= .5
    return s / t


def sm(a, b, v):
    u = np.clip((np.asarray(v, float) - a) / (b - a), 0, 1); return u * u * (3 - 2 * u)


# ---------------------------------------------------------------- 毛色（melanin・redness と、毛の下の肌の色）
WHITE = (.035, .3, (.62, .6, .57))
BLACK = (.985, .12, (.008, .007, .007))
ORANGE = (.24, 1.0, (.55, .24, .07))
ORANGE_D = (.55, 1.0, (.24, .075, .02))
CREAM = (.09, .85, (.66, .5, .34))
GREYB = (.4, .2, (.2, .18, .16))
GREY_L = (.16, .25, (.45, .42, .38))
STRIPE_K = (.93, .2, (.02, .018, .016))


def _mix(base, other, k):
    k = np.asarray(k, float)
    mel = base[0] + (other[0] - base[0]) * k; red = base[1] + (other[1] - base[1]) * k
    rgb = base[2] + (other[2] - base[2]) * k[:, None]
    return mel, red, rgb


def _const(t, n):
    return (np.full(n, t[0]), np.full(n, t[1]), np.tile(np.array(t[2], float), (n, 1)))


def _mixc(cur, t, k):
    return _mix(cur, (t[0], t[1], np.array(t[2], float)), k)


def _stripe_coord(kind, P):
    x, y, z = P.T
    if kind in ("leg", "paw"):
        return z, .03
    if kind == "tail":
        return -y + .3 * z, .036
    if kind in ("head", "lid", "jaw"):
        fore = sm(.312, .322, z)
        return (1 - fore) * (z * 1.0 + .25 * np.abs(x)) + fore * np.abs(x) * 1.6, .011
    return y + .35 * (z - .2) + .2 * np.abs(x), .05


def coat_eval(coat, P, kind, seed=1):
    """P：置いた姿勢の点（N×3）。kind：部品の種類。→ (mel, red, rgb)"""
    P = np.asarray(P, float); n = len(P); x, y, z = P.T; ax = np.abs(x)
    off = np.array([seed * 1.37, seed * 2.11, seed * .73])
    body = kind in ("body", "neck")
    belly = sm(.155, .135, z) if body else np.zeros(n)
    if kind in ("leg", "paw"):
        belly = np.zeros(n)
    muzzle = np.zeros(n)
    if kind in ("head", "jaw", "lid"):
        muzzle = sm(.297, .289, z) * sm(.272, .285, y)
        if kind == "jaw":
            muzzle = np.ones(n)
    if coat == "shiro":
        return _const(WHITE, n)
    if coat == "kuro":
        cur = _const(BLACK, n)
        k = fbm(P + off, 30, seed) ; cur = _mixc(cur, (.93, .3, (.012, .01, .009)), sm(.45, .7, k) * .6)   # 少しだけ赤茶けた毛
        return cur
    if coat == "hachiware":
        cur = _const(BLACK, n); w = np.zeros(n)
        if body:
            w = np.maximum(sm(.163, .148, z), sm(.205, .19, z) * sm(.125, .16, y))
        if kind in ("head", "lid"):
            th = np.maximum(.296, .334 - 1.5 * ax)
            w = sm(th + .003, th - .003, z) * sm(.262, .278, y)
        if kind == "jaw":
            w = np.ones(n)
        if kind in ("leg", "paw"):
            w = np.where(y > 0, sm(.11, .09, z), sm(.065, .05, z))
        w = np.clip(w + .0 * fbm(P + off, 40, seed), 0, 1)
        return _mixc(cur, WHITE, w)
    if coat == "mike":
        cur = _const(WHITE, n)
        up = np.ones(n)
        if body:
            up = sm(.17, .2, z) * (1 - sm(.13, .17, y) * sm(.24, .2, z))
        if kind in ("leg", "paw"):
            up = sm(.13, .16, z) * (y < 0)
        if kind in ("head", "lid"):
            up = sm(.302, .312, z) * (1 - sm(.012, .006, ax) * sm(.33, .3, z))
        if kind == "jaw":
            up = np.zeros(n)
        if kind == "tail":
            up = np.ones(n)
        no = fbm(P * np.array([1, .8, 1]) + off, 9, seed + 3) + .12 * fbm(P + off, 60, seed + 9)
        nk = fbm(P * np.array([1, .8, 1]) + off * 1.7, 8, seed + 7) + .12 * fbm(P + off, 55, seed + 11)
        if kind == "tail":
            no = no + .15
        mo = sm(.53, .56, no) * up; mk = sm(.56, .59, nk) * up
        cur = _mixc(cur, ORANGE, mo)
        cur = _mixc(cur, BLACK, mk * (1 - .7 * mo))
        return cur
    if coat in ("chatora", "sabatora"):
        base, dark, light = (ORANGE, ORANGE_D, CREAM) if coat == "chatora" else (GREYB, STRIPE_K, GREY_L)
        cur = _const(base, n)
        sv, per = _stripe_coord(kind, P)
        wob = fbm(P + off, 22, seed + 5); brk = fbm(P * np.array([1, 2.5, 1]) + off * 2, 30, seed + 8)
        s = np.sin(2 * np.pi * sv / per + 7.0 * (wob - .5))
        st = sm(.2, .7, s) * sm(.3, .5, brk)
        if body:
            st = st * (1 - belly) * (.9 - .2 * sm(.2, .15, z))
            spine = sm(.012, .004, ax) * sm(.23, .25, z)
            st = np.maximum(st, spine)
        if kind in ("leg", "paw"):
            st = st * sm(.02, .05, z) * .85
        if kind in ("head", "lid"):
            st = st * (1 - muzzle) * (sm(.31, .316, z) + (1 - sm(.31, .316, z)) * sm(.016, .026, ax)) * .9
        if kind == "tail":
            st = np.maximum(st, sm(-.43, -.46, y))
        if kind == "jaw":
            st = st * 0
        if kind == "ear":
            st = st * 0 + .35
        cur = _mixc(cur, dark, st)
        lt = np.maximum(belly, muzzle * .9)
        if kind == "paw":
            lt = np.maximum(lt, .6 * np.ones(n)) if coat == "sabatora" else lt
        cur = _mixc(cur, light, lt)
        return cur
    return _const(WHITE, n)


# ---------------------------------------------------------------- 材質
def _attr(t, name):
    a = t.nodes.new("ShaderNodeAttribute"); a.attribute_name = name; return a


def hair_mat():
    if "hair" in _M:
        return _M["hair"]
    m = bpy.data.materials.new("cat_hair"); m.use_nodes = True; nt = m.node_tree
    for nd in list(nt.nodes):
        nt.nodes.remove(nd)
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled"); out = nt.nodes.new("ShaderNodeOutputMaterial")
    hb.parametrization = "MELANIN"
    nt.links.new(_attr(nt, "mel").outputs["Fac"], hb.inputs["Melanin"]); nt.links.new(_attr(nt, "red").outputs["Fac"], hb.inputs["Melanin Redness"])
    hb.inputs["Roughness"].default_value = .38; hb.inputs["Radial Roughness"].default_value = .55
    hb.inputs["Coat"].default_value = .1
    hb.inputs["Random Color"].default_value = .12; hb.inputs["Random Roughness"].default_value = .25
    nt.links.new(hb.outputs[0], out.inputs[0])
    add_haze(m, 150., 4000., .8); _M["hair"] = m; return m


def skin_mat():
    if "skin" in _M:
        return _M["skin"]
    m = bpy.data.materials.new("cat_skin"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    t.links.new(_attr(t, "Col").outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .85; b.inputs["Specular IOR Level"].default_value = .12
    add_haze(m, 150., 4000., .8); _M["skin"] = m; return m


def wet(name, col, rough=.35, bump=.25, scale=2500., coat=.4):
    key = "wet_" + name
    if key in _M:
        return _M[key]
    m = bpy.data.materials.new("cat_" + name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if bump:
        nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 3
        bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = .0003
        t.links.new(nz.outputs["Fac"], bp.inputs["Height"]); t.links.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = .15
    b.inputs["Subsurface Weight"].default_value = .15; b.inputs["Subsurface Radius"].default_value = (.004, .001, .0008)
    add_haze(m, 150., 4000., .8); _M[key] = m; return m


def eye_mat(name, iris, iris2, r_iris):
    """目：物体の座標（+Y が視線）で、虹彩（放射状のすじ・縁の暗い輪）と縦長の瞳孔。角膜のつやは Coat"""
    key = "eye_" + name
    if key in _M:
        return _M[key]
    m = bpy.data.materials.new("cat_eye_" + name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links; N = t.nodes
    tc = N.new("ShaderNodeTexCoord"); sp = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0])

    def mth(op, a, b_=None, v=None):
        n_ = N.new("ShaderNodeMath"); n_.operation = op
        for i, s in enumerate((a, b_)):
            if s is None:
                continue
            if isinstance(s, (int, float)):
                n_.inputs[i].default_value = s
            else:
                L.new(s, n_.inputs[i])
        return n_.outputs[0]
    x, y, z = sp.outputs["X"], sp.outputs["Y"], sp.outputs["Z"]
    r = mth("SQRT", mth("ADD", mth("MULTIPLY", x, x), mth("MULTIPLY", z, z)))
    # 瞳孔：縦長の楕円（PW：幅、昼は細い）
    pw = N.new("ShaderNodeValue"); pw.outputs[0].default_value = .0012; pw.label = "pupil_w"
    ex = mth("DIVIDE", x, pw.outputs[0]); ez = mth("DIVIDE", z, .0071)
    e = mth("ADD", mth("MULTIPLY", ex, ex), mth("MULTIPLY", ez, ez))
    pup = N.new("ShaderNodeMapRange"); pup.inputs[1].default_value = .8; pup.inputs[2].default_value = 1.15; pup.inputs[3].default_value = 1.0; pup.inputs[4].default_value = 0.0
    L.new(e, pup.inputs[0])
    iris_m = N.new("ShaderNodeMapRange"); iris_m.inputs[1].default_value = r_iris - .0004; iris_m.inputs[2].default_value = r_iris + .0002
    iris_m.inputs[3].default_value = 1.0; iris_m.inputs[4].default_value = 0.0; L.new(r, iris_m.inputs[0])
    front = N.new("ShaderNodeMapRange"); front.inputs[1].default_value = .0; front.inputs[2].default_value = .003; L.new(y, front.inputs[0])
    irisk = mth("MULTIPLY", iris_m.outputs[0], front.outputs[0])
    # 虹彩の色：内側と外側、放射状のすじ
    rad = N.new("ShaderNodeMapRange"); rad.inputs[1].default_value = .0015; rad.inputs[2].default_value = r_iris; L.new(r, rad.inputs[0])
    cm = N.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(rad.outputs[0], cm.inputs[0]); cm.inputs[6].default_value = (*iris2, 1); cm.inputs[7].default_value = (*iris, 1)
    cxz = N.new("ShaderNodeCombineXYZ"); L.new(mth("DIVIDE", x, mth("ADD", r, .0001)), cxz.inputs[0]); L.new(mth("DIVIDE", z, mth("ADD", r, .0001)), cxz.inputs[2])
    L.new(mth("MULTIPLY", r, 300.), cxz.inputs[1])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 7.0; nz.inputs["Detail"].default_value = 6; L.new(cxz.outputs[0], nz.inputs["Vector"])
    st = N.new("ShaderNodeMapRange"); st.inputs[1].default_value = .3; st.inputs[2].default_value = .7; st.inputs[3].default_value = .65; st.inputs[4].default_value = 1.2; L.new(nz.outputs["Fac"], st.inputs[0])
    limb = N.new("ShaderNodeMapRange"); limb.inputs[1].default_value = r_iris - .0016; limb.inputs[2].default_value = r_iris; limb.inputs[3].default_value = 1.0; limb.inputs[4].default_value = .3
    L.new(r, limb.inputs[0])
    k1 = mth("MULTIPLY", st.outputs[0], limb.outputs[0])
    cmul = N.new("ShaderNodeMix"); cmul.data_type = "RGBA"; cmul.blend_type = "MULTIPLY"; cmul.inputs[0].default_value = 1.0
    L.new(cm.outputs[2], cmul.inputs[6]); cxx = N.new("ShaderNodeCombineXYZ"); L.new(k1, cxx.inputs[0]); L.new(k1, cxx.inputs[1]); L.new(k1, cxx.inputs[2]); L.new(cxx.outputs[0], cmul.inputs[7])
    sclera = N.new("ShaderNodeMix"); sclera.data_type = "RGBA"; L.new(irisk, sclera.inputs[0]); sclera.inputs[6].default_value = (.32, .27, .2, 1); L.new(cmul.outputs[2], sclera.inputs[7])
    pm = N.new("ShaderNodeMix"); pm.data_type = "RGBA"; L.new(mth("MULTIPLY", pup.outputs[0], irisk), pm.inputs[0]); L.new(sclera.outputs[2], pm.inputs[6]); pm.inputs[7].default_value = (.002, .002, .002, 1)
    L.new(pm.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = .35; b.inputs["Specular IOR Level"].default_value = .2
    b.inputs["Coat Weight"].default_value = 1.0; b.inputs["Coat Roughness"].default_value = .015; b.inputs["Coat IOR"].default_value = 1.38
    add_haze(m, 150., 4000., .8); _M[key] = m; m["pupil"] = pw.name; return m


# ---------------------------------------------------------------- 部品
def _paint(me, P, coat, kind, seed, override=None, Nn=None):
    mel, red, rgb = coat_eval(coat, P, kind, seed)
    rgb = rgb * .85
    if override is not None:
        rgb = override(P, rgb, Nn)
    n = len(P); ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", np.concatenate([rgb, np.ones((n, 1))], 1).ravel().astype(np.float32))


def _rest_verts(o):
    me = o.data; n = len(me.vertices); V = np.empty(n * 3); me.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
    Nn = np.empty(n * 3); me.vertex_normals.foreach_get("vector", Nn); Nn = Nn.reshape(-1, 3)
    return V, Nn, V + np.array(o["pivot"])


def part(c, nm, elems, pivot, parent, res=.004, kind="body", skin_override=None):
    o = mpart(c["name"] + "_" + nm, elems, pivot, parent, res, skin_mat(), None, 0)
    V, Nn, P = _rest_verts(o); _paint(o.data, P, c["coat"], kind, c["seed"], skin_override, Nn)
    o["kind"] = kind; c["parts"][nm] = o; return o


def mesh_part(c, nm, bm, pivot, parent, m, kind="body", paint=True, skin_override=None):
    """置いた姿勢の座標の bmesh を、pivot を原点にして parent の子に"""
    bmesh.ops.translate(bm, vec=-Vector(pivot), verts=bm.verts)
    me = bpy.data.meshes.new(c["name"] + "_" + nm); bm.to_mesh(me); bm.free()
    for mm in (m if isinstance(m, (list, tuple)) else [m]):
        me.materials.append(mm)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = mlink(bpy.data.objects.new(c["name"] + "_" + nm, me)); o["pivot"] = tuple(pivot); o.rotation_mode = "XYZ"
    if parent is not None:
        o.parent = parent; o.location = Vector(pivot) - Vector(parent["pivot"])
    else:
        o.location = pivot
    if paint:
        V, Nn, P = _rest_verts(o); _paint(me, P, c["coat"], kind, c["seed"], skin_override, Nn)
    o["kind"] = kind; c["parts"][nm] = o; return o


def _sphere_bm(center, r, scale=(1, 1, 1), seg=24, rot=None):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=1.0)
    bmesh.ops.scale(bm, vec=Vector(scale) * r, verts=bm.verts)
    if rot is not None:
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts); return bm


def _cr(pts, n):
    """Catmull-Rom で点列（K×D）をなめらかに n 点に"""
    P = np.asarray(pts, float); P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]]); out = []
    seg = len(P) - 3
    for i in range(n):
        u = i / (n - 1) * seg; k = min(int(u), seg - 1); t = u - k; p0, p1, p2, p3 = P[k:k + 4]
        out.append(.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.array(out)


def loft(prof, nr=60, ns=40, cap=6, ex=2.2):
    """胴・首：prof＝[(y, z, 横の半幅, 上の高さ, 下の高さ)]（軸は yz 平面の折れ線）。両端は丸いふた。断面は超楕円（ex）"""
    Q = _cr(prof, nr); bm = bmesh.new(); rings = []
    C = np.stack([np.zeros(len(Q)), Q[:, 0], Q[:, 1]], 1)
    T = np.gradient(C, axis=0); T /= np.linalg.norm(T, axis=1, keepdims=True)

    def ring(c, t, hw, ht, hb):
        X = np.array([1., 0, 0]); U = np.cross(X, t); U /= np.linalg.norm(U); vs = []
        for j in range(ns):
            ph = 2 * math.pi * j / ns; sp, cp = math.sin(ph), math.cos(ph)
            sx_ = math.copysign(abs(sp) ** (2 / ex), sp); cz = math.copysign(abs(cp) ** (2 / ex), cp)
            vs.append(bm.verts.new(c + X * hw * sx_ + U * (ht if cz > 0 else hb) * cz))
        return vs
    # ふた（先端）：楕円体の形で縮める
    caps0 = []; caps1 = []
    for k in range(cap, 0, -1):
        a = k / cap * math.pi / 2; sc_ = math.cos(a); dl = math.sin(a)
        q = Q[0]; caps0.append((C[0] - T[0] * dl * min(q[2], q[3]) * .9, T[0], q[2] * sc_, q[3] * sc_, q[4] * sc_))
    for k in range(1, cap + 1):
        a = k / cap * math.pi / 2; sc_ = math.cos(a); dl = math.sin(a)
        q = Q[-1]; caps1.append((C[-1] + T[-1] * dl * min(q[2], q[3]) * .9, T[-1], q[2] * sc_, q[3] * sc_, q[4] * sc_))
    allr = caps0 + [(C[i], T[i], Q[i, 2], Q[i, 3], Q[i, 4]) for i in range(len(Q))] + caps1
    allr = [r for r in allr if r[2] > 1e-5]
    for r in allr:
        rings.append(ring(*r))
    p0 = bm.verts.new(allr[0][0] - allr[0][1] * .0015); p1 = bm.verts.new(allr[-1][0] + allr[-1][1] * .0015)
    for a_, b_ in zip(rings[:-1], rings[1:]):
        for j in range(ns):
            bm.faces.new((a_[j], a_[(j + 1) % ns], b_[(j + 1) % ns], b_[j]))
    for j in range(ns):
        bm.faces.new((p0, rings[0][(j + 1) % ns], rings[0][j])); bm.faces.new((p1, rings[-1][j], rings[-1][(j + 1) % ns]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.normal_update()
    if bm.calc_volume(signed=True) < 0:      # 法線を必ず外向きに（内向きだと毛が中に生える）
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return bm


def solid(c, nm, center, r, m, parent, scale=(1, 1, 1), seg=24, rot=None):
    """形の変わらない小物（肉球・鼻・歯）：置いた姿勢の座標で、parent の原点を基準に"""
    bm = _sphere_bm(center, r, scale, seg, rot)
    bmesh.ops.translate(bm, vec=-Vector(parent["pivot"]), verts=bm.verts)
    me = bpy.data.meshes.new(c["name"] + "_" + nm); bm.to_mesh(me); bm.free(); me.materials.append(m)
    for p_ in me.polygons:
        p_.use_smooth = True
    o = mlink(bpy.data.objects.new(c["name"] + "_" + nm, me)); o.parent = parent; return o


# ---------------------------------------------------------------- 毛
def grow_fur(c, o, lenfn, flow, th=(.95, 1.38), r0=.000055, dens=1.0, npts=5, kind=None, wave=.15, seed=0):
    """o の表面から毛を生やす。lenfn(P, N) → (長さ m, 密度 0〜1)。flow(P) → 毛の流れる向き（置いた姿勢の座標）。
    th：毛の根元と先の、法線からの角度（ラジアン、大きいほど寝る）"""
    me = o.data; me.calc_loop_triangles(); V, Nn, P = _rest_verts(o)
    nt = len(me.loop_triangles); T = np.empty(nt * 3, np.int64); me.loop_triangles.foreach_get("vertices", T); T = T.reshape(-1, 3)
    Lv, Dv = lenfn(P, Nn); Lv = np.clip(np.asarray(Lv, float), 0, None); Dv = np.clip(np.asarray(Dv, float), 0, 1)
    a, b_, c_ = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    area = .5 * np.linalg.norm(np.cross(b_ - a, c_ - a), axis=1)
    Lt = Lv[T].mean(1); Dt = Dv[T].mean(1)
    w = area * Dt * (.02 / np.maximum(Lt, .003)) ** .65 * (Lt > .0008)
    N = int(w.sum() * 1.6e6 * dens * HAIR_DENS * c["dens"])
    if N < 10:
        return None
    rng = np.random.default_rng(zlib.crc32((o.name + str(seed)).encode()))
    ti = rng.choice(nt, N, p=w / w.sum())
    u1 = rng.random(N); u2 = rng.random(N); s1 = np.sqrt(u1)
    bw = np.stack([1 - s1, s1 * (1 - u2), s1 * u2], 1)
    tri = T[ti]
    p = (V[tri] * bw[:, :, None]).sum(1); nrm = (Nn[tri] * bw[:, :, None]).sum(1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    L = (Lv[tri] * bw).sum(1) * rng.uniform(.75, 1.15, N)
    pr = p + np.array(o["pivot"])
    f = np.asarray(flow(pr), float)
    if f.ndim == 1:
        f = np.tile(f, (N, 1))
    # 流れの揺らぎ：空間的にまとまった向きの乱れ（毛の束・分け目）＋1 本ずつの乱れ
    sd = zlib.crc32(o.name.encode()) % 1000
    jit = np.stack([fbm(pr, 160, sd + k, 2) - .5 for k in range(3)], 1) * .9 + rng.normal(0, .12, (N, 3))
    f = f + jit
    tng = f - nrm * (f * nrm).sum(1, keepdims=True); tl = np.linalg.norm(tng, axis=1, keepdims=True)
    tng = np.where(tl > 1e-6, tng / np.maximum(tl, 1e-9), np.cross(nrm, np.array([1., 0, 0])))
    bit = np.cross(nrm, tng)
    th0 = th[0] + rng.normal(0, .12, N); th1 = th[1] + rng.normal(0, .08, N)
    wv = rng.normal(0, wave, N)
    pts = np.empty((N, npts, 3)); pts[:, 0] = p - nrm * .0004
    seg = L / (npts - 1)
    for j in range(1, npts):
        s = (j - .5) / (npts - 1); a_ = th0 + (th1 - th0) * s ** .8
        d = nrm * np.cos(a_)[:, None] + tng * np.sin(a_)[:, None] + bit * (wv * math.sin(math.pi * s))[:, None]
        d /= np.linalg.norm(d, axis=1, keepdims=True)
        pts[:, j] = pts[:, j - 1] + d * seg[:, None]
    cd = bpy.data.hair_curves.new(o.name + "_fur"); cd.add_curves([npts] * N)
    cd.position_data.foreach_set("vector", pts.reshape(-1).astype(np.float32))
    k = np.linspace(1, .12, npts); rr = (np.outer(r0 * rng.uniform(.8, 1.2, N), k)).reshape(-1)
    ra = cd.attributes.get("radius") or cd.attributes.new("radius", "FLOAT", "POINT"); ra.data.foreach_set("value", rr.astype(np.float32))
    mel, red, _ = coat_eval(c["coat"], pr, kind or o["kind"], c["seed"])
    mel = np.clip(mel + rng.normal(0, .015, N), 0, 1)
    cd.attributes.new("mel", "FLOAT", "CURVE").data.foreach_set("value", mel.astype(np.float32))
    cd.attributes.new("red", "FLOAT", "CURVE").data.foreach_set("value", red.astype(np.float32))
    cd.materials.append(hair_mat())
    cv = mlink(bpy.data.objects.new(o.name + "_fur", cd)); cv.parent = o
    c["fur"][o.name] = cv; c["nhair"] += N; return cv


def strands(c, nm, roots, dirs, lens, parent, r0=.00028, droop=.25, mel=.03, npts=8):
    """ひげ：根元（置いた姿勢の座標）・向き・長さ"""
    roots = np.asarray(roots, float); dirs = np.asarray(dirs, float); N = len(roots)
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    pts = np.empty((N, npts, 3))
    for j in range(npts):
        s = j / (npts - 1); d = dirs * s * lens[:, None]; d[:, 2] -= droop * (s * lens) ** 2 / np.maximum(lens, 1e-6) * 1.0
        pts[:, j] = roots + d
    pts -= np.array(parent["pivot"])
    cd = bpy.data.hair_curves.new(c["name"] + "_" + nm); cd.add_curves([npts] * N)
    cd.position_data.foreach_set("vector", pts.reshape(-1).astype(np.float32))
    k = np.linspace(1, .1, npts) ** 1.3; ra = cd.attributes.get("radius") or cd.attributes.new("radius", "FLOAT", "POINT")
    ra.data.foreach_set("value", np.tile(k * r0, N).astype(np.float32))
    cd.attributes.new("mel", "FLOAT", "CURVE").data.foreach_set("value", np.full(N, mel, np.float32))
    cd.attributes.new("red", "FLOAT", "CURVE").data.foreach_set("value", np.full(N, .2, np.float32))
    cd.materials.append(hair_mat())
    cv = mlink(bpy.data.objects.new(c["name"] + "_" + nm, cd)); cv.parent = parent; return cv


# ---------------------------------------------------------------- 寸法（置いた姿勢、m）
HEAD_OFF = (0, -.026, -.017)
HEAD_S = 1.14
SEAM = .02     # 胴（後ろ）と胸（前）の毛の受け持ちの境（y）
BODY_R = [(-.2, .2, .027, .03, .034), (-.185, .199, .042, .044, .048), (-.15, .195, .052, .052, .055), (-.09, .19, .05, .052, .054),
          (-.03, .186, .052, .054, .058), (.03, .185, .053, .057, .062), (.07, .186, .053, .058, .064)]
BODY_F = [(-.03, .186, .052, .054, .058), (.03, .185, .053, .057, .062), (.09, .188, .052, .06, .066), (.14, .196, .049, .057, .062), (.175, .193, .042, .05, .056), (.195, .186, .03, .038, .044)]
NECK = [(.15, .2, .047, .046, .048), (.18, .222, .045, .044, .047), (.205, .245, .041, .04, .042), (.222, .268, .035, .035, .036)]
HEAD_C = Vector((0, .257, .307))
EYE = Vector((.0178, .2895, .3085)); EYE_R = .0103; EYE_YAW = .2
NOSE = Vector((0, .3135, .2965))
FL = dict(S=(.038, .15, .19), E=(.04, .125, .097), W=(.04, .143, .03), C=(.04, .16, 0.), bend=-1, front=True)
RL = dict(S=(.045, -.12, .17), E=(.047, -.07, .108), W=(.045, -.172, .062), C=(.045, -.148, 0.), bend=1, front=False)
TAIL = [((0, -.195, .205), (0, -.285, .2), .016, .013), ((0, -.285, .2), (0, -.375, .19), .013, .011), ((0, -.375, .19), (0, -.465, .178), .011, .008)]

IRIS = {"mike": ((.55, .62, .12), (.75, .62, .1)), "chatora": ((.78, .45, .05), (.85, .62, .12)), "kuro": ((.85, .55, .04), (.9, .7, .12)),
        "shiro": ((.62, .64, .14), (.82, .72, .2)), "sabatora": ((.3, .5, .1), (.62, .62, .14)), "hachiware": ((.72, .58, .08), (.82, .72, .16))}
NOSE_C = {"mike": (.72, .36, .36), "chatora": (.62, .26, .2), "kuro": (.025, .02, .02), "shiro": (.78, .42, .42), "sabatora": (.38, .17, .13), "hachiware": (.7, .34, .34)}
PAD_C = {"mike": (.7, .38, .38), "chatora": (.62, .3, .25), "kuro": (.025, .02, .02), "shiro": (.78, .45, .45), "sabatora": (.12, .07, .06), "hachiware": (.72, .38, .38)}
WHISK = {"kuro": .9}


def _len_body(P, Nn):
    x, y, z = P.T
    L = .021 + .004 * sm(.18, .25, z) + .006 * sm(.16, .13, z) + .008 * sm(.13, .19, y) * sm(.2, .14, z)   # 背は長め、おなかの下は短め、胸の前は長め
    return L, np.ones(len(P))


def _len_neck(P, Nn):
    return .022 + 0 * P[:, 0], np.ones(len(P))


def _len_head(P, Nn):
    q = P - np.array(HEAD_C); x, y, z = P.T; ax = np.abs(x)
    de = np.linalg.norm(np.stack([ax - EYE.x, y - EYE.y, z - EYE.z], 1), axis=1)
    dn = np.linalg.norm(P - np.array(NOSE), axis=1)
    face = sm(.27, .292, y)
    L = .011 - .006 * face + .006 * sm(.012, .03, ax) * sm(.3, .285, z) * sm(.25, .28, y)     # 顔の前は短く、ほおは長め
    L = L * sm(EYE_R * 1.05, EYE_R * 1.7, de) * sm(.006, .011, dn)
    D = sm(EYE_R * 1.0, EYE_R * 1.25, de) * sm(.0065, .0085, dn)
    mouth = sm(.004, .0, np.abs(x) - .014) * sm(.268, .278, y) * sm(.2835, .2805, z)      # 口の下（口の中の板）には生やさない
    D = D * (1 - mouth)
    L = np.maximum(L, .0025 * (D > 0))
    return L, D


def _len_leg(P, Nn):
    z = P[:, 2]
    return .009 + .009 * sm(.03, .15, z), np.ones(len(P))


def _len_paw(P, Nn):
    under = sm(-.2, -.6, Nn[:, 2])                    # 足の裏（肉球）は毛なし
    return .0055 * (1 - under) + .0001, 1 - under


def _len_tail(P, Nn):
    return .022 + .006 * sm(-.25, -.4, P[:, 1]), np.ones(len(P))


def _flow_body(P):
    x, y, z = P.T; n = len(P)
    f = np.stack([.25 * np.sign(x) * sm(.2, .14, z), -np.ones(n), -.25 - .6 * sm(.17, .12, z)], 1)
    return f


def _flow_head(P):
    d = P - np.array(NOSE) + np.array([0, 0, -.004]); d[:, 1] -= .01
    return d


def build_cat(name, coat="mike", seed=1, fur=True, dens=1.0):
    """猫を 1 匹作る。name：名前の頭（猫ごとに別の名前）。coat：mike・chatora・kuro・shiro・sabatora・hachiware。dens：毛の本数の倍率"""
    t0 = _time.time()
    c = dict(name=name, coat=coat, seed=seed, parts={}, fur={}, nhair=0, dens=dens)
    root = mlink(bpy.data.objects.new(name, None)); root["pivot"] = (0, 0, 0); root.rotation_mode = "XYZ"; c["root"] = root
    rs = random.Random(seed)
    # 胴（後ろ半分：腰が原点）と胸（前半分）
    torso = mesh_part(c, "torso", loft(BODY_R), (0, -.12, .175), root, skin_mat(), "body")
    chest = mesh_part(c, "chest", loft(BODY_F), (0, .03, .185), torso, skin_mat(), "body")
    neck = mesh_part(c, "neck", loft(NECK, 24, 36), (0, .165, .212), chest, skin_mat(), "neck")
    head = part(c, "head", [((0, .254, .313), .047, B, None), ((.019, .272, .293), .029, E, (1.1, 1, .85)), ((-.019, .272, .293), .029, E, (1.1, 1, .85)),
                            ((0, .292, .292), .022, E, (1.15, 1, .8)), ((.0088, .303, .2855), .0135, E, (1.1, 1, .85)), ((-.0088, .303, .2855), .0135, E, (1.1, 1, .85)),
                            ((0, .296, .303), .012, E, (.9, 1.25, .9)), ((.017, .281, .323), .014, E, (1.2, 1, .8)), ((-.017, .281, .323), .014, E, (1.2, 1, .8))],
                (0, .228, .272), neck, .0022, "head")
    jaw = part(c, "jaw", [((0, .286, .2738), .0165, E, (.8, 1.3, .55)), ((0, .275, .275), .019, E, (1.05, 1, .6))], (0, .266, .283), head, .0018, "jaw")
    # 目・まぶた
    iris, iris2 = IRIS[coat]; jr = random.Random(seed * 3 + 1); iris = tuple(max(0, v * jr.uniform(.85, 1.1)) for v in iris)
    em = eye_mat(f"{coat}{seed}", iris, iris2, .0086); c["eye_mat"] = em
    lids = []; eyes = []
    for sx in (-1, 1):
        ec = Vector((sx * EYE.x, EYE.y, EYE.z)); rot = Matrix.Rotation(-sx * EYE_YAW, 3, "Z")
        bm = _sphere_bm((0, 0, 0), EYE_R, (1, 1, 1), 32); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts); bmesh.ops.translate(bm, vec=ec, verts=bm.verts)
        eo = mesh_part(c, f"eye{sx}", bm, tuple(ec), head, em, paint=False); eo.rotation_euler = (0, 0, 0)
        # 目の物体の座標で +Y が視線になるよう、メッシュを戻して物体を回す
        for v in eo.data.vertices:
            v.co = rot.inverted() @ v.co
        eo.rotation_euler = (0, 0, -sx * EYE_YAW); eyes.append(eo)
        for up_ in (1, -1):
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=20, radius=EYE_R * 1.07)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * up_ < -1e-5], context="VERTS")
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(-sx * .14, 3, "Y"), verts=bm.verts)   # 目じりを少し上げる（アーモンド形）
            bmesh.ops.translate(bm, vec=ec, verts=bm.verts)

            def rim(P, rgb, Nn, up_=up_):
                d = np.abs((P[:, 2] - EYE.z)) / (EYE_R * 1.07)
                k = sm(.25, .05, d)[:, None]
                return rgb * (1 - k) + np.array([.015, .012, .012]) * k
            lo = mesh_part(c, f"lid{sx}{'u' if up_ > 0 else 'l'}", bm, tuple(ec), head, skin_mat(), "lid", True, rim)
            sd_ = lo.modifiers.new("so", "SOLIDIFY"); sd_.thickness = .0006; sd_.offset = 1
            lo["up"] = up_; lo["sx"] = sx; lo["yaw"] = -sx * EYE_YAW; lo.rotation_euler = (0, 0, lo["yaw"]); lids.append(lo)
    # 鼻（ピンクの逆三角）と鼻の穴、口の線
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=1.0)
    for v in bm.verts:
        wdt = .0062 * (1 - .5 * max(0., -v.co.z)); v.co.x *= wdt; v.co.z *= .0042; v.co.y *= .0036
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(-.45, 3, "X"), verts=bm.verts); bmesh.ops.translate(bm, vec=NOSE, verts=bm.verts)
    nm_ = wet("nose_" + coat, NOSE_C[coat], .38, .5, 3500., .3)
    mesh_part(c, "nose", bm, tuple(NOSE), head, nm_, paint=False)
    nk = wet("nostril", (.01, .006, .006), .6, 0, 1, 0)
    for sx in (-1, 1):
        solid(c, f"nostril{sx}", (sx * .0026, NOSE.y + .0028, NOSE.z - .0012), .0012, nk, head, (1.5, .6, .7))
    mouthk = wet("mouthline", (.02, .012, .012), .6, 0, 1, 0)
    pts = [(0, NOSE.y - .0005, NOSE.z - .0045), (0, NOSE.y - .0012, NOSE.z - .0095)]
    bm = bmesh.new()
    for sx in (-1, 1):
        prof = [(0, NOSE.y - .0012, NOSE.z - .0095), (sx * .004, NOSE.y - .0022, NOSE.z - .0118), (sx * .0085, NOSE.y - .0045, NOSE.z - .0118), (sx * .012, NOSE.y - .0075, NOSE.z - .0105)]
        for a_, b2 in zip(prof[:-1], prof[1:]):
            r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.00045, radius2=.00045, depth=(Vector(b2) - Vector(a_)).length)
            d = Vector(b2) - Vector(a_); bmesh.ops.translate(bm, vec=(0, 0, d.length / 2), verts=r_["verts"])
            bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=d.to_track_quat("Z", "Y").to_matrix(), verts=r_["verts"]); bmesh.ops.translate(bm, vec=a_, verts=r_["verts"])
    a_, b2 = Vector(pts[0]), Vector(pts[1]); d = b2 - a_
    r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.0004, radius2=.0004, depth=d.length); bmesh.ops.translate(bm, vec=(0, 0, d.length / 2), verts=r_["verts"])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=d.to_track_quat("Z", "Y").to_matrix(), verts=r_["verts"]); bmesh.ops.translate(bm, vec=a_, verts=r_["verts"])
    mesh_part(c, "mouthline", bm, (0, 0, 0), head, mouthk, paint=False)
    # 口の中（上あご・舌・牙）：あごを開くと見える
    pal = wet("mouth_in", (.36, .09, .1), .4, .3, 1500, .2); tg = wet("tongue", (.78, .32, .36), .35, .6, 4000, .25); tooth = wet("tooth", (.85, .82, .74), .25, 0, 1, .5)
    solid(c, "palate", (0, .284, .2782), .001, pal, head, (12, 14, 2.8))
    solid(c, "mouth_lo", (0, .287, .2785), .001, pal, jaw, (10.5, 17, 3.0))
    tongue = solid(c, "tongue", (0, .29, .2805), .001, tg, jaw, (7.5, 14, 2.4)); tongue.rotation_mode = "XYZ"; c["tongue"] = tongue
    tongue["rest"] = tuple(tongue.location)
    for sx in (-1, 1):
        bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=.0012, radius2=.0001, depth=.0072)
        bmesh.ops.translate(bm, vec=(sx * .0068, .3015, .2775 - .0036 + .0012), verts=r_["verts"])
        bmesh.ops.rotate(bm, cent=(sx * .0068, .3015, .2775), matrix=Matrix.Rotation(math.pi, 3, "X"), verts=r_["verts"])
        mesh_part(c, f"fang_u{sx}", bm, (0, 0, 0), head, tooth, paint=False).location = -Vector(head["pivot"])
        bm = bmesh.new(); r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=.0009, radius2=.0001, depth=.004)
        bmesh.ops.translate(bm, vec=(sx * .0058, .3, .2765 + .002), verts=r_["verts"])
        mesh_part(c, f"fang_l{sx}", bm, (0, 0, 0), jaw, tooth, paint=False).location = -Vector(jaw["pivot"])
    # 耳：前が開いた薄い殻（外は毛、内はピンクの肌とまばらな毛）
    ears = []
    for sx in (-1, 1):
        base = Vector((sx * .027, .251, .336)); upv = Vector((sx * .32, .02, 1)).normalized(); H = .045; W = .022; NU, NV = 18, 12
        fwd = Vector((sx * .25, 1, 0)).normalized(); side = upv.cross(fwd).normalized() * (1 if sx > 0 else -1); fwd = side.cross(upv).normalized() * (1 if sx > 0 else -1)
        bm = bmesh.new(); grid = {}
        for s_, off in (("o", 0.), ("i", 1.)):
            for j in range(NV + 1):
                v_ = j / NV; rho = W * (1 - v_) ** .85 + .0006; cc = base + upv * H * v_
                for i in range(NU + 1):
                    phi = (-1 + 2 * i / NU) * math.radians(118)
                    dep = .62 + .2 * v_
                    rr_ = max(rho - .0012, rho * .55) if off else rho
                    pnt = cc + side * rr_ * math.sin(phi) - fwd * rr_ * math.cos(phi) * dep
                    grid[s_, i, j] = bm.verts.new(pnt)
        for s_ in ("o", "i"):
            for j in range(NV):
                for i in range(NU):
                    q = [grid[s_, i, j], grid[s_, i + 1, j], grid[s_, i + 1, j + 1], grid[s_, i, j + 1]]
                    bm.faces.new(q if (s_ == "o") == (sx > 0) else q[::-1])
        for j in range(NV):
            for i in (0, NU):
                q = [grid["o", i, j], grid["o", i, j + 1], grid["i", i, j + 1], grid["i", i, j]]
                try:
                    bm.faces.new(q)
                except ValueError:
                    pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        inner_ids = None

        def ear_col(P, rgb, Nn, fwd=fwd):
            k = sm(-.1, .3, Nn @ np.array(fwd))[:, None]
            pink = np.array([.62, .36, .36]) if coat not in ("kuro",) else np.array([.2, .12, .12])
            return rgb * (1 - k) + pink * k
        eo = mesh_part(c, f"ear{sx}", bm, tuple(base), head, skin_mat(), "ear", True, ear_col)
        eo["fwd"] = tuple(fwd); ears.append(eo)
    # 脚（上・下・足先）。前足は肩から、後ろ足は腰から
    legs = []
    padm = wet("pad_" + coat, PAD_C[coat], .45, .7, 1800., .2)
    for k, (spec, sx) in enumerate(((FL, -1), (FL, 1), (RL, -1), (RL, 1))):
        S, Ee, W_, C = [Vector((sx * spec[q][0], spec[q][1], spec[q][2])) for q in ("S", "E", "W", "C")]
        par = chest if spec["front"] else torso; nm = ("f" if spec["front"] else "r") + ("l" if sx < 0 else "r")
        if spec["front"]:
            up = part(c, nm + "_up", ch(S + Vector((0, .003, -.01)), Ee, .03, .022, 6) + [(tuple(S + Vector((-sx * .004, -.006, -.025))), .032, E, (.65, 1.05, 1.2))], tuple(S), par, .003, "leg")
            lo = part(c, nm + "_lo", ch(Ee, W_, .023, .0165, 6), tuple(Ee), up, .0025, "leg")
            toe_y = C.y; heel = W_
        else:
            up = part(c, nm + "_up", ch(S, Ee, .032, .024, 5) + [((sx * .033, -.115, .165), .057, E, (.5, 1.1, 1.25))], tuple(S), par, .003, "leg")
            lo = part(c, nm + "_lo", ch(Ee, W_, .024, .015, 7), tuple(Ee), up, .0025, "leg")
            toe_y = C.y
        tip = Vector((sx * spec["C"][0], toe_y, .0125))
        pel = ch(W_, tip + Vector((0, -.006, .004)), .0145, .015, 5) + [(tuple(tip), .0185, E, (1.05, 1.2, .72))]
        for i, dx in enumerate((-.0105, -.0037, .0037, .0105)):
            pel.append(((tip.x + dx, tip.y + .0095 - .003 * abs(dx) / .0105, .0105), .0088, E, (1, 1.1, .95)))
        paw = part(c, nm + "_paw", pel, tuple(W_), lo, .0018, "paw")
        # 肉球：大きな肉球と、指の肉球 4 つ（足の裏）
        solid(c, nm + "_pad", (tip.x, tip.y - .002, .0026), .0072, padm, paw, (1.15, .9, .38))
        for i, dx in enumerate((-.0098, -.0034, .0034, .0098)):
            solid(c, f"{nm}_bean{i}", (tip.x + dx, tip.y + .0105 - .0035 * abs(dx) / .0098, .0028), .0034, padm, paw, (.9, 1.05, .5))
        legs.append(dict(up=up, lo=lo, paw=paw, S=S, E=Ee, W=W_, C=Vector((sx * spec["C"][0], spec["C"][1], 0)), bend=spec["bend"], front=spec["front"], sx=sx))
    # しっぽ（3 節）
    tails = []; par = torso
    for i, (a_, b2, r0, r1) in enumerate(TAIL):
        par = part(c, f"tail{i}", ch(a_, b2, r0, r1, 8) + ([((0, -.465, .178), .009, B, None)] if i == 2 else []), a_, par, .0025, "tail"); tails.append(par)
    # 毛
    if fur:
        HB = (.95, 1.36)
        grow_fur(c, torso, lambda P, N: (_len_body(P, N)[0], .55 + .45 * sm(SEAM + .04, SEAM - .01, P[:, 1])), _flow_body, HB)
        grow_fur(c, chest, lambda P, N: (_len_body(P, N)[0], .55 + .45 * sm(SEAM - .04, SEAM + .01, P[:, 1])), _flow_body, HB)
        grow_fur(c, neck, _len_neck, lambda P: np.tile([0, -1., -.6], (len(P), 1)), (.9, 1.3))
        grow_fur(c, head, _len_head, _flow_head, (1.0, 1.42), r0=.00005, dens=1.15)
        grow_fur(c, jaw, lambda P, N: (.0045 + 0 * P[:, 0], sm(.2, -.2, N[:, 2]) * .9 + .1), lambda P: np.tile([0, -.7, -1.], (len(P), 1)), (1.0, 1.4), r0=.00005)
        for eo in ears:
            fw = np.array(eo["fwd"])

            def ear_len(P, Nn, fw=fw, eo=eo):
                inner = sm(-.2, .3, Nn @ fw); hgt = (P - np.array(eo["pivot"]))[:, 2]
                Lo = .0035 * (1 - .6 * sm(.02, .04, hgt)); Li = .011 * sm(.03, .005, hgt) + .003
                return Lo * (1 - inner) + Li * inner, (1 - inner) + inner * .22
            cv = grow_fur(c, eo, ear_len, lambda P: np.tile([0, 0, 1.], (len(P), 1)), (.85, 1.2), r0=.000045)
        for lg in legs:
            grow_fur(c, lg["up"], _len_leg, lambda P: np.tile([0, -.15, -1.], (len(P), 1)), (1.0, 1.38))
            grow_fur(c, lg["lo"], _len_leg, lambda P: np.tile([0, -.1, -1.], (len(P), 1)), (1.05, 1.4))
            grow_fur(c, lg["paw"], _len_paw, lambda P: np.tile([0, 1., -.6], (len(P), 1)), (1.05, 1.4), r0=.00005)
        for i, tl in enumerate(tails):
            grow_fur(c, tl, _len_tail, lambda P: np.tile([0, -1., -.05], (len(P), 1)), (.8, 1.22), wave=.25)
        for lo in lids:
            grow_fur(c, lo, lambda P, N: (.003 + 0 * P[:, 0], sm(.2, .5, np.abs((P[:, 2] - EYE.z)) / EYE_R)), lambda P: np.tile([0, 0, 1.], (len(P), 1)), (1.1, 1.4), r0=.00004, dens=1.3, npts=4)
    # ひげ（鼻の横のふくらみから外へ 3 列、目の上、ほお）
    rr = np.random.default_rng(seed + 100); roots = []; dirs = []; lens = []
    for sx in (-1, 1):
        for row in range(3):
            for i in range(4):
                roots.append((sx * (.0075 + .0028 * i), .3045 - .0018 * i, .2885 - .0028 * row))
                dirs.append((sx * 1.0, .1 - .28 * i / 3 + rr.normal(0, .05), .03 - .14 * row + rr.normal(0, .04)))
                lens.append(.06 + .014 * (1 - abs(i - 1.5) / 1.5) - .006 * row + rr.normal(0, .004))
        for i in range(3):
            roots.append((sx * (.012 + .004 * i), .292 - .002 * i, .3215 + .0015 * i)); dirs.append((sx * .7, .35, .9)); lens.append(.03 + .006 * i)
        for i in range(2):
            roots.append((sx * .036, .268 - .004 * i, .295 + .003 * i)); dirs.append((sx * 1.0, -.2, .15)); lens.append(.035)
    strands(c, "whiskers", roots, dirs, np.array(lens), head, .00025, .35, WHISK.get(coat, .025))
    head.location = Vector(head.location) + Vector(HEAD_OFF); head.scale = (HEAD_S,) * 3    # 頭は首の先に少し下げて付ける（頭の寸法はそのまま）
    # 部品の一覧
    c.update(torso=torso, chest=chest, neck=neck, head=head, jaw=jaw, ears=ears, tails=tails, legs=legs, lids=lids, eyes=eyes)
    anim = [root, torso, chest, neck, head, jaw, tongue] + ears + tails + lids + [lg[k] for lg in legs for k in ("up", "lo", "paw")]
    for o in anim:
        o.rotation_mode = "XYZ"; o["rest_loc"] = tuple(o.location); o["rest_scale"] = tuple(o.scale)
    c["anim"] = anim; CANIM.extend(anim); CATS[name] = c
    hull = []
    for o in [torso, chest, neck, head, jaw] + tails + [lg[k] for lg in legs for k in ("up", "lo", "paw")]:
        V = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", V); V = V.reshape(-1, 3)
        hull.append((o, V[::max(1, len(V) // 150)]))
    c["hull"] = hull
    c["build_s"] = _time.time() - t0
    log(f"cat {name} ({coat}) built: {c['nhair']} hairs, {c['build_s']:.1f}s")
    return c


# ---------------------------------------------------------------- 胴輪
def harness(c, col=(.7, .06, .05), ring_col=(.8, .78, .72)):
    """胴輪（首の付け根と前足の後ろの 2 本の帯、背中の帯、D 環）。胸の部品の子。戻り値：綱をつなぐ点（世界座標）を返す関数"""
    chest = c["chest"]; pv = Vector(chest["pivot"])
    me = chest.data; tree = BVHTree.FromPolygons([tuple(v.co) for v in me.vertices], [tuple(p_.vertices) for p_ in me.polygons])
    fab = bpy.data.materials.new(c["name"] + "_harness"); fab.use_nodes = True; t = fab.node_tree; b = t.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = .62; b.inputs["Sheen Weight"].default_value = .4
    wv = t.nodes.new("ShaderNodeTexWave"); wv.inputs["Scale"].default_value = 900.; bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .25
    t.links.new(wv.outputs["Fac"], bp.inputs["Height"]); t.links.new(bp.outputs["Normal"], b.inputs["Normal"]); add_haze(fab, 150., 4000., .8)
    metal = mat("cat_ring", ring_col, .25, 1.0, haze=True)
    lift = .013                                    # 毛の厚み（帯は毛の上に乗る）

    def cast(org, d):
        loc, nor, _, dist = tree.ray_cast(Vector(org) - pv, Vector(d).normalized(), .5)
        return (loc + pv, nor) if loc is not None else (None, None)
    bands = [(Vector((0, .072, .19)), Vector((0, 1, -.2)).normalized(), .016), (Vector((0, .168, .2)), Vector((0, .75, .66)).normalized(), .014)]
    tops = []; bm = bmesh.new(); NS = 64
    for cen, nrm, wd in bands:
        a1 = Vector((1, 0, 0)); a2 = nrm.cross(a1).normalized()
        if a2.z < 0:
            a2 = -a2
        rows = []
        for i in range(NS):
            th = 2 * math.pi * i / NS; dv = a1 * math.sin(th) + a2 * math.cos(th); row = []
            for w_, h_ in ((-.5, 0.), (-.3, .0025), (.3, .0025), (.5, 0.)):
                o_ = cen + nrm * (wd * w_) + dv * .3; hp, hn = cast(o_, -dv)
                if hp is None:
                    hp = cen + nrm * (wd * w_) + dv * .06; hn = dv
                row.append(bm.verts.new(hp + hn * (lift + h_)))
            rows.append(row)
            if i == 0:
                tops.append(rows[0][1].co.lerp(rows[0][2].co, .5))
        for i in range(NS):
            r1, r2 = rows[i], rows[(i + 1) % NS]
            for j in range(3):
                bm.faces.new((r1[j], r2[j], r2[j + 1], r1[j + 1]))
    # 背中の帯：2 本の帯の上をつなぐ
    a_, b2 = tops[0], tops[1]; NB = 10; rows = []
    for i in range(NB + 1):
        p_ = a_.lerp(b2, i / NB); row = []
        for w_, h_ in ((-.5, 0.), (-.3, .0025), (.3, .0025), (.5, 0.)):
            o_ = p_ + Vector((.012 * w_ * 2, 0, .3)); hp, hn = cast(o_, (0, 0, -1))
            hp = hp if hp is not None else p_; hn = hn if hn is not None else Vector((0, 0, 1))
            row.append(bm.verts.new(hp + hn * (lift + .001 + h_)))
        rows.append(row)
    for i in range(NB):
        for j in range(3):
            bm.faces.new((rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ho = mesh_part(c, "harness", bm, tuple(pv), chest, fab, paint=False)
    so = ho.modifiers.new("so", "SOLIDIFY"); so.thickness = .0025; so.offset = 0
    # D 環（後ろの帯の上に立てる）
    top = tops[0] + Vector((0, 0, .001)); R_, r_ = .009, .0013; bm = bmesh.new(); NU, NV = 32, 10; vs = []
    for i in range(NU):
        u = 2 * math.pi * i / NU; cu = Vector((R_ * math.cos(u), 0, R_ * math.sin(u) * 1.15)); dn = Vector((math.cos(u), 0, math.sin(u)))
        vs.append([bm.verts.new(top + Vector((0, 0, R_ * 1.15)) + cu + (Vector((0, 1, 0)) * math.cos(2 * math.pi * j / NV) + dn * math.sin(2 * math.pi * j / NV)) * r_) for j in range(NV)])
    for i in range(NU):
        for j in range(NV):
            bm.faces.new((vs[i][j], vs[(i + 1) % NU][j], vs[(i + 1) % NU][(j + 1) % NV], vs[i][(j + 1) % NV]))
    ro = mesh_part(c, "dring", bm, tuple(pv), chest, metal, paint=False)
    ring_local = top + Vector((0, 0, 2 * R_ * 1.15)) - pv
    # 帯の下の毛を寝かせる（帯を突き抜けないように）
    cv = c["fur"].get(chest.name)
    if cv is not None:
        cd = cv.data; n = len(cd.points); P = np.empty(n * 3, np.float32); cd.position_data.foreach_get("vector", P); P = P.reshape(-1, 3)
        npts = len(P) // len(cd.curves); P = P.reshape(len(cd.curves), npts, 3); root_ = P[:, 0] + np.array(pv)
        k = np.ones(len(P))
        for cen, nrm, wd in bands:
            dd = np.abs((root_ - np.array(cen)) @ np.array(nrm)); k = np.minimum(k, .25 + .75 * sm(wd * .5, wd * .5 + .008, dd))
        dd = np.abs(root_[:, 0]); band_y = (root_[:, 1] > tops[0].y - .01) & (root_[:, 1] < tops[1].y + .01) & (root_[:, 2] > .22)
        k = np.where(band_y, np.minimum(k, .25 + .75 * sm(.012, .02, dd)), k)
        P = P[:, :1] + (P - P[:, :1]) * k[:, None, None]
        cd.position_data.foreach_set("vector", P.reshape(-1)); cd.update_tag()
    c["harness"] = (ho, ro)
    return lambda: chest.matrix_world @ ring_local


# ---------------------------------------------------------------- ポーズ
def _rx(a):
    return Matrix.Rotation(a, 4, "X")


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def _mw(o):
    """部品の世界の行列（view_layer.update() なしで、親をたどって計算する）"""
    m = o.matrix_basis.copy()
    p = o.parent
    while p is not None:
        m = p.matrix_basis @ m; p = p.parent
    return m


def leg_ik(c, lg, target_w, tilt=0.0, paw_rot=None):
    """足先（手首・かかと）を世界の点 target_w に。膝・ひじの向きは前足は後ろ、後ろ足は前。tilt：足先の、地面に対する傾き（+ で つま先が上）"""
    par = lg["up"].parent; Mp = _mw(par); pv = Vector(par["pivot"])
    tl = Mp.inverted() @ Vector(target_w) + pv
    S, Ee, W_ = lg["S"], lg["E"], lg["W"]
    d = Vector((0, tl.y - S.y, tl.z - S.z)); L1 = (Ee - S).yz.length; L2 = (W_ - Ee).yz.length
    lg["up"].location = lg["up"]["rest_loc"]
    over = d.length - (L1 + L2) * .985
    if over > 0:      # 届かないときは肩（肩甲骨）・腰を少しだけ足の方へずらす
        sh = d.normalized() * min(over, .03 if lg["front"] else .015)
        lg["up"].location = Vector(lg["up"]["rest_loc"]) + sh; d = d - sh
    dist = d.length; dc = max(abs(L1 - L2) + 1e-4, min(dist, (L1 + L2) * .9995))
    base = math.atan2(d.z, d.y); A = math.acos(max(-1, min(1, (L1 * L1 + dc * dc - L2 * L2) / (2 * L1 * dc))))
    u = base + lg["bend"] * A
    Ep = Vector((math.cos(u), math.sin(u))) * L1; Wp = Vector((math.cos(base), math.sin(base))) * dc
    l_ = math.atan2(Wp.y - Ep.y, Wp.x - Ep.x)
    u0 = math.atan2(Ee.z - S.z, Ee.y - S.y); l0 = math.atan2(W_.z - Ee.z, W_.y - Ee.y)
    a1 = _wrap(u - u0); a2 = _wrap(l_ - l0 - a1)
    lg["up"].rotation_euler = (a1, 0, 0); lg["lo"].rotation_euler = (a2, 0, 0)
    if paw_rot is None:
        R0 = c["root"].matrix_basis.to_3x3(); Rlo = (Mp.to_3x3() @ _rx(a1).to_3x3() @ _rx(a2).to_3x3())
        Rlo.normalize()
        want = R0 @ Matrix.Rotation(tilt, 3, "X")
        lg["paw"].rotation_euler = (Rlo.inverted() @ want).to_euler("XYZ")
    else:
        lg["paw"].rotation_euler = paw_rot
    return dist - dc


def leg_fk(lg, a1, a2, a3):
    lg["up"].rotation_euler = (a1, 0, 0); lg["lo"].rotation_euler = (a2, 0, 0); lg["paw"].rotation_euler = (a3, 0, 0)


def _gait(ph, off, S, h, duty=.62):
    """1 本の足の、地面の点からのずれ（前後 y・高さ z）と足先の傾き"""
    f = (ph + off) % 1.0
    if f < duty:
        u = f / duty; return S / 2 - S * u, 0.0, -.25 * max(0, u - .75) / .25
    u = (f - duty) / (1 - duty); e = .5 - .5 * math.cos(math.pi * u)
    return -S / 2 + S * e, h * math.sin(math.pi * u), -.9 * math.sin(math.pi * u) ** .7 + .25 * max(0, u - .7)


GAIT_OFF = (.25, .75, 0.0, .5)    # 左前・右前・左後ろ・右後ろ（猫の並足：左後ろ → 左前 → 右後ろ → 右前）


def _pulse(t, seed, every=4.0, dur=.35):
    """ときどきの小さな動き（耳をぴくっ）：0〜1"""
    r = random.Random(int(t // every) * 31 + seed); t0 = r.uniform(0, every - dur); u = (t % every - t0) / dur
    return math.sin(math.pi * u) if 0 <= u <= 1 else 0.0


def cpose(c, pos=(0, 0), heading=0.0, mode="stand", t=0.0, ph=0.0, k=1.0, **kw):
    """猫のポーズ。pos：胴の真下の地面の点（z を書けば高さも）。heading：0 で +Y を向く。
    mode：stand・walk・pull・sit・loaf・curl・stretch・groom・yawn。t：時刻（秒、呼吸・耳・しっぽ）。ph：歩きの周期（1 で 4 本が 1 歩ずつ）。
    k：そのモードの強さ（0〜1、stand から混ぜる）。kw：head=(上下, 左右)、jaw、lid、ears=(後ろへ, 外へ)、tail=(上下, 左右)、amp（歩幅の倍率）、stride（m）、
    pupil（瞳孔の幅、昼 .0012〜夜 .005）、tongue（0〜1）"""
    R = c["root"]; s = c["seed"]
    R.location = (pos[0], pos[1], pos[2] if len(pos) > 2 else 0.0); R.rotation_euler = (0, 0, heading)
    for o in c["anim"][1:]:
        o.location = o["rest_loc"]; o.rotation_euler = (0, 0, 0); o.scale = o["rest_scale"]
    torso, chest, neck, head, jaw = c["torso"], c["chest"], c["neck"], c["head"], c["jaw"]
    br = math.sin(t * 2 * math.pi / (3.2 if mode == "curl" else 1.6) + s)        # 呼吸
    hd = list(kw.get("head", (0, 0))); jw = kw.get("jaw", 0.0); lid = kw.get("lid", None); tg = kw.get("tongue", 0.0)
    tl = list(kw.get("tail", (0, 0))); ear = list(kw.get("ears", (0, 0))); amp = kw.get("amp", 1.0)
    legs = c["legs"]; Rh = Matrix.Rotation(heading, 3, "Z"); P0 = Vector(R.location)

    def plant(lg, dy=0., dz=0., tilt=0., dx=0.):
        C = Vector((lg["C"].x + dx * lg["sx"], lg["C"].y + dy, 0))
        off = Matrix.Rotation(tilt, 3, "X") @ (lg["W"] - Vector((lg["C"].x, lg["C"].y, 0)))   # 足先を傾けると、手首もつま先のまわりで回る
        w = P0 + Rh @ (C + off + Vector((0, 0, dz)))
        res = leg_ik(c, lg, w, tilt)
        if res > .003:
            DBG.append((lg["up"].name, round(res, 3)))
        return res
    fit = False
    torso.scale = (1 + .018 * br, 1, 1 + .022 * br)
    sway = math.sin(t * 1.3 + s) * .25 + math.sin(t * 2.9 + s * 2) * .08
    tail_z = [sway * (.4 + .4 * i) for i in range(3)]; tail_x = [0., 0., 0.]
    if mode in ("stand", "walk", "pull"):
        lean = k if mode == "pull" else 0.0
        stride = kw.get("stride", (.13 if mode == "pull" else .24)) * amp
        moving = mode in ("walk", "pull") and amp > 0
        w = 2 * math.pi * ph
        bob = (.004 * math.sin(2 * w) if moving else 0.0)
        torso.location = Vector(torso["rest_loc"]) + Vector((0, 0, -.01 * lean + bob - (.01 if moving else 0)))
        torso.rotation_euler = (-.05 * lean + .012 * math.sin(2 * w) * moving, .02 * math.sin(w) * moving, .03 * math.sin(w) * moving)
        chest.rotation_euler = (-.07 * lean, -.02 * math.sin(w) * moving, -.03 * math.sin(w + .3) * moving)
        neck.rotation_euler = (-.38 * lean, 0, 0)
        head.rotation_euler = (.42 * lean + .03 * math.sin(2 * w + 1) * moving + hd[0], 0, hd[1])
        tail_x = [.75 - .5 * lean, -.25 + .25 * lean, -.45 + .35 * lean]
        if mode == "walk":
            tail_x = [-.95, -.35, -.45]
        ear = [ear[0] + .3 * lean, ear[1]]
        for lg, off in zip(legs, GAIT_OFF):
            dy0 = (.012 if lg["front"] else -.085) * lean
            if moving:
                gy, gz, gt = _gait(ph, off, stride, .028 if not lean else .02)
            else:
                gy, gz, gt = 0., 0., 0.
            plant(lg, dy0 + gy, gz, gt)
    elif mode in ("sit", "groom", "yawn") or (mode == "yawn"):
        torso.location = Vector(torso["rest_loc"]) + Vector((0, -.005, -.118))
        torso.rotation_euler = (.62 * k, 0, 0)
        chest.rotation_euler = (-.27 * k, 0, 0)
        neck.rotation_euler = (-.25 * k, 0, 0)
        head.rotation_euler = (-.22 * k + hd[0], 0, hd[1])
        for lg in legs:
            if lg["front"]:
                plant(lg, -.035, 0, 0)
            else:
                plant(lg, .1, 0, .8, -.004)
        tail_x = [-.7, -.2, -.05]; tail_z = [.7 + .1 * sway, .9 + .1 * sway, .8 + .2 * sway]
        if mode == "groom":
            lg = legs[1]; u = .5 + .5 * math.sin(t * 5.0)
            head.rotation_euler = (-.45 - .08 * u, .1, -.35); jw = max(jw, .12 + .06 * u); tg = max(tg, .7 + .3 * u)
            Mh = _mw(head); tgt = Mh @ (Vector((0, .303, .262 + .006 * u)) - Vector(head["pivot"]))
            leg_ik(c, lg, tgt, -1.25 + .2 * u)
            lid = .45 if lid is None else lid
        if mode == "yawn":
            u = clamp(kw.get("open", 1.0))
            head.rotation_euler = (-.22 + .55 * u + hd[0], 0, hd[1]); jw = max(jw, .75 * u); lid = .75 * u if lid is None else lid; ear = [ear[0] + .6 * u, ear[1] + .3 * u]
            tg = max(tg, .2 * u)
    elif mode == "loaf":
        torso.location = Vector(torso["rest_loc"]) + Vector((0, .0, -.112)); torso.rotation_euler = (.03, 0, 0); chest.rotation_euler = (-.02, 0, 0)
        neck.rotation_euler = (-.12, 0, 0); head.rotation_euler = (.03 + hd[0], 0, hd[1])
        for lg in legs:
            if lg["front"]:
                leg_fk(lg, -1.3, 2.45, -1.05)
            else:
                plant(lg, .11, 0, 1.05, .01)
        tail_x = [.5, .1, 0]; tail_z = [.75, .9, .8 + .1 * sway]
        torso.scale = (1 + .012 * br, 1, 1 + .015 * br)
    elif mode == "curl":
        # ドーナツ形：おなかを下に、足をたたみ、背骨を横へ曲げて、頭をしっぽの近くの地面に置く。しっぽは内側へ巻く
        fit = True
        torso.location = Vector(torso["rest_loc"]) + Vector((0, .02, -.112)); torso.rotation_euler = (.03, .25, .7)
        chest.rotation_euler = (-.02, .1, .55); neck.rotation_euler = (-1.6, 0, .95); head.rotation_euler = (-.1 + hd[0], .5, .9 + hd[1])
        for lg in legs:
            if lg["front"]:
                leg_fk(lg, -1.3, 2.45, -1.05)
            else:
                leg_fk(lg, 1.45, -1.9, .55)
        tail_x = [.55, .12, .05]; tail_z = [-1.1, -1.25, -1.15 + .05 * sway]
        lid = 1.0 if lid is None else lid
        torso.scale = (1 + .02 * br, 1, 1 + .025 * br)
        ear = [ear[0] + .15, ear[1] + .1]
    elif mode == "stretch":
        u = k
        torso.location = Vector(torso["rest_loc"]) + Vector((0, 0, .005 * u)); torso.rotation_euler = (-.32 * u, 0, 0); chest.rotation_euler = (-.38 * u, 0, 0)
        neck.rotation_euler = (.1 * u, 0, 0); head.rotation_euler = (.55 * u + hd[0], 0, hd[1])
        for lg in legs:
            plant(lg, (.14 if lg["front"] else -.02) * u, 0, 0)
        tail_x = [1.2 * u, .3, .1]; tail_z = [.1 * sway, .2 * sway, .3 * sway]
        jw = max(jw, kw.get("yawn", 0) * .7)
    if fit:
        _ground_fit(c)
    # 耳：ときどきぴくっ
    tw = _pulse(t, s * 7 + 1, 3.7, .3)
    for i, eo in enumerate(c["ears"]):
        sx = 1 if i else -1; tw_i = tw if i == (s % 2) else _pulse(t, s * 7 + 5, 5.3, .3)
        eo.rotation_euler = (-(ear[0] + .35 * tw_i) * .8, sx * .15 * tw_i, -sx * (ear[0] * .9 + ear[1] + .25 * tw_i))
    for i, tl_ in enumerate(c["tails"]):
        tl_.rotation_euler = (tail_x[i] + (tl[0] if i == 0 else 0), 0, tail_z[i] + (tl[1] if i == 0 else 0))
    jaw.rotation_euler = (-jw, 0, 0)
    tgo = c["tongue"]; tgo.location = Vector(tgo["rest"]) + Vector((0, .006 * tg, .0012 * tg)); tgo.scale = (1, 1 + .35 * tg, 1); tgo.rotation_euler = (.25 * tg, 0, 0)
    # まばたき（ときどき）とまぶた
    blink = _pulse(t, s * 13 + 3, 4.6, .18)
    lv = clamp(max(lid if lid is not None else 0.0, blink))
    for lo in c["lids"]:
        op = (.78 if lo["up"] > 0 else -.6)
        lo.rotation_euler = (op * (1 - lv), 0, lo["yaw"])
    pw = kw.get("pupil", None)
    if pw is not None:
        c["eye_mat"].node_tree.nodes[c["eye_mat"]["pupil"]].outputs[0].default_value = pw


def _ground_fit(c, target=.004):
    """寝ころぶポーズ：いちばん低い点（皮膚）が地面の少し上に来るよう、猫全体の高さを合わせる"""
    zmin = 1e9
    for o, pts in c["hull"]:
        M = np.array(_mw(o)); z = pts @ M[2, :3] + M[2, 3]; zmin = min(zmin, z.min())
    R = c["root"]; R.location.z += target - zmin


def init_rest(c):
    cpose(c)
