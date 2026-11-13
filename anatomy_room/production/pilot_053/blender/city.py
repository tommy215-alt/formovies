"""pilot_050 の街（+Y にのびる大通り・ビル・街路樹・街灯・柵・門・時計）。特定の都市・大会・店の名前は写さない。
道の半分の幅 RW、歩道の幅 SW。ビルの窓は世界座標のシェーダー（箱を並べるだけで窓が入る）。"""
from common import *

RW, SW = 15.0, 7.0


def _nt(name):
    m = bpy.data.materials.new(name); m.use_nodes = True; t = m.node_tree
    return m, t.nodes, t.links, t.nodes["Principled BSDF"]


def _M(n, L, op, a, b=None, c=None):
    nd = n.new("ShaderNodeMath"); nd.operation = op
    for i, x in enumerate((a, b, c)):
        if x is None:
            continue
        if isinstance(x, (int, float)):
            nd.inputs[i].default_value = x
        else:
            L.new(x, nd.inputs[i])
    return nd.outputs[0]


def _mix(n, L, fac, a, b):
    nd = n.new("ShaderNodeMix"); nd.data_type = "RGBA"
    for i, x in ((0, fac), (6, a), (7, b)):
        if isinstance(x, (int, float)):
            nd.inputs[i].default_value = x
        elif isinstance(x, tuple):
            nd.inputs[i].default_value = (*x, 1)
        else:
            L.new(x, nd.inputs[i])
    return nd.outputs[2]


def _noise(n, L, scale, detail=4, vec=None, rough=.55):
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail; nz.inputs["Roughness"].default_value = rough
    if vec is not None:
        L.new(vec, nz.inputs["Vector"])
    return nz.outputs["Fac"]


def _bump(n, L, b, height, strength=.4, dist=.05):
    bp = n.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = dist
    L.new(height, bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])


