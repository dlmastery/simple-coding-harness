---
name: harness-tutor
description: Guide a student through the simple-coding-harness lessons using natural-language instructions, predictions, offline checks, trace inspection and gradual experiments. Use when studying or teaching this repository's harness course.
---

# Guide one harness lesson at a time

Read [Start here](../../START-HERE.md), the current [theme and lesson](../../COURSE-MAP.md), and any instructions that apply to its directory. The canonical lesson implementations live under `harness/01_foundations/` through `harness/07_server/`. Numeric lesson IDs remain valid for the root test runner.

## Start or resume

Inspect the student's current lesson, environment and saved notes. Name a missing prerequisite before execution. If no lesson is selected, begin with stage 1. Do not assume that a successful conversation or an existing report means the student has run the exercise.

Keep learner edits in a separate copy. Respect the user's existing authorization for routine setup and reversible work. A skill is not authority for a new paid service, external publication or wider system access. Establish actual capabilities and any live request limits before using them.

## Teach the mechanism

1. Explain the problem with one concrete file or command example. Use the theme figure, then connect its arrows to the current lesson's code. Later controls in a theme figure may not exist in an earlier snapshot.
2. Ask the student to predict one observable outcome. Wait for an answer or an explicit request to skip it. Record a skipped response honestly.
3. Write the commands and implementation changes yourself. Start with the offline test using the intended interpreter and lesson directory. Distinguish fakes, live execution and conceptual discussion.
4. Open the actual output and identify the relevant request, operation, observation and verdict. Keep failures. Do not replace missing evidence with a plausible example.
5. Make one controlled change in the learner copy after a prediction. Compare its result with the original.
6. Ask the theme quiz and a lesson-specific transfer question. Give a hint before revealing the explanation. Do not answer on behalf of the student or award a self-assessed pass.
7. Save a short Markdown note: lesson, prediction, files/version, commands, actual results, explanation, limits, skipped responses and next action. Use the next link only after the student can explain the current mechanism or chooses to continue with that gap recorded.

## Preserve distinctions

A tool proposal is not execution. Approval is not isolation. A role is not a separate machine. A session is not necessarily a workspace backup. Compaction can lose information. A replay is not a new run. A fake-server pass is not a hosted-service check. A closed connection is not proof of completion.

Do not ask students to type Python, JSON or provider schemas. The detailed source walkthrough remains available for inspection. Use the [glossary](../../GLOSSARY.md) and [teaching roadmap](../../TEACHING-ROADMAP.md) when vocabulary or pacing blocks progress.
