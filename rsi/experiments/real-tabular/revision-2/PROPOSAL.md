# Keep useful revisions and test a different representation

This second proposal follows the independently checked first revision: 24
successful fits and 471 checks. It spends the remaining 24 development slots,
four per task. No later task or final prediction has been read. No extra
development fits are available after this stage.

The first revision is evidence against a universal objective fix. Absolute
loss did not beat the existing abalone or auction models. On solar flare it
only tied a constant reference. Retain those outcomes. Numeric scaling changes
helped the two digit tasks slightly; the wider kernel helped optical digits.
These findings motivate changing representation and capacity, not repeating
the same failed objective patch everywhere.

## Classification proposals

1. Use unscaled numeric inputs with the RBF model at C=1. This tests whether
   the earlier unscaled result depended on the larger C=10 capacity.
2. Use unscaled numeric inputs at C=100 to test the opposite capacity direction.
3. Train a native-categorical histogram model. A training-fitted ordinal
   encoder supplies category IDs with an explicit categorical mask; this is
   not treating category IDs as ordered numeric distances. Unknown categories
   become missing values. Numeric inputs remain separate.
4. Train a random forest with all features considered at each split and
   minimum leaf size two. This tests whether feature subsampling hides useful
   interactions on these modest-sized tables.

## Regression proposals

1. Train histogram boosting in log1p target space, then invert predictions.
   This tests whether target scale compresses useful structure. It changes the
   training objective and may hurt original-unit MAE; report that risk.
2. Train SVR in the same target space with the narrow epsilon tube retained
   from revision one. This is actual source inheritance, not a renamed model.
3. Increase the minimum leaf size of Extra Trees to five. The baseline's
   near-zero training error and much larger selection error motivate this.
4. Fit Ridge to a quadratic-plus-spline representation. The earlier synthetic
   proposal showed one local gain but failed its gate. That result does not
   forbid a separately declared development test on this different panel;
   it also does not reopen or promote the rejected synthetic study.

The two log proposals reject negative training targets instead of silently
clipping them. All current development regression targets are nonnegative.
Regression target standardization remains training-fitted after the optional
log transform. Exact code and allocation are frozen before execution. Preserve
the original parent engine and first revision as explicit imported ancestors.

## Fixed limits and interpretation

One thread, seed 41, at most 30 subprocess seconds per slot, no retries, no
replacement tasks. The full development total is 48 original plus 48 revision
attempts. Scores are still selection feedback. Compare every child with the
best previously observed model and retain the previous winner on a loss.
The report also keeps the original-portfolio reference for continuity.

After this stage, freeze the candidate builders, retained rules and updater
variants. Design the matched comparison before fitting any of the six reserved
tasks. Do not add more development attempts to obtain a preferred result.
Conventional controls must receive the median reference and sensible tuning;
extra development compute and coding-agent inference remain separate costs.
