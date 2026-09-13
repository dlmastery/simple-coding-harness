# Step 31 - Project instruction files

**What this step adds:** the harness reads `AGENTS.md` files (or
`CLAUDE.md`, the same thing under another name) from the home directory,
from the git root and from every directory down to the working directory.
Their text goes into the system prompt, one header per file. `/init` sends
a subagent to survey the project and writes its report to `AGENTS.md`
after `approve? (y/n)`. `/instructions` lists the files that were loaded.

## Why a file, and why the system prompt

Every project has facts the model cannot guess: which command runs the
tests, which directory holds the real code, which style the maintainers
insist on. Up to now the user typed them into the chat, again in every
session, or the model found them out by trial and error, again in every
session.

An instruction file writes those facts down once. It lives next to the
code, under version control, so every person and every agent that opens
the project gets the same guidance. A file in the home directory holds the
user's own habits; a file in a subdirectory holds rules for that part of
the tree. The files are read from the most general to the most specific,
so a later file can refine an earlier one.

The text goes into the system prompt, not into the late block. The system
prompt is the stable prefix of every request: it is the same bytes from
the first call to the last, so the provider can cache it and the model
sees the rules before anything else. The late block changes every turn and
is the wrong place for text that never changes.

## The code, piece by piece

### 1. Where to look

`harness/instructions.py`:

```python
NAMES = ("AGENTS.md", "CLAUDE.md")  # the first one found in a directory wins
HOME = Path.home() / ".simple-harness"
MAX_CHARS = 20_000

LOADED = []  # the paths the last instructions_prompt() call read, in order
```

```python
def git_root(cwd=None):
    """The top level of the git repository around cwd, or cwd when there is none."""
    cwd = Path(cwd or os.getcwd()).resolve()
    try:
        done = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return cwd
    if done.returncode != 0 or not done.stdout.strip():
        return cwd
    return Path(done.stdout.strip()).resolve()
```

The git root marks where the project starts. A file above it belongs to
some other project, or to nobody, and is never read. When git is missing
or the directory is not a repository, the working directory is the root,
so the search still finds the file that sits next to the code.

```python
def search_dirs(cwd=None):
    """Home first, then every directory from the git root down to cwd."""
    cwd = Path(cwd or os.getcwd()).resolve()
    root = git_root(cwd)
    chain = []
    for directory in [cwd, *cwd.parents]:
        chain.append(directory)
        if same(directory, root):
            break
    else:
        chain = [cwd]  # the root is not an ancestor: only the working directory counts
    chain.reverse()
    return [HOME] + [d for d in chain if not same(d, HOME)]
```

The chain is walked upward from the working directory and stopped at the
root, then reversed. The home directory goes first, so the user's own file
is the most general and every project file can override it. `same()`
compares paths case-insensitively on Windows, where `git` and `pathlib`
can spell the same directory differently.

### 2. What to read

`harness/instructions.py`:

```python
def find_instructions(cwd=None):
    """Every instruction file, in the order it is read: home, root, ..., cwd."""
    found = []
    for directory in search_dirs(cwd):
        for name in NAMES:
            path = directory / name
            if path.is_file():
                found.append(path)
                break  # AGENTS.md and CLAUDE.md are one file under two names
    return found
```

```python
def read_instructions(path):
    """The file's text, cut at MAX_CHARS with a note that says so."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) <= MAX_CHARS:
        return text
    return (
        text[:MAX_CHARS]
        + f"\n\n[truncated: this file has {len(text):,} characters; only the first {MAX_CHARS:,} are shown]"
    )
```

One directory yields at most one file. `CLAUDE.md` is an alias: it is
read only when there is no `AGENTS.md` beside it, so a project that keeps
both for two tools does not send the same rules twice. A very long file is
cut, and the cut is announced in the text, so the model knows it is
reading a part and the user can see why a rule at the end was not
followed.

### 3. The prompt text

`harness/instructions.py`:

```python
def instructions_prompt(cwd=None):
    """Every instruction file, each under a header naming it; empty when there are none."""
    LOADED[:] = find_instructions(cwd)
    parts = []
    for path in LOADED:
        parts.append(f"# Instructions from {label(path, cwd)}\n\n{read_instructions(path).strip()}")
    return "\n\n".join(parts)
```

The header names the file relative to the working directory, so
`../AGENTS.md` and `AGENTS.md` are two different files and the model can
say which one a rule came from. The home file is named
`~/.simple-harness/AGENTS.md`. `LOADED` remembers the paths for
`/instructions`.

### 4. Into the system prompt

`harness/llm.py`:

```python
def instructions_section(cwd=None):
    """The instruction files with their introduction, or empty when there are none."""
    text = instructions_prompt(cwd)
    if not text:
        return ""
    return INSTRUCTIONS_INTRO + "\n" + text + "\n"


def build_system_prompt(cwd=None):
    """The system prompt for one working directory. Default: where the harness started.

    The instruction files are discovered here, every time, so the prompt is
    built after the discovery and a workspace gets the files that apply to it.
    """
    cwd = cwd or os.getcwd()
    return f"""
...
Your current working directory is: {cwd}
{instructions_section(cwd)}
You have skills available. Each one is a set of instructions for a task.
If a skill matches what the user wants, call read_skill first and follow it.

{skills_prompt()}
"""


SYSTEM_PROMPT = build_system_prompt()
```

`build_system_prompt()` is the function step 30 added so the eval runner
could point the prompt at a task workspace. Discovery runs inside it, so
the prompt is always built after the files are found, and a workspace gets
the files that apply to that workspace. The section is empty when there
are no files, so a project without one gets the same prompt as before.
`INSTRUCTIONS_INTRO` tells the model what the headers mean and which file
wins when two disagree: the later one, because it is closer to the code.

