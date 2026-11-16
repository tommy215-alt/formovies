"""pilot_058「キリンぞりで、南極を横断したら？」の 3D（Blender Cycles）。もしも設計の既定。pilot_057（犬ぞり）の舞台を使い回す。
キリンは Sketchfab "Reticulated Giraffe - Rigged & Animated"（Animal Animator、CC BY）：走る・歩く・反すう・食べるの動き。4 頭（2 頭ずつ 2 列）でそりを引く。
そりは "Dog Sled"（sayumiQ、CC BY）を大きくして葉っぱの束を積む、人は "Arctic Explorer Posed"（ChloeRobynSmith、CC BY）。地図は NASA Blue Marble（PD）。閃光なし。けが・倒れる姿は描かない。
blender -b -P blender/scene.py -- l00 [l01 …] [--resume] [--samples N]、試し描き AT="1.5" PCT=30"""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *
import track, city

NAMES = ["l00", "l01", "l02", "l03", "l04", "l05", "l06", "l07", "l08"]
SIMO = PLAN["sim"]
S = {}
SKF = os.path.join(HERE, "..", "assets", "sketchfab")
SPEED = 11.0                   # 全力で駆けるキリン m/s（時速 約 40 km。画面の見た目）
WALK = 1.8                     # 歩くキリン m/s
GH = 5.0                       # キリンの背の高さ m
RUN = (0, 32)
NPAIR = 2                      # 2 頭ずつ 2 列＝4 頭
GAP = 5.2                      # 列の間 m


def imp(path):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=path); new = [o for o in bpy.data.objects if o not in before]
    for o in [o for o in new if o.name.startswith("Icosphere")]:       # 模型に入っている大きな球（使わない）
        new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    return new


