# Artifact index

This index covers the current planning and skill-building phase. Git history preserves changes after the first checkpoint. The existing RSI course remains unchanged.

## Checked-in project artifacts

| Artifact | Purpose | Status |
|---|---|---|
| [Master plan](RSI-MASTERCLASS-PLAN.md) | Course design and implementation plan | Proposed; awaiting plan approval |
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

## Future artifacts

When implementation is approved, add lesson drafts, generated tools, failed runs, accepted runs, plots, image prompts and revisions, visual reviews, compatibility checks, compute records, and migration evidence. Use versioned files or Git history. For large artifacts, use an authorized store and a checked-in manifest with version, hash, and retrieval instructions.
