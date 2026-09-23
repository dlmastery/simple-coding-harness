# Presentation links survive regeneration

The RSI workflow for 5ffdb8b9 failed on Linux, macOS and Windows at the final
source-consistency check. Runtime checks completed successfully. The course-map
publisher omitted the presentation link that had been added to its output.
The [original failure log](ORIGINAL-CI-FAILURE.txt) retains the actual diffs.

Updated both the course-map and visual-guide publishers to retain the new link.
Rebuilding the visual guide also brought four captions into agreement with the
existing canonical lesson captions: WikiSkill, EvoSkill, recursive capstone and
teach-back. These clarify what the recorded exercises actually did. No figure,
model result, learner budget or frozen experiment changed.

The RSI workflow now rebuilds the visual guide as well as the lesson pages.
Its existing stale-output check therefore covers this additional generated page.
The teaching roadmap is maintained directly, not by these publishers.

Local checks: regenerate lessons, map, source index, visual guide, teaching
inventory and activity inventory; confirm the resulting teaching files match
the staged output. Check all selected illustration placements and local links.
Remote verification must use the follow-up commit's actual workflow run.
