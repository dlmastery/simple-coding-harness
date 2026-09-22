# Organize the harness course

Requested on 22 September 2026: reorganize the parent simple-coding-harness course and add professional infographics. The earlier course-building preferences still apply: patient explanations, themed directories, student-facing skills, clear navigation, quizzes, white-background illustrations, preserved originals and regular GitHub checkpoints.

## Scope and decisions

Preserve all 54 runnable lesson snapshots, their IDs and code explanations. Move them into seven themes under `harness/`: foundations (1–8, including four stage-2 lessons), control (9–15), adapters (16–20), tools (21–30), recovery (31–38), production (39–45), and server (46–51). Keep GenUI and RSI as separate series. Their links into the moved course must be updated.

The main README becomes a short course entrance with objectives, prerequisites, scope, a visual explanation, routes and a complete index. Preserve the old README byte-for-byte before replacing it. Add a start page, glossary, teaching roadmap and a tutor skill. Existing detailed code remains available; students can ask the agent to run and explain it without typing implementation code.

Make one overview and seven theme-specific infographics with the available built-in image generator, already authorized by the user. Each figure needs a factual brief, readable labels, a concrete mechanism, a caption explaining its limits, and a visual review. Keep prompts, originals, selection notes and checks in this directory. Images explain conceptual behavior; they do not invent measured outcomes.

## Implementation and acceptance

1. Back up the old README and test-discovery tools; capture the baseline offline test results.
2. Inventory lessons and paths. Relocate within the verified repository root and repair navigation, commands and test discovery. Preserve numeric test selectors.
3. Write course and theme guides, source/path migration index, tutor instructions, and lesson navigation/learning checkpoints.
4. Generate and inspect all eight figures. Link them from the appropriate pages with text explanations.
5. Compare tests before and after, check code snippets, internal paths and coverage, and report inherited failures separately from migration defects.
6. Checkpoint to `codex/rsi-masterclass-rebuild`, verify the remote hash, and update the restart record. Do not merge to main.

This is a course organization and teaching-support change, not a claim to have revalidated every external provider or current SDK release. Offline tests, hosted execution and learner validation need separate status.
