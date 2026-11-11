#!/usr/bin/env python3
"""Poly Haven（https://polyhaven.com 、すべて CC0、アカウント不要）から pilot_051 の素材を落とす。
    python assets/polyhaven.py        → assets/ph/<種類>/<名前>/…（git に入れない。.gitignore の work/ ではないので下の IGNORE を参照）
API：https://api.polyhaven.com/files/<id>（公式の公開 API）。HDRI は 4k の .hdr、質感は 2k の各マップ（jpg / exr）、模型は 2k の glTF。
権利の記録は scripts/pilot_051/assets.md。"""
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ph"
HDRIS = ["bloem_train_track_clear", "noon_grass", "rolling_hills", "kloofendal_43d_clear_puresky", "kloofendal_48d_partly_cloudy_puresky"]
TEXTURES = ["gravel_floor_02", "rocky_gravel", "rusty_metal_02", "brushed_concrete", "grass_path_2", "leafy_grass", "sparse_grass", "forest_ground_04"]
MODELS = ["grass_medium_01", "grass_medium_02", "grass_bermuda_01", "dandelion_01", "celandine_01", "nettle_plant", "shrub_01", "shrub_02", "shrub_04",
          "island_tree_01", "island_tree_02", "tree_small_02", "rock_moss_set_01"]
MAPS = ["Diffuse", "nor_gl", "Rough", "Displacement", "AO", "arm", "Metal"]


def get(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    req = urllib.request.Request(url, headers={"User-Agent": "reverse-pilot051/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())
    print("  ", path.relative_to(HERE), path.stat().st_size // 1024, "KB", flush=True)


def files(aid):
    req = urllib.request.Request(f"https://api.polyhaven.com/files/{aid}", headers={"User-Agent": "reverse-pilot051/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    only = sys.argv[1:]
    for h in HDRIS:
        if only and h not in only:
            continue
        f = files(h)["hdri"]["4k"]["hdr"]; get(f["url"], OUT / "hdri" / f"{h}_4k.hdr")
    for t in TEXTURES:
        if only and t not in only:
            continue
        f = files(t)
        for m in MAPS:
            if m in f and "2k" in f[m]:
                fm = f[m]["2k"]; ext = "jpg" if "jpg" in fm else "exr" if "exr" in fm else next(iter(fm))
                get(fm[ext]["url"], OUT / "tex" / t / f"{t}_{m}_2k.{ext}")
    for mdl in MODELS:
        if only and mdl not in only:
            continue
        g = files(mdl)["gltf"]["2k"]["gltf"]
        get(g["url"], OUT / "models" / mdl / Path(g["url"]).name)
        for rel, inc in g.get("include", {}).items():
            get(inc["url"], OUT / "models" / mdl / rel)


if __name__ == "__main__":
    main()
