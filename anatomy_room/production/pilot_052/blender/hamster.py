"""pilot_052 のハムスターと回し車（Sketchfab、どちらも CC BY 4.0。作者は assets/sketchfab/*/credit.json）。
ハムスター：「Curious Golden Hamster」by restore50（後ろ足で立った姿勢のスキャン。骨組みはない）。
  体を丸ごと傾け・上下させて姿勢を作る（脚を骨で大きく曲げると形が崩れるため）：
  sit＝立ったまま、run＝前に約 70° 傾けて回し車の内側を走る（上下の揺れと回し車の回転で見せる）、curl＝横たわって目を閉じる（まぶた）。
回し車：「Hamster Wheel」by Jenosuke。中の輪を回す。
寸法：ハムスターは体長 約 15 cm（立った高さ 13 cm）、回し車は直径 21 cm。原点はどちらも足もと（地面）。"""
from common import *

SKF = os.path.join(HERE, "..", "assets", "sketchfab")
H_SIZE = .13            # ハムスターの立った高さ m
W_DIAM = .28            # 回し車の直径 m（ゴールデンハムスター向けの大きさ）


def _import(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(SKF, name, "scene.gltf"))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c_ in list(o.users_collection):
            c_.objects.unlink(o)
        mlink(o)
    bpy.context.view_layer.update()
    meshes = [o for o in new if o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector([min(p[k] for p in pts) for k in range(3)]); hi = Vector([max(p[k] for p in pts) for k in range(3)])
    return new, meshes, lo, hi


def _holder(name, new, lo, hi, size, axis=2):
    """読み込んだ物を、足もとが原点・高さ（axis 方向の大きさ）が size になる空の親にまとめる"""
    h = mlink(bpy.data.objects.new(name, None)); h.rotation_mode = "XYZ"
    inner = mlink(bpy.data.objects.new(name + "_in", None)); inner.parent = h
    s = size / (hi - lo)[axis]; inner.scale = (s, s, s); inner.location = -Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)) * s
    for o in new:
        if o.parent is None:
            o.parent = inner
    return h


def _lid_mat():
    if "h_lid" in MATS:
        return MATS["h_lid"]
    m = mat("h_lid", (.42, .26, .14), .7, haze=False); MATS["h_lid"] = m; return m


class Hamster:
    """1 匹（毛はテクスチャ）。pose(pos, heading, mode, t, k) で姿勢をつける。heading 0 で +Y を向く"""
    def __init__(self, name):
        new, meshes, lo, hi = _import("golden")
        self.root = _holder(name, new, lo, hi, H_SIZE)
        self.pivot = mlink(bpy.data.objects.new(name + "_pv", None)); self.pivot.rotation_mode = "XYZ"
        inner = self.root.children[0]; inner.parent = self.pivot; self.pivot.parent = self.root
        self.inner = inner; self.inner.rotation_euler = (0, 0, math.pi)        # 模型の顔は -Y → +Y に向ける
        # まぶた（寝るときに目を閉じる）：目の位置は模型の座標の割合（立った高さの 0.86、左右 ±0.2、前 0.3）
        self.lids = []
        for sx in (-1, 1):
            bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=.0048)
            o = mesh_obj(f"{name}_lid{sx}", bm, [_lid_mat()]); o.parent = self.pivot; o.location = (sx * .0185, .033, H_SIZE * .865); o.scale = (1, .6, .08); o.rotation_mode = "XYZ"
            self.lids.append(o)
        self.objs = [self.root, self.pivot] + self.lids

    def pose(self, pos, heading=0.0, mode="sit", t=0.0, k=1.0, lid=None, look=(0.0, 0.0)):
        R = self.root; R.location = Vector(pos); R.rotation_euler = (0, 0, heading); P = self.pivot
        br = 1 + .025 * math.sin(t * 2 * math.pi / (2.4 if mode == "curl" else .9))
        if mode == "run":          # 前に傾けて走る：速い上下の揺れ（1 秒に約 6 歩）と、少しの左右
            ph = t * 6.0 * 2 * math.pi
            P.rotation_euler = (-math.radians(56) * k, math.radians(3) * math.sin(ph / 2), look[1]); P.location = (0, -.035 * k, .014 * abs(math.sin(ph)) * k)
            P.scale = (1, 1, 1 + .03 * math.sin(ph))
            l_ = 0.0 if lid is None else lid
        elif mode == "curl":       # 横たわって寝る：前に倒して低く、寝息
            P.rotation_euler = (-math.radians(84) * k, math.radians(-10) * k, .2 * k); P.location = (0, -.045 * k, .0 * k); P.scale = (1, 1, br)
            l_ = 1.0 if lid is None else lid
        else:                      # 立って見る：首をかしげる・寝息
            P.rotation_euler = (look[0], .05 * math.sin(t * .7), look[1] + .06 * math.sin(t * .5)); P.location = (0, 0, 0); P.scale = (1, 1, br)
            l_ = 0.0 if lid is None else lid
        for o in self.lids:
            o.scale = (1, .6, .08 + .92 * clamp(l_)) if l_ > 0 else (1, .6, .001)


