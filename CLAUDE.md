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
- **全動画の最後に共通エンディング**（W の声で「リバース。世界の仕組みを、はじめから。」）を付ける。pilot_015 までは専用の明るい画面、**pilot_016 以降は短い版**（明るい画面をやめ、最後の画の上にロゴと決めゼリフを重ねる。2026-10-29 にユーザーが承認。docs/ENDING_SPEC.md の「短い版」）。仕様は `anatomy_room/docs/ENDING_SPEC.md`、映像は `anatomy_room/production/common/ending.js`、声の設定は `production/common/voices.json` の `ending`。
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
- **ガイドライン v2.1（標準ルール v5、2026-10-28〜の新作に適用。既存の動画は直さない）**：`anatomy_room/templates/REVERSE_GUIDELINE_v2.1.md`。冒頭の掴み、**ナレーションの声を題材に合わせて選ぶ**（VOICEROID はこの PC にない → VOICEVOX の話者から。候補と規約は同ファイル、聞き比べ https://claude.ai/artifact/NjWmuyB7XADJHTxwpai1n1 、回ごとの指定は `lines.json` の `voice_override`）、場面ごとの BGM、効果音（`lock`・`scanline`・`reveal` を追加）、**主人公の具体的な困難と行動のエピソード**（台本の前に fact_check.md に「物語の核」）、**手のアップは原則使わない**、注目マーク（`Stage.hudTarget`・`hudBox`・`hudPointer`・`hudScan`）。完成チェックは `VIDEO_QA_CHECKLIST.md` の G1〜G11。
- **最新版の設定：ガイドライン v2.4（標準ルール v8、2026-10-29〜の新作）**：natomy_room/templates/REVERSE_GUIDELINE_v2.4.md（いまの設定の一覧つき）。CG のリアルさ（CC0 の HDRI・PBR の質感・3D モデル、SSAO などの仕上げ、MakeHuman のリアルな体型〔顔なし〕、必要なら Blender。PC へのソフトの導入はユーザーが承認）と、演出をもっと大げさに（速い寄り・スロー・光の転換・大きさの対比・音との同期。事実は誇張しない）。**新しい動画は、まずこのファイルを読む。**
- **ガイドライン v2.3（標準ルール v7、2026-10-29〜）**：`anatomy_room/templates/REVERSE_GUIDELINE_v2.3.md`。BGM は試聴でユーザーが選んだ 5 つの曲調（`lab_melodic`・`lab_electro`・`lab_break`・`lab_2step`・`lab_dub`、短調の和音）から動画ごとに選ぶ（`warm_drive` は使わない）。CG は時間をかけて質を上げる（2D の図も 3D のホログラムの台に置く、決定的な瞬間の迫力、主人公の思いが伝わる場面を 1〜2 か所）。
- **2 つの設計（2026-10-30）**：「知的設計」（pilot_017）と「ドパ設計」（pilot_018）。指示で名前を言われたらその設定で作る（`anatomy_room/templates/DESIGN_MODES.md`）。指定がなければ聞く。
- **引き継ぎ（会話が切れたとき）**：`anatomy_room/HANDOFF.md` に、いまの作業と次にやることを書いてある。新しい会話は、まずこれを読む。
- **ガイドライン v2.2（標準ルール v6、2026-10-29〜の新作に適用）**：`anatomy_room/templates/REVERSE_GUIDELINE_v2.2.md`。本編 60〜90 秒（全体 95 秒以内）、冒頭の最初の 1 秒に決定的な映像（答えは言わない）、最後の一文と画を冒頭につなげる、本物の写真を 1〜2 枚（パブリックドメイン・CC0・CC BY だけ。`scripts/pilot_NNN/assets.md` に権利を記録）、共通エンディングを短く（方法はユーザーの承認待ち）。pilot_015 の修正事項（warm_drive・冒頭の強化・注目のアイコン・効果音の増加・話速）も既定値。
- **標準ルール v4（2026-10-28）映像品質**：新しい回は `production/common/cine.js`（周りの光の映り込み・素材の凹凸とつや・水とガラスの透過・光の筋と埃・超解像度 1.5 倍・動きのぶれ・光のにじみ）を使い、各動画に決定的な映像を 1 つ設計する。GPU の調査結果と使い方は `docs/CINE_QUALITY.md`、見本は `production/pilot_012/renderer_cine.html`（pilot_012 の完成版 mp4 は従来の renderer.html のまま）。比較は `render_frames.js --renderer … --stills／--clip`。
- **自分の PC（GPU）で書き出す手順**は `anatomy_room/docs/PC_SETUP.md`。準備の確認は `node anatomy_room/tools/check_pc.js`。`render_frames.js` は GPU で WebGL が動けば GPU、動かなければソフトウェア描画（`REVERSE_GPU=off` で常にソフトウェア）。
- 尺は実際の音声合成で測る（`tools/measure_tts.py`）。VOICEVOX ENGINE を 127.0.0.1:50021 で起動して使う。
- YouTube へのアップロード・公開は、ユーザーの明示の指示があるまで行わない。

