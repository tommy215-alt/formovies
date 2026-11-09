"""pilot_048 ポメラニアンの試作（毛並みの見え方の確認用。静止画 1 枚）。
blender -b -P pom_proto.py -- out.png [samples]
体はメタボールで作ってメッシュにし、パーティクルの毛（子の毛で増やす）と Principled Hair BSDF（メラニンの量で毛色）で描く。
寸法は本物のポメラニアン（体高 21 cm）の 1 倍で作り、最後に全体を k 倍する想定。
"""
import math
import sys

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "pom_proto.png"
SAMPLES = int(argv[1]) if len(argv) > 1 else 64

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
pr = bpy.context.preferences.addons["cycles"].preferences
for t in ("OPTIX", "CUDA"):
    try:
        pr.compute_device_type = t; pr.get_devices(); break
    except Exception:
        pass
for d in pr.devices:
    d.use = True
sc.cycles.device = "GPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 50
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Medium High Contrast"


def mat(name, col, rough=.5, spec=.5):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    return m


# ---------------------------------------------------------------- 体（メタボール）。座標は m、前が -Y、上が Z
mb = bpy.data.metaballs.new("pom_mb"); mb.resolution = .004; mb.render_resolution = .003; mb.threshold = .6
ob = bpy.data.objects.new("pom_body", mb); sc.collection.objects.link(ob)


def ball(p, r, kind="BALL", s=(1, 1, 1), neg=False):
    e = mb.elements.new(); e.type = kind; e.co = p; e.radius = r; e.use_negative = neg
    if kind == "ELLIPSOID":
        e.size_x, e.size_y, e.size_z = s


ball((0, .02, .14), .075, "ELLIPSOID", (.9, 1.25, .9))        # 胴
ball((0, -.055, .15), .07, "ELLIPSOID", (1, .9, 1))           # 胸
ball((0, -.09, .225), .058)                                    # 頭
ball((0, -.142, .212), .026, "ELLIPSOID", (.9, 1.2, .8))       # 鼻先（短い）
for sx in (-1, 1):
    ball((sx * .032, -.075, .292), .02, "ELLIPSOID", (.65, .45, 1.5))   # 耳（とがった小さな耳が毛から出る）
    for y, fx in ((-.05, .03), (.075, .032)):                      # 前足・後ろ足
        ball((sx * fx, y, .07), .02, "ELLIPSOID", (1, 1, 2.2))
        ball((sx * fx, y - .006, .012), .016, "ELLIPSOID", (1.1, 1.4, .7))  # 足先
ball((0, .1, .22), .03, "ELLIPSOID", (1, 1.6, .8))             # しっぽの付け根（背中に乗る）
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.convert(target="MESH")
body = bpy.context.active_object; body.name = "pom"
bpy.ops.object.shade_smooth()
skin = mat("skin", (.55, .32, .2), .6); body.data.materials.append(skin)

# ---------------------------------------------------------------- 毛
ps_mod = body.modifiers.new("fur", "PARTICLE_SYSTEM"); ps = ps_mod.particle_system; st = ps.settings
st.type = "HAIR"; st.count = 6000; st.hair_length = .05; st.use_advanced_hair = False
st.emit_from = "FACE"; st.use_emit_random = True
st.child_type = "INTERPOLATED"; st.child_percent = 40; st.rendered_child_count = 120
st.child_length = 1.0; st.child_length_threshold = .3
st.clump_factor = .35; st.clump_shape = -.2
st.roughness_1 = .012; st.roughness_1_size = 1.0; st.roughness_endpoint = .008; st.roughness_2 = .01
st.kink = "CURL"; st.kink_amplitude = .002; st.kink_frequency = 2.0
st.root_radius = .00006 / .00006; st.tip_radius = 0.0
st.radius_scale = .00009; st.use_close_tip = True
st.display_step = 4; st.render_step = 5
hair = bpy.data.materials.new("hair"); hair.use_nodes = True; nt = hair.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled"); out = nt.nodes.new("ShaderNodeOutputMaterial")
hb.parametrization = "MELANIN"
hb.inputs["Melanin"].default_value = .32
hb.inputs["Melanin Redness"].default_value = .72
hb.inputs["Roughness"].default_value = .38
hb.inputs["Radial Roughness"].default_value = .5
hb.inputs["Random Color"].default_value = .12
hb.inputs["Random Roughness"].default_value = .2
nt.links.new(hb.outputs[0], out.inputs[0])
body.data.materials.append(hair); st.material_slot = "hair"

# 顔は毛を短く：頂点グループで長さを変える（鼻先・目のまわりは短い、首まわりのえりは長い）
vg = body.vertex_groups.new(name="len")
for v in body.data.vertices:
    p = v.co
    face = max(0., 1 - math.dist((p.x, p.y, p.z), (0, -.145, .215)) / .045)   # 鼻先
    eye = max(0., 1 - math.dist((abs(p.x), p.y, p.z), (.03, -.125, .24)) / .02)
    leg = max(0., 1 - p.z / .05)
    ear = max(0., 1 - math.dist((abs(p.x), p.y, p.z), (.032, -.075, .3)) / .025)
    w = 1 - .9 * max(face, eye) - .6 * leg - .75 * ear
    ruff = max(0., 1 - math.dist((p.x, p.y, p.z), (0, -.07, .16)) / .1)        # 首のえり（ふさふさ）
    w = min(1.0, w * (1 + .5 * ruff))
    vg.add([v.index], max(.05, w), "REPLACE")
