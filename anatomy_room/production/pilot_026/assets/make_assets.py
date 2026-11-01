#!/usr/bin/env python3
"""pilot_026 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。
- crater：バリンジャー・クレーター（USGS／D. Roddy、パブリックドメイン）、pump：「ETHYL」の給油機（John Margolies 1982、米国議会図書館、パブリックドメイン）
  権利は scripts/pilot_026/assets.md。3D の共通素材は ext/kit/scene_assets.js。画面の文字を変えたら、もう一度実行する。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {"crater": ("src_crater.jpg", "RGB"), "pump": ("src_pump.jpg", "RGB")}, fonts=False)
