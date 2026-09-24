# A host interruption, preserved

Windows entered Modern Standby during task 8105. The second worker wrote its
prediction and result files at about 20:07:29 UTC. The parent resumed at about
21:53:34 UTC, reported a timeout and charged 6,367.092 seconds to that attempt.
The [independent check](rollout/independent-check.txt) refused the rollout for
exceeding its allowed worker time.

The [power events](POWER-EVENTS.csv) corroborate the standby interval. The
[original tree](rollout/TREE.csv) preserves one accepted attempt and one timeout.
The timed-out attempt's partial output remains available, but its existence
does not restore a verified process-completion record. Its score was not
inserted into the tree after the fact.

The [declared recovery](../../../../how-did-i-generate-it/rsi/validation/DISCOVERY-STANDBY-DEVIATION.md)
replaces the entire task with a new instance of the same kind and signal family,
before final scoring. It keeps the twenty unaffected completed arms and all
method code unchanged. The two interrupted-task attempts and recorded 6,368.914
seconds remain additional incurred work outside the primary paired comparison.

This is a protocol deviation. It must remain visible in the final report.
The [manifest](ARCHIVE-MANIFEST.csv) verifies 37 copied rollout files. The power
event CSV and this explanation are additional publication records. No final
evaluation score was computed for this interrupted task.
