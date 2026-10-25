# Paired discovery-policy evaluation

Same synthetic grammar, new instances and separate final rows. Lower loss is better.

| arm | tasks | attempts | failures | mean_final_loss | worker_seconds |
|---|---|---|---|---|---|
| broad | 4 | 48 | 0 | 0.163551 | 96.393117 |
| greedy | 4 | 48 | 0 | 0.184707 | 95.766494 |
| lineage | 4 | 48 | 0 | 0.163551 | 96.419983 |
| evolved | 4 | 16 | 0 | 0.162538 | 31.622086 |
| broad-stop | 4 | 18 | 0 | 0.162538 | 35.100564 |

Search attempts: 178; separate scoring refits: 20.
Fit, worker-process, proposal and scoring costs are separate in RESULTS.csv.
PAIRED.csv reports task-bootstrap intervals; final_loss contrasts separate quality from cost.
No inference-cost or unseen-family generalization claim. Other RSI methods remain pending.
