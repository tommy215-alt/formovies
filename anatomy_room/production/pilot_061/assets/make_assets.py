#!/usr/bin/env python3
"""pilot_061 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。
写真（assets/photo/、Wikimedia Commons のパブリックドメイン、credits.jsonl。権利は scripts/pilot_061/assets.md）と、
書体：Dela Gothic One・Mochiy Pop One（kit の共通、OFL）＋本文の BIZ UDPゴシック Bold（OFL、assets/fonts/）を画面の文字だけに絞って埋め込む。
画面の文字を変えたら python plan.py のあとに再実行する。"""
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

PHOTOS = {k: (f"photo/{k}.jpg", "RGB") for k in ("vault",)}
PHOTOS["map"] = ("photo/map.jpg", "RGB")
PHOTOS.update({f"tx_{k}": (f"tex/{k}.jpg", "RGB") for k in ("wood", "plank", "concrete")})   # 質感（Poly Haven CC0、pilot_060 の textures.py で作ったもの）

if __name__ == "__main__":
    kit.episode(HERE, PHOTOS, size=2048)   # 地図は 2048 のまま（ほかは元が 1280 以下）
    text = (HERE.parent / "renderer.html").read_text(encoding="utf-8") + (HERE / "plan.js").read_text(encoding="utf-8") + (HERE.parent / "lines.json").read_text(encoding="utf-8")
    text += "0123456789:：.,，、。・（）()／/～〜-+％%億万人トングラム倍位約目安国金％ ？！?!$¥€"
    chars = "".join(sorted(set(c for c in text if c.strip())))
    p = HERE / "assets.js"; out = json.loads(p.read_text(encoding="utf-8")[len("window.ASSETS = "):].rstrip().rstrip(";"))
    out["font_biz"] = base64.b64encode(kit.font_subset(HERE / "fonts" / "BIZUDPGothic-Bold.ttf", chars)).decode()
    p.write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8")
    print("font_biz", len(chars), "文字")
