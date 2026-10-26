#!/usr/bin/env python3
"""台本のセリフを VOICEVOX で実際に合成し、読み上げ時間を実測する。

- 各行のセリフ所要時間（秒）と、台本表で割り当てた秒数を比べる
- --retime を付けると、実測値＋間（--gap 秒）で台本表の時間列を書き換える
- VOICEVOX ENGINE を 127.0.0.1:50021 で起動しておくこと（docs/PRODUCTION_WORKFLOW.md）

使い方:
  python3 anatomy_room/tools/measure_tts.py              # 全パイロットを実測
  python3 anatomy_room/tools/measure_tts.py pilot_001 --retime
"""
import argparse
import io
import json
import math
import re
import urllib.parse
import urllib.request
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = "http://127.0.0.1:50021"
# キャラクターと VOICEVOX の話者（style id）・話速。production でも同じ値を使う
VOICES = {
    "M": {"speaker": 12, "name": "白上虎太郎（ふつう）", "speed": 1.15},
    "W": {"speaker": 14, "name": "冥鳴ひまり（ノーマル）", "speed": 1.10},
}
ROW = re.compile(r"^\| (\d+):(\d\d)-(\d+):(\d\d) \| ([^|]+) \| ([^|]*) \|")


def to_speech(text):
    """セリフを読み上げ用に整える（記号を読み方に）。"""
    t = text.replace("…", "、").replace("!?", "！？")
    return t


def synth(text, who, query_only=False):
    v = VOICES[who]
    q = urllib.request.urlopen(urllib.request.Request(
        f"{ENGINE}/audio_query?text={urllib.parse.quote(to_speech(text))}&speaker={v['speaker']}",
        method="POST"), timeout=60)
    query = json.loads(q.read())
    query["speedScale"] = v["speed"]
    query["prePhonemeLength"] = 0.05
    query["postPhonemeLength"] = 0.05
    if query_only:
        return query
    r = urllib.request.urlopen(urllib.request.Request(
        f"{ENGINE}/synthesis?speaker={v['speaker']}", data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json"}), timeout=120)
    return r.read(), query


def wav_seconds(data):
    with wave.open(io.BytesIO(data)) as w:
        return w.getnframes() / w.getframerate()


def measure(pid, retime=False, gap=0.35):
    path = ROOT / "scripts" / pid / "script.md"
    text = path.read_text(encoding="utf-8")
    head, body = text.split("## 3. 完全な台本", 1)
    lines, total_speech, exact, t = [], 0.0, 0.0, 0
    report = []
    for ln in body.split("\n"):
        m = ROW.match(ln)
        if m:
            a = int(m[1]) * 60 + int(m[2]); b = int(m[3]) * 60 + int(m[4])
            who, line = m[5].strip(), m[6].strip()
            if who in VOICES:
                sec = wav_seconds(synth(line, who)[0])
                total_speech += sec
                flag = "  ←不足" if sec + 0.2 > (b - a) else ""
                report.append(f"  {m[1]}:{m[2]} {who} {sec:4.1f}s / 枠 {b - a}s{flag}  {line[:28]}")
                exact += sec + gap
            else:
                exact += b - a
            # 境界は累積の実測時間を四捨五入（丸め誤差を積み上げない）
            end = max(t + 1, round(exact))
            if retime:
                ln = re.sub(r"^\| \d+:\d\d-\d+:\d\d \|", f"| {t // 60}:{t % 60:02d}-{end // 60}:{end % 60:02d} |", ln)
            t = end
        lines.append(ln)
    if retime:
        new = head + "## 3. 完全な台本" + "\n".join(lines)
        new = re.sub(r"\| 想定尺 \| 約 \d+ 秒 \|", f"| 想定尺 | 約 {t} 秒 |", new)
        path.write_text(new, encoding="utf-8")
    print(f"== {pid}: セリフ実測 {total_speech:.1f} 秒 / 間を含む尺 {t} 秒" + ("（台本の時間列を更新）" if retime else ""))
    print("\n".join(report))
    return total_speech, t


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pilots", nargs="*")
    ap.add_argument("--retime", action="store_true")
    ap.add_argument("--gap", type=float, default=0.35)
    a = ap.parse_args()
    pids = a.pilots or sorted(p.name for p in (ROOT / "scripts").glob("pilot_*"))
    for pid in pids:
        measure(pid, a.retime, a.gap)
