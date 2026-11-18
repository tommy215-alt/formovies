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


# ---------------------------------------------------------------- 場面ごとの舞台（v5、2026-11-18 ユーザーの指示「ずっと同じ部屋は違和感。場面に応じて背景・舞台を変える」）
# 時計と 100 体の人形は同じ位置のまま、床・壁・光・小物を時代と出来事に合わせて替える。カメラの位置は v4 のまま。
# (床の質感, 床の一枚の大きさ m, 色, 壁の質感, 壁の一枚 m, 色, HDRI, 強さ, 回転, (key の強さ, 色), (rim の強さ, 色))
STAGES = {
    "nara":   ("japanese_cedar_planks", 2.4, (.72, .56, .44), "clay_plaster", 3.0, (.92, .8, .64), "brown_photostudio_02_2k.hdr", .5, .8, (1300, (1, .74, .5)), (900, (1, .6, .35))),
    "famine": ("mud_cracked_dry_03", 3.0, (.95, .86, .72), "brown_planks_07", 2.4, (.72, .64, .56), "kloofendal_overcast_2k.hdr", 1.1, 0.0, (850, (.86, .89, .96)), (380, (.9, .92, 1))),
    "kanto":  ("rubble", 3.0, (.9, .85, .8), "brick_wall_001", 2.2, (.95, .85, .8), "industrial_sunset_2k.hdr", .9, 2.2, (1400, (1, .6, .36)), (1100, (1, .46, .22))),
    "war":    ("burned_ground_01", 3.0, (.62, .56, .5), "cracked_concrete_wall", 3.0, (.46, .43, .4), "approaching_storm_2k.hdr", .55, 1.0, (800, (1, .52, .3)), (1300, (1, .36, .16))),
    "tohoku": ("damp_beach_sand", 3.0, (.85, .85, .85), "precast_concrete_wall", 3.0, (.8, .84, .88), "misty_dawn_2k.hdr", 1.1, 0.0, (1000, (.76, .86, 1)), (600, (.7, .85, 1))),
    "city":   ("concrete_tiles_02", 2.0, (.9, .9, .9), "concrete_tile_facade", 4.0, (.85, .85, .88), "urban_street_01_2k.hdr", 1.0, 1.5, (1300, (1, .97, .92)), (600, (.85, .9, 1))),
    "eve":    ("concrete_tiles_02", 2.0, (.8, .8, .82), "concrete_tile_facade", 4.0, (.7, .7, .75), "modern_evening_street_2k.hdr", 1.0, 1.5, (950, (1, .7, .46)), (900, (.5, .6, 1))),
    "future": ("floor_tiles_06", 2.0, (.9, .92, .95), "plastered_wall", 4.0, (.88, .9, .94), "studio_small_08_2k.hdr", 1.0, 0.0, (1150, (.9, .95, 1)), (420, (.9, .95, 1))),
}
STAGE_OF = {"s00": "room", "s01": "room", "s02": "nara", "s03": "nara", "s04": "famine", "s05": "kanto", "s06": "war", "s07": "tohoku",
            "s08": "city", "s09": "eve", "s10": "eve", "s11": "future", "s12": "room"}
CUR = ["s00"]
WALLH = {"famine": 5.6, "kanto": 6.5, "war": 5.6, "tohoku": 5.8}


def lights(key, rim, hdri="brown_photostudio_02_2k.hdr", strength=.9, rot=.8, bg=0):
    w = world(hdri, strength, rot, bg)
    if bg:                                                                 # 空を見せる：カメラの光線でも HDRI を使う
        for lk in list(w.node_tree.links):
            if lk.to_node.bl_idname == "ShaderNodeMixShader" and lk.to_socket == lk.to_node.inputs[0]:
                w.node_tree.links.remove(lk)
    KEY.data.energy, KEY.data.color = key; RIM.data.energy, RIM.data.color = rim


def glow_mat(name, col, k):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = k
    return m


