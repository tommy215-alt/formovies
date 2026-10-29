"""共通エンディングの短い版（2026-10-29〜、ユーザーの承認：標準ルール v6 の未決事項の案 2）。テンプレートの外に足す（common/voices.json・pipeline.py は変えない）。

案 2：明るい専用の画面をやめ、本編の最後の画の上にロゴと決めゼリフを重ねる（描画は renderer.html で HUD.endingOverlay）。
決めゼリフ（W の声「リバース。」「世界の仕組みを、はじめから。」）はそのまま。間だけを詰める。

各話の production_script.py で：
    import ending_ext
    ending_ext.apply(pipeline)            # 既定の短い間（SHORT）を、その回の処理の中だけで使う
"""
SHORT = {"gap_after_last_line": 0.15, "pause_between": 0.25, "tail": 0.45}   # 旧：0.6・0.5・0.8（約 5.2 秒 → 約 3.9 秒）
SPEED2 = 1.0                                                                 # 2 句目の話速（旧 0.9）


def apply(pipeline, **over):
    vals = {**SHORT, **over}
    if getattr(pipeline.Episode, "_ending_ext", False):
        return
    init0 = pipeline.Episode.__init__

    def init(self, *a, **k):
        init0(self, *a, **k)
        e = dict(self.ending)
        e.update({k_: v for k_, v in vals.items() if k_ in ("gap_after_last_line", "pause_between", "tail")})
        e["parts"] = [dict(p) for p in e["parts"]]
        if len(e["parts"]) > 1:
            e["parts"][1]["speed"] = vals.get("speed2", SPEED2)
        self.ending = e

    pipeline.Episode.__init__ = init
    pipeline.Episode._ending_ext = True
