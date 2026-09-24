# GenUI course refresh

The user requested fixes to `genui/` and useful illustrations in its READMEs.
Work started from main commit `0d10b486064a9a39f49c028f2cacf902db22ee51` on
24 September 2026. The seven themes and 23 lesson directories are retained.

## Reading experience

The [new introduction](../../genui/README.md) explains the outcome, prerequisites,
estimated duration, learning route, setup, model-call costs, and the distinction
between interface representation and delivery. It lists all 23 lessons, adds
three understanding questions, and links the existing screenshots.

The original long narrative remains in [WALKTHROUGH.md](../../genui/WALKTHROUGH.md),
with a notice separating recorded demonstrations from current verification.
The [complete pre-change backup](backups/README.md) retains the original bytes.

Two generated infographics explain the seven-theme route and the independent
generation/delivery decisions. Their captions identify them as conceptual
figures. Measured screenshots are labelled separately. The built-in image
generator was used with the user's previously approved alternative to Imagen;
no specific model identity is asserted. See [visual provenance](visuals/README.md).

## Repairs

The installed AG-UI 1.0.0 SDK represents state patch operations as typed Python
models. Three existing tests incorrectly expected dictionaries in the in-memory
event. Their replacement checks use the real event encoder and SSE parser, then
assert the browser's JSON Patch payload. The dashboard tests apply the encoded
operations and inspect the resulting state. No protocol assertion was removed.

Fifteen Node test wrappers assume TAP summary text. This host's default reporter
produced different text even when JavaScript tests passed. The relevant direct
commands and two npm scripts now explicitly select the TAP reporter.

The first failing AG-UI run and the full first suite run are retained under
`validation/`. The latter exposed the reporter mismatch after the AG-UI repair.
The final suite output is retained separately. These are test fixtures and
local test servers, not paid model calls or a newly recorded live demonstration.

## Sources and scope

Primary documentation inspected on 24 September 2026:

- [AG-UI shared state](https://docs.ag-ui.com/concepts/state): snapshot/delta semantics and JSON Patch on the wire.
- [A2UI](https://a2ui.org/): representation, component catalogs and transport separation; existing lessons teach their stated protocol version.
- [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview): host-mounted interfaces and bridge responsibilities.

The refresh does not assert a fresh reproduction of all external services,
all historical timing claims, or a new cross-format benchmark. Existing source
versions and recorded outputs remain identifiable. No unrelated harness or RSI
course code is changed.

## Verification completed locally

- 23 suites, 340 Python tests passed; the suites invoke the applicable Node tests and builds. No tests skipped in this run.
- Python 3.12.12, Node 24.19.0, AG-UI 1.0.0, TrueForge SDK 0.1.3 and pytest 8.4.2.
- 182 lesson snippets checked with zero mismatches.
- Seven theme diagrams and orientation links across all 23 lessons.
- Two selected infographics reviewed for labels, order, contrast and conceptual meaning.
- All 529 files in the original ZIP match their source Git blobs.
- The publication scan found two false positives in code examples, which were preserved in its first report. After excluding code spans and fenced examples, it passes 272 local file links with zero problems. This is not a check of every external URL or anchor.

The GenUI-specific workflow runs the same course tests and publication checks
on Linux, macOS and Windows with Python 3.12 and Node 22. Its result must be
inspected after publication. The separate whole-repository workflow also tests
the parent harness; this refresh does not claim to fix unrelated SDK failures.

One long shell command for writing Markdown was rejected by automatic approval
review with only "blocked by policy" returned. It made no changes. The intended
documentation was then written through the file-patch tool and normal file
operations. A setup probe with an incorrect relative Python path and an initial
reporter-edit pass that encountered an npm wrapper also stopped without running
tests; the corrected commands and their actual test results are retained.

## Resume

Use the current `main` checkout after publication. Read this record and the
test outputs before continuing. Keep image prompts, earlier drafts and failed
checks. Do not report a skipped test, historical screenshot, or a conceptual
figure as a successful live integration.
