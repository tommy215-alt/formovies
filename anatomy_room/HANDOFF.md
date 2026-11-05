# 引き継ぎ（2026-10-29 更新）

新しい会話は CLAUDE.md の次にこれを読む。

## いまの状態

- pilot_016（ヴェーゲナー）は完成（BGM lab_melodic・CG の質の向上を入れた版、コミット 43238e2）。YouTube へのアップロードはユーザーの指示まで行わない。
- **最新版の設定は `templates/REVERSE_GUIDELINE_v2.4.md`**（いまの設定の一覧つき）。
- **pilot_017（ヘンリエッタ・リービット）は完成**（90.0 秒、video_qa OK、BGM lab_dub）。
- **pilot_018（パスツールと少年）は完成**（80.4 秒、video_qa OK、BGM lab_break）。
- **2 つの設計（2026-10-30、ユーザーが命名）**：「知的設計」（pilot_017 の落ち着いた作り）と「ドパ設計」（pilot_018 の派手な作り）。どちらも採用。一覧は `templates/DESIGN_MODES.md`。新しい動画でどちらか指定がなければ聞く。
- 叫ぶナレーションの聞き比べ（`production/voice_tests/shout/` の 0〜5）は 2 番に決定（2026-10-30）。v2.4 を最初に使った回：Blender 5.2＋MPFB で人体（`production/pilot_017/assets/make_human.py`）、Poly Haven の HDRI・質感、SSAO・ボケ（`production/ext/vendor/three147/`）。素材をまとめ直すときは `assets/make_scene_assets.py`。事実確認 `scripts/pilot_017/fact_check.md`、権利 `assets.md`。

- **pilot_019（ジョン・ハリソン、経度の時計）を開始（2026-10-30）**：ドパ設計（ユーザーの指示）。ChatGPT への事実確認の依頼文 `scripts/pilot_019/gpt_fact_check_prompt.md` → 結果を出典で確かめ直して `fact_check.md`・`assets.md`、台本の下書き `script_draft.md`（本編 約 80 秒、実測）→ ユーザーの「OK」（2026-10-30）→ 制作中：`production/pilot_019/`（renderer.html はドパ設計の部品を pilot_018 から流用、閃光なし。人体の GLB と Poly Haven の素材は pilot_018 のものを複製。嵐の海・帆船・岩・H1〜H4 は自前の 3D）。叫ぶ声は lines.json の voice_override の style "shout"（青山龍星「熱血」id 81、抑揚 1.5）。**完成**（82.6 秒、video_qa は「最初のコマが暗い」だけ → thumbnail.png を使う）。ユーザーの感想待ち（叫ぶ声は「一旦 2 番」）。BGM は直前が lab_break なので lab_electro を優先。ユーザーの指示（2026-10-30）：叫ぶ声は要所だけ、青山龍星「熱血」を強く（聞き比べの 2 番、「一旦」なので仕上がりを見て再確認）／**閃光は入れない**（まぶしい）。`DESIGN_MODES.md` に反映済み。

- **悲劇用（2026-10-30、3 つ目の設計）**：`templates/DESIGN_MODES.md`。ギャンブルは**テンションだけ**（器具・オッズの表示は出さない）。1 本目は **pilot_020 スコットの南極点**（ユーザーが選択）。ChatGPT への依頼文 `scripts/pilot_020/gpt_fact_check_prompt.md`（BGM の候補探しも含む）→ 結果を出典で確かめ直して `fact_check.md`・`assets.md`、台本の下書き `script_draft.md`（本編 約 72 秒）→ ユーザーの「OK」（話速を聞き取れる限界近くまで上げる、台本も書き直してよい）→ **完成**：`production/pilot_020/reverse_020_scott.mp4`（66.0 秒、話速 1.5＝約 10 モーラ/秒、BGM は Kevin MacLeod「Blown Away」CC BY 4.0、外の曲の部品 `production/ext/bgm_file.py`、人体は `assets/make_human.py`〔そりを引く姿勢〕）。声と曲はユーザーが選ばなかったので Claude が選んだ（玄野武宏＋要所だけ青山龍星「熱血」）→ ユーザー「おおよそ完璧」＋直し → **設計「悲劇」として保存**（`templates/DESIGN_MODES.md`）し、**v2 を完成**（65.0 秒）：後半 2/3 から声・色・BGM を少しずつ暗く、最後の日記から BGM 無音、短調の曲（Black Vortex）、冷たい色調、共通エンディングなし（`ext/noend_ext.py`）。感想待ち。ナレーションはハイテンション気味（話者は聞き比べで決める）。

