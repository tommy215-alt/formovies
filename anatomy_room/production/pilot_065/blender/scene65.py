"""pilot_065「2013年まで、選挙に行けなかった日本人」の 3D（Blender Cycles）。新ドパ設計 v2（064 の scene64.py の複製から）。
ショット＝セリフの行（s00〜s11）。体育館の投票所の扉 → 扉の札 → 居間（選挙公報・入場券）→ 住宅街 → 判と後見人 → 郵便受け → 条文の石板 → 天秤 → 法廷 → 議場 → 郵便受け → 扉が開き一票。
人は顔のない陶器・金の模型（彼女だけ金）。実名・写真は使わない。動き・カメラの着地は表拍（lbeat の整数）。閃光なし。
blender -b -P blender/scene65.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib65 import *  # noqa: F401,F403
from lib65 import _sc

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
    clear_scene(); ANIM[:] = [cam.o]; HALL_DOTS.clear(); ENV.clear(); ENV_AT.clear()
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


def _env_handler(scene, *_):
    k = ENV_AT.get(scene.frame_current - 1)
    if k is not None and k in ENV:
        _apply_env(k)


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


# ---------------------------------------------------------------- 場面
def s_s00():                                   # 冒頭：体育館の投票所。白い人形が次々に入っていき、金の人形の前で扉が閉まる
    stage("poll"); spot("sp", (-2.5, -4.5, 5.5), (0, 0, 1.2), 2600, size=1.2, ang=1.0, blend=.6); reflector("rf", (0, -12, 3), (0, 0, 1.2), 8, 600)
    door_set("dr"); hall_inside("in")
    S["w"] = [fig("w%d" % i, (0, 0, -50), 1.1 + .06 * (i % 3), ceramic()) for i in range(4)]
    S["h"] = her()


def a_s00(u, t, f):
    tc = lbeat("s00", 5)                       # 扉が閉まる拍
    set_doors("dr", 1.0 if t < tc - .22 else eio(clamp((tc - t) / .22)))
    for i, o in enumerate(S["w"]):             # 白い人形が 1 拍ごとに扉を通って奥へ
        t0 = lbeat("s00", i) - .5; walk(o, (.35 * (i % 2 * 2 - 1), -3.2, 0), (.35 * (i % 2 * 2 - 1), 2.4, 0), t, t0, t0 + 1.6)
        if t < t0:
            o.location = (0, 0, -50)
    walk(S["h"], (0, -4.5, 0), (0, -.75, 0), t, lbeat("s00", 2), tc - .05)
    if t > tc:                                 # 扉にぶつかったように少し下がる
        S["h"].location = (0, -.75 - .12 * eio(clamp((t - tc) / .25)), 0)
    go("s00", [(0, (2.2, -6.0, 1.6), (0, 0, 1.3), 28), (3, (-1.6, -4.2, 1.4), (0, -.6, 1.2), 32), (5, (.9, -2.8, 1.25), (0, -.5, 1.15), 36), (7, (0, -4.6, 1.5), (0, 0, 1.4), 30)], t, 3.0)


def s_s01():                                   # 閉じた扉と、扉に掛かる札「成年後見制度」
    stage("poll"); spot("sp", (-2.0, -4.0, 5.0), (0, 0, 1.4), 2400, size=1.0, ang=1.0, blend=.6); reflector("rf", (0, -12, 3), (0, 0, 1.2), 8, 600)
    door_set("dr"); set_doors("dr", 0); S["h"] = her(loc=(.62, -.95, 0), rz=.3)
    pl = empty("plq", (0, 0, -50)); parent(box("plq_b", (1.2, .05, .34), (0, 0, 0), pbr_mat("plank", "wood_floor", 1.0, (1, .92, .8), 1.0, box_proj=True), bevel=.01), pl)
    parent(dark_text("plq_t", "成年後見制度", (0, -.035, 0), .14), pl); ANIM.append(pl); S["plq"] = pl
    S["chain"] = [box("ch%d" % k, (.012, .012, .5), (0, 0, -50), gold_mat("brassl", .3, (.86, .62, .3)), bevel=0) for k in range(2)]; ANIM.extend(S["chain"])


def a_s01(u, t, f):
    k1 = pb("L01", 1); T = lbeat("s01", k1)
    if t < T - .3:
        S["plq"].location = (0, 0, -50)
        for c in S["chain"]:
            c.location = (0, 0, -50)
    else:
        e = clamp((t - (T - .3)) / .3); z = 1.25 + 1.4 * (1 - e * e) + (.03 * math.exp(-6 * (t - T)) * math.sin(14 * (t - T)) if t > T else 0)
        S["plq"].location = (0, -.12, z); S["plq"].rotation_euler = (0, 0, .03 * math.sin(3 * (t - T)) * math.exp(-1.5 * max(0, t - T)))
        for k, sx in enumerate((-1, 1)):
            S["chain"][k].location = (sx * .35, -.11, z + .4); S["chain"][k].rotation_euler = (0, sx * .45, 0)
    go("s01", [(0, (2.0, -3.8, 1.3), (.2, 0, 1.25), 32), (k1, (-.5, -2.5, 1.35), (0, -.1, 1.25), 40), (k1 + 2, (-.9, -2.2, 1.4), (-.05, -.1, 1.25), 46)], t, 2.6)


def s_s02():                                   # 居間：ちゃぶ台に選挙公報、入場券が拍ごとに積み上がる（一度も休まなかった）
    stage("lounge"); spot("sp", (-1.5, -2.5, 3.5), (0, 0, .4), 900, (1, .9, .75), size=.8, ang=1.0, blend=.6); reflector("rf", (0, -8, 2), (0, 0, .6), 6, 350)
    chabudai("cb", (0, 0, 0)); gazette("gz", (-.12, -.05, .363), .1); S["h"] = her(loc=(.55, .45, 0), rz=2.5)
    S["tk"] = [ticket("tk%d" % i) for i in range(10)]


def a_s02(u, t, f):
    k1 = pb("L02", 1)
    for i, o in enumerate(S["tk"]):           # 句 1 から、半拍ごとに 1 枚
        T = lbeat("s02", k1) + i * BP / 2
        drop(o, (.26 + .004 * ((i * 7) % 3), -.08, .363 + .0028 * i), t, T, h=.5, dur=.18, rz=.15 * (((i * 5) % 5) - 2) / 2)
    S["h"].location = (.55, .45, bob("s02", t, range(0, 8, 2), .03))
    go("s02", [(0, (-1.2, -1.6, 1.1), (0, 0, .45), 32), (k1, (.6, -.75, .75), (.2, -.05, .36), 42), (k1 + 4, (1.3, -1.4, 1.0), (.2, 0, .45), 34)], t, 2.6)


def s_s03():                                   # 朝の住宅街：父・母と彼女が並んで投票所へ歩く。「投票所」の看板の矢印
    stage("suburb"); reflector("rf", (0, -12, 3), (0, 0, 1.0), 8, 450)
    S["fa"] = fig("fa", (0, 0, 0), 1.3, ceramic()); S["mo"] = fig("mo", (0, 0, 0), 1.2, ceramic()); S["h"] = her()
    sg = empty("sgn", (0, 0, -50)); parent(box("sgn_p", (.06, .06, 1.4), (0, 0, .7), plain("sgpost", (.3, .3, .32), .4, metal=.6), bevel=0), sg)
    parent(box("sgn_b", (.9, .04, .5), (0, 0, 1.55), plain("sgw", (.95, .95, .93), .5), bevel=.01), sg)
    parent(dark_text("sgn_t", "投票所 →", (0, -.03, 1.55), .15, col=(.75, .1, .08)), sg); ANIM.append(sg); S["sg"] = sg


def a_s03(u, t, f):
    t1 = lbeat("s03", 8)
    for o, dy, dx in ((S["fa"], .0, -.75), (S["h"], -.15, 0.0), (S["mo"], .0, .75)):
        walk(o, (-2.6 + dx, dy, 0), (1.4 + dx, dy, 0), t, -.3, t1, step=.06, rz=-math.pi / 2)
    k1 = pb("L03", 1); rise(S["sg"], (2.9, .6, 0), t, lbeat("s03", k1), dur=.35, depth=2.0)
    if t < lbeat("s03", k1) - .4:
        S["sg"].location = (0, 0, -50)
    go("s03", [(0, (-1.8, -4.0, 1.2), (-1.2, 0, 1.0), 30), (k1, (.6, -4.4, 1.3), (.8, 0, 1.1), 28), (k1 + 3, (1.4, -3.4, 1.0), (1.8, .3, 1.1), 30)], t, 3.0)


def s_s04():                                   # 居間：書類に判。父が隣に立ち、「後見人」の札
    stage("lounge"); spot("sp", (-1.5, -2.5, 3.5), (0, 0, .4), 900, (1, .9, .75), size=.8, ang=1.0, blend=.6); reflector("rf", (0, -8, 2), (0, 0, .6), 6, 350)
    chabudai("cb", (0, 0, 0)); S["h"] = her(loc=(-.3, .7, 0), rz=3.14)
    doc = empty("doc", (0, -.05, .363)); parent(box("doc_p", (.21, .297, .002), (0, 0, 0), paper(), bevel=0), doc)
    parent(dark_text("doc_t", "後見開始", (0, .1, .002), .028, rot=(0, 0, 0)), doc)
    for k in range(5):
        parent(box("doc_l%d" % k, (.15, .004, .0022), (0, .05 - k * .03, 0), plain("tkline", (.45, .45, .42), .7), bevel=0), doc)
    S["seal"] = plane("sealmk", .045, .045, (0, 0, -50), plain("sealred", (.7, .06, .05), .6))
    st = empty("stamp", (0, 0, -50)); parent(cyl("stamp_b", .025, .09, (0, 0, .045), plain("stampw", (.2, .12, .07), .4, coat=.3), 32), st); ANIM.append(st); S["st"] = st
    S["fa"] = fig("fa", (0, 0, -50), 1.3, ceramic())
    S["tag"] = empty("tag", (0, 0, -50)); parent(box("tag_b", (.62, .04, .2), (0, 0, 0), pbr_mat("plank", "wood_floor", 1.0, (1, .92, .8), 1.0, box_proj=True), bevel=.01), S["tag"])
    parent(dark_text("tag_t", "後見人", (0, -.025, 0), .12), S["tag"]); ANIM.append(S["tag"])


def a_s04(u, t, f):
    T0 = lbeat("s04", 1); k1, k2 = pb("L04", 1), pb("L04", 2)
    if t < T0:                                 # 判が下りる
        S["st"].location = (.04, -.12, .366 + .35 * eio(clamp((T0 - t) / .3))); S["seal"].location = (0, 0, -50)
    else:
        S["st"].location = (.04, -.12, .366 + .3 * eio(clamp((t - T0 - .15) / .3))); S["seal"].location = (.04, -.12, .3652)
    walk(S["fa"], (1.6, .9, 0), (.35, .75, 0), t, lbeat("s04", k1) - .8, lbeat("s04", k1), rz=3.14)
    if t < lbeat("s04", k1) - .8:
        S["fa"].location = (0, 0, -50)
    drop(S["tag"], (.35, .6, 1.95), t, lbeat("s04", k2), h=.8, dur=.25)
    go("s04", [(0, (.5, -.8, .8), (.04, -.1, .37), 40), (k1, (-.4, -2.4, 1.3), (.1, .6, .9), 30), (k2, (.6, -1.9, 1.5), (.3, .6, 1.4), 34)], t, 2.6)


def mail_set():
    stage("yard"); reflector("rf", (0, -10, 3), (0, 0, 1.2), 8, 450)
    mailbox("mb", (0, 0, 0)); S["tk"] = [ticket("mt%d" % i) for i in range(2)]; S["ol"] = outline_card("ol", (0, 0, -50)); S["g"] = ticket("mtg", gold=True)
    S["h"] = her(loc=(-.75, -.45, 0), rz=-.5)


SLOT = [(-.155, -.02), (.0, .02), (.155, -.01)]


def s_s05():                                   # 郵便受け：家族の 2 枚が落ちてくる。3 枚目（彼女の分）は来ない
    mail_set()


def a_s05(u, t, f):
    for i, o in enumerate(S["tk"]):
        drop(o, (SLOT[i][0], SLOT[i][1], 1.024 + .003 * i), t, lbeat("s05", i + 1), h=.25, dur=.2, rz=.1 * (i - .5))
    k1 = pb("L05", 1); T = lbeat("s05", k1 + 1)
    S["ol"].location = (SLOT[2][0], SLOT[2][1], 1.023) if t > T else (0, 0, -50)
    S["g"].location = (0, 0, -50)
    go("s05", [(0, (.7, -1.4, 1.5), (0, 0, 1.1), 34), (k1, (0, -.8, 1.42), (0, 0, 1.03), 40), (k1 + 2, (.15, -.62, 1.3), (.12, 0, 1.02), 46)], t, 2.4)


def s_s06():                                   # 役所のような石の廊下：条文の石板が落ちてくる（2026-11-20 書斎に見えるのでやめた）
    stage("hall"); spot("sp", (-2.0, -4.0, 6.0), (0, 0, 1.0), 2600, size=1.0, ang=.9, blend=.6); reflector("rf", (0, -12, 3), (0, 0, 1.0), 8, 650)
    S["tb"] = tablet("tb")


def a_s06(u, t, f):
    k1 = pb("L06", 1); drop(S["tb"], (0, 1.0, 0), t, lbeat("s06", k1), h=2.6, dur=.35)
    k2 = pb("L06", 2)
    go("s06", [(0, (0, -4.6, 1.0), (0, 0, 1.6), 30), (k1, (-1.2, -3.2, .7), (0, 1.0, .9), 30), (k2, (.4, -2.2, .55), (0, 1.0, .55), 38), (k2 + 2, (0, -3.6, .9), (0, 1.0, .8), 30)], t, 3.0)


def s_s07():                                   # 彼女の居間の天秤：左に電卓、右に投票用紙。釣り合わない（2026-11-20 書斎に見えるのでやめた）
    stage("lounge2"); spot("sp", (-2.0, -5.0, 7.0), (0, 0, 2.2), 2800, size=1.0, ang=.9, blend=.6); reflector("rf", (0, -12, 4), (0, 0, 2.0), 8, 700)
    S["bal"] = balance("bal", (0, 0, 0), .7); S["calc"] = calculator("calc"); S["bl"] = ballot("bl")


def a_s07(u, t, f):
    k1, k2 = pb("L07", 1), pb("L07", 0, 1); T1, T2 = lbeat("s07", k2), lbeat("s07", k1)
    ang = 0.0
    if t > T1:
        ang += .22 * eio(clamp((t - T1) / .35)) + .04 * math.exp(-2.5 * (t - T1)) * math.sin(9 * (t - T1))
    if t > T2:
        ang += -.06 * eio(clamp((t - T2) / .35)) + .05 * math.exp(-2.5 * (t - T2)) * math.sin(9 * (t - T2))
    root, pv, pans = S["bal"]; set_balance(root, pv, pans, ang)
    s = .7; L0, R0 = pans[0][1].location, pans[1][1].location
    lp = (L0.x * s, L0.y * s, (L0.z + .06) * s); rp = (R0.x * s, R0.y * s, (R0.z + .06) * s)
    drop(S["calc"], lp, t, T1, h=1.2, dur=.3) if t < T1 + .3 else setattr(S["calc"], "location", lp)
    drop(S["bl"], rp, t, T2, h=1.0, dur=.35) if t < T2 + .35 else setattr(S["bl"], "location", rp)
    k3 = pb("L07", 2)
    go("s07", [(0, (0, -5.6, 1.9), (0, 0, 1.6), 28), (k2, (-2.2, -3.0, 1.4), (-1.5, 0, 1.0), 34), (k1, (2.2, -3.0, 1.5), (1.5, 0, 1.2), 34), (k3, (0, -6.4, 1.6), (0, 0, 1.6), 26)], t, 3.0)


def s_s08():                                   # 法廷：証言台の前の彼女。判決の句で上から光が少しずつ差す（閃光なし）
    stage("court"); reflector("rf", (0, -12, 3), (0, 0, 1.2), 8, 800); spot("bsp", (0, -2.0, 6.0), (0, 2.6, 1.6), 2200, (1, .9, .75), size=1.0, ang=1.2, blend=.6)
    S["h"] = her(loc=(0, -1.2, 0), rz=0.0); S["fa"] = fig("fa", (1.3, -2.6, 0), 1.3, ceramic()); S["mo"] = fig("mo", (2.0, -2.6, 0), 1.2, ceramic())
    S["sp"] = spot("hsp", (0, -1.6, 5.5), (0, -1.2, .8), 0, (1, .88, .65), size=.4, ang=.5, blend=.7)


def a_s08(u, t, f):
    k2 = pb("L08", 2); T = lbeat("s08", k2)
    S["sp"].data.energy = 1800 * eio(clamp((t - T) / .8))
    go("s08", [(0, (.6, -7.5, 2.4), (0, 2.0, 1.5), 26), (pb("L08", 1), (-2.0, -4.6, 1.3), (0, 2.0, 1.7), 28), (k2, (-.9, -3.4, .95), (0, -1.2, 1.05), 34), (k2 + 3, (-.4, -6.2, 2.0), (0, 1.0, 1.3), 26)], t, 3.0)


def s_s09():                                   # 国会の議場（イメージ）：半円の席の議員が、列ごとに一斉に立つ（全会一致・起立）
    stage("rotunda"); spot("sp", (0, -4, 9), (0, 2.5, 0), 3000, size=1.5, ang=1.2, blend=.6); reflector("rf", (0, -14, 4), (0, 2, .8), 10, 600)
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.55, .38, .26), 1.0, box_proj=True); S["rows"] = []
    for r in range(5):                          # 半円の 5 列。机は列ごとに 1 つのメッシュ
        R = 2.2 + r * .75; n = 9 + r * 3; pts = []; bm = bmesh.new()
        for k in range(n):
            a = math.pi * (.08 + .84 * k / (n - 1)); x, y = R * math.cos(a), 2.6 + R * math.sin(a)
            pts.append((x, y, a - math.pi / 2))
            rr = bmesh.ops.create_cube(bm, size=1.0)
            for v in rr["verts"]:
                vx, vy, vz = v.co.x * .42, v.co.y * .22, v.co.z * .62
                cx, cy = x - .28 * math.cos(a), y - .28 * math.sin(a)
                ca, sa = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2); v.co.x = cx + vx * ca - vy * sa; v.co.y = cy + vx * sa + vy * ca; v.co.z = .31 + vz + r * .18
            if r:                               # 席の下の段（列ごとに高く）
                rr = bmesh.ops.create_cube(bm, size=1.0)
                for v in rr["verts"]:
                    vx, vy, vz = v.co.x * .62, v.co.y * .75, v.co.z * r * .18
                    cx, cy = x - .1 * math.cos(a), y - .1 * math.sin(a)
                    ca, sa = math.cos(a - math.pi / 2), math.sin(a - math.pi / 2); v.co.x = cx + vx * ca - vy * sa; v.co.y = cy + vx * sa + vy * ca; v.co.z = vz + r * .09
        link(bpy.data.objects.new("desk%d" % r, mesh_from_bm("desk%d" % r, bm, [wd], smooth=False)))
        o = crowd("mp%d" % r, [(x, y, rz) for x, y, rz in pts], .62, ceramic()); o["z"] = r * .18; ANIM.append(o); S["rows"].append(o)
    box("rostrum", (1.4, .8, 1.1), (0, 2.6, .55), wd, bevel=.02)


def a_s09(u, t, f):
    k1 = pb("L09", 1)
    for r, o in enumerate(S["rows"]):
        T = lbeat("s09", k1) + r * BP / 2; z0 = o["z"] - .28
        o.location = (0, 0, z0 + .28 * eio(clamp((t - (T - .2)) / .2)))
    go("s09", [(0, (0, -2.0, 4.6), (0, 3.2, .6), 26), (k1, (-3.4, -1.2, 1.8), (0, 3.0, .9), 28), (k1 + 3, (0, -2.6, 2.6), (0, 3.4, .9), 26)], t, 3.2)


def s_s10():                                   # 郵便受け：3 枚目のはがき（彼女の分）が、枠の中に落ちてくる
    mail_set()


def a_s10(u, t, f):
    for i, o in enumerate(S["tk"]):
        o.location = (SLOT[i][0], SLOT[i][1], 1.024 + .003 * i); o.rotation_euler = (0, 0, .1 * (i - .5))
    k1 = pb("L10", 1); T = lbeat("s10", k1)
    S["ol"].location = (SLOT[2][0], SLOT[2][1], 1.023) if t < T else (0, 0, -50)
    drop(S["g"], (SLOT[2][0], SLOT[2][1], 1.024), t, T, h=.3, dur=.22, rz=.05)
    S["h"].location = (-.75, -.45, hop(t, T + BP, .12, .4))
    go("s10", [(0, (0, -1.1, 1.5), (0, 0, 1.03), 36), (k1, (.08, -.85, 1.42), (.06, 0, 1.03), 38), (k1 + 3, (.3, -2.8, 1.3), (-.3, 0, .9), 30)], t, 5.6)


def s_s11():                                   # 最後：投票所の扉が開き、彼女が入って、一票を箱へ
    stage("poll"); spot("sp", (-2.5, -4.5, 5.5), (0, 1.0, 1.2), 2600, size=1.2, ang=1.0, blend=.6); reflector("rf", (0, -12, 3), (0, 1, 1.2), 8, 600)
    door_set("dr"); hall_inside("in"); S["h"] = her(); S["bl"] = ballot("blg", gold=True)


def a_s11(u, t, f):
    to = lbeat("s11", 1); set_doors("dr", eio(clamp((t - (to - .5)) / .5)))
    tw = lbeat("s11", 5); walk(S["h"], (0, -1.6, 0), (0, 1.55, 0), t, to, tw)
    k1 = pb("L11", 1); T = lbeat("s11", k1 + 1)
    bx, by, bz = 0, 1.2 + .9, 1.11
    if t < T - .4:
        S["bl"].location = (0, 0, -50)
    else:                                      # 金の票が箱の口へ（縦にして落ちる）
        e = clamp((t - (T - .4)) / .4); S["bl"].rotation_euler = (math.pi / 2, 0, 0); S["bl"].scale = (.6, .6, .6)
        S["bl"].location = (bx, by, bz + .45 * (1 - e) - .25 * clamp((t - T) / .3))
    go("s11", [(0, (0, -4.6, 1.5), (0, 0, 1.4), 30), (2, (1.2, -3.2, 1.4), (0, .8, 1.2), 30), (k1, (.8, .6, 1.5), (bx, by, 1.05), 40), (k1 + 3, (0, -4.8, 1.8), (0, 1.0, 1.2), 26)], t, 3.0)


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
