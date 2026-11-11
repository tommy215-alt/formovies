"""pilot_051 の舞台：晴れた昼の田園と、平らでまっすぐな線路（+Y の向き、線路の中心は x=0）。
素材は Poly Haven（CC0、assets/ph/、python assets/polyhaven.py）：空の光（HDRI）・砂利・さびた鉄・コンクリート・草の質感、草花・低木・木の模型。
草花は Blender のパーティクル（コレクションを並べる）で散らす：動かない物は 1 度置くだけで、毎コマ作り直さない。
ほかの回でも使えるよう、場面に依存しない関数だけにする（2026-11-11 ユーザーの承認「舞台を使い回す」）。"""
from common import *

PH = os.path.join(HERE, "..", "assets", "ph")
GAUGE = 1.435              # 標準軌（新幹線）
RAIL_H = .174              # レールの高さ（60 kg レール）
SLEEPER = (2.4, .3, .2)    # 枕木（コンクリート）の長さ・幅・高さ
BALLAST_W, BALLAST_H = 3.6, .45
TOP = BALLAST_H + SLEEPER[2] + RAIL_H     # レールの上の面の高さ（地面から）


# ---------------------------------------------------------------- 空の光（HDRI）＋太陽
def world_hdri(name="kloofendal_43d_clear_puresky", strength=1.0, rot=0.0, sun=(52., 150.), sun_k=0.0, exposure=0.0):
    """HDRI で空と周りの光、くっきりした影は太陽のランプで（sun：高さ・方位の度、方位は K.Sky と同じ）"""
    w = sc.world; nt = w.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Rotation"].default_value = (0, 0, math.radians(rot))
    et = nt.nodes.new("ShaderNodeTexEnvironment"); et.image = bpy.data.images.load(os.path.join(PH, "hdri", f"{name}_4k.hdr"), check_existing=True)
    bg = nt.nodes.new("ShaderNodeBackground"); bg.inputs["Strength"].default_value = strength; out = nt.nodes.new("ShaderNodeOutputWorld")
    L = nt.links; L.new(tc.outputs["Generated"], mp.inputs["Vector"]); L.new(mp.outputs["Vector"], et.inputs["Vector"]); L.new(et.outputs["Color"], bg.inputs["Color"]); L.new(bg.outputs[0], out.inputs[0])
    sc.view_settings.exposure = exposure
    if sun_k <= 0:                 # 空だけの HDRI の太陽で影を作る（ランプを足すと光が二重になる）
        return None
    lt = bpy.data.lights.get("sun_lamp") or bpy.data.lights.new("sun_lamp", "SUN"); lt.energy = sun_k; lt.angle = math.radians(.6); lt.color = (1.0, .97, .92)
    so = bpy.data.objects.get("sun_lamp") or bpy.data.objects.new("sun_lamp", lt)
    if so.name not in sc.collection.objects:
        sc.collection.objects.link(so)
    el, az = math.radians(sun[0]), math.radians(sun[1]); d = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))
    so.rotation_mode = "QUATERNION"; so.rotation_quaternion = (-d).to_track_quat("-Z", "Y")
    return so


def haze(col=(.62, .7, .8), k=.55, d0=800., d1=12000.):
    """遠くを空の色に近づける（材質の中の霧。world_hdri のあとは common.set_haze ではなくこちら）"""
    for em, mr in HAZE:
        em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = k; mr.inputs[1].default_value = d0; mr.inputs[2].default_value = d1


