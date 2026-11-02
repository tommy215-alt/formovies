# 置き場所：ext/blender（2026-11-02 の CG の試作。地球の画像は common/vendor/earth/earth_tex.js から取り出した earth_land.jpeg・earth_clouds.jpeg を同じフォルダに置いて使う〔いまの版は手続き的な地表なので未使用〕）
# 試作：035「高度31キロ」の決定的な場面を Blender（Cycles）で。素材は自前のモデル＋MakeHuman/MPFB（CC0）＋NASA Blue Marble（PD）。
# 使い方：blender -b -P strato.py -- OUTDIR [frames] [samples]
import bpy, math, sys, os
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]; NF = int(argv[1]) if len(argv) > 1 else 120; SAMP = int(argv[2]) if len(argv) > 2 else 96
HERE = os.path.dirname(os.path.abspath(__file__))
HUMAN = r"C:\Users\Duncan_Tommy21\formovies\anatomy_room\production\pilot_021\assets\human\man_stand.glb"

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for t in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = t; prefs.get_devices(); break
    except Exception:
        pass
for d in prefs.devices: d.use = d.type != "CPU"

sc.cycles.device = "CPU" if os.environ.get("BL_CPU") else "GPU"; sc.cycles.samples = SAMP; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.fps = 30; sc.frame_start, sc.frame_end = 1, NF
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"; sc.view_settings.exposure = -3.2
sc.render.image_settings.file_format = "PNG"; sc.render.filepath = os.path.join(OUT, "f_")
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5

def mat(name, col, rough=.5, metal=0., emit=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
    return m

# ---- 空：高度 31 km の多重散乱の空。太陽は低め（朝の成層圏）
w = bpy.data.worlds.new("sky"); sc.world = w; w.use_nodes = True; nt = w.node_tree
sky = nt.nodes.new("ShaderNodeTexSky"); sky.sky_type = "MULTIPLE_SCATTERING"; sky.altitude = 31000
sky.sun_elevation = math.radians(14); sky.sun_rotation = math.radians(205); sky.sun_size = math.radians(.545); sky.sun_intensity = 1.0
nt.links.new(sky.outputs[0], nt.nodes["Background"].inputs[0])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); sc.collection.objects.link(sun)
sun.data.energy = 9.0; sun.data.angle = math.radians(.545)
az, el = math.radians(205), math.radians(14)
d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))   # 空のテクスチャと同じ向き（+Y が北）
sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

# ---- 地球：半径 6371 km、カメラの 31 km 下が地表。地表の画像＋細かいノイズ、雲の層、薄い大気の層
R, H = 6371000.0, 31000.0
def sphere(name, r, seg=256):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=(0, 0, -(R + H)))
    o = bpy.context.object; o.name = name; bpy.ops.object.shade_smooth(); return o
LAT, LON = math.radians(33), math.radians(-106)
def face_up(o):   # 球の上の (緯度, 経度) の点をカメラの真下に回す（UV 球：経度 0 が -Y 側からの角度とみなす）
    p = Vector((math.cos(LAT) * math.cos(LON + math.pi / 2), math.cos(LAT) * math.sin(LON + math.pi / 2), math.sin(LAT)))
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = p.rotation_difference(Vector((0, 0, 1)))
earth = sphere("earth", R)
em = bpy.data.materials.new("earth"); em.use_nodes = True; n = em.node_tree.nodes; L = em.node_tree.links; b = n["Principled BSDF"]
# 地表は手続き的に（1 枚の衛星画像では 31 km からの細かさが出ない）：ニューメキシコの乾いた盆地と山並み。3 つの大きさのノイズを重ねる
tc = n.new("ShaderNodeTexCoord")
def noise(scale, detail=8, rough=.55):
    x = n.new("ShaderNodeTexNoise"); x.inputs["Scale"].default_value = scale; x.inputs["Detail"].default_value = detail
    x.inputs["Roughness"].default_value = rough; L.new(tc.outputs["Object"], x.inputs["Vector"]); return x
big, mid, fine = noise(1 / 60000, 4), noise(1 / 6000, 10), noise(1 / 600, 6)
mx = n.new("ShaderNodeMath"); mx.operation = "MULTIPLY_ADD"; L.new(mid.outputs["Fac"], mx.inputs[0]); mx.inputs[1].default_value = .6; L.new(big.outputs["Fac"], mx.inputs[2])
cr = n.new("ShaderNodeValToRGB"); L.new(mx.outputs[0], cr.inputs[0]); e = cr.color_ramp.elements
e[0].position, e[0].color = .38, (.62, .52, .38, 1); e[1].position, e[1].color = .9, (.10, .09, .08, 1)
for pos, col in [(.5, (.48, .38, .27, 1)), (.62, (.36, .30, .22, 1)), (.72, (.24, .22, .16, 1)), (.8, (.17, .17, .13, 1))]:
    el = e.new(pos); el.color = col
