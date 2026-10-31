#!/usr/bin/env python3
"""オープニングの音「衝撃波（open_impact）」の試聴ファイルを作る（2026-10-31）。
python anatomy_room/production/voice_tests/opening/make_impact.py → 同じフォルダに open_impact.mp3（3 秒）"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "common"))
sys.path.insert(0, str(HERE.parents[1] / "ext"))
import opening_bgm  # noqa: E402
from music import SR  # noqa: E402

y = opening_bgm._impact(int(3.0 * SR))
pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16)
w = HERE / "open_impact.wav"
with wave.open(str(w), "wb") as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-b:a", "192k", str(HERE / "open_impact.mp3")], check=True)
w.unlink()
print(HERE / "open_impact.mp3", "peak", float(np.abs(y).max()))
