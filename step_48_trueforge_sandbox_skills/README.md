# Step 48 - Sandbox, skills and code mode

**What this step adds:** the agent spec turns on TrueForge's sandbox.
The server provisions an isolated environment the first time the model
calls `exec`, streams a `sandbox.created` event, and keeps the sandbox for
the rest of the session. The client prints every event of the turn, lists
the stored events after `turn.done`, and downloads a file the agent
produced through `GET .../download-sandbox-file`. A second script
registers the stage 4 `explain-code` skill from this repository's public
GitHub URL. Code mode needs no code at all: with the sandbox on, the model
can write one script that calls several tools and prints a summary.

Stage 12 wrapped `bash` in an OS sandbox around the agent's own process.
Here the sandbox is a tool the server calls on demand. The agent loop, the
model key and the MCP credentials stay on the server. The sandbox holds
only files and shell commands.

## Quick demo

```text
$ python demo.py
session 01m2g5zs9vxrqvvgvsqb2313zf
> create hello.py that prints hello, run it, and report the python version
turn.created     01m2g5zsbbfsasy5qvekw5vm5y.local
model.message    exec  echo 'print("hello")' > hello.py && python hello.py
sandbox.created  v1:local:/home/you/.local/share/trueforge/sandboxes/01m2g5zs9vxrqvvgvsqb2313zf/01m2g5ztrszsf4xws7d8w8kkeh
tool.response    exit 0  hello
model.message    exec  python --version
tool.response    exit 0  Python 3.12.3
model.message    I created a file named hello.py that prints "hello". When I ran the script, it printed:
turn.done        done  in=5314 out=103

I created a file named hello.py that prints "hello". When I ran the script, it printed:

hello

The Python version in the environment is Python 3.12.3.

stored events: turn.created model.message sandbox.created tool.response model.message tool.response model.message turn.done
downloaded hello.py -> downloads\hello.py (15 bytes)
print("hello")
session deleted
```

The skill part registers, but its body could not load on this machine.
`python register_skill.py` succeeds and `python demo.py --skill` shows the
skill index in the prompt (`skill index in the prompt: 182 tokens`), but
the sandbox's outbound proxy aborts the `git ls-remote` to github.com
(`Sandbox initialization failed ... Proxy CONNECT aborted`), so every
`exec` in that turn fails and no file is produced. Trimmed output:

```text
$ python demo.py --skill
session 01m2g5xza4sdr2wn41rf94t7ma  skills=[s48-explain-code]
> create hello.py that prints hello, run it, and report the python version
turn.created     01m2g5xzbbatr24aret900kee4.local
model.message    exec  echo 'print("hello")' > hello.py
model.message    exec  python --version
sandbox.created  v1:local:/home/you/.local/share/trueforge/sandboxes/01m2g5xza4sdr2wn41rf94t7ma/01m2g5y0tc00x8pcv7btxp0c45
tool.response    error  Sandbox initialization failed: (exit code 1): WARNING: git ls-remote failed (exit 128): fatal: unable to access 'https://github.com/dlmastery/simple-coding-harness/': Proxy CONNECT aborted (skill: s48-explain-code) Failed to install 1/1 git skill(s); see warnings above.
...
turn.done        done  in=23504 out=569
skill index in the prompt: 182 tokens
download failed (404): File not found: /home/you/.local/share/trueforge/sandboxes/01m2g5xza4sdr2wn41rf94t7ma/01m2g5y0tc00x8pcv7btxp0c45/hello.py
session deleted
```

## Files

```text
step_48_trueforge_sandbox_skills/
├── client/                       the sandbox turn and the skill helpers
│   ├── __init__.py               package marker
│   ├── sandbox.py                a sandboxed turn: events, stored events, file download
│   └── skills.py                 skills on TrueForge: front matter to a GitHub-URL manifest
├── skills/explain-code/SKILL.md  the stage 4 skill; supplies the manifest description
├── demo.py                       one sandboxed turn; --skill, --download, --keep
├── register_skill.py             registers the skill from this repo's GitHub URL
├── test_step.py                  offline tests: a fake server streams SSE and serves a file
└── README.md                     this file
```

