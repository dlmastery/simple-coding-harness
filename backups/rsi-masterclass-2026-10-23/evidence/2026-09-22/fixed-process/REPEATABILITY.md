# Same predictions, different execution records

The historical 01.02 baseline and both new runs use constant/calendar with seed 17. All three prediction files have SHA-256 0004513ae666f36bcf4987e2b36944f1c4a8d79bf949ef09b788d0b95e6af93c. Matching complete bytes covers row identities, copied targets, prediction values and hours, rather than only the rounded score. The new separate prediction checks also compare those rows with the pinned source.

Each run has selection MAE 159.94791188618632. Historical recorded fit time is 0.099014 seconds; new process and skill fit times are 0.071519 and 0.069980 seconds. These timings are single observations of short operations, not evidence of a speed improvement. Command startup/check intervals are recorded separately and overlap action intervals; do not add both.

Contract bytes differ from the historical run. The historical tool hash is 1febbe8eacac7873d9a09031cc133200e55224e2fea0205c88090eea4bd5b5a0 and its shared ceiling was twelve. The current tool hash is d69d3fbd8a4ace3e0332f4dfbc9a2648f87f858867229db63bc854f7810120a0 and each new experiment freezes its intended one-attempt allocation. The task, raw data, split, metric and actual recipe are unchanged. Do not describe these as byte-identical software environments or contracts.

The historical and current reports name Python 3.12.12, sklearn 1.7.2, pandas 2.3.2 and NumPy 2.5.3. ENVIRONMENT.md records the current environment. We reused that installed environment and created new empty experiment workspaces. We did not reinstall dependencies or use a new coding-agent context.

Two new fits and six child commands completed. Both five-action traces were recorded during execution. No final evaluation, candidate search, procedure change or RSI result follows. Matching predictions support this fixed-recipe repeatability check.
