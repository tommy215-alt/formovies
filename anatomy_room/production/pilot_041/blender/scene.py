"""pilot_041（ロゴゾフの自己手術）の 3D の場面（Blender、ext/blender/blkit.py）。選択設計：問いまでは本人（ベッドの上）の目線だけ、後半は外から。
使い方：blender -b -P anatomy_room/production/pilot_041/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：南極の基地の小屋（模式）、吹雪（小さな雪の粒を横に流す）、手術の灯り・鏡・器具。人物は MakeHuman / MPFB（顔は描かない：後ろ姿・遠景・手だけ）。
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy, bmesh
from mathutils import Vector
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); cam = K.Cam()
R = random.Random(41)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (*col, 1); return m, b


# ---------------------------------------------------------------- 雪原（原点のまわり 600 m、なだらかな吹きだまり）と、遠くの平らな氷
snow = bpy.data.materials.new("snow"); snow.use_nodes = True; n = snow.node_tree.nodes; L = snow.node_tree.links; b = n["Principled BSDF"]
b.inputs["Base Color"].default_value = (.75, .8, .88, 1); b.inputs["Roughness"].default_value = .7
tc = n.new("ShaderNodeTexCoord"); no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = 2; L.new(tc.outputs["Object"], no.inputs["Vector"])
bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .15; L.new(no.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
bpy.ops.mesh.primitive_grid_add(x_subdivisions=160, y_subdivisions=160, size=600); gnd = bpy.context.object; gnd.data.materials.append(snow)
for v in gnd.data.vertices:
    x, y = v.co.x, v.co.y; v.co.z = .8 * math.sin(x * .05 + y * .02) + .5 * math.sin(y * .09) - .6
for p in gnd.data.polygons:
    p.use_smooth = True
bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, -1.6)); far = bpy.context.object; far.data.materials.append(snow)

# ---------------------------------------------------------------- 小屋（内側 5 × 4 m、高さ 2.4 m）。原点＝床の中央、-y がベッドの足もと、窓は +x の壁
HUT = group("hut"); wood = K.mat("wood", (.20, .13, .08), .75); wall = K.mat("wall", (.38, .34, .28), .85); floor = K.mat("floor", (.14, .1, .07), .8)
K.box("floor", (5, 4, .1), (0, 0, -.05), floor, bevel=0, parent=HUT); K.box("ceil", (5, 4, .1), (0, 0, 2.45), wood, bevel=0, parent=HUT)
K.box("wN", (5, .12, 2.5), (0, 2.06, 1.2), wall, bevel=0, parent=HUT); K.box("wS", (5, .12, 2.5), (0, -2.06, 1.2), wall, bevel=0, parent=HUT)
K.box("wW", (.12, 4, 2.5), (-2.56, 0, 1.2), wall, bevel=0, parent=HUT)
for z0, z1 in ((-.05, 1.0), (1.8, 2.5)):   # 東の壁：窓（y -.4〜.4、z 1.0〜1.8）の穴を残す
    K.box(f"wE{z0}", (.12, 4, z1 - z0), (2.56, 0, (z0 + z1) / 2), wall, bevel=0, parent=HUT)
for y0, y1 in ((-2, -.4), (.4, 2)):
    K.box(f"wEs{y0}", (.12, y1 - y0, .8), (2.56, (y0 + y1) / 2, 1.4), wall, bevel=0, parent=HUT)
glass = bpy.data.materials.new("frost"); glass.use_nodes = True; gb = glass.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (.85, .9, 1, 1); gb.inputs["Roughness"].default_value = .35; gb.inputs["Transmission Weight"].default_value = 1
K.box("pane", (.02, .8, .8), (2.56, 0, 1.4), glass, bevel=0, parent=HUT)
for k in range(6):   # 天井の梁
    K.box(f"beam{k}", (.12, 4, .14), (-2.2 + k * .88, 0, 2.33), wood, parent=HUT)
# ベッド（西の壁ぞい、頭は +y）・机・器具の台
K.box("bed", (.9, 2.0, .45), (-1.9, .6, .22), wood, parent=HUT); SHEET = K.mat("sheet", (.78, .78, .74), .85)
K.box("mattress", (.86, 1.96, .14), (-1.9, .6, .52), SHEET, bevel=.05, parent=HUT)
K.box("pillow", (.6, .35, .12), (-1.9, 1.4, .64), SHEET, bevel=.05, parent=HUT)
K.box("desk", (1.2, .7, .05), (1.8, -1.6, .78), wood, parent=HUT)
for x, y in ((1.25, -1.9), (2.35, -1.9), (1.25, -1.3), (2.35, -1.3)):
    K.box(f"dl{x}{y}", (.05, .05, .78), (x, y, .39), wood, parent=HUT)
K.box("radio", (.45, .3, .25), (2.0, -1.7, .93), K.mat("radio", (.18, .2, .17), .5, .3), parent=HUT)
TRAY = group("tray"); TRAY.parent = HUT; TRAY.location = (-1.25, .5, .78); steel = K.mat("steel", (.8, .8, .82), .18, 1)
K.box("tray", (.45, .3, .02), (0, 0, 0), steel, parent=TRAY)
for k in range(5):
    K.box(f"inst{k}", (.012, .2, .008), (-.16 + k * .08, 0, .02), steel, (0, 0, R.uniform(-.2, .2)), parent=TRAY)
K.box("stand", (.05, .05, .78), (-1.25, .5, .39), steel, parent=HUT)
# 体（ベッドの上の自分：シーツの盛り上がりと、おなか）
BODY = K.box("body", (.42, 1.3, .2), (-1.9, .25, .66), SHEET, bevel=.08, parent=HUT)
SKIN = K.mat("skin", (.62, .45, .36), .6)
BELLY = K.box("belly", (.3, .35, .06), (-1.9, .55, .76), SKIN, bevel=.04, parent=HUT)
# 手（自分の右手：前腕と手の甲、メス）
HAND = group("hand"); HAND.parent = HUT
GLOVE = K.mat("glove", (.78, .74, .62), .45)
K.tube((0, .3, .02), (0, 0, 0), .03, SKIN, HAND, 16); K.tube((0, 0, 0), (0, -.06, -.005), .026, GLOVE, HAND, 16)
K.box("palm", (.075, .085, .028), (0, -.1, -.008), GLOVE, (math.radians(-8), 0, 0), bevel=.012, parent=HAND)
for k, x in enumerate((-.027, -.009, .009, .027)):   # 指（メスを握る）
    K.tube((x, -.14, -.012), (x * .7, -.19, -.04), .009, GLOVE, HAND, 10)
K.tube((.035, -.08, -.01), (.015, -.17, -.035), .01, GLOVE, HAND, 10)
K.tube((0, -.15, -.03), (0, -.3, -.08), .004, steel, HAND, 8); K.box("blade", (.003, .03, .01), (0, -.315, -.085), steel, (math.radians(18), 0, 0), bevel=0, parent=HAND)
# 鏡（天井から下がる・仲間が持つ）
mirror = bpy.data.materials.new("mirror"); mirror.use_nodes = True; mb = mirror.node_tree.nodes["Principled BSDF"]
mb.inputs["Metallic"].default_value = 1; mb.inputs["Roughness"].default_value = .02; mb.inputs["Base Color"].default_value = (.92, .92, .92, 1)
MIRROR = group("mirror"); MIRROR.parent = HUT
bpy.ops.mesh.primitive_cylinder_add(radius=.16, depth=.01, vertices=48); mo = bpy.context.object; mo.data.materials.append(mirror); mo.parent = MIRROR
K.tube((0, 0, 0), (0, -.25, 0), .012, wood, MIRROR, 8)
# 灯り：天井の裸電球（揺れる）と、手術用の明るい灯り
BULB = group("bulb"); BULB.parent = HUT; BULB.location = (-1.2, .3, 2.4)
bm_m, BULB_E = emit("bulbm", (1, .75, .45), 30)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.04, location=(0, 0, -.55)); bo = bpy.context.object; bo.data.materials.append(bm_m); bo.parent = BULB
K.tube((0, 0, 0), (0, 0, -.5), .004, wood, BULB, 6)
bl = bpy.data.lights.new("bulbL", "POINT"); bl.energy = 60; bl.color = (1, .78, .5); bl.shadow_soft_size = .05
blo = bpy.data.objects.new("bulbL", bl); sc.collection.objects.link(blo); blo.parent = BULB; blo.location = (0, 0, -.62)
OL = bpy.data.lights.new("oplamp", "SPOT"); OL.energy = 0; OL.spot_size = math.radians(55); OL.color = (.95, .97, 1); OL.shadow_soft_size = .3
olo = bpy.data.objects.new("oplamp", OL); sc.collection.objects.link(olo); olo.parent = HUT; olo.location = (-1.9, .55, 2.2)
lh_m, LH = emit("lamphead", (.95, .97, 1), 0)
bpy.ops.mesh.primitive_cone_add(radius1=.28, radius2=.08, depth=.18, location=(-1.9, .55, 2.25)); lh = bpy.context.object; lh.data.materials.append(K.mat("lampshell", (.5, .52, .5), .4, .7)); lh.parent = HUT
bpy.ops.mesh.primitive_cylinder_add(radius=.25, depth=.01, location=(-1.9, .55, 2.155)); lf = bpy.context.object; lf.data.materials.append(lh_m); lf.parent = HUT
WIN = bpy.data.lights.new("winL", "AREA"); WIN.energy = 25; WIN.size = .8; WIN.color = (.5, .62, .9)
wlo = bpy.data.objects.new("winL", WIN); sc.collection.objects.link(wlo); wlo.parent = HUT; wlo.location = (2.4, 0, 1.4); wlo.rotation_euler = (0, math.radians(-90), 0)
# 仲間（気象学者・機械の技師）：後ろ姿
MATE = []
for k, (x, y, col) in enumerate([(-1.0, -.3, (.25, .27, .32)), (-1.3, 1.5, (.32, .25, .2))]):
    h = K.human("man_stand", suit=col, helmet=False, pack=False); h.parent = HUT; h.location = (x, y, 0); MATE.append(h)
SITM = K.human("man_sit", suit=(.85, .85, .8), helmet=False, pack=False); SITM.parent = HUT   # 後半：ベッドの上で半身を起こす本人（後ろ姿）
CHAIRS = [K.box(f"chair{k}", (.4, .4, .45), (1.4 + k * .8, -1.0, .22), wood, parent=HUT) for k in range(2)]

# ---------------------------------------------------------------- 外の小屋（基地）：小屋の外側と、まわりの小屋・無線の柱
BASE = group("base"); ext = K.mat("ext", (.28, .2, .14), .8)
for k, (x, y, sx, sy) in enumerate([(0, 0, 5.4, 4.4), (14, -6, 7, 4), (-12, 8, 6, 5), (8, 16, 4, 4), (-20, -14, 8, 4)]):
    K.box(f"hut{k}", (sx, sy, 2.8), (x, y, 1.3), ext, bevel=.05, parent=BASE); K.box(f"roof{k}", (sx + .4, sy + .4, .2), (x, y, 2.8), K.mat(f"rs{k}", (.7, .74, .8), .7), parent=BASE)
K.box("lit", (.05, .8, .8), (2.73, 0, 1.4), emit("litw", (1, .75, .45), 6)[0], bevel=0, parent=BASE)
K.tube((6, 6, 0), (6, 6, 14), .08, K.mat("mast", (.3, .3, .3), .5, .6), BASE, 8)

# ---------------------------------------------------------------- 雪の粒（横に流す。カメラのまわり 40 m の箱に 6000 粒、毎コマ動かして繰り返す）
SNOW = None
def make_snow(n=6000, size=40, h=10):
    global SNOW
    me = bpy.data.meshes.new("snow"); bm_ = bmesh.new()
    for _ in range(n):
        c = Vector((R.uniform(-size / 2, size / 2), R.uniform(-size / 2, size / 2), R.uniform(-1, h))); s = R.uniform(.008, .02)
        bmesh.ops.create_icosphere(bm_, subdivisions=0, radius=s, matrix=__import__("mathutils").Matrix.Translation(c))
    bm_.to_mesh(me); bm_.free(); SNOW = bpy.data.objects.new("snow", me); sc.collection.objects.link(SNOW)
    sm, _ = emit("snowp", (.85, .9, 1), .6); SNOW.data.materials.append(sm); SNOW.visible_shadow = False
make_snow()
ALL = {"hut": HUT, "base": BASE}


def unhide(o):
    for c in [o] + list(o.children_recursive):
        c.hide_render = False


def show(*names, mates=(), sit=False, snow=True):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()
    for o in (OL, bl):
        o.animation_data_clear()

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    if "hut" in names:
        for k, h in enumerate(MATE):
            hide(h, k not in mates)
        hide(SITM, not sit); hide(HAND, True); hide(MIRROR, True); BODY.hide_render = sit; BELLY.hide_render = True
    SNOW.hide_render = not snow; OL.energy = 0; bl.energy = 60; LH.inputs["Emission Strength"].default_value = 0
    for o in BASE.children:
        o.hide_render = "base" not in names
    [o for o in HUT.children if o.name.startswith("pane")][0].hide_render = False


def night(exp=-1.2):   # 極夜に近い冬：太陽は地平線のすぐ下、青い空
    sky.set(0, -2, 200, 0.0); sc.view_settings.exposure = exp
    w = sc.world.node_tree.nodes["Background"]; w.inputs[1].default_value = .35


def snow_at(t, center, wind=8.0):   # 雪を風で流す（箱の中で繰り返す）
    x = (t * wind) % 40 - 20; SNOW.location = (center[0] + x, center[1] + math.sin(t * .7) * 2, center[2] - (t * 1.2) % 4)


def swing(t, k=.12):   # 裸電球の揺れ（吹きつける風で小屋がきしむ）
    BULB.rotation_euler = (math.sin(t * 1.6) * k, math.sin(t * 1.1 + 1) * k * .6, 0)


def head(t, k=.004):   # 寝ている自分の目（頭は枕の上）
    return Vector((-1.9 + math.sin(t * 3) * k, 1.25, .95 + math.sin(t * 2.3) * k))


def key_op(f, v):
    OL.energy = v; OL.keyframe_insert("energy", frame=f + 1); LH.inputs["Emission Strength"].default_value = v / 25; LH.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)


# ---------------------------------------------------------------- ショット（問いまでは本人の目線）
def s_l00():
    show("hut")
def a_l00(u, t, f):   # 天井。揺れる裸電球（寝たまま見上げる）
    night(); swing(t, .2); snow_at(t, (23.5, 0, 0)); p = head(t, .01); cam.look(p, (p.x + .5, p.y - .9, 2.4), 18, roll=.05)

def s_l00a():
    show("hut", mates=(0, 1))
def a_l00a(u, t, f):   # A：仲間に任せる（ベッドの横に立つ二人の背中と、器具の台）
    night(); swing(t); snow_at(t, (23.5, 0, 0)); key_op(f, 300); p = head(t); cam.look(p, (-1.1, .1, 1.0), 20)
    MATE[0].location = (-1.05, .2, 0); MATE[0].rotation_euler = (0, 0, math.radians(39)); MATE[1].location = (-1.2, -.6, 0); MATE[1].rotation_euler = (0, 0, math.radians(20))

def s_l00b():
    show("hut"); unhide(HAND); unhide(MIRROR); BELLY.hide_render = False
def a_l00b(u, t, f):   # B：自分で切る（鏡の中のおなかと、メスを持つ自分の手）
    night(); swing(t, .05); snow_at(t, (23.5, 0, 0)); key_op(f, 400)
    MIRROR.location = (-1.9, .2, 1.45); MIRROR.rotation_euler = (math.radians(65), 0, 0)
    HAND.location = (-1.8, .85 - .08 * K.ease(u), .88); HAND.rotation_euler = (math.radians(-20), 0, math.radians(-15))
    MIRROR.location = (-1.9, .3, 1.25)
    p = Vector((-1.9, 1.2, 1.08)); cam.look(p, (-1.87, .58, .9), 24)

def s_l01():
    show("hut")
def a_l01(u, t, f):   # 小屋の中。凍った窓の外は吹雪
    night(); swing(t); snow_at(t, (23.5, 0, 0)); p = Vector((-1.6, 1.0, 1.05 + math.sin(t * 2) * .004)); cam.look(p, (2.5, -.2 + .2 * u, 1.35), 24)

def s_l02():
    show("hut", "base")
def a_l02(u, t, f):   # 窓から外：雪原と、閉ざされた海の方向
    night(-.9); snow_at(t, (12, 0, 0), 12); p = Vector((2.5, .1, 1.45)); cam.look(p, (40, -6 * u, .8), 28)
    [o for o in HUT.children if o.name.startswith("pane")][0].hide_render = True
    for o in BASE.children:
        if o.name.startswith(("hut0", "roof0", "lit")):
            o.hide_render = True

def s_l03():
    show("hut")
def a_l03(u, t, f):   # 痛み：おなかの上の毛布。顔をしかめて見下ろす
    night(); swing(t, .08); snow_at(t, (23.5, 0, 0)); p = head(t, .012); cam.look(p, (-1.9, .2, .6), 22, roll=-.08)

def s_l04():
    show("hut", mates=(0, 1))
def a_l04(u, t, f):   # 仲間たちは机のそばで（背中）。黙っている自分
    night(); swing(t); snow_at(t, (23.5, 0, 0)); p = head(t); cam.look(p, (1.6, -1.4, .9), 26)
    MATE[0].location = (1.4, -.8, 0); MATE[0].rotation_euler = (0, 0, 0); MATE[1].location = (2.1, -.7, 0); MATE[1].rotation_euler = (0, 0, math.radians(-10))

def s_l05():
    show("hut")
def a_l05(u, t, f):   # 痛みが強くなる：天井がゆがむ
    night(-1.4); swing(t, .25); snow_at(t, (23.5, 0, 0)); p = head(t, .02); cam.look(p, (p.x + .3, p.y - .5, 2.4), 16, roll=.12 * math.sin(t * .8))

def s_l06():
    show("hut"); unhide(MIRROR)
def a_l06(u, t, f):   # 問い：手術の灯りがともる
    night(); swing(t, .05); snow_at(t, (23.5, 0, 0)); key_op(f, 400 * min(1, u * 3)); MIRROR.location = (-1.9, .2, 1.45); MIRROR.rotation_euler = (math.radians(65), 0, 0)
    p = head(t); cam.look(p, (-1.9, .4, 2.1), 22 + 4 * u)

# 後半（外から）
def s_l07():
    show("base")
def a_l07(u, t, f):   # 吹雪の中の基地
    night(-.8); snow_at(t, (-10, -20, 0), 14); cam.look(K.ease(u) * Vector((4, 3, -.5)) + Vector((-18, -30, 2.2)), (0, 0, 1.6), 30)

def s_l08():
    show("hut", mates=(0, 1), sit=True, snow=False)
def a_l08(u, t, f):   # 仲間（背中）と、ベッドの上の本人（後ろ姿）
    night(); swing(t); SITM.location = (-1.9, .9, .45); SITM.rotation_euler = (0, 0, math.radians(180))
    MATE[0].location = (-.9, .4, 0); MATE[0].rotation_euler = (0, 0, math.radians(-90)); MATE[1].location = (-1.0, -.6, 0); MATE[1].rotation_euler = (0, 0, math.radians(-70))
    cam.look(mix((1.6, -1.6, 1.5), (1.4, -1.3, 1.45), K.ease(u)), (-1.5, .2, .9), 28)

def s_l09():
    show("hut", mates=(0, 1), sit=True, snow=False); unhide(MIRROR)
def a_l09(u, t, f):   # 役割を分ける：鏡を持つ仲間と、器具を渡す仲間
    night(); swing(t, .05); key_op(f, 400); SITM.location = (-1.9, .9, .45); SITM.rotation_euler = (0, 0, math.radians(180))
    MATE[0].location = (-1.0, .5, 0); MATE[0].rotation_euler = (0, 0, math.radians(-90)); MATE[1].location = (-1.25, -.4, 0); MATE[1].rotation_euler = (0, 0, math.radians(-40))
    MIRROR.location = (-1.6, .1, 1.3); MIRROR.rotation_euler = (math.radians(70), 0, math.radians(20))
    cam.look(mix((-.1, 1.4, 1.85), (-.2, 1.15, 1.8), K.ease(u)), (-1.7, .3, .8), 26)

def s_l10():
    show("hut", snow=False); unhide(MIRROR); BELLY.hide_render = False; unhide(HAND)
def a_l10(u, t, f):   # 鏡に映るおなか（寄り）
    night(); key_op(f, 450); MIRROR.location = (-1.9, .2, 1.45); MIRROR.rotation_euler = (math.radians(65), 0, 0)
    HAND.location = (-1.78, .78, .84); HAND.rotation_euler = (math.radians(-25), 0, math.radians(-15)); MIRROR.location = (-1.9, .3, 1.25)
    cam.look(mix((-1.6, 1.05, 1.15), (-1.65, .95, 1.1), K.ease(u)), (-1.87, .55, .8), 32)

def s_l11():
    show("base")
def a_l11(u, t, f):   # 吹雪の中で、ひとつだけ灯る窓
    night(-.8); snow_at(t, (8, 0, 0), 14); cam.look(mix((14, -4, 1.6), (12, -3, 1.5), K.ease(u)), (2.7, 0, 1.4), 40)

def s_l12():
    show("base", snow=False)
def a_l12(u, t, f):   # 吹雪のやんだ基地（明け方に近い光）
    sky.set(0, 1.5, 200, 2.0); sc.view_settings.exposure = -1.6; cam.look(mix((-30, -26, 3), (-26, -24, 2.6), K.ease(u)), (0, 2, 1.5), 32)


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]}
ORDER = ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, SNOW, BULB, HAND, MIRROR] + MATE + [SITM])
