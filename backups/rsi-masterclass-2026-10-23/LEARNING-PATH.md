# Work through the masterclass

[Course](README.md) · [Every lab](COURSE-MAP.md) · [Start here](START-HERE.md)

This path explains how the ideas build on each other. For session planning, use the [teaching roadmap](TEACHING-ROADMAP.md). For definitions and worked examples, use the [glossary](GLOSSARY.md).

The full path contains 101 lessons. Treat it as a sequence of short investigations, not a single coding session. Each block ends with an explanation you should be able to give from your own artifacts. If that explanation is unclear, revisit the named experiment before adding another mechanism.

## 1. Make one experiment trustworthy

Complete [theme 00](00_start_here/README.md), then [theme 01](01_process_without_loops/README.md). Begin with the meaning of one data row. Fix the question, run a simple baseline, check its predictions, write the process, and save that process as a skill.

**Checkpoint:** Open one saved prediction and explain the target, allowed inputs, row's partition, error, and how it contributes to the reported metric. Then show the procedure that would repeat the run without relying on chat history.

Keep your task brief, capability report, checked baseline, process, learner-owned skill, and handoff. The next block needs those objects, not only the final score.

## 2. Control repeated work and its meaning

Complete [loops](02_loop_engineering/README.md), [graphs](03_graph_engineering/README.md), and [ontology](04_ontology_engineering/README.md). A weak result motivates a change. A budget bounds the search. A graph routes different failures. Domain rules check whether the objects and measurements mean what the experiment assumes.

**Checkpoint:** Explain why a leaked input must stop before fitting, why missing evidence takes a different route from a pass, and why restarting a process does not restore spent attempts. Use an actual refusal and a preserved checkpoint.

Keep the candidate ledger, feedback and decision notes, workflow, domain facts, failure examples, and impact report. A correct route can still carry invalid information; you need both kinds of check.

## 3. Build a system, then a builder

Complete [system intelligence](05_system_intelligence/README.md) and [meta-harness engineering](06_meta_harness_engineering/README.md). First coordinate fixed components. Then describe their contract clearly enough for an agent to generate a runnable harness. Transfer from bike regression to wine classification.

**Checkpoint:** Point to the builder, the brief, the generated package, and an actual execution. Explain which changed between tasks. Show a refusal from the generated harness, not merely a sentence promising that it rejects invalid work.

Keep both task briefs, generated packages, tests, execution records, and generation identities. A working generator is an achievement; it does not yet show that the generator improved.

## 4. Distinguish adaptation from recursive improvement

Complete [the self-* family](07_understanding_self_star/README.md), [measurement](08_measuring_improvement/README.md), and [RSI](09_recursive_self_improvement/README.md). Observe correction, persistent memory, skill changes, organization, and modification separately. Then compare a changed improvement procedure with its predecessor.

**Checkpoint:** Trace a versioned improver revision into a later decision. Distinguish that evidence of use from evidence of benefit. Name the starting state, candidate budget, held-fixed evaluator, rejected edits, context boundary, and missing costs.

Keep ancestry and both successful and harmful changes. A zero gain or regression is a valid result. An acceleration claim requires more than a short upward sequence of scores.

## 5. Read current systems through their mechanisms

Work through all groups in [the research studio](10_research_studio/README.md). Read the framework and announcement audits first. Continue through exploration and memory, Dream-RSI, modular evolution, AIDE², meta-skills, ScientistTwo, ScienceBuddy, and the later comparisons.

For each source, identify what changes, what persists, what is fixed, and how the authors evaluate it. Read the activity label before running the lab: a replay, simulation, calculation, or claim audit makes a different kind of evidence from a source-faithful reproduction.

**Checkpoint:** Explain one paper's method using your local exercise, then name three differences that prevent your exercise from establishing the paper's headline result. Show the primary source and the actual local outputs.

Large-model training is an optional extension with its own compute and evidence plan. The required lessons retain a laptop path.

## 6. Transfer, audit, and teach

Complete all [capstones](11_capstones/README.md). Build a harness for a new task, run a bounded recursive experiment, inspect portability, audit another result, and teach the mechanism back.

**Checkpoint:** Another reader can find the task, reproduce a small run, inspect a failed proposal, and understand the strongest claim your evidence supports. A student's explanation and a successful tool run are separate outcomes; both matter.

The [instructor guide](instructor/README.md) describes the portfolio rubric. Keep the scope small enough to inspect while preserving the complete scientific chain.

## Keep your place

Ask the tutor to save PROGRESS.md at each stop. It should name the completed step, actual experiment paths, results and failures, remaining budget, unanswered learning questions, and next action. On return, it checks the files and any active process before continuing.

New lesson notes usually get a new folder. Resuming an experiment or evaluating its frozen candidate uses that experiment's original contract and ledger. The lab states when existing state must be reused. Starting a new folder does not make previously seen final data unseen.
