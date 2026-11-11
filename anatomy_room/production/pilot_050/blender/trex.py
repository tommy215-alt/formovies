"""pilot_050 のティラノサウルス（前が +Y、体長 約 12 m、腰の高さ 3.1 m）。メタボールの部品をつないで動かす。
色・縞・ゼッケン・メダルは演出（scripts/pilot_050/fact_check.md）。"""
from common import *

from gait import HIP, J_HIP, J_KNEE, J_ANK, J_MTP, STRIDE, DUTY, PERIOD, hip_z, leg

E = "ELLIPSOID"
LX = .78


def skin_mat(name, xray=False):
    """皮膚：頂点の色（背は暗いオリーブ、腹は明るく、背に縞）× まだら、うろこ＋しわの凹凸。xray：脚を透かす（骨を見せる）"""
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree; b = t.nodes["Principled BSDF"]; L = t.links
    tc = t.nodes.new("ShaderNodeTexCoord"); at = t.nodes.new("ShaderNodeAttribute"); at.attribute_name = "Col"
    nz = t.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 2.6; nz.inputs["Detail"].default_value = 6; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    mr = t.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = .3; mr.inputs[2].default_value = .7; mr.inputs[3].default_value = .72; mr.inputs[4].default_value = 1.12
    L.new(nz.outputs["Fac"], mr.inputs[0])
    ve = t.nodes.new("ShaderNodeTexVoronoi"); ve.feature = "DISTANCE_TO_EDGE"; ve.inputs["Scale"].default_value = 24; L.new(tc.outputs["Object"], ve.inputs["Vector"])
    me_ = t.nodes.new("ShaderNodeMapRange"); me_.inputs[1].default_value = 0.0; me_.inputs[2].default_value = .09; me_.inputs[3].default_value = .6; me_.inputs[4].default_value = 1.0
    L.new(ve.outputs["Distance"], me_.inputs[0])
    m1 = t.nodes.new("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1.0
    L.new(at.outputs["Color"], m1.inputs[6]); L.new(mr.outputs[0], m1.inputs[7])
    m2 = t.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1.0
    L.new(m1.outputs[2], m2.inputs[6]); L.new(me_.outputs[0], m2.inputs[7]); L.new(m2.outputs[2], b.inputs["Base Color"])
    b1 = t.nodes.new("ShaderNodeBump"); b1.inputs["Strength"].default_value = .8; b1.inputs["Distance"].default_value = .022; L.new(me_.outputs[0], b1.inputs["Height"])
    wr = t.nodes.new("ShaderNodeTexNoise"); wr.inputs["Scale"].default_value = 7.0; wr.inputs["Detail"].default_value = 9; wr.inputs["Roughness"].default_value = .65
    L.new(tc.outputs["Object"], wr.inputs["Vector"])
    b2 = t.nodes.new("ShaderNodeBump"); b2.inputs["Strength"].default_value = .45; b2.inputs["Distance"].default_value = .06
    L.new(wr.outputs["Fac"], b2.inputs["Height"]); L.new(b1.outputs["Normal"], b2.inputs["Normal"]); L.new(b2.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = .58; b.inputs["Specular IOR Level"].default_value = .38
    sock = None
    if xray:
        out = t.nodes["Material Output"]; tr = t.nodes.new("ShaderNodeBsdfTransparent"); mx = t.nodes.new("ShaderNodeMixShader")
        L.new(b.outputs[0], mx.inputs[1]); L.new(tr.outputs[0], mx.inputs[2]); L.new(mx.outputs[0], out.inputs["Surface"]); mx.inputs[0].default_value = 0.0; sock = mx.inputs[0]
    add_haze(m, 150., 4000., .8); return m, sock


C_BACK, C_FLANK, C_BELLY, C_STRIPE = np.array((.035, .06, .018)), np.array((.15, .1, .032)), np.array((.4, .29, .13)), np.array((.008, .012, .005))


def paint(me, limb=False):
    n = len(me.vertices); co = np.empty(n * 3); no = np.empty(n * 3)
    me.vertices.foreach_get("co", co); me.vertices.foreach_get("normal", no); co = co.reshape(-1, 3); no = no.reshape(-1, 3)
    x, y, z = co.T; nz = no[:, 2]
    up = smooth(-.35, .55, nz)[:, None]; bel = smooth(.2, .8, -nz)[:, None]
    col = C_FLANK + (C_BACK - C_FLANK) * up; col = col + (C_BELLY - col) * bel
    if limb:                                   # 脚・腕：横縞を薄く（縦の部品に体の縞を当てると全体が暗くなる）
        s = np.sin(2 * math.pi * z / .55 + 1.2 * np.sin(y * 3.1)); st = (smooth(.35, .8, s) * smooth(-.2, .5, -y + .2) * .5)[:, None]
    else:
        s = np.sin(2 * math.pi * y / .92 + 1.4 * np.sin(z * 1.9) + 1.1 * np.sin(x * 2.4))
        st = (smooth(.15, .6, s) * smooth(-.75, .05, nz) * .92)[:, None]
    col = col + (C_STRIPE - col) * st
    ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
    ca.data.foreach_set("color", np.concatenate([col, np.ones((n, 1))], 1).ravel())


def _cones(pts, m, name, parent, seg=8):
    """pts：(根元, 先, 根元の半径)。歯・爪"""
    bm = bmesh.new()
    for a, b_, r in pts:
        a = Vector(a); d = Vector(b_) - a; h = d.length
        r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r * .08, depth=h)
        bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=r_["verts"])
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=d.to_track_quat("Z", "Y").to_matrix(), verts=r_["verts"])
        bmesh.ops.translate(bm, vec=a, verts=r_["verts"])
    return child_mesh(name, bm, m, parent)


