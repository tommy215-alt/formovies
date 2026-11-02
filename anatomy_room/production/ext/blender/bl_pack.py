"""Blender で描いたコマ（work/blender/<ショット>/f_0001.png …）を、renderer.html が読める JS にする（ext/blender/blkit.py の 3）。

使い方：python anatomy_room/production/ext/blender/bl_pack.py 035 [ショット名 ...]
- f_0001.js：BLF("l01", 1, "data:image/jpeg;base64,…")。file:// の画像を canvas に描くと canvas が汚れて getImageData が使えないため、data URI にする。
- JPEG の品質 92（完成版は x264 CRF 18 なので、これ以上は差が出ない）。PNG は残す（作り直しのとき）。
- work/blender/index.js：BL_META（ショットごとのコマ数と、描いたときの開始時刻と版）。production_script.py の extra_files に
  "work/blender/index.js" と "../ext/blender/blframes.js" を入れる（rv がこの変化を見て、描き直した場面だけを作り直す）。
"""
import base64, hashlib, io, json, sys
from pathlib import Path
from PIL import Image

PROD = Path(__file__).resolve().parents[2]


def pack(ep, only=None):
    root = PROD / f"pilot_{ep}" / "work" / "blender"
    meta = {}
    for d in sorted(p for p in root.iterdir() if p.is_dir() and (p / "meta.json").exists()):
        m = json.loads((d / "meta.json").read_text())
        pngs = sorted(d.glob("f_*.png"))
        if not pngs:
            continue
        ver = hashlib.sha256("".join(f"{p.name}{p.stat().st_size}{p.stat().st_mtime_ns}" for p in pngs).encode()).hexdigest()[:12]
        meta[d.name] = {"frames": len(pngs), "start": m["start"], "end": m["end"], "ver": ver}   # ver：描き直したら変わる（rv が index.js の変化で場面を作り直す）
        if only and d.name not in only:
            continue
        for p in pngs:
            js = p.with_suffix(".js")
            if js.exists() and js.stat().st_mtime >= p.stat().st_mtime:
                continue
            buf = io.BytesIO(); Image.open(p).convert("RGB").save(buf, "JPEG", quality=92)
            i = int(p.stem.split("_")[1])
            js.write_text(f'BLF("{d.name}",{i},"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}");\n', encoding="ascii")
        print(d.name, len(pngs), flush=True)
    (root / "index.js").write_text("window.BL_META = " + json.dumps(meta) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    pack(sys.argv[1], sys.argv[2:])
