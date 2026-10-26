# A valid route needs complete dependencies

These author walkthroughs supplement graph labs 03.01, 03.02, 03.04 and 03.05. They execute ordering, routing, bounded repair and report-recovery checks with **zero new model fits**. Fifteen child commands have their expected exits; nine artifact invariants pass. The original parent script failed after its thirteenth child command. A retained continuation completed only the remaining two guards.

| Lesson activity | Inspect the evidence |
|---|---|
| 03.01: name the dependencies | [Artifact table](03-01/WORKFLOW.md), [editable diagram](03-01/workflow.mmd) and [rendered diagram](03-01/workflow.png) |
| 03.01: check normal and invalid order | [Normal verdict](03-01/normal.md), [check-before-fit refusal](03-01/check-first.md), commands [normal](order-normal-command.txt) and [invalid](order-check-first-command.txt) |
| 03.01: remove an edge | Split-before-inspection [fails under the original graph](03-01/split-first.md), but [passes the weakened copy](03-01/edge-removed.md) |
| 03.02: run all three routes | [Conditions, actions and exits](03-02/WORKFLOW.md); actual verdicts for [valid](03-02/valid-verdict.md), [invalid](03-02/missing-target-verdict.md) and [unknown](03-02/unknown-verdict.md) |
| 03.02: change unknown to pass | [Unsafe-policy verdict](03-02/unsafe-unknown-verdict.md) accepts absent evidence as modeling-ready; no fit runs |
| 03.04: test success and exhaustion | [Fixed rule](03-04/WORKFLOW.md), [effective trace](03-04/effective/TRACE.csv), [ineffective trace](03-04/ineffective/TRACE.csv), terminal states [success](03-04/effective/STOP.md) and [failure](03-04/ineffective/STOP.md) |
| 03.04: remove feedback | [Unexecuted prediction](03-04/NO-FEEDBACK.md), with no extra repair allocation |
| 03.05: fail and recover a report | [Injected exception](report-failure-command.txt), [actual recheck](recovery-check-command.txt), [recovered report](03-05/RECOVERED-REPORT.md), [ordered events](EVENTS.csv) |
| 03.05: invalidate affected descendants | [Changed-split plan](03-05/INVALIDATION.md), [one-cell substitution](03-05/SUBSTITUTION.md), guards for [original](03-05/original-dependency.md) and [changed](03-05/altered-dependency.md) predictions |

Removing inspect → split allows splitting before reading the data report. The ordering checker accepts that sequence because its graph is incomplete. It cannot supply the missing scientific reason. Likewise, changing unknown to pass supplies permission without supplying evidence.

The repair fixtures both start without a candidate ID. One edit adds it and passes. Two title edits leave it absent and exhaust the other fixture's allowance. All report versions and slot reservations remain available. The rule stays fixed; three repair slots are used across two fixtures.

Report recovery recomputes the copied baseline's MAE, **159.947912**, and leaves prediction and ledger bytes unchanged. A separate copy changes one prediction from 109 to 110. Its dependency guard refuses the old report. Changing the split produces an invalidation plan, not new training or mixed scores.

[The protocol](PROTOCOL.md), [source identities](INPUT-IDENTITIES.csv), [nine checks](CHECKS.csv), [83-file manifest](MANIFEST.csv) and [review](REVIEW.md) preserve the scope. Sequential child-command wall time totals about 3.261 seconds; inference and author costs are unknown. The copied ledger records an earlier fit, not one performed here.

The [unexpected parent error](EXECUTION-FAILURE.txt) came from using `prediction` instead of the actual `predicted` CSV field. The [original driver](run-graph-reconciliation.py) is preserved as failed provenance. The [continuation](continue-graph-reconciliation.py) verifies the completed state before its two remaining commands. These are one-time author records, not student entry commands. Students use the lab's tutor prompt.

The fixtures test fixed rules in one author context. They do not establish learner understanding, autonomous planning, real scheduling or adversarial isolation. Existing conceptual illustrations were inspected and preserved. This navigation page was added after sealing the original files.
