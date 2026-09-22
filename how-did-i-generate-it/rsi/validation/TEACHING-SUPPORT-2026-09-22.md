# Glossary and teaching roadmap

The user requested a glossary and teaching roadmap after the author handoff. This follow-up adds teaching support to the completed course. It does not reopen the completed authoring goal or establish learner validation.

## What changed

- Expanded the [glossary](../../../rsi/GLOSSARY.md) from its quick-reference table into 113 definition entries grouped around experiments, agent operation, revisions, evidence, research and compute. Added worked metric examples, ten commonly confused distinctions, lesson links and a short self-check.
- Added the [teaching roadmap](../../../rsi/TEACHING-ROADMAP.md): a two-hour preview, the 58-lab core and the full 101-lab route. Its 18 teaching blocks include prerequisites, outputs and explanations. Dense blocks can span several meetings; the calendar is not a measured completion promise.
- Added a 90-minute session pattern, readiness checks, capstone planning milestones, shorter studio routes, a complete tutor entry point and pilot feedback instructions. Reused the existing course mindmap without image generation.
- Linked both resources from the main README, learning path, instructor guide and generated course map. Changed the course-map generator so regeneration retains the links.
- Preserved these requirements in the reusable authoring standard and requirement-coverage table. Synchronized only the changed reference into the installed skill.

The definitions explain the existing course; this was not a new research sweep. Durations retain the existing distinction between guided reading/discussion estimates and additional execution, debugging and independent project time. Source-specific RSI meanings, structural recursion, measured benefit and acceleration remain distinct.

## Editing and checks

The pre-change materials remain in Git at `8d7b72776a89f856cc7229619660a21e0f504de0`. An initial patch attempted to delete and add the glossary in one patch; the tool rejected the duplicate target without changing the file. The corrected update preserved the existing table and added the new sections. No image drafts or model runs were produced.

The calendar was checked against the canonical lesson inventory: 18 sequential blocks, all 101 lesson IDs in order exactly once, and 58 labs in blocks 1–8. The glossary count includes definition rows, not navigation or comparison tables. The publication checker found no missing local file links. It does not validate remote URLs or Markdown anchors; the new section targets were also inspected in their source headings. Whitespace checks passed.

Final check output: `Checked 101 lessons and 5680 local links. 0 publication problems.` A separate heading check passed all eight local section links in the two teaching resources.

The installed reference matched its previously recorded hash before copying. After synchronization, both copies of `references/course-standard.md` have SHA-256 `E1ABC968A2426EDED1DC08458C6F8F16B0A1B799C63F3F511E32FC5E67D7B2CC`.

Runtime tests were not rerun for these documentation-only changes. Actual learner pacing, peer assessment, other native-agent contexts and optional cluster execution retain the limits recorded in the [author handoff](AUTHOR-HANDOFF-2026-09-22.md). Publication checks are not evidence of teaching effectiveness.
