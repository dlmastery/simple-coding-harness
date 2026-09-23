# What each repaired method must actually do

This is an implementation checklist. The user's original lesson numbers refer to the older course. The table maps those concerns to the maintained course. The progress record below separates completed measurements from remaining work.

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

## Evidence needed for the method names

Recuris and MetaSkill have source audits in the research folder. The expanded experiments below are classroom adaptations; their complete execution does not establish reproduction of those systems. AIDE2 requires code-level harness revision and later execution. A rearranged fixed list is not enough if every candidate still runs. Keep predictive selection, procedure promotion and evaluation of the improver as distinct decisions.

## Measured progress, 22 September

The development-only headroom pilot completed 288 fits. Its sound eight-attempt fixed control already matches the 48-fit reference on three tasks. See [the full evidence](../../../rsi/evidence/2026-09-22/headroom-pilot/README.md). The subsequent operator pilot added 72 attempts, including one timeout. These are headroom studies, not RSI claims.

The repaired discovery cycle executed 43 online development fits. Six agent-written policy revisions were assessed against recorded trees; one was promoted, then retained in a later cycle. Actual later workers used its frozen source. The completed sixteen-task comparison then executed 715 search fits and 80 scoring refits, plus two admitted attempts in a disclosed host-interrupted task. All 1,628 independent final checks pass. Evolved search used 55 fits against broad search's 192. Final quality improved on three tasks, tied on twelve and worsened on one; the paired loss interval includes zero. This supports lower measured search cost in this setting, not an established predictive benefit or net total research-cost saving.

| Required repair | Current evidence and remaining work |
|---|---|
| Proof and meta gate | Separate final rows, five matched arms, checked predictions, costs, uncertainty, recorded promotion and actual later use now exist. This is one shared comparison, not two independent studies. |
| Dream-inspired mechanism | Real parent workspaces, growing history pool, replay revisions and prospective online comparison completed. Fixed inner proposer and same-context coding agent remain explicit simplifications. |
| AIDE-inspired harness revision | The initial 144-fit revision failed promotion; its conditional final study stays closed. The later 624-attempt study executes complete generated researchers and their inherited second generation, with fixed/random controls. Final quality is inconclusive; no ignition or full AIDE2 reproduction. |
| Recuris and RSIAgent | The expanded public-task study now compares frozen experience with fixed and random controls. Memory improves three tasks and ties three against random, but loses to fixed overall. Checked experience and current state stay separate. The source-specific earlier curriculum exercises remain distinct; this is not a full reproduction. |
| MetaSkill and recursive capstone | The earlier role-file comparison verifies candidate-trial inheritance. The later complete-researcher study also verifies gate-conditioned parent retention, actual second-generation source creation and its reserved-task execution. I1 improves two tasks, ties three and worsens one against I0/parent. Overall benefit, autonomous meta-generations and post-study deployment remain unestablished. |

The [public-tabular comparison](../../../rsi/evidence/2026-09-22/tabular-comparison/README.md)
adds 288 search fits and 36 final refits, with 10,353 final checks. Its revised
harness also faces the original harness under the same updater: one gain,
four ties and one regression. Two different candidate sources construct the
same estimator after composed assignments; no frozen outcome was replaced.
Eleven lesson examples and the improvement skill now link this evidence or
the completed discovery-policy study. The PPTX remains required and pending
the requested successful repair. Fixing observable implementation weaknesses
and testing future revisions requires a new declared study, not retuning on
these final scores. Do not turn checked execution into established efficacy.

The [separately versioned operator repair](../../../rsi/evidence/2026-09-22/composition-repair/README.md)
now corrects overwritten template settings, constructor duplicate detection
and the unlimited-depth capacity error. Four successful integration fits
produce a tie and a small regression; 420 final construction checks and ten
additional capacity checks pass. Six [next-task candidates](NEXT-PROCEDURE-TASKS.md)
were then selected from metadata with source limitations recorded. Their
preparation and completed allocation comparison are reported below; the
earlier four-fit repair budget remains closed.

The [six-task data preparation](../../../rsi/evidence/2026-09-22/nested-data/README.md)
is now complete with zero fits. An independent parser and graph reconstruction
verify source rows, target exclusions, whole-group allocation and recorded-ID
isolation. The first parser failure is preserved. These data checks do not
establish any RSI benefit.

The [complete-researcher development phase](../../../rsi/evidence/2026-09-22/nested-research-development/README.md)
now executes 216 searches and 18 scoring refits. I1's generated researcher
improves two exposed-task evaluation results and ties four, narrowly passing
the predefined gate; I0 ties all six and is rejected. The 6,555 final checks
include the 6,245 search checks. Both inherited improvers actually generate a
second complete researcher; 22 independent lineage/gate checks pass.

The [reserved evaluation](../../../rsi/evidence/2026-09-22/nested-research-evaluation/README.md)
has also completed. Its 360 searches and 30 scoring refits bring the whole
study to the declared 624 attempts. All 10,813 final checks pass, including
10,299 search checks performed before final scoring. The inherited researchers
actually execute on the six reserved tasks. I1 improves two tasks, ties three
and worsens one against I0 and the parent. The primary mean loss change is
+0.000120, with an exploratory interval of [-0.001826, +0.002390]. All four
reported comparison intervals include zero. Later source use is established;
an overall quality benefit, acceleration and post-study deployment are not.
The full study is closed. No new fits or retuning on these final outcomes
are authorized by this record. The presentation decision remains pending:
the user was asked whether to present verified mixed results now or retain
the original condition of stronger results. Silence is not approval.
