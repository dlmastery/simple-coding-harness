# Diagnose the baseline before fitting alternatives

Read the existing constant-baseline selection report. At hour 8 its MAE is 324.076923 rentals; at hour 6 it is 47.972527. It predicts one training median for every row, so it cannot distinguish a quiet hour from a commuting hour. These are selected observations from the full hourly table, not new final-data inspection.

Hypothesis: replacing the constant predictor with a linear model on the same encoded calendar inputs will reduce overall selection MAE by representing some recurring hourly structure. The constant model receives those inputs but ignores them. The feature group is unchanged.

Possible failure: linear additive calendar effects may not capture hour-by-weekday interactions or a shifted demand pattern. Lower overall MAE may coexist with worse hourly slices. If linear MAE is equal or higher, this comparison does not support preferring it; retain both outcomes and the original rule. If only a few hours improve, do not claim uniform improvement.

Alternative explanation: calendar categories can represent several correlated patterns, not only hour. This model-family comparison cannot isolate a causal hour effect or prove that hourly representation is the sole cause of any gain.

Fixed conditions and allocation:

- Task: bike
- Models: constant,linear
- Features: calendar
- Seed: 17
- Limit: 2

Use the existing pinned task source, time-based partitions, MAE, tool and checker. Select only on the selection period. Retain the smaller selection MAE; on a tie retain the first candidate. No final evaluation or third fit.

The author has seen earlier public results for these recipes. This new pre-fit note records an execution decision, not a blinded scientific prediction. Student predictions, quiz answers and teach-back are not supplied by the author.