# ---------------------------------------------------------------- 質感（PBR）
def pbr(tex, scale=1.0, disp=0.0, tint=None, rough_k=1.0, metal=None, name=None, spec=None):
    """assets/ph/tex/<tex>/ の 2k のマップで質感を作る。座標はオブジェクトの位置（m）× scale。disp：凹凸の強さ（m）"""
    key = name or f"pbr_{tex}_{scale}_{disp}"
    if key in MATS:
        return MATS[key]
    d = os.path.join(PH, "tex", tex); fs = {f.split(f"{tex}_")[1].rsplit("_2k", 1)[0]: os.path.join(d, f) for f in os.listdir(d)}
    m = bpy.data.materials.new(key); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    tc = t.nodes.new("ShaderNodeTexCoord"); mp = t.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(k, color=True):
        n = t.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(fs[k], check_existing=True)
        n.projection = "BOX"; n.projection_blend = .25
        if not color:
            n.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], n.inputs["Vector"]); return n
    col = img("Diffuse").outputs["Color"]
    if tint:
        mx = t.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"; mx.inputs[0].default_value = 1.0
        L.new(col, mx.inputs[6]); mx.inputs[7].default_value = (*tint, 1); col = mx.outputs[2]
    L.new(col, b.inputs["Base Color"])
    if "Rough" in fs or "arm" in fs:
        r = img("Rough" if "Rough" in fs else "arm", False); rc = r.outputs["Color"]
        if "Rough" not in fs:
            sp = t.nodes.new("ShaderNodeSeparateColor"); L.new(rc, sp.inputs[0]); rc = sp.outputs[1]
        mt = t.nodes.new("ShaderNodeMath"); mt.operation = "MULTIPLY"; mt.inputs[1].default_value = rough_k; L.new(rc, mt.inputs[0]); L.new(mt.outputs[0], b.inputs["Roughness"])
    if metal is not None:
        b.inputs["Metallic"].default_value = metal
    if spec is not None:
        b.inputs["Specular IOR Level"].default_value = spec
    if "nor_gl" in fs:
        nm = t.nodes.new("ShaderNodeNormalMap"); L.new(img("nor_gl", False).outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    if disp and "Displacement" in fs:
        dn = t.nodes.new("ShaderNodeDisplacement"); dn.inputs["Scale"].default_value = disp; dn.inputs["Midlevel"].default_value = .5
        L.new(img("Displacement", False).outputs["Color"], dn.inputs["Height"]); L.new(dn.outputs[0], t.nodes["Material Output"].inputs["Displacement"])
        m.displacement_method = "BOTH"
    add_haze(m, 300., 9000., .7); MATS[key] = m; return m


# ---------------------------------------------------------------- 模型（glTF）
_GLTF = {}
_HAZED = set()


def model(name):
    """assets/ph/models/<name>/ の glTF を読み込み、隠したコレクションに入れて返す（パーティクルや instance で並べる元）"""
    if name in _GLTF:
        return _GLTF[name]
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PH, "models", name, f"{name}_2k.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new("src_" + name); sc.collection.children.link(col)
    for o in new:
        for c_ in list(o.users_collection):
            c_.objects.unlink(o)
        col.objects.link(o); o.location = (0, 0, 0) if o.parent is None else o.location
        if o.type == "MESH":
            for ms in o.material_slots:
                if ms.material and ms.material.name not in _HAZED:
                    _HAZED.add(ms.material.name); add_haze(ms.material, 300., 9000., .7)
    col.hide_render = False; vl = bpy.context.view_layer.layer_collection.children[col.name]; vl.exclude = True
    _GLTF[name] = col; return col


def scatter(target, srcs, count, size=(.8, 1.3), seed=1, name=None, vgroup=None):
    """target（メッシュ）の表面に srcs（模型の名前）を count 個散らす。パーティクル（毛）を形として描く＝動かない"""
    col = bpy.data.collections.new("mix_" + (name or "_".join(srcs))); sc.collection.children.link(col)
    for s in srcs:
        for o in model(s).objects:
            if o.parent is None:
                col.objects.link(o)
    bpy.context.view_layer.layer_collection.children[col.name].exclude = True
    md = target.modifiers.new(name or "scatter", "PARTICLE_SYSTEM"); ps = md.particle_system; st = ps.settings
    st.type = "HAIR"; st.count = count; st.hair_length = 1.0; st.use_advanced_hair = True; st.emit_from = "FACE"; st.use_emit_random = True
    st.render_type = "COLLECTION"; st.instance_collection = col; st.use_collection_pick_random = True; st.particle_size = (size[0] + size[1]) / 2; st.size_random = (size[1] - size[0]) / max(size[1], 1e-6)
    st.use_rotations = True; st.rotation_mode = "GLOB_Z"; st.phase_factor_random = 2.0; st.use_rotation_instance = True
    ps.seed = seed
    if vgroup:
        ps.vertex_group_density = vgroup
    return ps


# ---------------------------------------------------------------- 区画にまとめて並べる（2026-11-12：速さ）
# 草や石を 1 株ずつ並べると数百万個になり、Cycles は毎コマそれを GPU に渡し直す（1 コマ 27 秒のうち 25 秒）。
# 小さな区画（数 m）の中で散らした物を 1 つの形にまとめ、区画を並べる（見た目は同じ、渡す数は数千）。
_PATCH = bpy.data.collections.get("patches")


def _patch_col():
    global _PATCH
    if _PATCH is None:
        _PATCH = bpy.data.collections.new("patches"); sc.collection.children.link(_PATCH); bpy.context.view_layer.layer_collection.children[_PATCH.name].exclude = True
    return _PATCH


def bake(base_obj, name):
    """base_obj（パーティクルで物を散らした面）の散らした物を本物の形にして 1 つにまとめる。面そのものは消す"""
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    bpy.context.view_layer.objects.active = base_obj; base_obj.select_set(True)
    before = set(bpy.data.objects); bpy.ops.object.duplicates_make_real(); new = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in list(bpy.context.selected_objects):
        o.select_set(False)
    for o in new:
        o.select_set(True)
    for o in new:                     # 型（石・草の元）と形を共有したままつなぐと、型そのものが書き換わる
        o.data = o.data.copy()
    log("bake", name, len(new), sum(len(o.data.vertices) for o in new))
    anchor = link(bpy.data.objects.new(name, bpy.data.meshes.new(name)))   # 原点・回転なしの空の形にまとめる（最初の 1 株を基準にすると区画が傾く）
    anchor.select_set(True); bpy.context.view_layer.objects.active = anchor; bpy.ops.object.join(); P = anchor
    for c_ in list(P.users_collection):
        c_.objects.unlink(P)
    _patch_col().objects.link(P)
    bpy.data.objects.remove(base_obj, do_unlink=True); return P


def grass_patches(size=2.0, dens=120., nvar=4, seed=3):
    """草はらの区画（size m 四方、原点が中心）を nvar 種類"""
    out = []
    for v in range(nvar):
        g = plane(f"gp_base{v}", -size / 2, size / 2, -size / 2, size / 2, 0.0, mat("gp_tmp", (.3, .3, .3)), 2, 2)
        A = size * size
        scatter(g, ["grass_medium_01", "grass_medium_02", "grass_bermuda_01"], int(A * dens), (1.0, 2.2), seed + v * 7, f"gp_g{v}")
        scatter(g, ["dandelion_01", "celandine_01"], max(1, int(A * dens * .02)), (.8, 1.3), seed + v * 7 + 1, f"gp_f{v}")
        out.append(bake(g, f"grass_patch{v}"))
    return out


def tile(name, patches, x0, x1, y0, y1, step, z=0.0, seed=1):
    """区画を格子に並べる（区画の種類と 90° ごとの向きはばらばら）。区画ごとに 1 つの頂点＝頂点で並べる仕組み（VERTS）"""
    rnd = np.random.default_rng(seed); groups = {}
    for x in np.arange(x0 + step / 2, x1, step):
        for y in np.arange(y0 + step / 2, y1, step):
            groups.setdefault((int(rnd.integers(0, len(patches))), int(rnd.integers(0, 4))), []).append((x, y, z))
    for (v, r), P in groups.items():
        me = bpy.data.meshes.new(f"{name}_{v}{r}"); me.from_pydata(P, [], []); host = link(bpy.data.objects.new(f"{name}_{v}{r}", me)); host.instance_type = "VERTS"
        ch_ = bpy.data.objects.new(f"{name}_{v}{r}_p", patches[v].data); link(ch_); ch_.parent = host; ch_.rotation_euler = (0, 0, r * math.pi / 2)


# ---------------------------------------------------------------- 地面・線路
def plane(name, x0, x1, y0, y1, z, m, nx=1, ny=1):
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=nx, y_segments=ny, size=.5)
    for v in bm.verts:
        v.co.x = x0 + (v.co.x + .5) * (x1 - x0); v.co.y = y0 + (v.co.y + .5) * (y1 - y0); v.co.z = z
    return mesh_obj(name, bm, [m])