def stage(kind):
    if kind == "room":
        room(); lights((1500, (1, .9, .78)), (700, (1, .78, .55))); return
    ft, fs, fc, wt, ws, wc, hdri, st, rot, key, rim = STAGES[kind]
    clear_scene()
    wh = WALLH.get(kind, 16); sky = kind in WALLH                          # 外の舞台は塀・堤防を低くして、空（HDRI）を見せる
    plane("floor", 300 if sky else 40, 300 if sky else 40, (0, 0, 0), pbr_mat("fl_" + kind, ft, 1 / fs, fc, 1.1, box_proj=True))
    plane("wall", 40, wh, (0, 3.6, wh / 2), pbr_mat("wl_" + kind, wt, 1 / ws, wc, 1.0, box_proj=True), rot=(math.pi / 2, 0, 0))
    lights(key, rim, hdri, st, rot, 1 if sky else 0); R = random.Random(kind)
    dk = pbr_mat("post", "dark_wood", 1.0, (.5, .42, .36), 1.2, box_proj=True)
    if kind == "nara":                                                     # 奈良の寺：朱の柱と梁
        red = plain("shu", (.5, .07, .035), .45, coat=.5)
        for x in (-4.9, 4.9, -9.5, 9.5):
            cyl("pillar%g" % x, .3, 10, (x, 3.1, 5), red, 48)
        box("nbeam", (40, .4, .45), (0, 3.25, 5.7), red, bevel=.02); box("nsill", (40, .3, .22), (0, 3.4, .11), wood(), bevel=.01)
    elif kind == "famine":                                                 # 飢饉：板塀の柱、枯れた稲
        for i in range(-9, 10, 2):
            box("post%d" % i, (.16, .16, 5.6), (i * 1.0, 3.45, 2.8), dk, bevel=.01)
        straw = plain("straw", (.42, .33, .18), .8)
        for i in range(24):
            x = R.choice((-1, 1)) * R.uniform(3.6, 7.5); y = R.uniform(-7, 2.5)
            o = cyl("stalk%d" % i, .012, R.uniform(.5, 1.0), (x, y, .3), straw, 6); o.rotation_euler = (R.uniform(-.5, .5), R.uniform(-.5, .5), 0)
    elif kind == "kanto":                                                  # 大正の街：崩れたれんが・倒れた柱
        brick = pbr_mat("brk", "brick_wall_001", 1 / 2.2, (.95, .8, .75), 1.0, box_proj=True)
        for i in range(40):
            x = R.choice((-1, 1)) * R.uniform(3.4, 7.5); y = R.uniform(-7.5, 3.0)
            o = box("brick%d" % i, (.24, .12, .07), (x, y, .035 + .07 * (i % 3 == 0)), brick, bevel=.006); o.rotation_euler = (0, 0, R.uniform(0, 3.2))
        for i, (x, ry) in enumerate(((-6.2, .5), (6.6, -.6))):
            o = box("kbeam%d" % i, (.22, .22, 5.0), (x, 2.4, 1.6), dk); o.rotation_euler = (0, ry, .2)
    elif kind == "war":                                                    # 戦争：焦げた梁
        coal = plain("coal", (.03, .025, .02), .9)
        for i, (x, y, ry, rz) in enumerate(((-5.4, 2.2, .6, .3), (-6.8, -1.5, 1.45, .8), (5.6, 2.4, -.5, -.2), (6.9, -2.5, 1.5, -1.1), (-4.2, -6.5, 1.52, .3), (4.6, -7.0, 1.5, 2.0))):
            o = box("char%d" % i, (.26, .26, 4.2), (x, y, 1.6 if abs(ry) < 1 else .13), coal, bevel=.03); o.rotation_euler = (0, ry, rz)
    elif kind == "tohoku":                                                 # 海辺：浅い水と流れてきた板
        w = bpy.data.materials.get("water")
        if w is None:
            w = bpy.data.materials.new("water"); w.use_nodes = True; nt = w.node_tree; b = nt.nodes["Principled BSDF"]
            b.inputs["Base Color"].default_value = (.55, .7, .75, 1); b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = .04; b.inputs["IOR"].default_value = 1.33
            nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = .12
            nt.links.new(nz.outputs["Fac"], bp.inputs["Height"]); nt.links.new(bp.outputs["Normal"], b.inputs["Normal"])
        wt_o = plane("water", 40, 40, (0, 0, .07), w); wt_o.visible_shadow = False      # 下の砂に光を通す（屈折の光は計算しないため）
        pk = pbr_mat("plank_w", "wood_table_001", 1.0, (.6, .52, .45), 1.3, box_proj=True)
        for i in range(7):
            x = R.choice((-1, 1)) * R.uniform(3.6, 7.5); o = box("drift%d" % i, (R.uniform(.9, 2.0), .22, .05), (x, R.uniform(-7, 2.5), .08), pk, bevel=.01); o.rotation_euler = (0, 0, R.uniform(0, 3.2))
    elif kind in ("city", "eve"):                                          # いまの街：ビルの窓（夕方は明かりがつく）
        lit_m = glow_mat("winglow", (1, .72, .45), 2.2); dark = plain("wing", (.05, .06, .07), .1, metal=.3, coat=.8)
        for i, x in enumerate((-8.5, -6.5, 6.5, 8.5)):
            for j in range(4):
                lit = kind == "eve" and (i + j) % 3 != 1
                box("win%d_%d" % (i, j), (1.3, .05, .9), (x, 3.57, 1.0 + j * 1.5), lit_m if lit else dark, bevel=0)


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
    stage(STAGE_OF[CUR[0]]); ANIM[:] = [cam.o]; clock(); people()


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


