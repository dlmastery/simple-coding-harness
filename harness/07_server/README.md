# Move the loop behind a service

[Course](../../README.md) · [All lessons](../COURSE-MAP.md) · [Start here](../START-HERE.md) · [Glossary](../GLOSSARY.md)

Theme 7 of 7 · 6 lessons · Original stages 46–51

A client can send a task while a service owns the agent loop. This changes where sessions, tools and approvals live. The client must distinguish a completed turn from a connection that merely ended.

![Move the loop behind a service: a conceptual mechanism illustrated with actions and evidence.](../assets/server-v3.png)

*A fake server checks the client contract. It does not establish the security, availability or compatibility of a deployed service. This figure explains the theme; individual lessons introduce its components gradually.* [Open the full-size figure](../assets/server-v3.png).

## Before you start

Understand the local loop, streamed outcomes and recovery. Complete the relevant earlier mechanism before comparing its hosted version. Use [setup](../START-HERE.md) and a disposable learner workspace. Let the coding agent write commands and implementation changes. You predict behavior, inspect results and explain what happened.

## Work through the theme

Inspect the client code and its fake-server test. Follow the terminal event that sets the turn status, then compare a dropped stream.

| Lesson | Runnable snapshot |
|---|---|
| [Step 46 - The loop on TrueForge](step_46_trueforge_loop/README.md) | [Code and offline test](step_46_trueforge_loop/) |
| [Step 47 - Tools and permissions as MCP](step_47_trueforge_tools_mcp/README.md) | [Code and offline test](step_47_trueforge_tools_mcp/) |
| [Step 48 - Sandbox, skills and code mode](step_48_trueforge_sandbox_skills/README.md) | [Code and offline test](step_48_trueforge_sandbox_skills/) |
| [Step 49 - Context, questions and stop conditions on TrueForge](step_49_trueforge_context/README.md) | [Code and offline test](step_49_trueforge_context/) |
| [Step 50 - Subagents, sessions and evaluation on TrueForge](step_50_trueforge_subagents_eval/README.md) | [Code and offline test](step_50_trueforge_subagents_eval/) |
| [Step 51 - TrueForge versus this codelab versus managed agents](step_51_trueforge_comparison/README.md) | [Code and offline test](step_51_trueforge_comparison/) |

Read the lessons in this order. Each snapshot has its own files; the agent should run its test from that snapshot's directory. Do not install several versions of the same harness command into one environment at once.

## Run, inspect and explain

Ask the tutor to open the first unfinished lesson, explain its new mechanism and run its offline test. Keep live provider calls separate: confirm the available endpoint, credentials and resource limit before using it. Save a prediction and the actual observation in your learner notes.

Try one controlled change in a copy. Predict its effect before the agent edits it. Re-run the relevant check and compare both outcomes. If a dependency or platform capability is missing, keep the error and use the source explanation until setup is repaired; do not describe that as a successful live run.

## Key takeaways

- Map client/server responsibilities and explain incomplete, cancelled, failed and completed turns without treating them as interchangeable.
- A fake server checks the client contract. It does not establish the security, availability or compatibility of a deployed service.
- Keep an actual trace or test result beside each claim about behavior.

## Check your understanding

The socket closes after some answer text, with no terminal event. Which status should the client claim?

<details>
<summary>Hint and explanation</summary>

First name the object whose behavior you are claiming to know. Then identify the observation that supports that claim.

Incomplete or unknown, according to its contract. Text arrival does not justify completed success. Preserve the session identity and investigate before retrying.

</details>

## What's next

Use the [teaching roadmap](../TEACHING-ROADMAP.md) to prepare a small evidence-linked portfolio. Then choose [generative UI](../../genui/README.md) or [RSI](../../rsi/README.md) according to the problem you want to study.
