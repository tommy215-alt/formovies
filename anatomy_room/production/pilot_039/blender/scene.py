"""pilot_039（プロスペリ）の 3D の場面（Blender、ext/blender/blkit.py）。当事者設計：前半は当事者の目線、後半は後ろ姿・遠景。
使い方：blender -b -P anatomy_room/production/pilot_039/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：砂丘（手続き的）、聖者の墓（白い小さな廟を模した形）、木、夜空、ヘリコプター、コウモリ、夕方の雲、ヤギと少女（遠景）、人物（MakeHuman / MPFB、後ろ姿）。砂嵐の砂はブラウザ側（pov.js）。
"""
import sys, os, math, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy, bmesh
from mathutils import Vector, Euler
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); cam = K.Cam()
R = random.Random(39)
HUM = os.path.join(HERE, "..", "..", "pilot_018", "assets", "human")


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (*col, 1); return m, b


# ---------------------------------------------------------------- 砂丘（2 km 四方、波の模様＋ノイズで稜線）
sand = bpy.data.materials.new("sand"); sand.use_nodes = True; n = sand.node_tree.nodes; L = sand.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = .4; L.new(tc.outputs["Object"], no.inputs["Vector"])
rip = n.new("ShaderNodeTexWave"); rip.inputs["Scale"].default_value = 3.0; rip.inputs["Distortion"].default_value = 6; L.new(tc.outputs["Object"], rip.inputs["Vector"])
mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(no.outputs["Fac"], mx.inputs[0]); mx.inputs[6].default_value = (.62, .38, .18, 1); mx.inputs[7].default_value = (.78, .52, .27, 1)
L.new(mx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .95
bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .25; bp.inputs["Distance"].default_value = .02; L.new(rip.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
def H(x, y):
    """砂丘の高さ（廟のまわりと、ヤギのいる平地は低く平らに）"""
    h = 14 * max(0, math.sin(x * .011 + 1.3 * math.sin(y * .004))) ** 1.6 + 6 * math.sin(y * .017 + x * .006) + 3 * math.sin(x * .05 + y * .03)
    d = min(math.hypot(x, y + 40), math.hypot(x - 28, y + 110))
    return h * (min(1, d / 45) * .92 + .08)


bpy.ops.mesh.primitive_grid_add(x_subdivisions=400, y_subdivisions=400, size=2000, location=(0, 0, 0)); dune = bpy.context.object; dune.data.materials.append(sand)
for v in dune.data.vertices:
    v.co.z = H(v.co.x, v.co.y)
bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, -22)); far = bpy.context.object; far.data.materials.append(sand)   # 地平線まで続く砂
for p in dune.data.polygons:
    p.use_smooth = True

# ---------------------------------------------------------------- 廟（原点から -y へ 40 m）・木
SHR = group("shrine"); SX, SY = 0, -40; SHR.location.z = H(SX, SY) - .05
wash = K.mat("whitewash", (.86, .82, .74), .9)
K.box("shr_body", (4, 4, 3.2), (SX, SY, 1.6), wash, bevel=.15, parent=SHR)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.9, location=(SX, SY, 3.2)); dm = bpy.context.object; dm.scale = (1, 1, .8); dm.data.materials.append(wash); dm.parent = SHR; bpy.ops.object.shade_smooth()
door = K.box("shr_door", (1.0, .8, 2.0), (SX, SY - 2.0, 1.0), K.mat("doorhole", (.02, .015, .01), 1), bevel=0, parent=SHR); door.hide_render = True
body = [o for o in SHR.children if o.name.startswith("shr_body")][0]; sol = body.modifiers.new("hollow", "SOLIDIFY"); sol.thickness = .25; sol.offset = 1
bo = body.modifiers.new("door", "BOOLEAN"); bo.operation = "DIFFERENCE"; bo.object = door
K.box("shr_floor", (3.8, 3.8, .05), (SX, SY, .03), K.mat("shrfloor", (.4, .3, .2), .95), parent=SHR)
BATS = []
batm = K.mat("bat", (.05, .04, .035), .8)
for k in range(46):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.05, location=(SX + R.uniform(-1.4, 1.4), SY + 1.92, R.uniform(2.0, 2.9)), segments=10, ring_count=6); o = bpy.context.object
    o.scale = (1, .6, 1.5); o.data.materials.append(batm); o.parent = SHR; BATS.append(o)
