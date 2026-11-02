"""pilot_037（ケプケ）の 3D の場面（Blender、ext/blender/blkit.py）。当事者設計：前半は当事者の目線（POV）、後半は後ろ姿・遠景。
使い方：blender -b -P anatomy_room/production/pilot_037/blender/scene.py -- [ショット名 ...] [--still] [--samples N]
再現 CG：密林（幹・樹冠・下草・落ち葉・小川）、L-188 エレクトラを模した機内と翼（寸法はおおよそ）、川・小屋・船、人物（MakeHuman / MPFB、顔は映さない）。
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
R = random.Random(37)
HUM = os.path.join(HERE, "..", "..", "pilot_018", "assets", "human")


def nmat(name, c1, c2, scale=3.0, rough=.8, bump=.3, detail=6):
    """2 色をノイズで混ぜた質感（凹凸つき）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; L = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); no = n.new("ShaderNodeTexNoise"); no.inputs["Scale"].default_value = scale; no.inputs["Detail"].default_value = detail
    L.new(tc.outputs["Object"], no.inputs["Vector"])
    mx = n.new("ShaderNodeMix"); mx.data_type = "RGBA"; L.new(no.outputs["Fac"], mx.inputs[0]); mx.inputs[6].default_value = (*c1, 1); mx.inputs[7].default_value = (*c2, 1)
    L.new(mx.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; L.new(no.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], b.inputs["Normal"])
    return m


def leafmat(name, c1, c2):
    m = nmat(name, c1, c2, 6, .55, .5)
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Subsurface Weight"].default_value = .25
    return m


def group(name):
    g = bpy.data.objects.new(name, None); sc.collection.objects.link(g); return g


def inst(src, loc, rot=(0, 0, 0), scl=(1, 1, 1), parent=None):
    o = bpy.data.objects.new(src.name + "_i", src.data); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = rot; o.scale = scl; o.parent = parent; return o


def ico(name, r, m, sub=3, disp=.35, seed=0):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r); o = bpy.context.object; o.name = name
    tx = bpy.data.textures.new(name + "_t", "CLOUDS"); tx.noise_scale = r * .45
    d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = r * disp
    bpy.ops.object.modifier_apply(modifier="d"); bpy.ops.object.shade_smooth(); o.data.materials.append(m)
    sc.collection.objects.unlink(o) if False else None
    return o


# ---------------------------------------------------------------- 密林（原点のまわり 60 m 四方。小川は x=0 付近を -y 方向へ）
FOREST = group("forest")
bark = nmat("bark", (.16, .12, .09), (.3, .26, .2), 9, .9, .6)
leafA = leafmat("leafA", (.025, .07, .02), (.06, .14, .035)); leafB = leafmat("leafB", (.035, .09, .025), (.09, .17, .04))
litter = nmat("litter", (.06, .045, .025), (.12, .1, .05), 2.5, .95, .5)
bpy.ops.mesh.primitive_plane_add(size=160, location=(0, 0, 0)); gnd = bpy.context.object; gnd.data.materials.append(litter); gnd.parent = FOREST
sub = gnd.modifiers.new("s", "SUBSURF"); sub.subdivision_type = "SIMPLE"; sub.levels = sub.render_levels = 6
tx = bpy.data.textures.new("gt", "CLOUDS"); tx.noise_scale = 3; dd = gnd.modifiers.new("d", "DISPLACE"); dd.texture = tx; dd.strength = .5
def leafball(name, m, n=420, seed=0):
    """葉の面を n 枚、楕円体の中に散らした樹冠（半径 1）"""
    rr = random.Random(seed); me = bpy.data.meshes.new(name); bm = bmesh.new()
    for i in range(n):
        while True:
            c = Vector((rr.uniform(-1, 1), rr.uniform(-1, 1), rr.uniform(-1, 1)))
            if c.length <= 1:
                break
        c *= .55 + .45 * c.length ** .3
        rot = Euler((rr.uniform(0, 6), rr.uniform(0, 6), rr.uniform(0, 6))).to_matrix(); s_ = rr.uniform(.09, .16)
        vs = [bm.verts.new(c + rot @ Vector(v) * s_) for v in ((-1, -.45, 0), (1, -.45, 0), (1, .45, 0), (-1, .45, 0))]
        bm.faces.new(vs)
    bm.to_mesh(me); bm.free(); o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); me.materials.append(m); return o


