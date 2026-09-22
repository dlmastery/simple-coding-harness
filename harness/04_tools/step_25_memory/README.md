# Step 25 - Persistent memory

<!-- harness-navigation -->
[Course](../../../README.md) · [Theme](../README.md) · [All lessons](../../COURSE-MAP.md) · [Tutor](../../skills/harness-tutor/SKILL.md)

You are in **Connect tools and observe the work**. Start with [setup](../../START-HERE.md) if you opened this lesson directly. Previous: [Step 24 - Computer use](../step_24_computer_use/README.md). Next: [Step 26 - MCP client](../step_26_mcp_client/README.md).

[See the theme infographic](../README.md). Ask the tutor to explain this lesson, run its offline test, and pause for your prediction before a change. The detailed code walkthrough below remains available to inspect.
<!-- /harness-navigation -->

**What this step adds:** memory that survives the session. The agent gets
three tools: `remember` writes a markdown note to disk, `recall` reads one
back, `forget` deletes one. Every turn carries an index of what is stored
inside a `<memory>` tag. A `/memory` command lists the notes with their
scope and type. After a compaction, the handoff note is saved as a memory
too, `handoff-latest`, so the next session can pick up where the last one
stopped. A memory's name is its slug: one form for the file, the index and
`recall`.

## Why memory, and what breaks without it

Every session up to now started blank. The agent learned that the user
prefers pytest over unittest, that the build needs an environment
variable, that a refactor was rejected last week. Then the session ended
and all of it was gone. The next session asked the same questions and
made the same mistakes. "How do I run the tests here?" is answered from
the code on the first day and from memory on every day after, if there is
one.

A memory is a fact worth keeping past the end of the session. This step
stores each one as a small markdown file with YAML front matter, the same
shape a skill has. That shape was chosen on purpose. The user can open
the file in an editor, correct it, or delete it. Nothing is hidden in a
database. A memory lives under the harness home, never inside the
project, so it is not committed by accident and does not show up in
`git status`.

Two directories hold the files. One is per project, keyed by the working
directory the way sessions are. The other is shared by every project, for
facts about the user. A memory has a `type`: `user` for the person,
`project` for the codebase, `feedback` for a correction, `reference` for
a link or a ticket. The type is a label for the reader; the code treats
every memory the same way.

The model does not read every memory on every turn. That would fill the
context with notes it does not need. Instead the late block carries an
index: one line per memory, name and description, the same trick step 4
used for skills. The model reads the body with `recall` only when the
index suggests it is relevant.

## The code, piece by piece

### 1. Where memories live, and what a name is

`harness/memory.py`:

```python
TYPES = ("user", "project", "feedback", "reference")
SCOPES = ("project", "user")

MAX_BODY = 8_000  # chars; a memory is a note, not a document
```

```python
MEMORY_DIRS = [
    config.HOME / "memory" / session.PROJECT,  # this project's memories
    config.HOME / "memory" / "_user",          # memories that follow you everywhere
]


def slug(name):
    """A safe file name: lower case, letters, digits and dashes only."""
    cleaned = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return cleaned or "memory"
```

`config.HOME` is `~/.simple-harness`. `session.PROJECT` is the working
directory with every non-alphanumeric character replaced by a dash, the
same key the session store uses. The list is ordered: the project
directory comes first, so a project memory wins over a user memory with
the same name. `SCOPES` lines up with `MEMORY_DIRS` by position. The
tests replace this list with two temp directories, so a test run never
writes under the real home.

`slug()` is the name. `remember("Build Cmd", ...)` stores `build-cmd`,
lists `build-cmd` in the index, and `recall("Build Cmd")` and
`recall("build-cmd")` both find it. Without that rule the file was named
by the slug but the index by the raw string, so `Build Cmd` and `build
cmd` looked like two memories in the index and silently overwrote each
other on disk, and a `recall` by the slug the file had said "no memory
named". Every entry point - `remember`, `recall`, `forget`,
`find_memories` - now normalises first.

