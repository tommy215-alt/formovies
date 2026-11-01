# pilot_024 素材と権利（ソフィー・ブランシャール）

2026-11-01。ルール：収益化する YouTube で無料・許可なしで使えるもの（パブリックドメイン・CC0・CC BY）だけ（`templates/DESIGN_MODES.md`）。権利は Wikimedia Commons の API（extmetadata）で確認した。

## 画像

| ID | ファイル | 内容 | 作者・年 | 権利 | 使う場所 |
|---|---|---|---|---|---|
| A1 | [File:Blancharddeath.jpg](https://commons.wikimedia.org/wiki/File:Blancharddeath.jpg) | 燃える気球から落ちるブランシャールの版画（435×612） | 作者不明、*Harper's New Monthly Magazine*（1869） | パブリックドメイン | オープニングの中央（小さいので額縁の中で小さめに） |
| A2 | [File:Blanchardballoon3.jpg](https://commons.wikimedia.org/wiki/File:Blanchardballoon3.jpg) | 気球のかごに立つ全身の肖像（2484×3670） | Luigi Rados、1811（米国議会図書館） | パブリックドメイン | L02（人物の紹介） |
| A3 | [File:M.S. Blanchard, celebre aeronauta … 15 agosto 1811 LCCN2002716393.tif](https://commons.wikimedia.org/wiki/File:M.S._Blanchard,_celebre_aeronauta,_al_momento_del_volo_aerostatico_da_Lei_eseguito_in_Milano_in_presenza_delle_LL._AA._II._e_RR._la_sera_del_15_agosto_1811_LCCN2002716393.tif) | 1811 年 8 月 15 日、ミラノの夜の上昇（951×1536） | 1811、米国議会図書館 | パブリックドメイン | L05b |
| A4 | [File:Sophie Blanchard.jpg](https://commons.wikimedia.org/wiki/File:Sophie_Blanchard.jpg) | 肖像の版画（1053×1404） | Jules Porreau、1859（後世の版画） | パブリックドメイン | 予備 |
| — | File:Blanchard sophie grave.jpg | ペール・ラシェーズの墓 | Gede、2010 | **CC BY-SA 3.0 → 使わない** | — |

- A2 と A3 は同じ 1811 年のミラノの版画（A3 は小さい複製）だった。制作では高画質の A2 を、L02 では上半身に寄せて、L05b では全体で使う（A3 は使わない）。
- Smithsonian NASM の所蔵ページの版画は再利用に条件があるので使わない（ChatGPT の注意どおり）。議会図書館の同じ時期の版画（A2・A3）を使う。

## BGM（設計「悲劇」：短調でリズミカル）

incompetech の曲の一覧（pieces.json）で、存在・曲調・テンポを確認。ライセンスは CC BY 4.0（Kevin MacLeod）。

| 候補 | テンポ | 曲調（サイトの記載） | 理由 |
|---|---|---|---|
| **Danse Macabre**（第一候補） | 67（3 拍子のワルツ） | Epic, Intense, Mysterious。サン＝サーンス（1874）の編曲 | 「死の舞踏」。祭り・夜・死が題材にそのまま重なる。序盤は踊るように、後半の静けさへ |
| Volatile Reaction | 155 | Action, Aggressive, Dark, Intense（7/4 拍子、金管） | 速く暗い。前回の悲劇（Machinations・Black Vortex）に近い勢い |

- クレジット：「Danse Macabre」Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 License http://creativecommons.org/licenses/by/4.0/
- Content ID：Kevin MacLeod 本人は登録していないとしているが、第三者が誤って申し立てる例はある。申し立てが来たら、概要欄のクレジットで異議を出す。
- 読み込みは `production/ext/bgm_file.py`（pilot_020・021 と同じ）。
