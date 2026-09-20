// Reviewed conceptual illustrations. Exact prompts and rejected versions are
// retained in ../visuals/generated/. These are not experimental result plots.
export const illustrations = {
  '00.01': {
    file: 'target-leakage-v2.png',
    alt: 'Calendar and observed weather enter the model. Casual and registered counts add to total rentals, so their shortcut into features is blocked. Prediction and observation meet at the error check.',
    caption: 'The component counts already reveal the answer: casual + registered = total rentals. Keep them out of the input features. The checker still needs the observed total to measure error. This course uses observed weather for a retrospective teaching task; it does not assume that weather was known a day ahead.'
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
  '10.08': {
    file: 'replay-boundary-v2.png',
    alt: 'Replay follows a recorded baseline and tried change, while a failed attempt remains archived. It stops before an untried branch whose outcome is unknown. A separate new execution would produce a new report.',
    caption: 'The left panel is the record before another run. Replay can reuse its supported outcomes and failure status; it cannot supply D’s missing result. The right panel shows the additional execution needed to extend that record. This is a classroom mechanism inspired by Dream-RSI, not a reproduction of its benchmark or a claim that all counterfactual policies are covered.'
  },
  '10.25': {
    file: 'model-harness-v2.png',
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
illustrations['theme-07']=illustrations['07.08'];

export function renderIllustration(id, to) {
  const item = illustrations[id];
  if (!item) return '';
  const path = to(`assets/illustrations/${item.file}`);
  return `![${item.alt}](${path})\n\n*${item.caption}*\n\n[Open the illustration at full size](${path}).`;
}
