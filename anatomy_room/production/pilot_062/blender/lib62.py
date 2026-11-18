"""pilot_062 の 3D の部品（pilot_060 の lib60 の複製）（Blender Cycles）。金の延べ棒・金の玉・天秤・表彰台・机・世界地図・人形・スマホ・カード・お札。
質感：金は物理的な金属（Principled、金の反射色）に細かい傷のむら、机は Poly Haven の wood_table_001（CC0）、光は Poly Haven の HDRI（CC0）。
blkit（ext/blender）の setup・Cam・render_shots を使う。"""
import bpy, bmesh, math, os, sys, json
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "ext", "blender"))
import blkit as K  # noqa: E402

PH = os.path.join(HERE, "..", "assets", "ph")
PLAN = json.loads(open(os.path.join(HERE, "..", "assets", "plan.js"), encoding="utf-8").read()[len("window.PLAN = "):].rstrip().rstrip(";"))
BP = PLAN["beat"]["period"]


def clamp(v, a=0., b=1.):
    return max(a, min(b, v))


def ease(u):
    u = clamp(u); return u * u * (3 - 2 * u)


def eout(u):
    u = clamp(u); return 1 - (1 - u) ** 3


def spring(u):
    return 0. if u <= 0 else 1 - math.exp(-6 * u) * math.cos(10 * u)


def lerp(a, b, u):
    return a + (b - a) * u


# ---------------------------------------------------------------- 描画・光
def setup(samples=64):
    sc = K.setup(samples=samples, exposure=0.0)
    sc.view_settings.look = "AgX - Punchy"
    sc.cycles.max_bounces = 10; sc.cycles.glossy_bounces = 6; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0; sc.render.motion_blur_shutter = .45
    return sc


def world(hdri="brown_photostudio_02_2k.hdr", strength=1.0, rot=0.0, bg=0.0):
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree; n = nt.nodes; l = nt.links
    for x in list(n):
        n.remove(x)
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value[2] = rot
    env = n.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PH, "hdri", hdri))
    bgn = n.new("ShaderNodeBackground"); bgn.inputs["Strength"].default_value = strength
    dark = n.new("ShaderNodeBackground"); dark.inputs["Color"].default_value = (.012, .009, .007, 1); dark.inputs["Strength"].default_value = 1
    lp = n.new("ShaderNodeLightPath"); mix = n.new("ShaderNodeMixShader"); out = n.new("ShaderNodeOutputWorld")
    l.new(tc.outputs["Generated"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], env.inputs["Vector"]); l.new(env.outputs["Color"], bgn.inputs["Color"])
    # カメラから直接見える背景は暗く（映り込みと光は HDRI）
    l.new(lp.outputs["Is Camera Ray"], mix.inputs[0]); l.new(bgn.outputs[0], mix.inputs[1]); l.new(dark.outputs[0], mix.inputs[2]); l.new(mix.outputs[0], out.inputs["Surface"])
    if bg:
        mix.inputs[0].default_value = 0
    return w


def area_light(name, loc, at, size, energy, col=(1, .9, .78)):
    d = bpy.data.lights.new(name, "AREA"); d.size = size; d.energy = energy; d.color = col; o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o)
    o.location = loc; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (Vector(at) - Vector(loc)).to_track_quat("-Z", "Y"); return o


# ---------------------------------------------------------------- 質感
MATS = {}


def _img(path, non_color=False):
    im = bpy.data.images.load(path, check_existing=True)
    if non_color:
        im.colorspace_settings.name = "Non-Color"
    return im