def fit(new, length=None, height=None, axis=1):
    """読み込んだ物を 1 つの空の物にまとめ、長さ（axis 方向）か高さで大きさをそろえ、足もとを原点に"""
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    s_ = length / (hi[axis] - lo[axis]) if length else height / (hi.z - lo.z)
    root = link(bpy.data.objects.new("root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.scale = (s_,) * 3; root.location = -Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s_
    holder = link(bpy.data.objects.new("holder", None)); bpy.context.view_layer.update(); root.parent = holder; return holder


# ---------------------------------------------------------------- 舞台：氷の高原
def plateau(hdri="kloofendal_43d_clear_puresky", sun=(18., 120.), exposure=-.45, haze_k=.55, rot=0.0):
    env_clear(); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .35; S.clear()
    track.world_hdri(hdri, exposure=exposure, sun=sun, sun_k=3.2, rot=rot)
    snow = track.pbr("snow_02", .35, 0.0, tint=(.97, 1.0, 1.04), name="snow")
    far = track.pbr("snow_field_aerial", .012, 0.0, tint=(.95, .98, 1.03), name="snowfar")
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=6000.0); bmesh.ops.translate(bm, vec=(0, 0, -.25), verts=bm.verts)
    mesh_obj("far", bm, [far])
    # 近くはゆるい起伏と風紋（サスツルギ）：ノイズで高さを付けた細かい格子
    N = 220; L = 260.0; xs = np.linspace(-L / 2, L / 2, N); X, Y = np.meshgrid(xs, xs)
    Z = .35 * np.sin(X * .045 + 1.3) * np.cos(Y * .03) + .18 * np.sin(X * .23 + Y * .11) + .05 * np.sin(X * 1.7 + Y * .6) * np.sin(Y * 1.1)
    edge = np.clip((L / 2 - np.maximum(abs(X), abs(Y))) / 20.0, 0, 1); Z *= edge
    bm = bmesh.new(); vv = [bm.verts.new((float(X[j, i]), float(Y[j, i]), float(Z[j, i]))) for j in range(N) for i in range(N)]
    for j in range(N - 1):
        for i in range(N - 1):
            bm.faces.new((vv[j * N + i], vv[j * N + i + 1], vv[(j + 1) * N + i + 1], vv[(j + 1) * N + i]))
    S["ground"] = mesh_obj("ground", bm, [snow])
    for p in S["ground"].data.polygons:
        p.use_smooth = True
    S["gz"] = (xs, Z)
    track.haze(col=(.86, .9, .96), k=haze_k, d0=60., d1=2400.)


def gz(x, y):
    y = y - S.get("goff", 0.0); xs, Z = S["gz"]; L = xs[-1] - xs[0]; i = (x - xs[0]) / L * (len(xs) - 1); j = (y - xs[0]) / L * (len(xs) - 1)
    i = min(max(i, 0), len(xs) - 2); j = min(max(j, 0), len(xs) - 2); i0, j0 = int(i), int(j); a, b = i - i0, j - j0
    return float((Z[j0, i0] * (1 - a) + Z[j0, i0 + 1] * a) * (1 - b) + (Z[j0 + 1, i0] * (1 - a) + Z[j0 + 1, i0 + 1] * a) * b)


# ---------------------------------------------------------------- ハスキー（走る犬を塗り替えて複製）
def husky_mat(m, frost=None):
    """元の茶色の毛の明暗だけ使い、上を向いた面（背中・頭）は灰色、下（腹・脚・顔の下）は白に"""
    t = m.node_tree; b = t.nodes.get("Principled BSDF"); tex = next((l_.from_node for l_ in b.inputs["Base Color"].links), None)
    for l_ in list(b.inputs["Base Color"].links):
        t.links.remove(l_)
    bw = t.nodes.new("ShaderNodeRGBToBW")
    if tex:
        t.links.new(tex.outputs["Color"], bw.inputs[0])
    gm = t.nodes.new("ShaderNodeNewGeometry"); sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(gm.outputs["Normal"], sep.inputs[0])
    mk = t.nodes.new("ShaderNodeMapRange"); mk.inputs[1].default_value = -.7; mk.inputs[2].default_value = -.3; t.links.new(sep.outputs["Z"], mk.inputs[0])   # 腹（下を向いた面）は白
    # 高さ（足もとからの割合）：Position.z − 物の原点の z ＋ HB、÷ HH（HB・HH は team() で測って入れる）
    # 物の座標（骨で曲げた後）と世界の z の向き（行列の 3 行目、ZR）の内積＝原点からの高さ。HB＝足もと、HH＝体の高さ
    tco = t.nodes.new("ShaderNodeTexCoord"); zr = t.nodes.new("ShaderNodeCombineXYZ"); zr.name = "ZR"
    d1 = t.nodes.new("ShaderNodeVectorMath"); d1.operation = "DOT_PRODUCT"; t.links.new(tco.outputs["Object"], d1.inputs[0]); t.links.new(zr.outputs[0], d1.inputs[1])
    hb = t.nodes.new("ShaderNodeValue"); hb.name = "HB"; hb.outputs[0].default_value = 0.0; hh = t.nodes.new("ShaderNodeValue"); hh.name = "HH"; hh.outputs[0].default_value = .7
    d2 = t.nodes.new("ShaderNodeMath"); d2.operation = "ADD"; t.links.new(d1.outputs["Value"], d2.inputs[0]); t.links.new(hb.outputs[0], d2.inputs[1])
    d3 = t.nodes.new("ShaderNodeMath"); d3.operation = "DIVIDE"; t.links.new(d2.outputs[0], d3.inputs[0]); t.links.new(hh.outputs[0], d3.inputs[1])
    to = t.nodes.new("ShaderNodeTexCoord"); nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 5.0; t.links.new(to.outputs["Generated"], nz.inputs["Vector"])
    sgn = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(to.outputs["Generated"], sgn.inputs[0])        # 元の形（立った姿）の高さ 0〜1
    hz0 = t.nodes.new("ShaderNodeMath"); hz0.operation = "MULTIPLY_ADD"; t.links.new(nz.outputs["Fac"], hz0.inputs[0]); hz0.inputs[1].default_value = .12; t.links.new(sgn.outputs["Z"], hz0.inputs[2])
    hz = t.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = float(os.environ.get("HZ1", ".4")); hz.inputs[2].default_value = float(os.environ.get("HZ2", ".52")); t.links.new(hz0.outputs[0], hz.inputs[0])            # 脚・口もと（低い所）は白、高い所は灰色
    cl = t.nodes.new("ShaderNodeMath"); cl.operation = "MULTIPLY"; cl.use_clamp = True; t.links.new(hz.outputs[0], cl.inputs[0]); t.links.new(mk.outputs[0], cl.inputs[1])
    mx = t.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; t.links.new(cl.outputs[0], mx.inputs[0]); mx.inputs[6].default_value = (.78, .79, .8, 1) if not os.environ.get("DARK") else (.02, .02, .02, 1); mx.inputs[7].default_value = (.075, .078, .085, 1)
    sh = t.nodes.new("ShaderNodeMapRange"); sh.inputs[3].default_value = .7; sh.inputs[4].default_value = 1.35; t.links.new(bw.outputs[0], sh.inputs[0])
    mu = t.nodes.new("ShaderNodeMix"); mu.data_type = "RGBA"; mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0; t.links.new(mx.outputs[2], mu.inputs[6]); t.links.new(sh.outputs[0], mu.inputs[7])
    out = mu.outputs[2]
    if frost is not None:                                # 霜・雪（上を向いた面を白く、強さはコマごとに）
        fm = t.nodes.new("ShaderNodeMapRange"); fm.inputs[1].default_value = .35; fm.inputs[2].default_value = .8; t.links.new(sep.outputs["Z"], fm.inputs[0])
        fv = t.nodes.new("ShaderNodeValue"); fv.outputs[0].default_value = frost
        f2 = t.nodes.new("ShaderNodeMath"); f2.operation = "MULTIPLY"; f2.use_clamp = True; t.links.new(fm.outputs[0], f2.inputs[0]); t.links.new(fv.outputs[0], f2.inputs[1])
        fx = t.nodes.new("ShaderNodeMix"); fx.data_type = "RGBA"; t.links.new(f2.outputs[0], fx.inputs[0]); t.links.new(out, fx.inputs[6]); fx.inputs[7].default_value = (.95, .97, 1.0, 1)
        out = fx.outputs[2]; S.setdefault("frost", []).append(fv.outputs[0])
    t.links.new(out, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .9; b.inputs["Sheen Weight"].default_value = .05; b.inputs["Sheen Roughness"].default_value = .5
    b.inputs["Specular IOR Level"].default_value = .04; b.inputs["Coat Weight"].default_value = 0.0


def copy_tree(objs, suffix):
    mp = {o: o.copy() for o in objs}
    for o, c in mp.items():
        link(c)
        if o.parent in mp:
            c.parent = mp[o.parent]
        for md in c.modifiers:
            if getattr(md, "object", None) in mp:
                md.object = mp[md.object]
        c.name = o.name + suffix
    return mp


def run_nla(arm, off, speed=1.0, f0=RUN[0], f1=RUN[1], act=None):
    act = act or S["run_act"]; ad = arm.animation_data or arm.animation_data_create()
    slot = getattr(ad, "action_slot", None) if ad.action == act else None
    slot = slot or next((s_ for s_ in getattr(act, "slots", []) if s_.target_id_type == "OBJECT" and arm.name.split("_")[0] in s_.name_display), None)
    ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    tr = ad.nla_tracks.new(); st = tr.strips.new("run", 1, act)
    if hasattr(st, "action_slot") and len(getattr(act, "slots", [])):
        st.action_slot = slot or act.slots[0]
    st.action_frame_start = f0; st.action_frame_end = f1; st.scale = 30 / 24 / speed; st.repeat = 60
    st.frame_start = 1 - off * (f1 - f0) * st.scale
    st.extrapolation = "HOLD"


GACT = {"run": "03_Run_Gallop", "walk": "02_Walk", "idle": "01_Idle_Ruminating", "eat": "04_Eat_Browsing"}


def giraffe_template(snow=False):
    new = imp(os.path.join(SKF, "giraffe", "scene.gltf"))
    if snow:
        for o in new:
            if o.type == "MESH":
                for sl in o.material_slots:
                    m = sl.material; b = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
                    if b and not m.get("ok"):
                        snow_cover(m, b); m["ok"] = 1
    h = fit(new, height=GH, axis=2); return h, new


def act_of(kind):
    return next(a for a in bpy.data.actions if a.name.startswith(GACT[kind]))


def team(heading=0.0, n_pair=NPAIR, sled=True, musher=True, kind="run", speed=1.0, seed=1, snow=False):
    """隊の root。+Y が進む向き。キリンは y>0、そりは y<0"""
    r = np.random.default_rng(seed); S.setdefault("frost", [])
    root = link(bpy.data.objects.new("team", None)); root.rotation_euler = (0, 0, heading)
    h, objs = giraffe_template(snow); act = act_of(kind); S["run_act"] = act; arms = []
    tree = [h] + [o for o in bpy.data.objects if o.parent is not None and _anc(o, h)]
    for k in range(n_pair * 2):
        row, side = k // 2, (k % 2) * 2 - 1
        mp = copy_tree(tree, f"_{k}") if k else {o: o for o in tree}
        hk = mp[h]; hk.parent = root; hk.location = (side * .95, 3.6 + row * GAP + r.uniform(-.2, .2), 0); hk.rotation_euler = (0, 0, float(os.environ.get("GROT", str(math.pi))) + r.uniform(-.04, .04))
        sk = r.uniform(.93, 1.05); hk.scale = (sk,) * 3
        arm = next(o for o in mp.values() if o.type == "ARMATURE"); f0, f1 = act.frame_range
        run_nla(arm, r.uniform(0, 1), speed * r.uniform(.96, 1.04), int(f0), int(f1), act); arms.append((hk, arm))
    S["dogs"] = arms
    rope([(0, .4, 1.3)] + [(0, 3.6 + i * GAP - .6, 1.7) for i in range(n_pair)], .03, (.75, .1, .08), root)        # 引き綱（赤）
    for hk, arm in arms:
        x, y, _ = hk.location; rope([(0, y - 1.4, 1.7), (x * .8, y - .3, 1.9)], .016, (.1, .1, .12), root)
    if sled:
        sn = imp(os.path.join(SKF, "sled", "scene.gltf")); sh = fit(sn, length=3.6, axis=0); sh.parent = root; sh.rotation_euler = (0, 0, -math.pi / 2); sh.location = (0, -1.6, 0); S["sled"] = sh
        leaf = mat("leafbale", (.16, .32, .08), .85); r2 = np.random.default_rng(4)
        for k in range(14):                                                    # 積んだ葉っぱの束
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = mesh_obj(f"bale{k}", bm, [leaf]); o.parent = root
            o.location = (r2.uniform(-.45, .45), -1.2 + r2.uniform(-.9, .9), .75 + r2.uniform(0, .5)); o.scale = (r2.uniform(.3, .45), r2.uniform(.35, .5), r2.uniform(.22, .32))
            for p_ in o.data.polygons:
                p_.use_smooth = True
    if musher:
        mn = imp(os.path.join(SKF, "explorer", "scene.gltf")); mh = fit(mn, height=1.75, axis=2); mh.parent = root; mh.location = (0, -3.6, .12); S["musher"] = mh
    S["team"] = root; return root


def _anc(o, h):
    while o.parent is not None:
        if o.parent == h:
            return True
        o = o.parent
    return False


def rope(P, r, col, parent):
    cu = bpy.data.curves.new("rope", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 2
    sp = cu.splines.new("POLY"); sp.points.add(len(P) - 1)
    for k, p in enumerate(P):
        sp.points[k].co = (*p, 1)
    o = link(bpy.data.objects.new("rope", cu)); o.data.materials.append(mat("rope" + str(col), col, .7)); o.parent = parent; return o


def team_key(f, x, y, z=None, heading=0.0):
    z = gz(x, y) if z is None else z; keyp(S["team"], f, loc=(x, y, z), rot=(0, 0, heading))


# ---------------------------------------------------------------- 地吹雪・舞う雪・蹴り上げる雪・白い息
def drift(n=14, seed=3, wind=(1, 0), k=1.0, h=.8):
    """地面をはう雪煙：ノイズで透ける細長い板を、風の向きに流す"""
    S["drift"] = []; S["wind"] = Vector((*wind, 0)).normalized()
    for i in range(n):
        m = bpy.data.materials.new(f"drift{i}"); m.use_nodes = True; t = m.node_tree
        for nd in list(t.nodes):
            if nd.type != "OUTPUT_MATERIAL":
                t.nodes.remove(nd)
        tc = t.nodes.new("ShaderNodeTexCoord"); mp_ = t.nodes.new("ShaderNodeMapping"); mp_.inputs["Scale"].default_value = (.35, 1.4, 1.0); t.links.new(tc.outputs["Object"], mp_.inputs["Vector"])
        nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.2; nz.inputs["Detail"].default_value = 4; t.links.new(mp_.outputs["Vector"], nz.inputs["Vector"])
        sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(tc.outputs["Generated"], sep.inputs[0])
        e1 = t.nodes.new("ShaderNodeMath"); e1.operation = "PINGPONG"; e1.inputs[1].default_value = .5; t.links.new(sep.outputs["Z"], e1.inputs[0])
        e2 = t.nodes.new("ShaderNodeMath"); e2.operation = "PINGPONG"; e2.inputs[1].default_value = .5; t.links.new(sep.outputs["X"], e2.inputs[0])
        ed = t.nodes.new("ShaderNodeMath"); ed.operation = "MULTIPLY"; t.links.new(e1.outputs[0], ed.inputs[0]); t.links.new(e2.outputs[0], ed.inputs[1])
        es = t.nodes.new("ShaderNodeMapRange"); es.inputs[2].default_value = .08; t.links.new(ed.outputs[0], es.inputs[0])
        cr = t.nodes.new("ShaderNodeMapRange"); cr.inputs[1].default_value = .42; cr.inputs[2].default_value = .78; t.links.new(nz.outputs["Fac"], cr.inputs[0])
        m1 = t.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; t.links.new(es.outputs[0], m1.inputs[0]); t.links.new(cr.outputs[0], m1.inputs[1])
        vl = t.nodes.new("ShaderNodeValue"); vl.outputs[0].default_value = .5
        m2 = t.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; t.links.new(m1.outputs[0], m2.inputs[0]); t.links.new(vl.outputs[0], m2.inputs[1])
        tr = t.nodes.new("ShaderNodeBsdfTransparent"); df = t.nodes.new("ShaderNodeBsdfDiffuse"); df.inputs["Color"].default_value = (.93, .96, 1.0, 1)
        mx = t.nodes.new("ShaderNodeMixShader"); t.links.new(m2.outputs[0], mx.inputs[0]); t.links.new(tr.outputs[0], mx.inputs[1]); t.links.new(df.outputs[0], mx.inputs[2])
        t.links.new(mx.outputs[0], t.nodes["Material Output"].inputs["Surface"]); m.cycles.emission_sampling = "NONE"
        bm = bmesh.new(); vs = [bm.verts.new(v) for v in ((-1, -.5, 0), (1, -.5, 0), (1, .5, 0), (-1, .5, 0))]; bm.faces.new(vs)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"), verts=bm.verts)   # 立てた板（風の向きに長い）
        o = mesh_obj(f"drift{i}", bm, [m]); o.visible_shadow = False; o.visible_diffuse = False; o.visible_glossy = False; o.visible_transmission = False
        S["drift"].append((o, vl.outputs[0], i / n, k, h))
    sc.cycles.transparent_max_bounces = 16


def drift_key(t, f, center, span=30.0, k=1.0):
    w = S["wind"]; side = Vector((-w.y, w.x, 0)); r = np.random.default_rng(7)
    for i, (o, sock, ph, k0, h) in enumerate(S["drift"]):
        q = (t * .22 + ph) % 1.0; off = (q - .5) * span * 1.6; lat = ((i * 7.31) % 1.0 - .5) * span * .8
        p = center + w * off + side * lat; sx = 4.0 + 6.0 * ((i * 3.7) % 1.0); sz = h * (.5 + ((i * 5.3) % 1.0))
        keyp(o, f, loc=(p.x, p.y, gz(p.x, p.y) + sz * .45), rot=(0, 0, math.atan2(w.y, w.x)), scale=(sx, 1, sz))
        key_v(sock, k * k0 * .55 * math.sin(math.pi * q), f)


def flakes(n=6000, box=(-20, 20, -20, 20, 0, 8), wind=(9.0, 0.0), fall=1.2, size=(.006, .014), seed=5, dur=8.0):
    """舞う雪：小さな白い粒が風に流される（重力のかわりに一定の落ちる速さ）"""
    r = np.random.default_rng(seed); x0, x1, y0, y1, z0, z1 = box
    p0 = np.stack([r.uniform(x0, x1, n), r.uniform(y0, y1, n), r.uniform(z0, z1, n)], 1)
    w = np.array([*wind, -fall]); v0 = w[None] * r.uniform(.7, 1.3, (n, 1)) + r.normal(0, .4, (n, 3))
    p0 -= v0 * (dur * .5)                                    # 書き出しの最初から画面いっぱいに
    S["flakes"] = city.Drops("flakes", p0, v0, np.full(n, -1.0), r.uniform(*size, n), mat("flake", (.96, .98, 1.0), .5), g=0.0, life=99., seed=seed, floor=-99.)


def kick(n=2400, seed=9, dur=8.0):
    """犬の足が蹴り上げる雪（隊の root の位置から、犬ごとに後ろへ）。t ごとに隊の位置を足すので DYN で動かす"""
    r = np.random.default_rng(seed); nd = len(S["dogs"]); idx = r.integers(0, nd, n); born = r.uniform(-.5, dur, n)
    loc = np.array([tuple(S["dogs"][i][0].location) for i in idx]) + np.stack([r.normal(0, .35, n), r.uniform(-1.2, 1.0, n), np.full(n, .03)], 1)
    sp = S.get('spd', SPEED); v0 = np.stack([r.normal(0, .8, n), r.uniform(-sp - 1.5, -sp + .5, n), r.uniform(.8, 3.0, n)], 1)   # 隊から見ると後ろへ流れる
    S["kick"] = (loc, v0, born)
    d = city.Drops("kick", loc, v0, born, r.uniform(.01, .035, n), mat("kickm", (.95, .97, 1.0), .6), g=6.0, drag=0.0, life=1.1, seed=seed, floor=.02)
    d.o.parent = S["team"]; S["kickd"] = d


def breath(nose, n=5, seed=2):
    """白い息（ふわっと広がって消える小さな雲）"""
    S["breath"] = []
    for i in range(n):
        m = bpy.data.materials.new(f"breath{i}"); m.use_nodes = True; t = m.node_tree; t.nodes.clear()
        out = t.nodes.new("ShaderNodeOutputMaterial"); vol = t.nodes.new("ShaderNodeVolumePrincipled"); vol.inputs["Color"].default_value = (.95, .97, 1.0, 1)
        vv = t.nodes.new("ShaderNodeValue"); vv.outputs[0].default_value = 0.0; t.links.new(vv.outputs[0], vol.inputs["Density"]); t.links.new(vol.outputs[0], out.inputs["Volume"])
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = mesh_obj(f"breath{i}", bm, [m]); o.parent = nose
        o.visible_shadow = False; S["breath"].append((o, vv.outputs[0], i / n))


def breath_key(t, f):
    for (o, sock, ph) in S["breath"]:
        q = (t * 1.6 + ph) % 1.0; r = .03 + .14 * q; keyp(o, f, loc=(0, .12 + .35 * q, .02 + .05 * q), scale=(r, r * 1.3, r * .8)); key_v(sock, 6.0 * (1 - q) ** 2 * min(1, q * 8), f)


# ================================================================ ショット
def s_l00():
    plateau(sun=(16., 160.), haze_k=.6); S["spd"] = SPEED; team(kind="run", speed=1.0); kick(3000); drift(16, 3, (1, -.25), 1.2, 1.4); flakes(7000, (-30, 30, -40, 40, 0, 12), (10.0, -2.5), 1.0)


def a_l00(u, t, f):
    y = -30.0 + SPEED * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 8, 0)), 40, 1.3)
    cy = y + 19.0 - 4.0 * u; cam.look(Vector((1.8, cy, gz(1.8, cy) + .45)), Vector((0, y + 8.0, gz(0, y + 8) + 2.8)), 20)        # 正面の低い位置。見上げる


