# long_001 事実確認：再現性の危機（心理学の 3 分の 2 は、やり直すと消えた）

> 2026-11-05。ChatGPT の結果（チャットに貼られたもの）を、Claude が出典で確かめ直した。「確認」の欄は Claude が読んだ範囲（抄録＝Europe PMC の抄録の本文、本文＝ページの本文、抜粋＝検索の要約だけ、GPT＝ChatGPT の報告だけで Claude は未確認）。多くの出版社のページは 403 で開けなかったので、抄録は Europe PMC から取った。

## 方針（ChatGPT の提案を採用）

「再現できなかった」「効果が限られていた」「不正が確認された」の 3 つを分けて言う。「心理学の 3 分の 2 は嘘」とは言わない。タイトルの「消えた」は本編で「3 分の 2 の研究で、効果がはっきりとは確かめられなかった。効果がないと決まったわけではない」と回収する。

## 確認結果

| ID | 判定 | 事実（台本で使う形） | 出典 | 確認 |
|---|---|---|---|---|
| C01 | VERIFIED | 2015 年、心理学の 3 誌の 100 の研究をやり直した。元の研究の 97% が有意、やり直しで有意は 36%。効果の大きさは半分。元の効果量がやり直しの 95% 信頼区間に入ったのは 47%、主観的に再現とされたのは 39% | Open Science Collaboration, Science 349, aac4716 (2015) doi:10.1126/science.aac4716 | 抄録 |
| C01b | GPT | Gilbert ら 2016 の批判（"the data are consistent with the opposite conclusion"）と反論がある | Gilbert et al., Science 2016 doi:10.1126/science.aad7243 | GPT（台本では「分析をめぐる反論もある」程度に） |
| C02a | VERIFIED | Many Labs 2（2018）：28 の研究、36 の国と地域、15,305 人。同じ向きで有意は 15（54%）。効果量の中央値 d は元 0.60 → 0.15 | Klein et al., AMPPS 2018 doi:10.1177/2515245918810225 | 抜粋（抄録の要約） |
| C02b | VERIFIED | 2010〜2015 年に Nature・Science に載った社会科学の実験 21 本をやり直し、同じ向きで有意は 13（62%）、効果量は平均で元の約 50% | Camerer et al., Nature Human Behaviour 2018 doi:10.1038/s41562-018-0399-z | 抄録 |
| C03 | VERIFIED | Ioannidis 2005「Why Most Published Research Findings Are False」（研究が小さい・効果が小さい・分析の自由度が大きいほど、結論が誤りである可能性が高いと論じた） | PLOS Medicine 2(8): e124 doi:10.1371/journal.pmed.0020124（CC BY） | 抄録 |
| C03b | GPT | Begley & Ellis 2012：がんの重要な前臨床研究 53 本のうち確かめられたのは 6 本 | Nature 483, 531 (2012) doi:10.1038/483531a | GPT（使うなら要確認） |
| D01 | VERIFIED | 2012 年の PNAS の論文（書類の最初に署名させると不正直な申告が減る）は 2021 年 9 月に撤回。撤回のお知らせは Simonsohn・Simmons・Nelson が Data Colada で示した、データの妥当性を疑う証拠を理由に挙げる | Retraction, PNAS 2021 doi:10.1073/pnas.2115397118（PMC8463784） | 本文（要約。原文の引用は長さの制限で取れず） |
| D01b | VERIFIED | Data Colada [98]（2021-08-17）「Evidence of Fraud in an Influential Field Experiment About Dishonesty」：保険の走行距離のデータ（約 13,500 人）に異常（0〜50,000 マイルに一様に分布、2 つの字体など）。"There is very strong evidence that the data were fabricated." 誰が作ったかは「データからは分からない」と書いている | https://datacolada.org/98 | 本文 |
| D02 | VERIFIED | Data Colada の 3 人は、2011 年の「False-Positive Psychology」の 3 人と同じ | 上の 2 つ | 本文 |
| D04 | VERIFIED | 登録報告（N=71、2018 年 11 月時点）と通常の論文の無作為抽出（N=152）で、最初の仮説が支持された割合は 96% と 44%。差の理由は「出版バイアスや偽陽性の減少がもっともらしい要因」（断定ではない） | Scheel, Schijen & Lakens, AMPPS 2021 doi:10.1177/25152459211007467（プレプリント doi:10.31234/osf.io/p6e9c は CC BY） | 抄録（プレプリント）。96.05%・43.66% は GPT |
| D05 | VERIFIED | Burger 2009：70 人、150 ボルトまでの部分的な追試。服従の割合はミルグラムより「少しだけ低い」程度（45 年後） | Burger, American Psychologist 2009 doi:10.1037/a0010932 | 抄録。70% 対 82.5% は GPT |
| B01 | VERIFIED（計算） | 有意水準 5%。効果のないものを 20 回独立に調べると、偶然の「効果あり」は平均 1 回、少なくとも 1 回出る確率は 1−0.95^20 ≈ 64% | 計算 | Claude が計算 |
| B02 | GPT | Rosenthal 1979「The "file drawer problem" and tolerance for null results」（Psychological Bulletin） | doi:10.1037/0033-2909.86.3.638 | GPT（名前と年だけ使う） |
| B02b | GPT | Fanelli 2010：心理学（と精神医学）の論文で仮説が支持された割合は約 9 割（91.5%） | PLOS ONE doi:10.1371/journal.pone.0010068 | GPT（台本は「9 割を超える」、要確認） |
| B03 | VERIFIED | Simmons・Nelson・Simonsohn 2011：分析の自由度で偽陽性が大きく増えることを、シミュレーションと実際の実験で示した | Psychological Science 22, 1359 doi:10.1177/0956797611417632 | 抄録 |
| B03b | PARTIAL | 実験 2：ペンシルベニア大学の学生 20 人が「When I'm Sixty-Four」か「Kalimba」を聴く。調整後の平均 20.1 歳 対 21.5 歳、p=.040（「nearly a year-and-a-half younger」）。父親の年齢で調整しないと有意でない。ほかにも多くの質問をしていた | 同上 | 抜粋（複数の二次資料が本文を引用）＋GPT |
| B03c | VERIFIED | よくある 4 つの自由度をすべて使うと偽陽性率は 61%（"a stunning 61% false-positive rate"） | 同上 | 本文（PDF） |
| B04 | GPT | Gelman & Loken「分かれ道の庭」（2013 の原稿） | — | GPT（台本では名前を出さない） |
| B05 | VERIFIED | イギリスの 20 大学の 2011 年の発表文 462 本と記事 668 本：発表文が動物の結果を人に当てはめていると記事の 86% も同様（そうでないと 10%）。行動の助言の誇張は 58% 対 17%、因果の誇張は 81% 対 18% | Sumner et al., BMJ 2014 doi:10.1136/bmj.g7015（CC BY） | 抄録 |
| B06 | VERIFIED | 繰り返された文は処理しやすく、本当らしく感じられる。正しい知識がある人でも起きた | Fazio et al., J Exp Psychol Gen 2015 doi:10.1037/xge0000098 | 抄録 |
| B06b | GPT | 読みやすい文字の文は本当らしく感じられる | Reber & Schwarz 1999 doi:10.1006/ccog.1999.0386 | GPT（要確認） |
| A01 | VERIFIED | メラビアン本人のサイト：「Total Liking = 7% Verbal Liking + 38% Vocal Liking + 55% Facial Liking」。"Unless a communicator is talking about their feelings or attitudes, these equations are not applicable." | https://www.kaaj.com/psych/smorder.html | 本文 |
| A01b | GPT | 元の研究は 1967 年の 2 本（Mehrabian & Wiener doi:10.1037/h0024532、Mehrabian & Ferris doi:10.1037/h0024648）。言葉と声・表情が食い違う状況で好意を判断させた | — | GPT（人数・条件は未確認なので台本に入れない） |
| A02 | PARTIAL | Rauscher, Shaw & Ky 1993（Nature 365, 611）：モーツァルトの K.448 を聴いたあと、空間の課題の成績が一時的に上がった。メタ分析（Pietschnig ら 2010）では効果は小さい | doi:10.1038/365611a0、doi:10.1016/j.intell.2010.03.001 | GPT（36 人・10〜15 分は未確認なので台本に入れない） |
| A02b | VERIFIED | 1998 年 1 月、ジョージア州知事ゼル・ミラーが、州で生まれる赤ちゃん（年約 10 万人）にクラシック音楽のテープか CD を配るため 10 万 5000 ドルを求めた | NPR 1998-01-13、Deseret News 1998-01-14、コネチカット州議会の報告 98-R-0888 | 抜粋 |
| A03 | PARTIAL | 1957 年、広告業者ジェームズ・ヴィカリーがフォートリーの映画館で「Eat Popcorn」「Drink Coca-Cola」を一瞬映し、売上が増えたと発表。1962 年の Advertising Age（Fred Danzig）で、データは少なすぎて意味がなかったと認めたと伝えられる（原文は二次資料のみ。Pratkanis 1992） | Wikipedia（手がかり）、Pratkanis "The Cargo-Cult Science of Subliminal Persuasion" | 抜粋（台本は「認めたと伝えられています」） |
| A03b | GPT | サブリミナル刺激が弱い効果を持ちうる研究はある | — | GPT（台本では「映画で買わせる話は裏付けがない」に絞る） |
| A04 | VERIFIED | Strack ら 1988 のペンの実験。2016 年に 17 の研究室でやり直し、差は元の 0.82 に対し 0.03（95% CI −0.11〜0.16） | Wagenmakers et al., Perspect Psychol Sci 2016 doi:10.1177/1745691616674458 | 抄録 |
| A04b | VERIFIED | Many Smiles（2022）：19 か国 **3,878 人**（GPT の 3,778 は誤り）。表情をまねる・自分で笑顔を作る方法は幸福感を増やした。ペンの方法では証拠がはっきりしなかった | Coles et al., Nature Human Behaviour 2022 doi:10.1038/s41562-022-01458-9 | 抄録 |
| A05 | VERIFIED | Watts, Duncan & Quan 2018：関連は元の研究の半分。家庭背景・早期の認知能力・家庭環境をそろえると、さらに 3 分の 2 小さくなった（解釈への反論もある：Falk ら 2019 のプレプリント） | Psychological Science 2018 doi:10.1177/0956797618761661（PMC6050075） | 本文（抄録部分） |
| A06 | PARTIAL | パワーポーズ：Carney, Cuddy & Yap 2010（42 人）。Ranehill ら 2015 の大きな追試でホルモンの効果は出なかった。2016 年に Carney が "I do not believe that 'power pose' effects are real." と表明 | doi:10.1111/j.1467-9280.2010.02613.x ほか | GPT（声明の原文は Carney の大学のページで要確認） |
| A07 | VERIFIED | Le Texier 2019：資料の調査と参加者 15 人への聞き取り。看守役は囚人の扱いについて具体的な指示を受けていた | American Psychologist 2019 doi:10.1037/amp0000401 | 抄録（台本では使わない予定） |
| E01 | PARTIAL | 「人は 1 日に 3 万 5000 回決断する」：元になった研究は見つからない（出典をたどると「ネットの情報」に行き着く） | didtheresearch.substack.com、skeptics.stackexchange の質問 32672 | 抜粋（台本は「実際に数えた研究は、見つかっていません」） |

