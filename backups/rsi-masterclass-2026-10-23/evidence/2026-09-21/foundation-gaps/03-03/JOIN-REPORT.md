# Four observed scenarios

| Case | Expected | Actual |
|---|---|---|
| matching | proceed | proceed |
| missing | incomplete | incomplete |
| wrong-candidate | reject identity | reject identity |
| wrong-contract | reject contract | reject contract |

Only the complete matching pair proceeds. The delayed result is retained in the missing case without reopening its stopped decision.
