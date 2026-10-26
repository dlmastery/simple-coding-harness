# Recursive self-improvement: a 6-hour masterclass (work in progress)

> **Status:** draft. The code for all ten labs is in place and passes its offline tests.
> The measured results and the lab write-ups are not in yet; they come from live runs on
> MLE-bench Lite, which are pending. The previous course is archived in
> [`backups/rsi-masterclass-2026-10-23/`](../backups/rsi-masterclass-2026-10-23/README.md).

A frozen model (`gpt-5.4-nano`) solves real Kaggle competitions from
[MLE-bench Lite](https://github.com/openai/mle-bench) through an AIDE-style
draft/debug/improve loop. Every prompt, skill and setting of that loop is a file.
An improver edits those files; a meta-improver edits the improver. Each lab adds one
technique from the 2026 literature and measures whether it helps on competitions the
improver never saw. See [PAPERS.md](PAPERS.md) for the paper-to-lab map.

| Lab | Topic | Time |
|---|---|---|
| [00](step_00_setup/) | Setup and replay mode | 15m |
| [01](step_01_one_attempt/) | One attempt: self-reported vs hidden score | 30m |
| [02](step_02_measure/) | Measurement: splits, replicas, noise band | 35m |
| [03](step_03_first_improver/) | A first improver with a trace archive (Meta-Harness) | 40m |
| [04](step_04_traces_vs_scores/) | Traces versus scores as evidence | 35m |
| [05](step_05_regularized_rsi/) | Regularized RSI: budget, critic, pruner, noise floor (RRSI, CHASE) | 50m |
| [06](step_06_pareto_and_transfer/) | Pareto profiles and model transfer (HarnessPro, MaD-RSI) | 35m |
| [07](step_07_open_world/) | Open-world improvement without a grader (Harness²) | 45m |
| [08](step_08_improve_the_improver/) | Improving the improver | 45m |
| [09](step_09_audit_and_defend/) | Audit and defend (HackProbe, harness tampering) | 30m |
