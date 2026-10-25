# Data inspection

Python 3.12.12; scikit-learn 1.7.2; pandas 2.3.2; NumPy 2.5.3; Windows AMD64

Task: bike. Rows: 17379. Columns: 17.
Missing cells: 0. Exact duplicate rows: 0.

| Partition | Rows | Target mean | Target minimum | Target maximum |
|---|---:|---:|---:|---:|
| train | 8645 | 143.794 | 1 | 651 |
| selection | 4358 | 215.162 | 1 | 957 |
| final | 4376 | 254.091 | 1 | 977 |

Dates: 2011-01-01 to 2012-12-31.
Rows where casual + registered = cnt: 17379.
Do not use either component count as an input. Weather is observed, so this is not an advance forecast.

The source and partition summaries are public teaching data. This inspection is not independent evaluation.
