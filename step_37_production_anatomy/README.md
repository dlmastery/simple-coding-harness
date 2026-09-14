# Step 37 - Production harness anatomy

**What this step adds.** No new harness code. This step is a reading. It
places every mechanism built in steps 1 to 36 next to five production
harnesses: Claude Code, Codex CLI, OpenCode, pi and Hermes. For each
mechanism group there is one table. Each cell names the feature as that
harness calls it, says where it lives, and gives one line on how it differs
from this repo. Every row links to the public docs or source that support
it. Where a harness has no equivalent, the cell says so. Where a claim could
not be checked against a public page, the cell says "not verified".

The `harness/`, `.agents/`, `evals/`, `AGENTS.md` and `pyproject.toml` in
this directory are copied from step 36 without change, so that step 38 can
build on this step. Only the version number moved to `0.37.0`.

**The idea.** A coding agent is a small number of mechanisms arranged
around one loop. The loop calls a model, runs the tool calls it returns,
appends the results and calls again. Everything else guards, feeds or
records that loop. This repo built each mechanism in one step, so each one
has a name and a file here. Production harnesses have the same mechanisms
under other names, in other files, with other defaults. Reading them side
by side shows which choices are shared by everyone and which are open
design decisions. After this step, reading any of the five is reading
something already built here.

## Files

```text
step_37_production_anatomy/
├── harness/
│   ├── __init__.py       package marker
│   ├── agent.py          the loop; Ctrl-C steers the turn instead of killing it
│   ├── agents.py         agent definitions: subagents described in Markdown files
│   ├── ask_user.py       the ask_user tool: a question to the user, answer as result
│   ├── browse.py         the browse tool set over the step 23 browser subagent
│   ├── browser.py        browser tools: one Chromium page driven through Playwright
│   ├── budget.py         the context budget: where the window goes, when to warn
│   ├── checkpoint.py     workspace checkpoints: file copies taken before each edit
│   ├── commands.py       slash commands: /pipeline joins /undo, /rewind, /checkpoints
│   ├── compact.py        the compaction agent; its note is kept
│   ├── computer.py       computer use: the screen as a tool
│   ├── config.py         settings: real env vars win, ~/.simple-harness/env fills gaps
│   ├── context.py        the late injection block: <env>, <plan>, <jobs>
│   ├── durability.py     the loop detector and the crash-recovery scan
│   ├── evaluate.py       the evaluation harness; `isolated` auto-answers prompts
│   ├── history.py        keeps the transcript small enough to send, pictures too
│   ├── hooks.py          hook events with a built-in list; checkpoint capture is one
│   ├── instructions.py   project instruction files (AGENTS.md) for the prompt
│   ├── jobs.py           background jobs: commands that run while the chat goes on
│   ├── llm.py            the model call with retries; the prompt lists the agent definitions
│   ├── mcp_client.py     MCP client: tools served by other processes over stdio
│   ├── memory.py         persistent memory
│   ├── permissions.py    which calls need a human; session rules from `a` and `never`
│   ├── pipeline.py       the plan, work, review pipeline behind /pipeline
│   ├── plan.py           plan mode: the read-only tool set, ask_user included
│   ├── prompt.py         the input line
│   ├── sandbox.py        an OS sandbox for bash
│   ├── session.py        append-only JSONL session log, load() and --resume
│   ├── skills.py         skills, unchanged since stage 9
│   ├── subagent.py       the subagent loop; withheld() and the gather() thread pool
│   ├── todos.py          the plan behind write_todos
│   ├── tools.py          the tool registry; agents.register() adds agent_<name> at import
│   └── ui.py             rich panels; pipeline() draws the summary table
├── .agents/
│   ├── .gitignore                     ignores tool_log.txt, the PostToolUse hook's log
│   ├── hooks.json                     hook config: one PreToolUse and one PostToolUse hook
│   ├── block_env_writes.py            example PreToolUse hook: refuses to write a .env file
│   ├── log_tool_use.py                example PostToolUse hook: appends every tool name to a log
│   ├── mcp.json                       MCP config: one stdio server, echo
│   ├── mcp_echo_server.py             a tiny MCP server: two tools, stdio transport
│   ├── skills/explain-code/SKILL.md   the stage 4 skill
│   ├── agents/planner.md              definition: reads the code, returns a numbered plan
│   ├── agents/worker.md               definition: carries out one plan step with the edit tools
│   └── agents/reviewer.md             definition: checks one step, answers PASS or FAIL
├── evals/           three step 30 tasks: task.md, check.py or expect.txt, workspace/
├── AGENTS.md        project instructions the harness reads into its prompt
├── test_step.py     offline checks of this README: headings, tables, one link per row
├── pyproject.toml   package metadata; version 0.37.0
└── README.md        this file
```

## How to read the tables

- **This repo** names the stage or step that introduced the mechanism and
  the file that holds it. Stages 1 to 15 are the hand-built harness; steps
  21 to 36 extend it.
- **Sources** lists the pages checked for that row, one link per harness
  in the order Claude Code (CC), Codex CLI (CX), OpenCode (OC), pi, Hermes
  (HM). A row omits a harness from the sources when its cell is "none" or
  "not verified" and no page was needed.
- All pages were fetched on 2026-09-12 and 2026-09-13. Codex docs under
  `developers.openai.com/codex/` redirect to `learn.chatgpt.com/docs/`; the
  canonical address is cited. The pi repository moved from
  `badlogic/pi-mono` to `earendil-works/pi`; the new address is cited.
- A quoted setting or command is written as that harness writes it.

## Loop

