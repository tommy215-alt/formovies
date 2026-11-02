"""AivisSpeech の声を使う（2026-11-02〜、ユーザーの選んだ声：阿井田 茂）。テンプレートの外の部品。

AivisSpeech Engine（無料・LGPL）は VOICEVOX と同じ API なので、pipeline.py の合成をそのまま使い、
声の設定に "engine" があるときだけ問い合わせ先を切り替える。"engine" がない声は従来どおり VOICEVOX（127.0.0.1:50021）。

使い方（lines.json の voice_override、または voices.json の版）：
    "M": {"name": "阿井田 茂", "credit": "AivisSpeech: 阿井田 茂", "engine": "http://127.0.0.1:10101",
          "styles": {"calm": 1310138977, "normal": 1310138976}, "default_style": "calm", "speed": 1.15, "pitch": 0.0, "inton": 1.0}
- AivisSpeech の intonationScale は「スタイルの強さ」。pitch は 0 のまま（変えると声が崩れる）。
- merge_aux（文末の「いる」をつなげる VOICEVOX 向けの直し）は AivisSpeech では使わない（自然な抑揚になるため）。
- エンジンの起動：%LOCALAPPDATA%\\reverse_tools\\aivis\\Windows-x64\\run.exe --port 10101 --use_gpu（docs/PC_SETUP.md）。
- 声のモデルは AivisHub の ACML 1.0（商用可・クレジット「AivisSpeech: 名前」）か CC0 だけ。ACML-NC は使わない。
- 共通エンディングの決めゼリフは、W を差し替えた回も voices.json の版の W（冥鳴ひまり）が読む（クレジットにも足す）。

全設計の既定（2026-11-02、ユーザーの指示）：本編のナレーション M＝阿井田 茂 Calm、冒頭（L00）と最後の決めゼリフ＝W 冥鳴ひまり（いままでどおり）、
ドパ設計の叫ぶ行（style "shout"）＝VOICEVOX 青山龍星「熱血」のまま。lines.json には
    "voices": "v7", "voice_override": {"M": {"preset": "aida", "speed": 1.5}, "W": {"speed": 1.3, "inton": 1.0}}
と書く（preset の中身は PRESETS。書いた項目が preset より優先）。叫ぶ行がある回は credit を "AivisSpeech: 阿井田 茂／VOICEVOX:青山龍星" に。
style_engine：スタイルごとの問い合わせ先（叫ぶ行だけ VOICEVOX に回す）。
"""
import json

VOICEVOX = "http://127.0.0.1:50021"
AIVIS = "http://127.0.0.1:10101"
PRESETS = {
    "aida": {"name": "阿井田 茂", "display": "ナレーション", "credit": "AivisSpeech: 阿井田 茂", "engine": AIVIS,
             "styles": {"calm": 1310138977, "normal": 1310138977, "plain": 1310138976, "shout": 81},   # normal は Calm と同じ（従来の行の書き方のまま）、shout は VOICEVOX 青山龍星「熱血」
             "style_engine": {"shout": VOICEVOX}, "default_style": "calm", "speed": 1.5, "pitch": 0.0, "inton": 1.0, "merge_aux": False},
}


def apply(pipeline):
    E = pipeline.Episode
    if getattr(E, "_aivis_ext", False):
        return
    E._aivis_ext = True
    vp0, sc0, init0, sv0, ln0 = E.voice_params, E.synth_cached, E.__init__, E.step_voice, E.lines

    def lines(self):
        d = ln0(self)
        for who, ov in d.get("voice_override", {}).items():
            if isinstance(ov, dict) and "preset" in ov:
                d["voice_override"][who] = {**PRESETS[ov["preset"]], **{k: v for k, v in ov.items() if k != "preset"}}
        return d

    def __init__(self, here, cfg):
        init0(self, here, cfg)
        vc = json.loads((pipeline.COMMON / "voices.json").read_text(encoding="utf-8"))
        self._end_W = vc[self.lines()["voices"]]["W"]   # 共通エンディングの決めゼリフは、W を差し替えた回も元の W（冥鳴ひまり）の声

    def voice_params(self, ln):
        if ln.get("ending"):
            cur, self.voices = self.voices, {**self.voices, "W": self._end_W}
            try:
                return vp0(self, ln)
            finally:
                self.voices = cur
        p = vp0(self, ln)
        v = self.voices[ln["who"]]
        eng = v.get("style_engine", {}).get(p["style"], v.get("engine"))
        if eng and eng != VOICEVOX:
            p["engine"] = eng          # キャッシュのキーにも入る（VOICEVOX の声のキーは変わらない）
            p.pop("merge_aux", None)
        return p

    def synth_cached(self, ln, cache):
        eng = voice_params(self, ln).get("engine", VOICEVOX)
        old, pipeline.ENGINE = pipeline.ENGINE, eng
        try:
            return sc0(self, ln, cache)
        finally:
            pipeline.ENGINE = old

    def step_voice(self):
        r = sv0(self)
        f = self.work / "timeline.json"
        tl = json.loads(f.read_text(encoding="utf-8"))
        c = self._end_W["credit"]
        if any(x.get("ending") for x in tl["lines"]) and c not in tl["credits"]:   # 決めゼリフの声のクレジットも載せる
            tl["credits"].append(c)
            f.write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
        return r

    E.__init__, E.voice_params, E.synth_cached, E.step_voice, E.lines = __init__, voice_params, synth_cached, step_voice, lines
