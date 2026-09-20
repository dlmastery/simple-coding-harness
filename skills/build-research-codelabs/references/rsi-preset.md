# RSI preset

Use this only for the recursive self-improvement course or a closely related request. Read the target repository's latest steering record because later user instructions can change this preset.

## Starting request

Rebuild `dlmastery/simple-coding-harness/rsi` from an unclear, flat course into a progressive masterclass. A user-supplied Grok MHTML transcript in Downloads motivated the original course but contains claims that require correction. Clone and inspect the repository and relevant source material. Paraphrase the task and show a concrete plan before replacing lessons.

The audience is an advanced AI/ML class that may know no RSI. Students use skills, tools, and natural language. Coding agents generate implementation code and configuration. The final product is a complete, illustrated, tested, gently sequenced masterclass with quizzes, lasting intuition, and full provenance.

## Required sequence

1. An ordinary process with no learner-designed retry or improvement loop.
2. Loop engineering: state, feedback, budgets, stopping, resume, and failure.
3. Graph engineering: dependencies, branches, parallel work where useful, and explicit execution paths.
4. Ontology engineering: domain concepts, types, relations, constraints, and links to evidence.
5. System intelligence: how coordinated components and information contribute to behavior; define the term explicitly.
6. A meta-harness that generates a task-specific executable harness.
7. Separate experiments for correction, reflection, learning, improvement, self-organization, emergence, self-play, and self-modification.
8. Measuring improvement, transfer, costs, and evaluation boundaries.
9. Recursive improvement: revise an improvement procedure, inherit it, use it, and compare its effectiveness.
10. Recent research mechanisms, claim audits, and capstones.

“No loops” refers to the learner-designed workflow. A coding agent or fitting algorithm can already iterate internally. Explain this early. Do not confuse a workflow graph with an ontology, persistence with effective improvement, or self-organization with emergence.

A proposer–critic exchange can illustrate interaction, but does not by itself demonstrate self-play training. Identify challenge generation, outcomes, the actual update, and retained state. Label an exercise that omits learning as an interaction analogy. For organization and emergence, compare throughput, correctness, and lateness separately; an attractive collective pattern can harm the task.

When teaching self-play learning, include an actual affordable update, such as a tabular game policy learned from terminal returns. Keep the ML regression/classification project as the main thread and explain why this small side experiment exposes the mechanism. Freeze the learned policy before evaluation, retain failures, and distinguish policy updates under a fixed trainer from changes to the training procedure. Do not substitute dialogue alone for the requested learning mechanism.

Distinguish internal selection from external evaluation. An improver may revise its own proposal-ranking or promotion rule; the external tasks, metrics, final cases, and resource protocol used to judge that revision must stay fixed for the comparison. A blanket prohibition on editing any promotion rule would prevent legitimate improver experiments and confuse the levels.

## Running ML project

Use generic tabular ML hill climbing. The concrete proposal uses UCI Bike Sharing regression and UCI Wine Quality classification. Verify source files, license, schema, row count, splits, and task definitions before implementation. These historical datasets are small teaching fixtures, not recent research releases.

Include data acquisition, EDA, quality checks, leakage, feature availability, split design, baselines, transformations, model selection, error analysis, final evaluation, and reproducibility. For Bike Sharing, component rental counts leak the total. Observed weather requires a clear prediction-time assumption. For derived Wine Quality classes, define the label rule before evaluation and inspect imbalance and duplicates.

Begin with one fixed baseline. Later add bounded candidate proposals and selection. Ordinary feature and hyperparameter search is not sufficient evidence of RSI. The later target is the research skill or improvement procedure. A successor must use the retained procedure to produce further improvements.

Use small CPU models for required activities. Preserve compute adapters and evidence contracts for larger tabular jobs, neural models, GPUs, clusters, and genuine model–harness training extensions. State resource budgets and fairness of comparisons.

## Required research coverage

The original research cutoff was 19 September 2026, with a one-month search window. Refresh that window for a new run. Keep user-required older work dated separately.

Explicit requested sources include:

- [The Last AI Built by Humans](https://arxiv.org/abs/2609.11873).
- [AIDE²](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement).
- [Dream-RSI](https://arxiv.org/abs/2609.14858).
- [ScientistTwo](https://arxiv.org/abs/2609.19644).
- [ScienceBuddy](https://arxiv.org/abs/2609.17523).
- [RSIAgent](https://arxiv.org/abs/2609.15364).

Include ModularRSI and broaden the sweep beyond this seed list. Relevant families include harness evolution, procedural graphs, skill libraries, memory, exploration, feedback design, model–harness compatibility, research benchmarks, and economics. Search frontier labs and original Meta/FAIR researcher posts as well as arXiv.

Give named systems substantial advanced lessons. Explain hypotheses, ablations, peer review, GRPO, and domain terms just before students need them. Use affordable mechanism exercises and larger-compute extensions. Do not equate a small demonstration with a full scientific reproduction.

## Claim checks that must survive the rewrite

- AIDE²'s level numbering is separate from the survey's autonomy scale. Check its ignition evidence separately from inner-loop improvement.
- Dream-RSI replays the realized discovery space. Replay coverage and later online confirmation matter. Verify current code-release status.
- RSIAgent's verifier checks outcomes; the actor owns memory updates. Check the paper's actual protocol rather than copying the old lesson's role assignments.
- ScientistTwo's automated review scores are not human conference acceptance decisions. Improving a research result does not alone establish an improved researcher.
- ScienceBuddy couples harness changes with model updates. Distinguish real human interactions, simulated feedback, and training rewards. A fixed reflector does not automatically become a better improver.
- Skill or memory growth can harm performance. Harness/model updates can interfere. Teach failures and negative transfer alongside success reports.

For every RSI claim identify what changes, what is inherited, which component performs the next improvement, what remains fixed, and what independent evidence supports effectiveness. Structural recursion, effective improvement, and sustained acceleration are different claims.

## Provenance and style

Use themed directories and the full course standard. The current plan's counts are provisional, not a template requirement. Record all instructions and accepted changes in the project steering file.

Keep plans, intermediate artifacts, source corrections, illustration prompts and revisions, run records, and validations under `how-did-i-generate-it/rsi/`. Commit and push to the authorized GitHub branch at meaningful milestones. Verify the remote checkpoint. Preserve sensitive source material through an appropriate redacted copy and manifest.
