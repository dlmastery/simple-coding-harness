# Wine quality data

Source: [UCI Wine Quality](https://archive.ics.uci.edu/dataset/186/wine+quality), P. Cortez, A. Cerdeira, F. Almeida, T. Matos and J. Reis. Original study: *Modeling wine preferences by data mining from physicochemical properties*, Decision Support Systems, 2009. UCI supplies the data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Downloaded 20 September 2026. The [original description](source/winequality.names), red and white tables, and archive are retained. The required classification exercise uses red wine only.

| File | SHA-256 |
|---|---|
| `source/wine-quality.zip` | `3ed56667f4b828242bd732d7d1dd7f2861e54432239d7fa63877014cbb0304d4` |
| `source/winequality-red.csv` | `4a402cf041b025d4566d954c3b9ba8635a3a8a01e039005d97d6a710278cf05e` |

The course derives a binary label: quality score at least 7. This threshold is an instructional choice, not an original label from the authors. Freeze it before search. Use balanced accuracy as the primary metric and also inspect recall for each class. A majority-only classifier receives balanced accuracy 0.5 when both classes occur.

Keep identical physicochemical input rows in the same partition, even if labels differ. The supplied splitter assigns feature groups through a fixed hash. It reports class counts and refuses an unusable partition. This is an approximate group split, not guaranteed stratification. Do not hunt for a seed that improves the model's score.

Laboratory features may not represent information available in every real deployment. Quality scores are subjective, ordinal assessments. A binary threshold discards information and a score of 6 is close to 7. Include these limits in the model card.