def gold_mat(name="gold", rough=.13, tint=(1.0, .64, .22)):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; b = n["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*tint, 1); b.inputs["Metallic"].default_value = 1.0
    tc = n.new("ShaderNodeTexCoord")
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 18; nz.inputs["Detail"].default_value = 8
    ramp = n.new("ShaderNodeMapRange"); ramp.inputs["To Min"].default_value = rough * .7; ramp.inputs["To Max"].default_value = rough * 1.5
    l.new(tc.outputs["Object"], nz.inputs["Vector"]); l.new(nz.outputs["Fac"], ramp.inputs["Value"]); l.new(ramp.outputs["Result"], b.inputs["Roughness"])
    sc_ = n.new("ShaderNodeTexWave"); sc_.inputs["Scale"].default_value = 60; sc_.inputs["Distortion"].default_value = 30; sc_.inputs["Detail"].default_value = 4
    bump = n.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = .025; bump.inputs["Distance"].default_value = .002
    l.new(tc.outputs["Object"], sc_.inputs["Vector"]); l.new(sc_.outputs["Fac"], bump.inputs["Height"]); l.new(bump.outputs["Normal"], b.inputs["Normal"])
    MATS[name] = m; return m


def pbr_mat(name, folder, scale=1.0, tint=(1, 1, 1), rough_k=1.0, box_proj=False):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale); l.new(tc.outputs["Object" if box_proj else "UV"], mp.inputs["Vector"])
    d = n.new("ShaderNodeTexImage"); d.image = _img(os.path.join(PH, "tex", folder, "diff.jpg")); l.new(mp.outputs[0], d.inputs[0])
    mul = n.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1; mul.inputs[7].default_value = (*tint, 1)
    l.new(d.outputs["Color"], mul.inputs[6]); l.new(mul.outputs[2], b.inputs["Base Color"])
    r = n.new("ShaderNodeTexImage"); r.image = _img(os.path.join(PH, "tex", folder, "rough.jpg"), True); l.new(mp.outputs[0], r.inputs[0])
    rk = n.new("ShaderNodeMath"); rk.operation = "MULTIPLY"; rk.inputs[1].default_value = rough_k; l.new(r.outputs["Color"], rk.inputs[0]); l.new(rk.outputs[0], b.inputs["Roughness"])
    nm = n.new("ShaderNodeTexImage"); nm.image = _img(os.path.join(PH, "tex", folder, "nor.jpg"), True); l.new(mp.outputs[0], nm.inputs[0])
    nn = n.new("ShaderNodeNormalMap"); l.new(nm.outputs["Color"], nn.inputs["Color"]); l.new(nn.outputs["Normal"], b.inputs["Normal"])
    if box_proj:
        for x in n:
            if x.bl_idname == "ShaderNodeTexImage":
                x.projection = "BOX"; x.projection_blend = .2
    MATS[name] = m; return m


def plain(name, col, rough=.5, metal=0., coat=0.):
    if name in MATS:
        return MATS[name]
    m = K.mat(name, col, rough, metal); b = m.node_tree.nodes["Principled BSDF"]
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    MATS[name] = m; return m


def image_mat(name, path, rough=.6, emit=0.):
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; n = m.node_tree.nodes; l = m.node_tree.links; b = n["Principled BSDF"]
    t = n.new("ShaderNodeTexImage"); t.image = _img(path); t.extension = "CLIP"; l.new(t.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = rough
    if emit:
        l.new(t.outputs["Color"], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = emit
    MATS[name] = m; return m


# ---------------------------------------------------------------- 形
def _sc():
    c = bpy.data.collections.get("scene61")
    if c is None:
        c = bpy.data.collections.new("scene61"); bpy.context.scene.collection.children.link(c)
    return c


def link(o):
    _sc().objects.link(o); return o


def clear_scene():
    for o in list(_sc().objects):
        bpy.data.objects.remove(o, do_unlink=True)


def mesh_from_bm(name, bm, mats, smooth=True):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    return me


BAR_L, BAR_W, BAR_H = 1.0, .42, .2           # 延べ棒（下の面の長さ・幅・高さ。上の面は少し小さい）


def bar_mesh():
    if "barmesh" in bpy.data.meshes:
        return bpy.data.meshes["barmesh"]
    bm = bmesh.new(); L, Wd, Hh, k = BAR_L / 2, BAR_W / 2, BAR_H, .84
    v = [bm.verts.new(p) for p in [(-L, -Wd, 0), (L, -Wd, 0), (L, Wd, 0), (-L, Wd, 0), (-L * k, -Wd * k * .9, Hh), (L * k, -Wd * k * .9, Hh), (L * k, Wd * k * .9, Hh), (-L * k, Wd * k * .9, Hh)]]
    for f in [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        bm.faces.new([v[i] for i in f])
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=.022, segments=4, affect="EDGES", profile=.6)
    me = mesh_from_bm("barmesh", bm, [gold_mat()])
    for p in me.polygons:
        p.use_smooth = True
    return me


def bar(name, loc, rot_z=0.0, s=1.0, mat=None):
    o = bpy.data.objects.new(name, bar_mesh()); o.location = loc; o.rotation_euler = (0, 0, rot_z); o.scale = (s, s, s)
    if mat:
        o.material_slots[0].link = "OBJECT"; o.material_slots[0].material = mat
    return link(o)


def pile_slots(n):
    """n 本を積む位置（下の段から）：[(x, y, z, rz), ...]。段ごとに向きを 90° 変えて井桁に"""
    out = []; side = max(1, math.ceil(math.sqrt(n / 2.2))); r = 0
    while len(out) < n:
        rows = max(1, side - r // 2)
        for i in range(rows):
            for j in range(2):
                if len(out) >= n:
                    break
                if r % 2 == 0:
                    x = (i - (rows - 1) / 2) * (BAR_W * 1.05); y = (j - .5) * BAR_L * .98; rz = math.pi / 2
                else:
                    x = (j - .5) * BAR_L * .98; y = (i - (rows - 1) / 2) * (BAR_W * 1.05); rz = 0
                out.append((x, y, r * BAR_H * .99, rz))
        r += 1
    return out


def sphere(name, r, loc, m, seg=96):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; return link(o)


def box(name, size, loc, m, bevel=.01):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=bm.verts)
    if bevel:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bevel, segments=3, affect="EDGES")
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m], smooth=False)); o.location = loc; return link(o)


