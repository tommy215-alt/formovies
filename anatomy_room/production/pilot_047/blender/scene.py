"""pilot_047（毎日2倍になる隕石。地球は何日もつ？）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計の既定（土台は pilot_045・046）。
使い方："C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P anatomy_room/production/pilot_047/blender/scene.py -- [ショット名 ...] [--still] [--samples N] [--every N] [--resume]
前もって python blender/make_maps.py（地図の素材 work/maps/）、python plan.py（blender/plan.json）、python production_script.py voice（work/timeline.json）。

場面（どれも模式）：
  広場と新宿：都庁（pilot_045 と同じ形）・議事堂・都民広場・西新宿の街（建物の高さは pilot_045 の昼間人口から）。人は顔のないピクトグラム。
  関東・日本の地図：都庁を中心にした正距方位図法（make_maps.py）。被害の円（窓ガラスが割れる距離、sim の days.json）が広がり、中の街の光が消える。
  名古屋城：天守（白い壁・緑の屋根・金のしゃちほこ）に、土煙の壁が届く。
  宇宙：地球（手続き的な陸と海・雲）、その日の隕石、月と火星の大きさの比べ、地球が砕ける。
閃光は使わない（ユーザー「まぶしい」）：爆発・衝突は、煙・揺れ・色の変化（橙の光は弱く）で見せる。血は出さない。崩れる街は避難のあとの無人。
座標：都民広場が原点、x が東、y が北（m）。宇宙の場面は 1 単位＝1,000 km（地球の半径 6.371）。
"""
import sys, os, math, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); cam = K.Cam()
PLAN = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8"))
SPLAN = {s["id"]: s for s in PLAN["shots"]}
DAYS = {d["day"]: d for d in PLAN["days"]}
RND = random.Random(47)
MAPS = os.path.join(HERE, "..", "work", "maps")
INFO = json.load(open(os.path.join(MAPS, "maps.json"), encoding="utf-8"))
DAYP = np.load(os.path.join(HERE, "..", "..", "pilot_045", "work", "maps", "city_daypop.npy"))   # 新宿の昼間人口（建物の高さ）
D_, NOON = 86400, 43200

# 空：曇り（一様な色）と空のテクスチャを混ぜる。遠くの地面と建物は、この色にかすむ（HAZE）
_wn = sc.world.node_tree; _wbg = _wn.nodes["Background"]
WMIX = _wn.nodes.new("ShaderNodeMix"); WMIX.data_type = "RGBA"; _wn.links.new(sky.node.outputs[0], WMIX.inputs[6]); _wn.links.new(WMIX.outputs[2], _wbg.inputs[0])
HAZE = []


def add_haze(m, d0=600., d1=14000., top=.8):
    n = m.node_tree.nodes; L = m.node_tree.links; out = n["Material Output"]; src = out.inputs["Surface"].links[0].from_socket
    cd = n.new("ShaderNodeCameraData"); mr = n.new("ShaderNodeMapRange"); mr.inputs[1].default_value = d0; mr.inputs[2].default_value = d1; mr.inputs[4].default_value = top
    L.new(cd.outputs["View Distance"], mr.inputs[0])
    em = n.new("ShaderNodeEmission"); ms = n.new("ShaderNodeMixShader"); L.new(mr.outputs[0], ms.inputs[0]); L.new(src, ms.inputs[1]); L.new(em.outputs[0], ms.inputs[2]); L.new(ms.outputs[0], out.inputs["Surface"])
    HAZE.append((em, mr))


def set_haze(col, k):
    WMIX.inputs[7].default_value = (*col, 1); WMIX.inputs[0].default_value = 1.0; _wbg.inputs[1].default_value = k
    for em, mr in HAZE:
        em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = k


def clamp(v, a=0., b=1.):
    return max(a, min(b, v))


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def ease(u):
    return K.ease(u)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emat(name, col, rough=.6, metal=0., emit=None, k=0., alpha=None):
    m = K.mat(name, col, rough, metal); b = m.node_tree.nodes["Principled BSDF"]
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = k
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


def esock(m):
    return m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]


def asock(m):
    return m.node_tree.nodes["Principled BSDF"].inputs["Alpha"]


def key_fac(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f + 1)


def keyp(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f + 1)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f + 1)
    if scale is not None:
        o.scale = scale if isinstance(scale, tuple) and len(scale) == 3 else (scale,) * 3; o.keyframe_insert("scale", frame=f + 1)


def img(name):
    p = os.path.abspath(os.path.join(MAPS, name + ".png"))
    im = bpy.data.images.get(name + ".png") or bpy.data.images.load(p); im.colorspace_settings.name = "Non-Color"; return im


# ---------------------------------------------------------------- 時計（plan.json。renderer.html の clockAt と同じ式）
def clock(k, t):
    s = SPLAN[k]; u = clamp(t / s["dur"]); c = s["c"]
    for (u0, c0), (u1, c1) in zip(c, c[1:]):
        if u <= u1 or (u1, c1) == tuple(c[-1]):
            v = clamp((u - u0) / max(1e-9, u1 - u0))
            return c0 + (c1 - c0) * v
    return c[-1][1]


def ev_t(k, j):
    return SPLAN[k]["ev"][j][0]


def day_of(c):
    return int(c // D_) + 1


def since_noon(c):
    return c - ((day_of(c) - 1) * D_ + NOON)


def shake(f, amp, seed=0):
    r = random.Random(f * 7 + seed); return Vector(((r.random() - .5) * amp, (r.random() - .5) * amp, (r.random() - .5) * amp * .6))


# ---------------------------------------------------------------- ピクトグラムの人（pilot_045 と同じ形。顔なし、足もとが原点、-Y が前）
PM = {k: emat("p_" + k, c, .7) for k, c in {
    "suit": (.035, .045, .075), "shirt": (.75, .77, .8), "skin": (.62, .5, .42), "coat_w": (.55, .42, .3), "red": (.5, .07, .07),
    "skirt": (.12, .1, .14), "yellow": (.95, .75, .05), "gray": (.33, .33, .34), "white": (.85, .85, .85), "hair": (.04, .03, .025),
    "black": (.02, .02, .02), "kid": (.1, .3, .55), "bag": (.25, .16, .1)}.items()}


def _part(bm, mi, fn):
    before = set(bm.faces); fn(); [setattr(f_, "material_index", mi) for f_ in set(bm.faces) - before]


def cyl(bm, mi, a, b, r1, r2=None, seg=12):
    a, b = Vector(a), Vector(b); v = b - a
    M = Matrix.Translation((a + b) / 2) @ v.to_track_quat("Z", "Y").to_matrix().to_4x4()
    _part(bm, mi, lambda: bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2 if r2 is not None else r1, depth=v.length, matrix=M))


def sph(bm, mi, c, r, sx=1, sy=1, sz=1):
    M = Matrix.Translation(c) @ Matrix.Diagonal((sx, sy, sz, 1))
    _part(bm, mi, lambda: bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=8, radius=r, matrix=M))


def cube(bm, mi, c, s):
    M = Matrix.Translation(c) @ Matrix.Diagonal((*s, 1))
    _part(bm, mi, lambda: bmesh.ops.create_cube(bm, size=1, matrix=M))


def pict(kind, bag=False):
    """kind：man・woman・child・elder。bag＝避難の荷物（スーツケース）"""
    mats = list(PM.keys()); I = lambda k: mats.index(k); bm = bmesh.new()
    s = {"child": .66, "elder": .93, "woman": .94}.get(kind, 1.0)
    body = {"man": "suit", "woman": "coat_w", "child": "kid", "elder": "gray"}[kind]
    lean = .25 if kind == "elder" else 0.
    hip = .86 * s; sh = 1.42 * s; top = 1.6 * s
    fwd = lambda z: Vector((0, -(z - hip) * lean, z))
    if kind == "woman":
        cyl(bm, I("skin"), (-.07, 0, 0), (-.07, 0, .42 * s), .05); cyl(bm, I("skin"), (.07, 0, 0), (.07, 0, .42 * s), .05)
        cyl(bm, I("skirt"), (0, 0, .38 * s), (0, 0, hip + .06), .27 * s, .15 * s, 16)
    else:
        for x in (-.09, .09):
            cyl(bm, I("black" if kind == "man" else body), (x * s, 0, 0), (x * s, 0, hip), .075 * s)
    cyl(bm, I(body), fwd(hip), fwd(sh), .19 * s, .21 * s, 16)
    sph(bm, I("skin"), fwd(top), .125 * s)
    for x in (-.24, .24):
        cyl(bm, I(body), fwd(sh - .03) + Vector((x * s, 0, 0)), fwd(hip + .1) + Vector((x * s * 1.1, 0, 0)), .055 * s)
    if kind == "man":
        cube(bm, I("shirt"), fwd(sh - .1) + Vector((0, -.17, 0)), (.08, .02, .18))
    if kind == "woman":
        sph(bm, I("hair"), fwd(top) + Vector((0, .03, .02)), .135 * s, 1, 1, .95)
    if kind == "child":
        cyl(bm, I("yellow"), fwd(top) + Vector((0, 0, .05)), fwd(top) + Vector((0, 0, .12)), .13 * s); cube(bm, I("red"), fwd(sh - .2) + Vector((0, .2 * s, 0)), (.3 * s, .14 * s, .34 * s))
    if kind == "elder":
        sph(bm, I("white"), fwd(top) + Vector((0, .02, .03)), .13 * s)
    if bag:   # 引いて歩くスーツケース（右手の後ろ）
        cube(bm, I("bag"), Vector((.36 * s, .45, .3)), (.22, .4, .55)); cyl(bm, I("black"), (.36 * s, .32, .55), (.3 * s, .1, .8), .015, seg=6)
    me = bpy.data.meshes.new(f"pict_{kind}{'_bag' if bag else ''}"); bm.to_mesh(me); bm.free()
    for k in mats:
        me.materials.append(PM[k])
    for p in me.polygons:
        p.use_smooth = True
    return me


KINDS = ["man", "woman", "man", "woman", "child", "elder", "man", "woman"]
MESH = {k: pict(k) for k in set(KINDS)}
MESH.update({k + "_bag": pict(k, True) for k in set(KINDS)})


