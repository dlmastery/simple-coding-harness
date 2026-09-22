# Checked-reference protocol

Author walkthrough for lab 10.36, 21 September 2026. This is a deterministic report-audit exercise. It neither reproduces HarnessEvolve nor tests an independent agent's learning.

Before any actions, save a fixed contract, current and prior report fixtures, parent procedure, trace checker, and this protocol. The contract requires nonempty `Target`, `Metric`, and `Split` fields. The current fixture lacks Split; the prior fixture is complete. Correct field presence does not establish scientific validity of their values.

Budget: generate and check four current-case traces, make one skill proposal, run one proposal-quality gate, and evaluate that candidate on two fixtures. Zero fits. Trace construction itself executes file reads and field checks; the four trace validations inspect those records. Record these costs separately from the two candidate evaluations.

The failed parent checks only Target and Metric. The successful reference checks every contract field. The answer shortcut prints the missing-field answer without inspecting inputs. The alternative reads report before contract, then checks all fields. The checker must require actual instrumented reads of both frozen files, correct hashes, complete field coverage, and agreement between check observations and the emitted verdict. Either read order is allowed. A failed reference is not used for diagnosis.

After examining the failed and valid traces, propose one general procedure change: replace the limited field list with all fields in the contract. The quality gate allows only that declarative operation, forbids case-specific field names and answers, and limits instruction growth. It runs before any candidate evaluation. This small gate is a bounded format/content policy, not a general semantic leakage detector.

Freeze the accepted candidate, then evaluate it on current and prior reports. Compare the prior outcome to its predeclared expected result, not to an invented new parent run. Retain only if both match the frozen fixture oracles. No proposal revisions or extra evaluations. A prior expected outcome is a regression control, not evidence of broad retained competence.

All fixtures and expected answers are author-known. The runner is trusted instrumentation, not tamper-proof attestation. Different files do not provide context isolation. Save failed traces, quality and evaluation verdicts, hashes, timing, and the promotion decision. Mark learner checkpoints untested.