## Sandbox as a tool, not around the agent

| | Stage 12 | TrueForge |
|---|---|---|
| what is sandboxed | the harness's `bash` subprocess | a separate environment the server creates |
| when it exists | for every command, from the first turn | on the first `exec` call; `sandbox.created` says when |
| where secrets live | in the harness process, next to the sandbox | on the server; the sandbox never sees the model key |
| files | the project directory on disk | inside the sandbox; fetched with the download endpoint |
| lifetime | one command | the session; files persist across turns |

Stage 12 asked the kernel to fence one subprocess. TrueForge keeps the
whole agent loop out of the sandbox and sends only code, files and shell
commands in. A question that needs no shell costs no sandbox. A sandbox
crash loses files, not the conversation.

## The code, piece by piece

### 1. The spec: one flag turns the sandbox on

`client/sandbox.py`:

```python
class SkillRef(Skill):
    """A skill attached by name only. Server 0.1.4 rejects the SDK's default `preload` key."""

    preload: typing.Optional[bool] = None


def agent_spec(skills: typing.Sequence[str] = ()) -> AgentSpec:
    """An inline agent with the sandbox on, file downloads allowed and the named skills attached."""
    spec = AgentSpec(
        model=Model(name=MODEL),
        instructions=INSTRUCTIONS,
        config=RuntimeConfig(sandbox=SandboxConfig(enabled=True, file_downloads=True)),
    )
    if skills:  # an explicit `skills: null` is rejected, so the key is set only when needed
        spec.skills = [SkillRef(name=name) for name in skills]
    return spec
```

`config.sandbox.enabled` is the whole switch. `file_downloads` is on by
default and is written out here so the intent is visible. Skills attach
by name. The SDK's `Skill` model sends `preload: false` by default and
server 0.1.4 rejects the key, so `SkillRef` leaves it out.

### 2. Reading the `exec` tool's result

`client/sandbox.py`:

```python
def tool_output(content: str) -> str:
    """The `exec` tool's JSON result as one line: the exit code and the output, or the error text."""
    try:
        body = json.loads(content)
    except ValueError:
        return content.strip()
    if "error" in body:
        parts = body["error"] if isinstance(body["error"], list) else [body["error"]]
        text = " ".join(p.get("text", str(p)) if isinstance(p, dict) else str(p) for p in parts)
        return "error  " + " ".join(text.split())
    response = body.get("response", {})
    result = (response.get("result") or "").strip() or "(no output)"
    return f"exit {response.get('exitCode', '?')}  {result}"
```

The sandbox tool is called `exec` and takes `intent` and `command`. Its
`tool.response` content is JSON: `{"success": true, "response":
{"exitCode": 0, "result": "..."}}` on success, `{"error": [...]}` when the
sandbox itself failed. Stage 12 returned `stdout + stderr` as one string.
This function brings the result back to that shape.

### 3. Merging deltas so tool calls print before their responses

`client/sandbox.py`:

```python
def merge_delta(index: dict, delta) -> None:
    """Fold a `model.message.delta` into the base message with the same id, as the docs recommend."""
    base = index.setdefault(delta.id, {"content": "", "tool_calls": {}, "finish_reason": None})
    if delta.content:
        base["content"] += delta.content
    for call in delta.tool_calls or []:
        slot = base["tool_calls"].setdefault(call.index, {"name": "", "arguments": ""})
        if call.function and call.function.name:
            slot["name"] = call.function.name
        if call.function and call.function.arguments:
            slot["arguments"] += call.function.arguments
    if delta.finish_reason:
        base["finish_reason"] = delta.finish_reason
```

A `model.message` arrives empty on a live stream and fills in through
`model.message.delta` events that share its `id`. Text is appended; tool
call fragments merge by `index`, the same assembly step 21 did for
OpenAI chunks. The last delta carries `finish_reason` and `usage`, so
that is the moment to print the finished message.