- **pilot_020 は v3 で完成**（ユーザー「完璧」）。**設計「悲劇」を 3 回目の更新**（2026-10-30、`templates/DESIGN_MODES.md`）：ナレーターはずっと同じ人、最後の一言はゆっくりはっきり、BGM は短調でリズミカル、序盤はコテコテで派手な色、1/3 くらいから起承転結に合わせて少しずつシリアスに、最後は環境音と静かなナレーションと暗めの画面。
- **pilot_021 アンドレーの北極気球（1897）、設計「悲劇」**：ChatGPT への依頼文 `scripts/pilot_021/gpt_fact_check_prompt.md`（短調でリズミカルな BGM の候補探しも含む）→ 事実確認・台本 → ユーザーの「OK」＋BGM は Machinations ＋冒頭 3 秒のオープニング（結論の文字・別の声・本物の写真・ホラー調の音）→ **完成**：`production/pilot_021/reverse_021_andree.mp4`（71.0 秒）。オープニングは lines.json の L00（W の声）と bgm_file.py のモード h。renderer は pilot_020 の部品を組み立て直したもの（組み立てのスクリプトはスクラッチにあったので、直すときは renderer.html を直接直す）。感想待ち。オープニングを「悲劇」の設定に入れるかは未確認。

- **pilot_022 バリー・マーシャル（ピロリ菌を自分で飲んだ、1984）、ドパ設計**（ユーザーは「ドパガキ用」とも呼ぶ）＋**冒頭のオープニング（結論の文字・別の声・本物の写真、BGM はやさしい音）**＋**共通エンディング（リバース）あり**。ChatGPT への依頼文 `scripts/pilot_022/gpt_fact_check_prompt.md` → 事実確認・台本 → ユーザーが**知的設計**を選んで「OK」→ **完成**：`production/pilot_022/reverse_022_marshall.mp4`（83.3 秒、BGM lab_melodic、オープニングのやさしい音は `ext/opening_bgm.py` のモード open_soft）。知的設計の字幕（S.docSub）は 1 行 15 字まで、" / " で改行する（入れ忘れて書き直した）。
  - **2026-10-30 の直し（v2、83.3 秒）**：オープニングの写真をグレイ解剖学の胃の線画（パブリックドメイン、注記を外す）に（電子顕微鏡写真は「ややグロテスク」）、音を open_eerie（ゆっくりで少し不気味、気を引く）に、「ス／ストレス？」のアイコン付きの札を文字だけの札に、L08（自分の体で試す）を暗転の大きな文字 → 小瓶の極端な寄り → 後ろ姿 → 小瓶とカットで切り替える大きな演出に。`DESIGN_MODES.md` に「話が大きく変わるところ」を追加。renderer はスクラッチの組み立てスクリプトで作ったので、直すときは renderer.html を直接直す。
  - **2 回目の直し（v3、約 65 秒）**：話速をオモテ 1.5・W 1.3・行間 0.03 に（聞き取れる限界近く）、起承転結それぞれの頭（L02・L03・L08・L10）にカットイン（暗転の大きな文字 → 2 カット → 本来の画、`CI`・`ciPhase()`・`ciShot()`）、オープニングの写真をマーシャルが飲んだ培養液の瓶（ノーベル博物館、Gaius Cornelius、CC BY 4.0）に。**この編集設定を知的設計の既定にした**（`DESIGN_MODES.md` の「知的設計の編集設定」）。
  - **3 回目の直し（v4）**：カットインは起・承・結が暗転の文字 1 回だけ、転だけ 3 回に。オープニングの音を駆け上がるベルのチャイム（`open_chime`）に（open_eerie は「あるチャンネルの音に酷似」）。ユーザー「あとはバッチリ」→ 設計として保存済み。

