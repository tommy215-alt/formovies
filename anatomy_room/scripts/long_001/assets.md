# long_001 素材と権利

> 2026-11-05。使えるのは PD・CC0・CC BY だけ（CC BY-SA・NC・ND は使わない）。数字そのものに著作権はないので、グラフ・図は公開された数字から自前で描く。

## 本物の資料・写真

| 素材 | 権利 | 使い方 | 確認 |
|---|---|---|---|
| Ioannidis 2005 の論文の 1 ページ目（PLOS Medicine） | CC BY | 第 2 章で実物として映す。クレジット：John P. A. Ioannidis, "Why Most Published Research Findings Are False," PLOS Medicine (2005), CC BY 4.0 | Europe PMC のライセンス欄が cc by |
| Sumner ら 2014（BMJ）のページ | CC BY | 伝言ゲームの場面で実物として映せる | Europe PMC のライセンス欄が cc by |
| Scheel ら 2021 のプレプリント（PsyArXiv） | CC BY（プレプリント）。雑誌版は CC BY-NC とのこと（GPT） | 映すならプレプリントの版だけ。基本は数字から自前の棒グラフ | Europe PMC のライセンス欄（プレプリント） |
| モーツァルトの肖像画（Barbara Krafft、1819） | PD | モーツァルト効果の場面 | GPT（Commons のページで要確認） |
| NIH の研究の再現性のページ | 米国政府の著作物（PD の見込み）。ロゴは使わない | 必要なら | GPT |
| スタンフォード監獄実験の写真・Jordan Hall | CC BY-SA → 使わない | — | GPT |
| ヴィカリー・ミシェル・メラビアンの写真、1950〜60 年代の新聞 | 使える権利のものが見つからない → 使わない | 自前の図で | GPT |
| PNAS の撤回のお知らせ | 権利未確認 → ページは映さない | 文面の短い引用を自前の画面で | — |
| Data Colada の記事 | 権利未確認 → 映さない | 出典として名前を出す | — |
| xkcd「Significant」（グミ） | CC BY-NC → 使わない | 考え方だけ使い、絵は自前 | — |

## BGM（Kevin MacLeod、incompetech、CC BY 4.0。GPT が公式ページで確認。ダウンロードのときに Claude がもう一度確かめる）

| 場面 | 曲 |
|---|---|
| 冒頭・5 つの話 | Investigations |
| 仕組み 1・2・4・5 | Lightless Dawn |
| 仕組み 3（分かれ道の実演） | Crypto |
| 正直さの研究の撤回 | Satiate - only strings |
| 立ち直り・結論 | Comfortable Mystery |

クレジット（概要欄）："曲名" Kevin MacLeod (incompetech.com) Licensed under Creative Commons: By Attribution 4.0 License http://creativecommons.org/licenses/by/4.0/
Content ID の申し立てに備え、ダウンロードの記録を残す。

## 実際に使ったもの（2026-11-05、制作で確認）

- モーツァルトの肖像画：Wikimedia Commons「File:Wolfgang-amadeus-mozart_1.jpg」（Barbara Krafft、1819）。Commons の API で LicenseShortName＝Public domain を確認。960px の版を `production/long_001/assets/src/mozart_krafft_1819.jpg` に保存。
- Ioannidis 2005：PLOS の PDF（https://journals.plos.org/plosmedicine/article/file?id=10.1371/journal.pmed.0020124&type=printable）の 1 ページ目を PyMuPDF で画像にし、下の PLOS のロゴの帯を切り落とした（`assets/src/ioannidis_p1.jpg`）。ページの Copyright 欄に「open-access article distributed under the terms of the Creative Commons Attribution License」とある（本文で確認）。
- BGM：incompetech の曲一覧（pieces.json）で 5 曲の題名とファイル名を確認し、公式の mp3 をダウンロード（`production/long_001/assets/bgm/`）。「Satiate - only strings」のファイル名は Satiate Strings.mp3。FAQ のページで Creative Commons: By Attribution 4.0 を確認。
- Sumner 2014 のページの画像は使っていない（数字だけ自作の棒グラフに）。

## v4（2026-11-05 の作り直し）で使うもの

- 画像：モーツァルトの肖像画だけ（Ioannidis 2005 の 1 ページ目は、台本から外れたので使っていない。assets.js には残っている）。
- BGM：Investigations・Lightless Dawn・Crypto・Comfortable Mystery の 4 曲（Satiate - only strings は、正直さの研究の場面を削ったので使っていない）。