def s_l08():
    s_l00()


def a_l08(u, t, f):
    tt = t + 3.6; y = -30.0 + SPEED * tt; team_key(f, 0, y); drift_key(tt, f, Vector((0, y + 8, 0)), 40, 1.3)
    cy = -30.0 + SPEED * 3.6 + 19.0 - 4.0 + 3.0 * u; cam.look(Vector((1.8, cy, gz(1.8, cy) + .45)), Vector((0, y + 8.0, gz(0, y + 8) + 2.8)), 20)


# l01：地図（Blue Marble の南極、正射図法。極が原点、1 単位＝100 km、上が経度 0°、右が東経 90°）
R_E = 63.71
ROUTE = [(-65.1, -60.0), (-67.5, -64.5), (-70.5, -67.0), (-74.0, -72.0), (-77.5, -78.0), (-80.3, -81.4), (-84.0, -85.0), (-87.5, -60.0), (-90.0, 0.0),
         (-86.0, 100.0), (-82.0, 104.0), (-78.5, 106.8), (-74.1, 97.5), (-70.0, 94.0), (-66.55, 93.0)]


def polar(lat, lon):
    r = R_E * math.cos(math.radians(lat)); a = math.radians(lon); return (r * math.sin(a), r * math.cos(a))


def s_l01():
    env_clear(); sc.render.use_motion_blur = False; S.clear()
    w = sc.world.node_tree; w.nodes.clear(); bg = w.nodes.new("ShaderNodeBackground"); bg.inputs["Color"].default_value = (.0012, .0022, .016, 1); bg.inputs["Strength"].default_value = 1.0
    w.links.new(bg.outputs[0], w.nodes.new("ShaderNodeOutputWorld").inputs[0]); sc.view_settings.exposure = 0.0
    img = bpy.data.images.load(os.path.join(HERE, "..", "assets", "photo", "antarctica_bluemarble.jpg"), check_existing=True)
    m = bpy.data.materials.new("map"); m.use_nodes = True; t = m.node_tree; t.nodes.clear(); tx = t.nodes.new("ShaderNodeTexImage"); tx.image = img; tx.interpolation = "Cubic"
    em = t.nodes.new("ShaderNodeEmission"); em.inputs["Strength"].default_value = 1.6; t.links.new(tx.outputs["Color"], em.inputs["Color"]); t.links.new(em.outputs[0], t.nodes.new("ShaderNodeOutputMaterial").inputs["Surface"])
    half = 6400 / 2 * (R_E / (902 * 8))                       # 画像の半分の幅（R＝902×8 px が地球の半径）
    bm = bmesh.new(); vs = [bm.verts.new((sx * half, sy * half, 0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; fc = bm.faces.new(vs)
    uv = bm.loops.layers.uv.new()
    for lp in fc.loops:
        lp[uv].uv = ((lp.vert.co.x / half + 1) / 2, (lp.vert.co.y / half + 1) / 2)
    mesh_obj("map", bm, [m])
    P = [(*polar(a, b), .05) for a, b in ROUTE]
    cu = bpy.data.curves.new("route", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = .22; cu.bevel_resolution = 3
    sp = cu.splines.new("NURBS"); sp.points.add(len(P) - 1); sp.order_u = 3; sp.use_endpoint_u = True
    for k, p in enumerate(P):
        sp.points[k].co = (*p, 1)
    rm = emat("routem", (1.0, .12, .04), emit=(1.0, .12, .04), k=1.3, haze=False); o = link(bpy.data.objects.new("route", cu)); o.data.materials.append(rm); S["route"] = cu
    cu2 = bpy.data.curves.new("jp", "CURVE"); cu2.dimensions = "3D"; cu2.bevel_depth = .22; sp2 = cu2.splines.new("POLY"); sp2.points.add(1)
    sp2.points[0].co = (-15, 25.5, .05, 1); sp2.points[1].co = (15, 25.5, .05, 1)
    jm = emat("jpm", (1.0, .7, .0), emit=(1.0, .7, .0), k=1.3, haze=False); o2 = link(bpy.data.objects.new("jp", cu2)); o2.data.materials.append(jm); S["jp"] = cu2
    for (lat, lon) in (ROUTE[0], ROUTE[-1]):                 # 出発と到着の点
        bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=32, radius1=.75, radius2=.75, depth=.1); o = mesh_obj("pin", bm, [rm]); o.location = (*polar(lat, lon), .08)


def a_l01(u, t, f):
    k = smooth(2.3, 4.3, t); S["route"].bevel_factor_end = max(.001, k); S["route"].keyframe_insert("bevel_factor_end", frame=f + 1)
    j = smooth(3.9, 4.9, t); S["jp"].bevel_factor_end = max(.001, j); S["jp"].keyframe_insert("bevel_factor_end", frame=f + 1)
    e = ease(u); z = 96 - 18 * e
    cam.look(Vector((-1.0 + 2 * e, -30 + 10 * e, z)), Vector((1.0, 2.0, 0)), 30)


def s_l02():
    plateau(sun=(20., 150.)); S["spd"] = SPEED; team(kind="run", seed=3); kick(3000, 11); drift(12, 5, (1, .2), .8, .9); flakes(3000, (-30, 30, -10, 90, 0, 9), (6.0, 1.0), .8, (.006, .014), 7)


def a_l02(u, t, f):
    y = SPEED * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 6, 0)), 30, .8)
    cx, cy = 13.0 - 1.0 * u, y + 2.0 + 2.0 * u; cam.look(Vector((cx, cy, gz(cx, cy) + 1.6)), Vector((0, y + 4.5 + .6 * u, gz(0, y + 4) + 2.2)), 24)    # 横から並走


