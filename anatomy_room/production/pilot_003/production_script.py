#!/usr/bin/env python3
"""pilot_003（第 2 話）「コンビニおにぎりの海苔は、なぜパリパリなのか？」の制作スクリプト。

第 1 話（pilot_005/production_script.py）をもとに、声のスタイル指定・共通エンディング・3D レンダラー・
明るさと動きの検証を加えた版。

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
OUT = HERE / "world_anatomy_pilot_003.mp4"
COMMON = HERE.parent / "common"
ENGINE = "http://127.0.0.1:50021"
# 声の設定は production/common/voices.json（lines.json の "voices" で版を選ぶ）
VOICE_CFG = json.loads((COMMON / "voices.json").read_text(encoding="utf-8"))
VOICES = VOICE_CFG[json.loads((HERE / "lines.json").read_text(encoding="utf-8"))["voices"]]
ENDING = VOICE_CFG["ending"]
LEAD_IN = 0.4  # 最初のセリフまでの間


def load_lines():
    return json.loads((HERE / "lines.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------- voice
def voice_params(ln):
    """セリフ 1 行の声の設定（話者の既定値を、行ごとの style / speed / inton で上書き）。"""
    v = VOICES[ln["who"]]
    style = ln.get("style", v["default_style"])
    return {"speaker": v["styles"][style], "style": style, "speed": ln.get("speed", v["speed"]),
            "pitch": ln.get("pitch", v["pitch"]), "inton": ln.get("inton", v["inton"])}


def vv_query(text, p):
    req = urllib.request.Request(
        f"{ENGINE}/audio_query?text={urllib.parse.quote(text)}&speaker={p['speaker']}", method="POST")
    q = json.loads(urllib.request.urlopen(req, timeout=60).read())
    q.update(speedScale=p["speed"], pitchScale=p["pitch"], intonationScale=p["inton"], prePhonemeLength=0.05,
             postPhonemeLength=0.08, outputSamplingRate=SR, outputStereo=False)
    return q


def vv_synth(q, p):
    req = urllib.request.Request(f"{ENGINE}/synthesis?speaker={p['speaker']}",
                                 data=json.dumps(q).encode(), headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=120).read()


def synth_cached(ln, cache):
    """読み上げ文と声の設定が同じなら、前回の合成結果を使う（変えた行だけ合成し直す）。"""
    p = voice_params(ln)
    key = hashlib.sha256(json.dumps([ln["speech"], p, SR], ensure_ascii=False).encode()).hexdigest()[:16]
    cw, cq = cache / f"{key}.wav", cache / f"{key}.json"
    if cw.exists() and cq.exists():
        return cw.read_bytes(), json.loads(cq.read_text(encoding="utf-8")), p, False
    q = vv_query(ln["speech"], p)
    wav = vv_synth(q, p)
    cw.write_bytes(wav); cq.write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")
    return wav, q, p, True


def place(ln, t, vdir, cache, timeline):
    wav, q, p, fresh = synth_cached(ln, cache)
    path = vdir / f"{ln['id']}.wav"
    path.write_bytes(wav)
    # 開始時刻をコマの区切りにそろえる（場面ごとに書き出した映像を使い回せるように。step_render の segment_key）
    t = math.ceil(t * FPS - 1e-6) / FPS
    with wave.open(str(path)) as w:
        dur = w.getnframes() / w.getframerate()
    timeline.append({**ln, "start": round(t, 5), "end": round(t + dur, 5), "dur": round(dur, 5), "kana": q["kana"],
                     "voice": {"name": VOICES[ln["who"]]["name"], **{k: p[k] for k in ("style", "speed", "inton")}}})
    return t + dur, fresh


def step_voice():
    data = load_lines()
    vdir = WORK / "voice"
    vdir.mkdir(parents=True, exist_ok=True)
    cache = WORK / "voice_cache"
    cache.mkdir(exist_ok=True)
    t, fresh, timeline = LEAD_IN, 0, []
    for ln in data["lines"]:
        end, f = place(ln, t, vdir, cache, timeline)
        fresh += f
        t = end + data["gap"] + ln.get("pause", 0.0)
    end_speech = timeline[-1]["end"]
    # 共通エンディング：その回の W の声（ノーマル）で決めゼリフを 2 つに分けて合成し、間を入れる（docs/ENDING_SPEC.md）
    ending_start = math.ceil((end_speech + ENDING["gap_after_last_line"]) * FPS) / FPS
    t = ending_start + 0.35  # 白いワイプの後に声
    w = VOICES["W"]
    for i, part in enumerate(ENDING["parts"]):
        ln = {"id": f"END{i + 1}", "who": "W", "style": "normal", "speech": part["speech"], "sub": part["speech"],
              "fact": "—", "scene": "ending", "ending": True, "speed": part["speed"], "inton": w["inton"] * part["inton_mul"]}
        end, f = place(ln, t, vdir, cache, timeline)
        fresh += f
        t = end + ENDING["pause_between"]
    total = timeline[-1]["end"] + ENDING["tail"]
    for x in timeline:
        x["env"] = envelope(vdir / f"{x['id']}.wav")
    body = [x for x in timeline if not x.get("ending")]
    tl = {"fps": FPS, "duration": round(total, 5), "endcard_start": round(ending_start, 5), "ending_start": round(ending_start, 5),
          "credits": [v["credit"] for v in VOICES.values() if isinstance(v, dict) and "credit" in v],
          "cues": build_cues(timeline), "lines": timeline}
    (WORK / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    speech = sum(x["end"] - x["start"] for x in body)
    print(f"voice: 本編 {len(body)} 行＋エンディング 2 句（新しく合成 {fresh}）, 本編セリフ {speech:.1f}s, "
          f"エンディング {ending_start:.2f}s〜, 全体 {total:.1f}s")
    for x in timeline:
        print(f"  {x['start']:6.2f}-{x['end']:6.2f} {x['who']} [{x['voice']['style']}] {x['kana']}", flush=True)


# ---------------------------------------------------------------- cues
# 映像と効果音のきっかけ。(セリフID, セリフ内の位置 0〜1)。renderer.html と同じ名前を使う
CUE_DEFS = {
    "hook": ("L01", 0.0), "crunch": ("L01", 0.62),
    "xray": ("L02", 0.0), "reveal": ("L02", 0.62), "doubt": ("L03", 0.0), "two": ("L04", 0.55),
    "title": ("L05", 0.0),
    "explode": ("L06", 0.0), "split": ("L06", 0.35), "barrier": ("L07", 0.3), "skeptic": ("L08", 0.0),
    "moisture": ("L09", 0.0), "flow": ("L10", 0.25), "soggy": ("L11", 0.0), "home": ("L12", 0.0),
    "opening": ("L13", 0.0), "spot": ("L14", 0.0), "tab": ("L15", 0.3), "pull": ("L16", 0.35), "land": ("L17", 0.42),
    "payoff": ("L18", 0.0), "correct": ("L19", 0.0), "tear": ("L19", 0.45), "jab": ("L20", 0.0), "tease": ("L21", 0.0),
    "conclusion": ("L22", 0.0), "film": ("L22", 0.6), "callback": ("L23", 0.0),
    "end1": ("END1", 0.0), "end2": ("END2", 0.0),
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


def crunch(dur=0.35, amp=0.5):
    """パリッという海苔の音（短い雑音のはじけを重ねる）。"""
    n = int(dur * SR)
    rng = np.random.default_rng(3)
    out = np.zeros(n)
    for k in range(9):
        i = int(rng.uniform(0, 0.6) * n)
        m = int(0.012 * SR)
        burst = rng.standard_normal(m) * np.exp(-np.arange(m) / (0.003 * SR))
        out[i:i + m] += burst[: max(0, n - i)] * rng.uniform(0.4, 1.0)
    return amp * out / (np.abs(out).max() + 1e-9)


def sfx_bank():
    return {
        "whoosh": noise_sweep(0.45, 300, 3000, 0.35),
        "rwhoosh": noise_sweep(0.7, 3500, 250, 0.35),  # 巻き戻し（エンディング）
        "crunch": crunch(),
        "tick": add(tone(1320, 0.12, 0.22, 0.002, 0.03), tone(2640, 0.08, 0.06, 0.002, 0.02)),
        "pop": add(tone(587.3, 0.2, 0.25, 0.003, 0.06), tone(880, 0.2, 0.12, 0.003, 0.05)),
        "doubt": add(tone(196, 0.35, 0.18, 0.01, 0.12), tone(185, 0.35, 0.14, 0.01, 0.12)),
        "zip": noise_sweep(0.5, 1500, 5000, 0.28),
        "slide": noise_sweep(0.6, 600, 2400, 0.3),
        "chime": add(tone(1046.5, 1.4, 0.22, 0.004, 0.45), tone(1568, 1.4, 0.16, 0.004, 0.4), tone(2093, 1.0, 0.08, 0.004, 0.3)),
        "end": add(tone(523.25, 2.2, 0.16, 0.01, 0.8), tone(783.99, 2.2, 0.13, 0.01, 0.8), tone(1046.5, 2.2, 0.1, 0.01, 0.8)),
    }


SFX_AT = [("crunch", "crunch"), ("whoosh", "xray"), ("pop", "reveal"), ("tick", "two"), ("whoosh", "title"),
          ("slide", "split"), ("pop", "barrier"), ("doubt", "skeptic"), ("whoosh", "moisture"), ("tick", "soggy"),
          ("whoosh", "opening"), ("zip", "tab"), ("slide", "pull"), ("chime", "land"), ("crunch", "land"),
          ("pop", "correct"), ("tick", "tear"), ("whoosh", "conclusion"), ("pop", "film"),
          ("rwhoosh", "endcard"), ("end", "end1")]


def bgm(total, cues):
    """明るいパッド＋つまびき（C - G - Am - F、96 BPM）。opening の静かな場面で一度引き、着地（land）で戻す。"""
    n = int(total * SR)
    t = np.arange(n) / SR
    chords = [[261.63, 329.63, 392.0], [196.0, 246.94, 293.66], [220.0, 261.63, 329.63], [174.61, 220.0, 261.63]]
    beat = 60 / 96
    bar = beat * 4
    out = np.zeros(n)
    for i in range(int(total / bar) + 1):
        a, b = int(i * bar * SR), min(n, int((i + 1) * bar * SR + 0.5 * SR))
        if a >= n:
            break
        seg = t[: b - a]
        env = np.minimum(1, seg / 0.4) * np.minimum(1, (seg[::-1]) / 0.6)
        ch = chords[i % 4]
        for f in ch:
            for det in (-0.7, 0.7):
                out[a:b] += env * 0.032 * np.sin(2 * np.pi * (f + det) * seg)
        out[a:b] += env * 0.035 * np.sin(2 * np.pi * ch[0] / 2 * seg)
        for k in range(8):  # 8 分音符のつまびき（和音を上下に）
            j = a + int(k * beat / 2 * SR)
            if j >= n:
                break
            f = ch[[0, 1, 2, 1, 0, 2, 1, 2][k]] * 2
            m = min(n - j, int(0.35 * SR))
            tt = np.arange(m) / SR
            out[j:j + m] += 0.028 * np.exp(-tt / 0.12) * np.sin(2 * np.pi * f * tt)
    quiet = np.clip((t - cues["spot"]) / 0.4, 0, 1) * np.clip((cues["land"] - t) / 0.3, 0, 1)
    out *= 1 - 0.6 * quiet
    fade = np.clip((cues["endcard"] + 0.2 - t) / 0.5, 0.35, 1) * np.clip(t / 0.4, 0, 1) * np.clip((total - t) / 1.0, 0, 1)
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
    music *= 1 - 0.62 * talk  # 声を BGM に埋もれさせない
    sfx = np.zeros(n)
    bank = sfx_bank()
    for name, cue in SFX_AT:
        s = bank[name]
        i = int(cues[cue] * SR)
        sfx[i:i + len(s)] += s[: max(0, n - i)]
    mix = voice + 0.85 * music + 0.5 * sfx
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
SEG_CUES = ["xray", "title", "explode", "moisture", "opening", "tab", "payoff", "conclusion", "endcard"]
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
    code = hashlib.sha256(b"".join(f.read_bytes() for f in (HERE / "renderer.html", HERE / "render_frames.js",
                                                             COMMON / "ending.js", COMMON / "vendor" / "three.min.js"))).hexdigest()
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
    ("1 冒頭の疑問", None, "xray", "明るい暖色のスタジオ。包装されたおにぎりの 3D が回りながら近づく。M の「海苔だけパリパリ？」で海苔に寄り、パリッという音", "パリッ"),
    ("2 透視", "xray", "title", "包装が半透明になり、中の層が透けて見える（X 線）。「二枚」でフィルム 2 枚がオレンジに光る", "風切り音、ポップ"),
    ("3 タイトル", "title", "explode", "白い背景に大きな文字「海苔は、なぜパリパリ？」とおにぎり", "風切り音"),
    ("4 分解", "explode", "moisture", "おにぎりの層が上下に分かれて回る 3D の分解図（外フィルム／海苔／内フィルム／ごはん）。海苔とごはんの間に光るバリア", "スライド音、ポップ"),
    ("5 水分の移動", "moisture", "opening", "左右に並べた比較：フィルムなし（水の粒がごはんから海苔へ移り、海苔がしなびる）とフィルムあり（粒がはね返される）", "風切り音"),
    ("6 開け方", "opening", "payoff", "包装のアップ。①のテープを下まで引き、②③の左右のフィルムが引き抜かれ、海苔がごはんに着地（光の輪）。「模式図」と表示", "ジッパー音、スライド音、チャイム、パリッ"),
    ("7 種明かしの後", "payoff", "conclusion", "完成したおにぎりが回る。「開ける手順＝合体の手順」。順番を飛ばすと海苔が破れる例", "ポップ"),
    ("8 結論", "conclusion", "endcard", "白い背景に「パリパリを守っていたのは……フィルム」。フィルムが光る", "風切り音、ポップ"),
    ("9 共通エンディング", "endcard", None, "白い閃光 → 明るいグラデーションに巻き戻しの円弧と大きな「リバース」、サブタイトル「世界の仕組みを、はじめから」", "巻き戻しの風切り音、和音"),
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
    rows = ["| ID | 時間 | 話者 | 声 | セリフ（読み上げ文） | 画面字幕 | 事実確認ID |", "|----|------|------|----|------------------|----------|-----------|"]
    for x in lines:
        subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
        vo = x["voice"]
        rows.append(f"| {x['id']} | {fmt(x['start'])}–{fmt(x['end'])} | {x['who']} | {vo['style']}・{vo['speed']}・{vo['inton']:.2f} | {x['speech']} | {' ／ '.join(subs)} | {x['fact']} |")
    data = load_lines()
    md = [f"# pilot_003（第 2 話）完成台本：{data['title']}", "",
          "`production_script.py docs` が `lines.json` と実際の音声の長さ（`work/timeline.json`）から生成。手で編集しない。", "",
          f"- 尺：**{tl['duration']:.1f} 秒**（本編 {tl['ending_start']:.1f} 秒＋共通エンディング {tl['duration'] - tl['ending_start']:.1f} 秒）",
          f"- 音声：M＝{VOICES['M']['credit']}（{'・'.join(VOICES['M']['styles'])}）、W＝{VOICES['W']['credit']}（{'・'.join(VOICES['W']['styles'])}）。声の設定は `production/common/voices.json`",
          "- 「声」列は、その行で使ったスタイル・話速・抑揚（voices.json の既定値を lines.json で上書きした結果）。",
          "- 事実確認 ID は `anatomy_room/scripts/pilot_003/fact_check.md` に対応。END1・END2 は全動画共通のエンディング（`docs/ENDING_SPEC.md`）。", "",
          *rows, ""]
    (HERE / "final_script.md").write_text("\n".join(md), encoding="utf-8")
    # シーン設計
    rows = ["| シーン | 時間 | 映像・CG | 音（BGM 以外） | セリフ |", "|-------|------|---------|---------------|-------|"]
    for name, a, b, video, sound in SCENES:
        ta = 0.0 if a is None else cues[a]
        tb = tl["duration"] if b is None else cues[b]
        ids = [x["id"] for x in lines if ta - .01 <= x["start"] < tb - .01]
        rows.append(f"| {name} | {fmt(ta)}–{fmt(tb)} | {video} | {sound} | {', '.join(ids) or '—'} |")
    plan = [f"# pilot_003（第 2 話）シーン設計：{data['title']}", "",
            "`production_script.py docs` が生成（時間は実際の音声にもとづく）。各シーンの描画は `renderer.html` の `scene*` 関数。", "",
            "## 画面のレイアウト（1080×1920）", "",
            "- 3D（WebGL・three.js）の層の上に、文字・字幕・ラベルを描く 2D の層を重ねる。",
            "- 主役の 3D：画面の中央 y≈350〜1150。大きな見出しは y≈250〜420。",
            "- 字幕：中心 y≈1380、文字 64px、幅 920 以内（Shorts の右側ボタン列と下部の説明欄を避ける）。白い文字に濃い半透明の帯で、明るい背景でも読める。",
            "- 明暗のリズム：明るい暖色（冒頭）→ 白（タイトル）→ 明るいグレーのスタジオ（分解）→ 淡い水色と白の比較（水分）→ スポットライト（開け方の静かな瞬間）→ 明るい暖色（着地）→ 白（結論）→ 明るいグラデーション（エンディング）。", "",
            "## シーン一覧", "", *rows, "",
            "## 演出上の注意（事実確認から決めたこと）", "",
            "- 包装の構造と開け方は製品によって異なる。開け方の場面では「※模式図。構造・開け方は商品により異なります」と表示する。",
            "- テープがどの層を裂くかは確認できていないため、映像では「真ん中で裂け、左右のフィルムが抜ける」ことだけを見せ、層ごとの裂け方は描き込まない。",
            "- 水分の移動は、ごはん→海苔へ水の粒が移る比喩表現（実際の水分子の大きさ・速さではない）。", ""]
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
    rep = ["# pilot_003（第 2 話）品質検証の記録", "", f"対象：`{OUT.name}`（{OUT.stat().st_size / 1e6:.1f} MB）", ""]
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
    rep += qc_voice(tl) + qc_ending(tl, a) + qc_picture()
    # 確認用フレーム
    times = [0.6, *[tl["cues"][k] + .6 for k in ("crunch", "reveal", "two", "title", "split", "barrier", "flow", "soggy",
                                                   "spot", "tab", "pull", "land", "correct", "tear", "film", "callback")],
             tl["cues"]["end1"] + 0.4, tl["cues"]["end2"] + 1.0]
    for i, t in enumerate(times):
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(OUT), "-frames:v", "1", "-q:v", "3", str(qdir / f"f{i:02d}_{t:05.1f}.jpg")])
    run(["montage", *sorted(str(p) for p in qdir.glob("f*.jpg")), "-tile", "6x3", "-geometry", "300x533+4+4",
         "-background", "#222", str(qdir / "contact_sheet.jpg")])
    rep += ["## 抽出フレーム", "", f"`qc/` に {len(times)} 枚、一覧は `qc/contact_sheet.jpg`。", ""]
    (HERE / "qc_report.md").write_text("\n".join(rep), encoding="utf-8")
    print("\n".join(rep[:22]))


def f0_track(a, sr=SR):
    """簡易的な基本周波数（声の高さ）の推定。40ms ごとの自己相関で、有声らしい区間だけ返す。"""
    hop, win = int(0.02 * sr), int(0.04 * sr)
    out = []
    for i in range(0, len(a) - win, hop):
        x = a[i:i + win] - a[i:i + win].mean()
        if np.sqrt(np.mean(x ** 2)) < 0.02:
            continue
        ac = np.correlate(x, x, "full")[win - 1:]
        lo, hi = int(sr / 500), int(sr / 70)  # 70〜500 Hz
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45 * ac[0]:
            out.append(sr / k)
    return out


def qc_voice(tl):
    """実際に合成された音声ファイルから、男女の声の高さと抑揚の幅を測る。"""
    rows, res = [], {}
    for who in ("M", "W"):
        f0 = []
        for x in tl["lines"]:
            if x["who"] == who and not x.get("ending"):
                f0 += f0_track(read_wav(WORK / "voice" / f"{x['id']}.wav"))
        med = float(np.median(f0))
        semis = 12 * np.log2(np.array(f0) / med)
        res[who] = med
        rows.append(f"| {who}（{VOICES[who]['name']}） | {med:.0f} Hz | {np.std(semis):.2f} 半音 | {len(f0)} |")
    gap = 12 * math.log2(res["W"] / res["M"])
    return ["## 声の聞き分け（出力された音声ファイルから測定）", "",
            "| 話者 | 声の高さ（中央値） | 抑揚の幅（標準偏差） | 測定点 |", "|------|----------------|------------------|-------|", *rows, "",
            f"- 男女の高さの差：約 {gap:.1f} 半音（第 1 話の本編音声を同じ方法で測ると約 7.0 半音）。", ""]


def qc_ending(tl, astream):
    """共通エンディングが完成動画に入っているか。"""
    body = [x for x in tl["lines"] if not x.get("ending")]
    ends = [x for x in tl["lines"] if x.get("ending")]
    out = ["## 共通エンディング（docs/ENDING_SPEC.md）", ""]
    out.append(f"- 本編の最後のセリフの終わり {body[-1]['end']:.2f}s → 決めゼリフの始まり {ends[0]['start']:.2f}s"
               f"（間 {ends[0]['start'] - body[-1]['end']:.2f}s、重なり{'なし' if ends[0]['start'] > body[-1]['end'] else 'あり'}）")
    out.append(f"- 「リバース。」と「世界の仕組みを、はじめから。」の間：{ends[1]['start'] - ends[0]['end']:.2f}s")
    for x in ends:
        r = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(x["start"]), "-t", str(x["end"] - x["start"]), "-i", str(OUT),
                 "-af", "volumedetect", "-f", "null", "-"]).stderr
        out.append(f"- {x['id']}「{x['speech']}」（{x['voice']['name']}・{x['voice']['style']}）：完成動画の該当区間の平均 "
                   f"{r.split('mean_volume:')[1].split('dB')[0].strip()} dB、最大 {r.split('max_volume:')[1].split('dB')[0].strip()} dB")
    out.append(f"- 音声トラックの長さ {float(astream['duration']):.2f}s ／ 決めゼリフの終わり {ends[-1]['end']:.2f}s ／ 動画の長さ {tl['duration']:.2f}s")
    return out + [""]


def qc_picture():
    """明るさ（1 秒ごとの平均輝度）と、映像が止まったままの区間。"""
    import re
    txt = WORK / "luma.txt"
    run(["ffmpeg", "-v", "error", "-i", str(OUT), "-vf", f"fps=1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={txt}", "-f", "null", "-"])
    ys = [float(v) for v in re.findall(r"YAVG=([\d.]+)", txt.read_text())]
    # 動き：0.5 秒ごとのコマの差（縮小画像の平均絶対差）
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(OUT), "-vf", "fps=2,scale=108:192,format=gray", "-f", "rawvideo", "-"],
                         capture_output=True).stdout
    fr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 192, 108).astype(np.float32)
    diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
    still, run_len, longest = [], 0, 0
    for i, d in enumerate(diff):
        run_len = run_len + 1 if d < 0.6 else 0
        longest = max(longest, run_len)
        if run_len == 6:  # 3 秒以上ほぼ動きなし
            still.append(f"{(i - 5) / 2:.1f}s〜")
    bright = sum(y >= 80 for y in ys)
    return ["## 明るさと動き", "",
            f"- 平均輝度：**{np.mean(ys):.1f} / 255**（第 1 話は 36.6）。最小 {min(ys):.1f}、最大 {max(ys):.1f}。輝度 80 以上のコマ {bright}/{len(ys)}（第 1 話は 0/91）",
            f"- 1 秒ごとの輝度：{' '.join(f'{y:.0f}' for y in ys)}",
            f"- 動き：0.5 秒ごとのコマの差の平均 {diff.mean():.2f}。ほぼ止まっている区間（3 秒以上）：{'、'.join(still) if still else 'なし'}（最長 {longest / 2:.1f} 秒）", ""]


# ---------------------------------------------------------------- main
STEPS = {"voice": step_voice, "audio": step_audio, "render": step_render, "mux": step_mux, "docs": step_docs, "qc": step_qc,
         "update": step_update}

if __name__ == "__main__":
    names = sys.argv[1:] or ["all"]
    if names == ["all"]:
        names = ["voice", "audio", "render", "mux", "docs", "qc"]
    for n in names:
        STEPS[n]()
