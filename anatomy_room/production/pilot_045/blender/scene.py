"""pilot_045（もしも東京にゾンビが一体現れたら？）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計。
使い方："C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P anatomy_room/production/pilot_045/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
前もって python blender/make_maps.py（地図の素材 work/maps/）。

場面：
  広場（都庁前・都民広場）：都庁第一本庁舎（ツインタワー、243 m）・議事堂・西新宿の高層ビル（模式）。人はピクトグラム（男女・子ども・高齢者・警察官・自衛官）。
       人の動きは、この中の小さな計算（ゾンビは見えた人へ 10.4 m/s、かまれて 10 秒で変わる）。
  新宿の街：昼間人口から建物の高さ（模式）。地面に、最初の 10 分の計算（25 m）のゾンビの赤い点。
  関東・日本：計算の結果の地図（夜景のような人の光＋ゾンビの赤）。
座標：都民広場が原点、x が東、y が北（m）。
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
# 空：曇り（一様な灰色）と空のテクスチャを混ぜる。遠くの地面と建物は、この色にかすむ（HAZE）
_wn = sc.world.node_tree; _wbg = _wn.nodes["Background"]
WMIX = _wn.nodes.new("ShaderNodeMix"); WMIX.data_type = "RGBA"; _wn.links.new(sky.node.outputs[0], WMIX.inputs[6]); _wn.links.new(WMIX.outputs[2], _wbg.inputs[0])
HAZE = []   # 各材料の（かすみの色の Emission、距離の MapRange）


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
RND = random.Random(45)
MAPS = os.path.join(HERE, "..", "work", "maps")
INFO = json.load(open(os.path.join(MAPS, "maps.json")))


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def img(name):
    p = os.path.abspath(os.path.join(MAPS, name + ".png"))
    im = bpy.data.images.get(name + ".png") or bpy.data.images.load(p); im.colorspace_settings.name = "Non-Color"; return im


def emat(name, col, rough=.6, metal=0., emit=None, k=0.):
    m = K.mat(name, col, rough, metal)
    if emit:
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = k
    return m


# ---------------------------------------------------------------- ピクトグラムの人（顔なし）。種類ごとに 1 つのメッシュ、足もとが原点、-Y が前
PM = {k: emat("p_" + k, c, .7) for k, c in {
    "suit": (.035, .045, .075), "shirt": (.75, .77, .8), "skin": (.62, .5, .42), "coat_w": (.55, .42, .3), "red": (.5, .07, .07),
    "skirt": (.12, .1, .14), "yellow": (.95, .75, .05), "gray": (.33, .33, .34), "white": (.85, .85, .85), "police": (.02, .035, .09),
    "olive": (.12, .15, .07), "hair": (.04, .03, .025), "black": (.02, .02, .02), "kid": (.1, .3, .55)}.items()}
PM["zombie"] = emat("p_zombie", (.12, .02, .02), .8, emit=(1, .04, .02), k=.7)
PM["zskin"] = emat("p_zskin", (.22, .2, .18), .8, emit=(1, .1, .05), k=.15)
PM["bitten"] = emat("p_bitten", (.3, .08, .06), .8, emit=(1, .1, .05), k=1.2)


def _part(bm, mi, fn):
    before = set(bm.faces); fn(); [setattr(f, "material_index", mi) for f in set(bm.faces) - before]


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


def pict(kind):
    """kind：man・woman・child・elder・police・sdf・zombie・bitten"""
    mats = list(PM.keys()); I = lambda k: mats.index(k)
    bm = bmesh.new()
    s = {"child": .66, "elder": .93, "woman": .94}.get(kind, 1.0)
    body = {"man": "suit", "woman": "coat_w", "child": "kid", "elder": "gray", "police": "police", "sdf": "olive", "zombie": "zombie", "bitten": "bitten"}[kind]
    head = "zskin" if kind in ("zombie", "bitten") else "skin"
    lean = {"elder": .25, "zombie": .45}.get(kind, 0.)
    hip = .86 * s; sh = 1.42 * s; top = 1.6 * s
    fwd = lambda z: Vector((0, -(z - hip) * lean, z))   # 前かがみ
    if kind == "woman":
        cyl(bm, I("skin"), (-.07, 0, 0), (-.07, 0, .42 * s), .05); cyl(bm, I("skin"), (.07, 0, 0), (.07, 0, .42 * s), .05)
        cyl(bm, I("skirt"), (0, 0, .38 * s), (0, 0, hip + .06), .27 * s, .15 * s, 16)
    else:
        leg = "black" if kind in ("man", "police") else body
        for x in (-.09, .09):
            cyl(bm, I(leg), (x * s, 0, 0), (x * s, 0, hip), .075 * s)
    cyl(bm, I(body), fwd(hip), fwd(sh), .19 * s, .21 * s, 16)
    sph(bm, I(head), fwd(top) + Vector((0, -.02 if lean else 0, 0)), .125 * s)
    # 腕
    if kind == "zombie":
        for x in (-.2, .2):
            cyl(bm, I(body), fwd(sh - .05) + Vector((x * s, 0, 0)), fwd(sh - .05) + Vector((x * s * .8, -.62 * s, -.05)), .055 * s)
    else:
        for x in (-.24, .24):
            cyl(bm, I(body), fwd(sh - .03) + Vector((x * s, 0, 0)), fwd(hip + .1) + Vector((x * s * 1.1, 0, 0)), .055 * s)
    if kind in ("man",):
        cube(bm, I("shirt"), fwd(sh - .1) + Vector((0, -.17, 0)), (.08, .02, .18))   # ネクタイの白い胸元
    if kind == "woman":
        sph(bm, I("hair"), fwd(top) + Vector((0, .03, .02)), .135 * s, 1, 1, .95)
    if kind == "child":
        cyl(bm, I("yellow"), fwd(top) + Vector((0, 0, .05)), fwd(top) + Vector((0, 0, .12)), .13 * s); cyl(bm, I("yellow"), fwd(top) + Vector((0, 0, .04)), fwd(top) + Vector((0, 0, .055)), .2 * s, seg=16)   # 黄色い帽子
        cube(bm, I("red"), fwd(sh - .2) + Vector((0, .2 * s, 0)), (.3 * s, .14 * s, .34 * s))   # ランドセル
    if kind == "elder":
        sph(bm, I("white"), fwd(top) + Vector((0, .02, .03)), .13 * s); cyl(bm, I("black"), (.3, -.25, 0), (.3, -.2, .85), .018)   # 白髪・杖
    if kind == "police":
        cyl(bm, I("police"), fwd(top) + Vector((0, 0, .07)), fwd(top) + Vector((0, 0, .17)), .135); cyl(bm, I("black"), fwd(top) + Vector((0, -.05, .07)), fwd(top) + Vector((0, -.05, .085)), .17, seg=16)   # 制帽
        cyl(bm, I("white"), fwd(hip + .03), fwd(hip + .09), .205, seg=16)   # ベルト
    if kind == "sdf":
        sph(bm, I("olive"), fwd(top) + Vector((0, 0, .05)), .155, 1, 1, .75); cube(bm, I("olive"), fwd(sh - .2) + Vector((0, -.05, 0)), (.44, .44, .4))   # 鉄帽・防弾チョッキ
        cyl(bm, I("black"), fwd(sh - .25) + Vector((.15, -.1, 0)), fwd(sh - .2) + Vector((.1, -.75, .05)), .025, seg=6)   # 小銃
    me = bpy.data.meshes.new("pict_" + kind); bm.to_mesh(me); bm.free()
    for k in mats:
        me.materials.append(PM[k])
    for p in me.polygons:
        p.use_smooth = True
    return me


MESH = {k: pict(k) for k in ["man", "woman", "child", "elder", "police", "sdf", "zombie", "bitten"]}

# ---------------------------------------------------------------- 都庁と広場
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
# ゾンビのいる所はビルも赤く（地面と同じ計算の素材を、世界の x・y で引く）
_gp = n.new("ShaderNodeNewGeometry"); _sp = n.new("ShaderNodeSeparateXYZ"); L.new(_gp.outputs["Position"], _sp.inputs[0])
_uv = n.new("ShaderNodeCombineXYZ")
for _i in (0, 1):
    _m = n.new("ShaderNodeMath"); _m.operation = "MULTIPLY_ADD"; _m.inputs[1].default_value = 1 / 16000; _m.inputs[2].default_value = .5; L.new(_sp.outputs[_i], _m.inputs[0]); L.new(_m.outputs[0], _uv.inputs[_i])
BA = n.new("ShaderNodeTexImage"); BB = n.new("ShaderNodeTexImage")
for _t in (BA, BB):
    _t.interpolation = "Cubic"; L.new(_uv.outputs[0], _t.inputs["Vector"])
BMIX = n.new("ShaderNodeMix"); BMIX.data_type = "FLOAT"; L.new(BA.outputs["Color"], BMIX.inputs[2]); L.new(BB.outputs["Color"], BMIX.inputs[3])
B_K = n.new("ShaderNodeMath"); B_K.operation = "MULTIPLY"; B_K.inputs[1].default_value = 0.; L.new(BMIX.outputs[0], B_K.inputs[0])
_c1 = n.new("ShaderNodeMix"); _c1.data_type = "RGBA"; _c1.blend_type = "MULTIPLY"; _c1.inputs[0].default_value = 1; L.new(WIN_K.outputs[0], _c1.inputs[6]); _c1.inputs[7].default_value = (1, .82, .6, 1)
_c2 = n.new("ShaderNodeMix"); _c2.data_type = "RGBA"; _c2.blend_type = "MULTIPLY"; _c2.inputs[0].default_value = 1; L.new(B_K.outputs[0], _c2.inputs[6]); _c2.inputs[7].default_value = (1, .05, .03, 1)
_c3 = n.new("ShaderNodeMix"); _c3.data_type = "RGBA"; _c3.blend_type = "ADD"; _c3.inputs[0].default_value = 1; L.new(_c1.outputs[2], _c3.inputs[6]); L.new(_c2.outputs[2], _c3.inputs[7])
L.new(_c3.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.0
add_haze(glass)
TOCHO = group("tocho"); TOCHO.parent = PLAZA
K.box("tocho_low", (52, 108, 162), (-112, 0, 81), glass, bevel=0, parent=TOCHO)
for y in (-35, 35):
    K.box(f"tocho_tw{y}", (50, 38, 70), (-112, y, 197), glass, bevel=0, parent=TOCHO)
    K.box(f"tocho_top{y}", (36, 26, 16), (-112, y, 240), granite, bevel=.3, parent=TOCHO)
    K.box(f"tocho_fin{y}", (52, 4, 230), (-112, y + (19 if y > 0 else -19), 115), granite, bevel=0, parent=TOCHO)   # 縦の柱（花崗岩の格子）
K.box("tocho2", (60, 70, 163), (-245, -95, 81), glass, bevel=0, parent=TOCHO); K.box("tocho2b", (44, 50, 30), (-245, -95, 178), granite, bevel=0, parent=TOCHO)
# 議事堂（広場を囲む低い弧）
import bmesh as _bm
me = bpy.data.meshes.new("gikai"); bm = _bm.new()
for i in range(28):
    a0, a1 = math.radians(-75 + i * 150 / 28), math.radians(-75 + (i + 1) * 150 / 28)
    for (r0, r1, z) in [(78, 96, 36)]:
        vs = [bm.verts.new((-40 + r * math.cos(a), r * math.sin(a), h)) for a in (a0, a1) for r in (r0, r1) for h in (0, z)]
        for f in [(0, 2, 6, 4), (1, 5, 7, 3), (0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6)]:
            try:
                bm.faces.new([vs[k] for k in f])
            except ValueError:
                pass
bm.to_mesh(me); bm.free(); g = bpy.data.objects.new("gikai", me); sc.collection.objects.link(g); me.materials.append(granite); g.parent = PLAZA
paving = bpy.data.materials.new("paving"); paving.use_nodes = True; n = paving.node_tree.nodes; L = paving.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); br2 = n.new("ShaderNodeTexBrick"); br2.inputs["Scale"].default_value = .5; L.new(tc.outputs["Object"], br2.inputs["Vector"])
br2.inputs["Color1"].default_value = (.34, .33, .31, 1); br2.inputs["Color2"].default_value = (.29, .285, .27, 1); br2.inputs["Mortar"].default_value = (.06, .06, .06, 1); br2.inputs["Mortar Size"].default_value = .02
L.new(br2.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .55
bpy.ops.mesh.primitive_plane_add(size=1, location=(-20, 0, .03)); pl = bpy.context.object; pl.scale = (420, 420, 1); bpy.ops.object.transform_apply(scale=True); pl.data.materials.append(paving); pl.parent = PLAZA
tree_m = emat("tree", (.05, .09, .04), .9); trunk_m = emat("trunk", (.08, .06, .05), .9)
for k in range(26):
    a = math.radians(-80 + k * 160 / 25); x, y = -40 + 108 * math.cos(a), 108 * math.sin(a)
    K.tube((x, y, 0), (x, y, 4), .25, trunk_m, PLAZA, 8); bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=3.2, location=(x, y, 6)); s = bpy.context.object; s.data.materials.append(tree_m); s.parent = PLAZA
for (x, y) in [(10, -60), (30, -60), (10, 60), (30, 60), (50, -30), (50, 30)]:   # 街灯
    K.tube((x, y, 0), (x, y, 6), .08, granite, PLAZA, 8)

# ---------------------------------------------------------------- 新宿の街（建物は昼間人口から、模式）
ci = INFO["city"]; DAYP = np.load(os.path.join(MAPS, "city_daypop.npy")); NPX = DAYP.shape[0]; HALF = ci["x1"]
def daypop(x, y):
    a = int((y + HALF) / (2 * HALF) * NPX); b_ = int((x + HALF) / (2 * HALF) * NPX)
    return float(DAYP[min(NPX - 1, max(0, a)), min(NPX - 1, max(0, b_))])
SKY = [(110, 230, 210), (210, -230, 200), (-20, 380, 190), (300, 440, 220), (430, 20, 180), (380, -400, 170), (-300, 300, 150), (560, 260, 205), (120, -470, 185), (520, -180, 160), (250, 120, 230)]
me = bpy.data.meshes.new("bld"); bm = bmesh.new()
STEP = 44
for i in range(-100, 101):
    for j in range(-100, 101):
        if i % 7 == 0 or j % 7 == 0:
            continue   # 大きな道路
        x, y = i * STEP + RND.uniform(-6, 6), j * STEP + RND.uniform(-6, 6); r = math.hypot(x, y)
        if r > 4500 or (-330 < x < 80 and -170 < y < 170) or (-470 < x < -230 and -10 < y < 420) or (700 < x < 860 and -600 < y < 900):
            continue   # 都庁と広場・新宿中央公園・線路
        p = daypop(x, y)
        if RND.random() > min(.95, .25 + p / 60000):
            continue
        h = 8 + 26 * math.log10(1 + p / 4000) * RND.uniform(.5, 1.5) + (RND.uniform(60, 160) if (-300 < x < 650 and -600 < y < 650 and RND.random() < .45) else 0)
        w, d = RND.uniform(16, 38), RND.uniform(16, 38)
        bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, y, h / 2)) @ Matrix.Diagonal((w, d, h, 1)))
for x, y, h in SKY:
    bmesh.ops.create_cube(bm, size=1, matrix=Matrix.Translation((x, y, h / 2)) @ Matrix.Diagonal((60, 55, h, 1)))
bm.to_mesh(me); bm.free(); BLD = bpy.data.objects.new("bld", me); sc.collection.objects.link(BLD); me.materials.append(glass); BLD.parent = CITY
# 地面（16 km）：道路の格子＋ゾンビの赤い点（2 枚を混ぜる）
def ground_mat(name, w_scale, a_key, b_key, prefix):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    ta = n.new("ShaderNodeTexImage"); tb = n.new("ShaderNodeTexImage"); ta.image = img(prefix + a_key); tb.image = img(prefix + b_key)
    for t_ in (ta, tb):
        t_.interpolation = "Cubic"; L.new(tc.outputs["UV"], t_.inputs["Vector"])
    mx = n.new("ShaderNodeMix"); mx.data_type = "FLOAT"; L.new(ta.outputs["Color"], mx.inputs[2]); L.new(tb.outputs["Color"], mx.inputs[3])
    return m, n, L, b, tc, ta, tb, mx
gm, n, L, b, tc, GA, GB, GMIX = ground_mat("ground", 1, "0.5", "1", "city_z_")
road = n.new("ShaderNodeTexBrick"); road.inputs["Scale"].default_value = 1 / 308; road.inputs["Mortar Size"].default_value = .14; road.offset = 0; road.squash = 1; road.inputs["Brick Width"].default_value = 1; road.inputs["Row Height"].default_value = 1
L.new(tc.outputs["Object"], road.inputs["Vector"]); road.inputs["Color1"].default_value = (.07, .07, .075, 1); road.inputs["Color2"].default_value = (.08, .08, .085, 1); road.inputs["Mortar"].default_value = (.025, .025, .028, 1)
L.new(road.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8
G_K = n.new("ShaderNodeMath"); G_K.operation = "MULTIPLY"; G_K.inputs[1].default_value = 0.; L.new(GMIX.outputs[0], G_K.inputs[0])
pw = n.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.3; L.new(G_K.outputs[0], pw.inputs[0])
b.inputs["Emission Color"].default_value = (1, .06, .03, 1); L.new(pw.outputs[0], b.inputs["Emission Strength"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); GROUND = bpy.context.object; GROUND.scale = (2 * HALF, 2 * HALF, 1); bpy.ops.object.transform_apply(scale=True); GROUND.data.materials.append(gm); GROUND.parent = CITY
GFAC = GMIX.inputs[0]
add_haze(gm)
far = K.mat("far", (.07, .07, .075), .85); add_haze(far)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -.3)); FAR = bpy.context.object; FAR.scale = (90000, 90000, 1); FAR.data.materials.append(far); FAR.parent = CITY


def city_tex(a, b):
    GA.image = img("city_z_" + a); GB.image = img("city_z_" + b); BA.image = GA.image; BB.image = GB.image


def key_city(u, f):
    key_fac(GFAC, u, f); key_fac(BMIX.inputs[0], u, f)

# ---------------------------------------------------------------- 地図（関東・日本）
def map_plane(name):
    inf = INFO[name]
    m = bpy.data.materials.new("map_" + name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    def T(key):
        t_ = n.new("ShaderNodeTexImage"); t_.image = img(f"{name}_{key}"); t_.interpolation = "Cubic"; L.new(tc.outputs["UV"], t_.inputs["Vector"]); return t_
    land, pop, za, zb = T("land"), T("pop"), T("z_" + inf["keys"][0]), T("z_" + inf["keys"][1])
    mx = n.new("ShaderNodeMix"); mx.data_type = "FLOAT"; L.new(za.outputs["Color"], mx.inputs[2]); L.new(zb.outputs["Color"], mx.inputs[3])
    # 端をぼかして海に溶かす
    sep = n.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["UV"], sep.inputs[0])
    def edge(sock):
        a1 = n.new("ShaderNodeMath"); a1.operation = "PINGPONG"; a1.inputs[1].default_value = .5; L.new(sock, a1.inputs[0])
        a2 = n.new("ShaderNodeMapRange"); a2.inputs[1].default_value = 0; a2.inputs[2].default_value = .025; L.new(a1.outputs[0], a2.inputs[0]); return a2.outputs[0]
    e = n.new("ShaderNodeMath"); e.operation = "MULTIPLY"; L.new(edge(sep.outputs[0]), e.inputs[0]); L.new(edge(sep.outputs[1]), e.inputs[1])
    le = n.new("ShaderNodeMath"); le.operation = "MULTIPLY"; L.new(land.outputs["Color"], le.inputs[0]); L.new(e.outputs[0], le.inputs[1])
    col = n.new("ShaderNodeMix"); col.data_type = "RGBA"; L.new(le.outputs[0], col.inputs[0]); col.inputs[6].default_value = (.004, .007, .016, 1); col.inputs[7].default_value = (.03, .04, .06, 1)
    L.new(col.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .7
    # 光：人の光（ゾンビの所は暗く）＋ゾンビの赤
    zk = n.new("ShaderNodeMath"); zk.operation = "MULTIPLY"; zk.inputs[1].default_value = 2.2; zk.use_clamp = True; L.new(mx.outputs[0], zk.inputs[0])
    inv = n.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1; inv.use_clamp = True; L.new(zk.outputs[0], inv.inputs[1])   # ゾンビのいる所は人の光が消える
    pk = n.new("ShaderNodeMath"); pk.operation = "MULTIPLY"; L.new(pop.outputs["Color"], pk.inputs[0]); L.new(inv.outputs[0], pk.inputs[1])
    pk2 = n.new("ShaderNodeMath"); pk2.operation = "MULTIPLY"; L.new(pk.outputs[0], pk2.inputs[0]); L.new(e.outputs[0], pk2.inputs[1])
    zc = n.new("ShaderNodeMath"); zc.operation = "MULTIPLY"; L.new(zk.outputs[0], zc.inputs[0]); L.new(e.outputs[0], zc.inputs[1])
    wc = n.new("ShaderNodeMix"); wc.data_type = "RGBA"; wc.blend_type = "ADD"; wc.inputs[0].default_value = 1
    m1 = n.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1; L.new(pk2.outputs[0], m1.inputs[6]); m1.inputs[7].default_value = (.36, .26, .16, 1)
    m2 = n.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1; L.new(zc.outputs[0], m2.inputs[6]); m2.inputs[7].default_value = (1.0, .05, .025, 1)
    L.new(m1.outputs[2], wc.inputs[6]); L.new(m2.outputs[2], wc.inputs[7])
    L.new(wc.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 1.6
    bpy.ops.mesh.primitive_plane_add(size=1); p = bpy.context.object; p.name = "map_" + name
    p.scale = (inf["x1"] - inf["x0"], inf["y1"] - inf["y0"], 1); p.location = ((inf["x0"] + inf["x1"]) / 2, (inf["y0"] + inf["y1"]) / 2, 0)
    p.data.materials.append(m)
    return dict(obj=p, za=za, zb=zb, fac=mx.inputs[0], strength=b.inputs["Emission Strength"], name=name)
MAPK = map_plane("kanto"); MAPJ = map_plane("japan")
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -50)); OCEAN = bpy.context.object; OCEAN.scale = (4e7, 4e7, 1); OCEAN.data.materials.append(emat("ocean", (.004, .007, .016), .35))

# ---------------------------------------------------------------- 広場の人の動き（小さな計算）
class Crowd:
    """t=0 でゾンビが動きはじめる。t<0 はみんな歩いているだけ（最後のショットが冒頭につながるように）。"""
    def __init__(self, n=320, seed=45, t0=-12.0, t1=95.0, dt=1 / 30, kinds=None, zombie_at=(0., 0.), police=None):
        r = np.random.default_rng(seed)
        kinds = kinds or (["man"] * 52 + ["woman"] * 30 + ["child"] * 6 + ["elder"] * 12)
        self.kind = [kinds[k % len(kinds)] for k in r.permutation(n)]
        self.kind[0] = "zombie"
        p = np.c_[r.uniform(-35, 60, n), r.uniform(-60, 60, n)]
        p[0] = zombie_at
        for k in range(1, n):   # 最初の一体のすぐそばには立たせない
            while np.hypot(*(p[k] - p[0])) < 3.5 or (p[k][0] > 2 and abs(p[k][1] - 1) < 2.5 and p[k][0] < 9):
                p[k] = (r.uniform(-35, 60), r.uniform(-60, 60))
        ang = r.uniform(0, 2 * np.pi, n); spd = np.array([{"child": .9, "elder": .7}.get(k, 1.25) for k in self.kind]) * r.uniform(.8, 1.2, n)
        self.flee = np.array([{"child": 2.6, "elder": 1.4, "woman": 2.6}.get(k, 3.2) for k in self.kind])
        st = np.zeros(n, int); st[0] = 2   # 0：人、1：かまれた、2：ゾンビ
        tb = np.full(n, -1e9); busy = np.zeros(n)
        steps = int((t1 - t0) / dt) + 1
        self.t0, self.dt = t0, dt
        self.P = np.zeros((steps, n, 2), np.float32); self.S = np.zeros((steps, n), np.int8); self.H = np.zeros((steps, n), np.float32)
        head = ang.copy(); aware = np.zeros(n, bool)
        for s in range(steps):
            t = t0 + s * dt
            Z = st == 2; Hm = st == 0
            if t < 0:   # まだ誰も知らない：歩くだけ。ゾンビはうつむいて立っている
                ang += r.normal(0, .25, n) * dt
                v = np.c_[np.cos(ang), np.sin(ang)] * spd[:, None]; v[0] = 0
                p += v * dt
                out = (p[:, 0] < -60) | (p[:, 0] > 100) | (np.abs(p[:, 1]) > 100); ang[out] += np.pi
            else:
                zi = np.nonzero(Z)[0]; hi = np.nonzero(Hm)[0]
                if len(hi) and len(zi):
                    d = np.linalg.norm(p[zi][:, None] - p[hi][None], axis=2)
                    for a, z in enumerate(zi):
                        if busy[z] > t:
                            continue
                        j = np.argmin(d[a]); h = hi[j]
                        if d[a, j] < .8 and st[h] == 0:
                            st[h] = 1; tb[h] = t; busy[z] = t + 3.0; continue   # かむ（3 秒）
                        if d[a, j] < 45:
                            v = (p[h] - p[z]) / max(d[a, j], 1e-6); p[z] += v * min(10.4 * dt, d[a, j]); head[z] = math.atan2(v[1], v[0])
                        else:
                            p[z] += np.array([math.cos(head[z]), math.sin(head[z])]) * 1.5 * dt
                    dz = d.min(0)
                    aware[hi] |= (dz < 12) | (t > 22 + 10 * r.random())
                    for j, h in enumerate(hi):
                        if aware[h]:
                            z = zi[np.argmin(d[:, j])]; v = p[h] - p[z]; v /= max(np.linalg.norm(v), 1e-6)
                            p[h] += v * self.flee[h] * dt; head[h] = math.atan2(v[1], v[0])
                        else:
                            ang[h] += r.normal(0, .25) * dt; p[h] += np.array([math.cos(ang[h]), math.sin(ang[h])]) * spd[h] * dt; head[h] = ang[h]
                turn = (st == 1) & (t - tb >= 10.0); st[turn] = 2; busy[turn] = t + .6   # 10 秒でゾンビに
            for k in range(n):
                if t < 0 or st[k] == 0 and not aware[k]:
                    head[k] = ang[k] if k else 0.0   # 最初の一体はカメラの方（東）を向く
            self.P[s] = p; self.S[s] = st; self.H[s] = head
        self.n = n

    def at(self, t):
        s = min(len(self.P) - 1, max(0, int(round((t - self.t0) / self.dt)))); return self.P[s], self.S[s], self.H[s]

    def count(self, t):
        return int((self.at(t)[1] >= 1).sum())


class Actors:
    """1 人に 2 つの物（人の姿・ゾンビの姿）。かまれた人は、かがんだ赤い姿。"""
    def __init__(self, kinds, name):
        self.objs = []
        for k, kind in enumerate(kinds):
            hu = bpy.data.objects.new(f"{name}_h{k}", MESH["zombie" if kind == "zombie" else kind]); sc.collection.objects.link(hu)
            zo = bpy.data.objects.new(f"{name}_z{k}", MESH["zombie"]); sc.collection.objects.link(zo)
            bi = bpy.data.objects.new(f"{name}_b{k}", MESH["bitten"]); sc.collection.objects.link(bi)
            for o in (hu, zo, bi):
                o.hide_render = True
            self.objs.append((hu, zo, bi))

    def hide(self):
        for t_ in self.objs:
            for o in t_:
                o.hide_render = True; o.animation_data_clear()

    def pose(self, P, S, Hd, f, ox=0., oy=0., fall=None):
        for k, (hu, zo, bi) in enumerate(self.objs):
            st = S[k]; x, y = float(P[k][0]) + ox, float(P[k][1]) + oy
            for o, on in ((hu, st == 0 and not (fall is not None and fall[k])), (zo, st == 2), (bi, st == 1 or (fall is not None and fall[k] and st == 0))):
                o.hide_render = not on; o.keyframe_insert("hide_render", frame=f + 1)
                o.location = (x, y, 0); o.rotation_euler = (math.radians(80) if (fall is not None and fall[k] and o is not hu) else 0, 0, float(Hd[k]) + math.pi / 2)
                o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_euler", frame=f + 1)
            if st == 1:
                bi.scale = (1, 1, .55); bi.keyframe_insert("scale", frame=f + 1)



# 警察官の場面（L04）：駆けつけた警察官とパトカー、ゾンビの群れ
POL_N = 8; ZN = 34
pr = np.random.default_rng(7)
A_POL = Actors(["police"] * POL_N + ["zombie"] * ZN, "po")
car = group("patrol"); K.box("car_body", (1.8, 4.6, 1.0), (0, 0, .75), emat("car_w", (.8, .8, .82), .3), bevel=.15, parent=car)
K.box("car_low", (1.82, 4.62, .5), (0, 0, .45), emat("car_b", (.02, .02, .02), .3), bevel=.1, parent=car)
K.box("car_top", (1.5, 2.3, .55), (0, .2, 1.5), emat("car_g", (.04, .05, .07), .1, .3), bevel=.12, parent=car)
LIGHTBAR = K.box("lightbar", (1.1, .3, .15), (0, .2, 1.85), emat("lb", (.3, .02, .02), .3, emit=(1, .05, .03), k=6.0), bevel=.05, parent=car)
car.location = (0, 0, -500)

# 自衛隊の場面（L08）：夜の道路、防護柵、装甲車、迫るゾンビ
SDF_N = 12; SZN = 70
A_SDF = Actors(["sdf"] * SDF_N + ["zombie"] * SZN, "sd")
bar = group("barrier"); [K.box(f"bar{k}", (2.2, .6, 1.0), (-13 + k * 2.4, 0, .5), emat("concrete", (.4, .4, .38), .8), bevel=.05, parent=bar) for k in range(12)]
apc = group("apc"); K.box("apc_b", (2.6, 6.5, 1.8), (0, 0, 1.4), emat("apc", (.1, .12, .07), .7), bevel=.3, parent=apc); K.box("apc_t", (1.4, 1.6, .6), (0, -.5, 2.6), emat("apc2", (.1, .12, .07), .7), bevel=.15, parent=apc)
bar.location = apc.location = (0, 0, -500)
lamps = []
for k in range(6):
    l = bpy.data.objects.new(f"lamp{k}", bpy.data.lights.new(f"lamp{k}", "POINT")); l.data.energy = 0; l.data.color = (1, .78, .5); sc.collection.objects.link(l); lamps.append(l)
heli = bpy.data.objects.new("heli", bpy.data.lights.new("heli", "SPOT")); heli.data.energy = 0; heli.data.spot_size = math.radians(16); heli.data.spot_blend = .5; heli.data.color = (.85, .92, 1); sc.collection.objects.link(heli)
flood = bpy.data.objects.new("flood", bpy.data.lights.new("flood", "AREA")); flood.data.energy = 0; flood.data.size = 6; sc.collection.objects.link(flood)

# ---------------------------------------------------------------- 表示の切り替え
def hide_tree(o, h):
    o.hide_render = h
    for c in o.children_recursive:
        c.hide_render = h


def show(city=False, plaza=False, maps=None, emit=0., windows=0., day=True):
    for a in (A_PLAZA, A_POL, A_SDF):
        a.hide()
    hide_tree(CITY, not city); hide_tree(PLAZA, not plaza)
    for M_ in (MAPK, MAPJ):
        M_["obj"].hide_render = maps != M_["name"]; M_["fac"].default_value = 0
    OCEAN.hide_render = maps is None
    G_K.inputs[1].default_value = emit; B_K.inputs[1].default_value = emit * .35; WIN_K.inputs[1].default_value = windows
    cam.o.data.dof.use_dof = False
    car.location = bar.location = apc.location = (0, 0, -500)
    for l in lamps + [heli, flood]:
        l.data.energy = 0
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
    if maps:   # 地図：色が鈍らないように
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sky.set(0, -12, 160, 0.0); set_haze((.0, .0, .0), 0.); sc.view_settings.exposure = -1.6
    elif day:   # 曇りの正午（暗めの色調）
        sky.set(0, 80, 180, 1.4); set_haze((.42, .46, .52), 1.0); sc.view_settings.exposure = -1.2
    else:
        sky.set(0, -12, 160, 0.0); set_haze((.006, .008, .016), 1.0); sc.view_settings.exposure = -.6


def map_textures(M_, a, b):
    M_["za"].image = img(f"{M_['name']}_z_{a}"); M_["zb"].image = img(f"{M_['name']}_z_{b}")


def key_fac(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f + 1)


def space_world(k):
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = .0 + .0 * k
    sky.set(60000 + 200000 * k, -20, 160, 0.0); sc.view_settings.exposure = -1.2


# ---------------------------------------------------------------- ショット
EYE0 = ((6.5, 1.2, 1.55), (-2, -.3, 1.45), 28)   # 冒頭の構図（最後のショットはここで終わる）
def crowd_pose(t, f):
    P, S, Hd = CROWD.at(t); A_PLAZA.pose(P, S, Hd, f)

def s_l00():
    show(plaza=True, city=True); cam.o.data.dof.use_dof = True; cam.o.data.dof.focus_distance = 6.4; cam.o.data.dof.aperture_fstop = 2.8
def a_l00(u, t, f):   # 都庁を背に、うつむいて立つ一体。周りの人はまだ気づかない
    T = SHOT_T["l00"]; crowd_pose(T[0] + t, f)
    cam.look(mix(EYE0[0], (5.4, 1.0, 1.5), K.ease(u)), EYE0[1], EYE0[2] + 4 * u)

def s_l01():
    show(plaza=True, city=True)
def a_l01(u, t, f):   # 動きだす：最初の一人へ（カメラは下がりながら少し上へ）
    crowd_pose(t, f); cam.look(mix((5.4, 1.0, 1.5), (16, 7, 6), K.ease(u)), mix((-2, -.3, 1.45), (0, 0, 1), u), 30)

def s_l02():
    show(plaza=True, city=True)
def a_l02(u, t, f):   # 広場の上へ：かまれた人が次々に変わる（3 秒 → 80 秒を早送り）
    crowd_pose(3 + 42 * u, f); cam.look(mix((16, 7, 6), (36, -24, 24), K.ease(u)), mix((0, 0, 1), (10, 2, 0), u), 34)
    if os.environ.get("DBG_TOP"):
        cam.look((0, -1, 600), (0, 0, 0), 20)
        if os.environ.get("DBG_TOP") == "2":
            sky.sun.data.energy = 0

def s_l03():
    show(plaza=True, city=True, emit=8.0)
    city_tex("2", "3")
def a_l03(u, t, f):   # 300 m：西新宿から新宿駅へ（計算の 2〜3 分）
    key_city(u, f); cam.look(mix((900, -1350, 380), (1050, -1700, 650), K.ease(u)), (420, 80, 0), 30)

def s_l04():
    show(plaza=True, city=True)
    city_tex("3", "5")
def a_l04(u, t, f):   # 駆けつけた警察官。ゾンビの群れが迫る
    car.location = (8, -37, 0); car.rotation_euler = (0, 0, math.radians(15)); LIGHTBAR.rotation_euler = (0, 0, t * 6)
    P = np.zeros((POL_N + ZN, 2)); S = np.zeros(POL_N + ZN, int); Hd = np.zeros(POL_N + ZN)
    for k in range(POL_N):
        P[k] = (1 + (k % 4) * 2.2, -33 + (k // 4) * 2.5); Hd[k] = math.radians(140)
    for k in range(ZN):
        x0, y0 = (k % 7) * 3.5 - 42, 6 + (k // 7) * 4 + (k % 3)
        d = Vector((3 - x0, -31 - y0)); L_ = d.length; s_ = min(L_ - 1.0, 10.4 * max(0, t - .2 - .05 * k)); v = d.normalized()
        P[POL_N + k] = (x0 + v.x * s_, y0 + v.y * s_); S[POL_N + k] = 2; Hd[POL_N + k] = math.atan2(v.y, v.x)
    for k in range(POL_N):   # 取りつかれた警察官はかがむ
        near = np.linalg.norm(P[POL_N:] - P[k], axis=1).min(); S[k] = 1 if near < 1.2 else 0
    A_POL.pose(P, S, Hd, f)
    cam.look(mix((15, -46, 2.8), (19, -50, 9), K.ease(u)), mix((-4, -26, 1.5), (-12, -16, 1), u), 26)

def s_l05():
    show(plaza=True, city=True, emit=8.0)
    city_tex("5", "10")
def a_l05(u, t, f):   # 1 km → 5 km：都心の駅がのみ込まれる（計算の 5〜10 分）
    key_city(u, f); cam.look(mix((200, -2400, 900), (600, -6800, 5200), K.ease(u)), (600, 200, 0), 28)

def s_l06():
    show(plaza=True, city=True)
def a_l06(u, t, f):   # 人のいなくなった広場をうろつくゾンビ。建物の扉は閉ざされた
    P, S, Hd = CROWD.at(95.0); P = P.copy(); Hd = Hd.copy()
    for k in range(CROWD.n):
        if S[k] >= 1:
            a = k * 1.7; P[k] = (P[k][0] * .25 + 15 * math.cos(a) + 2.0 * math.sin(t * .6 + a) * t, P[k][1] * .25 + 18 * math.sin(a) + 2.0 * math.cos(t * .5 + a) * t); Hd[k] = a + t * .4
    S = np.where(S >= 1, 2, -1)
    A_PLAZA.pose(P, S, Hd, f)
    ang = math.radians(200 + 30 * u); cam.look((-40 + 70 * math.cos(ang) * -1, 70 * math.sin(ang), 26 - 4 * u), (0, 0, 2), 26)

def s_l07():
    show(maps="kanto", day=False); map_textures(MAPK, "1h", "6h")
def a_l07(u, t, f):   # 30 km → 60 km：関東へ（1〜6 時間）
    key_fac(MAPK["fac"], u, f); cam.look(mix((0, -60000, 50000), (0, -110000, 120000), K.ease(u)), (0, 8000, 0), 30)

SDF_O = (25.0, -150.0)   # 自衛隊の場面の位置：都庁前の広場の南（夜の都庁が見える）
def s_l08():
    show(plaza=True, city=True, day=False, windows=6.0); bar.location = (SDF_O[0], SDF_O[1], 0); apc.location = (SDF_O[0] + 8, SDF_O[1] - 9, 0)
def a_l08(u, t, f):   # 真夜中の道路：自衛隊の防衛線。闇の向こうから迫る赤い影
    P = np.zeros((SDF_N + SZN, 2)); S = np.zeros(SDF_N + SZN, int); Hd = np.zeros(SDF_N + SZN); fall = np.zeros(SDF_N + SZN, bool)
    for k in range(SDF_N):
        P[k] = (-12 + k * 2.2, -1.2); Hd[k] = -math.pi / 2 + math.pi
    for k in range(SZN):
        x0 = ((k * 7.3) % 40) - 20; y0 = 45 + (k * 13.7) % 70; s_ = 10.4 * max(0, t + .5 - .05 * k)
        y = y0 - s_; dead_at = 9 + (k * 5.3) % 30
        if y < dead_at:
            y = dead_at; fall[SDF_N + k] = True
        P[SDF_N + k] = (x0, y); S[SDF_N + k] = 2; Hd[SDF_N + k] = -math.pi / 2
        if fall[SDF_N + k]:
            S[SDF_N + k] = 2
    A_SDF.pose(P, S, Hd, f, ox=SDF_O[0], oy=SDF_O[1], fall=fall)
    ox, oy = SDF_O
    for k, l in enumerate(lamps):
        l.location = (ox - 16 + k * 6.5, oy + 6 + (k % 2) * 14, 8); l.data.energy = 30000
    heli.location = (ox + 10 * math.sin(t * .4), oy + 30 + 3 * t, 45); heli.data.energy = 3e6
    heli.rotation_euler = (Vector((ox, oy + 50 + 8 * t, 0)) - heli.location).to_track_quat("-Z", "Y").to_euler()
    for o in (heli,):
        o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_euler", frame=f + 1)
    cam.look(mix((ox + 3.5, oy - 5.5, 1.9), (ox + 2.5, oy - 8, 3.0), K.ease(u)), (ox - 1, oy + 30, 1.2), 26)

def s_l09():
    show(maps="kanto", day=False); map_textures(MAPK, "12h", "7d")
def a_l09(u, t, f):   # 12 時間 → 7 日：広がりが止まる（ほとんど動かない）
    key_fac(MAPK["fac"], K.ease(u), f); cam.look(mix((0, -115000, 125000), (0, -120000, 135000), u), (0, 8000, 0), 30)

def s_l10():
    show(maps="japan", day=False); map_textures(MAPJ, "7d", "8d")
def a_l10(u, t, f):   # 日本の上から：家の籠城が限界（7 日）
    key_fac(MAPJ["fac"], .15 * u, f); cam.look(mix((0, -330000, 300000), (0, -360000, 360000), K.ease(u)), (0, 0, 0), 30)

def s_l11():
    show(maps="japan", day=False); map_textures(MAPJ, "8d", "10d")
def a_l11(u, t, f):   # 8 日：一気に広がる
    key_fac(MAPJ["fac"], u, f); cam.look(mix((0, -360000, 360000), (-60000, -480000, 520000), K.ease(u)), (-40000, 0, 0), 30)

def s_l12():
    show(maps="japan", day=False); map_textures(MAPJ, "10d", "14d")
def a_l12(u, t, f):   # 名古屋、大阪へ（西へ振る）
    key_fac(MAPJ["fac"], u, f); cam.look(mix((-60000, -480000, 520000), (-260000, -500000, 560000), K.ease(u)), mix((-40000, 0, 0), (-300000, -60000, 0), K.ease(u)), 30)

def s_l13():
    show(maps="japan", day=False); map_textures(MAPJ, "14d", "22d")
def a_l13(u, t, f):   # 3 週間：大きな建物も限界
    key_fac(MAPJ["fac"], u, f); cam.look(mix((-260000, -500000, 560000), (-150000, -700000, 900000), K.ease(u)), mix((-300000, -60000, 0), (-150000, 50000, 0), K.ease(u)), 30)

def s_l14():
    show(maps="japan", day=False); map_textures(MAPJ, "22d", "60d")
def a_l14(u, t, f):   # 橋とトンネルを渡る
    key_fac(MAPJ["fac"], u, f); cam.look(mix((-150000, -700000, 900000), (-60000, -1000000, 1500000), K.ease(u)), mix((-150000, 50000, 0), (-80000, 220000, 0), K.ease(u)), 30)

def s_l15():
    show(maps="japan", day=False); map_textures(MAPJ, "60d", "90d")
def a_l15(u, t, f):   # 90 日：宇宙から
    key_fac(MAPJ["fac"], u, f); cam.look(mix((-60000, -1000000, 1500000), (-60000, -1500000, 2800000), K.ease(u)), (-60000, 250000, 0), 30)

def s_l16():
    show(plaza=True, city=True)
def a_l16(u, t, f):   # 始まりは、たった一体：冒頭の少し前の広場（最後のコマが冒頭の最初のコマにつながる）
    T = SHOT_T["l16"]; T0 = SHOT_T["l00"][0]
    crowd_pose(T0 - (T[1] - T[0]) + t, f)
    cam.look(mix((10.5, 2.2, 2.4), EYE0[0], K.ease(u)), EYE0[1], EYE0[2] - 4 * (1 - u))


cues, END = K.shot_lengths(HERE)
ORDER = K.renderer_order(HERE, ["l00"] + ["l%02d" % i for i in range(1, 17)])
def span(k):
    i = ORDER.index(k); a = cues[k]; b = cues[ORDER[i + 1]] if i + 1 < len(ORDER) else END
    return a, b
# 広場の時刻：l01 の始まりが t=0。冒頭（l00）は t<0、最後のショットはさらにその前
L01 = cues["l01"]
SHOT_T = {"l00": (cues["l00"] - L01 - .05, 0.0), "l16": span("l16")}
SHOT_T["l00"] = (-(L01 - cues["l00"]) - .05, 0.0)
CROWD = Crowd(t0=-(L01 + (span("l16")[1] - span("l16")[0]) + 2), t1=95.0)
A_PLAZA = Actors(CROWD.kind, "pl")
SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00"] + ["l%02d" % i for i in range(1, 17)]}
anim = [cam.o, car, LIGHTBAR, heli]   # 人とゾンビは Actors.pose が自分でキーを打つ
K.render_shots(HERE, SHOTS, None, O, anim)
