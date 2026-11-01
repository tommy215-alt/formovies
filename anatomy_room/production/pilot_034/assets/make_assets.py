#!/usr/bin/env python3
"""pilot_034 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。画像の権利は scripts/pilot_034/assets.md。画面の文字を変えたら、もう一度実行する。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {'flakes': ('src_flakes.jpg', 'L'), 'bentley': ('src_bentley.jpg', 'L')}, fonts=False)
