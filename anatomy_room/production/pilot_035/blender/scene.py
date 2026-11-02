"""pilot_035 の 3D の場面（Blender、ext/blender/blkit.py）。
使い方：blender -b -P anatomy_room/production/pilot_035/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：気球とゴンドラ（エクセルシオール III を模した形、寸法はおおよそ）、与圧服の人（MakeHuman / MPFB、顔はヘルメットで覆う）、
地表と雲（手続き的）、高度ごとの空（Blender の多重散乱の空）。l09 は 1959 年のエクセルシオール I（きりもみ）なので低めの高度の空。
"""
import sys, os, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import bpy
from mathutils import Vector, Euler
import blkit as K

O = K.args()
sc = K.setup(O["samples"])
sky = K.Sky(); earth = K.Earth(); cam = K.Cam()

# ---------------------------------------------------------------- ゴンドラ（床は原点、扉は -Y 側）
alu = K.mat("alu", (.75, .76, .78), .32, 1.0); pad = K.mat("pad", (.82, .62, .18), .7); dark = K.mat("dark", (.05, .05, .06), .6)
white = K.mat("white", (.86, .86, .84), .45)
G = bpy.data.objects.new("gondola", None); sc.collection.objects.link(G)
K.box("floor", (1.5, 1.3, .06), (0, 0, 0), alu, parent=G); K.box("step", (.5, .35, .04), (0, -.83, .02), alu, parent=G)
for x in (-.73, .73):
    for y in (-.63, .63):
        K.tube((x, y, 0), (x, y, 1.75), .022, alu, G)
for z in (.9, 1.75):
    for (a, b) in [((-.73, -.63), (.73, -.63)), ((-.73, .63), (.73, .63)), ((-.73, -.63), (-.73, .63)), ((.73, -.63), (.73, .63))]:
        if z == .9 and a[1] == -.63 and b[1] == -.63:
            continue
        K.tube((*a, z), (*b, z), .018, alu, G)
K.box("back", (1.4, .05, 1.2), (0, .6, .75), pad, parent=G)
for i, (x, z) in enumerate([(-.4, 1.2), (.05, 1.25), (.45, 1.1), (-.1, .7)]):
    K.box(f"inst{i}", (.28, .12, .2), (x, .52, z), dark, parent=G)
K.box("seat", (.5, .4, .08), (-.35, .25, .45), pad, parent=G); K.box("seatback", (.5, .06, .5), (-.35, .45, .72), pad, parent=G)
for x in (.3, .45, .6):
    K.tube((x, .45, .05), (x, .45, .75), .07, white, G)
for x in (-.73, .73):
    K.box(f"side{x}", (.03, 1.2, .55), (x, 0, .3), pad, parent=G)
LINES = [K.tube((x, y, 1.75), (0, 0, 40), .006, dark) for x in (-.73, .73) for y in (-.63, .63)]

# ---------------------------------------------------------------- 気球（ポリエチレン、満ちた形。底は高さ 40 m）
poly = bpy.data.materials.new("poly"); poly.use_nodes = True; n = poly.node_tree.nodes; L = poly.node_tree.links; pb = n["Principled BSDF"]
pb.inputs["Base Color"].default_value = (.95, .95, .97, 1); pb.inputs["Roughness"].default_value = .3; pb.inputs["Transmission Weight"].default_value = .5
gores = n.new("ShaderNodeTexGradient"); gores.gradient_type = "RADIAL"; L.new(n.new("ShaderNodeTexCoord").outputs["Object"], gores.inputs[0])   # 縦の継ぎ目（ゴア）
mth = n.new("ShaderNodeMath"); mth.operation = "PINGPONG"; mth.inputs[1].default_value = 1 / 60; L.new(gores.outputs["Fac"], mth.inputs[0])
bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .25; L.new(mth.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], pb.inputs["Normal"])
prof = [(.5, 0), (4, 6), (11, 16), (19, 28), (25, 40), (29, 52), (30.5, 62), (29, 72), (22, 80), (12, 85), (0, 86.5)]
BAL = K.lathe("balloon", prof, poly, 128, (0, 0, 40))

# ---------------------------------------------------------------- 人
DIV = K.human("man_stand")
dro = bpy.data.materials.new("drogue"); dro.use_nodes = True; dn = dro.node_tree.nodes; dl = dro.node_tree.links; db = dn["Principled BSDF"]
chk = dn.new("ShaderNodeTexChecker"); chk.inputs["Color1"].default_value = (.9, .32, .08, 1); chk.inputs["Color2"].default_value = (.92, .92, .9, 1); chk.inputs["Scale"].default_value = 4
dl.new(chk.outputs[0], db.inputs["Base Color"]); db.inputs["Roughness"].default_value = .7
DRO = K.lathe("drogue", [(.05, 0), (.5, .15), (.85, .45), (.9, .6)], dro, 48, (0, 0, DIV["top"] + 4.5)); DRO.rotation_euler = (math.pi, 0, 0); DRO.parent = DIV
dro_lines = [K.tube((.85 * math.cos(a), .85 * math.sin(a), DIV["top"] + 3.9), (0, .16, DIV["top"] - .3), .004, dark, DIV) for a in [i * math.pi / 3 for i in range(6)]]
WAT = K.human("man_stand", suit=(.08, .08, .09), helmet=False, pack=False)   # l13：地上で見上げる人（後ろ姿の影）
bpy.ops.mesh.primitive_uv_sphere_add(radius=60, location=(-4000, -50000, 39000)); FAR = bpy.context.object      # 2012 年の気球（遠くの光る点）
fm = K.mat("far", (1, 1, 1), .3); fb = fm.node_tree.nodes["Principled BSDF"]; fb.inputs["Emission Color"].default_value = (1, 1, 1, 1); fb.inputs["Emission Strength"].default_value = 40
FAR.data.materials.append(fm)

