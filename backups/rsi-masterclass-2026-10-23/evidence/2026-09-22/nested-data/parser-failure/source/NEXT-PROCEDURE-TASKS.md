# Candidate tasks for the next procedure comparison

Selected from the saved 107-task metadata inventory before new data acquisition
or model fitting. This is a data-preparation decision, not yet an executable
search protocol. The prior 96-fit development, 324-attempt comparison and
four-fit repair remain closed. No further fit is allocated by this document.

The next comparison needs to challenge the revised allocation policy against
the strong conventional portfolio. The six earlier evaluation tasks have
already informed the diagnosis; they are no longer untouched evaluation for
that new proposal. This panel uses different datasets and avoids the shared
multiple-feature digit views, earlier optical digits, wine and adult tasks.

| OpenML task / dataset | Subject | Target | Why include it |
|---|---|---|---|
| 43 / 44 | Email features | Spam class | Sparse frequency features and corpus-specific shortcuts |
| 45 / 46 | DNA sequence windows | Splice class | Many categorical positions; an excluded instance identifier |
| 2074 / 182 | Satellite neighborhoods | Central-pixel class | Multiclass numeric features and spatial dependence limits |
| 361241 / 44963 | Protein decoys | RMSD | A larger nonlinear regression table with grouping limitations |
| 361251 / 44973 | Simulated grid behavior | Stability value | Structured physical inputs; derived class labels must be excluded |
| 361260 / 44983 | Miami property sales | Sale price | Skewed regression, property identifiers and repeated sales |

These six IDs were enumerated from the local metadata before the source pages
below were read. Domain variety, manageable feature counts and previously
unused dataset identities determine the panel. No procedure score was
requested for task selection. Public descriptions include historical method
results, which were encountered during source review; the tasks are new to
these local executions, not unknown public problems or private benchmarks.

## Source review and preparation requirements

- [Spambase, UCI](https://archive.ics.uci.edu/dataset/94/spambase): 57 numeric
  email descriptors. The contributor-specific word and area-code features
  limit general-purpose filtering claims. Keep that scope visible. The page
  states CC BY 4.0 and credits Hopkins, Reeber, Forman and Suermondt.
- [Splice junctions, UCI](https://archive.ics.uci.edu/dataset/69/molecular+biology+splice+junction+gene+sequences):
  60 categorical positions and an instance ID. Exclude `Instance_name` as the
  OpenML descriptor instructs. Inspect whether gene identity can be recovered
  for grouping; otherwise state that gene-level independence is unverified.
  UCI states CC BY 4.0; the saved descriptor attributes GenBank and the donors.
- [Landsat Satellite, UCI](https://archive.ics.uci.edu/dataset/146/statlog+landsat+satellite):
  36 values represent overlapping pixel neighborhoods. OpenML's version has
  6,430 rows, while the UCI page lists 6,435. Verify the pinned OpenML checksum
  and describe the version difference rather than silently accepting a new
  file. The descriptor says the original image cannot be reconstructed.
  Random grouped rows cannot establish new-scene transfer. UCI states CC BY 4.0.
- [Protein properties, UCI](https://archive.ics.uci.edu/dataset/265/physicochemical+properties+of+protein+tertiary+structure):
  CASP decoy descriptors predict RMSD. Inspect for parent-protein identities;
  do not claim unseen-protein performance without them. UCI states CC BY 4.0
  and credits Prashant Rana.
- [Grid stability, UCI](https://archive.ics.uci.edu/dataset/471/electrical+grid+stability+simulated+data):
  simulated four-node system, not field observations. Check that the derived
  stability class is absent from regression inputs. UCI states CC BY 4.0 and
  credits Vadim Arzamasov.
- [Miami housing, OpenML descriptor](https://www.openml.org/api/v1/json/data/44983):
  the already archived descriptor states CC0 and identifies `PARCELNO` as an
  excluded identifier, with some repeated properties. Use it for grouping
  before dropping it from predictors. Check that special-feature value is
  described as an input appraisal, not silently treated as independent of
  sale price. State a retrospective property-price task; no future-market
  forecast or causal interpretation follows. The linked Kaggle source has
  not been independently audited in this preparation decision.

Read-only UCI pages were opened directly on 22 September. This is source and
data-license verification, not a new RSI literature sweep. Saved OpenML
descriptors and their hashes remain in the existing inventory archive.

## Before any new model fits

Acquire the pinned raw files and record hashes, exclusions and source notes.
Use training/selection/final roles with duplicate-feature groups; additionally
group recoverable repeated entity IDs. Preserve group conflicts. Cap rows
for laptop execution using a deterministic feature/group rule, not model
performance. Check every target, group and class boundary independently.
If data cannot satisfy the declared question, stop preparation and record the
problem; do not quietly substitute a favorable task.

Then finish and freeze the revised updater, strong controls, proposal guard,
fit/proposal budgets, evaluator, analysis and promotion rule. A revised policy
should preserve broad portfolio coverage before allocating local refinements,
and should justify using current-task feedback rather than an overconfident
global model ranking from three development tasks. These are design directions,
not proof that the next policy works. The next execution protocol must settle
the details before fitting; this page supplies no hidden additional trials.

## Keep the next experiment's levels explicit

Do not turn this follow-up into only a larger hyperparameter search and call
it RSI. Preserve three separately executable objects: a model candidate, an
inner researcher that runs a bounded sequence of model experiments, and an
improver that proposes and evaluates changes to that researcher. A revision
to the improver must govern a later researcher revision, whose complete inner
search is then evaluated under the same external contract as its counterpart.

The completed six-procedure study establishes changes to an allocation policy
and its later two-proposal research-skill artifacts. Those finite proposal
lists are narrower than newly generated general research procedures. The next
implementation must expose the whole revised researcher as executable source,
its proposed change, its parent, the improver rule that produced it and its
later execution. Count every losing inner search in the outer cost. Keep
ordinary fixed/random model search as controls, and do not relabel the best
conventional control as a self-improved system.
