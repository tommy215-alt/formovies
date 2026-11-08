"""pilot_046（全人類の体重が1日10%ずつ増えたら？）の 3D の場面（Blender、ext/blender/blkit.py）。もしも設計の既定（土台は pilot_045）。
使い方："C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b -P anatomy_room/production/pilot_046/blender/scene.py -- [ショット名 ...] [--still] [--samples N] [--every N] [--resume]
前もって python plan.py（blender/plan.json：ショットの長さと時計）と python production_script.py voice（work/timeline.json）。

ユーザーの指示（2026-11-07）：見た目はそのまま重さだけ増える・人類だけ・背景と色調は日常・壊れる所はスローで派手に・宇宙は短く。
場面はそれぞれ離れた場所に置き、使うときだけ原点に戻す（ほかは z=-900 に隠す）。人は顔のないピクトグラム。どれも模式。
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
RND = random.Random(46)
H0 = PLAN.get("start_hour", 7)


def clamp(v, a=0., b=1.):
    return max(a, min(b, v))


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def emat(name, col, rough=.6, metal=0., emit=None, k=0., alpha=None):
    m = K.mat(name, col, rough, metal); b = m.node_tree.nodes["Principled BSDF"]
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1); b.inputs["Emission Strength"].default_value = k
    if alpha is not None:
        b.inputs["Alpha"].default_value = alpha
    return m


def glassm(name, col=(.8, .9, 1.0), tw=.95, rough=.02):
    m = K.mat(name, col, rough); b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = tw; b.inputs["IOR"].default_value = 1.33; return m


def key_fac(sock, v, f):
    sock.default_value = v; sock.keyframe_insert("default_value", frame=f + 1)


def clock(k, t):
    s = SPLAN[k]; u = clamp(t / s["dur"]); c = s["c"]
    for (u0, c0), (u1, c1) in zip(c, c[1:]):
        if u <= u1 or (u1, c1) == tuple(c[-1]):
            v = clamp((u - u0) / max(1e-9, u1 - u0))
            if s.get("log") and c0 > 0 and c1 > 0:
                return math.exp(math.log(c0) + (math.log(c1) - math.log(c0)) * v)
            return c0 + (c1 - c0) * v
    return c[-1][1]


def hour_of(c):
    return (H0 + c / 3600.0) % 24


def ev_t(k, j):   # ポップアップ j の、ショットの中の秒（壊れる瞬間をそろえる）
    return SPLAN[k]["ev"][j][0]


# ---------------------------------------------------------------- 空：時計に合わせた太陽（日常の明るさ）
def set_sky(hour, f=None):
    el = 62 * math.sin(math.pi * (hour - 6) / 12) if 5 < hour < 19 else -8
    energy = 3.2 * clamp((el + 3) / 15)
    sky.set(0, el, 120 + 15 * (hour - 6), energy)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = .25 + .75 * clamp((el + 6) / 20)
    if f is not None:
        for prop in ("sun_elevation", "sun_rotation"):
            sky.node.keyframe_insert(prop, frame=f + 1)
        sky.sun.keyframe_insert("rotation_euler", frame=f + 1); sky.sun.data.keyframe_insert("energy", frame=f + 1)
        sc.world.node_tree.nodes["Background"].inputs[1].keyframe_insert("default_value", frame=f + 1)


# ---------------------------------------------------------------- ピクトグラムの人（pilot_045 と同じ形。顔なし、足もとが原点、-Y が前）
PM = {k: emat("p_" + k, c, .7) for k, c in {
    "suit": (.05, .07, .12), "shirt": (.8, .82, .85), "skin": (.66, .52, .42), "coat_w": (.62, .42, .3), "red": (.55, .08, .07),
    "skirt": (.15, .14, .2), "yellow": (.95, .75, .05), "gray": (.42, .42, .44), "white": (.88, .88, .88), "hair": (.05, .04, .03),
    "black": (.03, .03, .03), "kid": (.12, .35, .65), "swim": (.05, .25, .55), "green": (.15, .45, .25)}.items()}


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


def pict(kind, sit=False):
    """kind：man・woman・child・elder・swim・green。sit＝座った姿（太ももが前）"""
    mats = list(PM.keys()); I = lambda k: mats.index(k); bm = bmesh.new()
    s = {"child": .66, "elder": .93, "woman": .94}.get(kind, 1.0)
    body = {"man": "suit", "woman": "coat_w", "child": "kid", "elder": "gray", "swim": "swim", "green": "green"}[kind]
    hip = .86 * s; sh = 1.42 * s; top = 1.6 * s; lean = .25 if kind == "elder" else 0.
    fwd = lambda z: Vector((0, -(z - hip) * lean, z))
    leg = "black" if kind == "man" else ("skin" if kind in ("woman", "swim") else body)
    for x in (-.09, .09):
        if sit:
            cyl(bm, I(leg), (x * s, -.45 * s, 0), (x * s, -.45 * s, hip - .4 * s), .075 * s); cyl(bm, I(leg), (x * s, -.45 * s, hip - .4 * s), (x * s, 0, hip - .4 * s), .08 * s)
        else:
            cyl(bm, I(leg), (x * s, 0, 0), (x * s, 0, hip), .075 * s)
    if kind == "woman" and not sit:
        cyl(bm, I("skirt"), (0, 0, .38 * s), (0, 0, hip + .06), .27 * s, .15 * s, 16)
    z0 = hip - (.4 * s if sit else 0)
    cyl(bm, I(body), Vector((0, 0, z0)) + fwd(hip) - Vector((0, 0, hip)), fwd(sh) - Vector((0, 0, .4 * s if sit else 0)), .19 * s, .21 * s, 16)
    zt = top - (.4 * s if sit else 0)
    sph(bm, I("skin"), Vector((0, -(zt - hip) * lean, zt)), .125 * s)
    for x in (-.24, .24):
        cyl(bm, I(body if kind != "swim" else "skin"), Vector((x * s, 0, sh - .03 - (.4 * s if sit else 0))), Vector((x * s * 1.1, 0, hip + .1 - (.4 * s if sit else 0))), .055 * s)
    if kind == "woman":
        sph(bm, I("hair"), Vector((0, .03, zt + .02)), .135 * s, 1, 1, .95)
    if kind == "man":
        cube(bm, I("shirt"), Vector((0, -.17, sh - .1 - (.4 * s if sit else 0))), (.08, .02, .18))
    if kind == "child":
        cube(bm, I("red"), Vector((0, .2 * s, sh - .2 - (.4 * s if sit else 0))), (.3 * s, .14 * s, .34 * s))
    if kind == "elder":
        sph(bm, I("white"), Vector((0, .02, zt + .03)), .13 * s)
    me = bpy.data.meshes.new(f"pict_{kind}{'_sit' if sit else ''}"); bm.to_mesh(me); bm.free()
    for k in mats:
        me.materials.append(PM[k])
    for p in me.polygons:
        p.use_smooth = True
    return me


MESH = {k: pict(k) for k in ["man", "woman", "child", "elder", "swim", "green"]}
MESH.update({k + "_sit": pict(k, True) for k in ["man", "woman", "child"]})
KINDS = ["man", "woman", "man", "woman", "child", "elder", "man", "woman"]
PEOPLE = []   # 動かす人（毎コマ keyframe）


def person(kind, loc, heading=0., parent=None):
    o = bpy.data.objects.new("p", MESH[kind]); sc.collection.objects.link(o); o.location = loc; o.rotation_euler = (0, 0, heading); o.parent = parent
    return o


def keyp(o, f, loc=None, rot=None, scale=None):
    if loc is not None:
        o.location = loc; o.keyframe_insert("location", frame=f + 1)
    if rot is not None:
        o.rotation_euler = rot; o.keyframe_insert("rotation_euler", frame=f + 1)
    if scale is not None:
        o.scale = scale; o.keyframe_insert("scale", frame=f + 1)


def group(name, at):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); g["home"] = at; g.location = (0, 0, -900); return g


def box(name, s, loc, m, parent, rot=(0, 0, 0), bevel=0.):
    return K.box(name, s, loc, m, rot=rot, bevel=bevel, parent=parent)


# 材料（明るい日常）
wood = emat("wood", (.42, .26, .14), .5); wood2 = emat("wood2", (.5, .32, .18), .5); wall = emat("wall", (.82, .8, .74), .9); white = emat("white", (.9, .9, .88), .5)
fabric = emat("fabric", (.25, .35, .5), .9); concrete = emat("concrete", (.42, .42, .41), .9); asphalt = emat("asphalt", (.16, .16, .17), .9)
tile = emat("tile", (.75, .78, .78), .4); pooltile = emat("pooltile", (.25, .6, .75), .3); grass = emat("grass", (.16, .36, .1), .95); soil = emat("soil", (.32, .2, .11), .95)
steel = emat("steel", (.7, .72, .75), .3, .8); stripe = emat("stripe", (.1, .5, .25), .4); seat = emat("seat", (.15, .3, .6), .6); red = emat("redm", (.7, .08, .06), .5)
yellow = emat("yellowm", (.95, .78, .1), .5); dark = emat("darkm", (.04, .04, .05), .4); crack = emat("crack", (.02, .02, .02), .9)
window_day = emat("win_day", (.35, .5, .65), .05, .4); lamp_warm = emat("lamp_warm", (.9, .8, .6), .5, emit=(1, .85, .6), k=6)
water = glassm("water", (.55, .8, .9), .9, .03); tree_m = emat("tree", (.12, .32, .1), .9); trunk_m = emat("trunk", (.3, .2, .12), .9)
car_ms = [emat(f"car{i}", c, .25, .5) for i, c in enumerate([(.75, .1, .08), (.85, .85, .87), (.1, .2, .45), (.12, .12, .13)])]
carglass = glassm("carglass", (.6, .7, .8), .8, .05)


def tree(x, y, parent, s=1.):
    K.tube((x, y, 0), (x, y, 3 * s), .2 * s, trunk_m, parent, 8); bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=2.2 * s, location=(x, y, 4.2 * s)); o = bpy.context.object; o.data.materials.append(tree_m); o.parent = parent


def building(name, x, y, w, d, floors, parent, col=None, fh=3.4):
    """窓のある明るいビル。床ごとの箱（l12 で床が落ちる）"""
    m = col or emat(f"bld_{name}", (RND.uniform(.55, .85), RND.uniform(.55, .8), RND.uniform(.5, .75)), .7)
    slabs = []
    for i in range(floors):
        b_ = box(f"{name}_f{i}", (w, d, fh - .5), (x, y, i * fh + (fh - .5) / 2 + .5), m, parent); slabs.append(b_)
        box(f"{name}_w{i}", (w + .05, d + .05, 1.4), (x, y, i * fh + 1.9), window_day, parent)
    return slabs


def car(name, x, y, heading, parent, mi=0):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); g.parent = parent; g.location = (x, y, 0); g.rotation_euler = (0, 0, heading)
    box(name + "_b", (1.75, 4.2, .75), (0, 0, .6), car_ms[mi % 4], g, bevel=.15); box(name + "_c", (1.55, 2.2, .62), (0, .25, 1.25), carglass, g, bevel=.12)
    for sx in (-.8, .8):
        for sy in (-1.35, 1.35):
            bpy.ops.mesh.primitive_cylinder_add(radius=.33, depth=.25, location=(sx, sy, .33), rotation=(0, math.pi / 2, 0)); w_ = bpy.context.object; w_.data.materials.append(dark); w_.parent = g
    return g


# ================================================================ 場面
GROUPS = {}
# ---- 家（2 階の部屋。床は板。下は 1 階）
home = group("home", (0, 0, 0)); GROUPS["home"] = home
FLOORZ = 3.0
PLANKS = []
for i in range(14):
    PLANKS.append(box(f"plank{i}", (.42, 5.0, .12), (-2.9 + i * .45, 0, FLOORZ - .06), wood if i % 2 else wood2, home, bevel=.01))
box("home_ground", (7, 6, .1), (0, 0, -.05), wood, home); box("home_back", (6.4, .15, 6.2), (0, 2.6, 3.0), wall, home); box("home_left", (.15, 5.4, 6.2), (-3.2, 0, 3.0), wall, home)
box("home_ceiling1", (6.4, 5.4, .2), (0, 0, FLOORZ - .22), wall, home)   # 1 階の天井（床の板の下）
box("win", (2.2, .05, 1.5), (1.0, 2.52, FLOORZ + 1.6), window_day, home)
box("sofa", (2.0, .9, .45), (-1.8, 1.8, FLOORZ + .22), fabric, home, bevel=.08); box("sofa_b", (2.0, .25, .8), (-1.8, 2.2, FLOORZ + .5), fabric, home, bevel=.08)
TABLE = box("table", (1.4, .9, .06), (1.2, -.2, FLOORZ + .74), wood2, home, bevel=.02)
for sx in (-.6, .6):
    for sy in (-.38, .38):
        K.tube((1.2 + sx, -.2 + sy, FLOORZ), (1.2 + sx, -.2 + sy, FLOORZ + .72), .03, wood2, home, 8)
CHAIRS = []
for j, (cx, cy, rz) in enumerate([(.55, -.9, 0), (1.85, -.9, 0), (1.2, .55, math.pi)]):
    cg = bpy.data.objects.new(f"chair{j}", None); sc.collection.objects.link(cg); cg.parent = home; cg.location = (cx, cy, FLOORZ); cg.rotation_euler = (0, 0, rz)
    box(f"chs{j}", (.45, .45, .05), (0, 0, .46), wood, cg); box(f"chb{j}", (.45, .05, .5), (0, .22, .72), wood, cg)
    for sx in (-.2, .2):
        for sy in (-.2, .2):
            K.tube((sx, sy, 0), (sx, sy, .45), .02, wood, cg, 6)
    CHAIRS.append(cg)
SCALE = box("scale", (.32, .32, .05), (-.4, -.6, FLOORZ + .025), white, home, bevel=.01); box("scale_lcd", (.12, .05, .006), (-.4, -.72, FLOORZ + .053), dark, home)
CEIL = bpy.data.objects.new("ceil_light", bpy.data.lights.new("ceil_light", "AREA")); CEIL.data.size = 1.2; CEIL.data.energy = 0; CEIL.location = (0, 0, FLOORZ + 2.8); CEIL.parent = home; sc.collection.objects.link(CEIL)
H_SCALE = person("man", (-.4, -.6, FLOORZ + .05), 0, home)
H_FAM = [person(k + "_sit", (CHAIRS[j].location.x, CHAIRS[j].location.y, FLOORZ + .46 - .46), CHAIRS[j].rotation_euler.z, home) for j, k in enumerate(["man", "woman", "child"])]
DUST = []
for i in range(40):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.12, location=(0, 0, 0)); o = bpy.context.object; o.data.materials.append(emat(f"dust{i}", (.7, .65, .58), 1)); o.parent = home; DUST.append(o)


# ---- 一軒家（外から。ユーザー「一軒家で椅子に座ってるところ…は建物が派手に崩れるように」）
house = group("house", (0, 0, 0)); GROUPS["house"] = house
box("hs_ground", (120, 120, .1), (0, 0, -.05), grass, house); box("hs_road", (8, 120, .06), (0, -8, 0), asphalt, house, rot=(0, 0, math.pi / 2))
plaster = emat("plaster", (.8, .74, .62), .85); roofm = emat("roofm", (.22, .2, .24), .6); hdark = emat("hdark", (.05, .06, .08), .2, .3)
HX, HY = 0.0, 10.0
HP = {}   # 名前 → (物, 最初の位置, 高さ)


def hpiece(name, s_, loc, m, rot=(0, 0, 0)):
    o = box(name, s_, loc, m, house, rot=rot); HP[name] = (o, Vector(loc), s_[2]); return o


for nm, (sx, sy, x, y) in {"f": (8.4, .25, 0, -3.5), "b": (8.4, .25, 0, 3.5), "l": (.25, 7, -4.2, 0), "r": (.25, 7, 4.2, 0)}.items():
    w1 = hpiece("w1" + nm, (sx, sy, 2.8), (HX + x, HY + y, 1.4), plaster); w2 = hpiece("w2" + nm, (sx, sy, 2.6), (HX + x, HY + y, 4.2), plaster)
    if nm == "f":
        for wx in (-2.3, 2.3):
            o = box("hw1" + str(wx), (1.6, .05, 1.1), (wx, -.15, .2), hdark, w1); o = box("hw2" + str(wx), (1.6, .05, 1.1), (wx, -.15, .1), hdark, w2)
        box("hdoor", (1.0, .05, 2.0), (0, -.15, -.35), wood, w1)
hpiece("fl2", (8.6, 7.2, .25), (HX, HY, 2.9), wood2)
hpiece("roofL", (8.9, 4.6, .22), (HX, HY - 1.9, 6.45), roofm, rot=(math.radians(35), 0, 0)); hpiece("roofR", (8.9, 4.6, .22), (HX, HY + 1.9, 6.45), roofm, rot=(math.radians(-35), 0, 0))
for k, (nx, ny) in enumerate([(-14, 12), (14, 11), (-14, 28), (14, 27)]):   # となりの家
    box(f"nb{k}", (8, 7, 5.2), (nx, ny, 2.6), emat(f"nbm{k}", (.7 + .05 * k, .66, .58), .85), house); box(f"nbr{k}", (8.6, 7.6, .3), (nx, ny, 5.35), roofm, house)
for k in range(8):
    tree(-24 + k * 7, 34, house, .9)
box("fence", (18, .1, 1.0), (0, 4.5, .5), wood, house)
H_DEB = [box(f"hdeb{i}", (RND.uniform(.2, .9), RND.uniform(.1, .5), RND.uniform(.05, .3)), (0, 0, -50), RND.choice([plaster, wood, roofm]), house) for i in range(90)]
SMOKE_M = emat("smoke", (.6, .55, .48), 1.0, alpha=.4)   # 土煙：半透明（体積の材質は Cycles が落ちるので使わない）
_sn = SMOKE_M.node_tree.nodes; _sl = SMOKE_M.node_tree.links; _sb = _sn["Principled BSDF"]; _stc = _sn.new("ShaderNodeTexCoord"); _snz = _sn.new("ShaderNodeTexNoise"); _snz.inputs["Scale"].default_value = 1.8
_sl.new(_stc.outputs["Object"], _snz.inputs["Vector"]); _smr = _sn.new("ShaderNodeMapRange"); _smr.inputs[1].default_value = .35; _smr.inputs[2].default_value = .7; _smr.inputs[4].default_value = .55
_sl.new(_snz.outputs["Fac"], _smr.inputs[0]); _sl.new(_smr.outputs[0], _sb.inputs["Alpha"])


def smoke_balls(parent, n_, name):
    out = []
    for i in range(n_):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0, 0, -50)); o = bpy.context.object; o.name = f"{name}{i}"; o.data.materials.append(SMOKE_M); o.parent = parent; out.append(o)
    return out


H_SMOKE = smoke_balls(house, 10, "hsm")

# ---- 朝の街
street = group("street", (0, 0, 0)); GROUPS["street"] = street
box("road", (14, 400, .05), (0, 0, 0), asphalt, street); box("walkL", (5, 400, .15), (-9.5, 0, .07), tile, street); box("walkR", (5, 400, .15), (9.5, 0, .07), tile, street)
for k in range(-6, 7):
    box(f"zebra{k}", (.6, 4, .01), (k * 1.1, 30, .03), white, street)
for side in (-1, 1):
    y = -120
    while y < 160:
        w = RND.uniform(14, 24); building(f"st{side}_{y:.0f}", side * 20, y + w / 2, 18, w, RND.randint(5, 12), street); y += w + 2
    for k in range(10):
        tree(side * 11.5, -60 + k * 18, street, .8)
ST_PEOPLE = [person(KINDS[i % 8], (0, 0, 0), 0, street) for i in range(36)]
ST_CARS = [car(f"stcar{i}", (-3.5 if i % 2 else 3.5), 0, 0 if i % 2 else math.pi, street, i) for i in range(6)]

# ---- プール
pool = group("pool", (0, 0, 0)); GROUPS["pool"] = pool
box("deck_n", (60, 19, .2), (0, 15.6, -.1), tile, pool); box("deck_s", (60, 19, .2), (0, -15.6, -.1), tile, pool); box("deck_w", (17.2, 12.4, .2), (-21.4, 0, -.1), tile, pool); box("deck_e", (17.2, 12.4, .2), (21.4, 0, -.1), tile, pool)
box("pool_bottom", (25, 12, .1), (0, 0, -1.45), pooltile, pool); box("pool_wl", (.3, 12, 1.5), (-12.6, 0, -.75), pooltile, pool); box("pool_wr", (.3, 12, 1.5), (12.6, 0, -.75), pooltile, pool)
box("pool_wf", (25, .3, 1.5), (0, -6.1, -.75), pooltile, pool); box("pool_wb", (25, .3, 1.5), (0, 6.1, -.75), pooltile, pool)
box("water", (25, 12, 1.25), (0, 0, -.73), water, pool)
for k in range(1, 4):
    box(f"lane{k}", (25, .08, .08), (0, -6 + k * 3, -.1), red, pool)
for k in range(6):
    tree(-20 + k * 8, 15, pool, 1.1)
SWIM = [person("swim", (0, 0, 0), 0, pool) for _ in range(5)]
DECKP = [person(KINDS[i], (-10 + i * 3, -9, 0), math.pi, pool) for i in range(6)]

# ---- ビルのエレベーターの前（夜）
lobby = group("lobby", (0, 0, 0)); GROUPS["lobby"] = lobby
box("lobby_floor", (16, 14, .1), (0, 0, -.05), emat("marble", (.82, .8, .76), .2), lobby); box("lobby_wall", (16, .3, 4), (0, 3, 2), wall, lobby)
box("ev_inside", (2.2, 2.0, 2.6), (0, 4.1, 1.3), emat("ev_in", (.75, .72, .66), .3, emit=(1, .95, .85), k=.6), lobby)
for sx in (-1.6, 1.6):
    box(f"ev_door{sx}", (1.1, .1, 2.4), (sx, 2.85, 1.2), steel, lobby)
box("ev_door_b", (1.1, .1, 2.4), (-4.2, 2.85, 1.2), steel, lobby); box("ev_door_b2", (1.1, .1, 2.4), (-3.1, 2.85, 1.2), steel, lobby)
EV_LAMP_M = emat("ev_lamp", (.3, .02, .02), .3, emit=(1, .1, .05), k=0); box("ev_lamp", (.6, .08, .2), (0, 2.8, 2.75), EV_LAMP_M, lobby)
EV_LAMP_K = EV_LAMP_M.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
EV_IN = [person(KINDS[i % 8], (-.7 + (i % 3) * .7, 4.6 - (i // 3) * .6, 0), math.pi, lobby) for i in range(8)]
EV_OUT = [person(KINDS[(i + 3) % 8], (-1.5 + (i % 4) * 1.0, .8 - (i // 4) * 1.2, 0), math.pi, lobby) for i in range(8)]
L_LOBBY = bpy.data.objects.new("lobby_light", bpy.data.lights.new("lobby_light", "AREA")); L_LOBBY.data.size = 6; L_LOBBY.data.energy = 0; L_LOBBY.location = (0, 0, 3.9); L_LOBBY.parent = lobby; sc.collection.objects.link(L_LOBBY)

# ---- 駅（満員電車）
station = group("station", (0, 0, 0)); GROUPS["station"] = station
box("platform", (6, 160, 1.1), (-4.5, 0, .55), concrete, station); box("yline", (.3, 160, .01), (-1.8, 0, 1.11), yellow, station)
box("ballast", (5, 200, .3), (1.5, 0, .15), emat("ballast", (.35, .32, .3), .95), station)
for xr in (.75, 2.25):
    box(f"rail{xr}", (.08, 200, .14), (xr, 0, .37), steel, station)
TRAIN = bpy.data.objects.new("train", None); sc.collection.objects.link(TRAIN); TRAIN.parent = station
for c_ in range(4):
    y0 = -30 + c_ * 20.5
    box(f"tc{c_}", (2.9, 20, 3.0), (1.5, y0, 2.0), steel, TRAIN, bevel=.2); box(f"ts{c_}", (2.92, 19.6, .25), (1.5, y0, 1.2), stripe, TRAIN)
    for w_ in range(5):
        box(f"tw{c_}_{w_}", (2.94, 2.6, .9), (1.5, y0 - 7.6 + w_ * 3.8, 2.45), emat(f"tww{c_}{w_}", (.75, .85, .9), .1, emit=(1, .97, .9), k=1.5), TRAIN)
TR_IN = [person(KINDS[i % 8], (1.5 + (i % 2) * .6 - .3, -38 + i * .55, .9), -math.pi / 2, TRAIN) for i in range(60)]
TR_PLAT = [person(KINDS[i % 8], (-4.5 + RND.uniform(-1.8, 1.5), -40 + i * 4, 1.1), RND.uniform(0, 6.28), station) for i in range(20)]
SIGNAL_M = emat("signal", (.3, .02, .02), .3, emit=(1, .05, .03), k=0); box("signal", (.4, .2, .4), (3.6, -45, 4.5), SIGNAL_M, station)
SIGNAL_K = SIGNAL_M.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]

# ---- 公園（関東ローム層の土）
park = group("park", (0, 0, 0)); GROUPS["park"] = park
box("park_grass", (120, 120, .1), (0, 0, -.05), grass, park); box("park_soil", (14, 40, .02), (0, 0, .005), soil, park)
for k in range(14):
    tree(RND.uniform(-40, 40), RND.uniform(10, 45), park, RND.uniform(.9, 1.3))
PK_PEOPLE = [person(KINDS[i % 8], (RND.uniform(-5, 5), RND.uniform(-12, 12), 0), RND.uniform(0, 6.28), park) for i in range(14)]
PK_CRATER = []
for p_ in PK_PEOPLE:
    bpy.ops.mesh.primitive_torus_add(major_radius=.32, minor_radius=.08, location=(p_.location.x, p_.location.y, 0)); o = bpy.context.object; o.data.materials.append(soil); o.parent = park; o.scale = (1, 1, 0); PK_CRATER.append(o)

# ---- スタジアム（立ち見のスタンド）
stad = group("stad", (0, 0, 0)); GROUPS["stad"] = stad
box("field", (120, 80, .1), (0, -30, -.05), grass, stad)
TIERS = []   # [(物, 段, 区画)]
for i in range(12):
    for sct in range(6):
        b_ = box(f"tier{i}_{sct}", (10, 1.0, .5 + i * .55), (-27.5 + sct * 11, 4 + i * 1.0, (.5 + i * .55) / 2), concrete, stad); TIERS.append((b_, i, sct))
box("stad_roof", (70, 14, .6), (0, 12, 10.5), white, stad)
for sx in range(-3, 4):
    K.tube((sx * 11, 17, 0), (sx * 11, 17, 10.5), .3, steel, stad, 10)
ST_FANS = []
for i in range(1, 12, 2):
    for sct in range(6):
        for q in range(3):
            ST_FANS.append((person(KINDS[(i + sct + q) % 8], (-31 + sct * 11 + q * 3 + RND.uniform(-.5, .5), 4 + i * 1.0, .5 + i * .55), math.pi, stad), i, sct))
DEBRIS = []
for i in range(60):
    o = box(f"deb{i}", (RND.uniform(.2, .7),) * 2 + (RND.uniform(.2, .5),), (0, 0, -50), concrete, stad); DEBRIS.append(o)
SDUST = []
for i in range(30):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0, 0, -50)); o = bpy.context.object; o.data.materials.append(emat(f"sd{i}", (.75, .72, .66), 1)); o.parent = stad; SDUST.append(o)

# ---- 車
road = group("road", (0, 0, 0)); GROUPS["road"] = road
box("road2", (12, 200, .05), (0, 0, 0), asphalt, road); box("road2_walk", (5, 200, .15), (8.5, 0, .07), tile, road)
for k in range(12):
    building(f"rd{k}", 18, -80 + k * 16, 14, 14, RND.randint(3, 7), road)
CAR = car("mycar", 0, 0, math.pi / 2, road, 0); CAR_P = person("man_sit", (0, -.35, .25), 0, CAR)
CARS2 = [car(f"rcar{i}", -3.5, -20 + i * 9, 0, road, i + 1) for i in range(5)]
GLASS = []
for i in range(40):
    o = box(f"gl{i}", (.08, .08, .02), (0, 0, -50), carglass, road); GLASS.append(o)
RD_P = [person(KINDS[i % 8], (7 + RND.uniform(-1.5, 1.5), -10 + i * 2.5, .15), RND.choice([0, math.pi]), road) for i in range(8)]

# ---- ビル街（床が落ちる・人が沈む）
city = group("city", (0, 0, 0)); GROUPS["city"] = city
box("city_road", (16, 300, .05), (0, 0, 0), asphalt, city); box("city_walkL", (6, 300, .15), (-11, 0, .07), tile, city); box("city_walkR", (6, 300, .15), (11, 0, .07), tile, city)
CITY_B = []
for side in (-1, 1):
    for k in range(9):
        CITY_B.append(building(f"cb{side}_{k}", side * 22, -60 + k * 22, 18, 18, RND.randint(8, 16), city))
CT_P = [person(KINDS[i % 8], (RND.choice([-11, 11]) + RND.uniform(-2, 2), -40 + i * 3.2, .15), RND.uniform(0, 6.28), city) for i in range(26)]
CRACKS = []
for i in range(50):
    o = box(f"ck{i}", (RND.uniform(.05, .12), RND.uniform(1.5, 6), .02), (RND.uniform(-14, 14), RND.uniform(-40, 50), .17), crack, city, rot=(0, 0, RND.uniform(0, 3.14))); o.scale = (1, 0, 1); CRACKS.append(o)
HOLES = []
for p_ in CT_P:
    bpy.ops.mesh.primitive_cylinder_add(radius=.5, depth=.02, location=(p_.location.x, p_.location.y, .17)); o = bpy.context.object; o.data.materials.append(dark); o.parent = city; o.scale = (0, 0, 1); HOLES.append(o)


# ---- マンション（ユーザー「マンションのシーンは建物が派手に崩れるように」）：10 階建て。下から押しつぶされ、傾きながら崩れる
MAN = bpy.data.objects.new("mansion", None); sc.collection.objects.link(MAN); MAN.parent = city; MAN.location = (-15, 8, 0)
mansion_m = emat("mansion_m", (.78, .74, .68), .8); balcony = emat("balcony", (.6, .62, .65), .5, .3)
MAN_F = []
for i in range(10):
    fo = box(f"mf{i}", (22, 11, 2.4), (0, 0, i * 3.0 + 1.5), mansion_m, MAN); box(f"mfw{i}", (22.05, 11.05, 1.1), (0, 0, .1), window_day, fo)
    box(f"mfb{i}", (21, 1.4, .25), (0, -6.0, -1.05), balcony, fo); box(f"mfr{i}", (21, .1, .9), (0, -6.6, -.6), balcony, fo)
    MAN_F.append(fo)
M_DEB = [box(f"mdeb{i}", (RND.uniform(.3, 1.4), RND.uniform(.2, .8), RND.uniform(.15, .5)), (0, 0, -50), RND.choice([mansion_m, concrete, balcony]), city) for i in range(110)]
M_GLASS = [box(f"mgl{i}", (.12, .12, .02), (0, 0, -50), carglass, city) for i in range(60)]
M_SMOKE = smoke_balls(city, 14, "msm")


# ---- 世界の名所（ユーザー「崩れる自由の女神、エッフェル塔みたいなのを挟み込んで。なるべく笑えるやつ」）。どれも簡略な模式
copper = emat("copper", (.3, .55, .47), .6, .3); flame = emat("flame", (1, .7, .2), .4, emit=(1, .65, .15), k=12); sea = glassm("sea", (.2, .45, .6), .6, .05)
iron = emat("iron", (.3, .22, .15), .5, .6); marble = emat("marble2", (.86, .84, .78), .5)
# 自由の女神
liberty = group("liberty", (0, 0, 0)); GROUPS["liberty"] = liberty
box("lb_sea", (900, 900, .1), (0, 0, -1), sea, liberty); box("lb_island", (70, 70, 4), (0, 0, 1), concrete, liberty)
box("lb_ped", (22, 22, 27), (0, 0, 17.5), emat("ped", (.62, .58, .5), .8), liberty)
LB = bpy.data.objects.new("lb_statue", None); sc.collection.objects.link(LB); LB.parent = liberty; LB.location = (0, 0, 31)
bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=6.5, radius2=3.0, depth=34, location=(0, 0, 17)); o = bpy.context.object; o.data.materials.append(copper); o.parent = LB
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.6, location=(0, -.4, 36.5)); o = bpy.context.object; o.data.materials.append(copper); o.parent = LB
LB_SPIKES = []
for i in range(7):
    a = math.radians(-60 + i * 20); bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=.45, radius2=0, depth=3.2, location=(2.4 * math.sin(a), -.4 - 2.4 * math.cos(a) * .3, 39.2), rotation=(-.35 * math.cos(a), a * .6, 0))
    o = bpy.context.object; o.data.materials.append(copper); o.parent = LB; LB_SPIKES.append(o)
box("lb_tab", (3, 1, 5), (-4.5, -1.5, 26), copper, LB, rot=(0, .3, 0))
LB_ARM = bpy.data.objects.new("lb_arm", None); sc.collection.objects.link(LB_ARM); LB_ARM.parent = LB; LB_ARM.location = (3.2, 0, 32)
K.tube((0, 0, 0), (1.5, 0, 13), .9, copper, LB_ARM, 12); bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=.6, radius2=1.4, depth=2, location=(1.6, 0, 14)); o = bpy.context.object; o.data.materials.append(gold if False else copper); o.parent = LB_ARM
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.2, location=(1.6, 0, 15.8)); o = bpy.context.object; o.scale = (1, 1, 1.6); o.data.materials.append(flame); o.parent = LB_ARM
LB_TOUR = [person(KINDS[i % 8], (-9 + (i % 6) * 3.4, -10 + (i // 6) * 1.5, 31), math.pi, liberty) for i in range(12)]
LB_SPLASH = []
for i in range(40):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(.4, 1.2), location=(0, 0, -50)); o = bpy.context.object; o.data.materials.append(emat(f"spl{i}", (.85, .92, .95), .2)); o.parent = liberty; LB_SPLASH.append(o)
# エッフェル塔：脚が外へ開いて、開脚するようにしゃがみ込む
eiffel = group("eiffel", (0, 0, 0)); GROUPS["eiffel"] = eiffel
box("ef_ground", (600, 600, .1), (0, 0, -.05), grass, eiffel); box("ef_path", (30, 600, .06), (0, -150, 0), tile, eiffel)
EF = bpy.data.objects.new("ef_tower", None); sc.collection.objects.link(EF); EF.parent = eiffel
for sx in (-1, 1):
    for sy in (-1, 1):
        K.tube((sx * 31, sy * 31, 0), (sx * 11, sy * 11, 57), 3.2, iron, EF, 8); K.tube((sx * 11, sy * 11, 57), (sx * 5, sy * 5, 115), 2.0, iron, EF, 8)
        K.tube((sx * 25, sy * 25, 12), (sx * 25, -sy * 25, 12), .8, iron, EF, 6) if sx > 0 else None
box("ef_p1", (52, 52, 4), (0, 0, 57), iron, EF); box("ef_p2", (22, 22, 3), (0, 0, 115), iron, EF)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=7, radius2=1.2, depth=160, location=(0, 0, 196), rotation=(0, 0, math.pi / 4)); EF_TOP = bpy.context.object; EF_TOP.data.materials.append(iron); EF_TOP.parent = EF
EF_TOUR = [person(KINDS[i % 8], (-21 + (i % 8) * 6, -24 + (i // 8) * 3, 59), RND.uniform(0, 6.28), eiffel) for i in range(16)]
for k in range(10):
    tree(-60 + k * 13, -40, eiffel, 1.4)
# ピサの斜塔：観光客が寄りかかると、まっすぐになって沈む
pisa = group("pisa", (0, 0, 0)); GROUPS["pisa"] = pisa
box("ps_ground", (400, 400, .1), (0, 0, -.05), grass, pisa); box("ps_plaza", (80, 120, .06), (0, -20, 0), tile, pisa)
PS = bpy.data.objects.new("ps_tower", None); sc.collection.objects.link(PS); PS.parent = pisa; PS.rotation_euler = (0, math.radians(-4), 0)
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=8, depth=50, location=(0, 0, 25)); o = bpy.context.object; o.data.materials.append(marble); o.parent = PS
bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=6, depth=7, location=(0, 0, 53.5)); o = bpy.context.object; o.data.materials.append(marble); o.parent = PS
for k in range(7):
    bpy.ops.mesh.primitive_torus_add(major_radius=8.3, minor_radius=.45, location=(0, 0, 7 + k * 6.5)); o = bpy.context.object; o.data.materials.append(marble); o.parent = PS
PS_TOUR = []
for i in range(9):
    x = -16 + i * 4; o = person(KINDS[i % 8], (x, -14 - (i % 2) * 2, 0), math.atan2(14, -x) + math.pi / 2, pisa); PS_TOUR.append(o)

# ---- 宇宙（地球・月・ブラックホール・太陽・金星）
space = group("space", (0, 0, 0)); GROUPS["space"] = space
em_ = bpy.data.materials.new("earth46"); em_.use_nodes = True; n = em_.node_tree.nodes; L = em_.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = .32; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
cr = n.new("ShaderNodeValToRGB"); L.new(nz.outputs["Fac"], cr.inputs[0]); e = cr.color_ramp.elements
e[0].position, e[0].color = .52, (.01, .05, .2, 1); e[1].position, e[1].color = .54, (.12, .25, .08, 1); el = e.new(.66); el.color = (.42, .36, .22, 1)
L.new(cr.outputs[0], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .6
# ひび（ユーザー「人が空気や水よりも重くなったシーンも、少しずつ地球にひびが入っていく描写」）：ボロノイの境目が光るひび。GROW で広がり、CRK で光の強さ
vor = n.new("ShaderNodeTexVoronoi"); vor.feature = "DISTANCE_TO_EDGE"; vor.inputs["Scale"].default_value = .55; L.new(tc.outputs["Object"], vor.inputs["Vector"])
vmr = n.new("ShaderNodeMapRange"); vmr.inputs[1].default_value = 0; vmr.inputs[2].default_value = .035; vmr.inputs[3].default_value = 1; vmr.inputs[4].default_value = 0; L.new(vor.outputs["Distance"], vmr.inputs[0])
gn = n.new("ShaderNodeTexNoise"); gn.inputs["Scale"].default_value = .12; L.new(tc.outputs["Object"], gn.inputs["Vector"])
glt = n.new("ShaderNodeMath"); glt.operation = "LESS_THAN"; glt.inputs[1].default_value = 0.0; L.new(gn.outputs["Fac"], glt.inputs[0]); GROW = glt.inputs[1]
ck = n.new("ShaderNodeMath"); ck.operation = "MULTIPLY"; L.new(vmr.outputs[0], ck.inputs[0]); L.new(glt.outputs[0], ck.inputs[1])
cmix = n.new("ShaderNodeMix"); cmix.data_type = "RGBA"; L.new(ck.outputs[0], cmix.inputs[0]); L.new(cr.outputs[0], cmix.inputs[6]); cmix.inputs[7].default_value = (.02, .008, 0, 1); L.new(cmix.outputs[2], b.inputs["Base Color"])
cke = n.new("ShaderNodeMath"); cke.operation = "MULTIPLY"; cke.inputs[1].default_value = 0.0; L.new(ck.outputs[0], cke.inputs[0]); CRK = cke.inputs[1]
b.inputs["Emission Color"].default_value = (1, .35, .06, 1); L.new(cke.outputs[0], b.inputs["Emission Strength"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=6.4, location=(0, 0, 0)); EARTH = bpy.context.object; EARTH.data.materials.append(em_); EARTH.parent = space; bpy.ops.object.shade_smooth()
cm_ = emat("cloud46", (1, 1, 1), 1, alpha=.0); cn = cm_.node_tree.nodes; cl = cm_.node_tree.links; cb = cn["Principled BSDF"]
ctc = cn.new("ShaderNodeTexCoord"); cnz = cn.new("ShaderNodeTexNoise"); cnz.inputs["Scale"].default_value = .9; cnz.inputs["Detail"].default_value = 10; cl.new(ctc.outputs["Object"], cnz.inputs["Vector"])
crg = cn.new("ShaderNodeMapRange"); crg.inputs[1].default_value = .5; crg.inputs[2].default_value = .62; cl.new(cnz.outputs["Fac"], crg.inputs[0]); cl.new(crg.outputs[0], cb.inputs["Alpha"])
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=6.5, location=(0, 0, 0)); CLOUDS = bpy.context.object; CLOUDS.data.materials.append(cm_); CLOUDS.parent = space; bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1.7, location=(26, 10, 2)); MOON = bpy.context.object; MOON.data.materials.append(emat("moon", (.45, .44, .42), .9)); MOON.parent = space
FRAG = []
for i in range(220):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(.08, .35), location=(0, 0, -50)); o = bpy.context.object; o.data.materials.append(MOON.data.materials[0]); o.parent = space; FRAG.append((o, RND.uniform(0, 6.283), RND.uniform(12, 22), RND.uniform(-.6, .6)))
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=3.0, location=(0, 0, 0)); BH = bpy.context.object; BH.data.materials.append(emat("bh", (0, 0, 0), 1)); BH.parent = space
bpy.ops.mesh.primitive_torus_add(major_radius=7, minor_radius=2.2, location=(0, 0, 0)); DISK = bpy.context.object; DISK.scale = (1, 1, .08); DISK.data.materials.append(emat("disk", (.3, .08, .01), .5, emit=(1, .32, .06), k=5)); DISK.parent = space
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=.9, location=(0, 0, 0)); VENUS = bpy.context.object; VENUS.data.materials.append(emat("venus", (.9, .8, .55), .6, emit=(1, .85, .5), k=.4)); VENUS.parent = space
STAR_M = emat("star", (1, 1, 1), 1, emit=(1, 1, 1), k=20)
for i in range(400):
    v = Vector((RND.gauss(0, 1), RND.gauss(0, 1), RND.gauss(0, 1))).normalized() * 900
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=RND.uniform(.6, 1.6), location=v); o = bpy.context.object; o.data.materials.append(STAR_M); o.parent = space


# ================================================================ 表示の切り替え
# 前のショットの動き（抜けた床・沈んだ電車など）を残さないよう、場面を切り替えるたびに全部を最初の姿に戻す
INIT = {o.name: (o.location.copy(), o.rotation_euler.copy(), o.scale.copy()) for o in bpy.data.objects}
ANIM_DATA = [sky.node.id_data, sky.sun, sky.sun.data, sc.world.node_tree, CEIL.data, EV_LAMP_M.node_tree, SIGNAL_M.node_tree, em_.node_tree]


def reset_all():
    for o in bpy.data.objects:
        if o.name in INIT and o is not cam.o:
            o.animation_data_clear(); l_, r_, s_ = INIT[o.name]; o.location = l_; o.rotation_euler = r_; o.scale = s_
    for d in ANIM_DATA:
        d.animation_data_clear()
    CEIL.data.energy = 0; L_LOBBY.data.energy = 0; EV_LAMP_K.default_value = 0; SIGNAL_K.default_value = 0; GROW.default_value = 0; CRK.default_value = 0


def show(name, hour=12.0):
    reset_all()
    for k, g in GROUPS.items():
        g.location = (0, 0, 0) if k == name else (0, 0, -900)
        for c in g.children_recursive:
            c.hide_render = k != name
        g.hide_render = k != name
    cam.o.data.dof.use_dof = False
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -2.1
    if name == "space":
        sky.set(0, -20, 160, 0.0); sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0; sky.sun.data.energy = 4.0
        sky.sun.rotation_euler = (math.radians(60), 0, math.radians(-40)); sc.view_settings.exposure = -.6
    else:
        set_sky(hour)


def ease(u):
    return K.ease(u)


def shake(f, amp, seed=0):
    r = random.Random(f * 7 + seed); return Vector(((r.random() - .5) * amp, (r.random() - .5) * amp, (r.random() - .5) * amp * .6))


def ev_u(k, t, j=0):   # 壊れる瞬間からの秒（スローの所では、そのまま画面の秒）
    return t - ev_t(k, j)


# ================================================================ ショット
def s_l00():
    show("home", hour_of(0)); CEIL.data.energy = 500; cam.o.data.dof.use_dof = True; cam.o.data.dof.aperture_fstop = 2.8
def a_l00(u, t, f):   # 朝。体重計に乗る足もとから
    keyp(H_SCALE, f, loc=(-.4, -.6, FLOORZ + .05)); cam.look(mix((.6, -2.6, FLOORZ + .35), (.5, -2.2, FLOORZ + .6), ease(u)), (-.4, -.6, FLOORZ + .45 + .4 * u), 30)
    cam.o.data.dof.focus_distance = 2.2

def s_l01():
    show("home", hour_of(0)); CEIL.data.energy = 500
def a_l01(u, t, f):   # 設定の札。体重計の 1 人を少し離れて（札は上、人は下）
    keyp(H_SCALE, f, loc=(-.4, -.6, FLOORZ + .05)); a = math.radians(-80 + 40 * ease(u))
    cam.look((-.4 + 3.6 * math.cos(a), -.6 + 3.6 * math.sin(a), FLOORZ + 1.0), (-.4, -.6, FLOORZ + 1.5), 28)

def s_l02():
    show("street", hour_of(0))
def a_l02(u, t, f):   # 朝の通勤：歩く人と車（時計は 6 時間進む）
    set_sky(hour_of(clock("l02", t)), f)
    for i, p_ in enumerate(ST_PEOPLE):
        side = -1 if i % 2 else 1; d = 1 if i % 3 else -1
        keyp(p_, f, loc=(side * (8.5 + (i % 4) * .6), -40 + (i * 7.3) % 90 + d * 1.3 * t, .15), rot=(0, 0, 0 if d > 0 else math.pi))
    for i, c_ in enumerate(ST_CARS):
        d = -1 if i % 2 else 1; keyp(c_, f, loc=(-3.5 if i % 2 else 3.5, -60 + i * 25 + d * 9 * t, 0))
    cam.look(mix((5, -32, 1.7), (4, -26, 2.2), ease(u)), (0, 30, 3.5), 26)

def s_l03():
    show("pool", hour_of(clock("l03", 0)))
def a_l03(u, t, f):   # 泳いでいた人が沈み、底に立つ（水に浮かなくなる）
    set_sky(hour_of(clock("l03", t)), f); s_ = ease(clamp((t - ev_t("l03", 0) + .3) / 1.2))
    for i, p_ in enumerate(SWIM):
        x, y = -8 + i * 4, -4.5 + i * 2.2 + (1 - s_) * .4 * t
        keyp(p_, f, loc=(x, y, mix((-.15,), (-1.4,), s_)[0]), rot=(mix((math.radians(-85),), (0,), s_)[0], 0, math.pi))
    for p_ in DECKP:
        keyp(p_, f, loc=tuple(p_.location))
    cam.look(mix((-14, -12, 1.6), (-12, -10.5, 1.3), ease(u)), (-2, 0, -.6), 26)

def s_l04():
    show("lobby", 19.0); L_LOBBY.data.energy = 2500
def a_l04(u, t, f):   # 夜のビル：満員のエレベーター。重量超過のランプとブザー、扉は閉まらない
    on = ev_u("l04", t) > 0; key_fac(EV_LAMP_K, (12 if (t * 2.5) % 1 < .5 else 2) if on else 0, f)
    for p_ in EV_IN + EV_OUT:
        keyp(p_, f, loc=tuple(p_.location))
    cam.look(mix((2.6, -4.5, 1.6), (1.8, -3.6, 1.55), ease(u)), (0, 3.6, 1.4), 26)

def s_l05():
    show("home", 22.0); CEIL.data.energy = 900
def a_l05(u, t, f):   # 夜から朝：家族が座る椅子がきしみ、少したわむ（時計は 1 日半進む）
    h = hour_of(clock("l05", t)); set_sky(h, f)
    CEIL.data.energy = 900 if (h > 18 or h < 7) else 250; CEIL.data.keyframe_insert("energy", frame=f + 1)
    for j, cg in enumerate(CHAIRS):
        sag = 1 - .06 * ease(u) - .015 * math.sin(t * 9 + j) * clamp(u * 2)
        keyp(cg, f, scale=(1, 1, sag)); keyp(H_FAM[j], f, loc=(cg.location.x, cg.location.y, FLOORZ + .46 * sag - .46))
    cam.look(mix((3.6, -3.4, FLOORZ + 1.5), (3.2, -2.9, FLOORZ + 1.3), ease(u)), (1.2, -.2, FLOORZ + .7), 28)

def s_l06():
    show("station", 9.0)
def a_l06(u, t, f):   # 満員電車：床が重さの限界に。電車が沈み、赤信号
    sag = .18 * ease(clamp((t - ev_t("l06", 0) + .4) / .8)); keyp(TRAIN, f, loc=(0, 0, -sag)); key_fac(SIGNAL_K, 10 if t > ev_t("l06", 0) else 0, f)
    for p_ in TR_PLAT:
        keyp(p_, f, loc=tuple(p_.location))
    cam.look(mix((-4.5, -58, 2.9), (-4.2, -52, 2.6), ease(u)), (1.2, -20, 2.0), 30)

def s_l07():
    show("park", 12.0)
def a_l07(u, t, f):   # 関東ローム層：立っているだけで足がめり込み、足もとの土が盛り上がる（スロー）
    k = ease(clamp((t - ev_t("l07", 0) + .4) / 1.6))
    for i, (p_, cr_) in enumerate(zip(PK_PEOPLE, PK_CRATER)):
        keyp(p_, f, loc=(p_.location.x, p_.location.y, -.22 * k * (.7 + .3 * (i % 3) / 2))); keyp(cr_, f, scale=(1 + .4 * k, 1 + .4 * k, k))
    cam.look(mix((3, -16, .7), (2.5, -14, .55), ease(u)), (0, -2, .25), 30)

def s_l08():
    show("stad", 15.0)
def a_l08(u, t, f):   # 立ち見のスタンドが崩れる（スロー）。真ん中の区画から落ちる
    e = t - ev_t("l08", 0)
    for b_, i, sct in TIERS:
        fall = (sct in (2, 3, 4)) and e > .1 * (11 - i) * .15
        tt = max(0, e - .015 * (11 - i)) if fall else 0; drop = .5 * 9.8 * (tt * .45) ** 2
        keyp(b_, f, loc=(b_.location.x, b_.location.y, (.5 + i * .55) / 2 - min(drop, (.5 + i * .55) / 2 + .2)), rot=(-.35 * clamp(tt) * (1 if sct % 2 else -1), .25 * clamp(tt) * (sct - 3), 0))
    for p_, i, sct in ST_FANS:
        fall = sct in (2, 3, 4) and e > 0; tt = max(0, e - .015 * (11 - i)) if fall else 0; drop = .5 * 9.8 * (tt * .45) ** 2
        keyp(p_, f, loc=(p_.location.x, p_.location.y, max(0, .5 + i * .55 - drop)), rot=(-.6 * clamp(tt), 0, math.pi))
    for j, o in enumerate(DEBRIS):
        r = random.Random(j); tt = max(0, e - r.uniform(0, .4)); v0 = Vector((r.uniform(-6, 6), r.uniform(-8, -2), r.uniform(2, 8))) * .45
        p0 = Vector((r.uniform(-12, 22), r.uniform(5, 14), r.uniform(1, 6)))
        p_ = p0 + v0 * tt * 2 + Vector((0, 0, -4.9 * (tt * .9) ** 2)) if e > 0 else Vector((0, 0, -50))
        keyp(o, f, loc=(p_.x, p_.y, max(.2, p_.z)) if e > 0 else (0, 0, -50), rot=(tt * r.uniform(2, 6), tt * r.uniform(2, 6), 0))
    for j, o in enumerate(SDUST):
        r = random.Random(100 + j); tt = max(0, e - .2); s_ = (.6 + 2.2 * clamp(tt / 2)) * r.uniform(.6, 1.2)
        keyp(o, f, loc=(r.uniform(-14, 24), r.uniform(5, 15), 1.5 + 3 * clamp(tt / 2) + r.uniform(0, 4)) if e > .2 else (0, 0, -50), scale=(s_, s_, s_ * .8))
    pos = Vector(mix((5, -11, 1.5), (4.5, -9, 1.7), ease(u))) + shake(f, .25 * clamp(1 - abs(e - .3) / 1.2) if e > 0 else 0)
    cam.look(pos, (4, 8, 4.5), 22)

def s_l09():
    show("house", 13.0)


def topple(o, base, h, ang, axis="x"):
    """下の辺を軸に倒す（base＝下の辺の中心、h＝高さ）"""
    if axis == "x":
        o.rotation_euler = (ang, 0, 0); o.location = base + Vector((0, -math.sin(ang) * h / 2, math.cos(ang) * h / 2))
    else:
        o.rotation_euler = (0, ang, 0); o.location = base + Vector((math.sin(ang) * h / 2, 0, math.cos(ang) * h / 2))


def a_l09(u, t, f):   # 一軒家が崩れる（スロー）：1 階がつぶれ、2 階の床と壁が落ち、屋根が滑り落ちる。破片と土煙
    e = t - ev_t("l09", 0); k1 = ease(clamp(e / .9)); fall = 2.5 * k1
    for nm in "fblr":   # 1 階の壁：外へ倒れながらつぶれる
        o, p0, h = HP["w1" + nm]; ang = 1.35 * ease(clamp((e - .05) / 1.1))
        if nm in "fb":
            topple(o, Vector((p0.x, p0.y, 0)), h, -ang if nm == "f" else ang, "x")
        else:
            topple(o, Vector((p0.x, p0.y, 0)), h, -ang if nm == "l" else ang, "y")
        keyp(o, f, loc=tuple(o.location), rot=tuple(o.rotation_euler))
    o, p0, h = HP["fl2"]; keyp(o, f, loc=(p0.x, p0.y, p0.z - fall), rot=(.06 * k1, -.05 * k1, 0))
    for nm in "fblr":   # 2 階の壁：落ちてから外へ倒れる
        o, p0, h = HP["w2" + nm]; ang = 1.4 * ease(clamp((e - .5) / 1.0)); base = Vector((p0.x, p0.y, 2.9 - fall + .1))
        if nm in "fb":
            topple(o, base, h, -ang if nm == "f" else ang, "x")
        else:
            topple(o, base, h, -ang if nm == "l" else ang, "y")
        keyp(o, f, loc=tuple(o.location), rot=tuple(o.rotation_euler))
    for nm, sg in (("roofL", -1), ("roofR", 1)):   # 屋根：落ちて、外へ滑り落ちる
        o, p0, h = HP[nm]; k2 = ease(clamp((e - .35) / 1.2))
        keyp(o, f, loc=(p0.x, p0.y + sg * 2.5 * k2, p0.z - fall - 2.0 * k2), rot=(math.radians(-35 * sg) * (1 - .6 * k2) + sg * .4 * k2, .1 * k2, 0))
    for j, o in enumerate(H_DEB):
        r = random.Random(j); tt = max(0, e - r.uniform(0, .5)); v = Vector((r.uniform(-7, 7), r.uniform(-9, 2), r.uniform(2, 9)))
        p_ = Vector((HX + r.uniform(-4, 4), HY + r.uniform(-3.5, 3.5), r.uniform(1, 5))) + v * tt * .8 + Vector((0, 0, -4.9 * tt * tt))
        keyp(o, f, loc=(p_.x, p_.y, max(.05, p_.z)) if e > 0 else (0, 0, -50), rot=(tt * r.uniform(3, 9), tt * r.uniform(3, 9), 0))
    for j, o in enumerate(H_SMOKE):
        r = random.Random(50 + j); tt = max(0, e - .15 - .05 * j); s_ = (1.5 + 5.5 * ease(clamp(tt / 2.2))) * r.uniform(.7, 1.2)
        keyp(o, f, loc=(HX + r.uniform(-6, 6), HY + r.uniform(-5, 3), 1 + 2.5 * clamp(tt / 2)) if e > .15 else (0, 0, -50), scale=(s_, s_, s_ * .7))
    pos = Vector(mix((8, -2.5, 1.7), (7, -1.5, 1.6), ease(u))) + shake(f, .22 * clamp(1 - abs(e - .25) / 1.4) if e > 0 else 0)
    cam.look(pos, (HX, HY, 3.0 - 1.2 * k1), 24)

def s_l10():
    show("road", 14.0)
def a_l10(u, t, f):   # 車に乗ると車がつぶれる（スロー）。屋根と窓が押しつぶされ、ガラスが飛ぶ
    e = t - ev_t("l10", 1); k = ease(clamp((e + .1) / .5))
    keyp(CAR, f, scale=(1 + .12 * k, 1 + .05 * k, 1 - .55 * k))
    for j, o in enumerate(GLASS):
        r = random.Random(j); tt = max(0, e); v = Vector((r.uniform(-4, 4), r.uniform(-4, 4), r.uniform(1, 4)))
        p_ = Vector((r.uniform(-.8, .8), r.uniform(-1, 1), 1.1)) + v * tt + Vector((0, 0, -4.9 * tt * tt))
        keyp(o, f, loc=(p_.x, p_.y, max(.03, p_.z)) if e > 0 else (0, 0, -50), rot=(tt * 9, tt * 7, 0))
    for p_ in RD_P:
        keyp(p_, f, loc=tuple(p_.location))
    pos = Vector(mix((5.5, -5.5, 1.4), (4.8, -4.6, 1.3), ease(u))) + shake(f, .1 * clamp(1 - abs(e - .1) / .6) if e > 0 else 0)
    cam.look(pos, (0, 0, .8), 26)

def s_l11():
    show("city", 12.0)
def a_l11(u, t, f):   # 街：歩くたびに舗道にひび（早送り）
    k = clamp(u * 1.3)
    for j, o in enumerate(CRACKS):
        keyp(o, f, scale=(1, clamp(k * 1.5 - (j % 10) * .08), 1))
    for i, p_ in enumerate(CT_P):
        keyp(p_, f, loc=(p_.location.x, p_.location.y, .15 - .05 * k))
    cam.look(mix((-6, -55, 2.0), (-5, -48, 2.4), ease(u)), (0, 0, 2.5), 26)

def s_l12():
    show("city", 12.0)
def a_l12(u, t, f):   # 足もとのコンクリートが砕け、マンションが傾きながら押しつぶされる（スロー）。破片・ガラス・土煙
    e = t - ev_t("l12", 0); e2 = t - ev_t("l12", 1)
    for o in CRACKS:
        keyp(o, f, scale=(1.6, 1, 1))
    for i, (p_, h_) in enumerate(zip(CT_P, HOLES)):
        k = ease(clamp((e + .2 - .03 * i) / .8)); keyp(p_, f, loc=(p_.location.x, p_.location.y, .15 - .6 * k)); keyp(h_, f, scale=(k, k, 1))
    for bi, slabs in enumerate(CITY_B):   # 奥のビルも順に沈む
        st = e2 - .25 * (bi % 6)
        for fi, s_ in enumerate(slabs):
            z0 = fi * 3.4 + 1.95; tt = max(0, st - .05 * fi); drop = 4.9 * (tt * .55) ** 2
            keyp(s_, f, loc=(s_.location.x, s_.location.y, max(.6 + fi * .55, z0 - drop)))
    tt = max(0, e2 + .3); d = 4.9 * (tt * .75) ** 2   # マンション：全体が下がり、下の階から順につぶれる（つぶれた階は 0.5 m に）
    for i, fo in enumerate(MAN_F):
        z0 = i * 3.0 + 1.5; keyp(fo, f, loc=(0, 0, max(.3 + i * .5, z0 - d)), rot=(0, 0, 0))
    keyp(MAN, f, rot=(.12 * ease(clamp(tt / 1.6)), -.05 * ease(clamp(tt / 1.6)), 0))
    for j, o in enumerate(M_DEB):
        r = random.Random(j); tt2 = max(0, e2 - r.uniform(0, 1.0)); v = Vector((r.uniform(-4, 10), r.uniform(-12, -2), r.uniform(1, 7)))
        p0 = Vector((-15 + r.uniform(-11, 11), 8 - 5.6, r.uniform(1, 20))); p_ = p0 + v * tt2 * .7 + Vector((0, 0, -4.9 * tt2 * tt2))
        keyp(o, f, loc=(p_.x, p_.y, max(.1, p_.z)) if e2 > -.1 else (0, 0, -50), rot=(tt2 * r.uniform(2, 7), tt2 * r.uniform(2, 7), 0))
    for j, o in enumerate(M_GLASS):
        r = random.Random(500 + j); tt2 = max(0, e2 - r.uniform(0, .8)); v = Vector((r.uniform(-3, 6), r.uniform(-10, -3), r.uniform(0, 5)))
        p_ = Vector((-15 + r.uniform(-10, 10), 2.4, r.uniform(2, 24))) + v * tt2 + Vector((0, 0, -4.9 * tt2 * tt2))
        keyp(o, f, loc=(p_.x, p_.y, max(.05, p_.z)) if e2 > 0 else (0, 0, -50), rot=(tt2 * 11, tt2 * 8, 0))
    for j, o in enumerate(M_SMOKE):
        r = random.Random(900 + j); tt2 = max(0, e2 - .1 - .06 * j); s_ = (2 + 7 * ease(clamp(tt2 / 2.2))) * r.uniform(.7, 1.2)
        keyp(o, f, loc=(-15 + r.uniform(-12, 12), 8 + r.uniform(-9, 2), 1.5 + 3 * clamp(tt2 / 2)) if e2 > .1 else (0, 0, -50), scale=(s_, s_, s_ * .7))
    pos = Vector(mix((8, -26, 1.9), (7, -22, 2.4), ease(u))) + shake(f, .3 * clamp(1 - abs(e2 - .3) / 1.6) if e2 > -.2 else 0)
    cam.look(pos, (-13, 6, 11 - 4 * ease(clamp(e2 / 2))), 22)


def s_l13():
    show("city", 12.0)
def a_l13(u, t, f):   # 岩も砕け、人が地面に沈んでいく
    e = t - ev_t("l13", 1)
    for o in CRACKS:
        keyp(o, f, scale=(2.0, 1, 1))
    for bi, slabs in enumerate(CITY_B):
        for fi, s_ in enumerate(slabs):
            keyp(s_, f, loc=(s_.location.x, s_.location.y, .6 + fi * .55))
    for i, (p_, h_) in enumerate(zip(CT_P, HOLES)):
        k = clamp((e + .5) / 1.6); keyp(p_, f, loc=(p_.location.x, p_.location.y, -.45 - 1.6 * ease(k))); keyp(h_, f, scale=(1.2, 1.2, 1))
    cam.look(mix((-3, -30, 4), (-2, -24, 6), ease(u)), (0, 0, 0), 26)

def s_l14():
    show("space"); BH.hide_render = DISK.hide_render = VENUS.hide_render = True
    for o, *_ in FRAG:
        o.hide_render = True
def a_l14(u, t, f):   # 宇宙：地球と月（現象と日付だけ）
    keyp(CLOUDS, f, rot=(0, 0, t * .05)); keyp(EARTH, f, rot=(0, 0, t * .03))
    key_fac(GROW, .26 + .2 * ease(u), f); key_fac(CRK, 3 + 6 * u, f)   # 大気・海・月より重く：ひびが少しずつ
    cam.look(mix((0, -30, 5), (6, -26, 7), ease(u)), (3, 2, 0), 35)

def s_l15():
    show("space"); BH.hide_render = DISK.hide_render = VENUS.hide_render = True
def a_l15(u, t, f):   # 月が近づきすぎて砕け、輪になる
    e = t - ev_t("l15", 1); k = ease(clamp(e / 1.2))
    keyp(MOON, f, loc=mix((26, 10, 2), (14, 6, 1), clamp(u * 1.4)), scale=(1 - k, 1 - k, 1 - k) if e > 0 else (1, 1, 1))
    for o, ang, rad, zz in FRAG:
        a = ang + t * .5 / (rad / 12); p_ = mix((14, 6, 1), (rad * math.cos(a), rad * math.sin(a), zz), k)
        keyp(o, f, loc=p_ if e > 0 else (0, 0, -50))
    keyp(CLOUDS, f, rot=(0, 0, t * .05)); key_fac(GROW, .46 + .16 * ease(u), f); key_fac(CRK, 9 + 6 * u, f)
    cam.look(mix((8, -36, 9), (5, -38, 12), ease(u)), (2, 2, 0), 30)

def s_l16():
    show("space"); MOON.hide_render = True
    for o, *_ in FRAG:
        o.hide_render = True
def a_l16(u, t, f):   # 地球の中心がブラックホールに。金星がはじき飛ばされる
    e = t - ev_t("l16", 1); k = ease(clamp(e / .8))
    keyp(EARTH, f, scale=(1 - .9 * k,) * 3); keyp(CLOUDS, f, scale=(1 - .9 * k,) * 3)
    key_fac(GROW, .62 + .3 * clamp(u * 1.5), f); key_fac(CRK, 15 + 10 * clamp(u * 1.5), f)
    keyp(BH, f, scale=(k,) * 3); keyp(DISK, f, scale=(k, k, .08 * k), rot=(.25, 0, t * .8))
    e2 = t - ev_t("l16", 2); vp = mix((-30, 40, 4), (-30, 40, 4), 0) if e2 < 0 else (-30 - 60 * e2, 40 + 50 * e2, 4)
    keyp(VENUS, f, loc=vp)
    cam.look(mix((2, -30, 8), (4, -34, 11), ease(u)), (-4, 4, 0), 30)

def s_l17():
    show("home", hour_of(0)); CEIL.data.energy = 500
def a_l17(u, t, f):   # 最後の札。画は朝の体重計に戻る（冒頭につながる）
    keyp(H_SCALE, f, loc=(-.4, -.6, FLOORZ + .05))
    cam.look(mix((1.2, -3.4, FLOORZ + 1.0), (.6, -2.6, FLOORZ + .35), ease(u)), (-.4, -.6, FLOORZ + .9 - .45 * u), 30)


def s_w01():
    show("liberty", 13.0)
def a_w01(u, t, f):   # 自由の女神：展望台の観光客の重さで、たいまつの腕が折れて海へ。女神はのけぞって沈む
    e = t - ev_t("w01", 0); k = ease(clamp(e / 1.3))
    tt = max(0, e); keyp(LB_ARM, f, loc=(3.2 + 6 * clamp(tt), -2 * clamp(tt), 32 - 4.9 * (tt * 1.6) ** 2 if tt > 0 else 32), rot=(0, .3 + 2.2 * clamp(tt / 1.2), 0))
    keyp(LB, f, loc=(0, 0, 31 - 6 * k), rot=(-.22 * k, .05 * k, 0))
    for j, o in enumerate(LB_SPLASH):
        r = random.Random(j); te = max(0, e - .9); v = Vector((r.uniform(-6, 6), r.uniform(-6, 6), r.uniform(8, 18)))
        p_ = Vector((22, -6, 0)) + v * te + Vector((0, 0, -4.9 * te * te)); keyp(o, f, loc=(p_.x, p_.y, max(-1, p_.z)) if te > 0 else (0, 0, -50))
    for p_ in LB_TOUR:
        keyp(p_, f, loc=(p_.location.x, p_.location.y, 31 - 6 * k))
    cam.look(mix((48, -78, 6), (44, -70, 7), ease(u)), (6, 0, 52 - 12 * k), 30)

def s_w02():
    show("eiffel", 13.0)
def a_w02(u, t, f):   # エッフェル塔：展望台の観光客の重さで、4 本の脚が外へ開き、開脚するようにしゃがむ
    e = t - ev_t("w02", 0); k = ease(clamp(e / 1.2)); wob = .04 * math.sin(e * 12) * clamp(1 - e / 2) if e > 0 else 0
    keyp(EF, f, scale=(1 + .9 * k, 1 + .9 * k, 1 - .62 * k)); keyp(EF_TOP, f, rot=(wob + .12 * k, 0, math.pi / 4))
    for p_ in EF_TOUR:
        keyp(p_, f, loc=(p_.location.x * (1 + .9 * k), p_.location.y * (1 + .9 * k), 59 * (1 - .62 * k)))
    cam.look(mix((14, -230, 2.0), (12, -210, 2.0), ease(u)), (0, 0, 80 - 35 * k), 28)

def s_w03():
    show("pisa", 13.0)
def a_w03(u, t, f):   # ピサの斜塔：観光客が「支えるポーズ」で寄りかかると、まっすぐになり、それから沈む
    e = t - ev_t("w03", 0); k1 = ease(clamp(e / .8)); k2 = ease(clamp((e - 1.0) / 1.0))
    keyp(PS, f, loc=(0, 0, -9 * k2), rot=(0, math.radians(-4) * (1 - k1), 0))
    for p_ in PS_TOUR:
        keyp(p_, f, loc=tuple(p_.location))
    cam.look(mix((22, -62, 1.6), (20, -56, 1.6), ease(u)), (0, 0, 24 - 6 * k2), 26)

NAMES = [s["id"] for s in PLAN["shots"]]
SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in NAMES}
anim = [cam.o]
K.render_shots(HERE, SHOTS, NAMES, O, anim)