def s_l03():
    plateau(sun=(22., 200.), rot=180.0); S["spd"] = WALK; team(kind="walk", seed=4); kick(500, 12); drift(12, 6, (1, .1), 1.0, 1.0); flakes(4000, (-25, 25, -10, 40, 0, 9), (7.0, 1.0), 1.0, (.006, .014), 8)


def a_l03(u, t, f):
    y = WALK * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 6, 0)), 30, 1.0)
    e = ease(u); cam.look(Vector((-6.5 + 1.0 * e, y + 15.0 - 1.5 * e, gz(-6, y + 14) + 1.2)), Vector((0, y + 5.0, gz(0, y + 5) + 3.2)), 26)   # 前から、ゆっくり歩く首の長い隊


def s_l04():
    plateau(hdri="kloofendal_overcast_puresky", sun=(10., 100.), exposure=-.25, haze_k=.8); S["frost"] = []; S["spd"] = WALK; team(kind="walk", seed=5, speed=.8, snow=True); kick(400, 13)
    drift(26, 4, (1, .1), 2.0, 2.8); flakes(14000, (-40, 50, -5, 40, 0, 14), (16.0, 1.5), 1.5, (.008, .02), 6)


def a_l04(u, t, f):
    for s_ in S["frost"]:
        key_v(s_, .25 + .3 * u, f)
    x = -6.0 + WALK * .8 * t; team_key(f, x, 12.0, heading=-math.pi / 2); drift_key(t, f, Vector((x, 11, 0)), 40, 2.0)
    cam.look(Vector((-2.0 + 2.0 * u, -2.5, gz(-2, -2.5) + 1.4)), Vector((x + 4.0, 12.0, gz(x, 12) + 3.0)), 30)


