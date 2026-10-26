# Glossary

Plain-language definitions, examples, and distinctions for RSI and related concepts.

---

## A

**Agent**: A system that uses a language model to execute tasks via tools. In this course, the agent writes code and configuration while you provide natural-language instructions.

**Ablation**: Removing one component from a system to test whether it contributed to the observed benefit. An ablation that removes a domain check and observes performance drop indicates the check matters.

---

## B

**Baseline**: A simple starting point for comparison. In this course, a constant-prediction baseline establishes the minimum performance a useful model must exceed.

**Budget**: A limit on resources (time, compute, attempts). Bounded loops require explicit budgets to prevent unlimited work.

---

## C

**Capstone**: A final project that demonstrates course concepts. The five capstones require building, transferring, auditing, and explaining a complete experiment with evidence.

**Conditional memory**: Memory that distinguishes resolved findings from unresolved problems. Used in AReaL-RSI to avoid re-investigating settled questions.

---

## D

**Data leakage**: Using information from the test set during training or feature selection. Leakage produces unrealistically good scores that do not generalize.

**Dependency**: A relationship where one action must complete before another can begin. Dependencies explain why a workflow has a particular order.

---

## E

**Evaluation**: The process of measuring performance on a held-out test set. Evaluation must use a frozen final partition to be valid.

**Evidence**: Records that support a claim. Evidence includes predictions, data roles, metrics, and traces. A claim without evidence is an assertion, not a result.

---

## F

**Feedback**: Information from a previous run that guides the next attempt. Feedback must change behavior to be useful.

**Fixed improver**: An improver that does not change between rounds. Used as a baseline for comparing revised improversers.

---

## G

**Graph**: A representation of dependencies, branches, and recovery paths. Graphs make different failure routes explicit.

---

## H

**Harness**: A system that organizes execution: instructions, tools, state, checks, and limits. A meta-harness generates a harness from a brief.

**Held-out set**: Test data that is never used during training or improvement. The held-out set provides the final evaluation boundary.

---

## I

**Improver**: A procedure that proposes and evaluates changes to a research skill. Recursive self-improvement revises the improver itself.

**Inheritance**: When a revised improver generates the next improver. I0 generates I1, both generate researchers—a two-generation comparison tests inheritance.

---

## L

**Loop**: Repeated execution with state, feedback, and a stopping rule. Loops require budgets to avoid unlimited work.

---

## M

**Meta-harness**: A procedure that generates a harness from a task brief. The meta-harness does not run experiments; it produces a system that does.

**Mechanism**: The specific way a system achieves its result. Understanding mechanism requires inspecting code, configuration, and traces, not just reading headlines.

---

## O

**Ontology**: A shared vocabulary of named objects, relations, and invariants. An ontology prevents ambiguity about what "score" or "model" means in a given context.

---

## P

**Partition**: A division of data into training, selection, and final sets. Partitions must be frozen to prevent leakage.

**Procedure**: A repeatable sequence of actions. In this course, procedures are packaged as skills.

---

## Q

**Quiz**: A check for understanding. Each lab ends with a quiz that tests the key concept. Attempt the quiz before reading the answer.

---

## R

**Recursive self-improvement (RSI)**: A system where the improver itself is revised, and the revision governs later improvement work. RSI requires: (1) a revised improver, (2) the revision is inherited, (3) a fair comparison shows the revision helps.

**Research skill**: A procedure that conducts experiments. Editing a research skill changes how experiments are done, but does not by itself demonstrate RSI.

**RSI-Index**: A metric from RSIGym that measures the mean fraction of remaining performance gap closed across benchmarks.

---

## S

**Self-* family**: Correction, learning, organization, emergence, and modification. These are distinct mechanisms; not all are recursive self-improvement.

**Self-play**: An agent improving against its own history. Self-play improves a policy but does not necessarily improve the improvement procedure.

**Steering split**: A subset of test instances used for scoring and selection before final evaluation. Used in Budget RSI to avoid contaminating the held-out set.

**Skill**: A Markdown procedure that an agent can execute. Skills make intended behavior explicit and reusable.

---

## T

**Task model**: The fitted parameters or architecture that makes predictions. Changing the task model is improvement, not necessarily RSI.

**Trace**: A record of what actually happened during execution. Traces reveal whether the intended workflow was followed.

---

## V

**Vocabulary**: A set of named entities with agreed-upon meanings. A shared vocabulary prevents semantic contradictions.

---

## Common Confusions

**Self-play vs. self-improvement**: Self-play improves a policy; self-improvement revises the improver. Tic-tac-toe self-play is not RSI.

**Memory vs. learning**: Memory stores successful choices; learning changes the procedure itself. A skill that retrieves past configurations is memory, not learning.

**Organization vs. emergence**: Organization is fixed coordination; emergence is unpredicted global behavior from simple local rules.

**Meta-harness vs. RSI**: A meta-harness generates a harness; RSI revises the improver. Meta-harness generation is not by itself RSI.

---

## October 2026 Paper Terms

**Budget RSI**: Scoring code edits before full evaluation using a linear readout on a steering split.

**SO-RSI**: Second-order diagnostic inquiry that investigates WHY failures occur before patching.

**AReaL-RSI**: Adaptive scaling with leader agents and conditional memory sharing.

**RSIFlow**: Adaptive workflow orchestration with an evolving meta-agent.

**RSIGym**: An EaaS-based research environment with RSI-Index metric.

**Self-HPO**: Alternating harness and policy optimization.

**SwarmRSI**: Scientific agent swarms with mutation and recombination.

**R2Orch**: Agent orchestration via self-play within a skill-internalization loop.

**Terminal-RSI**: Recursive self-improving terminal agents with recursive self-rewrite and policy-refine.