import bmesh
crown = [leafball(f"crown{k}", leafA if k % 2 else leafB, 520, k) for k in range(4)]
bush = [leafball(f"bush{k}", leafB if k % 2 else leafA, 260, 10 + k) for k in range(3)]
for o in crown + bush:
    o.hide_render = True; o.location = (0, 0, -500)
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=1, vertices=14, location=(0, 0, -500)); trunk = bpy.context.object; trunk.data.materials.append(bark); trunk.hide_render = True


def creek_x(y):
    return 1.6 * math.sin(y * .09) + .8 * math.sin(y * .23 + 1)


for k in range(320):
    x, y = R.uniform(-70, 70), R.uniform(-70, 70)
    if abs(x - creek_x(y)) < 3.0:
        continue
    h = R.uniform(14, 34); r = R.uniform(.18, .7)
    t = inst(trunk, (x, y, h / 2), (R.uniform(-.06, .06), R.uniform(-.06, .06), 0), (r, r, h), FOREST)
    for j in range(R.randint(4, 8)):
        s = R.uniform(2.0, 4.5)
        inst(R.choice(crown), (x + R.uniform(-3, 3), y + R.uniform(-3, 3), h + R.uniform(-3, 2)), (R.random() * 6, R.random() * 6, R.random() * 6), (s, s, s * .7), FOREST)
for k in range(70):   # 目覚めた場所（x=0.6, y=-1）の真上を厚い樹冠で覆う
    a, d = R.uniform(0, 6.28), R.uniform(2, 16); h = R.uniform(14, 30); s_ = R.uniform(2.5, 5)
    inst(R.choice(crown), (.6 + d * math.cos(a), -1 + d * math.sin(a), h), (R.random() * 6, R.random() * 6, R.random() * 6), (s_, s_, s_ * .7), FOREST)
for k in range(900):
    x, y = R.uniform(-45, 45), R.uniform(-45, 45)
    if abs(x - creek_x(y)) < 1.4:
        continue
    s = R.uniform(.4, 1.6)
    inst(R.choice(bush), (x, y, s * .3), (R.random(), R.random(), R.random() * 6), (s, s, s * .6), FOREST)
for k in range(40):   # つる
    x, y = R.uniform(-30, 30), R.uniform(-30, 30); t = K.tube((x, y, 0), (x + R.uniform(-2, 2), y + R.uniform(-2, 2), R.uniform(12, 28)), .03, bark, FOREST, 8)
# 小川（幅 2.4 m の水の帯）
import bmesh
water = bpy.data.materials.new("water"); water.use_nodes = True; wn = water.node_tree.nodes; wl = water.node_tree.links; wb = wn["Principled BSDF"]
wb.inputs["Base Color"].default_value = (.12, .09, .05, 1); wb.inputs["Roughness"].default_value = .05; wb.inputs["Transmission Weight"].default_value = .1; wb.inputs["IOR"].default_value = 1.33
wtc = wn.new("ShaderNodeTexCoord"); wno = wn.new("ShaderNodeTexNoise"); wno.inputs["Scale"].default_value = 1.4; wno.inputs["Detail"].default_value = 8
wma = wn.new("ShaderNodeMapping"); wl.new(wtc.outputs["Object"], wma.inputs[0]); wl.new(wma.outputs[0], wno.inputs["Vector"])
wbp = wn.new("ShaderNodeBump"); wbp.inputs["Strength"].default_value = .25; wl.new(wno.outputs["Fac"], wbp.inputs["Height"]); wl.new(wbp.outputs[0], wb.inputs["Normal"])
FLOW = wma   # 流れ：毎コマ Location を動かす
me = bpy.data.meshes.new("creek"); bm = bmesh.new(); prev = None
for i in range(161):
    y = 70 - i * .875; cx = creek_x(y)
    a, b_ = bm.verts.new((cx - 1.2, y, .12)), bm.verts.new((cx + 1.2, y, .12))
    if prev:
        bm.faces.new((prev[0], prev[1], b_, a))
    prev = (a, b_)
