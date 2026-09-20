// Human-authored introductions and names; do not derive scientific names from slugs.
export const researchGroups = {
  '00_reading_frontier_research': {
    title:'Read a frontier claim', question:'Which claim does the available evidence support?',
    intro:'Begin with the claim audit you already know how to make. Apply it to a framework, then follow a current announcement to its primary evidence. Keep publication date, mechanism, reported result, and independent verification separate.',
    entry:'Bring the local evidence audit from 09.07. You need a browser or research tool for primary sources; these first two studio labs require no model fits.',
    exit:'Keep a source-linked framework map and one claim card. Use the same questions throughout the studio so unfamiliar names do not replace your judgment.'
  },
  '01_memory_and_exploration': {
    title:'Exploration and memory', question:'What should a system learn from an experiment, and what should it retain?',
    intro:'Start with broad probes of the familiar bike task, then use their errors to choose a focused follow-up. Separate checking a result from writing a lesson about it. Freeze memory when measuring its effect, and keep current run state distinct from reusable experience.',
    entry:'Bring the bike task contract, result checker, and memory distinctions from theme 07. The tutor prepares fresh bounded workspaces and identifies any shared-context comparison.',
    exit:'Keep the exploration plan, outcome verdict, memory comparison, and two-store retrieval checks. Next, give the experiment history a structure that can support replay.'
  },
  '02_dream_rsi': {
    title:'Dream-RSI: history, replay, and new evidence', question:'What can a saved discovery history answer without another experiment?',
    intro:'Build a small tree from actual ML attempts. Use that recorded structure to compare replay policies, keeping absent outcomes unknown. Finally, return to fresh work and test whether the replay-selected policy still helps.',
    entry:'Use a new bike workspace, a three-attempt plan, and the task/evaluation boundaries learned earlier. The later online comparison has its own declared budget.',
    exit:'Keep separate records for history collection, replay selection, and online confirmation, including their costs. A successful replay does not supply evidence for an unvisited branch.'
  },
  '03_modular_harness_evolution': {
    title:'Local changes and their interactions', question:'Which component failed, and does its repair still work in the whole system?',
    intro:'Diagnose one interface or action from contrasting traces. Restrict the edit, then test how it interacts with a second change. Finish by distinguishing a lineage of changed agents from a lineage of changed improvement procedures.',
    entry:'Bring one valid and one failed workflow trace, versioned harness components, and your solver/improver map. The integration activity uses seven small fixtures and no training.',
    exit:'Keep a localized patch, an integration report, and a typed lineage. These records prepare the nested-research examples without treating every generation as RSI.'
  },
  '04_aide2': {
    title:'AIDE²: researchers as the object of an experiment', question:'Does a better researcher also become better at improving researchers?',
    intro:'First expose the proposal and selection rules of an inner ML researcher. Then compare a change to that researcher under a total outer budget. Finally, test the distinct question of using the resulting researcher as an improver.',
    entry:'Bring the fixed bike evaluator and bounded-loop skills. The source is an explicitly dated July foundation requested for the course, not a new September release.',
    exit:'Keep inner-search traces, the outer comparison, and the separate ignition audit. A task-search gain cannot answer the role-transfer question by itself.'
  },
  '05_meta_skill_evolution': {
    title:'Task skills and the skills that revise them', question:'What changes when the updater itself is revised?',
    intro:'Establish a task-skill update under one fixed meta-skill. Then use accumulated evidence to propose a less frequent updater revision and trace its effect on a later round. Keep the two version histories separate.',
    entry:'Bring task-skill traces and the same fixed-evaluator discipline used in theme 09. Prepare missing prerequisite traces explicitly instead of inventing prior rounds.',
    exit:'Keep the fixed baseline, revised updater, schedule, and behavioral inheritance record. Distinguish the existence of the feedback path from evidence that it helps.'
  },
  '06_scientist_two': {
    title:'ScientistTwo: hypotheses, experiments, and review', question:'What turns a promising idea into evidence that another researcher can assess?',
    intro:'Use the bike task to write a falsifiable hypothesis, screen ideas, test a contribution, and answer a criticism with another experiment. Then inspect the difference between better research outputs and a better research procedure.',
    entry:'Bring the baseline predictions and selection error slices. Keep final outcomes out of hypothesis development, and label the reviewer as agent-generated when no human reviewer participates.',
    exit:'Keep the hypothesis, screening and ablation records, response, and discovery lineage. Each conclusion should name its measured object and remain open to a negative result.'
  },
  '07_sciencebuddy': {
    title:'ScienceBuddy: feedback, harness changes, and weight learning', question:'How do human requests, executable checks, and learning updates connect?',
    intro:'Start with a labelled correction about the wine report. Turn it into a rubric and revise the reporting skill. Then inspect grouped rewards numerically, simulate model–harness interactions, and audit the paper’s reported metrics. Each activity states whether it is execution, arithmetic, simulation, or source review.',
    entry:'Bring wine predictions and the distinction between external skills and model parameters. The required path does not train an LLM; larger training needs its own source-aligned plan.',
    exit:'Keep rubric verdicts, skill versions, the numerical update, pair records, and a source-scoped result audit. Do not combine synthetic values, local measurements, and paper results into one score.'
  },
  '08_skills_and_procedures': {
    title:'Experience, executable procedures, and interface skills', question:'How should a useful lesson become an active procedure?',
    intro:'Separate original traces, retained knowledge, and accepted skills. Refine a procedure graph without confusing it with a domain ontology. Then apply the same evidence discipline to a local experiment-results page and a visible UI mistake.',
    entry:'Bring a failed skill proposal, the workflow graph, and saved candidate metrics. Live UI execution requires a browser-capable agent; missing capability stays explicit.',
    exit:'Keep the rejected-edit knowledge, tested graph transition, and actual UI traces. A stored lesson or critic approval is not a substitute for observed behavior.'
  },
  '09_efficient_harnesses': {
    title:'Efficient harnesses and their builders', question:'What can become cheaper without weakening the task?',
    intro:'Define the quality floor before removing redundant work. Count the cost of finding and checking the change. Then separate the quality of a generated harness from the quality of the procedure that generates harnesses.',
    entry:'Bring the generated wine harness and cost ledger. Use existing fixtures where possible and retain unknown inference costs as unknown.',
    exit:'Keep a quality/cost comparison and a source-linked builder/harness map. A shorter trace or a better generated artifact does not establish a better builder.'
  },
  '10_feedback_and_transfer': {
    title:'Feedback, memory, and compatibility', question:'Which information changes behavior, and will it still fit the surrounding system?',
    intro:'Compare raw events with compact memory, distinguish action hints from richer observations, and test a local interface mismatch. These small checks make it easier to read training papers without mistaking a prompt intervention for a parameter update.',
    entry:'The tutor creates exact-checker fixtures with explicit budgets. Bring the earlier information-boundary and model/harness distinctions.',
    exit:'Keep all memory conditions, assistance traces, and parser failures. Identify which claims require actual weight training beyond these classroom exercises.'
  },
  '11_composition_and_reference_learning': {
    title:'Compose changes and learn from references', question:'How can several improvement operations share evidence without corrupting it?',
    intro:'Use a typed simulation to track data, harness, model, and scheduler versions. Then inspect reference trajectories: a known answer can guide diagnosis, but copied answers and invalid shortcuts must not become active skills.',
    entry:'Bring the ontology, lineage, and valid/failed workflow traces. Keep the scheduler exercise synthetic and the reference checks executable.',
    exit:'Keep the inherited scheduling trace, stale-evidence refusals, checked references, and regression decisions. These prepare the final comparison of systems and their evidence.'
  },
  '12_evidence_and_open_questions': {
    title:'Compare evidence and examine bottlenecks', question:'Which stronger claims still need another experiment?',
    intro:'Compare six source systems and your own experiment with the same questions about changes, feedback, inheritance, evaluation, and cost. Then use a small calculator to separate faster components from faster total research and cumulative gains from acceleration.',
    entry:'Bring the studio audits and your actual cost ledger. Keep unknown source details unresolved and synthetic timing separate from measurements.',
    exit:'Keep the comparison matrix and acceleration audit. The capstones ask you to apply this judgment to a new task, a new claim, and a peer handoff.'
  },
};