### 2. Front matter in, front matter out

`harness/memory.py`:

```python
def parse(text):
    """Split a memory file into (meta, body). Tolerates missing or broken front matter."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, parts[2].lstrip("\n")
```

`parse()` is the reader. The skills loader in step 4 skipped any file
without a name. Memories are more forgiving, because the user may edit
them by hand. A file with no front matter is a body with no metadata. A
file with a name but no description gets an empty description. Broken
YAML is treated as no front matter. Every file under the directory is a
memory; the worst case is an index line with nothing after the colon.

A memory file looks like this:

```text
---
name: run-tests
description: how the user runs the tests
type: feedback
---

Run `python run_tests.py 25` from the repository root, not pytest directly.
```

`harness/memory.py`:

```python
def find_memories():
    """Every memory on disk; name -> {description, type, scope, path}.

    The project directory is read first, so a project memory wins over a
    user memory with the same name.
    """
    memories = {}
    for directory, scope in zip(MEMORY_DIRS, SCOPES):
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            try:
                meta, _ = parse(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:  # unreadable file: skip it, the rest of the index still works
                continue
            name = slug(str(meta.get("name") or path.stem))
            if name in memories:
                continue
            memories[name] = {
                "description": " ".join(str(meta.get("description") or "").split()),
                "type": str(meta.get("type") or "project"),
                "scope": scope,
                "path": path,
            }
    return memories
```

`find_memories()` reads the directories every time it is called. Skills
were scanned once at import, because they do not change during a session.
Memories do: the agent writes one, and the next turn must list it. A
directory of a few dozen small files is cheap to scan. It runs before
every model call, so it must never fail: a file saved in Latin-1 by an
editor is read with the bad bytes replaced, and a file that cannot be
opened at all is skipped. One broken memory used to take down every turn
until it was fixed by hand.

### 3. The three tools

`harness/memory.py`:

```python
def remember(name: str, description: str, content: str, type: str = "project", scope: str = "project") -> str:
    """Write a memory, replacing one of the same name in the same scope."""
    if type not in TYPES:
        return f"Error: type must be one of {', '.join(TYPES)}."
    if scope not in SCOPES:
        return f"Error: scope must be one of {', '.join(SCOPES)}."
    if len(content) > MAX_BODY:
        return f"Error: the content is {len(content)} chars; a memory holds at most {MAX_BODY}. Keep the fact, drop the transcript."
    name = slug(name)  # the one form the file, the index and recall all use
    directory = MEMORY_DIRS[SCOPES.index(scope)]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.md"
    existed = path.exists()
    front = yaml.safe_dump({"name": name, "description": description, "type": type}, sort_keys=False, allow_unicode=True)
    path.write_text(f"---\n{front}---\n\n{content.strip()}\n", encoding="utf-8")
    return f"{'Replaced' if existed else 'Saved'} {scope} memory '{name}' ({type}) at {path}"
```

```python
def recall(name: str) -> str:
    """Return the body of a memory, capped like any other tool output."""
    name = slug(name)
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    _, body = parse(memories[name]["path"].read_text(encoding="utf-8", errors="replace"))
    return history.cap(body.strip() or "(empty memory)")


def forget(name: str) -> str:
    """Delete a memory."""
    name = slug(name)
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    memories[name]["path"].unlink()
    return f"Forgot '{name}'."
```

`remember()` writes the whole file. The slug keeps only letters, digits
and dashes, so the model cannot pick a path that escapes the directory.
Writing the same name again replaces the file; the result says which
happened. A bad type or scope, or a body over `MAX_BODY` characters,
comes back as an error result, not an exception, so the model can
correct itself. The size limit is there because a model that pastes a
whole transcript into a memory makes every later `recall` expensive; a
memory is a fact, with a line or two of why. `recall()` and `forget()`
look the name up in the index and act on the path they find. `recall`
passes its body through `history.cap`, so a hand-written memory of any
size is cut at ten thousand characters like any other tool output. All
three return short strings, because their results go straight into the
transcript.

