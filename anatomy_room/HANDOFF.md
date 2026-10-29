# 引き継ぎ（2026-10-29 更新）

会話のコンテキストが切れたときのためのメモ。新しい会話は CLAUDE.md の次にこれを読む。

## いまの作業：pilot_016（ヴェーゲナー）の作り直し

ユーザーの指示（2026-10-29）：
1. BGM：試聴で選んだ B03・B06・B08・B10・B14 を、短調の和音にして正式な曲調に（`lab_melodic`・`lab_electro`・`lab_break`・`lab_2step`・`lab_dub`）。動画ごとに使い分ける。→ `templates/REVERSE_GUIDELINE_v2.3.md`
2. CG の質を上げる（テクノロジー感・迫力・人物の思い。時間をかけてよい）。→ 同上の 2
3. 以上を設定として保存し、pilot_016 を作り直す。映像の内容・声・台本は前回のまま（ユーザーが「映像、音声は完璧」と言った）。変えるのは BGM と CG の質だけ。

進め方：
- [x] `production/ext/bgm_lab.py` に `bgm_style(total, sections, style)`（パートごとに作り、モードで厚さを変える）と短調の進行を足し、`music_ext.py` から 5 つの曲調を登録する
- [x] pilot_016 の `production_script.py` の `music.style` を `lab_melodic`（人物のドラマ）に
- [x] `renderer.html` の CG を上げる（holoDraw・studyShot・吹雪。静止画で確認済み）：地図を 3D のホログラムの台に貼る（傾き・奥行き・光の粒・走査の光）、冒頭の合わさる瞬間に衝撃波とカメラの揺れ、夜の書斎の場面（地図に向かう後ろ姿、L04〜L06 と L09 に）、吹雪の強化（風の筋・前かがみ）
- [x] 静止画で確認 → `python anatomy_room/tools/rv.py 016 render all`（完了：2026-10-29、20.9 分） → video_qa・全コマの確認 → 自己レビュー更新 → commit・push → URL を報告

## 決まったこと（この会話で）

- 書き出しは `rv.py`（変わった場面だけ）。最終の確認は 1 秒ごとの一覧（`qa/sheet_*.jpg`）。
- 事実確認は ChatGPT に依頼文で調べてもらい、Claude が出典で確かめ直す。台本はユーザーの「OK」で制作開始。
- 共通エンディングは短い版（pilot_016〜）。
- 話速 1.15・行間 0.05 秒（pilot_016 でユーザーが指定。次の回も同じでよいかは未確認）。
- 次のネタの候補：`scripts/pilot_016/production_request.md` の前の会話のリスト（伊能忠敬、ジョン・スノウ、ハリソンなど）。