def asphalt():
    if "asphalt" in MATS:
        return MATS["asphalt"]
    m, n, L, b = _nt("asphalt"); pos = n.new("ShaderNodeNewGeometry").outputs["Position"]
    fine = _noise(n, L, 45., 6, pos, .7); big = _noise(n, L, .12, 3, pos)
    col = _mix(n, L, big, (.05, .05, .054), (.085, .085, .09)); col2 = _mix(n, L, _M(n, L, "MULTIPLY", fine, .5), col, (.16, .16, .16))
    L.new(col2, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .82; _bump(n, L, b, fine, .35, .02)
    add_haze(m, 150., 4000., .8); MATS["asphalt"] = m; return m


def paving():
    if "paving" in MATS:
        return MATS["paving"]
    m, n, L, b = _nt("paving"); pos = n.new("ShaderNodeNewGeometry").outputs["Position"]
    br = n.new("ShaderNodeTexBrick"); L.new(pos, br.inputs["Vector"]); br.inputs["Scale"].default_value = 2.2; br.inputs["Mortar Size"].default_value = .012
    br.inputs["Color1"].default_value = (.36, .33, .3, 1); br.inputs["Color2"].default_value = (.3, .28, .26, 1); br.inputs["Mortar"].default_value = (.12, .11, .1, 1)
    col = _mix(n, L, _noise(n, L, .4, 3, pos), br.outputs["Color"], (.42, .4, .37))
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .8; _bump(n, L, b, br.outputs["Fac"], -.5, .02)
    add_haze(m, 150., 4000., .8); MATS["paving"] = m; return m


def grass():
    if "grass" in MATS:
        return MATS["grass"]
    m, n, L, b = _nt("grass"); pos = n.new("ShaderNodeNewGeometry").outputs["Position"]
    fine = _noise(n, L, 30., 8, pos, .75); big = _noise(n, L, .25, 3, pos)
    col = _mix(n, L, big, (.05, .13, .025), (.1, .2, .04)); col = _mix(n, L, _M(n, L, "MULTIPLY", fine, .6), col, (.16, .26, .06))
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .9; _bump(n, L, b, fine, .8, .06)
    add_haze(m, 150., 4000., .8); MATS["grass"] = m; return m


def bmat(name, wall, wx, fh, glass=(.025, .04, .055)):
    """ビルの壁：世界座標で窓を並べる（1 階は店の大きなガラス、屋根は窓なし）"""
    if name in MATS:
        return MATS[name]
    m, n, L, b = _nt(name); g = n.new("ShaderNodeNewGeometry")
    sp = n.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Position"], sp.inputs[0]); sn = n.new("ShaderNodeSeparateXYZ"); L.new(g.outputs["Normal"], sn.inputs[0])
    X, Y, Z = sp.outputs; ax = _M(n, L, "ABSOLUTE", sn.outputs[0]); ay = _M(n, L, "ABSOLUTE", sn.outputs[1]); az = _M(n, L, "ABSOLUTE", sn.outputs[2])
    h = _M(n, L, "ADD", _M(n, L, "MULTIPLY", X, ay), _M(n, L, "MULTIPLY", Y, ax))
    hu = _M(n, L, "DIVIDE", h, wx); zu = _M(n, L, "DIVIDE", _M(n, L, "SUBTRACT", Z, 4.3), fh); fu = _M(n, L, "FRACT", hu); fv = _M(n, L, "FRACT", zu)
    def band(v, a, c):
        return _M(n, L, "MULTIPLY", _M(n, L, "GREATER_THAN", v, a), _M(n, L, "LESS_THAN", v, c))
    side = _M(n, L, "LESS_THAN", az, .5)
    win = _M(n, L, "MULTIPLY", _M(n, L, "MULTIPLY", band(fu, .14, .86), band(fv, .2, .8)), _M(n, L, "GREATER_THAN", Z, 4.3))
    fu1 = _M(n, L, "FRACT", _M(n, L, "DIVIDE", h, wx * 2)); shop = _M(n, L, "MULTIPLY", band(fu1, .07, .93), band(Z, .55, 3.3))
    mask = _M(n, L, "MULTIPLY", _M(n, L, "MAXIMUM", win, shop), side)
    wn = n.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "3D"; cb = n.new("ShaderNodeCombineXYZ")
    L.new(_M(n, L, "FLOOR", hu), cb.inputs[0]); L.new(_M(n, L, "FLOOR", zu), cb.inputs[1]); L.new(ax, cb.inputs[2]); L.new(cb.outputs[0], wn.inputs["Vector"])
    gcol = _mix(n, L, wn.outputs["Value"], tuple(c * .45 for c in glass), tuple(c * 2.4 for c in glass))
    wcol = _mix(n, L, _noise(n, L, .35, 3, g.outputs["Position"]), tuple(c * .86 for c in wall), tuple(min(1, c * 1.08) for c in wall))
    L.new(_mix(n, L, mask, wcol, gcol), b.inputs["Base Color"])
    L.new(_M(n, L, "MULTIPLY_ADD", mask, -.72, .78), b.inputs["Roughness"])
    _bump(n, L, b, _M(n, L, "SUBTRACT", 1.0, mask), .7, .12)
    add_haze(m, 150., 4000., .8); MATS[name] = m; return m


WALLS = [((.62, .6, .56), 2.6, 3.4), ((.42, .44, .47), 2.2, 3.6), ((.7, .66, .58), 3.0, 3.3), ((.3, .32, .36), 1.8, 3.8), ((.55, .42, .34), 2.8, 3.4),
         ((.74, .74, .72), 2.4, 3.5), ((.36, .4, .42), 3.4, 3.7)]


def _bmats():
    return [bmat(f"bld{i}", *w) for i, w in enumerate(WALLS)]


def leaf_mat():
    if "leaf" in MATS:
        return MATS["leaf"]
    m, n, L, b = _nt("leaf"); pos = n.new("ShaderNodeNewGeometry").outputs["Position"]
    vo = n.new("ShaderNodeTexVoronoi"); L.new(pos, vo.inputs["Vector"]); vo.inputs["Scale"].default_value = 5.5
    col = _mix(n, L, _noise(n, L, 1.6, 4, pos), (.025, .085, .015), (.09, .2, .03)); col = _mix(n, L, _M(n, L, "MULTIPLY", vo.outputs["Distance"], .9), col, (.16, .3, .05))
    L.new(col, b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .55; _bump(n, L, b, vo.outputs["Distance"], 1.0, .25)
    add_haze(m, 150., 4000., .8); MATS["leaf"] = m; return m


def bark_mat():
    if "bark" in MATS:
        return MATS["bark"]
    m, n, L, b = _nt("bark"); pos = n.new("ShaderNodeNewGeometry").outputs["Position"]
    sc_ = n.new("ShaderNodeVectorMath"); sc_.operation = "MULTIPLY"; sc_.inputs[1].default_value = (9, 9, 1.2); L.new(pos, sc_.inputs[0])
    nz = _noise(n, L, 1.0, 6, sc_.outputs[0], .7)
    L.new(_mix(n, L, nz, (.05, .035, .025), (.2, .15, .1)), b.inputs["Base Color"]); b.inputs["Roughness"].default_value = .9; _bump(n, L, b, nz, 1.0, .08)
    add_haze(m, 150., 4000., .8); MATS["bark"] = m; return m


def _smooth(o):
    if o is not None:
        o.data.polygons.foreach_set("use_smooth", np.ones(len(o.data.polygons), bool)); o.data.update()
    return o


def _blob():
    """葉のかたまりの型（でこぼこの球）"""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0); r = np.random.default_rng(3)
    v = np.array([tuple(x.co) for x in bm.verts], float); f = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free()
    k = 1 + .16 * np.sin(v[:, 0] * 5.1 + 1.3) * np.sin(v[:, 1] * 4.3 + .4) + .13 * np.sin(v[:, 2] * 6.2 + v[:, 0] * 3.0) + r.uniform(-.05, .05, len(v))
    return v * k[:, None], f


def _cyl(seg=10, top=.7):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=1.0, radius2=top, depth=1.0)
    v = np.array([tuple(x.co) for x in bm.verts], float); f = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free(); v[:, 2] += .5; return v, f


