# pilot_018：事実確認リスト（パスツールと少年——狂犬病のワクチン、1885 年）

調査日：2026-10-29（ユーザーの PC のセッション）。確認方法の定義は `docs/FACT_CHECK_POLICY.md`。

**確認の流れ**：ChatGPT の報告（`gpt_fact_check_prompt.md` への回答）を下書きにし、Claude が主な出典に当たり直した。WebFetch は本文を取得し、小さなモデルが質問に沿って抜き出す方法（全文を一字一句は読んでいない）。

## 物語の核

- **困難**：狂犬病は症状が出るとほぼ助からない（S1）。パスツールは医師ではなかった（S3・S4）。犬での実験は行われていたが、人での効果と安全性を保証するデータは乏しかった（S2）。マイスターの前に人への試みが 2 例あり、そのうち 11 歳の少女は翌日に亡くなっていた（S2：手当てが遅すぎたとされる）。
- **本人たちがしたこと**：医師グランシェが、乾かして弱めたウサギの脊髄から、少しずつ強いものへ、10 日間毎日注射した（S3・S4）。
- **何が変わったか**：少年は発病しなかった。患者が世界中から集まり、国内外の寄付で 1888 年にパスツール研究所が開かれた（S4・S5）。
- **現在**：かまれた後の手当て（傷の洗浄・ワクチン・必要なら免疫グロブリン）で防げるが、いまも毎年数万人が亡くなっている（S1）。

## 出典

| ID | 資料 | URL | 確認方法 |
|---|---|---|---|
| S1 | WHO「Rabies」ファクトシート | https://www.who.int/news-room/fact-sheets/detail/rabies | **Claude が WebFetch で本文を確認** |
| S2 | Cavaillon & Legout「Louis Pasteur: Between Myth and Reality」Biomolecules 12(4):596, 2022 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9027159/ | **Claude が WebFetch で本文を確認**（実験ノートの原本は未確認） |
| S3 | Institut Pasteur「The final years 1877–1887」 | （ChatGPT の報告による。Claude の WebFetch は 404） | ChatGPT の報告のみ |
| S4 | Institut Pasteur「The history of the first rabies vaccination in 1885」 | https://www.pasteur.fr/en/whats-new/latest-news/news/history-first-rabies-vaccination-1885 | **Claude が WebFetch で本文を確認** |
| S5 | Institut Pasteur「History」「Du vaccin contre la rage à la création de l'Institut」 | https://www.pasteur.fr/en/about-us/our-dna/history | 検索の抜粋のみ |
| S6 | 厚生労働省「狂犬病に関するQ&A」 | https://www.mhlw.go.jp/bunya/kenkou/kekkaku-kansenshou10/07.html | **Claude が WebFetch で本文を確認** |
| S7 | Pasteur「Méthode pour prévenir la rage après morsure」Comptes rendus 101:765–772（1885 年 10 月 26 日） | （ChatGPT の報告による） | ChatGPT の報告のみ（Claude は原文を未確認） |

## 事実確認リスト

### FACT-01
- **主張**：狂犬病は、症状が出るとほぼ助からない。
- **出典**：S1（"Once the virus infects the central nervous system and clinical symptoms appear, rabies is fatal in 100% of cases."）
- **検証結果**：VERIFIED（WebFetch）。台本は「ほぼ助からない」。

### FACT-02
- **主張**：1885 年 7 月、アルザスの 9 歳のジョゼフ・マイスターが、狂犬病の犬に 14 か所かまれた。7 月 6 日にパスツールのもとへ連れてこられた。
- **出典**：S4（"In July 1885, nine-year-old Joseph Meister from Alsace was bitten 14 times by a rabid dog."）、S2（"treated on 6 July 1885"、1876 年生まれ）、S3
- **検証結果**：VERIFIED（S4・S2 は WebFetch）
- **注意点**：かまれた数はパスツール本人の報告と未照合（パスツール研究所の数）。母親と来たことは S3（ChatGPT の報告）。

### FACT-03
- **主張**：ワクチンは、狂犬病で死んだウサギの脊髄を乾かして弱めたもの。弱いものから強いものへ注射した。
- **出典**：S2（"it was Roux's idea to dry out the spinal cords of rabbits that had succumbed to rabies, hung in vials, while Pasteur had the idea to add potash to accelerate the drying."）、S3
- **検証結果**：VERIFIED（WebFetch）。乾かす考えがルーのものだったことは S2 にあるが、台本では人名を出さない。
- **注意点**：「ウイルスを見つけた」とは言わない（当時は見えない）。台本は「病気の力を弱めて」。

### FACT-04
- **主張**：犬での実験は行われていたが、人での効果と安全性は確かではなかった。
- **出典**：S2（1884 年 8 月〜1885 年 5 月に 26 頭、乾かした脊髄の方法は 5 月 28 日・6 月 3 日に 20 頭、6 月 25・27 日に新しい 20 頭。"Pasteur experimented with his rabies vaccine in humans before he had accumulated sufficient evidence of the efficacy and safety of his vaccine."）
- **検証結果**：VERIFIED（WebFetch。ノートの原本は未確認）

