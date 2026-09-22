# Harness course artifacts

| Artifact | Purpose |
|---|---|
| [Plan](PLAN.md) | Authorized scope, seven-theme structure and acceptance checks |
| [Work log](WORK-LOG.md) | Decisions, current progress and restart instructions |
| [Path inventory](MIGRATION.tsv) | Every original and current lesson directory |
| [Original README](backups/README-before-reorganization.md) | Unedited pre-change walkthrough, including its historical credits |
| [Guide generator](scripts/build-guides.mjs) | Maintained source for the new course/theme navigation |
| [Theme definitions](scripts/themes.mjs) | Pedagogical goals, quizzes and image briefs |
| [Lesson checks](scripts/lesson-checks.mjs) | All 54 mechanism-specific questions and explained answers |
| [Checkpoint generator](scripts/build-lesson-checks.mjs) | Maintains lesson quizzes and controlled-change prompts |
| [Visual guide](../../harness/VISUAL-GUIDE.md) | All eight selected infographics in learning order |
| [Path repair](scripts/repair-paths.mjs) | One-time migration logic, using the pre-move inventory |
| [Validation](VALIDATION.md) | Checks, failures, repairs and limits |
| [Publication checker](scripts/check-publication.mjs) | Lesson coverage, local links, backup and source identity |
| [Figures and prompts](visuals/README.md) | Selected assets, all variants and review notes |
| [Course](../../README.md) | Published parent-course entrance |

Git history retains successive written drafts. The one-time path-repair script is provenance, not a command to rerun on an already migrated tree. Guide generation and publication checks are repeatable. No new research claim or live provider result is established by this reorganization.
