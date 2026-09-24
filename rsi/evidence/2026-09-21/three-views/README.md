# Read the plan, the inputs, and the history separately

Author audit for lab 03.06, 21 September 2026. Open the completed [three-view walkthrough](v2/VIEWS.md). It contains three distinct rendered diagrams, an artifact table, an audit of the report failure, and a revised plan whose new check has not run.

The selected diagrams are [control](v2/control-view.png), [artifact flow](v2/artifact-view.png), and [trace](v2/trace-view.png), with SVG copies in the same folder. These are technical views of archived evidence. They supplement the course's conceptual infographic and do not change its generated-image counts.

The successful candidate is `00-03/trial-001`; the later `03-05/diagnostic` workspace copied it. The evidence includes the original [command log](../../2026-09-20/clean-journey/COMMANDS.md), [report exception](../../2026-09-20/clean-journey/03-05/diagnostic/REPORT-FAILURE.md), [recovered report](../../2026-09-20/clean-journey/03-05/diagnostic/RECOVERED-REPORT.md), and [recovery checks](../../2026-09-20/clean-journey/STRUCTURE-CHECKS.md). The [source list](v2/SOURCES.csv) pins the inspected local bytes. Publication uncovered older Git line-ending conversion; this checkpoint [restores byte-preserving archives](../../../../how-did-i-generate-it/rsi/validation/EVIDENCE-BYTE-PRESERVATION.md). Earlier commits may contain normalized copies with different byte hashes.

The critical distinction: the recovery folder's `CHECK.md` was copied from the earlier run. The later in-process check returned a score but did not write another `CHECK.md`. Its output supports the recovered report; the copied file alone cannot establish that later event.

The audit matched the archived candidate and prediction identities and confirmed all source hashes stayed unchanged. Zero fits and zero workflow rechecks were performed. Recovery event order is reconstructed from program order and retained outputs; exact timestamps and a separate recovery event journal were not retained. No learner prediction, teach-back, or quiz was tested.

Both rendering versions are preserved. [Revision 2 review](v2/REVIEW.md) records the connector/path layout correction and subsequent prose-path correction. Each version has its source snapshot and manifest; its files were copied and hash-verified. The maintained [renderer](../../../../how-did-i-generate-it/rsi/scripts/build-three-views.py) refuses to overwrite its existing workspace. The [protocol](v2/PROTOCOL.md) defines this as an audit of existing records, not a new experiment.