def _ball(name, p, r, m, parent, sc_=(1, 1, 1)):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=r)
    o = child_mesh(name, bm, m, parent); o.location = Vector(p) - Vector(parent["pivot"]); o.scale = sc_; return o


def _bone(bm, a, b_, r):
    a = Vector(a); d = Vector(b_) - a; h = d.length
    r_ = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=r, radius2=r * .85, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=r_["verts"])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=d.to_track_quat("Z", "Y").to_matrix(), verts=r_["verts"])
    bmesh.ops.translate(bm, vec=a, verts=r_["verts"])
    for p in (a, a + d):
        s_ = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r * 1.55); bmesh.ops.translate(bm, vec=p, verts=s_["verts"])


def paint_limb(me):
    paint(me, True)


def build_trex():
    SK, _ = skin_mat("trex_skin"); SKL, XR = skin_mat("trex_leg", True)
    root = mlink(bpy.data.objects.new("trex", None)); root["pivot"] = (0, 0, 0); root.rotation_mode = "XYZ"
    hipE = mlink(bpy.data.objects.new("trex_hip", None)); hipE["pivot"] = (0, 0, HIP); hipE.parent = root; hipE.location = (0, 0, HIP); hipE.rotation_mode = "XYZ"
    torso = mpart("t_torso", [((0, 0, 3.15), 1.15, E, (.85, 1.15, .95)), ((0, 1.2, 3.05), 1.25, E, (.85, 1.2, .95)), ((0, 2.3, 3.2), 1.05, E, (.8, 1.1, .9)),
                              ((0, 2.9, 3.4), .8, E, (.8, 1, .9)), ((0, -1.0, 3.15), .95, E, (.75, 1.3, .85))], (0, 0, HIP), hipE, .09, SK, paint)
    neck = mpart("t_neck", ch((0, 2.7, 3.55), (0, 3.75, 4.35), .78, .56, 4), (0, 2.6, 3.5), torso, .07, SK, paint)
    head = mpart("t_head", [((0, 3.95, 4.5), .62, E, (1.0, .95, .85)), ((0, 4.5, 4.48), .52, E, (.85, 1.3, .8)), ((0, 5.12, 4.4), .43, E, (.74, 1.4, .7)),
                            ((-.3, 4.25, 4.8), .2, E, (.9, 1.4, .6)), ((.3, 4.25, 4.8), .2, E, (.9, 1.4, .6)), ((0, 4.9, 4.64), .22, E, (.8, 1.6, .5)),
                            ((-.36, 4.1, 4.3), .3, E, (.7, 1, .9)), ((.36, 4.1, 4.3), .3, E, (.7, 1, .9))], (0, 3.7, 4.35), neck, .045, SK, paint)
    jaw = mpart("t_jaw", [((0, 4.66, 4.02), .4, E, (.75, 1.9, .42)), ((0, 4.05, 4.05), .42, E, (.95, .9, .6))], (0, 3.9, 4.15), head, .045, SK, paint)
    tm = mat("t_teeth", (.62, .56, .4), .35, haze=False); hm = mat("t_horn", (.06, .05, .04), .4, haze=False)
    up = []; lo = []
    rr = random.Random(5)
    for i in range(13):
        k = i / 12; y = 4.4 + 1.12 * k
        for sx in (-1, 1):
            h = (.08 + .1 * math.sin(math.pi * min(1, k * 1.25))) * rr.uniform(.6, 1.1); x = sx * (.235 - .11 * k ** 2)
            up.append(((x, y, 4.21), (x * 1.02, y - .05, 4.21 - h), .034)); yl = 4.36 + .9 * k; lo.append(((x * .84, yl, 4.1), (x * .86, yl - .03, 4.1 + h * .7), .027))
    _cones(up, tm, "t_teeth_u", head); _cones(lo, tm, "t_teeth_l", jaw)
    mm = mat("t_mouth", (.33, .07, .06), .45, haze=False)
    _ball("t_tongue", (0, 4.6, 4.13), 1.0, mm, jaw, (.2, .62, .06)); _ball("t_palate", (0, 4.7, 4.2), 1.0, mm, head, (.22, .6, .05))
    em = mat("t_eye", (.75, .42, .06), .08, haze=False); pm = mat("t_pupil", (.004, .004, .004), .05, haze=False); lids = []
    for sx in (-1, 1):
        ep = Vector((sx * .355, 4.36, 4.66)); out = Vector((sx * .9, .42, .1)).normalized()
        _ball(f"t_eye{sx}", ep, .07, em, head); _ball(f"t_pupil{sx}", ep + out * .052, .03, pm, head, (.75, .75, 1.25))
        l_ = _ball(f"t_lid{sx}", ep + Vector((0, 0, .012)), .078, SK, head, (1, 1, .08)); lids.append(l_)
    for sx in (-1, 1):
        _ball(f"t_nose{sx}", (sx * .13, 5.42, 4.555), .05, mat("t_nostril", (.01, .008, .006), .9, haze=False), head, (.7, 1.3, .5))
    tails = []; par = torso
    for i, (a, b_, r0, r1) in enumerate((((0, -1.3, 3.15), (0, -3.4, 3.1), .85, .6), ((0, -3.3, 3.1), (0, -5.2, 3.05), .6, .38), ((0, -5.1, 3.05), (0, -7.0, 3.0), .38, .12))):
        par = mpart(f"t_tail{i}", ch(a, b_, r0, r1, 6), a, par, .07, SK, paint); tails.append(par)
    legs = []; bn = emat("t_bone", (.02, .02, .02), .5, (1.0, .06, .03), 0.0, haze=False)
    for sx in (-1, 1):
        X = sx * LX; hip3, knee3, ank3, mtp3 = (X * .92, J_HIP[0], J_HIP[1]), (X, *J_KNEE), (X, *J_ANK), (X, *J_MTP)
        th = mpart(f"t_thigh{sx}", ch(hip3, knee3, .7, .52, 4) + [((X, .3, 2.7), .9, E, (.6, 1.1, 1.05)), ((X * .92, -.4, 2.9), .7, E, (.6, 1.0, .9))], hip3, hipE, .07, SKL, paint_limb)
        sh = mpart(f"t_shin{sx}", ch(knee3, ank3, .5, .26, 5) + [((X, .38, 1.75), .48, E, (.8, 1.0, 1.25)), ((X, .28, 1.4), .36, E, (.8, 1.0, 1.2))], knee3, th, .05, SKL, paint_limb)
        mt = mpart(f"t_meta{sx}", ch(ank3, mtp3, .29, .25, 4), ank3, sh, .045, SKL, paint_limb)
        toes = [((X, .3, .2), .4, E, (1.15, 1.1, .6))]; claws = []
        for a_, ln in ((-.42, .78), (0, .95), (.42, .78)):
            tip = (X + math.sin(a_) * ln, .26 + math.cos(a_) * ln, .1); toes += ch((X, .26, .17), tip, .23, .14, 5)
            claws.append((tip, (tip[0] + math.sin(a_) * .34, tip[1] + math.cos(a_) * .34, .02), .1))
        claws.append(((X - sx * .18, .05, .2), (X - sx * .3, -.1, .06), .05))
        ft = mpart(f"t_foot{sx}", toes, mtp3, mt, .04, SKL, paint_limb); _cones(claws, hm, f"t_claws{sx}", ft)
        for part, a_, b_, r in ((th, hip3, knee3, .1), (sh, knee3, ank3, .075), (mt, ank3, mtp3, .055)):
            bm = bmesh.new(); _bone(bm, a_, b_, r); child_mesh(part.name + "_bone", bm, bn, part)
        legs.append(dict(th=th, sh=sh, mt=mt, ft=ft))
    arms = []
    for sx in (-1, 1):
        a0 = (sx * .58, 2.8, 2.72); a1 = (sx * .7, 3.0, 2.3); a2 = (sx * .62, 3.34, 2.2)
        ar = mpart(f"t_arm{sx}", ch(a0, a1, .26, .17, 3) + ch(a1, a2, .16, .11, 3), a0, torso, .04, SK, paint_limb)
        _cones([(a2, (a2[0] - sx * .05, a2[1] + .13, a2[2] - .08), .035), (a2, (a2[0] + sx * .06, a2[1] + .12, a2[2] - .1), .035)], hm, f"t_aclaw{sx}", ar); arms.append(ar)
    # ゼッケン（胴の両脇に貼る：格子の板を胴の表面に押しつける）
    bibm = img_mat("bib", .75)
    for sx in (-1, 1):
        bm = bmesh.new(); uv = bm.loops.layers.uv.new("UVMap"); NY, NZ = 14, 10; y0, y1, z0, z1 = 1.22, 2.42, 2.86, 3.68
        vs = [[bm.verts.new((sx * 1.7, y0 + (y1 - y0) * i / NY, z0 + (z1 - z0) * j / NZ)) for i in range(NY + 1)] for j in range(NZ + 1)]
        for j in range(NZ):
            for i in range(NY):
                q = [vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]]; f = bm.faces.new(q if sx > 0 else q[::-1])
                for lp in f.loops:
                    u = (lp.vert.co.y - y0) / (y1 - y0); lp[uv].uv = (u if sx > 0 else 1 - u, (lp.vert.co.z - z0) / (z1 - z0))
        b_ = child_mesh(f"t_bib{sx}", bm, bibm, torso); sw = b_.modifiers.new("sw", "SHRINKWRAP"); sw.target = torso; sw.wrap_method = "PROJECT"
        sw.use_project_x = True; sw.use_negative_direction = True; sw.use_positive_direction = True; sw.offset = .035
    # 完走メダル（l09 だけ見せる）。リボンは首の付け根をひと回り（胴と首の表面に沿わせる）、いちばん下にメダル
    from mathutils.bvhtree import BVHTree
    gold = mat("t_gold", (.95, .62, .12), .22, 1.0, haze=False); rib = mat("t_ribbon", (.03, .16, .62), .6, haze=False); medal = []
    bpy.context.view_layer.update(); dg = bpy.context.evaluated_depsgraph_get()
    bv = [(BVHTree.FromObject(o, dg), Vector(o["pivot"])) for o in (torso, neck)]
    Cn = Vector((0, 3.2, 3.75)); U = Vector((0, -.581, .814)); Xa = Vector((1, 0, 0)); W = Vector((0, .814, .581))
    def hit(th, w):
        tgt = Cn + W * w; org = tgt + (Xa * math.sin(th) + U * math.cos(th)) * 2.4; d = (tgt - org).normalized(); best = None
        for tree, pv in bv:
            loc, nor, _, dist = tree.ray_cast(org - pv, d, 2.4)
            if loc is not None and (best is None or dist < best[2]):
                best = (loc + pv, nor, dist)
        return (best[0] + best[1] * .03) if best else tgt
    bm = bmesh.new(); NS = 120; ring = []
    for i in range(NS):
        th = 2 * math.pi * i / NS; ring.append((bm.verts.new(hit(th, -.075)), bm.verts.new(hit(th, .075))))
    for i in range(NS):
        p_, q_ = ring[i], ring[(i + 1) % NS]; bm.faces.new((p_[0], q_[0], q_[1], p_[1]))
    rb = child_mesh("t_ribbon", bm, rib, torso); so = rb.modifiers.new("so", "SOLIDIFY"); so.thickness = .02; so.offset = 1
    low = hit(math.pi, 0)
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=.3, radius2=.3, depth=.05)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=.22, radius2=.22, depth=.075)
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(72), 3, "X"), verts=bm.verts)
    bmesh.ops.translate(bm, vec=low + Vector((0, -.05, -.3)), verts=bm.verts)
    medal.append(child_mesh("t_medal", bm, gold, torso)); medal.append(rb)
    for o in medal:
        o.hide_render = True
    return dict(root=root, hip=hipE, torso=torso, neck=neck, head=head, jaw=jaw, tails=tails, legs=legs, arms=arms, lids=lids, xray=XR, bone=bn, medal=medal)


