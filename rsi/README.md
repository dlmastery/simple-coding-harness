# From one ML experiment to recursive self-improvement

You ask a coding agent to predict hourly bike demand. It trains a model and reports an error. You inspect the mistakes and ask it to try a better idea.

That is useful. It is also ordinary model improvement.

Now save the procedure that chooses experiments. Test a change to that procedure. Later, let the system revise the procedure that proposes and evaluates those changes. Make the next round use the revision. Compare what the old and new procedures can improve under the same conditions.

This course builds that distinction slowly. You begin with one understandable prediction and finish with an inspectable, bounded experiment in recursive self-improvement, or RSI. A successful final project can report a gain, a regression, or an inconclusive result. Its evidence must support its conclusion.

**Begin with [Start here](START-HERE.md).** You use ordinary language and Markdown. The coding agent writes the code, configuration, tests, and launch files.

## The project you will build

The main task is small enough for local CPU experiments: estimate bike rentals from calendar fields and observed weather. Later, transfer the research procedure to wine-quality classification.

![Observed bike demand by hour, with morning and afternoon peaks](evidence/2026-09-20/author-bike/data-overview.png)

*A chart from the pinned teaching data. A constant prediction misses the daily pattern. This gives you a concrete reason to improve the model. The chart describes public data; it is not evidence of forecast accuracy.*

You will follow the full data science process: frame a question, inspect data, prevent leakage, define partitions, fit baselines, test features and models, examine errors, compare candidates, and report limits. The task stays familiar while the research process becomes more capable.

The **task model** is a small regressor or classifier trained on your laptop. The **coding agent’s language model** reads instructions and operates tools. Editing a skill changes the agent’s external procedure. It does not train that language model’s weights.

## Your role and the agent’s role

| You | The coding agent |
|---|---|
| Read the question and predict an outcome | Prepare the workspace and check capabilities |
| Give a short natural-language instruction | Generate and run code and configuration |
| Inspect the actual report, plot, and failure | Preserve predictions, versions, costs, and traces |
| Explain why a result supports a claim | Offer hints and show the relevant evidence |
| Assess the explanation and its limits | Apply the declared checks and stopping rules |

You do not need to type Python, JSON, YAML, or scheduler syntax. The implementation remains available to inspect. Hiding syntax does not mean hiding scientific decisions.

## Follow one learning path

| Theme | The question you will answer |
|---|---|
| [00 · Start here](00_start_here/README.md) | What does one valid prediction and its evidence look like? |
| [01 · A process without loops](01_process_without_loops/README.md) | Can I run and reuse a fixed data science procedure? |
| [02 · Loop engineering](02_loop_engineering/README.md) | When should I repeat, what should change, and when should I stop? |
| [03 · Graph engineering](03_graph_engineering/README.md) | Which actions depend on others, and how should failures take different routes? |
| [04 · Ontology engineering](04_ontology_engineering/README.md) | Do data, models, metrics, and evidence have the intended meaning? |
| [05 · System intelligence](05_system_intelligence/README.md) | What capability comes from coordinating fixed components? |
| [06 · Meta-harness engineering](06_meta_harness_engineering/README.md) | Can a readable brief generate a runnable research harness? |
| [07 · The self-* family](07_understanding_self_star/README.md) | How do correction, learning, organization, emergence, and modification differ? |
| [08 · Measuring improvement](08_measuring_improvement/README.md) | Is the apparent gain real, transferable, and fairly measured? |
| [09 · Recursive self-improvement](09_recursive_self_improvement/README.md) | Does a revised improvement procedure govern later work, and does it help? |
| [10 · Research studio](10_research_studio/README.md) | How do recent systems implement and evaluate these mechanisms? |
| [11 · Capstones](11_capstones/README.md) | Can I build, transfer, audit, and explain a complete experiment? |

The [course map](COURSE-MAP.md) links 101 authored lessons. The research studio has 38 labs in 13 themed subdirectories, including Dream-RSI, RSIAgent, ModularRSI, AIDE², ScientistTwo, ScienceBuddy, MetaRSI, and HarnessEvolve. Five capstones connect the ideas to independent work. Written coverage and completed execution validation are tracked separately.

Each lab explains the purpose, starting state, run prompts, expected observations, checks, and recovery. It ends with key takeaways, an explained quiz, and a next step. The tutor pauses for your prediction and interpretation.

## Before you start

This is an advanced AI/ML course that starts from no RSI knowledge. Familiarity with tables, training, prediction, and error will help. New agent terms enter through examples. The [glossary](GLOSSARY.md) gives definitions and counterexamples.

The default path uses small datasets and CPU models. No GPU or foundation-model training is required. Initial dependency installation needs internet access. A hosted coding agent can require an account and paid inference. Agent costs are additional to the local fit budget unless measured.

An 8 GB laptop is a design target, not yet a measured minimum. The [execution record](evidence/2026-09-20/README.md) gives the tested environment and limits. [Agent adapters](adapters/README.md) distinguish the portable file-reading route from native integrations that need testing.

## Keep the evidence honest

A retry is not automatically learning. A saved memory is not automatically useful. A better task model does not automatically imply a better researcher. A meta-harness that generates a harness is not automatically RSI.

The supplied data is public. Fixed training, selection, and final partitions teach evaluation discipline, but do not hide cases from a host agent that can read the repository. A stronger independent evaluation requires a separate access boundary.

Current research discovery covers the preceding month, with priority given to the latest two weeks. The [research inventory](../how-did-i-generate-it/rsi/RSI-RESEARCH-SWEEP.md) records dates, reading depth, corrections, and access gaps. Older requested foundations remain explicitly dated. A classroom adaptation does not reproduce a paper’s headline result.

## Continue beyond the laptop

The scientific contract stays separate from compute. A larger experiment still needs a task brief, data version, candidate, evaluator, improvement procedure, and run record. The [scale skill](skills/scale-experiment/SKILL.md) lets an agent generate GPU or cluster setup while preserving those interfaces.

Larger jobs add checkpoints, cancellation, resumption, job identities, bounded concurrency, and resource accounting. A generated cluster configuration is not a tested backend. Optional larger-compute paths need validation on the actual hardware.

## For students and instructors

Work through the first themes in order. Keep one short lab note: prediction, observation, explanation, and remaining uncertainty. Attempt the quiz before opening the answers. When you return, ask the tutor to read your progress file.

Use the [instructor guide](instructor/README.md) to choose checkpoints and assess explanations. The complete [course-authoring skill](../skills/build-research-codelabs/SKILL.md) preserves the method for diffusion models, flow methods, or another complex topic.

This branch is a work in progress. Written lessons, executed checks, learner validation, research review, and illustration review have separate status. Requested illustration-generator access remains unresolved; measured data charts are included. The [development record](../how-did-i-generate-it/rsi/README.md) retains plans, intermediate artifacts, checks, and GitHub checkpoints.