### 4. One line per event

`client/sandbox.py`:

```python
def describe(event, index: dict) -> list[str]:
    """The lines to print for one streamed event. Deltas print only when they complete a message."""
    kind = event.type
    if kind == "turn.created":
        return [f"turn.created     {event.turn_id}"]
    if kind == "sandbox.created":
        return [f"sandbox.created  {event.sandbox_id}"]
    if kind == "tool.response":
        return [f"tool.response    {tool_output(event.content)}"]
    if kind == "model.message.delta":
        merge_delta(index, event)
        return describe_message(index[event.id]) if event.finish_reason else []
    if kind == "turn.done":
        state = event.state
        metrics = getattr(state, "metrics", None)
        tokens = f"  in={metrics.total_input_tokens} out={metrics.total_output_tokens}" if metrics else ""
        return [f"turn.done        {state.status}{tokens}"]
    return []
```

`sandbox.created` has `thread_id: null` because the sandbox belongs to
the session, not to a thread. It carries `sandbox_id`; for the local
provider the id is `v1:local:<working directory>`, which is what the
download step needs.

### 5. The turn, the stored events and the download

`client/sandbox.py`:

```python
def list_events(client: TrueForge, session_id: str, turn_id: str) -> list:
    """Every stored event of a finished turn, deltas already merged, across all pages."""
    events, token = [], None
    while True:
        page = client.sessions.list_turn_events(session_id=session_id, turn_id=turn_id, page_token=token)
        events.extend(page.data)
        token = getattr(page, "next_page_token", None)
        if not token:
            return events


def sandbox_root(sandbox_id: str | None) -> str | None:
    """The working directory of a local sandbox, read from its id `v1:local:<path>`."""
    if sandbox_id and sandbox_id.startswith("v1:local:"):
        return sandbox_id.split(":", 2)[2]
    return None


def download_file(client: TrueForge, session_id: str, turn_id: str, path: str, dest: Path) -> Path:
    """Fetch one file from the turn's sandbox and write it to `dest`. `path` must be absolute."""
    chunks = client.sessions.download_sandbox_file(session_id=session_id, turn_id=turn_id, path=path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as f:
        for chunk in chunks:
            f.write(chunk)
    return dest
```

After `turn.done`, `list_turn_events` returns the same events with the
deltas already merged: the server's copy of step 44's replay log. The
download endpoint is `GET /api/v1/sessions/{session_id}/turns/{turn_id}/download-sandbox-file?path=...`.
The server rejects a relative path (`Path must be absolute: hello.py`),
so the demo joins the file name to the sandbox root. Stage 12 never
needed this step: its files were already on disk.

### 6. The skill: a git URL, not a folder

`client/skills.py`:

```python
def front_matter(text: str) -> dict:
    """The YAML between the two `---` lines of a SKILL.md, as stage 4 read it."""
    if not text.startswith("---"):
        return {}
    _, meta, _ = text.split("---", 2)
    data = yaml.safe_load(meta) or {}
    data["description"] = " ".join(str(data.get("description", "")).split())
    return data


def skill_manifest(name: str = SKILL_NAME, ref: str = "main", skill_md: Path = LOCAL_COPY) -> GitSkill:
    """A `GitSkill` for the stage 4 skill, its description taken from the local copy of SKILL.md."""
    meta = front_matter(skill_md.read_text(encoding="utf-8"))
    return GitSkill(name=name, url=REPO_URL, ref=ref, path=SKILL_PATH, description=meta["description"])


def register(client: TrueForge, manifest: GitSkill) -> list[str]:
    """PUT the manifest (create or replace) and return the names of every configured skill."""
    client.settings.skills.create_or_update(manifest=manifest)
    return [skill.name for skill in client.settings.skills.list().data]
```

