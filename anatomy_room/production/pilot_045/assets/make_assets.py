#!/usr/bin/env python3
"""pilot_045 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。本物の写真は使わない（もしも設計、CG と計算の地図だけ）。"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {}, fonts=False)
