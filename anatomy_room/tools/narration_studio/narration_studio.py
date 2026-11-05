#!/usr/bin/env python3
"""ナレーション収録スタジオ（2026-11-05〜、ユーザーの依頼「台本を上げたらカラオケみたいに読む字幕が出て、録音ボタンで録音。
基本は自動編集で、ピッチと響きだけ変えられるソフト」）。PC の中だけで動く（127.0.0.1）。

使い方（リポジトリの直下で）：
    python anatomy_room/tools/narration_studio/narration_studio.py            # ブラウザで収録画面が開く
    python anatomy_room/tools/narration_studio/narration_studio.py long_001   # その回の台本（lines.json）を開いた状態で始める

流れ：
1. 台本を開く：動画の回（production/<回>/lines.json ＋共通エンディングの決めゼリフ 2 句）か、貼り付けた文章（文ごとに区切る）。
2. 収録：いまの行が大きく出る。録音ボタン（スペースキー）で録音を始めると、目標の速さで文字の色が変わっていく（カラオケ）。
   もう一度押すと止まり、自動で次の行へ。取り直しは行を選んでもう一度録るだけ。
3. 自動編集（録った行から裏で順に）：
   ① 音声認識（faster-whisper、large-v3-turbo、CPU）で単語ごとの時刻 → 「あー」「えー」「えっと」などのフィラーを除き、
      言い直したときは最後の読み直しから使い、長い息つぎを詰める（編集の結果は edit/<行>.wav）
   ② 声の加工：低い雑音の除去・雑音の軽減・サ行の刺さりを抑える・低音を強め（低音域の持ち上げ＋こもりの抑え＋明瞭さ）・
      コンプレッサー・ピッチ（rubberband、フォルマント保持）・話す速さを目標にそろえる・響き（合成した残響）・音量をそろえる
      （結果は out/<行>.wav）。ピッチと響きを変えると②だけをやり直す。
4. 書き出し：動画の回なら production/<回>/recording/final/ に置き、lines.json に "recorded": true を書く
   → production/ext/recorded_ext.py が合成音声の代わりに使う。
保存先：動画の回は production/<回>/recording/、文章のときは tools/narration_studio/projects/<名前>/。
"""
import json
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from difflib import SequenceMatcher
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # anatomy_room
PROD = ROOT / "production"
PORT = 8765
SR = 48000
DEFAULT_SETTINGS = {"pitch": 0.0, "reverb": 0, "rate": 7.0, "credit": "", "mode": "ai", "proc": 3}   # ピッチ（半音）・響き（%）・目標の速さ（モーラ/秒）・加工の版
PUNCT = re.compile(r"[\s、。，．,.!！?？「」『』（）()・…ー〜~]")

# ---------------------------------------------------------------------------- 台本
class Project:
    def __init__(self):
        self.name, self.episode, self.dir, self.lines = None, None, None, []
        self.settings = dict(DEFAULT_SETTINGS)
        self.status = {}          # 行 → {"state": 未録音|処理待ち|処理中|完了|失敗, "dur", "msg", "words", "rev"}
        self.lock = threading.Lock()

    def open_episode(self, ep):
        d = PROD / ep
        data = json.loads((d / "lines.json").read_text(encoding="utf-8"))
        ending = json.loads((PROD / "common" / "voices.json").read_text(encoding="utf-8"))["ending"]["parts"]
        lines = [{"id": x["id"], "speech": x["speech"], "sub": x.get("sub", x["speech"])} for x in data["lines"]]
        lines += [{"id": f"END{i + 1}", "speech": p["speech"], "sub": p["speech"]} for i, p in enumerate(ending)]
        self._set(ep, ep, d / "recording", lines)

    def open_text(self, name, text):
        sents = [s.strip() for s in re.split(r"(?<=[。！？!?])\s*|\n+", text) if s.strip()]
        lines = [{"id": f"S{i + 1:03d}", "speech": s, "sub": s} for i, s in enumerate(sents)]
        safe = re.sub(r"[^\w\-]", "_", name or "text")
        self._set(safe, None, HERE / "projects" / safe, lines)

    def _set(self, name, episode, d, lines):
        with self.lock:
            self.name, self.episode, self.dir, self.lines = name, episode, d, lines
            for sub in ("raw", "edit", "out"):
                (d / sub).mkdir(parents=True, exist_ok=True)
            sf = d / "studio.json"
            saved = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
            self.settings = {**DEFAULT_SETTINGS, **saved.get("settings", {})}
            if self.settings.get("proc", 1) < PROC_VERSION:    # 加工の版が上がったら、ピッチと響きも新しい既定値に
                self.settings.update(pitch=DEFAULT_SETTINGS["pitch"], reverb=DEFAULT_SETTINGS["reverb"],
                                     mode=DEFAULT_SETTINGS["mode"], proc=PROC_VERSION)
            for ln in lines:
                ln["moras"] = moras(ln["speech"])
            self.status = {}
            for ln in lines:
                st = saved.get("status", {}).get(ln["id"])
                raw = self.raw_path(ln["id"])
                if raw and st and st.get("state") == "完了" and st.get("proc", 1) < PROC_VERSION:
                    self.status[ln["id"]] = {**st, "state": "処理待ち"}; JOBS.put((ln["id"], "render"))   # 新しい加工で作り直す
                elif raw and st and st.get("state") in ("完了", "失敗"):
                    self.status[ln["id"]] = st
                elif raw:
                    self.status[ln["id"]] = {"state": "処理待ち"}; JOBS.put((ln["id"], "full"))
                else:
                    self.status[ln["id"]] = {"state": "未録音"}
            self.save()

    def raw_path(self, lid):
        for p in self.dir.glob(f"raw/{lid}.*"):
            return p
        return None

    def line(self, lid):
        return next(x for x in self.lines if x["id"] == lid)

    def save(self):
        (self.dir / "studio.json").write_text(json.dumps({"name": self.name, "episode": self.episode, "settings": self.settings,
                                                          "status": self.status}, ensure_ascii=False, indent=1), encoding="utf-8")