def cyl(name, r, h, loc, m, seg=96, bevel=.0):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    if bevel:
        bmesh.ops.bevel(bm, geom=[e for e in bm.edges if not e.is_manifold or abs(e.verts[0].co.z - e.verts[1].co.z) < 1e-6], offset=bevel, segments=3, affect="EDGES")
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; return link(o)


def desk(size=40, mat_name="wood_table_001", scale=6.0):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = mesh_from_bm("desk", bm, [pbr_mat("desk", mat_name, scale=scale, tint=(.7, .55, .45), rough_k=1.5)], smooth=False)
    me.uv_layers.new(); uv = me.uv_layers[0].data
    for i, lp in enumerate(me.loops):
        co = me.vertices[lp.vertex_index].co; uv[i].uv = (co.x / size + .5, co.y / size + .5)
    o = bpy.data.objects.new("desk", me); return link(o)


def cam_dof(cam, focus, fstop=2.8):
    d = cam.o.data; d.dof.use_dof = True; d.dof.focus_distance = max(.1, focus); d.dof.aperture_fstop = fstop


# ---------------------------------------------------------------- 小物
GEN = os.path.join(HERE, "..", "assets", "gen")


def plane(name, w, h, loc, m, rot=(0, 0, 0)):
    bm = bmesh.new(); bm.loops.layers.uv.new("UVMap"); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=.5, calc_uvs=True); bmesh.ops.scale(bm, vec=(w, h, 1), verts=bm.verts)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m], smooth=False)); o.location = loc; o.rotation_euler = rot; return link(o)


def parent(ch, pa):
    ch.parent = pa; return ch


def empty(name, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None); o.location = loc; return link(o)


def note_stack(name, key, loc, rz=0.0, s=1.0):
    """お札の束（帯つき）。親の空オブジェクトを返す"""
    root = empty(name, loc); root.rotation_euler = (0, 0, rz); root.scale = (s, s, s)
    paper = plain("paper_" + key, (.78, .8, .74), .7)
    parent(box(name + "_b", (1.56, .70, .12), (0, 0, .06), paper, bevel=.006), root)
    parent(plane(name + "_t", 1.54, .68, (0, 0, .1205), image_mat("note_" + key, os.path.join(GEN, f"note_{key}.jpg"), .55)), root)
    parent(box(name + "_band", (.16, .72, .125), (-.3, 0, .062), plain("band", (.92, .9, .84), .6), bevel=.004), root)
    return root


def card(name, loc, rot=(0, 0, 0), s=1.0):
    root = empty(name, loc); root.rotation_euler = rot; root.scale = (s, s, s)
    parent(box(name + "_b", (.856, .54, .012), (0, 0, .006), plain("cardbody", (.1, .18, .35), .25, coat=1.0), bevel=.004), root)
    parent(plane(name + "_t", .84, .525, (0, 0, .0125), image_mat("cardface", os.path.join(GEN, "card.jpg"), .22)), root)
    return root