il = bpy.data.lights.new("shrlight", "AREA"); il.energy = 40; il.size = 1; il.color = (1, .8, .55)
ilo = bpy.data.objects.new("shrlight", il); sc.collection.objects.link(ilo); ilo.location = (SX, SY - 1.6, 1.0); ilo.rotation_euler = (math.radians(80), 0, 0); ilo.parent = SHR
bark = K.mat("acacia", (.2, .14, .08), .9); leaf = K.mat("aleaf", (.18, .22, .08), .8)
TREE = group("tree")
TREE.location.z = H(8, -32) - .1
K.tube((8, -32, 0), (8.5, -32, 3.2), .18, bark, TREE)
for k in range(5):
    a = k * 1.26; K.tube((8.5, -32, 3.0), (8.5 + 2.2 * math.cos(a), -32 + 2.2 * math.sin(a), 4.4), .07, bark, TREE)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(8.5, -32, 4.6)); cr = bpy.context.object; cr.scale = (3.4, 3.4, .55); cr.data.materials.append(leaf); cr.parent = TREE

# ---------------------------------------------------------------- 夜空の星（大きな球の内側に点）
star = bpy.data.materials.new("stars"); star.use_nodes = True; sn = star.node_tree.nodes; sl = star.node_tree.links
for x in list(sn): sn.remove(x)
so = sn.new("ShaderNodeOutputMaterial"); se = sn.new("ShaderNodeEmission"); vo = sn.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 900
stc = sn.new("ShaderNodeTexCoord"); sl.new(stc.outputs["Generated"], vo.inputs["Vector"])
mr = sn.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = .06; mr.inputs[3].default_value = 1; mr.inputs[4].default_value = 0
sl.new(vo.outputs["Distance"], mr.inputs[0]); pw = sn.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 4; sl.new(mr.outputs[0], pw.inputs[0])
ml = sn.new("ShaderNodeMath"); ml.operation = "MULTIPLY"; ml.inputs[1].default_value = 30; sl.new(pw.outputs[0], ml.inputs[0]); sl.new(ml.outputs[0], se.inputs["Strength"]); sl.new(se.outputs[0], so.inputs["Surface"])
bpy.ops.mesh.primitive_uv_sphere_add(radius=3000, location=(0, 0, 0)); STARS = bpy.context.object; STARS.data.materials.append(star); STARS.visible_shadow = False

# ---------------------------------------------------------------- ヘリコプター・発炎筒・夕方の雲
HELI = group("heli"); hm = K.mat("heli", (.12, .13, .12), .5)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1.4, location=(0, 0, 0)); hb = bpy.context.object; hb.scale = (1, 2, .9); hb.data.materials.append(hm); hb.parent = HELI
K.tube((0, 1.8, .3), (0, 7, .9), .25, hm, HELI); K.box("rotor", (.25, 11, .04), (0, 0, 1.4), hm, bevel=0, parent=HELI); ROT = [o for o in HELI.children if o.name.startswith("rotor")][0]
fm, FLARE = emit("flare", (1, .15, .05), 0)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.6, location=(0, 0, -100)); FL = bpy.context.object; FL.data.materials.append(fm)
cloudm = bpy.data.materials.new("eveclouds"); cloudm.use_nodes = True; cn = cloudm.node_tree.nodes; cl = cloudm.node_tree.links; cb = cn["Principled BSDF"]
cno = cn.new("ShaderNodeTexNoise"); cno.inputs["Scale"].default_value = 2.5; cno.inputs["Detail"].default_value = 10
cmr = cn.new("ShaderNodeMapRange"); cmr.inputs[1].default_value = .48; cmr.inputs[2].default_value = .68; cl.new(cno.outputs["Fac"], cmr.inputs[0]); cl.new(cmr.outputs[0], cb.inputs["Alpha"])
cb.inputs["Base Color"].default_value = (.95, .7, .55, 1)
CLOUDS = group("clouds")
for k in range(9):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(R.uniform(-900, 900), -1700 + R.uniform(-150, 150), R.uniform(160, 380)), rotation=(math.radians(R.uniform(70, 88)), 0, 0)); c = bpy.context.object
    c.scale = (R.uniform(500, 1100), R.uniform(120, 260), 1); c.data.materials.append(cloudm); c.parent = CLOUDS

# ---------------------------------------------------------------- 人・ヤギ・少女
def imp(fn, name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(fn))
    new = [o for o in bpy.data.objects if o not in before]; g = group(name)
    for o in new:
        if o.parent is None:
            o.parent = g
    return g, new


