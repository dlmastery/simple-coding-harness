# Stage 6 - Late injection

Some system-level facts are best gathered right before the model call: the
current date, something about the working repository, the git status. Any
information that helps the agent do the task but is not present in the
user's message or the past context. Adding it at request time is late
injection.

**What this stage adds:** a small block of fresh facts attached to every
request, at the very end, and never stored in the transcript.

## The code, piece by piece

### 1. The block

`context.py`:

```python
def git_branch():
    result = subprocess.run("git branch --show-current", shell=True, capture_output=True, text=True)
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
same way. The block is a user-role message because that is the role a
mid-conversation note has to carry on this API. The `<env>` tags tell the
model it is context, not a request.

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

```bash
python agent.py
> what branch am I on and what time is it?
```

No tool call needed; the answer is read off the block.

## Diff from stage 5

```bash
diff ../step_05_file_editing/agent.py agent.py
cat context.py
```
