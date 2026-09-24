# One field repair, one unchanged parser

Author walkthrough for lab 10.34, executed on 21 September 2026. The driver exited 0. Four parser subprocesses produced these results:

| Report | Exit | Observed result |
|---|---:|---|
| [Valid](valid.txt) | 0 | Candidate and Status accepted |
| [Mismatched](mismatched.txt) | 1 | Result is unexpected; Status is missing |
| [Repaired](repaired.txt) | 0 | Changing Result to Status restores compatibility |
| [Incompatible template](incompatible.txt) | 1 | Run and Verdict violate the same contract |

The [frozen parser and contract](FREEZE.md) remained unchanged. The [repair](CHANGE.md) changed one field name. This is structural acceptance: it does not prove that candidate A was checked, or that its result is correct. There were zero model fits and no weight updates.

Read the [protocol](PROTOCOL.md), [measured timings](COST.csv), [results](RESULTS.md), and [source training audit](SOURCE-AUDIT.md). Each report has a matching `-VERDICT.md` file with exit status, stdout, and stderr. Node subprocess startup is included in time; agent inference cost is unknown. No learner prediction, teach-back, or quiz was tested.

The maintained [author driver](../../../../how-did-i-generate-it/rsi/scripts/run-model-harness-fit.mjs) refuses to overwrite its sibling workspace. Its archived snapshot records the exact implementation used. The manifest covers run files other than itself. This README and source audit were added after archival; they are not entries in that original run manifest. All copied run files were hash-verified against the workspace.
