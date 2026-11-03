"""pilot_042（フランシス・ケルシー）の 3D の場面（Blender、ext/blender/blkit.py）。選択設計：問いまでは審査官の目線だけ、後半は外から。
使い方：blender -b -P anatomy_room/production/pilot_042/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：1960 年ごろの役所の部屋（模式）、申請の書類の束、ダイヤル式の電話、タイプライター、時計、薬の瓶。人物は MakeHuman / MPFB（pilot_017 の机に向かう女性、後ろ姿だけ）と手。
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy
from mathutils import Vector
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); cam = K.Cam()
R = random.Random(42)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (*col, 1); return m, b


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


# ---------------------------------------------------------------- 部屋（6 × 5 m）。机は原点、審査官は +y 側に座り -y を向く。窓は -x の壁（ブラインド）
ROOM = group("room")
wall = K.mat("wall", (.42, .42, .36), .85); floor = K.mat("floor", (.16, .12, .08), .6); wood = K.mat("desk", (.22, .13, .07), .45)
K.box("floor", (6, 5, .1), (0, 0, -.05), floor, bevel=0, parent=ROOM); K.box("ceil", (6, 5, .1), (0, 0, 2.9), K.mat("ceil", (.6, .6, .56), .9), bevel=0, parent=ROOM)
K.box("wS", (6, .1, 3), (0, -2.5, 1.45), wall, bevel=0, parent=ROOM); K.box("wN", (6, .1, 3), (0, 2.5, 1.45), wall, bevel=0, parent=ROOM); K.box("wE", (.1, 5, 3), (3, 0, 1.45), wall, bevel=0, parent=ROOM)
for z0, z1 in ((-.05, .9), (2.3, 2.95)):
    K.box(f"wW{z0}", (.1, 5, z1 - z0), (-3, 0, (z0 + z1) / 2), wall, bevel=0, parent=ROOM)
for y0, y1 in ((-2.5, -1.4), (1.4, 2.5)):
    K.box(f"wWs{y0}", (.1, y1 - y0, 1.4), (-3, (y0 + y1) / 2, 1.6), wall, bevel=0, parent=ROOM)
blind = K.mat("blind", (.8, .76, .62), .6)
for k in range(28):   # ブラインドの板（外の光が筋になる）
    K.box(f"sl{k}", (.04, 2.8, .035), (-2.93, 0, .92 + k * .05), blind, (math.radians(35), 0, 0), bevel=0, parent=ROOM)
win = bpy.data.lights.new("win", "AREA"); win.energy = 900; win.size = 2.8; win.size_y = 1.4; win.shape = "RECTANGLE"; win.color = (1, .92, .8)
wo = bpy.data.objects.new("win", win); sc.collection.objects.link(wo); wo.parent = ROOM; wo.location = (-3.4, 0, 1.6); wo.rotation_euler = (0, math.radians(-90), 0)
K.box("desk", (1.6, .85, .05), (0, 0, .76), wood, parent=ROOM)
K.box("deskbody", (1.5, .8, .7), (0, -.02, .38), wood, parent=ROOM)
K.box("blotter", (.6, .42, .005), (0, .12, .79), K.mat("blot", (.12, .18, .12), .9), bevel=0, parent=ROOM)
# 申請の書類の束（厚いファイル）と、開いたページ
paper = K.mat("paper", (.86, .84, .76), .8); folder = K.mat("folder", (.55, .42, .25), .7)
FILES = group("files"); FILES.parent = ROOM; FILES.location = (-.45, .05, .79)
for k in range(9):
    K.box(f"file{k}", (.24, .32, .035), (R.uniform(-.01, .01), R.uniform(-.01, .01), .018 + k * .037), folder if k % 2 else paper, (0, 0, R.uniform(-.05, .05)), bevel=.003, parent=FILES)
OPEN = group("open"); OPEN.parent = ROOM; OPEN.location = (.02, .14, .795)
for k, x in enumerate((-.115, .115)):
    K.box(f"pg{k}", (.22, .3, .004), (x, 0, 0), paper, (0, math.radians(-4 if k else 4), 0), bevel=0, parent=OPEN)
lines = K.mat("ink", (.15, .15, .18), .8)
for k in range(16):
    for x in (-.115, .115):
        K.box(f"ln{k}{x}", (.17 * R.uniform(.6, 1), .006, .001), (x, .12 - k * .016, .003), lines, bevel=0, parent=OPEN)
# ダイヤル式の電話（受話器が鳴って震える）
PHONE = group("phone"); PHONE.parent = ROOM; PHONE.location = (.55, -.12, .79); black = K.mat("bake", (.02, .02, .022), .25)
K.box("pbase", (.2, .24, .08), (0, 0, .04), black, bevel=.03, parent=PHONE)
bpy.ops.mesh.primitive_cylinder_add(radius=.06, depth=.01, location=(0, -.03, .085), rotation=(math.radians(-20), 0, 0)); d = bpy.context.object; d.data.materials.append(K.mat("dial", (.85, .85, .8), .4)); d.parent = PHONE
RCV = group("rcv"); RCV.parent = PHONE; RCV.location = (0, .05, .11)
K.box("rbar", (.24, .045, .035), (0, 0, .0), black, bevel=.015, parent=RCV)
for x in (-.11, .11):
    K.box(f"rcup{x}", (.06, .07, .04), (x, 0, -.01), black, bevel=.02, parent=RCV)
# タイプライター・時計・ランプ・はんこ
TW = group("tw"); TW.parent = ROOM; TW.location = (.95, .55, .0)
K.box("twtable", (.6, .45, .05), (0, 0, .66), wood, parent=TW); K.box("tw", (.42, .32, .14), (0, 0, .76), K.mat("twm", (.12, .14, .13), .35, .4), bevel=.03, parent=TW)
K.box("twpaper", (.22, .004, .22), (0, .1, .92), paper, (math.radians(-15), 0, 0), bevel=0, parent=TW)
CLOCK = group("clock"); CLOCK.parent = ROOM; CLOCK.location = (0, -2.44, 2.1)
bpy.ops.mesh.primitive_cylinder_add(radius=.22, depth=.04, rotation=(math.radians(90), 0, 0)); c = bpy.context.object; c.data.materials.append(K.mat("cface", (.88, .86, .8), .5)); c.parent = CLOCK
HANDS = []
for k, (ln, w) in enumerate(((.15, .012), (.19, .008), (.2, .003))):
    h = group(f"hand{k}"); h.parent = CLOCK; h.location = (0, .03, 0); K.box(f"hb{k}", (w, .004, ln), (0, 0, ln / 2 - .02), K.mat(f"hm{k}", (.8, .1, .1) if k == 2 else (.05, .05, .05), .5), bevel=0, parent=h); HANDS.append(h)
lm, LAMP = emit("lampbulb", (1, .82, .55), 12)
K.tube((-.62, -.25, .79), (-.62, -.25, 1.15), .012, K.mat("brass", (.7, .55, .25), .3, 1), ROOM, 12)
bpy.ops.mesh.primitive_cone_add(radius1=.14, radius2=.05, depth=.14, location=(-.55, -.2, 1.2)); sh = bpy.context.object; sh.data.materials.append(K.mat("shade", (.08, .2, .12), .4, .2)); sh.parent = ROOM
bpy.ops.mesh.primitive_uv_sphere_add(radius=.035, location=(-.55, -.2, 1.15)); bb = bpy.context.object; bb.data.materials.append(lm); bb.parent = ROOM
dl = bpy.data.lights.new("desklamp", "SPOT"); dl.energy = 40; dl.spot_size = math.radians(80); dl.color = (1, .82, .55)
dlo = bpy.data.objects.new("desklamp", dl); sc.collection.objects.link(dlo); dlo.parent = ROOM; dlo.location = (-.55, -.2, 1.14)
STAMP = group("stamp"); STAMP.parent = ROOM; STAMP.location = (.35, .25, .79)
K.box("stb", (.07, .05, .02), (0, 0, .01), K.mat("rubber", (.5, .08, .06), .7), bevel=.005, parent=STAMP); K.tube((0, 0, .02), (0, 0, .1), .015, wood, STAMP, 12)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.025, location=(0, 0, .11)); k_ = bpy.context.object; k_.data.materials.append(wood); k_.parent = STAMP
# 手（自分の右手・ペン）
SKIN = K.mat("skin", (.66, .5, .42), .55); HAND = group("hand"); HAND.parent = ROOM
K.tube((0, .2, .03), (0, .06, .01), .034, K.mat("sleeve", (.22, .24, .3), .8), HAND, 16); K.tube((0, .07, .01), (0, -.03, 0), .024, SKIN, HAND, 16)
K.box("palm", (.07, .08, .026), (0, -.07, -.006), SKIN, (math.radians(-8), 0, 0), bevel=.012, parent=HAND)
for x in (-.025, -.008, .009, .025):
    K.tube((x, -.105, -.01), (x * .7, -.15, -.035), .008, SKIN, HAND, 10)
K.tube((.033, -.05, -.008), (.012, -.13, -.03), .009, SKIN, HAND, 10)
PEN = K.tube((.0, -.1, .0), (.01, -.22, -.05), .004, K.mat("pen", (.05, .05, .06), .2, .5), HAND, 8)
# 薬の瓶の棚（後半）
SHELF = group("shelf"); glass = bpy.data.materials.new("amber"); glass.use_nodes = True; gb = glass.node_tree.nodes["Principled BSDF"]
gb.inputs["Base Color"].default_value = (.55, .28, .08, 1); gb.inputs["Roughness"].default_value = .08; gb.inputs["Transmission Weight"].default_value = .9
for z in range(5):
    K.box(f"shb{z}", (4, .35, .03), (0, 0, .3 + z * .42), wood, bevel=0, parent=SHELF)
    for k in range(34):
        bpy.ops.mesh.primitive_cylinder_add(radius=.045, depth=.16, vertices=16, location=(-1.9 + k * .115, R.uniform(-.06, .06), .4 + z * .42)); b_ = bpy.context.object; b_.data.materials.append(glass); b_.parent = SHELF
        bpy.ops.mesh.primitive_cylinder_add(radius=.047, depth=.03, vertices=16, location=(b_.location.x, b_.location.y, .495 + z * .42)); c_ = bpy.context.object; c_.data.materials.append(K.mat(f"cap{z}{k}", (.85, .85, .82), .5)); c_.parent = SHELF
K.box("shwall", (12, .1, 10), (0, .3, 4.5), K.mat("shw", (.12, .11, .1), .9), bevel=0, parent=SHELF); K.box("shfl", (8, 12, .1), (0, -5, -.05), K.mat("shf", (.08, .07, .06), .8), bevel=0, parent=SHELF)
SHELF.location = (0, -30, 0)
# 審査官（机に向かう女性、後ろ姿）
K.HUMAN_DIR = os.path.join(HERE, "..", "..", "pilot_017", "assets", "human")
K.box("chair", (.45, .45, .05), (0, .8, .45), wood, parent=ROOM); K.box("chairb", (.45, .05, .5), (0, 1.02, .72), wood, parent=ROOM)
WOMAN = K.human("leavitt_desk", suit=(.18, .2, .26), helmet=False, pack=False); WOMAN.parent = ROOM
ALL = {"room": ROOM, "shelf": SHELF}


def show(*names, woman=False, hand=False):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    hide(WOMAN, not woman); hide(HAND, not hand)
    sky.set(0, 25, 250, 3.0); sc.view_settings.exposure = -1.0; sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0; STAMP.location = (.35, .25, .79); RCV.location = (0, .05, .11); RCV.rotation_euler = (0, 0, 0)


def ring(t, on=True):   # 電話のベル：受話器が細かく震える
    k = .004 if on and int(t * 2.5) % 2 == 0 else 0
    RCV.location = (math.sin(t * 90) * k, .05, .11 + abs(math.sin(t * 70)) * k); RCV.rotation_euler = (0, math.sin(t * 80) * k * 6, 0)


def tick(t, start=10 * 3600 + 58 * 60):   # 時計の針（秒針は 1 秒ごとに進む）
    s = start + int(t); a = [(s / 43200) * 2 * math.pi, (s % 3600 / 3600) * 2 * math.pi, (s % 60 / 60) * 2 * math.pi]
    for h, v in zip(HANDS, a):
        h.rotation_euler = (0, v, 0)


def eye(t, k=.003):   # 座った目の高さ
    return Vector((math.sin(t * 2.1) * k, .62, 1.22 + math.sin(t * 1.7) * k))


# ---------------------------------------------------------------- ショット（問いまでは審査官の目線）
def s_l00():
    show("room")
def a_l00(u, t, f):   # 机の上の厚い申請と、鳴る電話
    ring(t); tick(t); p = eye(t, .006); cam.look(p, mix((.28, -.05, .82), (.36, -.1, .84), K.ease(u)), 18)

def s_l00a():
    show("room", hand=True)
def a_l00a(u, t, f):   # A：追加のデータを求める手紙を書く
    ring(t, False); tick(t); HAND.location = (.1 + .02 * math.sin(t * 6), .3 - .03 * u, .83); HAND.rotation_euler = (math.radians(-10), 0, math.radians(15))
    p = eye(t); cam.look(p, (.06, .12, .79), 24)

def s_l00b():
    show("room", hand=True)
def a_l00b(u, t, f):   # B：承認のはんこを押す
    ring(t, False); tick(t); z = .79 + .1 * abs(math.cos(min(1, u * 1.4) * math.pi)) if u < .7 else .79
    STAMP.location = (.05, .14, z); HAND.location = (.06, .27, z + .12); HAND.rotation_euler = (math.radians(-35), 0, math.radians(10))
    p = eye(t); cam.look(p, (.04, .14, .82), 24)

def s_l01():
    show("room")
def a_l01(u, t, f):   # 1960 年の役所の部屋。ブラインドの光
    tick(t); p = eye(t); cam.look(p, mix((-2.6, -1.2, 1.4), (-2.2, -1.6, 1.3), K.ease(u)), 22)

def s_l02():
    show("room")
def a_l02(u, t, f):   # 申請の束が届く
    tick(t); FILES.location = (-.45, .05, .79 + .25 * (1 - K.ease(min(1, u * 2)))); p = eye(t); cam.look(p, (-.4, .02, .86), 30)

def s_l03():
    show("room")
def a_l03(u, t, f):   # 電話が何度も鳴る（寄り）
    ring(t); tick(t); p = eye(t); cam.look(p, (.55, -.12, .85), 40 + 12 * u)

def s_l04():
    show("room")
def a_l04(u, t, f):   # 壁の時計：期限が迫る
    tick(t * 30); p = eye(t); cam.look(p, (0, -2.44, 2.1), 40 + 20 * K.ease(u))

def s_l05():
    show("room")
def a_l05(u, t, f):   # 開いたページ：データが足りない
    tick(t); p = eye(t); cam.look(mix(p, (p.x, p.y - .2, p.z - .15), K.ease(u)), (.02, .12, .8), 32)

def s_l06():
    show("room")
def a_l06(u, t, f):   # 問い：机の全体。電話・書類・はんこ
    ring(t); tick(t); p = eye(t); cam.look(p, (.05, -.05, .8), 22 + 6 * u)

# 後半（外から）
def s_l07():
    show("room", woman=True)
def a_l07(u, t, f):   # 机に向かう審査官（後ろ姿）
    tick(t); WOMAN.location = (0, .62, 0); WOMAN.rotation_euler = (0, 0, 0)
    cam.look(mix((.9, 2.2, 1.6), (.6, 2.0, 1.5), K.ease(u)), (0, .2, .95), 28)

def s_l08():
    show("room", woman=True)
def a_l08(u, t, f):   # 鳴り続ける電話と、動かない背中
    ring(t); tick(t); WOMAN.location = (0, .62, 0); cam.look(mix((1.9, 1.6, 1.3), (1.7, 1.4, 1.25), K.ease(u)), (.3, -.05, .9), 32)

def s_l09():
    show("shelf")
def a_l09(u, t, f):   # 薬の瓶が並ぶ棚（ドイツなどで売られていた薬。暗い）
    sky.set(0, 25, 250, 0); sc.view_settings.exposure = -1.3; SHELF.location = (0, 0, 0)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = .02
    cam.look(mix((-2.4, -2.6, 1.1), (1.8, -2.4, 1.2), K.ease(u)), mix((-1.4, 0, 1.0), (1.4, 0, 1.1), K.ease(u)), 35)

def s_l10():
    show("room")
def a_l10(u, t, f):   # 閉じた申請の束と、ランプ
    tick(t); p = Vector((-.9, -.9, 1.0)); cam.look(mix(p, (-.85, -.8, .98), K.ease(u)), (-.45, .05, .9), 40)

def s_l11():
    show("shelf")
def a_l11(u, t, f):   # 治験用に配られた錠剤：棚の遠景
    sky.set(0, 25, 250, 0); sc.view_settings.exposure = -1.4; SHELF.location = (0, 0, 0)
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = .02
    cam.look(mix((0, -5.5, 1.2), (0, -6.5, 1.3), K.ease(u)), (0, 0, 1.1), 30)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l00", "l00a", "l00b"]}
SHOTS.update({k: (globals()["s_" + v], globals()["a_" + v]) for k, v in {"l00_2": "l03", "l00_3": "l04", "l05_2": "l03"}.items()})   # カット（2026-11-03〜）
ORDER = None   # renderer の SHOTS とカットから時刻の順に（blkit.renderer_order）
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, RCV, FILES, STAMP, HAND, WOMAN, SHELF] + HANDS)
