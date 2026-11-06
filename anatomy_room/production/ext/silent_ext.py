"""ナレーションのない回（2026-11-06〜、pilot_045 v2。ユーザー「ナレーションはなしにして、情報はポップアップで」）。

lines.json に "silent": true がある回だけ、各行を声の代わりに無音（長さは行の "hold" 秒）で置く。
行はショットの区切り（cue）として残るので、timeline.json・効果音のきっかけ・場面の切り替えは従来どおり使える。
クレジットから合成音声の名前を外す。テンプレートの外の部品で、pipeline.Episode の synth_cached・step_voice を包む（common/ は変えない）。
"""
import io
import json
import wave


def _silence(sec, sr):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(b"\0\0" * int(round(sec * sr)))
    return b.getvalue()


def apply(pipeline):
    E = pipeline.Episode
    if getattr(E, "_silent_ext", False):
        return
    E._silent_ext = True
    sc0, sv0 = E.synth_cached, E.step_voice

    def synth_cached(self, ln, cache):
        if not self.lines().get("silent"):
            return sc0(self, ln, cache)
        # 共通エンディングの句（このあと noend_ext が外す）も無音にする
        p = {"speaker": 0, "style": "normal", "speed": 1.0, "pitch": 0.0, "inton": 1.0, "silent": True}
        q = {"kana": "", "accent_phrases": [], "speedScale": 1.0, "prePhonemeLength": 0.0}
        return _silence(float(ln.get("hold", 0.5)), pipeline.SR), q, p, False

    def step_voice(self):
        r = sv0(self)
        if self.lines().get("silent"):
            f = self.work / "timeline.json"
            tl = json.loads(f.read_text(encoding="utf-8"))
            tl["credits"] = []
            tl["silent"] = True
            f.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
        return r

    E.synth_cached, E.step_voice = synth_cached, step_voice
    # 字幕のない行（sub が空）は、資料（docs・qc）の字幕の区切りから外す（0 で割らない）
    sc_ = pipeline.sub_chunks
    pipeline.sub_chunks = lambda x: [] if not "".join(x["sub"] if isinstance(x["sub"], list) else [x["sub"]]).strip() else sc_(x)
