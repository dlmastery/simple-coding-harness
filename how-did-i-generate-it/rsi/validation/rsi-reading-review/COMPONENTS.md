# Which object changed?

This is the component and permission map for the recorded synthetic-task comparison, written after execution. Exact file identities are in [SOURCE-IDENTITIES.csv](SOURCE-IDENTITIES.csv).

| Object | Concrete artifact or operation | Reads and writes |
|---|---|---|
| Host language model | The authoring coding agent | Writes procedures and implementation in one shared context. Its weights do not change in this experiment. The host can access all local files. |
| Task solver | Fitted ridge/logistic or decision-tree pipeline | Reads training inputs and targets. Writes fitted parameters and predictions. Training-only scaling is part of the parent pipeline. |
| Task skill | Saved parent/child Markdown in the original run's `skills` directory | Selects the declared linear or tree family. Requires prediction records and the fixed task metric. |
| Improver | Saved `IMPROVER-v0.md` and `IMPROVER-v1.md` | Proposes the same tree child and chooses whether to retain it. The changed instruction uses selection performance in place of training performance. |
| Interpreter | Recorded `run-matched-improver.py` | Recognizes exactly the two supported rules. Reads the selected skill and procedure, runs the declared fits and saves decisions. It is not a general natural-language execution engine. |
| External comparison | Saved protocol, data partitions, metric functions and frozen final-scoring procedure | Judges the retained outputs. Candidates do not change these by the declared protocol; filesystem permissions do not enforce that restriction against the host. |

The [original protocol](../../../../rsi/evidence/2026-09-20/clean-journey/09-05/PROTOCOL.md) fixes the task and comparison. The [driver](../../scripts/run-matched-improver.py) contains both implementation and checking logic. This is organizational separation in a cooperative local workflow, not independent evaluation authority or secret final data.

Three edits have different meanings:

1. Change tree depth: task-model search. Demonstrate it through a changed recipe and measured predictions. The improvement procedure can remain fixed.
2. Change the task skill from linear to tree: a solver-procedure edit. Run both skills under the fixed improver and evaluator to measure its effect. In this example the edit changes model family; a task-skill edit need not always be that simple.
3. Change the improver from training-based to selection-based promotion: an improvement-procedure edit. The later recorded round must read it and use its rule to retain or reject a task-skill change. Its effectiveness needs the matched comparison, not just a file difference.

For the boundary counterexample, imagine the candidate changes the **external** final objective from MAE to a convenient metric after seeing its result. The old and new outcomes no longer answer the same predeclared question. Contrast that with changing the improver's **internal** promotion rule while the external task, metric, final cases and resource allocation stay fixed. That internal change is the candidate being judged in this experiment.
