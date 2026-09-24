# What works in this tested setting

The two smoke runs use Codex desktop's file-reading route and local command tools in this author conversation. They do not use native skill discovery or a fresh independent agent. The desktop application build and serving model version were not exposed by the tools used; they are unknown. Do not substitute a CLI version for either.

Observed runtime: Windows 11 build 26200, AMD64, Python 3.12.12, scikit-learn 1.7.2, pandas 2.3.2, NumPy 2.5.3, SciPy 1.18.1 and matplotlib 3.10.6. Read commands/00-environment.md for the captured output.

| Dimension | Task | Agent / runtime | Backend | Status | Evidence and limit |
|---|---|---|---|---|---|
| Task A | Retrospective hourly bike count; MAE; chronological split | Current Codex file-reading route; versions above | Local CPU | Executed | One Ridge fit, prediction checker, hourly errors, budget refusal and new-process comparison |
| Task B | Red-wine quality at least seven; balanced accuracy; input-group split | Same author agent and versions | Same local CPU | Executed | One balanced logistic fit, both recalls, checker, budget refusal and new-process comparison |
| Capability guard | Same planned tasks; deliberately declared command access absent | Local profile fixture, actual host unchanged | No training submission | Executed fixture | Preflight refuses. This does not test another host or actually revoke permissions. |
| Native agent adapter | Same frozen task to be chosen | Claude Code or Gemini CLI; versions unknown | Local CPU | Planned | No native loading, permissions or execution tested here |
| Other file-reading agents | Same frozen task to be chosen | Host and version not selected | Local CPU | Planned | Readable procedure is available; actual target execution still required |
| Compute interface | Preserve a selected task's data, split and evaluator | Canonical adapter and backend-check documents read | Remote backend unspecified | Inspected | Interface requirements, not a submission or tested adapter |
| Larger-job outline | One unchanged bike candidate before any harder job | Future adapter and host versions unresolved | GPU/cluster unspecified | Generated | BACKEND-PLAN.md is a readable planning artifact; no launch file or job exists |

“Executed” applies only to the named operation and environment. It is not a global portability score. Earlier hosted OS/runtime checks in the course are separate evidence, not executions by another coding agent in this capstone.

## What stayed the same and what changed

The run-ml-experiment skill, supplied tool bytes, checker, Python environment, CPU and author context stayed the same. The skill directs inspection, a stated hypothesis, explicit settings, bounded execution, checking and honest accounting. DECISION.md records the author choices made under those instructions; matching policy hashes alone would establish only a snapshot.

Changing the scientific task changes the source data, target, split, permitted columns, estimator and metric. The common tool already implements both adapters. Their use proves those two existing paths run; it does not prove automatic adaptation to an arbitrary third task or transfer of capstone 11.02's revised improver. Numeric MAE and balanced accuracy cannot be compared as one progress score.

## Recovery and evidence boundaries

The unsupported task name was refused before workspace creation. Correcting that request led to the declared bike fit without increasing the budget. After each fit, a separate process reopened the workspace and selected its only candidate. That is state recovery for comparison, not interrupted training resumption. Extra-fit and changed-budget requests were refused. The sklearn estimators here have no mid-fit checkpoint recovery; no cancellation or retry was tested.

Data inspection exposes public partition target summaries and charts of all rows, including final-partition data. No final model performance was measured and no final fitting call ran. These files cannot support a claim of wholly unseen final data. The models and their parameters were fixed in the protocol before inspection.

Learner interpretation, independent agent execution, full-cost measurement and real remote cancellation/resume remain untested.
