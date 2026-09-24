# Modern Standby interrupted final search

Recorded 22 September 2026, before resuming search or scoring any final rows.

The original final comparison stopped at task 8105, broad-stop arm. Node 2
wrote predictions and its worker-result file at about 20:07:29 UTC, but the
parent reported a 60-second timeout only at 21:53:34 UTC. It recorded 6,367.092
worker-process seconds for that attempt. The independent checker rejected the
rollout because that exceeded its 120-second allocation.

Windows Kernel-Power events record entry into Modern Standby at 20:07:06 UTC
and exit at 21:53:34 UTC. This is an infrastructure interruption. The result
file's existence does not recover the missing process-completion observation,
so its score will not be retroactively inserted into the search history. The
recorded timeout and elapsed time remain unchanged.

## Recovery decision

Keep the twenty completed arms for tasks 8101–8104. Exclude the entire task
8105 from the primary paired comparison on this documented infrastructure
criterion. Preserve its two admitted attempts, including the rejected timeout,
and report their cost separately. Do not run the remaining four arms of 8105.

Replace 8105 with seed **8123**, before creating or examining its data. The
replacement has the same classification role and curved signal-family index
under the unchanged generator. Keep the original arm order for that position.
The comparison still contains sixteen task instances and eighty planned arms.
The two interrupted-task attempts are additional incurred work outside that
complete comparison; this is an explicit deviation from the original maximum
allocation, not a silent budget reset.

No final-row score has been computed in this phase. Policies, pipeline engine,
proposer, model seed, per-arm limits, metrics and analysis remain unchanged.
No policy decision uses the interrupted task's outcomes. Preserve the original
task order and data manifest before recording the replacement. Keep its unused
public and final arrays, with their original identities, in the evidence tree.

Use a process-scoped Windows execution-state request while search and scoring
run. It prevents automatic idle sleep during that process and releases the
request afterward. It does not change the user's persistent power plan or
prevent explicit sleep. Another infrastructure interruption must be recorded
and reviewed, never repaired by deleting a ledger row or silently retrying.

The final report must disclose the replacement and extra incurred work. It
cannot present the completed study as exactly the original uninterrupted
protocol. The raw interruption remains available for audit.
