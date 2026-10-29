# 引き継ぎ（2026-10-29 更新）

新しい会話は CLAUDE.md の次にこれを読む。

## いまの状態

- pilot_016（ヴェーゲナー）は完成（BGM lab_melodic・CG の質の向上を入れた版、コミット 43238e2）。YouTube へのアップロードはユーザーの指示まで行わない。
- **最新版の設定は `templates/REVERSE_GUIDELINE_v2.4.md`**（いまの設定の一覧つき）。
- **pilot_017（ヘンリエッタ・リービット）は完成**（90.0 秒、video_qa OK、BGM lab_dub）。
- **pilot_018（パスツールと少年）は完成**（80.4 秒、video_qa OK、BGM lab_break）。
- **2 つの設計（2026-10-30、ユーザーが命名）**：「知的設計」（pilot_017 の落ち着いた作り）と「ドパ設計」（pilot_018 の派手な作り）。どちらも採用。一覧は `templates/DESIGN_MODES.md`。新しい動画でどちらか指定がなければ聞く。
- 叫ぶナレーションの聞き比べ（`production/voice_tests/shout/` の 0〜5）は 2 番に決定（2026-10-30）。v2.4 を最初に使った回：Blender 5.2＋MPFB で人体（`production/pilot_017/assets/make_human.py`）、Poly Haven の HDRI・質感、SSAO・ボケ（`production/ext/vendor/three147/`）。素材をまとめ直すときは `assets/make_scene_assets.py`。事実確認 `scripts/pilot_017/fact_check.md`、権利 `assets.md`。

- **pilot_019（ジョン・ハリソン、経度の時計）を開始（2026-10-30）**：ドパ設計（ユーザーの指示）。ChatGPT への事実確認の依頼文 `scripts/pilot_019/gpt_fact_check_prompt.md` → 結果を出典で確かめ直して `fact_check.md`・`assets.md`、台本の下書き `script_draft.md`（本編 約 80 秒、実測）→ **ユーザーの「OK」待ち**。BGM は直前が lab_break なので lab_electro を優先。ユーザーの指示（2026-10-30）：叫ぶ声は要所だけ、青山龍星「熱血」を強く（聞き比べの 2 番、「一旦」なので仕上がりを見て再確認）／**閃光は入れない**（まぶしい）。`DESIGN_MODES.md` に反映済み。

## 次の動画でやること（ガイドライン v2.4）

1. 題材を決める（候補：伊能忠敬、ジョン・スノウ、ジョン・ハリソン、リービット、八木秀次など。前の会話のリスト）。
2. ChatGPT への事実確認の依頼文 → 結果を出典で確かめ直す → 台本 → ユーザーの「OK」。
3. CG のリアルさ（v2.4 の 1）：CC0 の HDRI・PBR の質感・3D モデル（Poly Haven・ambientCG）、SSAO などの仕上げ、MakeHuman でリアルな体型（顔なし）。PC に MakeHuman・Blender を入れてよい（ユーザーが承認済み）。素材は `assets.md` に記録。
4. 演出を大げさに（v2.4 の 2）：速い寄り・スロー・光の転換・大きさの対比・音との同期。
5. BGM は 5 つの曲調から題材で選ぶ（直前の 2 本と違うものを優先。pilot_016 は lab_melodic）。
