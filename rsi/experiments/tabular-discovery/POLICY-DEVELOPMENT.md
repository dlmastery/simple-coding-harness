# Policy development record

## Revision 1: probe a lineage before broadening

Written after both generation-0 trees completed, before evaluating this revision. The policy-development agent is the current coding-agent session. Its context includes development data and source research; this is not a fresh independent-agent comparison. The inner proposer remains the frozen deterministic pipeline engine.

Observed failure: the broad control spends three calls on independent drafts before testing the first draft's interaction operator. In classification, that first refinement improves balanced accuracy from 0.787092 to 0.911774; later changes do not beat it. In regression, the first candidate is best, with MAE 0.232303. Broad exploration still has value on other tasks, so neither observation justifies deleting it globally.

Proposed change: test up to four successive candidates in the first lineage, then open the remaining two starts and refine available leaves. This changes the order of real parent-workspace continuations; it does not select an outcome before it is observed.

Expected effect: expose a useful feature change earlier. Risk: spend too much on a weak first family and miss a better alternative. Falsifier: worse mean replay utility, missing continuation coverage, or later online regression against the fixed controls. Evaluation: the declared eight-decision replay over both generation-0 worlds, with no new fits.

## Revision 2: stop when measured quality justifies it

Revision 1's mean replay utility was 0.171237 versus 0.171589 for the incumbent.
Both made eight represented attempts per world and retained the same quality.
The small cost difference does not establish a robust effect.

Revision 2 adds a stopping rule when best observed normalized loss is at most
0.20. This threshold is a development-derived proposal, not a newly changed
external evaluation rule. It will stop actual future workers rather than merely
mark later fits as wasted. It leaves the branch-probing fallback intact.
Risk: a quality target can stop before a substantially better model is found,
or transfer poorly across task families. The existing replay utility and
later independent quality/cost comparisons remain the judges. No final task
has been generated or scored.

## Revision 3: require a second candidate before stopping

Revision 2 keeps the incumbent's best selection quality in both recorded worlds
while representing two classification fits and one regression fit. Its mean
utility is 0.159308. Revision 3 requires at least two observed candidates before
using the same quality stop. The extra candidate is a pipeline comparison,
not an independent statistical confirmation; it may expose a missed feature
benefit but costs another attempt. Test it under the unchanged replay objective
before selecting any revision for online deployment.

## Deployment of revision 2

The declared selector chose and froze revision 2 before either new task was
generated. Its exact source was then copied into both generation-1 rollouts
before fitting.
It actually stopped after four classification fits (0.908784 balanced accuracy)
and two regression fits (MAE 0.242510). These are new development instances,
not final transfer results. The new trees are added to the replay pool.

## Revisions 4–6 after generation 1

Revision 4 tightens the stop threshold to 0.15, testing whether the earlier rule
stops too soon. Revision 5 broadens after two candidates in the first lineage,
testing whether continuing a weak initial branch wastes resources. Revision 6
uses an intermediate threshold of 0.18. All use the same external replay rule
and four frozen worlds. Unknown continuations cannot count as negative or
positive discoveries; lack of coverage makes a revision ineligible here.
The incumbent participates and wins exact ties. None of these revisions has
seen procedure-selection or final task data.

## Retention and generation 2

Revision 4 was worse under the declared replay objective. Revision 5 requested
unrecorded continuations and was ineligible; this says nothing about the value
of those unexplored branches. Revision 6 tied the incumbent exactly. The
selector therefore retained revision 2, with the same source hash, before
generating tasks 1105 and 1106.

On classification 1105 it stopped after one actual fit with balanced accuracy
0.937299. On regression 1106 it used all twelve attempts and retained node 4,
with MAE 0.336272. The threshold did not fire on that task. The complete three
generations executed 43 fits, all successful, within the 72-attempt allocation.
One policy revision was promoted; the later round retained it. This is neither
repeated acceleration nor a final effectiveness result.
