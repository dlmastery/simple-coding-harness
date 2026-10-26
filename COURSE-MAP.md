# Your Route Through the RSI Masterclass (October 2026 Edition)

[Lecture slides and speaker notes](PRESENTATION.md): 37-slide PowerPoint review draft with the course figures and measured results.

[Course](README.md) · [Start here](START-HERE.md) · [October 2026 papers](12_october_2026_papers/PAPER_SUMMARIES.md) · [Intent, skills, and authoring sources](SOURCE-ARTIFACTS.md)

Start with one bike-demand prediction. Make its evidence trustworthy. Then add a reason for another experiment, rules for choosing the next action, and a way to preserve useful work. Only after those ideas are clear do you change the research procedure—and then the procedure that improves it.

This guide explains the full course route with October 2026 RSI paper integration. It is also a place to return when a new term obscures the purpose of the next step. The numbered themes give reading order; the mindmap shows how the ideas belong together. Your position in the course is not a claim that earlier experiments succeeded.

<a id="whole-course-mindmap"></a>

## The Whole Course

![A bike-demand research project connects six learning blocks and all twelve themes: one experiment, dependable workflows, a system and builder, changes and evidence, research studio, and capstones.](assets/illustrations/course-mindmap-v2.png)

*Follow theme numbers 00–11. The branches group concepts; they are not execution dependencies or a universal maturity ladder. The research names are selected examples. Use the theme number on each lesson to locate it here. This map describes the planned route, not completed experiments.*

[Open the illustration at full size](assets/illustrations/course-mindmap-v2.png).

The destination is the October 2026 research studio and the capstones. The earlier themes give you the vocabulary, tools, and judgment to inspect those systems instead of treating their names or headline scores as explanations.

## Objectives

By the end, you should be able to:

- Build and inspect a complete small ML experiment, from the question and data to a checked result.
- Design bounded loops, dependency graphs, domain rules, and reliable recovery.
- Use skills to have a coding agent generate and operate a research harness.
- Distinguish self-* mechanisms, harness generation, and recursive improvement.
- Test whether a changed research procedure helps under a fair comparison.
- Read October 2026 RSI research, explain its mechanism, and state what a laptop adaptation preserves.
- Build, transfer, audit, and teach a bounded project with an honest conclusion.

## Prerequisites and Time

You need basic ML familiarity: tables, features and targets, training versus evaluation, and prediction error. No RSI, agent, or infrastructure background is assumed. Students give natural-language instructions; the agent writes code and configuration. Use a coding agent with file and command access, a laptop for CPU experiments, and internet access for setup and research reading. Hosted-agent charges are separate.

The current per-lab author estimates sum to **49.8–82.0 hours** of reading and guided discussion. They are planning estimates, not measured learner durations. Allow additional time for setup, debugging, deeper paper reading, independent capstone work, and optional larger jobs.

| Part | Scope | Current author estimate |
|------|-------|-------------------------|
| Foundations through RSI | Themes 00–09, 58 labs | 19.5–34.0 hours |
| October 2026 Research Studio | Theme 10, 17 labs | 10.0–15.0 hours |
| Capstones | Theme 11, 5 labs | 5.0–10.0 hours |

Each lab includes an explained quiz and a next step. Attempt the quiz and explain one new case before continuing. A short workshop may stop after theme 02; that route teaches dependable ML loops and does not reach the full RSI outcome.

## Find Your Theme

