# CLAUDE.md — リバース（旧・世界の解剖室）（YouTube Shorts Studio）

このリポジトリには 2 つのプロジェクトがあります。

| 場所 | 内容 | 状態 |
|------|------|------|
| `anatomy_room/` | **YouTube Shorts チャンネル「リバース」**（旧名「世界の解剖室」）の制作方針・シナリオ・レビュー資料・制作物 | **現行プロジェクト** |
| リポジトリ直下（`scripts/`, `script.md`, `final_short.mp4` など） | 以前の別企画「なぜ黒板は緑色なのか？」の制作物と動画パイプライン | 完了済み・参考用（変更しない） |

新しい作業は、特に指示がない限り `anatomy_room/` で行ってください。

## 最初に読むもの

0. **`anatomy_room/templates/REVERSE_STANDARD_RULES.md` — リバース標準制作ルール（2026-10-27〜、最優先の既定値）。参考作品は pilot_010。新しい動画の指示が来たら、指示にない項目はすべてこのルールで決める（下の各 docs と食い違うときはこちらが優先、その回のユーザーの個別指示はさらに優先）**

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
- 標準の構成は `REVERSE_STANDARD_RULES.md` の 5 段（フック → 対象 → 背景・仕組み → 核心 → 余韻）で、ナレーション主体。**オモテとウラの会話形式の回**（ユーザーが指定したとき、または題材に合うとき）は：疑問 → オモテが巻き込まれる → とんでもない事態 → ウラが毒舌を交えて解説 → オモテが理解する／さらにひどい目に遭う（`CHANNEL_POLICY.md`）。ギャグ・非現実の演出・再現 CG は画面に明記し、事実と区別する。
- **全動画の最後に共通エンディング**（W の声で「リバース。世界の仕組みを、はじめから。」＋専用の明るい画面）を付ける。仕様は `anatomy_room/docs/ENDING_SPEC.md`、映像は `anatomy_room/production/common/ending.js`、声の設定は `production/common/voices.json` の `ending`。
- 画面は暗めでテクノロジー感のある色調を標準とする（`REVERSE_STANDARD_RULES.md`）。暗さが目的ではなく、被写体と文字がはっきり見えること。第 7 弾までの明るい画面（`CHANNEL_POLICY.md` の「映像」）は旧標準。
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
- **pilot_010「世界の果てに、空を飛べない小さな鳥がいる」（イナクセシブルクイナ）はユーザーの指示で動画化**：科学ドキュメンタリー形式（男性ナレーション `v6`＝VOICEVOX:玄野武宏、暗い 3DCG）。オモテは**顔のない、もちもちした人型ピクトグラム**（`stage.js` の `mochi3D`、`CHARACTER_GUIDE.md` v3.2）に統一。`production/pilot_010/`。
- **標準ルール v2（2026-10-27）**：新作の制作設定は `production/common/standard.py`（`standard.config({...})`：左上のロゴなし・BGM `tech_drive`（ビートのあるテクノ 124 BPM）・やわらかい効果音・冒頭 0.1 秒で話し始める）、声は `voices.json` の `v7`（文末の「いる・いた・ある」を前の句につなげて語尾上がりを防ぐ）。冒頭 3 秒は `video_qa.py` が `qa/hook_3s.mp4` に切り出す。注記は必要最小限。詳細は `REVERSE_STANDARD_RULES.md` v2。
- **標準ルール v3（2026-10-28）**：字幕と重要な画面内テキストは従来の約 1.2 倍（`stage.js` の `docSub`・`TEXT_SCALE`、字幕 62px・1 行 15 字まで）。BGM は単一のループで押し切らず感情に合わせて変える（`music.py` の `doc_tense`・`doc_hope`〔長調の和音が差し込む〕・`doc_alone`・`doc_warm`・`doc_warm_end`）。色調も感情に合わせて変える（`stage.js` の `moodGrade`）。既存の回の BGM・効果音・描画は変わらない（数値で確認済み）。新作の土台は `production/pilot_012/`。
- **標準ルール v4（2026-10-28）映像品質**：新しい回は `production/common/cine.js`（周りの光の映り込み・素材の凹凸とつや・水とガラスの透過・光の筋と埃・超解像度 1.5 倍・動きのぶれ・光のにじみ）を使い、各動画に決定的な映像を 1 つ設計する。GPU の調査結果と使い方は `docs/CINE_QUALITY.md`、見本は `production/pilot_012/renderer_cine.html`（pilot_012 の完成版 mp4 は従来の renderer.html のまま）。比較は `render_frames.js --renderer … --stills／--clip`。
- **自分の PC（GPU）で書き出す手順**は `anatomy_room/docs/PC_SETUP.md`。準備の確認は `node anatomy_room/tools/check_pc.js`。`render_frames.js` は GPU で WebGL が動けば GPU、動かなければソフトウェア描画（`REVERSE_GPU=off` で常にソフトウェア）。
- 尺は実際の音声合成で測る（`tools/measure_tts.py`）。VOICEVOX ENGINE を 127.0.0.1:50021 で起動して使う。
- YouTube へのアップロード・公開は、ユーザーの明示の指示があるまで行わない。