def s_l05():
    plateau(sun=(20., 330.), haze_k=.5); S["spd"] = 0.0; team(kind="eat", seed=6, musher=False)
    leaf = MATS.get("leafbale") or mat("leafbale", (.16, .32, .08), .85); r2 = np.random.default_rng(9)
    for k in range(22):                                                      # 前におろした葉っぱの山
        bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0); o = mesh_obj(f"pile{k}", bm, [leaf])
        x, y = r2.uniform(-1.6, 1.6), r2.uniform(10.5, 13.0); o.location = (x, y, gz(x, y) + r2.uniform(.1, .5)); o.scale = (r2.uniform(.35, .6), r2.uniform(.35, .6), r2.uniform(.25, .4))
        for p_ in o.data.polygons:
            p_.use_smooth = True
    flakes(2000, (-12, 12, -12, 12, 0, 9), (.8, .3), .6, (.005, .012), 9)


def a_l05(u, t, f):
    team_key(f, 0, 0); e = ease(u)
    cam.look(Vector((5.5 - 1.0 * e, 17.5 - 1.0 * e, gz(5, 17) + 1.3)), Vector((0, 8.5, gz(0, 9) + 1.8 + .8 * e)), 26)         # 前から：葉っぱの山と、食べるキリン


def s_l06():
    plateau(sun=(14., 240.), haze_k=.5); S["frost"] = []; S["spd"] = 0.0; team(kind="idle", seed=7, musher=False, snow=True)
    flakes(5000, (-12, 12, -12, 14, 0, 10), (.6, .2), .55, (.005, .012), 9)


