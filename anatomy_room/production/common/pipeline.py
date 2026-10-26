"""チャンネル「リバース」の新構成（第 3 話以降：pilot_006〜）の共通制作パイプライン。

第 2 話（pilot_003/production_script.py）をもとに、各話で違う部分（きっかけ・効果音・場面・BGM の構成）を
各話の production_script.py の設定（EP）に分けた版。各話のフォルダで

  python3 production_script.py voice    # VOICEVOX でセリフを合成 → work/voice/*.wav, timeline.json
  python3 production_script.py audio    # BGM・効果音を合成してミックス → work/mix.wav（パートごとの音も work/ に）
  python3 production_script.py render   # 映像（renderer.html を Playwright でコマ撮り）→ work/video.mp4
  python3 production_script.py mux      # 映像と音声を合成 → 完成 MP4
  python3 production_script.py docs     # final_script.md・scene_plan.md・subtitles.srt
  python3 production_script.py qc       # 完成 MP4 の検証（尺・デコード・音量・テンポ・明るさ・エンディング・フレーム抽出）
  python3 production_script.py all      # voice → audio → render → mux → docs → qc
  python3 production_script.py update   # 修正後の作り直し（変えた行の音声と、変わった場面の映像だけ作り直す）

前提：VOICEVOX ENGINE 0.24.1 を 127.0.0.1:50021 で起動。ffmpeg、Node.js + Playwright、Noto Sans CJK JP。
"""
import hashlib
import json
import math
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np

COMMON = Path(__file__).resolve().parent
sys.path.insert(0, str(COMMON))
import music  # noqa: E402

SR = 48000
FPS = 30
ENGINE = "http://127.0.0.1:50021"
LEAD_IN = 0.25  # 最初のセリフまでの間（冒頭からすぐ始める）
EP2_RATE = 5.27  # 第 2 話の本編のテンポ（間を含む 1 秒あたりのモーラ数。pilot_003 の timeline から測定）


