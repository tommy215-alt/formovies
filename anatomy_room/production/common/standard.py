"""リバースの標準の制作設定（REVERSE_STANDARD_RULES v2、2026-10-27〜）。

新しい回の production_script.py では、指定しなかった項目にこの既定値が入るように使う：

    import standard
    EP = standard.config({
        "out": "reverse_011_xxx.mp4",
        "cues": {...}, "sfx": [...], "segments": [...], "scenes": {...},
        "music": {"sections": [...]},          # style を書かなければ tech_drive
    })
    pipeline.main(__file__, EP)

声の版は lines.json の "voices" に書く（標準は "v7"）。
v3（2026-10-28〜）：字幕と重要な文字は約 1.2 倍（renderer.html で Stage.docSub と Stage.TEXT_SCALE）、色調は感情に合わせて Stage.moodGrade。既存の回（pilot_006〜010）はこのファイルを使わないので、変わらない。
"""
import copy

VOICES = "v7"   # lines.json の "voices"：玄野武宏のナレーション＋文末の「いる・いた・ある」をつなげる（語尾上がりの対策）

DEFAULTS = {
    "logo": False,                 # 左上の固定ロゴは出さない（個別に出す回だけ True）
    "lead_in": 0.1,                # 最初のセリフまでの秒（1 拍目の音のすぐあと）。冒頭 1 秒以内に話し始める（video_qa の「冒頭 3 秒」で 1.0 秒以内を確認）
    "sfx_bank": "soft",            # やわらかい音色＋自然の音。鋭い高音・大音量は使わない
    "sfx_duck": 0.7,               # セリフ中は効果音を 0.7 倍に
    "music_lp": 6000,              # BGM の高音を丸める（ハイハットが刺さらない範囲で、ビートの輪郭は残す）
    "music": {
        "style": "tech_drive",     # ビートのあるダークなテクノ／インダストリアル（124 BPM）
        # 区間の例（きっかけ, ずらす秒, モード）。冒頭は 1 拍目から doc_hook、解説は doc_drive、発見へ doc_build、
        # 一瞬の引きに doc_break（2〜4 秒まで）、核心で doc_peak、余韻は doc_outro、エンディングは ending
        # v3（2026-10-28〜）：単一のループで押し切らず、感情に合わせて変える。不安＝doc_tense、努力が実る瞬間＝doc_hope（長調の和音が差し込む）、
        # 対立・孤独＝doc_alone、現代の日常＝doc_warm → doc_warm_end（例は pilot_012 の production_script.py）
        "sections": [("t0", 0.0, "doc_hook"), ("end1", -0.6, "ending")],
    },
}


def config(ep):
    """その回の設定 ep を、標準の既定値に重ねる（ep に書いた項目が優先。music は中身ごとに重ねる）"""
    out = copy.deepcopy(DEFAULTS)
    for k, v in ep.items():
        if k == "music" and isinstance(v, dict):
            out["music"].update(v)
        else:
            out[k] = v
    return out