def ballast(y0, y1, w=BALLAST_W, h=BALLAST_H):
    """砂利の土手（台形の断面）"""
    bm = bmesh.new(); prof = [(-w / 2 - h * 1.5, 0), (-w / 2, h), (w / 2, h), (w / 2 + h * 1.5, 0)]; rows = []
    prof = [(-w / 2 - h * 1.5, 0), (-w / 2 - h * .75, h * .5), (-w / 2, h), (0, h), (w / 2, h), (w / 2 + h * .75, h * .5), (w / 2 + h * 1.5, 0)]
    for y in np.linspace(y0, y1, int((y1 - y0) / 2) + 2):
        rows.append([bm.verts.new((x, y, z)) for x, z in prof])
    for a, b_ in zip(rows, rows[1:]):
        for i in range(len(prof) - 1):
            bm.faces.new((a[i], a[i + 1], b_[i + 1], b_[i]))
    o = mesh_obj("ballast", bm, [pbr("gravel_floor_02", 3.0, 0.0, tint=(.2, .2, .19), name="ballast_base")])
    # 表面に 3D の砕石を敷き詰める（1 m² に 550 個）：長さ 4 m の区間で散らして 1 つにまとめ、線路に沿って並べる
    SEG = 4.0; segs = []
    for v in range(3):
        sb = bmesh.new(); r0 = [sb.verts.new((x, -SEG / 2, z)) for x, z in prof]; r1 = [sb.verts.new((x, SEG / 2, z)) for x, z in prof]
        for i in range(len(prof) - 1):
            sb.faces.new((r0[i], r0[i + 1], r1[i + 1], r1[i]))
        so = mesh_obj(f"bseg{v}", sb, [mat("gp_tmp", (.3, .3, .3))]); _stones_on(so, (w + h * 3.6) * SEG, 9 + v); segs.append(bake(so, f"ballast_patch{v}"))
    rnd = np.random.default_rng(4); groups = {}
    for y in np.arange(y0 + SEG / 2, y1, SEG):
        groups.setdefault(int(rnd.integers(0, 3)), []).append((0, y, 0))
    for v, P in groups.items():
        me = bpy.data.meshes.new(f"ballast_t{v}"); me.from_pydata(P, [], []); host = link(bpy.data.objects.new(f"ballast_t{v}", me)); host.instance_type = "VERTS"
        ch_ = bpy.data.objects.new(f"ballast_t{v}_p", segs[v].data); link(ch_); ch_.parent = host
    return o