P = Project()
JOBS = queue.Queue()


def moras(text):
    """読みのモーラ数（音声エンジンが動いていれば audio_query から、なければ文字数からの見積もり）"""
    for eng, spk in (("http://127.0.0.1:10101", 1310138977), ("http://127.0.0.1:50021", 13)):
        try:
            u = f"{eng}/audio_query?" + urllib.parse.urlencode({"speaker": spk, "text": text})
            q = json.loads(urllib.request.urlopen(urllib.request.Request(u, method="POST"), timeout=5).read())
            return sum(len(ap["moras"]) for ap in q["accent_phrases"])
        except Exception:
            continue
    return round(len(PUNCT.sub("", text)) * 1.35)


# ---------------------------------------------------------------------------- 音声の入出力
def decode(path, sr=SR):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def write_wav(path, x, sr=SR):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", str(path)], input=y, check=True)


def ffmpeg_filter(x, af, sr=SR):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2").tobytes()
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "s16le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", af,
                          "-ar", str(sr), "-ac", "1", "-f", "f32le", "-"], input=y, check=True, capture_output=True).stdout
    return np.frombuffer(out, dtype=np.float32).astype(np.float64)


# ---------------------------------------------------------------------------- ① 編集（フィラー・言い直し・長い間）
_MODEL = None


def model():
    global _MODEL
    if _MODEL is None:
        from faster_whisper import WhisperModel
        _MODEL = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    return _MODEL


