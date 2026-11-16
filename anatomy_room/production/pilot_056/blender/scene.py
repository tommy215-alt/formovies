"""pilot_056「頭の小さなプロペラで、空を飛んだら？」の 3D（Blender Cycles）。もしも設計の既定（templates/DESIGN_MODES.md）。
土管の置かれた空き地（板の塀、奥に家並み代わりの木）。頭に黄色い小さなプロペラを付けた子ども（顔なしピクトグラム、作品のキャラクターは出さない）。
足もとへ吹き下ろす風で砂・小石・葉が外へ飛び、土管が転がる。反動で体が逆に回る。軽自動車（Sketchfab "Small price car" by Oliv1e、CC BY）で大きさを比べる。
人の形（Puppet）は pilot_055 の関節つきピクトグラム（0.8 倍で子ども）。けがは描かない。閃光なし。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, people, city

NAMES = ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08"]
SIMO = PLAN["sim"]
KS = .8                        # 子どもの大きさ（大人のピクトグラムの 0.8 倍、身長 約 1.4 m）
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
    ch, fi, wk, ph, ra, spd = k.get("charge", 0), k.get("fire", 0), k.get("walk", 0), k.get("ph", 0), k.get("raise", 0), k.get("spread", 0)
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
        el_sp = sh + np.array([sx * .26, 0, -.06]); ha_sp = sh + np.array([sx * .5, .02, -.1])
        st = max(0.0, 1 - ch - fi - wk - ra - spd)
        J["sh" + s] = sh
        J["el" + s] = st * el_st + ch * el_ch + fi * el_fi + wk * el_wk + ra * el_ra + spd * el_sp
        J["ha" + s] = st * ha_st + ch * ha_ch + fi * ha_fi + wk * ha_wk + ra * ha_ra + spd * ha_sp
    return J



# ---------------------------------------------------------------- 舞台：土管の空き地
SKF = os.path.join(HERE, "..", "assets", "sketchfab")
PIPES = [(2.6, 1.2, .0), (3.65, 1.2, .0), (3.12, 1.2, .9)]       # 土管（直径 1 m、長さ 2 m）：下に 2 本、上に 1 本


def lot():
    env_clear(); sc.render.use_motion_blur = False; S.clear()
    track.world_hdri("kloofendal_43d_clear_puresky", exposure=-.1, sun=(50., 210.), sun_k=3.0)
    g = track.pbr("sparse_grass", .5, 0.0, tint=(.55, .95, .42), name="lawn")
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=2500.0); mesh_obj("lawn", bm, [g])
    dirt = track.pbr("grass_path_2", .35, 0.0, tint=(1.05, .95, .85), name="lotdirt")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(16, 16, .06), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 2, -.02), verts=bm.verts)
    mesh_obj("lot", bm, [dirt])
    # 板の塀（奥と左右）
    wood = track.pbr("weathered_planks", 1.0, 0.0, name="fence"); xf = []
    for i in range(80):
        x = -8 + i * .2; xf.append((x, 10.0, .8, .18, .03, 1.6, 0, 0, 0))
    for i in range(70):
        y = -4 + i * .2; xf.append((-8.0, y, .8, .03, .18, 1.6, 0, 0, 0)); xf.append((8.0, y, .8, .03, .18, 1.6, 0, 0, 0))
    S["fence"] = instances("fence", CUBE_V, CUBE_F, xf, [wood])
    # 土管
    con = track.pbr("brushed_concrete", 1.0, 0.0, tint=(.75, .74, .72), name="pipe"); S["pipes"] = []
    for i, (x, y, z) in enumerate(PIPES):
        bm = bmesh.new(); r = bmesh.ops.create_cone(bm, cap_ends=False, segments=40, radius1=.5, radius2=.5, depth=2.0)
        bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=.07); bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)
        o = mesh_obj(f"pipe{i}", bm, [con]); o.location = (x, y, z + .5); S["pipes"].append(o)
    rnd = np.random.default_rng(5)                                     # まわりの木
    for i in range(40):
        e = link(bpy.data.objects.new(f"tree{i}", None)); e.instance_type = "COLLECTION"; e.instance_collection = track.model(["island_tree_01", "island_tree_02", "tree_small_02"][i % 3])
        a = rnd.uniform(-.3, 3.45); rr = rnd.uniform(16, 60); e.location = (rr * math.cos(a), 8 + rr * math.sin(a), 0); e.rotation_euler = (0, 0, rnd.uniform(0, 6.28)); e.scale = (rnd.uniform(.9, 1.3),) * 3
    track.haze(col=(.78, .84, .9), k=.5, d0=80., d1=2500.)


# ---------------------------------------------------------------- 子ども（頭にプロペラ）
class Kid:
    """root（空の物）を浮かせて回す。人の形は root の中で 0.8 倍。プロペラは頭の上（直径 20 cm、本物の大きさ）"""
    def __init__(self, pose_k):
        self.root = link(bpy.data.objects.new("kid_root", None)); self.body = link(bpy.data.objects.new("kid_body", None)); self.body.parent = self.root; self.body.scale = (KS,) * 3
        self.pup = Puppet("kid", lambda t: pose(0, 0, pose_k(t)), shirt=(.98, .8, .1), pants=(.08, .12, .35)); self.pup.o.parent = self.body
        J = pose(0, 0, pose_k(0.0)); top = (np.array(J["head"]) + np.array([0, 0, .125])) * KS
        y = mat("prop", (1.0, .78, .05), .35)
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=.022, radius2=.022, depth=.05); bmesh.ops.translate(bm, vec=(0, 0, .025), verts=bm.verts)
        self.hub = mesh_obj("hub", bm, [y]); self.hub.parent = self.root; self.hub.location = tuple(top)
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=.008, radius2=.008, depth=.06); bmesh.ops.translate(bm, vec=(0, 0, .08), verts=bm.verts)
        for v in bm.verts:
            pass
        sh_ = mesh_obj("shaft", bm, [y]); sh_.parent = self.hub
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(.2, .028, .006), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, 0, .11), verts=bm.verts)
        bmesh.ops.rotate(bm, cent=(0, 0, .11), matrix=Matrix.Rotation(.18, 3, "X"), verts=bm.verts)
        self.blade = mesh_obj("blade", bm, [y]); self.blade.parent = self.hub
        dm = bpy.data.materials.new("blur"); dm.use_nodes = True; b = dm.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (1.0, .82, .2, 1); b.inputs["Alpha"].default_value = .22
        bm = bmesh.new(); bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=.1); bmesh.ops.translate(bm, vec=(0, 0, .11), verts=bm.verts)
        self.disk = mesh_obj("blurdisk", bm, [dm]); self.disk.parent = self.hub; self.disk.visible_shadow = False
        self.top = top

    def key(self, f, z, spin, prop_t):
        keyp(self.root, f, loc=(0, 0, z), rot=(0, 0, spin)); keyp(self.blade, f, rot=(0, 0, prop_t * 47.0))     # 羽根は見える速さで（本当は 1 分に 1.9 万回転）


# ---------------------------------------------------------------- 砂・小石・葉が外へ吹き飛ぶ（吹き下ろす風が地面で外へ広がる）
def blast(n=2600, t0=0.0, dur=6.0, seed=1, strength=1.0):
    r = np.random.default_rng(seed); a = r.uniform(0, 6.283, n); rr = r.uniform(.05, .6, n)
    p0 = np.stack([rr * np.cos(a), rr * np.sin(a), np.full(n, .03)], 1)
    sp = r.uniform(5, 14, n) * strength; v0 = np.stack([np.cos(a) * sp, np.sin(a) * sp, r.uniform(.5, 3.5, n)], 1)
    born = t0 + r.uniform(0, dur, n)
    sand = mat("sandgrain", (.42, .34, .25), .95)
    S["sand"] = city.Drops("sand", p0, v0, born, r.uniform(.005, .016, n), sand, g=9.8, drag=.8, seed=seed)
    m2 = 400; a2 = r.uniform(0, 6.283, m2); rr2 = r.uniform(.5, 4.0, m2)                    # 葉っぱ（ひらひら）
    p2 = np.stack([rr2 * np.cos(a2), rr2 * np.sin(a2), np.full(m2, .02)], 1); v2 = np.stack([np.cos(a2) * r.uniform(4, 9, m2), np.sin(a2) * r.uniform(4, 9, m2), r.uniform(1, 4, m2)], 1)
    S["leaves"] = city.Drops("leaves", p2, v2 * strength, t0 + r.uniform(0, dur, m2), r.uniform(.03, .06, m2), mat("leafm", (.35, .45, .12), .7), g=9.8, drag=1.2, flutter=1.0, card=True, seed=seed + 1)


def dust(n=10, seed=3):
    """足もとの砂ぼこりの輪（ノイズで透ける板を寝かせて、外へ広げる）"""
    S["dust"] = []
    for i in range(n):
        m = bpy.data.materials.new(f"dust{i}"); m.use_nodes = True; t = m.node_tree
        for nd in list(t.nodes):
            if nd.type != "OUTPUT_MATERIAL":
                t.nodes.remove(nd)
        tc = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 3
        t.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        ln = t.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"; t.links.new(tc.outputs["Object"], ln.inputs[0])
        rg = t.nodes.new("ShaderNodeMapRange"); rg.inputs[1].default_value = .3; rg.inputs[2].default_value = 1.0; rg.inputs[3].default_value = 1.0; rg.inputs[4].default_value = 0.0; t.links.new(ln.outputs["Value"], rg.inputs[0])
        cr = t.nodes.new("ShaderNodeMapRange"); cr.inputs[1].default_value = .4; cr.inputs[2].default_value = .75; t.links.new(nz.outputs["Fac"], cr.inputs[0])
        m1 = t.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; t.links.new(rg.outputs[0], m1.inputs[0]); t.links.new(cr.outputs[0], m1.inputs[1])
        vl = t.nodes.new("ShaderNodeValue"); vl.outputs[0].default_value = .6
        m2 = t.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; t.links.new(m1.outputs[0], m2.inputs[0]); t.links.new(vl.outputs[0], m2.inputs[1])
        tr = t.nodes.new("ShaderNodeBsdfTransparent"); df = t.nodes.new("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (.7, .6, .46, 1)
        mx = t.nodes.new("ShaderNodeMixShader"); t.links.new(m2.outputs[0], mx.inputs[0]); t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(df.outputs[0], mx.inputs[2])
        t.links.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"]); m.cycles.emission_sampling = "NONE"
        bm = bmesh.new(); vs = [bm.verts.new(v) for v in ((-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0))]; bm.faces.new(vs)
        o = mesh_obj(f"dust{i}", bm, [m]); o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False   # 照り返しの計算に入れない（1 コマ 9 秒の原因）
        S["dust"].append((o, vl.outputs[0], i / n))
    sc.cycles.transparent_max_bounces = 12   # 48 だと 1 コマ 9.5 秒。板は重なっても数枚なので 12 で足りる


def dust_key(t, f, k=1.0):
    for (o, sock, ph) in S["dust"]:
        q = (t * .55 + ph) % 1.0; r = .6 + 5.5 * q; keyp(o, f, loc=(0, 0, .15 + .9 * q * (0.3 + .7 * ph)), rot=(0, 0, ph * 6.0 + t * .3), scale=(r, r, 1)); key_v(sock, k * .75 * math.sin(math.pi * q), f)


def fence_shake(t, f, amp):
    S["fence"].location = (0, .02 * amp * math.sin(t * 23), 0); S["fence"].keyframe_insert("location", frame=f + 1)


# ================================================================ ショット
def hover_z(t, t0=0.0):
    return .02 + .55 * smooth(t0, t0 + 2.5, t) + .04 * math.sin(t * 2.3)


def kid(spread=.7):
    S["kid"] = Kid(lambda t: {"spread": spread})


def s_l00():
    lot(); kid(); blast(4200, 0, 4.5, 1, 1.3); dust(8)


def a_l00(u, t, f):
    S["kid"].key(f, hover_z(t + 1.0), 0.0, t); dust_key(t, f, 1.5); fence_shake(t, f, .9)    # 0 秒目から砂ぼこりが爆発的に
    e = ease(u); cam.look(Vector((1.4, -3.4, .45)).lerp(Vector((1.1, -2.9, .5)), e), Vector((0, 0, .7)), 24)


def s_l08():
    s_l00()


def a_l08(u, t, f):
    S["kid"].key(f, hover_z(t + 1.0), 0.0, t); dust_key(t, f); fence_shake(t, f, .6)
    e = ease(u); cam.look(Vector((2.1, -5.2, .95)).lerp(Vector((1.6, -4.2, .8)), e), Vector((0, 0, .75)), 26)


def s_l01():
    lot(); kid(); blast(1500, 0, 5.0, 2); dust(8, 4)


def a_l01(u, t, f):
    z = hover_z(t + 3.5); S["kid"].key(f, z, 0.0, t); dust_key(t, f); fence_shake(t, f, .5)
    e = ease(u); top = Vector(S["kid"].top) + Vector((0, 0, z))
    cam.look(Vector((.9, -1.7, z + .9)).lerp(Vector((.55, -1.05, z + 1.25)), e), Vector((0, 0, z + .9)).lerp(top + Vector((0, 0, .02)), e), 34 + 12 * e)


def s_l02():
    lot(); kid(); (None if os.environ.get("NOSAND") else blast(3600, 0, 5.2, 3, 1.2)); (None if os.environ.get("NODUST") else dust(8, 5))


def a_l02(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0), 0.0, t); (dust_key(t, f, 1.2) if S.get("dust") else None); fence_shake(t, f, 1.0)
    e = ease(u); cam.look(Vector((-.6, -3.4, .12)).lerp(Vector((-.4, -2.6, .1)), e), Vector((.2, 0, .35)), 22)


def s_l03():
    lot(); kid(); blast(2600, 0, 5.0, 4, 1.2); dust(10, 6)


def a_l03(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0), 0.0, t); dust_key(t, f, 1.1); fence_shake(t, f, 1.4)
    x, y, z = PIPES[2]; k = smooth(.6, 3.4, t); keyp(S["pipes"][2], f, loc=(x + 1.9 * k, y, z + .5 - .9 * smooth(1.4, 2.4, t)), rot=(0, 1.9 * k / .5, 0))   # 上の土管が転がり落ちる
    e = ease(u); cam.look(Vector((-1.4, -3.6, 1.3)).lerp(Vector((-1.0, -3.2, 1.2)), e), Vector((2.0, .8, .7)), 24)


def s_l04():
    lot(); kid(); blast(1800, 0, 6.0, 5); dust(8, 7)
    S["car"] = link(bpy.data.objects.new("i_car", None)); before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SKF, "car", "scene.gltf")); new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update(); pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)]); L = max(hi.x - lo.x, hi.y - lo.y)
    for o in new:
        if o.parent is None:
            o.parent = S["car"]
    s_ = 3.4 / L; S["car"].scale = (s_,) * 3; S["car"].location = Vector((-2.6, .6, 0)) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s_
    S["car"].rotation_euler = (0, 0, .5)


def a_l04(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0), 0.0, t); dust_key(t, f, .9); fence_shake(t, f, .8)
    e = ease(u); cam.look(Vector((.2, -4.4, 1.15)).lerp(Vector((-.4, -3.9, 1.1)), e), Vector((-1.3, .4, .75)), 24)


ALPHA = SIMO["alpha"]


def s_l05():
    lot(); kid(.85); blast(2200, 0, 6.0, 6); dust(10, 8); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5


def spin_angle(t, t0):
    tt = max(0.0, t - t0); return -.5 * ALPHA * tt * tt                     # プロペラと逆向き


def a_l05(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0), spin_angle(t, .6), t); dust_key(t, f); fence_shake(t, f, .8)
    e = ease(u); cam.look(Vector((1.5, -3.0, 1.0)).lerp(Vector((1.2, -2.5, 1.0)), e), Vector((0, 0, .9)), 30)


def s_l06():
    lot(); kid(.95); blast(3000, 0, 5.0, 7, 1.2); dust(12, 9); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5


def a_l06(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0) + .15 * smooth(0, 4, t), spin_angle(t + 5.0, .6), t); dust_key(t, f, 1.2); fence_shake(t, f, 1.0)
    a = .3 * u; cam.look(Vector((2.6 * math.sin(a) + .4, -3.2 * math.cos(a), .7)), Vector((0, 0, 1.0)), 26)


def s_l07():
    lot(); kid(.95); blast(2000, 0, 5.0, 10); dust(10, 11); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .5


def a_l07(u, t, f):
    S["kid"].key(f, hover_z(t + 4.0) + .15, spin_angle(t + 10.0, .6), t); dust_key(t, f); fence_shake(t, f, .8)
    e = ease(u); cam.look(Vector((2.4, -5.0, 1.6)).lerp(Vector((2.8, -5.8, 1.9)), e), Vector((.2, .8, .9)), 26)


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
