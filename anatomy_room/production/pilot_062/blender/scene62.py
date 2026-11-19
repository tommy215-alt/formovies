"""pilot_062「人類のスポーツ記録、いちばん"ありえない"のは？」の 3D（Blender Cycles）。新ドパ設計 v2（061 型）。
ショット＝セリフの行（s00〜s14）。場面ごとに舞台を変える（2026-11-18 ユーザーの指示「常に同一の場所に固定されない構造」）：
暗い展示室（6 つの競技の道具）→ 陸上のトラック → バスケのコート → ゴルフのグリーン → 野球場 → サッカー場 → 天才 5 人の柱 → クリケット場 → 偏差値の人の山 → 記念碑（v2、2026-11-19）。
人は顔のない陶器の人形（CHARACTER_GUIDE の方針）。動き・カメラの着地は表拍（lbeat の整数）。閃光なし。
blender -b -P blender/scene62.py -- [s00 s01 …] [--samples N]     試し描き：AT="1.5,3" PCT=40 で work/test/ に"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib62 import *  # noqa: F401,F403

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


def stage(kind):
    """舞台：arena（暗い展示室）・track・pitch（サッカー）・court（バスケ）・golf・diamond（野球）・cricket・night（夜のクリケット場）"""
    clear_scene(); ANIM[:] = [cam.o]
    if kind == "arena":
        plane("floor", 80, 80, (0, 0, 0), plain("blackfloor", (.025, .024, .027), .22, coat=.8))
        plane("backw", 80, 20, (0, 9, 10), pbr_mat("bw", "brushed_concrete", 1 / 3.0, (.16, .15, .15), 1.0, box_proj=True), rot=(math.pi / 2, 0, 0)); lights((900, (1, .92, .8)), (600, (1, .8, .6)), "studio_small_08_2k.hdr", .35)
    elif kind == "track":
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("trk", "running_track", 1 / 2.0, (1, .9, .85), 1.0, box_proj=True))
        line = plain("lane", (.92, .92, .9), .5)
        for i in range(-5, 6):
            box("lane%d" % i, (60, .035, .004), (0, i * .7 + .35, .002), line, bevel=0)
        box("finish", (.06, 7.7, .005), (3.0, 0, .003), line, bevel=0)
        lights((1300, (1, .96, .9)), (700, (1, .9, .8)), "stadium_01_2k.hdr", 1.0, 0.6, 1)
    elif kind in ("pitch", "cricket", "night"):
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("grs", "grass_ground", 1 / 2.5, (.75, .9, .7), 1.0, box_proj=True))
        if kind != "pitch":
            plane("strip", 1.6, 13, (0, 0, .004), pbr_mat("pitchdirt", "park_dirt", 1 / 1.5, (1, .92, .78), 1.0, box_proj=True))
            wl = plain("crease", (.95, .95, .92), .5)
            for y in (-5.0, 5.0):
                box("cr%g" % y, (1.6, .04, .003), (0, y, .006), wl, bevel=0)
        if kind == "night":
            lights((700, (1, .85, .65)), (1400, (.7, .8, 1)), "orlando_stadium_2k.hdr", .25, 2.0, 1)
        else:
            lights((1300, (1, .96, .9)), (700, (1, .9, .8)), "stadium_01_2k.hdr" if kind == "pitch" else "orlando_stadium_2k.hdr", 1.0, 1.2, 1)
    elif kind == "court":                     # バスケのコート（暗い体育館、木の床）
        plane("floor", 80, 80, (0, 0, 0), pbr_mat("court", "wood_floor", 1 / 1.6, (1, .9, .78), 1.0, box_proj=True))
        plane("paint", 1.7, 2.4, (0, 2.45, .003), plain("paint", (.5, .14, .07), .45, coat=.3))
        ln = plain("cline", (.95, .95, .92), .5)
        for (sx, sy, x, y) in ((1.74, .04, 0, 1.25), (.04, 2.4, -.87, 2.45), (.04, 2.4, .87, 2.45), (12, .04, 0, 3.65)):
            box("cl%g%g" % (x, y), (sx, sy, .003), (x, y, .005), ln, bevel=0)
        plane("backw", 80, 20, (0, 12, 10), plain("gymw", (.05, .05, .06), .7), rot=(math.pi / 2, 0, 0))
        lights((1100, (1, .95, .88)), (650, (1, .85, .7)), "studio_small_08_2k.hdr", .35)
    elif kind == "golf":                      # ゴルフのグリーン（昼の草原）
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("grs", "grass_ground", 1 / 2.5, (.75, .9, .7), 1.0, box_proj=True))
        cyl("green", 3.4, .012, (0, 1.6, .002), pbr_mat("greenm", "grass_ground", 1 / .6, (.55, 1.05, .45), 1.0, box_proj=True), 96)
        lights((1300, (1, .96, .9)), (700, (1, .9, .8)), "meadow_2_2k.hdr", 1.0, 1.0, 1)
    elif kind == "diamond":
        plane("floor", 300, 300, (0, 0, 0), pbr_mat("grs", "grass_ground", 1 / 2.5, (.75, .9, .7), 1.0, box_proj=True))
        d = plane("dirt", 7, 7, (0, 2.6, .004), pbr_mat("infield", "raked_dirt", 1 / 2.0, (1, .8, .65), 1.0, box_proj=True)); d.rotation_euler = (0, 0, math.pi / 4)
        bs = plain("base", (.95, .95, .92), .5)
        for (x, y) in ((0, -2.35), (3.5, 1.15), (0, 4.65), (-3.5, 1.15)):
            box("base%g%g" % (x, y), (.25, .25, .04), (x, y, .02), bs, bevel=.01)
        lights((1300, (1, .96, .9)), (700, (1, .9, .8)), "orlando_stadium_2k.hdr", 1.0, .4, 1)


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


# ---------------------------------------------------------------- 偏差値の人の山（正規分布）：x＝偏差値、列の人数＝分布の高さ
DX = .9                                     # 偏差値 10（1 標準偏差）あたりの間隔 m
dvx = lambda dv: (dv - 50) / 10 * DX


def bell(pfx, s=.32):
    out = []; m = ceramic()
    for zi in range(-10, 11):
        z = zi * .25; n = int(round(11 * math.exp(-z * z / 2)))
        for k in range(n):
            out.append(fig(f"{pfx}{zi}_{k}", (dvx(50 + z * 10), -k * .24, 0), s, m, rz=random.Random(zi * 31 + k).uniform(-.3, .3)))
    return out


def ruler(pfx, marks=(50, 60, 70, 80, 90, 100, 110, 120)):
    w = plain("rulerw", (.9, .88, .82), .5)
    box(pfx + "_bar", (dvx(125) - dvx(25), .03, .006), ((dvx(125) + dvx(25)) / 2, .45, .003), w, bevel=0)
    for dv in marks:
        box(pfx + "_tk%d" % dv, (.03, .18, .008), (dvx(dv), .45, .004), w, bevel=0)
        o = text_obj(pfx + "_n%d" % dv, str(dv), (dvx(dv), .78, .005), .2, gold_mat("goldtext", .2), rot=(0, 0, 0), extrude=.01)


# ================================================================ ショット
PROPS = [("陸上", "stopwatch"), ("バスケ", "basketball"), ("ゴルフ", "golf"), ("野球", "baseball"), ("サッカー", "soccer"), ("クリケット", "cricket")]
PX = [(i - 2.5) * 1.25 for i in range(6)]


def s_s00():                                   # 冒頭：暗い展示室、金の台座に 6 つの競技の道具が拍ごとに落ちる（台座に競技の名前）
    stage("arena"); sp = spot("sp", (0, -4, 7), (0, 0, .5), 3800, size=.8, ang=.95, blend=.6); sp.visible_glossy = False   # 斜めから見ると床に光の筋が写る
    reflector("rf", (0, -14, 3.5), (0, 0, 1.0), 10, 2500)
    for sx in (-1, 1):                         # 列の両端の壁（斜めのカメラで、床に周りの光が写り込まないように）
        plane("endw%d" % sx, 40, 20, (sx * 9, 0, 10), pbr_mat("bw", "brushed_concrete", 1 / 3.0, (.16, .15, .15), 1.0, box_proj=True), rot=(math.pi / 2, 0, math.pi / 2))
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.4, .32, .26), 1.0, box_proj=True); g = gold_mat("gold", .13)
    S["props"] = []
    for i, (lab, kind) in enumerate(PROPS):
        x = PX[i]; cyl("ped%d" % i, .5, .9, (x, 0, .45), wd, 64, bevel=.02); cyl("pedg%d" % i, .52, .05, (x, 0, .925), g, 64)
        label("lab%d" % i, lab, (x, -.52, .55), .15 if len(lab) < 5 else .12)
        if kind == "stopwatch":
            o = stopwatch("sw"); base = (x, 0, 1.13)
        elif kind == "basketball":
            o = basketball("bk", .2); base = (x, 0, 1.15)
        elif kind == "golf":
            o = golf_set("gf"); base = (x - .08, 0, .95)
        elif kind == "baseball":
            o = baseball("bb", .12); base = (x, 0, 1.07)
        elif kind == "soccer":
            o = soccer_ball("sb", .2); base = (x, 0, 1.15)
        else:
            o = cricket_props("ck"); base = (x - .12, 0, .95)
        o.rotation_euler = (0, 0, .25 if kind in ("baseball", "soccer") else 0); S["props"].append((o, base)); ANIM.append(o)


def a_s00(u, t, f):
    for j, (o, base) in enumerate(S["props"]):                   # 2 つずつ映す：台座の組ごとに、拍 0・1／3・4／6・7 に落ちる（最初のコマにもう 1 つ乗っている）
        drop(o, base, t, lbeat("s00", DB[j]), h=2.5)
    K_ = [(3 * i, ((PX[2 * i] + PX[2 * i + 1]) / 2, -3.7, 1.5), ((PX[2 * i] + PX[2 * i + 1]) / 2, 0, 1.0), 34) for i in range(3)]
    go("s00", K_ + [(9, (-5.4, -2.5, 1.55), (-.6, 0, 1.0), 30), (12, (5.4, -2.7, 1.6), (.6, 0, 1.0), 30)], t, 3.0)


DB = [0, 1, 3, 4, 6, 7]


def s_s01():                                   # 物差し：一流の選手の山（正規分布）、1 人だけ前へ
    stage("arena"); spot("sp", (0, -5, 8), (0, -1, 0), 2600, size=1.0, ang=1.3); S["bell"] = bell("b")
    S["out"] = fig("outl", (dvx(50), -2.9, 0), .36, goldfig())


def a_s01(u, t, f):
    for j, o in enumerate(S["bell"]):
        rise(o, (o.location.x, o.location.y, 0), t, lbeat("s01", 0) + (j % 7) * .02, .3, depth=1.0)
    t1 = lbeat("s01", 3); k = eio(clamp((t - t1) / (BP * 3))); S["out"].location = (lerp(dvx(50), dvx(87), k), lerp(-2.9, -.2, k), .02 * abs(math.sin(t * 9)) * (0 < k < 1))
    go("s01", [(0, (0, -7.5, 3.6), (0, -1.0, 0), 30), (3, (-1.0, -5.4, 1.2), (.4, -1.5, .3), 34), (6, (dvx(80), -4.6, 1.5), (dvx(78), -.6, .3), 32)], t, 3.0)


def s_s02():                                   # ボルト：トラックを 8 人が走り、金の 1 人が抜け出す
    stage("track"); S["run"] = []; S["pil"] = pillar("p85", (4.6, 2.6, 0), (85 - 50) * .08, label="85")
    for i in range(8):
        y = (i - 3.5) * .7; m = goldfig() if i == 4 else ceramic(); S["run"].append(fig("r%d" % i, (-6, y, 0), .55, m, rz=-math.pi / 2))


def runx(i, t):
    t1 = lbeat("s02", 1); v = 3.2 if i != 4 else 3.75
    return -6 + v * max(0, t - t1) - (0 if t > t1 else 0)


def a_s02(u, t, f):
    for i, r in enumerate(S["run"]):
        x = runx(i, t); r.location = (x, r.location.y, .03 * abs(math.sin(t * 14 + i)) if t > lbeat("s02", 1) else 0)
        r.rotation_euler = (0, .18 if t > lbeat("s02", 1) else 0, -math.pi / 2)
    xg = runx(4, t)
    go("s02", [(0, (-6.0, -3.8, .6), (-6.0, .3, .4), 36), (1, (xg - 1.5, -4.2, .7), (xg, .3, .4), 34), (3, (lbeat("s02", 3) * 3.75 - 6 - .2, -4.0, .8), (lbeat("s02", 3) * 3.75 - 6 + 1.2, .3, .4), 34),
               (5, (3.0, -1.2, 1.0), (1.4, .3, .4), 30), (6, (6.0, -2.0, 1.4), (4.6, 2.6, 1.8), 34)], t, 3.0, mv=.4)
    rise(S["pil"], (4.6, 2.6, 0), t, lbeat("s02", 6), .4)


def s_s03():                                   # ジョーダン：バスケのコート。金の 1 人が跳んでシュート → 偏差値 84 の柱
    stage("court"); dk = plain("pole", (.12, .12, .13), .4, metal=.6)
    cyl("hpole", .05, 1.3, (0, 4.4, .65), dk, 24); box("harm", (.06, .6, .06), (0, 4.1, 1.28), dk, bevel=.01)
    box("board", (.95, .03, .58), (0, 3.78, 1.28), plain("boardm", (.92, .93, .95), .15, coat=.6), bevel=.01)
    box("bsq", (.32, .032, .22), (0, 3.776, 1.17), plain("bsqm", (.8, .25, .08), .4), bevel=0)
    torus("rim", .12, .009, (0, 3.6, 1.05), plain("rimm", (.85, .3, .06), .3, metal=.5))
    S["ball"] = basketball("bkb", .065); ANIM.append(S["ball"])
    S["sh"] = fig("shooter", (0, 1.2, 0), .55, goldfig(), rz=0.0)
    S["pil"] = pillar("p84", (1.9, 2.4, 0), (84 - 50) * .08, label="84")


def a_s03(u, t, f):
    t1, t2 = lbeat("s03", 1), lbeat("s03", 2); z = hop(t, t1, .22, .5); S["sh"].location = (0, 1.2, z)
    if t < t1:
        S["ball"].location = (.06, 1.12, .62 + z)
    elif t < t2:
        k = (t - t1) / (t2 - t1); S["ball"].location = (lerp(.06, 0, k), lerp(1.12, 3.6, k), lerp(.84, 1.12, k) + 1.1 * 4 * k * (1 - k))
    else:
        v = t - t2; zz = 1.12 - 4.9 * v * v
        if zz < .065:
            v0 = math.sqrt((1.12 - .065) / 4.9); w = v - v0; zz = .065 + abs(1.2 * w - 4.9 * w * w) * (w < .245)
        S["ball"].location = (0, 3.6 + .3 * max(0, v - .4), zz)
    rise(S["pil"], (1.9, 2.4, 0), t, lbeat("s03", 4), .4)
    go("s03", [(0, (1.1, -1.5, .75), (0, 2.4, .95), 30), (2, (.55, 2.35, 1.3), (0, 3.6, 1.05), 40), (4, (3.8, -1.6, 1.4), (1.2, 2.6, 1.3), 30),
               (6, (4.2, -2.2, .9), (1.9, 2.4, 2.4), 34)], t, 3.0)


def s_s04():                                   # ニクラウス：ゴルフのグリーン。金の 1 人のパット → カップイン → 偏差値 85 の柱
    stage("golf"); cyl("cup", .055, .02, (0, 2.2, .003), plain("cupm", (.01, .01, .01), .9), 32)
    cyl("stick", .008, 1.3, (0, 2.2, .65), plain("stickm", (.95, .95, .93), .4), 16); box("flag", (.36, .006, .22), (.185, 2.2, 1.18), plain("flagm", (.9, .1, .08), .6), bevel=0)
    S["g"] = fig("golfer", (-.3, -1.1, 0), .55, goldfig(), rz=-.3)
    pt = empty("putter", (-.14, -1.02, .42)); parent(cyl("pt_s", .006, .42, (0, 0, -.21), plain("shaft", (.75, .75, .78), .2, metal=1.0), 16), pt)
    parent(box("pt_h", (.09, .03, .025), (.03, 0, -.42), plain("ironh", (.7, .7, .72), .25, metal=1.0), bevel=.006), pt); S["pt"] = pt; ANIM.append(pt)
    S["ball"] = sphere("gball", .028, (0, -1.0, .028), plain("gbw", (.95, .95, .93), .35, coat=.3), 32); ANIM.append(S["ball"])
    S["pil"] = pillar("p85g", (1.9, 3.3, 0), (85 - 50) * .08, label="85")


def a_s04(u, t, f):
    t1, t2 = lbeat("s04", 1), lbeat("s04", 2); sw = clamp((t - (t1 - .35)) / .35); S["pt"].rotation_euler = (-.35 * math.sin(math.pi * sw) if t < t1 else .25 * eio(clamp((t - t1) / .2)), 0, 0)
    if t < t1:
        S["ball"].location = (0, -1.0, .028)
    elif t < t2:
        k = eout(clamp((t - t1) / (t2 - t1))); S["ball"].location = (0, lerp(-1.0, 2.2, k), .028)
    else:
        S["ball"].location = (0, 2.2, max(-.04, .028 - 2.5 * (t - t2)))
    rise(S["pil"], (1.9, 3.3, 0), t, lbeat("s04", 4), .4)
    go("s04", [(0, (.12, -2.3, .22), (0, .9, .05), 30), (2, (.45, 1.55, .3), (0, 2.2, .02), 40), (4, (3.8, -1.2, 1.4), (1.2, 2.9, 1.3), 30),
               (6, (4.2, -1.8, .9), (1.9, 3.3, 2.4), 34)], t, 3.0)


def s_s05():                                   # カッブ：野球場。打球が上がる → 偏差値 86 の柱（87 の隣）
    stage("diamond"); S["bat"] = fig("hitter", (0, -2.35, 0), .55, goldfig(), rz=.3)
    b = bat("bbat", 1.0); b.location = (.15, -2.3, .45); ANIM.append(b); S["bb"] = b
    S["ball"] = sphere("bball", .06, (0, 0, -50), plain("whiteball", (.93, .93, .9), .4, coat=.3), 24); ANIM.append(S["ball"])
    S["pil"] = pillar("p86", (2.4, -1.0, 0), (86 - 50) * .08, label="86")


def a_s05(u, t, f):
    t1 = lbeat("s05", 1); sw = eio(clamp((t - (t1 - .12)) / .2)); S["bb"].rotation_euler = (0, -.6 + 2.2 * sw, .3 + 1.6 * sw)
    if t < t1:
        S["ball"].location = (lerp(0, .1, clamp((t - (t1 - .4)) / .4)), lerp(1.5, -2.2, clamp((t - (t1 - .4)) / .4)), .55)
    else:
        v = t - t1; S["ball"].location = (.1 - 1.8 * v, -2.2 + 7 * v, .55 + 5 * v - 4.9 * v * v * .5)
    rise(S["pil"], (2.4, -1.0, 0), t, lbeat("s05", 3), .4)
    go("s05", [(0, (1.6, -4.4, .8), (0, -2.3, .45), 34), (1, (-.4, -5.5, .5), (-.6, 2.0, 1.4), 28), (3, (5.6, -4.8, 1.4), (2.9, -1.0, 1.4), 30), (5, (6.2, -5.6, .9), (2.9, -1.0, 2.4), 34)], t, 3.0)


def s_s06():                                   # ペレ：サッカー場。球がゴールへ → 偏差値 87 の柱
    stage("pitch"); wh = plain("post", (.95, .95, .93), .4)
    for x in (-1.2, 1.2):
        cyl("gp%g" % x, .04, .8, (x, 3.0, .4), wh, 24)
    cb = cyl("gbar", .04, 2.48, (0, 3.0, .8), wh, 24); cb.rotation_euler = (0, math.pi / 2, 0)
    net = plain("net", (.95, .95, .95), .6); nn = plane("netp", 2.4, .8, (0, 3.5, .4), net, rot=(math.pi / 2, 0, 0))
    S["ball"] = sphere("sb", .11, (0, 0, -50), plain("whiteball", (.93, .93, .9), .4, coat=.3), 32); ANIM.append(S["ball"])
    S["kick"] = fig("kicker", (.4, -2.0, 0), .55, goldfig(), rz=.2)
    S["pil"] = pillar("p87", (2.6, 1.0, 0), (87 - 50) * .08, label="87")


def a_s06(u, t, f):
    t1, t2 = lbeat("s06", 1), lbeat("s06", 2)
    if t < t1:
        S["ball"].location = (.3, -1.7, .11)
    else:
        k = clamp((t - t1) / (t2 - t1)); S["ball"].location = (lerp(.3, -.4, k), lerp(-1.7, 3.3, k), .11 + .55 * math.sin(math.pi * min(k, 1)) * .9 + (.25 if k >= 1 else 0) * 0)
    rise(S["pil"], (2.6, 1.0, 0), t, lbeat("s06", 4), .4)
    go("s06", [(0, (1.4, -3.6, .7), (.3, -1.6, .3), 36), (2, (-.2, .2, 1.1), (-.3, 3.2, .4), 32), (4, (4.6, -3.6, 1.6), (2.4, 1.0, 1.4), 30), (6, (5.2, -4.4, 1.0), (2.6, 1.0, 2.6), 34)], t, 3.0)


def s_s07():                                   # 歴史に残る天才たちでも 84〜87：5 本の柱がほとんど同じ高さに並ぶ
    stage("arena"); spot("sp", (0, -6, 8), (0, 0, 1), 3000, size=1.0, ang=1.3); S["ps"] = []; reflector("rf", (0, -16, 4), (0, 0, 2), 16, 1100)
    for i, (nm, dv) in enumerate(GENIUS):
        x = (i - 2) * 1.0; h = (dv - 50) * .08; o = pillar("g%d" % i, (x, 0, 0), h, w=.62, label=str(dv)); S["ps"].append((o, x))
        parent(label("gn%d" % i, nm, (0, -.33, h + 1.0), .15), o); o["h"] = h + 1.3


GENIUS = [("ジョーダン", 84), ("ボルト", 85), ("ニクラウス", 85), ("カッブ", 86), ("ペレ", 87)]


def a_s07(u, t, f):
    for i, (o, x) in enumerate(S["ps"]):
        rise(o, (x, 0, 0), t, lbeat("s07", 1 + i // 2), .35)
    go("s07", [(0, (-4.8, -3.4, 1.4), (-1.2, 0, 2.2), 30), (3, (0, -9.2, 2.2), (0, 0, 2.2), 30), (5, (4.6, -3.8, 2.4), (.6, 0, 2.6), 30)], t, 3.0)


def s_s08():                                   # でも、ひとりだけ：クリケット場。87・86 の柱の横から、ブラッドマンの柱が空へ
    stage("cricket")
    dm = gold_mat("goldpil_dim", .3, (.6, .45, .22)); S["gq"] = []
    for i, (nm, dv) in enumerate(GENIUS):
        x = -3.4 + i * .6; S["gq"].append((pillar("q%d" % i, (x, 0, 0), (dv - 50) * .08, w=.5, m=dm, label=str(dv), lab_size=.26), x))
    S["pb"] = pillar("qb", (.6, 0, 0), 30.0, w=.9); S["ph"] = photo_frame("phb", "bradman_bat", (2.6, -.6, 0), rz=-.35)
    stumps("stA", (0, 5.0, 0))


def a_s08(u, t, f):
    for o, x in S["gq"]:
        o.location = (x, 0, 0)
    t1 = lbeat("s08", 2); k = clamp((t - t1) / (BP * 3)); S["pb"].location = (.6, 0, -30 + 30 * eio(k) if t > t1 else -30)
    drop(S["ph"], (2.6, -.6, 0), t, lbeat("s08", 5), h=2.0, rz=-.35)
    go("s08", [(0, (-1.2, -6.6, 1.7), (-1.6, 0, 1.6), 30), (2, (2.6, -5.8, .6), (.6, 0, 3.0), 26), (3, (3.4, -7.0, .4), (.6, 0, 9.0), 22), (5, (4.2, -3.8, 1.2), (2.6, -.6, .9), 36),
               (7, (1.0, -9.0, 1.0), (.6, 0, 6.0), 24)], t, 4.0)


def cricket_set(kind="cricket", night=False):
    stage(kind); S["stA"], S["bA"] = stumps("stA", (0, -5.3, 0)); S["stB"], S["bB"] = stumps("stB", (0, 5.3, 0))
    S["bat"], S["bt"] = batter("batter", (.25, -4.75, 0), .9, facing=0.0)
    S["bowl"] = fig("bowler", (-.3, 8.0, 0), .9, ceramic(), rz=math.pi); S["ball"] = ball("cb", .045)
    for i, (x, y) in enumerate(((-4.5, 1.5), (4.8, -1.0), (3.2, 6.0), (-3.8, -6.5), (5.5, 4.0))):   # 守る人
        fig("fld%d" % i, (x, y, 0), .9, ceramic(), rz=random.Random(i).uniform(0, 6))


def bowler_run(t, t_rel):
    o = S["bowl"]; k = clamp(1 - (t_rel - t) / 1.2) if t < t_rel else 1.0
    o.location = (-.3, 8.0 - 2.6 * eio(k), .03 * abs(math.sin(t * 12)) * (k < 1))


def s_s09():
    cricket_set()


def a_s09(u, t, f):                            # 投げる（拍 2）→ 弾む → 打つ（拍 3）→ 打者が反対側へ走る（拍 5〜8）
    t_rel, t_hit = lbeat("s09", 2), lbeat("s09", 3); bowler_run(t, t_rel)
    if t < t_rel:
        S["ball"].location = (-.3, 5.4, -50)
    elif t < t_hit:
        S["ball"].location = path_bowl(t, t_rel, t_hit, (-.2, 5.3, 1.9), (.1, -1.5, .05), (.3, -4.6, .5))
    else:
        v = t - t_hit; S["ball"].location = (.3 + 4.5 * v, -4.6 + 3.0 * v, max(.045, .5 + 2.2 * v - 4.9 * v * v))
    sw = eio(clamp((t - (t_hit - .12)) / .2)); S["bt"].rotation_euler = (-1.4 * sw, -.5, 0)
    tr = lbeat("s09", 5); k = clamp((t - tr) / (BP * 3))
    S["bat"].location = (.25, lerp(-4.75, 4.6, eio(k)), .03 * abs(math.sin(t * 12)) * (0 < k < 1)); S["bt"].location = (S["bat"].location.x + .22, S["bat"].location.y - .05, .56)
    go("s09", [(0, (2.5, -9.5, 1.6), (0, -3.0, .5), 30), (2, (-1.2, 7.2, 2.4), (0, 2.0, .6), 30), (3, (1.8, -7.2, .7), (.2, -5.0, .6), 34), (5, (4.0, -2.0, 1.4), (0, -1.0, .5), 26),
               (8, (2.6, 7.4, 1.2), (0, 4.0, .5), 30)], t, 3.0)


def s_s10():
    cricket_set(); g = gold_mat("coin", .15); S["coins"] = []
    for i in range(6):
        o = cyl("coin%d" % i, .3, .08, (0, 0, -50), g, 48, bevel=.01); S["coins"].append(o); ANIM.append(o)


def a_s10(u, t, f):                            # 球が柱に当たる（拍 2、ベイルが飛ぶ）→ 金の玉（点）が拍ごとに積み上がる（拍 4〜9）
    t_rel, t_hit = lbeat("s10", 1), lbeat("s10", 2); bowler_run(t, t_rel)
    if t < t_rel:
        S["ball"].location = (-.3, 5.4, -50)
    elif t < t_hit:
        S["ball"].location = path_bowl(t, t_rel, t_hit, (-.2, 5.3, 1.9), (-.05, -1.2, .05), (0, -5.3, .3))
    else:
        v = t - t_hit; S["ball"].location = (0, -5.3 - 1.2 * v, max(.045, .3 - 2 * v))
    bails_fly(S["bA"], t, t_hit)
    S["bt"].rotation_euler = (0, -.5, 0)
    for i, o in enumerate(S["coins"]):
        drop(o, (1.6, -3.4, .04 + .082 * i), t, lbeat("s10", 4 + i), h=1.2, dur=.25)
    go("s10", [(0, (1.6, -7.6, .5), (0, -5.3, .45), 40), (2, (.9, -6.4, .35), (0, -5.3, .55), 55), (4, (3.4, -5.4, 1.0), (1.6, -3.4, .4), 38), (7, (3.6, -6.0, 1.3), (1.6, -3.4, .6), 34)], t, 2.8)


def s_s11():                                   # 名選手でも 60 点前後：低い柱の列
    stage("arena"); spot("sp", (0, -6, 8), (0, 0, 0), 2600, size=1.0, ang=1.3)
    R = random.Random(8); dm = gold_mat("goldpil_dim", .3, (.6, .45, .22)); S["ps"] = []
    for i in range(12):
        av = R.uniform(55, 61.9); x = (i - 5.5) * .75; o = pillar("a%d" % i, (x, 0, 0), av * .05, w=.5, m=dm); S["ps"].append((o, x))


def a_s11(u, t, f):
    for i, (o, x) in enumerate(S["ps"]):
        rise(o, (x, 0, 0), t, lbeat("s11", 1 + i // 3), .35)
    go("s11", [(0, (-6.5, -4.5, 1.2), (-3.0, 0, 1.4), 32), (3, (0, -8.0, 2.6), (0, 0, 1.6), 28), (6, (5.5, -4.0, 1.0), (2.0, 0, 2.2), 30)], t, 3.0)


def s_s12():                                   # 99.94：金の柱が、60 の列の 1.7 倍の高さへ
    s_s11(); S["pb"] = pillar("b9994", (0, -1.4, 0), 99.94 * .05, w=.75, label="99.94", lab_size=.5); spot("spb", (0, -5, 9), (0, -1.4, 3), 2500, size=.5, ang=.6)


def a_s12(u, t, f):
    for i, (o, x) in enumerate(S["ps"]):
        o.location = (x, 0, 0)
    rise(S["pb"], (0, -1.4, 0), t, lbeat("s12", 1), .4)
    go("s12", [(0, (0, -9.0, 1.0), (0, 0, 2.0), 28), (1, (2.4, -7.6, .5), (0, -1.4, 3.6), 26), (3, (0, -10.5, 3.2), (0, -1.4, 3.4), 24)], t, 4.0)


def s_s13():                                   # 偏差値 94：人の山と物差し。天才 5 人（84〜87）から、金の 1 人が 94 へ。「＋7」
    stage("arena"); spot("sp", (2, -6, 9), (2.5, -1, 0), 3000, size=1.0, ang=1.4); S["bell"] = bell("c", .32); ruler("rl", (50, 60, 70, 80, 90, 100))
    S["gs"] = [fig("gz%d" % i, (dvx(dv), -.15 - .3 * (i % 2), 0), .42, goldfig(), rz=.2) for i, (nm, dv) in enumerate(GENIUS)]
    S["bm"] = fig("brad", (dvx(87), -.9, 0), .5, goldfig()); spot("spb", (dvx(94), -2.5, 4), (dvx(94), -.5, .3), 1400, size=.4, ang=.8)
    S["p7"] = text_obj("plus7", "+7", (0, 0, 0), .32, gold_mat("goldtext", .2), extrude=.03); ANIM.append(S["p7"])


def a_s13(u, t, f):
    t1 = lbeat("s13", 1); k = eio(clamp((t - (t1 - .4)) / .4)); S["bm"].location = (lerp(dvx(87), dvx(94), k), lerp(-.9, -.4, k), .03 * abs(math.sin(t * 10)) * (0 < k < 1))
    drop(S["p7"], ((dvx(87) + dvx(94)) / 2, -.6, 1.05), t, lbeat("s13", 4), h=1.2)
    go("s13", [(0, (dvx(85.5), -2.6, .9), (dvx(85.5), -.3, .35), 40), (1, (dvx(94) - .3, -2.2, .7), (dvx(94), -.4, .4), 42), (3, (dvx(80), -6.4, 2.4), (dvx(85), -.4, .4), 30),
               (4, (dvx(90.5), -3.2, 1.2), (dvx(90.5), -.5, .8), 36)], t, 3.0)


def s_s14():                                   # 偏差値 94：金の数字の記念碑（暗い展示室、光の柱）
    stage("arena"); spot("sp", (0, -2.5, 8), (0, 0, 1.0), 3200, size=.6, ang=.7, blend=.5)
    wd = pbr_mat("plinth", "dark_wood", 1.0, (.4, .32, .26), 1.0, box_proj=True); box("base", (3.0, 1.4, .6), (0, 0, .3), wd, bevel=.03); reflector("rf", (0, -14, 3), (0, 0, 1.4), 6, 450)
    label("hensa", "偏差値", (0, -.72, .3), .26)
    S["num"] = text_obj("n94", "94", (0, 0, 1.45), 1.7, gold_mat("goldnum", .12), extrude=.14); ANIM.append(S["num"])


def a_s14(u, t, f):
    S["num"].location = (0, 0, 1.45 + .02 * math.sin(t * 2))
    go("s14", [(0, (-3.6, -4.6, .8), (0, 0, 1.2), 34), (2, (2.8, -4.2, 1.6), (0, 0, 1.3), 34), (5, (0, -6.5, 1.3), (0, 0, 1.25), 30)], t, 4.0, mv=.5)


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
