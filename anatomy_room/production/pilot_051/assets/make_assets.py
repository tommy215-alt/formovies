#!/usr/bin/env python3
"""pilot_050 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。本物の写真は使わない（もしも設計、CG と計算の地図だけ）。

v2（2026-11-06 ユーザー「フォントはゴシック風でもっと堅めのフォントで、真面目感あるように」）：
BIZ UDPゴシック Bold（モリサワ、字幅が文字ごとに変わる版、SIL OFL 1.1。assets/fonts/）を、画面に出る文字だけに絞って埋め込む（font_biz）。
renderer.html と assets/plan.js の文字を拾うので、画面の文字を変えたら python plan.py のあとに再実行する。
"""
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {}, fonts=False)
    text = (HERE.parent / "renderer.html").read_text(encoding="utf-8") + (HERE / "plan.js").read_text(encoding="utf-8")
    text += "0123456789:：.,，、。・（）()／/～〜-+％%億万体秒分時間日目後前約経過ゾンビ早送り ？！?!"
    chars = "".join(sorted(set(c for c in text if c.strip())))
    p = HERE / "assets.js"; out = json.loads(p.read_text(encoding="utf-8")[len("window.ASSETS = "):].rstrip().rstrip(";"))
    out["font_biz"] = base64.b64encode(kit.font_subset(HERE / "fonts" / "BIZUDPGothic-Bold.ttf", chars)).decode()
    # タイトルの帯は Dela Gothic One（SIL OFL 1.1）。縁取りで太くすると字がつぶれるので、太い書体そのものを使う（2026-11-10 ユーザー）
    tt = "".join(sorted(set("猫 何匹で 新幹線は動く？")))
    out["font_title"] = base64.b64encode(kit.font_subset(HERE / "fonts" / "DelaGothicOne-Regular.ttf", tt)).decode()
    p.write_text("window.ASSETS = " + json.dumps(out) + ";\n", encoding="utf-8")
    print("font_biz", len(chars), "文字", len(out["font_biz"]) // 1024, "KB")