def edit(lid):
    ln = P.line(lid)
    x = decode(P.raw_path(lid))
    x16 = decode(P.raw_path(lid), 16000).astype(np.float32)
    segs, _ = model().transcribe(x16, language="ja", word_timestamps=True, beam_size=5, condition_on_previous_text=False,
                                 initial_prompt="えー、あのー、えっと、まあ、" + ln["speech"])
    words = [{"t": w.word.strip(), "s": w.start, "e": w.end} for sg in segs for w in (sg.words or []) if w.word.strip()]
    # 文字起こしを台本と文字単位で突き合わせ、台本にない部分（フィラー・言いかけ・言い直しの前半）を除く。
    # 言い直したときは、台本といちばん長く一致する読み（ふつうは最後の読み直し）が残る
    script = PUNCT.sub("", ln["speech"])
    owner = []                                     # 文字起こしの各文字 → 単語の番号
    for i, w in enumerate(words):
        owner += [i] * len(PUNCT.sub("", w["t"]))
    heard = "".join(PUNCT.sub("", w["t"]) for w in words)
    sm = SequenceMatcher(None, heard, script, autojunk=False)
    extra = np.zeros(len(words))
    for op, a1, a2, _, _ in sm.get_opcodes():
        if op == "insert" or op == "equal" or op == "replace":
            continue
        for k in range(a1, a2):                    # op == "delete"：聞こえたが台本にない文字
            extra[owner[k]] += 1
    for i, w in enumerate(words):
        n = len(PUNCT.sub("", w["t"]))
        w["filler"] = n == 0 or extra[i] / n >= .5
    # 台本とほとんど合わないとき（認識の失敗・無音で文字を作ってしまったとき）は単語では切らず、前後の無音だけを切る
    match = round(SequenceMatcher(None, heard, script, autojunk=False).ratio(), 2) if heard else 0
    kept = [w for w in words if not w["filler"]] if match >= .4 else []
    if not kept:   # 認識できなかったときは、音の大きさで前後の無音だけを切る
        env = np.convolve(np.abs(x), np.ones(960) / 960, "same"); on = np.where(env > env.max() * .06)[0]
        segs_t = [(max(0, on[0] / SR - .05), min(len(x) / SR, on[-1] / SR + .1))] if len(on) else [(0, len(x) / SR)]
    else:
        iv = [[max(0, w["s"] - .06), min(len(x) / SR, w["e"] + .09)] for w in kept]
        segs_t = [iv[0]]
        for a, b in iv[1:]:
            if a - segs_t[-1][1] < .12:
                segs_t[-1][1] = max(segs_t[-1][1], b)
            else:
                segs_t.append([a, b])
    out, prev = [], None
    for a, b in segs_t:
        if prev is not None:
            gap = a - prev
            keep = min(gap, .24)                       # 長い間・息つぎは 0.24 秒まで詰める（間の部屋の音はそのまま使う）
            i0 = int(prev * SR); out.append(x[i0:i0 + int(keep * SR)])
        out.append(x[int(a * SR):int(b * SR)]); prev = b
    y = np.concatenate(out) if out else x
    fade = int(.01 * SR); y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    write_wav(P.dir / "edit" / f"{lid}.wav", y)
    return {"words": [w["t"] for w in words], "match": match,
            "cut": [w["t"] for w in words if w["filler"] and PUNCT.sub("", w["t"])] if kept else []}


# ---------------------------------------------------------------------------- ② 声の加工（ピッチと響きはここだけ）
PROC_VERSION = 3   # 加工の版。上げると、開いたときに完了済みの行を新しい加工で作り直す
# v3：AI（Resemble Enhance）で作り直し＋薄い仕上げ（render_ai）。v2 の加工は「従来の加工」として残す（render_classic）
# v2（2026-11-05、ユーザー「加工が弱い・お風呂にいるみたい。スタジオのように、声はかなり強めに」）：
#   部屋の反響を取り除く（残響抑制）、足す響きは小さな部屋の短い響きに（既定 0）、低音・箱鳴りの削り・コンプを強く、言葉の間の部屋の音を下げる


def impulse(seconds=0.35, seed=3):
    """足す響き：録音ブースのような小さな部屋（短い初期反射＋0.35 秒で消える残響）"""
    r = np.random.default_rng(seed); n = int(seconds * SR); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-t / (seconds / 6.5)) * .5
    for d, g in ((.004, .5), (.007, .35), (.011, .3), (.016, .22)):
        ir[int(d * SR)] += g * 8
    lp = np.convolve(ir, np.ones(15) / 15, "same")      # 高い音を丸める（金属的に響かないように）
    return lp / np.sqrt(np.sum(lp ** 2))


def stft(x, n=1024, hop=256):
    w = np.hanning(n)
    pad = np.concatenate([np.zeros(n), x, np.zeros(n)])
    frames = np.lib.stride_tricks.sliding_window_view(pad, n)[::hop] * w
    return np.fft.rfft(frames, axis=1), w


def istft(X, w, length, n=1024, hop=256):
    frames = np.fft.irfft(X, n, axis=1) * w
    out = np.zeros(hop * (len(frames) - 1) + n); norm = np.zeros_like(out)
    for i, f in enumerate(frames):
        out[i * hop:i * hop + n] += f; norm[i * hop:i * hop + n] += w ** 2
    return (out / np.maximum(norm, 1e-8))[n:n + length]


