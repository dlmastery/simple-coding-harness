# Compare complete researchers and their improvers

This is a new study after the closed six-procedure comparison and operator
repair. It does not reopen their budgets or replace their results. Previous
public tasks are exposed development data. The six tasks prepared in
`nested-data/checked` remain reserved for prospective evaluation.

## Three executable objects

A model candidate builds one pipeline. A researcher runs twelve checked model
attempts, reads their feedback, chooses subsequent experiments and retains a
model. An improver reads completed researcher traces and emits the source of a
new complete researcher. Generated researchers include their loop and selection
logic; they are not precomputed lists of twelve task-specific candidates.

The root coding agent authors I0 and its revision I1 from the already observed
failure of narrow local allocation and global-ranking memory. Both are bounded
programs. Neither is a separate LLM agent; neither trains weights or invents
arbitrary algorithms. The rewrite space is deliberately limited and must be
reported. This tests a mechanism inspired by harness improvement and inherited
updaters, not a reproduction of AIDE2 or MetaSkill.

## Development, later revision and evaluation

1. Generate H1-I0 and H1-I1 from the archived eight-attempt comparison traces.
   Their sources and the unchanged H0 source are frozen before training.
2. Execute H0, H1-I0 and H1-I1 on exposed tasks 6, 23, 31, 361235, 361237 and
   361247. Each task/researcher has twelve attempts: **216 search attempts**.
   Freeze all eighteen choices before **18 outer-evaluation refits**. Their
   former final partitions are now known development evaluation, not untouched
   tests. They must never enter candidate fitting or candidate selection.
3. Independently check the complete traces and predictions. For each improver,
   retain its child if mean normalized outer loss improves by at least 0.002
   against H0 and it is no worse on at least four of six tasks, allowing only
   1e-12 numerical equality. Otherwise retain H0. Preserve the rejected child.
4. Execute that same frozen I0 or I1 again, using its retained researcher plus
   the completed first-generation traces and verdict. Save H2-I0 and H2-I1 as
   complete executable source with parent and evidence hashes. This later
   generation must read the inherited improver; saving I1 alone is insufficient.
5. Freeze H2-I0, H2-I1, H0, fixed and random before any reserved-task fitting.
   Run all five on tasks 43, 45, 2074, 361241, 361251 and 361260: **360 search
   attempts**, then freeze all thirty choices before **30 scoring refits**.
   There is no post-score retuning, replacement task or hidden restart.

The whole primary study permits **624 model attempts** including all losing
development searches and both scoring phases. No extra fit is implied by a
source check, failed gate or inconclusive result. Development and evaluation
have separate workspaces and admission markers. This phase does not allocate
a further deployment study. A promoted source is not evidence of deployment.

## Inner comparison contract

Each attempt has one process, one model fit, one thread, seed 41 and a
30-second worker limit including import, prediction and output. No shared fit
cache or retry. Timeout, invalid output and failure consume a fit slot. A
researcher without a successful candidate stops the study; no score is invented.
Record actual process seconds as well as attempt count. A process-scoped Windows
idle-sleep guard avoids the previously observed standby interruption.

Use the checked relative-refinement builder v2 and unchanged ancestor builders.
Every procedure receives the same valid candidate space and constructor-identity
guard. Training-only preprocessing remains inside each pipeline. A constructor
duplicate consumes a proposal but no fit; record the rejection. At most 128
proposals per researcher/task; do not silently enlarge this limit to reach twelve
fits. Known log-target templates require nonnegative training targets. This is
a pre-fit applicability rule, not performance-based task selection.

All procedures first run eight conventional templates. Classifiers use linear,
Extra Trees, RBF C=1, histogram boosting, random forest, RBF C=10 and distance-
weighted neighbors 5/25. Regressors use median, linear, random forest, RBF C=1,
Extra Trees, histogram boosting, RBF C=10 and neighbors 5.

- Fixed adds four sensible revised templates at factor one: wide RBF,
  regularized boosting, unscaled C=100 and native-category boosting for
  classification; absolute boosting, quadratic-plus-spline Ridge, leaf-five
  Extra Trees and tight-epsilon SVR for regression. It is a strong portfolio.
- Random uses seed 9173 + task ID to sample the full valid sixteen-template
  space with log-uniform capacity factors from 0.1 to 10, excluding the
  untunable median. It shares the broad eight-template start.
- H0 spends the remaining four fits on current-incumbent relative refinements.
  Recompute the incumbent after every checked outcome. Try factors 0.5, 2,
  0.25, 4, 0.75, 1.5, 0.125 and 8 cyclically, within the declared factor domain.
  Put the inherited first multiplier before this fixed fallback schedule.
  Keep the 0.5 fallback even when that inherited multiplier changes. The first
  preflight exposed an exhausted tree-refinement set when 0.5 was overwritten
  with 1.0; that zero-fit version remains preserved.
- I0 reads successful post-probe refinement outcomes. If their mean
  selection-minus-training loss exceeds 0.15, reduce the parent's first local
  multiplier by half (bounded at 0.125); otherwise double it (bounded at 8).
  It emits a full researcher with that changed local schedule and no added
  breadth. Use steps after four for the earlier eight-fit traces and after
  eight for the new twelve-fit traces; local refinements have a nonzero model
  parent and a factor other than one. This is the simple inherited updater control.
- I1 retains the eight-template coverage and assigns two remaining fits to
  unused representation/objective alternatives, ranked by checked prior
  same-kind within-task losses. It spends the other two on local refinements,
  alternating between the two best distinct families. The ordering uses only
  observed records; absent alternatives use a fixed name-order fallback.
  If its previous child was rejected, the next rewrite assigns all four
  remaining slots to breadth before considering further local refinement.
  That change is an explicit bounded recovery rule, not a claim that it helps.

Generated source must identify its parent, improver implementation, generation,
evidence and the reason for each next proposal. The proposal builder copies its
model parent's source bundle when a parent exists. Constructor identities are
checked after all operators compose. Finite rewrite and template spaces remain
visible in the report; new parameter values alone are ordinary model search.

## Evaluation and claims

Candidate selection minimizes 1 minus balanced accuracy for classification, or
MAE divided by training mean absolute deviation from its median for regression.
Exact ties retain the earlier candidate. Save native units, row IDs, truth,
predictions and checked metrics. Refits use the original training partition and
must reproduce the selection metric within 1e-12 before final scores are used.

Report all six reserved tasks and all five procedures. Prespecified primary
contrast is H2-I1 minus H2-I0 normalized final loss; secondary contrasts are
H2-I1 minus H0, fixed and random. Lower is better. Report mean paired difference,
wins/ties/losses, per-task native metrics, actual fits and process seconds.
Use a task bootstrap stratified by kind (three of each, with replacement),
10,000 replicates, seed 7342 and percentile 95% intervals. Six public tasks and
one model seed support only a small exploratory comparison; no multiple-testing
correction or general superiority claim. An interval containing zero remains
inconclusive. Do not convert saved search fits into net research savings when
outer work and coding-agent inference are excluded.

The same agent can access all files; directory boundaries are procedural.
Class support and grouping were checked before fitting. Gene/protein/spatial
independence is unverified, grid data are simulated, and Miami is retrospective.
No successful result is guaranteed. Diagnose concrete execution defects, but
preserve frozen failed experiments before starting any separately declared fix.