def trees(P, seed=1, h=(5.5, 8.5), r=(1.5, 2.3), name="trees"):
    """P：(x, y) の並び。幹＋葉のかたまり 5〜8 個"""
    rnd = np.random.default_rng(seed); tr = []; lf = []
    for x, y in P:
        H = rnd.uniform(*h); R = rnd.uniform(*r); tr.append((x, y, 0, .16 * R / 1.8, .16 * R / 1.8, H * .78, rnd.uniform(0, 6), 0, 0))
        for k in range(int(rnd.integers(5, 9))):
            a = rnd.uniform(0, 6.28); d = rnd.uniform(0, .75) * R; s = R * rnd.uniform(.55, .85)
            lf.append((x + math.cos(a) * d, y + math.sin(a) * d, H * .78 + rnd.uniform(-.1, .75) * R, s, s, s * rnd.uniform(.7, .95), rnd.uniform(0, 6), rnd.uniform(-.3, .3), rnd.uniform(-.3, .3)))
        lf.append((x, y, H * .78 + R * .2, R * .8, R * .8, R * .7, 0, 0, 0))
    tv, tf = _cyl(); bv, bf = _blob()
    return _smooth(instances(name + "_tr", tv, tf, tr, [bark_mat()])), _smooth(instances(name + "_lf", bv, bf, lf, [leaf_mat()]))


