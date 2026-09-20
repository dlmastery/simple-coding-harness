# Planning and skill validation

These checks cover documentation, the reusable skill package, and the redacted provenance artifact. They do not establish that course experiments work.

## Environment

- Windows, PowerShell 7.6.
- Bundled Python 3.12 runtime for the existing skill validator.
- PyYAML 6.0.2 installed into a task-local dependency directory because the bundled runtime did not contain it.
- No new Python application code was written. Validation uses the existing skill-creator validator.

## Checks performed

| Check | Observed result |
|---|---|
| First planning commit | `7f6bbd61eb029a307b38525e00beadc57d3535dc` committed and pushed |
| Remote verification | GitHub branch hash matched that local commit |
| Proposed lesson IDs | 99 rows, 99 unique IDs, 36 advanced labs |
| Skill frontmatter and structure | Existing `quick_validate.py` returned `Skill is valid!` |
| Initial validator dependency | First attempt failed with missing `yaml`; task-local PyYAML resolved it |
| Local Markdown links, first pass | Found the not-yet-created validation record; the record was added |
| Source transformation | Redacted transcript generated with the checked-in PowerShell script; source and output hashes recorded |
| Local Markdown links, final pass | 85 local targets across 17 Markdown files resolved |
| Redacted transcript | Output hash matched the manifest; the applied checks found zero email addresses and zero original forwarded-message identifiers |
| Local skill installation | Seven files installed in the personal Codex skills directory; every hash matched the repository package |
| Installed skill validation | Existing validator returned `Skill is valid!` |
| Design review | Common guidance remains topic-independent; RSI requirements use a separate preset; ambiguous topic terms need source verification |
| Working-tree diff check | `git diff --check` passed for tracked edits |
| Staged source whitespace | The initial stage found an extra final blank line; the redaction script now produces canonical UTF-8/LF text, and the manifest records both hashes |

The next checkpoint contains these validated records and the complete skill package. Its push and remote verification are recorded in the work log after they run.

## Repeating the relevant checks

Run `scripts/check-doc-links.ps1` from the repository root, or provide its `RepositoryRoot` argument. It checks local link targets in the planning record and skill package. It does not check remote websites or Markdown heading fragments.

Run the skill-creator package's existing `scripts/quick_validate.py` against `skills/build-research-codelabs`, with PyYAML available. This checks packaging, not the quality of a future course.

Run `scripts/redact-transcript.ps1` with the hashed source text and a destination path. Compare the resulting hash with the source manifest. The script does not claim to be a general-purpose personal-data detector.

The coverage table was reviewed against the user directions. This is a manual editorial check, not an independent classroom trial or a live cross-topic test.
