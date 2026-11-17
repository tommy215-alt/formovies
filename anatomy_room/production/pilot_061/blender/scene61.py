"""pilot_061 v2「もしも世界中のお金が、いま金に変わったら」の 3D（Blender Cycles）。ショット＝セリフの行（s00〜s10）。
blender -b -P blender/scene61.py -- [s00 s01 …] [--resume] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に
数字は scripts/pilot_061/sim/gold.json の broad（assets/plan.js）。金は物理的な金属、光は Poly Haven の HDRI（CC0）。
動き（落ちる・置かれる・傾く）は BGM の拍の頭（assets/bgm/beats.json）。閃光なし。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib61 import *  # noqa: F401,F403

O = K.args()
NAMES = [l["scene"] for l in PLAN["lines"]]
TL = json.load(open(os.path.join(HERE, "..", "work", "timeline.json"), encoding="utf-8")); CUE = TL["cues"]
RG = {r["name"]: r for r in PLAN["regions"]}
sc = setup(samples=O["samples"] if "--samples" in sys.argv else 48)
world(strength=1.1, rot=.8)
KEY = area_light("key", (-4, -5, 8), (0, 0, 1), 5, 1400); RIM = area_light("rim", (5, 6, 4), (0, 0, 1), 4, 700, (1, .78, .55))
cam = K.Cam(); ANIM = [cam.o]


def lbeat(name, k):
    """ショットの頭から数えて k 番目の拍（ショットの中の秒）"""
    c = CUE[name]; return (math.ceil(c / BP - 1e-6) + k) * BP - c


def look(P, A, lens=40, fstop=2.8, roll=0.0):
    P, A = Vector(P), Vector(A); cam.look(P, A, lens, roll); cam_dof(cam, (P - A).length, fstop)


def vlerp(a, b, u):
    return [lerp(x, y, u) for x, y in zip(a, b)]


def path(keys, t):
    """keys：[(秒, 位置, 注視点, 焦点距離), ...] を滑らかにつなぐ"""
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, p0, a0, l0), (t1, p1, a1, l1) in zip(keys, keys[1:]):
        if t <= t1:
            u = ease((t - t0) / (t1 - t0)); return vlerp(p0, p1, u), vlerp(a0, a1, u), lerp(l0, l1, u)
    return keys[-1][1:]


def drop(o, base, t, t0, h=3.0, dur=.32, spin=0.0, rz=0.0):
    """t0 に上から落ちて base に着く（重力のように加速 → 小さく弾む）。t0 より前は見えない（下に隠す）"""
    u = (t - t0) / dur
    if u < 0:
        o.location = (base[0], base[1], -50); return
    if u < 1:
        z = base[2] + h * (1 - u * u)
    else:
        v = (t - t0 - dur); z = base[2] + .05 * h * math.exp(-9 * v) * abs(math.sin(16 * v))
    o.location = (base[0], base[1], z); o.rotation_euler = (0, 0, rz + spin * (1 - clamp(u)))


def wood():
    return pbr_mat("plankw", "wood_table_001", 1.2, (.75, .6, .48), 1.3, box_proj=True)


def label(name, s, loc, size=.28, face_rot=0.0, gold_text=True):
    """木の札に金の文字（立てて置く）"""
    root = empty(name, loc); root.rotation_euler = (0, 0, face_rot)
    w = len(s) * size * .78 + size * .9; h = size * 1.55
    parent(box(name + "_b", (w, .09, h), (0, 0, h / 2), wood(), bevel=.02), root)
    parent(text_obj(name + "_t", s, (0, -.05, h / 2), size, gold_mat("goldtext", .22) if gold_text else plain("ink", (.05, .04, .03), .5), extrude=.012, font="BIZUDPGothic-Bold.ttf"), root)
    return root


def backdrop():
    """奥の壁（暗い暖色のしっくい、ぼける）と、壁の前の柔らかい暖かい光の玉（ボケ）"""
    wall = plane("wall", 80, 30, (0, 22, 10), pbr_mat("wallm", "brushed_concrete", 4.0, (.42, .3, .22), 1.0), rot=(math.pi / 2, 0, 0))
    em = bpy.data.materials.get("bokeh") or bpy.data.materials.new("bokeh")
    em.use_nodes = True; b = em.node_tree.nodes["Principled BSDF"]; b.inputs["Emission Color"].default_value = (1, .62, .28, 1); b.inputs["Emission Strength"].default_value = 1.2; b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    import random
    r = random.Random(61)
    for i in range(0):
        sphere(f"bk{i}", .5 + r.random() * .4, (r.uniform(-16, 16), r.uniform(19, 21), r.uniform(4, 10)), em, 24)


def base_set(desk_scale=6.0):
    clear_scene(); desk(size=60, scale=desk_scale * 1.5); backdrop()


# ---------------------------------------------------------------- 世界地図の上の金の山（1 本＝1 万トン）
MAPW = 12.0
UNIT_T = 10000
PS = .42                                    # 地図の上の延べ棒の大きさ
ORDER = sorted(PLAN["regions"], key=lambda r: -r["tonnes"])


def map_piles(name, appear=True):
    """地図と山を作る。戻り値：[(region, [(obj, base, rz), ...]), ...]"""
    m, w, h = map_sheet(MAPW, (0, 0, .008)); piles = []
    edge = box("mapedge", (MAPW + .16, h + .16, .006), (0, 0, .003), plain("mapback", (.25, .18, .1), .7), bevel=0)
    for r in ORDER:
        n = max(1, round(r["tonnes"] / UNIT_T)); x, y = map_xy(r["lon"], r["lat"], MAPW, h); bars = []
        for i, (bx, by, bz, rz) in enumerate(pile_slots(n)):
            o = bar(f"{name}_{r['name']}_{i}", (x + bx * PS, y + by * PS, .006 + bz * PS), rz, PS); bars.append((o, (x + bx * PS, y + by * PS, .006 + bz * PS), rz)); ANIM.append(o)
        piles.append((r, bars))
    return piles, h


def piles_anim(piles, t, t0, per_pile, per_bar=.035):
    for k, (r, bars) in enumerate(piles):
        tp = t0 + k * per_pile
        for i, (o, base, rz) in enumerate(bars):
            drop(o, base, t, tp + i * per_bar, h=1.6, dur=.28, rz=rz)


def tonnes_label(r):
    v = r["tonnes"] / 10000; return (f"{v:.0f}万t" if v >= 10 else f"{v:.1f}万t".replace(".0", ""))


# ---------------------------------------------------------------- s00：お札・カード・スマホが、拍ごとに金の延べ棒へ
S = {}


def s_s00():
    base_set(); ANIM[:] = [cam.o]; items = []
    spots = [(-1.1, 1.9, "usd", .25), (.9, 2.2, "jpy", -.2), (-1.0, .5, "eur", .1), (1.0, .7, "card", -.3), (-1.2, -1.0, "phone", .2), (.9, -.8, "gbp", -.15), (-.9, -2.5, "card2", .35), (1.0, -2.4, "usd", -.1)]
    for i, (x, y, k, rz) in enumerate(spots):
        if k.startswith("card"):
            it = card(f"it{i}", (x, y, 0), (0, 0, rz), 1.5)
        elif k == "phone":
            it = phone(f"it{i}", (x, y, 0), (0, 0, rz), 1.25)
        else:
            it = note_stack(f"it{i}", k, (x, y, 0), rz, 1.05)
        b = bar(f"gb{i}", (x, y, -50), rz, 1.05); items.append((it, b, (x, y, 0), rz)); ANIM.extend([it, b])
    S["s00"] = items


def a_s00(u, t, f):
    for i, (it, b, base, rz) in enumerate(S["s00"]):
        t0 = lbeat("s00", 1) + i * BP * .5
        k = clamp((t - t0) / .22)                       # 元の物は沈んで消える
        it.location = (base[0], base[1], -.6 * k * k if k < 1 else -50); it.rotation_euler = (0, 0, rz + .4 * k)
        drop(b, (base[0], base[1], 0), t, t0 + .12, h=2.4, dur=.3, spin=.6, rz=rz)
    P, A, L = path([(0, (0, -3.0, 6.2), (0, -.2, 0), 34), (3.6, (0, -2.6, 5.3), (0, -.1, .2), 36)], t); look(P, A, L, 4.0)


# ---------------------------------------------------------------- s01：地図の上に山 → 人類の金（立方体）と、足りない分
def s_s01():
    base_set(); ANIM[:] = [cam.o]; piles, h = map_piles("m1"); S["s01"] = piles
    # 人類が掘った金：1 つの金の立方体。お金を金にすると 4.8 倍：ガラスの立方体 4 つと 0.8 個
    side = 1.1; gx = -.7; gy = -5.6; S["cube"] = box("allgold", (side, side, side), (gx, gy, side / 2), gold_mat(), bevel=.02); ANIM.append(S["cube"])
    glass = bpy.data.materials.get("glass61") or bpy.data.materials.new("glass61"); glass.use_nodes = True; b = glass.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["Roughness"].default_value = .06; b.inputs["Base Color"].default_value = (1, .86, .6, 1); b.inputs["IOR"].default_value = 1.45
    need = PLAN["total_t"] / PLAN["all_gold_t"]; S["ghost"] = []
    for i in range(math.ceil(need)):
        fr = min(1.0, need - i); o = box(f"ghost{i}", (side, side, side * fr), (gx + side * 1.35, gy, i * side * 1.01 + side * fr / 2), glass, bevel=.02); S["ghost"].append((o, side * fr, i * side * 1.01)); ANIM.append(o)
    S["cube_lbl"] = label("lb_all", "人類の金 22万t", (gx, gy - .9, 0), .16); S["need_lbl"] = label("lb_need", f"必要 {need:.1f}倍", (gx + side * 1.35, gy - .9, 0), .16)


def a_s01(u, t, f):
    piles_anim(S["s01"], t, lbeat("s01", 1), BP * .45)
    tc = lbeat("s01", 8)                                # 「人類が掘った金の 4.8 倍」
    S["cube"].location.z = .65 if t > tc else -50
    for i, (o, hz, z0) in enumerate(S["ghost"]):
        t0 = tc + BP * (1 + i * .5); k = clamp(spring(clamp((t - t0) / .45) * 1.2), 0, 1.15) if t > t0 else 0; o.scale = (1, 1, max(.001, k)); o.location.z = z0 + hz * k / 2 if t > t0 else -50
    for lb, t0 in ((S["cube_lbl"], tc), (S["need_lbl"], tc + BP * 3)):
        lb.location.z = 0 if t > t0 else -50
    P, A, L = path([(0, (-3.8, -4.2, 6.4), (-3.4, .6, 0), 30), (lbeat("s01", 6.5), (3.6, -4.0, 6.0), (3.4, .7, 0), 30), (lbeat("s01", 8), (.2, -8.0, 4.0), (.1, -4.6, 1.2), 30),
                    (8, (.6, -12.8, 3.0), (.1, -5.6, 2.8), 30)], t); look(P, A, L, 5.0)


# ---------------------------------------------------------------- s02：中国の山（いちばん高い）
def s_s02():
    base_set(); ANIM[:] = [cam.o]; piles, h = map_piles("m2"); S["s02"] = piles
    r = RG["中国"]; x, y = map_xy(r["lon"], r["lat"], MAPW, h); S["cn"] = (x, y); S["cn_lbl"] = label("lb_cn", "中国 " + tonnes_label(r), (x + .2, y - 1.35, 0), .2)


def a_s02(u, t, f):
    for k, (r, bars) in enumerate(S["s02"]):
        for i, (o, base, rz) in enumerate(bars):
            if r["name"] == "中国":
                drop(o, base, t, lbeat("s02", 0) + i * .03, h=1.2, dur=.26, rz=rz)
            else:
                o.location = base; o.rotation_euler = (0, 0, rz)
    x, y = S["cn"]; a = .9 - .35 * ease(t / 3)
    P = (x + 3.0 * math.cos(a + 3.6), y + 3.0 * math.sin(a + 3.6), 1.2 + .6 * ease(t / 3)); look(P, (x, y, .35), 45, 2.2)


# ---------------------------------------------------------------- s03：アメリカ → ユーロ圏 → 日本
def s_s03():
    base_set(); ANIM[:] = [cam.o]; piles, h = map_piles("m3"); S["s03"] = piles; S["h3"] = h
    for k, nm in enumerate(("アメリカ", "ユーロ圏", "日本")):
        r = RG[nm]; x, y = map_xy(r["lon"], r["lat"], MAPW, h); label(f"lb3{k}", f"{nm} {tonnes_label(r)}", (x, y - 1.0, 0), .17)


def a_s03(u, t, f):
    for r, bars in S["s03"]:
        for o, base, rz in bars:
            o.location = base; o.rotation_euler = (0, 0, rz)
    h = S["h3"]; pts = [map_xy(RG[n]["lon"], RG[n]["lat"], MAPW, h) for n in ("アメリカ", "ユーロ圏", "日本")]
    ts = [0, lbeat("s03", 2.5), lbeat("s03", 5)]
    keys = [(ts[i] + (.0 if i == 0 else -.35), (p[0] - .3, p[1] - 3.2, 1.9), (p[0], p[1] - .2, .25), 40) for i, p in enumerate(pts)]
    keys = [keys[0], (ts[0] + .9, keys[0][1], keys[0][2], 42), keys[1], (ts[1] + .9, keys[1][1], keys[1][2], 42), keys[2], (8, (pts[2][0] - .6, pts[2][1] - 3.6, 2.2), (pts[2][0], pts[2][1] - .2, .25), 44)]
    P, A, L = path(keys, t); look(P, A, L, 2.6)


# ---------------------------------------------------------------- s04：一人あたりの表彰台（本当の大きさ：1 単位＝10 cm）
G_CM3 = 19.32


def dia_cm(g):
    return 2 * (3 * g / G_CM3 / (4 * math.pi)) ** (1 / 3)


def ball(name, g, loc):
    return sphere(name, dia_cm(g) / 20, loc, gold_mat(), 128)


def s_s04():
    base_set(desk_scale=14); ANIM[:] = [cam.o]; wd = wood()
    pods = [("スイス", 0.0, 1.0, 1), ("香港", -1.35, .72, 2), ("オーストラリア", 1.35, .52, 3)]; S["s04"] = []
    for nm, x, hh, n in pods:
        podium(f"pd{n}", (x, 0, 0), 1.2, hh, n, wd); r = RG[nm]; b = ball(f"bl{n}", r["g_pp"], (x, 0, -50)); S["s04"].append((b, (x, 0, hh + dia_cm(r["g_pp"]) / 20), n))
        ANIM.append(b); label(f"lp{n}", f"{nm} {r['g_pp'] / 1000:.1f}kg" if r["g_pp"] >= 1000 else f"{nm} {r['g_pp']:.0f}g", (x, -.75, 0), .11)
    jp = RG["日本"]; S["jp4"] = ball("bljp", jp["g_pp"], (2.75, -.2, -50)); ANIM.append(S["jp4"]); S["jp4_lbl"] = label("lpjp", f"日本 4位 {jp['g_pp']:.0f}g", (2.75, -.75, -50), .11)


def a_s04(u, t, f):
    for b, base, n in S["s04"]:
        drop(b, base, t, lbeat("s04", {1: 2, 2: 3.5, 3: 5}[n]), h=1.2, dur=.3)
    tj = lbeat("s04", 7.5); k = eout((t - tj) / .6) if t > tj else 0; rj = dia_cm(RG["日本"]["g_pp"]) / 20
    S["jp4"].location = (lerp(4.6, 2.75, k), -.2, rj if t > tj else -50); S["jp4"].rotation_euler = (0, lerp(6, 0, k), 0); S["jp4_lbl"].location.z = 0 if t > tj + .3 else -50
    P, A, L = path([(0, (0, -6.0, 2.6), (0, 0, .7), 50), (lbeat("s04", 6.5), (.3, -6.6, 2.3), (.3, -.3, .55), 46), (7, (2.0, -4.6, 1.4), (2.4, -.3, .25), 55)], t); look(P, A, L, 2.8)


# ---------------------------------------------------------------- 定規（本当の大きさの目安）
def ruler(name, loc, length_cm=10):
    p = os.path.join(GEN, f"ruler{length_cm}.png")
    if not os.path.exists(p):
        from PIL import Image, ImageDraw, ImageFont
        Wd, Hd = 200 * length_cm, 360; im = Image.new("RGB", (Wd, Hd), (236, 228, 208)); g = ImageDraw.Draw(im); fnt = ImageFont.truetype(os.path.join(HERE, "..", "assets", "fonts", "BIZUDPGothic-Bold.ttf"), 64)
        for mm in range(length_cm * 10 + 1):
            x = int(mm * Wd / (length_cm * 10)); hh = 150 if mm % 10 == 0 else 95 if mm % 5 == 0 else 60; g.line([(x, 0), (x, hh)], fill=(40, 34, 28), width=5 if mm % 10 == 0 else 3)
            if mm % 10 == 0 and 0 < mm < length_cm * 10:
                g.text((x, 230), str(mm // 10), font=fnt, fill=(40, 34, 28), anchor="mm")
        im.save(p)
    root = empty(name, loc); parent(box(name + "_b", (length_cm / 10, .36, .02), (0, 0, .01), plain("rulerb", (.85, .8, .7), .5), bevel=.004), root)
    parent(plane(name + "_t", length_cm / 10, .36, (0, 0, .0205), image_mat("rulerimg" + str(length_cm), p, .45)), root); return root


def pingpong(name, loc):
    return sphere(name, .2, loc, plain("pp", (.92, .9, .86), .55), 96)


# ---------------------------------------------------------------- s05：日本 671 g＝直径 4 cm、ピンポン玉
def s_s05():
    base_set(desk_scale=14); ANIM[:] = [cam.o]; g = RG["日本"]["g_pp"]; r = dia_cm(g) / 20
    S["jp5"] = ball("b5", g, (-.28, 0, r)); S["pp"] = pingpong("pp5", (.28, 0, -50)); ANIM.append(S["pp"]); ruler("rl5", (0, -.55, 0), 10)


def a_s05(u, t, f):
    tp = lbeat("s05", 2); k = eout((t - tp) / .5) if t > tp else 0
    S["pp"].location = (lerp(1.4, .28, k), 0, .2 if t > tp else -50); S["pp"].rotation_euler = (0, lerp(4, 0, k), 0)
    a = -1.75 + .25 * ease(t / 3.5); P = (2.6 * math.cos(a), 2.6 * math.sin(a), .8 - .1 * ease(t / 3.5)); look(P, (0, -.15, .15), 60, 2.8)


# ---------------------------------------------------------------- s06：中国・ロシア・インド（だんだん小さく）
def s_s06():
    base_set(desk_scale=14); ANIM[:] = [cam.o]; ruler("rl6", (0, -.6, 0), 10); S["s06"] = []
    for k, nm in enumerate(("中国", "ロシア", "インド")):
        g = RG[nm]["g_pp"]; x = -.75 + k * .75; b = ball(f"b6{k}", g, (x, 0, -50)); ANIM.append(b); S["s06"].append((b, (x, 0, dia_cm(g) / 20)))
        S.setdefault("l6", []).append(label(f"l6{k}", f"{nm} {g:.0f}g", (x, .45, -50), .07))


def a_s06(u, t, f):
    for k, (b, base) in enumerate(S["s06"]):
        t0 = lbeat("s06", k * 2.2); drop(b, base, t, t0, h=.8, dur=.26); S["l6"][k].location.z = 0 if t > t0 + .2 else -50
    P, A, L = path([(0, (-.9, -2.2, .75), (-.75, 0, .12), 70), (lbeat("s06", 2.2), (-.1, -2.2, .7), (0, 0, .1), 70), (lbeat("s06", 4.4), (.6, -2.0, .6), (.75, 0, .06), 75), (5, (.0, -2.6, .9), (0, 0, .08), 60)], t); look(P, A, L, 2.6)


# ---------------------------------------------------------------- s07：アフリカ 約 9 g＝直径 1 cm
def s_s07():
    base_set(desk_scale=14); ANIM[:] = [cam.o]; g = RG["アフリカ"]["g_pp"]; S["af"] = ball("b7", g, (0, 0, -50)); ANIM.append(S["af"]); ruler("rl7", (.2, -.18, 0), 5)
    S["l7"] = label("l7", f"アフリカ 約{g:.0f}g", (0, .45, -50), .06)


def a_s07(u, t, f):
    g = RG["アフリカ"]["g_pp"]; drop(S["af"], (0, 0, dia_cm(g) / 20), t, lbeat("s07", .5), h=.4, dur=.24); S["l7"].location.z = 0 if t > lbeat("s07", 1) else -50
    P, A, L = path([(0, (.25, -1.5, .5), (.1, -.05, .03), 70), (3.5, (-.05, -1.25, .4), (.1, -.05, .03), 75)], t); look(P, A, L, 2.8)


# ---------------------------------------------------------------- s08：天秤（日本 vs アフリカ）
def s_s08():
    base_set(desk_scale=10); ANIM[:] = [cam.o]; root, pv, pans = balance("bal", (0, 0, 0)); S["bal"] = (root, pv, pans)
    S["bj"] = ball("bj", RG["日本"]["g_pp"], (0, 0, 0)); S["ba"] = ball("ba", RG["アフリカ"]["g_pp"], (0, 0, 0)); ANIM.extend([pv] + [p for _, p in pans] + [S["bj"], S["ba"]])


def a_s08(u, t, f):
    root, pv, pans = S["bal"]; t0 = lbeat("s08", 1); k = clamp((t - t0) / .45)
    ang = .33 * (1 - math.cos(math.pi * k)) / 2 + (.04 * math.exp(-4 * (t - t0 - .45)) * math.sin(12 * (t - t0 - .45)) if t > t0 + .45 else 0)
    set_balance(root, pv, pans, ang)
    pl, pr = pans[0][1].location, pans[1][1].location
    S["bj"].location = (pl.x, 0, pl.z + .03 + dia_cm(RG["日本"]["g_pp"]) / 20); S["ba"].location = (pr.x, 0, pr.z + .03 + dia_cm(RG["アフリカ"]["g_pp"]) / 20)
    P, A, L = path([(0, (0, -9.6, 2.3), (0, 0, 1.75), 32), (2.5, (0, -9.0, 2.1), (0, 0, 1.65), 33)], t); look(P, A, L, 5.0)


# ---------------------------------------------------------------- s09：100 人の大人と、富の山
def s_s09():
    base_set(); ANIM[:] = [cam.o]; S["crowd"] = []; m = plain("ceramic", (.86, .84, .8), .35, coat=.5); gm = gold_mat()
    for k in range(98):
        i, j = k % 14, k // 14; x = -3.9 + i * .6; y = -2.4 - j * .62; fg = figure(f"fg{k}", (x, y, -50), .75, m); bb = bar(f"sm{k}", (x + .2, y - .05, -50), .5, .22)
        S["crowd"].append((fg, bb, (x, y))); ANIM.extend([fg, bb])
    S["top"] = [figure(f"tp{k}", (0, 0, -50), .85, gm) for k in range(2)]; ANIM.extend(S["top"])
    S["big"] = []; ps = pile_slots(48)
    for i, (bx, by, bz, rz) in enumerate(ps):
        o = bar(f"wb{i}", (0, 0, -50), rz, .62); S["big"].append((o, (bx * .62, 2.2 + by * .62, bz * .62), rz)); ANIM.append(o)
    S["topz"] = max(b[1][2] for b in S["big"]) + .2 * .62


def a_s09(u, t, f):
    for k, (fg, bb, (x, y)) in enumerate(S["crowd"]):
        t0 = .05 + k * .012; fg.location = (x, y, 0 if t > t0 else -50)
        drop(bb, (x + .2, y - .05, 0), t, lbeat("s09", 6) + k * .01, h=.6, dur=.22, rz=.5)
    tb = lbeat("s09", 3)
    for i, (o, base, rz) in enumerate(S["big"]):
        drop(o, base, t, tb + i * .025, h=2.2, dur=.3, rz=rz)
    tt = tb + 48 * .025 + .3
    for k, o in enumerate(S["top"]):
        drop(o, (-.3 + k * .6, 2.2, S["topz"]), t, tt + k * .12, h=1.2, dur=.3)
    P, A, L = path([(0, (0, -9.0, 2.6), (0, -3.6, .4), 40), (lbeat("s09", 2.5), (0, -9.5, 3.4), (0, -2.0, .6), 34), (lbeat("s09", 5), (2.6, -6.5, 4.0), (0, 1.6, 1.2), 32), (7, (3.0, -8.2, 5.4), (0, -.4, .8), 30)], t)
    look(P, A, L, 3.5)


# ---------------------------------------------------------------- s10：最後（地図の上の山を上から引いて見る）
def s_s10():
    base_set(); ANIM[:] = [cam.o]; piles, h = map_piles("m10"); S["s10"] = piles


def a_s10(u, t, f):
    for r, bars in S["s10"]:
        for o, base, rz in bars:
            o.location = base; o.rotation_euler = (0, 0, rz)
    P, A, L = path([(0, (3.6, -3.0, 2.6), (3.4, 1.0, .2), 38), (2.2, (1.0, -3.4, 6.4), (.8, .4, 0), 28), (4.5, (0, -2.6, 9.8), (0, .4, 0), 26)], t); look(P, A, L, 6.0)


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
