"""pilot_038（アポロ 12 号の落雷）の 3D の場面（Blender、ext/blender/blkit.py）。当事者設計：前半は管制官の目線、後半は後ろ姿・遠景。
使い方：blender -b -P anatomy_room/production/pilot_038/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：管制室（1960 年代の卓と画面を模した形）、司令船の計器盤（警告灯・スイッチ・計器）、サターン V を模したロケット・雨雲・雷。画面の数字は模式（実際の表示ではない）。
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
R = random.Random(38)
TEX = os.path.join(HERE, "tex")


# 画面の画像は make_tex.py（普通の Python。Blender の Python には PIL がない）で先に作る
if not os.path.exists(os.path.join(TEX, "screen_bad.png")):
    import subprocess; subprocess.run(["python", os.path.join(HERE, "make_tex.py")], check=True)


def emit_img(name, path, strength=2.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tx = n.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path); L.new(tx.outputs[0], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = strength
    b.inputs["Base Color"].default_value = (0, 0, 0, 1); b.inputs["Roughness"].default_value = .15; return m, tx


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (*[c * .3 for c in col], 1); return m, b


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


# ---------------------------------------------------------------- 管制室（原点。卓の列は -y 方向へ段々に下がる、正面の壁に大きな画面）
ROOM = group("room")
grayg = K.mat("consoleg", (.32, .36, .34), .55); dark = K.mat("dark", (.05, .05, .06), .7); wall = K.mat("wall", (.18, .17, .16), .9)
K.box("floor", (40, 40, .1), (0, -8, -.05), K.mat("carpet", (.12, .11, .1), .95), parent=ROOM)
K.box("backwall", (40, .2, 9), (0, -24, 4.4), wall, parent=ROOM)
if not os.path.exists(os.path.join(TEX, "wall.png")):
    import subprocess; subprocess.run(["python", os.path.join(HERE, "make_tex.py")], check=True)
wall_m, _ = emit_img("wallscr", os.path.join(TEX, "wall.png"), 1.6)
for k, x in enumerate((-9, 0, 9)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, -23.7, 5), rotation=(-math.pi / 2, 0, 0)); o = bpy.context.object; o.scale = (8, 4.5, 1); o.data.materials.append(wall_m); o.parent = ROOM
ok_m, OK_TX = emit_img("scr_ok", os.path.join(TEX, "screen_ok.png")); bad_m, _ = emit_img("scr_bad", os.path.join(TEX, "screen_bad.png"))
SCR = []
for row in range(4):
    y, z = -row * 3.2, -row * .45
    for i in range(7):
        x = -9 + i * 3.0
        K.box(f"desk{row}{i}", (2.8, .9, .8), (x, y, z + .4), grayg, parent=ROOM); K.box(f"top{row}{i}", (2.8, 1.0, .06), (x, y - .05, z + .82), K.mat("deskt", (.22, .24, .23), .4), parent=ROOM)
        K.box(f"hood{row}{i}", (2.6, .7, .7), (x, y - .2, z + 1.2), grayg, (.25, 0, 0), parent=ROOM)
        for sx in (-.65, .65):
            bpy.ops.mesh.primitive_plane_add(size=1, location=(x + sx, y + .16, z + 1.22), rotation=(math.radians(-(90 - 14)), 0, 0)); s = bpy.context.object
            s.scale = (.55, .42, 1); s.data.materials.append(ok_m); s.parent = ROOM; SCR.append(s)
# 自分の卓（row 0 の中央）の 2 つの画面：普段 → 崩れた表示（混ぜる割合を毎コマ keyframe にする）
MY = [s for s in SCR if abs(s.location.y - .16) < .01 and abs(s.location.x) < 1]
my_m = bpy.data.materials.new("scr_my"); my_m.use_nodes = True; mn = my_m.node_tree.nodes; ml = my_m.node_tree.links; mb = mn["Principled BSDF"]
t1 = mn.new("ShaderNodeTexImage"); t1.image = bpy.data.images.load(os.path.join(TEX, "screen_ok.png")); t2 = mn.new("ShaderNodeTexImage"); t2.image = bpy.data.images.load(os.path.join(TEX, "screen_bad.png"))
GMIX = mn.new("ShaderNodeMix"); GMIX.data_type = "RGBA"; ml.new(t1.outputs[0], GMIX.inputs[6]); ml.new(t2.outputs[0], GMIX.inputs[7]); ml.new(GMIX.outputs[2], mb.inputs["Emission Color"])
mb.inputs["Emission Strength"].default_value = 2.5; mb.inputs["Base Color"].default_value = (0, 0, 0, 1); mb.inputs["Roughness"].default_value = .15
for s_ in MY:
    s_.data = s_.data.copy(); s_.data.materials[0] = my_m
lamp = bpy.data.lights.new("roomlamp", "AREA"); lamp.energy = 7000; lamp.size = 20; lamp.color = (1, .95, .85)
lo = bpy.data.objects.new("roomlamp", lamp); sc.collection.objects.link(lo); lo.location = (0, -8, 7.5); lo.parent = ROOM
MEN = []
for (x, y, z) in [(-6, -.6, 0), (6, -.6, 0), (-3, -3.8, -.45), (3, -3.8, -.45), (0, -7, -.9), (-9, -7, -.9)]:
    h = K.human("man_sit", suit=(.88, .88, .86), helmet=False, pack=False); h.location = (x, y + .75, z); h.parent = ROOM; MEN.append(h)
AARON = K.human("man_sit", suit=(.9, .9, .88), helmet=False, pack=False); AARON.location = (0, .75, 0)

# ---------------------------------------------------------------- 計器盤（司令船の中、x=100）
PANEL = group("panel"); PX = 100
K.box("pbase", (3.2, .2, 1.8), (PX, 0, 1.4), K.mat("pgray", (.2, .21, .22), .5, .3), (-.3, 0, 0), parent=PANEL)
LAMPS = []
for i in range(6):
    for j in range(5):
        m, b = emit(f"lamp{i}{j}", (1, .25, .1) if (i + j) % 3 else (1, .7, .15), 0.0)
        K.box(f"lp{i}{j}", (.14, .05, .09), (PX - .9 + i * .16, -.12 + (j * .03), 1.9 - j * .12), m, (-.3, 0, 0), bevel=0, parent=PANEL); LAMPS.append(b)
R.shuffle(LAMPS)
SW = []
for i in range(10):
    x = PX + .2 + (i % 5) * .18; z = 1.2 + (i // 5) * .2
    K.tube((x, -.18, z), (x, -.3, z + .02), .012, K.mat("swm", (.75, .75, .76), .25, 1), PANEL, 10)
bpy.ops.mesh.primitive_cylinder_add(radius=.018, depth=.16, location=(PX + .4, -.34, 1.0)); SCE = bpy.context.object; SCE.data.materials.append(K.mat("scesw", (.85, .85, .86), .2, 1)); SCE.parent = PANEL
SCE.rotation_euler = (math.radians(60), 0, 0)
NEEDLES = []
for i in range(3):
    bpy.ops.mesh.primitive_cylinder_add(radius=.11, depth=.03, location=(PX - .2 + i * .3, -.2, 1.55), rotation=(math.radians(60), 0, 0)); g = bpy.context.object; g.data.materials.append(K.mat("gface", (.9, .9, .85), .5)); g.parent = PANEL
    bpy.ops.mesh.primitive_cube_add(size=1, location=(PX - .2 + i * .3, -.22, 1.55)); nd = bpy.context.object; nd.scale = (.005, .005, .09); nd.data.materials.append(K.mat("needle", (.8, .1, .05), .5)); nd.parent = PANEL; NEEDLES.append(nd)
pl = bpy.data.lights.new("panlight", "AREA"); pl.energy = 60; pl.size = 2; pl.color = (.9, .95, 1)
po = bpy.data.objects.new("panlight", pl); sc.collection.objects.link(po); po.location = (PX, -2, 2.6); po.rotation_euler = (math.radians(40), 0, 0); po.parent = PANEL

# ---------------------------------------------------------------- ロケット（x=-500、雨雲の中を上がる）
ROCK = group("rocket"); RX = -500
white = K.mat("rwhite", (.88, .88, .86), .4); black = K.mat("rblack", (.05, .05, .05), .5)
CMG = bpy.data.objects.new("cmg", None); sc.collection.objects.link(CMG); CMG.parent = ROCK   # 司令船と脱出塔（オープニングの B：打ち上げを中止 → 脱出）
for (z0, h, r, m) in [(0, 42, 5.05, white), (42, 25, 5.05, white), (67, 18, 3.3, white), (85, 4, 3.3, black), (89, 4, 2.0, white), (93, 6, .9, white)]:
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=48, location=(RX, 0, z0 + h / 2)); o = bpy.context.object; o.data.materials.append(m); o.parent = CMG if z0 >= 89 else ROCK; bpy.ops.object.shade_smooth()
esc_m, ESC = emit("escflame", (1, .6, .3), 0)
for a in range(4):
    bpy.ops.mesh.primitive_cone_add(radius1=.6, radius2=2.2, depth=9, location=(RX + 1.6 * math.cos(a * 1.57), 1.6 * math.sin(a * 1.57), 92), vertices=24); fo = bpy.context.object; fo.data.materials.append(esc_m); fo.parent = CMG
for k in range(4):
    a = k * math.pi / 2 + math.pi / 4; K.box(f"fin{k}", (.3, 3, 6), (RX + 5.5 * math.cos(a), 5.5 * math.sin(a), 4), white, (0, 0, a + math.pi / 2), parent=ROCK)
fl_m, FLB = emit("flame", (1, .7, .35), 30)
bpy.ops.mesh.primitive_cone_add(radius1=4.5, radius2=7, depth=26, location=(RX, 0, -13), vertices=48); fl = bpy.context.object; fl.data.materials.append(fl_m); fl.parent = ROCK
cloud = bpy.data.materials.new("raincloud"); cloud.use_nodes = True; cn = cloud.node_tree.nodes
for x in list(cn): cn.remove(x)
co = cn.new("ShaderNodeOutputMaterial"); cv = cn.new("ShaderNodeVolumePrincipled"); cv.inputs["Color"].default_value = (.5, .52, .56, 1); cv.inputs["Density"].default_value = .004
cloud.node_tree.links.new(cv.outputs[0], co.inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(RX, 0, 600)); cb = bpy.context.object; cb.scale = (3000, 3000, 900); cb.data.materials.append(cloud)
bpy.ops.mesh.primitive_plane_add(size=20000, location=(RX, 0, -1200)); grd = bpy.context.object; grd.data.materials.append(K.mat("land", (.12, .16, .1), .9))
BOLTS = []
for k in range(2):
    m, b = emit(f"bolt{k}", (.75, .82, 1), 0); pts = [Vector((RX + 6, 0, 120 - k * 30))]
    for j in range(18):
        pts.append(pts[-1] + Vector((R.uniform(-9, 9) + (3 if k else -3), R.uniform(-6, 6), -40)))
    bg_ = group(f"boltg{k}"); segs = [K.tube(a, b_, .9, m, bg_, 6) for a, b_ in zip(pts, pts[1:])]; BOLTS.append((b, segs, bg_))
ROCKY = [ROCK]
ALL = {"room": ROOM, "panel": PANEL, "rocket": ROCK}


def show(*names, aaron=False):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()
    for b in LAMPS:
        b.inputs["Emission Strength"].default_value = 0
    for b, segs, bg_ in BOLTS:
        b.inputs["Emission Strength"].default_value = 0
        for s in segs:
            s.hide_render = "rocket" not in names
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    CMG.location = (0, 0, 0); ESC.inputs["Emission Strength"].default_value = 0

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    cb.hide_render = grd.hide_render = "rocket" not in names
    hide(AARON, not aaron)
    GMIX.inputs[0].default_value = 0


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def indoor(exp=-.6):
    sky.set(0, -10, 150, 0); sc.view_settings.exposure = exp; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .02


def garble(on, f):
    GMIX.inputs[0].default_value = 1.0 if on else 0.0; GMIX.inputs[0].keyframe_insert("default_value", frame=f + 1)


ROCKET_Z = [0.0]


def rocket_at(t, z0=200, v=60):
    ROCK.location.z = z0 + v * t + 3 * t * t


# ---------------------------------------------------------------- ショット
def s_l00():
    show("rocket"); sky.set(0, 20, 120, 2.5); sc.view_settings.exposure = -.6; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .5
def a_l00(u, t, f):   # 雨雲を突き抜けるロケットに雷（オープニングの背景）
    rocket_at(t, 150); z = ROCK.location.z
    cam.look((RX - 70, -95, z + 20), (RX, 0, z + 45), 40)
    for k, (b, segs, bg_) in enumerate(BOLTS):
        b.inputs["Emission Strength"].default_value = 25 if (k == 0 and t > 1.0) else 0; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
        bg_.location.z = z - 60 + 30 * k

def s_l01():
    show("room"); indoor()
def a_l01(u, t, f):   # 自分の卓の前に座る（管制官の目線）
    p = Vector((0, 1.35, 1.5)) + Vector((math.sin(t * 1.3) * .01, 0, math.sin(t * 2.1) * .008)); e = K.ease(u)
    cam.look(p, mix((.3, -12, 1.6), (.5, .16, 1.15), e), mix((28,), (34,), e)[0])

def s_l03():
    show("room"); indoor()
def a_l03(u, t, f):   # 画面の数字が崩れる
    p = Vector((.55, .85, 1.35)); cam.look(p, (.65, .16, 1.22), 30)
    garble(u > .25, f)

def s_l04():
    show("panel"); indoor(-.2)
def a_l04(u, t, f):   # 警告灯が次々に点く（揺れ）
    k = .01 + .02 * u; cam.look((PX + math.sin(t * 19) * k, -1.6, 1.7 + math.sin(t * 23) * k), (PX - .3, 0, 1.5), 32)
    for i, b in enumerate(LAMPS):
        b.inputs["Emission Strength"].default_value = 12 if u > i / len(LAMPS) * .9 else 0; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)

def s_l05():
    show("panel"); indoor(-.2)
def a_l05(u, t, f):   # 計器の針が下がる、2 回目
    k = .015 + .03 * (1 if u > .45 else 0); cam.look((PX + .2 + math.sin(t * 21) * k, -1.3, 1.6 + math.sin(t * 25) * k), (PX - .2, 0, 1.5), 30)
    for b in LAMPS:
        b.inputs["Emission Strength"].default_value = 12; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
    for i, nd in enumerate(NEEDLES):
        nd.rotation_euler = (math.radians(60), math.radians(-60 + 120 * (1 - u) - i * 15), 0); nd.keyframe_insert("rotation_euler", frame=f + 1)

def s_l06():
    show("rocket"); sky.set(0, 20, 120, 2.5); sc.view_settings.exposure = -.6; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .5
def a_l06(u, t, f):   # ロケットは上がり続ける
    rocket_at(t, 600, 90); z = ROCK.location.z; cam.look((RX + 60, -120, z - 40), (RX, 0, z + 40), 34)

def s_l07():
    show("room"); indoor()
def a_l07(u, t, f):   # 問い：崩れた画面の前で
    garble(True, f)
    p = Vector((.4, 1.15, 1.42)) + Vector((0, 0, math.sin(t * 2.4) * .006)); cam.look(p, (.45, .16, 1.22), 30 + 8 * u)

def s_l09():
    show("room", aaron=True); indoor(-.4)
def a_l09(u, t, f):   # アーロンの後ろ姿（見覚えがある）
    garble(True, f)
    e = K.ease(u); cam.look(mix((1.6, 3.6, 2.2), (1.0, 2.8, 1.9), e), (0, -.2, 1.25), 34)

def s_l10():
    show("panel"); indoor(-.2)
def a_l10(u, t, f):   # SCE のスイッチを AUX へ → 灯が消える
    cam.look((PX + .55, -.85, 1.2), (PX + .4, -.34, 1.0), 40)
    SCE.rotation_euler = (math.radians(60 - 60 * min(1, max(0, (u - .45) / .1))), 0, 0); SCE.keyframe_insert("rotation_euler", frame=f + 1)
    for i, b in enumerate(LAMPS):
        b.inputs["Emission Strength"].default_value = 0 if u > .6 + .3 * i / len(LAMPS) else 12; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)

def s_l12():
    show("rocket"); sky.set(0, 20, 120, 2.5); sc.view_settings.exposure = -.6; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .5
def a_l12(u, t, f):   # ロケットと炎の柱が雷の通り道になる（模式）
    rocket_at(t, 150, 50); z = ROCK.location.z; cam.look((RX - 200, -260, z - 30), (RX, 0, z - 20), 34)
    for k, (b, segs, bg_) in enumerate(BOLTS):
        b.inputs["Emission Strength"].default_value = 20 if k == 0 else 0; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
        bg_.location.z = z - 40

def s_l13():
    show("room", aaron=True); indoor(-.5)
def a_l13(u, t, f):   # 落ち着いた管制室（遠景）
    e = K.ease(u); cam.look(mix((7, 6, 4.5), (5, 4.5, 3.8), e), (0, -6, 1.2), 30)


def s_l00a():
    show("panel"); indoor(-.2)
def a_l00a(u, t, f):   # A：燃料電池をつなぎ直す（スイッチの列と、点滅する警告灯）
    k = .012; cam.look((PX + .55 + math.sin(t * 17) * k, -.95, 1.55 + math.sin(t * 21) * k), (PX + .55, -.25, 1.3), 34)
    for i, b in enumerate(LAMPS):
        b.inputs["Emission Strength"].default_value = 12 if (int(t * 6) + i) % 3 else 2; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)

def s_l00b():
    show("panel"); indoor(-.2)
def a_l00b(u, t, f):   # B：謎のスイッチ SCE を AUX へ（寄り）
    cam.look((PX + .5, -.75, 1.15), (PX + .4, -.34, 1.0), 44)
    SCE.rotation_euler = (math.radians(60 - 60 * min(1, max(0, (u - .55) / .1))), 0, 0); SCE.keyframe_insert("rotation_euler", frame=f + 1)
    for b in LAMPS:
        b.inputs["Emission Strength"].default_value = 12; b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)

SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l00a", "l00b", "l01", "l03", "l04", "l05", "l06", "l07", "l09", "l10", "l12", "l13"]}
ORDER = ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12", "l13"]
anim = [cam.o, ROCK, CMG] + NEEDLES + [SCE] + [bg_ for b, segs, bg_ in BOLTS]
K.render_shots(HERE, SHOTS, ORDER, O, anim)