bm.to_mesh(me); bm.free(); creek = bpy.data.objects.new("creek", me); sc.collection.objects.link(creek); me.materials.append(water); creek.parent = FOREST
mist = bpy.data.materials.new("mist"); mist.use_nodes = True; mn = mist.node_tree.nodes
for x in list(mn): mn.remove(x)
mo = mn.new("ShaderNodeOutputMaterial"); mv = mn.new("ShaderNodeVolumePrincipled"); mv.inputs["Color"].default_value = (.75, .8, .78, 1); mv.inputs["Density"].default_value = .012
mist.node_tree.links.new(mv.outputs[0], mo.inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 20)); mbox = bpy.context.object; mbox.scale = (150, 150, 40); mbox.data.materials.append(mist); mbox.parent = FOREST
SANDAL = K.box("sandal", (.1, .25, .02), (.25, -.5, .13), K.mat("sandal", (.92, .9, .86), .5), (0, 0, .4), parent=FOREST)
K.box("strap", (.1, .03, .03), (.25, -.45, .16), K.mat("strap", (.92, .9, .86), .5), (0, 0, .4), parent=FOREST)

# ---------------------------------------------------------------- 川・小屋・船（森の外、x=200 に置く）
RIVER = group("river")
bpy.ops.mesh.primitive_plane_add(size=1, location=(200, 0, .05)); rv = bpy.context.object; rv.scale = (14, 80, 1); rv.data.materials.append(water); rv.parent = RIVER
bpy.ops.mesh.primitive_plane_add(size=1, location=(200, 0, -.6)); rb = bpy.context.object; rb.scale = (14, 80, 1); rb.data.materials.append(K.mat("mud", (.25, .18, .1), .9)); rb.parent = RIVER
for sd in (-1, 1):
    bpy.ops.mesh.primitive_plane_add(size=1, location=(200 + sd * 47, 0, .15)); g2 = bpy.context.object; g2.scale = (80, 160, 1); g2.data.materials.append(litter); g2.parent = RIVER
for k in range(140):
    x, y = 200 + R.choice([-1, 1]) * R.uniform(8, 45), R.uniform(-40, 40); s_ = R.uniform(.5, 1.6)
    inst(R.choice(bush), (x, y, .15 + s_ * .3), (R.random(), R.random(), R.random() * 6), (s_, s_, s_ * .6), RIVER)
for k in range(60):
    x, y = 200 + R.choice([-1, 1]) * R.uniform(10, 40), R.uniform(-60, 60); h = R.uniform(14, 30); r = R.uniform(.2, .6)
    inst(trunk, (x, y, h / 2), (0, 0, 0), (r, r, h), RIVER)
    for j in range(4):
        s = R.uniform(3, 6); inst(R.choice(crown), (x + R.uniform(-3, 3), y + R.uniform(-3, 3), h + R.uniform(-2, 2)), (R.random() * 6, 0, R.random() * 6), (s, s, s * .7), RIVER)
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(193.5, -4, .2)); boat = bpy.context.object; boat.scale = (.7, 4.5, .45); boat.data.materials.append(K.mat("boatw", (.32, .22, .14), .7)); boat.parent = RIVER
wood = K.mat("hutw", (.35, .26, .16), .85); thatch = nmat("thatch", (.42, .34, .18), (.25, .2, .1), 14, .95, 1.0)
HX, HY = 183, -12
for x in (-2, 2):
    for y in (-2, 2):
        K.tube((HX + x, HY + y, 0), (HX + x, HY + y, 2.6), .1, wood, RIVER)
K.box("hutfloor", (4.4, 4.4, .12), (HX, HY, .6), wood, parent=RIVER)
bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=4.0, radius2=.1, depth=2.2, location=(HX, HY, 3.6), rotation=(0, 0, math.pi / 4)); roof = bpy.context.object; roof.data.materials.append(thatch); roof.parent = RIVER
K.box("motor", (.35, .3, .5), (HX - .8, HY + .6, .95), K.mat("motor", (.12, .12, .13), .4, .6), parent=RIVER)