def box(name, x0, x1, y0, y1, z0, z1, m):
    return instances(name, CUBE_V, CUBE_F, [((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2, x1 - x0, y1 - y0, z1 - z0, 0, 0, 0)], [m])


def street(y0=-300., y1=900., seed=1, far=False, park=None, cross=140., bld=True, tree_gap=18.):
    """大通り。park：(side, ya, yb) の区間はビルの代わりに芝生（木は置かない）。far：空からの画のために遠くの街も作る"""
    rnd = np.random.default_rng(seed); A = asphalt(); L_ = y1 - y0; yc = (y0 + y1) / 2
    box("road", -RW, RW, y0, y1, -.3, 0, A); box("far", -3000, 3000, y0 - 2500, y1 + 2500, -.5, -.02, A)
    pv = paving(); cb = mat("curb", (.5, .5, .48), .8); wh = mat("paint", (.82, .82, .8), .55)
    for s in (-1, 1):
        box(f"curb{s}", min(s * RW, s * (RW + .3)), max(s * RW, s * (RW + .3)), y0, y1, -.3, .16, cb)
        box(f"walk{s}", min(s * (RW + .3), s * (RW + SW)), max(s * (RW + .3), s * (RW + SW)), y0, y1, -.3, .15, pv)
    ln = [(x, y, .006, .16, 5.0, .012, 0, 0, 0) for x in (-7.5, 0, 7.5) for y in np.arange(y0, y1, 10.)]
    ln += [(s * (RW - .8), yc, .006, .2, L_, .012, 0, 0, 0) for s in (-1, 1)]
    instances("lanes", CUBE_V, CUBE_F, ln, [wh])
    inpark = lambda s, y: park is not None and s == park[0] and park[1] <= y <= park[2]
    if park is not None:
        s = park[0]; box("park", min(s * (RW + SW), s * 400), max(s * (RW + SW), s * 400), park[1], park[2], -.3, .16, grass())
    # ビル：通り沿い・奥の列（・遠くの街）
    if bld:
        bx = []; bi = []; top = []; nm = len(WALLS)
        def add(xc, ycn, d, w, fl):
            hh = 4.3 + fl * rnd.choice([3.4, 3.6, 3.8]); bx.append((xc, ycn, hh / 2, d, w, hh, 0, 0, 0)); bi.append(int(rnd.integers(0, nm)))
            for _ in range(int(rnd.integers(1, 4))):          # 屋上の設備
                tw = rnd.uniform(2, min(8, w * .4)); td = rnd.uniform(2, min(7, d * .4)); th_ = rnd.uniform(1.2, 3.5)
                top.append((xc + rnd.uniform(-.3, .3) * (d - td), ycn + rnd.uniform(-.3, .3) * (w - tw), hh + th_ / 2, td, tw, th_, 0, 0, 0))
        for s in (-1, 1):
            y = y0 + rnd.uniform(0, 8)
            while y < y1:
                w = rnd.uniform(16, 40)
                if cross and (y - y0) % cross > cross - 16:      # 交差する道のすき間
                    y += 16; continue
                if not inpark(s, y + w / 2):
                    d = rnd.uniform(18, 30); add(s * (RW + SW + d / 2), y + w / 2, d, w, int(rnd.choice([4, 5, 6, 7, 8, 9, 10, 12, 14, 18, 22])))
                y += w + rnd.uniform(.3, 2.5)
            y = y0
            while y < y1:
                w = rnd.uniform(24, 55)
                if not inpark(s, y + w / 2):
                    d = rnd.uniform(24, 45); add(s * (RW + SW + 44 + d / 2), y + w / 2, d, w, int(rnd.integers(8, 34)))
                y += w + rnd.uniform(4, 14)
        if far:
            for _ in range(900):
                x = rnd.uniform(110, 900) * rnd.choice([-1, 1]); y = rnd.uniform(y0 - 300, y1 + 600)
                add(x, y, rnd.uniform(18, 50), rnd.uniform(18, 50), int(rnd.integers(3, 26) if rnd.random() < .85 else rnd.integers(26, 48)))
        instances("blds", CUBE_V, CUBE_F, bx, _bmats(), bi); instances("rooftops", CUBE_V, CUBE_F, top, [mat("rooftop", (.42, .42, .43), .7)])
    # 街路樹・街灯・旗・柵
    tp = [(s * (RW + 1.6), y + rnd.uniform(-1, 1)) for s in (-1, 1) for y in np.arange(y0 + 6, y1, tree_gap) if not (park is not None and s == park[0] and park[1] - 8 <= y <= park[2] + 8)]
    trees(tp, seed + 3)
    pole = []; arm = []; flag = []; fi = []; tv, tf = _cyl(8, .75)
    for s in (-1, 1):
        for j, y in enumerate(np.arange(y0 + 15, y1, 36.)):
            x = s * (RW + .75); pole.append((x, y, 0, .09, .09, 8.2, 0, 0, 0)); arm.append((x - s * 1.0, y, 8.1, 2.2, .1, .1, 0, 0, 0)); arm.append((x - s * 2.0, y, 8.0, .8, .3, .12, 0, 0, 0))
            flag.append((x - s * .5, y, 5.4, .8, .04, 2.2, 0, 0, 0)); fi.append(j % 3)
    dk = mat("pole", (.12, .13, .14), .45, .6)
    instances("poles", tv, tf, pole, [dk]); instances("arms", CUBE_V, CUBE_F, arm, [dk])
    instances("flags", CUBE_V, CUBE_F, flag, [mat("flag0", (.75, .06, .05), .6), mat("flag1", (.05, .2, .65), .6), mat("flag2", (.9, .6, .05), .6)], fi)
    fence(y0, y1)


def fence(y0, y1, x=RW - .35, sides=(-1, 1), gaps=()):
    """沿道の柵（車道の端）。gaps：(side, ya, yb) は柵を置かない"""
    rail = []; post = []
    for s in sides:
        for y in np.arange(y0, y1, 2.4):
            if any(s == g[0] and g[1] <= y <= g[2] for g in gaps):
                continue
            for z in (.28, .68, 1.06):
                rail.append((s * x, y + 1.2, z, .045, 2.4, .045, 0, 0, 0))
            post.append((s * x, y, .54, .06, .06, 1.08, 0, 0, 0)); post.append((s * x, y + 1.2, .54, .03, .03, 1.0, 0, 0, 0))
            for k in range(1, 8):
                post.append((s * x, y + .3 * k, .67, .018, .018, .78, 0, 0, 0))
    instances("fence", CUBE_V, CUBE_F, rail + post, [mat("fence", (.72, .73, .75), .35, .7)])


def text(name, body, size, loc, face_y, m, align="CENTER"):
    """立てた文字。face_y：-1 で -Y の側から読める、+1 で +Y の側から"""
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size; cu.align_x = align; cu.align_y = "CENTER"; cu.extrude = .01; cu.materials.append(m)
    o = link(bpy.data.objects.new(name, cu)); o.location = loc; o.rotation_euler = (math.pi / 2, 0, 0 if face_y < 0 else math.pi); return o


def hms(t):
    t = max(0, int(t)); return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}"