### 4. The index

`harness/memory.py`:

```python
def memory_index():
    """One line per memory: the index that goes into the late block."""
    return "\n".join(f"- {name}: {m['description']}" for name, m in find_memories().items())
```

`harness/context.py`:

```python
def memory_note():
    index = memory_index()
    return f"\n<memory>\n{index}\n</memory>" if index else ""
```

```python
            "</env>" + todos_note() + memory_note() + changes_note()
```

`memory_index()` has the same shape as `skills_prompt()`. The difference
is where it goes. The skills index sits in the system prompt, which is
built once. The memory index changes during a session, so it goes into
the late block, the user message appended to every request. It lands
after `<todos>` and before the file change reminder. The reason is the
prompt cache from step 14: the system prompt is the cached prefix, and
anything that changes between calls must come after it or the cache is
lost on every call. When there are no memories the tag is left out, so a
fresh install pays nothing.

### 5. Registering the tools, and who gets them

`harness/tools.py`:

```python
    *memory.MEMORY_SCHEMAS,
```

```python
    **memory.MEMORY_TOOLS,
```

The three schemas join `TOOL_SCHEMAS` and the three functions join
`TOOLS`. `permissions.check` has no rule for them, so they are allowed.
A memory file is small and lives outside the project; there is nothing
to protect with a prompt.

`harness/subagent.py`:

```python
# the computer tools too: an explorer reads and reports, it does not click - or write memories
WITHHELD = {"task", "browse", "write_todos", "str_replace", "write_file", "computer_act", "computer_screenshot", "remember", "forget"}
```

The `task` subagent may `recall` but not `remember` or `forget`. Its
prompt says "read and report, not change anything", and a memory is a
belief that outlives the session; only the main agent, which the user is
talking to, writes those. The subagent does not receive the `<memory>`
block either, so `recall` is useful to it only when the lead names the
memory in the request.

### 6. The handoff note becomes a memory

`harness/compact.py`:

```python
HANDOFF_MEMORY = "handoff-latest"  # one note, overwritten: the index must not grow by one per session


def remember_handoff(summary):
    """Save the handoff note as the project's handoff-latest memory."""
    goal = next((line.strip() for line in summary.splitlines() if line.strip() and not line.startswith("#")), "")
    return memory.remember(
        HANDOFF_MEMORY,
        f"where session {session.CURRENT} left off: {goal[:80]}" if goal else f"where session {session.CURRENT} left off",
        summary,
        type="project",
    )
```

```python
    summary = summarize(messages[1:cut], previous_summary(system))
    remember_handoff(summary)  # the next session can recall it
```

Compaction already writes the best summary the harness has of the work
so far. Step 14 folded it into the system prompt and nothing else. Now the
same note is saved as a project memory, `handoff-latest`. The next
session sees `handoff-latest: where session 20260912-101010 left off:
Finish the memory step.` in its index and can `recall` it before asking
the user what happened last time. There is one such memory, not one per
session: every compaction, in this session or the next, overwrites it.
The index is sent to the model on every call, and a line per past
session would make it grow without bound. The description carries the
first line of the note under its heading, so the model can tell whether
the last session is the one it wants.

### 7. Listing, and telling the model

`harness/commands.py`:

```python
def memories(messages):
    """Every memory, with its scope and type."""
    found = memory.find_memories()
    if not found:
        ui.note("no memories yet")
        return messages
    rows = [f"{name:<28} {m['scope']:<8} {m['type']:<10} {m['description']}" for name, m in found.items()]
    ui.note("\n".join(rows))
    return messages
```

`harness/llm.py`:

