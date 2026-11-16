"""pilot_059「日本アルプスが、ヒマラヤ山脈になったら？」v2 の 3D（Blender Cycles）。もしも設計の既定（templates/DESIGN_MODES.md）。
v2（ユーザーの指示）：ヒマラヤの真ん中を日本アルプスの真ん中に置く。松本の町で山がいきなり盛り上がり、人が戸惑う。エベレストの場所、日本の平均標高・気温、雪崩。
山は実際の標高データ（AWS Terrain Tiles、SRTM など USGS のパブリックドメイン、assets/get_dem.py・make_town.py）を 1 単位＝1 m で立体に。
盛り上がりは、今の松本のまわりの地形（town_now）からヒマラヤを置いた地形（town_new）へのシェイプキー（町の半径 2.5 km は動かさない）。
質感は Poly Haven（CC0）の aerial_rocks_02・aerial_grass_rock・roof_tiles・plastered_wall と、標高・傾きで積もらせる雪。人は顔のないピクトグラム（pilot_056 の Puppet）。
地図（l02・l03）は NASA の衛星画像（PD）と標高データから作ったヒマラヤの形（scripts/pilot_059/sim/place.py）。立体地図（l04・l07）は高さを 12 倍に強調。
東京から見る絵（l06）は地球の丸み（d²／2R）だけ山を下げる。閃光なし。けがは描かない。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city, people

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
PLJ = json.load(open(os.path.join(HERE, "..", "..", "..", "scripts", "pilot_059", "sim", "place.json"), encoding="utf-8"))
TJ = json.load(open(os.path.join(AS, "dem", "town.json"), encoding="utf-8"))


def local_km(lat, lon, lat0, lon0):
    return 6371.0 * math.radians(lon - lon0) * math.cos(math.radians(lat0)), 6371.0 * math.radians(lat - lat0)


# ---------------------------------------------------------------- 人（顔のないピクトグラム。pilot_056 の Puppet）
class Puppet:
    SEG = [("torso", "hip", "neck", .15, .17), ("thL", "hipL", "kneeL", .085, .07), ("shL", "kneeL", "footL", .065, .05), ("thR", "hipR", "kneeR", .085, .07),
           ("shR", "kneeR", "footR", .065, .05), ("uaL", "shL", "elL", .058, .05), ("faL", "elL", "haL", .048, .042), ("uaR", "shR", "elR", .058, .05), ("faR", "elR", "haR", .048, .042)]
    COL = {"torso": "shirt", "uaL": "shirt", "uaR": "shirt", "thL": "pants", "thR": "pants"}

    def __init__(self, name, pose_fn, shirt, pants):
        self.fn = pose_fn; self.cv, cf = people._capsule(12); self.hv, hf = people._ico(3); nc, nh = len(self.cv), len(self.hv); faces = []
        for i in range(len(self.SEG)):
            faces += [tuple(k + i * nc for k in fc) for fc in cf]
        o = len(self.SEG) * nc
        for j in range(3):
            faces += [tuple(k + o + j * nh for k in fc) for fc in hf]
        self.nv = o + 3 * nh; me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((self.nv, 3)).tolist(), [], faces); me.update(); me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        me.materials.append(people._pmat()); skin = np.array(people.SKIN); col = np.zeros((self.nv, 3))
        for i, (p, *_r) in enumerate(self.SEG):
            c = self.COL.get(p); col[i * nc:(i + 1) * nc] = shirt if c == "shirt" else pants if c == "pants" else skin
        col[o:] = skin; ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT"); ca.data.foreach_set("color", np.concatenate([col, np.ones((self.nv, 1))], 1).ravel())
        self.me = me; self.o = link(bpy.data.objects.new(name, me)); DYN.append(self.update); self.update(0.0)

    def update(self, t):
        J = self.fn(t); V = []
        for (p, a, b, r0, r1) in self.SEG:
            A_, B_ = np.array(J[a]), np.array(J[b]); d = B_ - A_; L_ = np.linalg.norm(d); d = d / max(L_, 1e-6)
            X = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < .95 else np.cross(d, [1.0, 0, 0]); X /= np.linalg.norm(X); Y = np.cross(d, X)
            tx, ty, tz, cap = self.cv[:, 0:1], self.cv[:, 1:2], self.cv[:, 2:3], self.cv[:, 3:4]; r = r0 + (r1 - r0) * tz
            V.append(A_ + d * (L_ * tz + r * cap * .75) + r * (tx * X + ty * Y))
        V += [np.array(J["head"]) + self.hv * .125, np.array(J["haL"]) + self.hv * .055, np.array(J["haR"]) + self.hv * .055]
        self.me.vertices.foreach_set("co", np.concatenate(V).astype(np.float32).ravel()); self.me.update()


def pose(k):
    """人は +Y（山）を向く。k：walk（ph）・look 見上げる・hold 頭を抱える・point 右手で山を指す・back 後ずさり（0〜1）"""
    wk, ph, lk, ho, pt, bk = k.get("walk", 0), k.get("ph", 0), k.get("look", 0), k.get("hold", 0), k.get("point", 0), k.get("back", 0)
    y0 = -bk * .6; hip = np.array([0, y0, .95 + .03 * wk * abs(math.sin(ph))]); up = np.array([0, -.1 * lk - .08 * bk, 1.0]); up /= np.linalg.norm(up)
    neck = hip + up * .5; hd = np.array([0, .02 - .1 * lk, .25]); head = neck + hd / np.linalg.norm(hd) * .25
    J = {"hip": hip, "neck": neck, "head": head}
    for s, sx in (("L", -1), ("R", 1)):
        a = .45 * wk * math.sin(ph + (0 if s == "L" else math.pi)); hp = hip + np.array([sx * .1, 0, -.04])
        foot = np.array([sx * .16, y0 + math.sin(a) * .45 + (-.18 if (s == "R" and bk) else 0) * bk, .05]); kn = (hp + foot) / 2 + np.array([0, .1, 0])
        J["hip" + s], J["knee" + s], J["foot" + s] = hp, kn, foot
        sh = neck + np.array([sx * .2, 0, -.05]); J["sh" + s] = sh
        el_st = sh + np.array([sx * .04, .02, -.27]); ha_st = el_st + np.array([0, .03, -.25])
        sw = .35 * wk * math.sin(ph + (math.pi if s == "L" else 0)); el_wk = sh + np.array([sx * .03, .27 * math.sin(sw), -.27 * math.cos(sw)]); ha_wk = el_wk + np.array([0, .25 * math.sin(sw + .3), -.25 * math.cos(sw + .3)])
        el_ho = sh + np.array([sx * .3, .05, .12]); ha_ho = head + np.array([sx * .12, -.02, .06])                          # 頭を抱える
        if s == "R":
            el_pt = sh + np.array([.05, .2, .17]); ha_pt = sh + np.array([.08, .42, .38])                                  # 山を指す
        else:
            el_pt, ha_pt = el_st, ha_st
        st = max(0.0, 1 - wk - ho - pt)
        J["el" + s] = st * el_st + wk * el_wk + ho * el_ho + pt * el_pt; J["ha" + s] = st * ha_st + wk * ha_wk + ho * ha_ho + pt * ha_pt
    return J


# ---------------------------------------------------------------- 松本の町と、盛り上がる山
T_END = 8.4                    # l00＋l01 の長さ。盛り上がりはこの間に


def rise(tg):
    return ease(smooth(.3, 5.6, tg))


def town_terrain():
    now = np.load(os.path.join(AS, "dem", "town_now.npy")); new = np.load(os.path.join(AS, "dem", "town_new.npy")); n = now.shape[0]; half = TJ["half_km"] * 1000.0
    mx, my = [v * 1000.0 for v in TJ["matsumoto_km"]]; z0 = 594.0
    xs = np.linspace(-half, half, n) - mx; ys = np.linspace(half, -half, n) - my; X, Y = np.meshgrid(xs, ys)
    w = np.clip((np.hypot(X, Y) - 2500.0) / 4000.0, 0, 1); w = w * w * (3 - 2 * w)                         # 町（半径 2.5 km）は動かさない
    Znow = now - z0; fl = np.clip((np.hypot(X, Y) - 1500.0) / 2500.0, 0, 1); fl = fl * fl * (3 - 2 * fl); Znow = -.3 * (1 - fl) + Znow * fl     # 町（半径 1.5 km）は平らに
    Znew = Znow + (new - now) * w
    step = 2; Xs, Ys, Zn, Zw = X[::step, ::step], Y[::step, ::step], Znow[::step, ::step], Znew[::step, ::step]; ny, nx = Xs.shape
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx - 1, y_subdivisions=ny - 1, size=1.0); o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = "town_terrain"; co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ix = np.round((co[:, 0] + .5) * (nx - 1)).astype(int); iy = np.round((.5 - co[:, 1]) * (ny - 1)).astype(int)
    base = np.stack([Xs[iy, ix], Ys[iy, ix], Zn[iy, ix]], 1); o.data.vertices.foreach_set("co", base.ravel()); o.data.update()
    o.data.polygons.foreach_set("use_smooth", np.ones(len(o.data.polygons), bool)); o.data.materials.append(mountain_mat("mtn_t", snowline=5200.0, green=2400.0))
    o.shape_key_add(name="Basis"); kb = o.shape_key_add(name="himalaya"); tgt = np.stack([Xs[iy, ix], Ys[iy, ix], Zw[iy, ix]], 1); kb.data.foreach_set("co", tgt.ravel())
    S["rise"] = kb; j, i = np.unravel_index(np.argmax(Zw), Zw.shape); S["peak"] = Vector((Xs[j, i], Ys[j, i], Zw[j, i]))
    return o


def gable(x, y, w, d, h, rh, ang, wall, roof):
    """切妻の家：壁（箱）＋三角の屋根"""
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w, d, h), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
    o = mesh_obj("house", bm, [wall]); o.location = (x, y, 0); o.rotation_euler = (0, 0, ang)
    bm = bmesh.new(); e = .45; vs = [bm.verts.new(v) for v in ((-w / 2 - e, -d / 2 - e, h), (w / 2 + e, -d / 2 - e, h), (w / 2 + e, d / 2 + e, h), (-w / 2 - e, d / 2 + e, h), (-w / 2 - e, 0, h + rh), (w / 2 + e, 0, h + rh))]
    for f_ in ((0, 1, 5, 4), (3, 4, 5, 2), (0, 4, 3), (1, 2, 5)):
        bm.faces.new([vs[i] for i in f_])
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=.12); r = mesh_obj("roof", bm, [roof]); r.location = (x, y, 0); r.rotation_euler = (0, 0, ang)


def town(dirv):
    """通り（山の方へまっすぐ）と、両側の家・電柱・電線"""
    ang = math.atan2(dirv.y, dirv.x) - math.pi / 2; fw = dirv.normalized(); side = Vector((fw.y, -fw.x, 0)); r = np.random.default_rng(12)
    asp = city.asphalt(); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(9, 900, .1), verts=bm.verts); o = mesh_obj("road", bm, [asp]); o.rotation_euler = (0, 0, ang); o.location = tuple(fw * 380)
    side_m = mat("sidewalk", (.55, .54, .52), .85)
    for sd in (-1, 1):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(3, 900, .22), verts=bm.verts); o = mesh_obj("walk", bm, [side_m]); o.rotation_euler = (0, 0, ang); o.location = tuple(fw * 380 + side * sd * 6)
    walls = [track.pbr("plastered_wall", .5, 0.0, tint=t, name=f"wall{k}") for k, t in enumerate(((1.0, .97, .9), (.85, .82, .78), (.7, .66, .6), (.95, .92, .86)))]
    roof = track.pbr("roof_tiles", .6, 0.0, tint=(.45, .48, .52), name="roof"); roof2 = track.pbr("roof_tiles", .6, 0.0, tint=(.35, .25, .22), name="roof2")
    for sd in (-1, 1):
        y = -40.0
        while y < 780:
            w, d, h = r.uniform(8, 12), r.uniform(8, 11), r.uniform(5.5, 7.5); off = 8.5 + d / 2 + r.uniform(0, 2)
            p = fw * (y + w / 2) + side * sd * off; gable(p.x, p.y, w, d, h, r.uniform(2.0, 3.0), ang + math.pi / 2, walls[r.integers(0, 4)], roof if r.random() < .6 else roof2)
            y += w + r.uniform(1.0, 4.0)
    pole = mat("pole", (.62, .62, .6), .7); wire = mat("wire", (.05, .05, .05), .6)
    tops = []
    for k in range(26):
        p = fw * (k * 32 - 20) + side * 5.6; bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=.17, radius2=.12, depth=10.0); bmesh.ops.translate(bm, vec=(0, 0, 5.0), verts=bm.verts)
        o = mesh_obj("pole", bm, [pole]); o.location = (p.x, p.y, 0); tops.append(p)
    for h_ in (8.6, 9.3):
        cu = bpy.data.curves.new("wire", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = .012; sp = cu.splines.new("POLY"); pts = []
        for a, b in zip(tops[:-1], tops[1:]):
            for q in np.linspace(0, 1, 6)[:-1]:
                m_ = a.lerp(b, q); pts.append((m_.x, m_.y, h_ - .6 * math.sin(math.pi * q)))
        sp.points.add(len(pts) - 1)
        for i, p_ in enumerate(pts):
            sp.points[i].co = (*p_, 1)
        o = link(bpy.data.objects.new("wire", cu)); o.data.materials.append(wire)


CROWD = [(-2.5, 14.0, (.85, .2, .2), (.15, .15, .2), 0.0), (1.8, 17.0, (.2, .45, .85), (.1, .1, .12), .7), (3.2, 22.0, (.95, .85, .3), (.2, .2, .25), 1.4),
         (-1.2, 26.0, (.3, .7, .4), (.12, .12, .15), 2.1), (.4, 11.0, (.9, .9, .92), (.25, .25, .3), 2.8), (-3.4, 31.0, (.6, .35, .7), (.15, .12, .12), 3.3),
         (2.6, 35.0, (.95, .55, .2), (.1, .1, .1), 1.0)]


def crowd(fw, side, tofs=0.0):
    """通りの人たち：歩いている → 揺れで立ち止まる → 見上げる・頭を抱える・指さす・後ずさる（人ごとに少しずつずらす）"""
    S["crowd"] = []
    for i, (sx, fy, shirt, pants, d0) in enumerate(CROWD):
        def fn(t, i=i, d0=d0):
            tg = t + S.get("tofs", 0.0); stop = smooth(1.0 + .25 * i % 1.0, 1.8 + .2 * (i % 3), tg); act = smooth(2.2 + .3 * (i % 3), 3.4 + .3 * (i % 3), tg)
            k = {"walk": 1 - stop, "ph": tg * 5.2 + d0, "look": stop}
            kind = i % 4
            if kind == 1:
                k["hold"] = act
            elif kind == 2:
                k["point"] = act
            elif kind == 3:
                k["back"] = act * smooth(3.0, 6.0, tg)
            return pose(k)
        p = Puppet(f"man{i}", fn, shirt, pants); p.o.location = tuple(fw * fy + side * sx); p.o.rotation_euler = (0, 0, math.atan2(fw.y, fw.x) - math.pi / 2)
        S["crowd"].append(p)


def s_town(tofs):
    sky(sun=(38., 140.), exposure=-.3, haze=(.72, .8, .92), hk=.5, d0=1500., d1=90000.); S["tofs"] = tofs
    town_terrain(); dirv = S["peak"].copy(); dirv.z = 0; fw = dirv.normalized(); side = Vector((fw.y, -fw.x, 0)); S["fw"], S["side"] = fw, side
    town(fw); crowd(fw, side); finish(); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .4


def town_key(tg, f):
    k = rise(tg); S["rise"].value = k; S["rise"].keyframe_insert("value", frame=f + 1)


def s_l00():
    s_town(0.0)


def a_l00(u, t, f):
    tg = t; town_key(tg, f); fw, side = S["fw"], S["side"]; e = ease(u)
    sk = shake(f, .05 * smooth(.4, 1.0, tg) * (1 - .4 * smooth(3, 8, tg)), 3)
    pos = fw * (-2.0 + 2.5 * e) + side * .6 + Vector((0, 0, 1.55)) + sk; pk = S["peak"]; at = Vector((pk.x * .5, pk.y * .5, 40 + pk.z * .26 * rise(tg)))
    cam.look(pos, at, 26 - 4 * e)


def s_l01():
    s_town(3.8)


def a_l01(u, t, f):
    tg = t + 3.8; town_key(tg, f); fw, side = S["fw"], S["side"]; e = ease(u)
    sk = shake(f, .035 * (1 - smooth(5, 8, tg)), 5)
    pos = fw * (8.0 + 3.0 * e) + side * (-1.2) + Vector((0, 0, .55)) + sk; at = S["peak"] * .5 + Vector((0, 0, S["peak"].z * .35 + 1200 * rise(tg)))
    cam.look(pos, at, 20)                                                     # 低い位置から見上げる（人の背中ごし）


def s_l08():
    s_town(-2.0)


def a_l08(u, t, f):
    tg = t - 2.0; town_key(tg, f); fw, side = S["fw"], S["side"]
    cam.look(fw * (-2.0 - 2.5 * (1 - u)) + side * .6 + Vector((0, 0, 1.55)), fw * 400 + Vector((0, 0, 30)), 26)


# ---------------------------------------------------------------- 地図（l02・l03）
def map_scene():
    env_clear(); S.clear(); sc.render.use_motion_blur = False
    w = sc.world.node_tree; w.nodes.clear(); bg = w.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (.0043, .0039, .0415, 1); w.links.new(bg.outputs[0], w.nodes.new("ShaderNodeOutputWorld").inputs[0])
    sc.view_settings.exposure = 0.0; MJ = json.load(open(os.path.join(AS, "photo", "map.json"), encoding="utf-8")); half = MJ["half_km"] * 1000.0
    def plane(nm, image, z, alpha=False):
        m = bpy.data.materials.new(nm); m.use_nodes = True; t = m.node_tree; t.nodes.clear(); tx = t.nodes.new("ShaderNodeTexImage"); tx.image = img(os.path.join(AS, "photo", image)); tx.interpolation = "Cubic"
        em = t.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.3; t.links.new(tx.outputs["Color"], em.inputs["Color"]); out = t.nodes.new("ShaderNodeOutputMaterial")
        if alpha:
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
    ex, ey = local_km(PLJ["everest_lat"], PLJ["everest_lon"], 36.3, 137.6); S["ev"] = Vector((ex * 1000, ey * 1000, 0))
    red = emat("pin", (1.0, .15, .1), emit=(1.0, .15, .1), k=1.6, haze=False)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=9000, radius2=9000, depth=400); o = mesh_obj("pin", bm, [red]); o.location = S["ev"] + Vector((0, 0, 600)); S["pin"] = o
    bm = bmesh.new(); N = 64; vo = [bm.verts.new((math.cos(a), math.sin(a), 0)) for a in np.linspace(0, 6.283, N, endpoint=False)]; vi = [bm.verts.new((.9 * math.cos(a), .9 * math.sin(a), 0)) for a in np.linspace(0, 6.283, N, endpoint=False)]
    for i in range(N):
        bm.faces.new((vo[i], vo[(i + 1) % N], vi[(i + 1) % N], vi[i]))
    ring = mesh_obj("ring", bm, [red]); ring.location = S["ev"] + Vector((0, 0, 700)); S["ring"] = ring                # 広がる輪


def s_l02():
    map_scene()


def a_l02(u, t, f):
    k = smooth(.2, 3.6, t); key_v(S["reveal"], .02 + .58 * k, f); keyhide(S["pin"], True, f); keyhide(S["ring"], True, f)
    e = ease(u); cam.look(Vector((100e3, -800e3 - 200e3 * e, 2.5e6 + 4e5 * e)), Vector((40e3, 60e3, 0)), 30)


def s_l03():
    map_scene()


def a_l03(u, t, f):
    key_v(S["reveal"], .6, f); e = ease(smooth(0, 3.0, t)); ev = S["ev"]
    p0, a0 = Vector((100e3, -1.0e6, 2.9e6)), Vector((40e3, 60e3, 0)); p1, a1 = ev + Vector((0, -260e3, 420e3)), ev
    cam.look(p0.lerp(p1, e), a0.lerp(a1, e), 30)
    q = (t * 1.2) % 1.0; r = 12000 + 60000 * q; keyp(S["ring"], f, scale=(r, r, 1)); keyhide(S["pin"], t < .3, f); keyhide(S["ring"], t < .3, f)


# ---------------------------------------------------------------- 新しい日本の立体地図（l04・l07）
VEX = 6.0                      # 高さの強調


def s_relief():
    sky(sun=(28., 150.), exposure=-.2, haze=(.6, .7, .85), hk=.35, d0=400000., d1=4.0e6)
    H = np.load(os.path.join(AS, "dem", "japan_new.npy")); half = 1.5e6; n = H.shape[0]; st = 2; Hs = H[::st, ::st] * VEX; ny, nx = Hs.shape
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=nx - 1, y_subdivisions=ny - 1, size=2 * half); o = bpy.context.active_object
    for c in o.users_collection:
        c.objects.unlink(o)
    link(o); o.name = "relief"; co = np.zeros(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ix = np.round((co[:, 0] / (2 * half) + .5) * (nx - 1)).astype(int); iy = np.round((.5 - co[:, 1] / (2 * half)) * (ny - 1)).astype(int); co[:, 2] = Hs[iy, ix]
    o.data.vertices.foreach_set("co", co.ravel()); o.data.update(); o.data.polygons.foreach_set("use_smooth", np.ones(len(o.data.polygons), bool))
    m = bpy.data.materials.new("relief"); m.use_nodes = True; t = m.node_tree; nd = t.nodes; L = t.links; b = nd["Principled BSDF"]
    tc = nd.new("ShaderNodeTexCoord"); tx = nd.new("ShaderNodeTexImage"); tx.image = img(os.path.join(AS, "photo", "japan.png")); L.new(tc.outputs["Generated"], tx.inputs[0])
    g = nd.new("ShaderNodeNewGeometry"); sp = nd.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sp.inputs[0])
    sn = nd.new("ShaderNodeMapRange"); sn.inputs[1].default_value = 5400 * VEX; sn.inputs[2].default_value = 6600 * VEX; L.new(sp.outputs["Z"], sn.inputs[0])
    rk = nd.new("ShaderNodeMapRange"); rk.inputs[1].default_value = 1200 * VEX; rk.inputs[2].default_value = 2600 * VEX; L.new(sp.outputs["Z"], rk.inputs[0])
    m1 = nd.new("ShaderNodeMix"); m1.data_type = "RGBA"; L.new(rk.outputs[0], m1.inputs[0]); L.new(tx.outputs["Color"], m1.inputs[6]); m1.inputs[7].default_value = (.32, .29, .27, 1)
    m2 = nd.new("ShaderNodeMix"); m2.data_type = "RGBA"; L.new(sn.outputs[0], m2.inputs[0]); L.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (.9, .93, .97, 1)
    L.new(m2.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8; add_haze(m); o.data.materials.append(m)
    finish()


def s_l04():
    s_relief()


def a_l04(u, t, f):
    e = ease(u); cam.look(Vector((-250e3 + 150e3 * e, -6.5e5 + 1.2e5 * e, 1.5e5 - 2e4 * e)), Vector((40e3, 120e3, 2e4)), 28)


def s_l07():
    s_relief()


def a_l07(u, t, f):
    a = -.5 + .25 * u; cam.look(Vector((9e5 * math.sin(a) + 2e5, -9e5 * math.cos(a), 2.2e5)), Vector((2.0e5, 2.5e5, 3e4)), 30)


# ---------------------------------------------------------------- 雪崩（l05）
def descend(p, n=60, ds=40.0):
    """斜面を一番急な向きにくだる道（地形の格子から）"""
    _, X, Y, Z = S["terr"][EV]; xs, ys = X[0], Y[:, 0]; pts = [p.copy()]
    def h(x, y):
        i = int(np.clip(np.searchsorted(xs, x), 1, len(xs) - 1)); j = int(np.clip(len(ys) - np.searchsorted(ys[::-1], y), 1, len(ys) - 1)); return Z[j, i]
    for _ in range(n):
        x, y = pts[-1].x, pts[-1].y; gx = (h(x + 60, y) - h(x - 60, y)) / 120; gy = (h(x, y + 60) - h(x, y - 60)) / 120; g = Vector((-gx, -gy, 0))
        if g.length < 1e-4:
            break
        q = Vector((x, y, 0)) + g.normalized() * ds; pts.append(Vector((q.x, q.y, h(q.x, q.y))))
    return pts


NB = 34                        # 雪煙のかたまりの数


def s_l05():
    sky(sun=(30., 40.), exposure=-.35, d0=3000., d1=90000.); terrain(EV, mountain_mat(), 1); clouds(4800, 5400, 3, 100000, scale=1 / 3000., dens=.8)
    path = descend(Vector((-900, -1400, 0))); S["path"] = path
    m = bpy.data.materials.new("powder"); m.use_nodes = True; t = m.node_tree; nd = t.nodes; L = t.links
    for x in list(nd):
        if x.type != "OUTPUT_MATERIAL":
            nd.remove(x)
    tc = nd.new("ShaderNodeTexCoord"); nz = nd.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.2; nz.inputs["Detail"].default_value = 12; nz.inputs["Roughness"].default_value = .62
    nz.inputs["Distortion"].default_value = .35; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    gr = nd.new("ShaderNodeVectorMath"); gr.operation = "LENGTH"; L.new(tc.outputs["Object"], gr.inputs[0]); fo = nd.new("ShaderNodeMapRange"); fo.inputs[1].default_value = 1.0; fo.inputs[2].default_value = .55; L.new(gr.outputs["Value"], fo.inputs[0])
    ad = nd.new("ShaderNodeMath"); ad.operation = "ADD"; L.new(nz.outputs["Fac"], ad.inputs[0]); L.new(fo.outputs[0], ad.inputs[1])                    # 縁はノイズで食われ、もこもこの輪郭に
    cr = nd.new("ShaderNodeMapRange"); cr.inputs[1].default_value = 1.25; cr.inputs[2].default_value = 1.45; L.new(ad.outputs[0], cr.inputs[0])
    m2 = nd.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; L.new(cr.outputs[0], m2.inputs[0]); m2.inputs[1].default_value = .022
    pv = nd.new("ShaderNodeVolumePrincipled"); pv.inputs["Color"].default_value = (.98, .98, .99, 1); pv.inputs["Anisotropy"].default_value = .1; L.new(m2.outputs[0], pv.inputs["Density"]); L.new(pv.outputs[0], nd["Material Output"].inputs["Volume"])
    S["blobs"] = []
    for k in range(NB):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = mesh_obj(f"powder{k}", bm, [m]); o.visible_shadow = True; S["blobs"].append(o)
    sc.cycles.volume_step_rate = 8.0; sc.cycles.volume_max_steps = 96; sc.cycles.volume_bounces = 2      # 中で光がはね回って白く明るい雪煙に
    if not os.environ.get("AT"):
        sc.render.resolution_percentage = 50                                 # 雪煙は重いので半分の大きさで描き、bl_pack の前に 1080×1920 へ拡大（やわらかい雪煙なので差は目立たない）
    finish()


AV = 83.0                      # 雪煙の先の速さ m/s（時速 約 300 km）


def gzE(x, y):
    _, X, Y, Z = S["terr"][EV]; xs, ys = X[0], Y[:, 0]; i = int(np.clip(np.searchsorted(xs, x), 0, len(xs) - 1)); j = int(np.clip(len(ys) - 1 - np.searchsorted(ys[::-1], y), 0, len(ys) - 1)); return float(Z[j, i])


def a_l05(u, t, f):
    path = S["path"]; L_ = len(path) - 1; seg = 40.0; r_ = np.random.default_rng(5)
    def at(d):
        q = np.clip(d / seg, 0, L_); i = int(min(q, L_ - 1)); return path[i].lerp(path[i + 1], q - i)
    front = 150 + AV * t
    for k, o in enumerate(S["blobs"]):
        jx, jy, jz, sp = r_.uniform(-1, 1), r_.uniform(-1, 1), r_.uniform(.2, 1.0), r_.uniform(0, 6.28)
        d = front - k * 30.0; age = max(0.0, d) / 500.0; r = (40 + 250 * min(1.0, age) ** .6) * r_.uniform(.7, 1.15)
        p = at(max(d, 0)) + Vector((jx * r * .6, jy * r * .6, r * (.35 + .5 * jz) + 320 * min(1.0, age) * jz))      # 前は地面をはい、後ろほど高く巻き上がる
        keyp(o, f, loc=tuple(p), rot=(sp + t * .5, sp * .7, sp), scale=(r * 1.15, r * 1.15, r * .9)); keyhide(o, d < 0, f)
    c0 = at(700); dv = (at(760) - at(640)); dv.z = 0; sd = Vector((dv.y, -dv.x, 0)).normalized()
    cpos = c0 + sd * 800 + dv.normalized() * 500; cpos.z = max(c0.z, gzE(cpos.x, cpos.y)) + 60                                   # 道の横・少し下手の高い所から、迫る雪煙を見る
    cam.look(cpos + shake(f, 4.0 * smooth(2.0, 5.0, t), 7), at(max(front - 150, 45.0)) + Vector((0, 0, 220)), 24)     # 出だしは尾根の陰を見ないように


# ---------------------------------------------------------------- 東京から（l06）
def s_l06():
    sky(sun=(22., 120.), exposure=.15, rot=180., haze=(.62, .75, .95), hk=.32, d0=3000., d1=380000.)
    D = PLJ["tokyo_km"] * 1000.0; terrain(EV, mountain_mat(), 2, at=(0, D, 0), curv=(0, 0), taper=14000.0)
    r = np.random.default_rng(3); walls = city.WALLS
    for k in range(240):
        y = r.uniform(1500, 14000); x = (y * .06) * r.uniform(-1, 1); w_ = r.uniform(30, 70); d_ = r.uniform(30, 60); h_ = r.uniform(50, 180) if r.random() < .4 else r.uniform(25, 70)
        wc = walls[k % len(walls)]; bm_ = city.bmat(f"b{k % len(walls)}", *wc)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w_, d_, h_), verts=bm.verts); bmesh.ops.translate(bm, vec=(x, y, h_ / 2 - (x * x + y * y) / (2 * RE)), verts=bm.verts)
        mesh_obj(f"bld{k}", bm, [bm_])
    g = mat("cityground", (.16, .17, .18), .9); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=60, y_segments=60, size=30000.0)
    for v in bm.verts:
        v.co.z = -(v.co.x ** 2 + v.co.y ** 2) / (2 * RE)                     # 地面も地球の丸みで下がる（平らな板の縁が白い壁に見えていた）
    mesh_obj("cg", bm, [g])
    m = bpy.data.materials.new("skyback"); m.use_nodes = True; nd = m.node_tree.nodes; L = m.node_tree.links                # 山の後ろの青空（遠くの空が灰色にくすんでいた）
    for x in list(nd):
        if x.type != "OUTPUT_MATERIAL":
            nd.remove(x)
    tc = nd.new("ShaderNodeTexCoord"); sp = nd.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sp.inputs[0]); rp = nd.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (.66, .76, .88, 1); rp.color_ramp.elements[1].position = .6; rp.color_ramp.elements[1].color = (.26, .43, .74, 1); L.new(sp.outputs["Z"], rp.inputs[0])
    em = nd.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.0; L.new(rp.outputs[0], em.inputs[0]); L.new(em.outputs[0], nd["Material Output"].inputs["Surface"])
    bm = bmesh.new(); r_ = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=.5); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    bmesh.ops.scale(bm, vec=(500000., 1., 50000.), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, D + 160000., 25000. - 9000.), verts=bm.verts); o = mesh_obj("skyback", bm, [m]); o.visible_shadow = False
    finish()


def a_l06(u, t, f):
    e = ease(u); D = PLJ["tokyo_km"] * 1000.0; top = 8741 - D * D / (2 * RE)
    cam.look(Vector((0, 0, 230)), Vector((0, D, top * .45 + 900 * e)), 380 + 280 * e)     # 街の上から山へ、ゆっくり寄りながら見上げる


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
