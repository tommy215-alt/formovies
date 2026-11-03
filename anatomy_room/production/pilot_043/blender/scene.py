"""pilot_043（ジョン・スノウ）の 3D の場面（Blender、ext/blender/blkit.py）。選択設計：問いまでは医者の目線だけ、後半は外から。
使い方：blender -b -P anatomy_room/production/pilot_043/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：1854 年ごろのロンドンの路地（模式：石畳・れんがの家・霧）、鋳鉄の井戸のポンプ、石灰の粉、ドア、水のコップ、ビール工場。人物は MakeHuman / MPFB（顔は描かない：後ろ姿・遠景・手だけ）。
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
R = random.Random(43)


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def emit(name, col, s):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = s; b.inputs["Base Color"].default_value = (*col, 1); return m, b


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


# ---------------------------------------------------------------- 石畳（ノイズの凹凸と、溝の模様）
cob = bpy.data.materials.new("cobble"); cob.use_nodes = True; n = cob.node_tree.nodes; L = cob.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord"); vo = n.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 6; vo.feature = "DISTANCE_TO_EDGE"; L.new(tc.outputs["Object"], vo.inputs["Vector"])
rr = n.new("ShaderNodeMapRange"); rr.inputs[1].default_value = 0; rr.inputs[2].default_value = .06; L.new(vo.outputs["Distance"], rr.inputs[0])
cm = n.new("ShaderNodeMix"); cm.data_type = "RGBA"; L.new(rr.outputs[0], cm.inputs[0]); cm.inputs[6].default_value = (.05, .045, .04, 1); cm.inputs[7].default_value = (.24, .22, .2, 1)
L.new(cm.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .55
bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .5; L.new(rr.outputs[0], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
brick = bpy.data.materials.new("brick"); brick.use_nodes = True; n = brick.node_tree.nodes; L = brick.node_tree.links; b = n["Principled BSDF"]
bt = n.new("ShaderNodeTexBrick"); bt.inputs["Scale"].default_value = 2.2; bt.inputs["Color1"].default_value = (.28, .13, .08, 1); bt.inputs["Color2"].default_value = (.2, .1, .07, 1); bt.inputs["Mortar"].default_value = (.12, .11, .1, 1)
tc = n.new("ShaderNodeTexCoord"); sp = n.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0]); ad = n.new("ShaderNodeMath"); L.new(sp.outputs[0], ad.inputs[0]); L.new(sp.outputs[1], ad.inputs[1])
cb = n.new("ShaderNodeCombineXYZ"); L.new(ad.outputs[0], cb.inputs[0]); L.new(sp.outputs[2], cb.inputs[1]); L.new(cb.outputs[0], bt.inputs["Vector"]); L.new(bt.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .9
bb = n.new("ShaderNodeBump"); bb.inputs["Strength"].default_value = .4; L.new(bt.outputs["Fac"], bb.inputs["Height"]); L.new(bb.outputs[0], b.inputs["Normal"])

# ---------------------------------------------------------------- 路地（x 方向に伸びる。道幅 8 m、両側にれんがの家）。ポンプは原点
ST = group("street")
K.box("road", (200, 8, .1), (0, 0, -.05), cob, bevel=0, parent=ST)
for side in (-1, 1):
    K.box(f"pave{side}", (200, 1.6, .16), (0, side * 4.8, .02), K.mat(f"pv{side}", (.2, .19, .18), .7), bevel=0, parent=ST)
    x = -60
    while x < 60:
        w = R.uniform(5, 8); h = R.uniform(8, 12)
        K.box(f"house{side}{x:.0f}", (w - .1, 6, h), (x + w / 2, side * 8.6, h / 2), brick, bevel=0, parent=ST)
        for k in range(int(w // 1.8)):
            for z in (1.2, 4.2, 7.2):
                if z < h - 1.5:
                    lit = R.random() < .12
                    K.box(f"win{side}{x:.0f}{k}{z}", (.9, .1, 1.5), (x + .9 + k * 1.8, side * 5.58, z + .4), emit(f"wm{side}{x:.0f}{k}{z}", (1, .7, .35), 2.5)[0] if lit else K.mat(f"wd{side}{x:.0f}{k}{z}", (.02, .025, .03), .15), bevel=0, parent=ST)
        if R.random() < .6:   # ドア
            K.box(f"door{side}{x:.0f}", (1.0, .12, 2.1), (x + w - 1.2, side * 5.57, 1.05), K.mat(f"dr{side}{x:.0f}", (.07, .09, .07), .6), bevel=.01, parent=ST)
        x += w
# 鋳鉄のポンプ（柄は外せる）
PUMP = group("pump"); iron = K.mat("iron", (.04, .045, .05), .45, .8)
K.lathe("pbody", [(.16, 0), (.16, .05), (.12, .1), (.11, 1.4), (.14, 1.5), (.13, 1.6), (.06, 1.75), (.0, 1.8)], iron, loc=(0, 0, 0)).parent = PUMP
K.tube((0, -.1, 1.15), (0, -.42, 1.0), .035, iron, PUMP, 16)
HANDLE = group("handle"); HANDLE.parent = PUMP; HANDLE.location = (0, .1, 1.4)
K.tube((0, 0, 0), (0, .9, .25), .028, iron, HANDLE, 12)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.05, location=(0, .9, .25)); k_ = bpy.context.object; k_.data.materials.append(iron); k_.parent = HANDLE
K.box("trough", (.6, .4, .25), (0, -.55, .13), K.mat("stone", (.3, .29, .27), .8), parent=PUMP)
WATER_M = bpy.data.materials.new("water"); WATER_M.use_nodes = True; wb = WATER_M.node_tree.nodes["Principled BSDF"]; wb.inputs["Base Color"].default_value = (.6, .62, .55, 1); wb.inputs["Transmission Weight"].default_value = 1; wb.inputs["Roughness"].default_value = .02
STREAM = K.tube((0, -.42, 1.0), (0, -.45, .26), .018, K.mat("streamw", (.7, .74, .78), .08), PUMP, 12)
# 石灰の粉（道にまかれた白い跡）
LIME = group("lime"); lm = K.mat("lime", (.82, .82, .78), .95)
for k in range(60):
    K.box(f"lime{k}", (R.uniform(.3, 1.2), R.uniform(.3, 1.0), .01), (R.uniform(-30, 30), R.uniform(-3.5, 3.5), .006), lm, (0, 0, R.uniform(0, 3)), bevel=0, parent=LIME)
# 水のコップ（室内の机）と手
CUP = group("cup"); glass = bpy.data.materials.new("glass"); glass.use_nodes = True; gb = glass.node_tree.nodes["Principled BSDF"]; gb.inputs["Transmission Weight"].default_value = 1; gb.inputs["Roughness"].default_value = .02
K.lathe("cupg", [(.04, 0), (.045, .005), (.05, .12), (.048, .12), (.043, .006)], glass).parent = CUP
K.lathe("cupw", [(.0, .006), (.042, .006), (.046, .09), (.0, .09)], WATER_M).parent = CUP
TABLE = group("table"); K.box("tab", (1.2, .8, .05), (0, 0, .76), K.mat("tabw", (.2, .13, .08), .5), parent=TABLE)
CANDLE_M, CANDLE = emit("candle", (1, .6, .25), 15)
bpy.ops.mesh.primitive_cylinder_add(radius=.02, depth=.14, location=(-.3, .1, .86)); cdl = bpy.context.object; cdl.data.materials.append(K.mat("wax", (.9, .86, .75), .6)); cdl.parent = TABLE
bpy.ops.mesh.primitive_uv_sphere_add(radius=.012, location=(-.3, .1, .95)); fl = bpy.context.object; fl.scale = (1, 1, 2); fl.data.materials.append(CANDLE_M); fl.parent = TABLE
cl = bpy.data.lights.new("candleL", "POINT"); cl.energy = 6; cl.color = (1, .6, .3); clo = bpy.data.objects.new("candleL", cl); sc.collection.objects.link(clo); clo.parent = TABLE; clo.location = (-.3, .1, 1.0)
K.box("tabwall", (4, .1, 3), (0, -.6, 1.5), K.mat("plaster", (.35, .3, .24), .9), bevel=0, parent=TABLE)
TABLE.location = (0, 0, -40); CUP.parent = TABLE; CUP.location = (.05, -.05, .785)
SKIN = K.mat("skin", (.66, .5, .42), .55); HAND = group("hand")
K.tube((0, .22, .03), (0, .06, .01), .034, K.mat("coat", (.06, .06, .07), .8), HAND, 16); K.tube((0, .07, .01), (0, -.03, 0), .024, SKIN, HAND, 16)
K.box("palm", (.07, .08, .026), (0, -.07, -.006), SKIN, (math.radians(-8), 0, 0), bevel=.012, parent=HAND)
for x in (-.025, -.008, .009, .025):
    K.tube((x, -.105, -.01), (x * .7, -.15, -.035), .008, SKIN, HAND, 10)
K.tube((.033, -.05, -.008), (.012, -.13, -.03), .009, SKIN, HAND, 10)
# ビール工場（後半）：大きな樽と、工場の井戸
BREW = group("brew"); wood = K.mat("barrel", (.3, .18, .09), .6)
for k in range(10):
    o = K.lathe(f"barrel{k}", [(.0, 0), (.45, 0), (.55, .5), (.45, 1.0), (.0, 1.0)], wood, loc=(-4 + (k % 5) * 1.3, 2.5 + (k // 5) * 1.3, 0)); o.parent = BREW
K.box("brewwall", (14, .3, 8), (0, 4.5, 4), brick, bevel=0, parent=BREW); K.box("brewfl", (14, 14, .1), (0, -2, -.05), cob, bevel=0, parent=BREW)
BREW.location = (0, 0, -80)
# 荷車（A：患者を街の外の病院へ運ぶ。毛布をかけた患者の形・木の車輪）
CART = group("cart"); cw = K.mat("cartw", (.22, .15, .09), .8); blanket = K.mat("blanket", (.32, .3, .26), .95)
K.box("cbed", (1.3, 2.4, .12), (0, 0, .75), cw, parent=CART)
for x in (-.65, .65):
    K.box(f"cside{x}", (.05, 2.4, .3), (x, 0, .95), cw, parent=CART)
    for y in (-.7, .7):
        bpy.ops.mesh.primitive_cylinder_add(radius=.5, depth=.08, vertices=24, location=(x * 1.12, y, .5), rotation=(0, math.radians(90), 0)); w_ = bpy.context.object; w_.data.materials.append(cw); w_.parent = CART
for k, y in enumerate((-.55, .55)):
    K.box(f"pat{k}", (.5, 1.0, .25), (0, y * .9, .95), blanket, bevel=.1, parent=CART)
for x in (-.35, .35):
    K.tube((x, -1.2, .8), (x, -2.4, .9), .03, cw, CART, 8)
CART.location = (0, 0, -60)
# 人（路地の人々：遠景の後ろ姿）
PEOPLE = []
for k in range(10):
    h = K.human("man_walk" if k % 2 else "man_stand", suit=(R.uniform(.05, .15), R.uniform(.05, .12), R.uniform(.05, .1)), helmet=False, pack=False); PEOPLE.append(h)
ALL = {"street": ST, "pump": PUMP, "lime": LIME, "table": TABLE, "brew": BREW, "cart": CART}


def unhide(o):
    for c in [o] + list(o.children_recursive):
        c.hide_render = False


def show(*names, people=0, hand=False, stream=False, fog=.03):
    for m in bpy.data.materials:
        if m.node_tree:
            m.node_tree.animation_data_clear()

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    for k, h in enumerate(PEOPLE):
        hide(h, k >= people)
    hide(HAND, not hand); STREAM.hide_render = not stream or "pump" not in names
    HANDLE.location = (0, .1, 1.4); HANDLE.rotation_euler = (0, 0, 0); TABLE.location = (0, 0, -40); BREW.location = (0, 0, -80); CART.location = (0, 0, -60)
    sky.set(0, 6, 120, 2.0); sc.view_settings.exposure = -1.0; sc.world.node_tree.nodes["Background"].inputs[1].default_value = .6
    set_fog(fog)


FOG = None
def set_fog(d):   # 霧（ロンドンの汚れた空気）：路地を覆う箱の体積
    global FOG
    if FOG is None:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 5.5)); FOG = bpy.context.object; FOG.scale = (160, 30, 13)
        m = bpy.data.materials.new("fog"); m.use_nodes = True; nt = m.node_tree; nt.nodes.remove(nt.nodes["Principled BSDF"])
        v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Color"].default_value = (.75, .7, .6, 1); nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
        FOG.data.materials.append(m); FOG["vol"] = v.name
    FOG.data.materials[0].node_tree.nodes[FOG["vol"]].inputs["Density"].default_value = d * 1.6; FOG.hide_render = d <= 0


def place_people(spots, t, walk=.8):
    for h, (x, y, r) in zip(PEOPLE, spots):
        h.location = (x + math.sin(r) * walk * t * .3, y, 0); h.rotation_euler = (0, 0, r)


def eye(t, x=0., y=0., k=.01):   # 歩く目の高さ（上下の揺れ）
    return Vector((x, y, 1.65 + abs(math.sin(t * 5.5)) * k))


# ---------------------------------------------------------------- ショット（問いまでは医者の目線）
def s_l00():
    show("street", "pump", "lime", people=6, fog=.04)
def a_l00(u, t, f):   # 霧の路地と、通りの真ん中のポンプ
    place_people([(-14, 3, -1.6), (-9, -2.5, -1.4), (-20, 1, -1.6), (-6, 3.8, 3.1), (-24, -3, -1.7), (-17, 0, 0)], t)
    p = eye(t, 8 - 2.2 * u, .6); cam.look(p, (0, 0, 1.1), 24)

def s_l00a():
    show("street", "cart", people=3, fog=.06)
def a_l00a(u, t, f):   # A：患者を荷車に乗せて、街の外へ運ぶ（引く人の背中を追う）
    CART.location = (-6 - 1.3 * t, 0, 0); CART.rotation_euler = (0, 0, math.radians(-90))
    PEOPLE[0].location = (-8.6 - 1.3 * t, 0, 0); PEOPLE[0].rotation_euler = (0, 0, math.radians(-90))
    place_people([(0, 0, 0), (-5, 1.2, -1.5), (-7, -1.2, -1.6)], t, .9); PEOPLE[0].location = (-8.6 - 1.3 * t, 0, 0); PEOPLE[0].rotation_euler = (0, 0, math.radians(-90))
    p = eye(t, -2.2 - 1.3 * t, .3); cam.look(p, (p.x - 6, -.1, 1.0), 24)

def s_l00b():
    show("street", "pump", fog=.03); unhide(HAND)
def a_l00b(u, t, f):   # B：ポンプの柄をつかんで、外す
    HANDLE.location = (0, .1, 1.4); HANDLE.rotation_euler = (math.radians(-25 * K.ease(u)), 0, 0)
    HAND.location = (0, .95, 1.66 - .18 * K.ease(u)); HAND.rotation_euler = (math.radians(-60), 0, math.radians(180))
    cam.look((0, 1.55, 1.75), (0, .7, 1.45), 26)

def s_l01():
    show("street", "lime", people=8, fog=.05)
def a_l01(u, t, f):   # 1854 年、ロンドン。霧の中を歩く
    place_people([(-12, 3, -1.6), (-18, -2, -1.5), (-25, 1.2, -1.6), (-8, -3.6, 3.1), (-30, -1, -1.6), (-15, 0, 0), (-35, 2, -1.5), (-22, -3, -1.5)], t)
    p = eye(t, 12 - 3 * u, -1); cam.look(p, (p.x - 20, -.3, -1.4), 22)

def s_l02():
    show("street", people=4, fog=.05)
def a_l02(u, t, f):   # 戸口で倒れる人たち（扉の前に座り込む影：遠景）
    place_people([(-8, 4.6, 0), (-14, -4.6, 3.14), (-20, 4.4, 0), (-26, -4.4, 3.14)], 0)
    p = eye(t, 4, 1.5); cam.look(p, mix((-12, 3.6, 1.2), (-12, -3, 1.0), K.ease(u)), 26)

def s_l03():
    show("street", "lime", people=3, fog=.07)
def a_l03(u, t, f):   # 道に白い石灰。悪い空気がうつすと考えられていた
    place_people([(-6, 2.6, -1.7), (-9, -1.5, -1.4), (-15, .5, -1.6)], t, .3)
    p = eye(t, 3, 0); cam.look(p, (-3, .2, 0), 22 + 6 * u)

def s_l04():
    show("street", fog=.04)
def a_l04(u, t, f):   # 家を一軒ずつ訪ねる：戸口を回る
    p = eye(t * 1.4, mix((10,), (-10,), u)[0], -2.6, .02); cam.look(p, (p.x - 4, -5.6, 1.4), 22)

def s_l05():
    show("table", fog=0)
def a_l05(u, t, f):   # 水を調べる：コップの水はほとんど透明
    TABLE.location = (0, 0, 0); CUP.location = (.05, -.05, .785)
    cam.look(mix((.0, .45, 1.05), (.0, .32, .95), K.ease(u)), (.05, -.05, .85), 40)

def s_l06():
    show("street", "pump", "lime", fog=.05)
def a_l06(u, t, f):   # 問い：霧の中のポンプの前に立つ
    p = eye(t, 0, 2.6 - .6 * K.ease(u), .004); cam.look(p, (0, 0, 1.3), 24)

# 後半（外から）
def s_l07():
    show("street", "pump", people=1, fog=.05)
def a_l07(u, t, f):   # ポンプの前に立つ医者（後ろ姿）
    PEOPLE[0].location = (0, 1.2, 0); PEOPLE[0].rotation_euler = (0, 0, 0)
    cam.look(mix((1.5, 5.0, 1.8), (1.2, 4.2, 1.7), K.ease(u)), (0, 0, 1.2), 28)

def s_l08():
    show("brew", fog=0)
def a_l08(u, t, f):   # ビール工場：自前の井戸と樽
    BREW.location = (0, 0, 0); sc.world.node_tree.nodes["Background"].inputs[1].default_value = .3
    bpy.data.lights.get("candleL").energy = 6
    cam.look(mix((-6, -4, 1.7), (-3, -4.5, 1.6), K.ease(u)), (-1, 3, .8), 26)

def s_l09():
    show("street", "pump", fog=.04, stream=True)
def a_l09(u, t, f):   # ポンプから水を汲む（水の筋）
    cam.look(mix((.8, -1.8, 1.0), (.6, -1.5, .9), K.ease(u)), (0, -.45, .6), 35)

def s_l10():
    show("street", "pump", fog=.02)
def a_l10(u, t, f):   # 空気ではなく、水：霧が晴れていくポンプ
    set_fog(.05 * (1 - K.ease(u)) + .005); FOG.data.materials[0].node_tree.nodes[FOG["vol"]].inputs["Density"].keyframe_insert("default_value", frame=f + 1)
    cam.look(mix((-3, -3, 1.3), (-2.4, -2.4, 1.25), K.ease(u)), (0, 0, 1.1), 28)

def s_l12():
    show("street", "pump", fog=.03)
def a_l12(u, t, f):   # 柄のないポンプ
    HANDLE.location = (0, 0, -50)
    cam.look(mix((0, -5, 1.4), (0, -4, 1.4), K.ease(u)), (0, 0, 1.2), 30)


SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l12"]}
ORDER = ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12"]
K.render_shots(HERE, SHOTS, ORDER, O, [cam.o, HANDLE, HAND, TABLE, CUP, BREW, CART] + PEOPLE)
