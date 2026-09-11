# simple-coding-harness

**A coding agent harness built from scratch, one commit at a time, following
[*Let's build a Coding Agent Harness from Scratch (Step by Step, No frameworks)*](https://www.youtube.com/watch?v=Lu1UWqVTbQg)
by Neural Breakdown with AVB and its repo
[avbiswas/neural-code](https://github.com/avbiswas/neural-code).** Then the
same harness rebuilt on four agent SDKs, so you can see what each one does
for you.

The video walks through its commits, stage 1 to stage 15. Each stage here is
a directory with the same files the video shows at that point, a README that
quotes the relevant part of the video, and an offline test that drives the
code with a fake model. The code is an independent implementation with the
same structure; the ideas and their order are the video's.

## Part 1 - The video, stage by stage

| Stage | Video | Adds | Files that change |
|------:|------:|------|-------------------|
| [1](step_01_minimal_chat/) | 01:19 | minimal chat: one prompt, one reply, usage printed | `llm.py` |
| [2.1](step_02_1_bash_tool/) | 02:54 | a `bash` tool: JSON schema, `subprocess.run`, tool call parsed | `llm.py` |
| [2.2](step_02_2_generic_tools/) | 09:53 | `tools.py`: `TOOLS` dict + `TOOL_SCHEMAS`, dispatch by name | `tools.py`, `llm.py` |
| [2.3](step_02_3_read_file/) | 10:57 | `read_file` | `tools.py` |
| [2.4](step_02_4_agent_loop/) | 12:07 | **the agent loop**: `agent.py` feeds tool results back; prefix caching | `agent.py`, `llm.py` |
| [3](step_03_better_ui/) | 16:54 | rich UI, outer chat loop, usage with cached tokens | `ui.py`, `agent.py` |
| [4](step_04_skills/) | 18:31 | skills: `SKILL.md` front matter in the prompt, `read_skill` on demand | `skills.py`, `tools.py`, `llm.py` |
| [5](step_05_file_editing/) | 25:08 | `write_file`, `str_replace` | `tools.py`, `llm.py` |
| [6](step_06_late_injection/) | 26:37 | late injection: `<env>` block appended to the request, never stored | `context.py`, `agent.py` |
| [7](step_07_file_freshness/) | 28:28 | file freshness: mtime `SEEN` dict, stale-file reminder | `context.py`, `tools.py` |
| [8](step_08_sessions_rewind/) | - | JSONL sessions, `--resume`, `/sessions`, `/rewind`; freshness via git status | `session.py`, `commands.py`, `agent.py`, `ui.py` |
| [9](step_09_installable_command/) | 30:30 | package + `main()` + console script (`harness`, the video's `neuralcode`) | `harness/`, `pyproject.toml` |
| [10](step_10_todos/) | 29:26 | `write_todos`; the plan re-injected every call | `todos.py`, `context.py`, `llm.py` |
| [11](step_11_permissions/) | 31:44 | allow / ask / deny rules before every tool call | `permissions.py`, `agent.py`, `ui.py` |
| [12](step_12_sandbox/) | 33:02 | OS sandbox for bash (Seatbelt / bubblewrap), timeouts | `sandbox.py`, `tools.py` |
| [13](step_13_readable_todos_input_line/) | - | todo checklist panel, prompt_toolkit input line | `prompt.py`, `ui.py` |
| [14](step_14_compaction/) | 36:50 | cap / strip / fit tool output; compaction agent, 85% → 35%, note in the system prompt | `history.py`, `compact.py`, `agent.py` |
| [15](step_15_subagents/) | 41:57 | `task` subagent: own context, fewer tools, same loop, only the answer returns | `subagent.py`, `tools.py` |

Stages 8 and 13 are in the reference commits but not narrated in the video.

## The loop, since that is the point

Stage 2.4, `agent.py`, unchanged in spirit through stage 15:

```python
while True:
    message, usage = call_llm(messages)              # the model sees the whole transcript
    messages.append(message.model_dump(exclude_none=True))
    if not message.tool_calls:                        # plain text: the turn is over
        break
    for tool_call in message.tool_calls:              # otherwise run each call ...
        args = json.loads(tool_call.function.arguments)
        result = TOOLS[tool_call.function.name](**args)
        messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})  # ... and feed it back
```

Later stages wrap it (stage 3), inject into its request (6), save its
messages (8), gate its tool calls (11, 12), shrink its transcript (14) and
point a copy of it at a fresh list (15). Follow `agent.py` through the
stages to see each change land.

## Run a stage

```bash
pip install -r requirements.txt
export BASE_URL=https://openrouter.ai/api/v1     # the video: OpenRouter
export API_KEY=sk-or-...
export MODEL=deepseek/deepseek-v4-flash          # the video's model; any tool-calling model works

cd step_02_4_agent_loop && python agent.py       # stages 2.4 - 8: flat files
cd step_15_subagents && python -m harness.agent  # stages 9 - 15: a package
pip install -e step_15_subagents && harness      # or install the command
```

Any OpenAI-compatible endpoint works: OpenAI (`https://api.openai.com/v1`),
Gemini (`https://generativelanguage.googleapis.com/v1beta/openai/`),
DeepSeek, Ollama. From stage 9 the variables can live in
`~/.simple-harness/env`.

## Tests

Every stage has a `test_step.py` that runs the real files against a fake
model, so nothing needs a key:

```bash
python run_tests.py            # every stage
python run_tests.py 2 14       # stages 2.x and 14
```

CI runs the whole ladder on Linux, macOS and Windows.

## Part 2 - The same harness on four agent SDKs

Stages 16-19 rebuild the stage 15 feature set on a framework each, so you
can see exactly which of the video's ideas a given SDK does for you and
which stay yours. The rules table from stage 11 (`rules.py`) is copied into
each unchanged: the SDK supplies the hook, you supply the policy.

| Step | Framework | Runs where | You still write |
|-----:|-----------|------------|-----------------|
| [16](step_16_claude_agent_sdk/) | **Claude Agent SDK** (`claude-agent-sdk`) - Claude Code as a library | spawns the `claude` CLI | policy (`can_use_tool` + `PreToolUse` hook), a `UserPromptSubmit` injection hook, one MCP tool, a subagent definition, the screen |
| [17](step_17_openai_agents_sdk/) | **OpenAI Agents SDK** (`openai-agents`) - loop, sessions, approvals, agents-as-tools | in-process, any OpenAI-compatible endpoint | all coding tools (stage 5 verbatim, wrapped), skills, todos, the request filter that does late injection + stripping, the screen |
| [18](step_18_google_antigravity_sdk/) | **Google Antigravity SDK** (`google-antigravity`) - the Antigravity runtime as a wheel | a bundled runtime binary, Gemini or OpenAI-compatible | a policy list, three hooks, a `SubagentConfig`, two tools, todos |
| [19](step_19_deepseek_harness/) | **DeepSeek Harness** (`deepseek-harness-sdk`) - everything is a Cordis plugin | a bundled `dsh` runtime over JSON-RPC | the policy as a `tools/pre-execute` plugin, the patch that mounts it, the event renderer |

### Who owns which mechanism

| Mechanism (stage) | Hand-built (1-15) | Claude Agent SDK | OpenAI Agents SDK | Antigravity SDK | DeepSeek Harness |
|------------------|:-:|:-:|:-:|:-:|:-:|
| agent loop (2.4) | you | SDK | SDK | runtime | runtime |
| coding tools (2.1-2.3, 5) | you | SDK | **you** | runtime | runtime |
| custom tools (2.2) | you | `@tool` + MCP server | `function_tool` | plain functions | `defineTool` plugin |
| skills (4) | you | SDK (`.claude/skills`) | **you** | runtime (`skills_paths`) | runtime |
| late injection (6) | you | hook | request filter | prompt prefix | runtime |
| file freshness (7) | you | SDK | **you** (filter) | runtime | runtime |
| sessions / rewind (8) | you | SDK | `SQLiteSession` + `pop_item` | runtime | runtime (JSONL) |
| todos (10) | you | SDK | **you** | **you** | runtime |
| permissions (11) | you | hook + callback | guardrail + approval pause | policy list + hook | plugin |
| OS sandbox (12) | you | SDK flag | - | runtime flag | provider seam |
| compaction (14) | you | SDK | **you** (strip only) | runtime | runtime |
| subagents (15) | you | `AgentDefinition` | `agent.as_tool()` | `SubagentConfig` | runtime |

Install the SDKs with `pip install -r requirements-sdks.txt`. Their tests
never launch a model.

## Platform notes

- **macOS / Linux**: the stage 12 sandbox uses `sandbox-exec` (built in) or
  `bwrap` (`apt install bubblewrap`). The banner shows which is active.
- **Windows**: no OS sandbox; the banner says `sandbox: none`. `bash` runs
  through `cmd.exe` unless you run from Git Bash or WSL.

## Credits

- Avishek Biswas, [neural-code](https://github.com/avbiswas/neural-code)
  and the [video walkthrough](https://www.youtube.com/watch?v=Lu1UWqVTbQg)
  this ladder follows stage for stage.
- The Seatbelt profile in stage 12 follows the one used by the OpenAI Codex
  CLI, as the video does.

MIT licensed.
