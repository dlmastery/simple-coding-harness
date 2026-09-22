# Harness course work log and restart

## 22 September 2026: organization and visual checkpoint

User scope: repair the parent course's organization and add proper infographics. Prior authorization covers commits and pushes to `codex/rsi-masterclass-rebuild`; no merge to main.

Moved all 54 root-level lesson snapshots into seven themes under `harness/`. Replaced the 3,300-line landing page with a guided introduction; preserved the original in `backups/`. Added course map, migration map, start guide, glossary, teaching roadmap, tutor skill, theme quizzes and complete lesson navigation. Existing detailed lesson explanations remain intact apart from path repair and navigation additions. GenUI needed one diff-command path update. RSI was not rewritten.

Generated eight selected illustrations using the built-in image generator. The overview and five theme images use their first versions; production uses version 2, and server uses version 3. Eleven image versions and every prompt remain in the repository. Visual inspection caught misleading arrows and implied compatibility checks; targeted edits corrected them. No unsupported Imagen model claim is made.

Publication check: 54 unique lessons, 68 pages and 812 local file links; zero problems. The implementation identity check finds 1,396 unchanged non-Markdown files and one expected comparison-test migration change. All 500 quoted code snippets still match the implementation.

The initial environment lacked harness dependencies and pip. Preserved failed setup and baseline outputs, then installed with uv. TrueForge 0.2 introduced an incompatible pager return type. The teaching snapshots use 0.1 response objects, so requirements now constrain `trueforge_sdk>=0.1.3,<0.2`. All 50 tests in the three affected suites pass after dependency/path repair. A full final harness pass is running. Optional SDK modules remain explicitly skipped when unavailable. Test-runner selectors support numeric IDs and theme prefixes, report optional collection skips honestly, and reject empty selections.

Next: finish the full offline pass, verify the other-series publication integration, add any missing lesson-level learning checks, inspect the final staged diff and publish the final validation checkpoint. Do not regenerate accepted figures without a concrete defect. Live provider/service and learner validation remain separate, unperformed activities.
