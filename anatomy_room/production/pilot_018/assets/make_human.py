"""pilot_018：MPFB（MakeHuman の Blender 版。作った人体と素材は CC0）で人体を作り、ポーズをつけて GLB に書き出す。

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
    # 腰かける（ベッド・汽車の座席。手はひざの上）
    "sit": {"Spine": (0, -.08, 1), "Neck": (0, -.2, 1), "Head": (0, -.35, 1),
            "LeftUpLeg": (.1, -1, -.05), "LeftLeg": (0, -.1, -1), "LeftFoot": (0, -1, -.4),
            "LeftArm": (.15, -.25, -1), "LeftForeArm": (-.05, -1, -.3)},
    # 歩く（片足を前へ）
    "walk": {"Neck": (0, -.1, 1), "Head": (0, -.2, 1), "LeftUpLeg": (.08, -.35, -1), "LeftLeg": (0, .15, -1), "RightUpLeg": (-.08, .3, -1), "RightLeg": (0, .45, -1),
             "LeftArm": (.15, .3, -1), "RightArm": (-.15, -.3, -1)},
    # 机に手をついてうつむく（迷い）
    "lean": {"Spine": (0, -.35, 1), "Spine1": (0, -.45, 1), "Neck": (0, -.7, 1), "Head": (0, -.9, 1),
             "LeftArm": (.25, -.55, -.8), "LeftForeArm": (.05, -.3, -1)},
}
ORDER = ["Hips", "Spine", "Spine1", "Spine2", "Neck", "Head", "LeftShoulder", "LeftArm", "LeftForeArm", "RightShoulder", "RightArm", "RightForeArm",
         "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot"]
WHO = {
    "boy": {"macro": {"gender": 1.0, "age": 0.17, "muscle": 0.45, "weight": 0.45, "height": 0.4, "proportions": 0.5},
            "clothes": ["male_casualsuit02", "shoes01"], "hair": "short02"},
    "mother": {"macro": {"gender": 0.0, "age": 0.6, "muscle": 0.45, "weight": 0.55, "height": 0.45, "proportions": 0.55},
               "clothes": ["female_elegantsuit01", "shoes02"], "hair": "ponytail01"},
    "pasteur": {"macro": {"gender": 1.0, "age": 0.85, "muscle": 0.4, "weight": 0.6, "height": 0.45, "proportions": 0.5},
                "clothes": ["male_elegantsuit01", "shoes01"], "hair": "short02"},
    "doctor": {"macro": {"gender": 1.0, "age": 0.62, "muscle": 0.5, "weight": 0.5, "height": 0.55, "proportions": 0.5},
               "clothes": ["male_worksuit01", "shoes01"], "hair": "short04"},
    "keeper": {"macro": {"gender": 1.0, "age": 0.7, "muscle": 0.5, "weight": 0.6, "height": 0.5, "proportions": 0.5},
               "clothes": ["male_casualsuit04", "shoes01"], "hair": "short02"},
}
JOBS = [("boy", "stand"), ("boy", "sit"), ("boy", "walk"), ("mother", "stand"), ("mother", "sit"), ("mother", "walk"),
        ("pasteur", "stand"), ("pasteur", "lean"), ("doctor", "stand"), ("keeper", "stand")]

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