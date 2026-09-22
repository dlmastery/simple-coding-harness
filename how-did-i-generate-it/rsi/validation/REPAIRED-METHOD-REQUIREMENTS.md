# What each repaired method must actually do

This is an implementation checklist, not a results claim. The user's original lesson numbers refer to the older course. The table maps those concerns to the maintained course.

| Original comparison | Current teaching location | Required execution evidence |
|---|---|---|
| 07 proof | 08 measurement; 09.05 matched improvers | Distinct predictive and resource outcomes, sound controls, separate task evaluation, uncertainty |
| 09 meta gate | 06 meta-harnesses; 09.03–09.05 | A generated or revised procedure, its gate decision and its later execution, with the external evaluation fixed |
| 10 Dream-RSI | 10.07–10.09 | Actual parent workspaces, recorded trees, executable policy revisions, multi-world replay, selected-policy deployment and a growing history pool |
| 13 Recuris | 10.06 and 10.10–10.12 | Current working state distinct from retained skills; evidence-linked local memory changes; validation and later skill use |
| 11 RSIAgent | 10.03–10.05 | Broad then focused practice; independently checked outcomes; actor-owned memory updates; frozen-memory evaluation |
| 15 AIDE2 | 10.13–10.15 | Inner researchers execute searches; an outer agent revises the inner harness; fair selection and task transfer; ignition assessed separately |
| 16 MetaSkill | 10.16–10.17 and 09.03–09.05 | Separate task-skill and updater changes; inherited updater actually governs later changes; compare the resulting improvement processes |
| Empirical culmination | 11.02 and 11.05 | A defensible retained lineage, matched comparisons, cost and uncertainty records, reproducible portfolio |

## Dream replay interface, rechecked 22 September

Read [Dream-RSI v1, section 3](https://arxiv.org/html/2609.14858v1). The policy can continue from the root or a currently observed leaf. Root requests reveal recorded independent starts in creation order; leaf requests reveal the recorded continuation. The policy cannot inspect an unrevealed score. Replay cannot create new outcomes. Policy development and deployment alternate, with recorded histories accumulating across cycles. Retaining the incumbent guarantees only its replay comparison, not fresh-task improvement.

The new `rsi/tools/discovery.py` supplies this observation and replay interface with one worker. Six constructed-fixture tests check information boundaries, ancestry, invalid actions, missing continuations, stopping and failed-attempt costs. These tests do not demonstrate online discovery or self-improvement. The pilot's flat candidate list will not be relabelled as a genuine discovery tree. Actual online runs must create their own ancestry and saved parent workspaces.

## Actor memory, rechecked 22 September

Read [RSIAgent v1, sections 3 and 8](https://arxiv.org/html/2609.15364v1). The actor writes memory after receiving an outcome grounded by a separate verifier. The curriculum selects practice and revisits gaps. Final evaluation disables learning. The paper includes target-conditioned practice; a course comparison on unseen tasks must distinguish its stricter transfer question from that setting. Role names inside one conversation do not provide independent contexts.

## Remaining method work

Recuris and MetaSkill already have source audits in the research folder; reconcile those audits with the expanded experiments before claiming implementation. AIDE2 requires code-level harness revision and later execution. A rearranged fixed list is not enough if every candidate still runs. Keep predictive selection, procedure promotion and evaluation of the improver as distinct decisions.

The development-only headroom pilot is running under its predeclared 288-fit allocation. It measures whether the task/search pairing is suitable. All seven effectiveness comparisons above remain unexecuted in the repaired benchmark at this checkpoint.