# ================================================================ v5：出来事を描く（2026-11-18 ユーザーの指示）
# 「背景を変えるだけでなく、飢饉なら飢えて倒れる人、震災なら押し寄せる水など、その時の出来事を描写して場面を転換する」。
# 出来事の場面では 100 体の並びをやめ、その出来事の小さな模型（ジオラマ）を作る。時計は舞台の奥の壁・塀・堤防に掛けて、最後の拍で寄る。
# 注意：blkit は location と rotation だけを毎コマ記録する（大きさ・質感の変化は写らない）。消す・出すは位置で行う。
def lamp(name, loc, energy, col, r=.4):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = col; d.shadow_soft_size = r
    o = bpy.data.objects.new(name, d); o.location = loc; return link(o)


def house(name, loc, w, d, h, wm, rm, rz=0.0, win=None, a=.55):
    """切妻屋根の小さな家（人形の大きさに合わせた模型）。win：窓の質感（正面＝−y の面に 2 つ）"""
    root = empty(name, loc); root.rotation_euler = (0, 0, rz)
    parent(box(name + "_w", (w, d, h), (0, 0, h / 2), wm, bevel=.01), root)
    sw = d / 2 / math.cos(a) * 1.18
    for sg in (-1, 1):
        r = box(name + "_r%d" % sg, (w * 1.14, sw, .045), (0, sg * d / 4, h + d / 4 * math.tan(a)), rm, bevel=.004); r.rotation_euler = (-sg * a, 0, 0); parent(r, root)
    if win is not None:
        for sx in (-.25, .25):
            parent(box(name + "_win%g" % sx, (w * .2, .02, h * .32), (sx * w, -d / 2 - .006, h * .55), win, bevel=0), root)
    return root