def gate(y, kind="start", clock=None, w=RW + .8):
    """スタート・ゴールの門。梁の下 5.5 m。両面に文字、上に時計（clock(t)：号砲からの秒。None なら時計なし）"""
    blue = mat("gate_blue", (.03, .1, .42), .45); dk = mat("gate_dark", (.02, .02, .025), .4)
    for s in (-1, 1):
        box(f"gate_col{s}", s * w - .45, s * w + .45, y - .45, y + .45, 0, 7.0, blue); box(f"gate_foot{s}", s * w - .8, s * w + .8, y - .8, y + .8, 0, .5, dk)
    box("gate_beam", -w, w, y - .45, y + .45, 5.5, 7.0, blue)
    im = img_mat(kind, .6); sw = 1.3 * 2048 / 176 / 2
    for fy in (-1, 1):
        e = y + fy * .47
        P = [(-sw * -fy, e, 5.6), (sw * -fy, e, 5.6), (sw * -fy, e, 6.9), (-sw * -fy, e, 6.9)]
        mesh_obj(f"gate_sign{fy}", quad("q", P, im), [im])
    if clock is not None:
        box("gate_clock", -3.2, 3.2, y - .3, y + .3, 7.0, 8.3, dk)
        lm = emat("clock_led", (.9, .5, .05), .5, (1.0, .45, .04), 5.0, haze=False)
        ts = [text(f"gate_time{fy}", hms(clock(0)), 1.25, (0, y + fy * .32, 7.65), fy, lm) for fy in (-1, 1)]
        def upd(t):
            s = hms(clock(t))
            for o in ts:
                if o.data.body != s:
                    o.data.body = s
        DYN.append(upd); upd(0)


