"""pilot_044（シャクルトン）の 3D の場面（Blender、ext/blender/blkit.py）。選択設計：問いまでは隊長の目線だけ、後半は外から。
使い方：blender -b -P anatomy_room/production/pilot_044/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：荒れた南の海（Blender の Ocean モディファイア）、エレファント島を模した岩の浜と崖（手続き的）、7 m 足らずの救命ボート（模式）、氷原と沈む船、サウスジョージアを模した雪の山。人物は MakeHuman / MPFB（後ろ姿・遠景だけ）。
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
R = random.Random(44)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


# ---------------------------------------------------------------- 海（Ocean モディファイア。time を毎コマ打つ）
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0)); SEA = bpy.context.object; SEA.name = "sea"
oc = SEA.modifiers.new("Ocean", "OCEAN"); oc.geometry_mode = "GENERATE"; oc.resolution = 16; oc.spatial_size = 90; oc.repeat_x = oc.repeat_y = 8
oc.wave_scale = 2.8; oc.choppiness = 1.9; oc.wind_velocity = 26; oc.wave_alignment = .4; oc.use_normals = True
SEA.location = (-480, -480, 0)
sea = bpy.data.materials.new("seam"); sea.use_nodes = True; n = sea.node_tree.nodes; L = sea.node_tree.links; b = n["Principled BSDF"]
b.inputs["Base Color"].default_value = (.02, .05, .06, 1); b.inputs["Roughness"].default_value = .12; b.inputs["Transmission Weight"].default_value = .0
b.inputs["Subsurface Weight"].default_value = .1; b.inputs["Coat Weight"].default_value = .4
tc = n.new("ShaderNodeTexCoord"); no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = .6; no.inputs["Detail"].default_value = 10; L.new(tc.outputs["Object"], no.inputs["Vector"])
gp = n.new("ShaderNodeNewGeometry"); sp = n.new("ShaderNodeSeparateXYZ"); L.new(gp.outputs["Position"], sp.inputs[0])
mr = n.new("ShaderNodeMapRange"); mr.inputs[1].default_value = .8; mr.inputs[2].default_value = 2.2; L.new(sp.outputs[2], mr.inputs[0])   # 波の頭は白く泡立つ
fm = n.new("ShaderNodeMath"); fm.operation = "MULTIPLY"; L.new(mr.outputs[0], fm.inputs[0]); L.new(no.outputs["Fac"], fm.inputs[1])
cm = n.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(fm.outputs[0], cm.inputs[0]); cm.inputs[6].default_value = (.02, .05, .06, 1); cm.inputs[7].default_value = (.75, .8, .82, 1)
L.new(cm.outputs[2], b.inputs["Base Color"]); rm = n.new("ShaderNodeMapRange"); L.new(fm.outputs[0], rm.inputs[0]); rm.inputs[3].default_value = .1; rm.inputs[4].default_value = .8; L.new(rm.outputs[0], b.inputs["Roughness"])
SEA.data.materials.append(sea)
bpy.ops.object.shade_smooth()


def sea_time(t, f, speed=1.0):
    oc.time = 10 + t * speed; SEA.keyframe_insert('modifiers["Ocean"].time', frame=f + 1)


# ---------------------------------------------------------------- 島（岩の浜と崖。原点の浜、海は -y）
rock = bpy.data.materials.new("rock"); rock.use_nodes = True; n = rock.node_tree.nodes; L = rock.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = .3; no.inputs["Detail"].default_value = 12; L.new(tc.outputs["Object"], no.inputs["Vector"])
gp = n.new("ShaderNodeNewGeometry"); sz = n.new("ShaderNodeSeparateXYZ"); L.new(gp.outputs["Position"], sz.inputs[0]); sn = n.new("ShaderNodeMapRange"); sn.inputs[1].default_value = 14; sn.inputs[2].default_value = 30; L.new(sz.outputs[2], sn.inputs[0])   # 高いところに雪
cmx = n.new("ShaderNodeMix"); cmx.data_type = "RGBA"; L.new(sn.outputs[0], cmx.inputs[0]); cmx.inputs[6].default_value = (.06, .055, .05, 1); cmx.inputs[7].default_value = (.8, .82, .86, 1)
L.new(cmx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8
bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .6; L.new(no.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])


def HI(x, y):   # 島の高さ：海（y<0）へ沈み、浜（y 0〜30）は波より高く、その先に崖がそびえる
    if y < 0:
        return 1.5 + y * .35
    base = 1.5 + y * .09 + max(0, y - 30) ** 1.25 * 1.6 + 25 * max(0, math.sin(x * .02 + 1)) * (y > 45)
    return min(240, base + 4 * math.sin(x * .07) * math.sin(y * .05) * (y > 30) + .25 * math.sin(x * 1.3) * math.sin(y * 1.1))


ISL = group("island")
bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=160, size=1, location=(0, 0, 0)); g = bpy.context.object; g.scale = (600, 300, 1); bpy.ops.object.transform_apply(scale=True)
for v in g.data.vertices:
    v.co.y += 140; v.co.z = HI(v.co.x, v.co.y)
for p in g.data.polygons:
    p.use_smooth = True
g.data.materials.append(rock); g.parent = ISL
pebble = K.mat("pebble", (.08, .075, .07), .6)
for k in range(220):   # 浜の大きな石
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=R.uniform(.2, .9), location=(R.uniform(-60, 60), R.uniform(-1, 25), 0)); s = bpy.context.object
    s.scale = (1, R.uniform(.7, 1.3), R.uniform(.4, .7)); s.location.z = HI(s.location.x, s.location.y) + .1; s.data.materials.append(pebble); s.parent = ISL

# ---------------------------------------------------------------- 救命ボート（全長 6.9 m）：船体・甲板・帆柱・帆
BOAT = group("boat"); hull_m = K.mat("hull", (.16, .14, .12), .6); canvas = K.mat("canvas", (.55, .5, .4), .9)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1); h = bpy.context.object
bm_ = bmesh.new(); bm_.from_mesh(h.data); bmesh.ops.delete(bm_, geom=[v for v in bm_.verts if v.co.z > .05], context="VERTS"); bm_.to_mesh(h.data); bm_.free()
h.scale = (1.0, 3.45, .9); h.location = (0, 0, .5); sol = h.modifiers.new("s", "SOLIDIFY"); sol.thickness = .05; h.data.materials.append(hull_m); h.parent = BOAT; bpy.ops.object.shade_smooth()
K.box("deck", (1.75, 5.6, .04), (0, 0, .5), canvas, bevel=.02, parent=BOAT)
K.tube((0, -1.2, .5), (0, -1.2, 4.2), .05, K.mat("mast", (.25, .2, .14), .6), BOAT, 10); K.tube((0, 1.6, .5), (0, 1.6, 2.6), .04, K.mat("mast2", (.25, .2, .14), .6), BOAT, 10)
bpy.ops.mesh.primitive_plane_add(size=1); sail = bpy.context.object; sail.scale = (1, 2.6, 1); sail.rotation_euler = (0, math.radians(90), 0); sail.location = (0, -2.4, 2.4)
bpy.ops.object.transform_apply(scale=True, rotation=True); sail.data.materials.append(canvas); sail.parent = BOAT
sb = sail.modifiers.new("bend", "SIMPLE_DEFORM"); sb.deform_method = "BEND"; sb.angle = math.radians(25); sb.deform_axis = "Z"
ICE_M = K.mat("boatice", (.82, .86, .9), .35)
ICE = K.box("ice", (1.82, 5.7, .12), (0, 0, .55), ICE_M, bevel=.05, parent=BOAT)
# 手（隊長の手：舵を握る、手袋）
GLOVE = K.mat("mitt", (.12, .1, .08), .9); HAND = group("hand"); HAND.parent = BOAT
K.tube((0, .25, .03), (0, 0, 0), .05, K.mat("jumper", (.2, .2, .18), .9), HAND, 16); K.box("mitt", (.1, .13, .06), (0, -.07, -.01), GLOVE, bevel=.025, parent=HAND)
K.tube((0, -.07, -.06), (0, -.07, .06), .02, K.mat("tiller", (.3, .22, .14), .6), HAND, 10)

# ---------------------------------------------------------------- 氷原と、沈む船（L01）
ICEF = group("icefield"); floe = K.mat("floe", (.75, .8, .88), .45)
K.box("pack", (2000, 2000, .1), (0, 0, -.05), K.mat("packice", (.62, .68, .76), .5), bevel=0, parent=ICEF)
for k in range(260):
    x, y = R.uniform(-150, 150), R.uniform(-260, 20); K.box(f"floe{k}", (R.uniform(4, 18), R.uniform(4, 18), R.uniform(.4, 1.2)), (x, y, .2), floe, (0, 0, R.uniform(0, 3)), bevel=.3, parent=ICEF)
SHIP = group("ship"); SHIP.parent = ICEF; SHIP.location = (10, -150, 0); SHIP.rotation_euler = (math.radians(12), math.radians(-18), math.radians(30))
K.box("shull", (8, 40, 6), (0, 0, 1), K.mat("shiph", (.06, .05, .05), .6), bevel=.5, parent=SHIP)
for y in (-12, 0, 12):
    K.tube((0, y, 3), (0, y, 28), .35, K.mat(f"smast{y}", (.08, .07, .06), .6), SHIP, 8)
    K.tube((-6, y, 20), (6, y, 20), .2, K.mat(f"syard{y}", (.08, .07, .06), .6), SHIP, 8)
ICEF.location = (0, 0, -500)
# ---------------------------------------------------------------- 雪の山（L11）：サウスジョージアを模した山並み
MT = group("mount"); snowm = K.mat("snowmt", (.85, .88, .94), .5)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=220, y_subdivisions=220, size=1); m = bpy.context.object; m.scale = (2000, 2000, 1); bpy.ops.object.transform_apply(scale=True)
for v in m.data.vertices:
    x, y = v.co.x, v.co.y; v.co.z = 180 * max(0, math.sin(x * .004 + 1.1) * math.sin(y * .0035 + .4)) ** 1.3 + 30 * math.sin(x * .02) * math.sin(y * .017) + 60 * max(0, y + 300) / 1000
for p in m.data.polygons:
    p.use_smooth = True
m.data.materials.append(snowm); m.parent = MT; MT.location = (0, 0, -2000)
# 人（浜の 28 人のうち手前の数人・山を越える 3 人：後ろ姿・遠景）
MEN = []
for k in range(8):
    hm = K.human("man_stand" if k % 3 else "man_sit", suit=(R.uniform(.08, .16), R.uniform(.07, .13), R.uniform(.06, .1)), helmet=False, pack=False); MEN.append(hm)
RESCUE = group("rescue"); K.box("rhull", (6, 30, 5), (0, 0, 1.5), K.mat("rh", (.1, .1, .1), .5), bevel=.4, parent=RESCUE); K.tube((0, 0, 3), (0, 0, 14), .6, K.mat("funnel", (.5, .2, .1), .5), RESCUE, 16)
RESCUE.location = (0, 0, -800)
ALL = {"sea": SEA, "island": ISL, "boat": BOAT, "icefield": ICEF, "mount": MT, "rescue": RESCUE}


def show(*names, men=0, ice=False, hand=False):
    SEA.animation_data_clear()

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    for k, hm in enumerate(MEN):
        hide(hm, k >= men)
    ICE.hide_render = not ice or "boat" not in names; hide(HAND, not hand or "boat" not in names)
    BOAT.location = (0, -30, 0); BOAT.rotation_euler = (0, 0, 0); ICEF.location = (0, 0, -500); MT.location = (0, 0, -2000); RESCUE.location = (0, 0, -800)
    storm()


# 曇り空：空のテクスチャに灰色の雲を混ぜる（雲のむらはノイズ）
_wn = sc.world.node_tree; _bg = _wn.nodes["Background"]; _sk = sky.node
_mx = _wn.nodes.new("ShaderNodeMix"); _mx.data_type = "RGBA"; _ns = _wn.nodes.new("ShaderNodeTexNoise"); _ns.inputs["Scale"].default_value = 3; _ns.inputs["Detail"].default_value = 8
_mr = _wn.nodes.new("ShaderNodeMapRange"); _mr.inputs[3].default_value = .6; _mr.inputs[4].default_value = .95; _wn.links.new(_ns.outputs["Fac"], _mr.inputs[0])
_vs = _wn.nodes.new("ShaderNodeVectorMath"); _vs.operation = "SCALE"; _vs.inputs["Scale"].default_value = .25; _wn.links.new(_sk.outputs[0], _vs.inputs[0])
_wn.links.new(_mr.outputs[0], _mx.inputs[0]); _wn.links.new(_vs.outputs[0], _mx.inputs[6]); _mx.inputs[7].default_value = (1.1, 1.15, 1.22, 1); _wn.links.new(_mx.outputs[2], _bg.inputs[0])
CLOUD = _mr


def storm(exp=-2.0, el=4, energy=1.8, cloud=(.6, .95)):   # 低い雲の空：太陽は雲に隠れ（弱く）、空気は灰色
    sky.set(0, el + 8, 160, energy * .3); sc.view_settings.exposure = exp
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.2; CLOUD.inputs[3].default_value, CLOUD.inputs[4].default_value = cloud


def bob(t, base, k=1.0, yaw=0.0):   # 波に揺られる小舟（高さ・ピッチ・ロール）
    BOAT.location = (base[0], base[1], base[2] + .6 * k * math.sin(t * 1.3) + .3 * k * math.sin(t * 2.1 + 1))
    BOAT.rotation_euler = (math.radians(9 * k * math.sin(t * 1.1 + .5)), math.radians(12 * k * math.sin(t * .9)), yaw)


def on_boat(local):   # ボートの上の点（世界座標）
    return BOAT.matrix_world @ Vector(local)


def beach_eye(t, x=0., y=6., k=.02):
    return Vector((x + math.sin(t * .7) * k, y, HI(x, y) + 1.65 + math.sin(t * 1.9) * k))


# ---------------------------------------------------------------- ショット（問いまでは隊長の目線）
def s_l00():
    show("sea", "island", "boat")
def a_l00(u, t, f):   # 浜から荒れた海を見る。浜に引き上げた小舟
    sea_time(t, f, 1.2); BOAT.location = (4, 3, HI(4, 3) + .25); BOAT.rotation_euler = (0, math.radians(8), math.radians(70))
    p = beach_eye(t, -2, 9, .05); cam.look(p, (3, -40, 0), 20)

def s_l00a():
    show("sea", "boat", hand=True)
def a_l00a(u, t, f):   # A：追い風の中を、小舟で（波が後ろから押す）
    sea_time(t, f, 1.4); bob(t, (0, -30 - 6 * t, .2), 1.0, 0); bpy.context.view_layer.update()
    HAND.location = (.45, 1.9, .95); p = on_boat((.55, 2.4, 1.6)); cam.look(p, on_boat((.2, -6, 1.0)), 20)

def s_l00b():
    show("sea", "boat", hand=True)
def a_l00b(u, t, f):   # B：向かい風の中を（舳先が波に突っ込む）
    sea_time(t, f, 1.6); bob(t * 1.4, (0, -30 - 1.5 * t, .2), 1.6, 0); bpy.context.view_layer.update()
    HAND.location = (.45, 1.9, .95); p = on_boat((.55, 2.4, 1.6)); cam.look(p, on_boat((.2, -6, .5)), 20, roll=.08 * math.sin(t * 2))

def s_l01():
    show("icefield")
def a_l01(u, t, f):   # 氷原と、押しつぶされて沈む船
    storm(-1.2, 3, 2.0); ICEF.location = (0, 0, 0); p = Vector((0, 12, 2.2 + math.sin(t) * .02)); cam.look(p, mix((8, -150, 8), (10, -150, 6), K.ease(u)), 26)

def s_l02():
    show("sea", "island", men=8)
def a_l02(u, t, f):   # 浜にたどり着いた仲間たち（背中）と崖
    sea_time(t, f)
    spots = [(-4, 14, math.pi), (-1, 16, math.pi), (2, 13, math.pi), (5, 17, math.pi), (-7, 18, math.pi), (8, 15, math.pi), (0, 20, math.pi), (-3, 22, math.pi)]
    for hm, (x, y, r) in zip(MEN, spots):
        hm.location = (x, y, HI(x, y) + .05); hm.rotation_euler = (0, 0, r)
    p = beach_eye(t, 1, 5); cam.look(p, (0, 60, 18 + 6 * u), 22)

def s_l03():
    show("sea", "island", "boat")
def a_l03(u, t, f):   # 小さな救命ボートと、その先の海
    sea_time(t, f, 1.2); BOAT.location = (1, 3, HI(1, 3) + .25); BOAT.rotation_euler = (0, math.radians(6), math.radians(95))
    p = beach_eye(t, -1, 9); cam.look(mix(p, (p.x - 1, p.y - 1.5, p.z - .2), K.ease(u)), (1, -10, .5), 22)

def s_l04():
    show("sea", "island")
def a_l04(u, t, f):   # 南米の方角：向かい風。雲が速い
    sea_time(t, f, 1.8); storm(-1.6, 3, 1.2); p = beach_eye(t, 0, 2, .06); cam.look(p, (-40, -60, 3), 22, roll=-.04)

def s_l05():
    show("sea", "island")
def a_l05(u, t, f):   # サウスジョージアの方角：背中を押す風。波は向こうへ
    sea_time(t, f, 1.2); storm(-1.3, 6, 2.2); p = beach_eye(t, 0, 2); cam.look(p, mix((60, -60, 2), (70, -60, 4), K.ease(u)), 20)

def s_l06():
    show("sea", "island", "boat", men=3)
def a_l06(u, t, f):   # 問い：舳先の前に立つ。後ろに仲間
    sea_time(t, f, 1.3); BOAT.location = (0, 3, HI(0, 3) + .25); BOAT.rotation_euler = (0, math.radians(5), math.radians(90))
    for hm, (x, y) in zip(MEN, [(-4, 12), (3, 13), (6, 16)]):
        hm.location = (x, y, HI(x, y)); hm.rotation_euler = (0, 0, math.pi)
    p = beach_eye(t, -.5, 7); cam.look(p, (0, -30, 1), 22 + 4 * u)

# 後半（外から）
def s_l07():
    show("sea", "boat", ice=False)
def a_l07(u, t, f):   # 荒れた海を進む小舟（外から）
    sea_time(t, f, 1.3); bob(t, (0, -30 - 3 * t, .2), 1.2, 0); cam.look(mix((14, -30, 4), (12, -40, 3.5), K.ease(u)), tuple(BOAT.location), 30)

def s_l09():
    show("sea", "boat", ice=True)
def a_l09(u, t, f):   # 氷に覆われた小舟。雲の切れ間の低い太陽
    storm(-1.6, 2.5, 4.0, (.3, .8)); sea_time(t, f, 1.2); bob(t, (0, -30 - 2 * t, .2), 1.0, 0)
    cam.look(mix((-8, -22, 2.5), (-7, -26, 2.2), K.ease(u)), tuple(BOAT.location), 32)

def s_l10():
    show("sea", "boat", ice=True)
def a_l10(u, t, f):   # 大きな海の、小さな舟（引き）
    sea_time(t, f, 1.3); bob(t, (0, -30 - 2 * t, .2), 1.2, 0); cam.look(mix((30, 10, 25), (40, 20, 45), K.ease(u)), tuple(BOAT.location), 24)

def s_l11():
    show("mount", men=3)
def a_l11(u, t, f):   # 雪の山を越える 3 人（遠景）
    storm(-1.2, 8, 3.0); MT.location = (0, 0, 0)
    for k, hm in enumerate(MEN[:3]):
        x, y = -2 + k * 1.6, -k * 2.2 + .6 * t; hm.location = (x, y, 0); hm.rotation_euler = (0, 0, math.pi)
    bpy.context.view_layer.update()
    gz = lambda x, y: 180 * max(0, math.sin(x * .004 + 1.1) * math.sin(y * .0035 + .4)) ** 1.3 + 30 * math.sin(x * .02) * math.sin(y * .017) + 60 * max(0, y + 300) / 1000
    for hm in MEN[:3]:
        hm.location.z = gz(hm.location.x, hm.location.y)
    c = Vector((0, -2, gz(0, -2))); cam.look((c.x + 6, c.y - 22, c.z + 4), (c.x, c.y + 6, c.z + 1.5), 30)

def s_l12():
    show("sea", "island", "rescue", men=6)
def a_l12(u, t, f):   # 救助の船が浜に近づく（浜の仲間の背中）
    sea_time(t, f, .8); storm(-1.1, 10, 3.5); RESCUE.location = (-30 + 6 * t, -260, 0); RESCUE.rotation_euler = (0, 0, math.radians(80))
    for hm, (x, y) in zip(MEN, [(-6, 10), (-3, 12), (0, 9), (3, 11), (6, 10), (9, 13)]):
        hm.location = (x, y, HI(x, y)); hm.rotation_euler = (0, 0, 0)
    cam.look(mix((2, 24, HI(2, 24) + 3), (1, 22, HI(1, 22) + 2.6), K.ease(u)), (-10, -240, 4), 28)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l01", "l02", "l03", "l04", "l05", "l06", "l07", "l09", "l10", "l11", "l12", "l00", "l00a", "l00b"]}
SHOTS.update({k: (globals()["s_" + v], globals()["a_" + v]) for k, v in {"l00_2": "l01", "l00_3": "l10", "l03_2": "l02"}.items()})   # カット（2026-11-03〜）
ORDER = None   # renderer の SHOTS とカットから時刻の順に（blkit.renderer_order）
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, BOAT, HAND, ICEF, MT, RESCUE] + MEN)