## v2 で足したもの（2026-11-05、冒頭の差し替え）

| ID | 判定 | 事実（台本で使う形） | 出典 | 確認 |
|---|---|---|---|---|
| F01 | VERIFIED | 2013 年、7〜29 歳の 1,011 人の安静時の脳の画像を調べ、「左脳型」「右脳型」の人がいるという全脳の特徴とは合わない（偏りは脳の局所の性質）と結論。"our data are not consistent with a whole-brain phenotype of greater \"left-brained\" or greater \"right-brained\" network strength across individuals." | Nielsen et al., PLOS ONE 8(8): e71275 (2013) doi:10.1371/journal.pone.0071275（CC BY） | 本文（抄録） |
| F02 | VERIFIED | 1 万時間：エリクソンのバイオリンの研究で、トップの学生が 20 歳までに一人で練習した時間の平均が約 1 万時間。グラッドウェルが「全員が 1 万時間」と読んだ、と本人が『Peak』（2016）で批判。Macnamara・Hambrick・Oswald 2014（88 の研究）：意図的な練習で説明できる差は、ゲーム 26%・音楽 21%・スポーツ 18%・教育 4%・職業 1% 未満（2018 年の再分析には反論もある） | Ericsson, Krampe & Tesch-Römer 1993、Psychological Science 25(8) 1608 (2014) doi:10.1177/0956797614535810、Princeton・APS のニュース | 抜粋（台本は「音楽で、およそ 2 割」） |
| F03 | VERIFIED | ロジャー・スペリーは 1981 年のノーベル生理学・医学賞（"for his discoveries concerning the functional specialization of the cerebral hemispheres"）。分離脳の研究 | nobelprize.org（受賞理由・プレスリリース） | 抜粋 |
| B01b | 説明 | コインを 10 回投げて 8 回以上表が出る確率は約 5.5%（56/1024）。「ふつうのコインでも、たまに起きる」の裏付け | 計算 | Claude が計算 |

