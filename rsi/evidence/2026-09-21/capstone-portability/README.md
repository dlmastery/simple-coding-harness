# Two tasks work here. Other hosts still need tests.

This author walkthrough executes [capstone 11.03](../../../11_capstones/step_03_portability/README.md) with two real fits. It uses the same canonical skill, supplied tool, checker, Windows Python environment, Codex file-reading route and local CPU. The two task adapters are already implemented; this is not automatic adaptation to an unknown task or a transfer test of the previous capstone's revised improver.

| Task | What changed | Observed selection result |
|---|---|---|
| Bike demand | Hourly rental count; chronological split; Ridge; MAE | 99.175924 MAE on 4,358 rows |
| Red-wine classification | Quality at least seven; feature-group split; balanced logistic model | 0.744955 balanced accuracy on 319 rows |

These metrics answer different questions and cannot be ranked against each other. Wine class recalls were 0.733813 and 0.756098; the prediction table retains 74 false positives and 10 false negatives. Bike's largest mean hourly error occurred at hour 8. Neither result establishes why errors occur or superiority over an untested alternative.

## Inspect the procedure and results

- [Protocol](PROTOCOL.md), [before-fit decisions](DECISION.md), and [source identities](SOURCES.csv) define what stayed fixed.
- [Compatibility matrix](PORTABILITY.md) separates executed task paths, planned agent paths, inspected compute contracts and a generated-only backend outline.
- [Bike result](bike/trial-001/RESULT.md) and [check](bike/trial-001/CHECK.md), plus [wine result](wine/trial-001/RESULT.md) and [check](wine/trial-001/CHECK.md), retain actual predictions and validation.
- [Fourteen audit checks](AUDIT-CHECKS.csv), [outcomes](OUTCOMES.csv), [costs](COST.md) and [recovery](RECOVERY.md) connect the claims to records.
- [Available-profile check](available-CHECK.md) and [commandless-profile refusal](no-commands-CHECK.md) implement the controlled capability-removal exercise. They are declaration fixtures; actual host permissions remain unchanged.
- [Handoff](HANDOFF.md), [learner-check status](LAB-NOTE.md) and [future backend outline](BACKEND-PLAN.md) describe how to continue honestly.

Both fits were checked in separate processes. Another process reopened each saved experiment and compared its one successful candidate. That demonstrates state recovery for reading results, not interrupted training resume. Unsupported task, extra bike fit, extra wine fit and changed wine budget requests all returned refusal. Exactly two fits ran.

## Read the boundaries

This host ran both task paths. It did not test Claude Code, Gemini CLI, native skill discovery, an independent context, a GPU scheduler or a cluster. The actual dependency versions are captured; the desktop application build and serving model version were not exposed and remain unknown. No student or peer participated.

The inspection reports and charts include public full-data summaries, including final-partition targets. No final performance score was calculated. Do not describe those data as wholly unseen. The settings were fixed before inspection, and no search followed these smoke results.

The existing [portability illustration](../../../assets/illustrations/capstone-portability-v1.png) was visually inspected and preserved. It explains three separate dimensions. The measured evidence here fills two local task cells; it does not fill every machine or agent shown in the picture.

The [manifest](MANIFEST.csv) covers 73 original files; all archived bytes matched their hashes. Generated figures come from the actual data-inspection tool, not image generation. [Publication notes](PUBLICATION-NOTES.md) explain the later link guides and the initial five-link check failure. The [maintained driver](../../../../how-did-i-generate-it/rsi/scripts/run-capstone-portability.mjs) preserves the run sequence; students invoke the tutor in natural language.