def dereverb(x, t60=0.6, strength=1.6, floor_db=-18):
    """部屋の反響（後部残響）と定常の雑音を、周波数ごとに引き算する（Lebart らの方法）。
    いまの音の強さから「少し前の音が残響として残っている分」を見積もり、それを超えない分だけを残す"""
    hop = 256
    X, w = stft(x, hop=hop)
    Pw = np.abs(X) ** 2
    Pw_s = Pw.copy()                                  # 時間方向になめらかにした強さ
    for i in range(1, len(Pw_s)):
        Pw_s[i] = .6 * Pw_s[i - 1] + .4 * Pw[i]
    td = int(.05 * SR / hop)                          # 50 ms より後ろの反響を消す
    decay = np.exp(-2 * (3 * np.log(10) / t60) * td * hop / SR)
    late = np.zeros_like(Pw); late[td:] = decay * Pw_s[:-td]
    noise = np.percentile(Pw_s, 12, axis=0)           # いちばん静かな部分＝部屋の雑音
    g = 1 - (strength * late + 1.5 * noise) / np.maximum(Pw, 1e-12)
    g = np.clip(g, 10 ** (floor_db / 20), 1)
    for i in range(1, len(g)):                        # ゲインの急な変化（ぶくぶくした音）を抑える
        g[i] = np.maximum(g[i], .7 * g[i - 1] + .3 * g[i])
    return istft(X * g, w, len(x), hop=hop)


IR = None


def fftconv(a, b):
    n = len(a) + len(b) - 1; N = 1 << (n - 1).bit_length()
    return np.fft.irfft(np.fft.rfft(a, N) * np.fft.rfft(b, N), N)[:len(a)]


