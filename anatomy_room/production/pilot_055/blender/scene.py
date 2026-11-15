"""pilot_055「10万ボルトの電撃が、現実にあったら？」の 3D（Blender Cycles）。もしも設計の既定（templates/DESIGN_MODES.md）。
昼のバトル場（土のコートに白い線、まわりは芝生、Poly Haven の木）。電気を出すのは黄色い服の顔なしピクトグラムの人（作品のキャラクターは出さない）、
的は木の人形（5 m 先）。電撃は光る線（ぎざぎざの折れ線を毎コマ作り直す）。閃光（画面が白くなる光）は使わない。けがは描かない。
人の形（Puppet）は people.py の筒と球で、関節の位置をポーズから毎コマ計算する。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, people

NAMES = ["l00", "l01", "l02", "l03", "l04", "l05", "l05b", "l06", "l07", "l08"]
SIMO = PLAN["sim"]
AY, DY = -2.5, 2.5             # 人と的の y（5 m）
S = {}


# ---------------------------------------------------------------- 人（関節の位置から筒と球を組む）
class Puppet:
    SEG = [("torso", "hip", "neck", .15, .17), ("thL", "hipL", "kneeL", .085, .07), ("shL", "kneeL", "footL", .065, .05), ("thR", "hipR", "kneeR", .085, .07),
           ("shR", "kneeR", "footR", .065, .05), ("uaL", "shL", "elL", .058, .05), ("faL", "elL", "haL", .048, .042), ("uaR", "shR", "elR", .058, .05), ("faR", "elR", "haR", .048, .042)]
    COL = {"torso": "shirt", "uaL": "shirt", "uaR": "shirt", "thL": "pants", "thR": "pants"}

    def __init__(self, name, pose_fn, shirt=(.95, .78, .08), pants=(.08, .08, .1)):
        self.fn = pose_fn; self.cv, cf = people._capsule(12); self.hv, hf = people._ico(3); nc, nh = len(self.cv), len(self.hv)
        faces = []
        for i in range(len(self.SEG)):
            faces += [tuple(k + i * nc for k in fc) for fc in cf]
        o = len(self.SEG) * nc
        for j in range(3):                                                  # 頭・左手・右手
            faces += [tuple(k + o + j * nh for k in fc) for fc in hf]
        self.nv = o + 3 * nh
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((self.nv, 3)).tolist(), [], faces); me.update(); me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        me.materials.append(people._pmat()); skin = np.array(people.SKIN)
        col = np.zeros((self.nv, 3))
        for i, (p, *_r) in enumerate(self.SEG):
            c = self.COL.get(p); col[i * nc:(i + 1) * nc] = shirt if c == "shirt" else pants if c == "pants" else skin
        col[o:] = skin
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT"); ca.data.foreach_set("color", np.concatenate([col, np.ones((self.nv, 1))], 1).ravel())
        self.me = me; self.o = link(bpy.data.objects.new(name, me)); DYN.append(self.update); self.update(0.0)

    def update(self, t):
        J = self.fn(t); V = []
        for (p, a, b, r0, r1) in self.SEG:
            A, B = np.array(J[a]), np.array(J[b]); d = B - A; L = np.linalg.norm(d); d = d / max(L, 1e-6)
            X = np.cross(d, [0, 0, 1.0]) if abs(d[2]) < .95 else np.cross(d, [1.0, 0, 0]); X /= np.linalg.norm(X); Y = np.cross(d, X)
            tx, ty, tz, cap = self.cv[:, 0:1], self.cv[:, 1:2], self.cv[:, 2:3], self.cv[:, 3:4]; r = r0 + (r1 - r0) * tz
            V.append(A + d * (L * tz + r * cap * .75) + r * (tx * X + ty * Y))
        V += [np.array(J["head"]) + self.hv * .125, np.array(J["haL"]) + self.hv * .055, np.array(J["haR"]) + self.hv * .055]
        self.me.vertices.foreach_set("co", np.concatenate(V).astype(np.float32).ravel()); self.me.update()


def pose(x, y, k):
    """関節の位置。k：stand 立つ・charge ためる（こぶしを胸の前、少し沈む）・fire 右手を前へ・walk 歩く（ph）・raise 右手を相手の胸の前へ。
    値は 0〜1 の混ぜ具合の辞書。人は +Y を向く"""
    ch, fi, wk, ph, ra = k.get("charge", 0), k.get("fire", 0), k.get("walk", 0), k.get("ph", 0), k.get("raise", 0)
    bob = -.06 * ch - .04 * fi + .03 * wk * abs(math.sin(ph))
    hip = np.array([x, y + .06 * fi, .95 + bob]); up = np.array([0, .12 * fi + .05 * ch, 1.0]); up /= np.linalg.norm(up)
    neck = hip + up * .5; head = neck + up * .25
    J = {"hip": hip, "neck": neck, "head": head}
    for s, sx in (("L", -1), ("R", 1)):
        a = .45 * wk * math.sin(ph + (0 if s == "L" else math.pi))
        hp = hip + np.array([sx * .1, 0, -.04]); foot = np.array([x + sx * (.16 + .1 * ch + .06 * fi), y + math.sin(a) * .5 + (.25 if (s == "L" and fi) else -.15 if fi else 0) * fi, 0.05])
        kn = (hp + foot) / 2 + np.array([0, .12 + .06 * ch, 0])
        J["hip" + s] = hp; J["knee" + s] = kn; J["foot" + s] = foot
        sh = neck + np.array([sx * .2, 0, -.05])
        # 腕：立つ（下）・ためる（こぶしを胸の前）・撃つ（右は前へまっすぐ、左は後ろ）・歩く（振る）・近づけた手
        el_st = sh + np.array([sx * .04, .02, -.27]); ha_st = el_st + np.array([0, .03, -.25])
        el_ch = sh + np.array([sx * .2, .12, -.18]); ha_ch = neck + np.array([sx * .07, .25, -.12])
        if s == "R":
            el_fi = sh + np.array([-.03, .27, 0]); ha_fi = sh + np.array([-.06, .55, .0])
            el_ra = sh + np.array([-.05, .22, -.08]); ha_ra = sh + np.array([-.1, .42, -.12])
        else:
            el_fi = sh + np.array([-.05, -.15, -.2]); ha_fi = el_fi + np.array([.02, -.1, -.18])
            el_ra = el_st; ha_ra = ha_st
        sw = .35 * wk * math.sin(ph + (math.pi if s == "L" else 0))
        el_wk = sh + np.array([sx * .03, .27 * math.sin(sw), -.27 * math.cos(sw)]); ha_wk = el_wk + np.array([0, .25 * math.sin(sw + .3), -.25 * math.cos(sw + .3)])
        st = max(0.0, 1 - ch - fi - wk - ra)
        J["sh" + s] = sh
        J["el" + s] = st * el_st + ch * el_ch + fi * el_fi + wk * el_wk + ra * el_ra
        J["ha" + s] = st * ha_st + ch * ha_ch + fi * ha_fi + wk * ha_wk + ra * ha_ra
    return J


def fingertip(J):
    return np.array(J["haR"]) + (np.array(J["haR"]) - np.array(J["elR"])) / max(1e-6, np.linalg.norm(np.array(J["haR"]) - np.array(J["elR"]))) * .055


# ---------------------------------------------------------------- 電気（ぎざぎざの光る線）
def bolt_mat(name, col, k, alpha=1.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree
    for nd in list(t.nodes):
        if nd.type != "OUTPUT_MATERIAL":
            t.nodes.remove(nd)
    em = t.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*col, 1); em.inputs["Strength"].default_value = k
    if alpha < 1:
        tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader"); mx.inputs[0].default_value = alpha
        t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(em.outputs[0], mx.inputs[2]); t.links.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    else:
        t.links.new(em.outputs[0], t.nodes["Material Output"].inputs["Surface"])
    m.cycles.emission_sampling = "NONE"; return m


class Bolts:
    """arcs_fn(t) → [(A, B, ぎざぎざの幅, 太さ), ...]。芯（白っぽい黄）と、まわりのにじみ（太く薄い）の 2 本で描く。コマごとに形が変わる"""
    def __init__(self, name, arcs_fn, seed=1):
        self.fn = arcs_fn; self.seed = seed
        self.core = link(bpy.data.objects.new(name, bpy.data.curves.new(name, "CURVE"))); self.halo = link(bpy.data.objects.new(name + "_h", bpy.data.curves.new(name + "_h", "CURVE")))
        for o, m in ((self.core, bolt_mat(name + "_m", (1.0, .97, .7), 60.0)), (self.halo, bolt_mat(name + "_hm", (1.0, .85, .25), 5.0, .18))):
            o.data.dimensions = "3D"; o.data.bevel_resolution = 2; o.data.materials.append(m); o.visible_shadow = False
        DYN.append(self.update); self.update(0.0)

    def update(self, t):
        r = np.random.default_rng(self.seed + int(round(t * 30)) * 7)
        for o in (self.core, self.halo):
            o.data.splines.clear()
        for (A, B, amp, w) in self.fn(t):
            A, B = np.array(A, float), np.array(B, float); L = np.linalg.norm(B - A)
            if L < 1e-4:
                continue
            n = max(3, int(L / max(.004, amp * 1.2)) + 2); n = min(n, 60)
            d = (B - A) / L; X = np.cross(d, [0, 0, 1.0]); X = X / (np.linalg.norm(X) + 1e-9) if np.linalg.norm(X) > 1e-6 else np.array([1.0, 0, 0]); Y = np.cross(d, X)
            u = np.linspace(0, 1, n); env = np.sin(np.pi * u) ** .7
            P = A + np.outer(u, B - A) + (np.outer(r.normal(0, amp, n) * env, X) + np.outer(r.normal(0, amp, n) * env, Y))
            paths = [P]
            for _ in range(int(r.integers(0, 3)) if L > .05 else 0):                 # 枝分かれ
                i = int(r.integers(1, n - 1)); m_ = max(3, n // 3); dd = d * L * .3 + (X * r.normal(0, 1) + Y * r.normal(0, 1)) * L * .15
                Q = P[i] + np.outer(np.linspace(0, 1, m_), dd) + np.outer(r.normal(0, amp * .7, m_), X); paths.append(Q)
            for o, k in ((self.core, 1.0), (self.halo, 3.0)):
                for j, Q in enumerate(paths):
                    sp = o.data.splines.new("POLY"); sp.points.add(len(Q) - 1)
                    for p_, q in zip(sp.points, Q):
                        p_.co = (*q, 1.0)
                    sp.use_smooth = False
                o.data.bevel_depth = w * k
        # 曲線は 1 つの太さしか持てないので、太さはいちばん太い電撃に合わせる（同じショットではそろえる）


# ---------------------------------------------------------------- 舞台：昼のバトル場
def arena():
    env_clear(); sc.render.use_motion_blur = False; S.clear()
    track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.1, sun=(48., 200.), sun_k=3.0)
    g = track.pbr("sparse_grass", .5, 0.0, tint=(.55, .95, .42), name="lawn")
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2500.0); mesh_obj("lawn", bm, [g])
    dirt = track.pbr("grass_path_2", .35, 0.0, tint=(1.05, .95, .85), name="court")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(12, 20, .06), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, -.02), verts=bm.verts)
    mesh_obj("court", bm, [dirt])
    wh = mat("line", (.92, .92, .9), .6); xf = []
    for (x0, y0, x1, y1) in ((-5.6, -9.6, 5.6, -9.5), (-5.6, 9.5, 5.6, 9.6), (-5.6, -9.6, -5.5, 9.6), (5.5, -9.6, 5.6, 9.6), (-5.6, -.05, 5.6, .05)):
        xf.append(((x0 + x1) / 2, (y0 + y1) / 2, .012, x1 - x0, y1 - y0, .004, 0, 0, 0))
    for i in range(48):                                                  # 真ん中の円
        a = 2 * math.pi * i / 48; xf.append((1.6 * math.cos(a), 1.6 * math.sin(a), .012, .1, .22, .004, 0, 0, -a))
    instances("lines", CUBE_V, CUBE_F, xf, [wh])
    rnd = np.random.default_rng(5)                                     # 奥の木
    for i in range(46):
        e = link(bpy.data.objects.new(f"tree{i}", None)); e.instance_type = "COLLECTION"; e.instance_collection = track.model(["island_tree_01", "island_tree_02", "tree_small_02"][i % 3])
        a = rnd.uniform(-.3, 3.45); rr = rnd.uniform(24, 70); e.location = (rr * math.cos(a), 6 + rr * math.sin(a), 0); e.rotation_euler = (0, 0, rnd.uniform(0, 6.28)); e.scale = (rnd.uniform(.9, 1.3),) * 3
    dummy(); track.haze(col=(.78, .84, .9), k=.5, d0=80., d1=2500.)


def dummy():
    """木の的の人形（柱・わらの胴・頭・腕の横木・十字の台）"""
    wood = track.pbr("weathered_planks", 2.0, 0.0, name="wood"); straw = mat("straw", (.78, .64, .34), .85); xf = []
    o = []
    for (nm, r, z0, z1, m) in (("post", .06, 0, 1.55, wood), ("body", .24, .85, 1.45, straw)):
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=r, radius2=r, depth=z1 - z0); bmesh.ops.translate(bm, vec=(0, DY, (z0 + z1) / 2), verts=bm.verts)
        o.append(mesh_obj("dm_" + nm, bm, [m]))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=16, radius=.17); bmesh.ops.translate(bm, vec=(0, DY, 1.68), verts=bm.verts); o.append(mesh_obj("dm_head", bm, [straw]))
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=.04, radius2=.04, depth=1.0); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, DY, 1.35), verts=bm.verts); o.append(mesh_obj("dm_arm", bm, [wood]))
    for a in (0, math.pi / 2):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(.9, .1, .08), verts=bm.verts); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(a, 3, "Z"), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(0, DY, .04), verts=bm.verts); o.append(mesh_obj("dm_base", bm, [wood]))
    pv = link(bpy.data.objects.new("dm_root", None)); pv.location = (0, DY, 0); bpy.context.view_layer.update()   # 親の位置を先に確定（しないと的が 2 倍の y に行った）
    for x in o:
        x.parent = pv; x.matrix_parent_inverse = pv.matrix_world.inverted()
    S["dummy"] = pv


def ruler(A, d, length=.12):
    """定規（cm の目盛り、assets の tex/ruler.png）。A：0 の位置、d：向き（単位ベクトル）"""
    im = img_mat("ruler", .5, 0.0); A = Vector(A); d = Vector(d).normalized(); n = Vector((0, 0, 1)); w = .022
    P = [A - n * .012 * 0 + Vector((0, 0, -.03)), A + d * length + Vector((0, 0, -.03)), A + d * length + Vector((0, 0, -.03 - w)), A + Vector((0, 0, -.03 - w))]
    return mesh_obj("ruler", quad("q", [tuple(p) for p in (P[3], P[2], P[1], P[0])], im), [im])




# ================================================================ 人と電気の動き（時刻 t の関数：描くときに DYN が呼ぶ）
def crackle(J, t, n=5, r=.35, seed=0):
    """体のまわりをはう小さな電気（ためるとき）"""
    out = []; rg = np.random.default_rng(seed + int(t * 30))
    pts = [J["haR"], J["haL"], J["neck"], J["head"], J["elR"], J["elL"], J["hip"]]
    for i in range(n):
        A = np.array(pts[int(rg.integers(0, len(pts)))]); B = A + rg.normal(0, r * .5, 3)
        out.append((A, B, .02, .004))
    return out


def setup_people(pose_fn, arcs_fn):
    S["pup"] = Puppet("hero", pose_fn); S["bolts"] = Bolts("bolts", arcs_fn, seed=3)


def spark_from(J, cm):
    """指先から cm センチ前へ伸びる火花"""
    A = fingertip(J); B = A + np.array([0, cm / 100.0, 0]); return (A, B, .004, .0016)


# ================================================================ ショット
def s_l00():
    arena(); setup_people(lambda t: pose(0, AY, {"charge": .35}), lambda t: crackle(pose(0, AY, {"charge": .35}), t, 4, .3, 1))


def a_l00(u, t, f):
    e = ease(u); cam.look(Vector((2.6, -7.2, 1.8)).lerp(Vector((2.0, -6.4, 1.7)), e), Vector((0, .8, 1.1)), 28)


def s_l08():
    s_l00()


def a_l08(u, t, f):
    e = ease(u); cam.look(Vector((3.2, -8.2, 2.0)).lerp(Vector((2.6, -7.2, 1.8)), e), Vector((0, .8, 1.1)), 28)


def s_l01():
    def pf(t):
        return pose(0, AY, {"charge": smooth(0, .8, t)})
    arena(); setup_people(pf, lambda t: crackle(pf(t), t, 4 + int(10 * smooth(.3, 3.5, t)), .25 + .35 * smooth(.3, 3.5, t), 11))


def a_l01(u, t, f):
    e = ease(u); cam.look(Vector((1.5, -.6, 1.45)).lerp(Vector((1.1, -1.1, 1.4)), e), Vector((0, AY, 1.25)), 40)


SLOW = .25        # l02・l03 のスロー（1 秒＝ 0.25 秒）


def fire_pose(t):
    k = smooth(.0, .5, t); return pose(0, AY, {"charge": 1 - k, "fire": k})


def fire_arcs(t, slow=SLOW):
    """撃つ：指先から火花がのび、約 3.3 cm で止まって消える（スロー）"""
    J = fire_pose(t); tt = (t - 1.0) * slow                               # 撃った瞬間から（実時間）
    if tt < 0:
        return crackle(J, t, 3, .2, 21)
    cm = SIMO["cm_sphere"] * smooth(0, .05, tt) * (1 - smooth(.25, .4, tt))
    return [spark_from(J, cm)] + ([spark_from(J, cm * .8)] if tt < .3 else [])


def s_l02():
    arena(); setup_people(fire_pose, fire_arcs); J = fire_pose(2.0); ruler(fingertip(J), (0, 1, 0), .12)


def a_l02(u, t, f):
    e = ease(u); J = fire_pose(2.0); h = Vector(fingertip(J))
    cam.look(h + Vector((.85, -.05, .12)).lerp(Vector((.65, 0, .1)), e), h + Vector((0, .02, -.04)), 40)


def s_l03():
    def arcs(t):   # 指先のアップ：約 3.3 cm の火花がちらつき続ける
        J = fire_pose(2.0); r = np.random.default_rng(int(t * 30)); return [spark_from(J, SIMO["cm_sphere"] * r.uniform(.85, 1.0))] if r.random() < .8 else []
    arena(); setup_people(fire_pose, arcs); J = fire_pose(2.0); ruler(fingertip(J), (0, 1, 0), .12)


def a_l03(u, t, f):
    J = fire_pose(2.0); h = Vector(fingertip(J)); e = ease(u)
    cam.look(h + Vector((.32, .02, .06)).lerp(Vector((.26, .03, .05)), e), h + Vector((0, .03, -.01)), 60)


def s_l04():
    arena(); setup_people(lambda t: pose(0, AY, {"charge": .6}), lambda t: crackle(pose(0, AY, {"charge": .6}), t, 8, .4, 31))


def a_l04(u, t, f):
    a = -.5 + .9 * u; cam.look(Vector((8.5 * math.sin(a), -8.5 * math.cos(a) - 1, 3.6)), Vector((0, 0, .9)), 26)


def s_l05():
    def pf(t):
        return fire_pose(1.2)
    def arcs(t):
        J = pf(t); return [spark_from(J, SIMO["cm_sphere"])] if (t % 1.2) < .5 else crackle(J, t, 2, .1, 51)   # 10 万ボルトの火花は 3 cm（大きな電撃は l05b）
    arena(); setup_people(pf, arcs)
    yl = mat("tape", (.95, .8, .1), .5); xf = [(0, (AY + DY) / 2, .02, .05, DY - AY - .3, .004, 0, 0, 0)] + [(0, AY + .15 + i, .02, .22, .03, .005, 0, 0, 0) for i in range(6)]
    instances("tape", CUBE_V, CUBE_F, xf, [yl])


def a_l05(u, t, f):
    e = ease(u); cam.look(Vector((7.2, -.5, 3.6)).lerp(Vector((6.6, 0, 3.2)), e), Vector((0, 0, .8)), 28)


def s_l05b():
    """もし 1,500 万ボルトなら：太い電撃が 5 m 飛んで的に当たる（想像）。的がゆれ、胸に焦げ跡、煙"""
    def pf(t):
        return fire_pose(1.2)
    def arcs(t):
        J = pf(t); A = fingertip(J); B = np.array([0, DY - .24, 1.25]); k = smooth(.5, .8, t); fade = 1 - smooth(3.6, 4.4, t)
        if fade < .02:
            return crackle(J, t, 2, .1, 61)
        L = [(A, A + (B - A) * k, .07 * fade + .015, .009)]
        if k > .9:
            L += [(B, B + np.array([.4 * math.sin(i * 2.1), -.15, -.35 + .25 * math.cos(i * 1.7)]), .03, .009) for i in range(3)]   # 当たった所から散る枝
        return L
    arena(); setup_people(pf, arcs)
    sm = bpy.data.materials.new("smoke"); sm.use_nodes = True; b = sm.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (.32, .32, .33, 1); b.inputs["Alpha"].default_value = .45
    S["smoke"] = []
    for i in range(7):
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = mesh_obj(f"smoke{i}", bm, [sm]); o.visible_shadow = False; S["smoke"].append(o)
    bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=.13); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=(0, DY - .245, 1.22), verts=bm.verts); S["burn"] = mesh_obj("burn", bm, [mat("burnm", (.04, .03, .02), .9)])


def a_l05b(u, t, f):
    hit = t >= .8; keyhide(S["burn"], not hit, f)
    k = math.exp(-max(0, t - .8) * 2.5) * math.sin(max(0, t - .8) * 16) if hit else 0.0      # 的がゆれる
    S["dummy"].rotation_euler = (math.radians(9) * k, 0, 0); S["dummy"].keyframe_insert("rotation_euler", frame=f + 1)
    rg = np.random.default_rng(71)
    for i, o in enumerate(S["smoke"]):                                   # 煙がのぼって広がる
        tt = t - .9 - i * .25
        if tt < 0:
            keyp(o, f, loc=(0, DY, -5), scale=(.01, .01, .01)); continue
        r = .1 + .12 * tt; keyp(o, f, loc=(rg.uniform(-.15, .15) + .1 * tt, DY - .3 + rg.uniform(-.1, .1), 1.25 + .45 * tt), scale=(r, r, r))
    e = ease(u); P = Vector((.95, AY - 1.7, 1.65)).lerp(Vector((.85, AY - 1.3, 1.6)), e) + (shake(f, .03) if .8 <= t < 1.6 else Vector((0, 0, 0)))
    cam.look(P, Vector((-.1, DY - .5, 1.15)), 28)


def walk_pose(t):
    d = DY - .76 - AY; T = 2.6                                            # 指先が的の胸（半径 .24）から 約 3 cm 手前で止まる                                            # 2.6 秒で的の手前まで歩く
    w = smooth(0, .3, t) * (1 - smooth(T - .2, T, t)); y = AY + d * smooth(0, T, t) ** 1.0
    ra = smooth(T, T + .6, t)
    return pose(0, y, {"walk": w, "ph": t * 7.5, "raise": ra})


def s_l06():
    def arcs(t):
        J = walk_pose(t)
        if t < 3.4:
            return crackle(J, t, 2, .15, 41)
        A = fingertip(J); B = np.array([A[0], DY - .245, A[2]])             # 的の胸まで 約 3 cm → パチッ
        return [(A, B, .006, .0018), (A, B, .006, .0018)] if t < 3.9 else crackle(J, t, 2, .1, 43)
    arena(); setup_people(walk_pose, arcs)


def a_l06(u, t, f):
    J = walk_pose(t); y = J["hip"][1]; e = ease(u)
    m = (y + DY) / 2; k = smooth(1.2, 3.0, t)                             # はじめは肩の後ろから的を見て、近づいたら横から 2 人を
    cam.look(Vector((1.3, y - 2.0, 1.65)).lerp(Vector((2.2, m - .4, 1.45)), k), Vector((0, y + 2.2, 1.1)).lerp(Vector((0, m + .05, 1.15)), k), 26 + 16 * k)
    if t > 3.4:                                                          # パチッで的が少しゆれる
        k = math.exp(-(t - 3.4) * 3) * math.sin((t - 3.4) * 18); S["dummy"].rotation_euler = (math.radians(4) * k, 0, 0)
    else:
        S["dummy"].rotation_euler = (0, 0, 0)
    S["dummy"].keyframe_insert("rotation_euler", frame=f + 1)


def s_l07():
    s_l06()


def a_l07(u, t, f):
    a_l06(1.0, 6.0 + t, f); e = ease(u); cam.look(Vector((3.6, .4, 2.2)).lerp(Vector((4.2, .2, 2.6)), e), Vector((0, 1.4, 1.0)), 30)


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