Stage 4 globbed `SKILL.md` files under `.agents/skills` and pasted each
name and description into the system prompt. TrueForge accepts a skill
only as a GitHub or GitLab HTTPS URL with a `ref` and an optional `path`:
`PUT /api/v1/settings/skills` with `{"manifest": {"type": "git", ...}}`.
The body is cloned into the sandbox at turn time, under
`/opt/tfy/skills/{name}`. A skill must be pushed before the server can
load it. A copy of the stage 4 skill ships under `skills/explain-code/`
so the reader can see what the URL points at; the manifest takes its
description from that copy.

The usage breakdown in every `model.message` shows the cost of the index:
`input_tokens_breakdown.skills` is 182 tokens with the skill attached and
0 without. That is stage 4's "one line per skill in the prompt", measured.

## Code mode: step 22 taken further

Step 22 ran several tool calls from one model reply in parallel. Code
mode goes one step further: the model writes a Python script that calls
tools through an in-sandbox `mcp_client`, processes the results in code,
and prints only the summary. Intermediate JSON never enters the context.
Tool calls from the script are bridged back to the server, which applies
the stored MCP credentials, so the sandbox holds no tokens.

There is no flag for it. The agent spec's `config` has `sandbox`,
`context_management`, `dynamic_sub_agents`, `ask_user_questions`,
`generative_ui` and `iteration_limit`, and nothing named code mode. It is
available whenever the sandbox is enabled; the model decides per task
whether one direct call is enough or a script is better. Approval rules
still apply: a script that calls a tool matching
`require_approval_for_tools` pauses like a direct call.

## Run it

TrueForge standalone needs Linux or macOS with `bwrap`, `socat` and `rg`
on PATH for the local sandbox; see step 46's setup section for the WSL
arrangement that puts the server on `localhost:8790` for Windows.

```bash
pip install trueforge_sdk pyyaml truststore
cd step_48_trueforge_sandbox_skills
python demo.py                    # the Quick demo above
python demo.py --keep             # keep the session; files persist for a second turn
python register_skill.py          # PUT the s48-explain-code manifest, list skills
python demo.py --skill            # the same prompt with the skill attached
python -m pytest -q test_step.py  # offline, against a fake server in a thread
```

`demo.py` deletes its session at the end unless `--keep` is given.
The skills settings API has no delete route, so `s48-explain-code` stays
registered.

## What to notice

- `sandbox.created` arrives after the first `model.message` with tool
  calls, not before the turn. The sandbox is provisioned when the model
  first needs it, and a turn that never calls `exec` never creates one.
- The event has `thread_id: null`. The sandbox is session-scoped; a
  second turn in the same session reuses it and emits no new event.
- The download endpoint wants an absolute path. For the local provider
  the sandbox id contains the working directory; for Daytona the
  assistant's `sandbox_artifacts` block lists the paths.
- The stored events carry the merged messages. Reading them back is
  simpler than the live stream and is what step 50's replay uses.
- A skill that fails to clone fails the whole sandbox initialisation, so
  every `exec` in the turn errors. Pin a `ref` and check the server's
  network before attaching a skill in production.

## Capability map

| Capability | This codelab | TrueForge |
|---|---|---|
| sandbox | stage 12: `sandbox.py` wraps `bash` in Seatbelt or bubblewrap around the harness process | `config.sandbox.enabled: true`; provisioned on the first `exec`, announced by `sandbox.created` |
| produced files | on disk in the project directory | `GET .../download-sandbox-file?path=<absolute>` with `file_downloads: true` |
| tool results | `bash` returns `stdout + stderr` | `tool.response` with JSON `{success, response: {exitCode, result}}` |
| skills | stage 4: `SKILL.md` under `.agents/skills`, index in the prompt, body via `read_skill` | `PUT /api/v1/settings/skills` with a `GitSkill`; `skills: [{name}]` on the spec; body cloned into the sandbox |
| skill cost | one prompt line per skill | `usage.input_tokens_breakdown.skills` per model call |
| parallel tools | step 22: several calls from one reply run together | code mode: one script calls several tools and prints a summary; automatic with the sandbox on |
| replay | step 44: the JSONL session log | `GET .../turns/{turn_id}/events`, deltas pre-merged |
