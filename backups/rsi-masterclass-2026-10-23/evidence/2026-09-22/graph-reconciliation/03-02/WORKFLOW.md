# Give missing evidence its own route

For these fixtures, valid means that the CSV contains the required cnt target column. Invalid means that a present CSV lacks it. Unknown means the requested evidence file is absent, so no target-presence verdict can be obtained. This is a narrow teaching check, not a complete data-quality audit.

| Input | Condition | Safe action | Actual exit |
|---|---|---|---|
| valid.csv | valid | Ready for modeling | 0 |
| missing-target.csv | invalid | Repair missing target | 2 |
| absent.csv, deliberately absent | unknown | Stop and obtain evidence | 2 |
| absent.csv under the labelled unsafe policy | unknown | Incorrectly marked ready for modeling | 0 |

No route calls a fitting operation. Readiness is the output being tested. The unsafe policy makes absence look acceptable without adding evidence. Its verdict is retained as a counterexample, not as the recommended rule. Source data remains unchanged; copied fixtures live in this workspace.
