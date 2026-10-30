#!/usr/bin/env python3
"""曲の調（長調か短調か）を推定する（悲劇の BGM 選び、2026-10-30）。クロマ（12 音の強さ）と Krumhansl の調のプロファイルの相関。
  python keycheck.py 曲1.mp3 曲2.mp3 …  → 上位 3 つの調と、長調・短調の最高相関
"""
import subprocess
import sys

import numpy as np

SR = 22050
MAJ = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MIN = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def chroma(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], check=True, capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n, hop, c = 8192, 4096, np.zeros(12)
    f = np.fft.rfftfreq(n, 1 / SR)
    ok = (f > 60) & (f < 2000)
    pc = (np.round(12 * np.log2(f[ok] / 440.0)) + 9) % 12
    w = np.hanning(n)
    for i in range(0, len(x) - n, hop):
        m = np.abs(np.fft.rfft(x[i:i + n] * w))[ok]
        np.add.at(c, pc.astype(int), m)
    return c / c.sum()


for p in sys.argv[1:]:
    c = chroma(p)
    sc = [(np.corrcoef(np.roll(prof, k), c)[0, 1], NAMES[k] + (" major" if mode else " minor")) for k in range(12) for mode, prof in ((1, MAJ), (0, MIN))]
    sc.sort(reverse=True)
    bmaj = max(s for s, n in sc if "major" in n); bmin = max(s for s, n in sc if "minor" in n)
    print(p.split("\\")[-1].split("/")[-1], "|", ", ".join(f"{n} {s:.2f}" for s, n in sc[:3]), f"| major {bmaj:.2f} / minor {bmin:.2f}")