def person(kind, loc, heading=0., parent=None):
    o = bpy.data.objects.new("p", MESH[kind]); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, heading); o.parent = parent; return o


# ================================================================ 広場と新宿（pilot_045 と同じ形）
CITY = group("city"); PLAZA = group("plaza")
granite = emat("granite", (.26, .25, .24), .55)
glass = bpy.data.materials.new("glass"); glass.use_nodes = True; n = glass.node_tree.nodes; L = glass.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); br = n.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0; br.offset = 0; br.squash = 1
br.inputs["Mortar Size"].default_value = .25; br.inputs["Brick Width"].default_value = 3.2; br.inputs["Row Height"].default_value = 3.6
sep = n.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs[0]); cmb = n.new("ShaderNodeCombineXYZ")
add = n.new("ShaderNodeMath"); add.operation = "ADD"; L.new(sep.outputs[0], add.inputs[0]); L.new(sep.outputs[1], add.inputs[1]); L.new(add.outputs[0], cmb.inputs[0]); L.new(sep.outputs[2], cmb.inputs[1])
L.new(cmb.outputs[0], br.inputs["Vector"]); br.inputs["Color1"].default_value = (.05, .07, .09, 1); br.inputs["Color2"].default_value = (.08, .1, .13, 1); br.inputs["Mortar"].default_value = (.32, .32, .33, 1)
L.new(br.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .25; b.inputs["Metallic"].default_value = .55
nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = .4; L.new(tc.outputs["Object"], nz.inputs["Vector"])
win = n.new("ShaderNodeMath"); win.operation = "GREATER_THAN"; win.inputs[1].default_value = .58; L.new(nz.outputs["Fac"], win.inputs[0])
wk = n.new("ShaderNodeMath"); wk.operation = "MULTIPLY"; L.new(win.outputs[0], wk.inputs[0]); L.new(br.outputs["Fac"], wk.inputs[1])
WIN_K = n.new("ShaderNodeMath"); WIN_K.operation = "MULTIPLY"; WIN_K.inputs[1].default_value = .0; L.new(wk.outputs[0], WIN_K.inputs[0])
_c1 = n.new("ShaderNodeMix"); _c1.data_type = "RGBA"; _c1.blend_type = "MULTIPLY"; _c1.inputs[0].default_value = 1; L.new(WIN_K.outputs[0], _c1.inputs[6]); _c1.inputs[7].default_value = (1, .82, .6, 1)
L.new(_c1.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.0
add_haze(glass)
TOCHO = group("tocho"); TOCHO.parent = PLAZA
K.box("tocho_low", (52, 108, 162), (-112, 0, 81), glass, bevel=0, parent=TOCHO)
for y in (-35, 35):
    K.box(f"tocho_tw{y}", (50, 38, 70), (-112, y, 197), glass, bevel=0, parent=TOCHO)
    K.box(f"tocho_top{y}", (36, 26, 16), (-112, y, 240), granite, bevel=.3, parent=TOCHO)
    K.box(f"tocho_fin{y}", (52, 4, 230), (-112, y + (19 if y > 0 else -19), 115), granite, bevel=0, parent=TOCHO)
K.box("tocho2", (60, 70, 163), (-245, -95, 81), glass, bevel=0, parent=TOCHO); K.box("tocho2b", (44, 50, 30), (-245, -95, 178), granite, bevel=0, parent=TOCHO)
me = bpy.data.meshes.new("gikai"); bm = bmesh.new()
for i in range(28):
    a0, a1 = math.radians(-75 + i * 150 / 28), math.radians(-75 + (i + 1) * 150 / 28)
    vs = [bm.verts.new((-40 + r * math.cos(a), r * math.sin(a), h)) for a in (a0, a1) for r in (78, 96) for h in (0, 36)]
    for f_ in [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]:
        try:
            bm.faces.new([vs[k] for k in f_])
        except ValueError:
            pass
bm.to_mesh(me); bm.free(); GIKAI = bpy.data.objects.new("gikai", me); sc.collection.objects.link(GIKAI); me.materials.append(granite); GIKAI.parent = PLAZA
paving = bpy.data.materials.new("paving"); paving.use_nodes = True; n = paving.node_tree.nodes; L = paving.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); br2 = n.new("ShaderNodeTexBrick"); br2.inputs["Scale"].default_value = .5; L.new(tc.outputs["Object"], br2.inputs["Vector"])
br2.inputs["Color1"].default_value = (.34, .33, .31, 1); br2.inputs["Color2"].default_value = (.29, .285, .27, 1); br2.inputs["Mortar"].default_value = (.06, .06, .06, 1); br2.inputs["Mortar Size"].default_value = .02
L.new(br2.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .55
bpy.ops.mesh.primitive_plane_add(size=1, location=(-20, 0, .03)); PAVE = bpy.context.object; PAVE.scale = (420, 420, 1); bpy.ops.object.transform_apply(scale=True); PAVE.data.materials.append(paving); PAVE.parent = PLAZA
tree_m = emat("tree", (.05, .09, .04), .9); trunk_m = emat("trunk", (.08, .06, .05), .9)
for k in range(26):
    a = math.radians(-80 + k * 160 / 25); x, y = -40 + 108 * math.cos(a), 108 * math.sin(a)
    K.tube((x, y, 0), (x, y, 4), .25, trunk_m, PLAZA, 8); bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=3.2, location=(x, y, 6)); s_ = bpy.context.object; s_.data.materials.append(tree_m); s_.parent = PLAZA

# 新宿の街（建物は昼間人口から、模式）。崩れるビルは別の部品（TOWERS）
NPX = DAYP.shape[0]; HALF = 8000.0


def daypop(x, y):
    a = int((y + HALF) / (2 * HALF) * NPX); b_ = int((x + HALF) / (2 * HALF) * NPX)
    return float(DAYP[min(NPX - 1, max(0, a)), min(NPX - 1, max(0, b_))])


SKYS = [(110, 230, 210), (210, -230, 200), (-20, 380, 190), (300, 440, 220), (430, 20, 180), (380, -400, 170), (-300, 300, 150), (560, 260, 205), (120, -470, 185), (520, -180, 160), (250, 120, 230)]
me = bpy.data.meshes.new("bld"); bm = bmesh.new(); STEP = 44
for i in range(-100, 101):
    for j in range(-100, 101):
        if i % 7 == 0 or j % 7 == 0:
            continue
        x, y = i * STEP + RND.uniform(-6, 6), j * STEP + RND.uniform(-6, 6); r = math.hypot(x, y)
        if r > 4500 or r < 700 or (700 < x < 860 and -600 < y < 900) or (math.hypot(x - 1450, y + 1650) < 260):
            continue   # 都庁から 700 m の内側は崩れる部品（TOWERS）、線路
        p = daypop(x, y)
        if RND.random() > min(.95, .25 + p / 60000):
            continue
        h = 8 + 26 * math.log10(1 + p / 4000) * RND.uniform(.5, 1.5)
        w, d = RND.uniform(16, 38), RND.uniform(16, 38)
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, y, h / 2)) @ Matrix.Diagonal((w, d, h, 1)))
bm.to_mesh(me); bm.free(); BLD = bpy.data.objects.new("bld", me); sc.collection.objects.link(BLD); me.materials.append(glass); BLD.parent = CITY
CAMX, CAMY = 330, -120   # 広場のカメラ（CAMP）


def keep_clear(x, y):
    """広場のカメラの周り・カメラから都庁への視線・窓が割れるビル（FACADE）の前は、建物を置かない"""
    ax, ay, bx, by = CAMX, CAMY, -112, 0; t_ = clamp(((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2))
    return math.hypot(x - ax - t_ * (bx - ax), y - ay - t_ * (by - ay)) < 70 or math.hypot(x - 100, y + 30) < 80
TOWERS = []   # (物, 高さ, 倒れる向き)
for (x, y, h) in SKYS:
    TOWERS.append((K.box(f"tower{x}_{y}", (60, 55, h), (x, y, h / 2), glass, bevel=0, parent=CITY), h, RND.uniform(-.5, .5)))
for i in range(60):   # 700 m の内側の中くらいのビル
    a = RND.uniform(0, 6.283); r = RND.uniform(260, 700); x, y = r * math.cos(a), r * math.sin(a)
    if (-330 < x < 80 and -170 < y < 170) or keep_clear(x, y):
        continue   # 広場・広場のカメラの周りと視線（南東）はあける
    h = RND.uniform(30, 110); TOWERS.append((K.box(f"midb{i}", (RND.uniform(20, 40), RND.uniform(20, 40), h), (x, y, h / 2), glass, bevel=0, parent=CITY), h, RND.uniform(-.6, .6)))
# 地面：道路の格子。被害の円の中は焼けた茶色（DMG_R：半径 m）
gm = bpy.data.materials.new("ground"); gm.use_nodes = True; n = gm.node_tree.nodes; L = gm.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); road = n.new("ShaderNodeTexBrick"); road.inputs["Scale"].default_value = 1 / 308; road.inputs["Mortar Size"].default_value = .14; road.offset = 0; road.squash = 1
road.inputs["Brick Width"].default_value = 1; road.inputs["Row Height"].default_value = 1
L.new(tc.outputs["Object"], road.inputs["Vector"]); road.inputs["Color1"].default_value = (.07, .07, .075, 1); road.inputs["Color2"].default_value = (.08, .08, .085, 1); road.inputs["Mortar"].default_value = (.025, .025, .028, 1)
gp = n.new("ShaderNodeNewGeometry"); vl = n.new("ShaderNodeVectorMath"); vl.operation = "LENGTH"; L.new(gp.outputs["Position"], vl.inputs[0])
dr = n.new("ShaderNodeMath"); dr.operation = "LESS_THAN"; L.new(vl.outputs["Value"], dr.inputs[0]); G_R = dr.inputs[1]; G_R.default_value = 0.
gmix = n.new("ShaderNodeMix"); gmix.data_type = "RGBA"; L.new(dr.outputs[0], gmix.inputs[0]); L.new(road.outputs["Color"], gmix.inputs[6]); gmix.inputs[7].default_value = (.09, .06, .045, 1)
L.new(gmix.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .85
# 円の縁：橙の細い帯（爆風の前線）
rim1 = n.new("ShaderNodeMath"); rim1.operation = "SUBTRACT"; L.new(vl.outputs["Value"], rim1.inputs[0]); G_R2 = rim1.inputs[1]
rim2 = n.new("ShaderNodeMath"); rim2.operation = "ABSOLUTE"; L.new(rim1.outputs[0], rim2.inputs[0])
rim3 = n.new("ShaderNodeMapRange"); rim3.inputs[1].default_value = 0; G_W = rim3.inputs[2]; G_W.default_value = 300; rim3.inputs[3].default_value = 1; rim3.inputs[4].default_value = 0; L.new(rim2.outputs[0], rim3.inputs[0])
rimk = n.new("ShaderNodeMath"); rimk.operation = "MULTIPLY"; L.new(rim3.outputs[0], rimk.inputs[0]); G_RK = rimk.inputs[1]; G_RK.default_value = 0.
b.inputs["Emission Color"].default_value = (1, .38, .1, 1); L.new(rimk.outputs[0], b.inputs["Emission Strength"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); GROUND = bpy.context.object; GROUND.scale = (2 * HALF, 2 * HALF, 1); bpy.ops.object.transform_apply(scale=True); GROUND.data.materials.append(gm); GROUND.parent = CITY
add_haze(gm)
far = K.mat("far", (.07, .07, .075), .85); add_haze(far)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -.3)); FAR = bpy.context.object; FAR.scale = (300000, 300000, 1); FAR.data.materials.append(gm); FAR.parent = CITY   # 被害の円が 8 km の外まで届くよう、地面と同じ材料


