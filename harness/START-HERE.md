# Start with one request

[Course](../README.md) · [Every lesson](COURSE-MAP.md) · [Teaching roadmap](TEACHING-ROADMAP.md)

Your first goal is small: explain what enters a model request and what comes back. Tools, loops and memory come later. You need basic familiarity with files and functions; you do not need to write the example implementation yourself.

## Open the course

Use the repository root in a coding agent with file and command access. If you need a copy, ask the agent to clone `https://github.com/dlmastery/simple-coding-harness` and select the `codex/rsi-masterclass-rebuild` branch. That branch contains this reorganization; do not assume it has been merged into main.

Ask it to read [the tutor skill](skills/harness-tutor/SKILL.md). Native skill discovery is optional: reading the file is the fallback. The skill cannot grant tools that the host agent does not have.

```text
Read harness/skills/harness-tutor/SKILL.md.
Check the environment for the first lesson.
Explain each setup action before running it.
Use an isolated environment and a disposable workspace.
Run the first offline test without a model key.
Then ask me what one request contains.
```

## Prepare the environment

The agent should identify the operating system and Python interpreter, create or reuse an isolated environment, and install the repository's `requirements.txt`. The main course uses Python 3.10 or later. SDK lessons can need `requirements-sdks.txt`; JavaScript examples name their Node and package requirements locally. Do not install every optional backend before learning the first concept.

Have the agent run `python run_tests.py 1` from the repository root with that environment's interpreter. The runner enters the correct lesson directory. The test substitutes a fake model client and checks the request, reply and error handling. Record its actual verdict; a fake-model pass is not a provider connection test.

If the environment has no package installer, repair the environment or use its supported package manager. If an import fails, preserve the missing package name and command before installing anything else. Keep setup errors separate from failed behavior assertions.

## Your first 60–90 minutes

1. Open [minimal chat](01_foundations/step_01_minimal_chat/README.md). Read its purpose and inspect the first request.
2. Predict which messages the fake client should receive. Let the agent point to the test that checks them.
3. Run the offline test. Open the result and identify what it establishes.
4. In a learner copy, ask the agent to change one input message. Predict which assertion or observed request should change, then check.
5. Explain why the model has not read an arbitrary local file merely because its reply mentions one.

Save a short note: prediction, command, actual result, explanation, remaining uncertainty and next lesson. Stop here if the request/observation distinction is unclear. The next stages add a shell tool, generic tools, file reading and then the loop.

## Add a live model only when ready

The early examples read `BASE_URL`, `API_KEY` and `MODEL` from the environment. Use an endpoint and model that you can actually access. Provider-specific API compatibility and tool support need a live check; the examples' model defaults are not recommendations or availability guarantees.

Set credentials locally through your environment or provider setup. Do not save keys in notes or commits. Ask the agent to verify that the values exist without printing them. Declare the request limit and spending limit before a live exercise. Start with one short request.

The offline path remains useful if no endpoint is available. Label it accurately and keep live integration as a separate activity.

## Keep lesson versions separate

Each lesson is a complete snapshot. Many later snapshots install a command named `harness`; installing another one can replace the command's source in that environment. Use one active snapshot per environment or run its local test directly. Do not infer that a command uses the folder currently open in your editor.

Do learner edits in a separate copy. Run shell and file-editing examples only against disposable task files. Inspect the later controls before trusting them with broader access. Existing platform notes explain where an exercise requires additional capabilities.

When a run stops, inspect its files and state before resuming. A saved conversation, a workspace checkpoint and a process restart are different things. The [glossary](GLOSSARY.md) explains them with examples.
