# Step 51 - TrueForge versus this codelab versus managed agents

**What this step adds.** No harness code. This step is a reading, in the
style of step 37. It places every capability the codelab built in steps 1
to 45, and ran on TrueForge in steps 46 to 50, next to two other harnesses
that run as a service: TrueForge itself and Anthropic's Claude Managed
Agents. For each capability there is one table with three columns: how
this codelab does it, how TrueForge does it, and how Managed Agents does
it. Every row links to the page that supports it. The Managed Agents
column comes from the public docs only. There is no Anthropic key on this
machine, so nothing in that column was run here.

The step ships one runnable thing, `demo.py`, which prints the table of
one capability from this file. Everything else is text and a test that
checks the text.

**The idea.** A coding agent is one loop with mechanisms around it. Steps
1 to 45 built each mechanism as Python in one process on the user's
machine. Steps 46 to 50 showed the same mechanisms on a harness that runs
as a server, reached over HTTP and Server-Sent Events. Managed Agents is
the same idea run by a vendor. Putting the three side by side shows which
mechanisms survive the move to a server unchanged, which change shape,
and which do not cross at all.

## Quick demo

The demo of this step is the live server's own description of itself. The
command prints the capabilities of the TrueForge server at
`http://localhost:8790` and the one model it has. No key is printed: the
`/models` endpoint carries names and limits only.

```bash
curl -s http://localhost:8790/api/v1/capabilities | python -m json.tool
curl -s http://localhost:8790/api/v1/models | python -m json.tool
```

Recorded output:

```text
{
    "data": {
        "sandbox": {
            "enabled": true
        },
        "skill": {
            "enabled": true
        },
        "settings": {
            "enabled": true
        }
    }
}
{
    "data": [
        {
            "name": "openai/gpt-4-1-mini",
            "model_id": "gpt-4.1-mini",
            "provider": {
                "name": "openai"
            },
            "properties": {
                "context_length": 1047576,
                "max_output_tokens": 32768
            }
        }
    ]
}
```

The server is TrueForge 0.1.4 in standalone mode. `sandbox`, `skill` and
`settings` are the three switches the server exposes; all three are on.
The model was registered by step 46's `setup_server.py`.

## How to read the tables

- **This codelab** names the stage or step that built the mechanism and
  the file that holds it. Stages 1 to 15 are the hand-built harness; steps
  21 to 45 extend it. Where a step from 46 to 50 ran the mechanism on
  TrueForge, the TrueForge cell names that step.
- **TrueForge** names the agent-spec field, the event or the endpoint.
  Field names are the HTTP wire names (`snake_case`). The server on this
  machine is version 0.1.4; the docs describe 0.2.0-rc.10 and one
  difference is noted where it matters.
- **Claude Managed Agents** names the concept as the docs call it. Every
  cell in that column ends with the marker `(docs)`, which means: from the
  docs, not run here.
- **Sources** lists the pages checked for the row, in the order TrueForge
  (TF), then Managed Agents (CMA). A TF link goes to `trueforge.dev` or to
  the repository at `github.com/truefoundry/trueforge`. A CMA link goes to
  `platform.claude.com/docs/en/managed-agents/`.
- All pages were fetched on 2026-09-14. A quoted setting is written as the
  harness writes it. Where the docs say nothing, the cell says "not in the
  docs" rather than guessing.

## Loop

The loop calls the model, runs the tool calls it returns and calls again.
In this codelab it is one function. In both servers it is code the client
never sees.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| The loop | `agent.turn` in `harness/agent.py` (stage 2.4). One function; a turn ends when a reply has no tool calls. | The loop runs in the server (`packages/trueforge-core`, TypeScript, MIT). A client opens a session with `POST /api/v1/sessions` and a turn with `POST /api/v1/sessions/{id}/turns`. The stream opens with `turn.created` and closes with `turn.done` (step 46). | The loop runs on Anthropic's orchestration layer. `POST /v1/agents` once, then `POST /v1/sessions` per run. A session moves between `running` and `idle`; `idle` carries a `stop_reason`. (docs) | [TF](https://trueforge.dev/api/overview) · [TF repo](https://github.com/truefoundry/trueforge) · [CMA](https://platform.claude.com/docs/en/managed-agents/overview) |
| Where the model and key live | `llm.call_llm` reads `API_KEY`, `BASE_URL` and `MODEL` from the environment (stage 1). The key is in the process that runs the tools. | `PUT /api/v1/settings/model-providers` stores the provider and key in the server. The agent spec names `model.name` as `provider/model`, here `openai/gpt-4-1-mini`, and never carries a key (step 46, `setup_server.py`). | `model` on the agent object, a Claude model id such as `claude-opus-5`, with optional `effort`, `speed` and `inference_geo`. The API key is the request's `x-api-key` header. (docs) | [TF](https://trueforge.dev/models) · [CMA](https://platform.claude.com/docs/en/managed-agents/agent-setup) |
| Agent definition | The system prompt is built per call by `llm.build_system_prompt`; agent definitions arrive in step 36 as `.agents/agents/*.md`. | An `AgentSpec`: `model`, `instructions`, `mcp_servers`, `skills`, `config`. Saved with `POST /api/v1/agents` under a unique name, or passed inline when the session is created. Server 0.1.4 takes the inline form as `agent: {spec: ...}` (step 46). | A persisted, versioned agent: `name`, `model`, `system`, `tools`, `mcp_servers`, `skills`, `multiagent`. Every update makes a new version; a session pins one. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/agent-setup) |
| Headless, one shot | `harness -p PROMPT` runs one turn, prints the final text, exits 0 (step 21). | `POST .../turns` with `stream: false` returns at once with `state.status: running`; poll `GET .../turns/{turn_id}` until `done`. Step 46's `demo.py -p` does the streamed form and prints `state.output`. | `initial_events` on `POST /v1/sessions` starts the loop in the create call; the session is created directly in `running`. Read the result from `GET /v1/sessions/{id}/events`. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/sessions) |
| Runaway calls | `stop.MAX_TURN_CALLS` (40 model calls per turn) and `MAX_TURN_SECONDS` in `harness/stop.py` (step 41); `durability.LoopDetector` stops a call repeated three times (step 34). | `config.iteration_limit`, default 100, range 1 to 1024 (step 49). Turns that run too long end with `turn.done` `state.status: cancelled`, reason `server-execution-timeout`. | No iteration cap in the docs. A session `budget` (`max_list_cost` in cents) pauses the session with `stop_reason: budget_reached`; the in-flight request finishes first. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/budgets) |
| Steering mid-turn | Ctrl-C during a turn reads one line and appends it after the pending tool results (step 35). | `POST /api/v1/sessions/{id}/cancel` stops the running turn; creating a new turn in the session also cancels it. The next `user.message` chains on the cancelled turn's history. | A `user.interrupt` event stops the agent; a `user.message` sent with it redirects. A `system.message` event appends system context for this turn and every later one. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |

