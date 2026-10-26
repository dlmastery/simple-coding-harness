# Trace a baseline backward

The original 00.03 result reports MAE 159.947912. Its predictions contain source row 8645, observed count 48 and baseline prediction 109, hence absolute error 61. The pinned source dates place that row in January 2012, inside selection. The task brief chooses cnt and excludes its component counts. Calendar-only inputs avoid using observed weather in this first baseline. The data card supplies source provenance and the fixed chronological rule.

The original process text combined inspection and partition checking. It did not give every action its own input, product and completion check. The revised PROCESS.md makes those dependencies explicit. Earlier command logs remain useful, but missing historical preparation timestamps cannot be invented. The newly declared 01.02 execution will record actual five-action timing instead.

## Put split design after fitting: a counterexample

If we fit, inspect errors and then choose which dates count as selection, we can favor dates where the model already looks good. The recipe and evaluation conditions have then been selected together. A lower MAE could reflect an easier chosen slice rather than a better model.

This is a hypothetical reordered process, not an executed contaminated experiment. Keep the original rule fixed, use selection for allowed development choices, and reserve the declared final role. These public files are accessible to the author, so the final role is a procedural boundary rather than secrecy.