# ---------------------------------------------------------------- 機内・翼（森の上空、z=5000 に置く。窓の外は暗い雲）
CAB = group("cabin"); CZ = 5000
cream = K.mat("cream", (.78, .74, .64), .6); fabric = nmat("fabric", (.18, .22, .32), (.12, .15, .24), 40, .9, .2)
bpy.ops.mesh.primitive_cylinder_add(radius=1.75, depth=20, vertices=48, location=(0, 0, CZ), rotation=(math.pi / 2, 0, 0)); fus = bpy.context.object
fus.data.materials.append(cream); fus.parent = CAB; sol = fus.modifiers.new("s", "SOLIDIFY"); sol.thickness = .08
for i in range(8):
    y = -8 + i * 1.6
    for xs in (-1.0, -.45, .45, 1.0):
        s = K.box(f"seat{i}{xs}", (.48, .5, .12), (xs, y, CZ - .95), fabric, parent=CAB); K.box(f"back{i}{xs}", (.48, .1, .75), (xs, y + .27, CZ - .55), fabric, parent=CAB)
    for xs in (-1.72, 1.72):   # 窓（外の暗さが見える穴のかわりに、暗い灰の板）
        K.box(f"win{i}{xs}", (.04, .32, .42), (xs * .99, y, CZ - .15), K.mat("winglass", (.05, .06, .07), .1), parent=CAB)
for xs in (-1.1, 1.1):
    K.box(f"bin{xs}", (.7, 16, .35), (xs, 0, CZ + .95), cream, parent=CAB)
BAGS = [K.box(f"bag{k}", (R.uniform(.25, .45), R.uniform(.2, .35), R.uniform(.15, .3)), (R.uniform(-1, 1), R.uniform(-4, 2), CZ + .7), K.mat(f"bagm{k}", (R.uniform(.3, .8), R.uniform(.2, .6), R.uniform(.2, .5)), .7), parent=CAB) for k in range(7)]
cl = bpy.data.lights.new("cablight", "AREA"); cl.energy = 400; cl.size = 3; cl.color = (1, .92, .8)
clo = bpy.data.objects.new("cablight", cl); sc.collection.objects.link(clo); clo.location = (0, -2, CZ + 1.3); clo.parent = CAB
MOM = None
try:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(os.path.join(HUM, "mother_sit.glb")))
    new = [o for o in bpy.data.objects if o not in before]; MOM = group("mom")
    for o in new:
        if o.parent is None:
            o.parent = MOM
    MOM.location = (-.45, -1.6, CZ - 1.75); MOM.rotation_euler = (0, 0, math.pi)
except Exception as e:
    print("mother_sit:", e)
# 翼とエンジン（左翼、機体の外）
WING = group("wing"); alum = K.mat("alum", (.6, .62, .65), .35, .9)
K.box("wingL", (14, 3.2, .35), (-9, 1, CZ - .9), alum, (0, -.05, 0), parent=WING)
for k, x in enumerate((-5.5, -10.5)):
    bpy.ops.mesh.primitive_cylinder_add(radius=.6, depth=4, vertices=32, location=(x, -.6, CZ - .7), rotation=(math.pi / 2, 0, 0)); nac = bpy.context.object; nac.data.materials.append(alum); nac.parent = WING
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.5, location=(x, -2.75, CZ - .7)); sp = bpy.context.object; sp.parent = WING
    if k == 1:
        glow = bpy.data.materials.new("glow"); glow.use_nodes = True; gb = glow.node_tree.nodes["Principled BSDF"]; gb.inputs["Emission Color"].default_value = (1, .75, .4, 1); gb.inputs["Emission Strength"].default_value = 0.0
        sp.data.materials.append(glow); GLOW = gb
        gl = bpy.data.lights.new("engl", "POINT"); gl.energy = 0; gl.color = (1, .7, .4); GL = bpy.data.objects.new("engl", gl); sc.collection.objects.link(GL); GL.location = (x, -3.4, CZ - .2); GL.parent = WING
    else:
        sp.data.materials.append(alum)
