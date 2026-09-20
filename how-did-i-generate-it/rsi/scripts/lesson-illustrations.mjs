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
  '06.02': {
    file: 'meta-harness-v2.png',
    alt: 'A task brief enters an unchanged meta-harness builder. It produces a separate package of skills, tools, state, checks, and limits. The package then runs a model and produces predictions and a checked report.',
    caption: 'In this example the builder stays fixed. It creates a package that must then run under the brief’s limits. Files alone do not show that the package works. A checked execution provides evidence about the generated harness; it does not establish that the builder improved itself.'
  },
  '09.01': {
    file: 'main-overview-v2.png',
    alt: 'Three objects can change: a task model, a research skill, and the improver that revises skills. A proposed improver is checked, accepted or rejected, and an accepted version governs a later round under fixed evaluation.',
    caption: 'This is a conceptual path, not a measured success story. The last panel shows what an accepted revision would require: the later round reads I1 and uses its added counterexample check. Saving I1 alone is insufficient. Whether it helps requires a fair comparison; rejection remains a valid result.'
  }
};

export function renderIllustration(id, to) {
  const item = illustrations[id];
  if (!item) return '';
  const path = to(`assets/illustrations/${item.file}`);
  return `![${item.alt}](${path})\n\n*${item.caption}*\n\n[Open the illustration at full size](${path}).`;
}