ps.vertex_group_length = "len"; ps.vertex_group_density = "len"

# ---------------------------------------------------------------- 目・鼻・舌
def sphere(name, loc, r, m, s=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=48, ring_count=24)
    o = bpy.context.active_object; o.name = name; o.scale = s; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


eye_m = mat("eye", (.008, .005, .004), .02)
nose_m = mat("nose", (.012, .01, .01), .3)
for sx in (-1, 1):
    sphere(f"eye{sx}", (sx * .027, -.142, .24), .0095, eye_m, (1, .8, 1))
sphere("nose", (0, -.172, .219), .0078, nose_m, (1.3, .9, .85))

# ---------------------------------------------------------------- 街：同じ縮尺（1/2381）の高層ビル群。0.084 m ≒ 200 m
import random
random.seed(3)
K = 2381.0
def bmat(name, wall, glass):   # 壁と窓（オブジェクト座標のレンガ模様で窓の格子）
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]
    geo = t.nodes.new("ShaderNodeNewGeometry"); br = t.nodes.new("ShaderNodeTexBrick")
    br.offset = 0; br.squash = 1; br.inputs["Scale"].default_value = K / 4   # 1 単位＝本物の 4 m
    br.inputs["Mortar Size"].default_value = .18; br.inputs["Brick Width"].default_value = .9; br.inputs["Row Height"].default_value = .9
    br.inputs["Color1"].default_value = (*glass, 1); br.inputs["Color2"].default_value = (*glass, 1); br.inputs["Mortar"].default_value = (*wall, 1)
    t.links.new(geo.outputs["Position"], br.inputs["Vector"])
    t.links.new(br.outputs["Color"], b.inputs["Base Color"]); t.links.new(br.outputs["Fac"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = .2
    return m


bmats = [bmat(f"bld{i}", w_, g_) for i, (w_, g_) in enumerate([((.42, .43, .45), (.08, .11, .15)), ((.55, .53, .5), (.12, .14, .17)), ((.3, .33, .37), (.05, .08, .12)), ((.62, .6, .56), (.15, .17, .2))])]
import bmesh  # noqa: E402
cm = bpy.data.meshes.new("city"); bm = bmesh.new()
for m_ in bmats:
    cm.materials.append(m_)
for i in range(4200):   # 1 つのメッシュにまとめる（オブジェクトを 1 つずつ作ると遅い）
    x, y = random.uniform(-1.4, 1.4), random.uniform(-2.4, 1.4)
    if math.hypot(x, y - .01) < .15:
        continue
    near_core = math.exp(-((x + .1) ** 2 + (y - .35) ** 2) / .2)
    h = (random.uniform(10, 45) + near_core * random.uniform(60, 230) * (random.random() < .5)) / K
    w = random.uniform(15, 45) / K; w2 = w * random.uniform(.7, 1.4)
    r_ = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(w, w2, h), verts=r_["verts"]); bmesh.ops.translate(bm, vec=(x, y, h / 2), verts=r_["verts"])
    mi = random.randrange(len(bmats))
    for f in {f for v in r_["verts"] for f in v.link_faces}:
        f.material_index = mi
bm.to_mesh(cm); bm.free(); city = bpy.data.objects.new("city", cm); sc.collection.objects.link(city)
bpy.ops.mesh.primitive_plane_add(size=6); gp = bpy.context.active_object; gp.data.materials.append(mat("ground", (.18, .19, .2), .8))
# 空気の霞（縮尺に合わせて濃く）
vol = bpy.data.materials.new("haze"); vol.use_nodes = True; vn = vol.node_tree
vs = vn.nodes.new("ShaderNodeVolumeScatter"); vs.inputs["Density"].default_value = .07; vs.inputs["Color"].default_value = (.75, .82, .95, 1)
vn.links.new(vs.outputs[0], vn.nodes["Material Output"].inputs["Volume"]); vn.nodes.remove(vn.nodes["Principled BSDF"])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -1, .6)); hz = bpy.context.active_object; hz.scale = (6, 8, 1.2); hz.data.materials.append(vol)
w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; wn = w.node_tree
sky = wn.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING" if hasattr(sky, "sky_type") else sky.sky_type
try:
    sky.sun_elevation = math.radians(25); sky.sun_rotation = math.radians(140)
except Exception:
    pass
wn.links.new(sky.outputs[0], wn.nodes["Background"].inputs[0]); wn.nodes["Background"].inputs[1].default_value = .35
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.6; sun.angle = math.radians(2)
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(150))
sc.view_settings.exposure = -.6
cam = bpy.data.cameras.new("cam"); cam.lens = 40; cam.clip_start = .001; co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
co.location = (.12, -1.5, .025)   # 地上 60 m ほどのビルの屋上から、3.5 km 先のポメラニアンを見上げる
d = Vector((0, -.05, .15)) - co.location; co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.dof.use_dof = False

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("saved", OUT)
