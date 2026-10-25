# Run a small white-wine regression experiment

This package turns a new prediction brief into an executable harness. Start with [the task](TASK.md) and [data card](DATA-CARD.md). The coding agent handles Python and commands; students state intent.

Give your agent this prompt:

```text
Read this package's TASK.md, DATA-CARD.md,
WORKFLOW.md, and RECOVERY.md. Explain the
prediction question and the MAE baseline.
Create a new sibling experiment with one
allowed attempt. Run the training-median
baseline, check its saved predictions, and
show me an intentional target-as-feature
refusal. Keep the commands and failures.
Leave final evaluation unused.
```

Expect a data report, frozen contract and split, attempt ledger, selection predictions, computed metrics, and a checked score. The baseline predicts the training median for every selection row. A valid run need not outperform another model; it establishes a measurable starting point.

The agent creates an environment from requirements.txt. Python 3.12 is the authoring target. The package requires file access and command execution. No native skill loader, API key, GPU, internet model service, or scheduler is used by its runtime.

Agent entry points are run.py prepare, run.py run, and evaluate.py. Preparation needs an absolute workspace and a declared budget. A run needs the same workspace, a unique candidate name, and a permitted model. evaluate.py takes the candidate directory and its experiment. The agent must record exact commands for your machine, including its Python path. Do not copy the author's absolute paths as your setup.

Read [workflow and boundaries](WORKFLOW.md), [recovery](RECOVERY.md), and [the larger-job plan](SCALE-PLAN.md). Tests are provided in test_guards.py; they inspect deliberately altered copies and a labelled failure stub. They do not train extra models. This package does not claim universal agent compatibility or a tested cluster adapter.
