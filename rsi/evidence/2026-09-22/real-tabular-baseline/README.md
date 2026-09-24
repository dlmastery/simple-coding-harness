# A strong starting portfolio on six public tasks

All **48 attempts succeeded**, and **801 independent checks pass**. No final
partition was scored. The [report](REPORT.md) lists the selected model and
selection metric for each task; [the ledger](LEDGER.csv) retains every attempt.
The archive contains 322 byte-verified original files, including source,
input copies, predictions and logs. [Inspect the manifest](ARCHIVE-MANIFEST.csv).

| Development task | Best portfolio member | Selection result |
|---|---|---:|
| Chess | RBF SVC, C=10 | 0.993846 balanced accuracy |
| Multiple Features | RBF SVC, C=1 | 0.982412 balanced accuracy |
| Optical digits | Extra Trees | 0.985203 balanced accuracy |
| Abalone | RBF SVR, C=1 | 1.427318 rings MAE |
| Auction verification | Random forest | 443.365057 milliseconds MAE |
| Solar flare | RBF SVR, C=1 | 0.365629 flares MAE |

This is conventional model selection. The different winners show why a
research procedure needs feedback instead of one universal model choice.
The high classification scores also show that a public dataset is not
automatically a hard improvement problem. Small remaining gains will need
careful comparisons. Solar flare's selected loss exceeds its training-based
normalization scale; the next development proposal must investigate this
failure rather than hide the task.

The [declared protocol](source/REAL-TABULAR-DEVELOPMENT-PROTOCOL.md) limits
future development to at most 48 further attempts, eight per task. A concrete
agent-authored proposal must precede those fits. The six reserved procedure
comparison tasks remain unused for training. A later matched comparison is
needed to establish whether any retained skill, harness or updater helps.

Return to [the data preparation](../real-tabular-data-v2/README.md) or inspect
[the implementation](../../../experiments/real-tabular/README.md).
