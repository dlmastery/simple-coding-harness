# Paired discovery-policy evaluation

Same synthetic grammar, new instances and separate final rows. Lower loss is better.

| arm | tasks | attempts | failures | mean_final_loss | worker_seconds |
|---|---|---|---|---|---|
| broad | 16 | 192 | 0 | 0.156857 | 412.041005 |
| greedy | 16 | 192 | 0 | 0.182729 | 424.636063 |
| lineage | 16 | 192 | 0 | 0.156857 | 415.006827 |
| evolved | 16 | 55 | 0 | 0.154037 | 110.920411 |
| broad-stop | 16 | 84 | 0 | 0.155744 | 173.959056 |

Search attempts: 715; separate scoring refits: 80.
Fit, worker-process, proposal and scoring costs are separate in RESULTS.csv.
PAIRED.csv reports task-bootstrap intervals; final_loss contrasts separate quality from cost.
No inference-cost or unseen-family generalization claim. Other RSI methods remain pending.

## Disclosed infrastructure deviation

Windows Modern Standby interrupted task 8105. Before final scoring, task 8123 replaced it, with the same kind and signal family. The original task, failed history, power events, task plan and data hashes remain in standby-recovery and rollouts/8105. All method code and comparison rules stayed fixed.

The paired table covers 715 search attempts and 80 scoring refits. An additional 2 admitted attempts belong to the excluded infrastructure case, with 6368.914 recorded worker-process seconds. That elapsed interval includes the host interruption and must not be interpreted as active model compute.

Total admitted model attempts across this phase, including scoring and the interruption: 797. INCURRED-COSTS.csv preserves the separate categories. The failed worker wrote partial fit telemetry, but its fit time is absent from the accepted tree and is not invented in this ledger. Its original worker-result.csv remains available as unaccepted output.

The paired efficiency comparison excludes the host-interrupted task. It is not a claim about net total research cost, which also includes development, orchestration and unmetered agent inference. REPORT-generated.md preserves the analyzer's original output. This annotation changes no result or contrast.
