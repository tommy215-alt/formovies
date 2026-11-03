#!/usr/bin/env python3
"""pilot_040 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。画像の権利は scripts/pilot_040/assets.md。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {'thumbbg': ('src_thumb.jpg', 'L')}, fonts=False)
