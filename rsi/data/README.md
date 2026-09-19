# Data for the rsi/ series

`adult_sample.csv` - 6,000 rows of the Adult Census Income table (OpenML "adult" version 2,
UCI Adult Census Income, CC BY 4.0), a stratified sample by the target with seed 0, with a
`target` column that is 1 when income is above 50K and the string `missing` where the source
had no value. It is bundled so every lesson and every test runs offline. The problem that uses
it is `../tasks/01_adult_income/intent.md` (`data: {kind: csv, path: data/adult_sample.csv}`,
relative to this `rsi/` directory).

No script ships here (the series ships no Python except each lesson's `test_step.py`). To
regenerate the sample: fetch OpenML `adult` version 2 as a frame
(`sklearn.datasets.fetch_openml("adult", version=2, as_frame=True).frame`), make `target` =
1 where `class` is `>50K`, drop `class`, take a stratified sample of 6,000 rows with
`random_state=0` (`train_test_split(frame, train_size=6000, stratify=frame.target,
random_state=0)`), fill missing values with `missing`, and write it with `index=False`.

The other problems need no files: breast cancer, wine and digits come from
`sklearn.datasets` (`kind: sklearn`), and problems 5-7, the lesson 12 pool and the lesson 14
held-out benchmark are `sklearn.datasets.make_classification` tables built from the seeded
parameters in their `intent.md` (`kind: synthetic`).
