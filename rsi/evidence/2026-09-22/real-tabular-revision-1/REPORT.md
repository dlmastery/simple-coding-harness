# Revision 1: development comparison

These selection results used extra development fits. They do not establish an equal-budget improvement or RSI.

| Task | Best new candidate | Native score | Parent loss | New loss | Decision against original portfolio |
|---|---|---:|---:|---:|---|
| 3 | boost-regularized | 0.993879 | 0.006154 | 0.006121 | Keep candidate for further study |
| 16 | rbf-unscaled | 0.982809 | 0.017588 | 0.017191 | Keep candidate for further study |
| 28 | rbf-wide | 0.987551 | 0.014797 | 0.012449 | Keep candidate for further study |
| 361234 | absolute-boost | 1.429452 | 0.596788 | 0.597680 | Retain parent |
| 361236 | absolute-forest | 778.887430 | 0.067844 | 0.119186 | Retain parent |
| 361244 | median-reference | 0.325926 | 1.252431 | 1.116431 | Keep candidate for further study |

24 attempts, 24 successes, 0 failures/timeouts. Worker-process time: 83.284 seconds. 471 checks pass.

No final score was read. A median reference is a conventional control, not an RSI gain. Further development and later comparison costs must remain separate.
