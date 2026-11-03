"""pilot_040（ギムリー・グライダー）の 3D の場面（Blender、ext/blender/blkit.py）。選択設計：問いまでは機長の目線だけ、後半は外から。
使い方：blender -b -P anatomy_room/production/pilot_040/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：767 を模した操縦室（画面は模式）、機体（塗装なし）、マニトバの畑と湖（手続き的）、閉鎖された空軍の滑走路とレースの車・テント。人物は描かない（席の後ろ姿だけ）。
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy
from mathutils import Vector, Euler
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); cam = K.Cam()
R = random.Random(40)
TEX = os.path.join(HERE, "tex")
if not os.path.exists(os.path.join(TEX, "eicas.png")):
    import subprocess; subprocess.run(["python", os.path.join(HERE, "make_tex.py")], check=True)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (0, 0, 0, 1); return m, b


def screen_mat(name, img):
    """画面：画像の明るさを MIX で 0（消えた）〜1（点いた）に。毎コマ keyframe"""
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tx = n.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(os.path.join(TEX, img))
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[6].default_value = (0, 0, 0, 1); L.new(tx.outputs[0], mx.inputs[7]); mx.inputs[0].default_value = 1
    L.new(mx.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = 3.2; b.inputs["Base Color"].default_value = (0, 0, 0, 1); b.inputs["Roughness"].default_value = .08
    return m, mx


# ---------------------------------------------------------------- 地面：マニトバの畑（手続き的）・ウィニペグ湖、地球の丸み
EARTH = K.Earth(cloud_alt=2500)
em = EARTH.earth.data.materials[0]; cr = [n for n in em.node_tree.nodes if n.type == "VALTORGB"][0].color_ramp
for e_, c in zip(cr.elements, [(.30, .36, .16, 1), (.22, .25, .12, 1), (.42, .40, .22, 1), (.26, .32, .14, 1), (.18, .22, .1, 1), (.12, .16, .08, 1)]):
    e_.color = c
lake = bpy.data.materials.new("lake"); lake.use_nodes = True; lb = lake.node_tree.nodes["Principled BSDF"]; lb.inputs["Base Color"].default_value = (.05, .09, .12, 1); lb.inputs["Roughness"].default_value = .08
bpy.ops.mesh.primitive_plane_add(size=1, location=(-60000, -40000, 0)); LAKE = bpy.context.object; LAKE.scale = (40000, 120000, 1); LAKE.data.materials.append(lake)

# ---------------------------------------------------------------- 滑走路（閉鎖された空軍の基地）・レースの車とテント。滑走路は原点から -y へ 2200m
RW = group("runway")
asph = K.mat("asph", (.08, .08, .085), .85); paint = K.mat("paint", (.85, .85, .8), .6)
K.box("rw", (45, 2200, .2), (0, -1100, 0), asph, bevel=0, parent=RW)
for k in range(30):
    K.box(f"cl{k}", (1, 30, .22), (0, -40 - k * 70, 0), paint, bevel=0, parent=RW)
K.box("grass", (2000, 4000, .1), (0, -1100, -.15), K.mat("grass", (.2, .28, .12), .95), bevel=0, parent=RW)
for k in range(14):   # レースの車（滑走路の奥）
    K.box(f"car{k}", (1.8, 4.2, 1.3), (R.uniform(-30, 30), -2050 - R.uniform(0, 140), .7), K.mat(f"carm{k}", (R.random(), R.random() * .6, R.random() * .4), .4, .5), parent=RW)
for k in range(10):   # テント
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3, depth=2.6, location=(R.uniform(-60, 60), -2250 - R.uniform(0, 80), 1.3)); t = bpy.context.object
    t.data.materials.append(K.mat(f"tent{k}", (R.uniform(.4, .9), R.uniform(.3, .8), R.uniform(.2, .5)), .9)); t.parent = RW

# ---------------------------------------------------------------- 機体（767 を模した形、塗装なし）
PLANE = group("plane"); white = K.mat("pw", (.88, .88, .86), .35, .1); grey = K.mat("pg", (.55, .56, .58), .4, .6); win = K.mat("pwin", (.03, .04, .05), .1)
bpy.ops.mesh.primitive_cylinder_add(radius=2.5, depth=44, vertices=48, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0)); f = bpy.context.object; f.data.materials.append(white); f.parent = PLANE; bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_uv_sphere_add(radius=2.5, location=(0, -22, 0)); n_ = bpy.context.object; n_.scale = (1, 2.2, 1); n_.data.materials.append(white); n_.parent = PLANE; bpy.ops.object.shade_smooth()
K.box("wings", (47, 7, .45), (0, 2, -1.2), white, (0, 0, 0), parent=PLANE); K.box("tailh", (18, 4, .3), (0, 21, .8), white, parent=PLANE); K.box("fin", (.35, 6, 8), (0, 22, 4.5), white, parent=PLANE)
for x in (-9, 9):
    bpy.ops.mesh.primitive_cylinder_add(radius=1.4, depth=5, vertices=32, location=(x, -2, -2.6), rotation=(math.pi / 2, 0, 0)); e_ = bpy.context.object; e_.data.materials.append(grey); e_.parent = PLANE
K.box("cockwin", (3.2, .3, .8), (0, -26.2, .9), win, (.5, 0, 0), parent=PLANE)
for k in range(30):
    K.box(f"w{k}", (.05, .35, .45), (2.48, -16 + k * 1.1, .6), win, bevel=0, parent=PLANE); K.box(f"wr{k}", (.05, .35, .45), (-2.48, -16 + k * 1.1, .6), win, bevel=0, parent=PLANE)
for x in (-3.5, 3.5):
    K.tube((x, 3, -2.4), (x, 3, -4.4), .25, grey, PLANE, 12)
NOSEGEAR = K.tube((0, -19, -2.4), (0, -19, -3.4), .2, grey, PLANE, 12)
SPARK_M, SPARK = emit("spark", (1, .55, .2), 0)
bpy.ops.mesh.primitive_cone_add(radius1=.4, radius2=2.5, depth=8, location=(0, -16, -2.6), rotation=(-math.pi / 2, 0, 0)); spk = bpy.context.object; spk.data.materials.append(SPARK_M); spk.parent = PLANE

# ---------------------------------------------------------------- 操縦室（機長の席から見る。窓の外は CAM_POS の空）。原点の上 z=5000（空の場面の基準）
CK = group("cockpit"); CZ = 0
panel_m = K.mat("ckp", (.03, .033, .037), .6, .2); frame = K.mat("ckf", (.05, .052, .056), .5, .3)
K.box("glare", (2.6, .7, .18), (0, -1.15, .55), panel_m, parent=CK)                       # 計器の庇
K.box("mainp", (2.6, .1, .75), (0, -1.0, .1), panel_m, (-.25, 0, 0), parent=CK)            # 計器盤
K.box("pedestal", (.6, 1.2, .5), (0, -.3, -.45), panel_m, parent=CK)
for x in (-1.25, -.42, .42, 1.25):   # 窓の柱
    K.box(f"post{x}", (.08, .08, 1.1), (x, -1.55, 1.0), frame, (-.45, 0, 0), parent=CK)
K.box("roofframe", (2.7, .9, .08), (0, -1.2, 1.45), frame, parent=CK)
SCR = []
for k, (x, img) in enumerate([(-.95, "adi.png"), (-.55, "nav.png"), (-.1, "eicas.png"), (.35, "eicas.png"), (.75, "nav.png"), (1.05, "adi.png")]):
    m, mx = screen_mat(f"scr{k}", img)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, -.94, .16), rotation=(math.radians(-(90 - 25)), 0, 0)); s = bpy.context.object; s.scale = (.36, .36, 1); s.data.materials.append(m); s.parent = CK; SCR.append(mx)
STBY = []
for k, x in enumerate((-.2, .0, .2)):   # 予備の計器（丸い計器）
    bpy.ops.mesh.primitive_cylinder_add(radius=.06, depth=.03, location=(x, -.9, -.18), rotation=(math.radians(65), 0, 0)); g = bpy.context.object; g.data.materials.append(K.mat(f"sg{k}", (.85, .85, .8), .4)); g.parent = CK
LAMP_M, LAMP = emit("amber", (1, .55, .05), 0)
for k in range(6):
    K.box(f"amb{k}", (.05, .02, .03), (-.3 + k * .12, -1.12, .42), LAMP_M, bevel=0, parent=CK)
for x in (-.55, .55):   # 操縦かん
    K.tube((x, -.55, -.6), (x, -.62, -.05), .03, frame, CK, 12); K.box(f"yoke{x}", (.32, .04, .1), (x, -.63, -.02), frame, parent=CK)
K.box("seatL", (.55, .55, .8), (-.55, .4, -.4), K.mat("seat", (.04, .035, .03), .8), parent=CK); K.box("seatR", (.55, .55, .8), (.55, .4, -.4), K.mat("seat2", (.04, .035, .03), .8), parent=CK)
cl = bpy.data.lights.new("cklight", "AREA"); cl.energy = 8; cl.size = 1.5; cl.color = (1, .9, .8); clo = bpy.data.objects.new("cklight", cl); sc.collection.objects.link(clo); clo.location = (0, .2, 1.1); clo.parent = CK
ALL = {"runway": RW, "plane": PLANE, "cockpit": CK}


def show(*names):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()
    for mx in SCR:
        mx.inputs[0].default_value = 1
    CK.rotation_euler = (0, 0, 0)
    LAMP.inputs["Emission Strength"].default_value = 0; SPARK.inputs["Emission Strength"].default_value = 0

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def evening(alt, exp=-2.6, el=9, rot=290):   # 夏の夜 8 時のマニトバ：低い太陽（西）
    sky.set(alt, el, rot, 4.5); EARTH.altitude(alt, .45); sc.view_settings.exposure = exp


def at_alt(alt, y=0.0, x=0.0):   # 操縦室・機体を高度 alt に置く（地球は原点の下にあるので、物を持ち上げる）
    for g in (CK, PLANE):
        g.location = (x, y, alt)


def keyscr(f, v):
    for mx in SCR:
        mx.inputs[0].default_value = v; mx.inputs[0].keyframe_insert("default_value", frame=f + 1)


def keylamp(f, v):
    LAMP.inputs["Emission Strength"].default_value = v; LAMP.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)


def eye(alt, t, k=.004):   # 機長の目の位置（左席）と小さな揺れ
    return Vector((-.55 + math.sin(t * 7) * k, .25, alt + .62 + math.sin(t * 9) * k))


# ---------------------------------------------------------------- ショット（問いまでは機長の目線）
A0 = 10670   # 3 万 5 千フィート
def s_l00():
    show("cockpit"); evening(A0); at_alt(A0)
def a_l00(u, t, f):   # 画面が消えていく操縦室（オープニング）
    p = eye(A0, t, .01); cam.look(p, p + Vector((.25, -4, -.6)), 22, roll=-.03); keyscr(f, max(0, 1 - t / 1.2)); keylamp(f, 8 if int(t * 3) % 2 else 1)

def s_l00a():
    show("cockpit"); evening(A0 - 3000); at_alt(A0 - 3000)
def a_l00a(u, t, f):   # A：左に旋回して、近くの空軍の基地へ（機体を傾ける）
    p = eye(A0 - 3000, t, .006); cam.look(p, p + Vector((-1.6, -4, -.9)), 22, roll=.28 * K.ease(u)); keyscr(f, 0)

def s_l00b():
    show("cockpit"); evening(400)
def a_l00b(u, t, f):   # B：湖へ不時着する（低く、水面が迫る）
    z = 260 - 55 * t; x0, y0 = -60000, -30000 - 75 * t; CK.location = (x0, y0, z); PLANE.location = (0, 0, -9000)
    EARTH.altitude(z, .45); sc.view_settings.exposure = -2.6
    CK.rotation_euler = (math.radians(10 + 3 * u), math.radians(1.5 * math.sin(t * 2)), 0); bpy.context.view_layer.update(); M = CK.matrix_world
    p = M @ Vector((-.55 + math.sin(t * 9) * .008, .25, .66 + math.sin(t * 11) * .008)); cam.look(p, M @ Vector((-.45, -4, .25)), 22); keyscr(f, 0)

def s_l01():
    show("cockpit"); evening(A0 + 1800); at_alt(A0 + 1800)
def a_l01(u, t, f):   # 巡航：画面は点いている
    p = eye(A0 + 1800, t); cam.look(p, mix((p.x + .2, p.y - 4, p.z - .4), (p.x + .3, p.y - 4, p.z - .9), K.ease(u)), 24); keyscr(f, 1)

def s_l02():
    show("cockpit"); evening(A0 + 1500); at_alt(A0 + 1500)
def a_l02(u, t, f):   # 警告灯（琥珀色）
    p = eye(A0 + 1500, t, .006); cam.look(p, (p.x + .25, -1.1, p.z - .15), 28); keylamp(f, 9 if int(t * 4) % 2 else 2); keyscr(f, 1)

def s_l03():
    show("cockpit"); evening(A0 + 700); at_alt(A0 + 700)
def a_l03(u, t, f):   # エンジンが止まる：画面がちらつく
    p = eye(A0 + 700, t, .012); cam.look(p, (p.x + .5, -1.0, p.z - .45), 26); keylamp(f, 9 if int(t * 5) % 2 else 2)
    keyscr(f, 1 if u < .6 else (.2 if int(t * 12) % 3 else .9))

def s_l04():
    show("cockpit"); evening(A0); at_alt(A0)
def a_l04(u, t, f):   # 画面がすべて消えた。残るのは予備の計器
    p = eye(A0, t, .008); cam.look(p, mix((p.x + .5, -1.0, p.z - .45), (p.x + .55, -.9, p.z - .7), K.ease(u)), mix((26,), (34,), K.ease(u))[0]); keyscr(f, 0); keylamp(f, 4)

def s_l05():
    show("cockpit"); evening(A0 - 1500); at_alt(A0 - 1500)
def a_l05(u, t, f):   # 窓の外：遠くの湖と、地上
    p = eye(A0 - 1500, t, .006); cam.look(p, p + Vector((-2.4, -3.2, -1.4)), 22, roll=.05); keyscr(f, 0)

def s_l06():
    show("cockpit"); evening(A0 - 2500, -2.8); at_alt(A0 - 2500)
def a_l06(u, t, f):   # 問い：暗い操縦室から前を見る
    p = eye(A0 - 2500, t, .006); cam.look(p, p + Vector((.0, -4, -.7)), 22 + 4 * u); keyscr(f, 0); keylamp(f, 6 if int(t * 2.5) % 2 else 1)

# 後半（外から）
def s_l07():
    show("plane"); evening(4000, -2.4); at_alt(4000)
def a_l07(u, t, f):   # 音のない空を滑る機体
    PLANE.location = (0, -40 * t, 4000 - 8 * t); cam.look((60 - 10 * u, -40 * t + 30, 4004), (0, -40 * t, 4000 - 8 * t), 32)

def s_l08():
    show("cockpit"); evening(3500, -2.6); at_alt(3500)
def a_l08(u, t, f):   # 副操縦士の席の後ろから（右の席、人は描かない）
    p = Vector((.9, 1.0, 3500 + .7)); cam.look(p, (.4, -1.0, 3500 + .1), 30); keyscr(f, 0)

def s_l09():
    show("plane", "runway"); evening(0, -2.3, 7)
def a_l09(u, t, f):   # 最後の進入：機体を横に滑らせる
    d = 2200 * (1 - u) + 300; PLANE.location = (8 * (1 - u), d, 60 + 300 * (1 - u)); PLANE.rotation_euler = (math.radians(-3), math.radians(-18 * (1 - u * .7)), math.radians(14 * (1 - u)))
    pl = PLANE.location; cam.look((pl.x - 70, pl.y - 90, pl.z + 6), (pl.x, pl.y - 10, pl.z), 45)

def s_l10():
    show("plane", "runway"); evening(0, -2.3, 7)
def a_l10(u, t, f):   # 前輪が出きらず、機首が滑走路をこする（火花）。その先にレースの車とテント
    y = -200 - 1500 * K.ease(min(1, u * 1.1)); PLANE.location = (0, y, 3.2); PLANE.rotation_euler = (math.radians(-4), 0, 0)
    SPARK.inputs["Emission Strength"].default_value = 30 * (1 if u > .1 else 0); SPARK.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
    cam.look((28, y - 110, 4), (0, y - 5, 2.5), 35)

def s_l11():
    show("plane", "runway"); evening(0, -2.4, 6)
def a_l11(u, t, f):   # 止まった機体（遠景）
    PLANE.location = (0, -1900, 3.0); PLANE.rotation_euler = (math.radians(-4), 0, 0); cam.look(mix((-160, -1700, 40), (-140, -1750, 30), K.ease(u)), (0, -1950, 3), 30)

def s_l12():
    show("plane", "runway"); evening(0, -2.5, 6)
def a_l12(u, t, f):   # 夕暮れの滑走路と機体
    PLANE.location = (0, -1900, 3.0); PLANE.rotation_euler = (math.radians(-4), 0, 0); cam.look(mix((30, -1830, 3), (25, -1845, 2.5), K.ease(u)), (-5, -1950, 4), 26)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]}
ORDER = ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, PLANE, CK])
