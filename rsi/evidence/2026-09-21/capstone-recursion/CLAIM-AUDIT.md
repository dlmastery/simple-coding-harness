# What this capstone establishes

## The concrete chain

I0 is a saved instruction for selecting changes to a prediction recipe. Generation one fits ridge and tree. I0 chooses tree because it has zero training error, despite worse selection error. The author inspects that failure and saves a single proposed instruction change as I1: rank by selection error.

Generation two reads that exact I1 file in one arm and the unchanged I0 file in the other. Both start from identical saved tree task-skill bytes. Both fit the same tree, ridge and forest recipes in the same order. Each corresponding recipe produces byte-identical selection predictions. The selectors retain different recipes: I0 keeps tree; I1 moves from tree to ridge to forest. The traces record the instruction, file identity, comparison and retained state at every decision.

The unchanged external rule accepts I1 from selection results: 0.553065850321 versus I0's 0.693386773547 MAE. This acceptance is frozen before terminal evaluation. Final scores are 0.546309052870 for the revised arm and 0.675403225806 for the original arm, on 992 evaluation rows. The final scores do not trigger any new choice or fit.

## Supported claims and limits

| Claim | Evidence and boundary |
|---|---|
| A model-research procedure was revised | The ranking instruction changes between I0.md and I1.md; it is not a model hyperparameter edit. |
| The revision governed later improvement work | Generation-two candidate trial loads I1's recorded identity and uses selection_MAE in each retention decision. |
| The revised procedure retained a better result in this comparison | Matched menu, seeds, inputs and fit counts; better selection and terminal MAE in this one task. |
| I1 was accepted | PROMOTION.csv applies the predeclared external rule before final scores; PRE-FINAL.csv preserves its identity. |
| Accepted I1 governed a post-acceptance generation | **Not tested.** Its observed later use was the candidate trial; no third generation is allocated. |
| Autonomous recursive self-improvement | **Not established.** The author diagnoses and edits the improver; the fixed controller does not generate or revise itself. This is a bounded, author-guided example of improver revision and inherited candidate use. |
| General improver effectiveness | **Not established.** One familiar development task, one deterministic seed, a small fixed menu and a deliberately weak parent. No fresh-task comparison. |
| Efficient or accelerating improvement | **Not established.** The proposed rule compares already fitted candidates; both arms spend three fits. Total design and inference costs are unknown. |

All model recipes, rejected alternatives and the weak initial outcome remain in the record. No model weights were updated through language-model training. The tree and forest are ordinary supervised estimators. Reading public local files is controlled by procedure and checks, not an isolated private evaluation service. The author knew the task family and overfitting risk; the experiment does not measure discovery.

## A counterexample and a useful follow-up

A noisy, repeatedly consulted selection set can favor a recipe that is worse on new cases. Replacing training error with selection error does not remove that possibility. A smallest useful **new** experiment would freeze these two procedures and their menus, then compare them on several previously unused prediction tasks under a separately approved budget. Prespecify task-level outcomes and uncertainty. Do not recycle this terminal partition as fresh development evidence.

No such follow-up ran here. No student, independent reviewer, fresh coding-agent context, or cluster was tested.
