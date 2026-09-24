# Conventional portfolio development results

These are selection scores. No final partition was scored. This is model selection, not RSI.

| Task | Selected model | Metric | Selection score | Normalized loss |
|---|---|---|---:|---:|
| 3 | rbf-10 | Balanced accuracy | 0.993846 | 0.006154 |
| 16 | rbf-1 | Balanced accuracy | 0.982412 | 0.017588 |
| 28 | extra-trees | Balanced accuracy | 0.985203 | 0.014797 |
| 361234 | rbf-1 | MAE | 1.427318 | 0.596788 |
| 361236 | random-forest | MAE | 443.365057 | 0.067844 |
| 361244 | rbf-1 | MAE | 0.365629 | 1.252431 |

48 attempts; 48 succeeded; 0 failed or timed out. Total worker-process time 114.197 seconds. 801 checks passed.

The fixed portfolio is the development reference for the next agent-authored proposal. No runtime-independent or total-cost gain follows from this baseline. Agent inference time/cost is unmetered.