- **pilot_023 インスリンの発見（バンティング、1922 年のレナード・トンプソン）、知的設計**（2026-10-31、ユーザーが選択。希望は「なるべく感動するようなやつ」、タイトル〔オープニング〕あり）。ChatGPT への依頼文 `scripts/pilot_023/gpt_fact_check_prompt.md` → ユーザーが結果を貼る → Claude が出典で確かめて `fact_check.md`・`assets.md`・`script_draft.md` → ユーザーの「OK」で制作。冒頭の一文（案）「死を待つだけの病に、薬が生まれた」。
  - 事実確認で ChatGPT の「血糖 約520 → 約120」は出典（J Clin Invest 2021）に無い → 使わず「1 日で正常まで」（トロント大学の展示）。写真はトロント大学の図書館が Flickr に CC BY 2.0 で公開したもの（犬と写った 2 人、テディの手紙）。ユーザーの「OK」（2026-10-31）→ 制作：`production/pilot_023/`（約 67 秒、BGM lab_dub、オープニングの音 open_impact）。renderer は pilot_022 の renderer.html の行を土台にスクラッチの組み立てスクリプトで作った（直すときは renderer.html を直接直す）。`production_script.py` の `cues` には `segments` の場面名（fail・turn・legacy）も書く（抜けて場面が切り替わらなかった）。
  - **書き出し完了（2026-11-01）**：`production/pilot_023/reverse_023_insulin.mp4`（67.4 秒）。video_qa は「最初のコマが暗い」だけ → `thumbnail.png` を使う。ユーザーの感想待ち。自己レビュー（`reviews/internal_review/pilot_023_review.md`）は未作成。
  - **直し（2026-11-01）**：斜めの光の筋（`Cine.shaft`、幕のように見えた）を削除。起承転結のカットインを文字なし・効果音なしのカメラの動き（傾き・急な寄り・引き、`camFX()`）に。どちらも知的設計の設定として `DESIGN_MODES.md` に保存。

- **1 日 2 本に向けた 3 本同時の制作（2026-11-01〜）**：pilot_024＝悲劇（ソフィー・ブランチャール、1819 年の花火の気球）、pilot_025＝ドパ設計（ジョン・ポール・スタップ、1954 年に 46G）、pilot_026＝知的設計（クレア・パターソン、地球の年齢とガソリンの鉛）。題材は「世間・SNS で知られていない、高学歴の人も引き込まれるもの」（ユーザーの指示）。ChatGPT への依頼文（3 本まとめて、BGM・画像の候補も）は `scripts/batch_024_026/gpt_fact_check_prompt.md` → ユーザーが結果を貼る → 確かめ直して 3 本の台本 → まとめて「OK」→ 3 本を続けて制作。**この 3 本で設計ごとの土台（部品化した renderer）を `production/ext/` に作る**（ユーザーが承認。4 本目から速くする）。BGM・画像はフリー素材だけ（`DESIGN_MODES.md`）。
  - **2026-11-01**：ChatGPT の結果を出典で確かめ直し、各回の `scripts/pilot_02N/fact_check.md`・`assets.md`・`script_draft.md`（VOICEVOX で実測、本編 52〜57 秒）を作成。画像は Commons の API で権利を確認（PD・CC0 だけ。パターソン本人の写真は権利不明で使わない）。BGM は incompetech の一覧で確認（024 Danse Macabre、025 Raving Energy (faster)、026 Clean Soul が第一候補）。ユーザーの「OK」（2026-11-01、ドパ設計のカットインは「文字なし、効果音たっぷり」）。
  - **3 本とも完成（2026-11-01）**：`production/pilot_024/reverse_024_blanchard.mp4`（63.0 秒、悲劇、Danse Macabre）、`pilot_025/reverse_025_stapp.mp4`（58.8 秒、ドパ、Raving Energy (faster)）、`pilot_026/reverse_026_patterson.mp4`（63.4 秒、知的、Clean Soul）。video_qa の残りは想定どおり（最初のコマが暗い → thumbnail.png、オープニング L00 の字幕なし、悲劇はエンディングなし）。タイトル・説明文は各回の `youtube_metadata.md`。ユーザーの感想待ち。YouTube へのアップロードはユーザーの指示まで行わない。
  - 書き出しで 3D が重い場面はブラウザが落ちることがある（1 回やり直すと通った）。
  - **設計「悲劇」を 5 回目の更新**（2026-11-01、ユーザーの指示、`DESIGN_MODES.md`）：明朝体・最初から暗く張り詰めた編集・悲しい BGM（終盤は無音）・知的設計と同じオープニング。**pilot_024 を作り直した**（BGM は Sad Trio、63.0 秒）。kit は `KIT.design = "tragedy"` で自動。
  - **制作の土台 `production/ext/kit/` を作成**（`DESIGN_MODES.md` の「制作の土台」）。3 本とも renderer.html は場面だけ。書き出しは `rv.py 02N render all`。

