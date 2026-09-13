# Steps 21 - 45: build spec

Shared conventions for every step below. Each step is one directory
`step_NN_<name>/` in this repo. Each step is built ON TOP of the previous
step: copy the predecessor's `harness/`, `.agents/`, `pyproject.toml`
(bump the version to `0.NN.0`), then add the feature. Keep every earlier
feature working.

## Rules for every step

- Base is `step_(NN-1)_*`. If that directory has no `.done` file yet, wait
  for it: `until [ -f ../step_(NN-1)_*/.done ]; do sleep 30; done` (loop in
  Bash calls of at most 10 minutes each). Then copy. Never edit files
  outside your own step directory.
- Offline `test_step.py`: never launches a model, browser, GUI, or network.
  Follow the fake-model pattern in `step_15_subagents/test_step.py`
  (`os.environ.setdefault("API_KEY", "x")` before importing `harness`,
  `FakeMessage` with `model_dump`, monkeypatch `agent.call_llm` or
  `llm.call_llm`). Aim for 5-10 focused tests plus one loop smoke test.
- `README.md` with this structure: `# Step NN - Title`; **What this step
  adds**; the idea (why); `## The code, piece by piece` with 5-8
  ` ```python ` snippets, each introduced by a line naming the file in
  backticks like `` `harness/browser.py`: ``; explanation under each; `##
  Run it` (commands + what you should see); `## What to notice`; `## Diff
  from step NN-1`. Every snippet line must exist verbatim (whitespace
  normalised) in the named file; `python check_snippets.py NN` checks it.
  Elide with a line `...`.
- Prose style: short sentences (about 20 words), active voice, consistent
  terms, no idioms, no first person, no references to any video or author.
- Module docstrings start with `"""Step NN - ...`. Docstrings only describe
  the code.
- Python 3.10+, Windows-compatible (this machine is Windows; paths via
  pathlib; no POSIX-only calls without a fallback).
- Optional heavy libraries (playwright, pyautogui, mcp) are imported lazily
  inside functions so the harness and tests work without them. Tests that
  need them use `pytest.importorskip`.
- When done and green: `python run_tests.py NN` and `python check_snippets.py
  NN` from the repo root must pass, `grep -rn -i "video\|youtube" step_NN_*`
  must be empty, then create the marker file `step_NN_*/.done` (empty file).
  Report the file list, test output and snippet-check output.

## Step 21 - Streaming and headless mode (`step_21_streaming_headless`)

Base: `step_15_subagents` (the hand-built harness; step 20 is the OpenRouter
variant and is not in this chain).

1. `harness/llm.py`: `call_llm(messages, tools=None, on_delta=None)` uses
   `stream=True` and `stream_options={"include_usage": True}`. Accumulate
   `delta.content` (calling `on_delta(text)` for each piece) and
   `delta.tool_calls` by `index` (id, function.name, function.arguments
   concatenated). Return `(message, usage)` where `message` is a
   `StreamedMessage` dataclass with `.content`, `.tool_calls` (objects with
   `.id`, `.function.name`, `.function.arguments`), and
   `model_dump(exclude_none=True)` returning the same dict shape the loop
   already appends. Usage comes from the final chunk (`chunk.usage`); keep
   the same usage dict keys.
2. `harness/ui.py`: `stream_start()`, `stream_delta(text)`, `stream_end()`
   print the agent's text live (a header, then raw text, then a newline).
   Keep `ui.agent()` for replay.
3. `harness/agent.py`: extract the inner loop into
   `turn(messages, user_input, cli=None)` that returns the (possibly
   compacted) message list; `main()` calls it. The spinner shows only until
   the first delta arrives. Add `-p/--print PROMPT`: run one turn without the
   banner or the input loop, print the final assistant text to stdout, exit 0.
4. Tests: a fake streaming client yielding chunks (text deltas, two tool
   calls split across chunks by index, a final usage chunk) assembles the
   right message; `on_delta` is called in order; `turn()` feeds tool results
   back; `-p` prints the final text.

## Step 22 - Parallel tool calls (`step_22_parallel_tools`)

1. `harness/tools.py`: split `execute()` into `decide(tool_call) ->
   (args, action, reason)` (JSON parse + `permissions.check`) and
   `run(tool_call, args) -> result`. Keep `execute()` as decide + ask + run
   for callers that want the old behaviour.
2. `harness/agent.py` and `harness/subagent.py`: when a reply has more than
   one tool call, decide all of them first on the main thread (so `ask`
   prompts appear one at a time, in order), then run the allowed ones
   concurrently with `concurrent.futures.ThreadPoolExecutor(max_workers=4)`,
   and append results in the original order. Denied or declined calls get
   their message as the result without running. UI panels print after all
   finish, in order. Single calls keep the direct path.
3. Tests: three calls to a slow fake tool (0.3s each) finish in under 0.7s
   total and results are in order; a denied call among allowed ones does not
   run; a single call still works; the subagent uses the same path.

## Step 23 - Browser use (`step_23_browser_use`)

1. `harness/browser.py`: a lazily created Playwright (sync API) Chromium
   page, headless unless `BROWSER_HEADLESS=0`. Tools: `browser_open(url)`,
   `browser_click(target)` (CSS selector, or visible text via
   `get_by_text`), `browser_type(selector, text, submit=False)`,
   `browser_read()` (page title + URL + visible text, through
   `history.cap`), `browser_screenshot(path)` (PNG inside the project),
   `browser_close()`. Each returns a short result string; errors are results.
2. A browser subagent, `browse(task)`, built like `subagent.task` but with
   only the `browser_*` tools plus `read_file`, its own system prompt
   (navigate, read, report under 200 words, never enter credentials),
   `MAX_TURNS = 20`. The main agent gets only `browse`, not the raw browser
   tools, so page dumps stay out of the main context. Explain this choice in
   the README.
3. `harness/permissions.py`: `browser_open` asks unless the URL's host is in
   `BROWSER_ALLOW` (comma list, default empty); other browser tools allow.
4. `pyproject.toml`: add `playwright` as an optional dependency group
   `browser`. README: `pip install playwright && playwright install chromium`.
5. Tests: a fake page object (monkeypatch `browser._page` and
   `browser.page()`) so all tools run offline; `browse` toolset excludes
   edits and `task`; permission decision for allow-listed and other hosts.
   Add one live test guarded by `pytest.importorskip("playwright")` and an
   env flag `HARNESS_LIVE_BROWSER=1` that opens `about:blank` and reads it.

## Step 24 - Computer use (`step_24_computer_use`)

1. `harness/computer.py`: `computer_screen()` -> size; `computer_screenshot()`
   captures the screen with `PIL.ImageGrab.grab()` (fallback `pyautogui`),
   saves a PNG under `~/.simple-harness/shots/`, and returns the marker
   `[[image:<path>]]` plus a note; `computer_act(action, x=None, y=None,
   text=None, keys=None)` with actions click, double_click, right_click,
   move, drag, type, key, scroll via `pyautogui` (imported lazily).
2. `harness/agent.py` (and the subagent loop): after appending a tool
   result, if the result contains `[[image:PATH]]`, also append a user
   message whose content is a list with a text part ("screenshot from tool
   X") and an `image_url` part with the PNG as a base64 data URL. Strip the
   marker from the stored tool result. Put this in a helper
   `history.image_message(path, caption)`.
3. `permissions.py`: `computer_act` asks unless `COMPUTER_AUTO=1`;
   `computer_screenshot` allows.
4. Tests: fake screenshot writes a 2x2 PNG with PIL; the loop appends an
   image message with a data URL; `computer_act` calls a fake pyautogui with
   the right arguments; permission asks by default.

## Step 25 - Persistent memory (`step_25_memory`)

1. `harness/memory.py`: `MEMORY_DIRS = [~/.simple-harness/memory/<project>,
   ~/.simple-harness/memory/_user]`. A memory is `<slug>.md` with YAML front
   matter `name`, `description`, `type` (user | project | feedback |
   reference) and a body. Tools: `remember(name, description, content,
   type="project", scope="project")` writes or replaces;
   `recall(name)` returns the body; `forget(name)`. `memory_index()` -> one
   line per memory (name: description), like `skills_prompt`.
2. `context.py`: inject `<memory>` block with the index in the late block
   (after `<todos>`), only when non-empty.
3. `commands.py`: `/memory` lists memories with scope and type.
4. `compact.py` or `commands.compact`: after a compaction, save the handoff
   note as a memory named `handoff-<session id>` (type `project`) so the
   next session can recall it. `llm.py`: system prompt tells the model when
   to remember (durable facts about the user, the project, corrections) and
   to recall before asking the user something it may already know.
5. Tests with a temp memory dir: remember/recall/forget round trip, index in
   the late block, `/memory` listing, compaction saves the note, front
   matter parsing tolerates a missing description.

## Step 26 - MCP client (`step_26_mcp_client`)

1. `harness/mcp_client.py`: read `~/.simple-harness/mcp.json` and
   `./.agents/mcp.json`; shape `{"servers": {"name": {"command": ..., "args":
   [...], "env": {...}}}}` (stdio only). Use the `mcp` package
   (`mcp.client.stdio.stdio_client` + `ClientSession`) inside a background
   thread running its own asyncio loop, so the sync harness can call
   `call_tool`. On start, `connect_all()` lists each server's tools and
   registers them in `TOOLS` / `TOOL_SCHEMAS` as `mcp__<server>__<tool>`
   with the server's JSON schema as `parameters`. The wrapper joins text
   content parts and passes through `history.cap`. A server that fails to
   start is reported with `ui.note` and skipped.
2. `permissions.py`: MCP tools ask unless the name matches an entry in
   `MCP_ALLOW` (comma list of globs, e.g. `mcp__fs__*`).
3. `commands.py`: `/mcp` lists servers, status, and tool names.
4. Ship `.agents/mcp.json` pointing at a tiny example server
   `.agents/mcp_echo_server.py` written with `mcp.server.fastmcp.FastMCP`
   (tools `echo(text)` and `add(a, b)`), so `harness` shows real MCP tools
   out of the box when `mcp` is installed.
5. Tests: registration from a fake session object (name mangling, schema
   pass-through, cap), permission default and allow-list, config loading
   from a temp dir; plus a live test guarded by `pytest.importorskip("mcp")`
   that spawns the echo server and calls `echo`.

## Step 27 - Hooks (`step_27_hooks`)

1. `harness/hooks.py`: config `~/.simple-harness/hooks.json` and
   `./.agents/hooks.json`; shape `{"PreToolUse": [{"matcher": "bash|write_*",
   "command": "python check.py"}], "PostToolUse": [...], "UserPromptSubmit":
   [...], "PreCompact": [...], "SessionStart": [...], "SessionEnd": [...]}`.
   A hook is either `command` (shell; gets a JSON event on stdin with
   `event`, `tool_name`, `tool_input`, `tool_result`, `prompt`, `cwd`;
   exit 0 = continue, exit 2 = block with stderr as the reason; stdout may
   be JSON `{"result": ...}` to replace a tool result or `{"context": ...}`
   to add text to the late block) or `python` (`"module:function"` imported
   and called with the event dict, returning the same dict shape or None).
   `run_hooks(event_name, event) -> HookOutcome(blocked, reason, result,
   context)`. Matchers are glob patterns on tool name, `*` for all.
2. Wire in: `tools.decide/run` (PreToolUse can block, PostToolUse can
   replace the result), `agent.turn` (UserPromptSubmit context goes into
   the late block for that turn), `commands.compact` (PreCompact),
   `agent.main` (SessionStart, SessionEnd). Blocking returns a tool result
   string `Blocked by hook: <reason>`.
3. Ship `.agents/hooks.json` with two examples: a PreToolUse hook that
   blocks `write_file`/`str_replace` on paths matching `.env`, and a
   PostToolUse hook that appends every tool name to
   `.agents/tool_log.txt`. Both as small Python scripts in `.agents/`.
4. Tests: a python hook blocks a call; a command hook replaces a result;
   UserPromptSubmit adds context; matcher globs; a hook that crashes is
   reported and ignored, never fatal.

## Step 28 - Plan mode and structured output (`step_28_plan_mode`)

1. `harness/plan.py`: `MODE` = "act" | "plan". In plan mode the tool set
   offered to the model is read-only: `bash` (only commands the rules rate
   `allow`), `read_file`, `read_skill`, `task`, plus `submit_plan`.
   `submit_plan(plan)` takes a JSON object validated against
   `PLAN_SCHEMA` (`goal`, `steps: [{title, files: [str], actions: [str]}]`,
   `risks: [str]`) with `jsonschema` if installed, else a manual check;
   invalid plans return an error result listing the problems. A valid plan
   is stored, drawn as a panel, and the harness asks `approve? (y/n)`. On
   yes: the steps become `write_todos` items, `MODE` becomes "act", and the
   plan is injected in the late block as `<plan>` until the todos are all
   completed. On no: stays in plan mode with the user's feedback appended.
2. `commands.py`: `/plan` and `/act` switch modes; the banner and the late
   block show the mode. `llm.py`: a plan-mode prompt suffix.
3. `agent.py`: `call_llm(messages, tools=plan.toolset())`; the bash rule
   restriction is enforced in `permissions.check` when `MODE == "plan"`.
4. Tests: plan toolset has no edit tools; a bash `ask` command is denied in
   plan mode; invalid plan -> error result; valid plan + approve -> todos and
   mode act; `/plan`, `/act`.

## Step 29 - Background jobs and parallel subagents (`step_29_jobs_parallel_subagents`)

1. `harness/jobs.py`: `bash_background(command)` starts a `subprocess.Popen`
   (through the sandbox wrapper) writing to a temp file, returns
   `job-<n>`; `job_status(id)` -> running/exit code + last 20 lines;
   `job_wait(id, timeout=60)`; `job_kill(id)`. Same permission rules as
   `bash`. The late block lists running jobs in `<jobs>`. Session end kills
   remaining jobs.
2. `subagent.task(description=None, descriptions=None)`: `descriptions`
   (list) runs one subagent per item concurrently (`ThreadPoolExecutor`,
   max 4), each with its own message list; the UI tags nested panels with
   the subagent number; the result is the reports joined with headers.
   Update `TASK_SCHEMA` (`description` or `descriptions`, at least one).
3. Tests: a background job with `python -c` finishes and status shows its
   output; `job_kill` on a sleeping job; three parallel subagents with a
   thread-safe fake `call_llm` return three reports in order; the late block
   lists a running job.

## Step 30 - Evaluation harness (`step_30_eval`)

1. `harness/evaluate.py` and a `harness eval <suite>` subcommand (argparse
   subparsers in `agent.main`; plain `harness` keeps the chat). A suite is a
   directory of task directories. Each task has `task.md` (the prompt),
   optional `workspace/` (copied into a fresh temp dir before the run), and
   one checker: `check.py` (run with the workspace as cwd; exit 0 = pass),
   or `expect.txt` (substring of the final answer), or `judge.md` (a prompt
   for an LLM judge; the judge gets task, answer and workspace file list,
   must reply PASS or FAIL first).
2. Each task runs `agent.turn` in-process with a fresh message list and a
   fresh session, cwd set to the temp workspace, `ui.approve` auto-yes,
   permissions kept. Record pass/fail, wall time, prompt/completion/cached
   tokens (sum of usage), cost if present, and the final answer. `--repeat N`
   runs each task N times and reports pass rate. Print a table and write
   `eval_report.json` in the suite dir.
3. Ship `evals/` with three tasks: `write_hello` (write hello.txt with five
   lines; check.py), `fix_test` (workspace with a failing pytest; check.py
   runs pytest), `find_function` (expect.txt with the file name; the prompt
   tells the agent to use a subagent).
4. Tests: run the suite with a scripted fake model that passes two tasks and
   fails one; assert the report shape, pass rate, and that each task ran in
   its own temp workspace; `--repeat 2` doubles the run count.

## Step 31 - Project instruction files (`step_31_instruction_files`)

1. `harness/instructions.py`: discover `AGENTS.md` (and `CLAUDE.md` as an
   alias) in `~/.simple-harness/`, in every ancestor of the working
   directory from the git root down, and in the working directory itself.
   Order: home first, then root to leaf. `instructions_prompt()` joins them
   with a header per file (`# Instructions from <relative path>`). Inject
   into the SYSTEM prompt (stable prefix), not the late block. Truncate each
   file at 20,000 characters and say so in the text.
2. `commands.py`: `/init` sends an explorer subagent (the `task` tool) with a
   fixed question (build system, test command, layout, conventions) and
   writes the report to `AGENTS.md` in the working directory after
   `approve? (y/n)`. `/instructions` lists the files that were loaded.
3. Ship an example `AGENTS.md` in the step directory.
4. Tests with a temp tree: discovery order, the alias, truncation, `/init`
   writes the file with a fake subagent, the prompt contains the headers.

## Step 32 - Context budget (`step_32_context_budget`)

1. `harness/budget.py`: `breakdown(messages)` -> ordered dict of estimated
   tokens for: system prompt, instruction files, skills index, memory index,
   tool schemas, transcript text, tool results, images; plus the total and
   the window. `render()` draws one bar per category and the percentage of
   `CONTEXT_WINDOW` used. The usage line shows the real prompt tokens next
   to the estimate.
2. `commands.py`: `/context` prints the breakdown. `ui.note` warnings at 50%
   and 75% of the window, once each per session.
3. Deferred tools: a tool whose schema is over 300 tokens is sent as a
   one-line stub; a `load_tool(name)` tool returns the full schema and
   enables it for the rest of the session (`TOOL_SCHEMAS` becomes
   `active_schemas()`). The system prompt lists the deferred tool names.
4. Tests: the breakdown sums to the total, every category is present, the
   stub and load flow enables a tool, warnings fire once.

## Step 33 - Workspace checkpoints and /undo (`step_33_checkpoints`)

1. `harness/checkpoint.py`: before `write_file` or `str_replace` runs, copy
   the current file (or record that it did not exist) into
   `~/.simple-harness/checkpoints/<session>/<turn>/<hashed path>` and
   append a manifest line. `undo_turn()` restores every file of the last
   turn in reverse order and deletes files that did not exist.
2. `commands.py`: `/undo` reverts the last turn's file changes and rewinds
   the transcript one turn. `/rewind` to point N also restores the files to
   the state at N. `/checkpoints` lists turns and files.
3. Wire it as a PreToolUse hook from step 27 rather than inside `tools.run`;
   explain the choice in the README.
4. Tests: edit then undo restores the file; a new file that is undone is
   deleted; rewind restores; the manifest survives a restart.

## Step 34 - Durability and recovery (`step_34_durability`)

1. `llm.call_llm`: retry on `openai.RateLimitError`, `APIConnectionError`
   and 5xx status errors with exponential backoff (0.5s, 1s, 2s, 4s, at most
   5 tries) and a `ui.note` per retry. On giving up, return an error the
   loop shows to the user; never crash.
2. `agent.turn`: a per-turn limit `MAX_CALLS = 40` model calls; on reaching
   it the loop stops and tells the user. A loop detector: the same tool name
   with the same arguments three times in a row replaces the third call's
   result with "Repeated call detected; change approach or ask the user".
3. Crash recovery: on `--resume`, if the last message is an assistant
   message with tool calls that have no results, `agent.recover()` runs
   those calls (through permissions) and appends the results before asking
   for input; the UI reports how many calls were recovered.
4. Tests: a client that fails twice then succeeds; a repeated call is
   detected; a session file ending in an unanswered tool call is recovered;
   the call limit stops the turn.

## Step 35 - Human in the loop (`step_35_human_in_the_loop`)

1. `ask_user(question, options=None)` tool: prints the question and numbered
   options, reads an answer with `prompt.read`, returns it as the tool
   result. Always allowed. System prompt: ask when a requirement is
   ambiguous; never guess at destructive choices.
2. Steering: during a turn, Ctrl-C does not kill the loop. It stops the
   current wait, reads one line from the user, appends it as a user message
   after the pending tool results, and continues. A second Ctrl-C within two
   seconds exits. Implement with a `KeyboardInterrupt` handler in
   `agent.turn`; document the Windows caveat.
3. Permissions: the approve prompt accepts `y`, `n`, `a` (always, for this
   session, for this tool and the first word of the command) and `never`;
   stored in `permissions.SESSION_RULES`, consulted before `BASH_RULES`.
4. Tests: `ask_user` returns the typed answer; option numbers map to text;
   steering appends the message in the right place (simulate the interrupt
   by raising `KeyboardInterrupt` from a fake tool); an `a` answer is
   remembered.

## Step 36 - Orchestration patterns (`step_36_orchestration`)

1. `harness/agents.py`: subagent definitions from `.agents/agents/*.md`
   (front matter: `name`, `description`, `tools` list, `max_turns`; body is
   the system prompt), like skills. Each definition becomes a tool named
   `agent_<name>` built on `subagent.loop`. The main system prompt lists
   them (name: description).
2. Ship three definitions: `planner` (read-only, returns a numbered plan),
   `worker` (edit tools, executes one step), `reviewer` (read-only, checks a
   diff against a plan step and returns PASS or FAIL with reasons).
3. `commands.py`: `/pipeline <task>` runs planner, then worker per step,
   then reviewer per step, retrying a failed step once with the reviewer's
   notes, and prints a summary table. Independent steps run in parallel
   with the step 29 runner when the plan marks them.
4. Tests: definitions load; tool names; withheld tools respected; the
   pipeline with a scripted fake model plans, works, reviews and retries
   once.

## Step 37 - Production harness anatomy (`step_37_production_anatomy`)

No new harness code. A README that maps every mechanism in this repo to
five production harnesses: Claude Code, Codex CLI, OpenCode, pi, Hermes.
One table per mechanism group (loop, tools, permissions, sandbox, context,
sessions, subagents, hooks, memory, evals) with columns for this repo and
for each harness: what it is called, where it lives, one line on how it
differs. Cite each claim with a link to public docs or source. Where a
harness has no equivalent, say so. Include a "what they all agree on"
section and a "where they disagree" section. A `test_step.py` that checks
each cited URL returns 200 is optional; skip when offline.

## Step 38 - Capstone (`step_38_capstone`)

1. The task: build a small FastAPI todo API with a SQLite store, tests and a
   README, in a fresh workspace, driven only through the harness. Provide
   `capstone/task.md` (the brief), `capstone/evals/` (a step 30 suite with
   five checks: the server starts, CRUD endpoints work, tests pass, a README
   exists, no file outside the workspace changed), and `capstone/run.py`
   that runs the harness headless on the brief and then the eval suite,
   writing `capstone/report.json` and a markdown scorecard.
2. The README documents a full recorded run: transcript summary, tool call
   counts, tokens, cost, eval results, what went wrong and how the harness
   recovered. Run it live once with the OpenAI key from
   `~/.simple-harness/env` if present (`BASE_URL=https://api.openai.com/v1`,
   `MODEL=gpt-4.1-mini`); if no key is present, mark that section pending.
3. Tests: the eval suite passes against a hand-written reference solution
   shipped in `capstone/reference/`.

## Step 39 - Approval modes (`step_39_approval_modes`)

1. `harness/modes.py`: named permission policies: `default` (the stage 11
   rules), `accept-edits` (write_file and str_replace inside the project
   never ask; bash rules unchanged), `read-only` (edits and any bash rated
   `ask` are denied; explorations run), `auto` (nothing asks; `deny` rules
   still apply; the sandbox still enforces), and `plan` (delegates to step
   28). `permissions.check` consults `modes.CURRENT` first.
2. `commands.py`: `/mode [name]` shows or switches the mode; `--mode` CLI
   flag; the banner and the late block `<env>` show the mode.
3. Tests: each mode's verdict for the same four calls (ls, python x.py,
   write inside, write outside); `/mode` switches; `--mode auto` never
   prompts; `deny` rules survive `auto`.

## Step 40 - Handoffs (`step_40_handoffs`)

1. `harness/handoff.py`: a handoff is a transfer of the whole conversation
   to another agent definition (from step 36's `.agents/agents/*.md`): the
   transcript stays, the system prompt and tool set change, and the new
   agent answers the user from then on. Tool `handoff_to(agent, reason)`.
   The loop in `agent.turn` swaps `ACTIVE` (prompt + toolset) when a
   handoff result is seen; the system prompt is replaced by rewriting
   `messages[0]` (explain in the README that this is the one deliberate
   prefix change, and why it is acceptable at a handoff boundary).
2. Ship `router` (decides which specialist should handle the request and
   hands off), `coder`, `reviewer` definitions with `handoffs:` lists in
   their front matter that limit who can hand off to whom.
3. `commands.py`: `/agent` shows the active agent; `/handoff <name>` forces
   one. The UI shows a "handoff -> name" line.
4. Tests: a scripted model hands off; the next call uses the new prompt and
   tools; a disallowed handoff returns an error result; `/handoff` works.

## Step 41 - Stop conditions (`step_41_stop_conditions`)

1. `harness/stop.py`: a `finish(summary)` tool the model calls to end a
   turn explicitly (result: the summary; the loop stops even if the reply
   had other calls); `MAX_TURN_CALLS` (from step 34) and new `MAX_SESSION_COST`
   (dollars, from step 20's cost when present, else token-estimated) and
   `MAX_TURN_SECONDS`; when a budget trips, the loop stops and reports.
2. A `Stop` hook (step 27's hooks): runs when the model produces a final
   answer; exit 2 blocks the stop and its stderr is appended as a user
   message ("Stop blocked: tests were not run"), so the agent continues.
   Ship an example Stop hook that requires pytest to have been run when any
   `.py` file was edited in the turn.
3. Tests: finish ends the turn; cost and time budgets stop the loop with a
   message; the Stop hook sends the agent back once and then allows.

## Step 42 - Streaming tool output (`step_42_streaming_tool_output`)

1. `tools.bash` streams: run through `subprocess.Popen`, forward each stdout
   line to `ui.tool_line(name, line)` as it arrives (through the sandbox
   wrapper), collect the full output, and return the capped result as
   before. The panel shows the last N lines live and finalises when the
   command exits. Background jobs (step 29) reuse the same reader.
2. Long-running subagent and browse calls stream their nested tool lines
   the same way.
3. Tests: a fake command that prints three lines with sleeps produces three
   `tool_line` calls before the result; the result is still capped; a
   timeout still becomes a result.

## Step 43 - Extensions (`step_43_extensions`)

1. `harness/extensions.py`: load every `.agents/extensions/*.py` (project)
   and `~/.simple-harness/extensions/*.py` (user). Each module exports
   `apply(ctx)`; `ctx` offers `ctx.tool(fn, schema)`, `ctx.command(name,
   help, fn)`, `ctx.hook(event, fn, matcher="*")`, `ctx.prompt_section(text)`,
   `ctx.agent(definition)`. Registrations are recorded so `/extensions`
   can list them and so a failing extension is skipped with a note.
2. Refactor skills, hooks, agents (step 36) and MCP (step 26) loading to
   go through the same registry calls, so they are extensions too; the
   README shows the before and after.
3. Ship two example extensions: `git_tools.py` (a `git_diff_summary` tool
   and a `/status` command) and `word_count.py` (a prompt section).
4. Tests: extensions load and register; a broken extension is skipped;
   `/extensions` lists them; the example tool works.

## Step 44 - Replay and trace viewer (`step_44_replay_trace`)

1. `harness replay <session id> [--speed 2]`: reads the JSONL session log
   (step 8) and redraws it turn by turn with the recorded timing (session
   entries gain a `ts` field from this step; older logs replay without
   delays). `--step` waits for enter between turns.
2. `harness trace <session id> --html trace.html`: writes a standalone HTML
   page: one row per model call with tokens, cost, duration, and collapsible
   tool calls and results; images (step 24) inline.
3. `session.save` records `ts` and the usage of each assistant message
   (store `usage` next to the message as a separate `{"usage": ...}` entry
   keyed by index, so the message shape sent to the model is unchanged).
4. Tests: a saved session replays in order; the HTML contains every tool
   call; usage entries are skipped by `load()`.

## Step 45 - The core loop in TypeScript (`step_45_typescript_core`)

1. A Node package `harness-ts/` with the stage 15 feature set: `llm.ts`,
   `tools.ts`, `agent.ts`, `context.ts`, `session.ts`, `permissions.ts`,
   `history.ts`, `compact.ts`, `subagent.ts`, `ui.ts` (plain console),
   using the `openai` npm client. Same file names, same env vars, same
   session JSONL format, so a session written by the Python harness can be
   resumed by the TypeScript one and vice versa.
2. `npm test` with `node --test` against a fake client, mirroring the
   Python tests for the loop, permissions, strip/fit and the subagent.
3. README: a side-by-side table, Python file -> TypeScript file, and the
   three places the two languages differ in practice (streams, threads
   versus promises, sandbox spawning).
4. `test_step.py` runs `npm test` when node is available
   (`pytest.importorskip` style check with `shutil.which("node")`).
