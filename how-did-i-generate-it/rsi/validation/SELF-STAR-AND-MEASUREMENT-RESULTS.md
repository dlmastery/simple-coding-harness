# Self-* and measurement execution review

Date: 20 September 2026. The [protocol](SELF-STAR-AND-MEASUREMENT-PROTOCOL.md) covers nine labs: 07.01–07.04, 07.08, and 08.03–08.06. The [run index](../../../rsi/evidence/2026-09-20/self-star-and-measurement/README.md) links every main activity, additional check, output, and limitation.

## Failure, correction, and preservation

The first run at `06a7d22` completed a report correction and stopped before new fitting. Its exact-equality regression target check failed. An eight-table audit found identical row identities and classification labels; some regression targets differed by at most 5.684341886080802e-14 after earlier decimal CSV round trips. The [precision audit](SELF-STAR-PRECISION-AUDIT.md) records the full table.

Preserved and hash-verified all 20 failed-attempt files. Changed only regression target verification to absolute tolerance 1e-12 with zero relative tolerance, retaining exact row/class checks. Added failure recording for unexpected exceptions. The corrected driver and linked audit were pushed at `d2d3488a156b917b68b0e8688f8641c1e4351bf7` before a new workspace ran. No old workspace was reopened, score criterion changed, candidate retuned, or charged fit refunded.

## New fits

Eight new CPU fits ran: four bike fits and four wine fits, each with a successful prediction, source-row, target, ledger, and result check. The parent task skill starts with constant and chooses tree next. The child replaces only that second-choice instruction with a predeclared residual-slice diagnostic. Every decision precedes its second fit. The task-skill hashes remain fixed across both tasks, as does the canonical improver hash.

| Task | Parent retained result | Child retained result | Resource equality actually established |
|---|---:|---:|---|
| Bike, selection MAE ↓ | 125.049488 | 109.807668 | Two fits and two checks per arm |
| Wine, selection balanced accuracy ↑ | 0.632611 | 0.744955 | Two fits and two checks per arm |

Wine parent recalls are 0.679856 and 0.585366; child recalls are 0.733813 and 0.756098. Both classes remain visible. The wine adapter uses alcohol quartiles with cutpoints 9.5, 10.1, and 11.0 calculated from training inputs. Its positive-over-zero residual ratio triggers linear under the unchanged rule. Ordinary error slices can emphasize classes differently from balanced accuracy; the diagnostic is a teaching heuristic, not a proved causal mechanism.

Prior wine outcomes were known to the author. These fits verify the frozen-procedure replay and its interface, not unseen transfer. The improver did not change. Its separate revision proposal is unexecuted.

## Other executed mechanisms

- **Output correction:** replaced the deliberately false MAE 1 with 159.947912. A separate process then used the unchanged weak reporter and repeated another supplied wrong score. No fresh LLM session was tested.
- **Reflection:** recomputed training and selection metrics for two saved synthetic cases. Selection favors linear for regression and tree for classification. “Always tree” fails one case. These are known replays, not new validation tasks.
- **External memory:** a later process reads the memory hash and metric direction, changing a decision between cached wine candidates. The no-memory numeric-minimization control is deliberately weak. A separate metric-mismatch fixture refuses an invalid comparison.
- **Instruction modification:** two report cases under both versions. The child recomputes from predictions, preserves the valid report, and repairs the wrong one. External acceptance stays fixed; the old instruction remains.
- **Cost:** reconciled all four bike attempts and checks, including the two rejected initial candidates. Unknown authoring, diagnosis, and provider costs stay unknown. The 20-second proposal break-even calculation is separately labelled numerical illustration.
- **Component ablation:** all four parent/child × memory combinations execute the saved rules. Cached balanced accuracies are 0.5, 0.5, 0.744955, and 0.5. The interaction is −0.244955. A separate fifth fixture removes the restrictive rule and restores the child's choice. This does not measure LLM conflict resolution.
- **Rollback:** saved the valid active pointer, installed a labelled invalid metric-switch instruction, recomputed majority metrics, rejected the promotion, and restored identical prior bytes. The rejected version, invalid pointer, and separate hypothetical accuracy task remain.

## Accounting and course changes

The corrected run has 18 successful child commands, 0.812581 recorded fit seconds, 39.233176 summed child wall seconds, and 41.616836 parent seconds through reporting. Nested timings overlap. The first failure and later author work add overhead that is not fully metered. No final evaluation, retries, GPU jobs, or cluster jobs occurred.

Copied and verified 160 original successful-run files. The four-arm chart and its exact plotting source were generated afterward and have a separate manifest. Inspected the chart's values, zero-based axis, labels, legend, and replay subtitle at full size. It is a scientific plot, not an Imagen asset. Narrow-page rendering remains separate.

Updated nine lesson examples with direct evidence links. Clarified that 07.02 reuses its two cases for the broad-rule contrast, 07.03's additional scope fixture has no extra fit, and 07.08 checks both instruction versions on the same two cases. All nine lessons retain their learner predictions, explained quizzes, takeaways, recovery, and next steps.

The activity inventory now maps 63 labs to related execution evidence and leaves 38 unmapped. Every core lab in themes 00–09 has a mapping, but several still have explicit closure gaps. Mapping is not completion. Real learner responses, fresh native-agent contexts, new reflection-validation tasks, uncontaminated transfer, remaining research studios/capstones, source-method review, and requested Imagen work remain open.

Local publication validation after integration: all 101 lessons and 2,193 local links pass. README guidance covers 101/101 labs. All 180 original files across both attempts still match their manifests; the chart's separate manifest, exact restored pointer, and unchanged improver also match. The reusable authoring skill validates and all seven installed files match its canonical source. The shared runtime was unchanged; the eight executed fits and their prediction checks verify this pass's use of it.
