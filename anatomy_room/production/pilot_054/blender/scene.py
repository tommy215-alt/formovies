"""pilot_054「全人類 82 億人が、渋谷のスクランブル交差点に集まったら？」の 3D（Blender Cycles）。新もしも設計（templates/DESIGN_MODES.md）。
舞台は pilot_053 の交差点（city.street・横断歩道・大型画面・信号）。車はなし、道はすべて人。
人：1 m² のます目に 2 人ずつ（plan.py・crowd.py の密度）。道の上だけに置く（ビルの中には置かない）。
  人の形は people.py のピクトグラムを 1 人ずつ固めた型（シャツ 10 色 × 立つ・手を振る 2 コマ、遠くは胴と頭だけ）にし、crowd.Crowd で点に置く。
  交差点から 220 m より遠くは、人の色の点の模様の面（人の絨毯）で見せる。押しつぶし・けがは描かない。閃光なし。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city, people, crowd

NAMES = ["l00", "l01", "l02", "l03", "l08"]
SKF = os.path.join(HERE, "..", "assets", "sketchfab")
CY = -28.0                      # 交差点の中心の y（city.street の交差する道のすき間）
RN = 220.0                      # 本物の人を置く半径（これより遠くは人の絨毯）
CAM01 = [(2.0, CY + 4.0), (1.4, CY + 3.0)]   # 人の中の目の高さのカメラ（ここには人を置かない）
S = {}


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


# ---------------------------------------------------------------- 人
def templates():
    """人の型：シャツ i × 姿勢（0 立つ・1 2 手を振る）＝ i*3+姿勢、遠く用（胴と頭）＝ 30+i"""
    out = []
    for i, sh in enumerate(people.SHIRTS):
        for k, (mode, t) in enumerate(((2, 0.0), (1, 0.0), (1, .32))):
            p = people.People(f"tpl{i}_{k}", [(0, 0)], heading=0.0, mode=mode, seed=200 + i, shirts=[sh], bib=False); p.update(t)
            if p.update in DYN:
                DYN.remove(p.update)
            out.append(p.o)
    for i, sh in enumerate(people.SHIRTS):
        p = people.People(f"tpl{i}_far", [(0, 0)], heading=0.0, mode=2, seed=300 + i, shirts=[sh], bib=False, lod=1); p.update(0.0)
        if p.update in DYN:
            DYN.remove(p.update)
        out.append(p.o)
    for o in out:
        for c_ in list(o.users_collection):
            c_.objects.unlink(o)
    return out


def on_street(x, y):
    """道（大通り・交差点・交差する道）の上か。ビルの中には人を置かない"""
    W = city.RW + city.SW
    gap = ((y - (-1500.0)) % 140.0) > 124.0
    return (np.abs(x) < W - .3) | (np.abs(y - CY) < 8.0) | gap


def crowd_points(seed=7):
    """1 m のます目に 2 人ずつ（ます目の中でばらつかせる）。道の上だけ、半径 RN まで"""
    r = np.random.default_rng(seed); g = np.arange(-RN, RN, 1.0)
    X, Y = np.meshgrid(g, g + CY); X = X.ravel(); Y = Y.ravel()
    keep = on_street(X + .5, Y + .5) & (np.hypot(X + .5, Y + .5 - CY) < RN); X, Y = X[keep], Y[keep]
    P = []
    for a, b in (((.05, .45), (.05, .95)), ((.55, .95), (.05, .95))):   # ます目の左半分と右半分に 1 人ずつ
        P.append(np.stack([X + r.uniform(*a, len(X)), Y + r.uniform(*b, len(X))], 1))
    P = np.concatenate(P)
    for cx, cy in CAM01:                                                  # カメラの立つ所はあける
        P = P[np.hypot(P[:, 0] - cx, P[:, 1] - cy) > .9]
    return P


class Mass:
    """道を埋める人（crowd.Crowd の点）。近くの一部の人は手を振る"""
    def __init__(self):
        P = crowd_points(); N = len(P); r = np.random.default_rng(11); self.N = N
        z = np.where((np.abs(P[:, 0]) > city.RW) & (np.abs(P[:, 0]) < city.RW + city.SW) & (np.abs(P[:, 1] - CY) > 8.0), .15, 0.0)
        self.P = np.concatenate([P, z[:, None]], 1); d = np.hypot(P[:, 0], P[:, 1] - CY)
        self.shirt = r.integers(0, 10, N); self.far = d > 70.0
        self.wave = (~self.far) & (r.random(N) < .16); self.ph = r.uniform(0, 6.28, N); self.wf = r.uniform(3.5, 6.0, N)
        toward = np.arctan2(-(P[:, 0]), (CY - P[:, 1]))                   # 交差点（の上の画面）の方を向く人が多い
        self.R = np.where(r.random(N) < .55, toward + r.normal(0, .5, N), r.uniform(-math.pi, math.pi, N))
        sc_ = r.uniform(.9, 1.08, N)
        self.cr = crowd.Crowd("mass", templates(), self.pos, scale=sc_); log("people", N)

    def pos(self, t):
        F = np.where(self.far, 30 + self.shirt, self.shirt * 3 + np.where(self.wave, np.where(np.sin(t * self.wf + self.ph) > 0, 1, 2), 0))
        return self.P, self.R, F


def carpet_mat():
    """遠くの人の絨毯：1 人＝1 つの点（ボロノイ）、シャツの色と頭の色。交差点から RN より近くは透ける"""
    m = bpy.data.materials.new("carpet"); m.use_nodes = True; t = m.node_tree; L = t.links; b = t.nodes["Principled BSDF"]
    tc = t.nodes.new("ShaderNodeTexCoord"); vo = t.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 1.41; vo.feature = "F1"
    L.new(tc.outputs["Object"], vo.inputs["Vector"])
    cr = t.nodes.new("ShaderNodeValToRGB"); el = cr.color_ramp; el.interpolation = "CONSTANT"
    pal = list(people.SHIRTS) + [(.06, .05, .05), (.08, .07, .07)]
    while len(el.elements) < len(pal):
        el.elements.new(0)
    for k, c in enumerate(pal):
        el.elements[k].position = k / len(pal); el.elements[k].color = (*c, 1)
    L.new(vo.outputs["Color"], cr.inputs["Fac"])
    sep = t.nodes.new("ShaderNodeSeparateColor"); L.new(vo.outputs["Color"], sep.inputs[0])
    # 点の中心は頭（肌の色）、まわりは服、すき間は地面の暗い色
    dist = vo.outputs["Distance"]
    head = t.nodes.new("ShaderNodeMath"); head.operation = "LESS_THAN"; head.inputs[1].default_value = .12; L.new(dist, head.inputs[0])
    gap = t.nodes.new("ShaderNodeMath"); gap.operation = "GREATER_THAN"; gap.inputs[1].default_value = .44; L.new(dist, gap.inputs[0])
    m1 = t.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; L.new(head.outputs[0], m1.inputs[0]); L.new(cr.outputs[0], m1.inputs[6]); m1.inputs[7].default_value = (*people.SKIN, 1)
    m2 = t.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; L.new(gap.outputs[0], m2.inputs[0]); L.new(m1.outputs[2], m2.inputs[6]); m2.inputs[7].default_value = (.05, .05, .055, 1)
    L.new(m2.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .7
    # 本物の人がいる所（半径 RN の中の道）だけ透ける。ビルのすき間・裏道も人で埋まって見える
    def M(op, a, b_=None):
        n_ = t.nodes.new("ShaderNodeMath"); n_.operation = op
        for k, v in enumerate((a, b_)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n_.inputs[k].default_value = v
            else:
                L.new(v, n_.inputs[k])
        return n_.outputs[0]
    xyz = t.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], xyz.inputs[0]); X, Y = xyz.outputs[0], xyz.outputs[1]
    ln = t.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    sub = t.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = (0, CY, 0); L.new(tc.outputs["Object"], sub.inputs[0]); L.new(sub.outputs[0], ln.inputs[0])
    near = M("LESS_THAN", ln.outputs["Value"], RN - 3)
    s1 = M("LESS_THAN", M("ABSOLUTE", X), city.RW + city.SW - .3); s2 = M("LESS_THAN", M("ABSOLUTE", M("SUBTRACT", Y, CY)), 8.0)
    s3 = M("GREATER_THAN", M("FLOORED_MODULO", M("ADD", Y, 1500.0), 140.0), 124.0)
    street = M("MAXIMUM", M("MAXIMUM", s1, s2), s3); st = M("SUBTRACT", 1.0, M("MULTIPLY", street, near))
    tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader"); out = t.nodes["Material Output"]
    L.new(st, mx.inputs[0]); L.new(tr.outputs[0], mx.inputs[1]); L.new(b.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"])
    add_haze(m, 150., 4000., .8); return m


def ground_grid():
    """l02 の 1 m のます目（交差点の真ん中 9 m 四方、白い細い線）"""
    xf = []
    for k in range(-5, 5):
        xf.append((k + .0, CY, .012, .025, 10.0, .006, 0, 0, 0)); xf.append((0, CY + k, .012, 10.0, .025, .006, 0, 0, 0))
    return instances("grid", CUBE_V, CUBE_F, xf, [emat("gridm", (1, 1, 1), .4, (1, 1, 1), .6)])


# ---------------------------------------------------------------- 舞台：人で埋まった渋谷のスクランブル交差点
def crossing_world(grid=False):
    env_clear(); sc.render.use_motion_blur = False; S.clear()
    track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.1)
    city.street(y0=-1500, y1=1500, cross=140, tree_gap=24., far=True)
    pt = mat("paint", (.82, .82, .8), .55)
    city.box("cross_road", -3000, 3000, CY - 8, CY + 8, -.29, .0, track.pbr("brushed_concrete", .3, 0.0, tint=(.32, .32, .33), name="asph2"))
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
        mesh_obj(f"screen{i}", quad("q", P, im, flip=x < 0), [im])   # 左側の画面は字が裏返らないように
    for (x, y, r) in ((-16, CY + 9.5, 0), (16, CY - 9.5, math.pi), (-16, CY - 9.5, -math.pi / 2), (16, CY + 9.5, math.pi / 2)):
        place("signal", 6.0, (x, y, .15), r)
    S["mass"] = Mass()
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=3000.0); bmesh.ops.translate(bm, vec=(0, CY, 0), verts=bm.verts)
    S["carpet"] = mesh_obj("carpet", bm, [carpet_mat()]); S["carpet"].location.z = 1.0; S["carpet"].visible_shadow = False
    if grid:
        ground_grid()
    sc.cycles.transparent_max_bounces = 16
    track.haze(col=(.82, .86, .9), k=.42, d0=500., d1=9000.)


# ================================================================ ショット
P00 = (Vector((0, CY + 17, 8.5)), Vector((0, CY - 12, .5)), 24)


def s_l00():
    crossing_world()


def a_l00(u, t, f):
    p, at, l = P00; e = ease(u) ** 1.4
    cam.look(p.lerp(Vector((0, CY + 95, 135)), e), at.lerp(Vector((0, CY - 260, 0)), e), l)


def s_l01():
    crossing_world()


def a_l01(u, t, f):
    (x0, y0), (x1, y1) = CAM01; e = ease(u)
    cam.look(Vector((x0 + (x1 - x0) * e, y0 + (y1 - y0) * e, 1.62)), Vector((-8 - 6 * e, CY - 12, 3.5 + 6 * e)), 22)


def s_l02():
    crossing_world(grid=True)


def a_l02(u, t, f):
    e = ease(u); cam.look(Vector((0, CY + .01, 9.0 - 1.2 * e)), Vector((0, CY, 0)), 24)


def s_l03():
    crossing_world()


def a_l03(u, t, f):
    z = 9.0 * (1300.0 / 9.0) ** (ease(u) ** 1.2); cam.look(Vector((0, CY + .01, z)), Vector((0, CY, 0)), 24)


def s_l08():
    crossing_world()


def a_l08(u, t, f):
    p, at, l = P00; e = ease(u)
    cam.look(Vector((0, CY + 40, 30)).lerp(p, e), Vector((0, CY - 40, 0)).lerp(at, e), l)


# ---------------------------------------------------------------- 書き出し
ANIM = [cam.o]
SHOTS = {k: (globals()["s_" + k], (lambda a: (lambda u, t, f: (log("anim frame", f) if f % 30 == 0 else None, a(u, t, f))))(globals()["a_" + k])) for k in NAMES}

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
    cues, end = K.shot_lengths(HERE); order = ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08"]
    for name in O["shots"]:
        setup, anim = SHOTS[name]; i = order.index(name); b = cues[order[i + 1]] if i + 1 < len(order) else end
        n = int(math.ceil((b - cues[name]) * K.FPS)) + 2
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
    K.render_shots(HERE, SHOTS, ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08"], O, ANIM)
