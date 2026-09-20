# Open the course in a coding agent

The common entry point is file reading. Open the repository root in an agent that can read local files, write a separate workspace, and run commands. Paste:

```text
Read rsi/AGENTS.md and rsi/skills/rsi-tutor/SKILL.md.
Guide me through the lesson I name, one step at a time.
You write and run the code. I will predict, inspect, and explain the results.
Keep my work in a sibling rsi-work folder and report the absolute path.
Start by checking the capabilities needed for that lesson.
```

No native skill installer is required for this route. The agent must actually read the file; recognizing its name is not enough.

## Native discovery

An agent may support a native skill folder or command. Ask it to create an adapter that loads the canonical skill from this repository. If it must copy files, record the source hash and regenerate the copy after changes. Do not edit two independent copies.

Claude, Codex, and Gemini do not necessarily share hook, permission, isolation, or session behavior. Test those capabilities separately. Do not translate a hook filename and assume enforcement is equivalent.

## Capability record

| Path | Status |
|---|---|
| Codex desktop reading canonical files and running local tools | Used during course authoring; see the dated evidence record |
| A student following the whole lesson in Codex | Learner study pending |
| Claude Code native skill discovery and execution | Not yet tested for the rebuilt course |
| Gemini CLI native skill discovery and execution | Not yet tested for the rebuilt course |
| Other capable coding agents using file reading | Intended portable route; not verified universally |
| Separate evaluator inaccessible to the candidate agent | Not supplied by the local teaching tool |
| GPU, Slurm, or cloud batch execution | Extension design; target backend tests pending |

If your agent cannot run commands, it can explain the lesson but cannot complete its execution requirement. Preserve that distinction in the progress report.
