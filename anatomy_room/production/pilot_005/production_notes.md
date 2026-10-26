# pilot_005 制作ノート

第 1 話「マイナス×マイナスは、なぜプラスになる？」の制作方法・素材・注意事項。

## ファイル

| ファイル | 内容 |
|---------|------|
| `world_anatomy_pilot_005.mp4` | **完成動画**（1080×1920、30fps、H.264 + AAC） |
| `thumbnail.png` | サムネイル（1080×1920） |
| `final_script.md` | 完成台本（実際の音声の時間つき。自動生成） |
| `scene_plan.md` | シーンごとの時間・映像・音・セリフ（自動生成） |
| `subtitles.srt` | 字幕ファイル（動画には焼き込み済み。YouTube の字幕として別に上げることもできる） |
| `qc_report.md`、`qc/` | 品質検証の記録と抽出フレーム |
| `lines.json` | **元データ**：セリフ（読み上げ文）・字幕・シーン・間 |
| `production_script.py` | 制作スクリプト（音声合成 → BGM・効果音・ミックス → 映像 → 合成 → 資料 → 検証） |
| `renderer.html` | 映像のレンダラー（Canvas。時刻 t の 1 コマを描く） |
| `render_frames.js` | renderer.html を Playwright で 1 コマずつ撮影し、ffmpeg で動画にする |
| `work/` | 中間ファイル（セリフの wav、timeline.json、ミックス前の音声など。Git には入れない） |

## 作り直し方

```bash
# 0) VOICEVOX ENGINE（CPU 版 0.24.1）を起動しておく
#    https://github.com/VOICEVOX/voicevox_engine/releases の linux-cpu-x64 版を展開して
./run --host 127.0.0.1 --port 50021

# 1) 全工程
cd anatomy_room/production/pilot_005
python3 production_script.py all      # voice → audio → render → mux
python3 production_script.py docs qc  # 完成台本・シーン設計・字幕 → 検証
node render_frames.js --thumb         # サムネイル

# 部分的に確認するとき
node render_frames.js --stills 12.5,60.8   # 指定した秒のコマを work/stills/ に
```

セリフや字幕を変えるときは `lines.json` を編集して `voice` から実行し直す（音声の長さが変わると、映像のきっかけ・効果音・字幕の時間も自動で追従する）。

## 使ったソフトと素材

| 用途 | 使ったもの | 費用・ライセンス |
|------|-----------|----------------|
| 音声合成 | VOICEVOX ENGINE 0.24.1（CPU 版、ローカル実行） | 無料。外部 API・課金なし |
| M の声 | VOICEVOX:白上虎太郎（ふつう）、話速 1.18 | エンジン内蔵の規約：「VOICEVOX:白上虎太郎」とクレジットすれば商用・非商用で利用可 |
| W の声 | VOICEVOX:冥鳴ひまり（ノーマル）、話速 1.13 | エンジン内蔵の規約：「VOICEVOX:冥鳴ひまり」とクレジットすれば商用・非商用で利用可 |
| 映像 | 自作の Canvas レンダラー + Playwright（Chromium）で 1 コマずつ撮影 | 無料 |
| 編集・書き出し | FFmpeg 6.1（libx264 / AAC、loudnorm、ebur128） | 無料 |
| BGM・効果音 | `production_script.py` の中で一から合成（サイン波・ノイズ） | 自作のため権利の問題なし |
| フォント | Noto Sans CJK JP | SIL Open Font License |
| ロゴ | `anatomy_room/branding/` の「解剖された立方体」 | 自作 |

外部の映像素材・音源は使っていない。

### 声について

- 依頼の「男性ナレーションを基本とする」と、キャラクターガイドの「M＝男性役、W＝女性役」を両立させるため、**M を男性の声（白上虎太郎）、W を女性の声（冥鳴ひまり）** にした。W も男性の声にしたい場合は、`production_script.py` と `tools/measure_tts.py` の `VOICES["W"]["speaker"]` を男性話者（例：13＝青山龍星、11＝玄野武宏）に変えて `voice` から作り直す。
- **投稿前の注意**：クレジットはエンドカードに表示済み。**概要欄にも「VOICEVOX:白上虎太郎」「VOICEVOX:冥鳴ひまり」を記載すること**。各話者の詳しい利用規約（エンジンが案内している URL：白上虎太郎＝virvoxproject.com、冥鳴ひまり＝meimeihimari.wixsite.com）は、制作環境のネットワーク制限で本文を開けていないため、**投稿前に本文を確認すること**。

### 読み上げの調整

音声合成の読み間違いを防ぐため、読み上げ文（`lines.json` の `speech`）と字幕（`sub`）を分けている。

- 「負の数」が「まけのかず」と読まれたため、読み上げ文は「ふのかず」とかな書き（字幕は「負の数」）。
- 数字の前後のスペースや読点で不自然な間が入ったため、読み上げ文から取り除いた。
- 全セリフの読み（カナ）は `work/timeline.json` の `kana` で確認できる。

## 実装の要点

- **タイミング**：音声を先に合成し、実際の長さから各セリフの開始・終了を決める（`work/timeline.json`）。映像のきっかけ（式が出る、？が反転する、数直線が回る）は「セリフ ID ＋そのセリフ内の位置」で決めているので、音声が変わっても映像と効果音が追従する（`production_script.py` の `CUE_DEFS`）。
- **字幕**：映像に焼き込み。長いセリフは字幕を複数に分け、文字数の比で切り替える。話者タグ（M＝橙の丸、W＝水色の六角形）の横のバーは、そのセリフの実際の音量で動く。
- **レイアウト**：Shorts の右側のボタン列と下部の説明欄を避け、数式は y≈380〜1160、字幕は中心 y≈1350・x の中心 500 に置いた。
- **音**：BGM はセリフ中に約 55% 下げる（ダッキング）。全体を −14 LUFS（YouTube の基準付近）・トゥルーピーク −1.5 dBTP に正規化。
- **描画速度**：GPU のないクラウド環境で、1 秒あたり約 2.4 コマ（全 2,709 コマで約 19 分）。

## 注意事項

- 冒頭の借用書は比喩表現。実在の書式・企業・金額は描いていない。
- 面積図は「※正の数での例」と表示し、負の数の導出の場面では消している（監査の指示）。
- `work/` は再生成できる中間ファイルのため Git に入れない。