def phone(name, loc, rot=(0, 0, 0), s=1.0):
    root = empty(name, loc); root.rotation_euler = rot; root.scale = (s, s, s)
    parent(box(name + "_b", (.74, 1.5, .07), (0, 0, .035), plain("phonebody", (.02, .02, .025), .2, metal=.3, coat=1.0), bevel=.03), root)
    parent(plane(name + "_s", .68, 1.40, (0, 0, .0712), image_mat("phonescreen", os.path.join(GEN, "phone.jpg"), .05, emit=1.2)), root)
    return root


def brass():
    return gold_mat("brass", rough=.28, tint=(.86, .62, .3))


def balance(name, loc, s=1.0):
    """天秤：root（置き場所）、pivot（腕の回転）、pans（2 つの皿の空オブジェクト）を返す。set_balance で傾ける"""
    root = empty(name, loc); root.scale = (s, s, s); m = brass()
    parent(cyl(name + "_base", .9, .12, (0, 0, .06), m), root); parent(cyl(name + "_base2", .55, .1, (0, 0, .17), m), root)
    parent(cyl(name + "_post", .07, 3.0, (0, 0, 1.7), m), root); parent(sphere(name + "_knob", .16, (0, 0, 3.25), m), root)
    pv = parent(empty(name + "_pivot", (0, 0, 3.1)), root)
    beam = parent(box(name + "_beam", (4.4, .14, .14), (0, 0, 0), m, bevel=.03), pv)
    pans = []
    for j, sx in enumerate((-1, 1)):
        hook = parent(empty(f"{name}_hook{j}", (sx * 2.15, 0, 0)), pv)
        pan = parent(empty(f"{name}_pan{j}", (sx * 2.15, 0, 1.25)), root)
        dish = parent(cyl(f"{name}_dish{j}", .95, .06, (0, 0, 0), m), pan)
        for k in range(3):
            a = k * 2 * math.pi / 3; p0 = Vector((math.cos(a) * .85, math.sin(a) * .85, .03)); p1 = Vector((0, 0, 1.82))
            d = p1 - p0; c = cyl(f"{name}_str{j}{k}", .012, d.length, (p0 + p1) / 2, plain("string", (.25, .2, .12), .6)); c.rotation_mode = "QUATERNION"; c.rotation_quaternion = d.to_track_quat("Z", "Y"); parent(c, pan)
        pans.append((hook, pan))
    return root, pv, pans


def set_balance(root, pv, pans, ang):
    """ang：左の皿が下がる向きが正"""
    pv.rotation_euler = (0, -ang, 0)
    for j, (hook, pan) in enumerate(pans):
        sx = -1 if j == 0 else 1; x = sx * 2.15 * math.cos(ang); z = 3.1 + sx * 2.15 * math.sin(ang)
        pan.location = (x, 0, z - 1.85)


def text_obj(name, s, loc, size, m, rot=(math.pi / 2, 0, 0), align="CENTER", extrude=.02, font="DelaGothicOne-Regular.ttf"):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = s; cu.size = size; cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = extrude; cu.bevel_depth = extrude * .3
    cu.font = bpy.data.fonts.load(os.path.join(HERE, "..", "assets", "fonts", font), check_existing=True)
    o = bpy.data.objects.new(name, cu); o.data.materials.append(m); o.location = loc; o.rotation_euler = rot; return link(o)


def podium(name, loc, w, h, num, wood):
    root = empty(name, loc); parent(box(name + "_b", (w, w * .8, h), (0, 0, h / 2), wood, bevel=.03), root)
    parent(text_obj(name + "_n", str(num), (0, -w * .4 - .005, h * .62), w * .45, gold_mat("goldtext", .2)), root); return root


def figure(name, loc, s=1.0, m=None):
    m = m or plain("ceramic", (.86, .84, .8), .35, coat=.5); root = empty(name, loc); root.scale = (s, s, s)
    parent(sphere(name + "_h", .17, (0, 0, 1.0), m, 48), root)
    b = sphere(name + "_b", .3, (0, 0, .4), m, 64); b.scale = (.85, .7, 1.35); parent(b, root); return root


def map_sheet(w=8.0, loc=(0, 0, .002)):
    h = w * 751 / 2048
    return plane("map", w, h, loc, image_mat("mapimg", os.path.join(HERE, "..", "assets", "photo", "map.jpg"), .75)), w, h


def map_xy(lon, lat, w, h, loc=(0, 0)):
    return (loc[0] + (lon + 180) / 360 * w - w / 2, loc[1] + h / 2 - (75 - lat) / 132 * h)