def set_ground_ring(R, f, rim=0., w=300.):
    key_fac(G_R, R, f); key_fac(G_R2, R, f); key_fac(G_RK, rim, f); G_W.default_value = w


# 窓が割れるビル（l04 の目の前）：窓の板と、落ちるガラス片
FACADE = group("facade"); FACADE.parent = PLAZA; FACADE.location = (60, -55, 0)   # 窓のビルは広場の南東（議事堂の外）。部品の座標は FACADE から
K.box("fac_body", (40, 2, 60), (30, 40, 30), emat("fac", (.16, .17, .19), .5), bevel=0, parent=FACADE)
glass_pane = emat("pane", (.25, .32, .38), .05, .6)
PANES = []
for i in range(10):
    for j in range(14):
        PANES.append(K.box(f"pane{i}_{j}", (3.2, .15, 3.2), (30 - 18 + i * 4, 38.9, 3 + j * 4.1), glass_pane, bevel=0, parent=FACADE))
SHARDS = [K.box(f"shard{i}", (RND.uniform(.2, .6), .03, RND.uniform(.2, .6)), (0, 0, -60), glass_pane, bevel=0, parent=FACADE) for i in range(140)]

# 人（広場）。見上げる人・スマホの人・避難する人
PEOPLE = []
for i in range(46):
    kind = KINDS[i % 8]; x, y = RND.uniform(-10, 40), RND.uniform(-30, 30)
    if abs(x - 4) < 3 and abs(y) < 3:
        x += 6
    PEOPLE.append((person(kind, (x, y, 0), RND.uniform(0, 6.283), PLAZA), person(kind + "_bag", (x, y, -60), 0, PLAZA), (x, y), RND.uniform(0, 6.283)))

# ================================================================ 隕石（空を切る光の筋と、岩）
rock_m = bpy.data.materials.new("rock"); rock_m.use_nodes = True; n = rock_m.node_tree.nodes; L = rock_m.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); rn = n.new("ShaderNodeTexNoise"); rn.inputs["Scale"].default_value = 3.0; rn.inputs["Detail"].default_value = 10; L.new(tc.outputs["Object"], rn.inputs["Vector"])
rcr = n.new("ShaderNodeValToRGB"); L.new(rn.outputs["Fac"], rcr.inputs[0]); rcr.color_ramp.elements[0].color = (.05, .045, .04, 1); rcr.color_ramp.elements[1].color = (.22, .19, .16, 1)
rf = n.new("ShaderNodeTexNoise"); rf.inputs["Scale"].default_value = 40.0; rf.inputs["Detail"].default_value = 12; L.new(tc.outputs["Object"], rf.inputs["Vector"])
rov = n.new("ShaderNodeMix"); rov.data_type = "RGBA"; rov.blend_type = "OVERLAY"; rov.inputs[0].default_value = .6; L.new(rcr.outputs[0], rov.inputs[6]); L.new(rf.outputs["Color"], rov.inputs[7])
L.new(rov.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .95
rhb = n.new("ShaderNodeMath"); rhb.operation = "MULTIPLY_ADD"; rhb.inputs[1].default_value = .35; L.new(rf.outputs["Fac"], rhb.inputs[0]); L.new(rn.outputs["Fac"], rhb.inputs[2])
rbump = n.new("ShaderNodeBump"); rbump.inputs["Strength"].default_value = .9; L.new(rhb.outputs[0], rbump.inputs["Height"]); L.new(rbump.outputs[0], b.inputs["Normal"])
# 熱で光る前の面（法線が進む向きを向いた所ほど橙）。HOT で強さ
gm2 = n.new("ShaderNodeNewGeometry"); dt = n.new("ShaderNodeVectorMath"); dt.operation = "DOT_PRODUCT"; L.new(gm2.outputs["Normal"], dt.inputs[0]); ROCK_DIR = dt.inputs[1]; ROCK_DIR.default_value = (0, 0, -1)
hr = n.new("ShaderNodeMapRange"); hr.inputs[1].default_value = .2; hr.inputs[2].default_value = 1.0; L.new(dt.outputs["Value"], hr.inputs[0])
crk = n.new("ShaderNodeMapRange"); crk.inputs[1].default_value = .42; crk.inputs[2].default_value = .3; L.new(rf.outputs["Fac"], crk.inputs[0])
hk0 = n.new("ShaderNodeMath"); hk0.operation = "MULTIPLY"; L.new(hr.outputs[0], hk0.inputs[0]); L.new(crk.outputs[0], hk0.inputs[1])
hk = n.new("ShaderNodeMath"); hk.operation = "MULTIPLY"; L.new(hk0.outputs[0], hk.inputs[0]); ROCK_HOT = hk.inputs[1]; ROCK_HOT.default_value = 0.
b.inputs["Emission Color"].default_value = (1, .42, .12, 1); L.new(hk.outputs[0], b.inputs["Emission Strength"])


def rock(name, seed):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=1.0); o = bpy.context.object; o.name = name
    rr = random.Random(seed)
    for v in o.data.vertices:   # でこぼこの岩（大きな凹凸＋小さな凹凸）
        p = v.co.copy(); k = 1 + .18 * math.sin(3.1 * p.x + rr.random()) * math.cos(2.3 * p.y) + .1 * math.sin(7 * p.z + 1.3) + .05 * math.sin(13 * p.x * p.y)
        v.co = p * k * Vector((1.0, .82, .9))
    o.data.materials.append(rock_m); bpy.ops.object.shade_smooth(); return o


ROCK = rock("rock", 3)
trail_m = emat("trail", (1, .5, .2), 1, emit=(1, .5, .2), k=0., alpha=.0)
TRAIL_K = esock(trail_m); TRAIL_A = asock(trail_m)
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=1.0, radius2=0.0, depth=1.0); TRAIL = bpy.context.object; TRAIL.data.materials.append(trail_m); TRAIL.visible_shadow = False   # 尾は影を落とさない
# 尾の形：先が原点、+Z（後ろ）へ伸びる
for v in TRAIL.data.vertices:
    v.co.z += .5
smoke_m = emat("smoke", (.32, .29, .26), 1.0, alpha=.55)
_n = smoke_m.node_tree.nodes; _L = smoke_m.node_tree.links; _lw = _n.new("ShaderNodeLayerWeight"); _lw.inputs[0].default_value = .5
_inv = _n.new("ShaderNodeMath"); _inv.operation = "SUBTRACT"; _inv.inputs[0].default_value = 1; _L.new(_lw.outputs["Facing"], _inv.inputs[1])
_sq = _n.new("ShaderNodeMath"); _sq.operation = "POWER"; _sq.inputs[1].default_value = 2.2; _L.new(_inv.outputs[0], _sq.inputs[0])
_am = _n.new("ShaderNodeMath"); _am.operation = "MULTIPLY"; _L.new(_sq.outputs[0], _am.inputs[0]); _L.new(_am.outputs[0], _n["Principled BSDF"].inputs["Alpha"])
SMOKE_A = _am.inputs[1]; SMOKE_A.default_value = .55
fire_m = emat("fire", (.4, .15, .05), 1.0, emit=(1, .4, .12), k=0., alpha=.6); FIRE_K = esock(fire_m)


def balls(n_, m, name, seed):
    rr = random.Random(seed); out = []
    for i in range(n_):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(0, 0, -5000)); o = bpy.context.object; o.name = f"{name}{i}"; o.data.materials.append(m)
        out.append((o, Vector((rr.gauss(0, 1), rr.gauss(0, 1), rr.gauss(0, .6))).normalized(), rr.uniform(.6, 1.0), rr.uniform(.5, 1.1)))
    return out


PUFF = balls(36, smoke_m, "puff", 1)        # 空中の爆発の煙
PUFF_F = balls(14, fire_m, "pufff", 2)     # その内側の、弱い橙
DUST = balls(60, smoke_m, "dust", 3)        # 地面の土煙（ドーム・柱）
DEBRIS = [K.box(f"deb{i}", (RND.uniform(3, 12), RND.uniform(3, 12), RND.uniform(2, 8)), (0, 0, -5000), emat(f"debm{i % 4}", (.12 + .04 * (i % 4), .11, .1), .9), bevel=0) for i in range(80)]
# クレーター（縁の盛り上がり＋暗い底）。大きさは scale で
crater_m = emat("crater", (.05, .035, .03), .95, emit=(1, .3, .08), k=0.); CRATER_K = esock(crater_m)
bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=.16, major_segments=96, minor_segments=16); RIM = bpy.context.object; RIM.scale = (1, 1, .35); RIM.data.materials.append(crater_m)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.0); PIT = bpy.context.object; PIT.scale = (.95, .95, .25); PIT.data.materials.append(emat("pit", (.02, .015, .012), .95))