## 書き出しの時短と、トークンの節約（rv、2026-10-28〜。ユーザーの指示「制作パイプラインの時間とトークン消費の最適化」）

**この節を読めば、毎回プロジェクトを探さなくてよい。** 書き出しは原則 `rv` で行う（従来の `production_script.py all` もそのまま使える）。

- **構成**：テンプレート＝`anatomy_room/templates/*.md`（制作ルール）と `production/common/`（`pipeline.py`・`render_frames.js`・`stage.js`・`cine.js`・`music.py`・`standard.py`・`ending.js`・`voices.json`）。各話の入力＝`production/pilot_NNN/` の `lines.json`（セリフ・字幕）、`production_script.py`（きっかけ・効果音・BGM・場面の区切り）、`renderer.html`（映像）。`rv` は外付けの `anatomy_room/tools/rv.py` で、テンプレートを書き換えない。
- **コマンド**（PC の PowerShell、リポジトリの直下で。番号は `production_script.py` の `scenes` と同じ。0 番は最初のセリフの前の数コマ）：
  - `python anatomy_room/tools/rv.py 014 scenes`：場面の番号・名前・時間・セリフ ID・mp4 の有無
  - `python anatomy_room/tools/rv.py 014 render all`：完成版まで（mux・docs・qc・video_qa も）。変わった場面だけを書き出す。`--full` で全場面を作り直す（完成前の最後や、心配な変更のとき）
  - `python anatomy_room/tools/rv.py 014 render scene 3`：場面 3 だけを最終の画質で書き出し、音つきで `work/rv/scene_03.mp4` に（完成版は `render all` でつなぐ。書いた場面は使い回される）
  - `python anatomy_room/tools/rv.py 014 preview scene 3`：場面 3 だけを 10 fps・540×960 で軽く（`work/rv/preview_scene_03.mp4`。確認用。完成版には使わない）
- **画面に出るのは進捗の 1 行と結果だけ**（「シーン3/9 完了（所要 X秒）／残り約Y分」）。各工程のログは `work/rv/log/`。失敗したら末尾 5 行だけが出る。**ログの全文は、原因がそれで分からないときだけ読む。**
- **キャッシュ**：
  - audio は、セリフの時刻と音声・BGM の区間・効果音の時刻・`music.py`・`pipeline.py` が同じなら作り直さない（BGM の合成結果は `work/rv/bgm/`）。
  - textcheck は、描画のファイルとタイムラインが同じなら飛ばす。必要なときは audio と同時に動かす。
  - 映像は、描画のファイル（renderer.html・共通の JS）が変わったら、各場面の見本のコマ（0.5 秒ごと＋最初と最後）を新しいコードで描いて前回と比べ、差がすべて 2 階調以下の場面は前回の mp4 を使う。前に作った版に戻したときも、その版の mp4 を使う。記録は `work/rv/state.json`、見本は `work/rv/samples/`（1 話 約 400 MB）。
