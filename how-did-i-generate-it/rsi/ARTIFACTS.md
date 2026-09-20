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

The [course map](../../rsi/COURSE-MAP.md) indexes 101 authored lessons. Their complete source prose is retained in the lesson modules beside [build-lessons.mjs](scripts/build-lessons.mjs). The publisher produces the themed READMEs, briefs, and navigation. Intermediate builds contained 15, 26, 58, and then 101 lessons. These temporary navigation outputs were regenerated before this checkpoint; the authored source modules are retained, but each transient navigation draft was not separately committed.

The [tool directory](../../rsi/tools/README.md) contains agent-written implementation. Original licensed dataset archives and attribution are in `rsi/examples`. Actual model predictions, reports, charts, and synthetic mechanism-check outputs are in [the dated evidence directory](../../rsi/evidence/2026-09-20/README.md). Validation command outputs and installed versions are retained here under `validation`.

The first publisher invocation failed because three inline Markdown backticks were not escaped inside a JavaScript template. They were changed to HTML code tags; subsequent publication succeeded. The original error was observed in tool output; this note records the correction rather than claiming an archived broken source version.

An optional cleanup of ignored legacy Python cache directories was blocked by automatic command policy. The cache directories were left in place. Navigation discovery now ignores directories without a README. Tracked legacy course files were removed through Git after their paths were verified; their history and migration mapping remain available.

Illustration prompts, generated assets, visual review, complete clean-session lab walkthroughs, and target-backend compatibility evidence remain to be added. No missing artifact is represented as already produced.
