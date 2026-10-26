# Move the useful input change within the three-fit budget

Read the actual 10.13 trace before this proposal. The constant/calendar baseline has selection MAE 159.947912. Linear/calendar reaches 109.807668. Tree/calendar reaches 125.049488, so it is rejected and the linear parent remains active. Adding permitted weather inputs to that parent reaches 99.175924 on attempt four.

R1 moves enrich before explore: draft, refine, enrich, explore. Keep the operator definitions, retained-parent rule, fixed evaluator, and tie rule unchanged. Under three fits R0 uses its first three operators; R1 uses its own first three. Both start from empty state and pay for their baseline. The earlier four-fit result is evidence motivating this proposal, not the parent comparison arm.

The author knew other bike results before this run. This is a development comparison with deliberately exposed selection evidence, not an independent test of improvement discovery. A repeated recipe is expected to reproduce its deterministic selection score; a difference would require investigation. No final evaluation is requested.

Data exposure correction: the supplied inspect action prints public final-partition aggregate statistics. The author saw those aggregates. It does not issue final model predictions, but the protocol's phrase about not accessing final data was too broad. Preserve that original statement and the correction in EXPOSURE-NOTE.md. These data have never been secret from the author.