## 10 本同時の制作（2026-11-01〜）
- ユーザーの指示：知的 4・ドパ 4・悲劇 2 を、知的 → ドパ → 知的 → ドパ → 悲劇 の順で投稿。番号は投稿の順：027 賢馬ハンス（知的）・028 フォルスマン（ドパ）・029 モーズリー（知的）・030 ブラント（ドパ）・031 ダリー（悲劇）・032 フォン・フリッシュ（知的）・033 テッポウエビ（ドパ）・034 ベントレー（知的）・035 キッティンジャー（ドパ）・036 ブロック（悲劇）。
- **2026-11-01**：ChatGPT の結果（`scripts/batch_027_036/gpt_results.md`）を確かめ直し、各回の `fact_check.md`・`assets.md`・`script_draft.md`（本編 39〜51 秒）。BGM は incompetech の 10 曲（ユーザーが Content ID のリスクを了承）。画像は Commons で確認（028 の X 線写真・035 の降下の写真は使わない、036 は画像なし）。**ユーザーの「OK」待ち。**
- **10 本とも完成（2026-11-02）**：各回の `reverse_0NN_*.mp4`（45.9〜58.0 秒）、サムネイル・`youtube_metadata.md`。video_qa の残りは想定どおり（最初のコマ、悲劇はエンディングなし）。制作は新しい部品 `production/ext/kit/shots.js`（セリフごとのショットの一覧 SHOTS）と、台本から制作データを作る手順（10 本同時）。予約の一覧 `publish/queue.json` に投稿の順で載せた（公開の枠は自動で 8:00・19:00 に振る）。
- ChatGPT への依頼文（10 本を 1 回で返す形）：`scripts/batch_027_036/gpt_fact_check_prompt.md` → ユーザーが結果を貼る → 確かめ直して台本 10 本 → まとめて「OK」→ 制作（kit を使う）→ queue.json に順に載せる。

## YouTube の予約投稿（2026-11-01〜、ユーザーの承認）

- 予約の一覧 `anatomy_room/publish/queue.json`（ユーザーが選んだ回だけを載せる）。毎日 8:00・19:00（日本時間）、公開前の確認は不要、「AI の使用」（改変または合成されたコンテンツ）は「いいえ」。
- `node anatomy_room/tools/yt_upload.js next`：一覧の次の回を上げて予約まで入れる（YouTube Studio の画面を Chrome で操作。窓は画面の外。`--show` で表示）。途中で止まった下書きがあれば続きから入れる（同じ動画を 2 本上げない）。各段階の画面は `publish/log/`（git に入れない）。
- ログインはユーザーが一度だけ画面で行った（`yt_upload.js login`、プロフィールは `%LOCALAPPDATA%
everse_yt_profile`）。切れたら、もう一度ユーザーに頼む。認証情報は扱わない。
- **自動で動く（2026-11-01、ユーザーの承認）**：Windows のタスク スケジューラ「Reverse-YouTube-Upload」が、ログオン時と 3 時間ごとに `yt_upload.js next` を動かす（PC が切れていた分は起動時に実行）。queue.json の queued の回を順に全部上げ、時刻を過ぎた回や `publish_at` が空の回は次の空いた 8:00・19:00 に振り直す。記録は `publish/log/run.log`・`task.log`。登録・削除は `tools/yt_task.ps1`（`-Remove`）。**新しい回を予約するには、queue.json に `{"id", "video", "meta", "publish_at": null, "status": "queued"}` を **PC の作業フォルダで** 足すだけ**（タスクは git pull しないので、クラウドのセッションで足したときは PC で `git pull` してから）。
- 予約済み：pilot_024（2026-11-02 8:00）、pilot_026（2026-11-02 19:00）。pilot_023・025 などはユーザーが自分で上げ済み。

