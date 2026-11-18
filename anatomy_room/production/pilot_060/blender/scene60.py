"""pilot_060 v4「日本終末時計」の 3D（Blender Cycles）。新ドパ設計 v2（061 型、2026-11-18 ユーザーの指示で 2D から作り直し）。
ショット＝セリフの行（s00〜s12）。畳の部屋の壁に大きな時計、手前に 100 体の人形（1 体＝人口の 1%）。
出来事ごとに、失われた割合だけ人形が倒れ、時計の針が「真夜中まで N 秒」へ拍の頭で動く。年の木札・本物の写真（PD）の額が拍の頭に落ちてくる。
動き・カメラの着地はすべて表拍（lbeat の整数）。閃光なし。数字は scripts/pilot_060/sim/clock.json（assets/plan.js）。
blender -b -P blender/scene60.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib60 import *  # noqa: F401,F403

O = K.args()
NAMES = [l["scene"] for l in PLAN["lines"]]
TL = json.load(open(os.path.join(HERE, "..", "work", "timeline.json"), encoding="utf-8")); CUE = TL["cues"]
EV = {e["key"]: e for e in PLAN["events"]}
sc = setup(samples=O["samples"] if "--samples" in sys.argv else 48)
world(strength=.9, rot=.8)
KEY = area_light("key", (-4, -6, 8), (0, 0, 1.5), 5, 1500); RIM = area_light("rim", (5, 2, 6), (0, 2, 2), 4, 700, (1, .78, .55))
cam = K.Cam(); ANIM = [cam.o]


def lbeat(name, k):
    """ショットの頭から数えて k 番目の拍（ショットの中の秒）"""
    c = CUE[name]; return (round(c / BP) + k) * BP - c                  # 0＝切り替わりの拍（行の頭は拍にそろえてある）


def look(P, A, lens=40, fstop=2.8, roll=0.0):
    P, A = Vector(P), Vector(A); cam.look(P, A, lens, roll); cam_dof(cam, (P - A).length, fstop)


def vlerp(a, b, u):
    return [lerp(x, y, u) for x, y in zip(a, b)]


def eio(u):
    u = clamp(u); return 16 * u ** 5 if u < .5 else 1 - (-2 * u + 2) ** 5 / 2


def snap(keys, t, mv=.42, kick=.09):
    """素早いカメラ（061 と同じ）：keys の時刻に着く。動くのは着く直前の mv 秒だけ、あいだは少しずつ寄る"""
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2], keys[0][3], 0.0
    for n, ((t0, p0, a0, l0), (t1, p1, a1, l1)) in enumerate(zip(keys, keys[1:])):
        if t <= t1:
            d = min(mv, (t1 - t0) * .8); ts = t1 - d
            p0d = vlerp(p0, a0, .07)
            if t < ts:
                return vlerp(p0, a0, .07 * ease((t - t0) / max(1e-3, ts - t0))), a0, l0, 0.0
            u = eio((t - ts) / d); sg = 1 if n % 2 else -1
            return vlerp(p0d, p1, u), vlerp(a0, a1, u), lerp(l0, l1, u), sg * kick * math.sin(math.pi * u)
    t1, p1, a1, l1 = keys[-1]; h = clamp((t - t1) / 3.0)
    return vlerp(p1, a1, .05 * ease(h)), a1, l1, 0.0


def go(name, keys, t, fstop, mv=.42, kick=.09):
    """keys：[(拍, 位置, 注視点, 焦点距離), ...]（拍は lbeat の整数。最初は 0 秒）"""
    ks = [(0 if i == 0 else lbeat(name, k), p, a, l) for i, (k, p, a, l) in enumerate(keys)]
    P, A, L, r = snap(ks, t, mv, kick); look(P, A, L, fstop, r)


def drop(o, base, t, t0, h=3.0, dur=.32, rz=0.0):
    u = (t - t0) / dur
    if u < 0:
        o.location = (base[0], base[1], -50); return
    z = base[2] + h * (1 - u * u) if u < 1 else base[2] + .05 * h * math.exp(-9 * (t - t0 - dur)) * abs(math.sin(16 * (t - t0 - dur)))
    o.location = (base[0], base[1], z); o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], rz)


# ---------------------------------------------------------------- 部屋・時計・人形
CLK = Vector((0, 3.25, 2.75)); RAD = 2.1
S = {}


def wood():
    return pbr_mat("lacq", "lacquer", 1.0, (.55, .32, .2), .8, box_proj=True)


def room():
    clear_scene()
    fl = plane("floor", 40, 40, (0, 0, 0), pbr_mat("tatami", "tatami", 6.0, (.85, .8, .62), 1.2))
    wall = plane("wall", 40, 16, (0, 3.6, 8), pbr_mat("plaster", "plaster", 3.0, (.62, .52, .42), 1.0), rot=(math.pi / 2, 0, 0))
    beam = box("beam", (40, .25, .3), (0, 3.45, 5.6), pbr_mat("hinoki", "hinoki", 1.0, (.55, .4, .28), 1.0, box_proj=True), bevel=.01)
    base = box("skirt", (40, .2, .18), (0, 3.5, .09), wood(), bevel=.01)


def clock():
    m = wood(); br = gold_mat("brass", rough=.25, tint=(.9, .66, .32))
    body = cyl("clk_body", RAD + .28, .32, (CLK.x, CLK.y + .1, CLK.z), m, 128, bevel=.04); body.rotation_euler = (math.pi / 2, 0, 0)
    ring = cyl("clk_ring", RAD + .08, .1, (CLK.x, CLK.y - .1, CLK.z), br, 128, bevel=.03); ring.rotation_euler = (math.pi / 2, 0, 0)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap"); bmesh.ops.create_circle(bm, cap_ends=True, segments=128, radius=RAD * .985)
    for fc in bm.faces:
        for lp in fc.loops:
            co = lp.vert.co; lp[uvl].uv = (co.x / (2 * RAD) + .5, co.y / (2 * RAD) + .5)
    face = bpy.data.objects.new("clk_face", mesh_from_bm("clk_face", bm, [image_mat("clkface", os.path.join(GEN, "clockface.jpg"), .45)], smooth=False)); link(face)
    face.location = (CLK.x, CLK.y - .16, CLK.z); face.rotation_euler = (math.pi / 2, 0, 0)
    glass_m = bpy.data.materials.new("glass"); glass_m.use_nodes = True; b = glass_m.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = .02; b.inputs["IOR"].default_value = 1.45
    hand_m = plain("handink", (.03, .025, .02), .3, metal=.6, coat=.6)
    piv = empty("clk_piv", (CLK.x, CLK.y - .22, CLK.z))
    mn = empty("clk_min", (0, 0, 0)); parent(mn, piv); parent(box("clk_min_b", (.1, .04, RAD * .92), (0, 0, RAD * .36), hand_m, bevel=.01), mn)
    parent(box("clk_min_t", (.05, .041, .35), (0, 0, -.18), hand_m, bevel=.01), mn)
    hr = empty("clk_hr", (0, .02, 0)); parent(hr, piv); parent(box("clk_hr_b", (.17, .04, RAD * .58), (0, 0, RAD * .22), hand_m, bevel=.01), hr)
    sec_m = plain("secred", (.55, .04, .03), .35, coat=.5)
    parent(cyl("clk_cap", .13, .08, (0, -.06, 0), br, 48), piv).rotation_euler = (math.pi / 2, 0, 0)
    S["min"], S["hr"] = mn, hr; ANIM.extend([mn, hr])
    # 737 年（31 秒）の印：赤い小さな札（s10 で出す）
    a = math.radians(-31.4 / 10); r = RAD * 1.08
    mk = empty("clk_mark", (CLK.x + r * math.sin(a), CLK.y - .2, CLK.z + r * math.cos(a))); mk.rotation_euler = (0, a, 0)
    parent(box("clk_mark_b", (.07, .05, .34), (0, 0, 0), sec_m, bevel=.01), mk); S["mark"] = mk; ANIM.append(mk)


def set_hands(sec):
    """真夜中まで sec 秒：長針は 12 から sec/10 度だけ左（反時計回り）、短針は 12 時の少し手前"""
    S["min"].rotation_euler = (0, math.radians(-sec / 10), 0); S["hr"].rotation_euler = (0, math.radians(-sec / 120), 0)


# 人形 100 体（1 体＝人口の 1%）。倒れる順は決まった乱数（散らばって倒れる）
GRID = [(-2.79 + (i % 10) * .62, -.9 - (i // 10) * .62) for i in range(100)]
ORDER = list(range(100)); random.Random(60).shuffle(ORDER)


def people():
    m = plain("ceramic", (.86, .84, .8), .35, coat=.5); S["ppl"] = []
    for i, (x, y) in enumerate(GRID):
        f = figure(f"p{i}", (x, y, 0), .46, m); f.rotation_euler = (0, 0, random.Random(i).uniform(-.25, .25)); S["ppl"].append(f); ANIM.append(f)


def fall_dir(i):
    return 1 if random.Random(1000 + i).random() < .5 else -1


def set_people(t, plan_):
    """plan_：[(t0, 倒れる順の始め, 終わり)] のリスト。それより前は立っている。倒れた人形は床に横たわる"""
    st = {}
    for t0, a, b in plan_:
        for k in range(a, b):
            st[ORDER[k]] = t0
    for i, f in enumerate(S["ppl"]):
        rz = f.rotation_euler[2]; t0 = st.get(i)
        if t0 is None or t < t0:
            f.rotation_euler = (0, 0, rz); f.location.z = 0; continue
        u = (t - t0) / .28; ang = (math.pi / 2) * (clamp(u) ** 2) if u < 1 else math.pi / 2 - .06 * math.exp(-8 * (t - t0 - .28)) * abs(math.sin(18 * (t - t0 - .28)))
        f.rotation_euler = (fall_dir(i) * ang, 0, rz); f.location.z = 0


def plaque(name, s, loc, size=.3, rz=.12):
    o = label(name, s, loc, size, face_rot=rz); ANIM.append(o); return o


def photo_frame(name, key, loc, rz=-.3, w=1.7):
    """白い縁の額（本物の写真、PD）。少し後ろへ傾けて立てる"""
    p = os.path.join(HERE, "..", "assets", "photo", key + ".jpg"); im = bpy.data.images.load(p, check_existing=True); h = w * im.size[1] / im.size[0]
    root = empty(name, loc); root.rotation_euler = (math.radians(-12), 0, rz)
    parent(box(name + "_f", (w + .22, .07, h + .22), (0, 0, h / 2 + .11), plain("frame", (.12, .08, .05), .5, coat=.4), bevel=.02), root)
    parent(box(name + "_m", (w + .1, .072, h + .1), (0, -.002, h / 2 + .11), plain("mat", (.93, .9, .84), .7), bevel=0), root)
    parent(plane(name + "_p", w, h, (0, -.04, h / 2 + .11), image_mat("ph_" + key, p, .5), rot=(math.pi / 2, 0, 0)), root)
    ANIM.append(root); return root


def label(name, s, loc, size=.28, face_rot=0.0):
    """木の札に金の文字（立てて置く）"""
    root = empty(name, loc); root.rotation_euler = (0, 0, face_rot)
    w = len(s) * size * .78 + size * .9; h = size * 1.55
    parent(box(name + "_b", (w, .09, h), (0, 0, h / 2), pbr_mat("plankw", "wood_table_001", 1.2, (.75, .6, .48), 1.3, box_proj=True), bevel=.02), root)
    parent(text_obj(name + "_t", s, (0, -.05, h / 2), size, gold_mat("goldtext", .22), extrude=.012, font="BIZUDPGothic-Bold.ttf"), root)
    return root


def base_set():
    room(); ANIM[:] = [cam.o]; clock(); people()


def hand_move(t, frm, to, t0, d=.3):
    """拍の頭 t0 に向かって動き、t0 に着く（着いたら小さく揺れる）"""
    if t < t0 - d:
        return frm
    if t < t0:
        return lerp(frm, to, eio((t - (t0 - d)) / d))
    v = t - t0; return to + (frm - to) * .04 * math.exp(-7 * v) * math.sin(22 * v)


# 時計の位置（よく使うカメラ）
TOP = (0, CLK.y, CLK.z + RAD * .62)          # 12 のあたり
FIG = (0, -3.6, .3)                           # 人形の中央
W0 = ((0, -10.5, 3.6), (0, .5, 1.9), 28)      # 部屋全体


def s_s00():
    base_set()


def a_s00(u, t, f):
    sec = 240 - 6 * max(0, int(t / BP))      # 拍ごとに針が 1 目盛り進む（冒頭の問い：いま、真夜中まで何秒？）
    set_hands(hand_move(t, sec + 6, sec, int(t / BP) * BP + BP, .12) if t > BP else sec); set_people(t, []); S["mark"].location.z = -50
    go("s00", [(0, (0, CLK.y - 2.0, TOP[2] + .2), TOP, 50), (2, (-1.2, CLK.y - 4.8, CLK.z + .3), (0, CLK.y, CLK.z), 38), (4, (3.4, -7.0, 1.0), FIG, 30),
               (6, *W0), (8, (.3, CLK.y - 3.0, TOP[2] - .2), TOP, 42)], t, 4.0)


def s_s01():
    base_set()


def a_s01(u, t, f):
    tf = lbeat("s01", 4); set_people(t, [(tf, 0, 10)]); set_hands(hand_move(t, 240, 60, lbeat("s01", 5))); S["mark"].location.z = -50
    go("s01", [(0, (-3.6, -8.2, 2.2), FIG, 32), (2, (0, -9.6, 5.6), (0, -3.4, 0), 30), (4, (2.6, -6.4, .9), (0, -2.8, .3), 34),
               (5, (0, CLK.y - 4.2, CLK.z + .4), (0, CLK.y, CLK.z + .3), 40), (7, *W0)], t, 3.2)


def s_ev(name, year, key=None):
    def s():
        base_set(); S["pl"] = plaque(name + "_pl", year, (-3.5, .3, 0), .34, .3)
        S["ph"] = photo_frame(name + "_ph", key, (3.5, .4, 0)) if key else None
    return s


def a_ev(name, k_ev, frm, keys, fall_beats=(), hand_beat=None, photo_beat=2):
    """出来事の場面：年の札（拍 0）→ 写真の額（photo_beat）→ 人形が倒れる（fall_beats）→ 針（hand_beat）"""
    e = EV[k_ev]; n = round(e["share"] * 100)

    def a(u, t, f):
        drop(S["pl"], (-3.5, .3, 0), t, lbeat(name, 0), h=2.5, rz=.3)
        if S["ph"] is not None:
            drop(S["ph"], (3.5, .4, 0), t, lbeat(name, photo_beat), h=2.5, rz=-.3)
        plan_, per = [], (n + len(fall_beats) - 1) // max(1, len(fall_beats))
        for j, kb in enumerate(fall_beats):
            plan_.append((lbeat(name, kb), j * per, min(n, (j + 1) * per)))
        set_people(t, plan_); S["mark"].location.z = -50
        set_hands(hand_move(t, frm, e["sec"], lbeat(name, hand_beat)) if hand_beat is not None else frm)
        go(name, keys, t, 3.0)
    return a


PL = (-3.5, .3, .35); PH = (3.5, .4, .9)
s_s02 = s_ev("s02", "737年", None)
a_s02 = a_ev("s02", "H1", 240, [(0, (-5.2, -3.6, 1.6), PL, 34), (2, (0, -9.8, 4.8), (0, -3.4, 0), 30), (3, (-1.6, -6.2, .7), (.2, -3.0, .3), 32),
                                (5, (2.4, -7.6, 2.2), FIG, 30)], fall_beats=(2, 3))
s_s03 = s_ev("s03", "737年", None)


def a_s03(u, t, f):
    S["pl"].location.z = -50; set_people(t, [(-9, 0, 30)]); S["mark"].location.z = -50
    set_hands(hand_move(t, 240, EV["H1"]["sec"], lbeat("s03", 1)))
    go("s03", [(0, (0, CLK.y - 6.0, CLK.z + .6), (0, CLK.y, CLK.z + .4), 36), (1, (0, CLK.y - 2.2, TOP[2] + .15), TOP, 55)], t, 3.0, mv=.3, kick=.12)


s_s04 = s_ev("s04", "1780年代", "tenmei")
a_s04 = a_ev("s04", "H2", 240, [(0, (-5.0, -3.4, 1.4), PL, 34), (2, (5.2, -3.6, 1.6), PH, 34), (4, (0, -8.6, 3.0), FIG, 30),
                                (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48), (7, *W0)], fall_beats=(4,), hand_beat=5)
s_s05 = s_ev("s05", "1923年", "kanto")
a_s05 = a_ev("s05", "H3", 240, [(0, (-4.6, -3.8, 1.8), PL, 32), (2, (5.4, -3.0, 1.2), PH, 36), (4, (-2.0, -8.8, 2.4), FIG, 30),
                                (6, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], fall_beats=(), hand_beat=6)
s_s06 = s_ev("s06", "1945年", "war")
a_s06 = a_ev("s06", "H4", 240, [(0, (-5.0, -3.2, 1.2), PL, 34), (2, (5.0, -3.8, 1.8), PH, 34), (3, (1.8, -8.4, 2.2), FIG, 30),
                                (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], fall_beats=(3,), hand_beat=5)
s_s07 = s_ev("s07", "2011年", "tohoku")
a_s07 = a_ev("s07", "H5", 240, [(0, (-4.8, -3.6, 1.6), PL, 34), (2, (5.2, -3.4, 1.4), PH, 34), (3, (0, -9.2, 3.2), FIG, 30),
                                (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], fall_beats=(), hand_beat=5)


def s_s08():
    base_set()


def a_s08(u, t, f):
    set_people(t, []); set_hands(EV["H5"]["sec"]); S["mark"].location.z = -50
    go("s08", [(0, (0, CLK.y - 2.6, TOP[2]), TOP, 48), (1, (0, -12.5, 4.2), (0, .5, 1.6), 26)], t, 5.0, mv=.38)


def s_s09():
    base_set(); S["pl"] = plaque("s09_pl", "2070年（推計）", (-3.5, .3, 0), .3, .28)


def a_s09(u, t, f):
    drop(S["pl"], (-3.5, .3, 0), t, lbeat("s09", 2), h=2.5, rz=.28)
    plan_ = [(lbeat("s09", 3 + j), j * 4, min(31, (j + 1) * 4)) for j in range(8)]      # 4 体ずつ、拍ごとに静かに倒れる
    set_people(t, plan_); set_hands(EV["H5"]["sec"]); S["mark"].location.z = -50
    go("s09", [(0, (-5.6, -9.0, 1.4), FIG, 30), (2, (-4.6, -3.0, 1.2), (-3.0, -.5, .4), 34), (4, (0, -10.0, 5.4), (0, -3.4, 0), 28),
               (7, (4.2, -6.6, 1.0), (.4, -3.6, .3), 32), (9, (0, -9.4, 2.6), FIG, 30), (10, *W0)], t, 3.5)


def s_s10():
    base_set()


def a_s10(u, t, f):
    set_people(t, [(-9, 0, 31)]); set_hands(hand_move(t, EV["H5"]["sec"], EV["P1"]["sec"], lbeat("s10", 1)))
    S["mark"].location.z = CLK.z + RAD * 1.08 * math.cos(math.radians(-3.14)) if t > lbeat("s10", 2) else -50
    go("s10", [(0, (0, CLK.y - 5.0, CLK.z + .5), (0, CLK.y, CLK.z + .4), 36), (1, (0, CLK.y - 2.0, TOP[2] + .2), TOP, 58), (2, (.5, CLK.y - 1.7, TOP[2] + .5), (0, CLK.y, CLK.z + RAD * .95), 62),
               (4, (-1.4, CLK.y - 4.6, CLK.z + .6), (0, CLK.y, CLK.z + .4), 40)], t, 3.0, mv=.34, kick=.12)


def s_s11():
    base_set(); S["pl"] = plaque("s11_pl", "2120年（参考推計）", (-3.5, .3, 0), .27, .28)


def a_s11(u, t, f):
    drop(S["pl"], (-3.5, .3, 0), t, lbeat("s11", 0), h=2.5, rz=.28)
    set_people(t, [(-9, 0, 31), (lbeat("s11", 1), 31, 61)]); S["mark"].location.z = -50
    set_hands(hand_move(t, EV["P1"]["sec"], EV["P2"]["sec"], lbeat("s11", 3)))
    go("s11", [(0, (0, -9.0, 2.0), FIG, 30), (1, (-3.2, -7.4, 3.6), (0, -3.4, 0), 30), (3, (0, CLK.y - 2.0, TOP[2] + .2), TOP, 56)], t, 3.0)


def s_s12():
    base_set()


def a_s12(u, t, f):
    set_people(t, [(-9, 0, 61)]); S["mark"].location.z = -50
    k = max(0, int((t - lbeat("s12", 0)) / BP)) if t > lbeat("s12", 0) else 0     # 拍ごとに、ほんの少しずつ進む
    sec = EV["P2"]["sec"] - .9 * k; set_hands(hand_move(t, sec + .9, sec, lbeat("s12", k), .1) if k else EV["P2"]["sec"])
    go("s12", [(0, (0, -11.5, 3.0), (0, .5, 1.8), 28), (2, (2.4, -7.6, 1.2), (0, -1.0, 1.4), 32), (4, (0, CLK.y - 2.0, TOP[2] + .2), TOP, 50)], t, 4.0)


# ---------------------------------------------------------------- 書き出し
SHOTS = {k: (globals()["s_" + k], (lambda a: (lambda u, t, f: a(u, t, f)))(globals()["a_" + k])) for k in NAMES}

if os.environ.get("AT"):
    ats = [float(x) for x in os.environ["AT"].split(",")]; out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
    sc.render.resolution_percentage = int(os.environ.get("PCT", "40"))
    for name in O["shots"]:
        setup_fn, anim = SHOTS[name]; setup_fn()
        for at in ats:
            anim(0, at, int(at * K.FPS)); sc.render.filepath = os.path.join(out, f"{name}_{at:g}.png")
            t0 = time.time(); bpy.ops.render.render(write_still=True); print("TEST", name, at, round(time.time() - t0, 1), "s", flush=True)
else:
    K.render_shots(HERE, SHOTS, NAMES, O, ANIM)
