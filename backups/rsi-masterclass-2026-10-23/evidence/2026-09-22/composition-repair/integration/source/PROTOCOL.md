# Repair composed parameter changes before further procedure evaluation

Declared before any repair fits. The completed six-procedure comparison
remains unchanged. This separately versioned implementation phase addresses
an observed source-composition defect; it does not reopen the prior 96-fit
development phase or 324-attempt evaluation.

## Changed implementation

Refinement v2 constructs the original template first. A capacity change scales
tree minimum leaf size from that template's setting, rather than overwriting
every template with a shared setting. It scales histogram leaf count and L2
from their template values. Zero L2 stays zero. The same existing bounds apply.
For an unlimited tree depth, the declared finite reference remains eight;
for an unlimited histogram leaf count, it is 31. Factor one exactly preserves
the template. Kernel, linear and neighbor behavior stays in the original
builder. All dependencies and this source are copied and frozen.

A constructor signature describes nested estimator types, parameters,
preprocessing and target transforms in this frozen implementation/environment.
It is not a general equivalence proof, source-code identity, learned-state
identity or promise of different predictions. A bounded proposal-list guard
refuses identical constructor settings without fitting or replenishing the
list. Future search protocols must account separately for refused proposals
and actual fitted candidates.

## No-fit checks

Use numeric and categorical fixture columns, not final rows. Check all
recorded development templates at factors 0.05, 0.3, 0.33, 1, 3 and 20, except
the untunable median at factor one only. Verify construction, sklearn cloning
and parameter validity, unchanged template behavior at factor one, and stable
constructor identity after cloning. Check the two observed tree-cancellation
factors, a saturated tree collision, equivalent RBF configurations from
different names, invalid factors and unsupported parameter objects.

Only after these checks pass, run the following **four total attempts**:

| Attempt | Already exposed task | Template | Factor | Builder |
|---|---|---|---:|---|
| 1 | 3: chess classification | one:extra-leaf2 | 0.3 | Frozen original |
| 2 | 3: chess classification | one:extra-leaf2 | 0.3 | Refinement v2 |
| 3 | 361234: abalone regression | two:extra-leaf5 | 0.3 | Frozen original |
| 4 | 361234: abalone regression | two:extra-leaf5 | 0.3 | Refinement v2 |

Use the existing frozen training and selection rows, one thread, seed 41,
and 30 wall seconds per subprocess including startup and prediction. Preserve
source, admission, output streams, predictions, metrics and elapsed time.
Failed attempts count. No retries, replacements, expanded grid or final data.
Do not require the new builder to win: correcting parameter composition can
improve or worsen a task. Independently recompute prediction metrics and
verify the frozen source/data after execution.

## Boundary and next action

The four-fit result establishes execution and observed behavior on two known
development tasks. It cannot supply a task-transfer, procedure-effectiveness
or RSI claim. Archive all checks and original bytes before new study work.
The next allocation design must compete with the strong fixed portfolio and
be frozen before new evaluation tasks are fitted. No extra model attempt is
permitted by this protocol.