The loop is the function that calls the model, runs tool calls and calls
again. This repo has it in one function, `agent.turn`.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| The loop | `agent.turn` in `harness/agent.py` (stage 2.4). One function; a turn ends when a reply has no tool calls or after 40 model calls (step 34). | "The agentic loop": gather context, take action, verify, repeat. Closed source; the loop is not readable. | The `codex-core` crate in `codex-rs/core` (Rust, open source). The same core serves the TUI, `codex exec` and `codex app-server`. | A client/server split: `opencode serve` runs the loop behind an OpenAPI server and the TUI is one client of it. | The `Agent` class in the `pi-agent-core` package: prompt, response, tools, repeat. Tool calls run in parallel by default. | `AIAgent` in `run_agent.py`, a synchronous engine; the loop body sits in `agent/conversation_loop.py`. The same engine serves the CLI and a gateway to chat platforms. | [CC](https://code.claude.com/docs/en/how-claude-code-works) · [CX](https://github.com/openai/codex/tree/main/codex-rs/core/src) · [OC](https://opencode.ai/docs/server/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/agent/README.md) · [HM](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) |
| Streaming | `llm.call_llm(stream=True)` with an `on_delta` callback (step 21). The spinner stops at the first delta. | `--output-format stream-json` with `--include-partial-messages` emits token deltas as NDJSON. | The app server sends JSON-RPC notifications such as `item/agentMessage/delta`; `codex exec --json` emits JSONL events. | Server-sent events at `GET /event`; `opencode run --format json` prints raw events. | `--mode json` prints every session event as a JSON line; `message_update` carries only the delta. | A `stream_delta_callback` in the engine; the gateway edits a chat message in place as text arrives. | [CC](https://code.claude.com/docs/en/headless) · [CX](https://developers.openai.com/codex/app-server) · [OC](https://opencode.ai/docs/server/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/json.md) · [HM](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) |
| Headless mode | `harness -p PROMPT` runs one turn, prints the final text, exits 0 (step 21). | `claude -p "<prompt>"`; `--bare` also skips hooks, CLAUDE.md and memory for reproducible runs. | `codex exec "<prompt>"` streams progress to stderr and the final message to stdout; `--output-schema` forces JSON. | `opencode run [message]`; `--attach` reuses a running server. | `pi -p` reads piped stdin into the prompt; `--mode rpc` is a JSONL protocol over stdin and stdout. | `hermes chat --oneshot -q "<prompt>"` answers and exits; `hermes -z` prints only the answer. | [CC](https://code.claude.com/docs/en/headless) · [CX](https://developers.openai.com/codex/non-interactive-mode) · [OC](https://opencode.ai/docs/cli/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/cli) |
| Steering mid-turn | Ctrl-C during a turn reads one line and appends it after the pending tool results (step 35). | Messages typed during a turn are queued; Esc interrupts. | `turn/steer` and `turn/interrupt` are app-server methods. | Not verified. | `steer()` interrupts the run; `followUp()` queues after it. RPC prompts choose one with `streamingBehavior`. | Not verified for the user. Child agents accept `steer` through `delegate_task`. | [CC](https://code.claude.com/docs/en/interactive-mode) · [CX](https://developers.openai.com/codex/app-server) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |
| Retries and runaway calls | `llm.py` retries with `BACKOFF` waits; `durability.LoopDetector` stops a call repeated three times (step 34). | Not verified. | Not verified. | Not verified. | A `retry` block in `settings.json`. | The engine owns "retries, fallback"; `agent.max_turns` bounds a run through an `IterationBudget`. | [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/settings.md) · [HM](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) |

## Tools

A tool is a function with a JSON schema. This repo keeps them in one
dictionary, `tools.TOOLS`, and sends the schemas with every request.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Built-in set | `bash` (stage 2.1), `read_file` (2.3), `write_file` and `str_replace` (5), plus `task`, `browse`, `remember`, `ask_user` and others from later steps. | Read, Write, Edit, Glob, Grep, Bash, WebFetch, WebSearch, Agent, Skill and more; Read, Glob and Grep need no permission. | `shell`, `unified_exec` (a PTY), `apply_patch`, `view_image`, `plan`, `request_user_input`. No separate read tool: reads go through the shell. | `bash`, `edit`, `write`, `read`, `grep`, `glob`, `apply_patch`, `webfetch`, `websearch`, `question`, `todowrite`, `skill`, `lsp`. | `read`, `bash` (`powershell` on Windows), `edit`, `write`, `grep`, `find`, `ls`; `--tools` allowlists them. | Seventy-plus tools in about 28 toolsets: `terminal`, `read_file`, `write_file`, `patch`, `search_files`, `execute_code`, browser, vision and messaging tools. | [CC](https://code.claude.com/docs/en/tools-reference) · [CX](https://github.com/openai/codex/tree/main/codex-rs/core/src/tools/handlers) · [OC](https://opencode.ai/docs/tools/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools) |
| Registry | `tools.TOOLS` and `tools.TOOL_SCHEMAS` in `harness/tools.py` (stage 2.2); a tool is a Python function plus a schema dict. | Not public. | `tools/registry.rs` and `tools/router.rs` in `codex-rs/core/src/tools`. | The `tools` config key enables or disables tools by name or glob, globally or per agent. | The SDK `tools` list and `customTools` on `createAgentSession()`. | `tools/registry.py`; each `tools/*.py` module registers itself at import. | [CX](https://github.com/openai/codex/tree/main/codex-rs/core/src/tools) · [OC](https://opencode.ai/docs/config/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sdk.md) · [HM](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture) |
| Custom tools | Add a function and a schema to `tools.py`; a skill in `.agents/skills/` describes a CLI tool instead (stage 4). | Only through MCP servers or plugin `bin/` executables; no file that defines a tool directly. | Only through MCP servers. | A TypeScript file in `.opencode/tools/*.ts` exporting `tool({ description, args, execute })`; the file name is the tool name. | `pi.registerTool()` in an extension, with TypeBox schemas. | A plugin's `register(ctx)` calls `ctx.register_tool(name, toolset, schema, handler)`. | [CC](https://code.claude.com/docs/en/plugins) · [CX](https://developers.openai.com/codex/extend/mcp) · [OC](https://opencode.ai/docs/custom-tools/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/plugins) |
| MCP | `harness/mcp_client.py` reads `.agents/mcp.json` and registers each tool as `mcp__<server>__<tool>` (step 26). | `claude mcp add`; scopes local, project (`.mcp.json`) and user; tools named `mcp__<server>__<tool>`. | `[mcp_servers.<name>]` in `config.toml`, stdio or streamable HTTP, OAuth, per-tool approval mode; `codex mcp add`. | The `mcp` config key with `local` or `remote` servers; tools named `<server>_<tool>`. | None, by design: "No MCP." An extension can add it. | `mcp_servers:` in `config.yaml`, stdio or HTTP, tools named `mcp_<server>_<tool>`; `hermes mcp serve` also exposes Hermes as a server. | [CC](https://code.claude.com/docs/en/mcp) · [CX](https://developers.openai.com/codex/extend/mcp) · [OC](https://opencode.ai/docs/mcp-servers/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp) |
| Deferred schemas | A schema over `DEFER_OVER` (300 tokens) is listed by name only; `load_tool` fetches it (step 32). | MCP tool definitions are deferred by default and loaded by the `ToolSearch` tool; `ENABLE_TOOL_SEARCH` changes the policy. | A `tool_search` handler exists in the core; its policy is not verified. | Not verified. | No deferral of tools; skills give progressive disclosure instead. | Not verified. | [CC](https://code.claude.com/docs/en/context-window) · [CX](https://github.com/openai/codex/tree/main/codex-rs/core/src/tools/handlers) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md) |

## Permissions

A permission is a decision made before a tool runs: allow, ask or deny.
This repo decides in `permissions.check` and asks in the terminal.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Rule model | `permissions.check` (stage 11) rates a bash command by its first word with `BASH_RULES`; edits outside the project ask. | `permissions.allow`, `ask` and `deny` lists in `settings.json`; evaluated deny, then ask, then allow; first match wins. | `approval_policy` (`on-request`, `never` or a granular table) plus Starlark `prefix_rule(...)` files with decisions `allow`, `prompt`, `forbidden`; the most restrictive rule wins. | The `permission` config key: `allow`, `ask` or `deny` per tool, with pattern objects for `bash` and `edit`; the last matching rule wins. | None in the core: "No permission popups." A `tool_call` extension handler can return `{ block: true }`. | `approvals.mode`: `smart` (an auxiliary model scores risk), `manual` or `off`; `approvals.deny` globs always block. | [CC](https://code.claude.com/docs/en/permissions) · [CX](https://developers.openai.com/codex/agent-configuration/rules) · [OC](https://opencode.ai/docs/permissions/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |
| Where rules live | In code: `harness/permissions.py`. | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed settings. | `~/.codex/config.toml`, `~/.codex/rules/default.rules`, `<repo>/.codex/rules/`; project files load only for trusted projects. | `opencode.json` globally and `agent.<name>.permission` per agent. | `~/.pi/agent/trust.json` holds project trust only. | `approvals:` in `~/.hermes/config.yaml`. | [CC](https://code.claude.com/docs/en/settings) · [CX](https://developers.openai.com/codex/agent-configuration/rules) · [OC](https://opencode.ai/docs/permissions/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Modes | Plan mode (`/plan`, step 28) offers only the `READ_ONLY` tools until a plan is approved. Named modes arrive in step 39. | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions`; `Shift+Tab` cycles them. | `--yolo` (`--dangerously-bypass-approvals-and-sandbox`) skips approvals; `/approvals` in the TUI. | `--auto` or the palette entry "Enable auto-approve permissions". | None. | `--yolo`, `/yolo` or `HERMES_YOLO_MODE=1`; a hardline blocklist still applies. | [CC](https://code.claude.com/docs/en/permission-modes) · [CX](https://developers.openai.com/codex/developer-commands) · [OC](https://opencode.ai/docs/cli/) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |
| Remembered answers | The approve prompt accepts `y`, `n`, `a` and `never`; `a` and `never` fill `SESSION_RULES` for this session (step 35). | Hook output `permissionDecision` can allow, deny or ask; `/permissions` edits the rule lists. | The TUI "always allow" writes a rule to `default.rules`; the app server accepts `acceptForSession`. | Prompt answers are `once`, `always` (this session) or `reject`. | None. | `command_allowlist` persists "always" approvals across sessions. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/agent-configuration/rules) · [OC](https://opencode.ai/docs/permissions/) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |
| Who enforces | The harness, before `tools.run`; the model never sees the rules. | The harness: "Permission rules are enforced by Claude Code, not by the model." | The harness; `codex execpolicy check` tests a rule file offline. | The harness, before the tool runs. | An extension, if one is installed; otherwise nobody. | The harness; checks are skipped inside container backends because the container is the boundary. | [CC](https://code.claude.com/docs/en/permissions) · [CX](https://developers.openai.com/codex/agent-configuration/rules) · [OC](https://opencode.ai/docs/permissions/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |

## Sandbox

A sandbox is an operating-system boundary around a command. It holds even
when the permission layer says yes.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Mechanism | `sandbox.wrap` (stage 12): a `sandbox-exec` profile on macOS, `bwrap` on Linux, nothing on Windows. | "Sandboxed Bash tool": Seatbelt on macOS, `bubblewrap` and `socat` on Linux and WSL2; native Windows is not supported. | `sandbox_mode`: `read-only`, `workspace-write`, `danger-full-access`; Seatbelt on macOS, Landlock, seccomp and `bwrap` on Linux, a native sandbox on Windows. | None built in. A third-party plugin wraps `bash` through the `tool.execute.before` hook. | None built in, by design; the docs say a partial sandbox would be mistaken for a security boundary. | "Terminal backends": `local`, `docker`, `ssh`, `modal`, `daytona`, `vercel_sandbox`, `singularity`, chosen by `terminal.backend`. | [CC](https://code.claude.com/docs/en/sandboxing) · [CX](https://developers.openai.com/codex/sandboxing) · [OC](https://github.com/isanchez31/opencode-sandbox-plugin) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/security.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |
| Filesystem | Writes are limited to the project directory. | `sandbox.filesystem.allowWrite`, `denyWrite`, `allowRead`, `denyRead`; writes default to the working directory and `--add-dir` paths. | `writable_roots` and `--add-dir` under `workspace-write`; `.git/` may stay read-only. | None. | None; the recommended Docker run mounts only the workspace. | Docker containers drop all capabilities, set `no-new-privileges` and a PID limit; `HERMES_WRITE_SAFE_ROOT` confines file tools. | [CC](https://code.claude.com/docs/en/sandboxing) · [CX](https://developers.openai.com/codex/sandboxing) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/containerization.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |
| Network | Not restricted. | A proxy outside the sandbox with `network.allowedDomains`; no domain is allowed until asked. | `sandbox_workspace_write.network_access` is off by default; `features.network_proxy` adds a domain list. | None. | None. | `docker_network` per container; SSH is a network boundary only. | [CC](https://code.claude.com/docs/en/sandboxing) · [CX](https://developers.openai.com/codex/config-file/config-reference) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Timeouts | `sandbox.run(command, timeout=60)`; the timeout is the same for all commands. | Not verified. | Not verified. | Not verified. | Not verified. | `terminal.timeout` (default 180 s). | [HM](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Escape hatch | None; a denied command is denied. | A retry with `dangerouslyDisableSandbox` goes through the normal permission flow. | `--dangerously-bypass-approvals-and-sandbox`. | Not applicable. | Not applicable. | `--yolo` skips prompts but not the blocklist. | [CC](https://code.claude.com/docs/en/sandboxing) · [CX](https://developers.openai.com/codex/developer-commands) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/security) |

## Context

Context is everything the model sees in one request: the system prompt,
instruction files, the transcript and the reminders added late.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| System prompt | `llm.build_system_prompt` (stage 1) assembles the base text, the skills list (stage 4), the instruction files (step 31) and the deferred tool names (step 32). | A fixed core prompt; `--append-system-prompt` and `--system-prompt` change it. CLAUDE.md content arrives as a user message after it. | Not verified beyond the AGENTS.md chain below. | `experimental.chat.system.transform` in a plugin can rewrite it. | `.pi/SYSTEM.md` replaces it; `APPEND_SYSTEM.md` appends; `--system-prompt` and `--append-system-prompt` on the CLI. | A stack: `SOUL.md` first, then tool guidance, memory, skills, context files, timestamp, platform hints and a `/personality` overlay. | [CC](https://code.claude.com/docs/en/memory) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/usage.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/personality) |
| Instruction files | `instructions.py` (step 31): `AGENTS.md` or `CLAUDE.md` from `~/.simple-harness`, then the git root down to the working directory; 20 000 characters at most. | Managed policy file, `~/.claude/CLAUDE.md`, every ancestor `CLAUDE.md`, `CLAUDE.local.md`; `@path` imports; `.claude/rules/*.md`; subdirectory files load when a file there is read. | `~/.codex/AGENTS.md`, then git root down to the working directory, one file per directory, `AGENTS.override.md` first; `project_doc_max_bytes` (32 KiB) caps the chain. | `AGENTS.md` found walking up, a global `~/.config/opencode/AGENTS.md`, `CLAUDE.md` as fallback; `instructions` config adds globs and URLs. | `AGENTS.md` or `CLAUDE.md`, never both, from `~/.pi/agent`, parent directories and the working directory; `--no-context-files` disables. | `.hermes.md`, `AGENTS.override.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`; first match wins per directory; content is scanned for prompt injection. | [CC](https://code.claude.com/docs/en/memory) · [CX](https://developers.openai.com/codex/agent-configuration/agents-md) · [OC](https://opencode.ai/docs/rules/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/usage.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) |
| Late injection | `context.reminder` (stage 6) appends a block to each user turn: changed files (stage 7), todos, memory index, jobs and hook context. | Hook output `additionalContext` and `UserPromptSubmit` hooks add text per turn. | `UserPromptSubmit` hooks may return `additionalContext`. | `experimental.chat.messages.transform` in a plugin edits the messages. | The `context` extension event fires before each model call and may modify the messages. | Context files are re-checked as the agent touches new directories. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files) |
| Compaction | `history.fit` caps and strips old tool output, then `compact.compact` (stage 14) asks the model for a `<summary>` and keeps a recent tail. `/compact` runs it by hand. | Auto-compact near the limit clears old tool output first, then summarises; `/compact [focus]`; CLAUDE.md, memory and recent files are re-injected afterwards. | `/compact` and `model_auto_compact_token_limit`; `PreCompact` and `PostCompact` hooks; a `get_context_remaining` tool. | `compaction: { auto, prune, reserved }`; `prune` drops old tool output; `/compact` in the TUI. | Auto-compaction when tokens exceed the window minus `reserveTokens` (16 384); keeps `keepRecentTokens` (20 000); the full history stays in the JSONL file. | `compression.threshold` (0.50), `target_ratio` (0.20), `protect_last_n` (20); `/compress`; a pluggable context engine. | [CC](https://code.claude.com/docs/en/context-window) · [CX](https://developers.openai.com/codex/config-file/config-reference) · [OC](https://opencode.ai/docs/config/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/compaction.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |
| Budget view | `budget.breakdown` and `/context` (step 32) show the window by category and warn at 50 % and 75 %. | `/context` shows usage; `/autocompact` sets the threshold. | The TUI shows "context left"; a `get_context_remaining` tool reports it to the model. | Not verified. | Not verified. | `/usage`, `/context` and `hermes prompt-size`. | [CC](https://code.claude.com/docs/en/context-window) · [CX](https://developers.openai.com/codex/config-file/config-reference) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/configuration) |

## Sessions

A session is the transcript on disk, plus whatever lets the user go back
to an earlier point.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Storage | One JSONL file per session under `~/.simple-harness/sessions/<project>/` (stage 8). | JSONL at `~/.claude/projects/<project>/<session-id>.jsonl`; `cleanupPeriodDays` retention. | "Rollout" JSONL files under `~/.codex/sessions`, named `rollout-<timestamp>-<thread-id>.jsonl`. | `~/.local/share/opencode/project/<slug>/storage/`. | A JSONL tree at `~/.pi/agent/sessions/--<path>--/<timestamp>_<id>.jsonl`; entries carry `id` and `parentId`. | SQLite at `~/.hermes/state.db` with FTS5 tables for search. | [CC](https://code.claude.com/docs/en/sessions) · [CX](https://github.com/openai/codex/blob/main/codex-rs/rollout/src/rollout_file_name.rs) · [OC](https://opencode.ai/docs/troubleshooting/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md) · [HM](https://github.com/NousResearch/hermes-agent/blob/main/hermes_state.py) |
| Resume | `harness --resume` opens the last session; `/sessions` picks one. | `--continue`, `--resume [id]`, `/resume`; `--fork-session` and `/branch` copy history to a new id. | `codex resume`, `--last`, `codex exec resume --last`; `codex fork` branches. | `opencode run --continue`, `--session <id>`, `--fork`; `/sessions` in the TUI. | `-c` continues the most recent; `-r` browses; `--session <file or partial id>`. | `hermes chat --resume <id>` or `--continue`; `hermes sessions list`. | [CC](https://code.claude.com/docs/en/sessions) · [CX](https://developers.openai.com/codex/developer-commands) · [OC](https://opencode.ai/docs/cli/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sessions.md) · [HM](https://hermes-agent.nousresearch.com/docs/reference/cli-commands) |
| Rewind | `/rewind` truncates the transcript to an earlier message (stage 8). | `/rewind` or `Esc Esc` restores conversation, code or both. | `/undo` is listed but became a no-op when ghost snapshots were removed. | `/undo` and `/redo` revert the last message. | `/tree` moves to any earlier point in place; the abandoned branch is summarised; `/fork` and `/clone` make new files. | Not verified. | [CC](https://code.claude.com/docs/en/checkpointing) · [CX](https://github.com/openai/codex/pull/19481) · [OC](https://opencode.ai/docs/tui/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/sessions.md) |
| File checkpoints | `checkpoint.py` (step 33) copies a file before `write_file` or `str_replace` touches it; `/undo` puts a turn back. | "Checkpointing": a snapshot before each user turn; files changed by bash or by subagents are not tracked. | None today (see the pull request above). | Git-based snapshots (`snapshot` config) revert files with `/undo`; the project must be a git repository. | Not verified. | Not verified. | [CC](https://code.claude.com/docs/en/checkpointing) · [CX](https://github.com/openai/codex/pull/19481) · [OC](https://opencode.ai/docs/tui/) |
| Crash recovery | A session that ends in an unanswered tool call gets a synthetic result on restart (step 34). | Not verified. | `[history] persistence` and `--ephemeral` control writing; recovery not verified. | Not verified. | Not verified. | Compression splits sessions through `parent_session_id` chains, so lineage survives. | [CX](https://developers.openai.com/codex/config-file/config-reference) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |

## Subagents

A subagent is a second loop with a fresh transcript and a smaller tool
set. Only its final report enters the parent's context.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Definition | Built in: `subagent.task` (stage 15). Since step 36, `.agents/agents/*.md` with front matter `name`, `description`, `tools`, `max_turns`; each becomes a tool `agent_<name>`. | `.claude/agents/*.md` with `name`, `description`, `tools`, `model`, `maxTurns`, `permissionMode`, `memory` and more; built-ins Explore, Plan, general-purpose, fork. | TOML files in `~/.codex/agents/` or `.codex/agents/` with `name`, `description`, `developer_instructions`; built-ins `default`, `worker`, `explorer`. | `agent.<name>` in `opencode.json` or `.opencode/agents/*.md` with `mode: primary`, `subagent` or `all`; built-ins `general`, `explore`, `scout`. | None in the core: "No sub-agents." The `pi-subagents` package adds a `subagent` tool. | `delegate_task` in `tools/delegate_tool.py`; no definition files. | [CC](https://code.claude.com/docs/en/sub-agents) · [CX](https://developers.openai.com/codex/agent-configuration/subagents) · [OC](https://opencode.ai/docs/agents/) · [pi](https://pi.dev/packages/pi-subagents) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |
| Invocation | The `task` tool, or `agent_<name>` tools; `/pipeline <task>` runs planner, workers and reviewer (step 36). | The Agent tool; `@"name (agent)"`; `claude --agent name`. | Model tools `spawn_agent`, `send_input`, `wait_agent`, `close_agent`; `/agents` switches threads. | `@general <text>` by hand, or a primary agent calls it through the `task` permission. | The `subagent` tool from the package. | `delegate_task` with `goal`, `context` and an optional `tasks[]` batch; `action: spawn`, `list`, `steer`, `stop`. | [CC](https://code.claude.com/docs/en/sub-agents) · [CX](https://github.com/openai/codex/blob/main/codex-rs/core/src/tools/handlers/multi_agents_spec.rs) · [OC](https://opencode.ai/docs/agents/) · [pi](https://pi.dev/packages/pi-subagents) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |
| Isolation | A fresh message list; `WITHHELD` removes `task`, edits, jobs and `ask_user`; `MAX_TURNS` is 12. | Its own context window; background subagents get a reduced tool set. | Inherits the parent's permission and sandbox; per-agent `sandbox_mode` override. | A child session; per-agent `permission` and `tools`. | Foreground children run in the parent process; background children run in a detached runner. | A fresh `AIAgent` with its own terminal session and filtered toolsets; only the final summary returns. | [CC](https://code.claude.com/docs/en/sub-agents) · [CX](https://developers.openai.com/codex/agent-configuration/subagents) · [OC](https://opencode.ai/docs/agents/) · [pi](https://pi.dev/packages/pi-subagents) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |
| Parallelism and depth | `descriptions` runs up to `MAX_PARALLEL` (4) at once (step 29); a subagent cannot call `task`. | Background by default when the result is not needed at once; `SendMessage` continues one. | `agents.max_concurrent_threads_per_session`. | `subagent_depth` (default 1). | Chains such as "implement, then review" in the package. | `tasks[]` fan out on a thread pool; `delegation.max_spawn_depth` (default 1). | [CC](https://code.claude.com/docs/en/sub-agents) · [CX](https://developers.openai.com/codex/config-file/config-sample) · [OC](https://opencode.ai/docs/config/) · [pi](https://pi.dev/packages/pi-subagents) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |
| Background jobs | `bash_background`, `job_status`, `job_wait`, `job_kill` in `harness/jobs.py` (step 29). | Background subagents and the Monitor tool. | A PTY-backed `unified_exec` tool. | Not verified. | None: "No background bash", the docs suggest tmux. | `/bg` and a live monitor on `Ctrl+T`. | [CC](https://code.claude.com/docs/en/tools-reference) · [CX](https://github.com/openai/codex/tree/main/codex-rs/core/src/tools/handlers) · [pi](https://pi.dev) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation) |

## Hooks

A hook is user code that runs at a named point in the loop and may block,
replace or add to what the loop does.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Form | `hooks.py` (step 27): a `command` (JSON event on stdin) or a `python` entry `module:function`. | Handler types `command`, `http`, `mcp_tool`, `prompt`, `agent`; a `matcher` regex per group. | Types `command` and `mcp_tool`; `prompt` and `agent` are parsed but skipped; `async` hooks run in the background. | TypeScript plugins only; no shell-command hooks. | TypeScript extensions only; `pi.on(event, handler)`. | Three kinds: Python plugin hooks, gateway hooks (`HOOK.yaml` plus `handler.py`) and shell hooks under `hooks:` in `config.yaml`. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) |
| Where | `~/.simple-harness/hooks.json` and `./.agents/hooks.json`, merged per event. | `hooks` in the settings files, plugin `hooks/hooks.json`, skill and subagent front matter. | `~/.codex/hooks.json`, `.codex/hooks.json`, `[[hooks.<Event>]]` in `config.toml`; `/hooks` trusts or disables them. | `.opencode/plugins/*.ts` or an npm package in the `plugin` config key. | `~/.pi/agent/extensions/` and `.pi/extensions/` (after project trust). | `~/.hermes/plugins/<name>/`, `~/.hermes/hooks/<name>/`, `~/.hermes/agent-hooks/`. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) |
| Events | Six: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `PreCompact`, `SessionStart`, `SessionEnd`. | Thirty or more, including `PermissionRequest`, `Stop`, `SubagentStart`, `PostCompact`, `FileChanged`. | Twelve, including `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `Stop`, `SubagentStart`. | `tool.execute.before`, `tool.execute.after`, `permission.ask`, `chat.message`, `event` for any bus event. | `tool_call`, `tool_result`, `turn_start`, `turn_end`, `context`, `before_provider_request`, `session_before_compact` and more. | Twenty-seven plugin hooks such as `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `transform_tool_result`, `subagent_start`. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) |
| Blocking | Exit code 2 with stderr as the reason, or JSON `{"block": "reason"}`. | Exit code 2 blocks; JSON `permissionDecision: deny`. | Exit code 2 blocks; JSON `decision: "block"`. | Throw from `tool.execute.before`. | Return `{ block: true, reason }` from `tool_call`. | `pre_tool_call` can block or modify. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [OC](https://opencode.ai/docs/plugins/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/hooks) |
| Failure policy | A hook that crashes, times out (30 s) or prints non-JSON is noted and ignored. | Non-zero exit codes other than 2 are non-blocking. | Other exit codes are non-fatal; `timeout` is 600 s by default. | Not verified. | Extensions run with full system permissions; a crash is not verified. | Not verified. | [CC](https://code.claude.com/docs/en/hooks) · [CX](https://developers.openai.com/codex/hooks) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/extensions.md) |

## Memory

Memory is what the agent keeps between sessions on its own, apart from
instruction files the user writes.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Store | `memory.py` (step 25): one markdown file per fact with front matter, under `~/.simple-harness/memory/<project>/` and `_user/`. | "Auto memory": `~/.claude/projects/<project>/memory/` with a `MEMORY.md` index and topic files. | "Memories": files under `~/.codex/memories/`, enabled by `[features] memories = true`. | None first-party; plugins or MCP servers supply it. | None; the session JSONL and `pi.appendEntry()` custom entries persist state. | `~/.hermes/memories/MEMORY.md` (2 200 characters) and `USER.md` (1 375 characters). | [CC](https://code.claude.com/docs/en/memory) · [CX](https://developers.openai.com/codex/customization/memories) · [OC](https://opencode.ai/docs/rules/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/session-format.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Who writes | The model, through `remember`, `recall` and `forget` tools. | The model, when asked to remember or on its own; `/memory` edits it. | A background job that summarises earlier sessions and redacts secrets. | Nobody. | Nobody. | The model, through a `memory` tool with `add`, `replace` and `remove`; `memory.write_approval` can gate it. | [CC](https://code.claude.com/docs/en/memory) · [CX](https://developers.openai.com/codex/customization/memories) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| How it loads | The index of names and descriptions rides in the late block; `recall` reads one file. | The first 200 lines of `MEMORY.md` load every session; topic files load on demand. | `/memories` toggles use and contribution per chat. | Not applicable. | Not applicable. | Injected into the system prompt once at session start; never changes mid-session. | [CC](https://code.claude.com/docs/en/memory) · [CX](https://developers.openai.com/codex/customization/memories) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory) |
| Procedures | Skills in `.agents/skills/` (stage 4), written by the user. | Skills (`SKILL.md`); custom commands merged into skills. | Skills in `.agents/skills`, `$HOME/.agents/skills`; `$skill-name` invokes one. | Skills in `.opencode/skills/`, `.claude/skills/`, `.agents/skills/`. | Skills in `~/.pi/agent/skills/`, `.pi/skills/`, `.agents/skills/`; the agent reads `SKILL.md` with `read`. | Skills the agent itself creates and patches through `skill_manage`; `/learn` turns a document into a skill. | [CC](https://code.claude.com/docs/en/skills) · [CX](https://developers.openai.com/codex/build-skills) · [OC](https://opencode.ai/docs/skills/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/skills.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) |
| External providers | None. | None. | ChatGPT memory on the web is separate from the local store. | Third-party plugins; not verified. | None. | `memory.provider`: `honcho`, `mem0`, `supermemory` and others, one at a time. | [CX](https://developers.openai.com/codex/customization/memories) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers) |

## Evals

An eval runs the agent on a fixed task in a fresh workspace and scores the
result.

| Aspect | This repo (stage/step) | Claude Code | Codex CLI | OpenCode | pi | Hermes | Sources |
|---|---|---|---|---|---|---|---|
| Harness | `evaluate.py` (step 30): `harness eval <suite> --repeat N --keep`. | `claude plugin eval` for plugins. | None built in; an external harness parses `codex exec --json`. | None. | None. | No scored harness; `batch_runner.py` records trajectories with per-tool statistics. | [CC](https://code.claude.com/docs/en/plugin-evals) · [CX](https://developers.openai.com/blog/eval-skills) · [OC](https://opencode.ai/docs/cli/) · [pi](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/README.md) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/batch-processing) |
| Task format | A directory with `task.md`, an optional `workspace/` and one checker: `check.py`, `expect.txt` or `judge.md`. | `evals/<case>/prompt.md` plus `graders/*.md` of type `regex`, `tool_used`, `tool_order`, `file_exists`, `llm` or `baseline`. | `--output-schema` gives structured output for a rubric. | Not applicable. | Not applicable. | A JSONL prompt file; output is ShareGPT-style conversations. | [CC](https://code.claude.com/docs/en/plugin-evals) · [CX](https://developers.openai.com/codex/non-interactive-mode) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/batch-processing) |
| Isolation | A fresh temp copy of the workspace, a fresh session, every prompt auto-approved. | Non-interactive sessions under the OS sandbox; refuses to run unsandboxed with Bash. | The normal sandbox of `codex exec`. | Not applicable. | Not applicable. | Not verified. | [CC](https://code.claude.com/docs/en/plugin-evals) · [CX](https://developers.openai.com/codex/non-interactive-mode) |
| Report | `eval_report.json` with pass rate, tokens and cost per task. | With and without the plugin, three runs each, `--json` for CI, an HTML report. | Not applicable. | Not applicable. | Not applicable. | Per-tool success and failure counts. | [CC](https://code.claude.com/docs/en/plugin-evals) · [HM](https://hermes-agent.nousresearch.com/docs/user-guide/features/batch-processing) |

## What they all agree on

- **One loop.** Every harness runs the same loop: call the model, run the
  tool calls, append the results, call again until a reply has no tool
  calls. Codex, OpenCode, pi and Hermes expose it in readable source. Claude
  Code documents it as the "agentic loop".
- **A JSON transcript on disk.** Four of five write one JSON file per
  session (Claude Code, Codex, OpenCode and pi use JSONL; Hermes uses
  SQLite). This repo does the same in stage 8. Resume is a file read.
- **Instruction files walk the directory tree.** All five read `AGENTS.md`
  or `CLAUDE.md` from a home directory, then from the project root down to
  the working directory, and concatenate them. Step 31 does the same. Three
  of five (OpenCode, pi, Hermes) accept both names.
- **A headless mode.** Each has a one-shot flag that prints the final
  answer and exits, and each has a JSON event stream for tools that wrap it.
  Step 21 adds `-p`.
- **Skills as a directory with `SKILL.md`.** Claude Code, Codex, OpenCode,
  pi and Hermes load skills by name and description and read the body on
  demand. Stage 4 does this with `read_skill`.
- **Compaction is a summary plus a kept tail.** Every harness asks the
  model for a summary and keeps recent messages. Claude Code and OpenCode
  can drop old tool output first. Stage 14 strips, then summarises.
- **Hooks block with a return value.** Where hooks exist (Claude Code,
  Codex, this repo) a command hook blocks by exit code 2 with stderr as the
  reason. OpenCode, pi and Hermes block by throwing or returning from code.
- **A subagent starts empty and returns one report.** Claude Code, Codex,
  OpenCode, Hermes and the pi package all give the child a fresh transcript
  and pass only the final text back. Stage 15 states this as three rules.

## Where they disagree

- **Whether to ship permissions at all.** Claude Code, Codex, OpenCode and
  Hermes ship rule systems. pi ships none and tells the user to run in a
  container or write an extension. This repo sides with the four in stage
  11.
- **Where rules live.** Claude Code and OpenCode put rules in JSON settings.
  Codex uses a Starlark rule language plus TOML. Hermes uses YAML with an
  auxiliary model scoring risk. This repo keeps rules in Python code.
- **Which rule wins.** Claude Code evaluates deny, then ask, then allow.
  OpenCode takes the last matching rule. Codex takes the most restrictive.
  These orders give different answers for the same command.
- **Whether a sandbox is the harness's job.** Claude Code and Codex ship an
  OS sandbox. Hermes ships container backends. OpenCode and pi ship none;
  pi argues that a partial sandbox is worse than an honest absence. Stage
  12 sides with Claude Code and Codex, and admits Windows has no boundary.
- **Custom tools.** Claude Code and Codex accept custom tools only through
  MCP. OpenCode, pi and Hermes accept a local file that defines a tool. pi
  rejects MCP outright because tool descriptions cost context. This repo
  does both: a Python function in stage 2.2 and an MCP client in step 26.
- **Hooks as shell commands or as code.** Claude Code, Codex and this repo
  run shell commands that read JSON on stdin. OpenCode and pi run
  TypeScript in-process. Hermes runs Python plugins, YAML gateway hooks and
  shell scripts. The shell form works from any language; the code form can
  edit messages in place.
- **Whether the harness needs subagents.** Claude Code, Codex, OpenCode and
  Hermes build them in. pi leaves them to a package. OpenCode and Hermes
  cap nesting with a depth setting that defaults to 1; this repo withholds
  `task` from every subagent.
- **Memory.** Claude Code and Hermes let the model write memory files
  during a session. Codex generates memories in a background job from past
  sessions. OpenCode and pi keep no memory beyond instruction files. This
  repo follows Claude Code and Hermes in step 25.
- **Rewinding files.** Claude Code snapshots before each turn and OpenCode
  uses git snapshots. Codex removed its snapshots. pi rewinds the
  transcript as a tree but not the files. Step 33 captures files per tool
  call and rewinds per turn.
- **Evals.** Only Claude Code ships a scored eval runner, and only for
  plugins. Codex points at an external harness. Hermes records trajectories
  without scoring. Step 30 ships a small scored runner with three checker
  types.
- **Language and openness.** Claude Code is closed. Codex is Rust. OpenCode
  and pi are TypeScript. Hermes is Python. This repo is Python until step
  45 ports the loop to TypeScript.

## Run it

This step has no new commands. The copied harness runs as in step 36.

```bash
cd step_37_production_anatomy
pip install -e .
harness
```

You should see the step 36 banner. `/help` lists `/pipeline`, and the
system prompt names the planner, worker and reviewer definitions.

To check the README itself:

```bash
python -m pytest -q test_step.py
```

You should see every test pass. The tests read this file and never touch
the network.

## What to notice

- Every table has a cell for this repo. Nothing in the five harnesses is
  missing a counterpart here, though the counterpart is often smaller.
- The disagreements cluster in three places: permissions, sandboxing and
  custom tools. The loop, the transcript and the instruction files are
  settled.
- "None" is a design choice in pi and a gap in OpenCode. The pi docs say
  why a feature is absent. Absence without a stated reason is the harder
  one to read.
- A harness that is closed (Claude Code) is documented in more detail than
  one that is open (OpenCode). Docs and source are different kinds of
  evidence, and the sources column says which one each cell rests on.

## Diff from step 36

- `README.md`: new. The ten comparison tables, the agreement and
  disagreement sections.
- `test_step.py`: new. Checks that the README exists, has the ten mechanism
  headings, and that every citation URL has a scheme and a host.
- `pyproject.toml`: version `0.36.0` to `0.37.0`.
- `harness/`, `.agents/`, `evals/`, `AGENTS.md`: copied from step 36
  without change.
