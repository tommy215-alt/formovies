"""リバースの制作の土台（kit、2026-11-01〜）：各回の production_script.py の決まった準備をまとめる。テンプレートの外の部品。

使い方（各回の production_script.py）：
    sys.path.insert(0, str(HERE.parent / "ext" / "kit"))
    import epkit
    pipeline, standard = epkit.setup(HERE, "tragedy", bgm=("Danse Macabre.mp3", 67))
    EP = standard.config({..., "extra_files": epkit.FILES, ...})

設計ごとの違い（templates/DESIGN_MODES.md）：
- intel（知的）・dopa（ドパ）：共通エンディングの短い版（ending_ext）、オープニングの音は衝撃波の一発（opening_bgm の open_impact）。
- tragedy（悲劇）：共通エンディングなし（noend_ext、最後は black 秒かけて暗転）、オープニングはホラー調の音（bgm_file のモード h）。
- BGM は外のフリー音源（assets/bgm/ の mp3、bgm_file）。スタイル名は "file_<回の番号>"。
"""
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent
PROD = KIT.parent.parent
for p in (PROD / "common", PROD / "ext"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

V3 = ["../ext/vendor/three147/" + f for f in ["GLTFLoader.js", "RGBELoader.js", "Pass.js", "EffectComposer.js", "RenderPass.js", "ShaderPass.js",
                                               "CopyShader.js", "SimplexNoise.js", "SSAOShader.js", "SSAOPass.js", "BokehShader.js", "BokehPass.js"]]
FILES = ["../ext/hud_ext.js", "../common/cine.js", "../ext/kit/kit.js", "../ext/kit/scene_assets.js", "assets/assets.js"] + V3


def setup(here, design, bgm, black=2.6, ending_gain=None):
    """bgm＝(assets/bgm のファイル名, BPM)。戻り値は (pipeline, standard)"""
    import pipeline
    import standard
    import music_ext  # noqa: F401
    import bgm_file   # 曲のファイル（opening_bgm より先に読む：opening_bgm が bgm_file を包む）
    import ending_ext
    ending_ext.apply(pipeline)
    if design == "tragedy":
        import noend_ext
        noend_ext.apply(pipeline, black=black)
    else:
        import opening_bgm  # noqa: F401
    name = "file_" + Path(here).name.split("_")[-1]
    gains = {"ending": ending_gain if ending_gain is not None else ("m0w70" if design == "tragedy" else .35)}
    bgm_file.register(name, Path(here) / "assets" / "bgm" / bgm[0], bpm=bgm[1], gains=gains, smooth=2.0 if design == "tragedy" else .4)
    return pipeline, standard