def _stones_on(o, A, seed):
    md = o.modifiers.new("stones", "PARTICLE_SYSTEM"); ps = md.particle_system; st = ps.settings
    st.type = "HAIR"; st.count = int(A * 550); st.hair_length = 1.0; st.use_advanced_hair = True; st.emit_from = "FACE"; st.use_emit_random = True; st.use_even_distribution = True
    st.render_type = "COLLECTION"; st.instance_collection = stones(); st.use_collection_pick_random = True; st.particle_size = 1.0; st.size_random = .45
    st.use_rotations = True; st.rotation_mode = "NOR"; st.phase_factor_random = 2.0; st.rotation_factor_random = 1.0; ps.seed = seed


def stones(nvar=8, seed=5):
    """バラストの石（角ばった砕石、3〜6 cm）の型を nvar 個：ゆがめた多面体。隠したコレクションに入れて返す"""
    if "src_stones" in bpy.data.collections:
        return bpy.data.collections["src_stones"]
    col = bpy.data.collections.new("src_stones"); sc.collection.children.link(col); rnd = np.random.default_rng(seed)
    gm = pbr("gravel_floor_02", 9.0, 0.0, tint=(.34, .33, .32), name="stone_m")
    for i in range(nvar):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=.022)
        for v in bm.verts:
            v.co = Vector((v.co.x * rnd.uniform(.7, 1.35), v.co.y * rnd.uniform(.7, 1.35), v.co.z * rnd.uniform(.55, 1.0))) * rnd.uniform(.85, 1.15)
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=.002, segments=1, affect="EDGES")
        me = bpy.data.meshes.new(f"stone{i}"); bm.to_mesh(me); bm.free(); me.materials.append(gm)
        o = bpy.data.objects.new(f"stone{i}", me); col.objects.link(o)
    bpy.context.view_layer.layer_collection.children[col.name].exclude = True
    return col


def _rail_profile():
    """60 kg レールの断面（頭・腹・底）を 2D の点で（x, z）"""
    hw, ww, bw = .065 / 2, .0165 / 2, .145 / 2
    return [(-bw, 0), (bw, 0), (bw, .012), (ww + .012, .03), (ww, .045), (ww, .125), (hw, .14), (hw, RAIL_H - .006), (hw - .006, RAIL_H), (-hw + .006, RAIL_H),
            (-hw, RAIL_H - .006), (-hw, .14), (-ww, .125), (-ww, .045), (-ww - .012, .03), (-bw, .012)]


