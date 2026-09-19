# Step 48 - Sandbox, skills and code mode

**What this step adds:** the agent spec turns on TrueForge's sandbox.
The server provisions an isolated environment the first time the model
calls `exec`, streams a `sandbox.created` event, and keeps the sandbox for
the rest of the session. The client prints every event of the turn, lists
the stored events after `turn.done`, and downloads a file the agent
produced through `GET .../download-sandbox-file`. A second script
registers the stage 4 `explain-code` skill from this repository's public
GitHub URL; on this machine the registration works and the clone into the
sandbox does not (see the second recording). Code mode is described from
the docs: nothing in this step exercises it.

Stage 12 wrapped `bash` in an OS sandbox around the agent's own process.
Here the sandbox is a tool the server calls on demand. The agent loop, the
model key and the MCP credentials stay on the server. The sandbox holds
only files and shell commands.

## Why a sandbox on the server, and what breaks without one

Step 47's tools run on the client's machine and edit the client's files:
a wrong `bash` command from the model is a wrong command on your laptop,
gated only by an approval prompt. Stage 12 fenced that command with
`bwrap` or Seatbelt, which does nothing on Windows. A server-side sandbox
moves the whole shell somewhere disposable: the model may run anything,
the files live in the sandbox, and the client copies out what it wants.
The cost is visible in this step's client: files come back through a
download endpoint, the turn has one more event to read, and a client that
does not read `turn.done` cannot tell a finished turn from a sandbox that
died (which is why `run_turn` reports a `status`).

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
│   ├── sandbox.py                a sandboxed turn: events, status, stored events, file download
│   └── skills.py                 skills on TrueForge: front matter to a GitHub-URL manifest
├── skills/explain-code/SKILL.md  the stage 4 skill; supplies the manifest description
├── demo.py                       one sandboxed turn; --skill, --download, --keep, --base-url
├── register_skill.py             registers the skill from this repo's GitHub URL
├── test_step.py                  offline tests: a fake server streams SSE, pages events, serves a file
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
        config=RuntimeConfig(
            sandbox=SandboxConfig(enabled=True, file_downloads=True),
            # on by default; this client answers no questions and labels no subagent threads
            ask_user_questions=AskUserQuestionsConfig(enabled=False),
            dynamic_sub_agents=DynamicSubAgentsConfig(enabled=False),
        ),
    )
    if skills:  # an explicit `skills: null` is rejected, so the key is set only when needed
        spec.skills = [SkillRef(name=name) for name in skills]
    return spec
```

`config.sandbox.enabled` is the whole switch. `file_downloads` is on by
default and is written out here so the intent is visible. Skills attach
by name. The SDK's `Skill` model sends `preload: false` by default and
server 0.1.4 rejects the key, so `SkillRef` leaves it out. Questions and
dynamic subagents are on by default in every TrueForge agent; this client
handles neither (step 49 and step 50 do), so both are off and the spec
promises only what the client can show.

### 2. Reading the `exec` tool's result

`client/sandbox.py`:

```python
def tool_output(content: str) -> str:
    """The `exec` tool's JSON result as one line: the exit code and the output, or the error text."""
    try:
        body = json.loads(content)
    except ValueError:
        return content.strip()
    if not isinstance(body, dict):  # a bare JSON string, list or number: show it as it is
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
This function brings the result back to that shape, and shows anything
that is not a JSON object as it came.

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
        detail = getattr(state, "message", None) or getattr(state, "reason", None)  # error and cancelled carry one
        return [f"turn.done        {state.status}{tokens}" + (f"  {detail}" if detail else "")]
    return []
```

`sandbox.created` has `thread_id: null` because the sandbox belongs to
the session, not to a thread. It carries `sandbox_id`; for the local
provider the id is `v1:local:<working directory>`, which is what the
download step needs. A `turn.done` that is not `done` prints its
`message` (error) or `reason` (cancelled) on the same line.

### 5. The turn, the stored events and the download

`client/sandbox.py`:

```python
def run_turn(client: TrueForge, session_id: str, prompt: str, out=print) -> dict:
    """Stream one turn, print every event, and return the ids, the final text, the metrics and the status.

    `status` is "done", "cancelled" or "error" from `turn.done`, and stays
    "incomplete" when the stream ends before that event.
    """
    result = {"turn_id": None, "sandbox_id": None, "text": "", "metrics": None, "status": "incomplete",
              "detail": "", "skills_tokens": 0}
