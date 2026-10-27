# CLAUDE.md — リバース（旧・世界の解剖室）（YouTube Shorts Studio）

このリポジトリには 2 つのプロジェクトがあります。

| 場所 | 内容 | 状態 |
|------|------|------|
| `anatomy_room/` | **YouTube Shorts チャンネル「リバース」**（旧名「世界の解剖室」）の制作方針・シナリオ・レビュー資料・制作物 | **現行プロジェクト** |
| リポジトリ直下（`scripts/`, `script.md`, `final_short.mp4` など） | 以前の別企画「なぜ黒板は緑色なのか？」の制作物と動画パイプライン | 完了済み・参考用（変更しない） |

新しい作業は、特に指示がない限り `anatomy_room/` で行ってください。

## 最初に読むもの

1. `anatomy_room/docs/CHANNEL_POLICY.md` — チャンネルの目的・テーマ・動画仕様
2. `anatomy_room/docs/CHARACTER_GUIDE.md` — M と W（女性役）の人物設定と掛け合いのルール
3. `anatomy_room/docs/SCRIPT_RULES.md` — 台本の構成・書式・字幕のルール
4. `anatomy_room/docs/FACT_CHECK_POLICY.md` — 事実確認・出典管理・判定ラベル
5. `anatomy_room/docs/PRODUCTION_WORKFLOW.md` — 工程と、各工程の開始条件
6. `anatomy_room/docs/RESEARCH_ENVIRONMENT.md` — 調査環境の制約（ネットワーク制限）
7. `anatomy_room/docs/ENDING_SPEC.md` — 全動画共通のエンディング
8. **`anatomy_room/templates/MASTER_VIDEO_TEMPLATE.md` — ショート動画の標準仕様（固定ルール／可変ルール）。新作は `templates/VIDEO_PRODUCTION_PROMPT.md` から始め、完成前に `templates/VIDEO_QA_CHECKLIST.md` と `python3 anatomy_room/tools/video_qa.py pilot_00N --sheets` で検査する**

## 絶対に守ること

- **動画制作の開始条件**：ユーザーが ChatGPT レビューを終え、採用するシナリオを明示的に指定するまで、
  CG 生成・音声合成・動画書き出し・YouTube へのアップロード／公開を行わない。
- **外部サービスへの課金をしない。認証情報を要求・保存しない。**
- **事実の正確性は面白さと同じくらい重要。** 確認していない URL や資料を「確認済み」と書かない。
  検索結果の要約・抜粋で確認したものは、その旨を必ず「確認方法」に書く。
- 事実・説明・冗談・比喩演出・不確実な情報を分けて記録する（`FACT_CHECK_POLICY.md`）。
- キャラクター設定（`CHARACTER_GUIDE.md` v3：**オモテ（M）＝破天荒な実験台**、好奇心と自信でブレーキが壊れているが頭は切れる／**ウラ（W）＝毒舌の解説者**、オモテを面白がり、短く鋭い一言で返す。人格否定はしない）を全動画で一貫させる。
- 第 3 話以降の基本構成：疑問 → オモテが巻き込まれる → とんでもない事態 → ウラが毒舌を交えて解説 → オモテが理解する／さらにひどい目に遭う（`CHANNEL_POLICY.md`）。ギャグ・非現実の演出は画面に明記し、事実と区別する。
- **全動画の最後に共通エンディング**（W の声で「リバース。世界の仕組みを、はじめから。」＋専用の明るい画面）を付ける。仕様は `anatomy_room/docs/ENDING_SPEC.md`、映像は `anatomy_room/production/common/ending.js`、声の設定は `production/common/voices.json` の `ending`。
- 画面は明るく、色のコントラストと動きのあるものにする（`CHANNEL_POLICY.md` の「映像」）。
- 台本を直したら `python3 anatomy_room/tools/check_scripts.py`、
  `python3 anatomy_room/tools/build_chatgpt_review.py`、`python3 anatomy_room/tools/build_copy_page.py` を順に実行し、
  レビュー資料とスマホ用コピーページを作り直す。コピーページは Artifact（https://claude.ai/artifact/MrxPiW8hLtaEUJDx5sDkSZ）としても公開しているので、同じファイルを再公開して更新する。
- チャンネルのアイコン・ヘッダーは `anatomy_room/branding/`（`node anatomy_room/branding/render.js` で再生成）。

## 現在の状態（2026-10-26 時点）

- パイロット 5 本：第 2 回監査（`anatomy_room/audit/`）を経て v2 に改訂済み。修正前は各 `scripts/pilot_00N/versions/`。
- **第 1 話 pilot_005 はユーザーの指示で動画化済み**：`anatomy_room/production/pilot_005/world_anatomy_pilot_005.mp4`。
  制作方法は同フォルダの `production_notes.md`。音声は VOICEVOX ENGINE（ローカル、無料）。共通エンディングを後から追加済み（追加前は `versions/v2_before_ending/`）。
- **第 2 話 pilot_003 はユーザーの指示で動画化済み**（演出刷新：新しい声・キャラクター・明るい 3D 画面）：
  `anatomy_room/production/pilot_003/world_anatomy_pilot_003.mp4`。制作方法は同フォルダの `production_notes.md`、第 1 話からの改善点は `IMPROVEMENTS_FROM_EP1.md`。
- 声の設定は話ごとに `production/common/voices.json`（`v1`＝第 1 話、`v2`＝第 2 話、`v3`＝第 3 話以降：オモテ＝青山龍星、ウラ＝冥鳴ひまり）。
- **第 3〜5 話（新構成）pilot_006〜008 はユーザーの指示で動画化済み**：飛行機の窓（`production/pilot_006/`）、QR コード（`pilot_007/`）、298 円（`pilot_008/`）。
  共通の制作パイプラインは `production/common/pipeline.py`（各話の `production_script.py` は設定だけ）、描画部品は `common/stage.js`、BGM・効果音は `common/music.py`。
  台本 `scripts/pilot_00N/script.md` は `python3 anatomy_room/tools/build_script_md.py pilot_00N` で制作データから作る。
- **第 7 弾（仮） pilot_009「結局、今回のPHP騒動は何だったの？」はユーザーの指示で動画化済み**（2026年10月のPHPの脆弱性とサービス停止。約 115 秒（v2：冒頭の問い・やわらかい効果音 sfx_bank_soft）、声は `v5`＝v4 の約 0.9 倍の速さ）：
  `production/pilot_009/reverse_009_php.mp4`。事実確認は `scripts/pilot_009/fact_check.md`（すべて検索抜粋。公式の本文は未確認）、自己レビューは `reviews/internal_review/pilot_009_review.md`。
- 尺は実際の音声合成で測る（`tools/measure_tts.py`）。VOICEVOX ENGINE を 127.0.0.1:50021 で起動して使う。
- YouTube へのアップロード・公開は、ユーザーの明示の指示があるまで行わない。
