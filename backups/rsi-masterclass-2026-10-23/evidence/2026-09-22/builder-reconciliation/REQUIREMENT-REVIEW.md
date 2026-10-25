# Requested, implemented and observed

| Requirement in the brief | Implementation inspected | Evidence or remaining limit |
|---|---|---|
| Bike target and MAE | Generated task choice is fixed to bike; shared target and scorer implement cnt/MAE | Original baseline and new checked baseline both have MAE 159.947912 |
| Permitted calendar inputs, no target components | Shared feature_names accepts calendar/weather/all, rejects casual as a feature-group request | Fresh leaked-feature request fails before training and leaves no predictions |
| Train-only preprocessing | Pipeline fits on the train mask; prediction uses the named evaluation mask | Exact historical tool recovered; this is source inspection, not a new dynamic contamination-injection test |
| Selection drives comparisons | compare ranks recorded selection scores under the contract | Historical wine comparison and checked predictions; no final evaluation in this pass |
| Two admitted attempts, including failures | Generated --limit choices and default are both 2; ledger reserves an attempt before feature validation | New ledger: one successful fit, one charged failure; third request refused with two slots still spent |
| Required candidate identity | Prediction checker binds a successful candidate in its ledger; new acceptance tools bind workspace/contract/prediction identities and current admission | Matching claim passes, unrelated and missing-ID claims fail; failed/unadmitted request states reject the old success |
| Recorded resources and stop behavior | Author driver supplies a 60-second timeout to each child; shared tool tracks attempt and aggregate recorded-time limits | Successful bounded commands and costs are saved. The copied entry does not itself provide an OS hard-timeout wrapper; its caller must enforce the stated command limit |
| Retain failures and costs | Candidate failure file, request ledger and command logs | Failed admitted request remains trial-002; its cost is not refunded |
| Generated instructions and dependencies | README, TASK, WORKFLOW, RECOVERY, requirements and shared-tool imports | Existing environment executes the copied package. This pass does not install a fresh environment or test another coding agent |

The diagnostic README claims ten attempts while its copied code still fixes two. AST inspection exposes the mismatch without running the diagnostic. A documentation-only review would see the new claim and miss the actual boundary. The existing infographic depicts the reverse mismatch—brief two, code ten—as another example; neither should be confused with the accepted package's two-attempt behavior.

A hidden assumption is the prediction setting. Calendar and observed weather are permitted for the retrospective bike exercise; the same observed weather would not automatically be available for a future forecast. The source brief makes this explicit. Another is environmental coupling: the generated wrapper imports the named repository instead of bundling its own independent tool implementation.

The recovered historical builder and tool files are evidence snapshots, not recommended execution entry points. Their versions differ from today's maintained skill/tool. The new baseline's contract records the current tool, so matching predictions are repeatability evidence, not identical software history.
