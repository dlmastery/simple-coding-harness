# Stage 5 - File editing tools

Two more tools: a write-file tool and a string-replace tool. The
write-file tool writes a new file to disk. The string-replace tool swaps
one block of text in a file for another.

**What this stage adds:** the agent can change code. Two tools in
`tools.py`, one line in the system prompt.

## The code, piece by piece

### 1. `write_file`

`tools.py`:

```python
def write_file(path: str, content: str) -> str:
    """Create a file, or overwrite it if it already exists."""
    with open(path, "w") as f:
        f.write(content)
    return f"Wrote {path}"
```

`write_file` takes a path and a content string and calls `f.write`. Note
what it returns: a short confirmation, not the content. Tool results go
into the model's context, so a tool should say what happened, not echo
what it was given.

### 2. `str_replace`

`tools.py`:

```python
def str_replace(path, old_str, new_str, allow_multi_edit=False):
    """Swap exact text in a file. old_str must match exactly once."""
    with open(path) as f:
        content = f.read()

    count = content.count(old_str)
    if count == 0:
        return f"Error: old_str was not found in {path}"
    if count > 1 and not allow_multi_edit:
        return (
            f"Error: old_str matches {count} times in {path}. "
            "Add surrounding lines to make it unique, "
            "or set allow_multi_edit to replace them all."
        )

    with open(path, "w") as f:
        f.write(content.replace(old_str, new_str))
    return f"Replaced {count} match(es) in {path}"
```

`str_replace` takes a path, the old string to replace, and the new
string. If the old string is found, the tool calls `content.replace` and
writes the result back to the file.

The two `Error:` branches are the important design choice. Zero matches
means the model is editing from memory rather than from the file. Two
matches means the edit is ambiguous. Both come back as the tool's
*result string*, so the model reads the error, re-reads the file and tries
a more specific `old_str`. Nothing is raised. The session never dies over
a bad edit. `allow_multi_edit` covers the replace-all case, where every
`hello world` becomes `goodbye`.

Why exact text rather than line numbers? The model's idea of line numbers
drifts the moment it makes one edit. Exact text does not drift.

### 3. The prompt tells the model how to edit

`llm.py`:

```python
Use write_file to create files and str_replace to edit them.
```

## Run it

```bash
python agent.py
> write a new file called hello.txt with five hello worlds
> replace every hello world with goodbye
```

The second request uses replace-all, so every match is swapped. The model
reads the file, then calls `str_replace`. The new file contains five
`goodbye` lines. The harness is now a coding agent that can write files.

## Diff from stage 4

```bash
diff ../step_04_skills/tools.py tools.py
diff ../step_04_skills/llm.py llm.py
```