class Episode:
    def __init__(self, here, cfg):
        self.here = Path(here).resolve().parent
        self.work = self.here / "work"
        self.cfg = cfg
        self.out = self.here / cfg["out"]
        vc = json.loads((COMMON / "voices.json").read_text(encoding="utf-8"))
        self.voices = vc[self.lines()["voices"]]
        self.ending = vc["ending"]

    def lines(self):
        return json.loads((self.here / "lines.json").read_text(encoding="utf-8"))

    def tl(self):
        return json.loads((self.work / "timeline.json").read_text(encoding="utf-8"))

    # ------------------------------------------------------------ voice
    def voice_params(self, ln):
        v = self.voices[ln["who"]]
        style = ln.get("style", v["default_style"])
        return {"speaker": v["styles"][style], "style": style, "speed": ln.get("speed", v["speed"]),
                "pitch": ln.get("pitch", v["pitch"]), "inton": ln.get("inton", v["inton"])}

    def synth_cached(self, ln, cache):
        p = self.voice_params(ln)
        key = hashlib.sha256(json.dumps([ln["speech"], p, SR], ensure_ascii=False).encode()).hexdigest()[:16]
        cw, cq = cache / f"{key}.wav", cache / f"{key}.json"
        if cw.exists() and cq.exists():
            return cw.read_bytes(), json.loads(cq.read_text(encoding="utf-8")), p, False
        req = urllib.request.Request(f"{ENGINE}/audio_query?text={urllib.parse.quote(ln['speech'])}&speaker={p['speaker']}",
                                     method="POST")
        q = json.loads(urllib.request.urlopen(req, timeout=60).read())
        q.update(speedScale=p["speed"], pitchScale=p["pitch"], intonationScale=p["inton"], prePhonemeLength=0.03,
                 postPhonemeLength=0.05, outputSamplingRate=SR, outputStereo=False)
        req = urllib.request.Request(f"{ENGINE}/synthesis?speaker={p['speaker']}", data=json.dumps(q).encode(),
                                     headers={"Content-Type": "application/json"})
        wav = urllib.request.urlopen(req, timeout=120).read()
        cw.write_bytes(wav); cq.write_text(json.dumps(q, ensure_ascii=False), encoding="utf-8")
        return wav, q, p, True

    def place(self, ln, t, vdir, cache, timeline):
        wav, q, p, fresh = self.synth_cached(ln, cache)
        path = vdir / f"{ln['id']}.wav"
        path.write_bytes(wav)
        t = math.ceil(t * FPS - 1e-6) / FPS  # コマの区切りにそろえる（場面ごとの映像を使い回すため）
        with wave.open(str(path)) as w:
            dur = w.getnframes() / w.getframerate()
        timeline.append({**ln, "start": round(t, 5), "end": round(t + dur, 5), "dur": round(dur, 5), "kana": q["kana"],
                         "voice": {"name": self.voices[ln["who"]]["name"], **{k: p[k] for k in ("style", "speed", "inton")}}})
        return t + dur, fresh

    def step_voice(self):
        data = self.lines()
        vdir = self.work / "voice"
        vdir.mkdir(parents=True, exist_ok=True)
        cache = self.work / "voice_cache"
        cache.mkdir(exist_ok=True)
        t, fresh, timeline = LEAD_IN, 0, []
        for ln in data["lines"]:
            end, f = self.place(ln, t, vdir, cache, timeline)
            fresh += f
            t = end + data["gap"] + ln.get("pause", 0.0)
        end_speech = timeline[-1]["end"]
        # 共通エンディング：その回の W の声で、決めゼリフを 2 つに分けて合成し、間を入れる（docs/ENDING_SPEC.md）
        ending_start = math.ceil((end_speech + self.ending["gap_after_last_line"]) * FPS) / FPS
        t = ending_start + 0.35
        w = self.voices["W"]
        for i, part in enumerate(self.ending["parts"]):
            ln = {"id": f"END{i + 1}", "who": "W", "style": "normal", "speech": part["speech"], "sub": part["speech"],
                  "fact": "—", "scene": "ending", "ending": True, "speed": part["speed"], "inton": w["inton"] * part["inton_mul"]}
            end, f = self.place(ln, t, vdir, cache, timeline)
            fresh += f
            t = end + self.ending["pause_between"]
        total = timeline[-1]["end"] + self.ending["tail"]
        for x in timeline:
            x["env"] = envelope(vdir / f"{x['id']}.wav")
        names = {k: self.voices[k].get("display", k) for k in ("M", "W")}
        tl = {"fps": FPS, "duration": round(total, 5), "endcard_start": round(ending_start, 5),
              "ending_start": round(ending_start, 5), "names": names,
              "credits": [self.voices[k]["credit"] for k in ("M", "W")],
              "cues": self.build_cues(timeline), "lines": timeline}
        (self.work / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
        body = [x for x in timeline if not x.get("ending")]
        print(f"voice: 本編 {len(body)} 行＋エンディング 2 句（新しく合成 {fresh}）, 本編 {body[-1]['end']:.1f}s, "
              f"エンディング {ending_start:.2f}s〜, 全体 {total:.1f}s, テンポ {pace(body):.2f} モーラ/秒（第 2 話 {EP2_RATE}）")
        for x in timeline:
            print(f"  {x['start']:6.2f}-{x['end']:6.2f} {x['who']} [{x['voice']['style']}] {x['kana']}", flush=True)

    def build_cues(self, timeline):
        by = {x["id"]: x for x in timeline}
        cues = {}
        for name, (lid, frac) in self.cfg["cues"].items():
            x = by[lid]
            cues[name] = round(x["start"] + frac * (x["end"] - x["start"]), 5)
        cues["end1"], cues["end2"] = by["END1"]["start"], by["END2"]["start"]
        return cues

    # ------------------------------------------------------------ audio
    def sections(self, tl):
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        sec = [(max(0.0, cues[c] + off), mode) for c, off, mode in self.cfg["music"]["sections"]]
        sec.append((tl["ending_start"] - 0.05, "ending"))
        return sorted(sec)

    def step_audio(self):
        tl = self.tl()
        total = tl["duration"]
        n = int(total * SR) + SR
        voice = np.zeros(n)
        for x in tl["lines"]:
            a = read_wav(self.work / "voice" / f"{x['id']}.wav")
            i = int(x["start"] * SR)
            voice[i:i + len(a)] += a
        for x in tl["lines"]:  # 話者ごとに音量をそろえる（RMS を -20 dBFS 付近へ）
            i, j = int(x["start"] * SR), int(x["end"] * SR)
            r = np.sqrt(np.mean(voice[i:j] ** 2)) + 1e-9
            voice[i:j] *= min(4.0, 0.1 / r)
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        m = self.cfg["music"]
        bg, _ = music.bgm(total, self.sections(tl), m["style"], m.get("seed", 0))
        mus = np.zeros(n)
        mus[: len(bg)] = bg
        # ダッキング：セリフ中は BGM を下げる（解説のモードでは BGM 自体も控えめ）。立ち上がり 0.08 秒、戻り 0.3 秒
        talk = np.zeros(n)
        for x in tl["lines"]:
            talk[int(x["start"] * SR):int(x["end"] * SR)] = 1
        att, rel = int(0.08 * SR), int(0.3 * SR)
        env = np.convolve(talk, np.ones(att) / att, mode="same")
        env = np.maximum(env, np.convolve(talk, np.ones(rel) / rel, mode="full")[: n])
        duck = 1 - 0.6 * np.clip(env, 0, 1)
        mus *= duck
        sfx = np.zeros(n)
        bank = music.sfx_bank()
        for name, cue, *rest in self.cfg["sfx"]:
            s = bank[name] * (rest[0] if rest else 1.0)
            i = int(cues[cue] * SR)
            sfx[i:i + len(s)] += s[: max(0, n - i)]
        mix = voice + 0.8 * mus + 0.5 * sfx
        write_wav(self.work / "mix_raw.wav", mix[: int(total * SR)])
        write_wav(self.work / "music.wav", (0.8 * mus)[: int(total * SR)])  # 検証用（BGM だけ・ダッキング後）
        write_wav(self.work / "voice_only.wav", voice[: int(total * SR)])
        meas = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(self.work / "mix_raw.wav"), "-af",
                               "loudnorm=I=-14:TP=-2.0:LRA=11:print_format=json", "-f", "null", "-"],
                              capture_output=True, text=True).stderr
        st = json.loads(meas[meas.rindex("{"):meas.rindex("}") + 1])
        af = (f"loudnorm=I=-14:TP=-2.0:LRA=11:measured_I={st['input_i']}:measured_TP={st['input_tp']}:"
              f"measured_LRA={st['input_lra']}:measured_thresh={st['input_thresh']}:offset={st['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(self.work / "mix_raw.wav"),
                        "-af", af, "-ar", str(SR), str(self.work / "mix.wav")], check=True)
        print(f"audio: {total:.1f}s, BGM {m['style']}（{music.STYLES[m['style']]['bpm']} BPM）, "
              f"元の積分ラウドネス {st['input_i']} LUFS → -14 LUFS")

    # ------------------------------------------------------------ render / mux
    def segment_key(self, tl, a, b, code):
        fps = tl["fps"]
        t0, t1 = a / fps, b / fps
        lo, hi = t0 - 1.5, t1 + 1.5
        rel = lambda v: round((v - t0) * fps, 1) + 0.0
        lines = [{"who": x["who"], "sub": x["sub"], "env": x["env"], "s": round((x["start"] - t0) * fps), "d": x["dur"]}
                 for x in tl["lines"] if x["end"] > lo and x["start"] < hi]
        cues = sorted((k, rel(v)) for k, v in tl["cues"].items() if lo <= v <= hi)
        extra = [rel(tl["ending_start"])] if lo <= tl["ending_start"] <= hi else []
        blob = json.dumps([code, fps, b - a, lines, cues, extra, tl["credits"], tl["names"]], ensure_ascii=False)
        return hashlib.sha256(blob.encode()).hexdigest()[:16]

    def step_render(self):
        tl = self.tl()
        fps, n = tl["fps"], math.ceil(tl["duration"] * tl["fps"])
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        bounds = sorted(set([0] + [round(cues[c] * fps) for c in self.cfg["segments"]] + [round(cues["endcard"] * fps), n]))
        files = [self.here / "renderer.html", COMMON / "render_frames.js", COMMON / "stage.js", COMMON / "ending.js",
                 COMMON / "vendor" / "three.min.js"] + [self.here / f for f in self.cfg.get("extra_files", [])]
        code = hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()
        sdir = self.work / "segments"
        sdir.mkdir(parents=True, exist_ok=True)
        segs = [{"a": a, "b": b, "out": str(sdir / f"{self.segment_key(tl, a, b, code)}.mp4")}
                for a, b in zip(bounds, bounds[1:]) if b > a]
        todo = [s for s in segs if not Path(s["out"]).exists()]
        print(f"render: 場面 {len(segs)} 個のうち、書き出しが必要なのは {len(todo)} 個"
              f"（{sum(s['b'] - s['a'] for s in todo)} / {n} コマ）", flush=True)
        if todo:
            workers = self.cfg.get("workers", 3)
            jobs = [[] for _ in range(min(workers, len(todo)))]
            for s in sorted(todo, key=lambda s: s["a"] - s["b"]):
                min(jobs, key=lambda j: sum(x["b"] - x["a"] for x in j)).append(s)
            procs = []
            for i, j in enumerate(jobs):
                jf = self.work / f"job{i}.json"
                jf.write_text(json.dumps(j), encoding="utf-8")
                procs.append(subprocess.Popen(["node", str(COMMON / "render_frames.js"), "--dir", str(self.here),
                                               "--segments", str(jf)]))
            if any(p.wait() for p in procs):
                sys.exit("render: 書き出しに失敗した場面がある")
        lst = self.work / "concat.txt"
        lst.write_text("".join(f"file '{s['out']}'\n" for s in segs), encoding="utf-8")
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                        "-c", "copy", "-movflags", "+faststart", str(self.work / "video.mp4")], check=True)
        print(f"render: {len(segs)} 場面をつないで work/video.mp4（{n} コマ）")

    def step_mux(self):
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(self.work / "video.mp4"),
                        "-i", str(self.work / "mix.wav"), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(self.out)], check=True)
        print("mux:", self.out.name, f"{self.out.stat().st_size / 1e6:.1f} MB")

    # ------------------------------------------------------------ docs
    def step_docs(self):
        tl = self.tl()
        cues = {**tl["cues"], "endcard": tl["ending_start"]}
        lines = tl["lines"]
        nm = tl["names"]
        pid = self.cfg["id"]
        srt, k = [], 1
        for x in lines:
            for a, b, s in sub_chunks(x):
                ts = lambda v: f"{int(v // 3600):02d}:{int(v % 3600 // 60):02d}:{int(v % 60):02d},{int(v * 1000 % 1000):03d}"
                srt.append(f"{k}\n{ts(a)} --> {ts(b)}\n{nm[x['who']]}：{s.replace('**', '').replace(' / ', chr(10))}\n")
                k += 1
        (self.here / "subtitles.srt").write_text("\n".join(srt), encoding="utf-8")
        rows = ["| ID | 時間 | 話者 | 声（スタイル・話速・抑揚） | セリフ（読み上げ文） | 画面字幕 | 事実確認ID |",
                "|----|------|------|------------------------|------------------|----------|-----------|"]
        for x in lines:
            subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
            vo = x["voice"]
            rows.append(f"| {x['id']} | {fmt(x['start'])}–{fmt(x['end'])} | {nm[x['who']]} | {vo['style']}・{vo['speed']}・{vo['inton']:.2f} "
                        f"| {x['speech']} | {' ／ '.join(subs)} | {x['fact']} |")
        data = self.lines()
        body = [x for x in lines if not x.get("ending")]
        md = [f"# {pid} 完成台本：{data['title']}", "",
              "`production_script.py docs` が `lines.json` と実際の音声の長さ（`work/timeline.json`）から生成。手で編集しない。", "",
              f"- 尺：**{tl['duration']:.1f} 秒**（本編 {tl['ending_start']:.1f} 秒＋共通エンディング {tl['duration'] - tl['ending_start']:.1f} 秒）",
              f"- テンポ：本編 {pace(body):.2f} モーラ/秒（間を含む。第 2 話は {EP2_RATE}、比 {pace(body) / EP2_RATE:.2f} 倍）",
              f"- 声：オモテ（M）＝{self.voices['M']['credit']}、ウラ（W）＝{self.voices['W']['credit']}。設定は `production/common/voices.json` の `{data['voices']}`",
              f"- 事実確認 ID は `anatomy_room/scripts/{pid}/fact_check.md` に対応。END1・END2 は全動画共通のエンディング（`docs/ENDING_SPEC.md`）。", "",
              *rows, ""]
        (self.here / "final_script.md").write_text("\n".join(md), encoding="utf-8")
        rows = ["| シーン | 時間 | 映像・CG | 音（BGM のモード・効果音） | セリフ |", "|-------|------|---------|------------------------|-------|"]
        for name, a, b, video, sound in self.cfg["scenes"]:
            ta = 0.0 if a is None else cues[a]
            tb = tl["duration"] if b is None else cues[b]
            ids = [x["id"] for x in lines if ta - .01 <= x["start"] < tb - .01]
            rows.append(f"| {name} | {fmt(ta)}–{fmt(tb)} | {video} | {sound} | {', '.join(ids) or '—'} |")
        plan = [f"# {pid} シーン設計（CG 演出）：{data['title']}", "",
                "`production_script.py docs` が生成（時間は実際の音声にもとづく）。描画は `renderer.html`。", "",
                *self.cfg.get("plan_notes", []), "", "## シーン一覧", "", *rows, ""]
        (self.here / "scene_plan.md").write_text("\n".join(plan), encoding="utf-8")
        print("docs: final_script.md, scene_plan.md, subtitles.srt")

    # ------------------------------------------------------------ qc
    def step_qc(self):
        out = self.out
        qdir = self.here / "qc"
        qdir.mkdir(exist_ok=True)
        for old in qdir.glob("*.jpg"):
            old.unlink()
        tl = self.tl()
        rep = [f"# {self.cfg['id']} 品質検証の記録", "", f"対象：`{out.name}`（{out.stat().st_size / 1e6:.1f} MB）", ""]
        pr = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(out)]).stdout)
        v = next(s for s in pr["streams"] if s["codec_type"] == "video")
        a = next(s for s in pr["streams"] if s["codec_type"] == "audio")
        rep += ["## ストリーム", "",
                f"- 映像：{v['codec_name']} {v['width']}×{v['height']}、{v['r_frame_rate']} fps、{v['pix_fmt']}、{v.get('nb_frames')} フレーム、{float(v['duration']):.2f} 秒",
                f"- 音声：{a['codec_name']} {a['sample_rate']} Hz {a['channels']} ch、{float(a['duration']):.2f} 秒",
                f"- 全体の尺：{float(pr['format']['duration']):.2f} 秒（設計値 {tl['duration']:.2f} 秒）", ""]
        dec = run(["ffmpeg", "-v", "error", "-i", str(out), "-f", "null", "-"])
        rep += ["## 全編デコード", "", f"- エラー出力：{'なし' if not dec.stderr.strip() else dec.stderr.strip()[:500]}", ""]
        lo = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
        summ = lo[lo.rindex("Summary:"):]
        pick = lambda key: summ.split(key)[1].split("\n")[0].strip()
        rep += ["## 音量", "", f"- 積分ラウドネス：{pick('I:')}（目標 −14 LUFS）", f"- ラウドネスレンジ：{pick('LRA:')}",
                f"- トゥルーピーク：{pick('Peak:')}（目標 −1.0 dBTP 以下）", ""]
        si = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(out), "-af", "silencedetect=n=-45dB:d=0.8", "-f", "null", "-"]).stderr
        sil = [ln.split("]")[1].strip() for ln in si.splitlines() if "silence_end" in ln]
        rep += ["## 無音区間（−45 dB 未満が 0.8 秒以上）", "", *(f"- {s}" for s in sil), "- なし" if not sil else "", ""]
        rows = []
        for x in tl["lines"]:
            r = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(x["start"]), "-t", str(x["end"] - x["start"]), "-i", str(out),
                     "-af", "volumedetect", "-f", "null", "-"]).stderr
            rows.append(f"| {x['id']} | {tl['names'][x['who']]} | {fmt(x['start'])} | {r.split('mean_volume:')[1].split('dB')[0].strip()} "
                        f"| {r.split('max_volume:')[1].split('dB')[0].strip()} |")
        rep += ["## セリフごとの音量（完成動画から、dB）", "", "| ID | 話者 | 開始 | 平均 | 最大 |", "|----|------|------|------|------|", *rows, ""]
        short = [(x["id"], s, b - a_) for x in tl["lines"] for a_, b, s in sub_chunks(x) if b - a_ < 0.7]
        rep += ["## 字幕の表示時間", "", f"- 字幕 {sum(len(sub_chunks(x)) for x in tl['lines'])} 枚。0.7 秒未満："
                + ("なし" if not short else "、".join(f"{i}「{s.replace('**', '')}」{d:.2f}s" for i, s, d in short)), ""]
        rep += ["## 読み上げの照合（VOICEVOX が使った読み）", "", "| ID | 字幕 | 読み（カナ） |", "|----|------|------------|",
                *[f"| {x['id']} | {' ／ '.join(x['sub'] if isinstance(x['sub'], list) else [x['sub']]).replace('**', '')} | {x['kana']} |"
                  for x in tl["lines"]], ""]
        rep += self.qc_voice(tl) + self.qc_music(tl) + self.qc_ending(tl, a) + self.qc_picture()
        times = [0.5] + [tl["cues"][k] + d for k, d in self.cfg["qc_frames"]] + [tl["cues"]["end1"] + 0.4, tl["cues"]["end2"] + 1.0]
        for i, t in enumerate(times):
            run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(out), "-frames:v", "1", "-q:v", "3",
                 str(qdir / f"f{i:02d}_{t:05.1f}.jpg")])
        cols = 7
        run(["montage", *sorted(str(p) for p in qdir.glob("f*.jpg")), "-tile", f"{cols}x{math.ceil(len(times) / cols)}",
             "-geometry", "300x533+4+4", "-background", "#222", str(qdir / "contact_sheet.jpg")])
        rep += ["## 抽出フレーム", "", f"`qc/` に {len(times)} 枚、一覧は `qc/contact_sheet.jpg`。", ""]
        (self.here / "qc_report.md").write_text("\n".join(rep), encoding="utf-8")
        print("\n".join(l for l in rep if not l.startswith("| L") and not l.startswith("| END")))

    def qc_voice(self, tl):
        rows, res = [], {}
        for who in ("M", "W"):
            f0 = []
            for x in tl["lines"]:
                if x["who"] == who and not x.get("ending"):
                    f0 += f0_track(read_wav(self.work / "voice" / f"{x['id']}.wav"))
            med = float(np.median(f0))
            res[who] = med
            rows.append(f"| {tl['names'][who]}（{self.voices[who]['name']}） | {med:.0f} Hz | {np.std(12 * np.log2(np.array(f0) / med)):.2f} 半音 | {len(f0)} |")
        body = [x for x in tl["lines"] if not x.get("ending")]
        gaps = [b["start"] - a_["end"] for a_, b in zip(body, body[1:])]
        sp = {w: speech_rate([x for x in body if x["who"] == w]) for w in ("M", "W")}
        return ["## 声とテンポ（出力された音声ファイルから測定）", "",
                "| 話者 | 声の高さ（中央値） | 抑揚の幅 | 測定点 |", "|------|----------------|---------|-------|", *rows, "",
                f"- 男女の高さの差：約 {12 * math.log2(res['W'] / res['M']):.1f} 半音",
                f"- テンポ（本編、間を含む）：**{pace(body):.2f} モーラ/秒**（第 2 話 {EP2_RATE} の **{pace(body) / EP2_RATE:.2f} 倍**）",
                f"- 話す速さ（間を除く）：オモテ {sp['M']:.2f}、ウラ {sp['W']:.2f} モーラ/秒（第 2 話は M 5.45、W 5.86）",
                f"- セリフの間：中央値 {np.median(gaps):.2f} 秒、最大 {max(gaps):.2f} 秒（第 2 話は 0.19 秒＋行ごとの間）", ""]

    def qc_music(self, tl):
        mus = read_wav(self.work / "music.wav", stereo_ok=True)
        bpm = music.estimate_bpm(mus)
        sec = self.sections(tl) + [(tl["duration"], None)]
        rows = []
        for (s0, mode), (s1, _) in zip(sec, sec[1:]):
            if s1 - s0 < 0.3:
                continue
            seg = mus[int(s0 * SR):int(s1 * SR)]
            db = 20 * math.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
            rows.append(f"| {fmt(s0)}–{fmt(s1)} | {mode} | {db:.1f} |")
        st = self.cfg["music"]["style"]
        return ["## BGM（ダッキング後の BGM だけを測定）", "",
                f"- スタイル {st}、設計 {music.STYLES[st]['bpm']} BPM。BGM の音から推定したテンポ：**{bpm:.1f} BPM**（第 2 話の BGM は 96 BPM）",
                "- 場面ごとの BGM の大きさ（RMS、dBFS）。モードで厚さと音量が変わっていることの確認：", "",
                "| 区間 | モード | BGM の大きさ |", "|------|-------|------------|", *rows, ""]

    def qc_ending(self, tl, astream):
        body = [x for x in tl["lines"] if not x.get("ending")]
        ends = [x for x in tl["lines"] if x.get("ending")]
        out = ["## 共通エンディング（docs/ENDING_SPEC.md）", "",
               f"- 本編の最後のセリフの終わり {body[-1]['end']:.2f}s → 決めゼリフ {ends[0]['start']:.2f}s（間 {ends[0]['start'] - body[-1]['end']:.2f}s、"
               f"重なり{'なし' if ends[0]['start'] > body[-1]['end'] else 'あり'}）",
               f"- 2 句の間：{ends[1]['start'] - ends[0]['end']:.2f}s、エンディングの長さ {tl['duration'] - tl['ending_start']:.2f}s"]
        for x in ends:
            r = run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(x["start"]), "-t", str(x["end"] - x["start"]), "-i", str(self.out),
                     "-af", "volumedetect", "-f", "null", "-"]).stderr
            out.append(f"- {x['id']}「{x['speech']}」（{x['voice']['name']}）：完成動画の該当区間 平均 "
                       f"{r.split('mean_volume:')[1].split('dB')[0].strip()} dB、最大 {r.split('max_volume:')[1].split('dB')[0].strip()} dB")
        out.append(f"- 音声トラック {float(astream['duration']):.2f}s ／ 決めゼリフの終わり {ends[-1]['end']:.2f}s ／ 動画 {tl['duration']:.2f}s")
        return out + [""]

    def qc_picture(self):
        txt = self.work / "luma.txt"
        run(["ffmpeg", "-v", "error", "-i", str(self.out), "-vf", f"fps=1,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={txt}",
             "-f", "null", "-"])
        ys = [float(v) for v in re.findall(r"YAVG=([\d.]+)", txt.read_text())]
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(self.out), "-vf", "fps=2,scale=108:192,format=gray", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 192, 108).astype(np.float32)
        diff = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))
        still, run_len, longest = [], 0, 0
        for i, d in enumerate(diff):
            run_len = run_len + 1 if d < 0.6 else 0
            longest = max(longest, run_len)
            if run_len == 6:
                still.append(f"{(i - 5) / 2:.1f}s〜")
        return ["## 明るさと動き", "",
                f"- 平均輝度：**{np.mean(ys):.1f} / 255**（第 1 話 36.6、第 2 話 185.6）。最小 {min(ys):.1f}。輝度 80 以上の秒 {sum(y >= 80 for y in ys)}/{len(ys)}",
                f"- 1 秒ごとの輝度：{' '.join(f'{y:.0f}' for y in ys)}",
                f"- 動き：0.5 秒ごとのコマの差の平均 {diff.mean():.2f}。3 秒以上ほぼ止まっている区間：{'、'.join(still) if still else 'なし'}"
                f"（最長 {longest / 2:.1f} 秒）", ""]


