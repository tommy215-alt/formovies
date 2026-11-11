"""猫だけを確かめる（blender -b -P blender/test_cat.py -- test）。work/test/cat_*.png
環境変数：ONLY＝描く画の番号（例 "013"）、FUR=0 で毛なし、PCT＝解像度の %（既定 25）、GPU=1 で GPU（既定は CPU）、DUMP=1 で部品の大きさを出す"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import cat
sc.cycles.device = "GPU" if os.environ.get("GPU") else "CPU"; sc.cycles.samples = int(os.environ.get("SPP", "8"))
sc.render.resolution_percentage = int(os.environ.get("PCT", "25")); sc.render.use_motion_blur = False
sky.set(0, 55, 150, 6.0); sc.view_settings.exposure = -4.5; set_haze((.8, .86, .93), .9, 150., 4000.)
bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=2, y_segments=2, size=50)
mesh_obj("ground", bm, [mat("g", (.32, .3, .27), .9)])
out = os.path.join(HERE, "..", "work", "test"); os.makedirs(out, exist_ok=True)
FUR = os.environ.get("FUR", "1") != "0"
COATS = ["mike", "chatora", "kuro", "shiro", "sabatora", "hachiware"]
only = os.environ.get("ONLY", "")
need = set(COATS) if (not only or "0" in only or "6" in only) else set()
for i, cc in (("1", "mike"), ("2", "chatora"), ("3", "hachiware"), ("4", "mike"), ("5", "sabatora"), ("7", "chatora"), ("8", "mike"), ("9", "kuro"), ("a", "mike"), ("b", "mike"), ("b", "chatora")):
    if not only or i in only:
        need.add(cc)
C = {}
for k, cc in enumerate(COATS):
    if cc in need:
        C[cc] = cat.build_cat("c_" + cc, cc, seed=k + 1, fur=FUR)
RING = cat.harness(C["hachiware"]) if "hachiware" in C else None
log("built", {k: v["nhair"] for k, v in C.items()})
if os.environ.get("DUMP"):
    bpy.context.view_layer.update()
    for o in MONC.objects:
        if o.type == "MESH" and o.name.startswith("c_mike_") and o.parent is not None:
            bb = [o.matrix_world @ Vector(c_) for c_ in o.bound_box]; lo = [min(v[i] for v in bb) for i in range(3)]; hi = [max(v[i] for v in bb) for i in range(3)]
            print("DUMP", o.name, [round(x, 3) for x in lo], [round(x, 3) for x in hi], flush=True)


def hide_all_but(names):
    for cc, c in C.items():
        h = cc not in names
        for o in MONC.objects:
            if o.name.startswith(c["name"] + "_") or o.name == c["name"]:
                o.hide_render = h


def shot(i, fn):
    if only and i not in only:
        return
    cat.DBG.clear(); fn(); bpy.context.view_layer.update()
    if cat.DBG:
        log("IK short", cat.DBG)
    sc.render.filepath = os.path.join(out, f"cat_{i}.png"); bpy.ops.render.render(write_still=True); log("view", i)


def v0():   # 6 匹の並び（立つ）
    hide_all_but(COATS)
    for k, cc in enumerate(COATS):
        if cc in C:
            cat.cpose(C[cc], ((k % 3 - 1) * .5 + (k // 3) * .12, -(k // 3) * .55), .35 + .2 * (k % 3 - 1), "stand", t=k * .7)
    cam.look((.5, 1.9, .75), (0, -.28, .12), 30)


def v1():   # 顔のアップ
    hide_all_but(["mike"]); cat.cpose(C["mike"], (0, 0), 0, "stand", t=.3, head=(.05, 0))
    cam.look((.08, .78, .33), (0, .27, .3), 60)


def v2():   # 全身 3/4
    hide_all_but(["chatora"]); cat.cpose(C["chatora"], (0, 0), 0, "walk", t=.5, ph=.2)
    cam.look((.85, .85, .32), (0, 0, .17), 42)


def v3():   # 引っぱる（胴輪）
    hide_all_but(["hachiware"]); cat.cpose(C["hachiware"], (0, 0), 0, "pull", t=.4, ph=.3)
    cam.look((.75, .75, .22), (0, .05, .15), 42)


def v4():   # 丸まって寝る
    hide_all_but(["mike"]); cat.cpose(C["mike"], (0, 0), 0, "curl", t=0)
    cam.look((.3, .4, .75), (0, 0, .06), 42)


def v5():   # あくび
    hide_all_but(["sabatora"]); cat.cpose(C["sabatora"], (0, 0), 0, "yawn", t=.2)
    cam.look((.35, .75, .3), (0, .2, .27), 50)


def v6():   # いろいろなポーズ
    hide_all_but(COATS); modes = ["sit", "loaf", "groom", "stretch", "walk", "pull"]
    for k, cc in enumerate(COATS):
        if cc in C:
            cat.cpose(C[cc], ((k % 3 - 1) * .55 + (k // 3) * .12, -(k // 3) * .6), .6, modes[k], t=k * .7, ph=.3)
    cam.look((.5, 1.9, .75), (0, -.3, .1), 30)


def v8():   # 丸まって寝る（横から、毛の確認）
    hide_all_but(["mike"]); cat.cpose(C["mike"], (0, 0), 0, "curl", t=0)
    cam.look((.9, -.1, .3), (0, 0, .08), 40)


def v9():   # グルーミング
    hide_all_but(["kuro"]); cat.cpose(C["kuro"], (0, 0), 0, "groom", t=0)
    cam.look((.55, .7, .3), (0, .1, .2), 45)


def va():   # 香箱座り（横）と丸まる（上から）
    hide_all_but(["mike"]); cat.cpose(C["mike"], (0, 0), 0, "curl", t=0)
    cam.look((-.05, -.25, .75), (-.1, -.05, 0), 40)


def vb():
    hide_all_but(["mike"]); cat.cpose(C["mike"], (0, 0), 0, "curl", t=0)
    cam.look((.55, .45, .35), (0, 0, .07), 40)


def v7():   # 横から（体の形の確認）
    hide_all_but(["chatora"]); cat.cpose(C["chatora"], (0, 0), 0, "stand", t=.5)
    cam.look((1.3, 0, .2), (0, 0, .17), 35)


for i, f in enumerate((v0, v1, v2, v3, v4, v5, v6, v7, v8, v9, va, vb)):
    shot("0123456789ab"[i], f)