def a_l06(u, t, f):
    team_key(f, 0, 0)
    for s_ in S["frost"]:
        key_v(s_, .08 + .45 * smooth(0, 5.5, t), f)                         # 雪がうっすら積もっていく
    e = ease(u); cam.look(Vector((3.0 - .5 * e, 10.5 - .6 * e, gz(3, 10) + 4.2)), Vector((.9, 5.0, gz(1, 5) + 4.3)), 32 + 10 * e)   # 首と顔の寄り（もぐもぐ）


def fit_eval(new, length):
    """fit と同じだが、骨で曲げた後の形（評価後のメッシュ）で大きさを測る"""
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for o in new:
        if o.type == "MESH":
            e = o.evaluated_get(dg); me = e.to_mesh(); pts += [e.matrix_world @ v.co for v in me.vertices]; e.to_mesh_clear()
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    s_ = length / max(hi.x - lo.x, hi.y - lo.y); root = link(bpy.data.objects.new("root", None))
    for o in new:
        if o.parent is None:
            o.parent = root
    root.scale = (s_,) * 3; root.location = -Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s_
    holder = link(bpy.data.objects.new("holder", None)); bpy.context.view_layer.update(); root.parent = holder; return holder


def sleeper():
    """丸まって眠る犬（Sketchfab "Sleeping dog 01" by thuberchs、写真測量）：下の地面を削り、ハスキーの色に塗り替える"""
    new = imp(os.path.join(SKF, "sleepdog", "scene.gltf")); o = next(x for x in new if x.type == "MESH"); bpy.context.view_layer.update()
    M = o.matrix_world.copy(); bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(M)
    up = np.array([tuple(v.co) for v in bm.verts if v.co.z > -.06 and math.hypot(v.co.x, v.co.y) < 1.6])         # 板の真ん中で丸まっている犬（端の紙くずは除く）
    cx, cy = up[:, 0].mean(), up[:, 1].mean(); rr = np.percentile(np.hypot(up[:, 0] - cx, up[:, 1] - cy), 99) * 1.1
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -.12 or math.hypot(v.co.x - cx, v.co.y - cy) > rr], context="VERTS")   # 地面の板を削る
    me = bpy.data.meshes.new("sleepdog"); bm.to_mesh(me); bm.free()
    for m in o.data.materials:
        me.materials.append(m)
    d = link(bpy.data.objects.new("sleepdog", me))
    for x in new:
        bpy.data.objects.remove(x, do_unlink=True)
    v = np.array([tuple(x.co) for x in me.vertices]); lo, hi = v.min(0), v.max(0); c = (lo + hi) / 2
    me.transform(Matrix.Translation(Vector((-c[0], -c[1], -lo[2])))); L = max(hi[0] - lo[0], hi[1] - lo[1]); d["s"] = .95 / L
    log("sleeper", len(me.vertices), "verts", tuple(round(float(x), 2) for x in lo), tuple(round(float(x), 2) for x in hi), "s", d["s"])
    for p_ in me.polygons:
        p_.use_smooth = True
    m = me.materials[0]; t = m.node_tree; tex = next(n for n in t.nodes if n.type == "TEX_IMAGE")
    for n in list(t.nodes):
        if n.type not in ("TEX_IMAGE", "OUTPUT_MATERIAL"):
            t.nodes.remove(n)
    if hasattr(m, "blend_method"):
        m.blend_method = "OPAQUE"
    b = t.nodes.new("ShaderNodeBsdfPrincipled"); t.links.new(b.outputs[0], next(n for n in t.nodes if n.type == "OUTPUT_MATERIAL").inputs["Surface"])
    bw = t.nodes.new("ShaderNodeRGBToBW"); t.links.new(tex.outputs["Color"], bw.inputs[0])
    to = t.nodes.new("ShaderNodeTexCoord"); sg = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(to.outputs["Generated"], sg.inputs[0])
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 4.0; t.links.new(to.outputs["Generated"], nz.inputs["Vector"])
    h0 = t.nodes.new("ShaderNodeMath"); h0.operation = "MULTIPLY_ADD"; t.links.new(nz.outputs["Fac"], h0.inputs[0]); h0.inputs[1].default_value = .25; t.links.new(sg.outputs["Z"], h0.inputs[2])
    hz = t.nodes.new("ShaderNodeMapRange"); hz.inputs[1].default_value = .35; hz.inputs[2].default_value = .6; t.links.new(h0.outputs[0], hz.inputs[0])   # 上（背中）は灰色、下は白
    mx = t.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; t.links.new(hz.outputs[0], mx.inputs[0]); mx.inputs[6].default_value = (.78, .79, .8, 1); mx.inputs[7].default_value = (.08, .083, .09, 1)
    sh = t.nodes.new("ShaderNodeMapRange"); sh.inputs[3].default_value = .55; sh.inputs[4].default_value = 1.5; t.links.new(bw.outputs[0], sh.inputs[0])
    mu = t.nodes.new("ShaderNodeMix"); mu.data_type = "RGBA"; mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0; t.links.new(mx.outputs[2], mu.inputs[6]); t.links.new(sh.outputs[0], mu.inputs[7])
    t.links.new(mu.outputs[2], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8; b.inputs["Sheen Weight"].default_value = .6; b.inputs["Specular IOR Level"].default_value = .2
    snow_cover(m, b); return d


def snow_cover(m, b):
    t = m.node_tree; src = next((l_.from_socket for l_ in b.inputs["Base Color"].links), None)
    gm = t.nodes.new("ShaderNodeNewGeometry"); sep = t.nodes.new("ShaderNodeSeparateXYZ"); t.links.new(gm.outputs["Normal"], sep.inputs[0])
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 40.0
    fm = t.nodes.new("ShaderNodeMapRange"); fm.inputs[1].default_value = .3; fm.inputs[2].default_value = .85; t.links.new(sep.outputs["Z"], fm.inputs[0])
    fv = t.nodes.new("ShaderNodeValue"); fv.outputs[0].default_value = 0.0
    m1 = t.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"; t.links.new(fm.outputs[0], m1.inputs[0]); t.links.new(fv.outputs[0], m1.inputs[1])
    m2 = t.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; m2.use_clamp = True; t.links.new(m1.outputs[0], m2.inputs[0]); t.links.new(nz.outputs["Fac"], m2.inputs[1])
    m3 = t.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"; m3.use_clamp = True; t.links.new(m2.outputs[0], m3.inputs[0]); m3.inputs[1].default_value = 2.2
    fx = t.nodes.new("ShaderNodeMix"); fx.data_type = "RGBA"; t.links.new(m3.outputs[0], fx.inputs[0]); fx.inputs[7].default_value = (.96, .98, 1.0, 1)
    if src:
        t.links.new(src, fx.inputs[6])
    else:
        fx.inputs[6].default_value = b.inputs["Base Color"].default_value
    t.links.new(fx.outputs[2], b.inputs["Base Color"]); S["frost"].append(fv.outputs[0])


def s_l07():
    plateau(sun=(12., 0.)); S["spd"] = WALK; team(kind="walk", seed=8); kick(300, 14); drift(10, 6, (1, 0), .7, .8)


def a_l07(u, t, f):
    y = 4.0 + WALK * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 10, 0)), 40, .7)
    cy = y - 9.0 + 1.0 * u; cam.look(Vector((1.2, cy, gz(1.2, cy) + 2.4)), Vector((0, y + 12, gz(0, y + 12) + 2.2)), 24)                     # 後ろから、地平線へ向かう隊


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
