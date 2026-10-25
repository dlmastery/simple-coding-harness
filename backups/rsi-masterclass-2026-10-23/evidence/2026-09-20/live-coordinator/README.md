# A coordinator whose saved state controls execution

This separate one-fit correction closes a gap in the [earlier walkthrough](../loops-and-systems/README.md): that run reconstructed its transition table after fitting. Here each state is saved and read before the next allowed action. The [protocol](PROTOCOL.md) and driver were pushed at `7850ec92378f6d1a52c105782dd9b5c770118a8f` before execution.

## Inspect the sequence

The [15 ordered events](EVENTS.csv) show:

1. `ready` was saved and read before admission.
2. `running` was saved before the fit command started.
3. The successful baseline entered `awaiting-check`; that process exited.
4. A later process read `awaiting-check`, ran three [handoff fixtures](FIXTURES.md), and launched the actual checker.
5. `complete` was saved after the successful check.
6. Another fit request read `complete` and returned exit 1 without launching a tool. The [before/after ledger hashes](outer-commands/03-refusal.md) agree.

The state snapshots, [procedure](COORDINATOR.md), [exact source](coordinator.source.py), actual [fit command](commands/fit.md), [check command](commands/check.md), and [checker report](run/trial-001/CHECK.md) make the control flow inspectable. The pending evidence used the full workspace-qualified candidate path and the prediction digest.

The wrong-candidate fixture references a genuinely checked baseline from the earlier run. Its predictions are byte-identical to this baseline, but it is a different candidate. The handoff is rejected. A matching metric or matching prediction file alone does not prove that the current candidate was checked.

## Budget and limits

One new constant/calendar fit used 0.103099 recorded fit seconds and returned selection MAE 159.947912. Fit/check child wall times were 2.048124 and 2.177792 seconds. Their parent-command timings include this work and must not be added to it. Agent implementation and inference costs remain unknown.

The original thirteen-fit run remains intact. This new correction brings the combined author work to fourteen fits; it does not expand any old experiment's allowance. No final evaluation or automatic retry occurred. The controller's failure-handling branch exists in source but was not tested by killing a running fit. The fixtures test local acceptance rules, not an independent LLM reviewer.

All 27 original files were copied and hash-checked against [the manifest](MANIFEST.csv). This index was added afterward. Separate processes demonstrate saved-state recovery, not a fresh coding-agent context. No learner prediction, quiz, teach-back, native-other-agent, or GPU/cluster validation is claimed.
