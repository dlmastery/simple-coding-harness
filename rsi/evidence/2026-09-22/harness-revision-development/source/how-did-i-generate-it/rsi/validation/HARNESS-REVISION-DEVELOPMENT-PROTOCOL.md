# A paired development test of a changed inner harness

Declared before any new-harness fit. This is the next experiment after the
frozen discovery-policy comparison, not an amendment to its methods or outcomes.

The coding agent proposes a new feature-construction capability in
`rsi/experiments/harness-revision`. Its written proposal cites development
task 1106 and the public generator. It does not use any final-row result.
The parent and child are executable inner search programs. This is an
AIDE-inspired adaptation with a deterministic inner proposer, not a full
reproduction of AIDE2 or a test of ignition.

## Matched work

Use six new development instances, seeds 3101–3106. The existing generator
gives one classification and one regression case from each known signal family.
Use only its 1,200 training and 800 selection rows. Create no final arrays for
this development study. These tasks are not a substitute for later evaluation
on separate instances or real data.

Run both harnesses on every task. Each receives twelve attempts, 120 worker
seconds, at most 60 seconds per worker, model seed 41 and one numerical thread.
Alternate arm order by task. Execute sequentially. The broad round-robin policy
stays identical in both arms. No fit starts while the other timed comparison
is running. Use temporary idle-sleep prevention on Windows.

The parent keeps its original engine and proposer. The child adds quadratic
plus spline features for the linear branch and changes when that branch tries
them. Other model-family proposals remain identical. Save the original builder
as `parent_engine.py` inside every child root and inherited workspace, so all
code needed for a candidate travels with it.

Initialize a new, unscored workspace for each arm. Assemble all harness files
before its final source manifest and contract are frozen. Never alter a contract
after the first attempt. Preserve full parent/child code, ancestry, predictions,
timings, rejected candidates and failures.

## Development gate

The child passes this exploratory gate only if its mean normalized selection
loss is at least 0.01 lower than the parent's, neither task-kind mean worsens,
and it introduces no additional failed attempts. This is a heuristic gate for
continuing research, not a statistical significance claim. Report every task
and raw metric. Cost remains a separate outcome. Do not change the gate after
seeing these results.

Maximum allocation: 144 search attempts. Both arms execute their declared
allowance unless a resource failure stops them. There is no final scoring or
scoring refit in this development phase. A failure of the gate retains the
parent and the rejected source. No repeated tuning against final tasks is
allowed. A passing child still needs a separately declared final comparison.