def rails(y0, y1):
    rust = pbr("rusty_metal_02", 6.0, 0.0, tint=(.75, .6, .5), name="rail_rust", metal=.6)
    shine = mat("rail_top", (.55, .55, .56), .22, 1.0)
    prof = _rail_profile(); objs = []
    for s in (-1, 1):
        bm = bmesh.new(); xc = s * GAUGE / 2 + s * .0325; z0 = BALLAST_H + SLEEPER[2]; rows = []
        for y in (y0, y1):
            rows.append([bm.verts.new((xc + x, y, z0 + z)) for x, z in prof])
        n = len(prof)
        for i in range(n):
            f = bm.faces.new((rows[0][i], rows[0][(i + 1) % n], rows[1][(i + 1) % n], rows[1][i])); f.material_index = 1 if prof[i][1] >= RAIL_H - .007 and prof[(i + 1) % n][1] >= RAIL_H - .007 else 0
        bm.faces.new(rows[0][::-1]); bm.faces.new(rows[1])
        objs.append(mesh_obj(f"rail{s}", bm, [rust, shine]))
    return objs


def sleepers(y0, y1, gap=.6):
    con = pbr("brushed_concrete", 2.0, 0.0, tint=(.9, .9, .88))
    xf = [(0, y, BALLAST_H + SLEEPER[2] / 2, *SLEEPER, 0, 0, 0) for y in np.arange(y0, y1, gap)]
    o = instances("sleepers", CUBE_V, CUBE_F, xf, [con])
    bv = o.modifiers.new("bv", "BEVEL"); bv.width = .012; bv.segments = 2
    # 締結具（レールを押さえる金具）
    clip = [(s * GAUGE / 2 + s * .0325 + d * .085, y, BALLAST_H + SLEEPER[2] + .03, .05, .12, .06, 0, 0, 0) for y in np.arange(y0, y1, gap) for s in (-1, 1) for d in (-1, 1)]
    instances("clips", CUBE_V, CUBE_F, clip, [mat("clip", (.08, .08, .085), .45, .8)])
    return o


_GP = {}


def field(x0, x1, y0, y1, dens=120., seed=3, name="field"):
    """草はら：土と草の質感の地面に、草の株（1 m² あたり dens 株、2 m の区画を並べる）・低木を散らす"""
    g = plane(name, x0, x1, y0, y1, 0.0, pbr("sparse_grass", .5, .02, tint=(.8, .95, .7), spec=.15), nx=4, ny=8); A = abs(x1 - x0) * abs(y1 - y0)
    if dens not in _GP:
        _GP[dens] = grass_patches(2.0, dens, 4, seed)
    tile(name + "_grass", _GP[dens], x0, x1, y0, y1, 2.0, 0.0, seed)
    scatter(g, ["nettle_plant", "shrub_02", "shrub_04"], int(A * dens * .0015), (.5, 1.0), seed + 2, name + "_shrubs")
    return g


def trees(P, seed=4):
    rnd = np.random.default_rng(seed); src = [model(n) for n in ("island_tree_01", "island_tree_02", "tree_small_02")]
    for i, (x, y) in enumerate(P):
        col = src[int(rnd.integers(0, len(src)))]; e = bpy.data.objects.new(f"tree{i}", None); e.instance_type = "COLLECTION"; e.instance_collection = col
        e.location = (x, y, 0); e.rotation_euler = (0, 0, rnd.uniform(0, 6.28)); s = rnd.uniform(.8, 1.25); e.scale = (s, s, s); link(e)