### FACT-05
- **主張**：マイスターの前にも人への試みがあった（1885 年 5 月 2 日の 61 歳の男性ジラール、6 月 22 日の 11 歳の少女ジュリー＝アントワネット・プジョン。少女は翌日に亡くなった）。
- **出典**：S2（"Pasteur's laboratory notebooks reveal that Joseph Meister was not the first human to be treated with Pasteur's rabies vaccine"）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「世界で初めて人に打った」「まだ人で試されていなかった」と言わない。台本では先行例の詳細は出さず、「人での効果も安全性も、まだ確かではなかった」とする。

### FACT-06
- **主張**：パスツールは医師ではなく、注射は医師のグランシェが打った。
- **出典**：S2（"it was Joseph Grancher who performed the injections."）、S3（"As Louis Pasteur was not a physician he requested Dr Grancher to inoculate the child."）
- **検証結果**：VERIFIED（S2 は WebFetch、S3 は ChatGPT の報告）

### FACT-07
- **主張**：注射は 10 日間、毎日続いた。
- **出典**：S4（"Every day for ten days, Dr. Grancher administered 12 doses of the vaccine."）、S3（10 日間で 13 回）
- **検証結果**：PARTIALLY_VERIFIED（回数が資料で 12 回・13 回と食い違う）。台本は回数を出さず「10日間、毎日」。

### FACT-08
- **主張**：少年は発病しなかった。
- **出典**：S4（"Less than a month later, the outcome was clear: Joseph Meister had been saved!"）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：「注射がなければ必ず死んでいた」とは言わない（かまれた人のすべてが発病するわけではない。S2・ChatGPT の報告）。

### FACT-09
- **主張**：1885 年 10 月、パスツールは科学アカデミーで「かまれた後に狂犬病を防ぐ方法」を報告した。
- **出典**：S7
- **検証結果**：PARTIALLY_VERIFIED（ChatGPT の報告。題名と日付は複数の資料で一致するとされるが、Claude は原文を未確認）

### FACT-10
- **主張**：治療を求める人が世界中からパリに集まった。国内外の寄付で、1888 年 11 月 14 日にパスツール研究所が開かれた。
- **出典**：S5（1886 年に国内外で寄付の募集、1887 年の政令、1888 年 11 月 14 日に開所）、S4（"On November 14, 1888, the day the Institut Pasteur was inaugurated"）
- **検証結果**：VERIFIED（開所日は WebFetch、寄付は検索の抜粋）

### FACT-11
- **主張**：マイスターはのちにパスツール研究所の門番として働いた。
- **出典**：S2（"Meister, like Jupille, was infinitely grateful and became a guardian of the Institut Pasteur."）
- **検証結果**：PARTIALLY_VERIFIED（WebFetch）。台本は「働いたと伝えられている」。
- **注意点**：1940 年の死の状況（S2 は「ナチスの軍がパリに入ったときに自ら命を絶った」と書くが、ChatGPT は一次資料で未確認とする）は台本に入れない。

### FACT-12
- **主張**：いまも狂犬病で、世界では毎年数万人が亡くなっている。かまれた後すぐの手当てで防げる。
- **出典**：S1（"causes 44 203 annual deaths"〔2021 年の Global Health Estimates〕、実際はもっと多いとされる。手当ては傷の洗浄・ワクチン・必要なら免疫グロブリンかモノクローナル抗体。死者の 40% が 15 歳未満、主にアジアとアフリカ）
- **検証結果**：VERIFIED（WebFetch）
- **注意点**：ChatGPT の報告の「年間約 5 万 9000 人」は、いまの WHO のページにはない（古い推計）。台本は「数万人」。

### FACT-13（台本には入れない）
- 日本では、人は 1956 年、動物は 1957 年（猫）を最後に国内での発生がない。2006 年に 2 例、2020 年に 1 例、フィリピンでかまれた人の輸入症例（S6、WebFetch）。

## 言ってはいけない言い方

- 「世界で初めて人にワクチンを打った」「まだ人で試されていなかった」
- 「パスツールが自分で注射した」「少年は確実に死ぬはずだった」
- 「犬で安全性が証明されていた」「ウイルスを顕微鏡で見つけた」
- 「1940 年、ドイツ軍が来て自殺した」
- 「ワクチンを打てば絶対に大丈夫」

## 演出（事実ではないもの）

| 箇所 | 内容 | 扱い |
|---|---|---|
| 人物 | MPFB の人体（顔なし・後ろ姿・遠景）。少年・母親・パスツール・グランシェ | 冒頭に 1 回「※再現CGを含みます」（ユーザーの設定：注記は最小限） |
| 乾かした脊髄の瓶・注射の場面 | 再現 CG（本物の瓶の写真ではない） | 冒頭の注記でまとめる |
| 本物の写真・版画 | `assets.md` の素材だけ | 画面に小さく出典 |