# 雲（暗い）と稲妻
storm = bpy.data.materials.new("storm"); storm.use_nodes = True; sn = storm.node_tree.nodes; sl = storm.node_tree.links
for x in list(sn): sn.remove(x)
so = sn.new("ShaderNodeOutputMaterial"); sv = sn.new("ShaderNodeVolumePrincipled"); sv.inputs["Color"].default_value = (.35, .37, .42, 1); sv.inputs["Density"].default_value = .02
sl.new(sv.outputs[0], so.inputs["Volume"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, CZ)); fog = bpy.context.object; fog.scale = (300, 300, 120); fog.data.materials.append(storm); fog.parent = CAB
BOLT = []
for k in range(2):
    pts = [Vector((-30 - 20 * k, 40 + 30 * k, CZ + 40))]
    for j in range(14):
        pts.append(pts[-1] + Vector((R.uniform(-4, 4), R.uniform(-2, 2), -6)))
    bm2 = bpy.data.materials.new(f"bolt{k}"); bm2.use_nodes = True; bb = bm2.node_tree.nodes["Principled BSDF"]; bb.inputs["Emission Color"].default_value = (.8, .85, 1, 1); bb.inputs["Emission Strength"].default_value = 0
    segs = [K.tube(a, b_, .25, bm2, CAB, 6) for a, b_ in zip(pts, pts[1:])]
    BOLT.append(bb)

# ---------------------------------------------------------------- 落下（森の上、高さ 2500 m → 250 m。地表は緑のノイズ、雲のちぎれ）
FALL = group("fall")
jungle = nmat("junglefar", (.03, .12, .03), (.09, .2, .06), .004, .9, .1, 10)
bpy.ops.mesh.primitive_plane_add(size=40000, location=(0, 0, -3000)); far = bpy.context.object; far.data.materials.append(jungle); far.parent = FALL
cloud = bpy.data.materials.new("cloudp"); cloud.use_nodes = True; cn = cloud.node_tree.nodes; cl_ = cloud.node_tree.links; cb = cn["Principled BSDF"]
cno = cn.new("ShaderNodeTexNoise"); cno.inputs["Scale"].default_value = 3; cno.inputs["Detail"].default_value = 10
cmr = cn.new("ShaderNodeMapRange"); cmr.inputs[1].default_value = .5; cmr.inputs[2].default_value = .7; cl_.new(cno.outputs["Fac"], cmr.inputs[0]); cl_.new(cmr.outputs[0], cb.inputs["Alpha"])
cb.inputs["Base Color"].default_value = (.85, .87, .9, 1)
for k in range(6):
    bpy.ops.mesh.primitive_plane_add(size=R.uniform(300, 600), location=(R.uniform(-600, 600), R.uniform(-600, 600), -3000 + R.uniform(400, 2200))); c = bpy.context.object; c.data.materials.append(cloud); c.parent = FALL

# ---------------------------------------------------------------- 人（後ろ姿）：白いワンピースの 17 歳
GIRL = None
try:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.abspath(os.path.join(HUM, "mother_walk.glb")))
    new = [o for o in bpy.data.objects if o not in before]; GIRL = group("girl")
    dress = K.mat("dress", (.85, .84, .8), .7)
    for o in new:
        if o.parent is None:
            o.parent = GIRL
        if o.type == "MESH" and ("dress" in o.name.lower() or "suit" in o.name.lower() or "cloth" in o.name.lower()):
            o.data.materials.clear(); o.data.materials.append(dress)
except Exception as e:
    print("mother_walk:", e)

# オープニングの A（その場で待つ）：密林に落ちた座席の列
BENCH = group("bench"); BENCH.parent = FOREST
for k in range(3):
    K.box(f"bseat{k}", (.5, .5, .14), (2.4 + k * .55, 2.3, .42), fabric, (0, .05, .04), parent=BENCH); K.box(f"bback{k}", (.5, .12, .7), (2.4 + k * .55, 2.58, .8), fabric, (-.25, .05, .04), parent=BENCH)
ALL = {"forest": FOREST, "river": RIVER, "cabin": CAB, "wing": WING, "fall": FALL}


def show(*names, girl=False, mom=False):
    for m in bpy.data.materials:      # 前のショットの質感の動き（稲妻・エンジンの光・水の流れ）を消す
        if m.node_tree:
            m.node_tree.animation_data_clear()
    for l in bpy.data.lights:
        l.animation_data_clear()
    GLOW.inputs["Emission Strength"].default_value = 0; bpy.data.lights["engl"].energy = 0
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    for b in BOLT:
        b.inputs["Emission Strength"].default_value = 0

    def hide(o, h):
        o.hide_render = h
        for c in o.children_recursive:
            c.hide_render = h
    for k, g in ALL.items():
        hide(g, k not in names)
    if GIRL:
        hide(GIRL, not girl)
    if MOM:
        hide(MOM, not mom)
    for o in crown + bush + [trunk]:
        o.hide_render = True