- **実測（pilot_014、111.6 秒・3349 コマ）**：全場面の書き出し 約 27 分＋audio 約 7 分＋textcheck 約 6.6 分 → 変更なしの作り直し 0.8 分、映像を 1 場面だけ直した作り直し 11.3 分（textcheck の作り直しは除く。含めると約 16 分）、`--full` 29.3 分。使い回した場面は基準の動画と framemd5 で全コマ一致。`--full` と比べた差は全場面で PSNR 45.8 dB 以上・SSIM 0.991 以上（書き出すたびの揺れの範囲）。場面の最初のコマは動きのぶれで直前の場面を少し描くので、ある場面を直すと次の場面も作り直しになることがある。
- **知っておくこと**：
  - 共通部品の描画は前のコマの状態を少し引き継ぐ。そのため、同じコードでも書き出すたびに画素がわずかに変わる（PSNR 45〜58 dB、SSIM 0.99 以上）。作り直した場面の一致は SSIM と PSNR で確かめる。
  - セリフの長さが変わると、それより後ろの場面は時刻がずれるので作り直しになる。
  - `pipeline.py` の場面のハッシュには `cine.js`・`vendor/earth` が入っていない（`rv` は含めて判定する）。
- **「シーン N を直して」と言われたときの手順**：
  1. `rv.py NNN scenes` で場面の範囲とセリフ ID を確かめる。
  2. 直すのは、セリフなら `lines.json` の該当行の `speech`・`sub` だけ、映像なら renderer.html の `name === "<場面名>"` の部分だけ。Grep で探し、ファイル全体は読まない。
  3. 直したら `rv.py NNN preview scene N` で確かめる。頼まれたとき、または問題が疑われるときだけ、静止画やプレビューを見る。
  4. 最後に `rv.py NNN render all` を 1 回だけ実行する。
- **禁止事項（ユーザーの絶対条件）**：
  - 最終出力の設定を変えない：1080×1920・30 fps・x264 medium・CRF 18・yuv420p、AAC 192k・48 kHz・−14 LUFS。GPU エンコード、preset の変更、画質を下げた合成は、完成版には使わない。
  - テンプレートのファイル・構成・演出・実行方法を変えない。変えないとできない改善は、変更箇所・理由・影響を示してユーザーの承認を得てから行う。
  - 速くするための変更は、基準の動画と比べて品質が変わらないことを確かめる。