def place_meteor(head, dirv, L_rock, trail_len, hot, trail_k, f, spin=0.):
    """head：岩の中心、dirv：進む向き（単位）、L_rock：岩の直径（m）、trail_len：尾の長さ"""
    d = Vector(dirv).normalized(); q = (-d).to_track_quat("Z", "Y")
    keyp(ROCK, f, loc=tuple(head), rot=tuple(q.to_euler()), scale=L_rock / 2)
    key_fac(ROCK_DIR, tuple(d), f); key_fac(ROCK_HOT, hot, f)
    keyp(TRAIL, f, loc=tuple(Vector(head)), rot=tuple(q.to_euler()), scale=(L_rock * .55, L_rock * .55, trail_len))
    key_fac(TRAIL_K, trail_k, f); key_fac(TRAIL_A, clamp(trail_k / 3, 0, .85), f)


def hide_meteor(f):
    keyp(ROCK, f, loc=(0, 0, -1e6)); keyp(TRAIL, f, loc=(0, 0, -1e6)); key_fac(TRAIL_K, 0, f); key_fac(TRAIL_A, 0, f)


def burst(center, R, k, f, rise=0., fire=0.):
    """空中の爆発・土煙のドーム：中心、広がり R（m）、k（0→1 の進み）。fire：内側の橙の強さ（閃光にしない弱さ）"""
    c = Vector(center)
    for j, (o, dv, rr, ss) in enumerate(PUFF):
        p = c + dv * R * rr * ease(k) + Vector((0, 0, rise * k * rr)); keyp(o, f, loc=tuple(p), scale=R * .32 * ss * (.4 + .6 * ease(k)))
    for j, (o, dv, rr, ss) in enumerate(PUFF_F):
        p = c + dv * R * .45 * rr * ease(k); keyp(o, f, loc=tuple(p), scale=R * .22 * ss * (.5 + .5 * k))
    key_fac(FIRE_K, fire * (1 - k) ** 1.5, f); key_fac(SMOKE_A, .55 * (1 - .4 * k), f)


def hide_burst(f):
    for o, *_ in PUFF + PUFF_F:
        keyp(o, f, loc=(0, 0, -5000))


def dust_dome(center, R, H, k, f):
    """地面の土煙（横に広がるドームと立ちのぼる柱）"""
    c = Vector(center)
    for j, (o, dv, rr, ss) in enumerate(DUST):
        if j % 3 == 0:   # 柱
            p = c + Vector((dv.x * R * .15, dv.y * R * .15, H * rr * ease(k))); sz = R * .22 * ss
        else:            # 横に広がる輪
            hv = Vector((dv.x, dv.y, 0)).normalized(); p = c + hv * R * rr * ease(k) + Vector((0, 0, R * .08 * ss)); sz = R * .18 * ss * (.3 + .7 * k)
        keyp(o, f, loc=tuple(p), scale=sz)


def hide_dust(f):
    for o, *_ in DUST:
        keyp(o, f, loc=(0, 0, -5000))
    for o in DEBRIS:
        keyp(o, f, loc=(0, 0, -5000))


# ================================================================ 地図（関東・日本）：被害の円が広がり、中の街の光が消える
def map_plane(name):
    inf = INFO[name]
    m = bpy.data.materials.new("map_" + name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")

    def T(key):
        t_ = n.new("ShaderNodeTexImage"); t_.image = img(f"{name}_{key}"); t_.interpolation = "Cubic"; L.new(tc.outputs["UV"], t_.inputs["Vector"]); return t_
    land, pop = T("land"), T("pop")
    # 都庁からの距離（m）：UV（0〜1）→ 地図の大きさ
    sp = n.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["UV"], sp.inputs[0])
    def axis(i, size):
        a = n.new("ShaderNodeMath"); a.operation = "MULTIPLY_ADD"; a.inputs[1].default_value = size; a.inputs[2].default_value = -size / 2; L.new(sp.outputs[i], a.inputs[0]); return a.outputs[0]
    cb = n.new("ShaderNodeCombineXYZ"); L.new(axis(0, inf["x1"] - inf["x0"]), cb.inputs[0]); L.new(axis(1, inf["y1"] - inf["y0"]), cb.inputs[1])
    ln = n.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; L.new(cb.outputs[0], ln.inputs[0])
    inside = n.new("ShaderNodeMath"); inside.operation = "LESS_THAN"; L.new(ln.outputs["Value"], inside.inputs[0]); R_ = inside.inputs[1]; R_.default_value = 0.
    # 縁の帯
    d1 = n.new("ShaderNodeMath"); d1.operation = "SUBTRACT"; L.new(ln.outputs["Value"], d1.inputs[0]); R2 = d1.inputs[1]
    d2 = n.new("ShaderNodeMath"); d2.operation = "ABSOLUTE"; L.new(d1.outputs[0], d2.inputs[0])
    d3 = n.new("ShaderNodeMapRange"); d3.inputs[1].default_value = 0; W_ = d3.inputs[2]; W_.default_value = 3000; d3.inputs[3].default_value = 1; d3.inputs[4].default_value = 0; L.new(d2.outputs[0], d3.inputs[0])
    # 陸と海の色（円の中の陸は焦げた赤茶）
    col = n.new("ShaderNodeMix"); col.data_type = "RGBA"; L.new(land.outputs["Color"], col.inputs[0]); col.inputs[6].default_value = (.004, .007, .016, 1); col.inputs[7].default_value = (.07, .085, .11, 1)
    burnt = n.new("ShaderNodeMix"); burnt.data_type = "RGBA"; L.new(inside.outputs[0], burnt.inputs[0]); L.new(col.outputs[2], burnt.inputs[6]); burnt.inputs[7].default_value = (.07, .025, .015, 1)
    L.new(burnt.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .7
    il = n.new("ShaderNodeMath"); il.operation = "MULTIPLY"; L.new(inside.outputs[0], il.inputs[0]); L.new(land.outputs["Color"], il.inputs[1])
    # 光：人の光（円の中は消える）＋縁の橙
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1; L.new(inside.outputs[0], inv.inputs[1])
    pk = n.new("ShaderNodeMath"); pk.operation = "MULTIPLY"; L.new(pop.outputs["Color"], pk.inputs[0]); L.new(inv.outputs[0], pk.inputs[1])
    m1 = n.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1; L.new(pk.outputs[0], m1.inputs[6]); m1.inputs[7].default_value = (.36, .26, .16, 1)
    rk = n.new("ShaderNodeMath"); rk.operation = "MULTIPLY"; L.new(d3.outputs[0], rk.inputs[0]); RK = rk.inputs[1]; RK.default_value = 0.
    m2 = n.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1; L.new(rk.outputs[0], m2.inputs[6]); m2.inputs[7].default_value = (1.0, .36, .08, 1)
    wc = n.new("ShaderNodeMix"); wc.data_type = "RGBA"; wc.blend_type = "ADD"; wc.inputs[0].default_value = 1; L.new(m1.outputs[2], wc.inputs[6]); L.new(m2.outputs[2], wc.inputs[7])
    m3 = n.new("ShaderNodeMix"); m3.data_type = "RGBA"; m3.blend_type = "MULTIPLY"; m3.inputs[0].default_value = 1; L.new(il.outputs[0], m3.inputs[6]); m3.inputs[7].default_value = (.09, .025, .01, 1)
    wc2 = n.new("ShaderNodeMix"); wc2.data_type = "RGBA"; wc2.blend_type = "ADD"; wc2.inputs[0].default_value = 1; L.new(wc.outputs[2], wc2.inputs[6]); L.new(m3.outputs[2], wc2.inputs[7])
    L.new(wc2.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.6
    bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.object; p.name = "map_" + name
    p.scale = (inf["x1"] - inf["x0"], inf["y1"] - inf["y0"], 1); p.location = (0, 0, 0); p.data.materials.append(m)
    return dict(obj=p, R=R_, R2=R2, W=W_, RK=RK)


MAPK = map_plane("kanto"); MAPJ = map_plane("japan")
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -50)); OCEAN = bpy.context.object; OCEAN.scale = (4e7, 4e7, 1); OCEAN.data.materials.append(emat("ocean", (.004, .007, .016), .35))
CITIES = INFO["cities"]


def key_map(M_, R, f, rim=4.0, w=None):
    key_fac(M_["R"], R, f); key_fac(M_["R2"], R, f); key_fac(M_["RK"], rim, f)
    if w:
        M_["W"].default_value = w


# ================================================================ 名古屋城（模式）と、迫る土煙の壁
NAGOYA = group("nagoya")
white = emat("lm_white", (.82, .82, .8), .7); roofg = emat("roof_green", (.12, .3, .26), .5, .3); gold = emat("gold", (.95, .68, .22), .3, 1.0)
stone = emat("lm_stone", (.36, .35, .33), .9); gravel = emat("gravel", (.42, .4, .36), .95); dkwin = emat("lm_win", (.03, .04, .04), .2)
K.box("ng_ground", (2000, 2000, .2), (0, 0, -.1), gravel, bevel=0, parent=NAGOYA)


def pyramid(name, w, h, z, m, parent, d=None, x=0., y=0.):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w / math.sqrt(2), radius2=0, depth=h, location=(x, y, z + h / 2), rotation=(0, 0, math.pi / 4))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    if d:
        o.scale = (1, d / w, 1)
    o.parent = parent; return o


