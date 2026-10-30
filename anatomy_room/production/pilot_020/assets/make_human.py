"""pilot_020（pilot_018 の複製）：MPFB（MakeHuman の Blender 版。作った人体と素材は CC0）で人体を作り、ポーズをつけて GLB に書き出す。

Blender を画面なしで動かす：
  blender -b --factory-startup? は使わない（MPFB の拡張を読み込むため、通常の設定で起動する）
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" -b --python make_human.py -- <出力フォルダ> [preview]

ポーズは POSES（骨の名前 → 骨のローカル軸の回転〔度〕）。顔は映さない（後ろ姿・遠景だけで使う）。
"""
import json
import math
import os
import sys

import bpy

ARGV = sys.argv[sys.argv.index("--") + 1:]
OUT = ARGV[0]
PREVIEW = len(ARGV) > 1 and ARGV[1] == "preview"
ONLY = ARGV[2].split(",") if len(ARGV) > 2 else None

from bl_ext.blender_org.mpfb.services.humanservice import HumanService  # noqa: E402
from bl_ext.blender_org.mpfb.services.locationservice import LocationService  # noqa: E402

DATA = LocationService.get_user_data()
R = "mixamorig:"

# 骨を向ける方向（アーマチュアの座標：Z が上、人体は -Y を向く、+X が人体の左）。Left の値だけ書き、Right は X を反転して使う
POSES = {
    # 立つ（少しうつむく）
    "stand": {"Neck": (0, -.12, 1), "Head": (0, -.3, 1), "LeftArm": (.18, .02, -1), "LeftForeArm": (.06, -.12, -1)},
    # そりを引く：体を前に倒し、片足を大きく前へ。手は胸の前（引き綱）。A と B で足を入れ替える
    "haulA": {"Spine": (0, -.35, 1), "Spine1": (0, -.4, 1), "Neck": (0, -.35, 1), "Head": (0, -.15, 1),
              "LeftUpLeg": (.08, -.55, -1), "LeftLeg": (0, -.05, -1), "RightUpLeg": (-.08, .35, -1), "RightLeg": (0, .55, -1),
              "LeftArm": (.25, -.45, -1), "LeftForeArm": (-.2, -1, .35)},
    "haulB": {"Spine": (0, -.35, 1), "Spine1": (0, -.4, 1), "Neck": (0, -.35, 1), "Head": (0, -.15, 1),
              "LeftUpLeg": (.08, .35, -1), "LeftLeg": (0, .55, -1), "RightUpLeg": (-.08, -.55, -1), "RightLeg": (0, -.05, -1),
              "LeftArm": (.25, -.45, -1), "LeftForeArm": (-.2, -1, .35)},
    # 吹雪の中へ歩き出す（前かがみ、腕を体に寄せる）
    "walk": {"Spine": (0, -.2, 1), "Neck": (0, -.3, 1), "Head": (0, -.3, 1), "LeftUpLeg": (.08, -.35, -1), "LeftLeg": (0, .15, -1), "RightUpLeg": (-.08, .3, -1), "RightLeg": (0, .45, -1),
             "LeftArm": (.12, -.15, -1), "LeftForeArm": (-.1, -.6, -.5)},
    # 座る（テントの中）
    "sit": {"Spine": (0, -.15, 1), "Neck": (0, -.35, 1), "Head": (0, -.45, 1),
            "LeftUpLeg": (.15, -1, -.05), "LeftLeg": (0, -.25, -1), "LeftFoot": (0, -1, -.4),
            "LeftArm": (.15, -.3, -1), "LeftForeArm": (-.1, -1, -.2)},
}
ORDER = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "RightShoulder", "RightArm", "RightForeArm",
         "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot"]
WHO = {   # 隊員（大人の男性 2 体型）。服は作業着（顔は映さない：後ろ姿・逆光・吹雪の中の影）
    "man": {"macro": {"gender": 1.0, "age": 0.55, "muscle": 0.6, "weight": 0.55, "height": 0.55, "proportions": 0.5},
            "clothes": ["male_worksuit01", "shoes01"], "hair": "short02"},
    "man2": {"macro": {"gender": 1.0, "age": 0.5, "muscle": 0.55, "weight": 0.6, "height": 0.48, "proportions": 0.5},
             "clothes": ["male_casualsuit04", "shoes01"], "hair": "short04"},
}
JOBS = [("man", "haulA"), ("man", "haulB"), ("man2", "haulA"), ("man2", "haulB"), ("man", "stand"), ("man", "walk"), ("man", "sit"), ("man2", "sit")]


def build(who):
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    w = WHO[who]
    macro = {"gender": .5, "age": .5, "muscle": .5, "weight": .5, "proportions": .5, "height": .5, "cupsize": .5, "firmness": .5,
             "race": {"asian": .1, "caucasian": .8, "african": .1}}
    macro.update(w["macro"])
    body = HumanService.create_human(macro_detail_dict=macro)
    body.name = "body"
    rig = HumanService.add_builtin_rig(body, "mixamo")
    for c in w["clothes"]:
        HumanService.add_mhclo_asset(os.path.join(DATA, "clothes", c, c + ".mhclo"), body, asset_type="Clothes", subdiv_levels=0, material_type="MAKESKIN")
    HumanService.add_mhclo_asset(os.path.join(DATA, "hair", w["hair"], w["hair"] + ".mhclo"), body, asset_type="Hair", subdiv_levels=0, material_type="MAKESKIN")
    return body, rig


def pose(rig, name):
    """親から順に、骨の向き（Y 軸）を指定の方向へ回す（骨の付け根を中心に）。"""
    from mathutils import Matrix, Vector
    for pb in rig.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = (1, 0, 0, 0)
    bpy.context.view_layer.update()
    want = {}
    for b, (x, y, z) in POSES[name].items():
        want[b] = (x, y, z)
        if b.startswith("Left"):
            want["Right" + b[4:]] = (-x, y, z)
    for b in ORDER:
        if b not in want:
            continue
        pb = rig.pose.bones.get(R + b)
        if pb is None:
            continue
        m = pb.matrix.copy()
        cur = (m.to_3x3() @ Vector((0, 1, 0))).normalized()
        q = cur.rotation_difference(Vector(want[b]).normalized())
        head = m.to_translation()
        pb.matrix = Matrix.Translation(head) @ q.to_matrix().to_4x4() @ Matrix.Translation(-head) @ m
        bpy.context.view_layer.update()


def export(path):
    bpy.ops.object.select_all(action="DESELECT")
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True,
                              export_skins=False, export_animations=False, export_morph=False, export_materials="NONE",
                              export_yup=True, export_normals=True, export_texcoords=True)


def preview(path):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = 600, 800
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    shots = []
    for i, (loc, rot) in enumerate([((3.2, -3.2, 1.2), (82, 0, 45)), ((-3.2, 3.2, 1.2), (82, 0, 225))]):
        cam.location = loc
        cam.rotation_euler = tuple(math.radians(a) for a in rot)
        sc.render.filepath = path.replace(".png", f"_{i}.png")
        bpy.ops.render.render(write_still=True)
        shots.append(sc.render.filepath)
    return shots


os.makedirs(OUT, exist_ok=True)
report = {}
for who, pn in JOBS:
    key = f"{who}_{pn}"
    if ONLY and key not in ONLY:
        continue
    body, rig = build(who)
    pose(rig, pn)
    if PREVIEW:
        report[key] = preview(os.path.join(OUT, key + ".png"))
    else:
        p = os.path.join(OUT, key + ".glb")
        export(p)
        report[key] = os.path.getsize(p)
print("RESULT", json.dumps(report))