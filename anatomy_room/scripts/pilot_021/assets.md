# pilot_021：本物の写真・BGM の権利（2026-10-30 確認）

写真はパブリックドメイン・CC0・CC BY だけ（ガイドライン v2.2 の 4）。BGM は無料・商用可・収益化で使えるものだけ。

## 写真

| ID | 素材 | 出典・ページ | 作者・年 | 権利 | 確認方法 | 使い方・クレジット |
|---|---|---|---|---|---|---|
| A1 | 氷の上に降りた気球（1398×1050） | https://commons.wikimedia.org/wiki/File:Andree.crash.site.jpg | Nils Strindberg（1872–1897）、1897 年 | パブリックドメイン（作者の没後 100 年以下の国、米国では 1931 年より前の公表。Public Domain Mark 1.0） | Claude が WebFetch でファイルのページを確認 | 「写真：Nils Strindberg（1897）／パブリックドメイン」 |
| A2 | フレンケルとストリンドベリとホッキョクグマ（2574×1707） | https://commons.wikimedia.org/wiki/File:Fr%C3%A6nkel_and_Strindberg_with_polar_bear.jpg | 撮影者の記載なし（1897 年、探検隊の写真） | パブリックドメイン（スウェーデン：1976 年より前の写真。米国のタグが必要との注意あり） | Claude が WebFetch でファイルのページを確認 | 使う場合は「写真：1897 年 アンドレー探検隊／パブリックドメイン」。**倒れた動物が写るので、使うかは要検討** |
| A3 | 葬儀（ストックホルム、大聖堂、1930 年。2608×3543） | https://commons.wikimedia.org/wiki/File:Begravning_av_kvarlevorna_av_bes%C3%A4ttningen_p%C3%A5_Andr%C3%A9es_polarexpedition,_1930.jpg | Tekniska museet（ストックホルム）、1930 年 | CC0 1.0 | Claude が WebFetch でファイルのページを確認 | 「写真：Tekniska museet（1930）／CC0」 |

## BGM（短調でリズミカル。`production/voice_tests/keycheck.py` で調を推定）

Kevin MacLeod（incompetech.com、CC BY 4.0）。曲の情報は incompetech の一覧（pieces.json）。

| 曲 | BPM | 楽器・雰囲気（作者の一覧） | 調の推定（短調 / 長調の相関） |
|---|---|---|---|
| **Rhinoceros** | 126 | Synths, Percussion／Intense, Action | **ハ短調**（0.84 / 0.79） |
| **Machinations** | 140 | Snare, Bass Drum, Tuba, Trombones, Bassoon, Oboe, Strings／Bouncy, Driving, Intense | **イ短調**（0.82 / 0.70） |
| Industrial Revolution | 140 | オルガン・金管の重い曲（荘厳寄り） | ホ短調（0.76 / 0.59） |
| In a Heartbeat | 130 | Dark, Intense（ChatGPT の候補） | ハ長調寄り（0.45 / 0.67）→ 外す |

- クレジット：「"曲名" Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 License」
- Pixabay の候補（Dark (Breakbeat Techno)、Dark Electro Breakbeat (Cheater)）は今回は使わない（Content ID の申し立ての可能性・調の未確認）。

## 使わないもの

- 出発の写真「Örnens affärd 11 juli 1897」（Commons、Swedenborg 撮影、Grenna Museum）：CC BY-SA 4.0（方針の外）。
- 「'Eagle'.crashed.jpg」「Strindberg.sled.jpg」：解像度が低い（500×208・450×359）。
- 1930 年の発見現場の写真：個別の権利を確かめていない。