```

```python
def list_events(client: TrueForge, session_id: str, turn_id: str) -> list:
    """Every stored event of a finished turn, deltas already merged, across all pages."""
    events, token = [], None
    while True:
        page = client.sessions.list_turn_events(session_id=session_id, turn_id=turn_id, page_token=token)
        events.extend(page.data)
        token = page.pagination.next_page_token  # the cursor lives under `pagination`, not on the page
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
response is `{"data": [...], "pagination": {"limit", "next_page_token"}}`
and the default page is 100 events; a turn with more tool rounds than that
needs the second page, so the loop follows `pagination.next_page_token`
until it is absent. (The first version of this step read the token from
the wrong object and silently stopped at page one; the test now pages.)
The download endpoint is
`GET /api/v1/sessions/{session_id}/turns/{turn_id}/download-sandbox-file?path=...`.
The server rejects a relative path (`Path must be absolute: hello.py`),
so the demo joins the file name to the sandbox root. Stage 12 never
needed this step: its files were already on disk.

### 6. The skill: a git URL, not a folder

`client/skills.py`:

```python
def front_matter(text: str) -> dict:
    """The YAML between the two `---` lines of a SKILL.md, as stage 4 read it.

    A file without a closed front-matter block, or with YAML that does not
    parse, gives `{}` rather than an exception.
    """
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        return {}
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(data, dict):
        return {}
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
description from that copy. The front matter is matched with the same
regular expression stage 4's loader uses, so a file with no closing `---`
or with broken YAML gives an empty dict, not a traceback.

The usage breakdown in every `model.message` shows the cost of the index:
`input_tokens_breakdown.skills` is 182 tokens with the skill attached and
0 without. That is stage 4's "one line per skill in the prompt", measured.

### 7. The demo

`demo.py`:

```python
    result = run_turn(client, session_id, args.prompt)
    print()
    print(result["text"] or "(no final message)")
    if result["status"] != "done":  # error, cancelled, or a stream that ended early
        print(f"turn {result['status']}: {result['detail'] or 'the stream ended before turn.done'}")

    if result["turn_id"]:  # a stream cut before turn.created has nothing to list
        events = list_events(client, session_id, result["turn_id"])
        print(f"\nstored events: {' '.join(e.type for e in events)}")
```

```python
    if not args.keep:
        client.sessions.delete(session_id=session_id)
        print("session deleted")
    return 0 if result["status"] == "done" else 1
```

```python
    try:
        return run(args)
    except REQUEST_ERRORS as error:  # server down, or a request it refused: one line, exit 1
```

The demo prints the final text, then how the turn ended when it did not
end in `done`, lists the stored events only when a `turn_id` arrived,
downloads the file only when the sandbox is a local one whose path is
known, deletes the session unless `--keep`, and exits 0 only for a `done`
turn. `REQUEST_ERRORS` (`httpx.HTTPError`, `ApiError`) around the whole
run turns a dead server into one line on stderr.

## Code mode: step 22 taken further (from the docs)

Step 22 ran several tool calls from one model reply in parallel. Code
mode, as the TrueForge docs describe it, goes one step further: the model
writes a Python script that calls tools through an in-sandbox
`mcp_client`, processes the results in code, and prints only the summary.
Intermediate JSON never enters the context. Tool calls from the script are
bridged back to the server, which applies the stored MCP credentials, so
the sandbox holds no tokens.

There is no flag for it. The agent spec's `config` has `sandbox`,
`context_management`, `dynamic_sub_agents`, `ask_user_questions`,
`generative_ui` and `iteration_limit`, and nothing named code mode. The
docs say it is available whenever the sandbox is enabled and that approval
rules still apply to a script's tool calls. Nothing in this step exercises
it: the agent here has no MCP servers, so a script would have no tools to
call, and no recording was made. Treat this section as a pointer, not a
result.

## Run it

Prerequisites, on top of step 46's server: a working local sandbox, which
means TrueForge running on Linux or macOS (WSL Ubuntu on this machine)
with `bwrap`, `socat` and `rg` on its `PATH`; and, for `--skill`, outbound
network from the sandbox to github.com. `pip install pyyaml` for the
front-matter parser.

bash:

```bash
pip install trueforge_sdk pyyaml truststore
cd step_48_trueforge_sandbox_skills
python demo.py                    # the Quick demo above
python demo.py --keep             # keep the session; files persist for a second turn
python register_skill.py          # PUT the s48-explain-code manifest, list skills
python demo.py --skill            # the same prompt with the skill attached
python -m pytest -q test_step.py  # offline, against a fake server in a thread
```

PowerShell:

```powershell
pip install trueforge_sdk pyyaml truststore
cd step_48_trueforge_sandbox_skills
python demo.py
python demo.py --skill
python -m pytest -q test_step.py
```

Expected output: the Quick demo above; `downloads\hello.py` (or
`downloads/hello.py`) holds the file. `demo.py` deletes its session at
the end unless `--keep` is given. The skills settings API has no delete
route, so `s48-explain-code` stays registered. `--base-url` or
`TRUEFORGE_BASE_URL` picks another server; `TRUEFORGE_MODEL` another
model.

## Error handling

- **Server not running.** `request failed: http://localhost:8790 is not answering (ConnectError: ...)`
  on stderr, exit 1.