| Theme | New Capability | Labs |
|-------|---------------|------|
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
| [10 · Read and rebuild October 2026 research](#theme-10) | October 2026 research studio | 17 |
| [11 · Build, transfer, and explain](#theme-11) | Capstones | 5 |

<a id="theme-00"></a>

## 00 · Start with a Prediction

**Your place:** One experiment. 4 labs; 1.3–2.3 hours of planned reading and discussion. [Open the theme](00_start_here/README.md).

A bike service wants an estimate of hourly demand. Before building an improving agent, learn to tell an executed prediction from a convincing description.

You need basic familiarity with tables and prediction error. You do not need RSI, agent, or infrastructure experience.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 00.01 | [Meet the prediction task](00_start_here/step_01_meet_the_task/README.md) | An agent can optimize the wrong task very efficiently. First make the question concrete. A task brief that says what one prediction means and which inputs are available. |
| 00.02 | [Prepare a workspace you can inspect](00_start_here/step_02_prepare_the_workspace/README.md) | "I can run this" is a claim. A small successful command supplies evidence for it. A separate learner workspace, a capability report, and a verified data report. |
| 00.03 | [Run one baseline](00_start_here/step_03_one_attempt/README.md) | Before asking whether a system improved, you need a clear starting result. A real constant-prediction baseline with a measured error and saved predictions. |
| 00.04 | [Check the evidence behind the answer](00_start_here/step_04_check_the_evidence/README.md) | A polished report can describe a run that never happened or claim more than the run establishes. A short evidence report that ties a claim to predictions, data roles, and a reproducible calculation. |

**Ready to continue when:** Explain one prediction: its target, permitted inputs, partition, and checked error. Identify a feature that would leak the answer.

The next theme turns these checked actions into a repeatable process.

[Previous: Overview](#whole-course-mindmap) · [Next: Theme 01](#theme-01)

<a id="theme-01"></a>

## 01 · Make One Process Dependable

**Your place:** One experiment. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](01_process_without_loops/README.md).

You can inspect an agent's output. Now make the actions behind it explicit and repeatable. Run a simple data science process once, then package it as a skill.

The process stays fixed. "No loops" means no learner-designed search or revision loop. The coding agent and numerical libraries can still have internal iterations.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 01.01 | [Write the data science process](01_process_without_loops/step_01_describe_the_process/README.md) | An implicit process is hard to inspect. Writing its dependencies exposes missing decisions. A five-action process from task framing to a checked baseline report. |
| 01.02 | [Run the process without changing it](01_process_without_loops/step_02_run_the_process/README.md) | A written sequence may omit setup or depend on forgotten state. A fresh run exposes those gaps. A clean-start execution trace for the fixed bike baseline process. |
| 01.03 | [Turn the process into a skill](01_process_without_loops/step_03_make_a_skill/README.md) | A chat history is a poor substitute for a reusable procedure. A skill makes the intended behavior explicit. A short Markdown skill that runs the fixed baseline process. |
| 01.04 | [Check outputs with a separate calculation](01_process_without_loops/step_04_separate_the_check/README.md) | A solver's confidence cannot substitute for measuring its output. An output checker that derives error from prediction rows and rejects a mismatch. |
| 01.05 | [Reuse the skill in a fresh session](01_process_without_loops/step_05_reuse_the_skill/README.md) | A process that depends on unrecorded chat details is fragile. Persistence should be visible in artifacts. A handoff that another session can execute from files alone. |

**Ready to continue when:** Show a readable fixed procedure, an actual checked baseline, and enough saved context for another session to repeat it.

A repeatable process gives you a useful starting point. The next theme asks what to do when that process produces a weak result.

[Previous: Theme 00](#theme-00) · [Next: Theme 02](#theme-02)

<a id="theme-02"></a>

## 02 · Repeat for a Reason

**Your place:** Dependable workflows. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](02_loop_engineering/README.md).

A weak result invites another attempt. Repeating only helps when you know what to change, how to remember the current state, and when to stop.

Use the baseline and readable skill from the previous theme. Add feedback, state, and budgets one at a time.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 02.01 | [Let a failure motivate a second attempt](02_loop_engineering/step_01_why_repeat/README.md) | The baseline ignores the daily demand pattern. Another identical attempt cannot supply that missing relationship. A controlled comparison between a constant baseline and a calendar-based linear model. |
| 02.02 | [Give the loop state and a budget](02_loop_engineering/step_02_bounded_state/README.md) | "Keep trying until it works" leaves both resource use and success undefined. A three-attempt loop with a current candidate, best candidate, ledger, and stopping rule. |
| 02.03 | [Turn an error into a different action](02_loop_engineering/step_03_use_feedback/README.md) | Passing a score back to an agent is not enough. You need to see how the feedback affects its decision. A feedback note that causes a documented change in the next experiment. |
| 02.04 | [Stop repeated failure and oscillation](02_loop_engineering/step_04_stop_the_loop/README.md) | An agent can alternate between two ideas and describe each as progress. A ledger makes the repetition visible. A loop controller that stops on a repeated recipe, exhausted budget, or unchanged failure. |
| 02.05 | [Resume without losing the experiment](02_loop_engineering/step_05_resume/README.md) | Restarting the program should not silently restart the scientific experiment. A checkpoint and a resumed loop that retains candidate identities and spent budget. |
| 02.06 | [Compare two ways to spend the same attempts](02_loop_engineering/step_06_compare_loops/README.md) | A better final candidate can result from how attempts were chosen, not only from the model family. A small comparison between fixed retries and feedback-guided revisions. |

**Ready to continue when:** Explain why the next attempt is allowed, which feedback changes it, how much budget remains, and what stops the loop.

A loop handles repeated work. It does not explain why a data failure and an expensive model should take different routes. That calls for a graph.

[Previous: Theme 01](#theme-01) · [Next: Theme 03](#theme-03)

<a id="theme-03"></a>

## 03 · Give Different Cases Different Routes

**Your place:** Dependable workflows. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](03_graph_engineering/README.md).

A workflow is more than a numbered list. Some actions depend on others. Some can proceed independently. Some should run only after a particular failure.

You already have a bounded improvement loop. Now place it inside a graph of dependencies, branches, and recovery paths.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 03.01 | [Draw the dependencies](03_graph_engineering/step_01_dependencies/README.md) | A numbered list hides why one action must precede another. Dependencies explain that order. An execution graph for the process you already ran. |
| 03.02 | [Route different failures differently](03_graph_engineering/step_02_branch/README.md) | Trying another model cannot fix a missing target or a leaked feature. The response should match the failure. A branch that sends invalid data to repair and valid data to modeling. |
| 03.03 | [Join independent checks](03_graph_engineering/step_03_join/README.md) | One successful check must not conceal another missing or failed check. A join that waits for both a data-quality check and a resource check. |
| 03.04 | [Put a bounded retry inside the graph](03_graph_engineering/step_04_cycle/README.md) | A return arrow can hide unlimited work unless the retry state travels with it. A graph with one explicit repair cycle and a terminal failure path. |
| 03.05 | [Resume only the affected work](03_graph_engineering/step_05_recover/README.md) | Restarting everything wastes work. Reusing everything risks stale results. Dependencies tell you what must change. A recovery trace that preserves valid upstream artifacts and reruns affected descendants. |
| 03.06 | [Read the plan, data flow, and trace](03_graph_engineering/step_06_three_views/README.md) | A diagram can look correct even when execution took a different route. Three views of one run: allowed actions, artifact movement, and actual events. |

**Ready to continue when:** Trace a failure through dependencies. Recover a failed report without refitting, and identify what a changed split would invalidate.

A graph tells the agent where work goes. The next theme asks whether the objects moving through it have the right meaning.

[Previous: Theme 02](#theme-02) · [Next: Theme 04](#theme-04)

<a id="theme-04"></a>

## 04 · Agree on What the Experiment Means

**Your place:** Dependable workflows. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](04_ontology_engineering/README.md).

Two files can both say "score" while describing different measurements. A shared vocabulary connects the data, models, decisions, and evidence.

Begin with concrete entities and relations in Markdown. Add only the rules needed to catch a real inconsistency.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 04.01 | [Name the objects in an experiment](04_ontology_engineering/step_01_entities/README.md) | "Improve the model" is ambiguous if one speaker means fitted parameters and another means the whole agent system. A small vocabulary for data, columns, targets, partitions, models, metrics, and evidence. |
| 04.02 | [Connect data, models, and evidence](04_ontology_engineering/step_02_relations/README.md) | A list of names does not tell you which model used which data or which score supports which decision. A readable relation table describing one ML experiment. |
| 04.03 | [State rules that must always hold](04_ontology_engineering/step_03_invariants/README.md) | Correct spelling and valid file structure do not prevent target leakage or misuse of final data. Three domain invariants, each with a passing and failing example. |
| 04.04 | [Catch a plausible but invalid experiment](04_ontology_engineering/step_04_catch_contradictions/README.md) | A realistic mistake combines several reasonable-looking facts. The rules must connect them. A semantic failure report and a corrected relation table. |
| 04.05 | [Change a definition without losing its consequences](04_ontology_engineering/step_05_evolve_vocabulary/README.md) | A harmless-looking word change can alter which inputs and results are valid. A versioned vocabulary change and an impact report for a new forecasting task. |

**Ready to continue when:** Use named objects, relations, and meaning rules to reject a plausible experiment with a wrong metric, unit, or leaked input.

You can now inspect both the route of an experiment and the meaning of its records. These become parts of a coordinated research system.

[Previous: Theme 03](#theme-03) · [Next: Theme 05](#theme-05)

<a id="theme-05"></a>

## 05 · Build Capability Around the Model

**Your place:** A system and its builder. 5 labs; 1.7–2.9 hours of planned reading and discussion. [Open the theme](05_system_intelligence/README.md).

A useful research system combines a model with tools, state, checks, and domain knowledge. In this course, "system intelligence" means the capability of that combination.

This is a course term, not an accepted RSI level. Keep the components fixed while studying how their coordination changes results.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 05.01 | [Combine fixed components into a useful system](05_system_intelligence/step_01_combine_components/README.md) | A language model's answer is only one part of reliable experimental work. The surrounding system determines what it can observe, execute, and verify. A fixed research workflow that uses a task skill, an ML tool, domain checks, and a report checker. |
| 05.02 | [Choose a skill for the task](05_system_intelligence/step_02_route_tasks/README.md) | A metric or model that fits one task can be wrong for another. Reuse should preserve meaning. A router that sends bike regression and wine classification to suitable fixed procedures. |
| 05.03 | [Retrieve what matters and retain task state](05_system_intelligence/step_03_context_and_state/README.md) | More text can add contradictions and stale instructions. Useful context is selected for a decision. A context packet that separates task rules, relevant knowledge, and current execution state. |
| 05.04 | [Coordinate planning, execution, and checking](05_system_intelligence/step_04_coordinate/README.md) | Good individual tools can still produce a weak system if nobody checks their handoffs. A coordinator that advances work only when the required artifacts and checks are present. |
| 05.05 | [Find which component makes the difference](05_system_intelligence/step_05_ablate_system/README.md) | A successful full system does not reveal which component caused the benefit. An ablation that compares the system with and without one domain check. |

**Ready to continue when:** Show a coordinator reading saved state before acting and refusing an incomplete or wrong-candidate handoff. Explain which fixed component contributes to the result.

Once you can describe a useful system, you can ask another procedure to build it from a brief.

[Previous: Theme 04](#theme-04) · [Next: Theme 06](#theme-06)

<a id="theme-06"></a>

## 06 · Generate a Harness from a Brief

**Your place:** A system and its builder. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](06_meta_harness_engineering/README.md).

A harness organizes execution: instructions, tools, state, checks, and limits. A meta-harness generates such a system from a task description.

You have built the parts by hand through natural language. Now the agent assembles them and proves that the result runs.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 06.01 | [Describe the harness you need](06_meta_harness_engineering/step_01_write_a_brief/README.md) | A generator needs the scientific and operating requirements, not just "make an intelligent agent." A plain-language specification for a small bike-research harness. |
| 06.02 | [Generate a harness from the brief](06_meta_harness_engineering/step_02_generate/README.md) | The agent must translate requirements into executable code and configuration. A generated harness package with scripts, configuration, and checks. |
| 06.03 | [Inspect the generated harness](06_meta_harness_engineering/step_03_inspect_generated/README.md) | Generated code can compile while still being wrong for the task. A review checklist that verifies data roles, partitions, metrics, and refusal cases. |
| 06.04 | [Test refusal of invalid requests](06_meta_harness_engineering/step_04_test_refusal/README.md) | A system that always runs is easy to build but dangerous. It must reject requests that violate its scientific contract. Test cases for missing data, wrong partitions, and unsupported metrics. |
| 06.05 | [Apply the same brief to a second task](06_meta_harness_engineering/step_05_second_task/README.md) | A useful generator should work for more than one hand-written example. Generate a wine-classification harness from the same brief template. |
| 06.06 | [Recreate the first harness from the brief](06_meta_harness_engineering/step_06_recreate/README.md) | Deterministic generation matters for reproducibility. Regenerate the bike harness and verify it matches the first run. |

**Ready to continue when:** Show a generated harness that runs, refuses invalid requests, and reproduces on regeneration.

You now have a system and a procedure that can build it. The next themes distinguish this from self-improvement.

[Previous: Theme 05](#theme-05) · [Next: Theme 07](#theme-07)

<a id="theme-07"></a>

## 07 · Separate the Self-* Ideas

**Your place:** Changes and their evidence. 8 labs; 2.5–4.0 hours of planned reading and discussion. [Open the theme](07_understanding_self_star/README.md).

Correction, learning, organization, emergence, and modification are not the same. October 2026 RSI papers add new mechanisms like second-order diagnostics and swarm evolution. This theme distinguishes these ideas before claiming recursion.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 07.01 | [Correct a single error](07_understanding_self_star/step_01_correction/README.md) | Fixing a bug does not make a system self-improving. A one-time error correction that does not change the improvement procedure. |
| 07.02 | [Reflect on what happened](07_understanding_self_star/step_02_reflection/README.md) | Retrospective analysis is different from adaptive learning. A post-run review that generates insights but does not automatically act on them. |
| 07.03 | [Add persistent learning](07_understanding_self_star/step_03_persistent_learning/README.md) | Storing successful choices for reuse is memory, not recursion. A skill that records working configurations and retrieves them for similar tasks. |
| 07.04 | [Test self-improvement](07_understanding_self_star/step_04_self_improvement/README.md) | A system that revises its own improvement procedure qualifies as self-improving. A small experiment where the improver updates itself between rounds. |
| 07.05 | [Observe organization](07_understanding_self_star/step_05_organization/README.md) | Coordinating multiple components is organization, not emergence. A fixed coordinator that routes work but does not change its own rules. |
| 07.06 | [Observe emergence](07_understanding_self_star/step_06_emergence/README.md) | Emergence requires that system-level behavior cannot be predicted from component-level rules. A multi-agent system with simple local rules that produces complex global patterns. |
| 07.07 | [Compare self-play to self-improvement](07_understanding_self_star/step_07_self_play/README.md) | Self-play improves a policy against its own history; it does not necessarily improve the improvement procedure. A tic-tac-toe self-play loop. |
| 07.08 | [Modify the system itself](07_understanding_self_star/step_08_modification/README.md) | Changing system code is modification; changing the improver of that code is recursive modification. A meta-skill that revises another skill's instructions. |

**Ready to continue when:** Explain why a given mechanism is correction, learning, organization, emergence, or modification. Distinguish self-play from self-improvement.

Now that the self-* family is clear, you can measure what actually improved.

[Previous: Theme 06](#theme-06) · [Next: Theme 08](#theme-08)

<a id="theme-08"></a>

## 08 · Measure What Improved

**Your place:** Changes and their evidence. 6 labs; 2.0–3.5 hours of planned reading and discussion. [Open the theme](08_measuring_improvement/README.md).

A better score does not automatically mean a better improver. You need to measure the right object, use a fair comparison, and account for cost.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 08.01 | [Repeat a measurement](08_measuring_improvement/step_01_repeat_measurement/README.md) | A single measurement can be noisy. A repeated experiment that reports mean and variance. |
| 08.02 | [Enforce a final evaluation boundary](08_measuring_improvement/step_02_final_boundary/README.md) | Testing on training data overstates performance. A frozen final partition and a check that no later code accesses it. |
| 08.03 | [Report the cost of improvement](08_measuring_improvement/step_03_cost/README.md) | An improvement that costs more than it saves is not an improvement. A cost ledger tracking compute, time, and inference. |
| 08.04 | [Ablate to find the contributing component](08_measuring_improvement/step_04_ablation/README.md) | A complex change may have many parts; ablation isolates which ones matter. A comparison that removes one component at a time. |
| 08.05 | [Test transfer to a new task](08_measuring_improvement/step_05_transfer/README.md) | Improvement on one task may not transfer. A transfer test on a different but related task. |
| 08.06 | [Rollback and re-measure](08_measuring_improvement/step_06_rollback/README.md) | A claimed improvement should survive undoing and redoing. A rollback test that restores the previous state and runs again. |

**Ready to continue when:** Show a measurement with variance, a frozen final boundary, a cost report, and an ablation that identifies the contributing change.

With measurement clear, you can now ask whether changing the improver itself helps.

[Previous: Theme 07](#theme-07) · [Next: Theme 09](#theme-09)

<a id="theme-09"></a>

## 09 · Improve the Improvement Procedure

**Your place:** Changes and their evidence. 7 labs; 2.3–4.0 hours of planned reading and discussion. [Open the theme](09_recursive_self_improvement/README.md).

Recursive self-improvement means the improver itself is revised, and the revision governs later improvement work. October 2026 papers like Budget RSI and SO-RSI introduce new ways to think about this.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 09.01 | [Name the three objects](09_recursive_self_improvement/step_01_three_objects/README.md) | Task model, research skill, and improver are distinct. Changing each has different implications. A diagram showing the three objects and their relationships. |
| 09.02 | [Run with a fixed improver](09_recursive_self_improvement/step_02_fixed_improver/README.md) | Establish a baseline with an improver that does not change. A fixed improver running multiple rounds of improvement. |
| 09.03 | [Revise the improver](09_recursive_self_improvement/step_03_revise_improver/README.md) | The revision must survive a fair comparison. A modified improver and the protocol for testing it. |
| 09.04 | [Inherit the revision](09_recursive_self_improvement/step_04_inherit/README.md) | A revised improver should generate the next improver. A two-generation comparison: I0 generates I1, both generate researchers. |
| 09.05 | [Compare two improvers under the same conditions](09_recursive_self_improvement/step_05_compare_improvers//README.md) | Different resources or budgets invalidate the comparison. A paired comparison with matched search cost and evaluation protocol. |
| 09.06 | [Bound the number of generations](09_recursive_self_improvement/step_06_bounded_generations/README.md) | Unbounded recursion is dangerous. A generation limit and a stopping rule based on evidence. |
| 09.07 | [State the claim with its limits](09_recursive_self_improvement/step_07_claim/README.md) | A recursive claim must be honest about what was tested. A claim statement that identifies the objects, the comparison, and the untested assumptions. |

**Ready to continue when:** Show a three-object diagram, a fixed-improver baseline, a revised improver, an inheritance test, a fair comparison, bounded generations, and an honest claim.

Now you can read October 2026 RSI research and understand what each paper actually tested.

[Previous: Theme 08](#theme-08) · [Next: Theme 10](#theme-10)

<a id="theme-10"></a>

## 10 · Read and Rebuild October 2026 Research

**Your place:** October 2026 research studio. 6 groups, 17 labs; 10.0–15.0 hours of planned reading and discussion. [Open the studio](10_research_studio/README.md).

Study the mechanism before the headline. Each studio lab maps a recent October 2026 RSI paper to a small executable activity or an explicit result audit.

Complete the foundation themes first. Laptop adaptations preserve an idea, not the scale or headline result of the original system.

| Group | October 2026 Paper Focus | Labs |
|-------|-------------------------|------|
| [Read a frontier claim](10_research_studio/00_reading_frontier_research/README.md) | Which claim does the available evidence support? | 10.01–10.02 |
| [Budget RSI: Scoring Before Running](10_research_studio/01_budget_rsi_scoring/README.md) | Can we score code edits before full evaluation? | 10.03–10.05 |
| [Second-Order RSI: Diagnostic Inquiry](10_research_studio/02_second_order_diagnostics/README.md) | Why do failures occur before patching? | 10.06–10.08 |
| [Scaling RSI: Coordination & Swarms](10_research_studio/03_scaling_coordination/README.md) | How do multiple agents coordinate for RSI? | 10.09–10.11 |
| [Adaptive Workflows: RSIFlow & Self-HPO](10_research_studio/04_adaptive_workflows/README.md) | Can workflows adapt to evolving bottlenecks? | 10.12–10.14 |
| [Environments & Metrics: RSIGym & More](10_research_studio/05_environments_metrics/README.md) | What environments support RSI research? | 10.15–10.17 |

**Full laptop demos available for:**
- Budget RSI: `12_october_2026_papers/01_budget_rsi/demo.py` (< 5 minutes)
- SO-RSI: `12_october_2026_papers/02_second_order_rsi/demo.py` (< 2 minutes)

**Ready to continue when:** Compare October 2026 RSI systems by their changed object, feedback, inheritance, evaluation, and cost. Distinguish a source claim from your laptop adaptation and its observed result.

Use the capstones to transfer the ideas to a new task and defend your conclusions with evidence.

[Previous: Theme 09](#theme-09) · [Next: Theme 11](#theme-11)

<a id="theme-11"></a>

## 11 · Build, Transfer, and Explain

**Your place:** Capstones. 5 labs; 5.0–10.0 hours of planned reading and discussion. [Open the capstones](11_capstones/README.md).

Now apply the course ideas to a project of your own. Each capstone requires evidence and an honest conclusion.

| Lab | Codelab | Why it matters and what you will make |
|------|---------|----------------------------------------|
| 11.01 | [Build a harness from a new brief](11_capstones/step_01_new_harness/README.md) | Generate a runnable harness for a task you define. A generated package with checks and a refusal test. |
| 11.02 | [Run a recursive comparison](11_capstones/step_02_recursive_experiment/README.md) | Test whether a revised improver helps on your task. A two-improver comparison with matched resources. |
| 11.03 | [Test portability](11_capstones/step_03_portability/README.md) | Can your system run in another environment? A portability test on a different machine or agent. |
| 11.04 | [External audit](11_capstones/step_04_external_audit/README.md) | Have another reviewer check your evidence. An audit report that confirms or questions your claims. |
| 11.05 | [Teach back](11_capstones/step_05_teach_back/README.md) | Can you explain what you built to someone else? A teaching session where you explain your mechanism, evidence, and limits. |

**Ready to continue when:** Demonstrate a generated harness, a recursive comparison with evidence, portability results, an external audit, and a clear teaching explanation.

---

## Quick Reference

**Starting points:**
- [Course README](README.md) - Overview and October 2026 highlights
- [Start here](START-HERE.md) - First session instructions
- [October 2026 papers](12_october_2026_papers/PAPER_SUMMARIES.md) - Paper summaries
- [Laptop demos](12_october_2026_papers/LAPTOP_DEMOS.md) - How to run demos

**Learning paths:**
- Quick start (5 hours): Themes 00-02 + Budget RSI demo + Capstone 11.01
- Standard course (30 hours): Themes 00-09 + October 2026 research studio (selected groups) + Capstones 11.01-11.03
- Full masterclass (60 hours): Complete course + all October 2026 groups + all capstones

**Key files:**
- [Glossary](GLOSSARY.md) - Definitions and counterexamples
- [Teaching roadmap](TEACHING-ROADMAP.md) - Session plans and checkpoints
- [Revamp summary](REVAMP_SUMMARY.md) - October 2026 changes