- **進捗の報告**：大きな作業（調査・実装・全編の書き出し・検証）のたびに「✅ 〇〇完了（所要 約X分）／残り：△△ ／ 残り時間の見積もり：約Y分」と 1 行で報告する。見積もりは実測で更新する。
- **作業前のバックアップ**は `anatomy_room/_backup/`、基準の動画は `production/pilot_NNN/baseline/`（どちらも git に入れない）。

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
- **pilot_014「目の見えない少年が、世界の読み方を変えた——ルイ・ブライユ」**（`production/pilot_014/`、111.6 秒、ガイドライン v2.1 を最初から使った回）：声は `voice_override` で青山龍星 しっとり。決定的な映像は 12 点 → 6 点 → 63 通りの図解。`production_script.py` の `cues` には `segments` の場面名をすべて書く（`invent`・`spread` が抜けて場面が切り替わらなかった）。最後のセリフのあとの余韻は `final_hold`（`pipeline.py`、書かない回は 0）。サムネイルは `thumbnail.png`、タイトル・説明文は `youtube_metadata.md`、自己レビューは `reviews/internal_review/pilot_014_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_016「大陸は動いている——アルフレート・ヴェーゲナー」**（production/pilot_016/、79.3 秒）：標準ルール v6 を最初に使った回。本物の写真・図（ssets/、権利は scripts/pilot_016/assets.md）、短い共通エンディング（ext/ending_ext.py・HUD.endingOverlay）、話速 1.15・行間 0.05 秒（ユーザーの指示）。自己レビューは eviews/internal_review/pilot_016_review.md。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_017「宇宙の物差し——ヘンリエッタ・スワン・リービット」**（`production/pilot_017/`、90.0 秒）：ガイドライン v2.4 を最初に使った回。人体は Blender 5.2＋MPFB（`assets/make_human.py`、CC0）、Poly Haven の HDRI・PBR、SSAO・ボケ（`production/ext/vendor/three147/`）。3D が重いので `"workers": 1`（2 本同時だとブラウザが落ちた）。自己レビューは `reviews/internal_review/pilot_017_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_018「パスツールと少年——狂犬病のワクチン」**（`production/pilot_018/`、80.4 秒）：v2.4＋この回だけの試し「派手な演出と文字」（叩きつける文字 `slam()`・跳ねる字幕 `popSub()`・画面の一打、フォント Dela Gothic One／Mochiy Pop One〔OFL〕は `assets/make_assets.py` で使う文字だけに絞って埋め込む。画面の文字を変えたら再実行）。ユーザーの反応を見て標準にするか決める。自己レビューは `reviews/internal_review/pilot_018_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_019「海の上の時計——ジョン・ハリソン」**（`production/pilot_019/`、82.6 秒）：ドパ設計の 2 本目。閃光なし（ユーザー「まぶしい」）、叫ぶ声は L01・L10 だけ（`lines.json` の `voice_override` に style `shout`＝青山龍星「熱血」id 81）。人体の GLB と Poly Haven の素材は pilot_018 のものを複製、嵐の海・帆船・H1〜H4 は自前の 3D。声が 3 人なのでエンディングのクレジットは renderer.html で 2 行に。自己レビューは `reviews/internal_review/pilot_019_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_020「あと18キロ——スコットの南極点」**（`production/pilot_020/`、66.0 秒）：悲劇用の 1 本目（`templates/DESIGN_MODES.md`）。話速 1.5（約 10 モーラ/秒、ユーザーの指示「聞き取れる限界近く」）、L08・L13 だけ青山龍星「熱血」。BGM は外の曲（Kevin MacLeod「Blown Away」CC BY 4.0）を `production/ext/bgm_file.py` で（場面のモード f_full・f_mid・f_low・f_mute で音量を変える）。人体は `assets/make_human.py`（そりを引く姿勢、毛皮のフード）。自己レビューは `reviews/internal_review/pilot_020_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_015「太陽は何でできているか——セシリア・ペイン」**（`production/pilot_015/`、118.5 秒）：ユーザーの修正事項（2026-10-29）を最初に入れた回。安心して聴ける BGM `warm_drive`・追加の効果音・注目のアイコン・冒頭の見出しは、テンプレートの外の **`production/ext/`**（`music_ext.py`：`import music_ext` でその回だけ登録、`hud_ext.js`：`HUD.*`）。声は玄野武宏を話速 1.12（7.7 モーラ/秒）。事実確認は ChatGPT に依頼文（`scripts/pilot_015/gpt_fact_check_prompt.md`）で調べてもらい、Claude が出典で確かめ直す流れ。ChatGPT のシナリオのレビューはやめ、Claude の自己レビューのあと、ユーザーの「OK」で制作を始める。自己レビューは `reviews/internal_review/pilot_015_review.md`。YouTube へのアップロードはユーザーの指示まで行わない。
- **pilot_012「手を洗うだけで、救える命があった」**（ゼンメルワイス、`production/pilot_012/`、99.9 秒、標準ルール v3 の最初の回）：PC で書き出し。事実確認は `scripts/pilot_012/fact_check.md`（WebFetch で本文から抜き出し。数字は著書の表の転載ページ）。YouTube へのアップロードはユーザーの指示まで行わない。