NX, NY = 0.0, 120.0
K.box("ng_base", (56, 50, 18), (NX, NY, 9), stone, bevel=.5, parent=NAGOYA)
z = 18.0; TILES_SRC = []
for i, w in enumerate([40, 34, 27, 21, 16]):
    hgt = 8.0 if i < 4 else 9.0
    K.box(f"ng_wall{i}", (w, w * .8, hgt), (NX, NY, z + hgt / 2), white, bevel=.1, parent=NAGOYA)
    nw = max(2, w // 6)
    for j in range(nw):
        K.box(f"ng_win{i}_{j}", (1.6, w * .8 + .3, 1.4), (NX - w / 2 + 3 + j * (w - 6) / max(1, nw - 1), NY, z + hgt * .5), dkwin, bevel=0, parent=NAGOYA)
    TILES_SRC.append(pyramid(f"ng_roof{i}", w + 7, 4.0 if i < 4 else 6.5, z + hgt - .4, roofg, NAGOYA, d=(w + 7) * .8, x=NX, y=NY))
    z += hgt + (2.2 if i < 4 else 0)
SHACHI = [K.box(f"ng_shachi{sx}", (1.2, .9, 2.6), (NX + sx, NY, z + 4.3), gold, bevel=.25, parent=NAGOYA) for sx in (-3.5, 3.5)]
NG_TREES = []
for k in range(40):
    x, y = RND.uniform(-160, 160), RND.uniform(-60, 60)
    if (abs(x) < 40 and y > 0) or (-60 < x < 30 and y < 110):
        continue
    t1 = K.tube((x, y, 0), (x, y, 5), .35, trunk_m, NAGOYA, 8); bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=4.5, location=(x, y, 8)); t2 = bpy.context.object; t2.data.materials.append(tree_m); t2.parent = NAGOYA
    NG_TREES.append((t1, t2, x, y))
TILES = [K.box(f"tile{i}", (RND.uniform(.4, 1.2), RND.uniform(.4, 1.2), .12), (0, 0, -60), roofg, bevel=0, parent=NAGOYA) for i in range(90)]
NAGOYA.location = (0, 0, -900)

# ================================================================ 宇宙（1 単位＝1,000 km）
SPACE = group("space")
em_ = bpy.data.materials.new("earth47"); em_.use_nodes = True; n = em_.node_tree.nodes; L = em_.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); enz = n.new("ShaderNodeTexNoise"); enz.inputs["Scale"].default_value = .32; enz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], enz.inputs["Vector"])
ecr = n.new("ShaderNodeValToRGB"); L.new(enz.outputs["Fac"], ecr.inputs[0]); e = ecr.color_ramp.elements
e[0].position, e[0].color = .52, (.01, .05, .2, 1); e[1].position, e[1].color = .54, (.12, .25, .08, 1); el = e.new(.66); el.color = (.42, .36, .22, 1)
# 海が干上がる（DRY：0→1 で海の色が灰色の海底に）
dry = n.new("ShaderNodeMix"); dry.data_type = "RGBA"; DRY = dry.inputs[0]; DRY.default_value = 0.; L.new(ecr.outputs[0], dry.inputs[6]); dry.inputs[7].default_value = (.2, .17, .14, 1)
# 衝突の跡（東京の位置を中心にした、焼けた円）と、地球を回る爆風の輪
geo = n.new("ShaderNodeNewGeometry"); nrm = n.new("ShaderNodeVectorMath"); nrm.operation = "NORMALIZE"; L.new(tc.outputs["Object"], nrm.inputs[0])
dot = n.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"; L.new(nrm.outputs[0], dot.inputs[0]); TOKYO_V = dot.inputs[1]
ang = n.new("ShaderNodeMath"); ang.operation = "ARCCOSINE"; L.new(dot.outputs["Value"], ang.inputs[0])
inn = n.new("ShaderNodeMath"); inn.operation = "LESS_THAN"; L.new(ang.outputs[0], inn.inputs[0]); BURN_A = inn.inputs[1]; BURN_A.default_value = 0.
bmx = n.new("ShaderNodeMix"); bmx.data_type = "RGBA"; L.new(inn.outputs[0], bmx.inputs[0]); L.new(dry.outputs[2], bmx.inputs[6]); bmx.inputs[7].default_value = (.06, .03, .02, 1)
L.new(bmx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .6
rg1 = n.new("ShaderNodeMath"); rg1.operation = "SUBTRACT"; L.new(ang.outputs[0], rg1.inputs[0]); RING_A = rg1.inputs[1]; RING_A.default_value = 0.
rg2 = n.new("ShaderNodeMath"); rg2.operation = "ABSOLUTE"; L.new(rg1.outputs[0], rg2.inputs[0])
rg3 = n.new("ShaderNodeMapRange"); rg3.inputs[1].default_value = 0; rg3.inputs[2].default_value = .045; rg3.inputs[3].default_value = 1; rg3.inputs[4].default_value = 0; L.new(rg2.outputs[0], rg3.inputs[0])
rgk = n.new("ShaderNodeMath"); rgk.operation = "MULTIPLY"; L.new(rg3.outputs[0], rgk.inputs[0]); RING_K = rgk.inputs[1]; RING_K.default_value = 0.
spot = n.new("ShaderNodeMapRange"); spot.inputs[1].default_value = 0; SPOT_A = spot.inputs[2]; SPOT_A.default_value = .001; spot.inputs[3].default_value = 1; spot.inputs[4].default_value = 0; L.new(ang.outputs[0], spot.inputs[0])
spk = n.new("ShaderNodeMath"); spk.operation = "MULTIPLY"; L.new(spot.outputs[0], spk.inputs[0]); SPOT_K = spk.inputs[1]; SPOT_K.default_value = 0.
eadd = n.new("ShaderNodeMath"); eadd.operation = "ADD"; L.new(rgk.outputs[0], eadd.inputs[0]); L.new(spk.outputs[0], eadd.inputs[1])
b.inputs["Emission Color"].default_value = (1, .4, .1, 1); L.new(eadd.outputs[0], b.inputs["Emission Strength"])
RE_U = 6.371
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=RE_U, location=(0, 0, 0)); EARTH = bpy.context.object; EARTH.data.materials.append(em_); EARTH.parent = SPACE; bpy.ops.object.shade_smooth()
cm_ = emat("cloud47", (1, 1, 1), 1, alpha=.0); cn = cm_.node_tree.nodes; cl = cm_.node_tree.links; cb = cn["Principled BSDF"]
ctc = cn.new("ShaderNodeTexCoord"); cnz = cn.new("ShaderNodeTexNoise"); cnz.inputs["Scale"].default_value = .9; cnz.inputs["Detail"].default_value = 10; cl.new(ctc.outputs["Object"], cnz.inputs["Vector"])
crg = cn.new("ShaderNodeMapRange"); CLOUD_LO = crg.inputs[1]; CLOUD_LO.default_value = .5; crg.inputs[2].default_value = .62; cl.new(cnz.outputs["Fac"], crg.inputs[0]); cl.new(crg.outputs[0], cb.inputs["Alpha"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=128, ring_count=64, radius=RE_U * 1.012, location=(0, 0, 0)); CLOUDS = bpy.context.object; CLOUDS.data.materials.append(cm_); CLOUDS.parent = SPACE; bpy.ops.object.shade_smooth()
# 東京の向き（地球の物体の座標で）。カメラはここを中心に見る
TOKYO = Vector((math.cos(math.radians(35.69)) * math.cos(math.radians(139.69 - 100)), math.cos(math.radians(35.69)) * math.sin(math.radians(139.69 - 100)), math.sin(math.radians(35.69)))).normalized()
TOKYO_V.default_value = tuple(TOKYO)
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=1.7375, location=(0, 0, -900)); MOON = bpy.context.object; MOON.data.materials.append(emat("moon", (.45, .44, .42), .9)); MOON.parent = SPACE
bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=32, radius=3.396, location=(0, 0, -900)); MARS = bpy.context.object; MARS.data.materials.append(emat("mars", (.55, .25, .12), .9)); MARS.parent = SPACE
# 砕けた地球のかけら
EFRAG = []
core_m = emat("core", (.12, .04, .02), .8, emit=(1, .35, .08), k=0.); CORE_K = esock(core_m)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=RE_U * .55, location=(0, 0, -900)); CORE = bpy.context.object; CORE.data.materials.append(core_m); CORE.parent = SPACE
for i in range(260):
    dv = Vector((RND.gauss(0, 1), RND.gauss(0, 1), RND.gauss(0, 1))).normalized()
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(.25, .9), location=(0, 0, -900)); o = bpy.context.object
    o.data.materials.append(em_ if RND.random() < .55 else core_m); o.parent = SPACE; EFRAG.append((o, dv, RND.uniform(.75, 1.0), RND.uniform(.5, 1.6)))
STAR_M = emat("star", (1, 1, 1), 1, emit=(1, 1, 1), k=20)
for i in range(400):
    v = Vector((RND.gauss(0, 1), RND.gauss(0, 1), RND.gauss(0, 1))).normalized() * 900
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(.6, 1.6), location=v); o = bpy.context.object; o.data.materials.append(STAR_M); o.parent = SPACE
SPACE.location = (0, 0, -1e5)

