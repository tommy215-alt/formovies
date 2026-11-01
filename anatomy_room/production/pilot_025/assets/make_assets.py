#!/usr/bin/env python3
"""pilot_025 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。
- sled：ソニック・ウインド 1 号の実物（Smithsonian、CC0）、strap：そりに固定されるスタップ（国立公文書館 111-SC-1500220、パブリックドメイン）、
  faces：加速と減速で顔がゆがむ 6 枚（111-SC-1500221、1954 年 6 月発表、パブリックドメイン）。権利は scripts/pilot_025/assets.md
- 派手な文字のフォント（Dela Gothic One・Mochiy Pop One・Shippori Mincho、OFL）を、使う文字だけに絞る。画面の文字を変えたら、もう一度実行する。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {"sled": ("src_sled.jpg", "RGB"), "strap": ("src_strap.jpg", "L"), "faces": ("src_faces.jpg", "L")})