## 質の向上（2026-11-02〜、ユーザーの指示「CG とナレーションを無料でできる範囲で高クオリティに」）

- 026〜033 の予約は、ユーザーの指示で非公開に戻した（`yt_upload.js private`）。034〜036 は hold。もう一度予約するかはユーザーの指示待ち。シリーズは C 案（「あなたならどうする？」の選択型）で行く（企画はこれから）。
- **ナレーション**：AivisSpeech Engine（無料）を導入（`docs/PC_SETUP.md` の 2b）。聞き比べ（同じ一文を 14 の声で、https://claude.ai/artifact/UJaQ2vbYU6SoQFX7iNmUT1 ）でユーザーが選んだのは 1 玄野武宏・3 VOICEVOX No.7 アナウンス（女性）・8 AivisSpeech 阿井田 茂 Calm・9 阿井田 茂 ノーマル。つなぎは `production/ext/aivis_ext.py`（`voice_override` に `"engine"`、共通エンディングの決めゼリフは W を差し替えても冥鳴ひまり）。
  - **試し**：pilot_029 を本編 阿井田 茂 Calm（話速 1.5）・冒頭 L00 No.7 アナウンス（1.3）で作り直した（59.4 秒）。元の mp4 は `_backup/voice_trial_029/`。ユーザーの感想待ち。AivisSpeech は読み（カナ）を返さないので、qc_report の「読み上げの照合」は文のまま（耳で確かめる）。No.7 の L00 は文末 +3.6 半音の上がりの警告。
- **声の既定（2026-11-02、ユーザーの指示、全設計）**：本編＝阿井田 茂 Calm、冒頭（L00）と最後の決めゼリフ＝冥鳴ひまり、ドパの叫ぶ行＝青山龍星「熱血」（`DESIGN_MODES.md` の「ナレーションの声」、`ext/aivis_ext.py` の preset aida）。029 と 035 をこの声で作り直した。035 は予約の一覧に載せる（ユーザーの指示）。AivisSpeech のエンジンは書き出しの前に起動しておく（PC_SETUP の 2b）。
- **CG の方針（2026-11-02、ユーザーの承認）：3D の場面は Blender、図・文字・字幕はブラウザ**（`templates/DESIGN_MODES.md` の最後の節、土台 `production/ext/blender/`）。**pilot_035 を Blender 版で作り直した**（9 場面・725 コマ、`pilot_035/blender/scene.py`、見比べ https://claude.ai/artifact/4Vi3mZY543Qi5gkUaX5fFq ）。ユーザーの感想待ち。描き直したら `bl_pack.py` → `rv.py render all`（extra_files に `work/blender/index.js` を入れてあるので、描き直した場面だけ作り直す）。
- **CG（最初の試作）**：Blender 5.2（Cycles・GPU）で 035 の成層圏の場面の試作（高度 31 km の多重散乱の空・手続き的な地表と雲・ゴンドラ・MPFB の人）。スクリプトはスクラッチ（`%TEMP%\claude\bl\strato.py`）。1 コマ約 17 秒（RTX 3070、128 サンプル）。今の 035 の同じ場面（l03b）と比べてもらう。

## 新シリーズ「あなたならどうする？」（選択設計〔旧・当事者設計〕、2026-11-02〜）

