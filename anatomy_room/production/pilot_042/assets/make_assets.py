#!/usr/bin/env python3
"""pilot_042 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。画像の権利は scripts/pilot_042/assets.md。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {'thumbbg': ('src_thumb.jpg', 'L'), 'kelsey': ('src_kelsey.jpg', 'L')}, fonts=False)
    kit.add_font(HERE, "syuku", "YujiSyuku-Regular.ttf", (HERE.parent / "renderer.html").read_text(encoding="utf-8"))   # 札の字体（2026-11-04）