H21 = os.path.join(HERE, "..", "..", "pilot_021", "assets", "human")
RUN, rn = imp(os.path.join(H21, "man_walk.glb"), "runner")
cloth = K.mat("runcloth", (.8, .78, .7), .8)
for o in rn:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(cloth)
K.box("rpack", (.35, .18, .45), (0, .14, 1.15), K.mat("rpackm", (.25, .3, .4), .8), parent=RUN)
SIT, sn_ = imp(os.path.join(H21, "man_sit.glb"), "sitter")
for o in sn_:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(cloth)
GIRL, gn = imp(os.path.join(HUM, "mother_walk.glb"), "girl")
GOATS = group("goats"); gm = K.mat("goat", (.25, .2, .16), .9)
for k in range(7):
    gx, gy = 30 + R.uniform(-12, 12), -120 + R.uniform(-8, 8)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.5, location=(gx, gy, .75)); gb = bpy.context.object; gb.scale = (.5, 1, .55); gb.data.materials.append(gm); gb.parent = GOATS
    for lx in (-.15, .15):
        for ly in (-.3, .3):
            K.tube((gx + lx, gy + ly, .55), (gx + lx, gy + ly, 0), .04, gm, GOATS, 6)
    K.box(f"gh{k}", (.18, .35, .22), (gx, gy - .55, 1.0), gm, (0.4, 0, 0), bevel=0, parent=GOATS)
CAN = group("canteen"); cm_ = K.mat("canteen", (.55, .55, .5), .35, .7)
bpy.ops.mesh.primitive_cylinder_add(radius=.11, depth=.05, location=(0, 0, 0), rotation=(math.pi / 2, 0, 0)); co = bpy.context.object; co.scale = (1, 1.4, 1); co.data.materials.append(cm_); co.parent = CAN

ml_ = bpy.data.lights.new("moon", "SUN"); ml_.energy = .25; ml_.color = (.6, .7, 1); MOON = bpy.data.objects.new("moon", ml_); sc.collection.objects.link(MOON); MOON.rotation_euler = (math.radians(50), 0, math.radians(30)); MOON.hide_render = True
ALL = {"shrine": SHR, "tree": TREE, "heli": HELI, "clouds": CLOUDS, "runner": RUN, "sitter": SIT, "girl": GIRL, "goats": GOATS, "canteen": CAN}


def show(*names, stars=False):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()
    FLARE.inputs["Emission Strength"].default_value = 0
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    STARS.hide_render = not stars; FL.hide_render = "heli" not in names; MOON.hide_render = True


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def day(el=35, rot=160, exp=-2.9, en=6):
    sky.set(0, el, rot, en); sc.view_settings.exposure = exp; sky.node.aerosol_density = 1.0


def eye(x, y, h=1.7):
    return Vector((x, y, H(x, y) + h))


def run_bob(t, k=.06):
    return Vector((math.sin(t * 5.5) * k * .5, 0, abs(math.sin(t * 5.5)) * k))


# ---------------------------------------------------------------- ショット
def s_l00():
    show(); day(28, 200, -1.6)
def a_l00(u, t, f):   # 砂嵐の中（砂はブラウザ）
    p = eye(60, 90) + run_bob(t, .05); cam.look(p, p + Vector((math.sin(t * .7) * 4, -30, -1)), 24)

def s_l01():
    show(); day(40, 160)
def a_l01(u, t, f):   # 砂丘を走る
    p = eye(60, 120 - 5 * t) + run_bob(t); cam.look(p, p + Vector((0, -40, -3)), 26)

def s_l02():
    show(); day(30, 200, -1.6)
def a_l02(u, t, f):
    p = eye(60, 100 - 3 * t) + run_bob(t, .04 * (1 - u)); cam.look(p, p + Vector((-2 * u, -40, -1)), 26)

def s_l03():
    show(); day(14, 250, -1.2)
def a_l03(u, t, f):   # 目印のない砂丘を見回す
    p = eye(40, 60); a = -math.pi / 2 + 1.6 * K.ease(u); cam.look(p, p + Vector((40 * math.cos(a), 40 * math.sin(a), -2)), 24)

def s_l04():
    show("canteen", stars=True); sky.set(0, -14, 250, 0); sc.view_settings.exposure = 1.2; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .3
    MOON.hide_render = False
    CAN.location = eye(40.18, 59.5, 1.25); CAN.rotation_euler = (.3, 0, .2)
