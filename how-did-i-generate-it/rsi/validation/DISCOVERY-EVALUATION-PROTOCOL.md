# Compare the frozen discovery policies

Declared after development generation 2 and before generating seeds 2101–2104
or 8101–8116. This evaluates the current discovery-policy adaptation only.
Other method comparisons and the presentation remain required.

## Five procedures

1. Broad round-robin exploration: the original fixed control.
2. Greedy leaf selection after three independent drafts: the second fixed control.
3. Probe a lineage: agent revision 1, without the learned stopping rule.
4. Evolved policy: revision 2, selected in the first replay round and retained
   in the second. Its source is frozen before all evaluation tasks.
5. Broad exploration with the same 0.20 loss threshold: an ablation constructed
   now. It receives the learned threshold, so it is not a prelearning baseline.

All use identical data, proposer, engine, model seed 41, 12-attempt maximum,
120 charged worker-process seconds, 60 seconds per attempt and one numerical
thread. Failed attempts count. Every arm runs online; controls are not inferred
from incomplete replay. Arm order rotates by task to reduce timing-order bias.
No concurrent workers in this comparison. Record policy and proposal time
separately; agent inference cost remains unknown.

## Separate tasks and rows

Procedure-selection seeds 2101–2104 serve as a prospective shakedown. No policy
selection or threshold tuning is planned from these results. A correctness
failure requires a versioned repair and a declared deviation before final
tasks are run. These four tasks do not count toward final performance.

Final seeds 8101–8116 provide sixteen paired task instances: odd seeds classify,
even seeds regress. Use the same three-family generator as development, with
new latent coefficients and feature scales for each seed. Reproduce the
generator's first 2,000 rows exactly: 1,200 training and 800 selection. Create
1,000 additional independent final rows from the same latent task, using a
separate RNG seed (task seed + 100,000). Keep final arrays outside rollout
workspaces. The generator's training/selection bytes must match the original
generation algorithm for an existing seed before running new tasks.

This is transfer to new instances within a known synthetic grammar, not to
unseen problem families or real datasets. Later claims about other settings
require separate evidence. Local filesystem separation is procedural, not
secure evaluation isolation.

## Freeze, score and report

Freeze source hashes before task generation. Complete all arms in a phase and
freeze each selected candidate before any final-row scoring for that phase.
Refit only the selected candidate on its original training rows, using the
same model seed. Reproduce its selection predictions before scoring final
rows. Charge these scoring refits separately; do not relabel them as search.
Do not refit on training plus selection, which would change the selected model.

Report each task's final balanced accuracy or MAE, normalized final loss,
executed attempts, worker seconds, fit seconds and failures. Classification
loss is twice balanced error; regression loss divides MAE by the training-median
predictor's final MAE. Compare evolved policy with every control on the same
task. Lower loss is better. Show predictive ties separately from reduced-cost
results. Also report the prespecified combined utility (loss + 0.001 worker
seconds), clearly secondary to its separate quality and cost components.

Summarize paired differences and a 95% task-bootstrap interval (10,000
resamples, seed 20260922). The primary contrast is evolved versus broad
round-robin. Other contrasts and per-family subsets are descriptive. Sixteen
tasks do not establish general RSI or make a tiny difference reliable.

Maximum search allocation: 240 attempts in shakedown and 960 in final
evaluation, plus one scoring refit per completed arm (20 and 80 respectively).
Do not extend allocations or tune against final outcomes to force a positive
result. Keep failures, refusals, negative contrasts and all source versions.
