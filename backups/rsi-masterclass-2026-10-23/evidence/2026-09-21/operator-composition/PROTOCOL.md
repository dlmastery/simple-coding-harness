# Operator-composition protocol

Author walkthrough for 10.35, 21 September 2026. This is a labelled simulation: version numbers and compatibility scores are synthetic. No training, data synthesis, or real model evaluation occurs.

Freeze the driver, operator contracts, evaluator, initial state, and this protocol before execution. Data, harness, and model have separate version counters and content fields. Data writes a target-format record; harness writes supported format; model copies the harness format into a simulated learned-format field. Every operator declares read surfaces and exactly one allowed write surface. Evidence records all three state versions and the task format. Regenerate it between accepted state changes.

The external evaluator awards 50 synthetic points for a harness matching the task format and 50 for a model matching it. It is deliberately simple and never changes. This rule illustrates order dependence, not measured ML performance.

Five schedule checks, in order:

1. From initial state, run data → harness → model. Expect 100 synthetic points.
2. From the identical state, run data → model → harness. Expect 50. Both schedules have three operator calls and fresh evidence at each call.
3. Apply a harness update, then attempt a model update with the pre-update evidence. Reject the stale evidence without applying the model update.
4. Attempt a data update that also writes the evaluator. Reject before any state or evaluator mutation.
5. Use the revised scheduler in one later constructed task. The task format changes from 1 to 2; the released system's versions and content carry forward from check 1. Load the saved scheduler from disk. Its added rule checks compatibility before model; when needed, move the pending harness operation ahead of model. Expect data → harness → model and 100 synthetic points. No original-scheduler comparison is allocated on this later task.

After the first two outcomes, propose one scheduler revision and apply one static policy gate before activation. Keep the original scheduler, base order, and all rules. The gate permits only the documented pre-model interface check. It establishes an allowed rule change, not general scheduler quality. The later execution establishes that the saved revision was read and used.

Cap operator attempts at 12: three in each order comparison, two in the stale-evidence check, one forbidden-write attempt, and three in the later term. Count failed attempts. Three synthetic evaluator calls are allocated. Save before/after states, evidence, exact actions, rejections, policy hashes, and timing. Stop on an unexpected outcome; no additional candidates or reruns.

Separately read the paper's same-start improver comparison and per-term results. Explain why positive but smaller increments still raise the cumulative total. Record source-reported results separately. All examples share author context; no learner checkpoints or autonomous agent adaptation are tested.