## Tools

A tool is a function with a JSON schema. This codelab keeps the functions
in one dictionary. Both servers keep them behind a protocol boundary.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Built-in set | `bash` (stage 2.1), `read_file` (stage 2.3), `write_file` and `str_replace` (stage 5), plus `task`, `browse`, `remember`, `ask_user` and others from later steps, all in `tools.TOOLS`. | No file tools. Built in are the sandbox tool, `ask_user_question`, `create_sub_agent` and four meta tools: `list_tools`, `get_tool_info`, `get_tool_output_schema`, `call_tool`. Step 47 serves the codelab's five coding tools as the MCP server `s47-tools`. | `agent_toolset_20260401`: `bash`, `read`, `write`, `edit`, `glob`, `grep`, `web_fetch`, `web_search`. Each can be switched with `enabled`. (docs) | [TF](https://trueforge.dev/key-features/deferred-tool-loading) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |
| Custom tools | A Python function plus a schema dict in `harness/tools.py` (stage 2.2); step 43's `ctx.tool(fn, schema)` registers one from an extension. | A remote MCP server. `PUT /api/v1/settings/mcp-servers` with `{"manifest": {"type": "remote", "name", "url"}}`; the agent attaches it by `name` in `mcp_servers` (step 47, `register.py`). No stdio servers. | A `custom` tool with `name`, `description`, `input_schema` on the agent. The agent emits `agent.custom_tool_use`, the session goes `idle`, the client runs the tool and sends `user.custom_tool_result`. (docs) | [TF](https://trueforge.dev/mcp-servers) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |
| MCP | `harness/mcp_client.py` reads `.agents/mcp.json`, starts stdio servers and registers each tool as `mcp__<server>__<tool>` (step 26). | Remote servers only, streamable HTTP or SSE; no auth, header auth, or OAuth with dynamic client registration. `mcp.initialize` reports the connection; `mcp.auth_required` ends the turn with an `auth_url`. | `mcp_servers: [{"type": "url", "name", "url"}]` on the agent plus `{"type": "mcp_toolset", "mcp_server_name"}` in `tools`. Credentials live in vaults attached with `vault_ids` on the session. (docs) | [TF](https://trueforge.dev/mcp-servers) · [CMA](https://platform.claude.com/docs/en/managed-agents/mcp-connector) |
| Tool annotations | None; `permissions.check` rates a bash command by its first word (stage 11). | `readOnlyHint` and `destructiveHint` from the MCP server drive the `@read-only`, `@write` and `@destructive` selectors (step 47, `tools_server.py`). `GET /api/v1/mcp-servers/{name}/tools` lists tools with their annotations. | Not in the docs. Policies are set per tool name, not per annotation. (docs) | [TF](https://trueforge.dev/api-reference/mcp-servers/list-tools-of-an-mcp-server) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Deferred schemas | A schema over `DEFER_OVER` (300 tokens) is listed by name only; `load_tool` fetches it (step 32). | `preload: false` is the default per server: only the server's name and description are in context and the meta tools fetch schemas on demand. `preload_tools` loads a few eagerly (step 47). | Not in the docs for Managed Agents. (docs) | [TF](https://trueforge.dev/key-features/deferred-tool-loading) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |
| Many calls in one step | Parallel tool calls from one reply run together (step 22); `bash_background` and `job_wait` for long commands (step 29). | `model.params.parallel_tool_calls`; Code Mode lets the model write one script that calls `mcp_client.call_tool` many times in the sandbox and prints a summary (step 48). | Not stated in the docs. (docs) | [TF](https://trueforge.dev/key-features/code-mode) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |
| Large results | `history.cap` truncates a result, `history.strip` drops old ones (stage 14); a long result is spilled to a file and a preview stays in context (step 32). | `config.context_management.large_tool_response.enabled`, default on: a response over 6,000 tokens, or a parallel batch over 10,000, is written to a sandbox file and replaced by the first and last 100 characters plus the path (step 49). | Output over 100,000 characters is written to a file in the sandbox; the agent gets a preview and the path, and can `read` the rest. (docs) | [TF](https://trueforge.dev/key-features/large-tool-responses) · [CMA](https://platform.claude.com/docs/en/managed-agents/mcp-connector) |

## Permissions

A permission is a decision before a tool runs: allow, ask or deny. This
codelab decides in `permissions.check` and asks in the terminal. Both
servers decide and then end the turn so the client can answer.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Rule model | `permissions.check` (stage 11) rates a bash command by its first word with `BASH_RULES`; edits outside the project ask. | Per MCP server, `require_approval_for_tools`, default `["@write", "@destructive"]`, resolved from the server's tool annotations. `enable_tools` and `disable_tools` narrow the set (step 47). | `permission_policy` per toolset or per tool: `always_allow`, `always_ask` or `auto`. The agent toolset defaults to `always_allow`; MCP toolsets default to `always_ask`. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| The ask | `ui.approve` prints the command and reads `y`, `n`, `a` or `never` (stage 11, step 35). | The turn ends with a `tool.approval_required` event whose `tool_calls` point at the `model.message` that made the call; `turn.done` lists it in `state.required_actions`. The client resumes with a new turn whose input is `user.tool_approval` with `{"status": "allow"}` or `{"status": "deny", "reason"}` (step 47, `client/approve.py`). | The session goes `idle` with `stop_reason.type: requires_action` and the blocking event ids in `stop_reason.event_ids`. The client sends `user.tool_confirmation` with `tool_use_id`, `result: allow` or `deny`, and an optional `deny_message`. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Modes | `harness/modes.py` (step 39): `default`, `accept-edits`, `read-only`, `auto`, `plan`; a mode rewrites the verdict of the rules. | No named modes. `auto` is `require_approval_for_tools: []`; `read-only` is `enable_tools: ["@read-only"]`; the rest is a list of tool names (step 47). | `auto` is a policy the server evaluates per call: it runs the call, denies it as high-risk, or asks. Every `agent.tool_use` carries `evaluated_permission` (`allow`, `ask`, `deny`) and an `evaluation` object. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Remembered answers | `a` and `never` fill `SESSION_RULES` for the session (step 35). | None in the API; each gated call needs one `user.tool_approval`. The roadmap lists "approve once" for several calls. | None in the docs; each `ask` needs one `user.tool_confirmation`. A denial under `auto` cannot be overridden. (docs) | [TF](https://trueforge.dev/roadmap) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Who enforces | The harness, before `tools.run`; the model never sees the rules. | The server, before the MCP call; a Code Mode script that calls a gated tool pauses the same way. | Anthropic's orchestration layer, for the agent toolset and MCP tools. Custom tools are outside the policy because the client runs them. (docs) | [TF](https://trueforge.dev/key-features/code-mode) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |

## Sandbox

A sandbox is an operating-system boundary around a command. This codelab
wraps each command. TrueForge and Managed Agents give the agent a machine.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Mechanism | `sandbox.wrap` (stage 12): a `sandbox-exec` profile on macOS, `bwrap` on Linux, nothing on Windows. The agent loop and the command share one process. | "Sandbox as a tool": the loop stays on the server and the sandbox runs code, files and shell. `config.sandbox.enabled`, off by default. Daytona is the only provider in the docs; the standalone server on this machine uses a local sandbox in WSL (step 48). | A container per session, provisioned from an `environment` with `config.type` `cloud` or `self_hosted`. The loop runs outside it and acts on it through the agent toolset. (docs) | [TF](https://trueforge.dev/sandbox) · [CMA](https://platform.claude.com/docs/en/managed-agents/environments) |
| Filesystem | Writes are limited to the project directory; the agent works on the user's files in place. | The sandbox's own filesystem, not the client's. Files persist across turns of a session. `GET .../turns/{turn_id}/download-sandbox-file` copies one out (step 48, `client/sandbox.py`). | `/workspace` in the container. `resources` on the session mount uploaded files, GitHub repositories and memory stores; outputs come back through the Files API. (docs) | [TF](https://trueforge.dev/api-reference/agent-sessions/download-a-file-from-the-turn-sandbox) · [CMA](https://platform.claude.com/docs/en/managed-agents/environments) |
| Network | Not restricted. | Not in the docs; the provider decides. | `networking` on the environment. `web_search` and `web_fetch` run on Anthropic's servers and take `allowed_domains` or `blocked_domains`. (docs) | [TF](https://trueforge.dev/sandbox) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |
| Credentials | The API key is in the environment of the process that runs the commands. | Model and MCP credentials stay in the server; a Code Mode script's tool calls are bridged back to the server, so the sandbox never holds a token. | Vault `environment_variable` credentials are substituted at egress; the container sees a placeholder. (docs) | [TF](https://trueforge.dev/sandbox) · [CMA](https://platform.claude.com/docs/en/managed-agents/mcp-connector) |
| Lifecycle | One process per command, `timeout=60`. | `sandbox.created` is emitted once per session with a `sandbox_id`; later turns reuse it. `exec_timeout_ms` and `auto_stop_interval_in_minutes` are set on the provider. | Provisioned when the session first needs it; kept while the session is idle. Session running time is priced at $0.08 per hour. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/budgets) |

## Skills

A skill is a directory with a `SKILL.md`. All three read the same file
format; they differ on where the file comes from.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Format | `.agents/skills/<name>/SKILL.md` with `name` and `description` front matter and a markdown body (stage 4). | The same `SKILL.md`, with `references/` and `scripts/` next to it. | The same `SKILL.md`. Pre-built skills `xlsx`, `docx`, `pptx` and `pdf` are referenced by name. (docs) | [TF](https://trueforge.dev/skills) · [CMA](https://platform.claude.com/docs/en/managed-agents/skills) |
| Where it comes from | Read from disk at startup by `skills.py`. | A GitHub or GitLab HTTPS URL with `ref` and optional `path`, registered with `PUT /api/v1/settings/skills` (`type: git`). The repository is cloned into the sandbox under `/opt/tfy/skills/{name}`. Step 48 registers `step_04_skills/.agents/skills/explain-code` from this codelab's public repository as `s48-explain-code`; a skill must be pushed before the server can load it. On this machine the sandbox's proxy blocked the clone, so the skill index reached the prompt but the body did not. | Uploaded with the Skills API (`POST /v1/skills`) and referenced by `skill_id` and `version`, or discovered in a mounted repository's root `.claude/skills/` directory at session start. (docs) | [TF](https://trueforge.dev/skills) · [CMA](https://platform.claude.com/docs/en/managed-agents/skills) |
| Loading | Name and description ride in the system prompt; `read_skill` reads the body on demand. | Name and description in context; the body is read from the sandbox when the model picks the skill. `config.sandbox.enabled` must be `true`. | Name, description and sandbox path are announced; the agent reads `SKILL.md` with `read`, so the `read` tool must stay enabled. (docs) | [TF](https://trueforge.dev/key-features/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/skills) |
| Limits | None. | 50 skills per agent; names of letters, digits, `.`, `_`, `-`, up to 64 characters; two skills on one agent cannot share a name. | 20 skills per agent. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/skills) |

## Context

Context is everything the model sees in one request. This codelab manages
it in the client. Both servers manage it on the server and report on it.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| System prompt | `llm.build_system_prompt` (stage 1) assembles the base text, the skills list (stage 4), the instruction files (step 31) and the deferred tool names (step 32). | `instructions`, plus harness guidance the server appends for each enabled capability. `messages` seeds every new session with user messages. | `system` on the agent, up to 100,000 characters. A `system.message` event appends to it mid-session. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/agent-setup) |
| Instruction files | `instructions.py` (step 31): `AGENTS.md` or `CLAUDE.md` from the home directory, then the git root down to the working directory. | None; the docs say to move long procedures into skills. | None in the docs beyond repository skills. (docs) | [TF](https://trueforge.dev/key-features/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/skills) |
| Late injection | `context.reminder` (stage 6) appends a block to each user turn: changed files, todos, memory index, jobs. | Not exposed. | A `system.message` event, accepted while the session runs or idles. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Compaction | `history.fit` strips old tool output, then `compact.compact` (stage 14) asks the model for a summary and keeps a recent tail; `/compact` runs it by hand. | `config.context_management.compaction`, on by default at 80% of the model's context length, or 50,000 input tokens when that length is unknown; `trigger: {"type": "input_tokens", "value": N}` sets it (step 49). The full event history stays in the session store. | Built in; the stream reports it with `agent.thread_context_compacted`. No setting in the docs. (docs) | [TF](https://trueforge.dev/key-features/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/reference) |
| Budget view | `budget.breakdown` and `/context` (step 32) show the window by category and warn at 50% and 75%. | Every `model.message` carries `usage.input_tokens_breakdown` with `harness`, `skills`, `instructions`, `tool_definitions` and `messages`; step 49 draws it as a table. | `span.model_request_end` carries `model_usage` per call; `session.usage` snapshots the totals and `list_cost`. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Questions to the user | `ask_user` tool with `question` and `options` (step 35). | `config.ask_user_questions.enabled`, on by default. The turn ends with `tool.response_required`; the pending call's arguments carry `question` and `options`; resume with `user.tool_response` (step 49). | Not a built-in tool. A `custom` tool gives the same pause: `agent.custom_tool_use`, then `user.custom_tool_result`. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |

## Sessions

A session is the transcript plus whatever lets the user come back to it.
This codelab writes a file. Both servers own a database.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Storage | One JSONL file per session under `~/.simple-harness/sessions/<project>/` (stage 8). | SQLite in local mode, Postgres in hosted mode. `GET /api/v1/sessions`, `.../turns`, `.../events` read it back (step 50, `client/sessions.py`). | Server-side, per session. `GET /v1/sessions/{id}/events` lists everything; delete removes the events, container and checkpoints. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/session-operations) |
| Resume | `harness --resume` opens the last session; `/sessions` picks one (stage 8). | Pass the session id back; `previous_turn_id` defaults to `auto`, so the new turn chains on the last one (step 46). | Send another event to an `idle` session; history and sandbox are kept. (docs) | [TF](https://trueforge.dev/api/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/sessions) |
| Reconnect to a running turn | A session that ends in an unanswered tool call gets a synthetic result on restart (step 34). | `GET .../turns/{turn_id}/subscribe` with `after_sequence_number`; the SDK sends `Last-Event-ID` on a drop (step 50). | Reopen `GET .../events/stream`, then `GET .../events` and dedupe by id; there is no replay on the stream. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Replay | `harness replay <id>` draws a saved session again from the stamped log (step 44). | `GET .../turns/{turn_id}/events` returns a finished turn's events with the deltas already merged (step 50, `replay`). | `events.list` with a `types` filter; the Console session viewer shows the transcript and per-tool statistics. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Rewind and checkpoints | `/rewind` truncates the transcript (stage 8); `checkpoint.py` copies a file before an edit and `/undo` puts a turn back (step 33). | None. | None in the docs. Agent versions pin configuration, not conversation. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/agent-setup) |
| Cancel and end | Ctrl-C; `/exit`. | `POST .../cancel`; `turn.done` reports `cancelled` with a reason: `client-cancelled`, `server-execution-timeout`, `cancelled-for-next-turn` or `abandoned`. `DELETE /api/v1/sessions/{id}` removes a session. | `user.interrupt`; archive makes a session read-only and is permanent; delete removes it. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/session-operations) |

## Subagents

A subagent is a second loop with a fresh transcript. Only its final report
enters the parent's context.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Definition | `subagent.task` (stage 15); since step 36, `.agents/agents/*.md` with `name`, `description`, `tools`, `max_turns`, each a tool `agent_<name>`. | `config.dynamic_sub_agents.enabled`, on by default. The root agent calls `create_sub_agent` with instructions it writes itself; there are no definition files (step 50, `client/threads.py`). | `multiagent: {"type": "coordinator", "agents": [...]}` on the agent: a roster of saved agents by id, `{"type": "self"}`, or one `{"type": "advisor"}`. The coordinator gets `list_agents` and `send_to_agent`. (docs) | [TF](https://trueforge.dev/key-features/subagents) · [CMA](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration) |
| Isolation | A fresh message list; `WITHHELD` removes `task`, edits, jobs and `ask_user`; `MAX_TURNS` is 12. | A fresh context with the same MCP tools and sandbox; it cannot ask the user; it cannot spawn subagents. | Its own thread with its own history, model, system prompt and tools; all threads share the container. One level of delegation. (docs) | [TF](https://trueforge.dev/key-features/subagents) · [CMA](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration) |
| Parallelism | `descriptions` runs up to `MAX_PARALLEL` (4) at once (step 29). | Subagents run concurrently; the root waits for all of them. | Up to 25 concurrent threads; one roster agent may be spawned many times. (docs) | [TF](https://trueforge.dev/key-features/subagents) · [CMA](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration) |
| Reading the stream | The job list of step 29 shows each child's state. | `thread.created` and `thread.done` bracket a subagent; every event carries `thread_id` (`main` for the root, `null` for turn-level events). Step 50 indents by thread. | `session.thread_created` and `session.thread_status_*` on the session stream; `GET .../threads/{tid}/stream` follows one thread. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/multiagent-orchestration) |
| Handoffs | `handoff.py` moves the conversation to another agent definition; the transcript stays (step 40). | None. | None as such. `agent_with_overrides` on session create swaps model, prompt or tools for one session. (docs) | [TF](https://trueforge.dev/key-features/subagents) · [CMA](https://platform.claude.com/docs/en/managed-agents/sessions) |

## Hooks

A hook is user code that runs at a named point in the loop. Neither
server exposes one; the table shows what stands in.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Form | `hooks.py` (step 27): a `command` that reads a JSON event on stdin, or a `python` entry `module:function`, from `.agents/hooks.json`. | None in the API. The loop is in `packages/trueforge-core`, so a hook means a fork. | None in the docs. Webhooks post session state changes to an HTTPS endpoint, HMAC-signed; they notify, they do not intercept. (docs) | [TF repo](https://github.com/truefoundry/trueforge) · [CMA](https://platform.claude.com/docs/en/managed-agents/webhooks) |
| Blocking a tool call | Exit code 2 with stderr as the reason, or JSON `{"block": "reason"}`. | Only through approval: `require_approval_for_tools` and a `user.tool_approval` with `deny`. | Only through policy: `always_ask` with a `deny`, or the `auto` policy's own denial. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Extending the harness | `extensions.py` (step 43): `.agents/extensions/*.py` with `apply(ctx)` registering tools, commands, hooks, prompt sections and agents. | Catalog YAML files (`MODEL_CATALOG_PATH`, `MCP_CATALOG_PATH`, `SKILL_CATALOG_PATH`, `SANDBOX_CATALOG_PATH`) change what the UI offers; anything else is a source change. | Custom tools and MCP servers; the harness itself is closed. (docs) | [TF](https://trueforge.dev/harness/initial-setup) · [CMA](https://platform.claude.com/docs/en/managed-agents/tools) |

## Memory

Memory is what the agent keeps between sessions on its own.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Store | `memory.py` (step 25): one markdown file per fact under `~/.simple-harness/memory/<project>/` and `_user/`. | None. Sessions persist; agents do not remember across sessions. | Memory stores: small text files under `/mnt/memory/<store-name>/`, mounted with `resources` at session create; every change makes a memory version. (docs) | [TF](https://trueforge.dev/roadmap) · [CMA](https://platform.claude.com/docs/en/managed-agents/memory) |
| Who writes | The model, through `remember`, `recall` and `forget`. | Nobody. | The agent with the ordinary file tools; the host through the memories API. "Dreaming" is a research preview. (docs) | [TF](https://trueforge.dev/roadmap) · [CMA](https://platform.claude.com/docs/en/managed-agents/dreams) |

## Evals

An eval runs the agent on a fixed task and scores the result.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Harness | `evaluate.py` (step 30): `evals/<task>/task.md` plus `check.py`, `expect.txt` or `judge.md`; the capstone of step 38 grades one workspace. | None in the product. Step 50's `client/evaluate.py` runs the step 30 format through sessions with approvals off. The repository's `benchmark/` runs Enterprise-Bench tasks against Managed Agents and deepagents. | `user.define_outcome` with a rubric starts a graded iterate loop; `span.outcome_evaluation_end` reports `satisfied`, `needs_revision`, `max_iterations_reached` or `failed`. (docs) | [TF](https://trueforge.dev/benchmarking) · [CMA](https://platform.claude.com/docs/en/managed-agents/define-outcomes) |
| Report | `eval_report.json` with pass rate, tokens and cost per task. | `turn.done` `state.metrics`: `total_input_tokens`, `total_output_tokens`, `total_tokens`, cache counters, `total_cost_in_usd`. Sessions carry `metrics` too. | `session.usage` events and the session's `usage` object: token totals, `list_cost` in cents, `active_seconds`. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/budgets) |
| Isolation | A fresh temp copy of the workspace, a fresh session, every prompt auto-approved. | A fresh session per task; the workspace is wherever the MCP tools server points (step 50 gives each task a temp directory). | A fresh container per session. (docs) | [TF](https://trueforge.dev/api/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/environments) |

## Streaming

Streaming is how text reaches the screen before the turn ends.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Transport | `llm.call_llm(stream=True)` with an `on_delta` callback (step 21); the spinner stops at the first delta. | Server-Sent Events from `POST .../turns` with `stream: true`. A `model.message` shell arrives first, then `model.message.delta` events that share its `id`; each event has a sequence number (step 46). | `GET /v1/sessions/{id}/events/stream`. Text arrives as a buffered `agent.message` after the model call; `event_deltas[]=agent.message` on the stream URL opts into `event_start` and `event_delta` previews. (docs) | [TF](https://trueforge.dev/api/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Tool output | `streaming.py` shows a running command line by line in a panel (step 42). | `tool.response` arrives whole when the tool returns. | `agent.tool_result` arrives whole. (docs) | [TF](https://trueforge.dev/api/use-agent) · [CMA](https://platform.claude.com/docs/en/managed-agents/reference) |
| Client SDKs | None; the harness is the program. Step 45 ports the loop to TypeScript. | `@truefoundry/trueforge-sdk` (TypeScript) and `trueforge_sdk` (Python): `TrueForge(base_url="http://localhost:8790", timeout=600)`, then `client.sessions.create_turn_stream(...)`. | The `anthropic` SDKs in seven languages under `client.beta.sessions.*`, and the `ant` CLI (`ant beta:sessions connect`). (docs) | [TF](https://trueforge.dev/api/quickstart) · [CMA](https://platform.claude.com/docs/en/managed-agents/quickstart) |

## UI

The UI is what the user looks at. This codelab draws in the terminal.

| Aspect | This codelab (step, mechanism) | TrueForge (field, event, endpoint) | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| Surface | `ui.py` prints panels, the spinner and the input line (stage 3, step 13). | A bundled chat UI at `http://localhost:8790`; `@truefoundry/trueforge-ui` embeds it in a React app. | The Console session viewer: transcript, per-tool statistics, cost, threads. `ant beta:sessions connect` follows a session in the terminal. (docs) | [TF](https://trueforge.dev/chat-ui) · [CMA](https://platform.claude.com/docs/en/managed-agents/events-and-streaming) |
| Approval and question widgets | Terminal prompts: `ui.approve` and the `ask_user` menu (stage 11, step 35). | An Allow / Deny card for `tool.approval_required`, a choice card for `tool.response_required`, a Connect button for `mcp.auth_required`. | Allow and deny from the Console or the CLI. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/permission-policies) |
| Generative UI | None. | `config.generative_ui.enabled`, on by default: the model emits OpenUI blocks that the UI renders as charts, tables and forms. | Not in the docs. (docs) | [TF](https://trueforge.dev/create-agent/overview) · [CMA](https://platform.claude.com/docs/en/managed-agents/overview) |

## What changes when the harness is a server

Steps 1 to 45 put the loop, the tools and the transcript in one process
on the user's machine. TrueForge and Managed Agents put all three behind
an HTTP API. The tables above show the same mechanisms on both sides; this
section names what the move gives and what it takes.

### What you gain

- **Many clients, one loop.** The chat UI, the Python client of steps 46
  to 50 and the TypeScript SDK all drive the same server. This codelab's
  loop has exactly one client: its own terminal.
- **One session store.** Every turn and every event of every session is
  in one database, readable with `GET /api/v1/sessions/{id}/events` from
  any machine. Step 44's replay reads a file on one disk.
- **Credentials never leave the server.** The model key sits in the
  server's settings; the agent spec names a model, not a key. An MCP
  server's token sits in the connector. A Code Mode script calls tools
  through the server, so the sandbox never sees a token. In this codelab
  the key is an environment variable of the process that runs `bash`.
- **Sandbox on demand.** A session that only talks pays for no sandbox.
  `sandbox.created` fires once, when a turn first needs one, and later
  turns reuse it. Stage 12 wraps every command and has no boundary at all
  on Windows.
- **Pauses are data.** An approval, a question and an OAuth prompt each
  end the turn with an event and a `required_actions` list. Any client can
  answer later, from anywhere. Stage 11's prompt blocks the process.
- **Reconnect for free.** A dropped stream resumes at a sequence number;
  a finished turn replays from the store. Step 34 had to invent a
  synthetic tool result to recover.

### What you lose

- **No direct file system.** The agent edits files in the sandbox, not in
  the user's checkout. Getting a file out is a download. Step 47's answer
  is an MCP server that serves the user's directory, which is a second
  process to run and a network hop per tool call.
- **Tools must be MCP.** A tool is a remote server with a URL. Stage 2.2's
  one Python function and one schema dict become a FastMCP server on a
  port. Stdio servers do not exist.
- **Hooks are not exposed.** Steps 27 and 43 ran user code before and
  after every tool call and shaped the prompt. The server offers approval
  and nothing else at that point. Changing the loop means changing the
  server.
- **No cross-language session file.** Step 45's TypeScript harness resumed
  a session the Python harness wrote, because both read one JSONL file.
  A TrueForge session lives in the server's database and is reachable
  only through its API.
- **A second machine to run.** The standalone server is a Node process
  with a database. On Windows it runs inside WSL; the local sandbox needs
  `bwrap`, `socat` and `rg`. Managed Agents removes the machine and adds
  a vendor.
- **Less to read.** Steps 1 to 45 are readable in an afternoon and every
  number in a table above has a file behind it. The TrueForge loop is
  readable but larger; the Managed Agents loop is not readable at all.

## Cost and hosting

### Hosting

| Aspect | This codelab | TrueForge | Claude Managed Agents (from the docs, not run here) | Sources |
|---|---|---|---|---|
| What runs | One Python process, `pip install -e .`, on Windows, macOS or Linux. | `npx @truefoundry/trueforge@latest` (local mode, SQLite) or Docker Compose, Helm or Railway (hosted mode, Postgres and Redis). Node 22.14 or later. Standalone 0.1.4 does not start on Windows; on this machine it runs in WSL Ubuntu with `networkingMode=mirrored`. | Nothing to host. Every request carries the `managed-agents-2026-04-01` beta header. A `self_hosted` environment moves tool execution to a worker on the user's machine. (docs) | [TF repo](https://github.com/truefoundry/trueforge) · [CMA](https://platform.claude.com/docs/en/managed-agents/self-hosted-sandboxes) |
| Sandbox provider | The operating system. | Daytona in the docs; a local sandbox in the standalone server, which needs Linux or macOS with `bwrap`, `socat` and `rg` on `PATH`. The roadmap lists local sandbox execution as planned. | An Anthropic cloud container, or a self-hosted worker. (docs) | [TF](https://trueforge.dev/roadmap) · [CMA](https://platform.claude.com/docs/en/managed-agents/environments) |
| What is billed | Model tokens, by the provider. | Model tokens, by the provider; the sandbox, by its provider. The server is MIT. | Model tokens at list price, web searches at $10 per 1,000, session running time at $0.08 per hour; the sum is the session's `list_cost`. (docs) | [TF repo](https://github.com/truefoundry/trueforge) · [CMA](https://platform.claude.com/docs/en/managed-agents/budgets) |
| Login | None; the key file. | None in local mode; OIDC in hosted mode with an ID token as a bearer token. | An API key. (docs) | [TF](https://trueforge.dev/api/quickstart) · [CMA](https://platform.claude.com/docs/en/managed-agents/quickstart) |

### Tokens per turn, recorded on this machine

Every step from 46 to 50 records one demo against the local server and
reads the numbers from `turn.done` `state.metrics`. Step 38 recorded the
codelab's capstone with the same model, `gpt-4.1-mini`, through the same
provider. The tasks differ, so the rows compare shape, not efficiency.

| Step | Demo | Turns | Input tokens | Cached | Output tokens | Cost at list price |
|---|---|---|---|---|---|---|
| 38 | capstone: a FastAPI todo API, graded 4/5 | 11 calls, 1 turn | 120,237 | 93,696 | 3,722 | $0.0259 |
| 46 | `-p` turn 1: remember a codename | 1 turn | 1,059 | 0 | 13 | $0.0004 |
| 46 | `-p --resume` turn 2: recall it | 1 turn | 1,089 | 0 | 10 | $0.0005 |
| 47 | add a docstring: two reads, one approved edit, summed | 2 turns | 6,648 | 0 | 115 | $0.0028 |
| 48 | write and run `hello.py` in the sandbox | 1 turn | 5,314 | 0 | 103 | $0.0023 |
| 49 | a question, then the answer: the second of two turns | 1 turn | 1,131 | 0 | 50 | $0.0005 |
| 50 | `--threads`: three subagents in parallel | 1 turn | 3,970 | 1,024 | 1,492 | $0.0037 |
| 50 | `--eval`: three tasks, 3/3 passed | 3 turns | 20,464 | 0 | 328 | $0.0087 |

- Input and output tokens are the numbers each README records: step 38
  from `report.json`, steps 46 to 50 from `turn.done` `state.metrics`
  (`total_input_tokens`, `total_output_tokens`) or, for step 50's suite,
  from its `eval_report.json` totals. The step 50 threads row shows
  `cache_read_tokens` in the cached column; the other TrueForge demos
  reported no cache figure.
- Cost is computed here, not reported: `gpt-4.1-mini` list prices of
  $0.40 per million input tokens, $0.10 per million cached input tokens
  and $1.60 per million output tokens, applied to the columns to the left.
  Step 38's README reports the same figure, $0.026, the same way.
- The cheapest TrueForge turn costs under a tenth of a cent and the
  dearest demo, the eval suite, under a cent. The capstone is a bigger
  task with more calls, so its 120,237 input tokens are not a harness
  overhead. The per-turn floor is visible in step 46: about 1,060 input
  tokens for a one-line prompt, which step 49's breakdown attributes
  mostly to `harness` (1,288 tokens of harness framing per call against
  67 of instructions).
- Managed Agents adds two charges no row above has: $0.08 per hour of
  session running time and $10 per 1,000 web searches. At the codelab's
  pace of about one minute per capstone run, the runtime charge would be
  about $0.0013 per run. That figure is arithmetic on the docs' price,
  not a measurement. (docs)

### The vendor's benchmark

TrueForge publishes one comparison against Managed Agents and deepagents:
14 enterprise tasks, three trials, the same MCP servers and system prompt.
On Claude Opus 4.8, TrueForge and Managed Agents solved the same number of
tasks per trial (10.7 of 14), at 3.7M tokens and $8.6 per run for
TrueForge against 10.0M tokens and $11.8 for Managed Agents. The numbers
are the vendor's, not reproduced here; the repository's `benchmark/`
directory holds the setup.
Source: [TF](https://trueforge.dev/benchmarking).

## Run it

```bash
cd step_51_trueforge_comparison
python demo.py
python demo.py permissions
```

You should see the capability names, then the permissions table printed
as blocks: the aspect, one line per harness, and the source URLs. Pick
any heading from the tables above in lower case.

To check the README itself:

```bash
python -m pytest -q test_step.py
```

You should see every test pass. The tests read this file and `demo.py`
and never touch the network.

## The code, piece by piece

`demo.py`:

```python
def section(name, text=None):
    """The lines between `## name` and the next `## ` heading."""
    lines = (text or README.read_text(encoding="utf-8")).splitlines()
    start = lines.index(f"## {name}") + 1
    body = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return body
```

The README is the data. `section` cuts out one heading's lines, the same
way step 37's test does, so the table printed by the demo is always the
table in this file.

`demo.py`:

```python
def table(name, text=None, index=0):
    """(header, rows) of one table in a section, each as a list of cells."""
    runs, run = [], []
    for line in section(name, text) + [""]:
        if line.startswith("|"):
            run.append(line)
        elif run:
            runs.append(run)
            run = []
    if len(runs) <= index or len(runs[index]) < 3:
        raise ValueError(f"no table {index} under {name}")
    header, _separator, *rows = runs[index]
    return cells(header), [cells(r) for r in rows]
```

A table is a run of lines that start with a pipe: a header, a separator,
then rows. A section may hold more than one run; `index` picks one. The
test uses the same function, so the demo and the test agree on what a row
is.

`demo.py`:

```python
def render(name, text=None):
    """The table of one capability as text, one block per row."""
    header, rows = table(name, text)
    out = [f"== {name} ==", ""]
    for row in rows:
        out.append(f"* {row[0]}")
        for label, cell in zip(header[1:-1], row[1:-1]):
            out.append(f"    {label}: {plain(cell)}")
        out.append(f"    sources: {', '.join(url for _, url in LINK.findall(row[-1]))}")
        out.append("")
    return "\n".join(out)
```

One block per row: the aspect, then each harness cell with its links
reduced to labels, then the bare URLs of the sources cell.

`demo.py`:

```python
def cells(row):
    """The stripped cells of one markdown table row."""
    return [c.strip() for c in row.strip().strip("|").split("|")]


def plain(cell):
    """A cell with its markdown links reduced to their labels."""
    return LINK.sub(r"\1", cell)
```

Two helpers. `cells` splits a row on its pipes; no cell in this file
contains a pipe. `plain` turns a markdown link into its label, so a
printed cell reads as prose.

`demo.py`:

```python
def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("capabilities: " + ", ".join(c.lower() for c in CAPABILITIES))
        return 0
    wanted = argv[0].lower()
    names = {c.lower(): c for c in CAPABILITIES}
    if wanted not in names:
        print(f"unknown capability {wanted!r}; pick one of: " + ", ".join(names))
        return 1
    print(render(names[wanted]))
    return 0
```

No argument lists the thirteen names. A name that is not a heading exits
with 1 and the list, so a typo is not a stack trace.

## What to notice

- Every mechanism has a cell in all three columns, but the cells are not
  the same size. The loop, permissions, sessions and subagents cross the
  server boundary with a new name and the same shape. Hooks, memory and
  rewind do not cross at all on TrueForge.
- The two servers agree on how a pause works: end the turn, list what is
  pending, resume with a typed event. They disagree on the names
  (`tool.approval_required` and `user.tool_approval` against
  `session.status_idle` and `user.tool_confirmation`) and on the default:
  TrueForge gates by annotation, Managed Agents by toolset.
- TrueForge reports the context by category on every model call. Neither
  this codelab's `/context` nor the Managed Agents usage events split the
  input that way. It is the one number a server can give that a client
  cannot compute.
- "Not in the docs" appears more in the Managed Agents column than in the
  TrueForge column, and "None" more in the TrueForge column. A closed
  harness leaves gaps in what can be known; an open one leaves gaps in
  what has been built.

## Diff from step 50

- This step is independent of step 50, as every step in this part is. No
  file is copied from another step.
- `README.md`: new. Thirteen capability tables, the server section, the
  cost and hosting section.
- `demo.py`: new. Prints one capability's table from the README.
- `test_step.py`: new. Checks the table shape, the marker on every
  Managed Agents cell, the hosts of every URL, the step numbers, and runs
  the demo.
