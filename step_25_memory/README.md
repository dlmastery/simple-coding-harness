# Step 25 - Persistent memory

**What this step adds:** memory that survives the session. The agent gets
three tools: `remember` writes a markdown note to disk, `recall` reads one
back, `forget` deletes one. Every turn carries an index of what is stored
inside a `<memory>` tag. A `/memory` command lists the notes with their
scope and type. After a compaction, the handoff note is saved as a memory
too, so the next session can pick up where this one stopped.

## Why memory, and why as files

Every session up to now started blank. The agent learned that the user
prefers pytest over unittest, that the build needs an environment
variable, that a refactor was rejected last week. Then the session ended
and all of it was gone. The next session asked the same questions and
made the same mistakes.

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

### 1. Where memories live

`harness/memory.py`:

```python
TYPES = ("user", "project", "feedback", "reference")
SCOPES = ("project", "user")

MEMORY_DIRS = [
    config.HOME / "memory" / session.PROJECT,  # this project's memories
    config.HOME / "memory" / "_user",          # memories that follow you everywhere
]
```

`config.HOME` is `~/.simple-harness`. `session.PROJECT` is the working
directory with every non-alphanumeric character replaced by a dash, the
same key the session store uses. The list is ordered: the project
directory comes first, so a project memory wins over a user memory with
the same name. `SCOPES` lines up with `MEMORY_DIRS` by position. The
tests replace this list with two temp directories, so a test run never
writes under the real home.

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
            meta, _ = parse(path.read_text(encoding="utf-8"))
            name = str(meta.get("name") or path.stem)
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
directory of a few dozen small files is cheap to scan.

### 3. The three tools

`harness/memory.py`:

```python
def remember(name: str, description: str, content: str, type: str = "project", scope: str = "project") -> str:
    """Write a memory, replacing one of the same name in the same scope."""
    if type not in TYPES:
        return f"Error: type must be one of {', '.join(TYPES)}."
    if scope not in SCOPES:
        return f"Error: scope must be one of {', '.join(SCOPES)}."
    directory = MEMORY_DIRS[SCOPES.index(scope)]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slug(name)}.md"
    existed = path.exists()
    front = yaml.safe_dump({"name": name, "description": description, "type": type}, sort_keys=False, allow_unicode=True)
    path.write_text(f"---\n{front}---\n\n{content.strip()}\n", encoding="utf-8")
    return f"{'Replaced' if existed else 'Saved'} {scope} memory '{name}' ({type}) at {path}"
```

```python
def recall(name: str) -> str:
    """Return the body of a memory."""
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    _, body = parse(memories[name]["path"].read_text(encoding="utf-8"))
    return body.strip() or "(empty memory)"


def forget(name: str) -> str:
    """Delete a memory."""
    memories = find_memories()
    if name not in memories:
        return f"No memory named '{name}'."
    memories[name]["path"].unlink()
    return f"Forgot '{name}'."
```

`remember()` writes the whole file. The file name comes from `slug()`,
which lowers the name and keeps only letters, digits and dashes, so the
model cannot pick a path that escapes the directory. Writing the same
name again replaces the file; the result says which happened. A bad type
or scope comes back as an error result, not an exception, so the model
can correct itself. `recall()` and `forget()` look the name up in the
index and act on the path they find. All three return short strings,
because their results go straight into the transcript.

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
after `<todos>` and before the file change reminder. When there are no
memories the tag is left out, so a fresh install pays nothing.

### 5. Registering the tools

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

### 6. The handoff note becomes a memory

`harness/compact.py`:

```python
def remember_handoff(summary):
    """Save the handoff note as a project memory, keyed by the session id."""
    return memory.remember(
        f"handoff-{session.CURRENT}",
        f"handoff note from session {session.CURRENT}",
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
same note is saved as a project memory named after the session id. The
next session sees `handoff-20260912-101010: handoff note from session
20260912-101010` in its index and can `recall` it before asking the user
what happened last time. A second compaction in the same session writes
the same name and replaces the note.

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

Start the harness and tell it something about yourself:

```bash
pip install -e .
harness
> remember that I run tests with `python run_tests.py`, not pytest directly
```

The model calls `remember`. The tool panel shows `Saved project memory
'...'`. Look at the file it wrote:

```bash
ls ~/.simple-harness/memory/
cat ~/.simple-harness/memory/*/run-tests.md
```

Now quit, start a new session, and ask:

```bash
harness
> how do I run the tests here?
```

The late injection panel shows the `<memory>` block with one line. The
model calls `recall` and answers from the note without asking you.
`/memory` lists what is stored. Try `/compact` in a long session and
check `/memory` again: a `handoff-...` entry has appeared.

Run the offline tests from the repository root. They point `MEMORY_DIRS`
at a temp directory, so they never touch `~/.simple-harness`:

```bash
python run_tests.py 25
```

## What to notice

- Memories are files. Open them, edit them, delete them. The agent sees
  the change on its next turn, because the index is rebuilt every time.
- Index in the late block, body on demand. The model pays one line per
  memory per turn. It pays for a body only when it asks for one, the same
  bargain skills made in step 4.
- Two scopes, one lookup. A project memory shadows a user memory with the
  same name. The `/memory` listing shows the scope, so a shadowed entry is
  easy to spot.
- The handoff note is now a memory. Compaction used to preserve context
  within a session; now it also carries it across sessions. Nothing new
  had to be summarised.
- Nothing asks for permission. A memory is a few hundred bytes outside
  the project. The cost of a wrong memory is a wrong belief, which is why
  the prompt tells the model to `forget` and the listing shows what is
  there.

## Diff from step 24

```bash
diff -r ../step_24_computer_use/harness harness
```

Added: `memory.py` (`MEMORY_DIRS`, `parse`, `find_memories`,
`memory_index`, `remember`, `recall`, `forget`, the schemas). Changed:
`context.py` (`memory_note` in the late block after `<todos>`),
`tools.py` (three memory tools in `TOOLS` and `TOOL_SCHEMAS`),
`commands.py` (`/memory`), `compact.py` (`remember_handoff` after the
summary), `llm.py` (system prompt). Everything else is unchanged from
step 24.