def crowd_pts(n, x0, x1, y0, y1, seed, gap=.42):
    R = random.Random(seed); pts = []
    while len(pts) < n:
        p = (R.uniform(x0, x1), R.uniform(y0, y1))
        if all((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2 > gap * gap for q in pts):
            pts.append(p)
    return pts


def topple(f, t, t0, sgn=1, dur=.28, kneel=False):
    """拍の頭 t0 で倒れる（kneel：膝をついてから前へ。飢え）"""
    rz = f.rotation_euler[2]
    if t0 is None or t < t0 - (dur if kneel else 0):
        f.rotation_euler = (0, 0, rz); return
    if kneel:
        u = clamp((t - (t0 - dur)) / dur); f.location.z = f["z0"] - .12 * ease(u) if t < t0 else f["z0"] - .12
        if t < t0:
            f.rotation_euler = (sgn * .25 * ease(u), 0, rz); return
    v = t - t0; u = v / dur
    ang = (math.pi / 2) * clamp(u) ** 2 if u < 1 else math.pi / 2 - .06 * math.exp(-8 * (v - dur)) * abs(math.sin(18 * (v - dur)))
    f.rotation_euler = (sgn * max(ang, .25 if kneel else 0), 0, rz)


def mk_crowd(pfx, pts, s=.46, m=None):
    out = []
    for i, (x, y) in enumerate(pts):
        f = figure(f"{pfx}{i}", (x, y, 0), s, m); f.rotation_euler = (0, 0, random.Random(i + 7).uniform(-.4, .4)); f["z0"] = 0.0
        out.append(f); ANIM.append(f)
    return out


def ev_base(name, year, key):
    """出来事の場面の共通：舞台・時計・年の札・写真の額（人形の並びは作らない）"""
    stage(STAGE_OF[CUR[0]]); ANIM[:] = [cam.o]; clock(); S["ppl"] = []
    S["pl"] = plaque(name + "_pl", year, (-3.5, .3, 0), .34, .3)
    S["ph"] = photo_frame(name + "_ph", key, (3.5, .4, 0)) if key else None


def ev_anim(name, t, frm, k_ev, hand_beat, photo_beat=2):
    drop(S["pl"], (-3.5, .3, 0), t, lbeat(name, 0), h=2.5, rz=.3)
    if S["ph"] is not None:
        drop(S["ph"], (3.5, .4, 0), t, lbeat(name, photo_beat), h=2.5, rz=-.3)
    S["mark"].location.z = -50
    set_hands(hand_move(t, frm, EV[k_ev]["sec"], lbeat(name, hand_beat)) if hand_beat is not None else frm)


# ---------------------------------------------------------------- 737 年：天然痘（赤黒いもやが村に広がり、3 割が倒れる）
def s_s02():
    ev_base("s02", "737年", None)
    straw = plain("mat_straw", (.5, .4, .22), .9); roofm = plain("kaya", (.36, .28, .16), .9); wallm = pbr_mat("clayw", "clay_plaster", 1.2, (.9, .8, .64), 1.0, box_proj=True)
    for i, (x, y, rz) in enumerate(((-5.2, -1.2, .2), (5.3, -1.6, -.25), (-5.6, -5.8, .1), (5.6, -6.2, -.1))):
        house("nh%d" % i, (x, y, 0), 1.6, 1.1, .75, wallm, roofm, rz)
    pts = crowd_pts(70, -3.3, 3.3, -7.2, -.7, 737); S["crowd"] = mk_crowd("c", pts)
    S["dist"] = sorted(range(len(pts)), key=lambda i: math.hypot(pts[i][0], pts[i][1] + 3.6))
    S["rmax"] = math.hypot(pts[S["dist"][20]][0], pts[S["dist"][20]][1] + 3.6)
    for i, (x, y) in enumerate(((-4.1, -3.0), (4.1, -3.4), (-4.2, -4.4))):         # 寝込む人：むしろの上に横たわる
        box("mat%d" % i, (.4, .8, .03), (x, y, .015), straw, bevel=.004)
        f = figure("sick%d" % i, (x, y + .25, .17), .42); f.rotation_euler = (math.pi / 2, 0, 0)
    # 広がるもや：浅い円すいを床の下から上げると、床の上に出る円が大きくなる
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=96, radius1=7.5, radius2=0.0, depth=.6)
    mm = bpy.data.materials.get("miasma")
    if mm is None:
        mm = bpy.data.materials.new("miasma"); mm.use_nodes = True; nt = mm.node_tree; b = nt.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (.3, .03, .05, 1); b.inputs["Emission Color"].default_value = (.5, .04, .06, 1); b.inputs["Emission Strength"].default_value = .6
        b.inputs["Alpha"].default_value = .55; b.inputs["Roughness"].default_value = .9
    o = bpy.data.objects.new("miasma", mesh_from_bm("miasma", bm, [mm])); link(o); o.visible_shadow = False; S["mia"] = o; ANIM.append(o)


