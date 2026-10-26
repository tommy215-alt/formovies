#!/usr/bin/env python3
"""pilot_005「マイナス×マイナスは、なぜプラスになる？」の制作スクリプト。

lines.json（セリフ・字幕・シーン）から、音声・BGM・効果音・映像・字幕を作り、MP4 に書き出す。

  python3 production_script.py voice    # VOICEVOX でセリフを合成 → work/voice/*.wav, timeline.json
  python3 production_script.py audio    # BGM・効果音を合成してミックス → work/mix.wav
  python3 production_script.py render   # 映像（renderer.html を Playwright でコマ撮り）→ work/video.mp4
  python3 production_script.py mux      # 映像と音声を合成 → world_anatomy_pilot_005.mp4
  python3 production_script.py docs     # final_script.md と subtitles.srt を書き出す
  python3 production_script.py qc       # 書き出した MP4 の検証（尺・解像度・デコード・音量・フレーム抽出）
  python3 production_script.py all      # 上をすべて順に実行（docs・qc も含む）
  python3 production_script.py update   # 修正後の作り直し（変えた行の音声と、変わった場面の映像だけ作り直す）

前提：VOICEVOX ENGINE 0.24.1 を 127.0.0.1:50021 で起動（production_notes.md）。ffmpeg、Node.js + Playwright、Noto Sans CJK JP。
"""
import hashlib
import json
import math
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
SR = 48000
FPS = 30
OUT = HERE / "world_anatomy_pilot_005.mp4"
ENGINE = "http://127.0.0.1:50021"
# tools/measure_tts.py と同じ話者・話速
VOICES = {
    "M": {"speaker": 12, "credit": "VOICEVOX:白上虎太郎", "speed": 1.18, "pitch": 0.0},
    "W": {"speaker": 14, "credit": "VOICEVOX:冥鳴ひまり", "speed": 1.13, "pitch": 0.0},
}
LEAD_IN = 0.4  # 最初のセリフまでの間