- 設計は `templates/DESIGN_MODES.md` の「5 つ目：選択設計」。2 択、前半は一人称（二人称の語り・当事者の目線）、後半は三人称の解説。オープニングは状況と 2 択だけ＋その場の環境音を強く（ユーザーの指示）。手は映してよい。
- 1 本目〜3 本目：pilot_037 ケプケ（密林）・038 アポロ 12 号の落雷・039 プロスペリ（サハラ）。ChatGPT の結果 `scripts/batch_037_039/gpt_results.md` → Claude が本文で確かめ直し（BBC の本人の手記・Apollo Flight Journal・Guardian のインタビュー）→ 台本はユーザーが「OK」（2026-11-02）。
- 土台：環境音のファイルを区間で敷く `production/ext/ambience.py`、目線の演出 `production/ext/kit/pov.js`、3D は Blender（各回の `blender/scene.py`）。生成スクリプト（scratch の make37.py・make37r.py・meta37.py）で lines.json・production_script.py・renderer.html・youtube_metadata.md を作った（直すときは各ファイルを直接直す）。
- **状況（2026-11-02 21:45）**：037（68.5 秒）・038（77.1 秒）は完成して予約済み（037＝11/3 19:00、038＝11/4 8:00）。**039 は途中で止めた**（ユーザーが 22 時からゲームで GPU を使う）：台本・声・制作データは最新（悩む理由と、待っても見つかる保証がない理由を足した版）。Blender の場面は l00・l08・l10 を描き直す必要がある（ほかは描いてある）→ `cd production/pilot_039/blender && blender -b -P scene.py -- l00 l08 l10 --samples 32` → `python production/ext/blender/bl_pack.py 039` → `rv.py 039 render all` → サムネイル（`render_frames.js --dir pilot_039 --thumb`）→ ユーザーに見てもらう。記録 `anatomy_room/_backup/chain37.log`。生成スクリプトはスクラッチの make37.py・make37r.py・meta37.py・drafts37.py（次の会話では各ファイルを直接直す）。
- 029・035 は新しい声で作り直して予約の一覧に載せた（queued）。2026-11-02 は 1 日のアップロードの上限に当たったので、タスク スケジューラが上限の戻ったあとに上げる（029 は下書きが途中まである。`reupload`：同じ題名の古い非公開の版は無視し、下書きなら続きから）。

## 選択設計の 3 本の状況（2026-11-03 1 時）

- 037（68.5 秒）11/3 19:00、038（77.1 秒、前半は管制官の目線だけ・赤い警告灯）11/4 8:00、039（76.5 秒）11/4 19:00 に予約済み。038 の前の 2 つの版は YouTube で非公開のまま残っている。
- 038 以降の決まり（呼吸音は場面ごと、赤い警告灯 `POV.alert`、前半は一人称だけ、分かる言葉の 2 択、答えの理由が分かる造り）は `templates/DESIGN_MODES.md` の選択設計。

## 選択設計の次の 5 本 040〜044（2026-11-03〜）

- 040 ギムリー・グライダー（答え A）・041 ロゴゾフの自己手術（B）・042 ケルシーとサリドマイド（A）・043 ジョン・スノウのポンプ（B）・044 シャクルトンのジェームズ・ケアード号（A）。台本はユーザーが「OK」（2026-11-03）。事実確認・素材は `scripts/pilot_04N/`、YouTube の文は各 `youtube_metadata.md`。
- 3D は各回の `blender/scene.py`（前半は当事者の目線だけ）。11:48 から連続の書き出し（Blender 全ショット 32 サンプル → サムネイルの背景 `assets/src_thumb.jpg` → `bl_pack.py` → `rv.py render all` → `--thumb`）を 040 から順に。記録は `anatomy_room/_backup/chain40.log`（台本はスクラッチの chain40.sh）。1 本 約 2 時間。途中で止まったら、その回から同じ手順で。
- 予約はユーザーが見て指示してから（queue.json に載せる）。
- **2026-11-03 23 時の作り直し（ユーザーの指示）**：全体 55 秒以内、冒頭は 0 秒目から文字、冒頭と一人称に複数のカット（決まりは `templates/DESIGN_MODES.md` の選択設計の表）。対象は 038〜044（037 は公開済みなのでそのまま）。カットの区切りは各 renderer の `const CUTS`、Blender は `blkit.renderer_cuts`・`renderer_order` が同じ定義を読む。040 は客室のカット（`s_cab`）を新しく作った。詰め直しの前の版は `_backup/cut55/`。
- 書き出しは 038 → 039 → 040〜044 の順（スクラッチの chain55.sh・queue55.txt、記録は `_backup/chain40.log`）。038・039 は完成したら swap55.sh が古い版を非公開にし、同じ枠（11/4 8:00・19:00）に予約し直す。
- 注意：Bash ツールのコマンドが 10 分を超えて裏に回ると、Blender が最後の画像の書き込みで止まることがあった（2 回）。長い描画は Start-Process で切り離して動かす。

## 038〜044 の状況（2026-11-05 朝）

