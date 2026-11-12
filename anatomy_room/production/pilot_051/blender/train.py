"""pilot_051 の新幹線（オリジナルの白い流線形。特定の会社の色・ロゴ・形式名は付けない）。前が +Y、レールの上の面が z=0 の座標で作り、
root を線路の上（z=track.TOP）に置く。16 両 × 25 m（先頭・最後尾は長い鼻）。車輪は軸ごとの物で、進んだ距離 ÷ 半径だけ回す。"""
from common import *

CAR, GAP = 25.0, .5            # 車両の長さ・すき間（ほろ）
W, H, FLOOR = 1.69, 3.6, .38   # 車体の半幅・屋根の高さ・床下の高さ（レールの上から）
NOSE = 11.0                    # 鼻の長さ
WR = .43                       # 車輪の半径
GAUGE = 1.435


def paint():
    if "tr_white" in MATS:
        return [MATS[k] for k in ("tr_white", "tr_glass", "tr_line", "tr_under")]
    w = mat("tr_white", (.86, .87, .88), .18, haze=True); b = w.node_tree.nodes["Principled BSDF"]
    b.inputs["Coat Weight"].default_value = .6; b.inputs["Coat Roughness"].default_value = .05
    g = mat("tr_glass", (.012, .016, .022), .06); g.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
    ln = mat("tr_line", (.02, .2, .3), .25)           # オリジナルの帯（深い青緑）
    u = mat("tr_under", (.12, .13, .14), .5, .3)
    MATS.update(tr_white=w, tr_glass=g, tr_line=ln, tr_under=u); return [w, g, ln, u]


def _section(s, nose):
    """鼻の先からの距離 s（m）での断面：半幅・上端・下端"""
    if not nose or s >= NOSE:
        return W, H, FLOOR
    u = clamp(s / NOSE)
    w = float(np.interp(u, [0, .08, .25, .5, .75, 1], [.32, .75, 1.22, 1.52, 1.66, W]))           # 細い鼻先から広がる
    top = float(np.interp(u, [0, .1, .3, .48, .6, .75, .88, 1], [.62, .92, 1.22, 1.55, 2.25, 3.05, 3.45, H]))   # 低く長い鼻 → 運転席でふくらむ
    return w, min(H, top), FLOOR + .12 * (1 - u) ** 2


def _ring(w, top, bot, n=56):
    """断面の点（x, z）：側面は少し内に傾き、屋根と裾は丸い（スーパー楕円）"""
    pts = []; zc = (top + bot) / 2; hh = (top - bot) / 2
    for i in range(n):
        a = 2 * math.pi * i / n; c, s_ = math.cos(a), math.sin(a)
        x = w * math.copysign(abs(c) ** (2 / 3.2), c); z = zc + hh * math.copysign(abs(s_) ** (2 / (3.6 if s_ > 0 else 6.0)), s_)
        x *= 1 - .05 * clamp((z - (bot + .4 * (top - bot))) / (top - bot))   # 上ほど少し細く
        pts.append((x, z))
    return pts


