"""pilot_064「同じ赤ちゃんが、違う国に生まれたら？」の 3D（Blender Cycles）。新ドパ設計 v2（061 型、063 の scene63.py の複製から）。
ショット＝セリフの行（s00〜s11）。書斎の抽選機 → 白い赤ちゃんの群れ → 4 つの国の台座 → 平均寿命の金の柱 → 5 歳まで・本・金貨と暦 → 100 年前の日本 → 抽選機。
人・赤ちゃんは顔のない陶器・金の模型（CHARACTER_GUIDE の方針）。動き・カメラの着地は表拍（lbeat の整数）。閃光なし。
blender -b -P blender/scene64.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib64 import *  # noqa: F401,F403
from lib64 import _sc

O = K.args()
NAMES = [l["scene"] for l in PLAN["lines"]]
TL = json.load(open(os.path.join(HERE, "..", "work", "timeline.json"), encoding="utf-8")); CUE = TL["cues"]
sc = setup(samples=O["samples"] if "--samples" in sys.argv else 48)
KEY = area_light("key", (-4, -6, 8), (0, 0, 1), 5, 1500); RIM = area_light("rim", (5, 4, 6), (0, 0, 1.5), 4, 700, (1, .8, .6))
cam = K.Cam(); ANIM = [cam.o]; S = {}; CUR = ["s00"]
for _l in (KEY, RIM):
    _l.visible_camera = False; _l.visible_glossy = False   # 照明の板が床に写り込まないように


def lbeat(name, k):
    c = CUE[name]; return (round(c / BP) + k) * BP - c


def look(P, A, lens=40, fstop=2.8, roll=0.0):
    P, A = Vector(P), Vector(A); cam.look(P, A, lens, roll); cam_dof(cam, (P - A).length, fstop)


def vlerp(a, b, u):
    return [lerp(x, y, u) for x, y in zip(a, b)]


def eio(u):
    u = clamp(u); return 16 * u ** 5 if u < .5 else 1 - (-2 * u + 2) ** 5 / 2


def snap(keys, t, mv=.42, kick=.09):
    if t <= keys[0][0]:
        return keys[0][1], keys[0][2], keys[0][3], 0.0
    for n, ((t0, p0, a0, l0), (t1, p1, a1, l1)) in enumerate(zip(keys, keys[1:])):
        if t <= t1:
            d = min(mv, (t1 - t0) * .8); ts = t1 - d; p0d = vlerp(p0, a0, .07)
            if t < ts:
                return vlerp(p0, a0, .07 * ease((t - t0) / max(1e-3, ts - t0))), a0, l0, 0.0
            u = eio((t - ts) / d); sg = 1 if n % 2 else -1
            return vlerp(p0d, p1, u), vlerp(a0, a1, u), lerp(l0, l1, u), sg * kick * math.sin(math.pi * u)
    t1, p1, a1, l1 = keys[-1]; h = clamp((t - t1) / 3.0)
    return vlerp(p1, a1, .05 * ease(h)), a1, l1, 0.0


def go(name, keys, t, fstop=3.0, mv=.42, kick=.09):
    ks = [(0 if i == 0 else lbeat(name, k), p, a, l) for i, (k, p, a, l) in enumerate(keys)]
    P, A, L, r = snap(ks, t, mv, kick); look(P, A, L, fstop, r)


def drop(o, base, t, t0, h=2.0, dur=.3, rz=None):
    """拍の頭 t0 に着地する（落ち始めは t0 − dur）"""
    t0 -= dur; u = (t - t0) / dur
    if u < 0:
        o.location = (base[0], base[1], -50); return
    z = base[2] + h * (1 - u * u) if u < 1 else base[2] + .05 * h * math.exp(-9 * (t - t0 - dur)) * abs(math.sin(16 * (t - t0 - dur)))
    o.location = (base[0], base[1], z)
    if rz is not None:
        o.rotation_euler = (o.rotation_euler[0], o.rotation_euler[1], rz)


def rise(o, base, t, t0, dur=.35, depth=None):
    """床の下からせり上がる（拍の頭 t0 に着く）。depth：最初に沈んでいる深さ"""
    d = depth if depth is not None else o.get("h", 3.0)
    u = clamp((t - (t0 - dur)) / dur); o.location = (base[0], base[1], base[2] - d * (1 - eio(u)))


# ---------------------------------------------------------------- 質感・部品
def ceramic():
    return plain("ceramic", (.86, .84, .8), .35, coat=.5)


def goldfig():
    return gold_mat("goldfig", .16)


def fig(name, loc, s=.6, m=None, rz=0.0):
    f = figure(name, loc, s, m); f.rotation_euler = (0, 0, rz); f["z0"] = loc[2]; ANIM.append(f); return f


def lamp(name, loc, energy, col, r=.4):
    d = bpy.data.lights.new(name, "POINT"); d.energy = energy; d.color = col; d.shadow_soft_size = r
    o = bpy.data.objects.new(name, d); o.location = loc; return link(o)


def spot(name, loc, at, energy, col=(1, .95, .85), size=.4, blend=.3, ang=.5):
    d = bpy.data.lights.new(name, "SPOT"); d.energy = energy; d.color = col; d.shadow_soft_size = size; d.spot_blend = blend; d.spot_size = ang
    o = bpy.data.objects.new(name, d); o.location = loc; o.rotation_mode = "QUATERNION"; o.rotation_quaternion = (Vector(at) - Vector(loc)).to_track_quat("-Z", "Y"); return link(o)


def lights(key, rim, hdri="studio_small_08_2k.hdr", strength=.8, rot=0.0, bg=0):
    w = world(hdri, strength, rot, bg)
    if bg:
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


HALL_DOTS = []
ENV = {}
# 景色：HDRI・地面の質感・質感の縮尺・色・地面の大きさ・HDRI の明るさ・向き・キーの光・リムの光
OUTENV = {"ward": ("hospital_room_2_2k.hdr", None, .3, (.5, .58, .64), 9, 1.0, math.pi / 2, (300, (1, 1, 1)), (300, (.9, .95, 1))),
          "veld": ("aarfontein_dirt_road_2k.hdr", "raked_dirt", 1 / 2.5, (.95, .82, .68), 300, 1.0, 0.0, (500, (1, .8, .6)), (500, (1, .7, .45))),
          "field": ("farm_sunset_2k.hdr", "park_dirt", 1 / 2.5, (.85, .75, .6), 300, 1.0, 0.0, (400, (1, .82, .62)), (500, (1, .7, .45))),
          "school": ("school_hall_2k.hdr", "wood_floor", 1 / 1.6, (1, .9, .78), 9, 1.0, math.pi, (400, (1, .92, .8)), (300, (1, .85, .7))),
          "garden": ("ninomaru_teien_2k.hdr", "grass_ground", 1 / 2.5, (.75, .9, .65), 300, 1.0, 0.0, (400, (1, .95, .85)), (400, (1, .9, .75))),
          "garden2": ("ninomaru_teien_2k.hdr", "grass_ground", 1 / 2.5, (.75, .9, .65), 300, 1.0, 3.14, (400, (1, .95, .85)), (400, (1, .9, .75)))}


def stage(*kinds):
    """舞台を 1 つ以上つくる。2 つ以上なら use_env() で場面の途中に切り替える（使わない方は床の下へ）"""
    clear_scene(); ANIM[:] = [cam.o]; HALL_DOTS.clear(); ENV.clear()
    for k in kinds:
        before = set(_sc().objects); _build_env(k); w = bpy.context.scene.world
        root = empty("env_" + k, (0, 0, 0))
        for o in _sc().objects:
            if o not in before and o is not root and o.parent is None:
                parent(o, root)
        ENV[k] = {"w": w, "root": root, "key": (KEY.data.energy, tuple(KEY.data.color)), "rim": (RIM.data.energy, tuple(RIM.data.color))}
        ANIM.append(root)
    use_env(kinds[0])


def use_env(k):
    e = ENV[k]; bpy.context.scene.world = e["w"]
    KEY.data.energy, KEY.data.color = e["key"]; RIM.data.energy, RIM.data.color = e["rim"]
    for kk, ee in ENV.items():
        ee["root"].location = (0, 0, 0) if kk == k else (0, 0, -300)


def dots_on(which):
    """世界地図の国の灯り（0 日本・1 アメリカ・2 インド・3 チャド）。which に入っていない灯りは消す"""
    for i in range(4):
        sp, li = HALL_DOTS[2 * i], HALL_DOTS[2 * i + 1]; on = i in which
        sp.scale = (1, 1, 1) if on else (.001, .001, .001); li.data.energy = 40 if on else 0
        if sp not in ANIM:
            ANIM.extend([sp, li])


def _build_env(kind):
    """舞台：world（064：世界地図の展示室）・study（書斎、v3）・arena（暗い展示室）・room（夜の食卓の部屋）・night（夜の住宅街の家の前）"""
    if kind == "arena":
        plane("floor", 80, 80, (0, 0, 0), plain("blackfloor", (.025, .024, .027), .22, coat=.8))
        plane("backw", 80, 20, (0, 9, 10), pbr_mat("bw", "brushed_concrete", 1 / 3.0, (.16, .15, .15), 1.0, box_proj=True), rot=(math.pi / 2, 0, 0)); lights((900, (1, .92, .8)), (600, (1, .8, .6)), "studio_small_08_2k.hdr", .35)
    elif kind == "world":                     # 064：紺の展示室の奥の壁いっぱいに金の大陸の世界地図、4 つの国の位置に灯り。床は暗い鏡面
        plane("floor", 80, 80, (0, 0, 0), plain("navyfloor", (.012, .016, .03), .16, coat=.9))
        nv = plain("navywall", (.03, .045, .09), .7)
        plane("backw", 80, 24, (0, 9.45, 12), nv, rot=(math.pi / 2, 0, 0))
        for sx in (-1, 1):
            plane("sidew%d" % sx, 40, 24, (sx * 15, 0, 12), nv, rot=(math.pi / 2, 0, math.pi / 2))
        MW, MH, MZ = 26.0, 26.0 * 1594 / 4096, 10.6
        plane("map", MW, MH, (0, 9.4, MZ - MH / 2), image_mat("worldmap", os.path.join(HERE, "..", "assets", "worldmap.png"), .55, .55), rot=(math.pi / 2, 0, 0))
        brass = gold_mat("brassl", .3, (.86, .62, .3))
        box("mapframe_t", (MW + .3, .12, .12), (0, 9.33, MZ + .06), brass, bevel=.02); box("mapframe_b", (MW + .3, .12, .12), (0, 9.33, MZ - MH - .06), brass, bevel=.02)
        dot = glow_mat("mapdot", (1, .9, .7), 30.0)
        for lon, lat in ((139.7, 35.7), (-98.0, 39.0), (78.9, 21.0), (18.7, 15.5)):       # 日本・アメリカ・インド・チャド
            x = ((lon + 170) % 360 / 360 - .5) * MW; z = MZ - (80 - lat) / 140 * MH
            HALL_DOTS.append(sphere("dot%g" % lon, .1, (x, 9.3, z), dot, 24))
            l = bpy.data.lights.new("dl%g" % lon, "POINT"); l.energy = 40; l.color = (1, .85, .6); l.shadow_soft_size = .1
            o = bpy.data.objects.new("dl%g" % lon, l); o.location = (x, 9.0, z); link(o); HALL_DOTS.append(o)
        lights((1000, (1, .9, .8)), (800, (.7, .8, 1)), "studio_small_08_2k.hdr", .4)
    elif kind in OUTENV:                      # 064：国・時代の景色（Poly Haven の CC0 の HDRI を背景に見せる）＋その地面の質感
        hd, tex, sc_, tint, size, stren, rot, key, rim = OUTENV[kind]
        fm = plain("fl_" + kind, tint, sc_, coat=.3) if tex is None else pbr_mat("fl_" + kind, tex, sc_, tint, 1.0, box_proj=True)   # 屋内は床を小さく（その先は HDRI の床）
        rot = float(os.environ.get("ROT_" + kind, rot))
        if size < 50:                         # 屋内：床は影だけを受ける（見えるのは HDRI の床）
            o = plane("fl_" + kind, 60, 60, (0, 0, 0), fm); o.is_shadow_catcher = True
        else:
            plane("fl_" + kind, size, size, (0, 0, 0), fm)
        lights(key, rim, hd, stren, rot, 1)
    elif kind == "study":                     # 書斎：大理石の床、奥に天井までの本棚と木の壁、真鍮の灯り（v3）
        plane("floor", 60, 60, (0, 0, 0), pbr_mat("marble", "marble_01", 1 / 2.2, (.95, .9, .82), .6, box_proj=True))
        wd = pbr_mat("panel", "dark_wood", 1 / 1.5, (.55, .38, .26), 1.0, box_proj=True)
        plane("backw", 60, 14, (0, 9.4, 7), wd, rot=(math.pi / 2, 0, 0))
        bookshelf("shelf", (0, 9.0, 0), 22.0, 5.6)
        for sx in (-1, 1):
            plane("sidew%d" % sx, 30, 14, (sx * 11, 0, 7), wd, rot=(math.pi / 2, 0, math.pi / 2))
            bookshelf("shelfs%d" % sx, (sx * 10.6, 1.0, 0), 14.0, 5.6, rz=-sx * math.pi / 2)
        brass = gold_mat("brassl", .3, (.86, .62, .3)); shade = glow_mat("lampglow", (1, .82, .55), 6.0)
        for x in (-4.2, 4.2):                 # 壁の真鍮の灯り
            cyl("sc%g" % x, .05, .5, (x, 8.85, 3.2), brass, 24); sphere("scg%g" % x, .16, (x, 8.75, 3.55), shade, 32)
            l = bpy.data.lights.new("scl%g" % x, "POINT"); l.energy = 260; l.color = (1, .78, .5); l.shadow_soft_size = .2
            o = bpy.data.objects.new("scl%g" % x, l); o.location = (x, 8.5, 3.5); link(o)
        lights((1100, (1, .9, .78)), (700, (1, .82, .62)), "brown_photostudio_02_2k.hdr", .55)
    elif kind == "room":
        plane("floor", 40, 40, (0, 0, 0), pbr_mat("court", "wood_floor", 1 / 1.6, (1, .9, .78), 1.0, box_proj=True))
        wl = plain("wall", (.55, .48, .4), .8)
        plane("backw", 40, 10, (0, 3.2, 5), wl, rot=(math.pi / 2, 0, 0)); plane("sidew", 40, 10, (-3.6, 0, 5), wl, rot=(math.pi / 2, 0, math.pi / 2))
        lights((500, (1, .85, .65)), (300, (1, .8, .6)), "brown_photostudio_02_2k.hdr", .25)
    elif kind == "night":
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("grs", "grass_ground", 1 / 2.5, (.55, .65, .5), 1.0, box_proj=True))
        plane("path", 1.2, 8, (0, -3.0, .004), pbr_mat("pv", "brushed_concrete", 1 / 1.5, (.6, .58, .55), 1.0, box_proj=True))
        lights((250, (.7, .78, 1)), (500, (1, .8, .55)), "modern_evening_street_2k.hdr", .5, 0.0, 1)


def pillar(name, loc, h, w=.7, m=None, label=None, lab_size=.42):
    """金の柱（床から h の高さ）。label は柱の上の正面に立つ金の数字"""
    root = empty(name, loc); m = m or gold_mat("goldpil", .14)
    parent(box(name + "_b", (w, w, h), (0, 0, h / 2), m, bevel=.03), root)
    if label:
        parent(text_obj(name + "_t", label, (0, -w / 2 - .02, h + lab_size * .75), lab_size, gold_mat("goldtext", .2), extrude=.04), root)
    root["h"] = h + (lab_size * 1.4 if label else 0) + .2; ANIM.append(root); return root


def stumps(name, loc):
    """クリケットの柱（ウィケット）：3 本の柱と、上の 2 本の横木（ベイル）"""
    wd = plain("stumpwood", (.86, .78, .6), .45, coat=.3); root = empty(name, loc); bails = []
    for x in (-.11, 0, .11):
        parent(cyl(name + "_s%g" % x, .022, .72, (x, 0, .36), wd, 24), root)
    for i, x in enumerate((-.055, .055)):
        b = cyl(name + "_bail%d" % i, .012, .11, (loc[0] + x, loc[1], loc[2] + .735), wd, 12); b.rotation_euler = (0, math.pi / 2, 0); b["base"] = (loc[0] + x, loc[1], loc[2] + .735); bails.append(b); ANIM.append(b)
    return root, bails


def bails_fly(bails, t, t0, dirs=((-1.2, -1.6), (1.0, -1.9))):
    for b, (vx, vy) in zip(bails, dirs):
        x, y, z = b["base"]
        if t < t0:
            b.location = (x, y, z); b.rotation_euler = (0, math.pi / 2, 0); continue
        v = t - t0; zz = z + 2.6 * v - 4.9 * v * v
        if zz < .012:
            v2 = (2.6 + math.sqrt(2.6 ** 2 + 4 * 4.9 * (z - .012))) / 9.8; v = v2; zz = .012
        b.location = (x + vx * .5 * v, y + vy * .5 * v, zz); b.rotation_euler = (7 * v * (1 if vx > 0 else -1), math.pi / 2 + 5 * v, 0)


def bat(name, s=1.0):
    wd = plain("batwood", (.88, .78, .55), .45, coat=.3); grip = plain("grip", (.08, .08, .1), .7); root = empty(name)
    parent(box(name + "_blade", (.11 * s, .04 * s, .55 * s), (0, 0, -.42 * s), wd, bevel=.012), root)
    parent(cyl(name + "_h", .018 * s, .3 * s, (0, 0, -.02 * s), grip, 16), root); return root


def batter(name, loc, s=1.0, facing=0.0):
    """打者：人形＋バット（手元を軸に回る）"""
    f = fig(name, loc, s, rz=facing); b = bat(name + "_bat", s); b.location = (loc[0] + .25 * s, loc[1] - .05 * s, loc[2] + .62 * s); b.rotation_euler = (0, -.5, 0); ANIM.append(b)
    return f, b


def ball(name, r=.05, col=(.55, .05, .04)):
    o = sphere(name, r, (0, 0, -50), plain("cball_%g" % col[0], col, .35, coat=.6), 32); ANIM.append(o); return o


def path_bowl(t, t0, t1, a, bounce, b):
    """t0 に a を出て、bounce で弾み、t1 に b へ（2 区間の放物線）"""
    tm = t0 + (t1 - t0) * .62
    if t < tm:
        u = clamp((t - t0) / (tm - t0)); p = vlerp(a, bounce, u); p[2] += 4 * .25 * u * (1 - u) - 0; return p
    u = clamp((t - tm) / (t1 - tm)); p = vlerp(bounce, b, u); p[2] += 4 * .18 * u * (1 - u); return p


def photo_frame(name, key, loc, rz=-.3, w=1.4):
    p = os.path.join(HERE, "..", "assets", "photo", key + ".jpg"); im = bpy.data.images.load(p, check_existing=True); h = w * im.size[1] / im.size[0]
    root = empty(name, loc); root.rotation_euler = (math.radians(-10), 0, rz)
    parent(box(name + "_f", (w + .18, .06, h + .18), (0, 0, h / 2 + .09), plain("frame", (.12, .08, .05), .5, coat=.4), bevel=.02), root)
    parent(box(name + "_m", (w + .08, .062, h + .08), (0, -.002, h / 2 + .09), plain("mat", (.93, .9, .84), .7), bevel=0), root)
    parent(plane(name + "_p", w, h, (0, -.035, h / 2 + .09), image_mat("ph_" + key, p, .5), rot=(math.pi / 2, 0, 0)), root)
    ANIM.append(root); return root



def torus(name, R, r, loc, m, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=64, minor_segments=12, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(m); bpy.ops.object.shade_smooth(); return o


def reflector(name, loc, at, size, energy):
    """カメラの後ろの大きな光の板：カメラには写らず、金の面にだけ映り込む（暗く沈まないように）"""
    o = area_light(name, loc, at, size, energy, (1, .95, .88)); o.visible_camera = False; o.visible_diffuse = False; return o


def label(name, txt, loc, size=.15, rot=(math.pi / 2, 0, 0)):
    return text_obj(name, txt, loc, size, gold_mat("goldtext", .2), rot=rot, extrude=.012, font="BIZUDPGothic-Bold.ttf")


ICO = [(0, a, b) for a in (-1, 1) for b in (-1.618, 1.618)] + [(a, b, 0) for a in (-1, 1) for b in (-1.618, 1.618)] + [(b, 0, a) for a in (-1, 1) for b in (-1.618, 1.618)]


def soccer_ball(name, r=.2):
    from mathutils import Vector
    root = empty(name); parent(sphere(name + "_w", r, (0, 0, 0), plain("sbw", (.93, .93, .9), .4, coat=.3), 64), root); bk = plain("sbk", (.03, .03, .035), .4, coat=.3)
    for i, v in enumerate(ICO):
        d = Vector(v).normalized(); o = cyl(name + "_p%d" % i, r * .36, r * .06, tuple(d * r * .985), bk, 5); o.rotation_euler = d.to_track_quat("Z", "Y").to_euler(); parent(o, root)
    return root


def baseball(name, r=.12):
    root = empty(name); parent(sphere(name + "_w", r, (0, 0, 0), plain("bbw", (.94, .92, .86), .5, coat=.2), 48), root); rd = plain("bbred", (.75, .06, .05), .5)
    a, b = .72, .28
    for i in range(72):
        t = i / 72 * 2 * math.pi; x, y, z = a * math.cos(t) + b * math.cos(3 * t), a * math.sin(t) - b * math.sin(3 * t), 2 * math.sqrt(a * b) * math.sin(2 * t)
        parent(sphere(name + "_s%d" % i, r * .07, (x * r * 1.0, y * r * 1.0, z * r * 1.0), rd, 8), root)
    return root


def basketball(name, r=.2):
    root = empty(name); parent(sphere(name + "_o", r, (0, 0, 0), plain("bkor", (.8, .3, .07), .65, coat=.1), 64), root); bk = plain("bkln", (.04, .03, .03), .6)
    for i, rot in enumerate(((0, 0, 0), (math.pi / 2, 0, 0), (0, math.pi / 2, 0))):
        parent(torus(name + "_r%d" % i, r * 1.002, r * .025, (0, 0, 0), bk, rot), root)
    return root


def stopwatch(name, s=1.0):
    root = empty(name); sil = plain("silver", (.8, .8, .82), .2, metal=1.0); wh = plain("swface", (.95, .94, .9), .4, coat=.3); bk = plain("swhand", (.05, .05, .05), .4)
    o = cyl(name + "_c", .17 * s, .06 * s, (0, 0, 0), sil, 64, bevel=.008); o.rotation_euler = (math.pi / 2, 0, 0); parent(o, root)
    o = cyl(name + "_f", .145 * s, .062 * s, (0, -.002, 0), wh, 64); o.rotation_euler = (math.pi / 2, 0, 0); parent(o, root)
    for k in range(12):
        a = k / 12 * 2 * math.pi; o = box(name + "_tk%d" % k, (.006 * s, .004, .025 * s), (math.sin(a) * .12 * s, -.034 * s, math.cos(a) * .12 * s), bk, bevel=0); o.rotation_euler = (0, a, 0); parent(o, root)
    o = box(name + "_h", (.008 * s, .004, .11 * s), (.03 * s, -.036 * s, .045 * s), plain("swred", (.8, .08, .06), .4), bevel=0); o.rotation_euler = (0, .55, 0); parent(o, root)
    parent(cyl(name + "_k", .025 * s, .05 * s, (0, 0, .2 * s), sil, 24), root); parent(torus(name + "_ring", .035 * s, .008 * s, (0, 0, .255 * s), sil, (math.pi / 2, 0, 0)), root)
    return root


def golf_set(name):
    root = empty(name); wh = plain("gbw", (.95, .95, .93), .35, coat=.3)
    parent(cyl(name + "_tee", .008, .05, (0, 0, .025), plain("tee", (.85, .7, .4), .5), 16), root); parent(sphere(name + "_b", .045, (0, 0, .095), wh, 32), root)
    sh = cyl(name + "_sh", .007, .8, (.18, .05, .39), plain("shaft", (.75, .75, .78), .2, metal=1.0), 16); sh.rotation_euler = (0, -.22, 0); parent(sh, root)
    parent(box(name + "_hd", (.12, .05, .035), (.12, .05, .02), plain("ironh", (.7, .7, .72), .25, metal=1.0), bevel=.008), root)
    parent(cyl(name + "_gr", .011, .2, (.26, .05, .74), plain("grip", (.08, .08, .1), .7), 16), root)
    return root


def cricket_props(name):
    root = empty(name); b = bat(name + "_bat", 1.0); b.location = (-.05, 0, .03); b.rotation_euler = (0, math.pi / 2, .3); parent(b, root)
    parent(sphere(name + "_rb", .1, (.32, -.1, .1), plain("cball_.55", (.55, .05, .04), .35, coat=.6), 32), root); return root


def hop(t, t0, h=.2, dur=.4):
    """t0 で頂点（拍の頭に一番高い）"""
    u = (t - (t0 - dur / 2)) / dur; return h * math.sin(math.pi * u) if 0 < u < 1 else 0.0




BOOKC = [(.42, .08, .07), (.09, .2, .14), (.1, .14, .3), (.55, .42, .2), (.3, .1, .2), (.72, .66, .55), (.18, .12, .08)]


def bookshelf(name, loc, w, h, rz=0.0, rows=6):
    """本棚：棚板と本を 1 つのメッシュにまとめる（物の数を増やさない）。本は色 7 種類"""
    import random as _r
    R = _r.Random(sum(map(ord, name))); bm = bmesh.new(); mats = [plain("shelfwood", (.22, .13, .08), .45, coat=.3)] + [plain("book%d" % i, c, .55, coat=.15) for i, c in enumerate(BOOKC)]
    def cube(cx, cy, cz, sx, sy, sz, mi):
        r = bmesh.ops.create_cube(bm, size=1.0); vs = r["verts"]
        for v in vs:
            v.co.x = cx + v.co.x * sx; v.co.y = cy + v.co.y * sy; v.co.z = cz + v.co.z * sz
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = mi
    rh = h / rows
    for i in range(rows + 1):
        cube(0, 0, i * rh + .03, w, .42, .06, 0)
    for xx in (-w / 2, w / 2):
        cube(xx, 0, h / 2, .08, .42, h, 0)
    for i in range(rows):
        x = -w / 2 + .08
        while x < w / 2 - .12:
            bw = R.uniform(.035, .075); bh = rh * R.uniform(.62, .86)
            if R.random() < .05:
                x += R.uniform(.1, .3); continue
            cube(x + bw / 2, R.uniform(-.03, .03), i * rh + .06 + bh / 2, bw, .3, bh, 1 + R.randrange(len(BOOKC))); x += bw + .004
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, mats, smooth=False)); o.location = loc; o.rotation_euler = (0, 0, rz); return link(o)


def glass_mat():
    m = bpy.data.materials.get("glass63")
    if m is None:
        m = plain("glass63", (.95, .97, 1.0), .03); b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Transmission Weight"].default_value = 1.0; b.inputs["IOR"].default_value = 1.45
    return m


def cone(name, r1, r2, h, loc, m, seg=64):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r1, radius2=r2, depth=h)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; return link(o)


def bob(name, t, beats, h=.05, dur=.28):
    """拍の頭で弾む高さ（beats の拍それぞれ）。MV のようなグルーブ（2026-11-19 ユーザーの指示）"""
    return sum(hop(t, lbeat(name, k), h, dur) for k in beats)


def kick(name, t, beats, d=.07):
    """拍の頭で手前へ押し出す量（時計の盤などの「ドン」）"""
    return sum(d * math.exp(-max(0.0, t - lbeat(name, k)) * 10) * (t >= lbeat(name, k)) for k in beats)


# ---------------------------------------------------------------- pilot_064：生まれた国のくじ
LINES_J = json.load(open(os.path.join(HERE, "..", "lines.json"), encoding="utf-8"))["lines"]
TLL = {x["id"]: x for x in TL["lines"]}


def pb(lid, j, off=0):
    """字幕の句 j が出る拍（場面の拍 0 から数えて）。renderer.html の phrases() と同じ計算"""
    ln = next(x for x in LINES_J if x["id"] == lid); L = TLL[lid]; tot = len("".join(ln["sub"])); acc = len("".join(ln["sub"][:j]))
    a = round((L["start"] + (L["end"] - L["start"]) * acc / tot - .05) / BP); return a - round(CUE[ln["scene"]] / BP) + off


CT = PLAN["countries"]; PX = [-3.3, -1.1, 1.1, 3.3]; LS = .045          # 平均寿命 1 年＝0.045m
PY = .95                                                               # 柱は台座の後ろ


def bm_ball(bm, c, r, sc=(1, 1, 1), seg=12, ring=8, mi=0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    for v in res["verts"]:
        v.co.x = c[0] + v.co.x * sc[0]; v.co.y = c[1] + v.co.y * sc[1]; v.co.z = c[2] + v.co.z * sc[2]
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mi


BABY = [((0, 0, .24), .22, (1, .85, 1.1)), ((0, 0, .58), .17, (1, 1, 1)), ((-.21, -.06, .36), .07, (1, 1, 1.2)), ((.21, -.06, .36), .07, (1, 1, 1.2)),
        ((-.11, -.17, .07), .08, (1, 1.3, .8)), ((.11, -.17, .07), .08, (1, 1.3, .8))]


def baby(name, m=None, s=1.0):
    """座った赤ちゃんの模型（顔なし）。高さ 約 0.75×s"""
    bm = bmesh.new()
    for c, r, sc in BABY:
        bm_ball(bm, c, r, sc, 32, 20)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m or goldfig()])); o.scale = (s, s, s); link(o); ANIM.append(o); return o


def crowd(name, pts, s, m, kind="baby"):
    """たくさんの赤ちゃん（または人形）を 1 つのメッシュに（物の数を増やさない）。1 体の形を作って numpy で並べる（bmesh に足していくと遅い）"""
    import numpy as np
    parts = BABY if kind == "baby" else [((0, 0, .4), .3, (.85, .7, 1.35)), ((0, 0, 1.0), .17, (1, 1, 1))]
    tb = bmesh.new()
    for c, r, sc in parts:
        bm_ball(tb, c, r, sc)
    tb.verts.index_update(); V = np.array([v.co[:] for v in tb.verts]) * s; F = [[v.index for v in f.verts] for f in tb.faces]; tb.free()
    nv = len(V); AV, AF = [], []
    for k, (x, y, rz) in enumerate(pts):
        cr, sr = math.cos(rz), math.sin(rz)
        AV.append(np.stack([V[:, 0] * cr - V[:, 1] * sr + x, V[:, 0] * sr + V[:, 1] * cr + y, V[:, 2]], 1)); AF.extend([[i + k * nv for i in fc] for fc in F])
    me = bpy.data.meshes.new(name); me.from_pydata(np.concatenate(AV).tolist(), [], AF); me.materials.append(m)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); o = bpy.data.objects.new(name, me); return link(o)


def mini(name, loc, s, m):
    bm = bmesh.new()
    for c, r, sc in [((0, 0, .4), .3, (.85, .7, 1.35)), ((0, 0, 1.0), .17, (1, 1, 1))]:
        bm_ball(bm, (c[0] * s, c[1] * s, c[2] * s), r * s, sc, 16, 10)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; link(o); ANIM.append(o); return o


def flag_mat(k):
    return image_mat("flag_" + k, os.path.join(HERE, "..", "assets", "flags", k + ".png"), .45)


def pedestal(i):
    """国の台座：木の台の正面に国旗と国名（金）"""
    nm, le, k = CT[i]; x = PX[i]; root = empty("ped%d" % i, (x, 0, 0))
    parent(box("pedb%d" % i, (1.5, 1.1, .8), (0, 0, .4), pbr_mat("plinth", "dark_wood", 1.0, (.42, .3, .22), 1.0, box_proj=True), bevel=.03), root)
    parent(box("pedt%d" % i, (1.56, 1.16, .04), (0, 0, .8), gold_mat("brassl", .3, (.86, .62, .3)), bevel=.01), root)
    fw = .66 if k != "us" else .78; fh = .44 if k != "us" else .41
    parent(plane("pedf%d" % i, fw, fh, (0, -.556, .52), flag_mat(k), rot=(math.pi / 2, 0, 0)), root)
    parent(label("pedn%d" % i, nm, (0, -.57, .17), .17 if len(nm) < 4 else .14), root)
    return root


def pedestals(babies=True):
    S["ped"] = [pedestal(i) for i in range(4)]
    S["bb"] = [baby("bb%d" % i, s=.62) for i in range(4)] if babies else []


def pillar_set():
    S["pil"] = []; m = gold_mat("goldpil", .14)
    for i, (nm, le, k) in enumerate(CT):
        r = empty("pil%d" % i, (PX[i], PY, 0)); parent(box("pilb%d" % i, (.62, .5, 1.0), (0, 0, .5), m, bevel=.0), r)
        lb = label("pill%d" % i, "%d年" % round(le), (0, 0, 0), .26); ANIM.append(lb); S["pil"].append((r, lb, le))


def set_pillar(i, h, t=None, t_lab=None, txt_obj=None):
    r, lb, le = S["pil"][i]; r.scale = (1, 1, max(.001, h)); r.location = (PX[i], PY, 0 if h > .002 else -50)
    o = txt_obj or lb
    if t_lab is None or t >= t_lab:
        o.location = (PX[i], PY - .3, h + .22)
    else:
        o.location = (PX[i], PY - .3, -50)


def grow(t, t0, h0, h1, dur=.4):
    return h0 + (h1 - h0) * eio((t - (t0 - dur)) / dur)


def flat(o):
    for pg in o.data.polygons:
        pg.use_smooth = False


def lottery():
    """ガラガラの抽選機：八角形の木の胴（x 軸まわりに回る）、金の縁、取っ手、手前の受け皿"""
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.42, .3, .22), 1.0, box_proj=True); g = gold_mat("gold", .13); red = plain("lacq", (.30, .03, .03), .3, coat=.8)
    root = empty("lot", (0, 0, 0))
    parent(box("lotbase", (2.0, 1.1, .12), (0, 0, .06), wd, bevel=.02), root)
    for sx in (-1, 1):
        parent(box("lotside%d" % sx, (.1, .5, 1.05), (sx * .82, 0, .6), wd, bevel=.02), root)
    dr = empty("drum", (0, 0, 1.08)); parent(dr, root)
    o = cyl("drumb", .56, 1.3, (0, 0, 0), red, 8, bevel=.015); o.rotation_euler = (0, math.pi / 2, 0); parent(o, dr); flat(o)   # 八角形の面が見えるように
    for sx in (-1, 1):
        o = cyl("drumc%d" % sx, .6, .06, (sx * .66, 0, 0), g, 8, bevel=.01); o.rotation_euler = (0, math.pi / 2, 0); parent(o, dr); flat(o)
    for k in range(8):                       # 胴の 8 面に 4 か国の国旗（国のくじ）
        ph = math.radians(22.5 + 45 * k); key = CT[k % 4][2]; ap = .56 * math.cos(math.radians(22.5)) + .004
        fw, fh = (.46, .24) if key == "us" else (.42, .28)
        parent(plane("drumf%d" % k, fw, fh, (0, ap * math.sin(ph), -ap * math.cos(ph)), flag_mat(key), rot=(ph + math.pi, 0, 0)), dr)
    o = cyl("axle", .045, 2.0, (0, 0, 0), g, 24); o.rotation_euler = (0, math.pi / 2, 0); parent(o, dr)
    parent(box("crank", (.05, .06, .5), (1.02, 0, -.25), g, bevel=.01), dr); o = cyl("knob", .05, .22, (1.12, 0, -.48), wd, 24); o.rotation_euler = (0, math.pi / 2, 0); parent(o, dr)
    parent(box("tray", (.62, .42, .05), (0, -.62, .66), g, bevel=.01), root)
    for sx in (-1, 1):
        parent(box("trayw%d" % sx, (.03, .42, .1), (sx * .3, -.62, .7), g, bevel=0), root)
    parent(box("trayf", (.62, .03, .1), (0, -.82, .7), g, bevel=0), root)
    parent(box("trayleg", (.08, .3, .62), (0, -.5, .33), wd, bevel=.01), root)
    for j, (bx, by) in enumerate(((-.2, -.52), (.21, -.7), (.19, -.5))):   # 受け皿に白い玉（はずれ）
        parent(sphere("wball%d" % j, .075, (bx, by, .7 + .075), ceramic(), 48), root)
    S["drum"] = dr; S["ball"] = sphere("ball", .075, (0, 0, -50), gold_mat("gold", .13), 48); ANIM.append(S["ball"])


def spin_drum(t, t0, t1, turns, base=0.0):
    """t0〜t1 に turns 回転（だんだん遅く）"""
    k = clamp((t - t0) / (t1 - t0)); S["drum"].rotation_euler = (base + 2 * math.pi * turns * (1 - (1 - k) ** 2), 0, 0)


def s_s00():                                   # 冒頭：書斎の抽選機が回り、金の玉が出て、金の赤ちゃんに
    stage("world"); spot("sp", (-2.6, -2.2, 5.0), (0, 0, 1.0), 1500, size=1.2, ang=.9, blend=.6); reflector("rf", (0, -12, 3), (0, 0, 1.0), 8, 650)
    lottery(); S["bb"] = baby("bb0", s=.5)


def a_s00(u, t, f):
    spin_drum(t, lbeat("s00", 0) - .3, lbeat("s00", 5), 3.2)
    t5, t6 = lbeat("s00", 5), lbeat("s00", 6)
    if t < t5 - .25:
        S["ball"].location = (0, 0, -50)
    elif t < t6:                                     # 胴の下から転がり出て、受け皿に落ちる
        u2 = clamp((t - (t5 - .25)) / .25); S["ball"].location = (0, -.3 - .32 * u2, .62 + .2 * (1 - u2 * u2) + .075 + .02 * hop(t, t5, 1, .2))
    else:
        S["ball"].location = (0, 0, -50)
    if t >= t6 - .02:                                # 玉が金の赤ちゃんに（受け皿の上で跳ねて大きくなる）
        k = spring(clamp((t - (t6 - .02)) / .35)); S["bb"].scale = (.5 * k, .5 * k, .5 * k); S["bb"].location = (0, -.62, .69 + bob("s00", t, (7, 8), .05))
    else:
        S["bb"].location = (0, 0, -50)
    go("s00", [(0, (-1.8, -2.8, 1.5), (0, 0, 1.0), 30), (3, (1.9, -2.6, 1.5), (0, -.2, .95), 30), (5, (.35, -1.7, .95), (0, -.62, .7), 42), (7, (0, -3.2, 1.3), (0, -.4, .9), 34)], t, 3.0)


# 白い赤ちゃんの群れ（19×10＝190 体、1 体だけ金）
GX, GY, GSP = 19, 10, .62
GOLD_IJ = (9, 2)


def s_s01():
    stage("world"); spot("sp", (0, -6, 9), (0, 1, 0), 3600, size=1.0, ang=1.1, blend=.5); reflector("rf", (0, -14, 5), (0, 1, 0), 10, 600)
    import random as _r
    R = _r.Random(64); pts = []
    for i in range(GX):
        for j in range(GY):
            if (i, j) == GOLD_IJ:
                continue
            pts.append(((i - (GX - 1) / 2) * GSP + R.uniform(-.06, .06), j * GSP - .6 + R.uniform(-.06, .06), R.uniform(-.5, .5)))
    crowd("crowd", pts, .62, ceramic())
    gx, gy = (GOLD_IJ[0] - (GX - 1) / 2) * GSP, GOLD_IJ[1] * GSP - .6; S["gp"] = (gx, gy)
    S["w"] = baby("wb", ceramic(), .62); S["bb"] = baby("gb", s=.62)
    S["gs"] = spot("gsp", (gx, gy - 1.2, 3.2), (gx, gy, .2), 0, (1, .85, .6), size=.3, ang=.45, blend=.6)


def a_s01(u, t, f):
    gx, gy = S["gp"]; k1 = pb("L01", 1); T = lbeat("s01", k1)
    if t < T:
        S["w"].location = (gx, gy, 0); S["bb"].location = (gx, gy, -50); S["gs"].data.energy = 0
    else:
        S["w"].location = (gx, gy, -50); S["bb"].location = (gx, gy, hop(t, T, .35, .4) + bob("s01", t, range(k1 + 1, k1 + 8), .05))
        S["gs"].data.energy = 900 * eio(clamp((t - T) / .3))
    go("s01", [(0, (0, -9.5, 6.5), (0, 2.0, 0), 28), (2, (-3.0, -7.0, 4.2), (0, 2.0, .2), 30), (k1, (gx + .9, gy - 2.0, 1.0), (gx, gy, .35), 40), (k1 + 3, (gx + 2.2, gy - 4.2, 2.4), (gx, gy + .6, .2), 32)], t, 3.0)


def s_s02():                                   # 同じ赤ちゃんを 4 つの国に：台座に国旗と国名、赤ちゃんが拍ごとに落ちる
    stage("world"); spot("sp", (0, -6, 7), (0, 0, .8), 3200, size=1.0, ang=1.1, blend=.5); reflector("rf", (0, -14, 3.5), (0, 0, 1.0), 12, 700)
    pedestals()


def a_s02(u, t, f):
    ks = [pb("L02", j) for j in range(1, 5)]
    dots_on([i for i in range(4) if t >= lbeat("s02", ks[i]) - .02])
    for i in range(4):
        drop(S["bb"][i], (PX[i], 0, .82), t, lbeat("s02", ks[i]), h=1.8)
        if t > lbeat("s02", ks[i]) + .3:
            S["bb"][i].location = (PX[i], 0, .82 + bob("s02", t, range(ks[i] + 2, ks[i] + 12, 2), .04))
    keys = [(0, (0, -9.5, 2.2), (0, 0, .9), 28)] + [(ks[i], (PX[i] + .9, -3.4, 1.5), (PX[i], 0, 1.0), 36) for i in range(4)] + [(ks[3] + 2, (0, -9.8, 2.0), (0, 0, .9), 28)]
    go("s02", keys, t, 3.2)


def life_set(env="world"):
    stage(env); spot("sp", (0, -6, 8), (0, .5, 1.6), 3400, size=1.0, ang=1.15, blend=.5); reflector("rf", (0, -14, 3.5), (0, 0, 1.8), 12, 750)
    pedestals(); pillar_set()
    for i in range(4):
        S["bb"][i].location = (PX[i], 0, .82)


def s_s03():                                   # 平均寿命の金の柱が拍ごとにせり上がる
    life_set()


def a_s03(u, t, f):
    ks = [pb("L03", j) for j in range(1, 5)]
    for i in range(4):
        T = lbeat("s03", ks[i]); set_pillar(i, grow(t, T, 0, CT[i][1] * LS) if t > T - .4 else 0, t, T)
        S["bb"][i].location = (PX[i], 0, .82 + bob("s03", t, (ks[i],), .06))
    keys = [(0, (0, -10.5, 1.6), (0, 0, 1.9), 28)] + [(ks[i], (PX[i] + (.9 if i < 3 else -.9), -4.2, 1.0), (PX[i], PY, CT[i][1] * LS * .6), 32) for i in range(4)] + [(ks[3] + 2, (0, -10.8, 1.4), (0, 0, 2.0), 28)]
    go("s03", keys, t, 3.4)


def s_s04():                                   # 差 約 29 年：チャドの柱の上に光る空白、日本の高さの線
    life_set()
    m = glow_mat("gapglow", (1, .72, .3), 1.6); S["gap"] = box("gap", (.62, .5, 1.0), (0, 0, 0), m, bevel=0)
    S["line"] = box("hline", (1, .03, .03), (0, 0, 0), glow_mat("lineglow", (1, .85, .5), 4.0), bevel=0)
    S["gl"] = label("gapl", "29年", (0, 0, -50), .34); ANIM.extend([S["gap"], S["line"], S["gl"]])


def a_s04(u, t, f):
    for i in range(4):
        set_pillar(i, CT[i][1] * LS)
    h0, h1 = CT[3][1] * LS, CT[0][1] * LS; k1 = pb("L04", 0, 1); T = lbeat("s04", k1)
    k = eio(clamp((t - (T - .35)) / .35)); x = PX[3]
    if k > 0:
        hh = (h1 - h0) * k; S["gap"].scale = (1, 1, hh); S["gap"].location = (x, PY, h0 + hh / 2)
        S["line"].scale = (PX[3] - PX[0] + .62, 1, 1); S["line"].location = ((PX[0] + PX[3]) / 2, PY - .27, h1); S["gl"].location = (x - 1.0, PY - .3, (h0 + h1) / 2)
    else:
        for o in (S["gap"], S["line"], S["gl"]):
            o.location = (0, 0, -50)
    k2 = pb("L04", 1)
    go("s04", [(0, (0, -10.5, 1.8), (0, 0, 2.0), 28), (k1, (x - 2.6, -5.0, 2.4), (x - .4, PY, h0 + .4), 32), (k2, (x - 1.4, -3.6, 3.2), (x - .3, PY, (h0 + h1) / 2), 36)], t, 3.4)


def s_s05():                                   # 5 歳まで：日本の 400 体（20×20）から 1 体、チャドの 10 体から 1 体が静かに沈む
    stage("garden", "veld"); spot("sp", (0, -6, 8), (0, .8, 0), 3200, size=1.0, ang=1.1, blend=.5); reflector("rf", (0, -14, 4), (0, 0, .5), 10, 650)
    sp, s = .2, .15; c = ceramic(); pts = []
    for i in range(20):
        for j in range(20):
            if (i, j) == (13, 6):
                continue
            pts.append((-2.6 + (i - 9.5) * sp, .8 + (j - 9.5) * sp * .9, 0))
    crowd("jp400", pts, s, c, "fig"); S["j1"] = mini("j1", (-2.6 + 3.5 * sp, .8 - 3.5 * sp * .9, 0), s, c); S["j1p"] = tuple(S["j1"].location)
    S["td"] = [mini("td%d" % i, (2.6 + (i - 4.5) * sp, .2, 0), s, c) for i in range(10)]
    label("l5j", "日本", (-2.6, 3.0, .3), .34); label("l5t", "チャド", (2.6, 1.0, .3), .34)


def a_s05(u, t, f):
    k1, k2 = pb("L05", 1), pb("L05", 2)
    use_env("garden" if t < lbeat("s05", k2) else "veld")            # 日本の話は日本庭園、チャドの話は乾いた大地（景色はイメージ）
    x, y, z = S["j1p"]; S["j1"].location = (x, y, -.4 * eio(clamp((t - lbeat("s05", k1 + 1)) / .7)))
    for i, o in enumerate(S["td"]):
        o.location = (2.6 + (i - 4.5) * .2, .2, -.4 * eio(clamp((t - lbeat("s05", k2 + 1)) / .7)) if i == 6 else bob("s05", t, (k2,), .03))
    go("s05", [(0, (-.4, -6.8, 1.5), (-1.2, 2.0, .2), 28), (k1, (-2.0, -1.6, 1.6), (x, y, .05), 40), (k2, (3.2, -1.6, .7), (2.6, .2, .12), 42), (k2 + 3, (2.2, -3.4, 1.4), (2.4, .2, .1), 34)], t, 3.0)


BOOKS = [(.15, .25, .45), (.5, .12, .1), (.12, .32, .2), (.55, .42, .15), (.3, .2, .4), (.6, .55, .45), (.1, .1, .12)]


def s_s06():                                   # 学ぶ年数：日本 14 冊、チャド 5 冊の本の山
    stage("garden2", "field"); spot("sp", (0, -5, 6), (0, 0, .7), 3000, size=.9, ang=1.0, blend=.5); reflector("rf", (0, -12, 3), (0, 0, .8), 8, 650)
    S["bk"] = {}
    for key, x, n in (("jp", -1.1, 14), ("td", 1.1, 5)):
        S["bk"][key] = []
        for j in range(n):
            o = box("bk%s%d" % (key, j), (.62 + .04 * ((j * 7) % 3), .44, .09), (0, 0, 0), plain("bookc%d" % (j % 7), BOOKS[j % 7], .5), bevel=.008); o.rotation_euler = (0, 0, (((j * 37) % 11) - 5) * .02)
            ANIM.append(o); S["bk"][key].append((o, (x, 0, .045 + j * .092)))
        parent(plane("bkf" + key, .42, .28, (0, -.36, .02), flag_mat(key), rot=(math.radians(-70) + math.pi / 2, 0, 0)), empty("bkfe" + key, (x, 0, 0)))
    S["n"] = {"jp": label("bkn_jp", "14年", (0, 0, -50), .26), "td": label("bkn_td", "5年", (0, 0, -50), .26)}; ANIM.extend(S["n"].values())


def a_s06(u, t, f):
    use_env("garden2" if t < lbeat("s06", pb("L06", 2)) else "field")  # 日本の話は日本庭園（別の向き）、チャドの話は乾いた野（景色はイメージ）
    for key, j0 in (("jp", pb("L06", 1)), ("td", pb("L06", 2))):
        T = lbeat("s06", j0); L = S["bk"][key]
        for j, (o, p) in enumerate(L):
            drop(o, p, t, T + j * .06, h=1.2, dur=.22)
        top = L[-1][1][2] + .3; T2 = T + len(L) * .06 + .1
        S["n"][key].location = (L[0][1][0], -.1, top + .1 * hop(t, T2, 1, .3)) if t > T2 - .1 else (0, 0, -50)
    k1, k2 = pb("L06", 1), pb("L06", 2)
    go("s06", [(0, (0, -5.4, 1.4), (0, 0, .7), 32), (k1, (-1.9, -3.0, 1.0), (-1.1, 0, .7), 34), (k2, (1.8, -2.9, .7), (1.1, 0, .3), 36), (k2 + 3, (0, -5.0, 1.6), (0, 0, .7), 30)], t, 3.2)


def coin(name, m):
    o = cyl(name, .2, .03, (0, 0, -50), m, 48, bevel=.004); ANIM.append(o); return o


def s_s07():                                   # 所得 約 40 倍：金貨 40 枚と 1 枚 → 365 日の暦のうち 9 日が金に
    stage("world"); spot("sp", (0, -6, 7), (0, 1.2, 1.2), 3400, size=1.0, ang=1.1, blend=.5); reflector("rf", (0, -14, 3.5), (0, 1, 1.4), 12, 700)
    g = gold_mat("gold", .13); S["cj"] = [coin("cj%d" % j, g) for j in range(40)]; S["ct"] = coin("ct", g)
    for key, x in (("jp", -.9), ("td", .9)):
        parent(plane("cf" + key, .36, .24, (0, -.4, .02), flag_mat(key), rot=(math.radians(-70) + math.pi / 2, 0, 0)), empty("cfe" + key, (x, 0, 0)))
    # 暦：25×15（365 日）、左上の 9 日が金に
    bm = bmesh.new(); S["cal"] = []; c = ceramic(); tw, gap = .15, .03
    for d in range(365):
        col, row = d % 25, d // 25; x = (col - 12) * (tw + gap); z = 3.2 - row * (tw + gap)
        if d < 9:
            S["cal"].append((x, z)); continue
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co.x = x + v.co.x * tw; v.co.y = 2.6 + v.co.y * .04; v.co.z = z + v.co.z * tw
    link(bpy.data.objects.new("cal", mesh_from_bm("cal", bm, [c], smooth=False)))
    box("calb2", (25 * (tw + gap) + .2, .05, 15 * (tw + gap) + .2), (0, 2.66, 3.2 - 7 * (tw + gap)), pbr_mat("panel2", "dark_wood", 1 / 1.5, (.45, .3, .2), 1.0, box_proj=True), bevel=.02)
    S["cw"] = [box("cw%d" % i, (tw, .04, tw), (x, 2.6, z), c, bevel=.004) for i, (x, z) in enumerate(S["cal"])]
    S["cg"] = [box("cg%d" % i, (tw, .06, tw), (x, 2.6, -50), g, bevel=.004) for i, (x, z) in enumerate(S["cal"])]; ANIM.extend(S["cw"] + S["cg"])
    label("l365", "365日", (0, 2.55, 3.55), .2)


def a_s07(u, t, f):
    T0 = lbeat("s07", 1)
    for j, o in enumerate(S["cj"]):
        drop(o, (-.9, 0, .015 + j * .031), t, T0 + j * .025, h=.9, dur=.18)
    drop(S["ct"], (.9, 0, .015), t, T0 + .3, h=.9, dur=.2)
    k1 = pb("L07", 1)
    for i, (x, z) in enumerate(S["cal"]):
        T = lbeat("s07", k1 + 1) + i * .07
        if t < T:
            S["cw"][i].location = (x, 2.6, z); S["cg"][i].location = (x, 2.6, -50)
        else:
            S["cw"][i].location = (x, 2.6, -50); S["cg"][i].location = (x, 2.6 - .25 * hop(t, T, 1, .35) - .05, z)
    cx, cz = S["cal"][4]
    go("s07", [(0, (0, -3.6, 1.0), (0, 0, .55), 32), (k1, (0, -5.2, 2.3), (0, 2.6, 2.0), 30), (k1 + 2, (cx + .4, -.8, cz - .1), (cx, 2.6, cz), 40), (k1 + 5, (0, -4.8, 2.2), (0, 2.6, 2.1), 30)], t, 3.4)


def s_s08():                                   # 同じ赤ちゃん：4 つの台座を横に流して見る
    stage("world"); spot("sp", (0, -6, 7), (0, 0, .8), 3200, size=1.0, ang=1.1, blend=.5); reflector("rf", (0, -14, 3.5), (0, 0, 1.0), 12, 700)
    pedestals()


def a_s08(u, t, f):
    for i in range(4):
        S["bb"][i].location = (PX[i], 0, .82 + bob("s08", t, range(0, 12), .045))
    k1 = pb("L08", 1)
    go("s08", [(0, (-5.0, -3.0, 1.3), (-2.2, 0, 1.0), 32), (k1, (0, -9.6, 1.7), (0, 0, .95), 28)], t, 3.2, mv=.6)


def s_s09():                                   # 100 年前の日本は約 43 年：日本の柱が縮み、チャドより低く（日本庭園）
    life_set("garden"); S["l43"] = label("l43", "43年", (0, 0, -50), .26); S["l1920"] = label("l1920", "1920年代", (0, 0, -50), .2); ANIM.extend([S["l43"], S["l1920"]])


def a_s09(u, t, f):
    k1, k2 = pb("L09", 1), pb("L09", 2); T = lbeat("s09", k1); h84, h43 = CT[0][1] * LS, 42.6 * LS
    for i in range(1, 4):
        set_pillar(i, CT[i][1] * LS)
    h = h84 if t < T - .5 else grow(t, T, h84, h43, .5); r, lb, le = S["pil"][0]
    set_pillar(0, h, t, None, S["l43"] if t >= T else lb)
    if t >= T:
        lb.location = (0, 0, -50); S["l1920"].location = (PX[0], PY - .3, h + .55)
    else:
        S["l43"].location = (0, 0, -50); S["l1920"].location = (0, 0, -50)
    go("s09", [(0, (0, -10.5, 1.8), (0, 0, 2.0), 28), (k1, (PX[0] + 1.6, -4.4, 1.6), (PX[0], PY, 1.6), 32), (k2, (0, -9.4, .7), (0, PY, 1.3), 30)], t, 3.4)


def s_s10():                                   # 同じ国でも時代で変わる：日本の柱が 1920 年代 → 1950 年ごろ → いま と伸びる（日本庭園）
    life_set("garden"); S["tags"] = []
    for i, (txt, le) in enumerate(PLAN["past"]):
        o = label("tag%d" % i, "%s %d年" % (txt, round(le)), (0, 0, -50), .17); ANIM.append(o); S["tags"].append((o, le))


def a_s10(u, t, f):
    for i in range(1, 4):
        set_pillar(i, CT[i][1] * LS)
    ks = [0, pb("L10", 0, 1), pb("L10", 1)]
    h = 42.6 * LS
    for j in range(1, 3):
        T = lbeat("s10", ks[j])
        if t > T - .4:
            h = grow(t, T, PLAN["past"][j - 1][1] * LS, PLAN["past"][j][1] * LS)
    set_pillar(0, h); S["pil"][0][1].location = (0, 0, -50)
    for j, (o, le) in enumerate(S["tags"]):
        T = lbeat("s10", ks[j]); o.location = (PX[0] + .95, PY - .3, le * LS) if (j == 0 or t >= T) else (0, 0, -50)
    go("s10", [(0, (PX[0] + 2.6, -3.0, 1.2), (PX[0] + .4, PY, 1.9), 30), (ks[2], (PX[0] + 3.2, -4.6, 2.4), (PX[0] + .4, PY, 2.6), 30), (ks[2] + 2, (0, -10.6, 1.8), (0, 0, 2.0), 28)], t, 3.4)


def s_s11():                                   # 最後：冒頭の抽選機と、受け皿の金の赤ちゃん（ゆっくり回る）
    s_s00()


def a_s11(u, t, f):
    spin_drum(t, 0, lbeat("s11", 8), 1.0)
    S["ball"].location = (0, 0, -50); S["bb"].scale = (.5, .5, .5); S["bb"].location = (0, -.62, .69 + bob("s11", t, range(0, 9, 2), .04))
    go("s11", [(0, (.3, -1.5, .95), (0, -.62, .75), 44), (2, (1.4, -2.6, 1.3), (0, -.4, .9), 34), (5, (0, -4.0, 1.6), (0, 0, 1.0), 30)], t, 3.0, mv=.6)


# ---------------------------------------------------------------- 書き出し
def _setup(k):
    def f():
        CUR[0] = k; S.clear(); globals()["s_" + k]()
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