def a_l04(u, t, f):   # 夜。白い星空、手もとの水筒
    p = eye(40, 60, 1.6) + Vector((0, 0, math.sin(t * 1.4) * .01)); z0 = H(40, 60); cam.look(p, mix((40.3, 58.6, z0 + 1.0), (40, 50, z0 + 6), K.ease(u)), 26)

def s_l05():
    show("heli"); day(18, 100, -1.3)
def a_l05(u, t, f):   # 低く飛ぶヘリコプター、発炎筒を撃つ → 去っていく
    HELI.location = (-60 + 90 * u, -40 - 160 * u, H(40, 60) + 30 + 30 * u); HELI.rotation_euler = (0, 0, math.radians(200)); ROT.rotation_euler = (0, 0, t * 40)
    ft = max(0, t - .5); FL.location = (40.5, 58 - 3 * ft, H(40, 60) + 2.0 + 28 * ft - 4.9 * ft * ft); FLARE.inputs["Emission Strength"].default_value = 80 if ft > 0 else 0
    FLARE.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
    p = eye(40, 60) + run_bob(t, .03); cam.look(p, mix(tuple(HELI.location), (10, -150, 30), .3), 24)

def s_l06():
    show("shrine", "tree"); day(30, 140)
def a_l06(u, t, f):   # 砂の向こうに廟
    p = eye(3, 30 - 8 * u) + run_bob(t, .02); cam.look(p, (SX, SY, SHR.location.z + 2.2), 30)

def s_l07():
    show("shrine", "clouds"); day(6, 200, -1.0)
def a_l07(u, t, f):   # 廟の戸口から、夕方に雲が集まる方を見る
    p = Vector((SX + .1, SY - 2.6, SHR.location.z + 1.5)); cam.look(p, mix((0, -400, 60), (-40, -400, 70), u), 24)   # 戸口のすぐ外（枠は pov.js 側）

def s_l08():
    show("shrine", "clouds"); day(4, 200, -.9)
def a_l08(u, t, f):   # 問い（戸口から、少しずつ寄る）
    p = Vector((SX + .05, SY - 2.6 - .5 * u, SHR.location.z + 1.5)); cam.look(p, (0, -400, 70), 24 + 6 * u)

def s_l09():
    show("shrine", "sitter"); day(20, 160, -.6)
    SIT.location = (SX + .3, SY - .4, SHR.location.z + .05); SIT.rotation_euler = (0, 0, math.pi)   # コウモリの壁の方を向く（顔は見せない）
def a_l09(u, t, f):   # 廟の中：壁のコウモリと、座る男の後ろ姿
    e = K.ease(u); z0 = SHR.location.z; cam.look(mix((SX + .9, SY - 1.6, z0 + 1.5), (SX + .6, SY - 1.3, z0 + 1.45), e), (SX, SY + 1.9, z0 + 2.1), 28)

def s_l10():
    show("shrine", "tree"); day(30, 160, -1.5)
def a_l10(u, t, f):   # 上空から：廟と、果てしない砂。誰もいない
    e = K.ease(u); cam.look(mix((40, 40, 70), (80, 80, 170), e), (SX, SY, SHR.location.z), 30)

def s_l11():
    show("runner", "clouds"); day(5, 200, -1.0)
def a_l11(u, t, f):   # 雲の方へ歩き出す（後ろ姿）
    RUN.location = (0, -60 - 3 * t, H(0, -60 - 3 * t)); RUN.rotation_euler = (0, 0, 0)
    e = K.ease(u); z0 = H(0, -60); cam.look(mix((2.5, -54, z0 + 1.6), (2, -57, z0 + 1.4), e), (-2, -100, z0 + 4), 30)

def s_l12():
    show("runner", "girl", "goats"); day(25, 120, -1.4)
    RUN.location = (24, -90, H(24, -90)); GIRL.location = (32, -126, H(32, -126)); GIRL.scale = (.82, .82, .82); GOATS.location.z = H(30, -120)
def a_l12(u, t, f):   # ヤギを連れた少女（遠景）
    e = K.ease(u); z0 = H(16, -86); cam.look(mix((14, -80, z0 + 1.9), (16, -86, z0 + 1.8), e), (31, -122, H(30, -124) + .9), 34)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]}
ORDER = ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12", "l13"]
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, HELI, ROT, FL, RUN])
