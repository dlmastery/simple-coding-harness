# Source instructions for every codelab

[Course](README.md) · [Course map](COURSE-MAP.md) · [Folder map](STRUCTURE.md)

This index links the instructions that define all 101 codelabs: their purpose, procedure, constraints, and authoring source. These are course materials, not generated learner inputs, experiment outputs, or execution records.

The per-lab intent file is named **BRIEF.md**. The detailed procedure is in the lab **README.md**, including its run prompts and checks. There is currently no separate INTENT.md or dedicated SKILL.md in each lab folder. Seven shared skills provide the common agent procedures; the tutor reads the selected lab and its brief.

The authored course is on [codex/rsi-masterclass-rebuild](https://github.com/dlmastery/simple-coding-harness/tree/codex/rsi-masterclass-rebuild/rsi). If you see the old eighteen-step RSI course on GitHub, check the selected branch.

## Whole-course intent and skills

| Source | What it defines |
|---|---|
| [Requirements and restart notes](../how-did-i-generate-it/rsi/RSI-STEERING-AND-RESTART.md) | The complete user requirements, accepted changes, and current priority |
| [Masterclass plan](../how-did-i-generate-it/rsi/RSI-MASTERCLASS-PLAN.md) | Learning progression, research treatment, architecture, and acceptance criteria |
| [Reusable course-building skill](../skills/build-research-codelabs/SKILL.md) | How to build a course for RSI or another complex topic |
| [Course agent entry point](AGENTS.md) | How an agent enters this course and finds its teaching procedure |
| [RSI tutor](skills/rsi-tutor/SKILL.md) | How to teach and execute one lab, with learner checkpoints |
| [Run an ML experiment](skills/run-ml-experiment/SKILL.md) | How to run one declared ML hypothesis |
| [Review domain meaning](skills/review-domain/SKILL.md) | How to check data, metrics, splits, and evidence meanings |
| [Improve a research skill](skills/improve-research-skill/SKILL.md) | How to propose and compare a procedural change |
| [Build an ML harness](skills/build-ml-harness/SKILL.md) | How to generate a harness from a readable brief |
| [Audit an RSI claim](skills/audit-rsi-claim/SKILL.md) | How to match a claim to its evidence |
| [Scale an experiment](skills/scale-experiment/SKILL.md) | How to preserve the experiment contract on larger compute |

## Per-lab source instructions

Open a lesson for the complete procedure, or its brief for the compact intent and constraints. The authoring module is the maintained source used to publish those Markdown files. Students read the Markdown and speak to the agent; they do not edit the publisher code.

### 00 · Start with a prediction — 4 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 00.01 | [Meet the prediction task](00_start_here/step_01_meet_the_task/README.md) | [BRIEF.md](00_start_here/step_01_meet_the_task/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 00.02 | [Prepare a workspace you can inspect](00_start_here/step_02_prepare_the_workspace/README.md) | [BRIEF.md](00_start_here/step_02_prepare_the_workspace/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 00.03 | [Run one baseline](00_start_here/step_03_one_attempt/README.md) | [BRIEF.md](00_start_here/step_03_one_attempt/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 00.04 | [Check the evidence behind the answer](00_start_here/step_04_check_the_evidence/README.md) | [BRIEF.md](00_start_here/step_04_check_the_evidence/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |

### 01 · Make one process dependable — 5 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 01.01 | [Write the data science process](01_process_without_loops/step_01_describe_the_process/README.md) | [BRIEF.md](01_process_without_loops/step_01_describe_the_process/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 01.02 | [Run the process without changing it](01_process_without_loops/step_02_run_the_process/README.md) | [BRIEF.md](01_process_without_loops/step_02_run_the_process/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 01.03 | [Turn the process into a skill](01_process_without_loops/step_03_make_a_skill/README.md) | [BRIEF.md](01_process_without_loops/step_03_make_a_skill/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 01.04 | [Check outputs with a separate calculation](01_process_without_loops/step_04_separate_the_check/README.md) | [BRIEF.md](01_process_without_loops/step_04_separate_the_check/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 01.05 | [Reuse the skill in a fresh session](01_process_without_loops/step_05_reuse_the_skill/README.md) | [BRIEF.md](01_process_without_loops/step_05_reuse_the_skill/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |

### 02 · Repeat for a reason — 6 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 02.01 | [Let a failure motivate a second attempt](02_loop_engineering/step_01_why_repeat/README.md) | [BRIEF.md](02_loop_engineering/step_01_why_repeat/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 02.02 | [Give the loop state and a budget](02_loop_engineering/step_02_bounded_state/README.md) | [BRIEF.md](02_loop_engineering/step_02_bounded_state/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 02.03 | [Turn an error into a different action](02_loop_engineering/step_03_use_feedback/README.md) | [BRIEF.md](02_loop_engineering/step_03_use_feedback/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 02.04 | [Stop repeated failure and oscillation](02_loop_engineering/step_04_stop_the_loop/README.md) | [BRIEF.md](02_loop_engineering/step_04_stop_the_loop/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 02.05 | [Resume without losing the experiment](02_loop_engineering/step_05_resume/README.md) | [BRIEF.md](02_loop_engineering/step_05_resume/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |
| 02.06 | [Compare two ways to spend the same attempts](02_loop_engineering/step_06_compare_loops/README.md) | [BRIEF.md](02_loop_engineering/step_06_compare_loops/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-foundation.mjs) |

### 03 · Give different cases different routes — 6 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 03.01 | [Draw the dependencies](03_graph_engineering/step_01_dependencies/README.md) | [BRIEF.md](03_graph_engineering/step_01_dependencies/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 03.02 | [Route different failures differently](03_graph_engineering/step_02_branch/README.md) | [BRIEF.md](03_graph_engineering/step_02_branch/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 03.03 | [Join independent checks](03_graph_engineering/step_03_join/README.md) | [BRIEF.md](03_graph_engineering/step_03_join/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 03.04 | [Put a bounded retry inside the graph](03_graph_engineering/step_04_cycle/README.md) | [BRIEF.md](03_graph_engineering/step_04_cycle/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 03.05 | [Resume only the affected work](03_graph_engineering/step_05_recover/README.md) | [BRIEF.md](03_graph_engineering/step_05_recover/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 03.06 | [Read the plan, data flow, and trace](03_graph_engineering/step_06_three_views/README.md) | [BRIEF.md](03_graph_engineering/step_06_three_views/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |

### 04 · Agree on what the experiment means — 5 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 04.01 | [Name the objects in an experiment](04_ontology_engineering/step_01_entities/README.md) | [BRIEF.md](04_ontology_engineering/step_01_entities/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 04.02 | [Connect data, models, and evidence](04_ontology_engineering/step_02_relations/README.md) | [BRIEF.md](04_ontology_engineering/step_02_relations/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 04.03 | [State rules that must always hold](04_ontology_engineering/step_03_invariants/README.md) | [BRIEF.md](04_ontology_engineering/step_03_invariants/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 04.04 | [Catch a plausible but invalid experiment](04_ontology_engineering/step_04_catch_contradictions/README.md) | [BRIEF.md](04_ontology_engineering/step_04_catch_contradictions/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |
| 04.05 | [Change a definition without losing its consequences](04_ontology_engineering/step_05_evolve_vocabulary/README.md) | [BRIEF.md](04_ontology_engineering/step_05_evolve_vocabulary/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-structure.mjs) |

### 05 · Build capability around the model — 5 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 05.01 | [Combine fixed components into a useful system](05_system_intelligence/step_01_combine_components/README.md) | [BRIEF.md](05_system_intelligence/step_01_combine_components/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 05.02 | [Choose a skill for the task](05_system_intelligence/step_02_route_tasks/README.md) | [BRIEF.md](05_system_intelligence/step_02_route_tasks/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 05.03 | [Retrieve what matters and retain task state](05_system_intelligence/step_03_context_and_state/README.md) | [BRIEF.md](05_system_intelligence/step_03_context_and_state/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 05.04 | [Coordinate planning, execution, and checking](05_system_intelligence/step_04_coordinate/README.md) | [BRIEF.md](05_system_intelligence/step_04_coordinate/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 05.05 | [Find which component makes the difference](05_system_intelligence/step_05_ablate_system/README.md) | [BRIEF.md](05_system_intelligence/step_05_ablate_system/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |

### 06 · Generate a harness from a brief — 6 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 06.01 | [Describe the harness you need](06_meta_harness_engineering/step_01_write_a_brief/README.md) | [BRIEF.md](06_meta_harness_engineering/step_01_write_a_brief/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 06.02 | [Generate a first harness](06_meta_harness_engineering/step_02_generate/README.md) | [BRIEF.md](06_meta_harness_engineering/step_02_generate/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 06.03 | [Inspect what the builder decided](06_meta_harness_engineering/step_03_inspect_generated/README.md) | [BRIEF.md](06_meta_harness_engineering/step_03_inspect_generated/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 06.04 | [Test the generated harness’s boundaries](06_meta_harness_engineering/step_04_test_refusal/README.md) | [BRIEF.md](06_meta_harness_engineering/step_04_test_refusal/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 06.05 | [Generate a classification harness](06_meta_harness_engineering/step_05_second_task/README.md) | [BRIEF.md](06_meta_harness_engineering/step_05_second_task/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |
| 06.06 | [Recreate and compare generated harnesses](06_meta_harness_engineering/step_06_recreate/README.md) | [BRIEF.md](06_meta_harness_engineering/step_06_recreate/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-systems.mjs) |

### 07 · Separate the self-* ideas — 8 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 07.01 | [Correct one result](07_understanding_self_star/step_01_correction/README.md) | [BRIEF.md](07_understanding_self_star/step_01_correction/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.02 | [Test a reflection before trusting it](07_understanding_self_star/step_02_reflection/README.md) | [BRIEF.md](07_understanding_self_star/step_02_reflection/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.03 | [Retain and use a lesson](07_understanding_self_star/step_03_persistent_learning/README.md) | [BRIEF.md](07_understanding_self_star/step_03_persistent_learning/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.04 | [Improve a task skill with a fixed procedure](07_understanding_self_star/step_04_self_improvement/README.md) | [BRIEF.md](07_understanding_self_star/step_04_self_improvement/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.05 | [Let work reorganize under local rules](07_understanding_self_star/step_05_organization/README.md) | [BRIEF.md](07_understanding_self_star/step_05_organization/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.06 | [Observe a collective pattern](07_understanding_self_star/step_06_emergence/README.md) | [BRIEF.md](07_understanding_self_star/step_06_emergence/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.07 | [Learn what self-play does and does not provide](07_understanding_self_star/step_07_self_play/README.md) | [BRIEF.md](07_understanding_self_star/step_07_self_play/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 07.08 | [Make a self-modification inspectable](07_understanding_self_star/step_08_modification/README.md) | [BRIEF.md](07_understanding_self_star/step_08_modification/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |

### 08 · Measure what improved — 6 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 08.01 | [Distinguish a result from a reliable comparison](08_measuring_improvement/step_01_repeat_measurement/README.md) | [BRIEF.md](08_measuring_improvement/step_01_repeat_measurement/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 08.02 | [Freeze selection before final evaluation](08_measuring_improvement/step_02_final_boundary/README.md) | [BRIEF.md](08_measuring_improvement/step_02_final_boundary/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 08.03 | [Count the cost of research](08_measuring_improvement/step_03_cost/README.md) | [BRIEF.md](08_measuring_improvement/step_03_cost/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 08.04 | [Separate the effects of memory and procedure changes](08_measuring_improvement/step_04_ablation/README.md) | [BRIEF.md](08_measuring_improvement/step_04_ablation/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 08.05 | [Test whether the lesson transfers](08_measuring_improvement/step_05_transfer/README.md) | [BRIEF.md](08_measuring_improvement/step_05_transfer/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 08.06 | [Reject a misleading win and roll back](08_measuring_improvement/step_06_rollback/README.md) | [BRIEF.md](08_measuring_improvement/step_06_rollback/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |

### 09 · Improve the improvement procedure — 7 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 09.01 | [Identify the solver, improver, and evaluator](09_recursive_self_improvement/step_01_three_objects/README.md) | [BRIEF.md](09_recursive_self_improvement/step_01_three_objects/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.02 | [Run repeated improvement with an unchanged improver](09_recursive_self_improvement/step_02_fixed_improver/README.md) | [BRIEF.md](09_recursive_self_improvement/step_02_fixed_improver/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.03 | [Propose a change to the improver](09_recursive_self_improvement/step_03_revise_improver/README.md) | [BRIEF.md](09_recursive_self_improvement/step_03_revise_improver/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.04 | [Use the revised improver in the next round](09_recursive_self_improvement/step_04_inherit/README.md) | [BRIEF.md](09_recursive_self_improvement/step_04_inherit/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.05 | [Measure whether the revised improver helps](09_recursive_self_improvement/step_05_compare_improvers/README.md) | [BRIEF.md](09_recursive_self_improvement/step_05_compare_improvers/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.06 | [Run bounded recursive generations](09_recursive_self_improvement/step_06_bounded_generations/README.md) | [BRIEF.md](09_recursive_self_improvement/step_06_bounded_generations/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |
| 09.07 | [State the result without overstating it](09_recursive_self_improvement/step_07_claim/README.md) | [BRIEF.md](09_recursive_self_improvement/step_07_claim/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-improvement.mjs) |

### 10 · Read and rebuild recent research — 38 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 10.01 | [Use a framework without turning it into a ladder](10_research_studio/00_reading_frontier_research/step_01_framework/README.md) | [BRIEF.md](10_research_studio/00_reading_frontier_research/step_01_framework/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.02 | [Audit a frontier announcement](10_research_studio/00_reading_frontier_research/step_02_announcements/README.md) | [BRIEF.md](10_research_studio/00_reading_frontier_research/step_02_announcements/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.03 | [Choose experiments that reduce uncertainty](10_research_studio/01_memory_and_exploration/step_03_exploration/README.md) | [BRIEF.md](10_research_studio/01_memory_and_exploration/step_03_exploration/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.04 | [Verify the outcome, then let the actor write memory](10_research_studio/01_memory_and_exploration/step_04_actor_memory/README.md) | [BRIEF.md](10_research_studio/01_memory_and_exploration/step_04_actor_memory/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.05 | [Evaluate with memory frozen](10_research_studio/01_memory_and_exploration/step_05_frozen_memory/README.md) | [BRIEF.md](10_research_studio/01_memory_and_exploration/step_05_frozen_memory/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.06 | [Separate working state from reusable experience](10_research_studio/01_memory_and_exploration/step_06_working_and_experience/README.md) | [BRIEF.md](10_research_studio/01_memory_and_exploration/step_06_working_and_experience/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.07 | [Build a tree of attempted solutions](10_research_studio/02_dream_rsi/step_07_discovery_tree/README.md) | [BRIEF.md](10_research_studio/02_dream_rsi/step_07_discovery_tree/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.08 | [Replay only what the history can answer](10_research_studio/02_dream_rsi/step_08_replay/README.md) | [BRIEF.md](10_research_studio/02_dream_rsi/step_08_replay/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.09 | [Test the replay winner on fresh work](10_research_studio/02_dream_rsi/step_09_online/README.md) | [BRIEF.md](10_research_studio/02_dream_rsi/step_09_online/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.10 | [Localize a harness problem](10_research_studio/03_modular_harness_evolution/step_10_localize/README.md) | [BRIEF.md](10_research_studio/03_modular_harness_evolution/step_10_localize/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.11 | [Integrate edits and test transfer](10_research_studio/03_modular_harness_evolution/step_11_integrate/README.md) | [BRIEF.md](10_research_studio/03_modular_harness_evolution/step_11_integrate/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.12 | [Compare agent evolution and improver evolution](10_research_studio/03_modular_harness_evolution/step_12_lineage/README.md) | [BRIEF.md](10_research_studio/03_modular_harness_evolution/step_12_lineage/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.13 | [Inspect an inner ML researcher](10_research_studio/04_aide2/step_13_inner_research/README.md) | [BRIEF.md](10_research_studio/04_aide2/step_13_inner_research/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.14 | [Improve the inner researcher under a total budget](10_research_studio/04_aide2/step_14_outer_research/README.md) | [BRIEF.md](10_research_studio/04_aide2/step_14_outer_research/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.15 | [Test the ignition claim separately](10_research_studio/04_aide2/step_15_ignition/README.md) | [BRIEF.md](10_research_studio/04_aide2/step_15_ignition/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.16 | [Improve task skills with a fixed pipeline](10_research_studio/05_meta_skill_evolution/step_16_task_skills/README.md) | [BRIEF.md](10_research_studio/05_meta_skill_evolution/step_16_task_skills/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.17 | [Update the skill updater on a slower schedule](10_research_studio/05_meta_skill_evolution/step_17_meta_skills/README.md) | [BRIEF.md](10_research_studio/05_meta_skill_evolution/step_17_meta_skills/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-research.mjs) |
| 10.18 | [Turn a limitation into a scientific hypothesis](10_research_studio/06_scientist_two/step_18_hypothesis/README.md) | [BRIEF.md](10_research_studio/06_scientist_two/step_18_hypothesis/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.19 | [Screen ideas and test their contributions](10_research_studio/06_scientist_two/step_19_screen_ablate/README.md) | [BRIEF.md](10_research_studio/06_scientist_two/step_19_screen_ablate/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.20 | [Answer a criticism with evidence](10_research_studio/06_scientist_two/step_20_review_rebuttal/README.md) | [BRIEF.md](10_research_studio/06_scientist_two/step_20_review_rebuttal/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.21 | [Distinguish better discoveries from a better scientist](10_research_studio/06_scientist_two/step_21_successive_results/README.md) | [BRIEF.md](10_research_studio/06_scientist_two/step_21_successive_results/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.22 | [Turn a researcher correction into a task](10_research_studio/07_sciencebuddy/step_22_human_task/README.md) | [BRIEF.md](10_research_studio/07_sciencebuddy/step_22_human_task/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.23 | [Adapt the harness to the rubric](10_research_studio/07_sciencebuddy/step_23_harness_adaptation/README.md) | [BRIEF.md](10_research_studio/07_sciencebuddy/step_23_harness_adaptation/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.24 | [See what grouped rewards contribute](10_research_studio/07_sciencebuddy/step_24_grpo/README.md) | [BRIEF.md](10_research_studio/07_sciencebuddy/step_24_grpo/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.25 | [Track model–harness pairs across cycles](10_research_studio/07_sciencebuddy/step_25_coevolution/README.md) | [BRIEF.md](10_research_studio/07_sciencebuddy/step_25_coevolution/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.26 | [Read the ScienceBuddy results precisely](10_research_studio/07_sciencebuddy/step_26_audit_results/README.md) | [BRIEF.md](10_research_studio/07_sciencebuddy/step_26_audit_results/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-science.mjs) |
| 10.27 | [Keep traces, knowledge, and active skills separate](10_research_studio/08_skills_and_procedures/step_27_wiki/README.md) | [BRIEF.md](10_research_studio/08_skills_and_procedures/step_27_wiki/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.28 | [Refine a procedure graph](10_research_studio/08_skills_and_procedures/step_28_procedural_graph/README.md) | [BRIEF.md](10_research_studio/08_skills_and_procedures/step_28_procedural_graph/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.29 | [Repair a skill for an experiment-results page](10_research_studio/08_skills_and_procedures/step_29_gui/README.md) | [BRIEF.md](10_research_studio/08_skills_and_procedures/step_29_gui/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.30 | [Reduce cost without hiding quality loss](10_research_studio/09_efficient_harnesses/step_30_cost_quality/README.md) | [BRIEF.md](10_research_studio/09_efficient_harnesses/step_30_cost_quality/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.31 | [Compare harness generation and harness improvement](10_research_studio/09_efficient_harnesses/step_31_harness_builders/README.md) | [BRIEF.md](10_research_studio/09_efficient_harnesses/step_31_harness_builders/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.32 | [Compare raw history and summarized memory](10_research_studio/10_feedback_and_transfer/step_32_memory_interface/README.md) | [BRIEF.md](10_research_studio/10_feedback_and_transfer/step_32_memory_interface/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.33 | [Compare action hints and richer observations](10_research_studio/10_feedback_and_transfer/step_33_scaffolding/README.md) | [BRIEF.md](10_research_studio/10_feedback_and_transfer/step_33_scaffolding/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.34 | [Keep model training aligned with its harness](10_research_studio/10_feedback_and_transfer/step_34_model_harness_fit/README.md) | [BRIEF.md](10_research_studio/10_feedback_and_transfer/step_34_model_harness_fit/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.35 | [Compose changes to data, harness, and model](10_research_studio/11_composition_and_reference_learning/step_35_metarsi/README.md) | [BRIEF.md](10_research_studio/11_composition_and_reference_learning/step_35_metarsi/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.36 | [Diagnose failures with checked reference trajectories](10_research_studio/11_composition_and_reference_learning/step_36_harnessevolve/README.md) | [BRIEF.md](10_research_studio/11_composition_and_reference_learning/step_36_harnessevolve/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.37 | [Compare systems without flattening their differences](10_research_studio/12_evidence_and_open_questions/step_37_compare_systems/README.md) | [BRIEF.md](10_research_studio/12_evidence_and_open_questions/step_37_compare_systems/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |
| 10.38 | [Reason about bottlenecks and acceleration](10_research_studio/12_evidence_and_open_questions/step_38_economics/README.md) | [BRIEF.md](10_research_studio/12_evidence_and_open_questions/step_38_economics/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-frontier.mjs) |

### 11 · Build, transfer, and explain — 5 labs

| Lab | Purpose and procedure | Intent brief | Authoring module |
|---|---|---|---|
| 11.01 | [Build a harness for a new prediction brief](11_capstones/step_01_new_harness/README.md) | [BRIEF.md](11_capstones/step_01_new_harness/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-capstone.mjs) |
| 11.02 | [Run and audit a bounded recursive experiment](11_capstones/step_02_recursive_experiment/README.md) | [BRIEF.md](11_capstones/step_02_recursive_experiment/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-capstone.mjs) |
| 11.03 | [Test transfer and portability separately](11_capstones/step_03_portability/README.md) | [BRIEF.md](11_capstones/step_03_portability/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-capstone.mjs) |
| 11.04 | [Audit an unfamiliar RSI claim](11_capstones/step_04_external_audit/README.md) | [BRIEF.md](11_capstones/step_04_external_audit/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-capstone.mjs) |
| 11.05 | [Teach the mechanism and defend the evidence](11_capstones/step_05_teach_back/README.md) | [BRIEF.md](11_capstones/step_05_teach_back/BRIEF.md) | [Source](../how-did-i-generate-it/rsi/scripts/lessons-capstone.mjs) |

## Supporting authoring sources

The [lesson index](../how-did-i-generate-it/rsi/scripts/lesson-content.mjs) assembles the themed modules. [Teaching guidance](../how-did-i-generate-it/rsi/scripts/lesson-guidance.mjs) supplies worked examples, output explanations, recovery, and quiz hints. [Research-group introductions](../how-did-i-generate-it/rsi/scripts/research-groups.mjs) supply the advanced group walkthroughs.

[Technical diagram source](../how-did-i-generate-it/rsi/scripts/lesson-diagrams.mjs), [selected illustration captions](../how-did-i-generate-it/rsi/scripts/lesson-illustrations.mjs), and [image prompts and revisions](../how-did-i-generate-it/rsi/visuals/generated/README.md) preserve the visual authoring work.

The [lesson publisher](../how-did-i-generate-it/rsi/scripts/build-lessons.mjs) rebuilds the readable course and invokes [this index publisher](../how-did-i-generate-it/rsi/scripts/build-source-index.mjs). A source file establishes authored instructions; it does not establish successful execution.