GROUP_GOND = [G, BAL] + LINES


def show(gond=True, diver=True, drogue=False, watcher=False, far=False):
    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for o in GROUP_GOND:
        hide(o, not gond)
    hide(DIV, not diver); hide(WAT, not watcher); FAR.hide_render = not far
    DRO.hide_render = not drogue
    for l in dro_lines:
        l.hide_render = not drogue


def stand():
    DIV.rotation_mode = "XYZ"; DIV.location = (0, -.78, .04); DIV.rotation_euler = (0, 0, 0)


def high(alt=31000, exp=-3.2, el=14, rot=205):
    sky.set(alt, el, rot); earth.altitude(alt); sc.view_settings.exposure = exp


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


# ---------------------------------------------------------------- ショット（u：0〜1、t：ショットの頭からの秒）
def s_l01():
    high(); show(); stand()
def a_l01(u, t, f):
    e = K.ease(u); cam.look(mix((72, -125, 10), (52, -108, 14), e), (0, 0, 22), 35)

def s_l02():
    high(); show(); stand()
def a_l02(u, t, f):
    e = K.ease(u); cam.look(mix((.34, -.22, 1.8), (.3, -.32, 1.74), e), (.7, -40, -24), mix((20,), (24,), e)[0])

def s_l03b():
    high(); show(); stand()
def a_l03b(u, t, f):
    e = K.ease(u); cam.look(mix((2.6, -4.6, 3.4), (2.0, -3.8, 2.8), e), (-.1, -.5, .4), 22)

def s_l04():
    high(); show(); stand()
def a_l04(u, t, f):
    e = K.ease(u); cam.look(mix((-1.75, -.05, 1.5), (-1.35, -.2, 1.45), e), (0, -.8, 1.15), mix((32,), (40,), e)[0])

def s_l06():
    high(); show(); stand()
def a_l06(u, t, f):
    tt = max(0, t - .12)                                     # 一歩を踏み出して、落ちる（実際の重力の落ち方）
    DIV.location = (0, -.78 - .9 * tt, .04 - 4.9 * tt * tt); DIV.rotation_euler = (.7 * tt, 0, .15 * tt)
    p = Vector(DIV.location) + Vector((0, 0, .8))
    cam.look((.55, -.35, 2.35), p, 24)

def s_l08():
    high(25000, -3.0); show(gond=False, drogue=True); DIV.rotation_mode = "XYZ"
def a_l08(u, t, f):
    DIV.location = (0, 0, 0); DIV.rotation_euler = (.22 + .05 * math.sin(t * 2.3), .06 * math.sin(t * 1.7), .3 * t)
    e = K.ease(u); sh = .015 * math.sin(f * 1.9)
    cam.look(mix((4.2, -4.4, .4), (3.4, -3.8, 1.2), e), (sh, 0, 3.4 + sh), 24)

SPIN_C = Vector((0, 0, .9))
def s_l09():
    high(18000, -3.0, 22); show(gond=False); DIV.rotation_mode = "XYZ"
def a_l09(u, t, f):
    rz = 2 * math.pi * 2.0 * t                              # きりもみ：毎秒 2 回転（120 rpm）
    DIV.rotation_euler = (1.4, 0, rz); DIV.location = -(Euler((1.4, 0, rz), "XYZ").to_matrix() @ SPIN_C)
    if t < .45:
        cam.look((3.2, -2.6, -1.0), (0, 0, 0), 35)
    elif t < .95:
        cam.look((.6, .6, 4.2), (0, 0, 0), 30)    # 真上から（手のアップにならない距離）
    elif t < 1.5:
        cam.look((-2.0, -2.6, .7), (0, 0, 0), 40)
    else:
        e = K.ease((t - 1.5) / max(.3, (u and t / u or 3) - 1.5)); cam.look(mix((-3.8, -3.2, 1.4), (-3.0, -2.6, 1.1), e), (0, 0, 0), 35)

def s_l11():
    high(); show(); stand()
def a_l11(u, t, f):
    e = K.ease(u); cam.look(mix((58, -100, -4), (95, -165, -18), e), (0, 0, 40), 35)

def s_l13():
    high(0, -3.4, 24, 190); earth.altitude(0, .04, 30); show(gond=False, diver=False, watcher=True, far=True)
    WAT.location = (0, 0, 0); WAT.rotation_euler = (0, 0, 0)
def a_l13(u, t, f):
    e = K.ease(u); cam.look(mix((.45, 2.6, .55), (.35, 2.1, .6), e), (-.3, -20, .6 + 8.1), 35)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l01", "l02", "l03b", "l04", "l06", "l08", "l09", "l11", "l13"]}
ORDER = ["l01", "l02", "l03", "l03b", "l04", "l05", "l06", "l07", "l08", "l08b", "l09", "l10", "l11", "l12", "l13"]   # renderer の SHOTS の at の順
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, DIV])