def paddy_mat():
    """遠くの田んぼ：区画（30×20 m 前後）ごとに緑の濃さが違い、あぜ道が細く通る（手続き的、Poly Haven の草の質感を重ねる）"""
    if "paddy" in MATS:
        return MATS["paddy"]
    m = bpy.data.materials.new("paddy"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    tc = t.nodes.new("ShaderNodeTexCoord"); mp = t.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 32, 1 / 21, 1); L.new(tc.outputs["Object"], mp.inputs["Vector"])
    br = t.nodes.new("ShaderNodeTexBrick"); br.inputs["Scale"].default_value = 1.0; br.inputs["Mortar Size"].default_value = .025; br.inputs["Mortar Smooth"].default_value = .2
    br.offset = 0.0; br.inputs["Brick Width"].default_value = 1.0; br.inputs["Row Height"].default_value = 1.0; L.new(mp.outputs["Vector"], br.inputs["Vector"])
    br.inputs["Color1"].default_value = (.12, .3, .05, 1); br.inputs["Color2"].default_value = (.2, .38, .07, 1); br.inputs["Mortar"].default_value = (.32, .27, .18, 1)
    wn = t.nodes.new("ShaderNodeTexWhiteNoise"); fl = t.nodes.new("ShaderNodeVectorMath"); fl.operation = "FLOOR"; L.new(mp.outputs["Vector"], fl.inputs[0]); L.new(fl.outputs[0], wn.inputs["Vector"])
    ramp = t.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (.035, .11, .015, 1); ramp.color_ramp.elements[1].color = (.12, .22, .03, 1); L.new(wn.outputs["Value"], ramp.inputs[0])
    gx = pbr("grass_path_2", .12, 0.0, name="_tmp_grass")    # 草の質感の明暗だけを借りる
    img = t.nodes.new("ShaderNodeTexImage"); img.image = next(n.image for n in gx.node_tree.nodes if n.type == "TEX_IMAGE"); mp2 = t.nodes.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (.15, .15, .15)
    L.new(tc.outputs["Object"], mp2.inputs["Vector"]); L.new(mp2.outputs["Vector"], img.inputs["Vector"])
    m1 = t.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = .6; L.new(ramp.outputs["Color"], m1.inputs[6]); L.new(img.outputs["Color"], m1.inputs[7])
    m2 = t.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.inputs[7].default_value = (.32, .27, .18, 1); L.new(br.outputs["Fac"], m2.inputs[0]); L.new(m1.outputs[2], m2.inputs[6])
    L.new(m2.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 1.0; b.inputs["Specular IOR Level"].default_value = .08   # 草地は空を映さない（真横から見ると白くなる）
    add_haze(m, 300., 9000., .7); MATS["paddy"] = m; return m


def hills(r0=1800., r1=4200., seed=6):
    """遠くの山並み（線路を囲む輪、高さ 80〜320 m、木におおわれた暗い緑）"""
    rnd = np.random.default_rng(seed); bm = bmesh.new(); na, nr = 220, 6; ph = rnd.uniform(0, 6.28, 6); rows = []
    for j in range(nr):
        r = r0 + (r1 - r0) * j / (nr - 1); row = []
        for i in range(na):
            a = 2 * math.pi * i / na; hgt = sum(math.sin(a * k + ph[k - 1]) / k for k in range(1, 7)); hgt = (110 + 70 * hgt) * math.sin(math.pi * j / (nr - 1)) ** .7 * (1 + .6 * j / nr)
            row.append(bm.verts.new((r * math.sin(a), r * math.cos(a), max(0., hgt) - 5)))
        rows.append(row)
    for j in range(nr - 1):
        for i in range(na):
            bm.faces.new((rows[j][i], rows[j][(i + 1) % na], rows[j + 1][(i + 1) % na], rows[j + 1][i]))
    m = pbr("forest_ground_04", .02, 0.0, tint=(.12, .2, .09), name="hill_m", spec=.1)
    o = mesh_obj("hills", bm, [m]); sd = o.modifiers.new("sd", "SUBSURF"); sd.levels = 2; sd.render_levels = 2
    for p_ in o.data.polygons:
        p_.use_smooth = True
    return o


def track_scene(y0=-150., y1=250., side=40., far=True, seed=3):
    """線路と両側の草はら。far：遠くの田んぼ（質感だけの大きな地面）と、ところどころの木"""
    ballast(y0, y1); sleepers(y0, y1); rails(y0, y1)
    e = BALLAST_W / 2 + BALLAST_H * 1.5
    for s in (-1, 1):
        a, b_ = s * e, s * min(side, e + 14)
        field(min(a, b_), max(a, b_), y0, y1, 120., seed + (s > 0) * 10, f"near{s}")
        if side > e + 14:
            a, b_ = s * (e + 14), s * side
            field(min(a, b_), max(a, b_), y0, y1, 25., seed + 20 + (s > 0) * 10, f"mid{s}")
    if far:
        plane("far_field", -5000, 5000, -5000, 5000, -.03, paddy_mat()); hills()
        rnd = np.random.default_rng(seed + 7); P = []
        for _ in range(60):                       # 木立（集落の屋敷林・鎮守の森のような固まり）
            cx, cy = rnd.choice([-1, 1]) * rnd.uniform(side + 20, 900), rnd.uniform(y0 - 300, y1 + 1500)
            P += [(cx + rnd.normal(0, 14), cy + rnd.normal(0, 14)) for _ in range(int(rnd.integers(10, 30)))]
        P += [(rnd.choice([-1, 1]) * rnd.uniform(side + 3, 120), rnd.uniform(y0, y1 + 300)) for _ in range(25)]
        trees(P, seed)
