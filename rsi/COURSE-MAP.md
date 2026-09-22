# Your route through the RSI masterclass

[Course](README.md) · [Start here](START-HERE.md) · [Intent, skills, and authoring sources](SOURCE-ARTIFACTS.md)

Start with one bike-demand prediction. Make its evidence trustworthy. Then add a reason for another experiment, rules for choosing the next action, and a way to preserve useful work. Only after those ideas are clear do you change the research procedure—and then the procedure that improves it.

This guide explains the full 101-lab route. It is also a place to return when a new term obscures the purpose of the next step. The numbered themes give reading order; the mindmap shows how the ideas belong together. Your position in the course is not a claim that earlier experiments succeeded.

<a id="whole-course-mindmap"></a>

## The whole course

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](assets/illustrations/course-mindmap-v2.png).

The destination is the research studio and the capstones. The earlier themes give you the vocabulary, tools, and judgment to inspect those systems instead of treating their names or headline scores as explanations.

## Objectives

By the end, you should be able to:

- Build and inspect a complete small ML experiment, from the question and data to a checked result.
- Design bounded loops, dependency graphs, domain rules, and reliable recovery.
- Use skills to have a coding agent generate and operate a research harness.
- Distinguish self-* mechanisms, harness generation, and recursive improvement.
- Test whether a changed research procedure helps under a fair comparison.
- Read current research, explain its mechanism, and state what a laptop adaptation preserves.
- Build, transfer, audit, and teach a bounded project with an honest conclusion.

## Prerequisites and time

You need basic ML familiarity: tables, features and targets, training versus evaluation, and prediction error. No RSI, agent-harness, cluster, or infrastructure background is assumed. Students give natural-language instructions; the agent writes code and configuration. Use a coding agent with file and command access, a laptop for CPU experiments, and internet access for setup and research reading. Hosted-agent charges are separate.

The current per-lab author estimates sum to **49.8–82.0 hours** of reading and guided discussion. They are planning estimates, not measured learner durations. Allow additional time for setup, debugging, deeper paper reading, independent capstone work, and optional larger jobs.

| Part | Scope | Current author estimate |
|---|---|---|
| Foundations through RSI | Themes 00–09, 58 labs | 19.5–34.0 hours |
| Research studio | Theme 10, 38 labs | 25.3–38.0 hours |
| Capstones | Theme 11, 5 labs | 5.0–10.0 hours |

Each lab includes an explained quiz and a next step. Attempt the quiz and explain one new case before continuing. A short workshop may stop after theme 02; that route teaches dependable ML loops and does not reach the full RSI outcome.

## Find your theme

