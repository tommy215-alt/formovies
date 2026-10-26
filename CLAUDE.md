# CLAUDE.md — 世界の解剖室（YouTube Shorts Studio）

このリポジトリには 2 つのプロジェクトがあります。

| 場所 | 内容 | 状態 |
|------|------|------|
| `anatomy_room/` | **YouTube Shorts チャンネル「世界の解剖室」** の制作方針・シナリオ・レビュー資料 | **現行プロジェクト** |
| リポジトリ直下（`scripts/`, `script.md`, `final_short.mp4` など） | 以前の別企画「なぜ黒板は緑色なのか？」の制作物と動画パイプライン | 完了済み・参考用（変更しない） |

新しい作業は、特に指示がない限り `anatomy_room/` で行ってください。

## 最初に読むもの

1. `anatomy_room/docs/CHANNEL_POLICY.md` — チャンネルの目的・テーマ・動画仕様
2. `anatomy_room/docs/CHARACTER_GUIDE.md` — M と W（女性役）の人物設定と掛け合いのルール
3. `anatomy_room/docs/SCRIPT_RULES.md` — 台本の構成・書式・字幕のルール
4. `anatomy_room/docs/FACT_CHECK_POLICY.md` — 事実確認・出典管理・判定ラベル
5. `anatomy_room/docs/PRODUCTION_WORKFLOW.md` — 工程と、各工程の開始条件
6. `anatomy_room/docs/RESEARCH_ENVIRONMENT.md` — 調査環境の制約（ネットワーク制限）

## 絶対に守ること

- **動画制作の開始条件**：ユーザーが ChatGPT レビューを終え、採用するシナリオを明示的に指定するまで、
  CG 生成・音声合成・動画書き出し・YouTube へのアップロード／公開を行わない。
- **外部サービスへの課金をしない。認証情報を要求・保存しない。**
- **事実の正確性は面白さと同じくらい重要。** 確認していない URL や資料を「確認済み」と書かない。
  検索結果の要約・抜粋で確認したものは、その旨を必ず「確認方法」に書く。
- 事実・説明・冗談・比喩演出・不確実な情報を分けて記録する（`FACT_CHECK_POLICY.md`）。
- キャラクター設定（M はアホっぽいが本質を突くこともある／W は知的で毒舌だが人格否定はしない）を全動画で一貫させる。
- 台本を直したら `python3 anatomy_room/tools/check_scripts.py`、
  `python3 anatomy_room/tools/build_chatgpt_review.py`、`python3 anatomy_room/tools/build_copy_page.py` を順に実行し、
  レビュー資料とスマホ用コピーページを作り直す。コピーページは Artifact（https://claude.ai/artifact/MrxPiW8hLtaEUJDx5sDkSZ）としても公開しているので、同じファイルを再公開して更新する。
- チャンネルのアイコン・ヘッダーは `anatomy_room/branding/`（`node anatomy_room/branding/render.js` で再生成）。

## 現在の状態（2026-10-26 時点）

- パイロット 5 本のシナリオ、事実確認リスト、内部レビュー、ChatGPT レビュー資料を作成済み。
- 次の工程：ユーザーによる ChatGPT レビュー → 採用シナリオの指定（`PRODUCTION_WORKFLOW.md` の工程 6）。