# ================================================================ 表示の切り替え
INIT = {o.name: (o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for o in bpy.data.objects}
MATS = [glass, gm, rock_m, trail_m, smoke_m, fire_m, crater_m, em_, cm_, core_m, MAPK["obj"].data.materials[0], MAPJ["obj"].data.materials[0]]


def hide_tree(o, h):
    o.hide_render = h
    for c in o.children_recursive:
        c.hide_render = h


def reset_all():
    for o in bpy.data.objects:
        if o.name in INIT and o is not cam.o:
            o.animation_data_clear(); l_, r_, s_ = INIT[o.name]; o.location = l_; o.rotation_euler = r_; o.scale = s_
    for m in MATS:
        if m.node_tree.animation_data:
            m.node_tree.animation_data_clear()
    for s_, v in [(G_R, 0.), (G_R2, 0.), (G_RK, 0.), (ROCK_HOT, 0.), (TRAIL_K, 0.), (TRAIL_A, 0.), (FIRE_K, 0.), (CRATER_K, 0.), (WIN_K.inputs[1], 0.),
                  (DRY, 0.), (BURN_A, 0.), (RING_K, 0.), (RING_A, 0.), (SPOT_K, 0.), (CORE_K, 0.), (CLOUD_LO, .5), (MAPK["RK"], 0.), (MAPJ["RK"], 0.)]:
        s_.default_value = v
    for o in [ROCK, TRAIL, RIM, PIT] + [x[0] for x in PUFF + PUFF_F + DUST] + DEBRIS:
        o.location = (0, 0, -1e6)


def show(where, tod="day"):
    """where：plaza（広場と新宿）・city（新宿だけ）・kanto・japan・nagoya・space"""
    reset_all()
    hide_tree(CITY, where not in ("plaza", "city")); hide_tree(PLAZA, where != "plaza")
    MAPK["obj"].hide_render = where != "kanto"; MAPJ["obj"].hide_render = where != "japan"; OCEAN.hide_render = where not in ("kanto", "japan")
    NAGOYA.location = (0, 0, 0) if where == "nagoya" else (0, 0, -900); hide_tree(NAGOYA, where != "nagoya")
    SPACE.location = (0, 0, 0) if where == "space" else (0, 0, -1e5); hide_tree(SPACE, where != "space")
    for o in (MOON, MARS, CORE):
        o.location = (0, 0, -900)
    cam.o.data.dof.use_dof = False; cam.o.data.clip_start = .0005 if where == "space" else .05
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
    if where in ("kanto", "japan"):
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sky.set(0, -12, 160, 0.0); set_haze((0, 0, 0), 0.); sc.view_settings.exposure = -.4
    elif where == "space":
        sky.set(0, -20, 160, 0.0); set_haze((0, 0, 0), 0.); sky.sun.data.energy = 4.0
        sd = (TOKYO * .8 + TOKYO.cross(Vector((0, 0, 1))).normalized() * .45 + Vector((0, 0, .35))).normalized()
        sky.sun.rotation_euler = (-sd).to_track_quat("-Z", "Y").to_euler(); sc.view_settings.exposure = -.6
    elif tod == "day":   # 曇りの正午（暗めの色調）
        sky.set(0, 80, 180, 1.4); set_haze((.42, .46, .52), 1.0); sc.view_settings.exposure = -1.2
    elif tod == "dust":  # 土煙の空（茶色くかすむ）
        sky.set(0, 40, 180, .8); set_haze((.2, .14, .1), .8); sc.view_settings.exposure = -1.0


# ---------------------------------------------------------------- 隕石の通り道（地上の場面）：北東の空から 45 度で都庁へ
ENTRY = Vector((.66, -.26, -.707)).normalized()   # 進む向き：北西の空から南東へ（広場のカメラから見て都庁の向こうの空）
TARGET = Vector((-112, 0, 0))                    # 都庁
CAMP = Vector((330, -120, 1.6))                  # 広場のカメラ（都庁まで約 450 m）
AZ = Vector((-.95, .3, 0))                      # 広場のカメラから、都庁と隕石の空の向き


def sky_point(alt, aim=TARGET):
    """通り道の上で、高さ alt（m）の点"""
    return aim - ENTRY * (alt / -ENTRY.z)


def sky_path(k, alt0, alt1):
    """1〜7 日目の流れ星（上空で燃え尽きる）：広場のカメラから見て、右上から左下へ空を横切る道。k：0→1。戻り値（頭の位置, 進む向き）"""
    a = AZ.normalized(); side = Vector((a.y, -a.x, 0))
    p0 = CAMP + a * 90000 + side * 35000 + Vector((0, 0, alt0)); p1 = CAMP + a * 95000 + side * 8000 + Vector((0, 0, alt1))
    return p0 + (p1 - p0) * k, (p1 - p0).normalized()


def look_dir(pos, az, pitch, lens, roll=0.):
    """az：向き（x 東・y 北）、pitch：見上げる角度（度）"""
    h = Vector((az[0], az[1], 0)).normalized(); d = h * math.cos(math.radians(pitch)) + Vector((0, 0, math.sin(math.radians(pitch))))
    cam.look(tuple(pos), tuple(Vector(pos) + d * 1000), lens, roll)


def face(dx, dy):
    """人の前（-Y）を (dx, dy) に向ける回転"""
    return math.atan2(dx, -dy)


# ================================================================ ショット
def s_l00():
    show("plaza", "dust"); WIN_K.inputs[1].default_value = 1.5
def a_l00(u, t, f):   # 28 日目：新宿の空を覆う岩の底（地平線から上がほとんど岩）。地面から見上げる
    R = 60000.0; z = 7000 - 900 * u; c = CAMP + AZ.normalized() * 26000
    keyp(ROCK, f, loc=(c.x, c.y, z + R * .9), rot=(.3, .2, t * .02), scale=R)
    key_fac(ROCK_DIR, (0, 0, -1), f); key_fac(ROCK_HOT, 3 + 2 * u, f)
    keyp(TRAIL, f, loc=(0, 0, -1e6))
    look_dir(CAMP + shake(f, .25 * u, 3), AZ, 30 + 6 * ease(u), 18)

def s_l01():
    show("plaza")
def a_l01(u, t, f):   # 1 日目：正午の広場。昼の空に小さな光の筋（10 cm、上空 56 km で燃え尽きる）。誰も気づかない
    for (p0, p1, (x, y), hd) in PEOPLE:
        keyp(p0, f, loc=(x + .3 * math.sin(t + x), y, 0), rot=(0, 0, hd)); keyp(p1, f, loc=(x, y, -60))
    e = t - 2.0; k = clamp((e + 1.0) / 1.4)
    if -1.0 < e < .4:
        head, dv = sky_path(k, 80000, 56000); place_meteor(head, dv, 800, 16000 * (.3 + k), 0., 5.0 * math.sin(math.pi * clamp(k)), f)
    else:
        hide_meteor(f)
    look_dir(CAMP + Vector((0, 0, .1 * u)), AZ, 21 + 2 * ease(u), 30)

def s_l02():
    show("plaza")
def a_l02(u, t, f):   # 2〜6 日目：毎日の正午に 1 本ずつ（1 日 1 秒）、光の筋が太くなる。人々は空を見上げる
    days = [(.5 + i, d) for i, d in enumerate(range(2, 7))]
    on = [(tt, d) for tt, d in days if -.45 < t - tt < .45]
    look = clamp((t - 1.5) / 1.5); H2 = face(-.66, .26)
    for (p0, p1, (x, y), hd) in PEOPLE:
        keyp(p0, f, loc=(x, y, 0), rot=(0, 0, hd + (H2 - hd) * look)); keyp(p1, f, loc=(x, y, -60))
    if on:
        tt, d = on[-1]; k = clamp((t - tt + .45) / .9); L_ = DAYS[d]["L_m"]
        head, dv = sky_path(k, 80000, DAYS[d]["burst_m"]); place_meteor(head, dv, 800 * (L_ / .1) ** .3, 16000 * (.4 + k) * (L_ / .1) ** .15, 2. * (d >= 4), 4.0 + 1.0 * d, f)
    else:
        hide_meteor(f)
    look_dir(CAMP + Vector((-6 * ease(u), 4 * ease(u), 0)), AZ, 22, 30)

def s_l03():
    show("plaza")
def a_l03(u, t, f):   # 7 日目：上空 36 km で爆発。煙の玉がゆっくり広がる。人々が見上げる
    e = t - ev_t("l03", 0)
    H2 = face(-.66, .26)
    for (p0, p1, (x, y), hd) in PEOPLE:
        keyp(p0, f, loc=(x, y, 0), rot=(0, 0, H2)); keyp(p1, f, loc=(x, y, -60))
    if e < 0:
        k = clamp((e + .7) / .7); head, dv = sky_path(k, 80000, DAYS[7]["burst_m"]); place_meteor(head, dv, 2500, 30000, 3., 6., f); hide_burst(f)
    else:
        hide_meteor(f); burst(sky_path(1, 80000, DAYS[7]["burst_m"])[0], 9000, clamp(e / 2.0), f, rise=1500, fire=2.5)
    look_dir(CAMP + Vector((-4, 3, 0)) + shake(f, .05 * clamp(1 - abs(e - .5)), 1), AZ, 21, 28)

def s_l04():
    show("plaza")
def a_l04(u, t, f):   # 8〜9 日目：目の前のビルの窓が震えて割れる → 荷物を持った人々が駅へ（避難）
    e = t - ev_t("l04", 0) + .1   # 9 日目の爆風が届く
    for i, o in enumerate(SHARDS):
        r = random.Random(i); pi_ = PANES[r.randrange(len(PANES))]; te = max(0, e - r.uniform(0, .3))
        p = Vector(pi_.location) + Vector((r.uniform(-1.5, 1.5), -.2, r.uniform(-1.5, 1.5))) + Vector((r.uniform(-1, 1), -r.uniform(3, 8), r.uniform(0, 3))) * te + Vector((0, 0, -4.9 * te * te))
        keyp(o, f, loc=(p.x, p.y, max(.05, p.z)) if e > 0 else (0, 0, -60), rot=(te * 9 + i, te * 7, i * .3))
    for j, pn in enumerate(PANES):
        r = random.Random(j + 500); keyp(pn, f, loc=tuple(Vector(INIT[pn.name][0]) + (shake(f, .12, j) if 0 < e < .5 else Vector())), scale=(1, 1, 1) if (e < 0 or r.random() < .35) else (0.001, 1, .001))
    walk = clamp((t - 2.0) / 1.4)
    for i, (p0, p1, (x, y), hd) in enumerate(PEOPLE):
        if walk <= 0:
            keyp(p0, f, loc=(x, y, 0), rot=(0, 0, hd)); keyp(p1, f, loc=(x, y, -60))
        else:   # 荷物を引いて、西（駅の方向）へ
            keyp(p0, f, loc=(x, y, -60)); keyp(p1, f, loc=(x - 2.2 * (t - 2.0), y, 0), rot=(0, 0, -math.pi / 2))
    hit = clamp(1 - abs(e - .15) / .4)
    cam.look(tuple(Vector(mix((112, -49, 2.0), (108, -53, 2.4), ease(u))) + shake(f, .12 * hit, 2)), (90, -15, 14 - 6 * ease(u)), 24)

def s_l05():
    show("plaza", "dust"); hide_tree(PLAZA, False); sc.view_settings.exposure = -.45
    for (p0, p1, *_ ) in PEOPLE:
        p0.location = p1.location = (0, 0, -60)
GZ = Vector((-112, 0, 0))   # 爆心（都庁の真下）
ZAX = Vector((0, 0, 1))


def topple(o, h, theta, sink=0.):
    """ビルを、爆心と反対の側の根もとを軸に倒す（theta：倒れる角度）"""
    x0, y0, _ = INIT[o.name][0]; d = Vector((x0 - GZ.x, y0 - GZ.y, 0)); d = d.normalized() if d.length > 1 else Vector((1, 0, 0))
    w = min(o.dimensions.x, o.dimensions.y) / 2; R = Matrix.Rotation(theta, 3, ZAX.cross(d))
    pivot = Vector((x0, y0, -sink)) + d * w; c = pivot + R @ (-d * w + ZAX * h / 2)
    keyp(o, f_now[0], loc=tuple(c), rot=tuple(R.to_euler()))


f_now = [0]


def a_l05(u, t, f):   # 10 日目：人のいない新宿。上空 7 km の爆発 → 衝撃波が地面を走り、ビルが爆心と反対へ次々に倒れる
    f_now[0] = f
    e = t - ev_t("l05", 0); c = GZ + Vector((0, 0, DAYS[10]["burst_m"]))
    if e < 0:
        k = clamp((e + .7) / .7); place_meteor(c - ENTRY * 20000 * (1 - k), ENTRY, 3000, 24000, 4., 7., f); hide_burst(f)
    else:
        hide_meteor(f); burst(c, 3500, clamp(e / 2.6), f, rise=2000, fire=2.0)
    R = 1300 * ease(clamp((e - .7) / 1.4))   # 衝撃波の前線（地面）
    for j, (o, h, tilt) in enumerate(TOWERS):
        x0, y0, _ = INIT[o.name][0]; r = math.hypot(x0 - GZ.x, y0 - GZ.y); th = .7 + 1.4 * (r / 1300) ** .8
        topple(o, h, 1.45 * ease(clamp((e - th) / .7)) + tilt * .05, sink=.06 * h * ease(clamp((e - th - .4) / .6)))
    k = ease(clamp((e - .7) / 1.0)); keyp(TOCHO, f, loc=(0, 0, -160 * k), rot=(0, .12 * k, 0))
    for j, (o, dv, rr, ss) in enumerate(DUST):   # 地面を走る土煙の輪
        a_ = j / len(DUST) * 6.283; rad = R * (.85 + .15 * rr)
        keyp(o, f, loc=(GZ.x + rad * math.cos(a_), GZ.y + rad * math.sin(a_), 25 * ss) if R > 30 else (0, 0, -5000), scale=45 * ss + R * .02)
    for i, o in enumerate(DEBRIS):   # ビルの上から飛ぶ破片
        rr = random.Random(i); tw, h, _ = TOWERS[rr.randrange(len(TOWERS))]; x0, y0, _ = INIT[tw.name][0]
        r = math.hypot(x0 - GZ.x, y0 - GZ.y); th = .7 + 1.4 * (r / 1300) ** .8 + rr.uniform(0, .3); te = e - th
        d = Vector((x0 - GZ.x, y0 - GZ.y, 0)).normalized(); v = d * rr.uniform(60, 140) + Vector((0, 0, rr.uniform(20, 60)))
        p_ = Vector((x0, y0, h * rr.uniform(.6, 1.0))) + v * te + Vector((0, 0, -40 * te * te))
        keyp(o, f, loc=(p_.x, p_.y, max(2, p_.z)) if te > 0 else (0, 0, -5000), rot=(te * 5 + i, te * 3, i))
    tgt = Vector(mix(tuple(c), (-112, 0, 140), ease(clamp((e - .4) / .7))))
    hit = clamp(1 - abs(R - 1250) / 200) if R > 1000 else 0.
    cam.look(tuple(Vector((1100, -900, 140)) + shake(f, 2.0 * hit, 4)), tuple(tgt), 24)

def s_l06():
    show("city", "dust"); hide_tree(TOCHO, True)
    for (o, h, _) in TOWERS:
        o.location = (o.location.x, o.location.y, -h * .45)
def a_l06(u, t, f):   # 11 日目：初めて地面に届く（102 m）。都庁があった所にクレーター 1.6 km。土煙のドーム
    e = t - ev_t("l06", 0); c = Vector((-112, 0, 0)); Dkm = DAYS[11]["crater_km"] * 1000
    if e < 0:
        k = clamp((e + .55) / .55); head = c - ENTRY * (14000 * (1 - k) + 60); place_meteor(head, ENTRY, 900, 12000, 6., 8., f)
    else:
        hide_meteor(f)
    kk = ease(clamp(e / .9))
    keyp(RIM, f, loc=(c.x, c.y, 0) if e > 0 else (0, 0, -1e6), scale=(Dkm / 2 * kk + 1, Dkm / 2 * kk + 1, Dkm / 2 * .35 * kk + 1))
    keyp(PIT, f, loc=(c.x, c.y, 2) if e > 0 else (0, 0, -1e6), scale=(Dkm / 2 * .95 * kk + 1, Dkm / 2 * .95 * kk + 1, Dkm * .06 * kk + 1))
    key_fac(CRATER_K, 3.0 * clamp(1 - e / 2.5) if e > 0 else 0., f)
    dust_dome(c, 2600, 2200, clamp(e / 2.2) if e > 0 else 0., f)
    set_ground_ring(Dkm * .5 + 4500 * ease(clamp(e / 2.0)) if e > 0 else 0., f, rim=0.)
    hit = clamp(1 - abs(e) / .7)
    cam.look(tuple(Vector(mix((5200, -6800, 1500), (5600, -7400, 1900), ease(u))) + shake(f, 18 * hit, 5)), (-200, 0, 300), 30)

def s_l07():
    show("city", "dust"); hide_tree(TOCHO, True)
    for (o, h, _) in TOWERS:
        o.location = (o.location.x, o.location.y, -h)
def a_l07(u, t, f):   # 12〜13 日目：カメラが上がる。被害の円（ビルが崩れる 31 km → 66 km）が街に広がる
    c = Vector((-112, 0, 0)); e1, e2 = t - ev_t("l07", 0), t - ev_t("l07", 1)
    d12, d13 = DAYS[12], DAYS[13]
    if e2 >= 0:
        R = d12["bldg_km"] * 1000 + (d13["bldg_km"] - d12["bldg_km"]) * 1000 * ease(clamp(e2 / 1.0)); Dk = d13["crater_km"] * 1000
    else:
        R = d12["bldg_km"] * 1000 * ease(clamp(e1 / 1.0)) if e1 > 0 else 0.; Dk = d12["crater_km"] * 1000
    set_ground_ring(R, f, rim=6.0, w=900 + R * .02)
    keyp(RIM, f, loc=(c.x, c.y, 0), scale=(Dk / 2, Dk / 2, Dk / 2 * .35)); keyp(PIT, f, loc=(c.x, c.y, 2), scale=(Dk / 2 * .95, Dk / 2 * .95, Dk * .06))
    alt = 9000 * (60000 / 9000) ** ease(u)
    cam.look((alt * .25, -alt * .7, alt), (0, 0, 0), 30)

def s_l08():
    show("japan")
def a_l08(u, t, f):   # 14 日目：関東の地図。被害の円（窓ガラスが割れる 403 km）が関東を覆い、中の街の光が消える
    e = t - ev_t("l08", 0); d13, d14 = DAYS[13], DAYS[14]
    R = (d13["glass_km"] + (d14["glass_km"] - d13["glass_km"]) * ease(clamp(e / 1.6))) * 1000 if e > 0 else d13["glass_km"] * 1000
    key_map(MAPJ, R, f, rim=5.0, w=9000)
    cam.look(mix((0, -520000, 700000), (0, -620000, 850000), ease(u)), (0, 20000, 0), 30)

def s_l09():
    show("nagoya", "dust"); sc.view_settings.exposure = -.8
def a_l09(u, t, f):   # 15 日目：名古屋城に爆風が届く。土煙の壁が東から迫り、木がしなり、瓦が飛ぶ
    e = t - ev_t("l09", 0) - .3; k = clamp(e / 1.2)
    for j, (o, dv, rr, ss) in enumerate(DUST):   # 土煙の壁（東から）
        x = 600 - 800 * ease(clamp((t - .1) / 1.5)) + dv.x * 60; keyp(o, f, loc=(x, NY + dv.y * 260, 30 + abs(dv.z) * 120 * rr), scale=60 * ss)
    for (t1, t2, x, y) in NG_TREES:
        w_ = clamp((e - (200 - x) / 400) / .4); keyp(t2, f, loc=(x - 3 * w_, y, 8 - .6 * w_)); keyp(t1, f, rot=(0, -.25 * w_, 0))
    for i, o in enumerate(TILES):
        r = random.Random(i); te = max(0, e - r.uniform(0, .6)); src = TILES_SRC[r.randrange(len(TILES_SRC))]
        p0 = Vector((NX + r.uniform(-14, 14), NY + r.uniform(-12, 12), src.location.z + r.uniform(0, 2)))
        p = p0 + Vector((-r.uniform(18, 40), r.uniform(-6, 6), r.uniform(2, 8))) * te + Vector((0, 0, -4.9 * te * te))
        keyp(o, f, loc=tuple(p) if te > 0 else (0, 0, -60), rot=(te * 8 + i, te * 6, i))
    for j, s_ in enumerate(SHACHI):
        te = max(0, e - .4); keyp(s_, f, loc=tuple(Vector(INIT[s_.name][0]) + Vector((-14 * te, 0, 3 * te - 4.9 * te * te))) if te > 0 else INIT[s_.name][0], rot=(te * 4, 0, 0))
    hit = clamp(1 - abs(e) / .6)
    cam.look(tuple(Vector(mix((-34, -30, 3), (-30, -24, 3.5), ease(u))) + shake(f, .5 * hit, 6)), (NX, NY, 40), 26)

def s_l10():
    show("japan")
def a_l10(u, t, f):   # 16 日目：日本の地図。被害の円（1,619 km）が日本を覆う。最後は石垣島まで（次の日の円）
    e = t - ev_t("l10", 0); d15, d16, d17 = DAYS[15], DAYS[16], DAYS[17]
    if e < 0:
        R = d15["glass_km"] * 1000
    else:
        R = (d15["glass_km"] + (d16["glass_km"] - d15["glass_km"]) * ease(clamp(e / 1.3))) * 1000
    key_map(MAPJ, R, f, rim=5.0, w=25000)
    cam.look(mix((-300000, -2600000, 2700000), (-500000, -2900000, 3300000), ease(u)), (-300000, -150000, 0), 30)

# 宇宙のカメラ：東京の真上の向き（TOKYO）から見る
def tokyo_cam(dist, side=.0, up=.25, lens=35, look_off=Vector()):
    t_ = TOKYO; s_ = t_.cross(Vector((0, 0, 1))).normalized(); u_ = s_.cross(t_).normalized()
    p = t_ * (RE_U + dist) + s_ * side * dist - u_ * up * dist
    cam.look(tuple(p), tuple(t_ * RE_U + look_off), lens)


def sp_meteor(L_m, k, f, dist=4.0, hot=4.):
    """宇宙の場面の隕石：直径 L_m（m）、k（0→1 で東京へ）。1 単位＝1,000 km"""
    side = TOKYO.cross(Vector((0, 0, 1))).normalized(); d = (-TOKYO * .6 - side).normalized(); tgt = TOKYO * RE_U   # 横から斜めに入る
    head = tgt - d * dist * (1 - k) - d * (L_m / 2e6); r = L_m / 1e6
    place_meteor(head, d, max(r, .004) * 1.0, max(r, .004) * 6 * (.3 + .7 * (1 - k)), hot, 2.5, f)   # 尾は細く短く（太い棒に見えないよう）


def s_l11():
    show("space")
def sp_dirs():
    side = TOKYO.cross(Vector((0, 0, 1))).normalized(); up_ = side.cross(TOKYO).normalized()
    return side, up_, (-TOKYO * .7 - side * .5 + up_ * .2).normalized()


def a_l11(u, t, f):   # 18 日目（直径 13 km）：岩を後ろから追い、東京へ。衝突のあと、カメラが引いて焼けた円を見せる
    side, up_, d = sp_dirs(); tgt = TOKYO * RE_U; r = DAYS[18]["L_m"] / 2e6; TI = 1.8
    s_ = 1.5 * (1 - ease(clamp(t / TI)) * .8 - .2 * clamp(t / TI)); head = tgt - d * (s_ + r)
    chase = head - d * .11 + side * .07 + up_ * .05
    if t < TI:
        place_meteor(head, d, 2 * r, .03, 4., 6., f); keyp(TRAIL, f, scale=(r * .7, r * .7, .03 + .04 * clamp(t / TI)))
        key_fac(ROCK_DIR, tuple(-d), f)   # 追いかけるカメラから見える側（後ろ）のひびを光らせる（見やすさのため）
        cam.look(tuple(chase), tuple(head + d * .03), 32)
    else:
        hide_meteor(f); k = ease(clamp((t - TI) / 1.3)); c0 = tgt - d * (.11 + r) + side * .07 + up_ * .05
        cam.look(tuple(Vector(c0).lerp(TOKYO * (RE_U + 2.4) + side * .6 - up_ * 1.1, k)), tuple(tgt), 32)
    e = t - TI
    key_fac(BURN_A, DAYS[18]["cloth_km"] / 6371 * ease(clamp(e / 1.0)) if e > 0 else 0., f)
    key_fac(SPOT_K, 3 * clamp(1 - e / 1.6) if e > 0 else 0., f); SPOT_A.default_value = .008
    keyp(CLOUDS, f, rot=(0, 0, t * .01))

def s_l12():
    show("space")
def a_l12(u, t, f):   # 20 日目（52 km）：光る尾を引いて東京へ → 爆風の輪が地球を一周
    side, up_, d = sp_dirs(); tgt = TOKYO * RE_U; r = DAYS[20]["L_m"] / 2e6; TI = .9; e = t - TI
    key_fac(BURN_A, DAYS[18]["cloth_km"] / 6371 + .3 * clamp(e / 1.5) if e > 0 else DAYS[18]["cloth_km"] / 6371, f)
    key_fac(RING_A, math.pi * ease(clamp(e / 1.7)) if e > 0 else 0., f); key_fac(RING_K, 5.0 * (1 - .5 * clamp(e / 1.7)) if e > 0 else 0., f)
    if e < 0:
        place_meteor(tgt - d * (3.5 * (1 - t / TI) + r), d, 2 * r, 1.4, 4., 8., f)
    else:
        hide_meteor(f)
    keyp(CLOUDS, f, rot=(0, 0, t * .01))
    cam.look(tuple(TOKYO * (RE_U + 9 + 2 * ease(u)) + side * 4.0 + up_ * 1.0), tuple(TOKYO * RE_U * .6), 35)

def s_l13():
    show("space")
def a_l13(u, t, f):   # 23 日目（419 km）：光る尾を引いて東京へ → 海が白い湯気になり、干上がっていく
    side, up_, d = sp_dirs(); tgt = TOKYO * RE_U; r = DAYS[23]["L_m"] / 2e6; TI = 1.0; e = t - TI
    key_fac(BURN_A, .9 + .7 * clamp(e / 1.5) if e > 0 else .9, f); key_fac(DRY, clamp(e / 1.6) if e > 0 else 0., f)
    key_fac(CLOUD_LO, .5 - .45 * clamp(e / 1.6) if e > 0 else .5, f)
    if e < 0:
        place_meteor(tgt - d * (6.0 * (1 - t / TI) + r), d, 2 * r, 3.0, 3., 7., f)
    else:
        hide_meteor(f)
    keyp(CLOUDS, f, rot=(0, 0, t * .02))
    cam.look(tuple(TOKYO * (RE_U + 15 + 2 * ease(u)) + side * 6.0 + up_ * 1.5), tuple(TOKYO * RE_U * .4), 35)

def s_l14():
    show("space")
def a_l14(u, t, f):   # 26 日目（3,355 km）：月とほぼ同じ大きさの岩が、月と並んで地球へ迫る
    side, up_, d = sp_dirs(); L_ = DAYS[26]["L_m"]; r = L_ / 2e6
    key_fac(DRY, 1.0, f); key_fac(BURN_A, 1.6, f); key_fac(CLOUD_LO, .05, f)
    head = TOKYO * RE_U - d * (RE_U * 2.6 - 2.0 * ease(u) + r)
    place_meteor(head, d, 2 * r, 4.0, 2.5, 3., f); keyp(TRAIL, f, loc=(0, 0, -1e6))
    keyp(MOON, f, loc=tuple(head + up_ * (r + 1.737 + 1.0)))
    cam.look(tuple(TOKYO * 12 - side * 26 + up_ * 6), tuple(head * .5), 35)

def s_l15():
    show("space")
def a_l15(u, t, f):   # 28 日目：地球より大きな岩が迫り、地球が砕ける（橙は弱く、閃光にしない）
    key_fac(DRY, 1.0, f); key_fac(BURN_A, 1.6, f); key_fac(CLOUD_LO, .05, f)
    e = t - 2.4; L_ = DAYS[28]["L_m"] / 1e6; side = TOKYO.cross(Vector((0, 0, 1))).normalized()
    if e < 0:
        k = ease(clamp(t / 2.4)); head = TOKYO * (RE_U + L_ / 2 + 20 * (1 - k) - .4 * k) + side * 3 * (1 - k)
        keyp(ROCK, f, loc=tuple(head), rot=(t * .1, .3, 0), scale=L_ / 2); key_fac(ROCK_HOT, 1.0 + 3 * k, f); key_fac(ROCK_DIR, tuple(-TOKYO), f)
        keyp(EARTH, f, loc=(0, 0, 0), scale=1.0); keyp(CLOUDS, f, scale=1.0); keyp(CORE, f, loc=(0, 0, -900))
        for o, dv, rr, ss in EFRAG:
            keyp(o, f, loc=(0, 0, -900))
    else:
        kk = ease(clamp(e / 1.8))
        keyp(EARTH, f, loc=(0, 0, -900)); keyp(CLOUDS, f, loc=(0, 0, -900))
        keyp(ROCK, f, loc=tuple(TOKYO * (L_ / 2 - 2 * kk)), scale=L_ / 2 * (1 - .5 * kk)); key_fac(ROCK_HOT, 4 * (1 - kk), f)
        keyp(CORE, f, loc=(0, 0, 0), scale=1 + .6 * kk); key_fac(CORE_K, 3.0 * (1 - kk), f)
        for i, (o, dv, rr, ss) in enumerate(EFRAG):
            p = dv * RE_U * rr * (1 + 2.6 * kk * ss); keyp(o, f, loc=tuple(p), rot=(kk * ss * 3, kk * 2, i))
    keyp(TRAIL, f, loc=(0, 0, -1e6))
    hit = clamp(1 - abs(e) / .8)
    cam.look(tuple(side * 60 + TOKYO * 14 + Vector((0, 0, 10)) + shake(f, .8 * hit, 7)), tuple(TOKYO * 4), 35)

def s_l16():
    show("space"); EARTH.location = CLOUDS.location = (0, 0, -900)
def a_l16(u, t, f):   # 砕けたかけらが流れ星のように散る → 暗転（冒頭の岩につながる）
    side = TOKYO.cross(Vector((0, 0, 1))).normalized(); kk = 1 + 1.2 * u
    for i, (o, dv, rr, ss) in enumerate(EFRAG):
        p = dv * RE_U * rr * (1 + 2.6 * ss) * kk; keyp(o, f, loc=tuple(p), rot=(u * ss * 3, u * 2, i))
    keyp(CORE, f, loc=(0, 0, -900))
    cam.look(tuple(side * (60 - 15 * ease(u)) + TOKYO * 14 + Vector((0, 0, 10))), tuple(TOKYO * 4), 35)


NAMES = [s["id"] for s in PLAN["shots"]]
SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in NAMES}
if "--probe" in sys.argv:   # 確認用：静止画のコマで、カメラを包んでいる物と、カメラの前の物を書き出す
    def _probe(setup_fn, anim_fn, name):
        def a2(u, t, f):
            anim_fn(u, t, f)
            if abs(u - .5) < .02:
                bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); p = cam.o.matrix_world.translation.copy()
                hit = sc.ray_cast(dg, p, cam.o.matrix_world.to_quaternion() @ Vector((0, 0, -1)))
                print(f"PROBE {name} cam={tuple(round(x) for x in p)} front={hit[4].name if hit[0] else None} dist={round((hit[1]-p).length) if hit[0] else None}", flush=True)
        return setup_fn, a2
    SHOTS = {k: _probe(*v, k) for k, v in SHOTS.items()}
anim = [cam.o]
K.render_shots(HERE, SHOTS, NAMES, O, anim)
