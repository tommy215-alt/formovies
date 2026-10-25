# なぜ黒板は緑色なのか？ — YouTube Shorts 制作プロジェクト

教養系チャンネル（仮）「当たり前の裏側」の Shorts 動画 1 本ぶんを、企画から書き出しまで行ったプロジェクトです。
映像・音楽・効果音はすべてこのリポジトリのスクリプトで作りました。外部の映像素材・音源・有料 API は使っていません。

## 成果物

| ファイル | 内容 |
|---------|------|
| `final_short.mp4` | 完成動画（1080×1920 / 30fps / H.264 + AAC / 95秒） |
| `narration.txt` | ナレーション全文（タイムコード付き） |
| `subtitles.srt` | 字幕ファイル |
| `script.md` | 構成と脚本 |
| `storyboard.md` | カットごとの絵コンテ |
| `sources.md` | 参照資料と、事実ごとの根拠 |
| `assets/audio/narration.wav` | ナレーション音声 |
| `assets/audio/bgm.wav`, `sfx.wav` | 自作の BGM と効果音（ミックス前） |
| `assets/logo.png` | 自作ロゴ |

## 使ったソフト（すべて無料）

| 用途 | ソフト | 入手方法 |
|------|--------|----------|
| 3DCG | Blender 4.0.2（EEVEE） | `apt install blender` |
| GPU なし環境での描画 | Xvfb + Mesa（llvmpipe） | `apt install xvfb` |
| 男性ナレーション | Open JTalk 1.11 + HTS 音声 `nitech_jp_atr503_m001` | `apt install open-jtalk open-jtalk-mecab-naist-jdic hts-voice-nitech-jp-atr503-m001` |
| 編集・書き出し | FFmpeg 6.1（libx264 / aac / libass） | `apt install ffmpeg` |
| 画像・音声処理 | Python 3、numpy、Pillow | 既存の環境 |
| フォント | Noto Sans CJK JP | `apt install fonts-noto-cjk` |

**ライセンスの注意**
- **HTS 音声 `nitech_jp_atr503_m001`**：名古屋工業大学のもので、修正 BSD ライセンスです。
- **Noto フォント**：SIL Open Font License です。
- **BGM・効果音**：`scripts/make_audio.py` で一から合成しています。

## 制作の流れ（再生成の方法）

```bash
# 0) 必要なソフト
sudo apt install blender xvfb ffmpeg open-jtalk open-jtalk-mecab-naist-jdic \
                 hts-voice-nitech-jp-atr503-m001 fonts-noto-cjk
pip install numpy pillow

# 1) ナレーション合成 → assets/audio/narration.wav と timeline.json（各文の開始・終了時刻）
python3 scripts/make_narration.py

# 2) チョークの筆記アニメーション（連番 PNG）と静止テクスチャ
python3 scripts/chalk.py
python3 scripts/make_textures.py

# 3) 3DCG のレンダリング（全19カット、途中で止めても続きから再開できる）
scripts/render_all.sh            # 1カットだけなら: scripts/render_all.sh C1
scripts/preview.sh D3            # 確認用に3コマだけ描画 → work/prev/

# 4) BGM・効果音・ミックス（ナレーション中は BGM を自動で下げる）
python3 scripts/make_audio.py

# 5) 字幕（SRT と、装飾付きの ASS）
python3 scripts/make_subs.py

# 6) 合成と書き出し → final_short.mp4
python3 scripts/compose.py
```

ナレーションの文言を変えるときは、`scripts/narration_data.py` を書き換えます（読み上げる文、字幕の分け方、強調する語 `{…}`、文のあとの間）。そのあと 1 → 4 → 5 → 6 を再実行してください。
カットの長さを変えるときは、`blender_shots.py` と `compose.py` の `SHOTS` を合わせて書き換えます。

## 技術メモ

- **チョークの筆記**：文字や図形ごとに「各ピクセルが現れる時刻」の地図を先に作り、フレームごとに切り出しています。チョークの棒の先の位置（`pen.json`）も同時に書き出し、Blender でチョークを動かして、効果音のタイミングにも使っています。
- **描画解像度**：GPU のないクラウド環境（CPU 4 コア、ソフトウェア OpenGL）では、1080×1920 だと 1 コマ約 15 秒かかりました。そのため 720×1280（8 サンプル）で描画し、Lanczos 法で 1080×1920 に拡大して、シャープネスとフィルムグレインを加えています。GPU のある PC なら、`blender_shots.py` の `resolution_x/y` を 1080×1920、`taa_render_samples` を 32 程度に上げると、さらに精細になります。
- **音量**：ナレーションは文ごとに音量をそろえてから、EQ・コンプレッサー・軽い残響をかけています。最終的なミックスは −14 LUFS（YouTube の基準付近）に正規化しています。

## 既知の制約
- **ナレーションの音質**：無料のローカル音声合成（Open JTalk + HTS）なので、ニューラル音声と比べると機械っぽさが残ります。
  - VOICEVOX ENGINE（無料、低音の男性話者あり）はダウンロードできましたが、このクラウド環境では外部の実行ファイルを動かす許可が出ず、使えませんでした。
  - 自分の PC で VOICEVOX を使えば、`make_narration.py` の `tts()` を VOICEVOX API（`/audio_query` → `/synthesis`）に差し替えるだけで品質を上げられます（クレジット表記「VOICEVOX:話者名」が必要です）。
- **資料の確認**：歴史資料は、ネットワーク制限のため Web 検索の要約で確認しました。詳しくは `sources.md` を見てください。
