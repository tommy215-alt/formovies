#!/usr/bin/env python3
"""pilot_060 v3 の質感（Poly Haven、すべて CC0）を落とし、左上からの光で陰影を焼き込んだ 1 枚の jpg にする。
    python assets/textures.py   → assets/tex/<key>.jpg（make_assets.py が assets.js に埋め込む）
元のファイルは assets/ph/（git に入れない）。権利は scripts/pilot_060/assets.md。"""
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
RAW, OUT = HERE / "ph", HERE / "tex"
UA = {"User-Agent": "reverse-pilot060/1.0"}
# key: (Poly Haven の id, 色の掛け算 (r,g,b), 陰影の強さ)
TEX = {
    "wood": ("lacquered_cherry_wood", (1.0, .95, .9), .9),     # 時計の箱
    "plank": ("hinoki_planks", (1.05, 1.0, .92), 1.0),          # 木の札
    "stone": ("japanese_stone_wall", (1.0, 1.0, 1.0), 1.3),     # ルールの石垣
    "granite": ("granite_tile", (.55, .56, .6), 1.0),           # 戦争の石碑
    "rock": ("rock_wall_08", (.95, .95, .95), 1.3),             # 津波の石碑
    "concrete": ("concrete_wall_006", (.95, .98, 1.05), 1.0),   # これからの時代
    "tatami": ("tatami_mat", (1.0, 1.0, 1.0), .9),              # いま
}


def get(url, path):
    if path.exists() and path.stat().st_size:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        path.write_bytes(r.read())
    return path


def main():
    OUT.mkdir(exist_ok=True); credits = []
    for key, (pid, tint, k) in TEX.items():
        with urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{pid}", headers=UA), timeout=60) as r:
            f = json.load(r)
        d = get(f["Diffuse"]["1k"]["jpg"]["url"], RAW / f"{pid}_diff_1k.jpg")
        n = get(f["nor_gl"]["1k"]["jpg"]["url"], RAW / f"{pid}_nor_gl_1k.jpg")
        D = np.asarray(Image.open(d).convert("RGB"), np.float32) / 255
        N = np.asarray(Image.open(n).convert("RGB"), np.float32) / 255 * 2 - 1
        L = np.array([-.55, .55, .63]); L /= np.linalg.norm(L)        # 左上から（OpenGL の法線は +y が上）
        sh = np.clip((N * L).sum(-1), 0, 1); sh = 1 + k * (sh - sh.mean())
        img = np.clip(D * sh[..., None] * np.array(tint), 0, 1)
        Image.fromarray((img * 255).astype(np.uint8)).save(OUT / f"{key}.jpg", quality=88)
        credits.append({"key": key, "polyhaven": pid, "license": "CC0", "url": f"https://polyhaven.com/a/{pid}"})
        print(key, pid)
    (OUT / "credits.json").write_text(json.dumps(credits, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