# ---------------------------------------------------------------- helpers
def envelope(path, fps=FPS):
    with wave.open(str(path)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        sr = w.getframerate()
    hop = sr // fps
    n = len(a) // hop
    rms = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    peak = max(float(rms.max()), 1e-6)
    return [round(float(v) / peak, 3) for v in rms]


def read_wav(path, stereo_ok=False):
    with wave.open(str(path)) as w:
        ch = w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        assert w.getframerate() == SR, path
    return a.reshape(-1, ch).mean(axis=1) if ch > 1 else a


def write_wav(path, a):
    a = np.clip(a, -1, 1)
    if a.ndim == 1:
        a = np.stack([a, a], axis=1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((a * 32767).astype(np.int16).tobytes())


def mora(kana):
    k = re.sub(r"[ '/、_？?！!。]", "", kana)
    return len(re.sub(r"[ャュョァィゥェォ]", "", k))


def pace(body):
    """間を含むテンポ（本編の最初のセリフの始まりから最後の終わりまで、1 秒あたりのモーラ数）。"""
    return sum(mora(x["kana"]) for x in body) / (body[-1]["end"] - body[0]["start"])


def speech_rate(xs):
    return sum(mora(x["kana"]) for x in xs) / max(1e-9, sum(x["dur"] for x in xs))


def fmt(t):
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}"


def sub_chunks(x):
    subs = x["sub"] if isinstance(x["sub"], list) else [x["sub"]]
    lens = [len(s.replace("**", "").replace(" / ", "")) for s in subs]
    tot, acc, out = sum(lens), 0, []
    for s, n in zip(subs, lens):
        a = x["start"] + (x["end"] - x["start"]) * acc / tot
        acc += n
        out.append((a, x["start"] + (x["end"] - x["start"]) * acc / tot, s))
    return out


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def f0_track(a, sr=SR):
    hop, win = int(0.02 * sr), int(0.04 * sr)
    out = []
    for i in range(0, len(a) - win, hop):
        x = a[i:i + win] - a[i:i + win].mean()
        if np.sqrt(np.mean(x ** 2)) < 0.02:
            continue
        ac = np.correlate(x, x, "full")[win - 1:]
        lo, hi = int(sr / 500), int(sr / 70)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.45 * ac[0]:
            out.append(sr / k)
    return out


def main(here, cfg):
    ep = Episode(here, cfg)
    steps = {"voice": ep.step_voice, "audio": ep.step_audio, "render": ep.step_render, "mux": ep.step_mux,
             "docs": ep.step_docs, "qc": ep.step_qc}
    names = sys.argv[1:] or ["all"]
    if names == ["all"]:
        names = ["voice", "audio", "render", "mux", "docs", "qc"]
    if names == ["update"]:
        names = ["voice", "audio", "render", "mux", "docs", "qc"]
    for n in names:
        steps[n]()