def a_s02(u, t, f):
    ev_anim("s02", t, 240, "H1", None)
    t1 = lbeat("s02", 1); n = 21                                           # 70 人の 3 割
    rmax = S["rmax"]; k = clamp((t - t1) / (3 * BP)); rad = rmax * ease(k) + .25 * ease(k)
    S["mia"].location = (0, -3.6, rad / 7.5 * .6 - .3)                    # 円すいの先の高さ ∝ 床の上に出る円の半径
    for j, i in enumerate(S["dist"]):
        fg = S["crowd"][i]; t0 = None
        if j < n:
            d = math.hypot(fg.location.x, fg.location.y + 3.6); t0 = lbeat("s02", 1 + max(1, min(3, math.ceil(3 * d / rmax - 1e-6))))   # もやが届いた拍の頭で倒れる
        topple(fg, t, t0, fall_dir(i))
    go("s02", [(0, (-5.2, -3.6, 1.6), PL, 34), (1, (0, -9.8, 5.2), (0, -3.6, 0), 30), (3, (-1.6, -6.4, .7), (.2, -3.0, .3), 32),
               (5, (2.6, -8.0, 2.4), (0, -3.4, .2), 30)], t, 3.0)


# ---------------------------------------------------------------- 天明の飢饉（干上がった田、枯れた稲、歩く人が膝をつき倒れる）
def s_s04():
    ev_base("s04", "1780年代", "tenmei")
    R = random.Random(1783); straw = plain("deadrice", (.45, .36, .2), .85)
    for i in range(160):                                                    # 枯れた稲の株
        x = R.uniform(-7, 7); y = R.uniform(-8.5, 2.6)
        if abs(y + 3.6) < .9 and abs(x) < 6:
            continue
        for j in range(3):
            o = cyl("st%d_%d" % (i, j), .008, R.uniform(.25, .5), (x + R.uniform(-.04, .04), y + R.uniform(-.04, .04), .15), straw, 5)
            o.rotation_euler = (R.uniform(-.7, .7), R.uniform(-.7, .7), 0)
    bowl = plain("bowl", (.12, .07, .05), .35, coat=.6)
    for i, (x, y) in enumerate(((-1.2, -5.2), (.6, -5.6), (1.9, -4.9), (-2.3, -2.3))):   # 空の茶わん
        cyl("bowl%d" % i, .07, .05, (x, y, .025), bowl, 32)
    roofm = plain("kaya", (.36, .28, .16), .9); wallm = pbr_mat("post", "dark_wood", 1.0, (.5, .42, .36), 1.2, box_proj=True)
    house("fh0", (-6.4, -2.4, 0), 1.8, 1.2, .8, wallm, roofm, .15); house("fh1", (5.5, -1.0, 0), 1.6, 1.1, .75, wallm, roofm, -.2)
    # 歩く人（右から左へ、ゆっくり）。3 人が拍 2・3・4 で膝をついて倒れる（死者 90 万人以上＝人口の約 3%）
    S["walk"] = mk_crowd("w", [(-3.0 + i * .6, -3.6 + (.18 if i % 2 else -.18)) for i in range(14)])
    S["sit"] = mk_crowd("sit", [(-4.3, -2.2), (-4.0, -2.8), (4.4, -2.9)])
    for f_ in S["sit"]:
        f_.location.z = -.12; f_["z0"] = -.12; f_.rotation_euler = (.35, 0, f_.rotation_euler[2])


def a_s04(u, t, f):
    ev_anim("s04", t, 240, "H2", 5)
    falls = {4: lbeat("s04", 2), 7: lbeat("s04", 3), 10: lbeat("s04", 4)}
    for i, w in enumerate(S["walk"]):
        x0 = -3.0 + i * .6; t0 = falls.get(i)
        tw = t if t0 is None else min(t, t0 - .28)                         # 倒れたら止まる
        w.location.x = x0 - .32 * tw; w.location.z = .015 * abs(math.sin(tw * 5.5 + i)); w["z0"] = w.location.z
        topple(w, t, t0, -1, kneel=True)
        w.rotation_euler = (w.rotation_euler[0], w.rotation_euler[1], math.pi / 2 + .05 * math.sin(i))
    go("s04", [(0, (-5.0, -3.4, 1.4), PL, 34), (2, (5.2, -3.6, 1.6), PH, 34), (3, (-.6, -6.6, .6), (.4, -3.6, .3), 46), (4, (0, -8.6, 3.0), (0, -3.4, .2), 30),
               (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48), (7, *W0)], t, 3.0)