```python
You have a memory that lasts across sessions. The <memory> block in every
turn lists what is stored, one line per memory. Call remember for durable
facts: who the user is and how they like to work, how this project is built
and run, a correction the user made, a link or ticket worth keeping. Do not
store what the code or git history already records. Before asking the user
something you may already know, look at the <memory> block and call recall
on the matching entry. Call forget when a memory turns out to be wrong.
```

`/memory` prints one row per memory: name, scope, type, description. It
is for the user; the model has the index. The system prompt says what is
worth remembering and, just as important, what is not. Facts the code
already records would only go stale. It also says to check the index
before asking the user a question, which is the whole point of the
feature.

## Run it

Start the harness and tell it something about yourself. Bash:

```bash
pip install -e .
harness
```

PowerShell:

```powershell
pip install -e .
harness
```

Then:

```text
> remember that I run tests with `python run_tests.py`, not pytest directly
```

The model calls `remember`. The tool panel shows `Saved project memory
'run-tests' (feedback) at ...`. Look at the file it wrote. Bash:

```bash
ls ~/.simple-harness/memory/
cat ~/.simple-harness/memory/*/run-tests.md
```

PowerShell:

```powershell
Get-ChildItem ~\.simple-harness\memory\
Get-Content ~\.simple-harness\memory\*\run-tests.md
```

Now quit, start a new session, and ask:

```text
> how do I run the tests here?
```

The late injection panel shows the `<memory>` block with one line. The
model calls `recall` and answers from the note without asking you.
`/memory` lists what is stored. Try `/compact` in a long session and
check `/memory` again: a `handoff-latest` entry has appeared.

Run the offline tests from the repository root. They point `MEMORY_DIRS`
at a temp directory, so they never touch `~/.simple-harness`:

```bash
python run_tests.py 25
```

### Expected output

```text
> how do I run the tests here?

  ┌─ injected ─────────────────────────────────────────────────────┐
  │ <env> ... </env>                                               │
  │ <memory>                                                       │
  │ - run-tests: how the user runs the tests                       │
  │ </memory>                                                      │
  └────────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────────┐
  │ recall {"name": "run-tests"}                                   │
  │ Run `python run_tests.py 25` from the repository root, not     │
  │ pytest directly.                                               │
  └────────────────────────────────────────────────────────────────┘

  agent

  From the repository root: `python run_tests.py 25`. You told me not to call pytest directly.

> /memory
  run-tests                    project  feedback   how the user runs the tests
  handoff-latest               project  project    where session 20260912-101010 left off: Finish the memory step.
```

## Error handling

- **A bad memory call.** `Error: type must be one of user, project,
  feedback, reference.`, `Error: scope must be one of project, user.`,
  `Error: the content is 12000 chars; a memory holds at most 8000. ...`,
  `No memory named 'x'.` Each is a tool result; the model corrects
  itself. Arguments that are not a JSON object or a missing `name` give
  the step 22 strings (`Error: the arguments of recall are not a JSON
  object: ...`, `Error: TypeError: ...`).
- **A broken file on disk.** Non-UTF-8 bytes are replaced on read; a
  file that cannot be opened is left out of the index. Neither stops a
  turn. Broken front matter makes the file a body with no description.
- **A failing command, a dead model call, ctrl-c.** As in step 24: the
  output or a timeout note, `model call failed: ...` ending the turn,
  `(interrupted before this tool ran)` for the calls that were cut. A
  compaction whose summariser call fails is not saved as a memory.
- **Leaving.** `/exit`, `/quit`, ctrl-d, or ctrl-z then enter on
  Windows. Memories are on disk the moment `remember` returns; nothing
  is flushed at exit.

## Gotchas / What this is not

- **Nothing asks before a memory is written or deleted.** `remember` and
  `forget` are `allow`. The cost of a wrong memory is a wrong belief on
  every later session; `/memory` shows what is there and the files are
  plain markdown.
- **A project memory shadows a user memory with the same slug.**
  `forget` on a shadowed name deletes the project copy and un-shadows the
  user copy; `/memory` shows both scopes so the second one is visible.
