"""pilot_053「日本の観測史上最大の記録が、東京で同時に起きたら？」の 3D（Blender Cycles）。l02（家の断面の図）は画面の図。
blender -b -P blender/scene.py -- l00 [l01 …] [--still] [--samples N] [--resume]
試し描き：AT="0.5,2.0" で work/test/<ショット>_<秒>.png（PCT で解像度 %）。
舞台は 1 つ（050 のビル街）に、雪の層（高さ）・水面（高さ・波）・雨（すじ）・風（雨の向き）・揺れ を時計 c（時間）から決めて重ねる。
雪の高さ H(c) ＝ 11.82 m ×（1 − c ÷ 23.8）、水の高さ W(c) ＝ 0.301 m × c（雪どけ＋雨 − 下水道）。雪の面が水面より下がると街が湖になる。
人は描かない（全員避難している設定）。霞の発光は照明として扱わない（common.add_haze）。"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city

NAMES = [s["id"] for s in PLAN["shots"]]
SNOW, MELT_H, WATER_END = PLAN["snow"], PLAN["melt_h"], PLAN["water_end"]
RATE = (SIM_ := PLAN["sim"])["inflow_mm_h"] / 1000 - .05          # 1 時間にたまる水 m（351 mm − 下水道 50 mm）
S = {}


def snow_h(c):
    return max(0.0, SNOW * (1 - c / MELT_H))


def water_h(c):
    return min(WATER_END, RATE * c)


def clock(k):
    s = SPLAN[k]; c = s["c"]; d = s["dur"]
    def f(t):
        u = clamp(t / d)
        for (u0, c0), (u1, c1) in zip(c, c[1:]):
            if u <= u1 or (u1, c1) == tuple(c[-1]):
                return c0 + (c1 - c0) * clamp((u - u0) / max(1e-9, u1 - u0))
        return c[-1][1]
    return f


# ---------------------------------------------------------------- 雪の層・水面・雨
def snow_mat():
    m = track.pbr("snow_field_aerial", .025, 0.0, tint=(1.18, 1.18, 1.22), name="snow", spec=.4); b = m.node_tree.nodes["Principled BSDF"]   # 上空から見た雪原（吹きだまりの模様）
    b.inputs["Subsurface Weight"].default_value = .25; b.inputs["Subsurface Radius"].default_value = (.4, .5, .6)
    wet = m.node_tree.nodes.new("ShaderNodeValue"); wet.name = "wet"; wet.outputs[0].default_value = 0.0     # 0＝乾いた雪、1＝水を含んだ雪（暗く、つやが出る）
    col_link = b.inputs["Base Color"].links[0]; src = col_link.from_socket
    mx = m.node_tree.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[7].default_value = (.32, .36, .38, 1)
    m.node_tree.links.new(wet.outputs[0], mx.inputs[0]); m.node_tree.links.new(src, mx.inputs[6]); m.node_tree.links.new(mx.outputs[2], b.inputs["Base Color"])
    return m, wet.outputs[0]


def water_mat():
    m = bpy.data.materials.new("flood"); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    b.inputs["Base Color"].default_value = (.06, .09, .07, 1); b.inputs["Roughness"].default_value = .06; b.inputs["IOR"].default_value = 1.33
    tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.noise_dimensions = "4D"; nz.inputs["Scale"].default_value = .8; nz.inputs["Detail"].default_value = 8
    L.new(tc.outputs["Object"], nz.inputs["Vector"]); bp = t.nodes.new("ShaderNodeBump"); bp.inputs["Distance"].default_value = .15; bp.inputs["Strength"].default_value = .25
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    add_haze(m, 300., 9000., .7); return m, nz.inputs["W"], bp.inputs["Strength"]


class Rain:
    """カメラのまわり（立方体 box）に降る雨のすじ N 本。update(t) で下へ（風で横へ）"""
    def __init__(self, N=9000, size=(50, 50, 24), seed=3):
        r = np.random.default_rng(seed); self.N = N; self.size = np.array(size, float); self.p0 = r.random((N, 3)) * self.size; self.sp = r.uniform(8, 10, N)
        self.center = Vector((0, 0, 0)); self.wind = 0.0; self.len = .6
        me = bpy.data.meshes.new("rain"); me.from_pydata(np.zeros((N * 4, 3)).tolist(), [], [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(N)]); me.update()
        m = mat("rain", (.85, .9, .95), .1); bs = m.node_tree.nodes["Principled BSDF"]; bs.inputs["Transmission Weight"].default_value = .6; bs.inputs["Alpha"].default_value = .8
        me.materials.append(m); self.me = me; self.o = link(bpy.data.objects.new("rain", me)); self.on = 1.0; DYN.append(self.update)

    def update(self, t):
        if self.on <= 0:
            self.me.vertices.foreach_set("co", np.zeros(self.N * 12, np.float32)); self.me.update(); return
        p = self.p0.copy(); p[:, 2] = (p[:, 2] - self.sp * t) % self.size[2]; p[:, 0] = (p[:, 0] + self.wind * t) % self.size[0]
        p = p - self.size / 2 + np.array(self.center); d = np.array([self.wind, 0, -9.0]); d = d / np.linalg.norm(d) * self.len
        w = np.array([0, .014, 0]); V = np.stack([p - w, p + w, p + w + d, p - w + d], 1)
        self.me.vertices.foreach_set("co", V.astype(np.float32).ravel()); self.me.update()


def base(c_fn, rain=0.0, wind=0.0):
    env_clear(); sc.render.use_motion_blur = False
    track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.2)            # 真夏の強い日ざし（雨の場面は下で暗く）
    city.street(y0=-300, y1=1400, far=True)
    sm, S["wet"] = snow_mat()
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1500.0); S["snow"] = mesh_obj("snow", bm, [sm])   # 平らな面＋質感の凹凸（厚みと形の凹凸は黒いすじが出た）
    wm, S["wW"], S["wB"] = water_mat()
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1500.0); S["water"] = mesh_obj("water", bm, [wm])   # 実際の大きさで作る（拡大すると質感の模様も引き伸ばされる）
    S["rain"] = Rain() if rain > 0 else None; S["c"] = c_fn; track.haze(col=(.8, .85, .92), k=.5)


def state(t, f, shake_amp=0.0):
    c = S["c"](t); h = snow_h(c); w = water_h(c)
    keyp(S["snow"], f, loc=(0, 0, max(.01, h))); keyp(S["water"], f, loc=(0, 0, max(-.5, w if h < w + .3 else -.5)))
    key_v(S["wet"], clamp(c / 6.0), f); key_v(S["wW"], t * .35, f)
    return c, h, w


# ---------------------------------------------------------------- ショット
def s_l00():
    base(clock("l00"))


C00 = ((18, -40, 46), (0, 120, 8), 28)


def a_l00(u, t, f):
    state(t, f); p, at, l = C00; e = ease(u); cam.look(Vector(p) + Vector((-3, 6, -2)) * e, at, l)


def s_l01():
    base(clock("l01"))


def a_l01(u, t, f):
    state(t, f); e = ease(u); p = Vector((15, -34, 44)).lerp(Vector((8, 10, 26)), e); cam.look(p, Vector((0, 160, 2)), 28)


def s_l09():
    base(clock("l09"))


def a_l09(u, t, f):
    state(t, f); p, at, l = C00; e = ease(u); cam.look(Vector(p) + Vector((6, -12, 6)) * (1 - e), at, l)


def s_l03():
    base(clock("l03")); S["steam"] = None


def a_l03(u, t, f):
    c, h, w = state(t, f); e = ease(u); cam.look((6, 20 + 6 * e, h + 4.5 - .5 * e), (-2, 110, h + 1), 30)


def s_l04():
    base(clock("l04"), rain=1.0); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.6); S["rain"].wind = 1.5


def a_l04(u, t, f):
    c, h, w = state(t, f); e = ease(u); p = Vector((4, 40 + 5 * e, h + 3.2)); S["rain"].center = p + Vector((0, 20, -6)); cam.look(p, (-3, 130, h + .5), 30)
    key_v(S["wB"], .25, f)


def s_l05():
    base(clock("l05"), rain=1.0); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.7); S["rain"].wind = 16.0; S["rain"].len = 1.2


def a_l05(u, t, f):
    c, h, w = state(t, f); e = ease(u); p = Vector((9, 60, h + 2.5)) + shake(f, .08 * e); S["rain"].center = p + Vector((0, 20, -6)); cam.look(p, (-4, 150, h + 1.2), 30)
    key_v(S["wB"], .6, f)


def s_l06():
    base(clock("l06"), rain=1.0); track.world_hdri("kloofendal_48d_partly_cloudy_puresky", exposure=-.7); S["rain"].wind = 15.0; S["rain"].len = 1.1


def a_l06(u, t, f):
    c, h, w = state(t, f); k = smooth(.2, .5, t) * (1 - smooth(3.6, 4.8, t)); p = Vector((9, 62, h + 2.6)) + shake(f, .9 * k); S["rain"].center = p + Vector((0, 20, -6))
    cam.look(p, Vector((-4, 150, h + 1.2)) + shake(f + 7, .9 * k), 30); key_v(S["wB"], .6 + 1.4 * k, f)


def s_l07():
    base(clock("l07")); track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.2)


def a_l07(u, t, f):
    c, h, w = state(t, f); e = ease(u); cam.look(Vector((30, -60, 70)).lerp(Vector((40, -90, 95)), e), Vector((0, 160, 0)), 28); key_v(S["wB"], .15, f)


def s_l08():
    base(clock("l08"))


def a_l08(u, t, f):
    c, h, w = state(t, f); cam.look(Vector((40, -90, 95)) + Vector((1, -2, 1)) * u, Vector((0, 160, 0)), 28); key_v(S["wB"], .15, f)


# ---------------------------------------------------------------- 書き出し
SHOTS3 = [k for k in NAMES if k != "l02"]
ANIM = [cam.o]
SHOTS = {k: (globals()["s_" + k], (lambda a: (lambda u, t, f: (log("anim frame", f) if f % 30 == 0 else None, a(u, t, f))))(globals()["a_" + k])) for k in SHOTS3}

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
