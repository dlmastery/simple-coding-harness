# Learn a better search procedure on public tabular tasks

Declared before the first fit on this panel. This development phase uses
classification tasks 3, 16 and 28, and regression tasks 361234, 361236 and
361244. The other six tasks remain reserved for later procedure comparison.
Do not read or score any final partition during development.

## A meaningful starting point

Run eight fixed candidates per development task: regularized linear model,
Extra Trees, histogram gradient boosting, random forest, two RBF kernel
strengths, and two nearest-neighbor neighborhood sizes. These are conventional
baselines, not RSI. Compare future proposals against the best observed member
of this portfolio. All preprocessing is fitted on training rows. Numeric
inputs use median imputation and standardization; categorical inputs use
mode imputation and one-hot encoding with unknown categories ignored.
Regression models standardize the target inside the fitted pipeline so that
SVR's C and epsilon do not depend on target units. Classification models that
support class weights use balanced weights. Do not use target encoding or
source-declared ignored columns.

Freeze the exact engine, driver, worker, dependency versions, this protocol,
and copied public train/selection files before fitting. The historic discovery
runner and its 16-feature limit remain unchanged. The new CSV runner supports
this mixed and higher-dimensional panel explicitly.

## Budget and records

The initial portfolio has exactly 48 admitted attempts, eight per task.
Each subprocess has a 30-second wall-time limit including imports, fitting,
prediction and output. One thread, model seed 41, no concurrent model runs.
Each admitted failure or timeout consumes its slot. No retries or replacement
tasks. Record planned candidates before execution, source and input hashes,
stdout, stderr, timings, status and predictions on train/selection. No model
pickle is needed: later scoring must charge any refit and reproduce its source.
Explicitly record temporary Windows idle-sleep prevention; do not change
persistent power settings. An interruption requires a preserved review.

Reserve at most another 48 development attempts for agent-authored revisions,
at most eight per task with the same per-attempt limit. Write a concrete
proposal and its allocation after inspecting the baseline, before its fits.
Unused allocations are not gains; report actual attempts and costs. The
48-attempt allowance is a maximum, not an instruction to run a full grid.
The root coding agent authors revisions. No separate LLM proposer, independent
scientist, model-weight update or autonomous agent is implied.

## Feedback and later evaluation

Primary classification loss is one minus balanced accuracy. Regression loss
is MAE divided by the training mean absolute deviation from the training
median. This denominator uses no selection or final labels. Report MAE in
native units too. Use minimum selection loss, then candidate order to break
ties. Keep all failures. Development gains are selection gains, not evidence
of task transfer or recursive improvement.

The next comparison must freeze each method's mechanism, retained artifacts,
the strong fixed control, equal resource allowances, promotion gates and
scoring procedure before training on the six reserved tasks. It must separate
task-model optimization, retained task skills, harness revisions and changes
to the updater itself. A good development score does not establish any of
those higher-level claims. Do not relabel this study a paper reproduction or
an industry benchmark result. Do not reopen the rejected synthetic gate.
