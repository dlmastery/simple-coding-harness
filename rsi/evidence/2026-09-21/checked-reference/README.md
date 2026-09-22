# An answer is not an execution trace

Author walkthrough for lab 10.36, executed on 21 September 2026. The driver exited 0. These are constructed report-audit fixtures with real file reads and field checks, using a deterministic runner.

| Current-case trace | Observed final text | Trace gate |
|---|---|---|
| [Failed parent](failed-parent/TRACE.tsv) | complete | [Rejected](failed-parent/VALIDATION.md): omitted a required field check |
| [Valid reference](valid-reference/TRACE.tsv) | missing Split | [Accepted](valid-reference/VALIDATION.md): read inputs and checked all fields |
| [Answer-only shortcut](shortcut/TRACE.tsv) | missing Split | [Rejected](shortcut/VALIDATION.md): no input reads or field checks |
| [Alternative route](alternative/TRACE.tsv) | missing Split | [Accepted](alternative/VALIDATION.md): read order changed, obligations met |

The useful contrast is the valid reference and the shortcut. They print the same answer. Only one records the required work. The alternative shows why a different action order is not automatically a defect.

The [diagnosis](DIAGNOSIS.md) led to one [general edit](PROPOSAL.md): check every field named by the contract. The [quality gate](QUALITY.md) passed before evaluation. It admits a small declarative operation and checks growth and forbidden case literals; it is not a universal leakage detector.

The frozen candidate then produced `missing Split` on the [current fixture](candidate-current/EVALUATION.md) and `complete` on the [prior fixture](candidate-prior/EVALUATION.md). Both match the [predeclared oracles](ORACLES.md), so the [local decision](PROMOTION.md) retained the edit. No separate measured parent run on the prior fixture is claimed.

Budget used: four trace-generation runs and four trace validations, one proposal and quality gate, two candidate fixture executions, zero model fits. See [timings](COST.csv), [protocol](PROTOCOL.md), and [progress](PROGRESS.md). Agent inference cost is unknown. Field presence does not prove valid data science. All cases share author context; trusted instrumentation does not establish tamper-proof execution. Neither autonomous learning, broad transfer, a paper reproduction, nor learner understanding was tested.

The maintained [author driver](../../../../how-did-i-generate-it/rsi/scripts/run-checked-reference.mjs) preserves existing workspaces. The archived driver, inputs, before-action notes, traces, and verdicts record this run. The manifest covers the run files other than itself; this README was added afterward. All copied run files were hash-verified against the workspace.