class Enhancer:
    """AI の声の作り直し（enhance_runner.py）を専用の環境で常駐させる。環境がなければ使えない（従来の加工になる）"""
    PY = Path(os.environ.get("LOCALAPPDATA", "")) / "reverse_tools" / "enhance" / "Scripts" / "python.exe"

    def __init__(self):
        self.proc, self.lock = None, threading.Lock()

    def available(self):
        return self.PY.exists()

    def run(self, src, dst, lambd=0.9, tau=0.5):
        with self.lock:
            if self.proc is None or self.proc.poll() is not None:
                self.proc = subprocess.Popen([str(self.PY), str(HERE / "enhance_runner.py")], stdin=subprocess.PIPE,
                                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
                ready = json.loads(self.proc.stdout.readline() or '{"ready": false}')
                if not ready.get("ready"):
                    raise RuntimeError("AI の準備に失敗しました")
            self.proc.stdin.write(json.dumps({"in": str(src), "out": str(dst), "lambd": lambd, "tau": tau}) + "\n")
            self.proc.stdin.flush()
            r = json.loads(self.proc.stdout.readline() or '{"ok": false, "error": "AI のプロセスが止まりました"}')
            if not r.get("ok"):
                raise RuntimeError(r.get("error"))
            return r


ENH = Enhancer()


def render(lid):
    st = P.settings
    if st.get("mode", "ai") == "ai" and ENH.available():
        return render_ai(lid)
    return render_classic(lid)


def finish(y, lid, tempo):
    """足す響き（スライダー）→ 話している部分の大きさを -18 dBFS（RMS）に → 書き出し"""
    global IR
    st = P.settings
    if st["reverb"] > 0:
        if IR is None:
            IR = impulse()
        y = np.concatenate([y, np.zeros(int(.4 * SR))])
        wet = fftconv(y, IR)
        y = y + wet * (st["reverb"] / 100) * .25
        tail = np.where(np.abs(y) > 1e-3)[0]; y = y[:tail[-1] + int(.05 * SR)] if len(tail) else y
    # loudnorm は短い音だと静かな部分を持ち上げるので使わない
    n = int(.02 * SR); m = len(y) // n
    e = (y[:m * n].reshape(m, n) ** 2).mean(1)
    act = e[e > e.max() * 10 ** (-3.5)] if m else np.array([1e-4])
    y = y * 10 ** (-18 / 20) / np.sqrt(act.mean() + 1e-12)
    y = ffmpeg_filter(y, "alimiter=limit=0.89:attack=2:release=40:level=disabled")
    pad = np.zeros(int(.03 * SR)); y = np.concatenate([pad, y, pad])
    write_wav(P.dir / "out" / f"{lid}.wav", y)
    return len(y) / SR, tempo


def render_ai(lid):
    """v3（2026-11-05、ユーザー「加工感が強くて違和感。生のアナウンサーが読んだような感じに」）：
    AI（Resemble Enhance）で反響と雑音を取り、スタジオで録ったような声に作り直す。そのあとの加工は薄く（自然さを優先）：
    ピッチは 0 なら変えない、速さはそろえるが幅を狭く（0.94〜1.06 倍）、低音は少しの温かさだけ、コンプは軽く"""
    ln, st = P.line(lid), P.settings
    src, ai = P.dir / "edit" / f"{lid}.wav", P.dir / "ai" / f"{lid}.wav"
    ai.parent.mkdir(exist_ok=True)
    if not ai.exists() or ai.stat().st_mtime < src.stat().st_mtime:   # AI の結果は、編集し直したときだけ作り直す
        ENH.run(src, ai)
    x = decode(ai)
    dur = len(x) / SR
    target = ln["moras"] / st["rate"]
    tempo = max(.94, min(1.06, dur / target)) if target > 0 else 1.0
    chain = ["highpass=f=60",
             "bass=g=3:f=110:w=0.8",                     # 少しの温かさ（低音強めの好みに合わせて、やりすぎない）
             "equalizer=f=350:t=q:w=1.2:g=-1.5",         # 軽いこもりの抑え
             "acompressor=threshold=-18dB:ratio=2:attack=12:release=220:knee=6:makeup=1.5",   # 抑揚を残す軽いコンプ
             "deesser=i=0.3:m=0.5:f=0.5"]
    if abs(st["pitch"]) > 1e-6 or abs(tempo - 1) > .005:
        chain.append(f"rubberband=pitch={2 ** (st['pitch'] / 12):.5f}:tempo={tempo:.4f}:formant=preserved")
    return finish(ffmpeg_filter(x, ",".join(chain)), lid, tempo)


def render_classic(lid):
    """v2 の加工（手作りの残響抑制＋強めの加工）。設定の「従来の加工」で使う"""
    ln, st = P.line(lid), P.settings
    x = decode(P.dir / "edit" / f"{lid}.wav")
    dur = len(x) / SR
    target = ln["moras"] / st["rate"]                       # 目標の速さで読んだときの長さ
    tempo = max(.88, min(1.15, dur / target)) if target > 0 else 1.0   # 速さをそろえる（0.88〜1.15 倍まで）
    pitch = 2 ** (st["pitch"] / 12)
    # 順番が大事：コンプは言葉の後ろの反響まで持ち上げる（強いコンプだけだと、大きい音と静かな音の差が 18→8 dB に縮んで
    # お風呂のように聞こえた）。反響をコンプの前で強く取り、コンプのあとでもう一度軽く取る（ユーザーの録音で、静かな部分が
    # 録音そのままより約 11 dB 下がることを確かめた）
    x = ffmpeg_filter(x, "highpass=f=75:p=2")
    x = x / (np.abs(x).max() + 1e-9) * .7
    x = dereverb(x, t60=0.8, strength=3, floor_db=-25)       # 部屋の反響と雑音を取る（お風呂のような響きの元）
    x = x / (np.abs(x).max() + 1e-9) * .7                   # 以下のしきい値が録音の大きさに左右されないように
    x = ffmpeg_filter(x, ",".join([
        "bass=g=10:f=120:w=0.7",                         # 低音を強く（近くで話すような厚み）
        "equalizer=f=190:t=q:w=1.0:g=2",                 # 胸の響きの温かさ
        "equalizer=f=420:t=q:w=1.2:g=-4.5",              # PC マイクの箱鳴り・こもりを削る
        "equalizer=f=900:t=q:w=1.5:g=-1.5",              # 鼻にかかった音を抑える
        "equalizer=f=3500:t=q:w=1.0:g=3",                # 言葉の輪郭
        "treble=g=1.5:f=11000",                          # 空気感（明るさ）
        "acompressor=threshold=-20dB:ratio=3.5:attack=5:release=200:knee=4:makeup=3",   # 声の大きさをそろえて前に出す
        "asoftclip=type=tanh:threshold=0.95",            # 少しだけ温かい歪み
    ]))
    x = dereverb(x, t60=0.6, strength=2, floor_db=-20)       # コンプで持ち上がった反響をもう一度取る
    y = ffmpeg_filter(x, ",".join([
        "deesser=i=0.5:m=0.6:f=0.5",
        f"rubberband=pitch={pitch:.5f}:tempo={tempo:.4f}:formant=preserved:transients=smooth",
    ]))
    return finish(y, lid, tempo)


def worker():
    while True:
        lid, kind = JOBS.get()
        try:
            if lid not in P.status:
                continue
            P.status[lid] = {**P.status[lid], "state": "処理中"}
            info = {}
            if kind == "full" or not (P.dir / "edit" / f"{lid}.wav").exists():
                info = edit(lid)
            dur, tempo = render(lid)
            P.status[lid] = {**P.status[lid], **info, "state": "完了", "dur": round(dur, 2), "tempo": round(tempo, 3),
                             "rev": time.time(), "proc": PROC_VERSION}
        except Exception as e:
            P.status[lid] = {**P.status.get(lid, {}), "state": "失敗", "msg": str(e)[:300]}
        finally:
            P.save()


# ---------------------------------------------------------------------------- 書き出し
def export():
    done = [ln["id"] for ln in P.lines if P.status.get(ln["id"], {}).get("state") == "完了"]
    if P.episode:
        fd = P.dir / "final"; fd.mkdir(exist_ok=True)
        for lid in done:
            (fd / f"{lid}.wav").write_bytes((P.dir / "out" / f"{lid}.wav").read_bytes())
        lp = PROD / P.episode / "lines.json"; d = json.loads(lp.read_text(encoding="utf-8"))
        d["recorded"] = True
        if P.settings.get("credit"):
            d["recorded_credit"] = P.settings["credit"]
        lp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        return {"dir": str(fd), "count": len(done), "missing": [x["id"] for x in P.lines if x["id"] not in done]}
    allx = [decode(P.dir / "out" / f"{lid}.wav") for lid in done]
    gap = np.zeros(int(.35 * SR))
    y = np.concatenate([np.concatenate([a, gap]) for a in allx]) if allx else np.zeros(1)
    out = P.dir / f"{P.name}_narration.wav"; write_wav(out, y)
    return {"file": str(out), "count": len(done)}


# ---------------------------------------------------------------------------- サーバー
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(b)

    def body(self):
        return self.rfile.read(int(self.headers.get("Content-Length", 0)))

    def do_GET(self):
        u = urllib.parse.urlparse(self.path); parts = u.path.strip("/").split("/")
        if u.path in ("/", "/index.html"):
            return self.send(200, (HERE / "studio.html").read_bytes(), "text/html; charset=utf-8")
        if u.path == "/api/state":
            eps = sorted(p.parent.name for p in PROD.glob("*/lines.json"))
            return self.send(200, {"name": P.name, "episode": P.episode, "settings": P.settings, "episodes": eps,
                                   "lines": [{**ln, **P.status.get(ln["id"], {})} for ln in P.lines], "queue": JOBS.qsize()})
        if parts[:2] == ["api", "audio"] and len(parts) == 4:
            lid, kind = parts[2], parts[3]
            p = P.raw_path(lid) if kind == "raw" else P.dir / kind / f"{lid}.wav"
            if p and p.exists():
                return self.send(200, p.read_bytes(), "audio/webm" if p.suffix == ".webm" else "audio/wav")
            return self.send(404, {"error": "no audio"})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path); parts = u.path.strip("/").split("/")
        try:
            if u.path == "/api/open":
                d = json.loads(self.body())
                P.open_episode(d["episode"]) if d.get("episode") else P.open_text(d.get("name", "text"), d["text"])
                return self.send(200, {"ok": True})
            if parts[:2] == ["api", "record"] and len(parts) == 3:
                lid = parts[2]; ext = "webm" if "webm" in self.headers.get("Content-Type", "") else "wav"
                for old in P.dir.glob(f"raw/{lid}.*"):
                    old.unlink()
                (P.dir / "raw" / f"{lid}.{ext}").write_bytes(self.body())
                P.status[lid] = {"state": "処理待ち"}; JOBS.put((lid, "full")); P.save()
                return self.send(200, {"ok": True})
            if u.path == "/api/settings":
                d = json.loads(self.body())
                for k in ("pitch", "reverb", "credit", "mode"):
                    if k in d:
                        P.settings[k] = d[k]
                for ln in P.lines:
                    if P.status.get(ln["id"], {}).get("state") == "完了":
                        P.status[ln["id"]]["state"] = "処理待ち"; JOBS.put((ln["id"], "render"))
                P.save()
                return self.send(200, {"ok": True})
            if u.path == "/api/export":
                return self.send(200, export())
        except Exception as e:
            return self.send(500, {"error": str(e)})
        self.send(404, {"error": "not found"})


def main():
    threading.Thread(target=worker, daemon=True).start()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        P.open_episode(args[0])
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"ナレーション収録スタジオ：http://127.0.0.1:{PORT}/ （止めるときは Ctrl+C）")
    if "--no-browser" not in sys.argv:
        threading.Thread(target=lambda: (time.sleep(.8), webbrowser.open(f"http://127.0.0.1:{PORT}/")), daemon=True).start()
    threading.Thread(target=model, daemon=True).start()     # 音声認識のモデルを先に読み込んでおく
    srv.serve_forever()


if __name__ == "__main__":
    main()
