#!/usr/bin/env python3
"""pilot_024 の素材を data の JS にまとめる（土台 ext/kit/make_assets.py）。
- fall：燃える気球から落ちるブランシャールの版画（Harper's New Monthly Magazine 1869、パブリックドメイン）
- portrait：かごに立つブランシャール（Luigi Rados 1811、ミラノの夜の上昇、米国議会図書館、パブリックドメイン）。権利は scripts/pilot_024/assets.md
- 派手な文字のフォントと明朝体（OFL）を、使う文字だけに絞る。画面の文字を変えたら、もう一度実行する。
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "ext" / "kit"))
import make_assets as kit  # noqa: E402

if __name__ == "__main__":
    kit.episode(HERE, {"fall": ("src_fall.jpg", "L"), "portrait": ("src_portrait.jpg", "L")})