- **The `<memory>` block costs one line per memory on every call.** A
  hundred memories is a hundred lines in every request. Keep
  descriptions to one line and prune; there is no automatic expiry.
- **Only one handoff note survives.** `handoff-latest` is overwritten
  at every compaction. If the previous session's note matters, `recall`
  it and `remember` it under another name before the next `/compact`.
- **Subagents do not see the index.** The `task` subagent can `recall`
  by name only; the browse subagent has no memory tools at all.
- **`bash` is `cmd.exe` on Windows, with no sandbox**; the memory
  directory is outside the project and outside any sandbox on every
  platform, which is what makes it writable at all.
- **Not a vector store.** No embeddings, no similarity search. The model
  reads a list of names and descriptions and picks by eye.

## What to notice

- Memories are files. Open them, edit them, delete them. The agent sees
  the change on its next turn, because the index is rebuilt every time.
- Index in the late block, body on demand. The model pays one line per
  memory per turn. It pays for a body only when it asks for one, the same
  bargain skills made in step 4.
- The slug is the name. Whatever the model or the user calls a memory,
  one normalised form is what the file, the index and `recall` agree on.
- The handoff note is now a memory. Compaction used to preserve context
  within a session; now it also carries it across sessions. Nothing new
  had to be summarised.
- Nothing here is behind a prompt. A memory is a few hundred bytes
  outside the project. The prompt tells the model to `forget` what is
  wrong, and the listing shows what is there.

## Files

```text
step_25_memory/
├── harness/
│   ├── memory.py      persistent memory: markdown files with front matter, two scopes, slug names
│   ├── tools.py       the registry gains memory: remember, recall and forget
│   ├── context.py     the late block carries the memory index in a <memory> tag
│   ├── llm.py         streams; the system prompt says when to remember and recall
│   ├── commands.py    /memory lists what the agent remembers, with scope and type
│   ├── compact.py     the compaction agent; its handoff note is kept as handoff-latest
│   ├── agent.py       the loop from step 24, image markers included
│   ├── subagent.py    the subagent loop from step 24; task may recall, not remember or forget
│   ├── computer.py    the three computer-use tools from step 24
│   ├── browser.py     six browser tools from step 23, screenshot with the image marker
│   ├── browse.py      the browse subagent from step 23
│   ├── permissions.py allow / ask / deny rules, including browser and computer
│   ├── history.py     keeps the transcript small, pictures included
│   ├── ui.py          replay, streaming panels and headless() from step 24
│   ├── config.py      settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── prompt.py      the input line, on prompt_toolkit
│   ├── sandbox.py     an OS sandbox for bash
│   ├── session.py     append-only JSONL session log; load() repairs a cut-off turn
│   ├── skills.py      skills, unchanged since stage 9
│   └── todos.py       the plan: write_todos and the task list
├── .agents/skills/explain-code/SKILL.md   the stage 4 skill
├── test_step.py       offline tests against a fake client and a temp memory home
├── pyproject.toml     package metadata; version 0.25.0
└── README.md          this file
```

## Diff from step 24

```bash
diff -r ../step_24_computer_use/harness harness
```

Added: `memory.py` (`MEMORY_DIRS`, `slug`, `parse`, `find_memories`,
`memory_index`, `remember`, `recall`, `forget`, `MAX_BODY`, the
schemas). Changed: `context.py` (`memory_note` in the late block after
`<todos>`), `tools.py` (three memory tools in `TOOLS` and
`TOOL_SCHEMAS`), `commands.py` (`/memory`), `compact.py`
(`remember_handoff` after the summary, `HANDOFF_MEMORY`), `llm.py`
(system prompt), `subagent.py` (`remember` and `forget` withheld).
Everything else is unchanged from step 24.

## What the next step adds

Step 26 connects MCP servers: tools from other processes join the
registry under a sanitised name, with the server's environment kept to
what `mcp.json` names.
