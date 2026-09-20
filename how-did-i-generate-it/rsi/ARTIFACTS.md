# Artifact index

This index covers planning, reusable skills, and implementation. The old RSI course remains in Git history. The replacement is authored and undergoing validation.

## Checked-in project artifacts

| Artifact | Purpose | Status |
|---|---|---|
| [Master plan](RSI-MASTERCLASS-PLAN.md) | Course design and implementation plan | Implementation authorized 20 September |
| [Steering and restart](RSI-STEERING-AND-RESTART.md) | Current user requirements and state | Maintained with steering |
| [Work log](RSI-WORK-LOG.md) | Steps, decisions, checks, and next work | Maintained per milestone |
| [Research inventory](RSI-RESEARCH-SWEEP.md) | Primary sources and reading status | Broad sweep complete; deeper reviews remain |
| [Search log](research/SEARCH-LOG.md) | Query bodies, dates, screening, and access gaps | Recorded from the broader sweep |
| [Claim corrections](research/CLAIM-CORRECTIONS.md) | Source and course issues that affect the rewrite | Planning findings; not complete audit |
| [Redacted source transcript](sources/rsiresearch-redacted.txt) | Historical input for independent review | Unverified; clearly labeled |
| [Redaction script](scripts/redact-transcript.ps1) | Repeat the documented transformation | Executed and checked |
| [Source manifest](sources/SOURCE-MANIFEST.md) | Hashes, transformations, and exclusions | Records originals and public derivative |
| [Reusable skill](../../skills/build-research-codelabs/SKILL.md) | Apply the user's course method to another topic | Full package included |
| [Skill requirement coverage](SKILL-REQUIREMENT-COVERAGE.md) | Map each instruction to the skill | Editorial coverage review |
| [Validation record](validation/PLANNING-AND-SKILL-CHECKS.md) | Actual checks and their limits | Updated after checks |

## Retention boundaries

The raw MHTML, decoded browser HTML, and unredacted text remain local. Their hashes and the redaction process are recorded. Browser captures can include incidental personal or browser information; they are not needed as public course material.

Raw external website dumps are not republished. Source links, dates, reading status, and original research notes are retained. Temporary installed dependencies are reconstructible tools, not authored course artifacts; versions and commands belong in validation records.

Earlier planning drafts were overwritten before the first Git checkpoint and are not recoverable as original files here. Their consequential changes are described in the work log. Do not mistake a reconstructed narrative for an archived draft. All subsequent meaningful revisions and intermediate artifacts must be checkpointed as they are produced.

## Implementation artifacts

The [clean journey](validation/CLEAN-JOURNEY-RESULTS.md) retains a fresh-clone protocol, authored drivers, generated learner artifacts, command logs, negative outcomes, charts, progress records, and a budget-persistence repair. Its coverage table distinguishes mechanism execution from full learner validation.

The [cross-platform record](validation/CROSS-PLATFORM-CHECKS.md) separates the dedicated RSI checks from repository-wide failures. The workflow and its eventual run links preserve the scope of each compatibility claim.

The [organization/emergence walkthrough](../../rsi/evidence/2026-09-20/organization-and-emergence/README.md) retains eight synthetic runs, their protocol, input tables, event CSVs, metrics, interpretation review, and source hash. Its [driver](scripts/run-organization-walkthrough.py) is agent-written; students use the lesson prompts. The [validation note](validation/SELF-STAR-WALKTHROUGH-CHECKS.md) identifies what was exercised.

The [course map](../../rsi/COURSE-MAP.md) indexes 101 authored lessons. Their complete source prose is retained in the lesson modules beside [build-lessons.mjs](scripts/build-lessons.mjs). The publisher produces the themed READMEs, briefs, and navigation. Intermediate builds contained 15, 26, 58, and then 101 lessons. These temporary navigation outputs were regenerated before this checkpoint; the authored source modules are retained, but each transient navigation draft was not separately committed.

The [tool directory](../../rsi/tools/README.md) contains agent-written implementation. Original licensed dataset archives and attribution are in `rsi/examples`. Actual model predictions, reports, charts, and synthetic mechanism-check outputs are in [the dated evidence directory](../../rsi/evidence/2026-09-20/README.md). Validation command outputs and installed versions are retained here under `validation`.

The first publisher invocation failed because three inline Markdown backticks were not escaped inside a JavaScript template. They were changed to HTML code tags; subsequent publication succeeded. The original error was observed in tool output; this note records the correction rather than claiming an archived broken source version.

An optional cleanup of ignored legacy Python cache directories was blocked by automatic command policy. The cache directories were left in place. Navigation discovery now ignores directories without a README. Tracked legacy course files were removed through Git after their paths were verified; their history and migration mapping remain available.

At the initial themed-text checkpoint, illustration prompts, generated assets, visual review, complete clean-session lab walkthroughs, and target-backend compatibility evidence remained to be added. The later entries below record progress against those gaps. No missing artifact is represented as already produced.

The [controlled walkthrough](../../rsi/evidence/2026-09-20/walkthrough/README.md) retains nine fits, final evaluation, and domain failures. The [inherited-procedure exercise](../../rsi/evidence/2026-09-20/inherited-improver/README.md) retains the proposed revision, both versions, a deliberately false fixture, a valid control, and actual check outputs. Both generation drivers are retained in `scripts`. The [checkpoint validation](validation/CONTROLLED-WALKTHROUGH-CHECKS.md) records the commands and limits.

Further artifacts include the [generated harness and its execution](../../rsi/evidence/2026-09-20/generated-harness/EXECUTION.md), [clean-source setup check](validation/CLEAN-SOURCE-CHECK.md), [method-reading notes](research/2026-09-20-METHOD-NOTES.md), [compute guide](../../rsi/compute/README.md), and [visual review](visuals/REVIEW.md). Both technical-diagram galleries retain their source and every rendered PNG. Published diagram copies have a hash manifest. The [raster prompts](visuals/ILLUSTRATION-BRIEF.md) are prepared, not generated images.
