# Clean journey results

The [protocol](CLEAN-JOURNEY-PROTOCOL.md) predates execution. Source checkout: `75e9988`. Python 3.12.12, Windows AMD64, fresh installation from the four pinned course requirements. The complete resolved package list is retained with the evidence.

## First checkpoint

The [published artifacts](../../../rsi/evidence/2026-09-20/clean-journey/README.md) cover the principal actions of 00.01–00.04, 01.01–01.05, 02.01–02.05, 03.01–03.06, 04.01–04.05, and 05.01. This is a mechanism-coverage statement, not a claim of complete learner acceptance for every listed lab.

Actual totals: 16 foundation fits, 38 recorded child commands, 25 graph/domain checks, and one further fixed-system baseline. The intended wrong-row rejection, duplicate refusal, two exhausted-budget refusals, ineffective repair exit, stale dependency check, and future-weather refusal all occurred. No final evaluation ran.

The foundation [driver](../scripts/run-clean-journey-foundation.py) writes and follows a fixed process, creates a learner-owned skill, uses the separate result checker, runs controlled ML changes, and invokes the [generated controller](../scripts/journey-controller.py) in distinct Python processes. The structure [driver](../scripts/run-clean-journey-structure.py) uses the supplied graph primitives and adds concrete file, routing, repair, recovery, domain, and release-time fixtures.

The original clone and environment remain local and reconstructible from the recorded commit. A copy of all 257 generated files was verified byte by byte before publication. The rendered data chart and workflow were inspected. The workflow rendering used Mermaid CLI 11.17.0 with a white background. No Imagen asset was generated.

## Limits and omissions

- Same authoring-agent context throughout; fresh-agent handoff in 01.05 is not established.
- Learner predictions, all quizzes, and teach-back: unattempted.
- Several per-lab progress notes were reconciled after the foundation stage; they are labelled. The actual 02.05 stop checkpoint predates resumption.
- The 01.04 calculation reuses the course checker; it is not evidence that a student agent independently generated a different checker.
- The 03.03 resource passes are declared fixtures, not measured resource checks. The checks ran sequentially.
- The 03.06 report distinguishes the three views, but separate rendered diagrams for all three views were not generated.
- A forced process interruption and stale-lock recovery were not run; 02.05 tests a clean stop between completed child processes.
- Optional changes not represented by retained artifacts were not executed. 02.06 and most later lessons remain outside this first stage.

## Repair found by the walkthrough

The comparison output used the shared twelve-attempt ceiling even for a three-attempt lesson. Added an agent-facing `--attempt-limit` option on the first fit. Later run, compare, and final CLI processes recover the same limit. Changing it is refused. A normalized-text contract checksum detects accidental edits; the host agent can still alter both files, so it is not a security boundary.

A meaningful regression test starts a one-attempt experiment, compares it in another process, tries another fit, tries a higher limit, and alters the recorded budget. It checks the correct displayed limit and each refusal. The complete local suite passed **16 tests in 17.05 seconds**; the publication check had no issues. These checks use the revised authoring source, separate from the unmodified journey clone. Older contracts continue only with their original tool version.

Next: generate complete task-specific harness packages from the prose briefs, execute their refusals and classification adaptation, then perform the bounded improver comparison and final claim audit.
