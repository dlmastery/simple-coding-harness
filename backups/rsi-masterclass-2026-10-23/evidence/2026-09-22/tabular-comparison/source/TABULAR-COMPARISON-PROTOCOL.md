# Frozen six-procedure public-tabular comparison

Declared before any reserved-task fitting. This protocol instantiates the
comparison design after the 96 development attempts and checked memory replay.
Use tasks 6, 23, 31, 361235, 361237 and 361247 with their already frozen grouped
partitions. Do not add or replace tasks, change metrics, retune from their
outcomes or restart a failed attempt. They are public classroom adaptations,
not the suites' official cross-validation or secret industrial benchmarks.

## Sources and data

Freeze the runner, worker, policy, ten role files, revised builder, three
executed ancestor builders, memory files, environment versions and every
partition identity before fitting. Candidate processes receive copied
train/selection paths. Final files live in a separate evaluator directory;
they are used only after all 36 choices are frozen and search checks pass.
The host can access both directories, so this is a procedural boundary.
Hashing frozen files is an identity check, not final-score access.

Every generated candidate contains its template and capacity factor in source.
A child copies its selected parent's builder files and preserves that parent's
candidate source. Preserve inherited hashes, the proposed source, skill hash,
admission, predictions, metrics, output streams and actual process time.
The immutable shared builder includes the code written in development; no
new LLM call occurs inside this fixed inner proposer.

## Allocation and controls

Six tasks by six procedures by eight attempts gives **288 search attempts**.
Each subprocess may run for 30 wall seconds, including import, fit, prediction
and output. One thread; model seed 41. No shared-fit cache, retry or task
replacement. Record failed, invalid and timed-out attempts. If no valid
incumbent exists, stop and preserve the failure rather than invent a score.
Execution order rotates the six procedure names once per task.

Every classifier starts with linear, Extra Trees, RBF C=1 and histogram
boosting. Every regressor starts with median, linear, random forest and RBF
C=1. All procedures then have four remaining slots:

- `fixed`: classification adds random forest, RBF C=10 and neighbors 5/25;
  regression adds Extra Trees, histogram boosting, RBF C=10 and neighbors 5.
- `random`: seed 7341 + task ID; draw four templates with replacement from
  the full revised same-kind builder set except the untunable median. Draw
  each capacity factor as 10^Uniform(-1,1). Prevent exact recipe collisions
  using the same declared collision rule as local search. The task ID seeds
  randomness; it is not a learned retrieval feature.
- `memory`: read the frozen experience. Average per-task selection-loss ranks
  over the three same-kind development tasks, break ties by candidate name,
  and run the next four untried templates at factor one.
- `parent`: use original five-role updater v0 and the parent harness. After
  four probes, write two refinements at 0.3 and 3 times the incumbent factor.
  Check both, retain the best, then write and execute two further refinements.
- `harness`: same v0 updater and two-round schedule; the revised builder uses
  a representation/objective variant for each lower-capacity branch. The
  higher-capacity branch keeps the incumbent template.
- `updater`: revised five-role updater v1 and the revised builder space. Each
  later round allocates one unused evidence-ranked template and one local
  refinement. A selection-minus-training normalized loss above 0.15 selects
  factor 0.3; otherwise factor 3. Require the regression median reference.

The representation map is fixed: RBF/SVR/unscaled models map to unscaled C=1
classification or log-SVR regression; forest/Extra Trees to leaf-two Extra
Trees classification or absolute-error forest regression; boosting to native
categorical classification or absolute-error boosting regression; other
classification to the wider RBF template and other regression to quadratic
plus splines. Refining a median starts from base histogram boosting.

Factors are rounded to eight decimals and bounded to [0.05,20]. At factor one
the template is unchanged. Otherwise: C scales for kernels/logistic; Ridge
alpha divides by factor (both clipped to [0.001,10000]); tree depth is
round(8*factor), clipped to [2,32], and minimum leaf size round(3/factor),
clipped to [1,30]; histogram leaf count is round(31*factor), clipped to [7,63],
with L2=1/factor; neighbor count is round(template count/factor), clipped to
[2,100]. The exact-recipe collision multipliers, tried in order, are
1, 1.1, 0.9, 1.25, 0.8, 1.5 and 0.67. Refuse if none supplies a unique recipe.
No unobserved score participates in this choice.

These factors generate candidates outside the 16 recorded points. An
operator that changes representation is a source-level harness intervention.
A five-role updater governs which skill proposals are generated and allocated.
These remain bounded programmatic adaptations, not independent LLM agents,
model-weight learning or reproductions of named source systems.

## Selection, lineage and final scoring

Selection loss is 1 minus balanced accuracy for classification, and MAE
divided by training mean absolute deviation from its training median for
regression. Keep native metrics too. The independent checker recomputes row
identity, target identity and metrics from saved predictions before a candidate
can become incumbent. Minimum loss wins; exact ties retain the earlier step.
The external rule is identical for all procedures and updater versions.

After four probes, updater procedures write skill round one, execute its two
proposals, write a retention decision, then write skill round two using that
feedback and execute its proposals. Save all five role-file hashes and the
prior skill hash at both rounds. This tests a revised updater's actual later
use during comparison. It does not establish post-promotion deployment,
autonomous invention of the updater, repeated meta-generations or acceleration.

Freeze all 36 selected candidate bundles and choices before scoring any final
row. Score each with one charged refit from training only: **36 refits**, for
**324 maximum total model attempts** in this study. The refit must reproduce
selection loss within 1e-12 absolute/relative tolerance; otherwise mark it
invalid, retain its outputs and do not replace it. No training+selection refit.
Final scoring failures stay visible as missing outcomes, never silent zeros.

## Reporting

The primary contrasts are revised harness minus parent; revised updater minus
revised harness with original updater; memory minus fixed; and memory minus
random. Report every task's native score and normalized loss, every cost and
failure, and the distinct meaning of each contrast. No blended “win” count
may combine quality with fewer fits. Each successful search arm spends eight
fits, so this study cannot claim fewer fitted candidates.

For complete pairs, use mean paired normalized-loss differences and a
descriptive 10,000-draw stratified task bootstrap (three classification and
three regression tasks, seed 7342). Report the interval as exploratory: six
tasks and one model seed do not establish broad superiority or account for
multiple-comparison selection. With missing pairs, show them and report only
explicitly labelled available-pair summaries; do not use a complete-study
interval or overall success claim.

Development cost, replay work and unknown coding-agent inference cost are
additional. Recorded worker time is not total research cost or a hardware-
independent benchmark. Keep the earlier full discovery-tree study separate
from this comparison. Update the course and presentation only from checked
results, including regressions and ties.