## 台本で言ってはいけないこと

- 「心理学の 3 分の 2 は嘘」「3 分の 2 は効果がない」と言わない（有意にならなかった、確かめられなかった）。
- 「笑顔を作っても楽しくならない」と言わない（ペンの方法が確かめられなかっただけ。2022 年は自分で笑顔を作ると幸福感が増えた）。
- 「マシュマロ・テストは否定された」と言わない（関連が小さかった）。
- 「モーツァルトは効果がない」と言わない（空間の課題の小さな一時的な効果の議論）。
- 正直さの研究で、誰が捏造したかを言わない・写さない（Data Colada も「データからは分からない」）。
- 「20 回試せば必ず 1 回当たる」と言わない（平均 1 回、少なくとも 1 回は約 64%）。
- GPT だけの数字（61%・91.5%・53 本中 6 本・96.05%）は、使う前に本文で確かめる。
- 「右脳と左脳の働きに違いはない」と言わない（働きの違いはある。性格のタイプに分かれる証拠がない）。
- 「練習は意味がない」と言わない（練習で説明できる差がある。1 万時間で誰でも一流、が言いすぎ）。

## v3 で確かめ直したもの（2026-11-05）

- B03b を本文（PDF、論文の 1364〜1365 ページ）で確認 → VERIFIED。論文の表向きの版：ペンシルベニア大学の学生 20 人が「When I'm Sixty-Four」か「Kalimba」（Windows 7 に入っている器楽曲）を聴き、関係のない作業のふりで誕生日（mm/dd/yyyy）と父親の年齢を答えた。父親の年齢で「もともとの年齢のばらつき」を補正し、20.1 歳 対 21.5 歳、p＝.040。開示版：本当は 34 人、3 曲目「Hot Potato」（The Wiggles）の条件もあった、約 10 人ごとに分析し終わりを決めていなかった、ほかに「何歳に感じるか」・ダイナーの食事・100 の平方根・「コンピューターは複雑な機械だ」・母親の年齢・早割の利用・政治的な立場・カナダのクォーターバック・「古き良き時代」・性別を聞いていた。父親の年齢で補正しないと 20.3 歳 対 21.2 歳、p＝.33（有意でない）。
- A02 の条件：モーツァルトの 2 台のピアノのためのソナタ（K.448）を 10 分聴く、リラックス用のテープ、無音の 3 条件のあと、スタンフォード・ビネーの「紙を折って切る」課題（複数の二次資料。効果は 10〜15 分ほど＝二次資料）。人数（36 人）は未確認なので台本に入れない。
- A01 の手順の細部（言葉の声の調子・顔写真の組み合わせ）は GPT と本人のサイト（like–dislike の伝達の実験、言葉と非言語が食い違うとき）から。人数は台本に入れない。
- 台本の「初めて会った人の印象の話ではない」は、本人の注意書き（気持ちや態度を話している場面でなければ当てはまらない）から言える結論として言う（本人が第一印象について直接述べた、とはしない）。
- D05b（2026-11-05 追加）：ミルグラムの服従の実験（1963 年の論文「Behavioral Study of Obedience」）。参加者は先生役、生徒役は演技をする協力者で電気は流れていない。基本の実験では 40 人中 26 人（65%）が最も強い 450 ボルトまで続けた。広く知られた事実（Claude の知識。教科書的な事実なので台本は「3 分の 2 ほど」）。Burger 2009 は実験 5 を 150 ボルト（生徒役が初めて抗議する点）まででやり直した（抄録で確認）。