def _tube(bm, a, b, r, seg=6):
    a = Vector(a); d = Vector(b) - a; h = d.length
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h)
    bmesh.ops.translate(bm, vec=(0, 0, h / 2), verts=res["verts"])
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=d.to_track_quat("Z", "Y").to_matrix(), verts=res["verts"]); bmesh.ops.translate(bm, vec=a, verts=res["verts"])


def _ring(bm, c, R, y, r, n=48):
    P = [Vector((c[0] + R * math.cos(2 * math.pi * i / n), y, c[2] + R * math.sin(2 * math.pi * i / n))) for i in range(n)]
    for i in range(n):
        _tube(bm, P[i], P[(i + 1) % n], r, 5)


class Wheel:
    """回し車 1 台（自作：銀色の針金の輪＋横棒＋スポーク＋台、直径 21 cm、幅 7 cm）。輪は X 軸のまわりに回る。原点は台の下"""
    def __init__(self, name, col=(.78, .79, .8)):
        metal = mat("wheel_metal", col, .28, 1.0); base_m = mat("wheel_base", (.86, .84, .8), .45)
        R = W_DIAM / 2; hub = (0, 0, R + .025); W = .07
        bm = bmesh.new()
        for x in (-W / 2, W / 2):                       # 両側の輪（x が幅の向き。回る軸は X）
            P = [Vector((x, R * math.cos(2 * math.pi * i / 48), R * math.sin(2 * math.pi * i / 48))) for i in range(48)]
            for i in range(48):
                _tube(bm, P[i], P[(i + 1) % 48], .0022, 5)
        for i in range(30):                              # 足場の横棒
            a = 2 * math.pi * i / 30; y, z = R * math.cos(a), R * math.sin(a); _tube(bm, (-W / 2, y, z), (W / 2, y, z), .0015, 5)
        for i in range(6):                               # スポーク（片側）
            a = 2 * math.pi * i / 6; _tube(bm, (W / 2, 0, 0), (W / 2, R * math.cos(a), R * math.sin(a)), .0018, 5)
        _tube(bm, (W / 2 - .002, 0, 0), (W / 2 + .03, 0, 0), .004, 10)
        self.ring = mesh_obj(name + "_ring", bm, [metal]); self.ring.rotation_mode = "XYZ"
        bm = bmesh.new(); _tube(bm, (W / 2 + .03, 0, -.002), (W / 2 + .03, 0, -R - .025), .003, 8)   # 支柱
        r_ = bmesh.ops.create_cube(bm, size=1.0); bmesh.ops.scale(bm, vec=(.11, .2, .008), verts=r_["verts"]); bmesh.ops.translate(bm, vec=(.02, 0, -R - .021), verts=r_["verts"])
        self.stand = mesh_obj(name + "_stand", bm, [metal]); self.stand.data.materials.append(base_m)
        for p in self.stand.data.polygons:
            if p.center.z < -R - .015:
                p.material_index = 1
        # 小さな発電機（軸の外側）と、豆電球への赤い線は場面ごとに
        bm = bmesh.new(); _tube(bm, (W / 2 + .03, 0, 0), (W / 2 + .06, 0, 0), .016, 16)
        self.gen = mesh_obj(name + "_gen", bm, [mat("gen_body", (.12, .13, .15), .4, .5)])
        self.root = link(bpy.data.objects.new(name, None))
        for o in (self.ring, self.stand, self.gen):
            o.parent = self.root
        self.ring.location = self.stand.location = self.gen.location = hub
        self.hub = hub; self.R = R

    def place(self, pos, heading=0.0):
        self.root.location = Vector(pos); self.root.rotation_euler = (0, 0, heading)

    def spin(self, angle):
        self.ring.rotation_euler = (angle, 0, 0)

    def runner_pos(self):
        """中を走るハムスターの足もとの位置（世界座標）：輪のいちばん下"""
        return self.root.matrix_world @ (Vector(self.hub) + Vector((0, 0, -self.R + .004)))