def car_body(name, front_nose, back_nose, y0):
    """y0：車両の前の端（y の大きい方）。前・後ろに鼻をつけるか"""
    ws, gl, ln, un = paint(); bm = bmesh.new(); rows = []; ys = []
    n_nose = 40
    st = [i / n_nose * NOSE for i in range(n_nose + 1)] if front_nose else [0.0]
    mid = [NOSE + (CAR - 2 * NOSE) * k / 12 for k in range(1, 12)] if (front_nose or back_nose) else [CAR * k / 12 for k in range(1, 12)]
    stb = [CAR - i / n_nose * NOSE for i in range(n_nose, -1, -1)] if back_nose else [CAR]
    stations = sorted(set([round(v, 4) for v in st + mid + stb]))
    for s in stations:
        sf, sb = s, CAR - s
        w, top, bot = W, H, FLOOR
        if front_nose and sf < NOSE:
            w, top, bot = _section(sf, True)
        if back_nose and sb < NOSE:
            w, top, bot = _section(sb, True)
        rows.append([bm.verts.new((x, y0 - s, z)) for x, z in _ring(w, top, bot)]); ys.append(s)
    n = len(rows[0])
    for j in range(len(rows) - 1):
        for i in range(n):
            f = bm.faces.new((rows[j][i], rows[j][(i + 1) % n], rows[j + 1][(i + 1) % n], rows[j + 1][i]))
            c = f.calc_center_median(); z = c.z; sf = y0 - c.y; sb = CAR - sf; edge = min(sf if front_nose else 99, sb if back_nose else 99)
            mi = 0
            wtop = _section(edge, True)[1] if edge < NOSE else H
            if edge < NOSE and NOSE * .5 < edge < NOSE * .8 and z > wtop - .75 and abs(c.x) < 1.1:
                mi = 1                                              # 運転席の窓
            elif edge >= NOSE * .95 and 2.12 < z < 2.62 and abs(c.x) > 1.2:
                mi = 1                                              # 客室の窓の帯
            elif 1.62 < z < 1.78 and abs(c.x) > 1.0:
                mi = 2                                              # 帯
            elif z < FLOOR + .35:
                mi = 3                                              # 床下・すそ
            f.material_index = mi
    if not front_nose:
        bm.faces.new(rows[0][::-1]).material_index = 3
    if not back_nose:
        bm.faces.new(rows[-1]).material_index = 3
    o = mesh_obj(name, bm, [ws, gl, ln, un])
    if front_nose or back_nose:                                     # 前照灯（鼻先の両わき）
        lm = emat("tr_lamp", (.9, .9, .85), .2, (1, .97, .9), 6.0, haze=False)
        for sx in (-1, 1):
            for nose_y, on in ((y0 - 1.15, front_nose), (y0 - CAR + 1.15, back_nose)):
                if on:
                    lb = bmesh.new(); bmesh.ops.create_uvsphere(lb, u_segments=16, v_segments=8, radius=.16); bmesh.ops.scale(lb, vec=(1.3, .6, .55), verts=lb.verts)
                    w_, t_, b_ = _section(1.15, True); bmesh.ops.translate(lb, vec=(sx * (w_ * .78), nose_y, b_ + (t_ - b_) * .55), verts=lb.verts)
                    l_ = mesh_obj(f"{name}_lamp{sx}{int(on)}{int(nose_y)}", lb, [lm]); l_.parent = o
    for p in o.data.polygons:
        p.use_smooth = True
    sd = o.modifiers.new("sd", "SUBSURF"); sd.levels = 1; sd.render_levels = 2
    return o


def _wheel_mesh():
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=WR, radius2=WR, depth=.14)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=40, radius1=WR + .03, radius2=WR + .03, depth=.03)   # フランジ
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=bm.verts)
    return bm


def bogie(name, yc, root):
    """台車：2 軸（軸距 2.5 m）。返り値：車輪（軸ごと、X 軸まわりに回す）"""
    st = mat("tr_steel", (.18, .18, .19), .4, .9); wh = []
    fr = bmesh.new(); r_ = bmesh.ops.create_cube(fr, size=1.0); bmesh.ops.scale(fr, vec=(2.2, 3.3, .35), verts=r_["verts"]); bmesh.ops.translate(fr, vec=(0, yc, WR + .1), verts=r_["verts"])
    f = mesh_obj(name + "_frame", fr, [st]); f.parent = root
    for k, dy in enumerate((-1.25, 1.25)):
        bm = _wheel_mesh(); ax = bmesh.ops.create_cone(bm, cap_ends=True, segments=16, radius1=.09, radius2=.09, depth=GAUGE + .3)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "Y"), verts=ax["verts"])
        w2 = _wheel_mesh()
        o = mesh_obj(f"{name}_ax{k}", bm, [st]); o.parent = root; o.location = (0, yc + dy, WR); o.rotation_mode = "XYZ"
        for sx in (-1, 1):
            ww = mesh_obj(f"{name}_w{k}{sx}", _wheel_mesh(), [st]); ww.parent = o; ww.location = (sx * (GAUGE / 2 + .02), 0, 0)
        wh.append(o)
    return wh


def build_train(n=16, name="tr"):
    """root（線路の上の点。先頭の鼻の先が root の y）と、車輪の一覧"""
    root = link(bpy.data.objects.new(name, None)); wheels = []; un = paint()[3]
    for i in range(n):
        y0 = -i * (CAR + GAP)
        body = car_body(f"{name}_car{i}", i == 0, i == n - 1, y0); body.parent = root
        for yc in (y0 - 4.2, y0 - CAR + 4.2):
            wheels += bogie(f"{name}_b{i}_{int(-yc)}", yc, root)
        if i < n - 1:                                            # ほろ（車両のつなぎ目）
            bm = bmesh.new(); r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(2.6, GAP + .3, 2.6), verts=r_["verts"])
            bmesh.ops.translate(bm, vec=(0, y0 - CAR - GAP / 2, FLOOR + 1.6), verts=r_["verts"]); g = mesh_obj(f"{name}_gap{i}", bm, [un]); g.parent = root
    return dict(root=root, wheels=wheels)


def place(T, y, z):
    """先頭の鼻の先を y に。車輪は進んだ距離に合わせて回す"""
    T["root"].location = (0, y, z)
    for w in T["wheels"]:
        w.rotation_euler = (-y / WR, 0, 0)