ov = n.new("ShaderNodeMix"); ov.data_type = "RGBA"; ov.blend_type = "OVERLAY"; ov.inputs[0].default_value = .3
wh = noise(1 / 25000, 3); wr = n.new("ShaderNodeMapRange"); wr.inputs[1].default_value = .66; wr.inputs[2].default_value = .7; L.new(wh.outputs["Fac"], wr.inputs[0])
ws = n.new("ShaderNodeMix"); ws.data_type = "RGBA"; L.new(wr.outputs[0], ws.inputs[0]); L.new(cr.outputs[0], ws.inputs[6]); ws.inputs[7].default_value = (.85, .84, .8, 1)
L.new(ws.outputs[2], ov.inputs[6]); L.new(fine.outputs["Color"], ov.inputs[7])
bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .4; bump.inputs["Distance"].default_value = 300
L.new(mx.outputs[0], bump.inputs["Height"]); L.new(bump.outputs[0], b.inputs["Normal"])
lw = n.new("ShaderNodeLayerWeight"); lw.inputs[0].default_value = .5
pw = n.new("ShaderNodeMath"); pw.operation = "POWER"; pw.inputs[1].default_value = 4; L.new(lw.outputs["Facing"], pw.inputs[0])
hz = n.new("ShaderNodeMix"); hz.data_type = "RGBA"; L.new(pw.outputs[0], hz.inputs[0]); L.new(ov.outputs[2], hz.inputs[6]); hz.inputs[7].default_value = (.5, .64, .88, 1)
L.new(hz.outputs[2], b.inputs["Base Color"])
eh = n.new("ShaderNodeMath"); eh.operation = "MULTIPLY"; eh.inputs[1].default_value = .35; L.new(pw.outputs[0], eh.inputs[0])
L.new(eh.outputs[0], b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (.4, .55, .9, 1)
b.inputs["Roughness"].default_value = .95; earth.data.materials.append(em)
# 積雲：高度 4 km の層に、まばらな雲（ノイズを切って白く）
clouds = sphere("clouds", R + 4000)
cm = bpy.data.materials.new("clouds"); cm.use_nodes = True; n = cm.node_tree.nodes; L = cm.node_tree.links; b = n["Principled BSDF"]
tc = n.new("ShaderNodeTexCoord")
c1 = n.new("ShaderNodeTexNoise"); c1.inputs["Scale"].default_value = 1 / 9000; c1.inputs["Detail"].default_value = 12; c1.inputs["Roughness"].default_value = .62
L.new(tc.outputs["Object"], c1.inputs["Vector"])
rg = n.new("ShaderNodeMapRange"); rg.inputs[1].default_value = .54; rg.inputs[2].default_value = .66; L.new(c1.outputs["Fac"], rg.inputs[0])
b.inputs["Base Color"].default_value = (1, 1, 1, 1); b.inputs["Roughness"].default_value = 1; L.new(rg.outputs[0], b.inputs["Alpha"])
clouds.data.materials.append(cm); clouds.visible_shadow = False

# ---- ゴンドラ（エクセルシオールの開いたゴンドラを模した再現。寸法はおおよそ）
alu = mat("alu", (.75, .76, .78), .32, 1.0); pad = mat("pad", (.82, .62, .18), .7); dark = mat("dark", (.05, .05, .06), .6)
def box(name, s, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot); o = bpy.context.object; o.name = name; o.scale = s
    bpy.ops.object.transform_apply(scale=True); bev = o.modifiers.new("b", "BEVEL"); bev.width = .012; bev.segments = 3
    o.data.materials.append(m); return o
def tube(a, b_, r, m):
    a, b_ = Vector(a), Vector(b_); v = b_ - a
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=v.length, location=(a + b_) / 2, vertices=24)
    o = bpy.context.object; o.rotation_euler = v.to_track_quat("Z", "Y").to_euler(); o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o
box("floor", (1.5, 1.3, .06), (0, 0, 0), alu)
box("step", (.5, .35, .04), (0, -.83, .02), alu)                       # 扉の前の小さな踏み台
for x in (-.73, .73):
    for y in (-.63, .63): tube((x, y, 0), (x, y, 1.75), .022, alu)