T = {}; TANIM = []


def init():
    T.update(build_trex())
    TANIM[:] = [T["root"], T["hip"], T["torso"], T["neck"], T["head"], T["jaw"]] + T["tails"] + T["arms"] + T["lids"] + [o for l in T["legs"] for o in l.values()]
    for o in TANIM:
        o.rotation_mode = "XYZ"


def tpose(pos=(0, 0), heading=0.0, ph=0.0, amp=1.0, sit=0.0, head=(0, 0), neck=(0, 0), jaw=0.0, lid=0.0, t=0.0, breathe=1.0, pant=0.0, z=0.0, tail=0.0, roll=0.0):
    """pos：腰の真下の地面の点。heading：0 で +Y を向く。ph：歩きの周期（1 で左右 1 歩ずつ＝6.5 m × amp）。amp：歩幅（0＝立つ）。sit：座る。
    head・neck：(上下, 左右)。jaw：口の開き。lid：まぶた（1＝閉じる）。pant：速い息"""
    w = 2 * math.pi * ph; R = T["root"]; R.location = (pos[0], pos[1], z); R.rotation_euler = (0, 0, heading)
    hz = hip_z(ph, amp, sit); T["hip"].location = (.07 * amp * math.sin(w), 0, hz)
    br = math.sin(t * 2.1) * breathe + pant * math.sin(t * 9.0)
    T["torso"].rotation_euler = (amp * .025 * math.sin(2 * w + .5) + sit * .1, amp * .04 * math.sin(w) + roll, amp * .05 * math.sin(w + .6))
    T["torso"].scale = (1 + .016 * br, 1, 1 + .014 * br)
    T["neck"].rotation_euler = (neck[0] - amp * .02 * math.sin(2 * w + .5) - sit * .05, 0, neck[1] - amp * .03 * math.sin(w + .6))
    T["head"].rotation_euler = (head[0] + amp * .03 * math.sin(2 * w + 1.3), -amp * .03 * math.sin(w), head[1] - amp * .02 * math.sin(w + .6))
    T["jaw"].rotation_euler = (-(jaw + pant * .05 * (1 + math.sin(t * 9.0))), 0, 0)
    for i, tl in enumerate(T["tails"]):
        tl.rotation_euler = (sit * .09 + tail - amp * .02 * math.sin(2 * w - .8 * i), 0, amp * (.06 + .05 * i) * math.sin(w - .7 * (i + 1)) + .025 * (i + 1) * math.sin(t * .8 + i * 1.3))
    for i, ar in enumerate(T["arms"]):
        ar.rotation_euler = (.12 * math.sin(2 * w + i * 2.0) * amp + .04 * math.sin(t * 1.3 + i), 0, 0)
    for l_ in T["lids"]:
        l_.scale = (1, 1, max(.08, lid))
    for lg, off in zip(T["legs"], (0.0, .5)):
        df, dt, dm, tp = leg((ph + off) % 1.0, amp, hz, sit)
        lg["th"].rotation_euler = (df, 0, 0); lg["sh"].rotation_euler = (dt - df, 0, 0); lg["mt"].rotation_euler = (dm - dt, 0, 0); lg["ft"].rotation_euler = (tp - dm, 0, 0)


def medal(on):
    for o in T["medal"]:
        o.hide_render = not on


def xray(k, glow, f=None):
    """脚を透かして骨を見せる（k：0〜1、glow：骨の光）。f を渡すとキーフレームを打つ"""
    if f is None:
        T["xray"].default_value = k; esock(T["bone"]).default_value = glow
    else:
        key_v(T["xray"], k, f); key_v(esock(T["bone"]), glow, f)