| Theme | New capability | Labs |
|---|---|---|
| [00 · Start with a prediction](#theme-00) | One experiment | 4 |
| [01 · Make one process dependable](#theme-01) | One experiment | 5 |
| [02 · Repeat for a reason](#theme-02) | Dependable workflows | 6 |
| [03 · Give different cases different routes](#theme-03) | Dependable workflows | 6 |
| [04 · Agree on what the experiment means](#theme-04) | Dependable workflows | 5 |
| [05 · Build capability around the model](#theme-05) | A system and its builder | 5 |
| [06 · Generate a harness from a brief](#theme-06) | A system and its builder | 6 |
| [07 · Separate the self-* ideas](#theme-07) | Changes and their evidence | 8 |
| [08 · Measure what improved](#theme-08) | Changes and their evidence | 6 |
| [09 · Improve the improvement procedure](#theme-09) | Changes and their evidence | 7 |
| [10 · Read and rebuild recent research](#theme-10) | Research studio | 38 |
| [11 · Build, transfer, and explain](#theme-11) | Capstones | 5 |

<a id="theme-00"></a>

## 00 · Start with a prediction

**Your place:** One experiment. 4 labs; 1.3–2.3 hours of planned reading and discussion. [Open the theme](00_start_here/README.md).

A bike service wants an estimate of hourly demand. Before building an improving agent, learn to tell an executed prediction from a convincing description.

You need basic familiarity with tables and prediction error. You do not need RSI, agent, or infrastructure experience.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 00.01 | [Meet the prediction task](00_start_here/step_01_meet_the_task/README.md) | An agent can optimize the wrong task very efficiently. First make the question concrete. A task brief that says what one prediction means and which inputs are available. |
| 00.02 | [Prepare a workspace you can inspect](00_start_here/step_02_prepare_the_workspace/README.md) | “I can run this” is a claim. A small successful command supplies evidence for it. A separate learner workspace, a capability report, and a verified data report. |
| 00.03 | [Run one baseline](00_start_here/step_03_one_attempt/README.md) | Before asking whether a system improved, you need a clear starting result. A real constant-prediction baseline with a measured error and saved predictions. |
| 00.04 | [Check the evidence behind the answer](00_start_here/step_04_check_the_evidence/README.md) | A polished report can describe a run that never happened or claim more than the run establishes. A short evidence report that ties a claim to predictions, data roles, and a reproducible calculation. |

**Ready to continue when:** Explain one prediction: its target, permitted inputs, partition, and checked error. Identify a feature that would leak the answer.

The next theme turns these checked actions into a repeatable process.

[Next theme: 01](#theme-01) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-01"></a>

## 01 · Make one process dependable

**Your place:** One experiment. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](01_process_without_loops/README.md).

You can inspect an agent’s output. Now make the actions behind it explicit and repeatable. Run a simple data science process once, then package it as a skill.

The process stays fixed. “No loops” means no learner-designed search or revision loop. The coding agent and numerical libraries can still have internal iterations.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 01.01 | [Write the data science process](01_process_without_loops/step_01_describe_the_process/README.md) | An implicit process is hard to inspect. Writing its dependencies exposes missing decisions. A five-action process from task framing to a checked baseline report. |
| 01.02 | [Run the process without changing it](01_process_without_loops/step_02_run_the_process/README.md) | A written sequence may omit setup or depend on forgotten state. A fresh run exposes those gaps. A clean-start execution trace for the fixed bike baseline process. |
| 01.03 | [Turn the process into a skill](01_process_without_loops/step_03_make_a_skill/README.md) | A chat history is a poor substitute for a reusable procedure. A skill makes the intended behavior explicit. A short Markdown skill that runs the fixed baseline process. |
| 01.04 | [Check outputs with a separate calculation](01_process_without_loops/step_04_separate_the_check/README.md) | A solver’s confidence cannot substitute for measuring its output. An output checker that derives error from prediction rows and rejects a mismatch. |
| 01.05 | [Reuse the skill in a fresh session](01_process_without_loops/step_05_reuse_the_skill/README.md) | A process that depends on unrecorded chat details is fragile. Persistence should be visible in artifacts. A handoff that another session can execute from files alone. |

**Ready to continue when:** Show a readable fixed procedure, an actual checked baseline, and enough saved context for another session to repeat it.

A repeatable process gives you a useful starting point. The next theme asks what to do when that process produces a weak result.

[Previous theme: 00](#theme-00) · [Next theme: 02](#theme-02) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-02"></a>

## 02 · Repeat for a reason

**Your place:** Dependable workflows. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](02_loop_engineering/README.md).

A weak result invites another attempt. Repeating only helps when you know what to change, how to remember the current state, and when to stop.

Use the baseline and readable skill from the previous theme. Add feedback, state, and budgets one at a time.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 02.01 | [Let a failure motivate a second attempt](02_loop_engineering/step_01_why_repeat/README.md) | The baseline ignores the daily demand pattern. Another identical attempt cannot supply that missing relationship. A controlled comparison between a constant baseline and a calendar-based linear model. |
| 02.02 | [Give the loop state and a budget](02_loop_engineering/step_02_bounded_state/README.md) | “Keep trying until it works” leaves both resource use and success undefined. A three-attempt loop with a current candidate, best candidate, ledger, and stopping rule. |
| 02.03 | [Turn an error into a different action](02_loop_engineering/step_03_use_feedback/README.md) | Passing a score back to an agent is not enough. You need to see how the feedback affects its decision. A feedback note that causes a documented change in the next experiment. |
| 02.04 | [Stop repeated failure and oscillation](02_loop_engineering/step_04_stop_the_loop/README.md) | An agent can alternate between two ideas and describe each as progress. A ledger makes the repetition visible. A loop controller that stops on a repeated recipe, exhausted budget, or unchanged failure. |
| 02.05 | [Resume without losing the experiment](02_loop_engineering/step_05_resume/README.md) | Restarting the program should not silently restart the scientific experiment. A checkpoint and a resumed loop that retains candidate identities and spent budget. |
| 02.06 | [Compare two ways to spend the same attempts](02_loop_engineering/step_06_compare_loops/README.md) | A better final candidate can result from how attempts were chosen, not only from the model family. A small comparison between fixed retries and feedback-guided revisions. |

**Ready to continue when:** Explain why the next attempt is allowed, which feedback changes it, how much budget remains, and what stops the loop.

A loop handles repeated work. It does not explain why a data failure and an expensive model should take different routes. That calls for a graph.

[Previous theme: 01](#theme-01) · [Next theme: 03](#theme-03) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-03"></a>

## 03 · Give different cases different routes

**Your place:** Dependable workflows. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](03_graph_engineering/README.md).

A workflow is more than a numbered list. Some actions depend on others. Some can proceed independently. Some should run only after a particular failure.

You already have a bounded improvement loop. Now place it inside a graph of dependencies, branches, and recovery paths.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 03.01 | [Draw the dependencies](03_graph_engineering/step_01_dependencies/README.md) | A numbered list hides why one action must precede another. Dependencies explain that order. An execution graph for the process you already ran. |
| 03.02 | [Route different failures differently](03_graph_engineering/step_02_branch/README.md) | Trying another model cannot fix a missing target or a leaked feature. The response should match the failure. A branch that sends invalid data to repair and valid data to modeling. |
| 03.03 | [Join independent checks](03_graph_engineering/step_03_join/README.md) | One successful check must not conceal another missing or failed check. A join that waits for both a data-quality check and a resource check. |
| 03.04 | [Put a bounded retry inside the graph](03_graph_engineering/step_04_cycle/README.md) | A return arrow can hide unlimited work unless the retry state travels with it. A graph with one explicit repair cycle and a terminal failure path. |
| 03.05 | [Resume only the affected work](03_graph_engineering/step_05_recover/README.md) | Restarting everything wastes work. Reusing everything risks stale results. Dependencies tell you what must change. A recovery trace that preserves valid upstream artifacts and reruns affected descendants. |
| 03.06 | [Read the plan, data flow, and trace](03_graph_engineering/step_06_three_views/README.md) | A diagram can look correct even when execution took a different route. Three views of one run: allowed actions, artifact movement, and actual events. |

**Ready to continue when:** Trace a failure through dependencies. Recover a failed report without refitting, and identify what a changed split would invalidate.

A graph tells the agent where work goes. The next theme asks whether the objects moving through it have the right meaning.

[Previous theme: 02](#theme-02) · [Next theme: 04](#theme-04) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-04"></a>

## 04 · Agree on what the experiment means

**Your place:** Dependable workflows. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](04_ontology_engineering/README.md).

Two files can both say “score” while describing different measurements. A shared vocabulary connects the data, models, decisions, and evidence.

Begin with concrete entities and relations in Markdown. Add only the rules needed to catch a real inconsistency.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 04.01 | [Name the objects in an experiment](04_ontology_engineering/step_01_entities/README.md) | “Improve the model” is ambiguous if one speaker means fitted parameters and another means the whole agent system. A small vocabulary for data, columns, targets, partitions, models, metrics, and evidence. |
| 04.02 | [Connect data, models, and evidence](04_ontology_engineering/step_02_relations/README.md) | A list of names does not tell you which model used which data or which score supports which decision. A readable relation table describing one ML experiment. |
| 04.03 | [State rules that must always hold](04_ontology_engineering/step_03_invariants/README.md) | Correct spelling and valid file structure do not prevent target leakage or misuse of final data. Three domain invariants, each with a passing and failing example. |
| 04.04 | [Catch a plausible but invalid experiment](04_ontology_engineering/step_04_catch_contradictions/README.md) | A realistic mistake combines several reasonable-looking facts. The rules must connect them. A semantic failure report and a corrected relation table. |
| 04.05 | [Change a definition without losing its consequences](04_ontology_engineering/step_05_evolve_vocabulary/README.md) | A harmless-looking word change can alter which inputs and results are valid. A versioned vocabulary change and an impact report for a new forecasting task. |

**Ready to continue when:** Use named objects, relations, and meaning rules to reject a plausible experiment with a wrong metric, unit, or leaked input.

You can now inspect both the route of an experiment and the meaning of its records. These become parts of a coordinated research system.

[Previous theme: 03](#theme-03) · [Next theme: 05](#theme-05) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-05"></a>

## 05 · Build capability around the model

**Your place:** A system and its builder. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](05_system_intelligence/README.md).

A useful research system combines a model with tools, state, checks, and domain knowledge. In this course, “system intelligence” means the capability of that combination.

This is a course term, not an accepted RSI level. Keep the components fixed while studying how their coordination changes results.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 05.01 | [Combine fixed components into a useful system](05_system_intelligence/step_01_combine_components/README.md) | A language model’s answer is only one part of reliable experimental work. The surrounding system determines what it can observe, execute, and verify. A fixed research workflow that uses a task skill, an ML tool, domain checks, and a report checker. |
| 05.02 | [Choose a skill for the task](05_system_intelligence/step_02_route_tasks/README.md) | A metric or model that fits one task can be wrong for another. Reuse should preserve meaning. A router that sends bike regression and wine classification to suitable fixed procedures. |
| 05.03 | [Retrieve what matters and retain task state](05_system_intelligence/step_03_context_and_state/README.md) | More text can add contradictions and stale instructions. Useful context is selected for a decision. A context packet that separates task rules, relevant knowledge, and current execution state. |
| 05.04 | [Coordinate planning, execution, and checking](05_system_intelligence/step_04_coordinate/README.md) | Good individual tools can still produce a weak system if nobody checks their handoffs. A coordinator that advances work only when the required artifacts and checks are present. |
| 05.05 | [Find which component makes the difference](05_system_intelligence/step_05_ablate_system/README.md) | A successful full system does not reveal which component caused the benefit. An ablation that compares the system with and without one domain check. |

**Ready to continue when:** Show a coordinator reading saved state before acting and refusing an incomplete or wrong-candidate handoff. Explain which fixed component contributes to the result.

Once you can describe a useful system, you can ask another procedure to build it from a brief.

[Previous theme: 04](#theme-04) · [Next theme: 06](#theme-06) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-06"></a>

## 06 · Generate a harness from a brief

**Your place:** A system and its builder. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](06_meta_harness_engineering/README.md).

A harness organizes execution: instructions, tools, state, checks, and limits. A meta-harness generates such a system from a task description.

You have built the parts by hand through natural language. Now the agent assembles them and proves that the result runs.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 06.01 | [Describe the harness you need](06_meta_harness_engineering/step_01_write_a_brief/README.md) | A generator needs the scientific and operating requirements, not just “make an intelligent agent.” A plain-language specification for a small bike-research harness. |
| 06.02 | [Generate a first harness](06_meta_harness_engineering/step_02_generate/README.md) | A specification is not executable until a builder turns it into tools and a workflow. A generated harness with a runnable entry point, checks, and readable instructions. |
| 06.03 | [Inspect what the builder decided](06_meta_harness_engineering/step_03_inspect_generated/README.md) | A generator can quietly invent a split, skip a check, or increase the budget. Review should expose those choices. A review that maps each important generated behavior back to the brief. |
| 06.04 | [Test the generated harness’s boundaries](06_meta_harness_engineering/step_04_test_refusal/README.md) | A system that only succeeds on valid inputs may still accept the mistakes it claims to prevent. A retained valid run and two meaningful refusals from the generated harness. |
| 06.05 | [Generate a classification harness](06_meta_harness_engineering/step_05_second_task/README.md) | A useful builder adapts scientific choices instead of copying regression labels into a new folder. A wine-classification harness generated from a revised readable brief. |
| 06.06 | [Recreate and compare generated harnesses](06_meta_harness_engineering/step_06_recreate/README.md) | A generated system that depends on hidden local state is difficult to share or evaluate. A clean-start reproducibility report for two generated harnesses. |

**Ready to continue when:** Distinguish the brief, builder, generated harness, and actual run. Show a baseline and a refusal in the generated system.

Generating a system is distinct from improving the generator. Before recursion, separate the many meanings of “self”.

[Previous theme: 05](#theme-05) · [Next theme: 07](#theme-07) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-07"></a>

## 07 · Separate the self-* ideas

**Your place:** Changes and their evidence. 8 labs; 2.8–4.8 hours of planned reading and discussion. [Open the theme](07_understanding_self_star/README.md).

Correction, reflection, learning, improvement, organization, emergence, self-play, and modification describe different properties. They can overlap; they are not interchangeable.

Most labs use the small ML workflow. Queue simulations expose organization and emergence; a tiny game exposes actual self-play learning. Ask what persists and what observation would establish a benefit.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 07.01 | [Correct one result](07_understanding_self_star/step_01_correction/README.md) | A system can repair an answer during a task without retaining any new method. A corrected experiment summary with the original mistake preserved. |
| 07.02 | [Test a reflection before trusting it](07_understanding_self_star/step_02_reflection/README.md) | A plausible story about a failure can be wrong. The story must earn its place in the procedure. A reflection that separates observation, explanation, and a proposed future rule. |
| 07.03 | [Retain and use a lesson](07_understanding_self_star/step_03_persistent_learning/README.md) | A saved lesson only matters to future behavior if a later process retrieves and uses it. A versioned memory note that changes a later decision. |
| 07.04 | [Improve a task skill with a fixed procedure](07_understanding_self_star/step_04_self_improvement/README.md) | A system can improve its solver while the method that creates improvements stays fixed. A parent and child research skill compared under one unchanged improvement procedure. |
| 07.05 | [Let work reorganize under local rules](07_understanding_self_star/step_05_organization/README.md) | A system can change its organization without changing any worker’s skill or improving its final quality. A small simulation in which queued checks redistribute between two workers. |
| 07.06 | [Observe a collective pattern](07_understanding_self_star/step_06_emergence/README.md) | “Emergent” often gets used as a synonym for impressive. Make the claimed pattern and mechanism observable. A labelled simulation that shows how a system-level pattern depends on local interactions. |
| 07.07 | [Learn what self-play does and does not provide](07_understanding_self_star/step_07_self_play/README.md) | Interaction is only one part of self-play learning. You need experience, a feedback source, a parameter update, and a way to judge the resulting policy. A small game makes each part visible on a laptop. A tiny tic-tac-toe player that learns from self-play, a saved policy table, and a frozen comparison with its untrained version. |
| 07.08 | [Make a self-modification inspectable](07_understanding_self_star/step_08_modification/README.md) | Writing a change is a capability. Improving the system is a separate result. A versioned edit to a learner-owned procedure with tests and rollback. |

**Ready to continue when:** For each self-* example, name what changes, what persists, and what stays fixed. Explain why a retry, memory file, or self-play update alone does not establish RSI.

A mechanism can exist without helping. The next theme makes the evidence for improvement explicit.

[Previous theme: 06](#theme-06) · [Next theme: 08](#theme-08) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-08"></a>

## 08 · Measure what improved

**Your place:** Changes and their evidence. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](08_measuring_improvement/README.md).

A better score can come from a better method, more attempts, easier data, or an evaluation mistake. Design comparisons that separate those explanations.

Use the fixed and modified skills from earlier themes. Freeze the comparison before reading its result.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 08.01 | [Distinguish a result from a reliable comparison](08_measuring_improvement/step_01_repeat_measurement/README.md) | One favorable result can reflect randomness or a convenient sample. Repetition helps reveal instability. A repeated comparison with paired seeds and an explicit uncertainty statement. |
| 08.02 | [Freeze selection before final evaluation](08_measuring_improvement/step_02_final_boundary/README.md) | A test repeatedly used to choose changes becomes part of the selection process. A selected recipe evaluated once on the final public partition, with further search closed. |
| 08.03 | [Count the cost of research](08_measuring_improvement/step_03_cost/README.md) | A method can look better because it spent more resources outside the model-fit counter. A resource ledger that includes proposals, checks, retries, failed work, and fitting. |
| 08.04 | [Separate the effects of memory and procedure changes](08_measuring_improvement/step_04_ablation/README.md) | Changing two components at once makes it hard to know which helped or harmed. A small factorial comparison of memory and a task-skill revision. |
| 08.05 | [Test whether the lesson transfers](08_measuring_improvement/step_05_transfer/README.md) | A procedure tuned on one regression dataset may encode assumptions that fail elsewhere. A transfer report that applies a frozen research skill to wine classification. |
| 08.06 | [Reject a misleading win and roll back](08_measuring_improvement/step_06_rollback/README.md) | A reliable improvement system must preserve its definition of success when a tempting result appears. A promotion decision that rejects a superficially strong but invalid candidate. |

**Ready to continue when:** Defend a comparison with fixed data roles, all planned outcomes, resource accounting, and explicit uncertainty. Keep selection separate from final evaluation.

You can now ask a sharper recursive question: does the changed procedure produce better future improvements?

[Previous theme: 07](#theme-07) · [Next theme: 09](#theme-09) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-09"></a>

## 09 · Improve the improvement procedure

**Your place:** Changes and their evidence. 7 labs; 2.3–4.1 hours of planned reading and discussion. [Open the theme](09_recursive_self_improvement/README.md).

The solver proposes ML experiments. The improver revises the solver’s research skill. Recursion enters when an improvement procedure is itself revised and that revision governs later improvement work.

Track three separate objects: task solver, improver, and evaluator. Keep claims of structure, effectiveness, and acceleration separate.

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 09.01 | [Identify the solver, improver, and evaluator](09_recursive_self_improvement/step_01_three_objects/README.md) | “The system improved itself” is too vague to inspect until you identify the system boundary and mutable object. A map of three distinct components and the changes each may make. |
| 09.02 | [Run repeated improvement with an unchanged improver](09_recursive_self_improvement/step_02_fixed_improver/README.md) | Repeated self-improvement is the comparison baseline for recursive improvement, not proof of it. Two generations of task-skill revision governed by one fixed improver. |
| 09.03 | [Propose a change to the improver](09_recursive_self_improvement/step_03_revise_improver/README.md) | To improve the improvement process, the target of an edit must reach that process. A child improver that changes how future task-skill revisions are chosen or tested. |
| 09.04 | [Use the revised improver in the next round](09_recursive_self_improvement/step_04_inherit/README.md) | A saved new improver can remain unused while the system silently follows the old procedure. An inheritance trace from a changed improver to a later task-skill proposal and decision. |
| 09.05 | [Measure whether the revised improver helps](09_recursive_self_improvement/step_05_compare_improvers/README.md) | The new improver may produce a strong current solver yet be worse at producing future improvements. A matched comparison of improvements produced by two improver versions. |
| 09.06 | [Run bounded recursive generations](09_recursive_self_improvement/step_06_bounded_generations/README.md) | Recursion without explicit scope can turn into unlimited search or an unreadable history. A two-generation recursive lineage with promotion, rejection, checkpoint, and stop records. |
| 09.07 | [State the result without overstating it](09_recursive_self_improvement/step_07_claim/README.md) | The strongest-looking label is less useful than a conclusion another researcher can verify. A final claim audit separating structural recursion, effective improvement, and acceleration. |

**Ready to continue when:** Trace the exact revised improver into a later action and compare its consequences with the old version. Report structural recursion and measured benefit separately.

A bounded recursive experiment is now inspectable. The research studio shows how current systems combine these mechanisms and where their evidence ends.

[Previous theme: 08](#theme-08) · [Next theme: 10](#theme-10) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-10"></a>

## 10 · Read and rebuild recent research

**Your place:** Research studio. 38 labs; 25.3–38.0 hours of planned reading and discussion. [Open the theme](10_research_studio/README.md).

Study the mechanism before the headline. Each studio lab maps a recent primary source to a small executable activity or an explicit result audit.

Complete the foundation themes first. Laptop adaptations preserve an idea, not the scale or headline result of the original system.

![The research studio contains thirteen groups across four areas: reading and retaining evidence, changing research procedures, scientific work, and composition, transfer, and assessment.](assets/illustrations/research-studio-map-v3.png)

*Read group numbers 00–12 in order. The four areas organize questions; each method has its own mechanism and evidence limits. These miniature scenes are abridged explanations, not execution traces or paper results. The ScienceBuddy laptop activities use numerical and synthetic examples; they do not train an LLM. Follow the group links for the source, adaptation, and focused figure.*

[Open the illustration at full size](assets/illustrations/research-studio-map-v3.png).

Work through the groups below in order. Each gives a source mechanism a concrete classroom question. Preserve the differences between live execution, replay, simulation, numerical illustration, and a paper-result audit.

### Read a frontier claim

Which claim does the available evidence support? Begin with the claim audit you already know how to make. Apply it to a framework, then follow a current announcement to its primary evidence. Keep publication date, mechanism, reported result, and independent verification separate. [Group introduction](10_research_studio/00_reading_frontier_research/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.01 | [Use a framework without turning it into a ladder](10_research_studio/00_reading_frontier_research/step_01_framework/README.md) | Different authors use different levels and definitions. A label is useful only with its stated criteria. A source-linked classification of three mechanisms from your own experiments. |
| 10.02 | [Audit a frontier announcement](10_research_studio/00_reading_frontier_research/step_02_announcements/README.md) | An announcement, a preprint, a benchmark entry, and an independent reproduction support different conclusions. A claim card traced from an original announcement to available methods and artifacts. |

### Exploration and memory

What should a system learn from an experiment, and what should it retain? Start with broad probes of the familiar bike task, then use their errors to choose a focused follow-up. Separate checking a result from writing a lesson about it. Freeze memory when measuring its effect, and keep current run state distinct from reusable experience. [Group introduction](10_research_studio/01_memory_and_exploration/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.03 | [Choose experiments that reduce uncertainty](10_research_studio/01_memory_and_exploration/step_03_exploration/README.md) | A fixed benchmark list can hide what the agent still does not understand about a new environment. A small exploration plan that moves from broad probes to a focused ML question. |
| 10.04 | [Verify the outcome, then let the actor write memory](10_research_studio/01_memory_and_exploration/step_04_actor_memory/README.md) | Changing who writes the lesson changes the mechanism being taught. An outcome check and a separate actor-authored memory update. |
| 10.05 | [Evaluate with memory frozen](10_research_studio/01_memory_and_exploration/step_05_frozen_memory/README.md) | Continuing to learn from evaluation cases changes what the evaluation measures. A memory-versus-no-memory comparison with updates disabled during evaluation. |
| 10.06 | [Separate working state from reusable experience](10_research_studio/01_memory_and_exploration/step_06_working_and_experience/README.md) | A current candidate ID is useful state but a poor general lesson. Mixing the two makes future instructions stale. Two memory stores with different lifetimes and update rules. |

### Dream-RSI: history, replay, and new evidence

What can a saved discovery history answer without another experiment? Build a small tree from actual ML attempts. Use that recorded structure to compare replay policies, keeping absent outcomes unknown. Finally, return to fresh work and test whether the replay-selected policy still helps. [Group introduction](10_research_studio/02_dream_rsi/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.07 | [Build a tree of attempted solutions](10_research_studio/02_dream_rsi/step_07_discovery_tree/README.md) | A flat best-score list hides which proposals descended from which observations. A small discovery tree whose nodes link to actual ML trial outcomes. |
| 10.08 | [Replay only what the history can answer](10_research_studio/02_dream_rsi/step_08_replay/README.md) | Replay can save environment executions, but it cannot reveal outcomes that were never recorded. Two replay policies evaluated on a recorded discovery tree, with explicit missing coverage. |
| 10.09 | [Test the replay winner on fresh work](10_research_studio/02_dream_rsi/step_09_online/README.md) | A policy that exploits a recorded tree may fail when new branches must actually be explored. An online confirmation comparison after replay selection. |

### Local changes and their interactions

Which component failed, and does its repair still work in the whole system? Diagnose one interface or action from contrasting traces. Restrict the edit, then test how it interacts with a second change. Finish by distinguishing a lineage of changed agents from a lineage of changed improvement procedures. [Group introduction](10_research_studio/03_modular_harness_evolution/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.10 | [Localize a harness problem](10_research_studio/03_modular_harness_evolution/step_10_localize/README.md) | Editing every instruction at once makes it hard to identify what fixed the problem. A failure diagnosis and one restricted edit to a harness component. |
| 10.11 | [Integrate edits and test transfer](10_research_studio/03_modular_harness_evolution/step_11_integrate/README.md) | Two useful changes can conflict when combined. An integration check for two individually tested harness edits. |
| 10.12 | [Compare agent evolution and improver evolution](10_research_studio/03_modular_harness_evolution/step_12_lineage/README.md) | A family tree of increasingly capable agents can still leave the operator that creates descendants fixed. A lineage audit distinguishing changed agent code from changed improvement procedure. |

### AIDE²: researchers as the object of an experiment

Does a better researcher also become better at improving researchers? First expose the proposal and selection rules of an inner ML researcher. Then compare a change to that researcher under a total outer budget. Finally, test the distinct question of using the resulting researcher as an improver. [Group introduction](10_research_studio/04_aide2/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.13 | [Inspect an inner ML researcher](10_research_studio/04_aide2/step_13_inner_research/README.md) | Nested improvement is easier to understand when the inner research task is concrete. A small inner researcher with explicit proposal operators and candidate selection. |
| 10.14 | [Improve the inner researcher under a total budget](10_research_studio/04_aide2/step_14_outer_research/README.md) | A better search procedure must be judged by the searches it produces, including the cost of evaluating it. An outer comparison of two inner-researcher procedures. |
| 10.15 | [Test the ignition claim separately](10_research_studio/04_aide2/step_15_ignition/README.md) | Being better at ML research does not automatically mean being better at improving ML researchers. A comparison plan for using old and new researchers as outer improvers. |

### Task skills and the skills that revise them

What changes when the updater itself is revised? Establish a task-skill update under one fixed meta-skill. Then use accumulated evidence to propose a less frequent updater revision and trace its effect on a later round. Keep the two version histories separate. [Group introduction](10_research_studio/05_meta_skill_evolution/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.16 | [Improve task skills with a fixed pipeline](10_research_studio/05_meta_skill_evolution/step_16_task_skills/README.md) | The task skill and the skill that improves it need separate identities before either can evolve. A task-skill update pipeline with a frozen diagnosis, proposal, and selection procedure. |
| 10.17 | [Update the skill updater on a slower schedule](10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md) | Changing every layer at every step makes attribution and evaluation difficult. A two-timescale trace with task-skill updates and one inherited meta-skill revision. |

### ScientistTwo: hypotheses, experiments, and review

What turns a promising idea into evidence that another researcher can assess? Use the bike task to write a falsifiable hypothesis, screen ideas, test a contribution, and answer a criticism with another experiment. Then inspect the difference between better research outputs and a better research procedure. [Group introduction](10_research_studio/06_scientist_two/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.18 | [Turn a limitation into a scientific hypothesis](10_research_studio/06_scientist_two/step_18_hypothesis/README.md) | An interesting idea becomes a research question when you can state what evidence would support or contradict it. A baseline, a testable hypothesis, and a prespecified experiment. |
| 10.19 | [Screen ideas and test their contributions](10_research_studio/06_scientist_two/step_19_screen_ablate/README.md) | Testing every idea at full scale is costly. Cheap screening can help, but it can also select for the wrong proxy. A small screening table followed by a controlled ablation. |
| 10.20 | [Answer a criticism with evidence](10_research_studio/06_scientist_two/step_20_review_rebuttal/README.md) | A rebuttal should resolve an uncertainty, not merely defend the original wording. A review, a follow-up experiment, and an evidence-based response. |
| 10.21 | [Distinguish better discoveries from a better scientist](10_research_studio/06_scientist_two/step_21_successive_results/README.md) | Successively better scientific artifacts do not alone show that the research procedure improved. A two-step research lineage and an audit of the researcher’s own changes. |

### ScienceBuddy: feedback, harness changes, and weight learning

How do human requests, executable checks, and learning updates connect? Start with a labelled correction about the wine report. Turn it into a rubric and revise the reporting skill. Then inspect grouped rewards numerically, simulate model–harness interactions, and audit the paper’s reported metrics. Each activity states whether it is execution, arithmetic, simulation, or source review. [Group introduction](10_research_studio/07_sciencebuddy/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.22 | [Turn a researcher correction into a task](10_research_studio/07_sciencebuddy/step_22_human_task/README.md) | Human feedback is most useful when the system can connect it to an artifact and an observable requirement. A task and rubric derived from a labelled researcher-request fixture. |
| 10.23 | [Adapt the harness to the rubric](10_research_studio/07_sciencebuddy/step_23_harness_adaptation/README.md) | Harness adaptation is often confused with training. Track the surface that actually changes. A reporting-skill revision that responds to the rubric without changing model weights. |
| 10.24 | [See what grouped rewards contribute](10_research_studio/07_sciencebuddy/step_24_grpo/README.md) | The phrase “GRPO learning” can hide the distinction between scoring outputs and updating a policy. A tiny numerical grouped-reward update illustration with an explicit limit statement. |
| 10.25 | [Track model–harness pairs across cycles](10_research_studio/07_sciencebuddy/step_25_coevolution/README.md) | A model checkpoint can perform differently with a new harness. Evaluate the pair that actually runs. A version table and a small labelled simulation of alternating model and harness changes. |
| 10.26 | [Read the ScienceBuddy results precisely](10_research_studio/07_sciencebuddy/step_26_audit_results/README.md) | Similar-looking percentages can describe different experiments and support different claims. A result audit that separates single-attempt accuracy, multi-attempt coverage, and feedback provenance. |

### Experience, executable procedures, and interface skills

How should a useful lesson become an active procedure? Separate original traces, retained knowledge, and accepted skills. Refine a procedure graph without confusing it with a domain ontology. Then apply the same evidence discipline to a local experiment-results page and a visible UI mistake. [Group introduction](10_research_studio/08_skills_and_procedures/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.27 | [Keep traces, knowledge, and active skills separate](10_research_studio/08_skills_and_procedures/step_27_wiki/README.md) | Rejecting a procedure does not require forgetting what its experiment taught you. Three stores with different retention rules, including a rejected skill edit whose lesson survives. |
| 10.28 | [Refine a procedure graph](10_research_studio/08_skills_and_procedures/step_28_procedural_graph/README.md) | A long instruction document can obscure the next relevant action. A graph can make local decisions explicit. A small procedure graph with one tested transition edit and retained rejected proposals. |
| 10.29 | [Repair a skill for an experiment-results page](10_research_studio/08_skills_and_procedures/step_29_gui/README.md) | GUI work adds observation and action errors that a text-only success claim can hide. A local results page, one interaction trace, and a revised inspection skill. |

### Efficient harnesses and their builders

What can become cheaper without weakening the task? Define the quality floor before removing redundant work. Count the cost of finding and checking the change. Then separate the quality of a generated harness from the quality of the procedure that generates harnesses. [Group introduction](10_research_studio/09_efficient_harnesses/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.30 | [Reduce cost without hiding quality loss](10_research_studio/09_efficient_harnesses/step_30_cost_quality/README.md) | A shorter trace is useful only if it still performs the required work reliably. A quality-and-cost comparison of two small harness variants. |
| 10.31 | [Compare harness generation and harness improvement](10_research_studio/09_efficient_harnesses/step_31_harness_builders/README.md) | Generating infrastructure, improving its task output, and improving its generator are different claims. A source audit and a local comparison of a generated harness before and after one revision. |

### Feedback, memory, and compatibility

Which information changes behavior, and will it still fit the surrounding system? Compare raw events with compact memory, distinguish action hints from richer observations, and test a local interface mismatch. These small checks make it easier to read training papers without mistaking a prompt intervention for a parameter update. [Group introduction](10_research_studio/10_feedback_and_transfer/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.32 | [Compare raw history and summarized memory](10_research_studio/10_feedback_and_transfer/step_32_memory_interface/README.md) | A long history and a useful memory can contain similar facts but impose different retrieval demands. A tiny state-tracking task with an exact checker and two memory representations. |
| 10.33 | [Compare action hints and richer observations](10_research_studio/10_feedback_and_transfer/step_33_scaffolding/README.md) | Help can change what a system does without establishing what it can do unaided. A small task comparison with action guidance, observation enrichment, and assistance removed. |
| 10.34 | [Keep model training aligned with its harness](10_research_studio/10_feedback_and_transfer/step_34_model_harness_fit/README.md) | Training or instruction changes can teach behavior that no longer fits the surrounding workflow. An interface-mismatch experiment and a source audit of local versus whole-trajectory correction. |

### Compose changes and learn from references

How can several improvement operations share evidence without corrupting it? Use a typed simulation to track data, harness, model, and scheduler versions. Then inspect reference trajectories: a known answer can guide diagnosis, but copied answers and invalid shortcuts must not become active skills. [Group introduction](10_research_studio/11_composition_and_reference_learning/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.35 | [Compose changes to data, harness, and model](10_research_studio/11_composition_and_reference_learning/step_35_metarsi/README.md) | A failure does not automatically reveal whether it needs better data, a harness change, or model training. A typed operator schedule and a labelled simulation of revising that schedule. |
| 10.36 | [Diagnose failures with checked reference trajectories](10_research_studio/11_composition_and_reference_learning/step_36_harnessevolve/README.md) | A final failure score says little about the first wrong action. A valid reference can help localize it, but an answer shortcut can mislead. A reference-guided diagnosis with leakage and regression checks on the proposed skill edit. |

### Compare evidence and examine bottlenecks

Which stronger claims still need another experiment? Compare six source systems and your own experiment with the same questions about changes, feedback, inheritance, evaluation, and cost. Then use a small calculator to separate faster components from faster total research and cumulative gains from acceleration. [Group introduction](10_research_studio/12_evidence_and_open_questions/README.md).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 10.37 | [Compare systems without flattening their differences](10_research_studio/12_evidence_and_open_questions/step_37_compare_systems/README.md) | A single “RSI” label hides differences in mutable components, feedback, inheritance, and evaluation. A comparison matrix of six systems and your own bounded experiment. |
| 10.38 | [Reason about bottlenecks and acceleration](10_research_studio/12_evidence_and_open_questions/step_38_economics/README.md) | Faster proposal generation does not remove slow evaluation, missing data, hardware limits, or human review. A small resource model and an evidence checklist for an acceleration claim. |

**Ready to continue when:** Compare research systems by their changed object, feedback, inheritance, evaluation, and cost. Distinguish a source claim from your laptop adaptation and its observed result.

Use the capstones to transfer the ideas to a new task and defend your conclusions with evidence.

[Previous theme: 09](#theme-09) · [Next theme: 11](#theme-11) · [Whole-course mindmap](#whole-course-mindmap)

<a id="theme-11"></a>

## 11 · Build, transfer, and explain

**Your place:** Capstones. 5 labs; 5.0–10.0 hours of planned reading and discussion. [Open the theme](11_capstones/README.md).

Your final work should be understandable to another student. Give them a task, a runnable system, an honest result, and a clear explanation of its limits.

Use the tools and skills that your experiment needs. A larger architecture is not automatically a better answer.

![Five capstones build a new harness, run a bounded recursive comparison, test task, agent, and compute portability, audit an unfamiliar claim, and teach a project portfolio.](assets/illustrations/capstone-map-v3.png)

*The portfolio connects the five activities. In 11.02, the changed rule is used in a provisional I1 trial before the keep-or-reject decision. Match starting artifacts and resources, keep the external comparison fixed, and record later behavior. Two generations and eight CPU fits are maxima, not a guarantee of useful results; also declare the inference limit. Empty portability boxes and illustrative records do not certify completed tests. Explain a gain, regression, or inconclusive result from actual evidence.*

[Open the illustration at full size](assets/illustrations/capstone-map-v3.png).

| Lab | Codelab | Why it matters and what you will make |
|---|---|---|
| 11.01 | [Build a harness for a new prediction brief](11_capstones/step_01_new_harness/README.md) | A new task reveals whether you understand the method or only remember the earlier examples. A runnable harness that another student can inspect and execute. |
| 11.02 | [Run and audit a bounded recursive experiment](11_capstones/step_02_recursive_experiment/README.md) | The capstone should demonstrate the mechanism you claim, including inheritance and the cost of finding a change. A solver–improver lineage with matched comparisons and an honest final claim. |
| 11.03 | [Test transfer and portability separately](11_capstones/step_03_portability/README.md) | A procedure can transfer across tasks while failing in another agent’s tool environment, or the reverse. A compatibility matrix backed by actual small runs and clearly marked untested paths. |
| 11.04 | [Audit an unfamiliar RSI claim](11_capstones/step_04_external_audit/README.md) | Independent judgment matters more than remembering the systems in this course. A short primary-source audit with a concrete follow-up experiment. |
| 11.05 | [Teach the mechanism and defend the evidence](11_capstones/step_05_teach_back/README.md) | You understand a complex system better when you can explain one concrete path through it and one case where it fails. A concise portfolio that a peer can run, question, and understand. |

**Ready to continue when:** Give another student a runnable project and an evidence-backed explanation. They should be able to inspect the lineage, question the comparison, and understand a negative result.

Keep the portfolio small enough to inspect and complete enough to reproduce. A well-explained failure can be a strong final project.

The [example portfolio](PORTFOLIO.md) connects actual author evidence. Its peer reproduction is prepared and explicitly pending.

[Previous theme: 10](#theme-10) · [Whole-course mindmap](#whole-course-mindmap)

## Find the instructions behind a lab

The [source-artifact index](SOURCE-ARTIFACTS.md) links every lab README, intent brief, authoring module, and shared skill. Use it to inspect how the course is authored. Follow the [learning path](LEARNING-PATH.md) for conceptual checkpoints, the [teaching roadmap](TEACHING-ROADMAP.md) for session plans and capstone milestones, and the [glossary](GLOSSARY.md) for definitions and examples. Written coverage and completed execution are tracked separately in the [completion ledger](../how-did-i-generate-it/rsi/COURSE-COMPLETION-LEDGER.md).
