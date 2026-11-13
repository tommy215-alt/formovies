"""pilot_053 v2「観測史上最大が東京で全部同時に起きたら？」の 3D（Blender Cycles）。v1 は scene_v1.py。
v2（2026-11-13 ユーザーの直し）：東京の名所（渋谷のスクランブル交差点・東京タワー）、人と車、風の強さがわかる物（旗・飛ぶ傘）、
灼熱と豪雨の同時（温度計 41.8℃ と雨量計、雨の中の湯気）、人のリアクション（傘・両手を上げて驚く・走る・屋上で手を振る）。
時計 c（時間）：雪は 0.1〜2.5 時間で 11.82 m まで積もり、そこから 1 時間に 0.50 m ずつとける。水は 2.5 時間から 1 時間に 0.30 m たまる（上限 4.45 m）。
人は簡易のピクトグラム（顔なし）。けが・犠牲は描かない。閃光なし。霞の発光は照明として扱わない（common.add_haze）。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city, people

NAMES = [s["id"] for s in PLAN["shots"]]
SNOW, MELT_H, WATER_END = PLAN["snow"], PLAN["melt_h"], PLAN["water_end"]
RATE = PLAN["sim"]["inflow_mm_h"] / 1000 - .05
SKF = os.path.join(HERE, "..", "assets", "sketchfab")
CY = -28.0                      # 交差点の中心の y（city.street の交差する道のすき間）
S = {}


def snow_h(c):
    if c < 2.5:
        return float(SNOW * smooth(.1, 2.5, c))
    return max(0.0, SNOW * (1 - (c - 2.5) / MELT_H))


def water_h(c):
    return min(WATER_END, max(0.0, RATE * (c - 2.5)))


def clock(k):
    s = SPLAN[k]; c = s["c"]; d = s["dur"]
    def f(t):
        u = clamp(t / d)
        for (u0, c0), (u1, c1) in zip(c, c[1:]):
            if u <= u1 or (u1, c1) == tuple(c[-1]):
                return c0 + (c1 - c0) * clamp((u - u0) / max(1e-9, u1 - u0))
        return c[-1][1]
    return f


# ---------------------------------------------------------------- 読み込む模型（Sketchfab、CC BY：作者は assets/sketchfab/*/credit.json）
_SRC = {}


def src(name, size, axis=2):
    if name in _SRC:
        return _SRC[name]
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(SKF, name, "scene.gltf")); new = [o for o in bpy.data.objects if o not in before]
    col = bpy.data.collections.new("src_" + name); sc.collection.children.link(col)
    for o in new:
        for c_ in list(o.users_collection):
            c_.objects.unlink(o)
        col.objects.link(o)
    bpy.context.view_layer.update(); pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    h = bpy.data.objects.new("hold_" + name, None); col.objects.link(h); s_ = size / (hi - lo)[axis]; h.scale = (s_,) * 3; h.location = -Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s_
    for o in new:
        if o.parent is None:
            o.parent = h
    bpy.context.view_layer.layer_collection.children[col.name].exclude = True
    _SRC[name] = col; return col


def place(name, size, pos, rot=0.0, axis=2, scale=1.0):
    e = link(bpy.data.objects.new(f"i_{name}", None)); e.instance_type = "COLLECTION"; e.instance_collection = src(name, size, axis)
    e.location = Vector(pos); e.rotation_euler = (0, 0, rot); e.scale = (scale,) * 3; return e


# ---------------------------------------------------------------- 雪・水・雨・雪のつぶ・旗
def snow_mat():
    m = track.pbr("snow_field_aerial", .025, 0.0, tint=(1.18, 1.18, 1.22), name="snow", spec=.4); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = .25; b.inputs["Subsurface Radius"].default_value = (.4, .5, .6)
    wet = m.node_tree.nodes.new("ShaderNodeValue"); wet.outputs[0].default_value = 0.0; src_ = b.inputs["Base Color"].links[0].from_socket
    mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[7].default_value = (.4, .44, .47, 1)
    m.node_tree.links.new(wet.outputs[0], mx.inputs[0]); m.node_tree.links.new(src_, mx.inputs[6]); m.node_tree.links.new(mx.outputs[2], b.inputs["Base Color"])
    return m, wet.outputs[0]


def water_mat():
    m = bpy.data.materials.new("flood"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    b.inputs["Base Color"].default_value = (.07, .09, .07, 1); b.inputs["Roughness"].default_value = .05; b.inputs["IOR"].default_value = 1.33
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = .6; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"]); bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = .2; bp.inputs["Strength"].default_value = .3
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"]); add_haze(m, 300., 9000., .7); return m, nz.inputs["W"], bp.inputs["Strength"]


class Falling:
    """カメラのまわりに降る雨のすじ（snow=False）か雪のつぶ（snow=True）。wind：横に流れる速さ m/s"""
    def __init__(self, name, N, size=(44, 44, 22), snow=False, seed=3):
        r = np.random.default_rng(seed); self.N = N; self.size = np.array(size, float); self.p0 = r.random((N, 3)) * self.size; self.snow = snow
        self.sp = r.uniform(1.0, 1.8, N) if snow else r.uniform(8, 10, N); self.ph = r.uniform(0, 6.28, N); self.center = Vector((0, 0, 0)); self.wind = 0.0
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((N * 4, 3)).tolist(), [], [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(N)]); me.update()
        if snow:
            m = emat(name + "_m", (.95, .96, 1.0), .6, (1, 1, 1), .4, haze=False)
        else:
            m = mat(name + "_m", (.85, .9, .95), .1); bs = m.node_tree.nodes["Principled BSDF"]; bs.inputs["Transmission Weight"].default_value = .5; bs.inputs["Alpha"].default_value = .85
        me.materials.append(m); self.me = me; self.o = link(bpy.data.objects.new(name, me)); DYN.append(self.update)

    def update(self, t):
        p = self.p0.copy(); p[:, 2] = (p[:, 2] - self.sp * t) % self.size[2]; p[:, 0] = (p[:, 0] + self.wind * t * (.6 if self.snow else 1)) % self.size[0]
        if self.snow:
            p[:, 1] += .4 * np.sin(t * 1.3 + self.ph)
        p = p - self.size / 2 + np.array(self.center)
        if self.snow:
            s = .03; V = np.stack([p + [-s, 0, -s], p + [s, 0, -s], p + [s, 0, s], p + [-s, 0, s]], 1)
        else:
            d = np.array([self.wind, 0, -9.0]); d = d / np.linalg.norm(d) * (.5 + .02 * abs(self.wind)); w = np.array([0, .016, 0]); V = np.stack([p - w, p + w, p + w + d, p - w + d], 1)
        self.me.vertices.foreach_set("co", V.astype(np.float32).ravel()); self.me.update()


class Flag:
    """はためく旗（風が強いほど速く大きく波打ち、まっすぐ横に張る）"""
    def __init__(self, name, pole, h=6.0, col=(.85, .1, .1), heading=0.0):
        self.nx, self.ny = 14, 6; L, H = 1.8, 1.1; base = Vector(pole) + Vector((0, 0, h - H))
        bm = bmesh.new(); vs = [[bm.verts.new((i / (self.nx - 1) * L, 0, j / (self.ny - 1) * H)) for i in range(self.nx)] for j in range(self.ny)]
        for j in range(self.ny - 1):
            for i in range(self.nx - 1):
                bm.faces.new((vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]))
        m = mat(name + "_m", col, .7); self.o = mesh_obj(name, bm, [m]); self.o.location = base; self.o.rotation_euler = (0, 0, heading)
        self.rest = np.array([tuple(v.co) for v in self.o.data.vertices]); self.wind = 20.0; self.L = L
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.05, radius2=.04, depth=h); bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=bm.verts)
        p_ = mesh_obj(name + "_pole", bm, [mat("pole", (.12, .13, .14), .45, .6)]); p_.location = Vector(pole); DYN.append(self.update)

    def update(self, t):
        x = self.rest[:, 0] / self.L; k = clamp(self.wind / 70.0); f = 2 + 9 * k
        y = (.08 + .5 * k) * x * np.sin(2 * np.pi * (x * 1.6 - f * t)) + .05 * x * np.sin(7 * t + x * 9)
        z = self.rest[:, 2] - (1 - k) * .35 * x ** 2
        V = np.stack([self.rest[:, 0] * (1 - .06 * k * np.abs(np.sin(f * t))), y, z], 1)
        self.o.data.vertices.foreach_set("co", V.astype(np.float32).ravel()); self.o.data.update()


# ---------------------------------------------------------------- 舞台 A：渋谷のスクランブル交差点
def crossing_world(c_fn, people_on=True, rain=True, snowfall=True):
    env_clear(); sc.render.use_motion_blur = False; S.clear(); S["c"] = c_fn
    track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.15)
    city.street(y0=-300, y1=700, cross=140, tree_gap=24.)
    pt = mat("paint", (.82, .82, .8), .55)
    city.box("cross_road", -300, 300, CY - 8, CY + 8, -.29, .0, track.pbr("brushed_concrete", .3, 0.0, tint=(.32, .32, .33), name="asph2"))
    st = []                                                             # 横断歩道の白い縞：四方と斜め
    for k in range(13):
        x = -13 + k * 2.2
        st += [(x, CY + 11, .006, 1.1, 4.0, .012, 0, 0, 0), (x, CY - 11, .006, 1.1, 4.0, .012, 0, 0, 0)]
        y = CY - 7 + k * 1.15
        st += [(-19, y, .006, 4.0, .6, .012, 0, 0, 0), (19, y, .006, 4.0, .6, .012, 0, 0, 0)]
    for k in range(-8, 9):
        for sx in (-1, 1):
            st.append((k * 1.35, CY + sx * k * 1.0, .007, 3.2, .55, .012, sx * .64, 0, 0))
    instances("zebra", CUBE_V, CUBE_F, st, [pt])
    for i, (x, y, h, tex) in enumerate(((-21.9, CY + 22, 26, "screen_a"), (21.9, CY + 30, 20, "screen_b"), (-21.9, CY - 30, 18, "screen_c"))):
        im = img_mat(tex, .4, 2.5)
        P = [(x, y - 7, h - 5), (x, y + 7, h - 5), (x, y + 7, h + 5), (x, y - 7, h + 5)] if x > 0 else [(x, y + 7, h - 5), (x, y - 7, h - 5), (x, y - 7, h + 5), (x, y + 7, h + 5)]
        mesh_obj(f"screen{i}", quad("q", P, im), [im])
    # 道をまたぐ案内板：気温 41.8℃ と 雨量 153 mm/h を並べる（灼熱と豪雨が同時、どの場面からも見える。+Y 向き）
    Yg = CY - 46; dk = mat("gantry", (.15, .16, .17), .45, .6)
    for sx in (-1, 1):
        city.box(f"gpost{sx}", sx * 14.8 - .3, sx * 14.8 + .3, Yg - .3, Yg + .3, 0, 22, dk)
    city.box("gbeam", -15, 15, Yg - .4, Yg + .4, 21.0, 22.2, dk); city.box("gback", -14.4, 14.4, Yg - .2, Yg - .05, 13.0, 21.0, dk)
    for tex, x0, x1 in (("thermo", 14.0, .3), ("rain", -.3, -14.0)):
        im = img_mat(tex, .4, 3.0); mesh_obj("g_" + tex, quad("q", [(x0, Yg, 13.4), (x1, Yg, 13.4), (x1, Yg, 20.6), (x0, Yg, 20.6)], im), [im])
    for (x, y, r) in ((-16, CY + 9.5, 0), (16, CY - 9.5, math.pi), (-16, CY - 9.5, -math.pi / 2), (16, CY + 9.5, math.pi / 2)):
        place("signal", 6.0, (x, y, .15), r)
    rnd = np.random.default_rng(31)
    for x in (-11.2, -3.8, 3.8, 11.2):                                  # 赤信号で止まっている車
        sgn = 1 if x > 0 else -1
        for k in range(6):
            place("car", 5.8, (x + rnd.uniform(-.2, .2), CY + sgn * (16 + k * 6.6), 0), (0 if sgn < 0 else math.pi) + rnd.uniform(-.03, .03), axis=1)
    sm, S["wet"] = snow_mat(); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1500.0); S["snow"] = mesh_obj("snow", bm, [sm])
    wm, S["wW"], S["wB"] = water_mat(); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1500.0); S["water"] = mesh_obj("water", bm, [wm])
    S["ppl"] = []; S["umb"] = []
    if people_on:
        P = people.grid(420, -14, 14, CY - 9, CY + 9, seed=5, jitter=.45)                # 交差点の上の人
        P2 = np.concatenate([people.grid(160, 15.6, 21.5, CY - 40, CY + 40, seed=6), people.grid(160, -21.5, -15.6, CY - 40, CY + 40, seed=7)])
        md = rnd.choice([0, 1, 2, 2, 2], len(P)); hd = rnd.uniform(-math.pi, math.pi, len(P))
        S["ppl"].append(people.split("crowd", P, heading=hd, speed=np.where(md == 0, rnd.uniform(1.6, 3.2, len(P)), 0.0), mode=md, seed=8, bib=False))
        S["ppl"].append(people.split("walk", P2, heading=rnd.uniform(-math.pi, math.pi, len(P2)), speed=0.0, mode=rnd.choice([1, 2, 2], len(P2)), seed=9, bib=False))
        for i in np.nonzero((md == 2) & (rnd.random(len(P)) < .45))[0][:110]:        # 傘を差している人
            S["umb"].append(place("umbrella", 1.0, (P[i, 0] + .12, P[i, 1], 1.15), rnd.uniform(0, 6.28)))
    S["rain"] = Falling("rain", 9000) if rain else None; S["flakes"] = Falling("flakes", 5000, snow=True, seed=5) if snowfall else None
    S["flags"] = [Flag(f"flag{i}", (sx * 22.8, CY + dy, 0), 7.5, col, math.pi / 2 if sx < 0 else -math.pi / 2) for i, (sx, dy, col) in enumerate(((-1, 20, (.85, .1, .1)), (1, 26, (.1, .3, .8)), (-1, 46, (.95, .7, .1))))]
    track.haze(col=(.82, .86, .9), k=.45)


def set_state(t, f, wind=6.0, center=None):
    c = S["c"](t); h = snow_h(c); w = water_h(c)
    wl = max(w, h + .04) if c > 9.0 else (w if (w > h - .2 and w > .02) else -1.0)      # 9 時間から：水を含んだ雪の上に水があふれる
    keyp(S["snow"], f, loc=(0, 0, h if h > .03 else -.3)); keyp(S["water"], f, loc=(0, 0, wl))
    key_v(S["wet"], clamp((c - 2.5) / 5.0), f); key_v(S["wW"], t * .35, f)
    for fl in S.get("flags", []):
        fl.wind = wind
    for k in ("rain", "flakes"):
        if S.get(k):
            S[k].wind = wind * (1.0 if k == "rain" else .7)
            if center is not None:
                S[k].center = center
    return c, h, w


# ---------------------------------------------------------------- 舞台 B：東京タワー
TOWER = Vector((40, 520, 0))


def tower_world(c_fn, rain=True, snowfall=True):
    env_clear(); sc.render.use_motion_blur = False; S.clear(); S["c"] = c_fn
    track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.55)
    city.street(y0=-300, y1=1400, far=True, tree_gap=20.)
    S["tower"] = place("tower", 333.0, TOWER, .3)
    sm, S["wet"] = snow_mat(); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2500.0); S["snow"] = mesh_obj("snow", bm, [sm])
    wm, S["wW"], S["wB"] = water_mat(); bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2500.0); S["water"] = mesh_obj("water", bm, [wm])
    S["rain"] = Falling("rain", 9000) if rain else None; S["flakes"] = Falling("flakes", 5000, snow=True, seed=5) if snowfall else None
    S["flags"] = [Flag(f"flag{i}", (sx * 13.5, 70 + i * 9, 12.0), 6.5, col, math.pi / 2 if sx < 0 else -math.pi / 2) for i, (sx, col) in enumerate(((-1, (.85, .1, .1)), (1, (.1, .3, .8)), (-1, (.95, .7, .1)), (1, (.95, .95, .95))))]
    rnd = np.random.default_rng(41); S["fly"] = [(place("umbrella", 1.0, (0, 0, -50)), rnd.uniform(-20, 20), rnd.uniform(40, 110), rnd.uniform(12, 22), rnd.uniform(0, 4), rnd.uniform(0, 6.28)) for _ in range(14)]
    track.haze(col=(.7, .74, .8), k=.6, d0=200., d1=5000.)


def state_b(t, f, wind, center=None):
    c = S["c"](t); h = snow_h(c); w = water_h(c)
    wl = max(w, h + .04) if c > 9.0 else (w if (w > h - .2 and w > .02) else -1.0)
    keyp(S["snow"], f, loc=(0, 0, h)); keyp(S["water"], f, loc=(0, 0, wl)); key_v(S["wet"], clamp((c - 2.5) / 5.0), f); key_v(S["wW"], t * .35, f)
    for fl in S["flags"]:
        fl.wind = wind
    for k in ("rain", "flakes"):
        if S.get(k):
            S[k].wind = wind * (1.0 if k == "rain" else .7)
            if center is not None:
                S[k].center = center
    return c, h, w


def fly_umbrellas(t, f, wind):
    for (o, x0, y0, z0, t0, ph) in S["fly"]:
        tt = t - t0
        if tt < 0:
            keyp(o, f, loc=(0, 0, -50), rot=(0, 0, 0)); continue
        keyp(o, f, loc=(x0 + wind * .55 * tt - 30, y0 + 3 * math.sin(tt + ph), z0 + 4 * math.sin(tt * 1.7 + ph) + 2.5 * tt), rot=(tt * 5 + ph, tt * 3.3, tt * 2))


# ================================================================ ショット
C00 = ((9, CY + 22, 7.0), (-4, CY - 6, 5.0), 24)


def s_l00():
    crossing_world(clock("l00"))


def a_l00(u, t, f):
    p, at, l = C00; e = ease(u); P = Vector(p) + Vector((-1.5, -2, -.5)) * e; set_state(t, f, 6.0, P + Vector((0, -16, -4))); cam.look(P, at, l)


def s_l10():
    crossing_world(clock("l10"))


def a_l10(u, t, f):
    p, at, l = C00; e = ease(u); P = Vector(p) + Vector((4, 10, 4)) * (1 - e); set_state(t, f, 6.0, P + Vector((0, -16, -4))); cam.look(P, at, l)


def s_l01():
    crossing_world(clock("l01"))


def a_l01(u, t, f):
    e = ease(u); P = Vector((14, 34, 26)).lerp(Vector((10, 26, 18)), e); set_state(t, f, 8.0, Vector((0, CY, 6))); cam.look(P, Vector((0, CY - 4, -4)), 26)


def s_l02():
    crossing_world(clock("l02"))


def a_l02(u, t, f):
    e = ease(u); P = Vector((6.5, CY + 13, 1.7)).lerp(Vector((5.0, CY + 12, 1.6)), e); set_state(t, f, 8.0, P + Vector((0, -14, 6))); cam.look(P, (-1, CY - 2, 1.6), 30)


def s_l03():
    crossing_world(clock("l03"))


def a_l03(u, t, f):
    c, h, w = set_state(t, f, 10.0, Vector((0, CY, 14)))
    gone = h > .6                                                       # 雪が腰より上になる前に、人は逃げる（隠す）
    for p in S["ppl"]:
        keyhide(p.o, gone, f)
    for o in [bpy.data.objects.get(n) for n in ("crowd_still", "walk_still")] + S["umb"]:
        if o:
            keyhide(o, gone, f)
    e = ease(u); cam.look(Vector((16, 30, 14)).lerp(Vector((20, 40, 24)), e), Vector((0, CY - 6, 4 + 6 * e)), 26)


def s_l04():
    tower_world(clock("l04"))


def a_l04(u, t, f):
    e = ease(u); P = Vector((-6, 40, 0)); c, h, w = state_b(t, f, 72.5); P.z = h + 6; P = P + shake(f, .25)
    for k in ("rain", "flakes"):
        S[k].center = P + Vector((0, 18, -4))
    fly_umbrellas(t, f, 72.5); cam.look(P, Vector((TOWER.x * .8, TOWER.y, 150 + 40 * e)), 24)


def steam_card(name, loc, r):
    """湯気の板（+Y 向き、ノイズの透け）。体積の湯気は 1 コマ 14 秒かかったので板にした（5 秒前後）。返り値 (物, 濃さ)"""
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 5
    t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ln = t.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; t.links.new(tc.outputs["Object"], ln.inputs[0])
    edge = t.nodes.new("ShaderNodeMapRange"); edge.inputs[1].default_value = .2; edge.inputs[2].default_value = 1.0; edge.inputs[3].default_value = 1.0; edge.inputs[4].default_value = 0.0
    t.links.new(ln.outputs["Value"], edge.inputs[0])
    cr = t.nodes.new("ShaderNodeMapRange"); cr.inputs[1].default_value = .38; cr.inputs[2].default_value = .72; t.links.new(nz.outputs["Fac"], cr.inputs[0])
    m1 = t.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; t.links.new(edge.outputs[0], m1.inputs[0]); t.links.new(cr.outputs[0], m1.inputs[1])
    vl = t.nodes.new("ShaderNodeValue"); vl.outputs[0].default_value = .0
    m2 = t.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; t.links.new(m1.outputs[0], m2.inputs[0]); t.links.new(vl.outputs[0], m2.inputs[1])
    tr = t.nodes.new("ShaderNodeBsdfTransparent"); df = t.nodes.new("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (.92, .93, .95, 1)
    mx = t.nodes.new("ShaderNodeMixShader"); t.links.new(m2.outputs[0], mx.inputs[0]); t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(df.outputs[0], mx.inputs[2])
    t.links.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    m.cycles.emission_sampling = "NONE"
    bm = bmesh.new(); vs = [bm.verts.new(v) for v in ((-1, 0, -1), (1, 0, -1), (1, 0, 1), (-1, 0, 1))]; bm.faces.new(vs)
    o = mesh_obj(name, bm, [m]); o.location = loc; o.scale = (r, r, r); o.visible_shadow = False
    return o, vl.outputs[0]


def s_l05():
    crossing_world(clock("l05"), people_on=False)
    rnd = np.random.default_rng(51); S["steam"] = [steam_card(f"steam{i}", (rnd.uniform(-12, 12), CY + rnd.uniform(-38, -4), 0), rnd.uniform(4, 7)) for i in range(16)]
    bpy.context.scene.cycles.transparent_max_bounces = 48              # 湯気の板が重なると黒く抜けるので


def a_l05(u, t, f):
    c, h, w = set_state(t, f, 14.0, Vector((0, CY + 12, 14)))
    for i, (o, sock) in enumerate(S["steam"]):                         # 雪の面から湯気が立ちのぼる
        ph = (t * 1.2 + i * .7) % 6.0; keyp(o, f, loc=(o.location.x, o.location.y, h + 1.5 + ph * 1.3)); key_v(sock, .8 * math.sin(math.pi * ph / 6.0), f)
    e = ease(u); cam.look(Vector((2, CY + 8, h + 3.5)).lerp(Vector((1, CY, h + 3.0)), e), Vector((0, CY - 46, 15.5)), 26)


def s_l06():
    tower_world(clock("l06"))
    rnd = np.random.default_rng(61); n = 900; p0 = np.stack([rnd.choice([-1, 1], n) * rnd.uniform(16, 24, n), rnd.uniform(60, 220, n), rnd.uniform(25, 60, n)], 1)
    v0 = np.stack([-np.sign(p0[:, 0]) * rnd.uniform(1, 4, n), rnd.uniform(-1, 1, n), rnd.uniform(-1, 1, n)], 1)
    S["aval"] = city.Drops("aval", p0, v0, rnd.uniform(.4, 2.5, n), .5, mat("snowchunk", (.9, .92, .95), .7), g=9.8, drag=.6, seed=62)


def a_l06(u, t, f):
    k = smooth(.2, .5, t) * (1 - smooth(3.6, 4.7, t)); c, h, w = state_b(t, f, 40.0); P = Vector((-6, 30, h + 5)) + shake(f, 1.2 * k)
    for kk in ("rain", "flakes"):
        S[kk].center = P + Vector((0, 18, -4))
    S["tower"].rotation_euler = (math.radians(.6) * k * math.sin(t * 11), math.radians(.5) * k * math.sin(t * 9 + 1), .3); S["tower"].keyframe_insert("rotation_euler", frame=f + 1)
    key_v(S["wB"], .3 + 1.5 * k, f); fly_umbrellas(t, f, 40.0); cam.look(P, Vector((TOWER.x * .8, TOWER.y, 150)) + shake(f + 5, 1.2 * k), 24)


def s_l07():
    crossing_world(clock("l07"), people_on=False, snowfall=False)


def a_l07(u, t, f):
    c, h, w = set_state(t, f, 10.0, Vector((0, CY, 10))); key_v(S["wB"], .5, f)
    e = ease(u); cam.look(Vector((16, 32, 20)).lerp(Vector((18, 38, 26)), e), Vector((0, CY - 6, 2)), 26)


def s_l08():
    tower_world(clock("l08"), rain=False, snowfall=False); track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.2)
    rnd = np.random.default_rng(81); bt = mat("boat", (.9, .45, .1), .5); S["boats"] = []
    for i in range(9):                                                  # ゴムボートで避難する人（手を振る）
        x, y = rnd.uniform(-10, 10), rnd.uniform(18, 140)
        bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(1.8, 3.8, .55), verts=r_["verts"]); o = mesh_obj(f"boat{i}", bm, [bt])
        pp = people.People(f"rescue{i}", [(-.4, -.9), (.4, .1), (-.2, 1.0)], heading=rnd.uniform(-1, 1, 3), mode=1, seed=83 + i, bib=False); pp.o.parent = o; pp.o.location = (0, 0, .2)
        S["boats"].append((o, x, y))


def a_l08(u, t, f, t_off=0.0, cam_end=False):
    c, h, w = state_b(t, f, 3.0); key_v(S["wB"], .12, f)
    for (o, x, y) in S["boats"]:
        keyp(o, f, loc=(x + .3 * (t + t_off), y + .8 * (t + t_off), w + .25 + .05 * math.sin(t * 2 + x)), rot=(.03 * math.sin(t * 1.7 + x), .03 * math.sin(t * 1.3 + y), .2 * x))
    e = ease(u)
    if cam_end:
        cam.look(Vector((7, -14, 13)) + Vector((.5, -1, .5)) * u, Vector((2, 200, 20)), 28)
    else:
        cam.look(Vector((5, -6, 9)).lerp(Vector((7, -14, 13)), e), Vector((2, 200, 20)), 28)


def s_l09():
    s_l08()


def a_l09(u, t, f):
    a_l08(u, t, f, 5.0, True)


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
            sc.frame_set(int(round(at * K.FPS)) + 1); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            t0 = __import__("time").time(); bpy.ops.render.render(write_still=True); log("test", name, at, "render", round(__import__("time").time() - t0, 1), "s")
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
