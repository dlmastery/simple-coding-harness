# Harness reorganization validation

This file separates publication checks, offline behavior tests and live integration evidence. The organization and illustration checkpoint is `24a8b4aa2c3f357569522fd8a04dabd5a4a08f12`, verified on the authorized GitHub branch.

The original README and discovery scripts were backed up before changes. The first offline pass is retained in `validation/before-tests.txt`; many tests could not collect because this environment initially lacked harness dependencies. The environment had no pip module. The failed installer command is retained, followed by the successful `uv pip` installation log. No model key or hosted run was used.

After the move, the test and snippet runners discover `harness/*/step_*/` and retain numeric selectors. GenUI and RSI remain separate series; one GenUI diff command was updated to the new path.

## Actual results

| Check | Result | Evidence |
|---|---|---|
| All 54 harness suites | 785 passed, 7 skipped, no failures; runner exit 0 | [Final test output](validation/final-tests.txt) |
| Repository-wide quoted code | 705 snippets, zero mismatches | [All snippets](validation/all-snippets.txt) |
| RSI publication integration | 101 lessons, 5,680 local links, zero problems | Existing RSI checker, run after the move |
| RSI behavior integration | 20 tests passed after dependency installation and relocation | [RSI output](validation/rsi-integration.txt) |
| Harness publication | 54 unique lessons; all checked local file links resolve | [Publication output](validation/publication.txt) |
| Source preservation | 1,396 non-Markdown lesson files match the pre-move Git objects; one test has the expected path-discovery change | [Publication checker](scripts/check-publication.mjs) |
| Illustrations | 8 selected figures, 11 retained versions; visual review completed | [Review and prompts](visuals/README.md) |
| Learning support | 54 lesson-specific questions and explained answers; 7 theme quizzes; tutor, glossary and roadmap | [Lesson-check source](scripts/lesson-checks.mjs) |

Numeric selector `2` ran all four stage-2 suites successfully (15 tests). An unknown selector exited 1 with a specific no-match message. The comparison suite passed its 16 tests again after the lesson quiz was added. The final publication inventory is 69 pages and 887 local file links; a separate provenance check found all 42 links present.

The seven skips are four absent optional SDK modules, an unavailable operating-system sandbox, the opt-in live Chromium check and TypeScript type-checking because its local compiler was not installed. The Node runtime tests did run. Skips are not counted as passed. This run used the local Windows/Python environment. Live model requests, browser/desktop integrations, a deployed TrueForge service, cross-platform execution and learner outcomes were not newly validated here.

## Failures and repairs

The first post-move run found two comparison tests still searching the old root folders. They now search the seven theme directories. The same run found eight pagination failures because the open-ended dependency range installed TrueForge SDK 0.2.0, whose local implementation returns `SyncPager`; the teaching code expects 0.1 response objects. `requirements.txt` now specifies `trueforge_sdk>=0.1.3,<0.2`. Installing 0.1.3 repaired those failures. The three affected suites passed all 50 tests before the complete pass.

The runtime teaching implementations were preserved. This dependency bound is deliberate compatibility maintenance, not a migration to the newer SDK. A future SDK upgrade should revise pagination code, snippets and the fake-server tests together. The remote skill example in step 48 still references the existing `main` layout; this branch is not merged. Review that reference before a future default-branch migration.

The runner now prints progress immediately, accepts numeric and theme selectors, distinguishes an optional collection skip from a failed test, and rejects an empty selection. No failed assertion was converted into a pass.

The first draft link check incorrectly recognized Python indexing/calls inside code examples as Markdown links. The checker now excludes code fences and inline code. The original draft output is retained. Test logs were normalized only for line endings and trailing whitespace after the first checkpoint; substantive output is unchanged.

## Limits

Local file-link checks do not establish remote URL availability or audit every historical external claim in the original walkthrough. The preserved examples contain dated provider details; the new start guide requires students to verify access and compatibility before live use. Duration estimates need a learner pilot. The figures explain intended mechanisms and do not certify security, deployment readiness or universal agent support.
