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
