# Precision failure before fitting

The driver at `06a7d2231f8d1e2e12fefbbda1151155a61781b9` exited 1 at its regression target equality assertion. It completed the output-correction activity and its fixed-reporter subprocess, then stopped in the first reflection-input check. No new ML fits ran.

Compared the retained `09-05/cases/<task>.csv` target values with each v1 parent/child prediction table, using all training and selection rows. Row identity and order matched in all eight tables.

| Task | Candidate | Partition | Rows | Numerically unequal targets | Maximum absolute difference |
|---|---|---|---:|---:|---:|
| Regression | Parent | Training | 600 | 8 | 5.684341886080802e-14 |
| Regression | Parent | Selection | 200 | 4 | 5.684341886080802e-14 |
| Regression | Child | Training | 600 | 8 | 5.684341886080802e-14 |
| Regression | Child | Selection | 200 | 4 | 5.684341886080802e-14 |
| Classification | Parent | Training | 600 | 0 | 0 |
| Classification | Parent | Selection | 200 | 0 | 0 |
| Classification | Child | Training | 600 | 0 | 0 |
| Classification | Child | Selection | 200 | 0 | 0 |

The earlier artifacts preserve decimal serializations across data-generation, loading, and prediction-writing steps. The difference is far below a meaningful target change, but it is not bitwise numeric equality. Use absolute tolerance 1e-12, relative tolerance 0, for this regression replay only. Do not relax row-identity or classification checks, rewrite the original artifacts, or adjust a result to pass. Selection comparisons still use the recomputed metrics and their original direction.

The failed run, its exact source, and copied inputs remain archived separately. A corrected run has a new workspace and records the extra diagnostic work as unmetered author overhead. No fit budget was spent or refunded in this pre-fit failure.