# ---------------------------------------------------------------- 関東大震災（れんがの街が揺れ、上の階が崩れ落ちる。人は通りの中央へ逃げる）
def s_s05():
    ev_base("s05", "1923年", "kanto")
    brick = pbr_mat("brk", "brick_wall_001", 1 / 2.2, (.95, .8, .75), 1.0, box_proj=True); dark = plain("bwin", (.04, .035, .03), .3)
    S["bld"] = []
    for i, (x, y) in enumerate(((-5.2, -2.6), (-5.2, -5.0), (-5.2, -7.4), (5.4, -2.8), (5.4, -5.2), (5.4, -7.6))):
        sg = -1 if x < 0 else 1
        root = empty("b%d" % i, (x, y, 0)); low = parent(box("b%d_l" % i, (1.4, 2.0, 1.2), (0, 0, .6), brick, bevel=.01), root)
        for zz in (.35, .85):
            for yy in (-.5, .5):
                parent(box("b%d_w%g%g" % (i, zz, yy), (.02, .3, .26), (-sg * .705, yy, zz), dark, bevel=0), root)
        top = empty("b%d_tp" % i, (x, y, 1.2)); parent(box("b%d_u" % i, (1.4, 2.0, .9), (0, 0, .45), brick, bevel=.01), top)
        parent(box("b%d_uw" % i, (.02, .3, .26), (-sg * .705, 0, .45), dark, bevel=0), top)
        S["bld"].append((root, top, (x, y), sg)); ANIM.extend([root, top])
    R = random.Random(1923); S["bricks"] = []
    for i in range(24):                                                    # 落ちてくるれんが
        x = R.choice((-1, 1)) * R.uniform(3.8, 4.4); y = R.uniform(-7, 0)
        o = box("fb%d" % i, (.24, .12, .07), (x, y, -50), brick, bevel=.006); S["bricks"].append((o, (x, y, .035), R.uniform(0, 3), 2 + i % 4)); ANIM.append(o)
    lamp("fire1", (-6.5, -9, 1.2), 900, (1, .45, .15), 1.0); lamp("fire2", (6.8, 1.5, 1.5), 1100, (1, .45, .15), 1.0)
    S["crowd"] = mk_crowd("k", crowd_pts(18, -2.6, 2.6, -7.0, -.8, 1923))


