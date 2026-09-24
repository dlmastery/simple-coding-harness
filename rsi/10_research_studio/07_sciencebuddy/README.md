# ScienceBuddy: feedback, harness changes, and weight learning

[Research studio](../README.md) · [Course](../../README.md)

**You are here:** Theme 10 → research group 07 of 00–12 → labs 10.22–10.26. [Studio overview and mindmap](../README.md) · [Whole-course map](../../COURSE-MAP.md#theme-10).

Start with a labelled correction about the wine report. Turn it into a rubric and revise the reporting skill. Then inspect grouped rewards numerically, simulate model–harness interactions, and audit the paper’s reported metrics. Each activity states whether it is execution, arithmetic, simulation, or source review.

![Versioned pairs progress from H0 with M0 to H1 with M0, then H1 with M1. The first change edits harness instructions; the second updates model parameters. Training evidence goes to the update, while held-out cases remain in external evaluation.](../../assets/illustrations/model-harness-v4.png)

*Track both versions because a harness and model can interact. First hold M0 fixed while changing the harness; then hold H1 fixed while changing weights. Keep training evidence separate from the cases used for the declared external comparison, and do not feed final results back into selection. This lab illustrates pair accounting with synthetic scores. It does not train an LLM or reproduce ScienceBuddy’s reported gains.*

[Open the illustration at full size](../../assets/illustrations/model-harness-v4.png).

Point to the object that changes in each transition. A new instruction notebook leaves model weights unchanged; a parameter update changes the model. Our required labs explain the latter with arithmetic and synthetic pair records. They do not train the scientific language model in the paper.

**Start with:** Bring wine predictions and the distinction between external skills and model parameters. The required path does not train an LLM; larger training needs its own source-aligned plan.

- [10.22 · Turn a researcher correction into a task](step_22_human_task/README.md): A task and rubric derived from a labelled researcher-request fixture.
- [10.23 · Adapt the harness to the rubric](step_23_harness_adaptation/README.md): A reporting-skill revision that responds to the rubric without changing model weights.
- [10.24 · See what grouped rewards contribute](step_24_grpo/README.md): A tiny numerical grouped-reward update illustration with an explicit limit statement.
- [10.25 · Track model–harness pairs across cycles](step_25_coevolution/README.md): A version table and a small labelled simulation of alternating model and harness changes.
- [10.26 · Read the ScienceBuddy results precisely](step_26_audit_results/README.md): A result audit that separates single-attempt accuracy, multi-attempt coverage, and feedback provenance.

**Carry forward:** Keep rubric verdicts, skill versions, the numerical update, pair records, and a source-scoped result audit. Do not combine synthetic values, local measurements, and paper results into one score.

Read the source connection in each lab. The required path fits a laptop; actual large-model training is an optional, separately planned extension.