- **A turn that ends in `error` or `cancelled`.** The event line shows the
  message (`turn.done        error  in=100 out=5  model unavailable`), the
  demo prints `turn error: model unavailable` under the final text, still
  lists the stored events, and exits 1. The session is deleted unless
  `--keep`.
- **A dropped stream.** `status` stays `"incomplete"`; the demo says
  `turn incomplete: the stream ended before turn.done`, lists what the
  server stored if a `turn_id` arrived, and exits 1.
- **A failed command in the sandbox.** `exec` returns
  `{"success": true, "response": {"exitCode": 1, ...}}`; the line reads
  `tool.response    exit 1  ...` and the model reads the output. A sandbox
  that could not start returns `{"error": [...]}`, printed as
  `tool.response    error  ...` (the skill recording above).
- **A file that was never written.** `download failed (404): File not found: ...`;
  the demo goes on and still deletes the session.
- **ctrl-c while the turn streams.** A `KeyboardInterrupt` traceback; the
  turn keeps running on the server and the session is not deleted. Run
  `python demo.py --keep` and reuse the id if you want to look at it.

## Gotchas / what this is not

- The sandbox needs Linux or macOS with `bwrap`, `socat` and `rg`. On a
  Windows host that means WSL, and the sandbox's network is whatever WSL
  and the corporate proxy allow: the skill clone failed here for that
  reason, not because of the manifest.
- `--download` works only for the local provider, whose sandbox id
  carries the working directory. For any other provider the demo prints
  `no download: the sandbox id ... is not a local one` and moves on.
- The stage 4 skill body is read from GitHub at turn time, from `main`.
  Pin a `ref` for anything that matters; a clone failure fails every
  `exec` of the turn.
- There are no coding tools on this agent: `exec` in the sandbox is the
  only tool. Step 47's MCP tools and this sandbox are combined in step 50's
  eval runner, not here.
- Questions and subagents are switched off in the spec.
- Code mode is described from the docs and was not run.

## What to notice

- `sandbox.created` arrives after the first `model.message` with tool
  calls, not before the turn. The sandbox is provisioned when the model
  first needs it, and a turn that never calls `exec` never creates one.
- The event has `thread_id: null`. The sandbox is session-scoped; a
  second turn in the same session reuses it and emits no new event.
- The download endpoint wants an absolute path. For the local provider
  the sandbox id contains the working directory; for Daytona the
  assistant's `sandbox_artifacts` block lists the paths.
- The stored events carry the merged messages, one page at a time.
  Reading them back is simpler than the live stream and is what step 50's
  replay uses.
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
| parallel tools | step 22: several calls from one reply run together | code mode (docs): one script calls several tools and prints a summary; not run here |
| replay | step 44: the JSONL session log | `GET .../turns/{turn_id}/events`, deltas pre-merged, paged |

## What the next step adds

Step 49 puts four more codelab mechanisms into the agent spec's `config`
(compaction, large tool output, an iteration limit, the question tool),
answers the model's questions through `tool.response_required`, and draws
the per-call token breakdown the server reports.