def load_lines():
    return json.loads((HERE / "lines.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- voice
def vv_query(text, who):
    v = VOICES[who]
    req = urllib.request.Request(
        f"{ENGINE}/audio_query?text={urllib.parse.quote(text)}&speaker={v['speaker']}", method="POST")
    q = json.loads(urllib.request.urlopen(req, timeout=60).read())
    q.update(speedScale=v["speed"], pitchScale=v["pitch"], prePhonemeLength=0.05,
             postPhonemeLength=0.08, outputSamplingRate=SR, outputStereo=False)
    return q


def vv_synth(q, who):
    req = urllib.request.Request(f"{ENGINE}/synthesis?speaker={VOICES[who]['speaker']}",
                                 data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=120).read()


def step_voice():
    data = load_lines()
    vdir = WORK / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    t = LEAD_IN
    timeline = []
    cache = WORK / "voice_cache"
    cache.mkdir(exist_ok=True)
    fresh = 0
    for ln in data["lines"]:
        # 読み上げ文と声の設定が同じなら、前回の合成結果を使う（変えた行だけ合成し直す）
        key = hashlib.sha256(json.dumps([ln["speech"], VOICES[ln["who"]], SR], ensure_ascii=False).encode()).hexdigest()[:16]
        cw, cq = cache / f"{key}.wav", cache / f"{key}.json"
        if cw.exists() and cq.exists():
            wav, q = cw.read_bytes(), json.loads(cq.read_text(encoding="utf-8"))
        else:
            q = vv_query(ln["speech"], ln["who"])
            wav = vv_synth(q, ln["who"])
            cw.write_bytes(wav); cq.write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")
            fresh += 1
        path = vdir / f"{ln['id']}.wav"
        path.write_bytes(wav)
        # 開始時刻をコマの区切りにそろえる。前の行の長さが変わっても後ろはコマ単位でずれるだけなので、
        # 場面ごとに書き出した映像を使い回せる（step_render の segment_key）
        t = math.ceil(t * FPS - 1e-6) / FPS
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
        timeline.append({**ln, "start": round(t, 5), "end": round(t + dur, 5), "dur": round(dur, 5), "kana": q["kana"]})
        t += dur + data["gap"] + ln.get("pause", 0.0)
    end_speech = timeline[-1]["end"]
    total = end_speech + data.get("endcard", 3.0)
    for x in timeline:
        x["env"] = envelope(vdir / f"{x['id']}.wav")
    tl = {"fps": FPS, "duration": round(total, 5), "endcard_start": round(end_speech + 0.3, 5),
          "credits": [v["credit"] for v in VOICES.values()], "cues": build_cues(timeline), "lines": timeline}
    (WORK / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    speech = sum(x["end"] - x["start"] for x in timeline)
    print(f"voice: {len(timeline)} 行（新しく合成 {fresh} 行）, セリフ合計 {speech:.1f}s, 全体 {total:.1f}s")
    for x in timeline:
        print(f"  {x['start']:6.2f}-{x['end']:6.2f} {x['who']} {x['kana']}", flush=True)


# ---------------------------------------------------------------- cues
# 映像と効果音のきっかけ。(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前を使う
CUE_DEFS = {
    "bills_in": ("L01", 0.0), "collide": ("L01", 0.30), "giant": ("L01", 0.52), "deflate": ("L02", 0.0),
    "title": ("L03", 0.0),
    "pattern": ("L05", 0.0), "row0": ("L05", 0.52), "row1": ("L06", 0.0), "row2": ("L07", 0.0),
    "row3": ("L08", 0.0), "plus2": ("L09", 0.0), "rowq": ("L10", 0.2), "ghost": ("L11", 0.0),
    "freeze": ("L12", 0.0), "badge1": ("L13", 0.15), "badge2": ("L13", 0.62),
    "dist": ("L14", 0.0), "formula": ("L14", 0.55), "area": ("L15", 0.0), "split": ("L15", 0.55),
    "bridge": ("L17", 0.0), "eq1": ("L18", 0.0), "zero": ("L18", 0.48), "eq1done": ("L18", 0.78),
    "eq2": ("L19", 0.0), "eq3": ("L19", 0.42), "solve": ("L20", 0.52), "final": ("L21", 0.0),
    "general": ("L22", 0.0), "general2": ("L22", 0.62),
    "numline": ("L23", 0.0), "flip1": ("L23", 0.50), "uturn": ("L24", 0.0), "flip2": ("L24", 0.55),
    "restore": ("L26", 0.0), "outro": ("L27", 0.0), "fold": ("L28", 0.75),
}


def build_cues(timeline):
    by = {x["id"]: x for x in timeline}
    cues = {}
    for name, (lid, frac) in CUE_DEFS.items():
        x = by[lid]
        cues[name] = round(x["start"] + frac * (x["end"] - x["start"]), 5)
    return cues


def envelope(path, fps=FPS):
    """セリフの音量の包絡（話者アイコンの動きに使う）。1 フレームごとの 0〜1。"""
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        sr = w.getframerate()
    hop = sr // fps
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    peak = max(float(rms.max()), 1e-6)
    return [round(float(v) / peak, 3) for v in rms]


# ---------------------------------------------------------------- audio
def read_wav(path):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        assert w.getframerate() == SR, path
    return a


def write_wav(path, a):
    a = np.clip(a, -1, 1)
    if a.ndim == 1:
        a = np.stack([a, a], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def tone(freq, dur, amp=1.0, attack=0.005, decay=None):
    t = np.arange(int(dur * SR)) / SR
    env = np.minimum(1, t / attack)
    env *= np.exp(-t / decay) if decay else np.ones_like(t)
    return amp * env * np.sin(2 * np.pi * freq * t)


def noise_sweep(dur, f0, f1, amp):
    """フィルタした雑音を f0→f1 に掃引した風切り音（ワイプ・反転の効果音）。"""
    n = int(dur * SR)
    rng = np.random.default_rng(7)
    x = rng.standard_normal(n)
    out = np.zeros(n)
    y = 0.0
    for i in range(n):  # 1 次ローパスの係数を時間で変える
        f = f0 + (f1 - f0) * i / n
        k = 1 - math.exp(-2 * math.pi * f / SR)
        y += k * (x[i] - y)
        out[i] = y
    env = np.sin(np.pi * np.arange(n) / n) ** 2
    return amp * out * env / (np.abs(out).max() + 1e-9)


def add(*xs):
    """長さの違う波形を、短いほうを 0 で埋めて足す。"""
    out = np.zeros(max(len(x) for x in xs))
    for x in xs:
        out[: len(x)] += x
    return out


def sfx_bank():
    return {
        "whoosh": noise_sweep(0.45, 300, 3000, 0.35),
        "thud": add(tone(70, 0.35, 0.6, 0.002, 0.08), tone(140, 0.2, 0.25, 0.002, 0.05)),
        "tick": add(tone(1320, 0.12, 0.22, 0.002, 0.03), tone(2640, 0.08, 0.06, 0.002, 0.02)),
        "pop": add(tone(520, 0.18, 0.25, 0.003, 0.05), tone(780, 0.18, 0.12, 0.003, 0.05)),
        "doubt": add(tone(220, 0.4, 0.25, 0.01, 0.15), tone(207.65, 0.4, 0.2, 0.01, 0.15)),
        "chime": add(tone(880, 1.4, 0.22, 0.004, 0.45), tone(1318.5, 1.4, 0.16, 0.004, 0.4), tone(1760, 1.0, 0.08, 0.004, 0.3)),
        "flip": noise_sweep(0.6, 400, 2200, 0.25),
        "end": add(tone(659.25, 1.8, 0.16, 0.01, 0.6), tone(987.77, 1.8, 0.12, 0.01, 0.6)),
    }


SFX_AT = [("whoosh", "bills_in"), ("thud", "collide"), ("pop", "deflate"), ("whoosh", "title"),
          ("tick", "row0"), ("tick", "row1"), ("tick", "row2"), ("tick", "row3"), ("pop", "rowq"),
          ("doubt", "freeze"), ("pop", "formula"), ("whoosh", "split"), ("tick", "eq1"), ("pop", "zero"),
          ("tick", "eq2"), ("pop", "eq3"), ("chime", "solve"), ("flip", "flip1"), ("flip", "flip2"),
          ("pop", "restore"), ("whoosh", "fold")]


def bgm(total, cues):
    """控えめなパッド（Am - F - C - G）。解き明かす場面（solve 以降）で少し明るく厚くする。"""
    n = int(total * SR)
    t = np.arange(n) / SR
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [130.81, 196.0, 261.63], [196.0, 246.94, 293.66]]
    bar = 60 / 76 * 4  # 76 BPM、4 拍で 1 コード
    out = np.zeros(n)
    for i in range(int(total / bar) + 1):
        a, b = int(i * bar * SR), min(n, int((i + 1) * bar * SR + 0.6 * SR))
        if a >= n:
            break
        seg = t[: b - a]
        env = np.minimum(1, seg / 0.8) * np.minimum(1, (seg[::-1]) / 0.8)
        for f in chords[i % 4]:
            for det in (-0.6, 0.6):  # わずかにずらして厚みを出す
                out[a:b] += env * 0.05 * np.sin(2 * np.pi * (f + det) * seg)
            out[a:b] += env * 0.012 * np.sin(2 * np.pi * f * 2 * seg)
        out[a:b] += env * 0.04 * np.sin(2 * np.pi * chords[i % 4][0] / 2 * seg)
    pulse = 0.5 + 0.5 * np.cos(2 * np.pi * t / (60 / 76))  # 拍に合わせたゆるい揺れ
    out *= 0.85 + 0.15 * pulse
    bright = np.clip((t - cues["solve"]) / 1.5, 0, 1) * (t < cues["endcard"])
    out *= 1 + 0.35 * bright
    fade = np.clip((total - t) / 2.0, 0, 1) * np.clip(t / 0.6, 0, 1)
    return out * fade


def step_audio():
    tl = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    total = tl["duration"]
    n = int(total * SR) + SR
    voice = np.zeros(n)
    for x in tl["lines"]:
        a = read_wav(WORK / "voice" / f"{x['id']}.wav")
        i = int(x["start"] * SR)
        voice[i:i + len(a)] += a
    # 話者ごとに音量をそろえる（RMS を -20 dBFS 付近へ）
    for x in tl["lines"]:
        i, j = int(x["start"] * SR), int(x["end"] * SR)
        r = np.sqrt(np.mean(voice[i:j] ** 2)) + 1e-9
        voice[i:j] *= min(4.0, 0.1 / r)
    cues = {**tl["cues"], "endcard": tl["endcard_start"]}
    music = np.zeros(n)
    music[: int(total * SR)] = bgm(total, cues)
    # セリフ中は BGM を下げる（ダッキング）
    talk = np.zeros(n)
    for x in tl["lines"]:
        talk[int(x["start"] * SR):int(x["end"] * SR)] = 1
    k = int(0.25 * SR)
    talk = np.convolve(talk, np.ones(k) / k, mode="same")
    music *= 1 - 0.55 * talk
    sfx = np.zeros(n)
    bank = sfx_bank()
    for name, cue in SFX_AT + [("end", "endcard")]:
        s = bank[name]
        i = int(cues[cue] * SR)
        sfx[i:i + len(s)] += s[: max(0, n - i)]
    mix = voice + 0.9 * music + 0.55 * sfx
    write_wav(WORK / "mix_raw.wav", mix[: int(total * SR)])
    # ラウドネスを -14 LUFS（YouTube の基準付近）、ピーク -2.0 dBTP に（AAC 変換での上振れを見込む）
    m = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(WORK / "mix_raw.wav"), "-af",
                        "loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-2.0:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
          f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(WORK / "mix_raw.wav"),
                    "-af", af, "-ar", str(SR), str(WORK / "mix.wav")], check=True)
    print(f"audio: {total:.1f}s, 元の積分ラウドネス {st['input_i']} LUFS → -14 LUFS")


# ---------------------------------------------------------------- render / mux
# 場面の切れ目（ここで映像を区切って、場面ごとに書き出して保存する）
SEG_CUES = ["title", "pattern", "freeze", "dist", "bridge", "eq1", "general", "numline", "outro", "endcard"]
WORKERS = 3  # 同時に書き出すブラウザの数（CPU 4 コアで 3 が目安）


def segment_key(tl, a, b, code):
    """場面の内容を表すハッシュ。場面の中身（前後の余白を含む）とレンダラーのコードが同じなら、
    場面の開始時刻がずれても前回の映像をそのまま使える。"""
    fps = tl["fps"]
    t0, t1 = a / fps, b / fps
    lo, hi = t0 - 1.5, t1 + 1.5  # 場面の切り替え（フェード）と字幕の持ち越しを含む余白
    # 場面の先頭からのコマ数。丸め誤差で判定が揺れないよう 0.1 コマ単位にし、-0.0 は 0.0 にそろえる
    rel = lambda v: round((v - t0) * fps, 1) + 0.0
    lines = [{"who": x["who"], "sub": x["sub"], "env": x["env"], "s": round((x["start"] - t0) * fps), "d": x["dur"]}
             for x in tl["lines"] if x["end"] > lo and x["start"] < hi]
    cues = sorted((k, rel(v)) for k, v in tl["cues"].items() if lo <= v <= hi)
    extra = [rel(tl["endcard_start"])] if lo <= tl["endcard_start"] <= hi else []
    blob = json.dumps([code, fps, b - a, lines, cues, extra, tl["credits"]], ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def step_render():
    tl = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    fps, n = tl["fps"], math.ceil(tl["duration"] * tl["fps"])
    cues = {**tl["cues"], "endcard": tl["endcard_start"]}
    bounds = [0] + [round(cues[c] * fps) for c in SEG_CUES] + [n]
    code = hashlib.sha256((HERE / "renderer.html").read_bytes() + (HERE / "render_frames.js").read_bytes()).hexdigest()
    sdir = WORK / "segments"
    sdir.mkdir(parents=True, exist_ok=True)
    segs = []
    for a, b in zip(bounds, bounds[1:]):
        if b > a:
            segs.append({"a": a, "b": b, "out": str(sdir / f"{segment_key(tl, a, b, code)}.mp4")})
    todo = [s for s in segs if not Path(s["out"]).exists()]
    print(f"render: 場面 {len(segs)} 個のうち、書き出しが必要なのは {len(todo)} 個"
          f"（{sum(s['b'] - s['a'] for s in todo)} / {n} コマ）", flush=True)
    if todo:
        # 書き出すコマ数がなるべく均等になるように、ブラウザごとに振り分ける
        jobs = [[] for _ in range(min(WORKERS, len(todo)))]
        for s in sorted(todo, key=lambda s: s["a"] - s["b"]):
            min(jobs, key=lambda j: sum(x["b"] - x["a"] for x in j)).append(s)
        procs = []
        for i, j in enumerate(jobs):
            jf = WORK / f"job{i}.json"
            jf.write_text(json.dumps(j), encoding="utf-8")
            procs.append(subprocess.Popen(["node", str(HERE / "render_frames.js"), "--segments", str(jf)]))
        if any(p.wait() for p in procs):
            sys.exit("render: 書き出しに失敗した場面がある")
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{s['out']}'\n" for s in segs), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c", "copy", "-movflags", "+faststart", str(WORK / "video.mp4")], check=True)
    print(f"render: {len(segs)} 場面をつないで work/video.mp4（{n} コマ）")


def step_update():
    """修正後の作り直し：変えた行の音声だけ合成し、変わった場面だけ映像を書き出して、つなぎ直す。"""
    for s in (step_voice, step_audio, step_render, step_mux, step_docs, step_qc):
        s()


def step_mux():
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(WORK / "video.mp4"),
                    "-i", str(WORK / "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT)], check=True)
    print("mux:", OUT.name, f"{OUT.stat().st_size / 1e6:.1f} MB")


# ---------------------------------------------------------------- docs
SCENES = [  # (名前, 開始 cue, 終了 cue, 映像, 音)
    ("1 冒頭の疑問", None, "title", "借用書 2 枚が左右から飛んできて「×」でぶつかり、巨大な「大借金！？」に。W のツッコミでしぼんで「？」になる", "風切り音→衝突音→ポップ"),
    ("1b タイトル", "title", "pattern", "走査線で「マイナス × マイナス は / なぜプラス？」「(−)×(−)=(+)」が現れる", "風切り音"),
    ("2 計算パターン", "pattern", "freeze", "左に 3×(−2)=−6 … 0×(−2)=0 を 1 行ずつ。右の縦の数直線で点が −6→−4→−2→0 と上がり、＋2 の弧が残る。最後に (−1)×(−2)=？ と、予想の点線（+2？）", "行ごとにチック音"),
    ("3 反論", "freeze", "dist", "表が暗くなり、M の大きな「？」。バッジ「パターン＝予想のヒント ✓」「それだけでは証明にならない ✕」", "低い不協和の 2 音"),
    ("4 分配法則（正の数の例）", "dist", "bridge", "公式 a×(b+c)=a×b+a×c。縦 2・横 3+4 の面積図を 2×3 と 2×4 に分ける。「※正の数での例」と明示", "ポップ、風切り音"),
    ("4b 負の数への橋渡し", "bridge", "eq1", "面積図を完全に消し、a=−2, b=3, c=−3 を示す。「負の数でも同じルールが成り立つなら？」", "—"),
    ("5 核心の導出", "eq1", "general", "(−2)×(3+(−3)) → かっこの中＝0 → ＝0。分配法則で (−2)×3+(−2)×(−3)=0。大きく −6＋？＝0。M の「プラス 6 なら」で ？ が反転して +6、光。最後に (−2)×(−3)=+6", "チック、ポップ、ひらめきのチャイム"),
    ("5b 一般化", "general", "numline", "「負の数でも同じ計算ルールを保つなら ↓ (−)×(−)=(+)」「ルールを決めたら、答えは論理で決まる」", "BGM が少し明るくなる"),
    ("6 数直線", "numline", "outro", "奥行きのある数直線。0→+2 の矢印が ×(−1) で縦軸のまわりに半回転して −2 へ（奥を通る）。2 回目は手前を通って +2 に戻る。軌跡を点線で残し、(−1)×(−1)=+1", "反転の風切り音 ×2"),
    ("7 締め", "outro", "endcard", "冒頭の「大借金！？」の借用書が戻り、M の一言で折りたたまれて消える", "風切り音"),
    ("7b エンドカード", "endcard", None, "解剖された立方体のマーク、「世界の解剖室」、キャッチコピー、音声クレジット", "終わりのチャイム、BGM フェードアウト"),
]


def fmt(t, ms=True):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}" if ms else f"{int(m)}:{int(s):02d}"


def sub_chunks(x):
    """字幕のかたまりと、その表示時間（文字数の比で配分）。renderer.html の subChunk と同じ規則。"""
    subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
    lens = [len(s.replace("**", "").replace(" / ", "")) for s in subs]
    tot, acc, out = sum(lens), 0, []
    for s, n in zip(subs, lens):
        a = x["start"] + (x["end"] - x["start"]) * acc / tot
        acc += n
        out.append((a, x["start"] + (x["end"] - x["start"]) * acc / tot, s))
    return out


def step_docs():
    tl = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    cues = {**tl["cues"], "endcard": tl["endcard_start"]}
    lines = tl["lines"]
    # 字幕ファイル（SRT）
    srt, k = [], 1
    for x in lines:
        for a, b, s in sub_chunks(x):
            ts = lambda v: f"{int(v // 3600):02d}:{int(v % 3600 // 60):02d}:{int(v % 60):02d},{int(v * 1000 % 1000):03d}"
            srt.append(f"{k}\n{ts(a)} --> {ts(b)}\n{x['who']}：{s.replace('**', '').replace(' / ', chr(10))}\n")
            k += 1
    (HERE / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
    # 完成台本
    rows = ["| ID | 時間 | 話者 | セリフ（読み上げ文） | 画面字幕 | 事実確認ID |", "|----|------|------|------------------|----------|-----------|"]
    for x in lines:
        subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
        rows.append(f"| {x['id']} | {fmt(x['start'])}–{fmt(x['end'])} | {x['who']} | {x['speech']} | {' ／ '.join(subs)} | {x['fact']} |")
    data = load_lines()
    md = [f"# pilot_005 完成台本：{data['title']}", "",
          "`production_script.py docs` が `lines.json` と実際の音声の長さ（`work/timeline.json`）から生成。手で編集しない。", "",
          f"- 尺：**{tl['duration']:.1f} 秒**（セリフ {sum(x['end'] - x['start'] for x in lines):.1f} 秒、エンドカード {tl['duration'] - tl['endcard_start']:.1f} 秒）",
          f"- 音声：M＝{VOICES['M']['credit']}（話速 {VOICES['M']['speed']}）、W＝{VOICES['W']['credit']}（話速 {VOICES['W']['speed']}）",
          "- 読み上げ文の数字やかな書きは、音声合成の読み間違いを防ぐため。字幕は記号（−、×、＝）で表示する。",
          "- 事実確認 ID は `anatomy_room/scripts/pilot_005/fact_check.md` に対応。", "", *rows, "",
          "## エンドカード", "", f"{fmt(tl['endcard_start'])}– 「世界の解剖室」／見えない仕組みを、CGで解き明かす。／音声：{'／'.join(tl['credits'])}", ""]
    (HERE / "final_script.md").write_text("\n".join(md), encoding="utf-8")
    # シーン設計
    rows = ["| シーン | 時間 | 映像・CG | 音（BGM 以外） | セリフ |", "|-------|------|---------|---------------|-------|"]
    for name, a, b, video, sound in SCENES:
        ta = 0.0 if a is None else cues[a]
        tb = tl["duration"] if b is None else cues[b]
        ids = [x["id"] for x in lines if ta - .01 <= x["start"] < tb - .01]
        rows.append(f"| {name} | {fmt(ta)}–{fmt(tb)} | {video} | {sound} | {', '.join(ids) or '—'} |")
    plan = [f"# pilot_005 シーン設計：{data['title']}", "",
            "`production_script.py docs` が生成（時間は実際の音声にもとづく）。各シーンの描画は `renderer.html` の `scene*` 関数。", "",
            "## 画面のレイアウト（1080×1920）", "",
            "- 上部 y≈120：小さなチャンネル名（ロゴ）。",
            "- 数式・図解：y≈380〜1160、x≈80〜1000（Shorts の右側ボタン列と下部の説明欄を避ける）。",
            "- 字幕：中心 y≈1350、幅 900 以内、x の中心 500（右のボタン列を避けて少し左寄せ）。話者タグ（M＝橙の丸、W＝水色の六角形）と声に合わせて動くバー。",
            "- 色の約束：負の数＝赤系、正の数＝緑系、強調＝黄。数式と字幕は重ならない位置に固定。", "",
            "## シーン一覧", "", *rows, "",
            "## 演出上の注意（監査で決めたこと）", "",
            "- 面積図は正の数の例としてだけ使い、「※正の数での例」と表示。負の数の導出に入る前に図を完全に消し、式で示す。",
            "- 式は一度に全部出さない：①かっこの中が 0 → ②分配法則で分ける → ③「−6＋？＝0」を大きく → ④M が気づく → ⑤一般化 → ⑥数直線。",
            "- 「−6＋？＝0」の後に約 1.1 秒の間を置き、視聴者が式を読む時間を取る。",
            "- 数直線の反転は「見方」の一つとして、導出の後に置く（導出の代わりにしない）。", ""]
    (HERE / "scene_plan.md").write_text("\n".join(plan), encoding="utf-8")
    print("docs: final_script.md, scene_plan.md, subtitles.srt")


# ---------------------------------------------------------------- qc
def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def step_qc():
    qdir = HERE / "qc"
    qdir.mkdir(exist_ok=True)
    for old in qdir.glob("*.jpg"):  # 前回の抽出フレームを消す
        old.unlink()
    tl = json.loads((WORK / "timeline.json").read_text(encoding="utf-8"))
    rep = ["# pilot_005 品質検証の記録", "", f"対象：`{OUT.name}`（{OUT.stat().st_size / 1e6:.1f} MB）", ""]
    pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(OUT)]).stdout)
    v = next(s for s in pr["streams"] if s["codec_type"] == "video")
    a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
    dur = float(pr["format"]["duration"])
    nfr = int(v.get("nb_frames", 0))
    rep += ["## ストリーム", "",
            f"- 映像：{v['codec_name']} {v['width']}×{v['height']}、{v['r_frame_rate']} fps、{v['pix_fmt']}、{nfr} フレーム、{float(v['duration']):.2f} 秒",
            f"- 音声：{a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch、{float(a['duration']):.2f} 秒",
            f"- 全体の尺：{dur:.2f} 秒（タイムライン上の設計値 {tl['duration']:.2f} 秒）", ""]
    dec = run(["ffmpeg", "-v", "error", "-i", str(OUT), "-f", "null", "-"])
    rep += ["## 全編デコード", "", f"- `ffmpeg -v error -f null` のエラー出力：{'なし' if not dec.stderr.strip() else dec.stderr.strip()[:500]}", ""]
    lo = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    summ = lo[lo.rindex("Summary:"):]
    pick = lambda key: summ.split(key)[1].split("\n")[0].strip()
    rep += ["## 音量", "", f"- 積分ラウドネス：{pick('I:')}（目標 −14 LUFS）", f"- ラウドネスレンジ：{pick('LRA:')}",
            f"- トゥルーピーク：{pick('Peak:')}（目標 −1.0 dBTP 以下。ミックスは −2.0 で余裕を取る）", ""]
    si = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(OUT), "-af", "silencedetect=n=-45dB:d=0.8", "-f", "null", "-"]).stderr
    sil = [ln.split("]")[1].strip() for ln in si.splitlines() if "silence_end" in ln]
    rep += ["## 無音区間（−45 dB 未満が 0.8 秒以上）", "", *(f"- {s}" for s in sil), "- なし" if not sil else "", ""]
    # セリフ区間ごとの音声レベル（途切れ・音割れの確認）
    rows = []
    for x in tl["lines"]:
        r = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(x["start"]), "-t", str(x["end"] - x["start"]), "-i", str(OUT),
                 "-af", "volumedetect", "-f", "null", "-"]).stderr
        mean = r.split("mean_volume:")[1].split("dB")[0].strip()
        peak = r.split("max_volume:")[1].split("dB")[0].strip()
        rows.append(f"| {x['id']} | {x['who']} | {fmt(x['start'])} | {mean} | {peak} |")
    rep += ["## セリフごとの音量（dB）", "", "| ID | 話者 | 開始 | 平均 | 最大 |", "|----|------|------|------|------|", *rows, ""]
    # 字幕 1 枚あたりの表示時間（短すぎると読めない）
    short = [(x["id"], s, b - a) for x in tl["lines"] for a, b, s in sub_chunks(x) if b - a < 0.8]
    rep += ["## 字幕の表示時間", "", f"- 字幕 {sum(len(sub_chunks(x)) for x in tl['lines'])} 枚。0.8 秒未満の字幕："
            + ("なし" if not short else "、".join(f"{i}「{s.replace('**', '')}」{d:.2f}s" for i, s, d in short)), ""]
    # 読み（音声合成が実際に使ったカナ）と字幕の照合用
    rep += ["## 読み上げの照合（VOICEVOX が使った読み）", "", "| ID | 字幕 | 読み（カナ） |", "|----|------|------------|",
            *[f"| {x['id']} | {' ／ '.join(x['sub'] if isinstance(x['sub'], list) else [x['sub']]).replace('**', '')} | {x['kana']} |" for x in tl["lines"]], ""]
    # 確認用フレーム
    times = [0.5, *[tl["cues"][k] + .6 for k in ("collide", "giant", "title", "row3", "ghost", "badge2", "split", "bridge",
                                                   "zero", "eq3", "solve", "final", "general2", "flip1", "restore", "fold")],
             tl["endcard_start"] + 1.2]
    for i, t in enumerate(times):
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(OUT), "-frames:v", "1", "-q:v", "3", str(qdir / f"f{i:02d}_{t:05.1f}.jpg")])
    run(["montage", *sorted(str(p) for p in qdir.glob("f*.jpg")), "-tile", "6x3", "-geometry", "300x533+4+4",
         "-background", "#222", str(qdir / "contact_sheet.jpg")])
    rep += ["## 抽出フレーム", "", f"`qc/` に {len(times)} 枚、一覧は `qc/contact_sheet.jpg`。", ""]
    (HERE / "qc_report.md").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep[:22]))


# ---------------------------------------------------------------- main
STEPS = {"voice": step_voice, "audio": step_audio, "render": step_render, "mux": step_mux, "docs": step_docs, "qc": step_qc,
         "update": step_update}

if __name__ == "__main__":
    names = sys.argv[1:] or ["all"]
    if names == ["all"]:
        names = ["voice", "audio", "render", "mux", "docs", "qc"]
    for n in names:
        STEPS[n]()