### 5. `/init`

`harness/commands.py`:

```python
def init(messages):
    """Survey the project with a subagent; write the report to AGENTS.md on approval."""
    target = Path.cwd() / "AGENTS.md"
    report = subagent.task(INIT_QUESTION.strip())
    ui.agent(report)
    if report.startswith("(") or report.startswith("Error:"):
        ui.note("the subagent did not produce a guide; nothing written")
        return messages
    if not ui.confirm(f"write {target.name}" + (" (it exists; this replaces it)" if target.exists() else "")):
        ui.note("not written")
        return messages
    target.write_text(report.strip() + "\n", encoding="utf-8")
    if messages and messages[0].get("role") == "system":
        messages[0]["content"] = llm.build_system_prompt()  # discovery runs again, so the new file is in the prefix
    ui.note(f"wrote {target}; it is in the system prompt from the next call on")
    return messages
```

`/init` is the `task` tool called by hand with a fixed question: what the
project is, how it is built, how the tests run, how the tree is laid out,
and which conventions the code shows. The subagent explores in its own
context window, so the survey costs the chat nothing. The report is shown,
then written only after a yes, because the file changes what every future
session is told. The system message is rebuilt at once, so the new file
takes effect in the next call rather than the next session.

### 6. `/instructions` and the approve prompt

`harness/commands.py`:

```python
def instruction_list(messages):
    """The instruction files the system prompt carries, in the order they were read."""
    if not instructions.LOADED:
        ui.note("no instruction files loaded (AGENTS.md or CLAUDE.md in ~/.simple-harness, the git root, or below)")
        return messages
    rows = []
    for path in instructions.LOADED:
        size = len(path.read_text(encoding="utf-8", errors="replace"))
        cut = f"  (cut at {instructions.MAX_CHARS:,})" if size > instructions.MAX_CHARS else ""
        rows.append(f"{instructions.label(path):<40} {size:>7,} chars{cut}")
    ui.note("\n".join(rows))
    return messages
```

`harness/ui.py`:

```python
    def confirm(self, reason):
        """Step 31: say what a command is about to do and ask approve? (y/n)."""
        self.console.print(Padding(Text(reason, style=f"bold {TOOL}"), (1, 0, 0, 2)))
        try:
            answer = prompt.read("  approve? (y/n)> ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        return answer.lower().startswith("y")
```

`confirm()` is `approve()` with the plan-mode wording. It reads through
`prompt.read`, like every other question the harness asks, so a test can
script the answer and a ctrl-d means no.

## Run it

```bash
pip install -e .
harness
```

This directory ships an `AGENTS.md`, so the banner is followed by nothing
new but the model already knows how this step is built and tested. Type
`/instructions`:

```text
AGENTS.md                                  1,794 chars
```

Ask `how do I run the tests here?` and the answer names
`python -m pytest -q test_step.py` without a single tool call, because the
file said so. Now put a personal file in place:

```bash
mkdir -p ~/.simple-harness
echo "Answer in one short paragraph unless asked for more." > ~/.simple-harness/AGENTS.md
harness
```

`/instructions` lists two files, the home one first. Start the harness in
a directory without a file, in any git repository, and type `/init`. The
subagent's panels show it reading `pyproject.toml`, the test files and the
tree; then its report appears and the prompt reads `approve? (y/n)`. On
`y`, `AGENTS.md` is written in the working directory and the next
`/instructions` lists it.

A file over 20,000 characters is cut, the row in `/instructions` says
`(cut at 20,000)`, and the prompt text ends with a line that says how long
the file was.

Run the offline tests from the repository root:

```bash
python run_tests.py 31
python check_snippets.py 31
```

## What to notice

- **The prefix stays stable.** The instruction text is in the system
  message, so it is the same bytes in every request of a session, and the
  provider's prompt cache keeps paying for it. `/init` is the one command
  that changes it, once, on purpose.
- **General to specific.** Home, root, then each directory down to the
  working directory. A rule in a leaf overrides a rule at the root because
  it comes later and the intro says the later one wins.
- **Above the root is nobody's business.** A stray `AGENTS.md` in the
  user's home or in `/tmp` is never read, unless it is the one in
  `~/.simple-harness`, which is on purpose.
- **One name, two spellings.** `CLAUDE.md` exists for another tool. It is
  read only when `AGENTS.md` is absent, so a project with both does not
  say everything twice.
- **The subagent does the survey.** `/init` reuses the `task` tool from
  step 15 with a fixed question. Nothing new was built to explore a
  project; the exploration tool already existed.
- **The cut is visible.** A truncated file says so inside the prompt text
  and in `/instructions`, so a rule near the end of a long file that went
  unread has an explanation.

## Diff from step 30

```bash
diff -r ../step_30_eval/harness harness
```

Added: `instructions.py` (`NAMES`, `HOME`, `MAX_CHARS`, `LOADED`,
`git_root`, `same`, `search_dirs`, `find_instructions`, `label`,
`read_instructions`, `instructions_prompt`). Changed: `llm.py`
(`INSTRUCTIONS_INTRO`, `instructions_section`, `build_system_prompt` places
the section after the working directory line), `commands.py`
(`INIT_QUESTION`, `init`, `instruction_list`, `/init` and `/instructions`
in `COMMANDS` and `handle`), `ui.py` (`confirm`, `/init` in the banner).
Shipped: `AGENTS.md` in this directory. Everything else is unchanged from
step 30.