def a_s05(u, t, f):
    ev_anim("s05", t, 240, "H3", 6)
    t1 = lbeat("s05", 1)
    sh = .05 * math.exp(-.9 * max(0, t - t1)) * math.sin(38 * (t - t1)) if t > t1 else 0.0       # 揺れ（拍 1 から）
    for j, (root, top, (x, y), sg) in enumerate(S["bld"]):
        root.rotation_euler = (0, sh * .4 * (1 + j % 2), 0)
        tc = lbeat("s05", 2 + j % 3)                                           # 上の階が倒れる拍
        k = 0 if t < tc else clamp((t - tc) / .42) ** 2                    # 通りの側へ傾いて、地面へ落ちる
        top.location = (x - sg * 1.2 * k, y, 1.2 - .95 * k); top.rotation_euler = (0, -sg * 1.1 * k + sh, 0)
    for o, base, rz, kb in S["bricks"]:
        drop(o, base, t, lbeat("s05", kb), h=1.6, dur=.3, rz=rz)
    for i, c in enumerate(S["crowd"]):                                     # 揺れのあと、通りの中央へ寄る
        x0 = c.get("x0", c.location.x); c["x0"] = x0; k = ease(clamp((t - t1) / 1.5)); c.location.x = x0 * (1 - .55 * k); c.location.z = .02 * abs(math.sin(t * 9 + i)) * k
    go("s05", [(0, (-4.6, -3.8, 1.8), PL, 32), (1, (0, -9.8, 2.2), (0, -3.4, .8), 28), (2, (2.2, -3.0, 1.3), PH, 36), (3, (-1.0, -9.6, .5), (-3.8, -5.0, 1.0), 26),
               (6, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], t, 3.0)
    if t > t1:
        cam.o.location.x += sh * .8; cam.o.location.z += sh * .5


# ---------------------------------------------------------------- 1945 年：焼けた街（焦げた家、火の粉、人が倒れる）
def s_s06():
    ev_base("s06", "1945年", "war")
    coal = plain("coal", (.03, .025, .02), .9); ember = glow_mat("ember", (1, .42, .1), 6.0); fire = glow_mat("fireglow", (1, .35, .08), 3.0)
    R = random.Random(1945)
    for i, (x, y) in enumerate(((-5.0, -.8), (-5.4, -3.2), (-5.0, -5.8), (5.2, -1.0), (5.0, -3.6), (5.4, -6.2))):
        root = empty("wh%d" % i, (x, y, 0)); root.rotation_euler = (0, 0, R.uniform(-.2, .2))
        for (px, py) in ((-.7, -.5), (.7, -.5), (-.7, .5), (.7, .5)):         # 焼け残った柱
            parent(box("wh%d_p%g%g" % (i, px, py), (.08, .08, R.uniform(.5, 1.1)), (px, py, .4), coal, bevel=.01), root)
        b = parent(box("wh%d_b" % i, (1.6, .08, .08), (0, -.5, .9), coal, bevel=.01), root); b.rotation_euler = (0, R.uniform(-.4, .4), 0)
        if i % 2 == 0:
            parent(box("wh%d_f" % i, (.9, .6, .12), (0, 0, .06), fire, bevel=.02), root); lamp("whl%d" % i, (x, y, .5), 260, (1, .45, .15), .6)
    S["emb"] = []
    for i in range(70):
        o = sphere("em%d" % i, .018, (0, 0, -50), ember, 8); S["emb"].append((o, R.uniform(-6.5, 6.5), R.uniform(-8, 2), R.uniform(0, 3), R.uniform(.35, .7))); ANIM.append(o)
    S["crowd"] = mk_crowd("x", crowd_pts(40, -3.0, 3.0, -7.2, -.8, 45))


def a_s06(u, t, f):
    ev_anim("s06", t, 240, "H4", 5)
    for o, x, y, ph, sp in S["emb"]:
        z = (ph + sp * t) % 3.0; o.location = (x + .2 * math.sin(t * 1.3 + ph * 4), y, z)
    tf = lbeat("s06", 3)
    for i, c in enumerate(S["crowd"]):
        topple(c, t, tf if i in (3, 11, 22, 30) else None, fall_dir(i))    # 約 310 万人＝人口の約 4%（40 人のうち 2 人では少ないので 4 人。目安の比喩）
    go("s06", [(0, (-5.0, -3.2, 1.2), PL, 34), (1, (0, -9.6, 1.4), (0, -3.4, .6), 28), (2, (5.0, -3.8, 1.8), PH, 34), (3, (1.8, -8.4, 2.2), (0, -3.6, .2), 30),
               (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], t, 3.0)


# ---------------------------------------------------------------- 2011 年：津波（右から水が押し寄せ、家が浮いて流される）
def s_s07():
    ev_base("s07", "2011年", "tohoku")
    wallm = plain("hwall", (.82, .8, .76), .6); roofm = plain("hroof", (.18, .22, .3), .45, coat=.4); S["hs"] = []
    for i, (x, y, rz) in enumerate(((-1.6, -2.2, .1), (1.4, -2.0, -.1), (-2.2, -5.2, .05), (.9, -5.6, .2), (2.8, -4.0, -.15), (-.3, -3.8, 0))):
        h = house("th%d" % i, (x, y, 0), .9, .7, .55, wallm, roofm, rz); S["hs"].append((h, x, y, rz)); ANIM.append(h)
    w = bpy.data.materials["water"]; wb = box("wave", (30, 5.4, 1.0), (60, -3.7, 0), w, bevel=.25); wb.visible_shadow = False; S["wave"] = wb; ANIM.append(wb)
    foam = plain("foam", (.92, .94, .95), .6); fm = cyl("foamc", .16, 5.4, (60, -3.7, .5), foam, 24); fm.rotation_euler = (math.pi / 2, 0, 0); S["foam"] = fm; ANIM.append(fm)
    S["crowd"] = mk_crowd("y", crowd_pts(10, -3.0, 3.0, -7.6, -6.4, 311))


def wave_x(t):
    t1, t4 = lbeat("s07", 1), lbeat("s07", 4)
    return 9.0 - 18.5 * ease(clamp((t - t1) / (t4 - t1)))


def a_s07(u, t, f):
    ev_anim("s07", t, 240, "H5", 5)
    X = wave_x(t); hgt = .62
    S["wave"].location = (X + 15, -3.7, hgt - .5); S["foam"].location = (X + .05, -3.7, hgt + .02); S["foam"].rotation_euler = (math.pi / 2, t * 3, 0)
    for h, x, y, rz in S["hs"]:
        if X < x + .5:                                                     # 水が来たら浮いて、左へ流される
            v = (x + .5 - X); h.location = (x - .55 * v, y + .15 * math.sin(v + x), .38 + .03 * math.sin(t * 4 + x)); h.rotation_euler = (.06 * math.sin(t * 3 + y), .05 * math.sin(t * 2.3 + x), rz + .45 * v)
        else:
            h.location = (x, y, 0); h.rotation_euler = (0, 0, rz)
    for i, c in enumerate(S["crowd"]):                                     # 手前の人は高い所（手前）へ逃げる
        if "y0" not in c:
            c["y0"] = c.location.y
        c.location.y = c["y0"] - .5 * ease(clamp((t - lbeat("s07", 1)) / 2))
    go("s07", [(0, (-4.8, -3.6, 1.6), PL, 34), (1, (0, -11.0, 3.6), (0, -3.6, .2), 28), (2, (5.2, -3.4, 1.4), PH, 34), (3, (-4.6, -7.6, 1.4), (0, -3.4, .3), 28),
               (5, (0, CLK.y - 2.6, TOP[2]), TOP, 48)], t, 3.0)


# ---------------------------------------------------------------- いま〜これから：街の家々（夕方は窓の明かりが、拍ごとに消えていく）
def town(kind):
    wallm = plain("cw_" + kind, (.86, .86, .86) if kind != "future" else (.93, .94, .96), .55); roofm = plain("cr_" + kind, (.3, .3, .34) if kind != "future" else (.85, .87, .9), .45)
    dark = plain("wdark", (.04, .045, .05), .2, coat=.6); lit = glow_mat("winglow", (1, .72, .45), 2.2); S["lit"] = []
    for i, (x, y, rz) in enumerate(((-5.0, -1.0, .1), (-5.2, -3.4, -.05), (-5.0, -5.8, .08), (5.0, -1.2, -.1), (5.2, -3.6, .06), (5.0, -6.0, -.08),
                                    (-6.9, -2.2, 0), (6.9, -4.6, 0))):
        h = house("ch%d" % i, (x, y, 0), 1.2, .9, .8, wallm, roofm, rz + (math.pi / 2 if x < 0 else -math.pi / 2), win=dark)
        if kind == "eve":
            for sx in (-.25, .25):
                o = parent(box("chl%d%g" % (i, sx), (1.2 * .2, .02, .8 * .32), (sx * 1.2, -.9 / 2 - .012, .8 * .55), lit, bevel=0), h); S["lit"].append(o); ANIM.append(o)


def s_s08():
    base_set(); town("city")


def s_s09():
    base_set(); town("eve"); S["pl"] = plaque("s09_pl", "2070年（推計）", (-3.5, .3, 0), .3, .28)


_a_s09_v4 = a_s09


def a_s09(u, t, f):
    _a_s09_v4(u, t, f)
    for j, o in enumerate(S["lit"]):                                       # 明かりが拍ごとに消える（16 のうち 5 つ）
        off = j in (2, 5, 9, 12, 14) and t >= lbeat("s09", 3 + (j % 5) * 1)
        o.location.y = -.9 / 2 - .012 + (.05 if off else 0)


def s_s10():
    base_set(); town("eve")
    for j, o in enumerate(S["lit"]):
        if j in (2, 5, 9, 12, 14):
            o.location.y += .05


def s_s11():
    base_set(); town("future"); S["pl"] = plaque("s11_pl", "2120年（参考推計）", (-3.5, .3, 0), .27, .28)


# ---------------------------------------------------------------- 書き出し
def _setup(k):
    def f():
        CUR[0] = k; globals()["s_" + k]()
    return f


SHOTS = {k: (_setup(k), (lambda a: (lambda u, t, f: a(u, t, f)))(globals()["a_" + k])) for k in NAMES}

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
