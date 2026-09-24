# Publish the masterclass on main

On 24 September 2026, the user authorized replacing the default RSI course with
the reviewed masterclass while keeping the old course in a backup.

The replacement is based on masterclass commit
`4764b9c9b1a021b4094e9fe3008544b6a753ac5c`. Its RSI workflow passed on Linux,
macOS and Windows before this publication. The current main branch had six
additional commits to the old course, so the original pre-rebuild backup alone
would not preserve its latest state.

## Preserve the latest old course

The [new backup](../../../../backups/rsi-before-masterclass-2026-09-24/README.md)
contains all 500 tracked RSI files from main commit
`c8c5153d87947cf2e872bfe6894e808a97be83d4`. The
[verification script](verify_backup.py) compared every file with its original
Git blob and checked the archive SHA-256. All passed.

Before publishing the replacement, the annotated tag
`backup/rsi-before-masterclass-2026-09-24` was pushed and checked remotely.
Its target is the exact original main commit. The ZIP provides a direct
download; the tag retains the complete original repository for browsing.
The earlier pre-rebuild backup is retained as well.

## Keep the replacement scoped

An isolated checkout starts from latest main. It imports `rsi/`,
`how-did-i-generate-it/rsi/`, `skills/build-research-codelabs/`, and the RSI
workflow from the reviewed branch. This includes the images, measured evidence,
PPTX, notes, authoring sources, failures and intermediate artifacts.

The root README gains current RSI navigation, a course-map preview and backup
link. The test and snippet launchers recognize the themed RSI layout while
retaining main's root harness and GenUI discovery. The root dependency list
adds Matplotlib for the new course runtime. Other course files are unchanged.
The current entry instructions and source-index publisher now point to `main`.
Historical source links continue to identify their original revisions.

The desktop worktree helper did not recognize this task's outer directory as
a Git repository. A normal `git worktree add` from the actual repository created
the isolated checkout instead. No source history was rewritten.

## Validation

- All 500 backup files match original Git objects.
- All 26 RSI maintainer tests pass in the integration checkout.
- The course link scan passes: 101 lessons, 6,326 local links, zero problems.
- All 338 illustration-placement checks pass.
- All 101 lessons have published teaching support and worked examples.
- Generated lesson pages, visual guide, source index and activity inventory
  were rebuilt from their canonical source.
- RSI snippet discovery reports zero problems. Its student prompts are natural
  language; zero extracted code snippets does not establish execution.
- Repository-wide snippet discovery passes: 788 extracted snippets, zero problems.
- The staged import matches the reviewed source byte for byte except for the
  listed publication documentation and new publication record. No other course
  files changed. Newly edited files pass whitespace checks; original source
  documents and archived logs retain their existing whitespace rather than
  altering provenance to satisfy a whole-import whitespace check.

This publication changes the default course, not its research conclusions.
The empirical comparisons remain mixed. Independent student evaluation,
broader agent support and remote compute still have their documented limits.
