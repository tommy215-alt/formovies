"""pilot_045（もしも東京にゾンビが一体現れたら？）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計。v2（2026-11-06）。
使い方："C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P anatomy_room/production/pilot_045/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
前もって python blender/make_maps.py（地図の素材 work/maps/）と python plan.py（blender/plan.json：ショットの長さと時計）。v1 は versions/v1/。

v2（ユーザーの指示）：ゾンビはジタバタして少し間抜けに（腕と体を毎コマ動かす）。最初の一人がかまれる所はスローで迫真に、最初の 20 人ほどは
逃げまどう人をかみに行く様子を地上から。機動隊（盾の列を飛び越える）。インフラが止まるカット（電車・乗り捨てられた車の道路・停電）。
場面：
  広場（都庁前・都民広場）：都庁第一本庁舎（ツインタワー、243 m）・議事堂・西新宿の高層ビル（模式）。人はピクトグラム（男女・子ども・高齢者・警察官・機動隊・自衛官）。
       人の動きは、この中の小さな計算（ゾンビは見えた人へ 10.4 m/s、かまれて 10 秒で変わる）。
  新宿の街：昼間人口から建物の高さ（模式）。地面に、最初の 10 分の計算（25 m）のゾンビの赤い点。
  関東・日本：計算の結果の地図（夜景のような人の光＋ゾンビの赤）。地図は時計に合わせて何枚もつなぐ（chain）。
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
PLAN = json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8"))
SPLAN = {s["id"]: s for s in PLAN["shots"]}
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


def clamp(v, a=0., b=1.):
    return max(a, min(b, v))


def img(name):
    p = os.path.abspath(os.path.join(MAPS, name + ".png"))
    im = bpy.data.images.get(name + ".png") or bpy.data.images.load(p); im.colorspace_settings.name = "Non-Color"; return im


def emat(name, col, rough=.6, metal=0., emit=None, k=0.):
    m = K.mat(name, col, rough, metal)
    if emit:
        b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = k
    return m


def key_fac(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f + 1)


# ---------------------------------------------------------------- 時計（plan.json。renderer.html の clockAt と同じ式）
def clock(k, t):
    s = SPLAN[k]; u = clamp(t / s["dur"]); c = s["c"]
    for (u0, c0), (u1, c1) in zip(c, c[1:]):
        if u <= u1 or (u1, c1) == tuple(c[-1]):
            v = clamp((u - u0) / max(1e-9, u1 - u0))
            if s.get("log") and c0 > 0 and c1 > 0:
                return math.exp(math.log(c0) + (math.log(c1) - math.log(c0)) * v)
            return c0 + (c1 - c0) * v
    return c[-1][1]


def key_sec(k):
    return float(k[:-1]) * (3600 if k.endswith("h") else 86400) if k[-1] in "hd" else float(k) * 60


def chain_p(keys, c):
    """時計 c（秒）が、keys（地図の時刻の名前）のどこにいるか（0〜len-1、対数で補間）"""
    ts = [key_sec(k) for k in keys]
    if c <= ts[0]:
        return 0.
    for i in range(len(ts) - 1):
        if c <= ts[i + 1]:
            return i + (math.log(c) - math.log(ts[i])) / (math.log(ts[i + 1]) - math.log(ts[i]))
    return float(len(ts) - 1)


def chain(n, L, texs):
    """texs（画像のノード）を順に混ぜる。戻り値：(出力, 混ぜる割合のソケットの一覧)。割合 i は clamp(p - i)"""
    out = texs[0].outputs["Color"]; facs = []
    for t_ in texs[1:]:
        m = n.new("ShaderNodeMix"); m.data_type = "FLOAT"; L.new(out, m.inputs[2]); L.new(t_.outputs["Color"], m.inputs[3]); out = m.outputs[0]; facs.append(m.inputs[0])
    return out, facs


def key_chain(facs, p, f):
    for i, s in enumerate(facs):
        key_fac(s, clamp(p - i), f)


# ---------------------------------------------------------------- ピクトグラムの人（顔なし）。種類ごとに 1 つのメッシュ、足もとが原点、-Y が前
PM = {k: emat("p_" + k, c, .7) for k, c in {
    "suit": (.035, .045, .075), "shirt": (.75, .77, .8), "skin": (.62, .5, .42), "coat_w": (.55, .42, .3), "red": (.5, .07, .07),
    "skirt": (.12, .1, .14), "yellow": (.95, .75, .05), "gray": (.33, .33, .34), "white": (.85, .85, .85), "police": (.02, .035, .09),
    "olive": (.12, .15, .07), "hair": (.04, .03, .025), "black": (.02, .02, .02), "kid": (.1, .3, .55)}.items()}
PM["zombie"] = emat("p_zombie", (.12, .02, .02), .8, emit=(1, .04, .02), k=.7)
PM["zskin"] = emat("p_zskin", (.22, .2, .18), .8, emit=(1, .1, .05), k=.15)
PM["bitten"] = emat("p_bitten", (.3, .08, .06), .8, emit=(1, .1, .05), k=1.2)
PM["visor"] = emat("p_visor", (.01, .012, .02), .08, .2)
sh_m = bpy.data.materials.new("p_shield"); sh_m.use_nodes = True; _b = sh_m.node_tree.nodes["Principled BSDF"]
_b.inputs["Base Color"].default_value = (.55, .68, .85, 1); _b.inputs["Roughness"].default_value = .2; _b.inputs["Transmission Weight"].default_value = .5; _b.inputs["IOR"].default_value = 1.49
PM["shield"] = sh_m


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


def _mesh(name, bm):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for k in PM:
        me.materials.append(PM[k])
    for p in me.polygons:
        p.use_smooth = True
    return me


ZLEAN, ZHIP, ZSH = .45, .86, 1.42
ZSHOULDER = Vector((0, -(ZSH - .05 - ZHIP) * ZLEAN, ZSH - .05))   # ゾンビの肩（腕の付け根）


def pict(kind):
    """kind：man・woman・child・elder・police・riot・sdf・zombie（腕なし。腕は zarm を別に付けて動かす）・bitten"""
    mats = list(PM.keys()); I = lambda k: mats.index(k)
    bm = bmesh.new()
    s = {"child": .66, "elder": .93, "woman": .94}.get(kind, 1.0)
    body = {"man": "suit", "woman": "coat_w", "child": "kid", "elder": "gray", "police": "police", "riot": "police", "sdf": "olive", "zombie": "zombie", "bitten": "bitten"}[kind]
    head = "zskin" if kind in ("zombie", "bitten") else "skin"
    lean = {"elder": .25, "zombie": ZLEAN}.get(kind, 0.)
    hip = .86 * s; sh = 1.42 * s; top = 1.6 * s
    fwd = lambda z: Vector((0, -(z - hip) * lean, z))   # 前かがみ
    if kind == "woman":
        cyl(bm, I("skin"), (-.07, 0, 0), (-.07, 0, .42 * s), .05); cyl(bm, I("skin"), (.07, 0, 0), (.07, 0, .42 * s), .05)
        cyl(bm, I("skirt"), (0, 0, .38 * s), (0, 0, hip + .06), .27 * s, .15 * s, 16)
    else:
        leg = "black" if kind in ("man", "police", "riot") else body
        for x in (-.09, .09):
            cyl(bm, I(leg), (x * s, 0, 0), (x * s, 0, hip), .075 * s)
    cyl(bm, I(body), fwd(hip), fwd(sh), .19 * s, .21 * s, 16)
    sph(bm, I(head), fwd(top) + Vector((0, -.02 if lean else 0, 0)), .125 * s)
    if kind not in ("zombie",):   # 腕（ゾンビは別の部品）
        for x in (-.24, .24):
            cyl(bm, I(body), fwd(sh - .03) + Vector((x * s, 0, 0)), fwd(hip + .1) + Vector((x * s * 1.1, 0, 0)), .055 * s)
    if kind == "zombie":   # ぼさぼさの髪とだらしないシャツの裾（少し間抜けに）
        sph(bm, I("hair"), fwd(top) + Vector((.03, .02, .06)), .11, 1.2, 1, .6)
        cyl(bm, I("gray"), fwd(hip + .02) + Vector((0, 0, -.06)), fwd(hip + .02) + Vector((0, 0, .04)), .215, .2, 16)
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
    if kind == "riot":   # 機動隊：ヘルメットと面体、大きな透明の盾
        sph(bm, I("police"), fwd(top) + Vector((0, 0, .03)), .16, 1, 1.05, .9); cube(bm, I("visor"), fwd(top) + Vector((0, -.12, -.01)), (.24, .06, .14))
        cube(bm, I("black"), fwd(sh - .22), (.46, .32, .36))   # 防護衣
        cube(bm, I("shield"), Vector((0, -.42, .95)), (.62, .035, 1.15))
    if kind == "sdf":
        sph(bm, I("olive"), fwd(top) + Vector((0, 0, .05)), .155, 1, 1, .75); cube(bm, I("olive"), fwd(sh - .2) + Vector((0, -.05, 0)), (.44, .44, .4))   # 鉄帽・防弾チョッキ
        cyl(bm, I("black"), fwd(sh - .25) + Vector((.15, -.1, 0)), fwd(sh - .2) + Vector((.1, -.75, .05)), .025, seg=6)   # 小銃
    return _mesh("pict_" + kind, bm)


def zarm():
    """ゾンビの腕：付け根が原点、前（-Y）へまっすぐ。手は少し大きめ（間抜けに）"""
    mats = list(PM.keys()); I = lambda k: mats.index(k); bm = bmesh.new()
    cyl(bm, I("zombie"), (0, 0, 0), (0, -.56, -.04), .058); sph(bm, I("zskin"), Vector((0, -.62, -.05)), .075, 1, 1.2, .8)
    return _mesh("zarm", bm)


MESH = {k: pict(k) for k in ["man", "woman", "child", "elder", "police", "riot", "sdf", "zombie", "bitten"]}
MESH["zarm"] = zarm()

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
# 停電（v2）：大きな模様で地区ごとに明かりが消える。BLACK_T を上げるほど消える（-1 で全部つく）
_gp0 = n.new("ShaderNodeNewGeometry"); bz = n.new("ShaderNodeTexNoise"); bz.inputs["Scale"].default_value = .0016; bz.inputs["Detail"].default_value = 1.0; L.new(_gp0.outputs["Position"], bz.inputs["Vector"])
BLACK = n.new("ShaderNodeMath"); BLACK.operation = "GREATER_THAN"; BLACK.inputs[1].default_value = -1.0; L.new(bz.outputs["Fac"], BLACK.inputs[0])
wk2 = n.new("ShaderNodeMath"); wk2.operation = "MULTIPLY"; L.new(wk.outputs[0], wk2.inputs[0]); L.new(BLACK.outputs[0], wk2.inputs[1])
WIN_K = n.new("ShaderNodeMath"); WIN_K.operation = "MULTIPLY"; WIN_K.inputs[1].default_value = .0; L.new(wk2.outputs[0], WIN_K.inputs[0])
BLACK_T = BLACK.inputs[1]
# ゾンビのいる所はビルも赤く（地面と同じ計算の素材を、世界の x・y で引く）
_gp = n.new("ShaderNodeNewGeometry"); _sp = n.new("ShaderNodeSeparateXYZ"); L.new(_gp.outputs["Position"], _sp.inputs[0])
_uv = n.new("ShaderNodeCombineXYZ")
for _i in (0, 1):
    _m = n.new("ShaderNodeMath"); _m.operation = "MULTIPLY_ADD"; _m.inputs[1].default_value = 1 / 16000; _m.inputs[2].default_value = .5; L.new(_sp.outputs[_i], _m.inputs[0]); L.new(_m.outputs[0], _uv.inputs[_i])
BT = [n.new("ShaderNodeTexImage") for _ in range(3)]
for _t in BT:
    _t.interpolation = "Cubic"; L.new(_uv.outputs[0], _t.inputs["Vector"])
_bout, BFAC = chain(n, L, BT)
B_K = n.new("ShaderNodeMath"); B_K.operation = "MULTIPLY"; B_K.inputs[1].default_value = 0.; L.new(_bout, B_K.inputs[0])
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
me = bpy.data.meshes.new("gikai"); bm = bmesh.new()
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
# 地面（16 km）：道路の格子＋ゾンビの赤い点（3 枚を時計に合わせて混ぜる）
gm = bpy.data.materials.new("ground"); gm.use_nodes = True; n = gm.node_tree.nodes; L = gm.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); GT = [n.new("ShaderNodeTexImage") for _ in range(3)]
for t_ in GT:
    t_.interpolation = "Cubic"; L.new(tc.outputs["UV"], t_.inputs["Vector"])
_gout, GFAC = chain(n, L, GT)
road = n.new("ShaderNodeTexBrick"); road.inputs["Scale"].default_value = 1 / 308; road.inputs["Mortar Size"].default_value = .14; road.offset = 0; road.squash = 1; road.inputs["Brick Width"].default_value = 1; road.inputs["Row Height"].default_value = 1
L.new(tc.outputs["Object"], road.inputs["Vector"]); road.inputs["Color1"].default_value = (.07, .07, .075, 1); road.inputs["Color2"].default_value = (.08, .08, .085, 1); road.inputs["Mortar"].default_value = (.025, .025, .028, 1)
L.new(road.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8
G_K = n.new("ShaderNodeMath"); G_K.operation = "MULTIPLY"; G_K.inputs[1].default_value = 0.; L.new(_gout, G_K.inputs[0])
pw = n.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 1.3; L.new(G_K.outputs[0], pw.inputs[0])
b.inputs["Emission Color"].default_value = (1, .06, .03, 1); L.new(pw.outputs[0], b.inputs["Emission Strength"])
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); GROUND = bpy.context.object; GROUND.scale = (2 * HALF, 2 * HALF, 1); bpy.ops.object.transform_apply(scale=True); GROUND.data.materials.append(gm); GROUND.parent = CITY
add_haze(gm)
far = K.mat("far", (.07, .07, .075), .85); add_haze(far)
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -.3)); FAR = bpy.context.object; FAR.scale = (90000, 90000, 1); FAR.data.materials.append(far); FAR.parent = CITY
CITY_KEYS = []


def city_tex(keys):
    global CITY_KEYS
    CITY_KEYS = keys; ks = keys + [keys[-1]] * (3 - len(keys))
    for t_, bt, k in zip(GT, BT, ks):
        t_.image = img("city_z_" + k); bt.image = t_.image


def key_city(c, f):
    p = chain_p(CITY_KEYS, c); key_chain(GFAC, p, f); key_chain(BFAC, p, f)


# ---------------------------------------------------------------- 地図（関東・日本）：時計に合わせて 6 枚までつなぐ
def map_plane(name):
    inf = INFO[name]
    m = bpy.data.materials.new("map_" + name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord")
    def T(key):
        t_ = n.new("ShaderNodeTexImage"); t_.image = img(f"{name}_{key}") if key else None; t_.interpolation = "Cubic"; L.new(tc.outputs["UV"], t_.inputs["Vector"]); return t_
    land, pop = T("land"), T("pop"); zs = [T(None) for _ in range(6)]
    zout, facs = chain(n, L, zs)
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
    zk = n.new("ShaderNodeMath"); zk.operation = "MULTIPLY"; zk.inputs[1].default_value = 2.2; zk.use_clamp = True; L.new(zout, zk.inputs[0])
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
    return dict(obj=p, zs=zs, facs=facs, name=name, keys=[])
MAPK = map_plane("kanto"); MAPJ = map_plane("japan")
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, -50)); OCEAN = bpy.context.object; OCEAN.scale = (4e7, 4e7, 1); OCEAN.data.materials.append(emat("ocean", (.004, .007, .016), .35))


def map_textures(M_, keys):
    M_["keys"] = keys; ks = keys + [keys[-1]] * (6 - len(keys))
    for t_, k in zip(M_["zs"], ks):
        t_.image = img(f"{M_['name']}_z_{k}")


def key_map(M_, c, f):
    key_chain(M_["facs"], chain_p(M_["keys"], c), f)


# ---------------------------------------------------------------- 広場の人の動き（小さな計算）
VICTIM = (5.0, -2.0)   # 最初にかまれる人（l02 のカメラの前）
AWARE_R, SAFE_TAU = 20.0, 4.0
RING_C, RING_R, PLAZA_X0 = (-40.0, 0.0), 74.0, -82.0   # 議事堂の輪（内側の半径 78 m）の内側と、都庁の手前（x>-86）だけを歩く   # 騒ぎに気づく距離（m）、気づいてから建物に入るまで（秒、指数分布＋2 秒）


class Crowd:
    """t=0 でゾンビが動きはじめる（0.5 秒ジタバタしてから走る）。t<0 はみんな歩いているだけ（最後のショットが冒頭につながるように）。"""
    def __init__(self, n=420, seed=45, t0=-12.0, t1=95.0, dt=1 / 30, kinds=None, zombie_at=(0., 0.)):
        r = np.random.default_rng(seed)
        kinds = kinds or (["man"] * 52 + ["woman"] * 30 + ["child"] * 6 + ["elder"] * 12)
        self.kind = [kinds[k % len(kinds)] for k in r.permutation(n)]
        self.kind[0] = "zombie"; self.kind[1] = "man"
        inside = lambda q: np.hypot(q[0] - RING_C[0], q[1] - RING_C[1]) < RING_R - 4 and q[0] > PLAZA_X0 + 4
        p = np.zeros((n, 2))
        p[0] = zombie_at; p[1] = VICTIM
        for k in range(2, n):   # 広場の中（議事堂の輪の内側）。最初の一体と、最初にかまれる人のすぐそばには立たせない（カメラの通り道も空ける）
            p[k] = (1e9, 1e9)
            while not inside(p[k]) or np.hypot(*(p[k] - p[0])) < 7.0 or np.hypot(*(p[k] - p[1])) < 3.0 or (p[k][0] > 2 and abs(p[k][1] - 1) < 2.5 and p[k][0] < 9) or (4 < p[k][0] < 11 and -8 < p[k][1] < -3):
                p[k] = (r.uniform(PLAZA_X0, 32), r.uniform(-72, 72))
        ang = r.uniform(0, 2 * np.pi, n); spd = np.array([{"child": .9, "elder": .7}.get(k, 1.25) for k in self.kind]) * r.uniform(.8, 1.2, n)
        ang[1] = math.radians(60); spd[1] = 0.   # 最初にかまれる人：立ち止まってスマホを見ている
        self.flee = np.array([{"child": 2.6, "elder": 1.4, "woman": 2.6}.get(k, 3.2) for k in self.kind])
        st = np.zeros(n, int); st[0] = 2   # 0：人、1：かまれた、2：ゾンビ
        tb = np.full(n, 1e9); busy = np.zeros(n); busy[0] = .5
        steps = int((t1 - t0) / dt) + 1
        self.t0, self.dt = t0, dt
        self.P = np.zeros((steps, n, 2), np.float32); self.S = np.zeros((steps, n), np.int8); self.H = np.zeros((steps, n), np.float32); self.V = np.zeros((steps, n), np.float16)
        head = ang.copy(); aware = np.zeros(n, bool); prev = p.copy(); safe = np.full(n, 1e9)
        for s in range(steps):
            t = t0 + s * dt
            Z = st == 2; Hm = st == 0
            if t < 0:   # まだ誰も知らない：歩くだけ。ゾンビはその場でジタバタ
                ang += r.normal(0, .25, n) * dt
                v = np.c_[np.cos(ang), np.sin(ang)] * spd[:, None]; v[0] = 0
                p += v * dt
                out = (np.hypot(p[:, 0] - RING_C[0], p[:, 1] - RING_C[1]) > RING_R - 3) | (p[:, 0] < PLAZA_X0 + 2); ang[out] = np.arctan2(-p[out, 1], RING_C[0] + 20 - p[out, 0])
                dd = p - p[0]; close = np.hypot(dd[:, 0], dd[:, 1]) < 6.5; close[:2] = False   # 冒頭の撮影のため、一体のそばには寄らない
                ang[close] = np.arctan2(dd[close, 1], dd[close, 0])
            else:
                zi = np.nonzero(Z)[0]; hi = np.nonzero(Hm)[0]
                if len(hi) and len(zi):
                    d = np.linalg.norm(p[zi][:, None] - p[hi][None], axis=2)
                    for a, z in enumerate(zi):
                        j = np.argmin(d[a]); h = hi[j]
                        if z == 0 and st[1] == 0:   # 最初の一体は、最初の一人だけを狙う
                            j = int(np.nonzero(hi == 1)[0][0]); h = 1
                        if busy[z] > t:
                            if z == 0 and t < .5:
                                v = p[h] - p[z]; head[z] = math.atan2(v[1], v[0])   # 獲物を見つけて向き直る
                            continue
                        if d[a, j] < .8 and st[h] == 0:
                            st[h] = 1; tb[h] = t; busy[z] = t + 3.0; continue   # かむ（3 秒）
                        if d[a, j] < 45:
                            v = (p[h] - p[z]) / max(d[a, j], 1e-6); p[z] += v * min(10.4 * dt, d[a, j]); head[z] = math.atan2(v[1], v[0])
                        else:
                            p[z] += np.array([math.cos(head[z]), math.sin(head[z])]) * 1.5 * dt
                    dz = d.min(0)
                    near = (dz < AWARE_R) & ((hi != 1) | (t > .6))   # 最初にかまれる人は 0.6 秒で気づく
                    newly = hi[(near | (t > 22 + 10 * r.random())) & ~aware[hi]]
                    aware[newly] = True; safe[newly] = t + r.exponential(SAFE_TAU, len(newly)) + 2.0
                    safe[1] = 1e9
                    for j, h in enumerate(hi):
                        if aware[h]:
                            z = zi[np.argmin(d[:, j])]; v = p[h] - p[z]; v /= max(np.linalg.norm(v), 1e-6)
                            p[h] += v * self.flee[h] * dt; head[h] = math.atan2(v[1], v[0])
                            if t > safe[h] and dz[j] > 15:
                                st[h] = 3   # 建物に逃げ込んだ（見えなくなる。計算の SHELTER_TAU と同じ考え方）
                        else:
                            ang[h] += r.normal(0, .25) * dt; p[h] += np.array([math.cos(ang[h]), math.sin(ang[h])]) * spd[h] * dt; head[h] = ang[h]
                turn = (st == 1) & (t - tb >= 10.0); st[turn] = 2; busy[turn] = t + .6   # 10 秒でゾンビに
            for k in range(n):
                if t < 0 or st[k] == 0 and not aware[k]:
                    head[k] = ang[k] if k else 0.0   # 最初の一体はカメラの方（東）を向く
            d0 = p - np.array(RING_C); r0 = np.hypot(d0[:, 0], d0[:, 1]); o = r0 > RING_R   # 議事堂の壁と都庁の前で止まる
            p[o] = np.array(RING_C) + d0[o] / r0[o, None] * RING_R; p[:, 0] = np.maximum(p[:, 0], PLAZA_X0)
            self.P[s] = p; self.S[s] = st; self.H[s] = head; self.V[s] = np.linalg.norm(p - prev, axis=1) / dt; prev = p.copy()
        self.n = n; self.TB = tb

    def at(self, t):
        s = min(len(self.P) - 1, max(0, int(round((t - self.t0) / self.dt)))); return self.P[s], self.S[s], self.H[s], self.V[s]

    def centroid(self, t):
        P, S, _, _ = self.at(t); m = (S == 1) | (S == 2)
        return P[m].mean(0) if m.any() else P[0]


class Actors:
    """1 人に 3 つの物（人の姿・ゾンビの姿・かまれた姿）。ゾンビの姿には腕が 2 本（毎コマ振り回す）。"""
    def __init__(self, kinds, name):
        self.objs = []; self.arms = []
        for k, kind in enumerate(kinds):
            hu = bpy.data.objects.new(f"{name}_h{k}", MESH["zombie" if kind == "zombie" else kind]); sc.collection.objects.link(hu)
            zo = bpy.data.objects.new(f"{name}_z{k}", MESH["zombie"]); sc.collection.objects.link(zo)
            bi = bpy.data.objects.new(f"{name}_b{k}", MESH["bitten"]); sc.collection.objects.link(bi)
            arms = []
            for sx in (-1, 1):
                a = bpy.data.objects.new(f"{name}_a{k}{sx}", MESH["zarm"]); sc.collection.objects.link(a); a.parent = zo
                a.location = ZSHOULDER + Vector((.2 * sx, 0, 0)); arms.append(a)
            for o in (hu, zo, bi, *arms):
                o.hide_render = True
            self.objs.append((hu, zo, bi)); self.arms.append(arms)

    def hide(self):
        for t_, arms in zip(self.objs, self.arms):
            for o in (*t_, *arms):
                o.hide_render = True; o.animation_data_clear()

    def pose(self, P, S, Hd, f, ox=0., oy=0., oz=0., fall=None, V=None, t=None, TB=None, Z=None, speed=1.0):
        """vt（見た目の秒＝コマ/30）でジタバタ。V：速さ（走る人は前かがみで弾む）。TB と t：かまれた時刻と今の時刻（後ろへ倒れて、10 秒で跳ね起きる）。Z：高さ（飛び越える）"""
        vt = f / 30.0
        for k, ((hu, zo, bi), arms) in enumerate(zip(self.objs, self.arms)):
            st = S[k]; x, y = float(P[k][0]) + ox, float(P[k][1]) + oy; z0 = oz + (float(Z[k]) if Z is not None else 0.)
            fallen = fall is not None and fall[k]
            ph = k * 1.7; run = V is not None and float(V[k]) > 2.5
            w = 2 * math.pi * (2.0 + .6 * ((k * .37) % 1)) * (1.5 if run else 1.0)
            heading = float(Hd[k]) + math.pi / 2
            # 人：走ると前かがみで弾む
            lean_h = .22 if (run and st == 0) else 0.; bob_h = .07 * abs(math.sin(w * .65 * vt + ph)) if (run and st == 0) else 0.
            # ゾンビ：体を左右に揺らし、ぴょこぴょこ弾む
            roll = .2 * math.sin(.55 * w * vt + ph) + .08 * math.sin(1.9 * w * vt); pitch = .1 * math.sin(w * vt + ph)
            hop = (.14 if run else .09) * abs(math.sin(.9 * w * vt + ph))
            # かまれた人：後ろへ倒れ、起き上がる直前に震え、10 秒でゾンビに
            fb = 0.
            if st == 1 and TB is not None and t is not None:
                dt_ = t - float(TB[k]); fb = -1.4 * K.ease(dt_ / .45) * (1 - K.ease((dt_ - 9.4) / .6))
                if 8.6 < dt_ < 10:
                    fb += .12 * math.sin(vt * 55 + ph)
            for o, on in ((hu, st == 0 and not fallen), (zo, st == 2 and not fallen), (bi, st == 1 or (fallen and st == 2))):
                o.hide_render = not on; o.keyframe_insert("hide_render", frame=f + 1)
                if o is zo:
                    o.location = (x, y, z0 + hop); o.rotation_euler = (pitch, roll, heading)
                elif o is bi:
                    o.location = (x, y, z0)
                    if fallen:
                        o.rotation_euler = (math.radians(80), 0, heading)
                    elif TB is not None:
                        o.rotation_euler = (fb, 0, heading)
                    else:
                        o.rotation_euler = (-.35, 0, heading)   # 取りつかれて、のけぞる
                else:
                    o.location = (x, y, z0 + bob_h); o.rotation_euler = (lean_h, 0, heading)
                o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_euler", frame=f + 1)
            # 腕：ばらばらに振り回す（上下と左右）
            for i, a in enumerate(arms):
                sgn = -1 if i == 0 else 1; q = ph + 2.1 * i
                a.rotation_euler = (.75 * math.sin(w * vt + q) + .38 * math.sin(2.3 * w * vt + 1.1 * q) - .15, 0, sgn * (.25 + .55 * math.sin(.85 * w * vt + 2 * q)))
                a.hide_render = zo.hide_render
                a.keyframe_insert("rotation_euler", frame=f + 1); a.keyframe_insert("hide_render", frame=f + 1)


# 警察官と機動隊の場面（l06）：パトカー、盾の列、飛び越えるゾンビ
RIOT_N, POL_N, ZN = 9, 3, 30
A_POL = Actors(["riot"] * RIOT_N + ["police"] * POL_N + ["zombie"] * ZN, "po")
car = group("patrol"); K.box("car_body", (1.8, 4.6, 1.0), (0, 0, .75), emat("car_w", (.8, .8, .82), .3), bevel=.15, parent=car)
K.box("car_low", (1.82, 4.62, .5), (0, 0, .45), emat("car_b", (.02, .02, .02), .3), bevel=.1, parent=car)
K.box("car_top", (1.5, 2.3, .55), (0, .2, 1.5), emat("car_g", (.04, .05, .07), .1, .3), bevel=.12, parent=car)
LIGHTBAR = K.box("lightbar", (1.1, .3, .15), (0, .2, 1.85), emat("lb", (.3, .02, .02), .3, emit=(1, .05, .03), k=6.0), bevel=.05, parent=car)
bus = group("riotbus"); K.box("bus_b", (2.5, 10, 3.0), (0, 0, 1.9), emat("bus", (.05, .07, .14), .5), bevel=.2, parent=bus); K.box("bus_w", (2.52, 7, .6), (0, .5, 2.6), emat("bus_w", (.01, .01, .015), .1), bevel=.05, parent=bus)
car.location = bus.location = (0, 0, -500)

# 自衛隊の場面（l11）：夜の道路、防護柵、装甲車、迫るゾンビ
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

# 電車・道路の場面のゾンビ（l08・l10）
MZN = 80
A_MISC = Actors(["zombie"] * MZN, "mi")

# ---------------------------------------------------------------- インフラ 1：止まった電車（新宿の線路の区画、x≈780）
TRAIN = group("train"); TX = 780.0
steel = emat("steel", (.55, .57, .6), .35, .7); stripe = emat("stripe", (.05, .32, .2), .4)
winm = emat("train_win", (.02, .02, .02), .1, emit=(1, .86, .62), k=7.0); dark = emat("dark", (.015, .015, .02), .3)
ballast = emat("ballast", (.16, .15, .14), .95); rail = emat("rail", (.3, .28, .26), .4, .8)
for c in range(10):
    y0 = -150 + c * 20.5
    K.box(f"car{c}", (2.9, 20, 3.0), (TX, y0, 2.1), steel, bevel=.25, parent=TRAIN)
    K.box(f"cars{c}", (2.92, 19.6, .25), (TX, y0, 1.35), stripe, bevel=.02, parent=TRAIN)
    for w_ in range(5):
        K.box(f"cw{c}_{w_}", (2.94, 2.6, .8), (TX, y0 - 7.6 + w_ * 3.8, 2.5), winm, bevel=.02, parent=TRAIN)
    for d_ in range(4):
        K.box(f"cd{c}_{d_}", (2.95, 1.3, 2.0), (TX, y0 - 5.7 + d_ * 3.8, 1.9), dark, bevel=.02, parent=TRAIN)
K.box("ballast", (14, 1400, .6), (TX, 100, .3), ballast, bevel=0, parent=TRAIN)
for xr in (TX - .75, TX + .75, TX - 4.75, TX - 3.25, TX + 3.25, TX + 4.75):
    K.box(f"rail{xr}", (.08, 1400, .16), (xr, 100, .68), rail, bevel=0, parent=TRAIN)
for k in range(-12, 16):   # 架線の柱
    K.tube((TX - 6.5, k * 50, 0), (TX - 6.5, k * 50, 7.5), .14, granite, TRAIN, 8); K.box(f"arm{k}", (12, .15, .15), (TX - 1, k * 50, 7.3), granite, bevel=0, parent=TRAIN)
SIG = K.box("signal", (.5, .2, .5), (TX - 6.3, -175, 5.5), emat("sig", (.3, .02, .02), .3, emit=(1, .03, .02), k=12.0), bevel=.05, parent=TRAIN)
TRAIN.location = (0, 0, -900)

# ---------------------------------------------------------------- インフラ 2：乗り捨てられた車でふさがる高速道路（街の南の外れ、y≈-4750、高さ 9 m）
HW = group("highway"); HY, HZ = -4750.0, 9.0
deck = emat("deck", (.18, .18, .19), .85)
K.box("deck", (1400, 24, 1.2), (0, HY, HZ - .6), deck, bevel=0, parent=HW)
for sy in (-12.2, 12.2, 0):
    K.box(f"wall{sy}", (1400, .35, 1.1), (0, HY + sy, HZ + .55), granite, bevel=.03, parent=HW)
for k in range(-14, 15):
    K.box(f"pier{k}", (2.2, 7, HZ - .6), (k * 50, HY, (HZ - .6) / 2), granite, bevel=.1, parent=HW)
lane = emat("lane", (.8, .8, .78), .6)
for sy in (-8, -4, 4, 8):
    for k in range(-70, 70):
        K.box(f"ln{sy}_{k}", (4, .15, .02), (k * 10, HY + sy, HZ + .01), lane, bevel=0, parent=HW)
CARC = [(.6, .62, .65), (.05, .05, .06), (.75, .75, .74), (.35, .03, .03), (.05, .1, .25), (.5, .45, .3), (.15, .17, .2)]
cmats = [emat(f"cc{i}", c, .3, .5) for i, c in enumerate(CARC)]
cabin = emat("cabin", (.02, .025, .03), .08, .3)
HAZ = emat("hazard", (.4, .2, .02), .4, emit=(1, .45, .05), k=0.)
HAZ_K = HAZ.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
hr = random.Random(7)
for k in range(110):
    x = hr.uniform(-420, 420); ly = hr.choice([-10, -6, -2, 2, 6, 10]) + hr.uniform(-.6, .6); a = hr.uniform(-.25, .25) + (math.pi if ly > 0 else 0)
    cg = group(f"hcar{k}"); cg.parent = HW; cg.location = (x, HY + ly, HZ); cg.rotation_euler = (0, 0, a + math.pi / 2)
    K.box(f"hb{k}", (1.8, 4.5, .9), (0, 0, .65), cmats[k % len(cmats)], bevel=.15, parent=cg); K.box(f"hc{k}", (1.6, 2.4, .6), (0, .2, 1.35), cabin, bevel=.15, parent=cg)
    if k % 2 == 0:
        for sx in (-.7, .7):
            K.box(f"hz{k}{sx}", (.25, .05, .12), (sx, 2.27, .85), HAZ, bevel=0, parent=cg)
for k in range(40):   # 遠くのビル（夕方の空に影）
    x = hr.uniform(-1500, 1500); K.box(f"hbg{k}", (hr.uniform(30, 70), 40, 1), (x, HY + hr.uniform(400, 900), 0), glass, bevel=0, parent=HW)
    o = bpy.context.object; o.scale = (1, 1, hr.uniform(40, 180)); o.location.z = o.scale.z / 2
HW.location = (0, 0, -900)

# ---------------------------------------------------------------- v2.3：ご当地の名所（ユーザー「仙台、大阪、北海道で、その観光名所でかまれる人のカットを」）。模式（実際の形を簡略に）
LMK = {}
bronze = emat("bronze", (.09, .085, .06), .45, .7); gold = emat("gold", (.95, .68, .22), .3, 1.0); white = emat("lm_white", (.82, .82, .8), .7)
roofg = emat("roof_green", (.12, .3, .26), .5, .3); roofr = emat("roof_red", (.42, .1, .07), .6); stone = emat("lm_stone", (.36, .35, .33), .9)
gravel = emat("gravel", (.42, .4, .36), .95); dkwin = emat("lm_win", (.03, .04, .04), .2); dial = emat("dial", (.9, .9, .86), .5)


def lm_group(name, ground):
    g = group("lm_" + name); K.box(f"{name}_ground", (900, 900, .2), (0, 0, -.1), ground, bevel=0, parent=g)
    for k in range(18):   # 周りの木
        a = k / 18 * 2 * math.pi; x, y = 60 * math.cos(a) + RND.uniform(-6, 6), 60 * math.sin(a) + 40 + RND.uniform(-6, 6)
        K.tube((x, y, 0), (x, y, 4), .3, trunk_m, g, 8); bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=4, location=(x, y, 7)); o = bpy.context.object; o.data.materials.append(tree_m); o.parent = g
    LMK[name] = g; return g


def pyramid(name, w, h, z, m, parent, d=None, x=0., y=0.):
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=w / math.sqrt(2), radius2=0, depth=h, location=(x, y, z + h / 2), rotation=(0, 0, math.pi / 4))
    o = bpy.context.object; o.name = name; o.data.materials.append(m)
    if d:
        o.scale = (1, d / w, 1)
    o.parent = parent; return o


# 仙台：青葉城跡の伊達政宗の騎馬像（三日月の前立ての兜）
g = lm_group("sendai", gravel); SX, SY = 3.0, 17.0
K.box("sd_base", (10, 10, 2.5), (SX, SY, 1.25), stone, bevel=.1, parent=g); K.box("sd_ped", (3.6, 6.0, 6.5), (SX, SY, 5.75), granite, bevel=.08, parent=g)
hz = 9.0
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(SX, SY, hz + 2.1)); o = bpy.context.object; o.scale = (.62, 1.45, .7); o.data.materials.append(bronze); o.parent = g   # 馬の胴
K.tube((SX, SY - 1.2, hz + 2.3), (SX, SY - 1.9, hz + 3.6), .38, bronze, g, 12); K.box("sd_head", (.45, 1.0, .5), (SX, SY - 2.3, hz + 3.7), bronze, bevel=.12, parent=g)
for (lx, ly, up) in [(-.35, -.9, 1), (.35, -.9, 0), (-.35, .9, 0), (.35, .9, 0)]:
    if up:   # 前足を上げる
        K.tube((SX + lx, SY + ly, hz + 1.8), (SX + lx, SY + ly - .8, hz + 1.2), .15, bronze, g, 8)
    else:
        K.tube((SX + lx, SY + ly, hz + 1.8), (SX + lx, SY + ly, hz), .15, bronze, g, 8)
K.tube((SX, SY + 1.4, hz + 2.4), (SX, SY + 2.2, hz + 1.2), .12, bronze, g, 8)   # しっぽ
K.tube((SX, SY + .1, hz + 2.7), (SX, SY - .1, hz + 3.9), .38, bronze, g, 12)   # 政宗の胴
bpy.ops.mesh.primitive_uv_sphere_add(radius=.3, location=(SX, SY - .15, hz + 4.2)); o = bpy.context.object; o.data.materials.append(bronze); o.parent = g
for i in range(16):   # 三日月の前立て（金）
    a0, a1 = math.radians(200 + i * 140 / 16), math.radians(200 + (i + 1) * 140 / 16); R0 = .95
    K.tube((SX + R0 * math.cos(a0), SY - .45, hz + 5.25 + R0 * math.sin(a0)), (SX + R0 * math.cos(a1), SY - .45, hz + 5.25 + R0 * math.sin(a1)), .07 * (1 - abs(i - 7.5) / 9), gold, g, 6)
for k in range(10):   # 石垣の上の手すり
    K.box(f"sd_rail{k}", (2.0, .15, .9), (SX - 10 + k * 2.2, SY - 9, .45), stone, bevel=.03, parent=g)
# 大阪：大阪城の天守（白い壁・緑の屋根・金の飾り）
g = lm_group("osaka", gravel); OX, OY = 10.0, 150.0
K.box("os_base", (60, 60, 14), (OX, OY, 7), stone, bevel=.5, parent=g)
z = 14.0
for i, w in enumerate([40, 34, 28, 22, 17]):
    hgt = 8.5 if i < 4 else 9.5
    K.box(f"os_wall{i}", (w, w * .85, hgt), (OX, OY, z + hgt / 2), white, bevel=.1, parent=g)
    K.box(f"os_band{i}", (w + .2, w * .85 + .2, .8), (OX, OY, z + hgt - 1.2), gold if i == 4 else roofg, bevel=.05, parent=g)
    nw = max(2, w // 6)
    for j in range(nw):   # 窓
        K.box(f"os_win{i}_{j}", (1.6, w * .85 + .3, 1.4), (OX - w / 2 + 3 + j * (w - 6) / max(1, nw - 1), OY, z + hgt * .5), dkwin, bevel=0, parent=g)
    pyramid(f"os_roof{i}", w + 7, 4.2 if i < 4 else 7, z + hgt - .4, roofg, g, d=(w + 7) * .85, x=OX, y=OY)
    z += hgt + (2.4 if i < 4 else 0)
for sx in (-3.5, 3.5):
    K.box(f"os_shachi{sx}", (1.0, .8, 2.2), (OX + sx, OY, z + 4.5), gold, bevel=.2, parent=g)
# 札幌：時計台（白い木造の 2 階建て・赤い屋根・時計の塔）。周りはビル
g = lm_group("sapporo", gravel); PX, PY = 3.0, 34.0
K.box("sp_body", (20, 12, 8), (PX, PY, 4), white, bevel=.05, parent=g)
for k in range(9):
    K.box(f"sp_win{k}", (1.2, 12.2, 1.9), (PX - 8 + k * 2, PY, 2.2 + 3.6 * (k % 2)), dkwin, bevel=0, parent=g)
me = bpy.data.meshes.new("sp_roof"); bm = bmesh.new(); hw, hd, rh = 10.8, 6.8, 4.2
vs = [bm.verts.new(v) for v in [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0), (-hw, 0, rh), (hw, 0, rh)]]
for f_ in [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (0, 3, 2, 1)]:
    bm.faces.new([vs[i] for i in f_])
bm.to_mesh(me); bm.free(); o = bpy.data.objects.new("sp_roof", me); sc.collection.objects.link(o); me.materials.append(roofr); o.location = (PX, PY, 8); o.parent = g
K.box("sp_tower", (3.8, 3.8, 6.5), (PX, PY - 4, 11.5), white, bevel=.04, parent=g)
for (dx, dy, rz) in [(0, -1.95, 0), (0, 1.95, 0), (-1.95, 0, math.pi / 2), (1.95, 0, math.pi / 2)]:   # 4 面の時計
    K.box(f"sp_clock{dx}{dy}", (2.6, .08, 2.6), (PX + dx, PY - 4 + dy, 13.0), dial, rot=(0, 0, rz), bevel=0, parent=g)
    K.box(f"sp_h1{dx}{dy}", (.12, .1, 1.0), (PX + dx * 1.03, PY - 4 + dy * 1.03, 13.35), dkwin, rot=(0, 0, rz), bevel=0, parent=g)
    K.box(f"sp_h2{dx}{dy}", (.8, .1, .12), (PX + dx * 1.03 + (.3 if rz == 0 else 0), PY - 4 + dy * 1.03 + (.3 if rz else 0), 13.0), dkwin, rot=(0, 0, rz), bevel=0, parent=g)
pyramid("sp_troof", 4.6, 3.0, 14.75, roofr, g, x=PX, y=PY - 4)
K.tube((PX, PY - 4, 17.6), (PX, PY - 4, 20), .08, dkwin, g, 6)
for k, (bx, by, bh) in enumerate([(-40, 70, 60), (-10, 80, 90), (30, 75, 70), (55, 60, 50), (-60, 40, 45)]):   # 周りのビル
    K.box(f"sp_bld{k}", (26, 22, bh), (bx, by, bh / 2), glass, bevel=0, parent=g)
for gg in LMK.values():
    gg.location = (0, 0, -900)
A_CUT = Actors(["man", "woman", "child", "elder", "man", "woman", "man", "woman", "man", "elder", "zombie", "zombie", "zombie", "zombie", "zombie"], "cu")

# ---------------------------------------------------------------- 表示の切り替え
def hide_tree(o, h):
    o.hide_render = h
    for c in o.children_recursive:
        c.hide_render = h


def show(city=False, plaza=False, maps=None, emit=0., windows=0., tod="day"):
    for a in (A_PLAZA, A_POL, A_SDF, A_MISC, A_CUT):
        if a:
            a.hide()
    for gg in LMK.values():
        gg.location = (0, 0, -900)
    hide_tree(CITY, not city); hide_tree(PLAZA, not plaza); TRAIN.location = HW.location = (0, 0, -900)
    for M_ in (MAPK, MAPJ):
        M_["obj"].hide_render = maps != M_["name"]
    OCEAN.hide_render = maps is None
    G_K.inputs[1].default_value = emit; B_K.inputs[1].default_value = emit * .35; WIN_K.inputs[1].default_value = windows; BLACK_T.default_value = -1.0
    cam.o.data.dof.use_dof = False
    car.location = bus.location = bar.location = apc.location = (0, 0, -500)
    for l in lamps + [heli, flood]:
        l.data.energy = 0
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
    if maps:   # 地図：色が鈍らないように（昼と夜は renderer.html が背景の色で描く）
        sc.view_settings.view_transform = "Standard"; sc.view_settings.look = "None"; sky.set(0, -12, 160, 0.0); set_haze((.0, .0, .0), 0.); sc.view_settings.exposure = -1.6
    elif tod == "day":   # 曇りの正午（暗めの色調）
        sky.set(0, 80, 180, 1.4); set_haze((.42, .46, .52), 1.0); sc.view_settings.exposure = -1.2
    elif tod == "dusk":   # 夕方（西の低い太陽）
        sky.set(0, 4.5, 280, 3.0); set_haze((.3, .2, .17), .7); sc.view_settings.exposure = -.2
    else:
        sky.set(0, -12, 160, 0.0); set_haze((.006, .008, .016), 1.0); sc.view_settings.exposure = -.6


def shake(f, amp, seed=0):
    r = random.Random(f * 7 + seed); return Vector(((r.random() - .5) * amp, (r.random() - .5) * amp, (r.random() - .5) * amp * .6))


# ---------------------------------------------------------------- ショット
EYE0 = ((6.5, 1.2, 1.55), (-2, -.3, 1.45), 28)   # 冒頭の構図（最後のショットはここで終わる）
def crowd_pose(ts, f):
    P, S, Hd, V = CROWD.at(ts); A_PLAZA.pose(P, S, Hd, f, V=V, t=ts, TB=CROWD.TB)

def s_l00():
    show(plaza=True, city=True); cam.o.data.dof.use_dof = True; cam.o.data.dof.focus_distance = 6.4; cam.o.data.dof.aperture_fstop = 2.8
def a_l00(u, t, f):   # 都庁を背に、ジタバタする一体。周りの人はまだ気づかない
    T = SHOT_T["l00"]; crowd_pose(T[0] + t, f)
    cam.look(mix(EYE0[0], (5.4, 1.0, 1.5), K.ease(u)), EYE0[1], EYE0[2] + 4 * u)

def s_l01():
    show(plaza=True, city=True); cam.o.data.dof.use_dof = True; cam.o.data.dof.aperture_fstop = 2.4
def a_l01(u, t, f):   # スペックの札：ジタバタする一体の周りを回る（札は上、ゾンビは画面の下）
    T = SHOT_T["l01"]; crowd_pose(T[0] + t, f)
    a = math.radians(75 - 50 * K.ease(u)); p = (3.4 * math.cos(a), 3.4 * math.sin(a), .9)
    cam.look(p, (0, 0, 1.85), 30); cam.o.data.dof.focus_distance = 3.4

def s_l02():
    show(plaza=True, city=True); cam.o.data.dof.use_dof = True; cam.o.data.dof.aperture_fstop = 2.0
def a_l02(u, t, f):   # 最初の一人：気づいて振り向き、走り、かまれて倒れる（スロー）。カメラは倒れる人の目の前
    ts = clock("l02", t); crowd_pose(ts, f)
    P, S, _, _ = CROWD.at(ts); vx, vy = float(P[1][0]), float(P[1][1]); zx, zy = float(P[0][0]), float(P[0][1])
    at = Vector((vx * .55 + zx * .45, vy * .55 + zy * .45, 1.15 - .2 * K.ease(clamp((ts - 1.1) / .5))))   # 二人の間（かまれたあとは、倒れた人へ少し下げる）
    pos = Vector(mix((9.7, -5.4, 1.2), (9.1, -4.9, 1.0), K.ease(u)))
    hit = clamp(1 - (ts - 1.1) / .9) if ts > 1.05 else 0.
    pos += shake(f, .08 * hit); cam.look(pos, at, 30 + 10 * K.ease(clamp((ts - .7) / .8)))
    cam.o.data.dof.focus_distance = (pos - at).length

def s_l03():
    show(plaza=True, city=True)
def a_l03(u, t, f):   # 地上：逃げまどう人と、かみに行くゾンビ（3 倍速）。広場の東から都庁を背に、群れがこちらへ
    ts = clock("l03", t); crowd_pose(ts, f)
    c = sum((CROWD.centroid(ts + d) for d in np.linspace(-1.2, 1.2, 7)), np.zeros(2)) / 7; c = c * .7 + np.array([5, -2]) * .3
    e = K.ease(u); cam.look(mix((34, -16, 1.5), (27, -5, 2.4), e), (c[0], c[1], 1.1), 22)

def s_l04():
    show(plaza=True, city=True)
def a_l04(u, t, f):   # 広場の上へ：最初の 20 人ほど（10 倍速）。議事堂の壁を越える前に高くなる
    ts = clock("l04", t); crowd_pose(ts, f)
    c = sum((CROWD.centroid(ts + d) for d in (-3, -1.5, 0, 1.5, 3)), np.zeros(2)) / 5; c = c * .5 + np.array([-15, 0]) * .5
    e = K.ease(u); cam.look(mix((30, -8, 4), (44, -4, 4), e)[:2] + (4 + 48 * K.ease(min(1, u * 1.7)),), (c[0], c[1], 0), 24)

def s_l05():
    show(plaza=True, city=True, emit=8.0); city_tex(["2", "3"])
def a_l05(u, t, f):   # 300 m：西新宿のオフィス街へ（計算の 2〜3 分）
    key_city(clock("l05", t), f); cam.look(mix((900, -1350, 380), (1050, -1700, 650), K.ease(u)), (420, 80, 0), 30)

def s_l06():
    show(plaza=True, city=True); city_tex(["3", "5"])
def a_l06(u, t, f):   # 警察官と機動隊：盾の列。ゾンビは盾に体当たりし、跳び越える
    car.location = (12, -40, 0); car.rotation_euler = (0, 0, math.radians(15)); LIGHTBAR.rotation_euler = (0, 0, t * 6)
    bus.location = (-6, -44, 0); bus.rotation_euler = (0, 0, math.radians(95))
    N = RIOT_N + POL_N + ZN; P = np.zeros((N, 2)); S = np.zeros(N, int); Hd = np.full(N, math.pi / 2); Z = np.zeros(N); V = np.zeros(N)
    LINE = -31.0
    for k in range(RIOT_N):
        P[k] = (-4 + k * 1.15, LINE - .2 * math.sin(k)); V[k] = 0
    for k in range(POL_N):
        P[RIOT_N + k] = (-1 + k * 3.2, LINE - 3.2)
    rr = random.Random(5)
    for k in range(ZN):
        j = RIOT_N + POL_N + k; x0 = rr.uniform(-6, 8); y0 = -26 + rr.uniform(0, 28); t0 = rr.uniform(0, 1.2)
        y = y0 - 10.4 * max(0, t - t0); leap = rr.random() < .45; V[j] = 10
        if y <= LINE + 1.0:
            over = (LINE + 1.0 - y) / 10.4   # 列に着いてからの秒
            if leap:   # 跳び越える：0.55 秒で 4.5 m、高さ 1.8 m
                v = clamp(over / .55); y = LINE + 1.0 - 4.5 * v; Z[j] = 1.8 * math.sin(math.pi * v)
                if v >= 1:
                    y = LINE - 3.5 - .6 * clamp((over - .55) / .4)
            else:   # 盾に体当たりして、ジタバタ押し合う
                y = LINE + .75 + .12 * math.sin(t * 9 + k); V[j] = 0
        P[j] = (x0, y); S[j] = 2; Hd[j] = -math.pi / 2
    zs = P[RIOT_N + POL_N:]
    for k in range(RIOT_N + POL_N):   # 跳び越えて着地したゾンビに取りつかれた警察官はのけぞる
        dd = np.hypot(zs[:, 0] - P[k][0], zs[:, 1] - P[k][1]); S[k] = 1 if ((dd < 1.4) & (zs[:, 1] < LINE - 2.5)).any() else 0
    A_POL.pose(P, S, Hd, f, Z=Z, V=V)
    cam.look(mix((7, -41, 1.6), (12, -46, 4.5), K.ease(u)), mix((2, -14, 2.6), (1, -26, 1.2), K.ease(u)), 24)

def s_l07():
    show(plaza=True, city=True, emit=8.0); city_tex(["5", "7", "10"])
def a_l07(u, t, f):   # 1 km → 5 km：都心へ（計算の 5〜10 分）
    key_city(clock("l07", t), f); cam.look(mix((200, -2400, 900), (600, -6800, 5200), K.ease(u)), (600, 200, 0), 28)

def s_l08():
    show(city=True, emit=.3); city_tex(["10"]); TRAIN.location = (0, 0, 0); B_K.inputs[1].default_value = .05
def a_l08(u, t, f):   # インフラ：止まった電車。線路の上をうろつくゾンビ
    rr = random.Random(11); P = np.zeros((MZN, 2)); S = np.full(MZN, 2); Hd = np.zeros(MZN)
    for k in range(MZN):
        side = rr.choice([-1, 1]); x = TX + side * rr.uniform(2.0, 9); y = rr.uniform(-170, 60)
        if rr.random() < .35:   # 窓に張りついてジタバタ
            x = TX + side * 1.85; hd = math.pi if side > 0 else 0.
        else:
            a = rr.uniform(0, 2 * math.pi); s_ = rr.uniform(.6, 2.0); x += math.cos(a) * s_ * t; y += math.sin(a) * s_ * t; hd = a
        P[k] = (x, y); Hd[k] = hd
    A_MISC.pose(P, S, Hd, f, V=np.zeros(MZN))
    cam.look(mix((796, -196, 7), (800, -160, 12), K.ease(u)), mix((781, -135, 2.0), (780, -95, 1.5), K.ease(u)), 28)

def s_l10():
    show(city=True, tod="dusk"); HW.location = (0, 0, 0)
def a_l10(u, t, f):   # インフラ：乗り捨てられた車の道路（夕方）。ハザードがゆっくり点滅
    key_fac(HAZ_K, 2.5 + 2.5 * math.sin(t * 2 * math.pi * .9), f)
    rr = random.Random(23); P = np.zeros((MZN, 2)); S = np.full(MZN, 2); Hd = np.zeros(MZN)
    for k in range(MZN):
        x = rr.uniform(-330, 0); y = HY + rr.uniform(-11, 11); a = rr.uniform(0, 2 * math.pi); s_ = rr.uniform(.5, 1.8)
        P[k] = (x + math.cos(a) * s_ * t, y + math.sin(a) * s_ * t * .3); Hd[k] = a
    A_MISC.pose(P, S, Hd, f, oz=HZ, V=np.zeros(MZN))
    cam.look(mix((-352, HY - 14, 16), (-322, HY - 12, 13), K.ease(u)), mix((-250, HY + 3, 8), (-215, HY + 4, 8), K.ease(u)), 28)

def s_l09():
    show(maps="kanto"); map_textures(MAPK, ["0.5h", "1h", "2h", "3h", "6h"])
def a_l09(u, t, f):   # 30 km → 60 km：関東へ（30 分〜6 時間）
    key_map(MAPK, clock("l09", t), f); cam.look(mix((0, -60000, 50000), (0, -110000, 120000), K.ease(u)), (0, 8000, 0), 30)

SDF_O = (25.0, -150.0)   # 自衛隊の場面の位置：都庁前の広場の南（夜の都庁が見える）
def s_l11():
    show(plaza=True, city=True, tod="night", windows=6.0); bar.location = (SDF_O[0], SDF_O[1], 0); apc.location = (SDF_O[0] + 8, SDF_O[1] - 9, 0)
def a_l11(u, t, f):   # 真夜中の道路：自衛隊の防衛線。闇の向こうから迫る赤い影
    P = np.zeros((SDF_N + SZN, 2)); S = np.zeros(SDF_N + SZN, int); Hd = np.zeros(SDF_N + SZN); fall = np.zeros(SDF_N + SZN, bool); V = np.zeros(SDF_N + SZN)
    for k in range(SDF_N):
        P[k] = (-12 + k * 2.2, -1.2); Hd[k] = -math.pi / 2 + math.pi
    for k in range(SZN):
        x0 = ((k * 7.3) % 40) - 20; y0 = 45 + (k * 13.7) % 70; s_ = 10.4 * max(0, t + .5 - .05 * k)
        y = y0 - s_; dead_at = 9 + (k * 5.3) % 30; V[SDF_N + k] = 10
        if y < dead_at:
            y = dead_at; fall[SDF_N + k] = True
        P[SDF_N + k] = (x0, y); S[SDF_N + k] = 2; Hd[SDF_N + k] = -math.pi / 2
    A_SDF.pose(P, S, Hd, f, ox=SDF_O[0], oy=SDF_O[1], fall=fall, V=V)
    ox, oy = SDF_O
    for k, l in enumerate(lamps):
        l.location = (ox - 16 + k * 6.5, oy + 6 + (k % 2) * 14, 8); l.data.energy = 30000
    heli.location = (ox + 10 * math.sin(t * .4), oy + 30 + 3 * t, 45); heli.data.energy = 3e6
    heli.rotation_euler = (Vector((ox, oy + 50 + 8 * t, 0)) - heli.location).to_track_quat("-Z", "Y").to_euler()
    for o in (heli,):
        o.keyframe_insert("location", frame=f + 1); o.keyframe_insert("rotation_euler", frame=f + 1)
    cam.look(mix((ox + 3.5, oy - 5.5, 1.9), (ox + 2.5, oy - 8, 3.0), K.ease(u)), (ox - 1, oy + 30, 1.2), 26)

def s_l12():
    show(maps="kanto"); map_textures(MAPK, ["24h", "48h", "3d", "5d", "7d"])
def a_l12(u, t, f):   # 1 日 → 7 日：広がりが止まる（ほとんど動かない）
    key_map(MAPK, clock("l12", t), f); cam.look(mix((0, -115000, 125000), (0, -120000, 135000), u), (0, 8000, 0), 30)

def s_l13():
    show(maps="japan"); map_textures(MAPJ, ["7d", "8d"])
def a_l13(u, t, f):   # 日本の上から：家の籠城が限界（7 日 → 8 日）
    key_map(MAPJ, clock("l13", t), f); cam.look(mix((0, -330000, 300000), (0, -360000, 360000), K.ease(u)), (0, 0, 0), 30)

def s_l14():
    show(plaza=True, city=True, tod="night", windows=3.0, emit=2.5); city_tex(["10"])
def a_l14(u, t, f):   # インフラ：夜の街の明かりが地区ごとに消えていく（停電）
    key_fac(BLACK_T, -.2 + .95 * K.ease(clamp(u * 1.15)), f)
    cam.look(mix((1500, -2700, 950), (1250, -2350, 820), K.ease(u)), (250, 150, 0), 32)

# 地図の上の都市（make_maps.py と同じ投影：都庁が原点、東へ x、北へ y、m）
def lonlat(lat, lon):
    return ((lon - 139.6920) * 111320 * math.cos(math.radians(35.6893)), (lat - 35.6893) * 110950)
SENDAI, OSAKA, SAPPORO = lonlat(38.268, 140.872), lonlat(34.686, 135.520), lonlat(43.062, 141.354)

def s_l15():
    show(maps="japan"); map_textures(MAPJ, ["8d", "10d"])
def a_l15(u, t, f):   # 名古屋・仙台へ。最後は仙台に寄る
    key_map(MAPJ, clock("l15", t), f); e = K.ease(u)
    cam.look(mix((0, -360000, 360000), (SENDAI[0], SENDAI[1] - 70000, 120000), e), mix((-40000, 0, 0), (SENDAI[0], SENDAI[1], 0), e), 30)

def s_l16():
    show(maps="japan"); map_textures(MAPJ, ["10d", "14d"])
def a_l16(u, t, f):   # 大阪へ。仙台から引いて、大阪に寄る
    key_map(MAPJ, clock("l16", t), f); e = K.ease(u)
    cam.look(mix((SENDAI[0] - 60000, SENDAI[1] - 300000, 420000), (OSAKA[0], OSAKA[1] - 70000, 120000), e), mix((SENDAI[0] - 120000, SENDAI[1] - 100000, 0), (OSAKA[0], OSAKA[1], 0), e), 30)

def s_l17():
    show(maps="japan"); map_textures(MAPJ, ["14d", "21d", "22d", "30d", "45d", "60d"])
def a_l17(u, t, f):   # 3 週間 → 2 か月：四国・九州・北海道へ
    key_map(MAPJ, clock("l17", t), f); e = K.ease(u)
    cam.look(mix((OSAKA[0], OSAKA[1] - 250000, 420000), (-60000, -1000000, 1500000), e), mix((OSAKA[0], OSAKA[1], 0), (-80000, 220000, 0), e), 30)

def s_l19():
    show(maps="japan"); map_textures(MAPJ, ["60d", "90d"])
def a_l19(u, t, f):   # 宇宙から、札幌に寄る
    key_map(MAPJ, clock("l19", t), f); e = K.ease(u)
    cam.look(mix((-60000, -1000000, 1500000), (SAPPORO[0], SAPPORO[1] - 70000, 120000), e), mix((-80000, 220000, 0), (SAPPORO[0], SAPPORO[1], 0), e), 30)

# 名所のカット：名所を背に写真を撮っていた人へ、ゾンビがジタバタ走ってきてかむ。周りの人は逃げる
def cut_action(t, f, cam_from, cam_to, look, lens=26, seed=1):
    rr = random.Random(seed); N = 15; P = np.zeros((N, 2)); S = np.zeros(N, int); Hd = np.full(N, math.pi / 2); V = np.zeros(N); TB = np.full(N, 1e9)
    tb = .5 + 9.3 / 10.4   # 先頭のゾンビが最初の人に着く時刻
    zt = clamp((t - .5) / (tb - .5)); P[10] = (9.0 - 8.6 * zt, 3.0 - 2.85 * zt); Hd[10] = math.atan2(-2.85, -8.6); V[10] = 10 if zt < 1 else 0
    P[0] = (0, 0); Hd[0] = math.pi / 2 if t < 1.0 else math.atan2(P[10][1], P[10][0])   # 名所を向いて写真 → 振り向く
    if t >= tb:
        S[0] = 1; TB[0] = tb
    for k in range(1, 10):   # 周りの人：気づいたら逃げる
        x0, y0 = rr.uniform(-12, 12), rr.uniform(-4, 14)
        if abs(x0) < 2.5 and abs(y0) < 2.5:
            x0 += 5
        run = max(0, t - .9 - .15 * k); d = Vector((x0 - 9, y0 - 3)).normalized(); hd0 = rr.uniform(0, 6.28)
        P[k] = (x0 + d.x * 3.2 * run, y0 + d.y * 3.2 * run); Hd[k] = math.atan2(d.y, d.x) if run > 0 else hd0; V[k] = 3.2 if run > 0 else 0
    for k in range(11, 15):   # 後ろから走ってくるゾンビ
        x0, y0 = rr.uniform(16, 30), rr.uniform(-6, 16); run = max(0, t - .3 - .2 * (k - 11)); tx, ty = rr.uniform(-6, 6), rr.uniform(0, 10)
        d = Vector((tx - x0, ty - y0)); L_ = d.length; s_ = min(L_, 10.4 * run); d.normalize(); P[k] = (x0 + d.x * s_, y0 + d.y * s_); Hd[k] = math.atan2(d.y, d.x); S[k] = 2; V[k] = 10
    S[10] = 2
    A_CUT.pose(P, S, Hd, f, V=V, t=t, TB=TB)
    hit = clamp(1 - (t - tb) / .8) if t > tb else 0.
    pos = Vector(mix(cam_from, cam_to, K.ease(clamp(t / 2.6)))) + shake(f, .06 * hit); cam.look(pos, look, lens)

def s_m01():
    show(tod="day"); sc.view_settings.exposure = -.55; LMK["sendai"].location = (0, 0, 0)
def a_m01(u, t, f):   # 仙台：青葉城跡の騎馬像を背に
    cut_action(t, f, (-1.5, -9.0, 1.3), (-1.2, -7.8, 1.2), (2.5, 12.0, 4.6), 26, 11)

def s_m02():
    show(tod="day"); sc.view_settings.exposure = -.55; LMK["osaka"].location = (0, 0, 0)
def a_m02(u, t, f):   # 大阪：大阪城を背に
    cut_action(t, f, (-1.5, -9.5, 1.2), (-1.2, -8.2, 1.15), (4.0, 60.0, 16.0), 22, 12)

def s_m03():
    show(tod="day"); sc.view_settings.exposure = -.55; LMK["sapporo"].location = (0, 0, 0)
def a_m03(u, t, f):   # 札幌：時計台を背に
    cut_action(t, f, (-1.5, -9.0, 1.3), (-1.2, -7.8, 1.2), (2.5, 20.0, 5.5), 24, 13)

def s_l18():
    show(plaza=True, city=True)
def a_l18(u, t, f):   # 90 日後の数を出す。画は冒頭の少し前の広場（最後のコマが冒頭の最初のコマにつながる）
    T = SHOT_T["l18"]; crowd_pose(T[0] + t, f)
    cam.look(mix((10.5, 2.2, 2.4), EYE0[0], K.ease(u)), EYE0[1], EYE0[2] - 4 * (1 - u))


NAMES = [s["id"] for s in PLAN["shots"]]
cues, END = K.shot_lengths(HERE)
D = {k: SPLAN[k]["dur"] for k in NAMES}
# 広場の時刻：l02 の始まりが t=0。冒頭（l00・l01）は t<0、最後のショット（l18）はさらにその前（冒頭につながる）
SHOT_T = {"l01": (-D["l01"], 0.0), "l00": (-D["l01"] - D["l00"], -D["l01"]), "l18": (-D["l01"] - D["l00"] - D["l18"], -D["l01"] - D["l00"])}
CROWD_SHOTS = {"l00", "l01", "l02", "l03", "l04", "l18"}   # 広場の人の動きの計算（約 7 分）は、これらを描くときだけ
if not O["shots"] or CROWD_SHOTS & set(O["shots"]):
    CROWD = Crowd(t0=SHOT_T["l18"][0] - 2, t1=62.0); A_PLAZA = Actors(CROWD.kind, "pl")
else:
    CROWD = A_PLAZA = None
SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in NAMES}
anim = [cam.o, car, LIGHTBAR, heli]   # 人とゾンビは Actors.pose が自分でキーを打つ
K.render_shots(HERE, SHOTS, NAMES, O, anim)