class Drops:
    """水しぶき・紙ふぶき：N 個の小さな粒を 1 つのメッシュで。粒 i は born[i] に p0[i] から v0[i] で飛び、重力で落ちる（drag：空気の抵抗、flutter：ひらひら）"""
    def __init__(self, name, p0, v0, born, size, m, g=9.8, drag=0.0, flutter=0.0, card=False, life=9.0, seed=1, mi=None, floor=0.02):
        self.p0 = np.asarray(p0, float); self.v0 = np.asarray(v0, float); self.born = np.asarray(born, float); N = len(self.p0); self.N = N
        r = np.random.default_rng(seed); self.size = np.broadcast_to(np.asarray(size, float), (N,)) * r.uniform(.6, 1.3, N); self.g = g; self.drag = drag; self.fl = flutter; self.life = life; self.floor = floor
        self.ph = r.uniform(0, 6.28, (N, 3)); self.wf = r.uniform(5, 11, N)
        if card:
            tv = np.array([(-1, -.6, 0), (1, -.6, 0), (1, .6, 0), (-1, .6, 0)], float); tf = [(0, 1, 2, 3)]
        else:
            bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0); tv = np.array([tuple(x.co) for x in bm.verts], float); tf = [tuple(x.index for x in fc.verts) for fc in bm.faces]; bm.free()
        self.tv = tv; self.card = card; nv = len(tv)
        me = bpy.data.meshes.new(name); me.from_pydata(np.zeros((N * nv, 3)).tolist(), [], [tuple(i * nv + k for k in fc) for i in range(N) for fc in tf]); me.update()
        for mm in (m if isinstance(m, (list, tuple)) else [m]):
            me.materials.append(mm)
        if mi is not None:
            me.polygons.foreach_set("material_index", np.repeat(np.asarray(mi, np.int32), len(tf)))
        if not card:
            me.polygons.foreach_set("use_smooth", np.ones(len(me.polygons), bool))
        self.me = me; self.o = link(bpy.data.objects.new(name, me)); DYN.append(self.update); self.update(0.0)

    def update(self, t):
        tau = t - self.born; on = (tau > 0) & (tau < self.life); ta = np.clip(tau, 0, None)[:, None]
        if self.drag > 0:
            k = self.drag; vt = self.g / k      # 終端の速さ
            p = self.p0 + self.v0 * (1 - np.exp(-k * ta)) / k; p[:, 2] -= (vt * (ta - (1 - np.exp(-k * ta)) / k))[:, 0]
        else:
            p = self.p0 + self.v0 * ta; p[:, 2] -= .5 * self.g * (ta ** 2)[:, 0]
        if self.fl:
            p[:, 0] += self.fl * np.sin(self.wf * ta[:, 0] * .35 + self.ph[:, 0]) * np.minimum(1, ta[:, 0]); p[:, 1] += self.fl * np.cos(self.wf * ta[:, 0] * .3 + self.ph[:, 1]) * np.minimum(1, ta[:, 0])
        gone = p[:, 2] < self.floor; p[:, 2] = np.maximum(p[:, 2], self.floor)
        s = np.where(on & ~(gone & (not self.card)), self.size, 0.0)[:, None, None]; v = self.tv[None] * s
        if self.card:
            a = np.where(gone, 0.0, self.wf * ta[:, 0] + self.ph[:, 2])[:, None]; c, sn = np.cos(a), np.sin(a)
            y, z = v[..., 1].copy(), v[..., 2].copy(); v[..., 1] = y * c - z * sn; v[..., 2] = y * sn + z * c
            a = self.ph[:, 0][:, None]; c, sn = np.cos(a), np.sin(a); x, y = v[..., 0].copy(), v[..., 1].copy(); v[..., 0] = x * c - y * sn; v[..., 1] = x * sn + y * c
        v = v + p[:, None]
        self.me.vertices.foreach_set("co", v.reshape(-1).astype(np.float32)); self.me.update()


def confetti(name, center, n=500, t0=0.0, spread=6.0, up=7.0, seed=1, dur=.5):
    """紙ふぶき（center から吹き上がって、ひらひら落ちる）"""
    r = np.random.default_rng(seed); p0 = np.asarray(center, float)[None] + r.normal(0, .25, (n, 3))
    v0 = np.stack([r.normal(0, spread, n), r.normal(0, spread, n), r.uniform(.5, 1.3, n) * up], 1)
    cols = [mat(f"conf{i}", c, .5) for i, c in enumerate([(.9, .1, .1), (.95, .75, .05), (.1, .4, .9), (.9, .9, .9), (.1, .7, .3), (.9, .35, .6)])]
    return Drops(name, p0, v0, t0 + r.uniform(0, dur, n), .075, cols, g=9.8, drag=2.6, flutter=.35, card=True, life=30., seed=seed, mi=r.integers(0, len(cols), n))
