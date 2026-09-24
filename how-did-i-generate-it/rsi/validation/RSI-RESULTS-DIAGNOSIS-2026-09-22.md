# Why the reported gains are mostly zero

This is the original diagnosis, preserved as the starting point of the repair.
For completed experiments and the current boundary of the claims, read
[what changed after the zero-gain results](../../../rsi/RESULTS-GUIDE.md).
The proposed next steps below are historical; the implementation record tracks
which have since run.

The user supplied a seven-row comparison from the original course and asked where self-improvement was demonstrated. The concern is valid. The table does not establish a reliable predictive gain or a general recursive improvement result. Course authoring and illustration completion must not be confused with that scientific outcome.

## Evidence inspected

Read the original contracts at Git commit `eed9cbb`: the exam intent, actor evaluation and tool contracts, recipe schema, Dream policy library, and lesson-17 map. Also inspected the preserved [original README](../backups/before-rebuild-eed9cbb/README.original.txt), the rebuilt [Dream exercise](../../../rsi/evidence/2026-09-21/dream-labs/README.md), [AIDE exercise](../../../rsi/evidence/2026-09-21/aide-labs/README.md), [meta-skill exercise](../../../rsi/evidence/2026-09-21/meta-skills/README.md) and [recursive capstone](../../../rsi/evidence/2026-09-21/capstone-recursion/README.md).

Checked the primary [Dream-RSI paper](https://arxiv.org/html/2609.14858v1), especially its method, and opened the [AIDE² author report](https://www.weco.ai/blog/first-evidence-of-recursive-self-improvement). The dated discovery query targeted the last 30 days: `Dream-RSI September 2026 discovery tree replay self improvement arxiv`. This was a targeted diagnosis, not another complete literature sweep.

The user's rounded numbers have not been independently recomputed from every historical run artifact. The diagnosis below distinguishes contract evidence from interpretations of that supplied table. A displayed zero may hide a smaller difference at greater precision.

## What is wrong with the experiment

**The search is too constrained for the claim.** The original control enumerates a fixed list of 24 recipes. Other policies can select from a small grid, with 24 fits per arm and three model families. If two procedures evaluate the same deterministic candidates under the same selection rule, reordering them cannot improve the best final score. The original README explicitly records memory moving the best Adult recipe from attempt 17 to attempt 1 without changing validation or test performance, and warns that wine and digits saturate quickly in this space. This does not prove those datasets have no room for improvement; it shows the chosen search interface can remove the opportunity to demonstrate it.

**The win counter mixes outcomes.** The original exam defines a win as better ROC-AUC OR the same score with fewer `wasted_fits`. Both arms can still execute all 24 fits. Earlier arrival at a score is a search-order improvement, but not automatically a reduction in actual total compute. The contracts also describe the wasted-fit threshold differently: the evaluation prose refers to the control's best, while the scorecard tool contract refers to the arm's own best. That definition needs reconciliation before comparing the metric. Do not label 5/5 such wins as five accuracy gains.

**The transfer evidence is weak.** The exam has 600 rows; its fixed 55/15/10/20 split gives 330 training, 90 selection, 60 private-gate and 120 test rows. With the declared imbalance, the small selection partition can yield noisy rankings. Five seeds of the split reuse one generated task; they are not five independent task families. The supplied negative exam gaps are failures of that comparison, not successful transfer. Their exact cause requires the actual traces; overfitting, policy instability and unsuitable memory are plausible explanations, not proven diagnoses from the table alone.

**The method adaptations omit decisive mechanisms.** The original Dream example ranks five hand-written policy names using a recipe log and changes one policy line. This differs materially from the paper's programmable exploration-policy revision, tree/workspace dynamics, simulator pool and renewed online discovery. The rebuilt three-node replay exercise is clearer about its limits but remains a mechanism lesson. A role-file edit or a successful gate is not evidence that a better improver emerged.

## What the current course actually establishes

| Evidence | Supported claim | Missing claim |
|---|---|---|
| Original efficiency-only wins | Earlier arrival at a comparable score under the recorded metric, if traces confirm it | Higher model quality or lower total compute |
| Rebuilt Dream exercise | Tree recording, replay coverage and a fresh comparison ran; the baseline won | Successful recursive policy improvement |
| Rebuilt AIDE exercise | Reordering operators improved selection MAE on an exposed task at three fits | Better generation of researchers or ignition |
| Rebuilt meta-skill fixtures | A revised checking rule affected later decisions on constructed cases | Measured ML generalization improvement |
| Rebuilt recursive capstone | An author-written change from training-error to selection-error ranking retained a better model in one comparison | Autonomous discovery of the change, superiority over a sound baseline, cross-task improvement or acceleration |

These are useful teaching demonstrations and honest negative results. They are insufficient as the empirical culmination of the requested RSI masterclass. The earlier completion statements cover authored content and maintainer checks; they must not be read as completion of a convincing RSI experiment.

## Repair the benchmark before adding more results

Keep regression and classification. Change the task distribution, search opportunities, method implementation and evaluation protocol together.

1. **Establish headroom on development tasks.** Use several task families with differing feature structure, categorical handling, missingness, imbalance and interactions. Compare sensible fixed and random-search baselines. A larger-budget development-only reference can test whether useful solutions exist beyond the small budget. Do not tune task selection on the final benchmark or deliberately cripple the baseline.
2. **Make the search budget smaller than the useful candidate space.** Permit bounded pipeline changes, diagnostics and branching from actual retained parents. Test several declared budgets. Equal eventual maxima can still be compatible with different quality-versus-cost curves.
3. **Implement a complete Dream-style cycle.** Record real discovery trees; evaluate candidate policy revisions on a pool of earlier trees; keep unsupported branches unknown; deploy the selected policy on new development tasks; collect the next trees. Repeat several recorded cycles. Label remaining departures from the primary algorithm.
4. **Test learning the improver separately.** Freeze the underlying task solver when testing an exploration controller. For a claim about improving the updater itself, demonstrate its inherited revision changing later proposal/evaluation behavior and test the resulting procedures independently. Do not demand that every paper use the same definition of recursion.
5. **Separate task-level and row-level holdouts.** Train task models on training rows; select candidates without final rows. Develop the research procedure on one task pool, select it on a separate task pool, then freeze it for untouched final tasks. Keep previously exposed public tasks labelled development material. Treat repeated seeds as repeated measurements within tasks.
6. **Report separate outcomes.** Final predictive quality at a fixed total budget; time or cost to a predeclared target; success/failure rate; and the cost of meta-optimization. Count data inspection, LLM inference, replay and failed trials. Zero new fits is not zero total cost. Report per-task variation and negative transfer, not a blended win count.
7. **Require a behavior trace, then an effectiveness comparison.** Show the parent policy, proposed child, selection decision, later use and actual difference in action. Compare against frozen baseline policies under matched resources. Multiple generations are needed to study trends; they do not by themselves establish acceleration.

No new fit, revised positive outcome or successful reproduction is claimed here. The next substantive work is a preregistered pilot benchmark and a faithful method implementation, not additional illustrations. The laptop path should use bounded CPU experiments; larger compute may expand the workload without changing the declared comparison silently.
