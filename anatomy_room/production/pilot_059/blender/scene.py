"""pilot_059「日本アルプスが、ヒマラヤ山脈になったら？」の 3D（Blender Cycles）。もしも設計の既定（templates/DESIGN_MODES.md）。
山は実際の標高データ（AWS Terrain Tiles、SRTM など USGS のパブリックドメイン、assets/get_dem.py）を 1 単位＝1 m で立体にする。
質感は Poly Haven（CC0）の aerial_rocks_02・aerial_grass_rock と、標高・傾きで積もらせる雪。雲は透ける板を重ねた雲海。
地図（l01）は NASA の衛星画像（PD）と、標高データから作ったヒマラヤの形（assets/make_map.py）。旅客機は Sketchfab "Medium haul plane (low poly)"（reeledzin、CC BY、ロゴなし）。
東京から見る絵（l04）は地球の丸み（d²／2R）だけ山を下げる。閃光なし。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city

NAMES = ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08"]
SIMO = PLAN["sim"]
S = {}
AS = os.path.join(HERE, "..", "assets")
PH = os.path.join(HERE, "..", "..", "pilot_051", "assets", "ph", "tex")
RE = 6_371_000.0


def imp(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith("Icosphere")]:
        new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    return new


# ---------------------------------------------------------------- 標高データ → 地形
def dem(name):
    H = np.load(os.path.join(AS, "dem", f"{name}.npy")).astype(np.float64); M = json.load(open(os.path.join(AS, "dem", f"{name}.json"), encoding="utf-8"))
    latc = sum(M["lat"]) / 2; w = (M["lon"][1] - M["lon"][0]) * 111_320 * math.cos(math.radians(latc)); h = (M["lat"][1] - M["lat"][0]) * 110_540
    return np.maximum(H, 0.0), w, h


def terrain(name, mat_, step=2, at=(0, 0, 0), peak_at_origin=True, taper=9000.0, curv=None, zk=1.0, crop=None):
    """標高データの格子。peak_at_origin：一番高い点を at に。taper：ふちを m かけて 0 に下げる（切り口の壁を見せない）。curv：(x, y) から地球の丸みで下げる"""
    H, w, h = dem(name)
    if crop:                                                                    # 一番高い所のまわり ±crop m だけ
        j, i = np.unravel_index(np.argmax(H), H.shape); ry, rx = int(crop / h * H.shape[0]), int(crop / w * H.shape[1])
        j0, j1, i0, i1 = max(0, j - ry), min(H.shape[0], j + ry), max(0, i - rx), min(H.shape[1], i + rx); w = w * (i1 - i0) / H.shape[1]; h = h * (j1 - j0) / H.shape[0]; H = H[j0:j1, i0:i1]
    H = H[::step, ::step]; ny, nx = H.shape
    xs = np.linspace(-w / 2, w / 2, nx); ys = np.linspace(h / 2, -h / 2, ny); X, Y = np.meshgrid(xs, ys)
    if peak_at_origin:
        j, i = np.unravel_index(np.argmax(H), H.shape); X = X - xs[i]; Y = Y - ys[j]
    e = np.minimum.reduce([X - X.min(), X.max() - X, Y - Y.min(), Y.max() - Y]); k = np.clip(e / taper, 0, 1); k = k * k * (3 - 2 * k)
    Z = H * k * zk
    X = X + at[0]; Y = Y + at[1]; Z = Z + at[2]
    if curv is not None:
        Z = Z - ((X - curv[0]) ** 2 + (Y - curv[1]) ** 2) / (2 * RE)
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx - 1, y_subdivisions=ny - 1, size=1.0); o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = name
    co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ix = np.round((co[:, 0] + .5) * (nx - 1)).astype(int); iy = np.round((.5 - co[:, 1]) * (ny - 1)).astype(int)
    co[:, 0] = X[iy, ix]; co[:, 1] = Y[iy, ix]; co[:, 2] = Z[iy, ix]
    o.data.vertices.foreach_set("co", co.reshape(-1)); o.data.update()
    o.data.polygons.foreach_set("use_smooth", np.ones(len(o.data.polygons), bool)); o.data.materials.append(mat_)
    S.setdefault("terr", {})[name] = (float(Z.max()), X, Y, Z); return o


def img(path, cs="sRGB"):
    im = bpy.data.images.load(path, check_existing=True); im.colorspace_settings.name = cs; return im


def mountain_mat(name="mtn", snowline=5600.0, green=-1.0, k_snow=1.0):
    """岩（aerial_rocks_02）、低い所は草と岩（aerial_grass_rock）、高くて傾きのゆるい所は雪"""
    if name in MATS:
        return MATS[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; n = t.nodes; L = t.links; b = n["Principled BSDF"]
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / 650.,) * 3; L.new(tc.outputs["Object"], mp.inputs["Vector"])
    def tex(nm, kind, cs="sRGB"):
        x = n.new("ShaderNodeTexImage"); x.image = img(os.path.join(PH, nm, f"{nm}_{kind}_2k.jpg"), cs); x.projection = "BOX"; x.projection_blend = .3; L.new(mp.outputs[0], x.inputs[0]); return x
    rock = tex("aerial_rocks_02", "diff"); grass = tex("aerial_grass_rock", "diff"); nrm = tex("aerial_rocks_02", "nor_gl", "Non-Color")
    g = n.new("ShaderNodeNewGeometry"); sp = n.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sp.inputs[0]); sn = n.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Normal"], sn.inputs[0])
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1 / 600.; nz.inputs["Detail"].default_value = 8; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    zn = n.new("ShaderNodeMath"); zn.operation = "MULTIPLY_ADD"; L.new(nz.outputs["Fac"], zn.inputs[0]); zn.inputs[1].default_value = 900.0; L.new(sp.outputs["Z"], zn.inputs[2])
    sh = n.new("ShaderNodeMapRange"); sh.inputs[1].default_value = snowline - 700; sh.inputs[2].default_value = snowline + 300; L.new(zn.outputs[0], sh.inputs[0])          # 高さ
    sl = n.new("ShaderNodeMapRange"); sl.inputs[1].default_value = .72; sl.inputs[2].default_value = .88; L.new(sn.outputs["Z"], sl.inputs[0])                          # 傾き（急な崖は岩のまま）
    sw = n.new("ShaderNodeMath"); sw.operation = "MULTIPLY"; sw.use_clamp = True; L.new(sh.outputs[0], sw.inputs[0]); L.new(sl.outputs[0], sw.inputs[1])
    sk = n.new("ShaderNodeMath"); sk.operation = "MULTIPLY"; sk.use_clamp = True; L.new(sw.outputs[0], sk.inputs[0]); sk.inputs[1].default_value = k_snow
    gr = n.new("ShaderNodeMapRange"); gr.inputs[1].default_value = green + 400; gr.inputs[2].default_value = green - 400; L.new(zn.outputs[0], gr.inputs[0])            # 低い所は草
    hs = n.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = .35; hs.inputs["Value"].default_value = .8; L.new(rock.outputs["Color"], hs.inputs["Color"])    # 灰色がかった岩
    rk = n.new("ShaderNodeMix"); rk.data_type = "RGBA"; L.new(gr.outputs[0], rk.inputs[0]); L.new(hs.outputs["Color"], rk.inputs[6]); L.new(grass.outputs["Color"], rk.inputs[7])
    dk = n.new("ShaderNodeMix"); dk.data_type = "RGBA"; dk.blend_type = "MULTIPLY"; dk.inputs[0].default_value = .55; L.new(rk.outputs[2], dk.inputs[6]); dk.inputs[7].default_value = (.42, .4, .4, 1)
    sc_ = n.new("ShaderNodeMix"); sc_.data_type = "RGBA"; L.new(sk.outputs[0], sc_.inputs[0]); L.new(dk.outputs[2], sc_.inputs[6]); sc_.inputs[7].default_value = (.86, .9, .96, 1)
    L.new(sc_.outputs[2], b.inputs["Base Color"])
    rr = n.new("ShaderNodeMapRange"); rr.inputs[3].default_value = .9; rr.inputs[4].default_value = .45; L.new(sk.outputs[0], rr.inputs[0]); L.new(rr.outputs[0], b.inputs["Roughness"])
    nm = n.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = .8; L.new(nrm.outputs["Color"], nm.inputs["Color"]); L.new(nm.outputs[0], b.inputs["Normal"])
    b.inputs["Specular IOR Level"].default_value = .3
    add_haze(m); MATS[name] = m; return m


# ---------------------------------------------------------------- 雲（透ける板を重ねる）
def clouds(z0, z1, n=6, size=60000.0, center=(0, 0), scale=1 / 2500., dens=.9, mask_y=None, name="cloud", col=(1, 1, 1)):
    S.setdefault("clouds", [])
    for i in range(n):
        m = bpy.data.materials.new(f"{name}{i}"); m.use_nodes = True; t = m.node_tree; nd = t.nodes; L = t.links
        for x in list(nd):
            if x.type != "OUTPUT_MATERIAL":
                nd.remove(x)
        tc = nd.new("ShaderNodeTexCoord"); mp = nd.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (scale, scale, scale); mp.inputs["Location"].default_value = (i * 3.1, i * 1.7, i * .9)
        L.new(tc.outputs["Object"], mp.inputs["Vector"]); nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Detail"].default_value = 10; nz.inputs["Roughness"].default_value = .62; L.new(mp.outputs[0], nz.inputs["Vector"])
        q = i / max(1, n - 1); cr = nd.new("ShaderNodeMapRange"); cr.inputs[1].default_value = .52 + .1 * q; cr.inputs[2].default_value = .7 + .06 * q; L.new(nz.outputs["Fac"], cr.inputs[0])
        a = cr.outputs[0]
        if mask_y is not None:                                                  # 片側だけ（風上に積み上がる雲）
            sp = nd.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sp.inputs[0]); my = nd.new("ShaderNodeMapRange"); my.inputs[1].default_value = mask_y[0]; my.inputs[2].default_value = mask_y[1]
            L.new(sp.outputs["Y"], my.inputs[0]); mm = nd.new("ShaderNodeMath"); mm.operation = "MULTIPLY"; L.new(a, mm.inputs[0]); L.new(my.outputs[0], mm.inputs[1]); a = mm.outputs[0]
        dv = nd.new("ShaderNodeMath"); dv.operation = "MULTIPLY"; dv.use_clamp = True; L.new(a, dv.inputs[0]); dv.inputs[1].default_value = dens
        tr = nd.new("ShaderNodeBsdfTransparent"); df = nd.new("ShaderNodeBsdfPrincipled"); df.inputs["Base Color"].default_value = (*col, 1); df.inputs["Roughness"].default_value = 1.0
        df.inputs["Subsurface Weight"].default_value = .0; df.inputs["Specular IOR Level"].default_value = 0.0
        bp = nd.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 1.0; bp.inputs["Distance"].default_value = 400.0; L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs[0], df.inputs["Normal"])
        mx = nd.new("ShaderNodeMixShader"); L.new(dv.outputs[0], mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(df.outputs[0], mx.inputs[2])
        L.new(mx.outputs[0], nd["Material Output"].inputs["Surface"]); m.cycles.emission_sampling = "NONE"
        bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2); o = mesh_obj(f"{name}{i}", bm, [m])
        o.location = (center[0], center[1], z0 + (z1 - z0) * q); o.visible_shadow = i % 2 == 0; S["clouds"].append((o, mp))
    sc.cycles.transparent_max_bounces = 24


def cloud_volume(loc, size, dens):
    """風上に積み上がる雲（体積）：ノイズで濃淡、上と端はうすく"""
    m = bpy.data.materials.new("cvol"); m.use_nodes = True; t = m.node_tree; nd = t.nodes; L = t.links
    for x in list(nd):
        if x.type != "OUTPUT_MATERIAL":
            nd.remove(x)
    tc = nd.new("ShaderNodeTexCoord"); nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 8; L.new(tc.outputs["Generated"], nz.inputs["Vector"])
    cr = nd.new("ShaderNodeMapRange"); cr.inputs[1].default_value = .45; cr.inputs[2].default_value = .7; L.new(nz.outputs["Fac"], cr.inputs[0])
    sp = nd.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0])
    gz_ = nd.new("ShaderNodeMapRange"); gz_.inputs[1].default_value = 1.0; gz_.inputs[2].default_value = .55; L.new(sp.outputs["Z"], gz_.inputs[0])           # 上ほどうすい
    gy = nd.new("ShaderNodeMapRange"); gy.inputs[1].default_value = 1.0; gy.inputs[2].default_value = .7; L.new(sp.outputs["Y"], gy.inputs[0])            # 山側（+Y）の端は壁に沿って
    m1 = nd.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; L.new(cr.outputs[0], m1.inputs[0]); L.new(gz_.outputs[0], m1.inputs[1])
    m2 = nd.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; L.new(m1.outputs[0], m2.inputs[0]); L.new(gy.outputs[0], m2.inputs[1])
    m3 = nd.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; L.new(m2.outputs[0], m3.inputs[0]); m3.inputs[1].default_value = dens
    pv = nd.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (.92, .94, .97, 1); pv.inputs["Anisotropy"].default_value = .5; L.new(m3.outputs[0], pv.inputs["Density"])
    L.new(pv.outputs[0], nd["Material Output"].inputs["Volume"])
    bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=size, verts=r_["verts"]); o = mesh_obj("cvol", bm, [m]); o.location = loc
    sc.cycles.volume_step_rate = 4.0; sc.cycles.volume_max_steps = 256; S["cvol"] = (o, nz)


def clouds_key(t, f, v=(30.0, 8.0)):
    for k, (o, mp) in enumerate(S.get("clouds", [])):
        keyp(o, f, loc=(o.location.x, o.location.y, o.location.z))
        mp.inputs["Location"].default_value = (k * 3.1 + v[0] * t / 2500., k * 1.7 + v[1] * t / 2500., k * .9 + .02 * t); mp.inputs["Location"].keyframe_insert("default_value", frame=f + 1)


def sky(hdri="kloofendal_43d_clear_puresky", sun=(30., 120.), sun_k=3.0, exposure=-.4, rot=0.0, haze=(.7, .8, .92), hk=.55, d0=3000., d1=160000.):
    env_clear(); S.clear(); sc.render.use_motion_blur = False
    track.world_hdri(hdri, exposure=exposure, sun=sun, sun_k=sun_k, rot=rot); S["haze"] = (haze, hk, d0, d1)


def finish():
    h, k, d0, d1 = S["haze"]; track.haze(col=h, k=k, d0=d0, d1=d1)


# ================================================================ ショット
EV = "everest"


def s_l00():
    sky(sun=(24., 140.), exposure=-.35, d0=4000., d1=120000.); terrain(EV, mountain_mat(), 1); clouds(4600, 5300, 4, 120000, scale=1 / 3000., dens=.9)
    finish()


def a_l00(u, t, f):
    tt = t + S.get("t_off", 0.0); p = Vector((-5200, -9800, 5600)).lerp(Vector((-3900, -7600, 6100)), tt / 5.6)
    cam.look(p, Vector((0, 0, 7800)), 24); clouds_key(tt, f)


def s_l08():
    S0 = s_l00(); S["t_off"] = 3.6


def a_l08(u, t, f):
    S["t_off"] = 3.6; a_l00(u, t, f)


def s_l01():
    env_clear(); S.clear(); sc.render.use_motion_blur = False
    w = sc.world.node_tree; w.nodes.clear(); bg = w.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (.001, .002, .012, 1); w.links.new(bg.outputs[0], w.nodes.new("ShaderNodeOutputWorld").inputs[0])
    sc.view_settings.exposure = 0.0; MJ = json.load(open(os.path.join(AS, "photo", "map.json"), encoding="utf-8")); half = MJ["half_km"] * 1000.0
    def plane(nm, image, z, alpha=False):
        m = bpy.data.materials.new(nm); m.use_nodes = True; t = m.node_tree; t.nodes.clear(); tx = t.nodes.new("ShaderNodeTexImage"); tx.image = img(os.path.join(AS, "photo", image)); tx.interpolation = "Cubic"
        em = t.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.3; t.links.new(tx.outputs["Color"], em.inputs["Color"]); out = t.nodes.new("ShaderNodeOutputMaterial")
        if alpha:                                                               # 日本アルプスの所から広がる（半径を毎コマ）
            tc = t.nodes.new("ShaderNodeTexCoord"); vm = t.nodes.new("ShaderNodeVectorMath"); vm.operation = "DISTANCE"; t.links.new(tc.outputs["Generated"], vm.inputs[0]); vm.inputs[1].default_value = (.5, .5, 0)
            rv = t.nodes.new("ShaderNodeValue"); S["reveal"] = rv.outputs[0]
            rd = t.nodes.new("ShaderNodeMath"); rd.operation = "SUBTRACT"; t.links.new(rv.outputs[0], rd.inputs[0]); t.links.new(vm.outputs["Value"], rd.inputs[1])
            ed = t.nodes.new("ShaderNodeMath"); ed.operation = "MULTIPLY"; ed.use_clamp = True; t.links.new(rd.outputs[0], ed.inputs[0]); ed.inputs[1].default_value = 25.0
            al = t.nodes.new("ShaderNodeMath"); al.operation = "MULTIPLY"; t.links.new(ed.outputs[0], al.inputs[0]); t.links.new(tx.outputs["Alpha"], al.inputs[1])
            tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader"); t.links.new(al.outputs[0], mx.inputs[0]); t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(em.outputs[0], mx.inputs[2])
            t.links.new(mx.outputs[0], out.inputs["Surface"])
        else:
            t.links.new(em.outputs[0], out.inputs["Surface"])
        bm = bmesh.new(); vs = [bm.verts.new((sx * half, sy * half, z)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; fc = bm.faces.new(vs); uv = bm.loops.layers.uv.new()
        for lp in fc.loops:
            lp[uv].uv = ((lp.vert.co.x / half + 1) / 2, (lp.vert.co.y / half + 1) / 2)
        return mesh_obj(nm, bm, [m])
    plane("japan", "japan.png", 0.0); plane("hima", "himalaya_ov.png", 200.0, True)


def a_l01(u, t, f):
    k = smooth(.3, 3.4, t); S["reveal"].default_value = .02 + .55 * k; key_v(S["reveal"], .02 + .55 * k, f)
    e = ease(u); cam.look(Vector((150e3, -700e3 - 300e3 * e, 2.4e6 + 6e5 * e)), Vector((40e3, 30e3, 0)), 30)


def s_l02():
    sky(sun=(30., 170.), exposure=-.35, d0=20000., d1=900000., hk=.35)
    mf = mountain_mat("mtn_f", snowline=3100.0, green=2300.0)
    terrain("fuji", mf, 1, at=(-7500, 0, 0), crop=14000.0, taper=4000.0); terrain(EV, mountain_mat(), 1, at=(7500, 0, 0), crop=12000.0, taper=6000.0)
    S["lines"] = []
    for k, z in enumerate((SIMO["fuji"], 2 * SIMO["fuji"])):                  # 富士山の高さ・富士山 2 つ分の高さの線
        m = emat(f"hl{k}", (1.0, .85, .25), emit=(1.0, .85, .25), k=1.2, haze=False); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(30000, 40, 40), verts=bm.verts); o = mesh_obj(f"hline{k}", bm, [m]); o.location = (0, 0, z); S["lines"].append(o)
    g = mat("plain", (.35, .37, .33), .9); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=600000.0); mesh_obj("plain", bm, [g])
    finish()


def a_l02(u, t, f):
    for o, t0 in zip(S["lines"], (.4, 3.3)):                                     # 線は左から右へ伸びる
        k = ease(smooth(t0, t0 + .8, t)); keyp(o, f, loc=(-15000 * (1 - k), 0, o.location.z), scale=(max(.001, k), 1, 1))
    e = ease(u); cam.look(Vector((-500, -44000 - 3000 * e, 2600)), Vector((-500, 0, 1800)), 36)


def s_l03():
    sky(sun=(35., 200.), exposure=-.35, d0=4000., d1=140000.); terrain(EV, mountain_mat(), 1); clouds(4600, 5300, 4, 120000, scale=1 / 3000., dens=.9)
    new = imp(os.path.join(AS, "sketchfab", "plane", "scene.gltf")); bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]; lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    L_ = max(hi.x - lo.x, hi.y - lo.y); root = link(bpy.data.objects.new("plane_root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.scale = (40.0 / L_,) * 3; root.location = -(lo + hi) / 2 * (40.0 / L_); hold = link(bpy.data.objects.new("plane", None)); root.parent = hold; S["plane"] = hold
    S["pl_ax"] = 0 if hi.x - lo.x > hi.y - lo.y else 1
    finish()


def a_l03(u, t, f):
    x = -1500 + 240 * t; P = Vector((x, 1300, 10000)); keyp(S["plane"], f, loc=tuple(P), rot=(0, 0, float(os.environ.get("PROT", "0")) + (0 if S["pl_ax"] == 0 else -math.pi / 2)))   # 時速 約 860 km
    cam.look(P + Vector((-75 + 25 * u, 95, 30)), P + Vector((60, -260, -170)), 24)                                   # 旅客機を斜め後ろから追う。下に山頂


def s_l04():
    sky(sun=(22., 120.), exposure=-.25, haze=(.68, .76, .88), hk=.85, d0=3000., d1=230000.)
    D = SIMO["tokyo_d"] * 1000.0; terrain(EV, mountain_mat(), 2, at=(0, D, 0), curv=(0, 0), taper=14000.0)
    r = np.random.default_rng(3); walls = city.WALLS                           # 手前のビル街（2〜9 km 先）
    for k in range(70):
        y = r.uniform(4000, 12000); x = (y * .06) * r.uniform(-1, 1); w_ = r.uniform(30, 70); d_ = r.uniform(30, 60); h_ = r.uniform(50, 180) if r.random() < .4 else r.uniform(25, 70)
        wc = walls[k % len(walls)]; bm_ = city.bmat(f"b{k % len(walls)}", *wc)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w_, d_, h_), verts=bm.verts); bmesh.ops.translate(bm, vec=(x, y, h_ / 2 - (x * x + y * y) / (2 * RE)), verts=bm.verts)
        mesh_obj(f"bld{k}", bm, [bm_])
    g = mat("cityground", (.3, .3, .31), .9); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30000.0); mesh_obj("cg", bm, [g])
    finish()


def a_l04(u, t, f):
    e = ease(u); cam.look(Vector((0, 0, 230)), Vector((0, SIMO["tokyo_d"] * 1000.0, 2600 + 300 * e)), 260 + 60 * e)     # 東京の高いビルの屋上から西へ、望遠


def s_l05():
    sky(hdri="kloofendal_48d_partly_cloudy_puresky", sun=(5., 95.), sun_k=2.2, exposure=-.55, rot=200.0, haze=(.98, .82, .66), hk=.5, d0=5000., d1=150000.)
    lt = bpy.data.lights.get("sun_lamp")
    if lt:
        lt.color = (1.0, .78, .55)                                              # 朝のやわらかい光（まぶしくしない）
    terrain(EV, mountain_mat(), 1); clouds(5600, 6400, 4, 140000, scale=1 / 3500., dens=.95, col=(1.0, .93, .86)); finish()


def a_l05(u, t, f):
    e = ease(u); cam.look(Vector((-300 + 60 * e, 200, 8820)), Vector((16000, -11000 + 1500 * e, 7600)), 30); clouds_key(t, f, (20.0, 4.0))


def s_l06():
    sky(sun=(25., 300.), exposure=-.35, haze=(.72, .8, .92), hk=.55, d0=4000., d1=120000.)
    terrain(EV, mountain_mat(), 1); cloud_volume((0, -14000, 6200), (60000, 22000, 4400), .004)
    finish()


def a_l06(u, t, f):
    e = ease(u); cam.look(Vector((16000 - 2500 * e, 14000, 9600)), Vector((0, -6000, 6600)), 28); clouds_key(t, f, (0.0, -60.0))


def s_l07():
    s_l05()


def a_l07(u, t, f):
    a = .4 + .12 * u; cam.look(Vector((-14000 * math.cos(a), -14000 * math.sin(a), 9800)), Vector((0, 0, 7800)), 26); clouds_key(t, f, (20.0, 4.0))


# ---------------------------------------------------------------- 書き出し
ANIM = [cam.o]
SHOTS = {k: (globals()["s_" + k], (lambda a: (lambda u, t, f: (log("anim frame", f) if f % 30 == 0 else None, a(u, t, f))))(globals()["a_" + k])) for k in NAMES}

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
    for name in O["shots"]:
        setup, anim = SHOTS[name]; n = int(math.ceil(SPLAN[name]["dur"] * K.FPS)) + 2
        cam.o.animation_data_clear(); setup()
        for f in range(n):
            anim(f / max(1, n - 3), f / K.FPS, f)
            for path in ("location", "rotation_quaternion"):
                cam.o.keyframe_insert(path, frame=f + 1)
            cam.o.data.keyframe_insert("lens", frame=f + 1)
        for at in ats:
            sc.frame_set(min(n, int(round(at * K.FPS)) + 1)); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            t0 = __import__("time").time(); bpy.ops.render.render(write_still=True); log("test", name, at, "render", round(__import__("time").time() - t0, 1), "s")
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
