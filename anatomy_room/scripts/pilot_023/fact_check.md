# pilot_023 事実確認（インスリンの発見、2026-10-31）

ChatGPT の調査結果（2026-10-31、ユーザーが貼った）を、Claude が出典で確かめ直した。判定は `docs/FACT_CHECK_POLICY.md` に従う。
「確認方法」に、Claude が自分で何を見たかを書く。ChatGPT の報告だけのものは、その旨を書く。

## 物語の核（台本の前に）

- **主人公の困難**：研究の経験がほとんどない外科医が、ノートに書いた仮説だけを持って大学の教授に頼む。死にかけた 14 歳の少年への最初の注射は効き目が弱く、注射の跡が膿んだ。
- **行動**：生化学者コリップが抽出液を精製し、12 日後にもう一度注射する。
- **結果**：少年の血糖は 1 日で正常まで下がり、少年はそれから 13 年生きた。幼い患者テディは「ぼく、太ったよ」と手紙を書いた。3 人は特許を 1 ドルずつで大学に譲った。
- **思いが伝わる場面**：テディの本物の手紙（CC BY 2.0）。

## 主張ごとの確認

| ID | 主張（台本での言い方） | 判定 | 出典 | 確認方法 |
|---|---|---|---|---|
| FACT-01 | 1922 年 1 月、トロントの病院で 14 歳の少年（レナード・トンプソン）が重い糖尿病だった | VERIFIED | トロント大学 Fisher Library の展示「Leonard Thompson」（fisherdigitus.library.utoronto.ca/exhibits/show/insulin100/early-patients/leonard-thompson）："at age fourteen"、"admitted to Toronto General Hospital on December 2, 1921, suffering from acute diabetes" | Claude が WebFetch で本文を読んだ |
| FACT-02 | 当時、重い若年の糖尿病に薬はなく、食事を極端に減らして死を先延ばしにすることしかできなかった | VERIFIED（「死を少し先に延ばす」は解釈を含む） | トロント大学「From a Patient's Point of View」："Prior to the discovery of insulin severe diabetics were treated primarily by means of a strict diet"（ChatGPT の引用） | ChatGPT の報告（展示の本文を読んだとのこと）。Claude は未確認。「全員が数か月で死んだ」とは言わない |
| FACT-03 | 1920 年 10 月、外科医バンティングが論文（Moses Barron）を読み、ノートに計画を書いた | VERIFIED | トロント大学の展示（Michael Bliss の解説）：日付は 10 月 30 日を 31 日に直したもの。原文 "Diabetus / Ligate pancreatic ducts of dogs. Keep dogs alive till acini degenerate leaving Islets. / Try to isolate the internal secretion of these to relieve glycosuria." | ChatGPT の報告（展示の本文と、ノートの所蔵記録を確認したとのこと）。Claude は未確認。「夜中に」は確かめられないので言わない |
| FACT-04 | 膵臓から、血糖を抑える物質を取り出せないか（計画の中身） | VERIFIED（言い換え） | FACT-03 のメモ（「尿の糖を和らげるため、島の内分泌物を取り出す」） | 同上 |
| FACT-05 | トロント大学のマクラウド教授が研究の場を与え、学生のベストと犬の実験をした（1921 年の夏） | VERIFIED | トロント大学の展示（Bliss）。1920 年 11 月 8 日にマクラウドを訪ねた | ChatGPT の報告。マクラウドは研究の場だけでなく助言もしたので「研究の場を与えた」にとどめ、「場所を貸しただけ」とは言わない。ベストを選んだ「コイン投げ」は確かめられないので使わない |
| FACT-06 | 膵臓を失った犬に抽出液を注射すると、血糖が下がった | VERIFIED | トロント大学の展示、Lewis & Brubaker 2021（J Clin Invest 131(1):e142239） | ChatGPT の報告。犬「マージョリー」の 70 日は台本に入れない（番号の対応が未確認） |
| FACT-07 | 1922 年 1 月 11 日、少年に初めて注射した。効き目は弱く、注射の跡が膿んだ | VERIFIED | Fisher Library の展示："the first test of extract on Leonard Thompson on January 11"、"it contained contaminants which caused an abscess to develop at the site of the injection"。J Clin Invest 2021："largely ineffective" | Claude が展示の本文（WebFetch）と論文の本文（WebFetch）で確認。「まったく効かなかった」とは言わない（血糖は少し下がった） |
| FACT-08 | 生化学者コリップが抽出液を精製した | VERIFIED | J Clin Invest 2021：Collip "joined Banting and Best in December 1921"、"His contribution to the process was to optimize the alcohol extraction procedure" | Claude が論文の本文で確認 |
| FACT-09 | 1 月 23 日、精製した液を打つと、少年の血糖は 1 日で正常まで下がった | VERIFIED | Fisher Library の展示："the dramatically successful second test on January 23"、"After the second series of injections Thompson's blood sugar dropped to normal in one day"。J Clin Invest 2021："declined by approximately 75%" | Claude が両方の本文で確認。**ChatGPT の「約 520 → 約 120 mg/dL」は、出典とされた J Clin Invest の論文に見つからない → 使わない** |
| FACT-10 | 少年はそれから 13 年生きた（1935 年、27 歳、気管支肺炎と糖尿病の合併症） | VERIFIED | Fisher Library の展示："Leonard Thompson lived for thirteen years on insulin. He died in 1935, at the age of twenty-seven, of broncho-pneumonia and complications from his diabetes." | Claude が展示の本文で確認 |
| FACT-11 | 幼い患者テディ（テディ・ライダー）がバンティングに手紙を書いた：「ぼく、太ったよ。木にも登れるよ」 | VERIFIED（年齢は 5〜6 歳と資料で違う） | 手紙の画像と所蔵記録（Thomas Fisher Rare Book Library、MS. COLL. 76, Box 8B, Folder 11、ca. 1923）。原文 "I am a fat boy now and I feel fine. I can climb a tree."（Fisher Library の展示「Theodore (Ted) Ryder」、検索の抜粋）。1922 年 7 月 10 日に治療開始、1993 年に没 | Commons のファイルの説明（所蔵の記録）は Claude が API で確認。手紙の文は検索の抜粋。**年齢は言わず「幼い患者」** |
| FACT-12 | 3 人（バンティング・ベスト・コリップ）は特許を 1 ドルずつでトロント大学に譲った | PARTIALLY_VERIFIED（広く伝えられる。特許の原本は未確認） | ChatGPT の報告（医学史の論文・Diabetes UK）。1923 年 1 月 | ChatGPT の報告だけ。Claude は未確認。「無料で配った」とは言わない。「インスリンは世界のもの」の言葉は原典が確かめられないので使わない |
| FACT-13 | 1923 年、薬は大量に作られ始めた | VERIFIED（「大量に」は始まりの意味） | Diabetes UK（イーライリリー社が 1923 年 10 月に商業供給を開始）、トロント大学「The Manufacture of Insulin」 | ChatGPT の報告。「すぐに世界中に届いた」とは言わない |
| FACT-14 | 1923 年のノーベル生理学・医学賞はバンティングとマクラウド。バンティングは賞金をベストと、マクラウドはコリップと分け合った | VERIFIED（受賞者）／PARTIALLY_VERIFIED（賞金の分け方の手続き） | NobelPrize.org（"for the discovery of insulin"）。賞金を分けた話は医学史の定説（Bliss） | ChatGPT の報告（NobelPrize.org は Claude の WebFetch では 403 で読めない）。ベストとコリップを受賞者のように言わない |
| FACT-15 | インスリンは糖尿病を治す薬ではない。命をつなぐ薬だ | VERIFIED（医学的な事実）／バンティングの言葉としては PARTIALLY | バンティングのノーベル講演（1925 年 9 月 15 日）"Insulin is not a cure for diabetes; it is a treatment."（Nobel Lectures の 68 ページとする引用集、検索の抜粋） | 講演の本文（NobelPrize.org）は 403 で読めない。**台本ではナレーションの地の文にして、本人の言葉としては引用しない** |
| FACT-16 | 死を待つだけだった病は、生きていける病になった | 解釈・比喩 | FACT-02・FACT-10・FACT-11 | 台本の結び（説明）。「治る病気」とは言わない |

## 使わないもの・言い方の注意

- 「昏睡の子どもたちが並ぶ病棟で、次々に目を覚ました」：同時代の記録が見つからない（ChatGPT も UNVERIFIED）。使わない。
- 「バンティングが一人で発見した」「最初の注射で劇的に回復した」「インスリンで糖尿病が治る」「世界中に無料で配られた」：誤り・誇張。
- 血糖の数値（520 → 120）：出典に見つからない。
- 写真の犬はマージョリーではない（所蔵記録では Dog 408）。画面で犬の名前を言わない。
- 動物実験は、手術や苦痛を描かない。犬・注射器・血糖の記録・瓶で見せる。
