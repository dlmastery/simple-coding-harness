# Operators: the inner agent as a tree search over solutions

Each operator is one prompt the actor applies to the tree of solutions it has fitted. Every operator carries the guard, word for word.

## draft
Draft: one solution per model family - the baseline preprocessing at the model's middle hyper value - so the tree has a root in every family before anything is expanded.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## debug
Debug: a solution that errored is not expanded; replace it by the same recipe with the other encoding, once, and move on.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## improve
Improve: expand the best solution - fit its untried neighbours, one field away, nearest first.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.

## review
Review: the score of a solution is the `val_score` of its fit result, nothing else. A score at or above 0.999, or one that jumps more than 0.2 above the previous best in one fit, is suspicious - `fit_recipe` marks it `suspicious: true` - and is fitted again before it is believed (it costs a fit). A statistical layer at the outer loop discards outlier successes.
Guard: do not tune to the validation split; a score that looks too good is re-run before it is believed.