## 制作の分担と PC（Windows）での作業（2026-10-27〜）

- **書き出しはユーザーの PC**（Windows、NVIDIA RTX 3070、`render_frames.js` が GPU を自動で使う。pilot_010 の静止画で 1 コマ 0.67 秒、クラウドは約 3 秒）。PC のセッションは `claude remote-control`（`~\formovies`、same-dir）で、ユーザーはスマホから指示する。PC がスリープ・シャットダウン中は動かない。
- **クラウドのセッション**は、PC がなくても進められる工程（題材・事実確認・台本・レビュー資料）を担当する。書き出しを両方で同時にしない。push がぶつからないよう、作業の前に `git pull`。
- **決まった手順（指示に書いていなくても、毎回必ず行う）**：ユーザーの指示は ChatGPT からのコピーのことがあり、git の操作が書かれていないことが多い。
  1. 作業を始める前に `git pull`（クラウドのセッションが進めた分を取り込む）。
  2. 書き出しのあとは `python tools/video_qa.py pilot_NNN --sheets` をかけ、結果（NG の項目）をユーザーに伝える。
  3. 作業が終わったら `git add -A` → `git commit` → `git pull --no-edit` → `git push`。push できたことを確かめてから終わりにする。
  4. 書き出しの前に VOICEVOX（127.0.0.1:50021）が応答するか確かめる。応答しなければ、ユーザーに VOICEVOX のアプリを開くよう頼む。
- PC の環境（`docs/PC_SETUP.md`、確認は `node tools/check_pc.js`）：
  - コマンドは `python`（`python3` ではない）。PowerShell では `npm.cmd`・`npx.cmd`。Node の部品は `anatomy_room/node_modules`（Playwright 1.63.0）。
  - VOICEVOX は**アプリ版 0.26.0**（クラウドは ENGINE 0.24.1）。声が少し変わることがあるので、PC で声を作ったら `qc_report.md` の「文末の音程」「読み上げの照合」を見直す。
  - fontconfig がないので、`textcheck` の「フォントにない文字」は PC では未確認になる（必要ならクラウドで確認）。ImageMagick もない（一覧画像は Pillow）。外部コマンドの出力・JSON は UTF-8 で読む（cp932 で止まった）。
- **pilot_011「紙袋を変えた女性、マーガレット・ナイト」**（`production/pilot_011/`、99.5 秒）：**完成**（ユーザーの判断で f0bc12a の版。L14 の語尾と最初のコマの直しは入っていない。サムネイルは `thumbnail.png`、タイトル・説明文は `youtube_metadata.md`）。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_013「宇宙飛行士の命を、数字で支えた女性——キャサリン・ジョンソン」**（`production/pilot_013/`、95.7 秒、標準ルール v4 で cine.js を最初から使った回）：決定的な映像は地球を回るカプセル（NASA Visible Earth の画像＋自前の地球シェーダー。画像は file:// だと WebGL に渡せないので `common/vendor/earth/earth_tex.js` の data URI）。書き出しは同時 2 本（`"workers": 2`。3 本では起動直後にブラウザが閉じた）。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_012「手を洗うだけで、救える命があった」**（ゼンメルワイス、`production/pilot_012/`、99.9 秒、標準ルール v3 の最初の回）：PC で書き出し。事実確認は `scripts/pilot_012/fact_check.md`（WebFetch で本文から抜き出し。数字は著書の表の転載ページ）。YouTube へのアップロードはユーザーの指示まで行わない。
