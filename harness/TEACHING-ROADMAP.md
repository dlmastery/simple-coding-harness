# Teach the mechanism before the integration

[Course](../README.md) · [Every lesson](COURSE-MAP.md) · [Glossary](GLOSSARY.md)

Students should leave with an account they can defend: what the model proposed, what actually executed, what evidence returned, and why the process continued or stopped. A polished answer alone does not demonstrate that understanding.

![The seven themes build a controlled and inspectable agent around a model call.](assets/overview-v1.png)

## Choose a route

| Route | Content | Honest outcome |
|---|---|---|
| Two-hour orientation | Selected activities from 1, 2.3 and 2.4, after setup | Trace a file observation through the loop; this is a preview, not three completed lessons |
| Core | All 18 lessons in themes 1–2 | Explain and inspect the local harness, its controls and context |
| Full course | All 54 lessons across seven themes | Compare implementations and demonstrate a recoverable, inspectable small task |

Allow approximately 30–50 hours for the full course's reading, guided discussion and small exercises, plus setup, live provider work and the independent capstone. This is a provisional teaching estimate, not a sum of measured student times. Use learner feedback to set the final timetable. No GPU training is required.

## Plan the seven blocks

Each block can span several meetings. Use the course map for the precise ordered list; original stage 2 contains four lessons.

| Block | Lessons | Bring forward | Readiness demonstration |
|---|---|---|---|
| 1. Foundations | 1–8 including 2.1–2.4; 11 lessons | Basic file/function knowledge and working setup | Trace a real tool result into the next request; distinguish session state from current files |
| 2. Control | 9–15; 7 lessons | An understood local loop | Show a refused action and explain how approval differs from containment |
| 3. Adapters | 16–20; 5 lessons | Loop, tools, state and permission model | Compare ownership in one local and one SDK example; mark live compatibility separately |
| 4. Tools | 21–30; 10 lessons | Local stage-15 harness; adapter knowledge helps comparison | Follow a streamed or background operation into an outcome and an evaluation check |
| 5. Recovery | 31–38; 8 lessons | Action identities and explicit outcome records | Recover a disposable task from inspected state; explain an uncertain action |
| 6. Production | 39–45; 7 lessons | Recovery and the first capstone | Read a trace, locate a stopping reason and distinguish replay from new execution |
| 7. Server | 46–51; 6 lessons | Earlier mechanisms and stream-status handling | Compare client/server responsibilities and diagnose a stream without a terminal event |

For a shorter local-harness course, complete blocks 1–2, then 4–6; treat adapters and the server as comparisons. That route is 43 lessons, not the complete 54. Preserve the relevant prerequisites when selecting individual extensions.

## Use one meeting well

For a 90-minute meeting, spend 10 minutes recalling the previous result, 15 tracing the new figure and predicting behavior, 30 running one bounded action, 20 inspecting a failure and explanation, and 15 answering the quiz and saving the next step. A long integration should stop at a valid checkpoint and resume later.

Ask students to trace arrows in the infographic before showing code. Then connect each arrow to an actual function, message or event. A conceptual diagram can explain the intended mechanism; a trace is needed to establish what occurred in a particular run.

Use pairs when practical. One student directs the experiment; the other checks its evidence. Swap roles. The coding agent should not answer its own assessment questions on the student's behalf.

## Assess understanding

Score each lab note from 0–2 on four criteria: a testable prediction, a recorded observation, a causal explanation, and a limit or transfer case. Treat this as a classroom rubric, not a validated assessment instrument.

Revisit a prerequisite if a student equates text with execution, approval with isolation, a saved chat with restored files, or replay with reproduction. The theme quizzes target these confusions. Do not reward the memorization of provider names or file paths.

## Start the capstone early

After block 2, choose a small disposable project: for example, repair a deliberately failing test in a tiny command-line program. Declare allowed files, a success check, an attempt limit and the human decisions required. The agent can create the implementation; the student owns the task and its acceptance criteria.

At block 5, use the existing step-38 capstone or a documented equivalent. Require an initial failure, a bounded change and checked evidence. Do not replace its original task and claim the original benchmark result.

By block 6, add an inspectable run record and a recovery demonstration. Block 7 can compare a hosted execution if the service is available. A fake-server check remains a client-contract check.

Finish with a compact portfolio: task brief, source versions, setup, prediction, actual commands and results, one failure, one controlled intervention, trace explanation, costs and limits. Let another student reproduce a small part and record what they actually did. An unperformed peer review stays pending.

## Improve the course from a pilot

Record setup time, confusing terminology, useful figures, wrong predictions and recovery difficulties. Update estimates from those observations. Instructor inspection, offline tests and a genuine learner session provide different evidence.
