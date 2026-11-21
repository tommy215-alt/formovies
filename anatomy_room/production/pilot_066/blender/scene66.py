"""pilot_066「選ばれなかった子犬は、どこへ行く？」の 3D（Blender Cycles）。新ドパ設計 v2（065 の scene65.py の複製から）。
ショット＝セリフの行（s00〜s10）。夜のペットショップ → 繁殖場 → 2022 年の札 → 18 匹の子犬 → 役所の窓口 → 夜の河川敷（首輪だけ）→ 犬種の名札 → 暗い倉庫のケージ → 居間と殺処分の柱 → ヨーロッパの街の空のショーケース → ショーケースの明かりが消える。
犬・人は顔のない陶器の模型。事件の現場は直接映さない。動き・カメラの着地は表拍。閃光なし。
blender -b -P blender/scene66.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib66 import *  # noqa: F401,F403
from lib66 import _sc

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
          "garden2": ("ninomaru_teien_2k.hdr", "grass_ground", 1 / 2.5, (.75, .9, .65), 300, 1.0, 3.14, (400, (1, .95, .85)), (400, (1, .9, .75))),
          # 2026-11-20 v2：日本＝都会（ユーザーの指示）。インド＝田舎（garden・garden2）、チャド＝乾いた大地（veld・field）
          "city": (os.environ.get("CITY_HD", "canary_wharf") + "_2k.hdr", "concrete_floor_02", 1 / 2.0, (.8, .8, .8), 300, 1.0, 0.0, (400, (1, .95, .9)), (400, (.9, .95, 1))),
          "city2": (os.environ.get("CITY2_HD", "potsdamer_platz") + "_2k.hdr", "concrete_floor_02", 1 / 2.0, (.8, .8, .8), 300, 1.0, 0.0, (400, (1, .95, .9)), (400, (.9, .95, 1))),
          "city3": (os.environ.get("CITY3_HD", "modern_buildings_2") + "_2k.hdr", "concrete_floor_02", 1 / 2.0, (.8, .8, .8), 300, 1.0, 0.0, (400, (1, .95, .9)), (400, (.9, .95, 1)))}


def stage(*kinds):
    """舞台を 1 つ以上つくる。2 つ以上なら use_env() で場面の途中に切り替える（使わない方は床の下へ）"""
    clear_scene(); ANIM[:] = [cam.o]; HALL_DOTS.clear(); ENV.clear(); ENV_AT.clear(); FV.clear()
    for k in kinds:
        before = set(_sc().objects); _build_env(k); w = bpy.context.scene.world
        root = empty("env_" + k, (0, 0, 0))
        for o in _sc().objects:
            if o not in before and o is not root and o.parent is None:
                parent(o, root)
        ENV[k] = {"w": w, "root": root, "key": (KEY.data.energy, tuple(KEY.data.color)), "rim": (RIM.data.energy, tuple(RIM.data.color))}
        ANIM.append(root)
    use_env(kinds[0])


ENV_AT = {}                                     # コマ番号 → 舞台（world と灯りの強さは keyframe にならないので、描く直前に切り替える）
CURF = [None]


FV = {}                                         # コマ番号 → {名前: (入れる関数, 値)}（灯りの強さ・光る材質など keyframe にならない値）


def setv(key, fn, val):
    fn(val)
    if CURF[0] is not None:
        FV.setdefault(CURF[0], {})[key] = (fn, val)


def _env_handler(scene, *_):
    k = ENV_AT.get(scene.frame_current - 1)
    if k is not None and k in ENV:
        _apply_env(k)
    for fn, val in FV.get(scene.frame_current - 1, {}).values():
        fn(val)


bpy.app.handlers.frame_change_pre.append(_env_handler)


def use_env(k):
    if CURF[0] is not None:
        ENV_AT[CURF[0]] = k
    _apply_env(k)


def _apply_env(k):
    e = ENV[k]; bpy.context.scene.world = e["w"]
    KEY.data.energy, KEY.data.color = e["key"]; RIM.data.energy, RIM.data.color = e["rim"]
    for kk, ee in ENV.items():
        ee["root"].location = (0, 0, 0) if kk == k else (0, 0, -300)


def dots_on(which):
    """世界地図の国の灯り（0 日本・1 インド・2 チャド）。which に入っていない灯りは消す"""
    for i in range(len(CT)):
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
        for lon, lat in ((139.7, 35.7), (78.9, 21.0), (18.7, 15.5)):       # 日本・インド・チャド（v2 でアメリカを外した）
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


# ---------------------------------------------------------------- pilot_065：2013 年まで、選挙に行けなかった日本人
LINES_J = json.load(open(os.path.join(HERE, "..", "lines.json"), encoding="utf-8"))["lines"]
TLL = {x["id"]: x for x in TL["lines"]}


def pb(lid, j, off=0):
    """字幕の句 j が出る拍（場面の拍 0 から数えて）。renderer.html の phrases() と同じ計算"""
    ln = next(x for x in LINES_J if x["id"] == lid); L = TLL[lid]; tot = len("".join(ln["sub"])); acc = len("".join(ln["sub"][:j]))
    a = round((L["start"] + (L["end"] - L["start"]) * acc / tot - .05) / BP); return a - round(CUE[ln["scene"]] / BP) + off


def bm_ball(bm, c, r, sc=(1, 1, 1), seg=12, ring=8, mi=0):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=r)
    for v in res["verts"]:
        v.co.x = c[0] + v.co.x * sc[0]; v.co.y = c[1] + v.co.y * sc[1]; v.co.z = c[2] + v.co.z * sc[2]
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mi


def crowd(name, pts, s, m):
    """たくさんの人形を 1 つのメッシュに（物の数を増やさない）。pts：(x, y, rz)"""
    import numpy as np
    tb = bmesh.new()
    for c, r, sc in [((0, 0, .4), .3, (.85, .7, 1.35)), ((0, 0, 1.0), .17, (1, 1, 1))]:
        bm_ball(tb, c, r, sc, 16, 10)
    tb.verts.index_update(); V = np.array([v.co[:] for v in tb.verts]) * s; F = [[v.index for v in f.verts] for f in tb.faces]; tb.free()
    nv = len(V); AV, AF = [], []
    for k, (x, y, rz) in enumerate(pts):
        cr, sr = math.cos(rz), math.sin(rz)
        AV.append(np.stack([V[:, 0] * cr - V[:, 1] * sr + x, V[:, 0] * sr + V[:, 1] * cr + y, V[:, 2]], 1)); AF.extend([[i + k * nv for i in fc] for fc in F])
    me = bpy.data.meshes.new(name); me.from_pydata(np.concatenate(AV).tolist(), [], AF); me.materials.append(m)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); o = bpy.data.objects.new(name, me); return link(o)


def dark_text(name, txt, loc, size, rot=(math.pi / 2, 0, 0), col=(.06, .05, .04), extrude=.006):
    return text_obj(name, txt, loc, size, plain("ink_%g" % col[0], col, .6), rot=rot, extrude=extrude, font="BIZUDPGothic-Bold.ttf")


def paper():
    return plain("paper", (.93, .92, .87), .7)


def her(name="her", loc=(0, 0, 0), rz=0.0, s=1.15):
    return fig(name, loc, s, goldfig(), rz)


def walk(o, p0, p1, t, t0, t1, step=.05, rz=None):
    """t0〜t1 に p0 → p1 へ歩く（拍ごとに小さく弾む）"""
    u = clamp((t - t0) / max(1e-3, t1 - t0)); p = vlerp(p0, p1, u)
    hopz = step * abs(math.sin(math.pi * (t - t0) / BP)) if 0 < u < 1 else 0.0
    o.location = (p[0], p[1], p[2] + hopz)
    if rz is not None:
        o.rotation_euler = (0, 0, rz)


def ticket(name, m=None, gold=False):
    """選挙のはがき（投票所の入場券）：はがきの大きさ 14.8×10cm、上に色の帯と、見出しの線"""
    root = empty(name, (0, 0, -50))
    parent(box(name + "_p", (.148, .1, .0025), (0, 0, 0), gold_mat("goldcard", .2) if gold else (m or paper()), bevel=.0005), root)
    if not gold:
        parent(box(name + "_b", (.148, .022, .0027), (0, .035, 0), plain("tkband", (.18, .45, .32), .6), bevel=0), root)
        for k in range(3):
            parent(box(name + "_l%d" % k, (.09 - .02 * k, .004, .0027), (-.02 + .01 * k, .005 - .016 * k, 0), plain("tkline", (.45, .45, .42), .7), bevel=0), root)
    ANIM.append(root); return root


def door_set(name, loc=(0, 0, 0), wall=True):
    """投票所の入口：薄い色の壁に両開きの扉（蝶番で回る）。扉は S[name+"_L"]・S[name+"_R"]（rz で開く）"""
    root = empty(name, loc); wl = plain("wallc", (.78, .76, .7), .8); st = plain("doorsteel", (.62, .64, .63), .35, metal=.6); gl = glass_mat()
    W2, H2 = 1.0, 2.2
    if wall:
        for sx in (-1, 1):
            parent(box(name + "_w%d" % sx, (3.4, .25, 3.2), (sx * (W2 + 1.7), 0, 1.6), wl, bevel=.01), root)
        parent(box(name + "_wt", (2 * W2, .25, 1.0), (0, 0, H2 + .5), wl, bevel=.01), root)
        parent(box(name + "_fr", (2 * W2 + .16, .3, .08), (0, 0, H2 + .04), st, bevel=.01), root)
    for side, sx in (("L", -1), ("R", 1)):
        hg = parent(empty(name + "_" + side, (sx * W2, 0, 0)), root)
        parent(box(name + "_d" + side, (W2 - .02, .06, H2), (-sx * W2 / 2, 0, H2 / 2), st, bevel=.01), hg)
        parent(box(name + "_g" + side, (.36, .065, .7), (-sx * W2 / 2, 0, 1.45), gl, bevel=.005), hg)
        parent(box(name + "_h" + side, (.04, .1, .32), (-sx * (W2 - .14), -.05, 1.0), gold_mat("brassl", .3, (.86, .62, .3)), bevel=.005), hg)
        S[name + "_" + side] = hg; ANIM.append(hg)
    # 「投票所」の札（木の板に黒い字）
    pl = parent(box(name + "_sign", (1.3, .06, .42), (0, -.16, H2 + .5), pbr_mat("plank", "wood_floor", 1.0, (1, .92, .8), 1.0, box_proj=True), bevel=.01), root)
    parent(dark_text(name + "_st", "投票所", (0, -.2, H2 + .5), .26), root)
    ANIM.append(root); return root


def set_doors(name, k):
    """k：0 閉 → 1 全開（内側へ 80°）"""
    S[name + "_L"].rotation_euler = (0, 0, math.radians(80) * k); S[name + "_R"].rotation_euler = (0, 0, -math.radians(80) * k)


def hall_inside(name, y0=1.2):
    """扉の向こう：記載台（白い仕切りの台）と、アルミの投票箱"""
    root = empty(name, (0, y0, 0)); wh = plain("booth", (.92, .92, .9), .5); al = plain("alu", (.78, .79, .8), .25, metal=1.0)
    for i, x in enumerate((-1.6, -.8, .8, 1.6)):
        parent(box(name + "_t%d" % i, (.7, .5, .05), (x, 1.8, .95), wh, bevel=.005), root)
        for sx in (-1, 1):
            parent(box(name + "_s%d%d" % (i, sx), (.03, .5, .5), (x + sx * .35, 1.8, 1.22), wh, bevel=.003), root)
        parent(box(name + "_l%d" % i, (.04, .04, .95), (x, 1.95, .47), wh, bevel=.002), root)
    bx = parent(box(name + "_box", (.55, .42, .6), (0, .9, .3 + .5), al, bevel=.01), root)
    parent(box(name + "_slot", (.22, .025, .02), (0, .9, 1.105), plain("slot", (.02, .02, .02), .5), bevel=0), root)
    parent(box(name + "_tbl", (.8, .6, .5), (0, .9, .25), plain("tblc", (.25, .22, .2), .6), bevel=.01), root)
    parent(dark_text(name + "_bt", "投票箱", (0, .9 - .215, .85), .08), root)
    return root


def chabudai(name, loc):
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.55, .38, .26), 1.0, box_proj=True); root = empty(name, loc)
    parent(cyl(name + "_t", .55, .04, (0, 0, .34), wd, 64, bevel=.006), root)
    for a in range(4):
        x, y = .32 * math.cos(a * math.pi / 2 + .78), .32 * math.sin(a * math.pi / 2 + .78)
        parent(box(name + "_l%d" % a, (.05, .05, .32), (x, y, .16), wd, bevel=.004), root)
    return root


def gazette(name, loc, rz=0.0):
    """選挙公報：机の上に広げた紙（見出しと候補者の枠の線）"""
    root = empty(name, loc); root.rotation_euler = (0, 0, rz)
    parent(box(name + "_p", (.42, .3, .002), (0, 0, 0), paper(), bevel=0), root)
    parent(dark_text(name + "_h", "選挙公報", (0, .1, .003), .045, rot=(0, 0, 0)), root)
    for i in range(4):
        parent(box(name + "_f%d" % i, (.085, .14, .0024), (-.15 + i * .1, -.04, 0), plain("gzframe", (.8, .78, .72), .7), bevel=0), root)
    return root


def mailbox(name, loc):
    """郵便受け：柱の上の箱（前が開いていて、中の受け皿が見える）"""
    root = empty(name, loc); bk = plain("mbox", (.12, .14, .16), .4, coat=.4); post = plain("mpost", (.25, .22, .2), .5)
    parent(box(name + "_post", (.08, .08, 1.0), (0, 0, .5), post, bevel=.005), root)
    parent(box(name + "_bot", (.5, .32, .02), (0, 0, 1.01), bk, bevel=.003), root)
    parent(box(name + "_back", (.5, .02, .36), (0, .15, 1.19), bk, bevel=.003), root)
    for sx in (-1, 1):
        parent(box(name + "_side%d" % sx, (.02, .32, .36), (sx * .24, 0, 1.19), bk, bevel=.003), root)
    parent(box(name + "_top", (.54, .36, .025), (0, 0, 1.38), bk, bevel=.004), root)
    parent(box(name + "_lip", (.5, .02, .05), (0, -.15, 1.035), bk, bevel=.003), root)
    parent(dark_text(name + "_n", "郵便", (0, -.155, 1.3), .06, col=(.85, .8, .7)), root)
    return root


def outline_card(name, loc):
    """来ないはがきの形：金の細い線の枠"""
    root = empty(name, loc); g = glow_mat("outl", (1, .78, .4), 3.0); w, d, t = .148, .1, .004
    for (x, y, sx, sy) in ((0, d / 2, w, t), (0, -d / 2, w, t), (w / 2, 0, t, d), (-w / 2, 0, t, d)):
        parent(box(name + "_%g%g" % (x, y), (sx, sy, .002), (x, y, 0), g, bevel=0), root)
    ANIM.append(root); return root


def tablet(name):
    """条文の石板（公職選挙法 第11条）"""
    st = pbr_mat("stone", "brushed_concrete", 1 / 1.5, (.72, .7, .66), 1.0, box_proj=True); root = empty(name, (0, 0, -50))
    parent(box(name + "_s", (2.2, .3, 1.5), (0, 0, .75), st, bevel=.04), root)
    ink = (.04, .035, .03)
    parent(dark_text(name + "_t0", "公職選挙法 第11条", (0, -.16, 1.25), .13, col=ink), root)
    parent(box(name + "_ln", (1.7, .01, .012), (0, -.155, 1.12), plain("ink_ln", ink, .6), bevel=0), root)
    parent(dark_text(name + "_t1", "成年被後見人は", (0, -.16, .86), .2, col=ink), root)
    parent(dark_text(name + "_t2", "選挙権を有しない", (0, -.16, .48), .2, col=ink), root)
    ANIM.append(root); return root


def calculator(name):
    root = empty(name, (0, 0, -50)); bd = plain("calc", (.12, .12, .13), .4, coat=.3)
    parent(box(name + "_b", (.5, .7, .08), (0, 0, .04), bd, bevel=.02), root)
    parent(box(name + "_sc", (.4, .16, .01), (0, .22, .085), plain("lcd", (.55, .62, .5), .3), bevel=.003), root)
    kb = plain("key", (.85, .84, .8), .45)
    for i in range(4):
        for j in range(4):
            parent(box(name + "_k%d%d" % (i, j), (.08, .07, .025), (-.15 + i * .1, .07 - j * .1, .09), kb, bevel=.006), root)
    ANIM.append(root); return root


def ballot(name, gold=False):
    root = empty(name, (0, 0, -50)); m = gold_mat("goldcard", .2) if gold else paper()
    parent(box(name + "_p", (.3, .42, .004), (0, 0, 0), m, bevel=.001), root)
    if not gold:
        parent(dark_text(name + "_t", "投票用紙", (0, .14, .004), .05, rot=(0, 0, 0)), root)
        parent(box(name + "_w", (.2, .2, .0045), (0, -.04, 0), plain("blank", (.98, .98, .96), .7), bevel=0), root)
    ANIM.append(root); return root


# ---------------------------------------------------------------- 景色（Poly Haven の CC0 の HDRI）
OUTENV.update({
    "lounge": ("lythwood_lounge_2k.hdr", "wood_floor", 1 / 1.6, (1, .9, .78), 9, 1.0, 0.0, (450, (1, .9, .78)), (300, (1, .85, .7))),
    "suburb": ("stuttgart_suburbs_2k.hdr", "asphalt_02", 1 / 2.0, (.8, .8, .8), 300, 1.0, 0.0, (500, (1, .95, .88)), (400, (.9, .95, 1))),
    "yard": ("courtyard_2k.hdr", "concrete_floor_02", 1 / 2.0, (.85, .83, .8), 300, 1.0, 0.0, (450, (1, .95, .88)), (400, (.9, .95, 1))),
    "rotunda": ("sepulchral_chapel_rotunda_2k.hdr", "marble_01", 1 / 2.0, (.9, .88, .84), 9, 1.0, 0.0, (500, (1, .93, .85)), (400, (1, .9, .8))),
    "hall": ("large_corridor_2k.hdr", "marble_01", 1 / 2.0, (.85, .83, .8), 9, 1.0, 3.14, (600, (1, .93, .85)), (450, (1, .9, .8))),   # 役所のような石の廊下（条文の石板）
    "lounge2": ("lythwood_lounge_2k.hdr", "wood_floor", 1 / 1.6, (1, .9, .78), 9, 1.0, 4.71, (450, (1, .9, .78)), (300, (1, .85, .7))),   # 天秤の場面（家具と重ならない向き）
    "poll": ("school_hall_2k.hdr", "wood_floor", 1 / 1.6, (1, .9, .78), 9, 1.0, 0.0, (500, (1, .93, .82)), (350, (1, .88, .74))),
})


def court_env():
    """法廷：木の壁、高い裁判官席（3 席）、手前に証言台。床は濃い木"""
    wd = pbr_mat("panel", "dark_wood", 1 / 1.5, (.55, .38, .26), 1.0, box_proj=True); fl = pbr_mat("court", "wood_floor", 1 / 1.6, (.7, .55, .42), 1.0, box_proj=True)
    plane("floor", 40, 40, (0, 0, 0), fl); plane("backw", 30, 10, (0, 4.2, 5), wd, rot=(math.pi / 2, 0, 0))
    for sx in (-1, 1):
        plane("sidew%d" % sx, 20, 10, (sx * 7, 0, 5), wd, rot=(math.pi / 2, 0, math.pi / 2))
    box("bench_dais", (6.4, 1.4, .5), (0, 3.0, .25), wd, bevel=.02); box("bench", (6.0, .5, 1.2), (0, 2.5, 1.1), wd, bevel=.03)
    box("bench_top", (6.2, .7, .06), (0, 2.6, 1.72), pbr_mat("plinth", "dark_wood", 1.0, (.42, .3, .22), 1.0, box_proj=True), bevel=.01)
    blk = plain("robe", (.05, .05, .06), .6)
    for x in (-1.6, 0, 1.6):                  # 裁判官の椅子の背（高い）
        box("chair%g" % x, (.7, .12, 1.4), (x, 3.3, 1.6), plain("chairl", (.25, .12, .08), .4, coat=.3), bevel=.04)
        f = figure("judge%g" % x, (x, 2.95, .75), 1.3, blk)
    box("witness", (.9, .5, 1.0), (0, -.6, .5), wd, bevel=.02)
    for x in (-4.5, 4.5):                     # 左右の席
        box("table%g" % x, (2.2, .8, .75), (x, .8, .375), wd, bevel=.02)
    lights((1300, (1, .9, .78)), (900, (1, .82, .62)), "brown_photostudio_02_2k.hdr", .9)


_prev_build = _build_env


def _build_env(kind):
    if kind == "court":
        court_env()
    else:
        _prev_build(kind)


# ---------------------------------------------------------------- 場面（066：選ばれなかった子犬は、どこへ行く？）
# 犬は顔のない陶器の模型（子犬は頭が大きい）。事件の現場は直接映さない（首輪と影だけ）。閃光なし
DOG = [((0, 0, .34), .26, (1.0, 1.55, .78)), ((0, -.36, .55), .19, (1, 1, 1)), ((0, -.52, .5), .08, (1, 1.3, .8)),
       ((-.13, -.33, .7), .07, (.6, .5, 1.3)), ((.13, -.33, .7), .07, (.6, .5, 1.3)),
       ((-.13, -.22, .14), .065, (1, 1, 2.0)), ((.13, -.22, .14), .065, (1, 1, 2.0)), ((-.13, .25, .14), .065, (1, 1, 2.0)), ((.13, .25, .14), .065, (1, 1, 2.0)),
       ((0, .42, .5), .05, (1, 1, 2.2))]
PUP = [((0, 0, .3), .24, (1.0, 1.3, .85)), ((0, -.3, .56), .23, (1, 1, 1)), ((0, -.49, .5), .08, (1, 1.2, .8)),
       ((-.16, -.27, .74), .075, (.6, .5, 1.2)), ((.16, -.27, .74), .075, (.6, .5, 1.2)),
       ((-.12, -.18, .1), .06, (1, 1, 1.6)), ((.12, -.18, .1), .06, (1, 1, 1.6)), ((-.12, .2, .1), .06, (1, 1, 1.6)), ((.12, .2, .1), .06, (1, 1, 1.6)),
       ((0, .35, .42), .045, (1, 1, 1.8))]


def dog_mesh(name, parts, s, m, loc=(0, 0, 0), rz=0.0):
    bm = bmesh.new()
    for c, r, sc in parts:
        bm_ball(bm, (c[0] * s, c[1] * s, c[2] * s), r * s, sc, 24, 14)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m])); o.location = loc; o.rotation_euler = (0, 0, rz); link(o); ANIM.append(o); return o


def dogs(name, pts, parts, s, m):
    """たくさんの犬を 1 つのメッシュに（pts：(x, y, z, rz)）"""
    import numpy as np
    tb = bmesh.new()
    for c, r, sc in parts:
        bm_ball(tb, c, r, sc, 12, 8)
    tb.verts.index_update(); V = np.array([v.co[:] for v in tb.verts]) * s; F = [[v.index for v in f.verts] for f in tb.faces]; tb.free()
    nv = len(V); AV, AF = [], []
    for k, (x, y, z, rz) in enumerate(pts):
        cr, sr = math.cos(rz), math.sin(rz)
        AV.append(np.stack([V[:, 0] * cr - V[:, 1] * sr + x, V[:, 0] * sr + V[:, 1] * cr + y, V[:, 2] + z], 1)); AF.extend([[i + k * nv for i in fc] for fc in F])
    me = bpy.data.meshes.new(name); me.from_pydata(np.concatenate(AV).tolist(), [], AF); me.materials.append(m)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons)); o = bpy.data.objects.new(name, me); return link(o)


def pup_mat():
    return plain("pupc", (.9, .86, .8), .45, coat=.4)


def cages(name, cells, w=.9, d=.7, h=.7, wire=.012, m=None):
    """針金のケージ（たくさんを 1 つのメッシュに）。cells：(x, y, z) の下の中心。縦の針金 9 本・横の枠"""
    m = m or plain("wire", (.62, .63, .64), .35, metal=.8); bm = bmesh.new()
    def bar(cx, cy, cz, sx, sy, sz):
        r = bmesh.ops.create_cube(bm, size=1.0)
        for v in r["verts"]:
            v.co.x = cx + v.co.x * sx; v.co.y = cy + v.co.y * sy; v.co.z = cz + v.co.z * sz
    for (x, y, z) in cells:
        for zz in (z, z + h):
            bar(x, y - d / 2, zz, w, wire, wire); bar(x, y + d / 2, zz, w, wire, wire); bar(x - w / 2, y, zz, wire, d, wire); bar(x + w / 2, y, zz, wire, d, wire)
        for k in range(10):
            xx = x - w / 2 + w * k / 9; bar(xx, y - d / 2, z + h / 2, wire, wire, h); bar(xx, y + d / 2, z + h / 2, wire, wire, h)
        for k in range(1, 7):
            yy = y - d / 2 + d * k / 7; bar(x - w / 2, yy, z + h / 2, wire, wire, h); bar(x + w / 2, yy, z + h / 2, wire, wire, h)
        bar(x, y, z + .01, w, d, .02)
    o = bpy.data.objects.new(name, mesh_from_bm(name, bm, [m], smooth=False)); return link(o)


def showcase(name, loc, lit=True, pup=True):
    """ペットショップのショーケース：白い枠のガラスの箱、中に暖かい灯りと子犬"""
    root = empty(name, loc); wh = plain("scframe", (.92, .92, .9), .35, coat=.4)
    W, D, H = 1.0, .8, .8
    parent(box(name + "_floor", (W, D, .04), (0, 0, .02), plain("scfloor", (.85, .8, .7), .6), bevel=.004), root)
    parent(box(name + "_back", (W, .03, H), (0, D / 2, H / 2), plain("scback", (.55, .5, .45), .6), bevel=.004), root)
    for sx in (-1, 1):
        parent(box(name + "_side%d" % sx, (.03, D, H), (sx * W / 2, 0, H / 2), wh, bevel=.004), root)
    parent(box(name + "_top", (W + .03, D, .03), (0, 0, H), wh, bevel=.004), root)
    parent(box(name + "_glass", (W, .01, H), (0, -D / 2, H / 2), glass_mat(), bevel=0), root)
    em = glow_mat("scglow_" + name, (1, .86, .62), .7)
    g = parent(box(name + "_lamp", (W * .8, .1, .02), (0, 0, H - .03), em, bevel=0), root)
    l = bpy.data.lights.new(name + "_l", "POINT"); l.energy = 8 if lit else 0; l.color = (1, .85, .62); l.shadow_soft_size = .3
    lo = bpy.data.objects.new(name + "_l", l); lo.location = (0, -.3, H - .06); link(lo); parent(lo, root)
    p = dog_mesh(name + "_pup", PUP, .55, pup_mat(), (0, .05, .04), 0.0) if pup else None
    if p:
        parent(p, root); p.location = (0, .05, .04)
    S[name] = {"root": root, "light": l, "lamp": g, "pup": p, "em": em}; return root


def shop_set(lit_all=True):
    stage("shop"); reflector("rf", (0, -10, 2.5), (0, 0, 1.2), 8, 300)
    S["sc"] = []
    for r in range(3):
        for c in range(4):
            nm = "sc%d%d" % (r, c); showcase(nm, ((c - 1.5) * 1.06, 0, .45 + r * .86)); S["sc"].append(nm)
    box("shelfbase", (4.4, .9, .45), (0, 0, .225), plain("shelfb", (.2, .18, .17), .5), bevel=.01)


def set_lamp(nm, k):
    d = S[nm]
    setv(nm + "_l", lambda v, d=d: setattr(d["light"], "energy", v), 8 * k)
    setv(nm + "_e", lambda v, d=d: setattr(d["em"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"], "default_value", v), .7 * k)


def year_plate(name, txt, loc):
    root = empty(name, (0, 0, -50)); parent(box(name + "_b", (1.2, .06, .44), (0, 0, 0), pbr_mat("plank", "wood_floor", 1.0, (1, .92, .8), 1.0, box_proj=True), bevel=.012), root)
    parent(dark_text(name + "_t", txt, (0, -.035, 0), .26), root); ANIM.append(root); return root


OUTENV.update({
    "shop": ("phone_shop_2k.hdr", "floor_tiles_06", 1 / 2.0, (.6, .58, .56), 9, .35, 0.0, (250, (1, .9, .78)), (200, (1, .85, .7))),
    "kennel": ("workshop_2k.hdr", "brushed_concrete", 1 / 2.0, (.62, .62, .6), 9, .8, 0.0, (450, (.92, .97, 1)), (300, (.9, .95, 1))),
    "lobby": ("st_fagans_interior_2k.hdr", "wood_floor", 1 / 1.6, (.9, .85, .78), 9, 1.0, 0.0, (450, (1, .93, .85)), (350, (1, .9, .8))),
    "night": ("kloppenheim_07_2k.hdr", "grass_ground", 1 / 2.5, (.45, .5, .45), 300, 1.2, 0.0, (120, (.7, .8, 1)), (200, (.7, .8, 1))),
    "plant": ("peppermint_powerplant_2k.hdr", "brushed_concrete", 1 / 2.0, (.5, .5, .5), 9, .45, 0.0, (200, (.85, .9, 1)), (200, (.85, .9, 1))),
    "street": ("modern_evening_street_2k.hdr", "asphalt_02", 1 / 2.0, (.7, .7, .7), 300, 1.0, 0.0, (300, (1, .9, .8)), (300, (.8, .9, 1))),
})


def s_s00():                                   # 冒頭：夜のペットショップ。明るいショーケースの列に子犬
    shop_set()


def a_s00(u, t, f):
    for i, nm in enumerate(S["sc"]):
        p = S[nm]["pup"]
        if p:
            p.location = (0, .05, .04 + bob("s00", t, range(i % 2, 9, 2), .02))
    go("s00", [(0, (-2.6, -4.2, 1.6), (0, 0, 1.4), 30), (3, (1.4, -3.0, 1.2), (.5, 0, 1.3), 34), (6, (.55, -2.3, 1.38), (.53, .1, 1.32), 38)], t, 3.0, mv=.6)


def s_s01():                                   # 繁殖場：蛍光灯の下のケージの列、母犬、6 つの印
    stage("kennel"); reflector("rf", (0, -10, 3), (0, 0, .8), 8, 500); spot("sp", (0, -2.5, 4.5), (0, .3, .4), 1500, (.95, .98, 1), size=.8, ang=.9, blend=.6)
    cells = [((c - 2) * 1.0, 1.2 + r * .0, z) for c in range(5) for r in range(1) for z in (0, .75)] + [((c - 2) * 1.0, -.1, 0) for c in (0, 4)]
    cages("cg", cells)
    S["mom"] = dog_mesh("mom", DOG, .85, ceramic(), (0, .1, 0), 0.0)
    S["pups"] = dogs("pups", [(-.35 + .18 * k, -.25 + .05 * (k % 2), 0, .3 * (k - 1.5)) for k in range(4)], PUP, .32, pup_mat())
    g = gold_mat("gold", .15); S["dots"] = [sphere("dot%d" % k, .06, (0, 0, -50), g, 32) for k in range(6)]; ANIM.extend(S["dots"])


def a_s01(u, t, f):
    k1 = pb("L01", 1)
    for k, o in enumerate(S["dots"]):
        T = lbeat("s01", k1) + k * BP / 2
        o.location = ((k - 2.5) * .2, .1, 1.25 + hop(t, T, .12, .3)) if t >= T - .05 else (0, 0, -50)
    go("s01", [(0, (2.6, -3.6, 1.8), (0, .6, .6), 28), (2, (-1.2, -2.4, 1.0), (0, .2, .5), 32), (k1, (.3, -2.2, 1.1), (0, .1, .9), 36)], t, 3.0)


def s_s02():                                   # 「2022年」の札が母犬の前に落ちる
    s_s01(); S["yp"] = year_plate("yp", "2022年", (0, 0, 0))


def a_s02(u, t, f):
    for k, o in enumerate(S["dots"]):
        o.location = ((k - 2.5) * .2, .1, 1.25)
    k1 = pb("L02", 1); drop(S["yp"], (0, -.55, .9), t, lbeat("s02", k1), h=1.2, dur=.3)
    go("s02", [(0, (.3, -2.4, 1.1), (0, .1, .9), 34), (k1, (0, -3.4, 1.05), (0, -.3, .9), 32)], t, 3.0)


def s_s03():                                   # 18 匹の子犬が台の上に 2 列。1 匹の灯りがゆっくり消え、沈む
    stage("kennel"); reflector("rf", (0, -10, 3), (0, 0, .8), 8, 500)
    box("table", (4.2, 1.4, .8), (0, .2, .4), plain("tablec", (.75, .76, .78), .3, metal=.6), bevel=.01)
    pts = []
    for r in range(2):
        for c in range(9):
            if (r, c) == (0, 6):
                continue
            pts.append(((c - 4) * .42, -.1 + r * .5, .8, .15 * ((c * 7 + r) % 3 - 1)))
    dogs("row", pts, PUP, .34, pup_mat())
    S["one"] = dog_mesh("one", PUP, .34, pup_mat(), (2 * .42, -.1, .8), 0.0)
    S["osp"] = spot("osp", (2 * .42, -.9, 2.4), (2 * .42, -.1, .9), 400, (1, .9, .75), size=.2, ang=.35, blend=.5)


def a_s03(u, t, f):
    k2 = pb("L03", 2); T = lbeat("s03", k2)
    e = eio(clamp((t - T) / 1.2)); S["one"].location = (2 * .42, -.1, .8 - .4 * e); setv("osp", lambda v: setattr(S["osp"].data, "energy", v), 400 * (1 - e))
    go("s03", [(0, (0, -4.2, 2.0), (0, .1, .9), 28), (pb("L03", 1), (-1.6, -2.6, 1.4), (0, 0, .9), 30), (k2, (1.2, -1.6, 1.15), (.84, -.1, .9), 38)], t, 3.0)


def s_s04():                                   # 役所の窓口：犬の入ったキャリーが置かれ、シャッターが下りる
    stage("lobby"); reflector("rf", (0, -10, 3), (0, 0, 1.0), 8, 500)
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.55, .38, .26), 1.0, box_proj=True)
    box("counter", (3.0, .7, 1.05), (0, .4, .525), wd, bevel=.02); box("ctop", (3.1, .8, .05), (0, .4, 1.07), plain("ctopc", (.9, .88, .84), .4), bevel=.01)
    box("wall", (6, .2, 3.0), (0, 1.2, 1.5), plain("wallc", (.82, .8, .76), .8), bevel=.01)
    box("win", (1.6, .21, 1.1), (0, 1.2, 1.75), plain("winhole", (.08, .08, .09), .6), bevel=0)
    S["sh"] = box("shutter", (1.6, .05, 1.1), (0, 1.08, 1.75 + 1.1), plain("shut", (.7, .71, .72), .35, metal=.7), bevel=.004); ANIM.append(S["sh"])
    dark_text("wsign", "動物の引取り", (0, 1.08, 2.55), .14)
    cr = empty("carrier", (0, 0, -50)); parent(box("cr_b", (.6, .4, .4), (0, 0, .2), plain("crb", (.55, .62, .7), .5), bevel=.04), cr)
    parent(box("cr_d", (.012, .3, .3), (-.3, 0, .2), plain("wire", (.62, .63, .64), .35, metal=.8), bevel=0), cr)
    parent(dog_mesh("crp", PUP, .32, pup_mat(), (-.05, 0, .03), math.pi / 2), cr); ANIM.append(cr); S["cr"] = cr


def a_s04(u, t, f):
    k1, k2 = pb("L04", 1), pb("L04", 2); drop(S["cr"], (.2, .3, 1.1), t, lbeat("s04", k1), h=.6, dur=.25, rz=.2)
    T = lbeat("s04", k2); S["sh"].location = (0, 1.08, 1.75 + 1.1 * (1 - eio(clamp((t - (T - .6)) / .6))))
    go("s04", [(0, (0, -4.6, 1.8), (0, 1.0, 1.4), 28), (k1, (1.4, -2.2, 1.6), (.2, .4, 1.3), 34), (k2, (-.6, -1.8, 1.5), (0, 1.1, 1.6), 34)], t, 3.0)


def s_s05():                                   # 夜の河川敷：草の上に首輪だけが点々と（月明かり）
    stage("night"); reflector("rf", (0, -10, 2), (0, 0, .2), 6, 150)
    import random as _r
    R = _r.Random(66); cols = [(.7, .1, .1), (.1, .3, .7), (.8, .6, .1), (.2, .55, .3), (.6, .2, .6)]
    S["col"] = []
    for k in range(14):
        x, y = R.uniform(-2.2, 2.2), R.uniform(-.5, 4.0)
        o = torus("col%d" % k, .1, .016, (x, y, -50), plain("collar%d" % (k % 5), cols[k % 5], .5), (R.uniform(-.3, .3), R.uniform(-.3, .3), 0)); o["p"] = (x, y); ANIM.append(o); S["col"].append(o)


def a_s05(u, t, f):
    k2 = pb("L05", 2)
    for k, o in enumerate(S["col"]):
        T = lbeat("s05", k2) + (k % 7) * .09 - .4 if k >= 4 else -1
        x, y = o["p"]; o.location = (x, y, .02) if t >= T else (x, y, -50)
    go("s05", [(0, (0, -3.0, .5), (0, 3, .3), 26), (pb("L05", 1), (-1.4, -2.0, .7), (0, 2, .1), 28), (k2, (.6, -1.4, 1.6), (0, 1.5, 0), 30)], t, 3.4, mv=.6)


def s_s06():                                   # 犬種の名札が拍ごとに並ぶ（暗い展示室）。雌の札に出産の印
    stage("arena"); spot("sp", (0, -4, 6), (0, 0, 1.0), 2200, size=1.0, ang=1.0, blend=.6); reflector("rf", (0, -12, 3), (0, 0, 1.0), 8, 500)
    names = ["トイプードル", "ミニチュアダックス", "チワワ", "ポメラニアン"]; S["tg"] = []
    for k, nm in enumerate(names):
        r = empty("tg%d" % k, (0, 0, -50)); parent(box("tgb%d" % k, (1.9, .05, .34), (0, 0, 0), pbr_mat("plank", "wood_floor", 1.0, (1, .92, .8), 1.0, box_proj=True), bevel=.01), r)
        parent(dark_text("tgt%d" % k, nm, (-.12, -.03, 0), .15), r)
        for j in range(3 + k % 3):
            parent(sphere("tgd%d_%d" % (k, j), .035, (.62 + j * .09, -.04, 0), plain("birthmk", (.7, .12, .1), .5), 16), r)
        ANIM.append(r); S["tg"].append(r)


def a_s06(u, t, f):
    for k, r in enumerate(S["tg"]):
        drop(r, (0, 0, 1.9 - k * .45), t, lbeat("s06", 1 + k), h=.8, dur=.22)
    k1 = pb("L06", 1)
    go("s06", [(0, (0, -4.8, 1.3), (0, 0, 1.3), 30), (k1, (.5, -3.6, 1.15), (.1, 0, 1.2), 32)], t, 3.0)


def s_s07():                                   # 暗い倉庫：4 段に積まれたケージ、中に犬の影
    stage("plant"); reflector("rf", (0, -10, 3), (0, 0, 1.5), 8, 200); spot("sp", (0, -3, 5), (0, 1, 1.5), 900, (.85, .9, 1), size=1.0, ang=1.0, blend=.7)
    cells = [((c - 3.5) * .72, 1.0 + r * .0, z * .6) for c in range(8) for r in range(1) for z in range(4)] + [((c - 3.5) * .72, 2.2, z * .6) for c in range(8) for z in range(4)]
    cages("stack", cells, w=.68, d=.55, h=.55, wire=.01)
    pts = [(x, y, z + .02, .4 * ((i * 5) % 3 - 1)) for i, (x, y, z) in enumerate(cells) if (i * 7) % 5]
    dogs("inside", [(x, y, z, r) for x, y, z, r in pts], DOG, .42, plain("shadowdog", (.35, .33, .31), .6))


def a_s07(u, t, f):
    go("s07", [(0, (-2.8, -3.2, 1.0), (0, 1.5, 1.2), 26), (pb("L07", 1), (0, -2.6, 1.4), (0, 1.3, 1.2), 30), (pb("L07", 2), (2.2, -1.8, 2.4), (.5, 1.5, 1.0), 28)], t, 3.4, mv=.6)


def s_s08():                                   # 明るい居間：家族と子犬。殺処分の柱が 39 万 → 7 千に縮む
    stage("lounge"); reflector("rf", (0, -8, 2), (0, 0, .6), 6, 350); spot("sp", (-1.5, -2.5, 3.5), (0, 0, .5), 900, (1, .9, .75), size=.8, ang=1.0, blend=.6)
    S["f1"] = fig("f1", (-.5, .6, 0), 1.25, ceramic(), 3.14); S["f2"] = fig("f2", (.3, .7, 0), 1.1, ceramic(), 3.14)
    S["pp"] = dog_mesh("pp", PUP, .45, goldfig(), (-.05, .05, 0), 0.0)
    S["pil"] = empty("pil", (1.4, .3, 0)); parent(box("pilb", (.45, .45, 1.0), (0, 0, .5), gold_mat("goldpil", .14), bevel=.0), S["pil"]); ANIM.append(S["pil"])
    S["pl1"] = label("pl1", "約39万", (0, 0, -50), .16); S["pl2"] = label("pl2", "約7千", (0, 0, -50), .16); ANIM.extend([S["pl1"], S["pl2"]])


def a_s08(u, t, f):
    k2, k3 = pb("L08", 2), pb("L08", 3); T = lbeat("s08", k3)
    h = 2.0 if t < T - .5 else 2.0 - (2.0 - .04) * eio(clamp((t - (T - .5)) / .9))
    vis = t >= lbeat("s08", k2) - .3
    S["pil"].scale = (1, 1, max(.001, h)); S["pil"].location = (1.4, .3, 0 if vis else -50)
    S["pl1"].location = (1.4, .05, h + .18) if vis and t < T else (0, 0, -50); S["pl2"].location = (1.4, .05, h + .18) if t >= T + .4 else (0, 0, -50)
    S["pp"].location = (-.05, .05, hop(t, lbeat("s08", 2), .12, .35) + hop(t, lbeat("s08", 4), .12, .35))
    go("s08", [(0, (0, -2.6, 1.1), (0, .4, .6), 32), (pb("L08", 1), (-.8, -1.6, .7), (-.1, .2, .4), 38), (k2, (1.0, -2.6, 1.3), (1.0, .3, .9), 30), (k3, (1.8, -1.9, .7), (1.4, .3, .3), 34)], t, 3.0)


def s_s09():                                   # ヨーロッパの夕方の街角：空っぽのショーケース（街はイメージ）
    stage("street"); reflector("rf", (0, -10, 2.5), (0, 0, 1.2), 8, 300)
    showcase("emp", (0, 0, .5), lit=True, pup=False); box("standb", (1.2, .9, .5), (0, 0, .25), plain("shelfb", (.2, .18, .17), .5), bevel=.01)


def a_s09(u, t, f):
    go("s09", [(0, (1.8, -3.4, 1.4), (0, 0, 1.0), 28), (pb("L09", 1), (.2, -1.9, 1.05), (0, 0, .9), 38)], t, 3.0)


def s_s10():                                   # 最後：冒頭のショーケース。明かりが 1 つずつ、ゆっくり消える
    shop_set()


def a_s10(u, t, f):
    for i, nm in enumerate(S["sc"]):
        T = lbeat("s10", 2) + i * BP * .6
        set_lamp(nm, 1 - eio(clamp((t - T) / .8))) if nm != "sc11" else set_lamp(nm, 1.0)
    go("s10", [(0, (.55, -2.3, 1.38), (.53, .1, 1.32), 38), (2, (0, -4.6, 1.6), (0, 0, 1.3), 28)], t, 3.0, mv=.8)


# ---------------------------------------------------------------- 書き出し
def _setup(k):
    def f():
        CUR[0] = k; S.clear(); globals()["s_" + k]()
    return f


def _wrap(a):
    def run(u, t, f):
        CURF[0] = f
        try:
            return a(u, t, f)
        finally:
            CURF[0] = None
    return run


SHOTS = {k: (_setup(k), _wrap(globals()["a_" + k])) for k in NAMES}

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
