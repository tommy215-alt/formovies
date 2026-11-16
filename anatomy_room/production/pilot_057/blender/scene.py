"""pilot_057「犬ぞりで、南極を横断したら？」の 3D（Blender Cycles）。もしも設計の既定（templates/DESIGN_MODES.md）。
南極の氷の高原（Poly Haven の雪の質感・空の光、CC0）、ハスキー 10 頭の犬ぞり隊。
犬は Sketchfab "Dog animated"（MAXDESIGN-3D、CC BY、走る動き）をハスキーの毛色（背中は灰色、顔・腹・脚は白）に塗り替えて複製。
眠る犬は "wolf animated"（Paleo Modelist、CC BY、SLEEP の動き）。そりは "Dog Sled"（sayumiQ、CC BY）、人は "Arctic Explorer Posed"（ChloeRobynSmith、CC BY）。
l01 の地図は NASA Blue Marble の南極（正距ではなく正射図法、Dave Pape、パブリックドメイン）。閃光なし。
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
SPEED = 4.2                    # 隊の速さ m/s（時速 約 15 km。1 日 27 km は休みを入れた平均）
DOG_LEN = 1.15                 # 犬の長さ（鼻先〜しっぽ）m
RUN = (0, 32)                  # "Take 001" の走る 1 回分のコマ（24 fps）
NPAIR = 5                      # 2 頭ずつ 5 列＝10 頭
GAP = 1.55                     # 列の間 m


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
def plateau(hdri="kloofendal_43d_clear_puresky", sun=(18., 120.), exposure=-.45, haze_k=.55):
    env_clear(); sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = .35; S.clear()
    track.world_hdri(hdri, exposure=exposure, sun=sun, sun_k=3.2)
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


def dogs_template(frost=None):
    new = imp(os.path.join(SKF, "dogreal", "scene.gltf"))
    for o in new:
        if o.type == "MESH":
            for sl in o.material_slots:
                if sl.material and not sl.material.get("husky"):
                    husky_mat(sl.material, frost); sl.material["husky"] = 1
    S["run_act"] = next(a for a in bpy.data.actions if a.name.startswith("Take"))
    h = fit(new, length=DOG_LEN, axis=1)
    dg = bpy.context.evaluated_depsgraph_get(); ms = [o for o in new if o.type == "MESH"]
    o = ms[0]; e = o.evaluated_get(dg); me = e.to_mesh(); M = e.matrix_world; row = Vector((M[2][0], M[2][1], M[2][2]))
    d = [row.dot(v.co) for v in me.vertices]; e.to_mesh_clear(); hb, hh = -min(d), max(d) - min(d)
    for o in ms:
        for sl in o.material_slots:
            nd = sl.material.node_tree.nodes
            if nd.get("HB"):
                nd["HB"].outputs[0].default_value = hb; nd["HH"].outputs[0].default_value = hh
                for k in range(3):
                    nd["ZR"].inputs[k].default_value = row[k]
    log("husky row", tuple(round(x, 4) for x in row), "hb", round(hb, 3), "hh", round(hh, 3))
    return h, new


def team(heading=0.0, n_pair=NPAIR, sled=True, musher=True, frost=None, seed=1):
    """隊の root（空の物）。+Y が進む向き。犬は y>0、そりは y<0。root を動かして走らせる"""
    r = np.random.default_rng(seed)
    root = link(bpy.data.objects.new("team", None)); root.rotation_euler = (0, 0, heading)
    h, objs = dogs_template(frost); arms = []
    tree = [h] + [o for o in bpy.data.objects if o.parent is not None and _anc(o, h)]
    for k in range(n_pair * 2):
        row, side = k // 2, (k % 2) * 2 - 1
        mp = copy_tree(tree, f"_{k}") if k else {o: o for o in tree}
        hk = mp[h]; hk.parent = root; hk.location = (side * .42, 1.6 + row * GAP + r.uniform(-.08, .08), 0); hk.rotation_euler = (0, 0, math.pi + r.uniform(-.06, .06) - side * .03)
        sk = r.uniform(.94, 1.05); hk.scale = (sk,) * 3
        arm = next(o for o in mp.values() if o.type == "ARMATURE"); off, spd = r.uniform(0, 1), r.uniform(.96, 1.04)
        for o in mp.values():                                                 # 骨と、その親の Bip001（体の上下）を同じ位相で
            if o.animation_data and o.animation_data.action == S["run_act"]:
                run_nla(o, off, spd)
        arms.append((hk, arm))
    S["dogs"] = arms
    gang = rope([(0, .2, .45)] + [(0, 1.6 + i * GAP + .3, .42) for i in range(n_pair)], .012, (.75, .1, .08), root)   # 引き綱（赤）
    for hk, arm in arms:                                                     # 引き綱から各犬の胴へ
        x, y, _ = hk.location; rope([(0, y - .45, .42), (x * .9, y - .2, .38)], .007, (.1, .1, .12), root)
    if sled:
        sn = imp(os.path.join(SKF, "sled", "scene.gltf")); sh = fit(sn, length=2.5, axis=0); sh.parent = root; sh.rotation_euler = (0, 0, -math.pi / 2); sh.location = (0, -1.2, 0)
        S["sled"] = sh
    if musher:
        mn = imp(os.path.join(SKF, "explorer", "scene.gltf")); mh = fit(mn, height=1.75, axis=2); mh.parent = root; mh.location = (0, -2.35, .12); mh.rotation_euler = (0, 0, 0)
        S["musher"] = mh
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
    loc = np.array([tuple(S["dogs"][i][0].location) for i in idx]) + np.stack([r.normal(0, .12, n), r.uniform(-.35, .25, n), np.full(n, .03)], 1)
    v0 = np.stack([r.normal(0, .5, n), r.uniform(-SPEED - 1.2, -SPEED + .4, n), r.uniform(.6, 2.0, n)], 1)   # 隊から見ると後ろへ流れる
    S["kick"] = (loc, v0, born)
    d = city.Drops("kick", loc, v0, born, r.uniform(.006, .02, n), mat("kickm", (.95, .97, 1.0), .6), g=6.0, drag=0.0, life=1.1, seed=seed, floor=.02)
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
    plateau(hdri="kloofendal_43d_clear_puresky", sun=(16., 160.), haze_k=.6); team(frost=.35); kick(); drift(16, 3, (1, -.25), 1.2, 1.1); flakes(7000, (-30, 30, -40, 30, 0, 9), (10.0, -2.5), 1.0)


def a_l00(u, t, f):
    y = -14.0 + SPEED * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 3, 0)), 34, 1.3)
    cy = y + 12.0 - 2.2 * u; cam.look(Vector((.9, cy, gz(.9, cy) + .38)), Vector((0, y + 5.5, gz(0, y + 5.5) + .6)), 22)                 # 正面の低い位置。迫ってくる


def s_l08():
    s_l00()


def a_l08(u, t, f):
    tt = t + 3.6; y = -14.0 + SPEED * tt; team_key(f, 0, y); drift_key(tt, f, Vector((0, y + 3, 0)), 34, 1.3)
    cy = -14.0 + SPEED * 3.6 + 12.0 - 2.2 + 1.5 * u; cam.look(Vector((.9, cy, gz(.9, cy) + .38)), Vector((0, y + 5.5, gz(0, y + 5.5) + .6)), 22)


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
    plateau(hdri="kloofendal_overcast_puresky", sun=(10., 100.), exposure=-.15, haze_k=.85); team(frost=.6, seed=2); kick(1200, 10)
    drift(30, 4, (1, .1), 2.6, 3.0); flakes(16000, (-40, 60, -5, 40, 0, 10), (16.0, 1.5), 1.5, (.008, .02), 6)


def a_l02(u, t, f):
    x = -10.0 + SPEED * t * .95; team_key(f, x, 14.0, heading=-math.pi / 2); drift_key(t, f, Vector((x, 12, 0)), 40, 2.4)
    cam.look(Vector((-3.0 + 3.0 * u, 2.0, gz(-3, 2) + 1.3)), Vector((x * .8 + 1.0, 14.0, gz(x, 14) + .7)), 40)


def s_l03():
    plateau(sun=(20., 150.)); team(frost=.3, seed=3); kick(3000, 11); drift(12, 5, (1, .2), .8, .7); flakes(3000, (-25, 25, -10, 60, 0, 6), (6.0, 1.0), .8, (.005, .012), 7)


def a_l03(u, t, f):
    y = SPEED * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 4, 0)), 26, .8)
    cx, cy = 3.0 - .5 * u, y + 1.0 + 1.4 * u; cam.look(Vector((cx, cy, gz(cx, cy) + .55)), Vector((0, y + 3.2 + .6 * u, gz(0, y + 3.2) + .5)), 26)        # 横から並走


def s_l04():
    plateau(sun=(18., 200.)); team(frost=.75, seed=4); kick(900, 12); flakes(2500, (-12, 12, -5, 40, 0, 5), (4.0, -1.0), .7, (.004, .01), 8)
    lead = S["dogs"][-1][0]; nose = link(bpy.data.objects.new("nose", None)); nose.parent = lead; nose.location = (0, DOG_LEN * .5, .52); breath(nose)
    S["lead"] = lead


def a_l04(u, t, f):
    y = SPEED * t; team_key(f, 0, y); breath_key(t, f)
    hx, hy, _ = S["lead"].location; e = ease(u)
    cx, cy = hx + .9 - .3 * e, y + hy + 2.6 - .4 * e; cam.look(Vector((cx, cy, gz(cx, cy) + .6)), Vector((hx, y + hy + .25, gz(hx, y + hy) + .5)), 52 + 10 * e)   # 先頭の犬の顔へ寄る


def s_l05():
    plateau(sun=(14., 240.), haze_k=.5); S["frost"] = []
    sh = imp(os.path.join(SKF, "sled", "scene.gltf")); sh = fit(sh, length=2.5, axis=0); sh.location = (-.3, 1.4, 0); sh.rotation_euler = (0, 0, .4)
    new = imp(os.path.join(SKF, "wolfsit", "scene.gltf"))
    for o in list(new):
        if o.type == "MESH":
            if not any(sl.material and sl.material.name.startswith("Mat_0") for sl in o.material_slots):   # 岩・雪の台・頭骨は外して、オオカミだけ
                new.remove(o); bpy.data.objects.remove(o, do_unlink=True)
            else:
                for sl in o.material_slots:
                    m = sl.material; b = m.node_tree.nodes.get("Principled BSDF") if m and m.use_nodes else None
                    if b and not m.get("ok"):
                        snow_cover(m, b); m["ok"] = 1
    h = fit_eval(new, .62); tree = [h] + [o for o in bpy.data.objects if _anc(o, h)]
    spots = [(.8, -.3, 2.6, 1.0), (-.5, -.9, .4, .92), (1.9, 1.1, -1.4, 1.05), (-1.7, .7, 3.4, .96)]
    S["sleepers"] = []
    for k, (x, y, a, sk) in enumerate(spots):
        mp = copy_tree(tree, f"_s{k}") if k else {o: o for o in tree}
        hk = mp[h]; hk.location = (x, y, gz(x, y) - .04); hk.rotation_euler = (0, 0, a); hk.scale = (sk,) * 3; S["sleepers"].append((hk, sk))
    flakes(5000, (-10, 10, -10, 10, 0, 7), (.6, .2), .55, (.006, .016), 9)


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


def a_l05(u, t, f):
    for k, (o, s0) in enumerate(S["sleepers"]):                              # 寝息（ゆっくり、犬ごとにずらす）
        b = 1 + .025 * math.sin(t * 2 * math.pi / (2.6 + .4 * k) + k * 1.7); keyp(o, f, scale=(s0, s0 * (1 + (b - 1) * .4), s0 * b))
    for s_ in S["frost"]:
        key_v(s_, .08 + .32 * smooth(0, 5.5, t), f)                       # 雪がうっすら積もっていく
    e = ease(u); cam.look(Vector((2.4 - .5 * e, -2.6 + .5 * e, gz(2.3, -2.4) + .55 - .1 * e)), Vector((.6, -.3, gz(.8, -.3) + .35)), 30 + 8 * e)


EDGE = 52.0                    # l06：氷の崖のふち（y）


def s_l06():
    plateau(sun=(22., 300.)); team(frost=.5, seed=6); kick(2000, 13)
    bpy.data.objects.remove(bpy.data.objects["far"], do_unlink=True)
    S["ground"].location = (0, EDGE - 130.0, 0)                                  # 起伏の格子の北のふちを崖に
    xs, Z = S["gz"]; S["gz"] = (xs, Z); S["goff"] = EDGE - 130.0
    sea = mat("sea", (.006, .03, .055), .04)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=4000.0); bmesh.ops.translate(bm, vec=(0, 2000 + EDGE, -9.0), verts=bm.verts); mesh_obj("sea", bm, [sea])
    ice = track.pbr("snow_02", .08, 0.0, tint=(.62, .82, 1.0), name="icecliff")
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(400, 3.0, 12.0), verts=bm.verts); bmesh.ops.translate(bm, vec=(0, EDGE - 1.4, -5.6), verts=bm.verts); mesh_obj("cliff", bm, [ice])
    r = np.random.default_rng(3)
    for k in range(9):                                                            # 氷山（平らな卓状）
        x, y = r.uniform(-260, 260), r.uniform(EDGE + 80, EDGE + 900); w_, d_, h_ = r.uniform(20, 70), r.uniform(15, 50), r.uniform(10, 25)
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w_, d_, h_), verts=bm.verts); bmesh.ops.translate(bm, vec=(x, y, -9 + h_ / 2 - 2), verts=bm.verts); mesh_obj(f"berg{k}", bm, [ice])
    red = mat("hut", (.6, .07, .045), .45); wht = mat("hutw", (.9, .9, .88), .5)
    for k, (x, y, w_, d_, h_) in enumerate(((9.0, 36.0, 6.0, 3.6, 2.8), (17.0, 39.0, 4.2, 3.2, 2.4), (-6.0, 41.0, 8.0, 4.0, 3.1))):
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w_, d_, h_), verts=bm.verts); bmesh.ops.translate(bm, vec=(x, y, h_ / 2), verts=bm.verts); mesh_obj(f"hut{k}", bm, [red])
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(w_ + .3, d_ + .3, .22), verts=bm.verts); bmesh.ops.translate(bm, vec=(x, y, h_ + .1), verts=bm.verts); mesh_obj(f"roof{k}", bm, [wht])
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.07, radius2=.04, depth=10.0); bmesh.ops.translate(bm, vec=(13.0, 37.5, 5.0), verts=bm.verts); mesh_obj("mast", bm, [wht])
    flakes(1500, (-25, 25, -5, 50, 0, 6), (3.0, 1.0), .6, (.004, .01), 10)


def a_l06(u, t, f):
    y = 8.0 + SPEED * .8 * t; team_key(f, 2.0, y)
    e = ease(u); cam.look(Vector((-9.0 + 1.5 * e, 4.0 + 2.5 * e, gz(-9, 4) + 3.2)), Vector((4.0, 34.0, .6)), 26)


def s_l07():
    plateau(sun=(12., 0.)); team(frost=.4, seed=7); kick(1500, 14); drift(10, 6, (1, 0), .7, .6)


def a_l07(u, t, f):
    y = 4.0 + SPEED * t; team_key(f, 0, y); drift_key(t, f, Vector((0, y + 8, 0)), 40, .7)
    cy = y - 6.5 + 1.0 * u; cam.look(Vector((.8, cy, gz(.8, cy) + 1.7)), Vector((0, y + 10, gz(0, y + 10) + .6)), 24)                          # 後ろから、地平線へ向かう隊


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
