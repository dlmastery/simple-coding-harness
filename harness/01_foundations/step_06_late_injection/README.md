# Stage 6 - Late injection

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **From a reply to an agent**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Stage 5 - File editing tools](../step_05_file_editing/README.md). Next: [Stage 7 - File freshness reminders](../step_07_file_freshness/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

Some system-level facts are best gathered right before the model call: the
current date, something about the working repository, the git status. Any
information that helps the agent do the task but is not present in the
user's message or the past context. Adding it at request time is late
injection.

**What this stage adds:** a small block of fresh facts attached to every
request, at the very end, and never stored in the transcript.

## Why inject late, and why never store it

The system prompt is the obvious place for "today is ...", and it is the
wrong one. It changes every day (every minute, with a clock), and stage
2.4's rule is that the prefix must not change: one changed token at the
top of the prompt and the whole cached prefix is paid for again on every
call. Storing the block in the transcript is wrong too: after ten turns
there would be ten dates, nine of them stale, all of them costing tokens.
So the block is built fresh for each request, appended after everything
else, and thrown away.

## The code, piece by piece

### 1. The block

`context.py`:

```python
def git_branch():
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True,
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:  # no git, or not a repository: say so instead of guessing
        return "(not a git repository)"
    return result.stdout.strip() or "(detached)"


def reminder():
    """The block we append to the request on every call."""
    return {
        "role": "user",
        "content": (
            "<env>\n"
            f"time: {datetime.now():%Y-%m-%d %H:%M}\n"
            f"git branch: {git_branch()}\n"
            "</env>"
        ),
    }
```

`context.py` holds functions that return small string snippets. Each one
describes a piece of state the agent can use: the git branch, and a
reminder block that shows the current date. Git status can be added the
same way. Outside a repository, or without git installed, the branch line
says so; an empty answer inside a repository means a detached HEAD.

The block carries the `user` role. Chat Completions accepts a `system`
message anywhere in the list, but several providers behind the same API
(Gemini and Anthropic compatibility endpoints among them) accept a system
message only at the top, and every one of them accepts a user message
anywhere. Two user messages in a row - yours, then the block - are legal
and are what most providers see. The `<env>` tags tell the model it is
context, not a request.

### 2. The one changed line in the loop

`agent.py`:

```python
                message, usage = call_llm(messages + [reminder()])  # request = transcript + late block
```

The model call now receives the stored messages plus the reminder computed
for this call. That is the only change in `agent.py`. The messages list
itself is never touched.

`messages + [reminder()]` builds a new list for this request only. The
stored transcript does not contain the block, so old dates and old git
status blocks never reach the model in later turns. One fresh block per
call, no stale copies piling up.

Inside a turn the block also follows the `tool` messages. That is legal:
a `tool` message must come after the assistant message that asked for
it, but nothing has to come last.

## Why at the end

The injected block must always go at the very bottom of the messages
list. The date in it changes with every message. A block at the top
would break the prefix on every call, and the prefix cache would never
hit often enough to save money. This is the stage 2.4 rule applied:
stable things first, volatile things last, and the middle never edited.

The offline test pins both properties: the block is the last item of every
request, and the stored prefix of request two equals request one minus its
block.

## What this enables

The block is a place to put more than the date. Stage 7 adds a warning
about files that changed on disk. Stage 10 adds the todo list. Both ride
in this same message.

## Run it

bash:

```bash
export BASE_URL=https://openrouter.ai/api/v1
export API_KEY=sk-or-...
python agent.py
```

PowerShell:

```powershell
$env:BASE_URL = "https://openrouter.ai/api/v1"
$env:API_KEY = "sk-or-..."
python agent.py
```

Expected output:

```text
> what branch am I on and what time is it?

  312 prompt · 22 completion · 256 cached

  agent

  You are on branch main and it is 2026-09-18 14:02.
```

No tool call needed; the answer is read off the block.

## Error handling

- Not a git repository, or git not installed: the block says
  `git branch: (not a git repository)`; nothing fails.
- Everything from stage 5 (bad tool calls, ctrl-c, dead model calls,
  `/exit`) is unchanged. When a tool call fails, its `Error:` result is
  in the transcript and the block still comes last.

## Gotchas

- `git branch` runs before every model call. On a very large repository
  that is a few milliseconds each time.
- The time is minute precision. Two calls in the same minute send the
  same block, which is fine: it is not in the prefix either way.
- A provider that merges consecutive user messages sees your message and
  the block as one; the `<env>` tags are what keep them apart.

## Files

```text
step_06_late_injection/
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── agent.py         the loop sends messages + [reminder()]
├── context.py       the late injection block: date, git branch
├── llm.py           call_llm, unchanged
├── skills.py        skill discovery, unchanged from stage 4
├── tools.py         tools, unchanged
├── ui.py            the presentation layer, unchanged
├── test_step.py     offline tests: the block is sent but never stored; outside a repo; after tool errors
├── pyproject.toml   package metadata; version 0.4.0
└── README.md        this file
```

## Test

`python -m pytest test_step.py` checks the block's shape, that outside a
repository it says so, that two requests carry one block each at the end
with the stored prefix untouched, and that after failed tool calls the
`Error:` results precede the block.

## Diff from stage 5

```bash
diff ../step_05_file_editing/agent.py agent.py
cat context.py
```

## What the next step adds

Stage 7 uses the same block to warn the agent when a file it read has
changed on disk.

<!-- harness-learning-check -->
## Check your understanding

Why add a fresh observation near its use instead of assuming the initial prompt remains current?

<details>
<summary>Hint and explanation</summary>

Name the object you are making a claim about. Then identify the observation that would support that claim.

Files and state can change after the first request. The relevant observation must reach the later decision; caching concerns do not justify stale facts.

</details>

**Connect it to your run.** Point to one relevant test, trace or source branch in this lesson. Explain what it checks and one thing it does not establish. If you have only read the source, label that as inspection rather than execution.

**Try one change.** Ask the tutor to choose one small input or failure case related to this question. Predict its effect, make the change in your learner copy, and compare the actual outcome. Keep the original and changed results.

Save your prediction, evidence and remaining uncertainty before following the next lesson link at the top of this page. Use the [theme guide](../README.md) to explain why the next mechanism is useful.
<!-- /harness-learning-check -->
