# 自分の PC で書き出す（GPU で速く）

クラウドの環境には GPU がなく、1 コマ約 3 秒（1 本 約 2 時間）かかる。GPU のある PC なら、書き出しのプログラム（`production/common/render_frames.js`）が**自動で GPU を使う**（GPU が使えなければ、これまでどおりのソフトウェア描画で書き出す）。

以下は **Windows** の手順。すべて無料で、登録・課金はいらない。黒い画面（「ターミナル」）に打つ文字は、そのままコピーして貼り付ければよい。

## 1. 道具を入れる（最初の 1 回だけ）

スタートメニューで「ターミナル」を開き、1 行ずつ貼り付けて Enter。途中で「許可しますか」と出たら「はい」。

```
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.12
winget install Gyan.FFmpeg
winget install Git.Git
```

終わったら**ターミナルを閉じて開き直す**（入れた道具が見つかるようになる）。続けて：

```
pip install numpy pillow
```

## 2. VOICEVOX を入れる

https://voicevox.hiroshiba.jp/ から「ダウンロード」→ Windows 版（**GPU 版**があればそちら）を入れる。
書き出しの間は **VOICEVOX のアプリを起動したままにしておく**（アプリを開くと、裏で声を作る部分が動く）。

> 第 1 話からの声は VOICEVOX ENGINE 0.24.1 で作っている。アプリの新しい版でも同じ声で動くはずだが、声の細部が少し変わることがある。

## 3. リポジトリを取ってくる

```
cd ~
git clone https://github.com/tommy215-alt/formovies.git
cd formovies
git checkout claude/jolly-knuth-5nlxei
cd anatomy_room
npm install
npx playwright install chromium
```

## 4. 日本語フォント（Noto Sans CJK JP）を入れる

https://github.com/notofonts/noto-cjk/releases を開き、「**03_NotoSansCJK-OTC.zip**」をダウンロードして展開。
中の `NotoSansCJK-*.ttc` をすべて選んで右クリック →「**すべてのユーザーに対してインストール**」。

> Google Fonts の「Noto Sans JP」は名前が違うので使えない。

## 5. そろったか確かめる

`anatomy_room` で：

```
node tools/check_pc.js
```

最後に「すべてそろっています」と出れば OK。「NG」の行があれば、その行の「→」のあとに直し方が出る。

- 「GPU で WebGL」が NG のとき：GPU のドライバを最新にする（NVIDIA は GeForce Experience / NVIDIA App、AMD は Adrenalin、Intel はドライバ更新ツール）。それでも NG なら、書き出しはできるが速くならない。

## 6. 速さを測る（pilot_010 の数コマ）

```
cd production/pilot_010
python production_script.py voice
node ../common/render_frames.js --dir . --stills 3,20,40,60,80
```

1 行目で声を作り（1〜2 分）、2 行目で 5 コマを `work/stills/` に書き出す。最後に「**1 コマあたり ○ 秒**」と出る（クラウドは約 3 秒）。最初の行に「WebGL: GPU（…）」と出ていれば GPU で描いている。

## 7. 1 本を書き出す

```
python production_script.py all
```

## うまくいかないとき

- `python` が見つからない → `py` に変えて打つ（例：`py production_script.py voice`）。
- `ffmpeg` や `node` が見つからない → ターミナルを開き直す。それでもだめなら PC を再起動。
- GPU を使わずに書き出したい（色の出方を前の回とぴったり同じにしたいときなど）→ 書き出しの前に `set REVERSE_GPU=off`（PowerShell なら `$env:REVERSE_GPU="off"`）。

## Mac の場合

1 の代わりに https://brew.sh の Homebrew を入れて `brew install node python ffmpeg git`、2 は VOICEVOX の Mac 版、4 は `brew install --cask font-noto-sans-cjk-jp`。3・5〜7 は同じ（`python` は `python3`）。
