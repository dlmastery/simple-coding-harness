# Test pipeline operators before the improvement loops

Declared after the 288-fit headroom pilot and before fitting these extensions, 22 September 2026. This is an adaptive development experiment. It is not preregistered final evidence.

The first pilot found little predictive headroom beyond a sound fixed control. Hypothesis: transformations and interactions can expose useful alternatives that scalar hyperparameter changes miss. A contrary result would be that conventional configurations still match the expanded reference, or that any apparent gains are too small to motivate the advanced exercise.

Reuse exactly the six prepared training/selection datasets from the first pilot; no new or final task rows. Add two operators to the default configuration of each of six families:

- Numeric quantile transformation to a normal distribution, fitted only on training rows. Categorical one-hot encoding is unchanged.
- Pairwise feature interactions after preprocessing, followed by scaling. Fit all transformations within the training pipeline. This uses all preprocessed inputs, including categorical indicators. Retain redundant/constant interactions rather than label-dependent filtering.

Budget: 72 new attempts (six tasks × six families × two operators), one library thread, 60 seconds per fit subprocess, no silent retries. The previous 288 fits are reused only as recorded reference measurements and are not charged as new executions. The combined catalogue therefore has 60 candidates per task, not 120. Count predictions are clipped at zero from the start.

Report every candidate, failure, fit and process duration, saved predictions and source identities. Recompute scores independently. Compare the 60-candidate development reference with two eight-attempt controls: the original fixed diverse order, and a strengthened diverse order comprising the six raw defaults plus linear interactions and linear quantile transformation. Neither control is selected after seeing extension scores. No gain is promised, and no result from this phase is called RSI.

If useful headroom exists, retain these operators as candidate actions available to *all* later methods and baselines. If it does not, retain the negative result and improve task suitability before spending on nested agent comparisons. Final task pools remain uncreated and untouched. Separate rows, unrelated task instances and different task families will have distinct roles in the later evaluation.