def day(rain=True, exp=-1.6):
    sky.set(0, 38, 150, .8 if rain else 4.0); sc.view_settings.exposure = exp - (.6 if rain else 0)
    sky.node.air_density = 1.0; sky.node.aerosol_density = 6.0 if rain else 1.0


def mix(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def bob(t, k=.03):   # 息づかい・歩きの揺れ
    return Vector((math.sin(t * 1.9) * k * .6, 0, math.sin(t * 2.8) * k))


FLOW_V = [0.0]
def flow(t):
    FLOW.inputs["Location"].default_value[1] = -t * .9
    FLOW.inputs["Location"].keyframe_insert("default_value", index=1, frame=int(round(t * 30)) + 1)


# ---------------------------------------------------------------- ショット
def s_l00():
    show("forest"); day()
def a_l00(u, t, f):   # 目を開けると木々の天井（オープニング）
    p = Vector((.6, -1.0, .45)) + bob(t, .02); cam.look(p, p + Vector((.3, .8, 6)), 18, roll=.25 * math.sin(t * .4)); flow(t)

def s_l01():
    show("cabin"); fog.hide_render = True; sky.set(0, -5, 150, 0); sc.view_settings.exposure = -1.0; sv.inputs["Density"].default_value = .02
    for b in BOLT: b.inputs["Emission Strength"].default_value = 0
def a_l01(u, t, f):   # 窓側の席から前を見る（となりに母の肩）
    p = Vector((-1.0, .05, CZ - .12)) + Vector((math.sin(t * 7) * .004, 0, math.sin(t * 9.3) * .006)); cam.look(p, (-.2, -8, CZ - .1), 24)

def s_l02():
    s_l01(); fog.hide_render = False   # 窓の外の稲妻が霧に光る
def a_l02(u, t, f):   # 激しい揺れ、荷物が落ちる、窓の外に稲妻
    k = .03 + .05 * u; p = Vector((-1.0, .05, CZ - .12)) + Vector((math.sin(t * 17) * k, math.sin(t * 13) * k * .5, math.sin(t * 21) * k * 1.4))
    cam.look(p, (-1.4, -6, CZ - .1 + math.sin(t * 15) * .3), 24, roll=math.sin(t * 11) * .06)
    for k2, bg in enumerate(BAGS):
        tt = max(0, t - .25 * k2); bg.location.z = max(CZ - .9, CZ + .7 - 4.9 * tt * tt); bg.rotation_euler = (tt * 3, tt * 2, 0)
    for j, b in enumerate(BOLT):
        on = 1 if (abs(t - (1.2 + j * 1.6)) < .12) else 0; b.inputs["Emission Strength"].default_value = 40 * on
        b.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)

def s_l03():
    show("cabin", "wing"); fus.hide_render = True
    for o in CAB.children:
        if o.name.startswith(("win", "seat", "back", "bin", "bag")): o.hide_render = True
    sky.set(0, 6, 200, .25); sc.view_settings.exposure = .3; sv.inputs["Density"].default_value = .008
    sc.world.node_tree.nodes["Background"].inputs[1].default_value = .025   # 嵐の雲の中：空は暗く、光るエンジンだけが目立つ
def a_l03(u, t, f):   # 窓の外：左の外側のエンジンが明るく光る
    p = Vector((-1.6, -1.2, CZ - .1)) + Vector((math.sin(t * 15) * .02, 0, math.sin(t * 19) * .03)); cam.look(p, (-10.5, -2.6, CZ - .8), 26)
    e = max(0, (u - .3) / .4); GLOW.inputs["Emission Strength"].default_value = 60 * e; GLOW.inputs["Emission Strength"].keyframe_insert("default_value", frame=f + 1)
    bpy.data.lights["engl"].energy = 3000 * e; bpy.data.lights["engl"].keyframe_insert("energy", frame=f + 1)

def s_l04():
    show("fall"); sky.set(2500, 30, 150, 5); sc.view_settings.exposure = -3.6
def a_l04(u, t, f):   # 座席ごと、逆さまに回りながら落ちる
    z = -3000 + 2500 - 2250 * u * u; cam.look((0, 0, z), (math.cos(t * 2.2) * 30, math.sin(t * 2.2) * 30, z - 60), 22, roll=t * 2.6)

