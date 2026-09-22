# 10.12 · Compare agent evolution and improver evolution

[Course](../../../README.md) · [Theme](../../README.md)

**You are here:** Theme 10, Research studio → lab 12 of 38. [Find this theme in the course map](../../../COURSE-MAP.md#theme-10) · [Whole-course mindmap](../../../COURSE-MAP.md#whole-course-mindmap).

## What you will build

A lineage audit distinguishing changed agent code from changed improvement procedure.

## Why this matters

A family tree of increasingly capable agents can still leave the operator that creates descendants fixed.

## Before you start

Complete [10.11: Integrate edits and test transfer](../step_11_integrate/README.md). You need the concepts and the reports named below, not its old chat. If you start here directly, ask the tutor to prepare the listed starting state and explain the missing prerequisite first.

Open the coding agent at the repository root. Read [the tutor skill](../../../skills/rsi-tutor/SKILL.md) and this lab's [brief](BRIEF.md). The agent keeps this lab's notes in <code>rsi-work/10-12</code>, outside the repository, and reports the absolute path. If the lab continues an earlier experiment, keep that experiment in its original workspace with its existing budget and locks. A new notes folder does not reset an experiment. The agent checks local Python and the [tool requirements](../../../tools/README.md) before execution. You do not write code or configuration.

**Starting state:** Your local lineage and the primary historical method descriptions. Verify the DGM primary source before making detailed claims.

**Budget:** No fits. Audit two source diagrams and one local lineage. Plan about 40–60 minutes of reading and discussion; this is an author estimate, not a measured student duration. Coding-agent inference may use a paid online service. Record its cost separately when available.

## How it works

For every edge, ask which artifact changed and who produced the change. Then ask whether an altered improvement operator is inherited and used. Do not infer improver evolution merely from a system’s name or from multiple generations of agent code. DGM reuses evolved coding agents to make later code changes, so a generic fixed-operator cartoon does not describe its full mechanism. HyperAgents explicitly makes task-agent and meta-agent procedures editable. Inspect each source’s changed surfaces and later use before judging whether its improvement process improved.

**A concrete example.** The [typed local audit](../../../evidence/2026-09-21/modular-labs/README.md#name-the-procedure-on-each-lineage-edge) checked eight proposal rows against retained versions and before-action records. The task skill improved, but both improver proposals were rejected and the next generation still used the original rule. The separate source maps explain why a paper name or a family-tree shape cannot replace inspection of which procedure changed and was later used. The [later source-composition audit](../../../evidence/2026-09-22/tabular-comparison/composition/README.md) finds two parent/harness pairs whose candidate source differs but whose complete estimator settings match. A later capacity assignment overwrites the template edit. An ancestry edge proves which source was inherited; inspect effective behavior before attributing a performance change.

![One generic lineage changes task-agent versions under the same operator O0. Another shows O0 producing proposed O1, which governs a later A1-to-A2 change. A blank ledger asks for separate DGM, HyperAgents, and local evidence.](../../../assets/illustrations/agent-and-improver-lineages-v1.png)

*A0, A1, and A2 identify agent versions, not scores or task conditions. The two strips illustrate possibilities; neither is assigned to DGM or HyperAgents. DGM reuses evolving coding agents for self-modification, so labelling it a fixed-operator system from this cartoon would be misleading. In the lower example, later use of O1 needs an actual trace; improved effectiveness needs an additional fair comparison. Read each original source and record which procedure, code, model, and evaluation components remain fixed.*

[Open the illustration at full size](../../../assets/illustrations/agent-and-improver-lineages-v1.png).

<details>
<summary>See the step diagram</summary>

![A lineage must identify what each child changes. Agent changes and changes to the agent’s updater support different claims.](../../../assets/diagrams/lab-10-12.png)

*Read the diagram:* A lineage must identify what each child changes. Agent changes and changes to the agent’s updater support different claims.

</details>

## Run the lab

Start with this prompt. The tutor pauses for your prediction before it runs the next step.

```text
Read rsi/AGENTS.md and
rsi/skills/rsi-tutor/SKILL.md.
Guide me through lab 10.12, Compare agent
evolution and improver evolution, one step
at a time.
Read its README and BRIEF. Prepare its
separate workspace.
You write and run the implementation. Keep
the reports and failures.
Ask me to predict the result before the
experiment.
```

**Make a prediction:** Could every node in an agent family tree be different while the improver stays identical?

### 1. Read the original mechanisms

Avoid relying on secondary labels.

```text
Use audit-rsi-claim to inspect the primary
DGM and HyperAgents method descriptions.
Record mutable surfaces, parent selection,
evaluation, and inheritance. Mark any
inaccessible detail unresolved.
```

**Observe:** The comparison is source-specific.

### 2. Map your lineage

Apply the same questions locally.

```text
Annotate each edge in your solver and
improver lineage with the changed artifact
and the procedure that generated it.
Identify which edges support structural
recursion.
```

**Observe:** Agent evolution and improver evolution can be distinguished.

## Check your result

Every historical technical assertion has a primary citation. The local classification is based on actual versions and traces.

### Open these outputs

The agent keeps these in your lab workspace or records the original experiment path when reusing evidence.

| Output | What to inspect |
|---|---|
| Two primary-source mechanism maps | Cite changed surfaces, parent selection, evaluation, and inheritance for each historical work. |
| Typed local lineage | Names both the changed object and the procedure used on each edge. |
| Claim comparison | Separates ancestry, operator inheritance, and measured effectiveness. |

Ask the agent to open the actual files and show the command exit status. A written description of a run is not a run. Keep a short <code>LAB-NOTE.md</code> with your prediction, measured observation, explanation, and one limit. The tutor must mark skipped learner responses as skipped.

## Try one change

Erase the improver-version column and explain which conclusions become ambiguous.

## If something goes wrong

If the source is inaccessible, leave its specific mechanism unresolved instead of substituting a third-party label. These named historical foundations are dated exceptions to the recent discovery window. If the local operator version is missing, the family tree cannot establish that the operator evolved.

Say “Stop this lab” to stop further work. Ask the agent to save <code>PROGRESS.md</code> with the last completed step and remaining budget. To resume, have it read that file and inspect active processes first. A reset creates a new sibling workspace; it does not erase failures or alter the source data. See the [recovery rules](../../../tools/README.md) for interrupted tool runs.

## Key takeaways

- A lineage needs typed changes.
- Repeated agent evolution can use a fixed operator.
- Inherited procedural change requires its own evidence.

## Research connection

[HyperAgents](https://ai.meta.com/research/publications/hyperagents/), Meta research, March 2026, and [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954), Jenny Zhang and colleagues, first submitted 29 May 2025 and revised 12 March 2026. These are older foundations.

**Activity type: source audit.** You inspect and compare evidence from primary sources. This activity does not execute or reproduce the paper’s system.

## Check your understanding

Answer before opening the explanation. You can ask the tutor for a hint.

1. What does a family tree alone show?
2. Why track the operator on each edge?
3. Can source terminology replace inspection?
4. What remains necessary for effective RSI?

<details>
<summary>Hint</summary>

Read an edge as “procedure P produced child C from parent B.” Then ask whether P itself changes and is used later.

</details>

<details>
<summary>Explained answers</summary>

1. Ancestry among recorded versions, not necessarily what kind of component changed.

2. It identifies how descendants were produced and whether that method changed.

3. No. Similar names can describe different mutable surfaces.

4. A fair comparison showing that the inherited procedure improves later improvement work.

</details>

## What's next

Study a nested ML researcher and its outer improvement process. Continue to [10.13: Inspect an inner ML researcher](../../04_aide2/step_13_inner_research/README.md).