for z in (.9, 1.75):
    for (a, b_) in [((-.73, -.63), (.73, -.63)), ((-.73, .63), (.73, .63)), ((-.73, -.63), (-.73, .63)), ((.73, -.63), (.73, .63))]:
        if z == .9 and a[1] == -.63 and b_[1] == -.63: continue      # 扉の側は腰の高さの手すりなし
        tube((*a, z), (*b_, z), .018, alu)
box("back", (1.4, .05, 1.2), (0, .6, .75), pad)                         # 後ろの断熱パッド
for i, (x, z) in enumerate([(-.4, 1.2), (.05, 1.25), (.45, 1.1), (-.1, .7)]):
    box(f"inst{i}", (.28, .12, .2), (x, .52, z), dark)
box("seat", (.5, .4, .08), (-.35, .25, .45), pad); box("seatback", (.5, .06, .5), (-.35, .45, .72), pad)
white = mat("white", (.86, .86, .84), .45)
for i, x in enumerate((.3, .45, .6)): tube((x, .45, .05), (x, .45, .75), .07, white)
for x in (-.73, .73): box(f"side{x}", (.03, 1.2, .55), (x, 0, .3), pad)
for x in (-.73, .73):
    for y in (-.63, .63): tube((x, y, 1.75), (0, 0, 40), .006, dark)    # 気球へ吊る索
# ---- 気球の下端（上はフレームの外。半透明のポリエチレン）
bpy.ops.mesh.primitive_cone_add(vertices=96, radius1=.4, radius2=9, depth=34, location=(0, 0, 57)); bal = bpy.context.object
bm = bpy.data.materials.new("poly"); bm.use_nodes = True; bb = bm.node_tree.nodes["Principled BSDF"]
bb.inputs["Base Color"].default_value = (.95, .95, .97, 1); bb.inputs["Roughness"].default_value = .25
bb.inputs["Transmission Weight"].default_value = .6
bal.data.materials.append(bm); bpy.ops.object.shade_smooth()

# ---- 人（MakeHuman / MPFB、顔なし）：扉の前の踏み台に立ち、外を向く。白い与圧服のかわりに明るい生地
bpy.ops.import_scene.gltf(filepath=HUMAN)
hum = [o for o in bpy.context.selected_objects]
root = bpy.data.objects.new("man", None); sc.collection.objects.link(root)
for o in hum:
    if o.parent is None: o.parent = root
root.location = (0, -.78, .04)
suit = mat("suit", (.78, .74, .62), .75)
for o in hum:
    if o.type == "MESH":
        o.data.materials.clear(); o.data.materials.append(suit)
bpy.context.view_layer.update()
top = max((o.matrix_world @ Vector(c)).z for o in hum if o.type == "MESH" for c in o.bound_box)
bpy.ops.mesh.primitive_uv_sphere_add(radius=.2, location=(0, -.80, top - .12)); helm = bpy.context.object   # ヘルメット（顔は見せない）
helm.data.materials.append(mat("helm", (.85, .85, .82), .3)); bpy.ops.object.shade_smooth()
box("chute", (.4, .2, .5), (0, -.62, top - .55), mat("olive", (.3, .32, .2), .8))

# ---- カメラ：ゴンドラの中、後ろ上から人の背中ごしに地球の丸みを見る。ゆっくり寄りながら少し下へ
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 22; cam.data.sensor_width = 36; cam.data.clip_start = .05; cam.data.clip_end = 1e8
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 5.6
tgt = bpy.data.objects.new("tgt", None); sc.collection.objects.link(tgt)
c = cam.constraints.new("TRACK_TO"); c.target = tgt; c.track_axis = "TRACK_NEGATIVE_Z"; c.up_axis = "UP_Y"
cam.data.dof.focus_object = root
for f, loc, tl in [(1, (2.6, -4.6, 3.4), (-.1, -.5, .2)), (NF, (2.0, -3.7, 2.7), (-.05, -.6, .5))]:
    cam.location = loc; cam.keyframe_insert("location", frame=f); tgt.location = tl; tgt.keyframe_insert("location", frame=f)
for a in (cam.animation_data.action, tgt.animation_data.action):
    try:
        for fc in a.fcurves:
            for k in fc.keyframe_points: k.interpolation = "SINE"
    except Exception:
        pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "strato.blend"))
bpy.ops.render.render(animation=True)
