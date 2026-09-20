// Reviewed conceptual illustrations. Exact prompts and rejected versions are
// retained in ../visuals/generated/. These are not experimental result plots.
export const illustrations = {
  '00.01': {
    file: 'target-leakage-v2.png',
    alt: 'Calendar and observed weather enter the model. Casual and registered counts add to total rentals, so their shortcut into features is blocked. Prediction and observation meet at the error check.',
    caption: 'The component counts already reveal the answer: casual + registered = total rentals. Keep them out of the input features. The checker still needs the observed total to measure error. This course uses observed weather for a retrospective teaching task; it does not assume that weather was known a day ahead.'
  },
  '01.01': {
    file: 'data-science-process-v4.png',
    alt: 'Five actions frame hourly bike demand, inspect data, define chronological train/selection/final partitions, fit a training-median baseline, and compare selection predictions with targets.',
    caption: 'Follow the numbered actions once. Train supplies the fitted median; the matching Selection labels identify the rows used for checking. Final stays reserved. The inspection checkmarks name work to complete, not proof about your run. Observed weather makes this a retrospective task, and the public data are not access-controlled. A checked baseline is the starting evidence for later improvement.'
  },
  '02.02': {
    file: 'bounded-loop-v1.png',
    alt: 'Propose, run, check, and record surround persistent state. A limit gate leads to the next attempt or stop. A failed fit is recorded and still consumes an attempt. Resumption reads the same saved state.',
    caption: 'The notebook survives the process. Read the remaining budget before another attempt, reserve that attempt before fitting, and preserve failures. A successful fit still needs checking. After interruption, reconcile any in-progress attempt before deciding what can run next; do not reset the allowance.'
  },
  '04.02': {
    file: 'graph-ontology-v1.png',
    alt: 'A workflow graph routes valid data toward fitting and invalid data toward repair. Separate domain relations say the scaler is fit on training data, search selects on selection data, and the model is measured by MAE.',
    caption: 'Read the left arrows as dependencies between actions. Read the right arrows as sentences about domain meaning. These are selected facts and one rule, not a complete ontology. Correct execution order cannot rescue a leaked feature or the wrong metric. A declared fact also needs evidence that the implementation follows it.'
  },
  '05.04': {
    file: 'system-coordination-v3.png',
    alt: 'Numbered steps read ready, save running, and fit candidate C1. Saved awaiting-check state survives a process exit. A new process checks C1; a C2 report, missing check, or unclear target cannot complete the task.',
    caption: 'Read steps 1, 2, and 3 in order: starting the fit requires running to be saved first. Matching C1 labels connect the scenes across the process boundary. The checkmarks illustrate a possible accepted handoff, not a new measured run. A missing check leaves work pending; a wrong candidate is refused. The coordinator remains fixed. Its read-only label describes the procedure, not an independently enforced permission boundary.'
  },
  '06.02': {
    file: 'meta-harness-v2.png',
    alt: 'A task brief enters an unchanged meta-harness builder. It produces a separate package of skills, tools, state, checks, and limits. The package then runs a model and produces predictions and a checked report.',
    caption: 'In this example the builder stays fixed. It creates a package that must then run under the brief’s limits. Files alone do not show that the package works. A checked execution provides evidence about the generated harness; it does not establish that the builder improved itself.'
  },
  '07.08': {
    file: 'self-star-v2.png',
    alt: 'Eight parallel examples show current-output correction, tested reflection, retained learning, task-skill improvement under a fixed improver, local reorganization, emergence, self-play under a fixed update rule, and active instruction modification.',
    caption: 'These are examples of mechanisms, not mutually exclusive categories or a maturity ladder. A system can combine them. The self-play panel changes policy values under a fixed update rule; the modification panel changes active instructions without proving a benefit. The emergence drawing is a conceptual group-pattern analogy, not a measurement from the queue exercise. Ask what changed, what persisted, and how its effect was checked.'
  },
  '09.01': {
    file: 'main-overview-v2.png',
    alt: 'Three objects can change: a task model, a research skill, and the improver that revises skills. A proposed improver is checked, accepted or rejected, and an accepted version governs a later round under fixed evaluation.',
    caption: 'This is a conceptual path, not a measured success story. The last panel shows what an accepted revision would require: the later round reads I1 and uses its added counterexample check. Saving I1 alone is insufficient. Whether it helps requires a fair comparison; rejection remains a valid result.'
  },
  '09.04': {
    file: 'inherited-improver-v1.png',
    alt: 'A proposed improver adds a contrasting-case check. Acceptance activates that same version in a later round, where the new check is executed. Rejection keeps I0 active. A later task-skill proposal can also be rejected.',
    caption: 'The highlighted instruction appears in proposed I1, active I1, and the later executed check. That connection matters more than a new filename. The image shows a possible accepted path; the course’s two-generation comparison rejected both improver proposals. An inherited change can also perform worse. Keep version identity, observed use, and measured benefit as separate claims.'
  },
  '10.04': {
    file: 'actor-memory-v2.png',
    alt: 'A curriculum selects practice. The actor executes an experiment, the verifier checks observed evidence, and the actor writes a bounded memory. After exploration, the memory is frozen and read on a later task.',
    caption: 'The verdict concerns the task outcome. The actor still has to interpret it and can write an overbroad lesson. The notebook fields are our teaching aid, not a required paper format. This figure adapts RSIAgent’s responsibility split to the laptop ML exercise. It does not reproduce the paper’s environments or establish that the memory-writing procedure improved. Frozen evaluation memory is read without updates.'
  },
  '10.08': {
    file: 'replay-boundary-v2.png',
    alt: 'Replay follows a recorded baseline and tried change, while a failed attempt remains archived. It stops before an untried branch whose outcome is unknown. A separate new execution would produce a new report.',
    caption: 'The left panel is the record before another run. Replay can reuse its supported outcomes and failure status; it cannot supply D’s missing result. The right panel shows the additional execution needed to extend that record. This is a classroom mechanism inspired by Dream-RSI, not a reproduction of its benchmark or a claim that all counterfactual policies are covered.'
  },
  '10.10': {
    file: 'modular-harness-v2.png',
    alt: 'Passing and failing traces differ at a context handoff. Only the Context module changes to preserve candidate identity; the other four modules stay fixed. Original and passing cases, integration, and later transfer need separate checks.',
    caption: 'The missing candidate ID is an original classroom example inspired by ModularRSI. A trace suggests a cause; the restricted edit still needs testing. Empty boxes mark checks to perform, not recorded passes. The same H1 identity appears before and after freezing for transfer. Keeping H1 is a possible outcome; rejection retains the prior harness. The next lab examines two edits and their interaction. This figure does not reproduce a paper benchmark.'
  },
  '10.14': {
    file: 'nested-research-v2.png',
    alt: 'A researcher directs task search. Parent and candidate researchers are compared under the same task and total budget. A separate test uses each as an improver of an identical starting researcher, then executes their proposals.',
    caption: 'R0 and R1 are classroom identities. The middle comparison tests research procedures; the right comparison tests what they produce in the improver role. Neither has a preselected winner. The latter is the separate ignition question discussed in Weco’s July report; its ignition efficiency comparison was not statistically significant. This diagram explains the distinction; it does not reproduce the published run or establish ignition.'
  },
  '10.17': {
    file: 'meta-skill-schedules-v3.png',
    alt: 'Task skills S0, S1, and S2 change under the same updater U0. The pipeline then proposes a change to U0 itself. An accepted U1 uses its new contrasting-case rule on a later S3 proposal before keeping or rejecting it.',
    caption: 'The notebook lines are classroom examples, not complete skills. The updater edits procedures; the task skills direct experiments. Match Activate U1 to Active U1, then follow the same new rule into the later check. Acceptance is a possible path, not a guaranteed gain. The four-line updater is a teaching simplification of MetaSkill-Evolve’s July method. Keep the external comparison fixed and measure later behavior; a saved revision or a slower schedule alone does not establish benefit.'
  },
  '10.18': {
    file: 'scientific-claim-v2.png',
    alt: 'A bike-demand limitation leads to a hypothesis, cheap screening and fuller experiments, matched weather-feature ablation, and an agent review answered by a follow-up experiment with retained records.',
    caption: 'This is a bike-task adaptation of the research stages. The pictured paper and records are illustrative. Each ablation recipe is fitted again; only its permitted feature group changes. Use development evidence for screening and refinement. A review can lead to a narrower or rejected claim, and agent review is not conference acceptance. The illustration does not demonstrate frontier discovery or an improved research procedure.'
  },
  '10.25': {
    file: 'model-harness-v4.png',
    alt: 'Versioned pairs progress from H0 with M0 to H1 with M0, then H1 with M1. The first change edits harness instructions; the second updates model parameters. Training evidence goes to the update, while held-out cases remain in external evaluation.',
    caption: 'Track both versions because a harness and model can interact. First hold M0 fixed while changing the harness; then hold H1 fixed while changing weights. Keep training evidence separate from the cases used for the declared external comparison, and do not feed final results back into selection. This lab illustrates pair accounting with synthetic scores. It does not train an LLM or reproduce ScienceBuddy’s reported gains.'
  },
  'compute': {
    file: 'compute-contract-v2.png',
    alt: 'A research skill passes a versioned experiment contract to an adapter that can select local CPU, accelerator, or cluster execution. Every backend returns an identified attempt record with status and total cost.',
    caption: 'The backends are alternatives. Preserve the scientific contract when moving the same experiment; declare a new one when changing the task, data, or comparison. A candidate can have several submission attempts, so record both identities and all failures. Checkpoint resumption applies only when the job supports it. The course tests the local CPU path; accelerator and cluster adapters still need tests on the actual systems.'
  }
};

// Reuse the reviewed comparison without duplicating its explanatory text.
illustrations['theme-01']=illustrations['01.01'];
illustrations['theme-05']=illustrations['05.04'];
illustrations['theme-07']=illustrations['07.08'];

export function renderIllustration(id, to) {
  const item = illustrations[id];
  if (!item) return '';
  const path = to(`assets/illustrations/${item.file}`);
  return `![${item.alt}](${path})\n\n*${item.caption}*\n\n[Open the illustration at full size](${path}).`;
}
