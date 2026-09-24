# Loop and system execution review

Date: 20 September 2026. This review covers labs 02.06, 05.02–05.05, and 08.01. It separates observed actions from untested learner and agent claims.

## Original declared run

The [protocol](LOOPS-AND-SYSTEMS-PROTOCOL.md) and [driver](../scripts/run-loops-and-systems.py) were pushed at `c9f9cd9a6dd49b1187b8010dc71fd331a46fa7e9` before execution. The driver completed thirteen CPU fits and 26 child commands with exit 0. Every candidate passed the row-identity, target, ledger, and reported-score check. There was no final evaluation. All 146 original files were copied and verified. See the [archived run](../../../rsi/evidence/2026-09-20/loops-and-systems/README.md).

| Requirement | Actual input and action | Result and limit |
|---|---|---|
| Compare two search procedures | Two fresh two-attempt bike workspaces. A repeats constant/calendar; B chooses linear/calendar from its saved hourly error evidence. | Retained MAE 159.947912 versus 109.807668. Starting prediction bytes match. The choice is saved and hashed before the second fit. Known public task and unknown reasoning cost limit the comparison. |
| Route by task meaning | Bike and wine task briefs, separate contracts, one baseline each, two valid and two rejected route inputs. | Wine has 278 negative and 41 positive selection cases; majority accuracy 0.871473, positive recall 0, balanced accuracy 0.5. All 1,599 rows checked for duplicate-group partition separation. |
| Resolve stale context | Current bike contract allows two attempts and has one charged attempt. Current/stale notes claim one/three left. | One current note accepted; stale claim rejected. Derived packet omits irrelevant wine metrics. Missing-availability copy and recovery explanation retained. No extra fit. |
| Check component contribution | Two systems × valid/leaked fixtures, then a separately declared removal of both protections. | Removing domain check alone has no observed effect because allowlist remains. Removing both reaches the fit stub for the leaked input. Four main and two additional fixtures; no leaked training. |
| Repeat a model comparison | Tree/forest on calendar fields, seeds 17, 29, 43, six fits on the same partition. | Differences −16.919881, −16.402636, −16.592637; mean −16.638385. All pairs, measured costs, actual-data plot, and best-seed-only reporting contrast are preserved. One split leaves data uncertainty unmeasured. |

The main loop/system run records 4.611563 fit seconds, 77.637044 child wall seconds, and 83.428121 parent seconds through reporting. These are nested timings. Agent inference and full authoring costs remain unmetered. The optional ten-fit unequal-budget extension is analysis only, not execution.

## Review finding and corrective experiment

The original coordinator produced a successful baseline and executable handoff verdicts, but built the transition table afterward. That retrospective trace was too weak to show that state governed execution. The [separate correction protocol](LIVE-COORDINATOR-PROTOCOL.md) and [driver](../scripts/run-live-coordinator.py) were pushed at `7850ec92378f6d1a52c105782dd9b5c770118a8f` before a fresh one-fit experiment. No original budget or outcome was changed.

The [corrected evidence](../../../rsi/evidence/2026-09-20/live-coordinator/README.md) has 15 ordered events and four state snapshots. `running` is saved before fitting. The fit process exits at `awaiting-check`; another process reads that state before checking. Three handoff fixtures reject missing evidence, ambiguous meaning, and the wrong candidate. The wrong candidate has genuinely checked, byte-identical predictions. A matching real check permits `complete`. A subsequent fit action returns the expected exit 1 and leaves the ledger hash unchanged.

The correction adds one fit, with 0.103099 fit seconds. Fit/check child wall times are 2.048124 and 2.177792 seconds. Twenty-seven original files were copied and hash-verified. Combined new work is fourteen fits; failed validation reasoning and the initial run's costs are not erased.

## Lesson changes and open boundaries

Replaced six illustrative examples with links to these measured cases. Lab 05.04 now explicitly requires saved state before action, a process exit at awaiting-check, and recovery from disk. The reusable authoring skill preserves the same distinction. Lab 08.01 shows the actual paired-seed plot; its labels, signs, and text were visually inspected at full size. A narrow-page rendering check remains separate.

All predictions, quizzes, and teach-back are unattempted by a real learner. The fixed router, coordinator, and dry-run guards are agent-written implementations, not independent LLM policy tests. Forced interruption during a fit, other native coding agents, GPU jobs, and cluster jobs were not tested. The inventory maps 54 labs to related execution evidence and leaves 47 unmapped; neither count is a completed-lab count.

Publication checking initially found two broken source-description links in the archived data-card copies. Added their unchanged source-description files as labelled post-run supplements, with a separate manifest; the 146 original files remain byte-identical. The corrected publisher checks 101 lessons and 2,121 local links with no problems. Runtime code was unchanged, so this pass used the actual fourteen fits and their checks rather than repeating the entire shared runtime suite.