def s_l05():
    show("forest"); day()
def a_l05(u, t, f):   # 目を覚ます：上を見る（ぼけは pov.js）
    p = Vector((.6, -1.0, .35)) + bob(t, .015); cam.look(p, p + Vector((.2, .5, 6)), 20, roll=.3); flow(t)

def s_l06():
    show("forest"); day()
def a_l06(u, t, f):   # 足もと：片方だけの白いサンダル
    p = Vector((.0, -.2, 1.0)) + bob(t, .015); cam.look(p, (.25, -.55, .1), 30); flow(t)

def s_l07():
    show("forest"); day()
def a_l07(u, t, f):   # 樹冠の上を飛ぶ捜索の飛行機（見えない）
    p = Vector((-.5, 3, 1.5)) + bob(t, .02); cam.look(p, p + Vector((-1 + 2 * u, 2, 8)), 22); flow(t)

def s_l08():
    show("forest"); day()
def a_l08(u, t, f):   # 小川：水の流れていく先
    p = Vector((creek_x(4) + .2, 4, 1.45)) + bob(t, .02); cam.look(p, (creek_x(-12), -12, .2), 26); flow(t)

def s_l09():
    show("forest", girl=True); day()
    if GIRL: GIRL.location = (creek_x(-2), -2, .1); GIRL.rotation_euler = (0, 0, 0)
def a_l09(u, t, f):
    e = K.ease(u); cam.look(mix((creek_x(4) + 1.2, 4.5, 1.7), (creek_x(3) + .6, 3, 1.5), e), (creek_x(-4), -4, 1.0), 32); flow(t)

def s_l10():
    show("forest", girl=True); day()
def a_l10(u, t, f):   # 水の中を歩く（後ろ姿が遠ざかる）
    if GIRL:
        y = -2 - 2.5 * u; GIRL.location = (creek_x(y), y, .1 + .02 * math.sin(t * 6))
    e = K.ease(u); cam.look(mix((creek_x(6) + 2.5, 6, 3.2), (creek_x(5) + 2, 5, 2.6), e), (creek_x(-6), -6, .6), 30); flow(t)

def s_l12():
    show("river"); day(False, -2.0)
def a_l12(u, t, f):   # 川べりの船と、小道の先の小屋
    e = K.ease(u); cam.look(mix((205, 22, 2.2), (202, 12, 1.9), e), (190, -8, 1.2), 30)

def s_l13():
    show("river"); day(False, -2.2); sky.set(0, 8, 100, 3)
def a_l13(u, t, f):   # 翌朝、小屋（男たちの声）
    e = K.ease(u); cam.look(mix((HX + 9, HY + 10, 1.8), (HX + 7, HY + 7, 1.7), e), (HX, HY, 1.4), 34)


def s_l00a():
    show("forest", mom=True); day()
    if MOM: MOM.location = (2.95, 2.25, 0.02); MOM.rotation_euler = (0, 0, 0)
def a_l00a(u, t, f):   # A：座席のそばで、救助を待つ（後ろ姿）
    e = K.ease(u); cam.look(mix((3.9, 5.6, 1.6), (3.6, 4.9, 1.45), e), (2.9, 1.2, .75), 30); flow(t)

def s_l00b():
    show("forest", girl=True); day()
def a_l00b(u, t, f):   # B：小川を歩いて進む（後ろ姿、低いカメラで水しぶきの高さ）
    if GIRL:
        y = 2 - 2.2 * u; GIRL.location = (creek_x(y), y, .1 + .02 * math.sin(t * 6))
    yc = 4.2 - 2 * u; cam.look((creek_x(yc) + .5, yc, .55 + .02 * math.sin(t * 5)), (creek_x(-6), -6, 1.0), 26); flow(t)

SHOTS = {k: (globals()["s_" + k], globals()["a_" + k]) for k in ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l12", "l13"]}
ORDER = ["l00", "l00a", "l00b", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08", "l09", "l10", "l11", "l12", "l13", "l14"]
anim = [cam.o] + BAGS + ([GIRL] if GIRL else [])
K.render_shots(HERE, SHOTS, ORDER, O, anim)