- 2026-11-04：札は Yuji Syuku・おどろおどろしい背景（A 赤・B 青）、冒頭の A・B は札 1 枚ずつ、冒頭の話速 1.25、上の小さな札のはみ出し直し（043 は上下 2 段）で 038〜044 をすべて書き出し直した（53.4〜54.0 秒、記録 `_backup/chain40.log`）。
- 038（11/5 8:00）・039（11/4 19:00）はこの版で予約し直し済み。
- 040〜044 は完成。2026-11-05 にユーザーの指示で予約済み：040＝11/5 19:00、041＝11/6 8:00、042＝11/6 19:00、043＝11/7 8:00、044＝11/7 19:00。video_qa の残りは「共通エンディング」（選択設計は想定どおり）と、一部の回の「字幕の欠落」（冒頭 L00〜L00b だけ。大きな文字と札が字幕の代わりなので想定どおり）。

## 長い動画の 1 本目 long_001（2026-11-05〜）

- テーマ「再現性の危機」、約 8 分、タイトル「心理学の 3 分の 2 は、やり直すと消えた」。2D の図が中心で、CG は視聴者に問いを投げる 3 か所だけ。構成は `scripts/long_001/plan.md`。
- ChatGPT への依頼文 `scripts/long_001/gpt_fact_check_prompt.md` → ユーザーが結果を貼る → Claude が出典で確かめて `fact_check.md`・`assets.md` → 台本 → ユーザーの「OK」。長い動画用の設計（声・BGM・図の部品）はこれから決める。
- 2026-11-05：ChatGPT の結果を確かめ直して `fact_check.md`・`assets.md`・`script_draft.md`（L00〜L58、約 3,000 字）を作成。冒頭のカードは「笑顔」をやめ「パワーポーズ」に（笑顔は 2022 年の研究で効果ありの面があるので結論側へ）。ユーザーの「OK」（2026-11-05、横長で、ピクトグラム・図・矢印・アイコンを多めに、動きにメリハリ、ナレーションはやや低温で落ち着いた温かいトーン）。
- **制作（2026-11-05）**：`production/long_001/`（横長 1920×1080、8 分 38 秒）。長い動画の部品は `production/ext/long/`（`long_ext.py`：横長の書き出し `render_frames_long.js` に差し替え・場面ごとに曲を切り替える BGM）。描画は `kit_long.js`（ピクトグラム・アイコン・矢印・3D の問いかけ）＋`renderer.html`（場面）。声は阿井田 茂 Calm 話速 1.15・抑揚 0.9（行間 0.22）。書き出しは `python production_script.py audio textcheck render mux docs qc`（rv.py は縦長用なので使わない）。1 コマ約 0.2 秒、2 本同時（映像 約 20 分）。音声のミックスは 8 分の長さで約 30 分かかる（pipeline のダッキングの畳み込みが長さに比例して重い）。
- **完成（2026-11-05）**：（8 分 38 秒、113 MB）。GitHub の 1 ファイル 100 MB の上限を超えるので **mp4 は git に入れない**（.gitignore。PC の作業フォルダにだけある）。サムネイル 、タイトル・説明文（チャプター付き）。video_qa の NG は「解像度」（横長なので想定どおり）・「最初のコマ」（thumbnail.png を使う）・「冒頭 3 秒の動き」（3D の判子がゆっくり迫る）。ユーザーの感想待ち。YouTube へのアップロードはユーザーの指示まで行わない。

## 次の動画でやること（ガイドライン v2.4）

1. 題材を決める（候補：伊能忠敬、ジョン・スノウ、ジョン・ハリソン、リービット、八木秀次など。前の会話のリスト）。
2. ChatGPT への事実確認の依頼文 → 結果を出典で確かめ直す → 台本 → ユーザーの「OK」。
3. CG のリアルさ（v2.4 の 1）：CC0 の HDRI・PBR の質感・3D モデル（Poly Haven・ambientCG）、SSAO などの仕上げ、MakeHuman でリアルな体型（顔なし）。PC に MakeHuman・Blender を入れてよい（ユーザーが承認済み）。素材は `assets.md` に記録。
4. 演出を大げさに（v2.4 の 2）：速い寄り・スロー・光の転換・大きさの対比・音との同期。
5. BGM は 5 つの曲調から題材で選ぶ（直前の 2 本と違うものを優先。pilot_016 は lab_melodic）。
