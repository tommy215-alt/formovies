#!/usr/bin/env python3
"""悲劇用のハイテンションなナレーションの聞き比べ（2026-10-30）。台本 pilot_020 の L02 を 6 通りで読む。

話者は templates/REVERSE_GUIDELINE_v2.1.md で規約を確かめた VOICEVOX の話者だけ（そのスタイル違いを含む）。
  python make_hype.py   → 0〜5 の mp3（VOICEVOX ENGINE 127.0.0.1:50021、ffmpeg）
"""
import json
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
E = "http://127.0.0.1:50021"
TEXT = "1910年、イギリスのスコット隊が南極へ。狙うは、人類初の南極点！"
CASES = [  # (ファイル名, 話者 ID, 話速, 抑揚, 音高)
    ("0_kurono_yorokobi", 39, 1.25, 1.5, 0.0),     # 玄野武宏 喜び
    ("1_kurono_normal_hype", 11, 1.25, 1.7, 0.03),  # 玄野武宏 ノーマル（抑揚と音高を上げる）
    ("2_aoyama_nekketsu", 81, 1.2, 1.3, 0.0),      # 青山龍星 熱血（ドパ設計の叫ぶ声と同じ話者）
    ("3_aoyama_yorokobi", 83, 1.25, 1.4, 0.0),     # 青山龍星 喜び
    ("4_kenzaki_hype", 21, 1.25, 1.6, 0.02),       # 剣崎雌雄 ノーマル（抑揚を上げる）
    ("5_tobari_akarui", 119, 1.25, 1.5, 0.0),      # 夜語トバリ 明るい（女性）
]
for name, sid, sp, it, pt in CASES:
    q = json.load(urllib.request.urlopen(urllib.request.Request(f"{E}/audio_query?" + urllib.parse.urlencode({"text": TEXT, "speaker": sid}), method="POST")))
    q.update(speedScale=sp, intonationScale=it, pitchScale=pt, volumeScale=1.15, prePhonemeLength=.05, postPhonemeLength=.1, outputSamplingRate=48000)
    wav = urllib.request.urlopen(urllib.request.Request(f"{E}/synthesis?speaker={sid}", data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})).read()
    w = HERE / f"{name}.wav"; w.write_bytes(wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(w), "-af", "loudnorm=I=-16", "-b:a", "160k", str(w.with_suffix(".mp3"))], check=True); w.unlink()
    print(name)
